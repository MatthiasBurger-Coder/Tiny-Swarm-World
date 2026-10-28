# S449-02F distribution decision — v1.37 candidate

- Workflow: `issue-449-lcm-w09`, v1.37, `ACTIVE_FOR_ISSUE_449`.
- Slice: `S449-02F — Capture native LXD/Incus ownership without mutation`.
- Dependency: S449-02E at `6c48b1d0ef90ec0316769257e8a821946b2200c8`.
- Execution mode: sequential. Runner, tests, workflow and evidence share one contract and one slice lock; no parallel worktree was needed.
- Final review tuple:
  - source: `2084dc090f3b0d55007a9ad017fee4621b4d077642fe402f6fd0538c883f5f0c`
  - tests: `23c8395a3c8a5b6167f36b5e76f052f9df4a307cdc7499a88c898d0cf942aa37`
  - workflow: `99eb850093361ab6801f56951398366ac2fe56238a5e525fda587e0de9cf18ec`
  - context Markdown: `15991fac52aa8de29f0f8e61cd0bf301fcdbaa0af05bbea911d4eee3329ecd9a`
  - context JSON: `9dd6fd4ae89f858aaf60ef2a1d3887ba387d652f244360962bcff184f2afcef0`
- Reviews: Requirement, Architecture, Python Automation, Tester, Security and DevOps approved the v1.37 contract and final source/test hashes. S3D approved only verification on PC WSL; native capture is excluded.
- PC WSL focused inventory suite: 53 tests passed.
- Full quality: 3,048 tests, 18 skipped; seven gates passed, `GATE_EXIT=0`. Isolated HOME: `/home/pc/projects/issue449-s02f-home-v137-20261028`. Log SHA-256: `cc3f5f1b94219e5b4774c57e5f5063b1d8315c497d9938457d9d66c5ed1ec295`.
- An initial default-HOME full-gate run had two stale-checkpoint failures in Incus preparation tests; the isolated-HOME rerun passed. The first focused run found and led to removal of one obsolete assertion; the final focused run passed.
- The v1.36 native read-only attempt returned `UNIT_SCHEMA_INVALID`, created no artifact, and made no host changes. No v1.37 native capture has run.
- Next step: commit S02F, then request a separate S3D plan bound to committed source/test/workflow/context hashes before one bounded read-only capture on native Linux `192.168.178.33`. No WSL runtime capture or host mutation is authorized by S02F.
