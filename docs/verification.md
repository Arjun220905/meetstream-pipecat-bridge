# Verification

## Current results — reviewed November 1, 2026

Public source and CI: [Arjun220905/meetstream-pipecat-bridge](https://github.com/Arjun220905/meetstream-pipecat-bridge).
Live results below are dated October 27–29; publication does not rerun those calls.

| Platform | Live result | Independent playback evidence |
| --- | --- | --- |
| Google Meet | Conversation and two hardened-build recovery trials passed October 28; five earlier trials passed October 27 | Meeting captions |
| Zoom | Conversation and five recovery trials passed October 29, plus a final-build regression trial | Audio captured by a second bot and independently transcribed |
| Teams | Conversation and five final recovery trials passed October 29 | Teams captions plus independently transcribed second-bot capture |

These are scripted spoken calls with the actual STT → Gemini → TTS pipeline.
They do not establish human microphone, echo/overlap, restrictive host-policy, or
concurrency acceptance. Windows-only remote CI was run separately before
publication, as described below. Current repository checks are visible in
[Actions](https://github.com/Arjun220905/meetstream-pipecat-bridge/actions/workflows/checks.yml).

### Native Windows launcher — implementation and acceptance status

`start.cmd`, `status.cmd`, and `stop.cmd` run directly in PowerShell or Command
Prompt. No WSL installation or Linux shell is required on the host. The bridge
and cleanup worker still run in the hardened Linux container through Docker
Desktop's Hyper-V backend (supported x86-64 Windows Pro/Enterprise/Education).
Running the voice pipeline as a bare Windows Python process is not offered.

The launcher discovers Windows Python, uses `.venv/Scripts/python.exe`, installs
only hash-locked `python-dotenv`, and uses native Windows file locking, process
inspection, and process-tree shutdown. Windows ACLs restrict settings and logs
to the current user; settings updates are staged in the private directory so
replacement does not restore inherited access. Docker must report Linux-container
mode before startup. Existing cleanup retries and one-line Mac/Linux commands
are preserved.

On October 29, the native Windows CI matrix **passed all six checks on each of
Python 3.11, 3.12, and 3.13**, with no skipped checks:
[successful run](https://github.com/Arjun220905/meetstream-pipecat-windows-checks/actions/runs/40900532893).
The runners used Windows Server 2025, image `windows-2025-vs2026` version
`20261021.278`. Only the launcher dependency was installed.

The MeetStream repository was read-only for the connected GitHub account, so the
exact launcher/check files were tested in an isolated private repository. This
did not publish the reference implementation or upload credentials, meeting audio,
or private runtime state. Run commit: `b5478fcc9536d1b36ebc34066a9b53913301f127`.

The checks exercised:

- Real `.cmd` forwarding of arguments containing spaces and `&`, and preservation
  of exit codes, for start/status/stop.
- Clean `start.cmd` bootstrap in a fresh folder: a Windows virtual environment,
  hash-locked dependency installation, settings creation, and the expected setup
  prompt without configured credentials. `status.cmd` then reported Stopped.
- Real Windows byte-lock exclusion, ACLs after settings replacement, detached
  process ownership, process-tree shutdown, and refusal to kill unrelated PIDs.
- Container lifecycle, failed-cleanup retention, and successful retry with
  **mocked Docker and health responses**. This test does not run a bridge container.

The initial run failed. Windows PowerShell 5.1 inherited PowerShell 7's module
path and could not load `Microsoft.PowerShell.Security` for `Set-Acl`. The shared
PowerShell helper now lets Windows PowerShell construct its own module path.
The test also needed to leave its temporary working directory before deleting
it on Windows; that test cleanup was corrected. All three versions passed after
these fixes. Sanitized evidence and file hashes are in the ignored local report
`reports/windows-ci-verification.json`.

The October 29 macOS suite ran 45 checks: 40 passed, four native Windows checks
skipped, and the image-only library check skipped. Ruff lint/format passed.
The prior hardened Linux arm64 run passed 41 of 44 checks and skipped three
native Windows checks; it predates the added clean-bootstrap check. The ordinary
Mac container start/status/stop lifecycle was verified earlier and remains stopped.

**Full Windows end-to-end test is blocked, not passed.** No Windows client host
or configured self-hosted runner with Docker Desktop/Hyper-V was available.
GitHub's hosted Windows jobs use Windows Server, where
[Docker Desktop is unsupported](https://docs.docker.com/desktop/setup/install/windows-install/).
The successful CI run therefore does not establish Docker Desktop/Hyper-V startup,
automatic ngrok connectivity, live meetings, or Windows production acceptance.
It also does not extend the arm64 image scan to an untested x86-64 build.

To finish on an accessible supported Windows desktop with Docker Desktop using
Hyper-V/Linux containers, configure `.env` and run these actual one-line commands
from the project folder (use a disposable test meeting):

```powershell
.\start.cmd "MEETING_URL"
.\status.cmd
.\stop.cmd
.\status.cmd
```

Require startup and the first status to succeed, verify real spoken playback in
the meeting, require stop to confirm bot removal and exit zero, and require the
last status to print Stopped (exit one). Also confirm the owned ngrok process and
both Compose services are gone. Keep state and retry stop if cleanup is incomplete.

## Evidence and scan dates

Raw captures, screenshots, detailed traces, credentials, and runtime state are
private and excluded from this repository. `reports/...` references below identify
maintainer-held evidence, not files included in a clone. The dated summaries here
record what ran and what remains unverified. The original Windows validation run
is in a private repository; public reruns are available through this repository's
Actions workflow once complete.

The zero-advisory result below is the October 29 Linux arm64 scan. Vulnerability
databases and upstream availability change; use the latest workflow result for
current dependency and image status. The image gate checks high/critical findings;
the historical all-severity scan is a separate result.

## Initial verification — October 27, 2026

The initial implementation was prepared locally for publication. A scripted
conversation and interruption/recovery were verified in Google Meet. At that
point, Zoom and Teams acceptance was still pending; their later results are below.

## Local automated checks

Python 3.11.15 on macOS arm64, Pipecat 1.14.0:

- Seven unittest checks passed using real Pipecat processors and a synthetic meeting
  peer over actual localhost WebSockets.
- Both socket arrival orders, authentication, malformed frames, duplicate channel
  rejection, Unicode speaker metadata, sample-rate conversion, paced output,
  interruption/resume, failure acknowledgements, and session cleanup are covered.
- Ruff lint/format checks and package dependency consistency checks passed.
- Wheel and source distribution built successfully. Both were inspected to confirm
  they contain neither the private `.env` nor any configured API key or token.
- CI is configured for Python 3.11, 3.12, and 3.13 on Linux; those CI runs have
  not been executed here.

## Real provider check, synthetic meeting

Deepgram STT → Gemini 3.5 Flash-Lite → Deepgram TTS, local Silero VAD:

1. Fed a spoken 48 kHz mono question: “Hello assistant. In one sentence, what is
   a meeting bridge?” The STT transcript contained that question and the LLM
   generated a relevant explanation.
2. As response audio began, fed “Actually stop. What is two plus two?” as new
   speech, without injecting an interruption command.
3. VAD caused the pipeline to send `interrupt`. The new question was transcribed;
   the LLM replied “Two plus two is four.” The bridge sent `resume_audio`, followed
   by the new reply audio. There were 1.6 seconds of audio after resuming.

Result: **passed** at 21:45 IST (16:15 UTC). The sanitized local report is
`reports/provider-flash-lite.json` (ignored by Git). The report's
`live_meeting` field is explicitly `false`. This proves the local speech pipeline
and interruption wiring, not remote meeting playback or human-audible stop latency.

Earlier checks observed an exhausted OpenAI credential and intermittent Gemini
503 capacity errors. Gemini 2.5 also rejected this account as a new user. The
reference therefore uses the tested Gemini 3.5 Flash-Lite model and Deepgram for
both speech services. Provider availability remains external; this is not a
guarantee of uninterrupted service.

## Live Google Meet

A private meeting was created in the signed-in browser. Camera and microphone
were disabled. A MeetStream Pipecat agent and a separate controlled MeetStream
test-speaker bot joined the same call. The speaker injected synthesized spoken
questions through the meeting's audio path; no PCM was injected directly into
the agent pipeline. Google Meet's live captions independently showed both speakers.

The agent initially failed to decode the actual incoming format: `0x04` declaring
24 kHz mono PCM16, rather than the public example's `0x01` at 48 kHz. The bridge
now supports both headers, reads the declared rate, and resamples correctly.
A regression check covers the observed frame layout, unsupported channels/rates,
and the transport's 24 kHz → 16 kHz path.

The agent explained a meeting bridge and answered “Paris” to the capital-of-France
question. During a longer explanation, the speaker said “Actually stop. What is
two plus two?” Meet captions showed the old reply cut off at “A voice assistant
connects,” then the new question, followed by the agent saying “2 plus 2 is 4.”
This verifies actual meeting input, generation, audible output recognized by Meet,
speech-triggered cancellation, and playback of the next response.

Five consecutive interruption/recovery trials passed, with a new audible
“Two plus two is four” reply each time. Local driver-prompt-start to
bridge-interrupt-send timings were 0.816, 0.867, 0.832, 0.893, and 0.870 seconds
(median 0.867 seconds). These include prompt delivery, meeting capture, network,
and VAD; they are **not** human-onset-to-last-audible-sample measurements and
must not be published as an end-to-end interruption latency guarantee.

Both bots were stopped through MeetStream; its stop-status endpoint confirmed
`stopped` / `MediaProcessing` for each. The browser host left the call. The
temporary bridge token was rotated after testing.

Private local evidence (ignored by Git): `reports/google-meet-first-reply.png`,
`reports/google-meet-barge-in.png`, the `google-meet-barge-in-*.json` reports,
the captured meeting audio and event log. These contain test meeting details
and should be reviewed before sharing.

The live deployment returned successful `interrupt_ack` messages with `forwarded`
or `already_interrupted` status, differing from the docs' `cleared` example.
Playout was checked through meeting captions, not inferred from those acknowledgements.
An earlier LLM completion timed out; the next question recovered in the same session.

## Still required

Complete the remaining scenarios in [acceptance.md](acceptance.md), including a
human microphone, loudspeaker echo, overlapping humans, host restrictions, and
human-onset-to-last-audible-sample latency. The October 29 scripted Zoom and Teams
results below complete basic live coverage, not those remaining scenarios.

## Hardened-build acceptance — October 28, 2026

The 0.2.0 container uses the unchanged production registration, per-meeting
credentials, pairing, transports, audio budgets, agent, deadlines, and cleanup
worker. A disposable, authenticated acceptance harness attached observers and
provided a second registered test-speaker pipeline. It emitted synthesized WAV
prompts through that speaker's meeting audio, never into the agent input. The
harness was mounted read-only for this test, is absent from the production image,
and was removed from the running deployment after testing.

### Image advisories: passed

The previous Debian-based runtime reported 44 HIGH advisories. The replacement
uses a digest-pinned public Wolfi base and pinned Python 3.13.17, libstdc++, and
libgomp packages. It omits the affected Debian utilities instead of waiving their
findings. Trivy 0.76.1 scanned its OS and Python packages and reported **zero known
advisories at every severity**. The existing HIGH/CRITICAL CI gate remains enabled;
no ignore list, ignore-unfixed flag, or package-database removal was used.

The soundfile wheel bundled vulnerable libsndfile 1.2.2, which package scanning did
not identify. The container now installs soundfile from its locked source and
loads a shared libsndfile built from the checksum-verified upstream
[fix commit c32c090](https://github.com/libsndfile/libsndfile/commit/c32c090ff9bb45e1dae637957c9c9b47b3967623)
for CVE-2026-37555. Compiler/build tooling stays in a separate build stage. The
image retains the native component's source URL and LGPL license under
`/usr/local/share/libsndfile/`. A container regression check verifies the bundled
binary is absent, the patched shared library is actually loaded, source provenance
is present, and PCM WAV read/write works. Raw meeting PCM behavior is unchanged.

### Live Google Meet: passed

A new private meeting was created in the signed-in browser, with host camera and
microphone off. The agent and registered test speaker were admitted. Both creation
payloads had `audio_required: false`; video was disabled. Incoming audio included
`0x01`/48 kHz and `0x04`/24 kHz, and the real STT → Gemini → TTS pipeline ran inside
the hardened Linux arm64 image.

- The test speaker asked the capital of France; the agent answered Paris.
  Google Meet captions independently displayed both question and spoken answer.
- Twice consecutively, the speaker requested a longer explanation, waited until
  agent audio began, then said “Actually stop. What is two plus two?” Speech/VAD
  caused an interrupt, local cancellation, resume, and a new spoken answer.
- Meeting captions showed the old answer cut off at “A voice.” and the new reply
  “2 plus 2 is 4.” This verifies meeting-side playback and recovery, rather than
  relying solely on control acknowledgements or generated text.
- Driver prompt start → interrupt command send measured 0.788 and 0.847 seconds.
  These are diagnostic timings, **not** human-onset-to-last-audible-sample latency.
- After the voice trials, the actual application process was killed with SIGKILL
  while both bots were live. Docker restarted the bridge; the separate cleanup
  worker removed both bots. MeetStream confirmed `stopped` for both after about
  12.8 seconds. Meet's participant panel independently showed the bots gone.
- The browser host left the meeting. `./stop` shut down the test deployment and
  owned tunnel. The ordinary production entrypoint was restored and its one-line
  start/status/stop lifecycle checked again.

Private local evidence, ignored by Git: `reports/hardened-meet-answer.png`,
`reports/hardened-meet-recovery.png`, `reports/hardened-google-meet-trial-1.json`,
`reports/hardened-google-meet-trial-2.json`, `reports/hardened-live-events.jsonl`,
and `reports/hardened-live-crash-cleanup.json`. These contain synthetic test
speech and meeting details; review before sharing. The harness does not persist
audio. The production app does not persist test transcripts or include QA routes.

### Other checks and boundaries

- All **35 checks passed in the production Linux arm64 image**, with networking
  disabled, read-only root, dropped capabilities, and bounded resources.
  macOS Python 3.11 passed 34 checks and skipped the image-specific native-library
  check. The pacing regression measures server send times, so client scheduling
  does not falsely appear to violate output pacing.
- Ruff lint/format, frozen lock validation, hashed requirement export consistency,
  package build/exclusion checks, and the Python dependency audit passed.
- The real paid-provider local-WebSocket interruption check also passed earlier;
  this is separate from the live meeting evidence above.
- No sustained four-call load or human microphone/echo/overlap test was run. Zoom
  and Teams were still pending at this stage. The image scan is a point-in-time known-advisory
  check; refresh it when releasing.
- Remote GitHub CI, publication, off-host expiry scheduling, and external alerts
  remain owner deployment steps. They are not implied by local acceptance.


## Zoom and Teams acceptance — October 29, 2026

Both tests used newly created private meetings, an admitted MeetStream Pipecat
agent, and a separately registered scripted speaker. The host microphone and
camera stayed off; no existing group or external contacts were invited. Each
bot used the ordinary authenticated registration, expiring per-meeting credentials,
production transports, and real providers. A temporary authenticated harness
observed events and captured only the synthetic meeting audio received by the
speaker bot. No prompt PCM was injected into the agent input. The harness is
not shipped or enabled in the production image.

### Fixes exposed by live testing

1. **Zoom unmute ordering:** audio used to follow `resume_audio` immediately,
   before the SDK's acknowledgement. Zoom now waits at most five seconds for a
   successful acknowledgement with the current `resume_id`. A stale ID cannot
   release a newer reply, and failure/timeout ends the session and schedules
   cleanup. Other platforms do not wait for this Zoom-specific message.
2. **Natural meeting-end cleanup:** ending Zoom returned
   `status: not_requested` with `bot_status: Done`. The old cleanup loop kept
   retrying, leaving readiness at 503. Cleanup now accepts documented ended or
   post-call bot lifecycle states as confirmation, even without a stop request.
   The actual completed Zoom records were reconciled and readiness recovered.
   Unknown or still-live states remain pending. This handling is shared with
   the stateless deployment sweep.
3. **Late cancelled TTS:** a Teams probe exposed old audio arriving after the
   local interruption queue was cleared, briefly restarting playback before a
   new answer existed. The transport now rejects subsequent frames tagged with
   a cancelled Pipecat TTS context ID. The regression reproduces late old audio,
   verifies silence, and confirms a new context still plays. The repeated live
   Teams trace shows every resume followed fresh generated text; no earlier
   cancelled context restarted playback.

Regression checks cover matching/stale/missing Zoom acknowledgements, natural
completion without a stop request, retention of still-live bots, and delayed
cancelled-context audio. **All 39 checks pass in the production Linux arm64
container** with networking disabled, read-only root, dropped capabilities, and
resource limits. macOS passes 38 checks and skips the image-only library check.
Ruff checks and the package build pass. The refreshed image advisory scan reports
zero known OS/Python advisories; no scan exception was added.

### Zoom: passed

- A password-protected meeting was created with host and participant video off.
  Both bots needed the host to approve their local recording requests for live
  capture. Zoom displayed a recording indicator, labelled “Cloud recording is on”
  in its UI, despite both creation payloads requesting `audio_required: false`.
  That payload setting must not be described as indicator-free or permission-free
  capture; it controls the requested stored recording.
- Input was **32 kHz mono, binary header `0x04`**. The existing decoder/resampler
  handled it. The agent heard the France question and replied Paris. Some cold
  synthetic prompts lost their opening words in capture/transcription; perfect
  first-phoneme capture is not claimed.
- Five recorded trials interrupted longer explanations at different offsets
  after output began. Every new arithmetic question produced a spoken four answer.
  A separate bot captured the actual Zoom audio; independent transcription shows
  five truncated explanation fragments, each followed by “Two plus two is four.”
  Thus recovery was checked beyond local generation/send events or SDK acks.
- Each Zoom resume returned a successful, matching `resume_audio_ack`; the trace
  verifies unmute acknowledgement preceded the first audio of each reply. An
  additional regression call on the final transport passed after the common
  late-context fix.
- Prompt-start → interrupt-send diagnostic timings for the five retained trials:
  0.396, 0.471, 0.462, 0.472, and 0.460 seconds (median 0.462; maximum 0.472).
  These are not human-onset-to-last-audible-old-sample measurements.

Private evidence: `reports/zoom-verification.json`, `zoom-barge-trial-*.json`,
`zoom-final-live-events.jsonl`, `zoom-final-agent-heard-in-meeting.wav`,
`zoom-final-meeting-listener.json`, and `zoom-live-proof.png`. The extra final-build
trial is `zoom-barge-trial-6.json`. Meeting IDs and invitation passcodes remain
private and are absent from this document.

### Teams: passed

- A private instant meeting was created in the signed-in Teams app. Guests were
  admitted from its lobby and appeared as Unverified. The newer
  `teams.microsoft.com/meet/...` invitation format worked. No host recording
  request was needed in this run; the payload requested stored recording off.
- Input was **24 kHz mono, header `0x04`**, with speaker labels `unknown`. The
  existing decoder/resampler worked. Do not assume reliable participant
  attribution or attribution-based echo suppression from this test.
- Native Teams captions independently displayed the France question and Paris
  answer, the interrupted explanations, and the new “2 + 2 is 4” replies. A
  second-bot audio capture independently confirmed all five retained recoveries.
- `interrupt_ack` returned `success: true`. No `resume_audio_ack` was observed;
  sending `resume_audio` before new audio restored playback. There was no need to
  make Teams wait for a Zoom-style acknowledgement.
- The earlier stale-audio probe was fixed and retested. One additional probe had
  STT omit “plus”; the agent clarified and answered four. A test-harness assertion
  also initially checked too early for a delayed LLM reply. Final checks wait for
  the new answer and audio rather than assuming a fixed response latency.
- Five final diagnostic timings were 1.037, 1.093, 1.096, 1.084, and 1.143 seconds
  (median 1.093; maximum 1.143). They measure prompt-start → interrupt-send, not
  remote audible stop latency or an interruption SLO.

Private evidence: `reports/teams-verification.json`, `teams-barge-trial-*.json`,
`teams-final-live-events.jsonl`, `teams-final-agent-heard-in-meeting.wav`,
`teams-final-meeting-listener.json`, `teams-live-answer.png`, and
`teams-live-recovery.png`. Earlier reproduction evidence is kept separately in
`teams-before-fix-events.jsonl` and `teams-before-fix-agent-heard.wav`.

### Cleanup and limits

Both host meetings were ended for everyone. MeetStream lifecycle/stop endpoints
confirmed that all test bots were out of the calls. The ordinary production
entrypoint was restored; `./start`, `./status`, and `./stop` were checked and the
project was left stopped. Test-only captures/events were copied to private ignored
reports and removed from the runtime volume.

Host policies that forbid self-unmute, a real human microphone, loudspeaker echo,
overlapping humans, and sustained concurrent calls were not tested live. Negative
Zoom unmute acknowledgements and missing acknowledgements are covered locally.
No universal full-duplex, first-syllable, or end-to-end latency guarantee is made.
For vendor semantics, see [control commands](https://docs.meetstream.ai/guides/websockets/meeting-control-patterns),
[stop status](https://docs.meetstream.ai/api-reference/api-endpoints/bot-endpoints/get-stop-status),
and [bot lifecycle states](https://docs.meetstream.ai/guides/reference/bot-status-and-error-codes).
