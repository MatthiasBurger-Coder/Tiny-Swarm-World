# S440-03 distribution

Workflow issue-440-final-acceptance v1.0; slice S440-03 — Cancellation and strict-type reliability.
S3/S3D baseline a68c873c; branch/ref and clean worker worktree required before writes. S440-01 deterministic inventory independently ACCEPTED while live readiness remains PARTIAL/NOT_VERIFIED; explicit continuation rule permits these independent deterministic fixes.
Affected areas: backend, tests, security/quality and architecture review. Owner: Senior Python Automation Developer.
Mode: parallel isolated implementation relative to the other independent fix slice; tests/production edits inside each stream are sequential under one worker to avoid overlap.
Real Codex subagents: yes. Fallback: no. Worktree: ../Tiny-Swarm-World-worktrees/issue440-slice-03-reliability, branch <workflow-branch>-slice-03-reliability.
Expected touched files: S440-03 metadata's installation_profile, versioned_manifest_repository, migration_admission and their exact targeted tests. Root owns shared workflow status/context/distribution/consolidation only; workers must not edit those.
Locks: source/test sets and contract locks for 02 versus 03 are disjoint; no shared schema, module move or architecture mutation. Each remote test environment is separately source-bound and root-controlled; full gates are serialized.
Quality: regression tests first (root executes on designated SSH PC WSL, reproducing RED before worker fix), then targeted suite, current-source full canonical quality, diff check and independent review. No live effects, host configuration or Sonar issue-state write is authorized.
Consolidation: root reviews isolated worker diff, accepts stream-specific test evidence, integrates only this slice, runs its required gate and records per-slice checkpoint. No worker commit/push/merge to workflow/main. No guard/type/path/cancellation/coverage weakening or blanket analysis suppression.
