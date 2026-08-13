# Context Pack — Issue #123

- Workflow id: `issue-123-isms-light-20260812`
- Issue: `#123`; predecessors: `#121` and completed `#122`
- Workflow path: `documentation/workflow/issues/issue-123/workflow.md`
- Authoring branch: `docs/workflow-public-beta-roadmap-20260812`
- Planned execution branch: `docs/issue-123-isms-light-20260812`
- Process strand: ISMS-light security governance
- Execution profile: `SECURITY_GOVERNANCE`
- Affected areas: `documentation/security/` ISMS files, risk/control/evidence links
- Forbidden areas: real secrets, active attacks/scans, live commands,
  certification claims and weakened redaction/consent guards
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior Tester
- Conditional roles: ISMS-light Security Governance Expert, Security And Threat Modeling, OWASP ASVS Expert, Senior Documentation Engineer
- Quality commands: `git diff --check`; `python3 tools/quality_gate.py quality`
- Evidence path: `.tiny-swarm/evidence/issue-123/`
- Governing-file hashes: see `context-pack.json`
