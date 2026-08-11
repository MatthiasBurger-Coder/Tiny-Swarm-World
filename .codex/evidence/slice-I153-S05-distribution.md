# I153-S05 Distribution and Handoff

Slice: Document failure cases and user actions

Owner role: Senior Documentation Engineer

Secondary review roles: Linux Host Preparation, Senior System Architect, Senior
Tester

Execution mode: explicit role-based fallback. Recovery guidance was reviewed
for bounded scope and kept in the canonical troubleshooting document.

## Implemented guidance

- Added a common failure decision path mapping consent, provider readiness,
  reset safety, APT reachability, ports/WSL bridge, and service reachability to
  the existing detailed sections.
- Reduced the handbook troubleshooting section to a navigation/checklist role;
  detailed commands now have one canonical owner.
- Preserved narrow recovery actions and explicitly prohibited broad Incus
  cleanup, secret/token sharing, and static-to-live success inference.

## Verification

```text
git diff --check
```

Result: `PASS`. No source behavior changed and no live recovery action ran.

