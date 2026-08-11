# Slice Distribution — I148-S03

Primary role: Senior Python Automation Developer  
Review roles: Senior Tester, Senior System Architect

Distribution mode: role-based fallback review; no visible Codex subagent
runtime was available.

## Implementation

`git check-ignore -q -- .tiny-swarm-world/` now provides the single Git safety
probe used by `run()`. Git's documented return classes are mapped into an
invocation-local result:

- `0`: inside a worktree and ignored;
- `1`: inside a worktree and not ignored, preserving the warning;
- `128`: outside a worktree, preserving the previous no-warning behavior;
- any other result: optional probe state `unknown_<code>`, with no unsafe
  positive decision.

This removes the separate `git rev-parse --is-inside-work-tree` call while
keeping the existing warning boundary.

## Verification

```text
PYTHONPATH=src python3 -m unittest tests.test_installer
Ran 38 tests in 0.271s
OK
```

The new tests verify one subprocess call and the ignored, not-ignored and
outside-worktree classifications.

Decision: `PASS_LOCAL`; S04 may begin.
