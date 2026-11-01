# Live acceptance and release gate

Status reviewed November 1, 2026 (live tests October 27–29): **scripted live conversation and interruption/recovery
are verified on Google Meet, Zoom, and Teams**. Zoom and Teams each have five
retained recovery trials; see [verification.md](verification.md) for evidence,
fixes, recording-permission behavior, and precise limits. The human/overlap/host-
restriction scenarios below remain release gates for those uses. Source is
published at [Arjun220905/meetstream-pipecat-bridge](https://github.com/Arjun220905/meetstream-pipecat-bridge).

## Commands by operating system

Run commands from the extracted/cloned project folder. On Windows, use
`.\start.cmd "MEETING_URL"`, `.\status.cmd`, and `.\stop.cmd` instead of the
Mac/Linux shell commands below. Keep meeting URLs in double quotes on Windows.
A link-bearing start adds another bot. Full Docker Desktop/Hyper-V and live-call
acceptance on a Windows desktop is still pending; native launcher CI alone does
not satisfy that gate.

## Google Meet first

1. Start the bridge and public WSS tunnel. Run `./status` and confirm readiness.
2. Join a private Google Meet call with a human participant wearing headphones.
3. Run `./start '<actual meeting URL>'`, admit the bot and note its ID.
4. Ask “What is a meeting bridge?” Confirm a relevant spoken reply is audible in
   the meeting. Complete at least three back-and-forth spoken turns.
5. Ask for a long answer. While it speaks, say “Stop, tell me the short version.”
   Confirm old speech stops, the new question is understood, and a new reply plays.
6. Repeat at the beginning, middle, and end of speech (at least five interruptions).
   Check no stale answer resumes and audio does not remain permanently muted.
7. Test pauses, an unmuted loudspeaker, and two overlapping human speakers. Record
   echo, dropped overlap, false interruptions, and capture-to-clear latency.
8. Disconnect the audio socket, control socket, and then remove the bot from the
   meeting. Confirm the companion socket closes and provider sessions stop. Test
   reconnect only after teardown; history is deliberately not restored.
9. Run `./stop` and require confirmed bot removal and exit zero. Run `./status`
   afterward and require Stopped (exit one). Check that both Compose services and
   the owned ngrok tunnel are gone. If removal is unconfirmed, keep state and retry.

Repeat these human-microphone checks on Zoom and Teams before claiming human
acceptance; the scripted checks have already passed on all three platforms. On Zoom,
check `resume_audio_ack`, including a host restriction that prevents self-unmute.
On Google Meet, record the actual `interrupt` acknowledgement (`forwarded` and
`already_interrupted` were observed) and check it does not trigger a loop. Some acknowledgements are platform-specific;
record what actually arrives.

## Evidence to keep

Create a sanitized report for each platform with:

- Date, bridge version, Python and Pipecat versions, platform and bot ID.
- Number of complete spoken turns and interruptions attempted/passed.
- Observed stop latency (human onset to last audible old response), measurement
  method, median and maximum. Do not substitute local command-send latency.
- Whether the next reply played after each interruption.
- Observed echo, overlapping-speech loss, host permissions, and command failures.
- Recording/transcript location if participants permitted evidence capture.
- Pass/fail and remaining limitations. Never include API keys or tokenized URLs.

## Definition of done

- [x] Local implementation and automated transport checks.
- [x] Document source-backed platform interruption semantics and known limits.
- [x] Relevant, real spoken conversation inside a live meeting, with evidence (scripted Google Meet test).
- [x] Successful live barge-in and recovery (scripted Google Meet test).
- [x] Public repository with setup instructions and the verified platform matrix.

The live tests used a second bot to speak scripted questions through each real
meeting; they did not use a human microphone. Basic scripted platform coverage
is complete. Leave the remaining human, overlap, restrictive host-policy, and
concurrency scenarios pending until they are actually tested.
