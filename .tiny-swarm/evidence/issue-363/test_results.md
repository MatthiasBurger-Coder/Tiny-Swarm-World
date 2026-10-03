# Test results

Candidate: `2a74134e1a39cd3dab27bbc43de1803844a9a004`.
Host: WSL2, Linux kernel `6.18.33.2-microsoft-standard-WSL2`.
Primary interpreter: Python 3.14.4. A separate isolated Python 3.12.14
environment also ran targeted local tests; it is not native-host live evidence.

| Command | Result | Scope |
|---|---|---|
| `PYTHONPATH=src python3 -m unittest tests.test_installer tests.test_simple_installer tests.test_package_entrypoint tests.test_classic_update_cli tests.application.services.platform.test_platform_lifecycle tests.application.services.platform.test_classic_update_workflow tests.application.services.deployment.test_ensure_infisical_bootstrap tests.application.services.deployment.test_ensure_infisical_secret_items tests.e2e.classic.test_lifecycle_contract tests.e2e.classic.test_browser_e2e_contract tests.e2e.classic.test_classic_suite_layout tests.e2e.classic.test_authenticated_service_contract tests.tools.test_classic_live_runner` | PASS, 292 tests, 0 skipped | Mocked installer, CLI, lifecycle, secrets and E2E contracts |
| `python3 tools/quality_gate.py quality` | PASS, 2,341 tests, 18 skipped | Policy, complexity, lint, import contracts, 36 architecture tests, typecheck of 726 files and full local unittest discovery |
| `PYTHONPATH=src python3 -m unittest tests.tools.test_classic_live_runner` | PASS, 13 tests | Corrected preflight classification and existing runner contracts |
| `python3 tools/quality_gate.py lint` | PASS | After runner correction |
| `python3 tools/quality_gate.py typecheck` | PASS, 726 files | After runner correction |
| `PYTHONPATH=src /tmp/tsw-issue363-py312/bin/python -m unittest tests.tools.test_classic_live_runner tests.e2e.classic.test_lifecycle_contract tests.e2e.classic.test_browser_e2e_contract tests.test_installer tests.test_package_entrypoint` | PASS, 189 tests | Python 3.12.14 targeted local regression after installing `requirements.txt` into an isolated venv |
| `PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_resources tests.infrastructure.test_composition tests.application.services.platform.test_preflight_service` | PASS, 187 tests | WSL2/native resource-profile and preflight regression |
| `PYTHONPATH=src /tmp/tsw-issue363-py312/bin/python -m unittest tests.domain.preflight.test_resources tests.infrastructure.test_composition tests.application.services.platform.test_preflight_service` | PASS, 187 tests | Same preflight regression on Python 3.12.14 |
| `python3 tools/quality_gate.py quality` | PASS, 2,343 tests, 18 skipped | Final branch diff, including WSL2 preflight correction; protected `final-quality-gate-after-preflight.log` |
| `python3 tools/quality_gate.py quality` | PASS, 2,343 tests, 18 skipped | Final gate after Jenkins Dockerfile correction; protected `final-quality-gate.log` |
| `git diff --cached --check && git diff --check` | PASS before final evidence update | Rerun after final staging |

The initial bare `python3.12` targeted attempt failed because runtime
dependencies, including `pydantic`, were absent. After creating an isolated
3.12 environment and installing `requirements.txt`, the same selected modules
passed. Its private output is retained at
`/home/micro/.local/state/tiny-swarm-world/evidence/issue-363/python312-targeted.log`
(mode `0600`). The full gate after the preflight correction is retained in the
adjacent `final-quality-gate-after-preflight.log`; the gate after the Jenkins
Dockerfile correction is in `final-quality-gate.log`.

The local gate's 18 skips are not live or browser successes. Operator consent
was supplied on 2026-10-03. The WSL2 Classic runner was invoked five times using
the owned test target, protected WSL-native credential/evidence paths and
controlled Jenkins update inputs. Protected evidence is under
`/home/micro/.local/state/tiny-swarm-world/evidence/classic-live/`:

| Run ID | Recorded state | Operations | Finding |
|---|---|---|---|
| `20261003T124322.763533Z` | `LIVE_FAILED_AFTER_MUTATION` (runner defect) | diagnostics exit 0; setup exit 1 | Setup's structured preflight was `resource_gated` on `RESOURCE-STRUCTURED` and `RESOURCE-MEMORY`; no lifecycle mutation phase ran. This original artifact is retained, not accepted as a correct mutation classification. |
| `20261003T125229.826078Z` | `LIVE_BLOCKED_BEFORE_MUTATION` | diagnostics exit 0; setup exit 1 | Same resource gate, correct overall state after runner fix; nested result was still `completed`. |
| `20261003T130144.128030Z` | `LIVE_BLOCKED_BEFORE_MUTATION` | diagnostics exit 0; setup exit 1 | Same resource gate; both overall state and nested `resource_gated` result now truthful. Later phases unrun. SHA-256 chain passed. |
| `20261003T131346.486260Z` | `LIVE_FAILED_AFTER_MUTATION` | diagnostics exit 0; setup exit 1 | After the WSL2 preflight correction, setup reached deployment apply and failed `deployment:traefik-gui-input`. Later phases unrun. |
| `20261003T131632.606459Z` | `LIVE_FAILED_AFTER_MUTATION` | diagnostics exit 0; setup exit 1 | Setup reached deployment apply and failed `deployment:infisical-sync`. Later phases unrun; checksum chain passed. |

