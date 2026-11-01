# Scope and readiness — November 1, 2026

**Verdict: local image and scripted live acceptance passed on all three platforms.**
The October 29 arm64 image scan found zero known advisories; check current CI
for later dependency and image results. Google Meet conversation,
two interruption/recovery trials, and crash cleanup passed October 28. Zoom and
Teams each passed five live recovery trials October 29. Stored recording was
requested off; Zoom still required capture permission and showed a recording
indicator. This supports the owner-operated local use described below;
it does not establish all-platform or multi-user production acceptance.

Target: local Docker Compose, one trusted operator, one bridge worker and an
independent cleanup worker. This is not a multi-tenant hosted service or an HA
cluster. The reference source is published at
[Arjun220905/meetstream-pipecat-bridge](https://github.com/Arjun220905/meetstream-pipecat-bridge).
The [November 1 public CI run](https://github.com/Arjun220905/meetstream-pipecat-bridge/actions/runs/41278502218)
passed all seven jobs: Linux and Windows matrices, production-container tests,
Python audits, and the high/critical image advisory gate. Windows desktop
end-to-end acceptance remains pending.

## Scope

| Requirement | Result |
| --- | --- |
| Pipecat STT → LLM → TTS in a real meeting | Hardened container verified in Google Meet October 28 |
| Barge-in and recovery | Two hardened-build trials passed October 28; five earlier trials passed October 27 |
| Zoom and Teams | Scripted conversation and five recovery trials each verified October 29 |
| Public reference | Source, license, setup instructions, locked dependencies, and CI published in this repository |
| Share boundary with LiveKit | Framework-neutral codec/commands in `protocol.py`; no second bridge in this checkout. Shared lifecycle extraction deferred until a second consumer exists |
| One-line lifecycle | Mac/Linux: `./start`, `./status`, `./stop`; Windows: `.\start.cmd`, `.\status.cmd`, `.\stop.cmd`; Docker default |
| Windows host | Six native launcher checks passed on each of Python 3.11–3.13; real Docker Desktop/Hyper-V and live-meeting acceptance remain blocked on an accessible Windows host |

The reference scope has public source, real scripted meeting conversations, and
documented interruption limits. The existing live evidence uses a synthesized speaker through a second bot in the
actual call, not a human microphone. Do not promise reliable overlap/echo handling
or all-platform interruption before the remaining acceptance scenarios pass.

## Code blockers addressed

| Previous blocker | Implemented behavior and evidence |
| --- | --- |
| Shared socket token could pair arbitrary bots | Expiring random per-meeting credentials, registered bot binding, hash verification, revocation, duplicate rejection; cross-session and spoofing tests |
| Unbounded raw audio backlog | One-second ingress credits released after STT/VAD; five-second output budget before Pipecat queues; two-second slow-consumer failure; real-time rate guard; overload and interruption-generation tests |
| Orphaned bots after disconnect/crash | Durable SQLite intent and leases, independent five-second reaper, deadline/heartbeat cleanup, fail-closed recovery; fixtures plus real two-bot crash cleanup in 12.8 seconds |
| Ambiguous create/remove requests | Persist request before network, stable idempotency key, documented 507 replay handling, never forget an unconfirmed removal; failure fixtures |
| Local registry could diverge from container | Creation goes through authenticated running bridge; shared state volume for bridge and reaper; host CLI guard |
| Worker could silently die | Docker restart policy, maintenance failure termination, single-worker lock; supervised container lifecycle |
| Provider errors could leave silent calls | Bounded first-chunk retry, safe chat fallback, cancellation, readiness cooldown, cleanup on fatal/repeated errors; simulated failure test |
| No operations surface | Authenticated low-cardinality metrics, liveness/readiness, private/redacted/rotated logs, runbook, bounded resources |
| Unlocked release | Frozen uv lock, hashed requirements export, pinned base/tool versions, Python matrix and container/image scan CI definition |
| Recording enabled | Stored audio/video recording requested off by default; Zoom capture permission/indicator still applies; no bridge audio/transcript persistence |
| Host loss loses local bot IDs | Stateless remote-tag expiry sweep requires only deployment ID and MeetStream key; safety and pagination fixtures |

Session credentials isolate meeting sockets. The admin API remains an owner-only
boundary: a caller holding BRIDGE_TOKEN can create meetings with any attribution
label. `tenant` is not tenant authentication, billing enforcement, or RBAC.

## Remaining release conditions

- **Broader call acceptance:** scripted calls passed on Meet, Zoom, and Teams.
  Human microphone/echo/overlap, restrictive host policies, and sustained concurrent
  calls remain unverified. Zoom capture permission/recording indicators must be
  disclosed even when stored recording is requested off.
- **Whole-host outage:** local operation is supported while this host is on.
  Continuous production needs the off-host expiry sweep/alerts described in
  operations.md. That schedule has not been installed. Meet/Teams do not enforce
  a hard in-call timeout themselves.
- **Release process:** publication CI passed November 1. Review artifacts, tag a release, and configure the deployment's proxy logging, secrets,
  encrypted storage, alerts, and retention policy. These are not configured merely
  by building a local container.
- **Capacity:** four sessions is a conservative admission cap, not a measured
  concurrency SLO. Slow-consumer and rate tests pass; sustained multi-call provider
  load and user-audible end-to-end latency have not been measured.

This is a focused engineering readiness review, not a penetration-test or security
certification. Fixing the source blockers does not establish an all-platform
production acceptance result. See [verification](verification.md) for precisely which checks ran.
