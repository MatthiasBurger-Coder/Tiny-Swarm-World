# Findings Register

This register is the stable finding index for the current audit baseline. It
does not close, downgrade or accept a finding merely because a document was
created. Each row needs an owner, a remediation route, a disposition and an
evidence link before closure can be considered.

## Severity and disposition contract

Severity values are `Major`, `Minor`, `Observation` and `Positive finding`.
Disposition values are `Open`, `In progress`, `Evidence pending`, `Risk
accepted`, `Closed` and `Not applicable`.

`Closed` requires evidence that directly addresses the finding, a reviewable
link or protected-system reference, and independent review. `Risk accepted`
requires a named decision owner, supporting evidence and an expiry/review
condition. `Not applicable`
requires a documented applicability decision. Planned, missing, blocked,
refused, resource-gated, failed-to-apply and failed-to-verify evidence never
supports a `Closed` disposition by itself.

## Major findings

| Finding ID | Severity | Affected standard/framework | Finding text | Risk | Required remediation | Owner role | Status | Evidence link | Related issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MAJ-01` | Major | ISO/IEC 27001 | Missing full ISMS, Statement of Applicability and risk register. | Security risks and control applicability cannot be governed consistently. | Define the ISMS-light scope, risk register, control applicability and SoA evidence. | ISMS Governance Owner | Open | Evidence pending in [`evidence-matrix.md`](evidence-matrix.md) | #123; #120 if an additional child is required |
| `MAJ-02` | Major | Project acceptance; ISO/IEC 12207 lifecycle | Missing full live green path. | A successful local install cannot establish public-beta readiness. | Define and execute the consented clean-host Linux/WSL2 fresh, reconcile and update scenarios with redacted evidence. | Live Evidence Owner | Open | Planned: [`evidence-matrix.md`](evidence-matrix.md) | #125; Public-Beta Green-Path gate; #120 |
| `MAJ-03` | Major | ISO/IEC 12207; ISO 20246; ISO/IEC 25010 | Missing requirement-to-test-to-evidence traceability. | Reviewers cannot determine whether acceptance claims are supported. | Create and review the traceability matrix linking requirements, architecture, implementation, tests, gates and evidence. | Traceability Owner | Open | Evidence pending in [`evidence-matrix.md`](evidence-matrix.md) | #124 |
| `MAJ-04` | Major | ISO/IEC 27001; OWASP ASVS | Docker socket exposure risk. | A compromised administrative surface may gain host-level control. | Model the threat, constrain access, document compensating controls and verify the resulting admin surface. | Security Architecture Owner | Open | Evidence pending in [`evidence-matrix.md`](evidence-matrix.md) | #123, #126, #150 |
| `MAJ-05` | Major | ISO 9001; ISO 20246; ISO/IEC 33001 | Missing QMS-light, CAPA, audit cycle and quality objectives. | Quality decisions may be inconsistent, non-repeatable or unauditable. | Define quality objectives, change/review control, CAPA handling and a repeatable audit cycle. | QMS Governance Owner | Open | Evidence pending in [`evidence-matrix.md`](evidence-matrix.md) | #122; #120 |

## Minor findings

| Finding ID | Severity | Affected standard/framework | Finding text | Risk | Required remediation | Owner role | Status | Evidence link | Related issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MIN-01` | Minor | ISO/IEC/IEEE 26514 | Documentation audience separation is incomplete. | Operators, developers and reviewers may use the wrong guidance. | Define audience-specific navigation and keep operational, governance and architecture views distinct. | Documentation Engineer | Open | Evidence pending in [`evidence-matrix.md`](evidence-matrix.md) | #129; #120 |
| `MIN-02` | Minor | Supply-chain security; ISO/IEC 27001 | Missing SBOM, SCA and dependency-security evidence. | Vulnerable or unreviewed dependencies may enter a release. | Retain the existing #127 prerequisite evidence and verify its current scope in the release baseline. | Supply-chain Security Owner | Open | Evidence pending in [`evidence-matrix.md`](evidence-matrix.md) | #127 closed prerequisite; #120 |
| `MIN-03` | Minor | ISO/IEC 25010 | Missing performance and resource metrics. | Capacity, repeatability and host suitability remain unverified. | Define the required metrics and capture them in the appropriate acceptance evidence. | Performance/Runtime Owner | Open | Planned evidence in [`evidence-matrix.md`](evidence-matrix.md) | #120 |
| `MIN-04` | Minor | ISO 9001; ISO/IEC 12207 | Operational-readiness checklist is not evidence-based. | Readiness may be asserted without observable proof. | Convert checklist items to requirement, evidence and reviewer mappings. | Release Readiness Owner | Open | Evidence pending in [`evidence-matrix.md`](evidence-matrix.md) | #124, #125; #120 |
| `MIN-05` | Minor | Release governance | Missing repository license. | Redistribution and usage expectations are unclear. | Decide and add the repository license through a dedicated reviewed change. | Release Governance Owner | Open | Missing; see [`evidence-matrix.md`](evidence-matrix.md) | #120 |
| `MIN-06` | Minor | ISO/IEC 12207; release governance | Release and baseline process is incomplete. | Reproducibility and rollback evidence may be inconsistent. | Define baseline identity, release evidence, rollback and change approval rules. | Release Baseline Owner | Open | Planned in [`remediation-plan.md`](remediation-plan.md) | #120 |
| `MIN-07` | Minor | OWASP ASVS | Missing ASVS control matrix. | Admin-surface security requirements cannot be traced to verification. | Map applicable ASVS controls to the local infrastructure/admin surfaces and evidence. | Security Architecture Owner | Open | Planned in [`evidence-matrix.md`](evidence-matrix.md) | #126; #150 |
| `MIN-08` | Minor | ISO 20246; ISO/IEC/IEEE 26514 | Review records are not formalized. | Decisions and dissent may not be reproducible. | Use named reviewers, date, scope, decision, evidence and remaining-risk records. | Review/Evidence Owner | Open | Starting structure: [`evidence-matrix.md`](evidence-matrix.md) | #121; #124 |

## Additional dispositions

The register schema supports `Observation` and `Positive finding` for later
review results. They must use stable IDs, an evidence link and the same
independent-review rule. No observation or positive finding is invented here
without a source record.

## Update protocol

Update a row only when the underlying evidence, owner decision or review state
changes. Keep the old evidence reference available through the normal repository
history. Do not replace an open finding with a new row to make the register
appear green.
