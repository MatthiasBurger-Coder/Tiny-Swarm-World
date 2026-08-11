# S3D Execution Plan — Issue #148

Workflow: `issue-148-20260809`
Version: `issue-148-v1.0.0`
Execution mode: `FULL_PATH`
Ordering: strictly serial, following the workflow and the user-requested
issue chain.

## Preflight

- Upstream handoff `I147-S06`: PASS_LOCAL at commit `6b415c9`.
- Active branch is the issue-chain feature branch, not a shared branch.
- No live LXC, Incus, Docker, Swarm, network, or service-bootstrap commands are
  authorized or required.
- Shared performance evidence uses the `installer-bootstrap` segment from
  `documentation/process/performance-evidence-contract.md`.
- Local Linux/WSL quality is authoritative; live and external quality states
  remain explicitly unverified.

## Serial dependency graph

```text
I148-S01 -> I148-S02 -> I148-S03 -> I148-S04 -> I148-S05 -> I148-S06 -> I148-S07
```

All implementation slices lock the same installer and installer-test files,
so no parallel stream is safe. No visible Codex subagent runtime is available;
each slice receives an explicit role-based fallback review and distribution
record.

## Slice gates

| Slice | Scope | Exit gate |
|---|---|---|
| I148-S01 | inventory and measurement plan | every probe/file-read region mapped |
| I148-S02 | single-pass env parsing | parser compatibility and one invocation-local representation |
| I148-S03 | Git/worktree/ignore probe reduction | safety warning semantics and call-count tests |
| I148-S04 | identity/group probe boundary | no host-state persistence or new native probe behavior |
| I148-S05 | evidence-context coalescing | deterministic redacted context and optional unknown state |
| I148-S06 | regression/performance evidence | focused tests and full local quality PASS |
| I148-S07 | independent completion audit | all nine requirements PASS_LOCAL |

Each slice is committed and pushed before the next serial slice starts. The
workflow must not jump to Issue #145 until I148-S07 has passed.
