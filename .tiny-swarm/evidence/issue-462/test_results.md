# Test and static verification results

Date: 2026-10-17. Linux shell; existing `.venv` Python 3.14.4.
No Windows-native product Python, live host mutation, service authentication,
reset, preparation apply, browser or external gate was executed.

| Command / check | Result |
|---|---|
| `./prepare_linux.sh --help` | PASS, exit 0; supported host/profile/read-only/stage consent/group boundaries match docs |
| `PATH="$PWD/.venv/bin:$PATH" ./install.sh --help` | PASS, exit 0; Linux/WSL preflight/dry-run, ordinary reconcile, explicit deprecated reset and live-approval switches match docs |
| `prepare_windows.ps1 -Help` implementation / `Application.ps1` static review | Reviewed only; PowerShell unavailable on PATH, NOT EXECUTED. Distro/release/LinuxCheckout/qualification guard and handoff match source |
| `TMPDIR=/home/micro/tsw-issue462-checks PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m unittest tests.test_install_handoff tests.test_bootstrap_recovery tests.test_simple_installer tests.architecture.test_skill_registry_integrity` | PASS, exit 0; 50 tests in 18.054s, no skips reported |
| `PATH="$PWD/.venv/bin:$PATH" python3 tools/quality_gate.py verification-policy` | PASS, exit 0 |
| Local documentation static script | PASS, exit 0; 8 Bash blocks syntax, Markdown file links, matrix test paths, entrypoint/state paths, README hash checked. New Mermaid block inspected; no renderer run |
| `git diff --check` | PASS, exit 0 |

Focused tests protect read-only source proof, selected checkout handoff, dependency
ordering, interrupted resume, protected/corrupt state, credentials preservation,
reset isolation and provenance. They are mocked/disposable local fixtures, not
live installation proof. Logs retained locally in /home/micro/tsw-issue462-checks/;
no raw logs, credentials, host addresses or generated artifacts are published.
Task-private disk-backed TMPDIR avoids the nearly full shared RAM-backed /tmp;
no existing files were removed and no test thresholds were changed.

The final README activation correction uses the prepared environment when it
exists, otherwise the already prepared system interpreter. Direct examples use
`PYTHONPATH=src python3 -m tiny_swarm_world` to avoid assuming a CLI executable
was installed on the caller's PATH. Final provenance check: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
.venv/bin/python -m unittest tests.architecture.test_skill_registry_integrity`
PASS, exit 0; 5 tests in 0.899s after the last README hash refresh.

Full `python3 tools/quality_gate.py quality`: NOT RUN for this documentation-only
scope, as permitted by QUALITY.md Documentation And Governance Checks. No Python,
configuration, test or quality-policy behavior changed. Focused regressions,
policy, provenance and static checks are the relevant narrower gate. Historical
W09 full-gate results are cited with their own source; not claimed for this branch.
