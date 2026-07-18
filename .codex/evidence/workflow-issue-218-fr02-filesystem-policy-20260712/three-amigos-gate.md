# FR-2 Four-Role Three Amigos Gate

Date: `2026-07-12`
Decision: `READY_FOR_WORKFLOW`
Confidence: `96%`
Execution profile: `FULL_PATH`
Live infrastructure: `NOT_RUN`

## Requirement perspective

Direct ownership is FR-002, AC-002's path portion, AC-003, UT-006 through
UT-009, CLI-002, SEQ-002, DOC-005, DOD-003, FORBID-002, and GOV-006. A Windows
mount is a default blocker. The exact override is narrow and auditable; it
cannot bypass host support, consent, resources, networking, or any later gate.
Unknown WSL mount facts fail closed. No automatic move/copy is permitted.

Decision: `READY_FOR_WORKFLOW`.

## Architecture perspective

Use a pure `project_filesystem` domain contract, an inspector port, separate
evaluate and authorize services, a protected-evidence repository port,
mountinfo and XDG local-state adapters, and composition-root wiring. General
serializers are path-free. The protected repository verifies atomicity and
owner-only permissions. The accepted WSL2 boundary and autonomous setup safety
ADRs are sufficient; no new ADR is required.

Decision: `PASS` for workflow creation; execution only after dedicated FR-2
publication and S3/S3D locks.

## Development perspective

Preserve the standard-library-only installer bootstrap. Filesystem
authorization occurs after typed host detection and before Python bootstrap,
secrets, general evidence, subprocesses, or live steps. The global
`--preflight` is the CLI-002 equivalent; the override propagates through
installer, preflight, setup, and platform-init guards. Responsibilities remain
small and hexagonal.

Decision: `READY`.

## Test and operations perspective

Baseline regressions are green and FR-2 is explicitly RED. Tests must cover
generic drive/mount detection, false prefixes, WSL-native/native paths,
resolved symlinks, longest mountpoint and escaping, unreadable/contradictory
mountinfo, irrelevant and applied overrides, evidence failures, path leakage,
bootstrap closure, direct setup, and no later action after `BLOCKED`.

Decision: `PASS_FOR_WORKFLOW_CREATE`.

## Security/evidence perspective

The resolved path is allowed only in the protected local XDG decision file.
That document is allowlist-only, atomically replaced, `0600`, below a `0700`
directory, and permission-verified. An evidence failure blocks override use.
Committed workflow evidence, preflight JSON, logs, progress, and general
installation context remain path-free.

Decision: `PASS` with the protected-evidence lock.

## Dependency and parallelization decision

FR-1 is merged, cleaned up, and green on `main`. FR-2 is one serial slice.
Parallel writes are unsafe because domain schema, preflight ordering, installer
bootstrap, CLI propagation, and evidence schema are coupled. Read-only
specialist reviews are allowed.

Final gate: `READY_FOR_WORKFLOW`.
