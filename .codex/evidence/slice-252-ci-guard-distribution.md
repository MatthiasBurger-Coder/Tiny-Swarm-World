# Issue #252 CI/live-runner guard slice distribution

- workflow id: issue-252-classic-public-beta-rc1-remediation-20260823
- slice id: S252-CI-GUARD-20260829
- slice title: Restrict CI triggers and prevent skipped Classic acceptance
- affected areas: runtime, quality, tests, documentation review
- chosen execution mode: sequential
- selected streams: runtime, quality, tests
- real subagents used: no
- fallback role-based review: yes; Senior DevOps, Senior Tester, Live Evidence Validation
- Git worktrees used: no; this is the verified issue execution branch and no parallel stream is safe
- expected touched files/directories: `.github/workflows/`, `tools/live/`, `tests/test_ci_workflow_contract.py`, `documentation/governance/ci-quality-gates.md`, `.codex/evidence/`
- conflict risks: shared CI workflow contract and one shared live runner; live infrastructure state is not touched
- quality gates: `git diff --check`, focused CI contract tests, `python3 tools/quality_gate.py quality`
- consolidation plan: review workflow trigger/approval semantics, runner live-test activation and contract tests together; reject any change that invents update semantics or weakens evidence rules
- parallelization decision: rejected because the workflow files, runner behavior and contract tests share one observable safety contract
- blocking context: credentialed live execution remains paused after local secret exposure; no live infrastructure command is part of this slice
