# Issue #201 Test Results

Date: 2026-08-06

| Check | Result | Evidence |
|---|---|---|
| `git diff --check` | PASS | No whitespace errors. |
| `python3 tools/check_verification_policy_consistency.py` | PASS | Canonical policy, state vocabulary, wording, and consent-context checks passed. |
| `PYTHONPATH=src python3 -m unittest tests.tools.test_check_verification_policy_consistency` | PASS | 6 focused tests passed. |
| `python3 tools/quality_gate.py verification-policy` | PASS | Deterministic policy checker passed through the quality-gate entry point. |
| `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && python3 -u tools/quality_gate.py lint'` | PASS | Ruff reported all checks passed. |
| `python3 tools/quality_gate.py arch-lint` | PASS | Three import contracts kept; zero broken. |
| `python3 tools/quality_gate.py arch-tests` | PASS | 18 tests passed. |
| `python3 tools/quality_gate.py typecheck` | PASS | mypy reported no issues in 526 source files. |
| `python3 -m unittest tests.architecture.test_skill_registry_integrity` | PASS | 5 tests passed after governing hash refresh. |
| `python3 tools/quality_gate.py quality` | PASS | Policy checker, lint, architecture, typecheck, and 1,595 tests passed; 28 skipped. |
| GitHub issue re-read for #176, #183, #184, #186–#192 | PASS | All required policy states present; no unconditional live/Selenium/Sonar wording. |
| GitHub issue re-read for #195/#185 | PASS | #195 aligned; #185 closed as duplicate. |
| Open-issue phrase search for unconditional Selenium/Sonar wording | PASS | Zero matches for the forbidden success phrases; the remaining `mandatory Selenium` hit in #195 is an explicit negative merge-note statement. |
| Canonical live installer command | `LIVE_BLOCKED_BEFORE_MUTATION` | Windows-mounted checkout guard stopped the run before mutation. |
| Authorized override live installer command (initial run) | `LIVE_FAILED_AFTER_MUTATION` | Reset passed; setup failed with `apt_repository_unreachable` on all three LXC nodes. |
| Targeted `./tsw network repair --linux-forwarding --apply` | PASS | Persistent Incus forwarding rules applied; LXC HTTP egress verified. |
| Final live `setup run` | PASS | All setup phases completed, including deployment and platform verification. |
| Final live `platform verify --json` | PASS | 26 preflight checks, three nodes, Docker runtime, Swarm membership, 18 proxy devices, and Portainer endpoint verified. |
| Final service smoke | PASS | 18 long-running services at healthy replicas; Pulsar manager bootstrap job completed. |
| Windows-side localhost HTTP smoke | NOT VERIFIED | Elevated PowerShell portproxy validation remains a separate external gate. |
| `tools/windows/doctor-portproxy.ps1` | BLOCKED / EXTERNAL_GATE_UNAVAILABLE | The documented check requires an elevated Administrator PowerShell session. |

The first live run exposed the network prerequisite; the targeted repair and
the subsequent idempotent rerun completed successfully. No browser/Selenium or
external SonarQube quality-gate claim is required or made for Issue #201.

The first combined quality invocation timed out at 125 seconds without a
result, and an intermediate run exposed stale governing hashes. Both were
resolved and the final full quality gate passed.

Live evidence: `.tiny-swarm-world/evidence/installation-tests/wsl2/20260805T045023Z/`.
