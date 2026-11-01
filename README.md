# MeetStream × Pipecat

[![Checks](https://github.com/Arjun220905/meetstream-pipecat-bridge/actions/workflows/checks.yml/badge.svg)](https://github.com/Arjun220905/meetstream-pipecat-bridge/actions/workflows/checks.yml)

New to running projects? Follow the [plain-language quickstart](quickstart.md).

Run a Pipecat voice agent in Google Meet, Zoom, or Teams. MeetStream joins the
call; Pipecat runs Deepgram STT → Google Gemini → Deepgram TTS with Silero VAD.

Scripted live conversation and interruption/recovery are verified on Google Meet
(October 28, 2026), Zoom, and Teams (October 29, 2026). Zoom and Teams each passed
five recovery trials. The October 29 arm64 image scan found zero known advisories;
current CI scans are linked above. Human microphones, loudspeaker echo,
overlapping speakers, and restrictive host policies
still need acceptance testing. The supported local setup is one trusted operator
on one host. See [readiness](docs/readiness.md) and [verification](docs/verification.md).
Source: [Arjun220905/meetstream-pipecat-bridge](https://github.com/Arjun220905/meetstream-pipecat-bridge).

## Start and stop

Clone or download this repository first:

```sh
git clone https://github.com/Arjun220905/meetstream-pipecat-bridge.git
cd meetstream-pipecat-bridge
```

Prerequisites: Python 3.11–3.13, Docker Desktop (or Docker Engine with Compose on
Linux), and the ngrok CLI for automatic tunneling. Keep Docker running while
using the bridge. Use the instructions for your operating system below.

On Windows (without WSL), use Docker Desktop's **Hyper-V backend** in Linux-container
mode on supported x86-64 Windows Pro/Enterprise/Education. Install Windows Python
3.11–3.13 and ngrok on PATH. From PowerShell or Command Prompt:

```powershell
.\start.cmd "MEETING_URL"
.\status.cmd
.\stop.cmd
```

Windows installs only the locked launcher dependency; the voice pipeline and
cleanup worker stay in the existing hardened container. `--native` is a Mac/Linux
development option. See the [quickstart](quickstart.md) for setup and the
[verification guide](docs/verification.md) for the pending Windows acceptance checks.
On Mac/Linux:

```sh
./start
```

First run creates a private `.env`, random `BRIDGE_TOKEN`, stable `DEPLOYMENT_ID`,
and installs locked launcher dependencies. Set `MEETSTREAM_API_KEY`,
`DEEPGRAM_API_KEY`, and `GOOGLE_API_KEY` in `.env` when prompted, then rerun.
Set `NGROK_AUTHTOKEN` and install the ngrok CLI for automatic local tunneling;
or set `PUBLIC_URL` to your existing HTTPS/WSS proxy and leave the ngrok token blank.
The proxy must forward `/bridge` and `/bridge/audio`, support WebSockets, and
suppress credential query strings in access logs.

```sh
./start                         # Build/start bridge, cleanup worker, optional tunnel
./start 'https://meet.google.com/your-meeting-code'  # Also invite the agent
./status                        # Check instance, readiness, and owned tunnel
./stop                          # Stop admission, remove bots, stop containers/tunnel
```

Admit **MeetStream Pipecat** from the lobby and speak first. Each URL-bearing start
creates another bot; a start without a URL reuses the deployment. Use the same
command with Zoom/Teams URLs. Hosts may need to allow guest admission and bot audio.
Usage is billed by MeetStream and the voice providers.

`./start --port 8080` changes the host port. `./start --native` selects an optional
unsupervised development process; `./start --container` restores the default.
Run `./stop` before switching modes. Changing `.env` or source requires
`./stop && ./start` to rebuild/reload. On Windows, run `.\stop.cmd` and then
`.\start.cmd` as separate commands. These commands target a single Uvicorn worker;
SQLite refuses another bridge worker sharing its state.

The runtime uses pinned Wolfi/Python 3.13 packages. It replaces the vulnerable
bundled libsndfile with a source build containing the upstream fix; no advisory
exceptions are used. The normal one-line commands also rebuild this image.

Docker provides crash restart, non-root execution, read-only filesystems, bounded
memory/CPU/processes/logs, and persistent private state in a named volume. The
separate cleanup worker removes disconnected, expired, and interrupted creations.
Socket loss ends the conversation and removes its bot; invite a new bot to retry.
History is not restored or replayed. Default limits: four meetings, one hour each,
five minutes to join, and platform idle-leave settings. Configure `.env` before starting.

`./stop` retains unresolved cleanup and exits nonzero until MeetStream confirms
removal. Rerun it after connectivity returns. Do not delete the state volume or
change `DEPLOYMENT_ID` while bots might remain. It also scans this deployment's
remote tags, so losing a local row does not silently lose the bot.

For additional control in container mode (replace PROJECT with the Compose
project shown by `docker compose ls`):

```sh
docker compose -p PROJECT exec -T bridge meetstream-pipecat join 'MEETING_URL' --max-seconds 600 --name 'Meeting Assistant'
docker compose -p PROJECT exec -T reaper meetstream-pipecat stop BOT_ID
```

The local creation API `POST /meetings` and `/metrics` require
`Authorization: Bearer BRIDGE_TOKEN`; creation accepts a UUID-hex
`Idempotency-Key`. The admin token is for the trusted operator, not tenant clients.
The server issues independent expiring credentials bound to each registered bot
and both sockets. The admin token cannot open a meeting socket. `tenant` is an
operator-assigned attribution field, not a tenant login system.

## Transport

```text
Meeting → MeetStream → /bridge/audio → Pipecat input (native rate → 16 kHz)
                                      STT → turn/VAD → LLM → TTS
Meeting ← MeetStream ← /bridge       ← Pipecat output (→ 48 kHz)
```

Both sockets send `{"type":"ready","bot_id":"…"}`. Either may arrive first;
both must pair within 30 seconds. Credentials, registered bot identity, duplicate
channels, deadlines, payload sizes, and message rates are checked. Revocation,
malformed data, overload, or a disconnected channel closes the whole session.

Incoming audio supports `0x01` at 48 kHz and `0x04` with a uint32LE rate and one-byte
mono channel count, then length-prefixed UTF-8 speaker ID/name and PCM16. Actual
Google Meet input was 24 kHz. Output is 48 kHz PCM16 mono in paced 100 ms `sendaudio`
chunks. Ingress permits three seconds of burst but only one second of outstanding
pipeline audio, and enforces real-time rate. Output has a five-second budget before
Pipecat queues. A consumer stalled for two seconds fails closed rather than growing
an unlimited audio queue. Interruption invalidates outstanding output credits and
clears the remote queue. Reference text history is capped at 40 messages.

Replace `agent.create_agent()` or pass an `agent_factory` to `server.create_app()`
to customize the pipeline. It receives `MeetStreamTransport` and returns a
`PipelineWorker`. Include `transport.drain()` after STT/VAD to acknowledge and consume
raw ingress audio; custom consumers must release audio credits. Preserve 16 kHz
input for Silero and 48 kHz mono output. Pipecat is pinned to 1.14.0.

## Barge-in and platform limits

Command semantics below come from MeetStream's documentation, checked on October
27, 2026. The final column records this project's separate live verification.

| Platform | `interrupt` | Starting the next reply | Repository live test |
| --- | --- | --- | --- |
| Google Meet | Stops playback and clears its queue; documented `status: cleared` | Next `sendaudio` plays; `resume_audio` is ignored | Hardened build: scripted conversation and two recovery trials passed, October 28 |
| Zoom | Stops playback, clears queue, blocks later audio | Requires `resume_audio`; bridge waits for its matching success acknowledgement | Five scripted live recovery trials passed, October 29 |
| Teams | Stops playback, clears queue, blocks later audio | Requires `resume_audio`; no resume acknowledgement was observed | Five scripted live recovery trials passed, October 29 |

The bridge maps Pipecat's `InterruptionFrame` to MeetStream's `interrupt`, after
Pipecat cancels queued local output. Before new audio it sends `resume_audio`;
this is safe on Google Meet too. It consumes acknowledgements without treating
an interrupt acknowledgement as a fresh interruption. An explicit command failure
(including Zoom `resume_audio_ack` with `success: false`) closes the session and
logs a failure instead of continuing silently. For Zoom links, audio waits up to
five seconds for a successful `resume_audio_ack` carrying the current `resume_id`.
A stale acknowledgement cannot unlock a newer reply; a missing acknowledgement
ends the session. Meet and Teams do not wait for this Zoom-specific acknowledgement.
Sending a command still does not prove remote playback or clearing.

The tested Google Meet deployment returned `interrupt_ack` with `success: true`
and `status: forwarded` (and `already_interrupted` for repeated clears), rather
than the docs' `status: cleared`. Meeting-side captions confirmed truncated old
speech and the new reply. These acknowledgements alone are not proof of playout.

Silero detects speech with a 200 ms onset. Response generation uses a timed
end-of-turn strategy; natural pauses can finish a turn early. Interrupt response
time also includes platform capture buffering, network delay, and playback
buffering. Incoming frames can contain more than a second of audio, so this is
not a promise of subsecond interruption. The bridge paces output to avoid filling
the remote queue far ahead of playback; the platform controls final playout.
Cancelled Pipecat TTS context IDs are also rejected if a provider delivers late
frames after the local queue was cleared. Custom TTS implementations should
preserve those context IDs.

Incoming audio is **mixed**, with dominant-speaker metadata. It is not an isolated
participant track. The reference drops frames tagged with the bot's exact name
to reduce self-echo, which can also drop overlapping human speech. If the platform
returns the bot's voice with a different/empty label, self-interruption or an echo
loop remains possible. Validate this in the target meeting; do not claim reliable
full-duplex barge-in across platforms until the overlap tests pass. There is no
acoustic echo canceller in this reference.

Zoom required host approval of each bot's recording request for live audio capture
and displayed a recording indicator even with `RECORD_AUDIO=false`. That setting
controls the requested stored recording; it does not suppress Zoom's capture
permission or indicator. Teams required lobby admission in the tested meeting.
The observed native input was 32 kHz on Zoom and 24 kHz on Teams; Teams labelled
speakers `unknown`, so attribution-based echo filtering cannot be assumed there.

## Shared scope with LiveKit

`protocol.py` has no Pipecat dependency. Its binary decoder, PCM format constants,
and control command builders form the reusable MeetStream boundary. Keep these
in one shared package if a LiveKit bridge is added. Socket authentication,
handshake/pairing, and teardown policies should also be shared once there is a
second implementation. No LiveKit dependency or speculative adapter is included.
Pipecat frame cancellation, VAD, resampling, and its output queue stay in this adapter.

## Operations and verification

`/health` checks process identity; `/ready` checks state, cleanup heartbeat/backlog,
and recent provider failures. It does not make billable provider probes. Fatal or
repeated provider errors cancel speech, send a safe meeting chat fallback, and
remove the bot; transient errors briefly block new meetings. No stale speech is replayed.

Stored audio recording is **requested off by default** (`RECORD_AUDIO=false`);
video recording is requested off. Zoom's live-capture permission and recording
indicator still apply. The bridge
writes no audio or transcript files. Vendor processing/retention policies still
apply. Private SQLite holds creation payloads and socket credentials until confirmed
removal, then removes them and retains a 24-hour tombstone. Protect `.env`, `.run/`,
and the Docker volume; URL credentials must also be redacted by your proxy.

See the [operations runbook](docs/operations.md) for logs, metrics, backup, outage
recovery, and off-host cleanup. A local machine cannot clean meetings while it is
powered off: continuous production use requires a separately scheduled `sweep`
with only the MeetStream key and deployment identity. MeetStream does not enforce
a hard in-call deadline on Meet/Teams; the cleanup scheduler enforces it.

For development on Mac/Linux, with `uv` installed:

```sh
uv sync --frozen --extra dev
uv run --frozen --extra dev python -m unittest discover -s tests -v
uv run --frozen --extra dev ruff check .
uv run --frozen --extra dev ruff format --check .
uv run --frozen --extra dev python -m build
```

The [Checks workflow](https://github.com/Arjun220905/meetstream-pipecat-bridge/actions/workflows/checks.yml) runs
Python 3.11–3.13 tests, native Windows launcher tests, container integration tests,
lock consistency, and dependency/image advisory scans on pushes and pull requests.
It can also be run manually from Actions. All seven jobs passed in the
[November 1 public run](https://github.com/Arjun220905/meetstream-pipecat-bridge/actions/runs/41278502218),
including six native Windows launcher checks per Python version; full Windows desktop
Docker/live-meeting acceptance remains pending. See [verification](docs/verification.md)
for dated evidence and limits. Tests do not call paid providers. To rerun only
the native Windows launcher checks after first-time setup:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_launcher.py -v
```

The optional paid-provider test (Mac/Linux) uses local WebSockets, not a meeting:

```sh
.venv/bin/python scripts/check_voice.py question.wav --interrupt-with followup.wav --report reports/voice.json
```

Complete [live acceptance](docs/acceptance.md) for your platform before promising
its interruption behavior. No human-audible interruption latency guarantee is made.

## References

- [MeetStream audio protocol](https://docs.meetstream.ai/guides/websockets/real-time-audio-streaming)
- [MeetStream commands and platform differences](https://docs.meetstream.ai/guides/websockets/meeting-control-patterns)
- [MeetStream bridge architecture](https://docs.meetstream.ai/guides/websockets/bridge-server-architecture)
- [MeetStream Create Bot API](https://docs.meetstream.ai/api-reference/api-endpoints/bot-endpoints/create-bot)
- [MeetStream public reference agent](https://github.com/meetstream-ai/meetstream-agent)
- [Pipecat source](https://github.com/pipecat-ai/pipecat)

MIT licensed. See [LICENSE](LICENSE).
