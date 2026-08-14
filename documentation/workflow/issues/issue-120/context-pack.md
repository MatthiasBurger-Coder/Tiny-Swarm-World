# Context Pack — Issue #120

- Workflow id: `issue-120-roadmap-reassessment-20260812`
- Issue: `#120`; final parent roadmap
- Workflow path: `documentation/workflow/issues/issue-120/workflow.md`
- Authoring branch: `docs/workflow-public-beta-roadmap-20260812`
- Planned execution branch: `docs/issue-120-roadmap-reassessment-20260812`
- Process strand: final roadmap audit, Public-Beta acceptance and closure
- Execution profile: `FULL_PATH` with an approved live gate (not active by default)
- Affected areas: audit registers, child evidence, live evidence, arc42/risk/release baseline
- Forbidden areas: closure without evidence, inferred live success, unconsented
  infrastructure, silent finding downgrade and unreviewed certification claims
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior Tester
- Conditional roles: Issue Completion Auditor, Audit Evidence Manager, Live Evidence Validation, Acceptance Checks, QMS/ISMS, Senior DevOps
- Quality commands: `git diff --check`; `python3 tools/quality_gate.py quality` where required; live commands only after explicit consent
- Evidence path: `.tiny-swarm/evidence/issue-120/`
- Execution blocker: Public-Beta Green-Path issue/contract and explicit consent are not yet defined
- Governing-file hashes: see `context-pack.json`
