# Issue #121 Requirement Matrix

Workflow: `issue-121-audit-evidence-20260812`
Issue: [#121](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/121)
Parent roadmap: [#120](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/120)
Execution branch: `docs/issue-121-audit-evidence-20260812`
Matrix owner: Senior Requirement Engineer
Reviewers: Audit Evidence Manager, Senior System Architect, Senior Tester

## Status and interpretation

This matrix is the controlled extraction of the issue body, the parent
roadmap, the active workflow and repository governance. `IMPLEMENTED` means
that the required artifact exists in the execution change and has an explicit
verification route; it does not mean that live evidence or a certification
exists. `VERIFIED_LOCAL` means that a repository-local artifact or check was
verified. `PLANNED` is reserved for a future live or follow-up artifact.
`OPEN`, `BLOCKED`, `REFUSED`, `RESOURCE-GATED`,
`failed-to-apply` and `failed-to-verify` are non-pass states.

At matrix creation time, S121-01 is complete only when every requirement has a
stable mapping. S121-02 must replace planned implementation placeholders with
the five audit documents and final issue evidence. Issue #121 is `DONE` only
after the final acceptance checklist and independent completion audit return
`PASS` on the merged integration baseline.

## Authority and scope decisions

- The issue body and #120 are the issue-level requirement sources.
- `AGENTS.md`, `QUALITY.md` and
  `documentation/process/verification-state-policy.md` govern repository
  behavior and verification-state wording.
- The [System Unification EPIC](../../documentation/arc42/01_introduction/system-unification.md)
  explicitly owns the repository-level audit-evidence backbone as a governance
  extension. This ownership does not close findings or authorize live work.
- `documentation/audit/` is a governance index and pointer layer. It is not a
  replacement for runtime, deployment, test or live-system sources of truth.
- No live command, browser check, external service check, certification
  assessment or runtime change is authorized by this issue.

## Requirement-to-evidence matrix

| ID | Requirement from issue or governing workflow | Type | Files likely affected | Implementation evidence | Test/evidence verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-121-001 | Create a canonical, versioned audit evidence structure under `documentation/audit/`. | Functional | `documentation/audit/` | `documentation/audit/README.md` and four linked registers, S121-02 | Required-file check and `git diff --check` | VERIFIED_LOCAL |
| REQ-121-002 | Connect findings to standards, owners, planned actions, evidence and later review. | Traceability | Five audit documents | Register schemas and stable IDs, S121-02 | Cross-links and column/content review | VERIFIED_LOCAL |
| REQ-121-003 | Keep repository, planned, live and missing evidence distinct. | Quality | `evidence-matrix.md`, `README.md` | Evidence status contract | Evidence-state vocabulary review | VERIFIED_LOCAL |
| REQ-121-004 | Never claim unresolved findings are closed or downgraded without evidence. | Governance | `findings-register.md`, `README.md` | Closure rule and finding statuses | Independent evidence review | VERIFIED_LOCAL |
| REQ-121-005 | Execute on a dedicated issue branch/worktree from the current workflow baseline. | Process | Workflow/context pack | `docs/issue-121-audit-evidence-20260812` and isolated worktree | Branch/status check | IMPLEMENTED |
| REQ-121-006 | Keep the change documentation/governance-only. | Scope | Documentation and `.tiny-swarm/evidence/issue-121/` | No `src/`, runtime, deployment or service files | Changed-file audit | IMPLEMENTED |
| REQ-121-007 | Do not execute LXD, Incus, LXC, Docker Swarm, Portainer, Nexus, Jenkins, Pulsar, SonarQube, Swagger, Infisical, Traefik, image build/push or stack-deployment commands. | Safety | None | No-live execution decision | Command history and evidence review | IMPLEMENTED |
| REQ-121-008 | Do not change runtime behavior. | Architecture | None outside documentation | Governance-only artifacts | Changed-file audit | IMPLEMENTED |
| REQ-121-009 | Do not introduce certification claims. | Compliance | All audit docs | Applicability and limitation wording | Red-flag wording review | IMPLEMENTED |
| REQ-121-010 | Do not commit secrets, raw environment data, private host data or unredacted local evidence. | Security/data protection | All audit docs/evidence | Redaction rules | Secret/path/IP scan and review | IMPLEMENTED |
| REQ-121-011 | Create `documentation/audit/README.md`. | Required file | `documentation/audit/README.md` | S121-02 | File and heading check | VERIFIED_LOCAL |
| REQ-121-012 | Create `documentation/audit/audit-register.md`. | Required file | `documentation/audit/audit-register.md` | S121-02 | File, schema and entry check | VERIFIED_LOCAL |
| REQ-121-013 | Create `documentation/audit/findings-register.md`. | Required file | `documentation/audit/findings-register.md` | S121-02 | File, schema and finding check | VERIFIED_LOCAL |
| REQ-121-014 | Create `documentation/audit/evidence-matrix.md`. | Required file | `documentation/audit/evidence-matrix.md` | S121-02 | File, schema and category check | VERIFIED_LOCAL |
| REQ-121-015 | Create `documentation/audit/remediation-plan.md`. | Required file | `documentation/audit/remediation-plan.md` | S121-02 | File and #120 workflow check | VERIFIED_LOCAL |
| REQ-121-016 | README states the purpose of the audit documentation area. | Documentation | `audit/README.md` | Purpose section | Content review | VERIFIED_LOCAL |
| REQ-121-017 | README states the relationship to #120 and #121. | Documentation | `audit/README.md` | Issue links/relationship section | Link and content review | VERIFIED_LOCAL |
| REQ-121-018 | README distinguishes repository evidence from live evidence. | Evidence semantics | `audit/README.md` | Evidence boundary section | Policy wording review | VERIFIED_LOCAL |
| REQ-121-019 | README covers ISO 19011 as an audit-guidance reference. | Standards | `audit/README.md` | Standards section | Standards-entry review; no certification claim | VERIFIED_LOCAL |
| REQ-121-020 | README covers ISO 20246 as a review/evaluation reference. | Standards | `audit/README.md` | Standards section | Standards-entry review | VERIFIED_LOCAL |
| REQ-121-021 | README covers ISO/IEC 33001 ff. and related process-assessment references. | Standards | `audit/README.md` | Standards section | Standards-entry review | VERIFIED_LOCAL |
| REQ-121-022 | README covers ISO 9001 as a quality-management reference. | Standards | `audit/README.md` | Standards section | Standards-entry review | VERIFIED_LOCAL |
| REQ-121-023 | README covers ISO/IEC 25010 as a quality-model reference. | Standards | `audit/README.md` | Standards section | Standards-entry review | VERIFIED_LOCAL |
| REQ-121-024 | README covers ISO/IEC 27001 as an information-security reference. | Standards | `audit/README.md` | Standards section | Standards-entry review | VERIFIED_LOCAL |
| REQ-121-025 | README covers OWASP ASVS as an application-security reference. | Standards | `audit/README.md` | Standards section | Standards-entry review | VERIFIED_LOCAL |
| REQ-121-026 | README mentions DIN 66270 with an applicability caveat. | Standards | `audit/README.md` | Applicability note | Caveat review; no applicability assumed | VERIFIED_LOCAL |
| REQ-121-027 | README covers ISO/IEC 12207 as a lifecycle reference. | Standards | `audit/README.md` | Standards section | Standards-entry review | VERIFIED_LOCAL |
| REQ-121-028 | README covers ISO/IEC/IEEE 26514 as a documentation reference. | Standards | `audit/README.md` | Standards section | Standards-entry review | VERIFIED_LOCAL |
| REQ-121-029 | `blocked` is not a pass state. | Evidence contract | `audit/README.md`, `evidence-matrix.md` | Status vocabulary | State review | VERIFIED_LOCAL |
| REQ-121-030 | `refused` is not a pass state. | Evidence contract | `audit/README.md`, `evidence-matrix.md` | Status vocabulary | State review | VERIFIED_LOCAL |
| REQ-121-031 | `resource-gated` is not a pass state. | Evidence contract | `audit/README.md`, `evidence-matrix.md` | Status vocabulary | State review | VERIFIED_LOCAL |
| REQ-121-032 | `failed-to-apply` is not a pass state. | Evidence contract | `audit/README.md`, `evidence-matrix.md` | Status vocabulary | State review | VERIFIED_LOCAL |
| REQ-121-033 | `failed-to-verify` is not a pass state. | Evidence contract | `audit/README.md`, `evidence-matrix.md` | Status vocabulary | State review | VERIFIED_LOCAL |
| REQ-121-034 | Live evidence excludes secrets and tokens. | Security | `audit/README.md`, `evidence-matrix.md` | Redaction section | Secret scan/review | VERIFIED_LOCAL |
| REQ-121-035 | Live evidence excludes raw environment payloads. | Security | `audit/README.md`, `evidence-matrix.md` | Redaction section | Content review | VERIFIED_LOCAL |
| REQ-121-036 | Live evidence excludes Swarm join tokens. | Security | `audit/README.md`, `evidence-matrix.md` | Redaction section | Content review | VERIFIED_LOCAL |
| REQ-121-037 | Live evidence excludes raw command dumps and raw stdout/stderr. | Security | `audit/README.md`, `evidence-matrix.md` | Redaction section | Content review | VERIFIED_LOCAL |
| REQ-121-038 | Live evidence excludes private host paths and private IP data unless explicitly redacted. | Security | `audit/README.md`, `evidence-matrix.md` | Redaction section | Path/IP review | VERIFIED_LOCAL |
| REQ-121-039 | Audit-register columns are Audit ID, Audit name, Standard/framework, Scope, Evidence type, Status, Last reviewed, Owner role and Related issue/PR. | Schema | `audit-register.md` | Table schema | Column check | VERIFIED_LOCAL |
| REQ-121-040 | Prepopulate `AUD-ISO9001-QMS`. | Register entry | `audit-register.md` | Stable row | Entry check | VERIFIED_LOCAL |
| REQ-121-041 | Prepopulate `AUD-ISO25010-QUALITY`. | Register entry | `audit-register.md` | Stable row | Entry check | VERIFIED_LOCAL |
| REQ-121-042 | Prepopulate `AUD-ISO27001-ISMS`. | Register entry | `audit-register.md` | Stable row | Entry check | VERIFIED_LOCAL |
| REQ-121-043 | Prepopulate `AUD-ASVS-SECURITY`. | Register entry | `audit-register.md` | Stable row | Entry check | VERIFIED_LOCAL |
| REQ-121-044 | Prepopulate `AUD-ISO12207-LIFECYCLE`. | Register entry | `audit-register.md` | Stable row | Entry check | VERIFIED_LOCAL |
| REQ-121-045 | Prepopulate `AUD-ISO26514-DOCS`. | Register entry | `audit-register.md` | Stable row | Entry check | VERIFIED_LOCAL |
| REQ-121-046 | Prepopulate `AUD-ISO20246-REVIEWS`. | Register entry | `audit-register.md` | Stable row | Entry check | VERIFIED_LOCAL |
| REQ-121-047 | Prepopulate `AUD-ISO33001-PROCESS`. | Register entry | `audit-register.md` | Stable row | Entry check | VERIFIED_LOCAL |
| REQ-121-048 | Prepopulate `AUD-LIVE-GREENPATH`. | Register entry | `audit-register.md` | Live evidence is planned, not claimed | Entry/status check | VERIFIED_LOCAL |
| REQ-121-049 | Findings severity values are Major, Minor, Observation and Positive finding. | Schema | `findings-register.md` | Severity contract | Vocabulary check | VERIFIED_LOCAL |
| REQ-121-050 | Findings status values are Open, In progress, Evidence pending, Risk accepted, Closed and Not applicable. | Schema | `findings-register.md` | Status contract | Vocabulary and closure check | VERIFIED_LOCAL |
| REQ-121-051 | Findings columns are Finding ID, Severity, Affected standard/framework, Finding text, Risk, Required remediation, Owner role, Status, Evidence link and Related issue. | Schema | `findings-register.md` | Table schema | Column check | VERIFIED_LOCAL |
| REQ-121-052 | Prepopulate major findings MAJ-01 through MAJ-05 with the issue descriptions. | Findings | `findings-register.md` | Five stable rows | ID/text check | VERIFIED_LOCAL |
| REQ-121-053 | MAJ-01 records missing full ISMS/SoA/risk register. | Finding | `findings-register.md` | MAJ-01 row | Content check | VERIFIED_LOCAL |
| REQ-121-054 | MAJ-02 records missing full live green path. | Finding | `findings-register.md` | MAJ-02 row | Content check | VERIFIED_LOCAL |
| REQ-121-055 | MAJ-03 records missing requirement-to-test-to-evidence traceability. | Finding | `findings-register.md` | MAJ-03 row | Content check | VERIFIED_LOCAL |
| REQ-121-056 | MAJ-04 records Docker socket exposure risk. | Finding | `findings-register.md` | MAJ-04 row | Content check | VERIFIED_LOCAL |
| REQ-121-057 | MAJ-05 records missing QMS-light/CAPA/audit cycle/quality objectives. | Finding | `findings-register.md` | MAJ-05 row | Content check | VERIFIED_LOCAL |
| REQ-121-058 | Prepopulate minor findings MIN-01 through MIN-08 with the issue descriptions. | Findings | `findings-register.md` | Eight stable rows | ID/text check | VERIFIED_LOCAL |
| REQ-121-059 | MIN-01 records incomplete documentation audience separation. | Finding | `findings-register.md` | MIN-01 row | Content check | VERIFIED_LOCAL |
| REQ-121-060 | MIN-02 records missing SBOM/SCA/dependency-security evidence. | Finding | `findings-register.md` | MIN-02 row | Content check | VERIFIED_LOCAL |
| REQ-121-061 | MIN-03 records missing performance/resource metrics. | Finding | `findings-register.md` | MIN-03 row | Content check | VERIFIED_LOCAL |
| REQ-121-062 | MIN-04 records an operational-readiness checklist that is not evidence-based. | Finding | `findings-register.md` | MIN-04 row | Content check | VERIFIED_LOCAL |
| REQ-121-063 | MIN-05 records missing repository license. | Finding | `findings-register.md` | MIN-05 row | Content check | VERIFIED_LOCAL |
| REQ-121-064 | MIN-06 records incomplete release/baseline process. | Finding | `findings-register.md` | MIN-06 row | Content check | VERIFIED_LOCAL |
| REQ-121-065 | MIN-07 records missing ASVS control matrix. | Finding | `findings-register.md` | MIN-07 row | Content check | VERIFIED_LOCAL |
| REQ-121-066 | MIN-08 records informal review records. | Finding | `findings-register.md` | MIN-08 row | Content check | VERIFIED_LOCAL |
| REQ-121-067 | Planned remediation links to #120 when no concrete child issue is known; otherwise it links the child issue. | Traceability | `findings-register.md`, `remediation-plan.md` | Issue links and explicit unknown-child marker | Link review | VERIFIED_LOCAL |
| REQ-121-068 | `Closed` requires evidence and cannot be inferred from documentation presence. | Governance | `findings-register.md` | Closure rule | Independent review | VERIFIED_LOCAL |
| REQ-121-069 | Evidence categories are repository documentation, static quality-gate, architecture, security, live, review and release. | Schema | `evidence-matrix.md` | Category contract | Category check | VERIFIED_LOCAL |
| REQ-121-070 | Evidence-matrix columns are Evidence ID, Evidence name, Evidence type, Source path/expected path, Related requirement/finding, Status, Redaction requirement and Notes. | Schema | `evidence-matrix.md` | Table schema | Column check | VERIFIED_LOCAL |
| REQ-121-071 | Prepopulate `README.md` as repository evidence. | Evidence entry | `evidence-matrix.md` | Repository row | Path/status check | VERIFIED_LOCAL |
| REQ-121-072 | Prepopulate `AGENTS.md` as repository evidence. | Evidence entry | `evidence-matrix.md` | Repository row | Path/status check | VERIFIED_LOCAL |
| REQ-121-073 | Prepopulate `QUALITY.md` as repository evidence. | Evidence entry | `evidence-matrix.md` | Repository row | Path/status check | VERIFIED_LOCAL |
| REQ-121-074 | Prepopulate `.importlinter` as architecture-quality evidence. | Evidence entry | `evidence-matrix.md` | Repository row | Path/status check | VERIFIED_LOCAL |
| REQ-121-075 | Prepopulate `tools/quality_gate.py` as static quality-gate evidence. | Evidence entry | `evidence-matrix.md` | Repository row | Path/status check | VERIFIED_LOCAL |
| REQ-121-107 | Prepopulate `tests/architecture/test_hexagonal_imports.py` as architecture-test evidence. | Evidence entry | `evidence-matrix.md` | Architecture-test row | Path/status check | VERIFIED_LOCAL |
| REQ-121-076 | Prepopulate `documentation/arc42.adoc`. | Evidence entry | `evidence-matrix.md` | Issue-named path and availability state | Path-drift check | VERIFIED_LOCAL |
| REQ-121-077 | Prepopulate `documentation/arc42/10_quality_requirements.adoc`. | Evidence entry | `evidence-matrix.md` | Repository row | Path/status check | VERIFIED_LOCAL |
| REQ-121-078 | Prepopulate `documentation/arc42/11_risks_and_debt.adoc`. | Evidence entry | `evidence-matrix.md` | Repository row | Path/status check | VERIFIED_LOCAL |
| REQ-121-079 | Prepopulate `documentation/system/live-operation-surfaces.adoc`. | Evidence entry | `evidence-matrix.md` | Repository row | Path/status check | VERIFIED_LOCAL |
| REQ-121-080 | Prepopulate `documentation/user-handbook.adoc`. | Evidence entry | `evidence-matrix.md` | Repository row | Path/status check | VERIFIED_LOCAL |
| REQ-121-081 | Record the operator configuration contract path and distinguish the stale issue path `documentation/configuration/operator-configuration-contract.md` from the canonical verified path `documentation/arc42/08_configuration/operator-configuration-contract.md`. | Path governance | `evidence-matrix.md` | Explicit stale/missing and canonical rows | File existence and link check | VERIFIED_LOCAL |
| REQ-121-082 | Mark live evidence as planned/missing until a permitted live run produces redacted evidence. | Live evidence | `evidence-matrix.md`, `audit-register.md` | `AUD-LIVE-GREENPATH` and live rows | No-live review | PLANNED |
| REQ-121-083 | Remediation plan covers all ten #120 workflows. | Roadmap | `remediation-plan.md` | Ten workflow rows/sections | Count and issue-link check | VERIFIED_LOCAL |
| REQ-121-084 | Workflow 1 is Audit evidence structure. | Roadmap | `remediation-plan.md` | Workflow 1 section | Content check | VERIFIED_LOCAL |
| REQ-121-085 | Workflow 2 is QMS-light documentation. | Roadmap | `remediation-plan.md` | Workflow 2 section | Content check | VERIFIED_LOCAL |
| REQ-121-086 | Workflow 3 is ISMS-light documentation. | Roadmap | `remediation-plan.md` | Workflow 3 section | Content check | VERIFIED_LOCAL |
| REQ-121-087 | Workflow 4 is Traceability matrix. | Roadmap | `remediation-plan.md` | Workflow 4 section | Content check | VERIFIED_LOCAL |
| REQ-121-088 | Workflow 5 is Live evidence contract. | Roadmap | `remediation-plan.md` | Workflow 5 section | Content check | VERIFIED_LOCAL |
| REQ-121-089 | Workflow 6 is OWASP ASVS mapping. | Roadmap | `remediation-plan.md` | Workflow 6 section | Content check | VERIFIED_LOCAL |
| REQ-121-090 | Workflow 7 is Supply-chain security gate proposal. | Roadmap | `remediation-plan.md` | Workflow 7 section | Content check | VERIFIED_LOCAL |
| REQ-121-091 | Workflow 8 is Branch protection and CI governance. | Roadmap | `remediation-plan.md` | Workflow 8 section | Content check | VERIFIED_LOCAL |
| REQ-121-092 | Workflow 9 is Documentation navigation restructuring. | Roadmap | `remediation-plan.md` | Workflow 9 section | Content check | VERIFIED_LOCAL |
| REQ-121-093 | Workflow 10 is Release and baseline process. | Roadmap | `remediation-plan.md` | Workflow 10 section | Content check | VERIFIED_LOCAL |
| REQ-121-094 | Every #120 workflow has a goal. | Roadmap | `remediation-plan.md` | Goal column/section | Completeness check | VERIFIED_LOCAL |
| REQ-121-095 | Every #120 workflow has expected output. | Roadmap | `remediation-plan.md` | Output column/section | Completeness check | VERIFIED_LOCAL |
| REQ-121-096 | Every #120 workflow identifies related major/minor findings. | Roadmap | `remediation-plan.md` | Finding links | Completeness check | VERIFIED_LOCAL |
| REQ-121-097 | Every #120 workflow has completion criteria and status. | Roadmap | `remediation-plan.md` | Criteria/status fields | Completeness check | VERIFIED_LOCAL |
| REQ-121-098 | Slice 1 creates the directory and README without certification overclaim. | Execution slice | S121-02 docs | Slice mapping and no-overclaim rule | Slice evidence | VERIFIED_LOCAL |
| REQ-121-099 | Slice 2 creates audit and findings registers. | Execution slice | S121-02 docs | Slice mapping | Slice evidence | VERIFIED_LOCAL |
| REQ-121-100 | Slice 3 creates the evidence matrix and marks live evidence planned/missing. | Execution slice | S121-02 docs | Slice mapping | Slice evidence | VERIFIED_LOCAL |
| REQ-121-101 | Slice 4 creates the remediation plan and links #120. | Execution slice | S121-02 docs | Slice mapping | Slice evidence | VERIFIED_LOCAL |
| REQ-121-102 | Slice 5 inspects existing documentation and adds only an appropriate short root pointer; it does not duplicate large content. | Navigation | `documentation/README.adoc` | Link decision and concise pointer | Diff/content review | VERIFIED_LOCAL |
| REQ-121-103 | Run `git diff --check`. | Quality | Repository | S121 evidence test results | Command result | VERIFIED_LOCAL |
| REQ-121-104 | Run `python3 tools/quality_gate.py quality`, or document an explicit environment blocker. | Quality | Repository | S121 evidence test results | Command result or blocker evidence | VERIFIED_LOCAL |
| REQ-121-105 | PR/issue evidence contains summary, created files, no-live confirmation, quality result and remaining gaps. | Completion evidence | `.tiny-swarm/evidence/issue-121/` | Six required evidence files | Completion-auditor review | VERIFIED_LOCAL |
| REQ-121-106 | Completion occurs only after the structure is merged and future issues can link to stable registers. | Release/process | Branch/issue evidence | Stable paths and guarded publication record; PR #254 merged as `a335fed0` | Final independent audit on merged baseline | VERIFIED_PR_MERGED |

## S121-01 execution contract

| ID | Workflow requirement | Implementation evidence | Verification | Status |
| --- | --- | --- | --- | --- |
| S121-01-001 | Owner is Senior Requirement Engineer. | Active and indexed workflow metadata | Workflow review | IMPLEMENTED |
| S121-01-002 | Reviewers are Audit Evidence Manager, Senior System Architect and Senior Tester. | Active and indexed workflow metadata | Role review reports | IMPLEMENTED |
| S121-01-003 | Matrix output is `.tiny-swarm/evidence/issue-121/requirement_matrix.md`. | This file | File existence check | IMPLEMENTED |
| S121-01-004 | Contract lock is `audit-status-contract`. | Workflow metadata | Lock review | IMPLEMENTED |
| S121-01-005 | Architecture lock is `documentation-as-governance-evidence`. | Workflow metadata | Architect review | IMPLEMENTED |
| S121-01-006 | S121-01 is serial and precedes S121-02. | Dependency graph and distribution evidence | Dependency/parallelism review | IMPLEMENTED |
| S121-01-007 | Stop on missing issue requirements, ambiguous evidence status or an unverified path treated as present. | Matrix status rules and blocker section | Independent review | IMPLEMENTED |
| S121-01-008 | S121-01 has no runtime, frontend, live or executable-tooling scope. | Scope and changed-file evidence | Changed-file audit | IMPLEMENTED |
| S121-01-009 | Distribution evidence exists before implementation and consolidation evidence follows implementation. | `.codex/evidence/issue-121/slice-S121-01-distribution.md`, `.codex/evidence/issue-121/slice-S121-01-consolidation.md` | Evidence-file check | VERIFIED_LOCAL |
| S121-01-010 | Required quality gates are `git diff --check` and `python3 tools/quality_gate.py quality`; unavailable results remain non-pass. | Workflow metadata and issue test results | Gate execution | VERIFIED_LOCAL |
| S121-01-011 | Issue completion requires requirement_matrix, implementation_summary, changed_files, test_results, remaining_risks and acceptance_checklist. | `.tiny-swarm/evidence/issue-121/` | Required-file check | VERIFIED_LOCAL |
| S121-01-012 | Requirement Lead, System Architect, Test/Evidence Reviewer and independent Issue Completion Auditor review completion. | Review evidence | Final audit | PASS |
| S121-01-013 | Any open or unverified requirement blocks `DONE`. | This matrix and acceptance checklist | Final audit | IMPLEMENTED |

## Verification-state and data-protection contract

The following are explicit non-pass states and must remain distinguishable in
all five audit documents: `planned`, `missing`, `blocked`, `refused`,
`resource-gated`, `failed-to-apply`, `failed-to-verify`, `not applicable`,
`evidence pending`, `open`, `in progress` and `risk accepted`. `closed` is
allowed only when a redacted, linkable evidence artifact and independent review
support it. Documentation presence alone is never closure evidence.

Future live evidence must be summarized or redacted. It must not contain
secrets, API tokens, environment payloads, Swarm join tokens, raw command
dumps, raw stdout/stderr, private host paths or private IP addresses. The
repository may contain expected paths and command names as governance metadata,
but this matrix contains no live output.

## Open source and drift findings to carry forward

| Finding | Why it remains open | Required treatment |
| --- | --- | --- |
| EPIC traceability | System Unification explicitly owns the repository-level audit-evidence backbone. | `VERIFIED_LOCAL`; preserve the ownership link and its governance-only boundary. |
| Audit-summary completeness | `documentation/audit/audit-summary.md` snapshots the five major and eight minor findings explicitly supplied by #120/#121. | `VERIFIED_LOCAL` against those sources; new findings require a reviewed authoritative source and are not silently excluded. |
| Operator contract path drift | The issue path is absent; the verified repository path is under `documentation/arc42/08_configuration/`. | Record both paths and their distinct states; never treat the stale path as present. |
| Quality-gate authority | Issue #121 requires the full gate or an explicit blocker; `QUALITY.md` allows a documented skip for documentation-only work. | The active workflow now declares the full gate required for this issue; record PASS, FAIL or BLOCKED/FAILED_TO_VERIFY. |
| Root navigation choice | A short pointer is conditional on appropriateness. | Inspect `documentation/README.adoc`; add only a concise verified pointer in S121-02. |

## Completion gate

S121-01 is ready for S121-02 only after this file, the S121-specific
distribution evidence and the workflow lock/quality reconciliation pass local
review. Issue #121 is not complete from this matrix alone. S121-02 must create
the five audit files, complete the six-file evidence package, run the declared
quality gates, and obtain an independent completion-auditor `PASS`.
