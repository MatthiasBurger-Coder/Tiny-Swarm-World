# S252-R01 Distribution Decision

- Workflow id: `issue-252-classic-public-beta-rc1-remediation-20260823`
- Slice: `S252-R01 — Canonical TLS contract and CA lifecycle`
- Execution profile: `FULL_PATH`
- Affected areas: domain contract, application port/service, infrastructure
  managed-PKI adapter, LXC Swarm runtime, installer, tests and security.
- Execution mode: sequential.
- Selected streams: Python automation, architecture, tests and security.
- Real subagents: yes; one implementation worker owns the complete R01 write
  scope after independent Requirement, Architecture, Python, Test and Workflow
  Architect reviews.
- Fallback role review: not used.
- Git worktree: isolated execution worktree
  `issue-252-remediation-execution` on the declared workflow branch.
- Candidate source: preserved read-only worktree
  `preserve/issue-252-candidate-20260823`; candidate changes are adopted only
  when they satisfy the accepted ADR and R01 acceptance criteria.
- Expected touched paths: the R01 `affected_files` and explicit create scopes
  declared in `documentation/workflow/workflow.md`.
- Conflict risks: TLS files are shared with R02 and R06; R01 holds the
  canonical TLS, external-precedence, managed-reuse and protected-local-state
  locks until consolidation.
- Parallelization rejected: domain, lifecycle, runtime and tests share one
  TLS contract and cannot be attributed safely as independent write streams.
- Targeted gates: focused installer, stack-prerequisite and LXC runtime tests;
  lint; typecheck.
- Required gate: `python3 tools/quality_gate.py quality`.
- Consolidation: root executor reviews worker diff, runs targeted gates, fixes
  only R01 findings, runs the full gate, writes R01 consolidation evidence and
  creates exactly one slice checkpoint commit.
