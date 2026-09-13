# Classic Public Beta RC1 release notes and checklist

Qualified product: `c921e69533450fba86d908e2990c106bef87769a`; integrated evidence candidate: `69f040a75fa8a7bc9b9c01bf5eb62f53abeb6a6e`.
[Acceptance decision](rc1-decision.md). Qualification is complete; these notes
prepare publication and do not create a Git tag or GitHub release.

The Classic service-access profile now has verified fresh installation,
reconcile, reversible Jenkins image update, original-direction recovery and
authenticated use on WSL2 and native Linux. Updates observe deployed task images,
preserve data and unrelated configuration, and make repeated convergence a
no-op. The protected runner executes the same canonical full lifecycle.

| Checklist | Verified evidence |
|---|---|
| [x] WSL and native fresh/reconcile/update with every post-phase acceptance | R01/R02/R03/R05 |
| [x] Controlled failed rollout, partial node recovery and repeat recovery | R01/R03 |
| [x] Planned owned-WSL restart and actual native VM reboot, followed by authentication | R02/R03 |
| [x] Deterministic test credentials, supported override precedence and no unintended drift | #277/#295/#296 and current source applicability |
| [x] Final integrated Quality, Python 3.12/3.13 and actual Sonar gate | Candidate evidence matrix |
| [x] Protected manual nightly lifecycle, blocked-dispatch guard and redacted artifacts | R05 and final-ci.json |
| [x] Dependency/SBOM/container configuration scan; candidate digests and bounded access checks | R04/R08 |
| [x] Executed operator journey, current docs and four successful AsciiDoc renders | R07 |
| [x] Maintenance ownership and complete requirement audit | R09/R06 |
| [x] Native test data archived and guest poweroff requested; owned WSL distro stopped and original environment restored | R06 cleanup-and-baseline |

Linux/WSL only; managed Incus/LXC, one manager and two workers, Docker Swarm.
Required stacks: service-access, Portainer, Traefik, Nexus, Jenkins, Pulsar,
SonarQube, Swagger and Infisical. Vaultwarden is historical and not selected.
No Podman/Kubernetes/Java/React runtime is added. Documented prerequisites include
qualified native source/private evidence storage, capacity, unique Incus DNS
names and ownership of the WSL network/bridge. Fresh runs reuse base-image cache
only, with no previous workload volumes.

Known limits: planned Docker-quiesced WSL restart, not hard power loss; supported
Jenkins startup credential consumer, not arbitrary rotation; isolated test
network/socket privileges, not production hardening. Scans cover 13 locked Python
packages and three Dockerfiles; image package-vulnerability status is unassessed.
Resource snapshots are allocated/observed host capacity, not measured peak demand.
The operator walkthrough is an executed automation-assisted journey, not a
fabricated independent first-user study. Actual earlier failures remain retained.

The native guest accepted `systemctl poweroff` after archival. A separate
Hyper-V status query was cancelled, so an observed hypervisor Off state is not
claimed. Original WSL runner 23 actually completed the final blocked control job;
its list API still reported offline at the recorded observation. No test data
or unrelated worktree/session was deleted. Temporary runner 24 was removed and
all seven original GitHub variables restored.

Publication procedure: verify the R06 PR head checks, merge, verify exact merged
SHA Quality/Conda/Sonar, then link the final integration record in #294/#302.
Tag/release creation remains a separate release action. Open #329/#331 are
owned nonblocking maintenance follow-ups.
