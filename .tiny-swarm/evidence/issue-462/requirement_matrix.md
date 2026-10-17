# Issue #462 requirement matrix

Source: #462 BOOT-W10; parent #452. Baseline: recorded in implementation_summary.md.
Scope: documentation and read-only completion audit; no runtime changes or live consent.

| ID | Requirement | Type | Implementation / verification target | Status |
|---|---|---|---|---|
| R462-01 | README has concise elevated PowerShell/WSL and native Linux preparation then installation paths (AC1) | UX | README and installation guide; command/help/source review | IMPLEMENTED; AC1 UNVERIFIED |
| R462-02 | Explain complete extracted release/checkout, distro selection and interactive ordinary account setup (AC1) | UX/security | README and installation guide; source-proof and checkout checks | IMPLEMENTED; archive limitation explicit |
| R462-03 | Explain plan/apply consent, resources, restart and resumption (AC1) | safety/resilience | README and guide; preparation/handoff/recovery tests | IMPLEMENTED; local coverage, live limits explicit |
| R462-04 | Move venv/pip/quality details out of default operator path, retain advanced references | UX | README and guide; developer manual link | VERIFIED by doc diff |
| R462-05 | Document URLs, credential sources, ordinary install vs explicit reset, versions and concrete remedies | operations | README and guide; usage and manual-host references | VERIFIED by source/reference review |
| R462-06 | Use Mermaid for suitable new diagrams | documentation | installation flow diagram; static syntax review | VERIFIED static Mermaid review |
| R462-07 | Every shown command exists/help matches; default walkthroughs exercised during W09 (AC2) | quality/live | source/help checks and W09 scenario evidence; clean walkthroughs remain unverified | PARTIAL: help/source checked; fresh walkthroughs UNVERIFIED |
| R462-08 | Scope/support/limitations match evidence with no unsupported success claims (AC3) | evidence | version and scope tables; W09 current amended audit and combined evidence | VERIFIED by W09 amended evidence review |
| R462-09 | Audit all BOOT requirements against child implementation/tests/live evidence before EPIC closure (AC4) | traceability | documentation/evidence/issue-462-bootstrap-completion-audit.md | AUDITED; original EPIC closure INCOMPLETE |
| R462-10 | Preserve architecture, Linux product execution, read-only preflight, reset isolation and bounded recovery; no duplicate provider/service work | constraint | documentation-only diff; existing local regression coverage | VERIFIED documentation-only scope |
| R462-11 | Record meaningful checks, redacted six-file evidence, independent review and truthful completion state | quality | issue-462 evidence and independent completion audit | VERIFIED local checks; independent audit INCOMPLETE (AC1/AC2 gaps) |

AC1 cannot be declared fully verified while ordinary Windows Apply is unqualified-blocked
and clean walkthrough prerequisites remain unexercised. AC2 and original EPIC live
closure remain open even though W09's operator-amended delivery passed. No scope
amendment for W10 or the entire EPIC is inferred from W09's closure.
