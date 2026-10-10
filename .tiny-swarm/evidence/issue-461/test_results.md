# Test results

Candidate: `0528aac913c37ddfd66fc8f326d5f92505bdd7dd`.
Local verification executed on Linux/WSL using the existing project virtual
environment, Python 3.14.4; no Python 3.12 execution is claimed.

- `PATH="$PWD/.venv/bin:$PATH" PYTHONPATH=src python3 -m unittest tests.test_bootstrap_recovery tests.test_install_handoff tests.test_ubuntu_bootstrap_integration tests.test_prepare_windows tests.test_security_gate`: PASS, exit 0, 35 tests in 27.226s, no skips reported. Log: `/tmp/issue-461-targeted.log` (local transient artifact).
- `PATH="$PWD/.venv/bin:$PATH" python3 tools/security_gate.py dependencies`: FAIL, exit 1. pip_audit found 3 known vulnerabilities in locked urllib3 2.7.0: PYSEC-2026-4175, PYSEC-2026-4176, PYSEC-2026-4177; tool-reported fix version 2.8.0. Log: `/tmp/issue-461-dependencies.log`. No dependency lock edits. AC4 remains BLOCKED.
- `PATH="$PWD/.venv/bin:$PATH" python3 tools/quality_gate.py quality`: FAIL, exit 1: 2,554 tests in 644.359s, 18 skips, one subprocess timeout in `tests.test_install_script.TestInstallScript.test_install_uses_private_configured_evidence_root` (fixture deadline 10s on the mounted checkout). Policy, complexity, lint, 7 import contracts, 43 architecture tests and typecheck of 799 files passed. This used the existing Python 3.14.4 environment; it is not an exact clean final-candidate run. Log: `/tmp/issue-461-quality.log`.
- `git diff --check`: PASS at evidence preparation; repeat after finalization.

The focused suite preceded the first full gate. The corrected lock is being
verified in a separate Linux-native checkout with an isolated Python 3.12
environment and PowerShell 7.6.6; no shared test fixture files are used.
The dependency audit is independent of regression verification.
Container image/config scanning is not claimed: no container configuration change
and no local trivy executable observed. External result unavailable, not verified.

Read-only target inspection: native password-authenticated SSH OS/kernel/PID1/
executable inventory exit 0; initial key-only attempt exit 255 (authentication
not accepted), not a qualification failure. Local OS/kernel/PID1 inspection and
Windows OS/WSL version/distribution inventory exit 0. Redacted facts are in
qualification_matrix.md; no passwords or remote address stored here.

No mutating live scenario executed. Required live scenarios: LIVE_CONSENT_MISSING
pending explicit recoverable-target/operation consent.
No current external CI/SonarQube result accessed.

## AC4 remediation in progress

- Supported Python 3.12.14 lock generation with pip-tools 7.5.3 changed only urllib3 2.7.0 -> 2.8.0 and its two artifact hashes. No audit ignores or policy changes. Upstream source: [urllib3 2.8.0 release](https://pypi.org/project/urllib3/2.8.0/).
- `PATH="$PWD/.venv/bin:$PATH" python3 tools/security_gate.py dependencies` after lock remediation: PASS, exit 0, no known vulnerabilities found. Log: `/tmp/issue-461-dependencies-fixed.log`. This does not erase the original failed audit.
- Clean Python 3.12 environment hash-verified runtime lock installation: PASS, exit 0. `python -m pip check`: PASS, no broken requirements.
- `PATH="/tmp/tsw-issue461-runtime312/bin:/tmp/tsw-powershell-7.6.6:$PATH" python3 tools/quality_gate.py quality` in `/home/micro/tsw-issue461-verification`: PASS, exit 0, 2,554 tests in 137.523s with 18 existing skips; 43 architecture tests, 7 import contracts, typecheck 799 files, lint, complexity and verification-policy passed. Tested base candidate plus byte-identical corrected lock; source freeze follows.
- Hyper-V administrator inventory: initial unelevated `Get-VM` denied (exit 1); UAC-elevated inventory succeeded. Owned VM creation succeeded with no other VM/switch changes; full bootstrap is unverified.

Final corrected-candidate gate used Python 3.12.14 and PowerShell 7.6.6.
The earlier mounted-checkout timeout is retained as a failed invocation; the
new Linux-native checkout result is a separate success. No test deadline,
assertion, complexity threshold, import rule or audit rule was weakened.