Each run has a private `run-summary.json`, `checksums.sha256` and
`checksums.sha256.sha256`; only redacted summaries and checksums were stored.
The WSL2 host exposed about 19 GiB total RAM. The original 20 GB `.wslconfig`
value was restored after a temporary change; no restart occurred. The corrected
WSL2 service-access floor is 16 GiB, while native Linux retains 20 GiB.
Read-only WSL2 preflight with the protected operator environment passed exit 0.
The native Ubuntu 26.04 VM was reached with operator-provided credentials and
an isolated archive of the current candidate. Native preflight passed exit 0.
The transferred archive SHA-256 is
`e2ec074df3a13d724c322cd4a9c8458b84dd0d3b56b447073b1b7a71b6964a2d`.
The first native runner attempt lacked a Git commit in the archive copy; its
setup, platform verify and eight readiness E2E tests passed, then the
authenticated helper failed its provenance check. A local snapshot commit
`b52f6c1` was created only in the isolated VM copy. The rerun
`20261003T132652.889688Z` again passed setup, platform verify and eight
readiness E2E tests, then returned `LIVE_FAILED_AFTER_MUTATION` because all
nine Selenium browser tests were skipped (`authenticated_checks_failed`).
After installing Firefox and Selenium in a separate native VM test environment,
the direct authenticated baseline helper returned `LIVE_VERIFIED`: 8 readiness
tests before and after, 9 browser route tests, 7 API authentication checks,
25 live tests total, zero failures/errors/skips. The complete native runner
`20261003T133458.535975Z` then returned `LIVE_VERIFIED`: all 14 operations
had exit 0, including setup, platform verify, four 8/8 readiness E2E checks,
four authenticated browser/API checks with zero skips, reconcile, controlled
Jenkins update and recovery. Both `checksums.sha256` and its checksum verified.
A separate controlled Jenkins service restart returned exit 0 and replaced
task `221zlvo1i99u5dvt2gry8ydw9` with `iostglq8l1iqblkaz7nch2iar`; the
service returned to 1/1 replicas. The post-restart authenticated helper
returned `LIVE_VERIFIED` with 8+8 readiness, 9 browser and 7 API checks,
zero failures/errors/skips. Confirmed `platform destroy` then returned exit 0,
reported converged mutation and verified outcome; `incus list` showed no
managed nodes. The first installer rerun stopped before mutation on an active
LXD daemon, with no LXD instances present. The competing daemon was stopped on
the disposable VM. The second installer invocation from empty managed state
returned exit 0, with protected `setup-run.exit` equal to 0 under
`/home/tsw/.local/state/tiny-swarm-world/evidence/issue-363/installer/native_linux/20261003T134838582962Z/`.
All three Swarm nodes were `Ready/Active`; the Pulsar Manager bootstrap task
was `Complete`, while ordinary service replicas reached their desired counts.
The first post-install authenticated check returned `LIVE_PARTIAL`: all 8+8
readiness tests ran, but the Jenkins browser route failed and Jenkins API
authentication was false; 6 of 7 API checks completed, with one assertion
failure and zero skips. A bounded retry reproduced the same `LIVE_PARTIAL`
state. The deployed image's Groovy initialization file was `600 root:root`;
the service log reported permission denied, and both valid and invalid login
appeared as anonymous. The candidate Dockerfile set `--chown=jenkins:jenkins`
and `--chmod=0644`. On the native VM, a fresh image build returned exit 0,
`docker run --entrypoint stat` observed `644 jenkins:jenkins`, the local
registry push returned exit 0, and a guarded Jenkins image update completed
with one running task. The replacement task logged `Jenkins setup completed
successfully.` The post-update authenticated helper exited 0 with
`LIVE_VERIFIED`: 8+8 readiness tests, 9 browser routes, 7 API checks, 25 live
tests in all, and zero failures, errors or skips. Protected output is at
`/home/tsw/.local/state/tiny-swarm-world/evidence/issue-363/native-post-jenkins-fix.log`.
This is a managed-state reinstall on a prepared host, not a factory-clean
installation.
Native protected evidence is under
`/home/tsw/.local/state/tiny-swarm-world/evidence/issue-363/classic-live/`.
The WSL2 host has not reached update, recovery, restart or cleanup in a
successful current-candidate chain.
External SonarQube was not consulted and has no verified result here.
