# S252-13 Consolidation

Status: `PASS_LOCAL`; external GitHub Actions and SonarCloud run evidence is
still open for S252-16.

## Stream results

- Runtime/DevOps: added `.github/workflows/python-quality-gate.yml` for push
  and pull-request execution of the canonical Linux quality gate.
- Quality: kept the hashed runtime lock, pinned the quality-tool installation,
  generated a deterministic `coverage.xml` handoff and made Sonar a separate
  external analysis gate.
- Tests: added `tests/test_ci_workflow_contract.py`; focused contract tests
  passed 11/11, and the full repository suite passed 1772 tests with 18
  documented skips.
- Documentation: updated the CI governance contract and corrected stale
  verification-state names in the active workflow so the policy gate remains
  authoritative.
- Security: missing Sonar token, missing coverage handoff, failed quality
  prerequisite and unavailable external status fail closed; no secret or live
  infrastructure command is emitted by the hosted quality workflow.

## Accepted findings

- The existing Sonar workflow duplicated the canonical quality gate and
  treated a missing token as a successful skip. It now consumes the quality
  workflow's coverage artifact and owns only external analysis.
- The active workflow contained obsolete `LIVE_BLOCKED` and
  `LIVE_UNVERIFIED` tokens and policy-checker false-positive stop-condition
  wording. These were replaced with canonical verification states and explicit
  non-success wording.

## Rejected findings

- No product-runtime or `composition.py` change was accepted; the slice owns
  CI workflow contracts only.
- No real SonarCloud or GitHub Actions result was inferred from local tests.

## Changed files by stream

- Runtime/quality: `.github/workflows/python-quality-gate.yml`,
  `.github/workflows/sonar_check.yml`
- Tests: `tests/test_ci_workflow_contract.py`
- Documentation/governance: `documentation/governance/ci-quality-gates.md`,
  `documentation/workflow/workflow.md`
- Process evidence: `.codex/evidence/slice-13-distribution.md`

## Verification

- YAML parse of `.github/workflows/*.yml`: PASS.
- `python3 -m unittest tests.test_ci_workflow_contract tests.test_package_metadata tests.tools.test_check_verification_policy_consistency`: PASS, 17 tests.
- `python3 tools/quality_gate.py quality`: PASS; 1772 tests, 18 skips; lint,
  architecture checks and mypy passed.
- `git diff --check`: PASS.
- SonarCloud result: `EXTERNAL_GATE_UNAVAILABLE` locally; no token or hosted
  workflow-run evidence was available in this execution environment.

## Final integration decision

Accept S252-13 as locally implemented and verified. Keep REQ-252-045 and
REQ-252-047 open until S252-16 records real workflow-run and external-gate
evidence. The next executable slice is S252-14.
