# Issue #361 requirement matrix

Source: ARCH-03.18, parent #313. Baseline branch: `issue-361-complexity-guardrails` from clean `main`.

| ID | Requirement from issue | Type | Files likely affected | Implementation evidence | Test evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | Record the current orchestration complexity and maintainability baseline. | Acceptance | `tools/`, `documentation/arc42/05_analysis/` | `arch-03-18-complexity-baseline.json` records 259 modules and 1,955 functions; method in guardrail document | Final complexity gate passes and matches snapshot | VERIFIED |
| REQ-002 | Cover cyclomatic complexity, oversized functions/classes/modules, dependency fan-out, and duplicated orchestration where relevant. | Scope | `tools/`, baseline, documentation | AST branching indicator, physical spans, direct import targets, and duplicate fingerprints in checker and snapshot; exact metric limits documented | 12 focused metric tests and final complexity gate pass | VERIFIED |
| REQ-003 | Focus guardrails on architectural erosion without arbitrary style-driven size limits. | Goal and acceptance | `tools/`, `QUALITY.md`, architecture documentation | Combined critical signals, material growth checks, and documented rationale; size alone cannot fail | `test_size_alone_does_not_fail_and_coupled_growth_does` and crossing/growth tests pass | VERIFIED |
| REQ-004 | Make new critical complexity regressions fail CI or explicitly require review. | Acceptance | `tools/quality_gate.py`, `tools/`, CI workflow | Complexity command in canonical gate; existing PR workflow runs `quality`; finding keys and reviewed exception map | New/grown/crossing/duplicate/disappearing-path tests pass; final quality gate passes | VERIFIED |
| REQ-005 | Document intentional exceptions. | Acceptance | baseline and architecture documentation | Empty explicit exception map; owner/reason/issue contract and baseline grandfathering documented | `test_reviewed_exceptions_require_metadata_and_cannot_be_stale` passes | VERIFIED |
| REQ-006 | Keep the existing quality gate green. | Acceptance | `tools/quality_gate.py`, tests | Quality gate integration and governing `QUALITY.md` hash refresh | Final `python3 tools/quality_gate.py quality`: PASS, 2,335 tests, 18 skipped | VERIFIED |
| REQ-007 | Preserve parent EPIC #313 architecture and live-safety boundaries. | Inherited constraint | Tooling and documentation | Source-only static check; no product runtime changes | Import-linter 6 kept/0 broken, 30 architecture tests pass, independent architecture review confirms fit | VERIFIED |

Verification applicability: `APPLICABLE_LOCAL` for deterministic source analysis and quality checks. Live installation and browser checks are `NOT_APPLICABLE`. SonarQube is `APPLICABLE_EXTERNAL` to publication, with `EXTERNAL_GATE_UNAVAILABLE` before a pull-request result; no external success is claimed.
