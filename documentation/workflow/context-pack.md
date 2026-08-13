# Context Pack — Issue #128

- Workflow id: `issue-128-branch-ci-governance-20260812`
- Issue: `#128`; predecessors: `#121`, `#122`
- Workflow path: `documentation/workflow/issues/issue-128/workflow.md`
- Authoring branch: `docs/workflow-public-beta-roadmap-20260812`
- Planned execution branch: `docs/issue-128-branch-ci-governance-20260812`
- Execution branch: `docs/issue-128-branch-ci-governance-20260812`
- Process strand: branch, PR and CI governance
- Execution profile: `GOVERNANCE`
- Affected areas: `documentation/governance/`, `.github` evidence and quality links
- Forbidden areas: direct GitHub settings mutation, unscoped CI changes, live
  commands and unverifiable required-check claims
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior Tester
- Conditional roles: Branch CI Governance Expert, QMS-light Governance Expert, Senior Documentation Engineer
- Quality commands: `git diff --check`; `python3 tools/quality_gate.py quality`
- Evidence path: `.tiny-swarm/evidence/issue-128/`
- Governing-file hashes: see `context-pack.json`
