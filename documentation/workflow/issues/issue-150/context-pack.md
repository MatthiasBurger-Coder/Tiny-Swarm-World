# Context Pack — Issue #150

- Workflow id: `issue-150-secure-traefik-gui-20260812`
- Issue: `#150`; predecessors: `#123`, `#126`, `#128`
- Workflow path: `documentation/workflow/issues/issue-150/workflow.md`
- Authoring branch: `docs/workflow-public-beta-roadmap-20260812`
- Planned execution branch: `feature/issue-150-secure-traefik-gui-20260812`
- Process strand: secure Traefik admin-surface feature
- Execution profile: `SECURITY_ARCHITECTURE` then `FULL_PATH`
- Affected areas: Traefik compose/config, ingress desired state, renderers,
  routing tests, arc42/ADR and live-evidence handoff
- Forbidden areas: `api.insecure`, raw credentials, open ports, unapproved auth,
  general React frontend and live commands by default
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior Tester
- Conditional roles: ISMS/ASVS, Security Threat Modeling, Senior DevOps, Live Evidence Validation, Documentation Engineer
- Quality commands: targeted ingress/compose/routing tests; `python3 tools/quality_gate.py quality`; `git diff --check`
- Evidence path: `.tiny-swarm/evidence/issue-150/`
- Governing-file hashes: see `context-pack.json`
