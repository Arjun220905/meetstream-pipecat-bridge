# Local operations

Windows operators use `.\start.cmd`, `.\status.cmd`, and `.\stop.cmd` directly in
PowerShell or Command Prompt. Use Docker Desktop's Hyper-V backend with Linux
containers; WSL is unnecessary. See [Windows setup](../quickstart.md#windows-setup-without-wsl)
and [Windows verification status](verification.md#native-windows-launcher--implementation-and-acceptance-status).
The `--native` development mode below is for Mac/Linux only.

The supported topology is one bridge plus a separate cleanup worker on one
Docker host. `./start`, `./status`, and `./stop` manage this deployment and its
optional ngrok tunnel. Native mode is for development. No Kubernetes, Redis,
or external database is required for this topology.

## Health, logs, and alerts

`./status` checks the expected instance, `/ready`, and the owned tunnel. `/health`
is liveness only. Readiness requires usable SQLite, a cleanup heartbeat younger
than 90 seconds, no pending cleanup failures, and no recent provider-error cooldown.
It does not probe STT/LLM/TTS accounts; provider quota/capacity can still fail a call.
Docker restarts crashed processes. Docker health status alone does not restart
an unhealthy process. Maintenance failures terminate the bridge for restart.

Use `docker compose ls` to find PROJECT. Inspect `docker compose -p PROJECT ps`
and `docker compose -p PROJECT logs --tail 100 bridge reaper`. Launcher/build logs
are private in `.run/containers.log`; tunnel logs are `.run/ngrok.log` and
`.run/tunnel-console.log`. Native logs are `.run/bridge.log`. Docker logs rotate
at 10 MB, three files per service. Do not publish raw logs or database files.

`GET /metrics` requires the admin Bearer token. It exposes active sessions,
input/output backlog seconds, pipeline/command errors, overloads, cleanup failures,
and cleanup heartbeat. Keep scraping and alerts on a trusted network. Recommended
operator alerts: `/ready` non-200 for 90 seconds, cleanup pending for 60 seconds,
cleanup heartbeat older than 90 seconds, any sustained overload or provider error
increase, or missing tunnel. No external alert service has been configured locally.

## Stop, retry, and recover

`./stop` stops bridge admission first, removes registered remote bots, and scans
only this deployment's remote tags before taking the cleanup worker and tunnel
down. A 202 accepted removal is not confirmation. Unconfirmed cleanup returns
nonzero and retains state for another `./stop`. If MeetStream is unavailable,
retry when it recovers or remove the identified bots in its dashboard.

On a bridge crash/restart, previous worker leases are revoked and cleaned up;
conversation history is not resumed. A failed socket or stalled audio consumer
closes both channels and schedules bot removal. Invite a new bot after recovery.
The cleanup worker polls every five seconds; an absent worker heartbeat is
recognized after 30 seconds. Remote/API delays can extend removal time.

Default lifetime is one hour, even if speech continues; it is enforced by the
cleanup worker. Lobby/unclaimed joins time out after five minutes. MeetStream's
Meet/Teams integrations do not enforce a hard in-call timeout. Do not rely on
vendor idle-leave behavior as a billing deadline.

## Whole-host loss

The local reaper cannot execute while the machine is off. For continuous
production use, schedule the same image's stateless `sweep` command every minute
on a separate host/container platform with **only** `MEETSTREAM_API_KEY` and this
deployment's stable `DEPLOYMENT_ID` injected through its secret store:

```sh
docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:size=64m --env MEETSTREAM_API_KEY --env DEPLOYMENT_ID meetstream-pipecat:0.2.0 sweep
```

No SQLite volume, STT/LLM keys, admin token, or meeting URL is needed. The sweep
lists only tagged bots, checks each returned deployment tag again, and removes
expired bots. Alert on nonzero exits. It does not end unexpired meetings after
host loss: cleanup occurs at their recorded expiry plus scheduler/API delay.
A hard shorter outage RTO needs an external deployment health monitor that
requests removal; that is outside the local-only setup requested here.

This off-host schedule has **not** been installed. Keep the local machine on
for live use, and run `./stop` before closing it. Preserve DEPLOYMENT_ID during
rebuilds/recovery so remote cleanup continues to find the right bots.

## Credentials, privacy, backup, and updates

The launcher restricts `.env` to mode 0600 on Mac/Linux and a current-user NTFS
ACL on Windows; `.run` is private to that user as well. The private SQLite volume contains per-meeting hashes,
creation payloads (including callback credentials), meeting URLs, leases, and
cleanup state. Logical credential/payload fields are cleared after confirmed
removal; stopped tombstones expire after 24 hours. SQLite WAL/backups may retain
older pages: use encrypted host storage and protect backups as secrets.
Stored audio recording is requested only when `RECORD_AUDIO=true`; video
recording is requested off. Zoom's capture permission/indicator still applies.
The bridge itself does not persist audio or transcripts. Provider policies still apply.

Do not expose `.env`, `.run`, the volume, Docker socket, or metrics publicly.
Terminate HTTPS/WSS at the tunnel/proxy. Disable query-string access logging there;
application access logs are disabled and application logs redact tokens.
The admin token permits creation/metrics; `tenant` does not create a tenant auth boundary.

Before updating, `./stop` and confirm success; then back up the volume using your
platform's encrypted volume snapshot and back up `.env` separately. Avoid copying
a live SQLite main file without WAL. Restore both state and deployment identity,
start once, inspect readiness and cleanup before inviting meetings. Never run
multiple copies against the same deployment identity/state concurrently.

Update the pinned Wolfi base/packages, upstream native-library fix, and `uv.lock` deliberately; regenerate
`requirements.lock` and `requirements-launcher.lock`, run CI/advisory scans, then
start again. On Windows, stop with `.\stop.cmd` and start with `.\start.cmd`.
For dependency maintenance with `uv` installed, the exports used by CI are:

```sh
uv export --frozen --no-dev --no-editable --no-emit-project --no-header -o requirements.lock
uv export --frozen --only-group launcher --no-header -o requirements-launcher.lock
```

Rollback requires
stopping the new deployment first and restoring a compatible image/state snapshot.
Do not remove the named volume until all remote meetings are confirmed stopped.

The container builds soundfile from source so it loads the patched shared
libsndfile in `/usr/local/lib`, with source/license provenance in
`/usr/local/share/libsndfile`. Keep the image-specific regression check and the
advisory gate when updating it. Native mode remains a development convenience
and uses the platform's locked wheel dependencies; production acceptance above
applies to the container.

## Platform-specific operating notes

Zoom needs the host to approve the bot's recording/capture request before live
audio is available. A Zoom recording indicator appeared in the test even though
`audio_required` was false. Do not promise indicator-free capture based on
RECORD_AUDIO alone. Use the complete `/j/` invitation URL with its passcode.
The bridge waits up to five seconds for Zoom's matching successful unmute
acknowledgement; failure or timeout closes the session and schedules removal.
Teams guests needed admission from the lobby in the tested meeting.

A host-ended meeting may return stop-request status `not_requested` together
with lifecycle status `Done`. The reaper treats that completed lifecycle, and
other documented ended/post-call states, as confirmation that the bot is no
longer in the call. It retains unconfirmed live/unknown states for retry. This
keeps readiness and `./stop` from remaining blocked after a naturally ended call.
