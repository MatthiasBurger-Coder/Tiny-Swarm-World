# RC1-E03 restart recovery decision

Candidate c921e69533450fba86d908e2990c106bef87769a. Existing full operator
approval applies to the isolated disposable WSL distribution only. Original
Ubuntu and unrelated sessions must stay running. This isolated branch owns
issue-299 evidence and the restart recovery runbook. The indexed workflow in
the integration checkout remains the selected workflow; host mutations are serialized.

All real agents reached their session usage limit. The root AGENTS fallback
therefore applies: the following are sequential role perspectives, not a new
independent agent or human approval.

Requirement perspective: retain the failed first distribution restart. A
platform-only readiness pass was insufficient; the first full authentication
attempt failed and must remain LIVE_PARTIAL. The subsequent retry exposed an
actual missing Pulsar Manager overlay endpoint. A targeted container restart
caused Swarm replacement; retain the port-allocation task failures and verify
all service/configuration/data/authentication assertions afterward. Do not
claim the first boot recovered automatically or within its original bound.

Architecture perspective: the proposed second boundary is a planned shutdown:
stop Docker and its socket/containerd inside the three owned nodes, manager
first, then shut down Incus and terminate only the isolated distribution.
No service specification, persistent data, Docker version or product guard is
changed. Enabled services resume during normal node startup. The observation
motivates orderly shutdown; Docker's underlying startup race is not established
as a proven root cause. Hard power loss and whole-WSL-kernel recovery are excluded.

QA perspective: record each shutdown exit and inactive unit state, PID-namespace
and PID1 start-time change, unchanged shared kernel boot ID and provider UUIDs.
Bound startup by 600 seconds and require platform plus all eight readiness tests
before the complete 25-live-test and seven-API-check authenticated suite. Require
zero errors/failures/skips and persisted Jenkins fixture/configuration/identity
comparisons. If the repeated boundary fails, retain that failure and continue
root-cause repair; this decision is not a PASS result.
