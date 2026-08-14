# Audit Register

This register records audit and review scopes. It is an evidence index, not a
certificate or a declaration of conformity. `Evidence pending` means the scope
has been identified but the required evidence or independent review is not yet
complete.

## Status contract

Allowed audit statuses are `Open`, `In progress`, `Evidence pending`, `Risk
accepted`, `Closed` and `Not applicable`. A `Closed` status requires a redacted
evidence link, review date and independent review record. `Blocked`, `Refused`,
`Resource-gated`, `Failed-to-apply` and `Failed-to-verify` remain non-pass
evidence states and must not be hidden by an audit status.

## Register

| Audit ID | Audit name | Standard/framework | Scope | Evidence type | Status | Last reviewed | Owner role | Related issue/PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AUD-ISO9001-QMS` | QMS-light quality governance | ISO 9001 | Quality objectives, CAPA, change control, reviews and audit cycle | Repository governance; future review evidence | Evidence pending | 2026-08-13 | QMS Governance Owner | #120, #122 |
| `AUD-ISO25010-QUALITY` | Product quality model review | ISO/IEC 25010 | Product quality characteristics and quality-gate evidence | Repository quality docs; static gate; future measurements | Evidence pending | 2026-08-13 | Quality Gate Owner | #120, #124 |
| `AUD-ISO27001-ISMS` | ISMS-light security governance | ISO/IEC 27001 | Risks, controls, secrets, admin surfaces and incident response | Repository security governance; future redacted evidence | Evidence pending | 2026-08-13 | ISMS Governance Owner | #120, #123 |
| `AUD-ASVS-SECURITY` | Application/admin-surface security review | OWASP ASVS | Authentication, authorization, transport and administrative surfaces | Control mapping; review evidence; future verification | Evidence pending | 2026-08-13 | Security Architecture Owner | #126, #150 |
| `AUD-ISO12207-LIFECYCLE` | Software lifecycle governance | ISO/IEC 12207 | Requirements, implementation, verification, release and maintenance | Workflow and repository evidence | Evidence pending | 2026-08-13 | Workflow Architect | #120, #124 |
| `AUD-ISO26514-DOCS` | Documentation quality review | ISO/IEC/IEEE 26514 | Audience, structure, navigation and operational documentation | Repository documentation and review record | Evidence pending | 2026-08-13 | Documentation Engineer | #129 |
| `AUD-ISO20246-REVIEWS` | Review and evaluation governance | ISO 20246 | Review planning, participants, decisions and evidence | Review records and acceptance checklists | Evidence pending | 2026-08-13 | Review/Evidence Owner | #121, #124 |
| `AUD-ISO33001-PROCESS` | Process assessment reference | ISO/IEC 33001 and related parts | Process capability and repeatability of governance workflows | Workflow, quality and review evidence | Evidence pending | 2026-08-13 | Process Governance Owner | #120, #128 |
| `AUD-LIVE-GREENPATH` | Public-beta live green-path gate | Project acceptance contract; related standards to be assessed | Clean-host installation, reconcile, update, service access and redacted evidence | Explicitly consented live evidence only | Evidence pending | 2026-08-13 | Live Evidence Owner | #120, #125, #129 |

## Review rules

1. The audit ID is stable and must not be reused for another scope.
2. A standard/framework entry is a reference unless applicability and evidence
   are explicitly reviewed.
3. A repository quality-gate pass is local verification only. It is not live,
   browser, installation or external-service evidence.
4. The live green-path row stays `Evidence pending` until a later workflow has
   an explicit issue identity, host matrix, consent and redacted run evidence.
5. Finding closure is controlled by
   [`findings-register.md`](findings-register.md), not by changing this table
   alone.
