# I153-S03 Distribution and Handoff

Slice: Add ready-for-install checklist and minimal smoke test

Owner role: Linux Host Preparation

Secondary review roles: Senior Documentation Engineer, Senior System Architect,
Senior Tester

Execution mode: explicit role-based fallback. The smoke path was reviewed as
optional live guidance and was not executed.

## Implemented guidance

- `documentation/user_guide/installation.adoc` now owns a ready-for-install
  checklist covering host shell, filesystem, Incus access, profile/storage,
  quality/preflight, and secret hygiene.
- The Incus baseline contains an explicitly optional temporary-container smoke
  and bounded cleanup instruction.
- README, handbook, and troubleshooting point operators to the canonical
  checklist and do not imply that the smoke is part of the quality gate.
- Commands remain POSIX/Linux/WSL examples and do not use `sudo incus` or broad
  provider cleanup.

## Verification

```text
git diff --check
```

Result: `PASS`. Live smoke was not run.
