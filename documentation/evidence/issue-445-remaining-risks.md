# Remaining risks and support limits — issue #445

- Native baseline references are authoritative packaging metadata, not qualified
  upgrades. Zero native source-to-target upgrades are currently advertised.
- Registry/release lookups are not performed. Missing upstream versions and
  resolved digests stay unknown; catalog failure blocks rather than guessing.
- Recorded observations can be stale. No-op refers only to matching recorded
  immutable state; execution must revalidate runtime before mutation.
- Portainer execution/backup/recovery is W07; generic Incus package updates are
  unsupported. Neither mandatory foundation is removed or implicitly changed.
- W06 owns live execution/convergence and persisted desired-image changes.
  #297 keeps its existing invocation-local desired-image limitation.
- No new supported product transition, Podman/Kubernetes scope, live native/WSL2
  qualification, browser result or SonarQube result is claimed. The full gate
  passed on supported Python 3.12.14 with locked dependencies (2,747 tests;
  18 skipped). Skips do not establish live or external success.
- Synthetic digest/transition fixtures validate policy behavior only. They are
  excluded from native product metadata and must never be used as live evidence.
- `.tiny-swarm` is intentionally Git-ignored. A reviewable copy of the six
  required evidence documents is under `documentation/evidence/issue-445-*`.
