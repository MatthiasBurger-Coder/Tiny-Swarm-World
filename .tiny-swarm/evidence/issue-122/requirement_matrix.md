# Issue #122 Requirement Matrix

Workflow: `issue-122-qms-light-20260812`
Issue: [#122](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/122)
Predecessor: [#121](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/121)
Parent roadmap: [#120](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/120)

Matrix owner: Senior Requirement Engineer
Reviewers: QMS-light Governance Expert, Senior System Architect,
Senior Tester, Senior Documentation Engineer, Audit Evidence Manager

## Status and interpretation

`VERIFIED_LOCAL` means a repository-local document or check was verified.
`PLANNED` means the requirement is assigned to a later slice in this
workflow. `OPEN`, `BLOCKED`, `REFUSED`, `RESOURCE-GATED`,
`FAILED_TO_APPLY` and `FAILED_TO_VERIFY` are non-pass states. No QMS
document claims ISO certification or overrides `QUALITY.md`.

The predecessor #121 completion audit is `PASS` at the integrated branch
baseline. S122-01 establishes this matrix and control model; S122-02 creates
the five QMS documents and the navigation link. Issue #122 remains incomplete
until all planned rows are verified and the six-file evidence package has an
independent completion-auditor `PASS`.

## Requirement-to-evidence matrix

| ID | Requirement | Type | Planned implementation/evidence | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-122-001 | Create a lightweight QMS structure under `documentation/qms/`. | Functional | Five QMS documents in S122-02 | Required-file and path check | PLANNED |
| REQ-122-002 | Create `qms-light.md` as the QMS scope and operating model. | Required file | `documentation/qms/qms-light.md` | File/content review | PLANNED |
| REQ-122-003 | Create `quality-objectives.md`. | Required file | `documentation/qms/quality-objectives.md` | File/content review | PLANNED |
| REQ-122-004 | Create `capa-process.md`. | Required file | `documentation/qms/capa-process.md` | File/content review | PLANNED |
| REQ-122-005 | Create `change-control.md`. | Required file | `documentation/qms/change-control.md` | File/content review | PLANNED |
| REQ-122-006 | Create `internal-audit-process.md`. | Required file | `documentation/qms/internal-audit-process.md` | File/content review | PLANNED |
| REQ-122-007 | Define measurable quality objectives with metric, target, evidence source, cadence and owner. | Quality governance | `quality-objectives.md` objective table | Field completeness and link review | PLANNED |
| REQ-122-028 | Track architecture boundary compliance as a quality objective. | Objective | `quality-objectives.md` | Objective field review | PLANNED |
| REQ-122-029 | Track quality-gate pass rate as a quality objective. | Objective | `quality-objectives.md` | Objective field review | PLANNED |
| REQ-122-030 | Track test-coverage visibility even without a numeric coverage gate. | Objective | `quality-objectives.md` | Objective field/restriction review | PLANNED |
| REQ-122-031 | Track audit-finding closure rate as a quality objective. | Objective | `quality-objectives.md` | Objective field review | PLANNED |
| REQ-122-032 | Track documentation freshness as a quality objective. | Objective | `quality-objectives.md` | Objective field review | PLANNED |
| REQ-122-033 | Track secret-leakage prevention as a quality objective. | Objective/security | `quality-objectives.md` | Objective field and redaction review | PLANNED |
| REQ-122-034 | Track live-evidence completeness as a quality objective without inferring live success. | Objective/evidence | `quality-objectives.md` | Objective state review | PLANNED |
| REQ-122-035 | Track release-baseline reproducibility as a quality objective. | Objective/release | `quality-objectives.md` | Objective field review | PLANNED |
| REQ-122-008 | Use repository evidence and local quality-gate results without treating skipped or missing checks as passes. | Evidence semantics | `qms-light.md`, `quality-objectives.md`, #121 matrix | Evidence-state review | PLANNED |
| REQ-122-009 | Define CAPA triggers for failed gates, audit findings, incidents and recurring defects. | CAPA | `capa-process.md` trigger table | Trigger/content review | PLANNED |
| REQ-122-036 | Include audit finding, quality-gate failure, security finding, failed live run, regression and documentation drift as CAPA triggers. | CAPA | `capa-process.md` | Trigger-by-trigger review | PLANNED |
| REQ-122-037 | Define CAPA severity classes and escalation/ownership rules. | CAPA | `capa-process.md` | Severity and owner review | PLANNED |
| REQ-122-038 | Require root-cause analysis appropriate to the CAPA severity. | CAPA | `capa-process.md` | Lifecycle review | PLANNED |
| REQ-122-039 | Define corrective action and preventive action records. | CAPA | `capa-process.md` | Lifecycle/record review | PLANNED |
| REQ-122-040 | Require objective effectiveness verification before CAPA closure. | CAPA/evidence | `capa-process.md` | Closure gate review | PLANNED |
| REQ-122-041 | Link CAPA records to the #121 findings register when applicable. | CAPA/traceability | `capa-process.md`, `documentation/audit/findings-register.md` | Link review | PLANNED |
| REQ-122-042 | Keep skipped, missing, blocked or failed evidence from closing a CAPA. | CAPA/fail-closed | `capa-process.md` | Negative-state review | PLANNED |
| REQ-122-010 | Define CAPA ownership, containment, root-cause analysis, corrective action and preventive action. | CAPA | `capa-process.md` lifecycle | Lifecycle review | PLANNED |
| REQ-122-011 | Require effectiveness evidence before CAPA closure. | CAPA/evidence | `capa-process.md` closure gate | Closure-rule review | PLANNED |
| REQ-122-012 | Preserve blocked, failed and evidence-pending states until verified. | Resilience/evidence | QMS status contract and CAPA rules | Vocabulary and fail-closed review | PLANNED |
| REQ-122-013 | Define change classification, impact analysis and required approver. | Change control | `change-control.md` | Control-field review | PLANNED |
| REQ-122-043 | Require a branch per workflow and small implementation slices. | Change control | `change-control.md` | Control-flow review | PLANNED |
| REQ-122-044 | Require a PR for governed changes. | Change control | `change-control.md` | Control-flow review | PLANNED |
| REQ-122-045 | Require the applicable quality gate before merge. | Change control | `change-control.md` | Gate-control review | PLANNED |
| REQ-122-046 | Require documentation updates when behavior changes. | Change control | `change-control.md` | Rule/content review | PLANNED |
| REQ-122-047 | Require security-risk review for security-sensitive changes. | Change control/security | `change-control.md` | Rule/content review | PLANNED |
| REQ-122-048 | Prohibit live commands unless explicitly requested and approved. | Change control/safety | `change-control.md` | No-live rule review | PLANNED |
| REQ-122-049 | Require summary, changed files, quality result, no-live confirmation and remaining gaps in PR evidence. | Change control/evidence | `change-control.md` | PR-evidence field review | PLANNED |
| REQ-122-014 | Connect changes to branch, PR, quality gate, review, merge and evidence. | Change control | `change-control.md` control flow | Flow and link review | PLANNED |
| REQ-122-015 | Keep `QUALITY.md` authoritative and do not weaken or bypass quality gates. | Governance | QMS authority statement and links | Authority comparison | PLANNED |
| REQ-122-016 | Define internal-audit scope, cadence, owner, inputs, findings and follow-up. | Audit governance | `internal-audit-process.md` | Field/cadence review | PLANNED |
| REQ-122-050 | Define audit planning and scope selection. | Audit governance | `internal-audit-process.md` | Procedure review | PLANNED |
| REQ-122-051 | Define audit criteria, evidence collection and finding classification. | Audit governance | `internal-audit-process.md` | Procedure review | PLANNED |
| REQ-122-052 | Define CAPA handoff from internal audits. | Audit/CAPA | `internal-audit-process.md` | Cross-link review | PLANNED |
| REQ-122-053 | Define a recurring audit cadence and an event-driven audit trigger. | Audit governance | `internal-audit-process.md` | Cadence/trigger review | PLANNED |
| REQ-122-054 | Define follow-up audit timing, owner and evidence record. | Audit governance | `internal-audit-process.md` | Follow-up review | PLANNED |
| REQ-122-055 | Reference ISO 19011 and ISO 20246 as guidance without certification claims. | Audit guidance | `internal-audit-process.md` | Standards/claim review | PLANNED |
| REQ-122-017 | Link internal audits to the #121 evidence matrix, findings register and CAPA process. | Traceability | QMS cross-links | Link resolution review | PLANNED |
| REQ-122-018 | Add concise verified navigation from `documentation/README.adoc`. | Documentation | README QMS pointer | Diff/link review | PLANNED |
| REQ-122-019 | Keep the implementation documentation/governance-only; do not change runtime, CI or deployment behavior. | Scope/safety | Changed-file evidence | Scope audit | PLANNED |
| REQ-122-020 | Make no ISO 9001 certification, compliance or audit-closure claim. | Compliance | QMS scope/limitation wording | Red-flag wording review | PLANNED |
| REQ-122-021 | Do not run live infrastructure or service bootstrap commands. | Safety | No-live execution record | Command/evidence review | PLANNED |
| REQ-122-022 | Preserve Linux/WSL-only and Docker Swarm-first repository governance. | Product constraints | QMS scope and evidence wording | AGENTS comparison | PLANNED |
| REQ-122-023 | Execute #122 only after #121 evidence is complete and use the serial S122-01 -> S122-02 order. | Dependency/process | #121 completion audit and workflow metadata | Dependency/order check | VERIFIED_LOCAL |
| REQ-122-024 | Create distribution evidence before each slice and consolidation evidence after each slice. | Execution evidence | `.codex/evidence/issue-122/` | Evidence-file review | VERIFIED_LOCAL |
| REQ-122-025 | Run `git diff --check` and `python3 tools/quality_gate.py quality` as required by the issue; record exact result and never claim a skipped gate as pass. | Quality | Workflow and test results | Command-result review | PLANNED |
| REQ-122-026 | Provide six issue evidence files: matrix, implementation summary, changed files, test results, remaining risks and acceptance checklist. | Completion evidence | `.tiny-swarm/evidence/issue-122/` | Required-file check | PLANNED |
| REQ-122-027 | Obtain Requirement Lead, System Architect, Test/Evidence, QMS/Documentation reviews and an independent completion audit before DONE. | Review governance | Distribution/consolidation and completion audit | Role-result review | PLANNED |
| REQ-122-056 | Define the Linux/WSL-only Python automation, Docker Swarm-first and Incus/LXC provider identity in the QMS scope. | Product governance | `qms-light.md` | Scope/content review | PLANNED |
| REQ-122-057 | Define quality responsibilities for the Lead Architect, Senior Tester, Senior Documentation Engineer, Senior DevOps Engineer, Security Owner and Workflow Executor. | Responsibilities | `qms-light.md` | Role/content review | PLANNED |
| REQ-122-058 | Define repository quality evidence and the rule that no pass is claimed without evidence. | Evidence governance | `qms-light.md` | Evidence-rule review | PLANNED |
| REQ-122-059 | Trace QMS-light to the System Unification EPIC as compatible process governance while keeping #120/#122 issue authority explicit. | Architecture/traceability | `qms-light.md`, requirement matrix | EPIC/source review | PLANNED |
| REQ-122-060 | Record validation results, no-live confirmation and remaining QMS gaps in issue/PR evidence. | Completion evidence | Issue evidence package | Evidence review | PLANNED |

## Slice contract

| Slice | Responsibility | Output | Status |
| --- | --- | --- | --- |
| S122-01 | Requirement Engineer with QMS, architecture and test review | This matrix and control model | VERIFIED_LOCAL |
| S122-02 | QMS-light Governance Expert with Documentation and Audit Evidence review | Five QMS documents, navigation and final evidence | PLANNED |

## Open-source and boundary decisions

- `QUALITY.md` remains the authority for executable quality commands and
  verification policy; QMS documents may explain but not replace it.
- #121 provides the canonical audit evidence vocabulary and findings links.
- This is documentation-only. No ADR or runtime architecture change is
  expected.
- The full Python quality gate is required by the original issue and has been
  executed for S122-01. Its result is local evidence only; it must never be
  represented as live, browser or external-service success.
