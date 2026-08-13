# Remediation Plan

This plan translates the ten remediation workflows in parent roadmap #120
into stable goals, outputs, finding links and completion criteria. It is a
coordination index, not proof that any workflow is complete.

Statuses use `In progress`, `Planned`, `Blocked`, `Evidence pending` and
`Closed prerequisite`. A workflow may use `Closed` only when its own evidence
and independent review support that state. Unknown future child issues link to
#120 rather than inventing an issue number.

## #120 workflow plan

| No. | Workflow | Goal | Expected output | Related major/minor findings | Completion criteria | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Audit evidence structure ([#121](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/121)) | Establish a canonical evidence backbone and status contract. | Five audit files, stable IDs, redaction rules and issue evidence. | MAJ-01 through MAJ-05; MIN-01, MIN-04, MIN-08 | Required files exist, links/statuses are reviewed, quality gates pass and independent completion audit passes. | In progress |
| 2 | QMS-light documentation ([#122](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/122)) | Define quality objectives, CAPA, change control, review and audit-cycle governance. | QMS-light process, objectives, CAPA/change/review records and evidence links. | MAJ-05; MIN-04, MIN-08 | Scope, owner, records, review cadence and evidence contract are approved and verified. | Planned |
| 3 | ISMS-light documentation ([#123](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/123)) | Define security risks, controls, secrets, admin surfaces and incident response. | Risk register, control applicability/SoA view, secret/admin rules and incident process. | MAJ-01, MAJ-04; MIN-02, MIN-07 | Applicability, owners, treatment and redacted evidence are independently reviewed. | Planned |
| 4 | Traceability matrix ([#124](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/124)) | Link requirements to architecture, implementation, tests, gates and evidence. | Requirement-to-architecture-to-test-to-evidence matrix and review record. | MAJ-03; MIN-04, MIN-08 | Every in-scope requirement has implementation and verification evidence or an explicit non-pass state. | Planned |
| 5 | Live evidence contract ([#125](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/125)) | Define how live green-path runs are consented, redacted and accepted. | Host/scenario matrix, command/result contract, redaction and retention rules. | MAJ-02; MIN-03, MIN-04 | Fresh, reconcile and update scenarios are defined; consent and evidence storage are explicit. | Planned |
| 6 | OWASP ASVS mapping ([#126](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/126)) | Map applicable security controls to APIs and administrative surfaces. | ASVS control matrix, threat/risk links, transport/authz requirements and evidence. | MAJ-04; MIN-07 | Applicable controls have owners, implementation references, tests and evidence states. | Planned |
| 7 | Supply-chain security gate proposal ([#127](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/127)) | Preserve and review SBOM, SCA, dependency and image-scan governance. | Existing policy artifacts and security-gate evidence with a current review. | MIN-02 | The closed prerequisite remains consistent with repository artifacts; any drift is reopened through the governing issue. | Closed prerequisite |
| 8 | Branch protection and CI governance ([#128](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/128)) | Make changes flow through branch, PR, quality gate, review and merge controls. | Branch/CI policy, required checks, review ownership and exception process. | MAJ-05; MIN-04, MIN-06, MIN-08 | Policy is documented, configured where authorized and evidenced without claiming unverified GitHub settings. | Planned |
| 9 | Documentation navigation restructuring ([#129](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/129)) | Provide audience-appropriate, stable navigation to maintained documentation. | Root pointers, audience map, canonical paths and stale-path treatment. | MIN-01; MIN-08 | Links resolve or are explicitly planned/missing; no large duplicate content is introduced. | Planned |
| 10 | Release and baseline process ([#120](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/120)) | Define release identity, baseline, rollback, change approval and final re-audit. | Release/baseline record, acceptance summary and final #120 closure/re-audit. | MAJ-02, MAJ-03, MAJ-05; MIN-03, MIN-04, MIN-05, MIN-06 | Child work is complete, Green-Path evidence is accepted, findings are re-evaluated and no untreated major finding remains. | Planned |

## Additional ordered dependency

The current public-beta execution index adds the secure Traefik GUI feature as
an explicit controlled step between the security model and traceability work:

`#126 ASVS/admin-surface model -> #150 secure Traefik GUI -> #124 traceability`

Issue [#150](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/150)
is therefore not silently counted as a replacement for one of the ten #120
governance workflows. Its implementation remains subject to the ISMS, ASVS,
branch/CI and secret-handling prerequisites.

## Completion semantics

- A plan row is not complete because its expected output is named.
- A planned child issue is not evidence that its controls exist.
- #127 is recorded as a closed prerequisite because the workflow index states
  that its supply-chain artifacts are already present; a later audit may reopen
  it if those artifacts drift.
- The Public-Beta Green-Path is a blocked release gate until a concrete
  execution identity, host matrix, explicit live consent and redacted evidence
  exist.
- #120 is the final closure/re-audit authority and must not be closed from this
  plan alone.
