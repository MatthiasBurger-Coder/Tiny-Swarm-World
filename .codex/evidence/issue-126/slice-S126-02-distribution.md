# S126-02 Distribution Evidence

Workflow: `issue-126-owasp-asvs-admin-surface-20260812`
Slice: S126-02 — Mapping, RBAC model and threat model

## Distribution decision

- Affected areas: ASVS mapping, admin/RBAC boundaries, Service Access threat
  model, Traefik ingress, secrets, evidence and #150 handoff.
- Execution mode: sequential because ownership, auth/TLS and route decisions
  share security locks.
- Selected streams: ASVS, system architecture, ISMS/threat modeling,
  documentation, quality and audit evidence.
- Forbidden: certification claims, active scans, live commands, secrets and
  insecure/unauthenticated exposure proposals.

## Quality and evidence

Targeted: `git diff --check`.
Required: `python3 tools/quality_gate.py quality` in WSL/Linux. Results are
local evidence only and do not prove a deployed control.
