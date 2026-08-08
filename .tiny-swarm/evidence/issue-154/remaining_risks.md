# Issue #154 Remaining Risks

Workflow: `issue-154-20260808`

No implementation requirement remains open. The following are explicitly
unverified or operational follow-ups, not hidden completion claims:

1. No live-consented Incus/LXC run was requested or executed. The repository
   therefore makes no `LIVE_VERIFIED` claim for Docker installation, Swarm
   bootstrap, manager `Leader` state, overlay networking, routing, registry,
   Portainer, or downstream service readiness.
2. A real managed manager may report missing or changing membership state, or
   the configured nodes may not communicate over the required Swarm ports.
   The new verification boundary fails closed in those cases; operator live
   evidence is still required for environmental acceptance.
3. Docker-in-container nesting, cgroup, AppArmor, seccomp, capability,
   privileged-profile, host-firewall, and WSL2-specific behavior remain
   provider and host risks that local fakes cannot prove.
4. Existing proxy drift, external Swarm inputs, artifact readiness, and
   deployment credentials remain governed by their existing explicit
   consent and evidence contracts.

The requested local file-storage port is unaffected and carries no new risk
from this issue.
