# Issue #252 — S252-01 Distribution Decision

- Workflow ID: `issue-252-classic-public-beta-rc1-20260814`
- Slice ID: `S252-01`
- Slice title: Requirement, service and asset baseline; Three-Amigos gate
- Execution mode: `sequential`
- Dependency state: no predecessors; S3D topological validation passed for all
  12 slices and found no unknown dependency or cycle.
- Selected review streams: Senior Requirement Engineer, Senior System
  Architect, Senior Python Automation Developer, Senior Tester, Senior
  DevOps Engineer, Senior Live Evidence Validator, Senior Documentation
  Engineer and Senior Execution Orchestrator.
- Real subagents used: `no`; no callable subagent tool is exposed in this
  environment.
- Fallback role-based review: `yes`; the applicable role instructions were
  read and the review is recorded in
  `.tiny-swarm-world/evidence/classic-public-beta-rc1/three-amigos.md`.
- Git worktrees: none; this slice is serial and evidence/configuration scoped.
- Expected touched paths: `.tiny-swarm/evidence/issue-252/`,
  `.tiny-swarm-world/evidence/classic-public-beta-rc1/`, and the workflow-local
  requirement matrix.
- File locks: issue-252 evidence roots and
  `documentation/workflow/requirement-matrix.md`.
- Contract locks: `requirement-to-evidence`, `classic-service-inventory`,
  `scenario-record-schema`, `explicit-live-consent`.
- Architecture locks: `linux-wsl2-only`, `incus-lxc-provider`,
  `docker-swarm-first`, `fail-closed-evidence`.
- Conflict risks: the generic paths `.codex/evidence/slice-01-*` already
  contain tracked evidence for Issue #188 and must not be overwritten. This
  issue therefore uses the namespaced `slice-S252-01-*` evidence names.
- Live safety: no Incus, Docker, Swarm, network, service, browser, credential
  or Administrator PowerShell operation is authorized or executed.
- Quality gates: S3/S3D metadata/dependency validation, static source/config
  review, verification-policy consistency check and `git diff --check`; the
  full WSL quality gate remains the required gate when implementation slices
  modify Python or test code.
- Parallelization decision: rejected. S252-01 is the ordered release-gate
  baseline and owns shared inventory and requirement locks used by every later
  slice.
- Handoff condition: S252-02 may start only after the materialized matrix,
  service inventory, asset decisions and Three-Amigos gate are present and
  redacted.
