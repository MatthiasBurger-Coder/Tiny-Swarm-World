# Issue #362 — Architecture regression suite

Issue: [ARCH-03.19] Add Architectural Regression Test Suite. Parent: #313.
Branch: `issue-362-architecture-regression-suite`. No active workflow slice or file lock applies to this direct issue branch.

| ID | Requirement | Type | Likely files | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Detect forbidden imports across documented package layers. | Scope | `tests/architecture/` | `architecture_violations` scans domain, application, and ports. | Synthetic prohibited import probes and repository scan | VERIFIED |
| REQ-002 | Detect root level infrastructure bypasses. | Scope | `tests/architecture/` | Entrypoint and new root module rules. | Synthetic root bypass probes and repository scan | VERIFIED |
| REQ-003 | Detect concrete runtime imports from application. | Scope | `tests/architecture/` | Application rule covers infrastructure package and CLI. | Concrete adapter import and construction probe | VERIFIED |
| REQ-004 | Detect CLI and infrastructure responsibility mixing. | Scope | `tests/architecture/` | Infrastructure cannot import CLI; application cannot import CLI. | Synthetic probes for both directions | VERIFIED |
| REQ-005 | Enforce composition ownership of concrete adapter binding. | Scope | `tests/architecture/` | Root and application cannot import adapters; composition may. | Adapter construction failure and composition allowed probes | VERIFIED |
| REQ-006 | Cover known orchestration hotspots from ARCH-03 inventory. | Scope | `tests/architecture/` | Root entrypoints, legacy installer, simple installer, application and composition import edges scanned; new cyclic composition edges rejected. | Mutation probes for root/installer/application and a synthetic composition cycle; repository scan | VERIFIED |
| REQ-007 | Run the suite in CI. | Acceptance | `tools/quality_gate.py`, CI workflow | New module in `arch-tests`; CI runs `quality`. | Targeted `arch-tests` and `.github/workflows/python-quality-gate.yml` review | VERIFIED |
| REQ-008 | Deliberate prohibited dependencies fail the suite with actionable locations and rules. | Acceptance | `tests/architecture/` | Diagnostic strings contain relative path, line, rule, import. | `test_prohibited_dependency_mutations_fail_with_actionable_messages` | VERIFIED |
| REQ-009 | Keep justified legacy exceptions explicit and bounded. | Acceptance | `tests/architecture/`, architecture documentation | Exact module allowlist, child source-module resolution, wildcard rejection, and ARCH-03.02 explanation. | Allowed and prohibited legacy import probes, including a new package child and wildcard import | VERIFIED |
| REQ-010 | Match documented package responsibilities. | Acceptance | `documentation/arc42/05_analysis/`, `tests/architecture/` | Rules reflect ARCH-03.02 layer contract. | Contract review and architecture gate | VERIFIED |
