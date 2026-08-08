# Issue #183 Test and Quality Results

All project Python commands were executed through WSL/Linux.

| Check | Result |
| --- | --- |
| Slice 02 focused command/runtime suite | PASS — 65 tests |
| Slice 03 direct Swarm modules | PASS — 6 tests |
| Slice 03 legacy/runtime compatibility suite | PASS — 65 tests |
| Slice 04 direct Docker/service/image modules | PASS — 14 tests |
| Slice 04 legacy runtime/logging suite | PASS — 60 tests |
| Slice 05 composition/runtime/boundary suite | PASS — 157 tests |
| Slice 06 static browser contract | PASS — 17 tests |
| Legacy facade cleanup regression | PASS — 69 focused tests; boundary test rejects every non-approved class definition |
| `python3 tools/quality_gate.py test` | PASS — 1,633 tests, 28 skipped, 117.951s |
| `python3 tools/quality_gate.py quality` | PASS — 148.2s; policy, lint, arch-lint, arch-tests, mypy, and tests |
| `git diff --check` at slice checkpoints | PASS |
| Live post-install installation checks | PARTIAL — 28 tests; management/API checks passed, but direct urllib HTTP/HTTPS route probes recorded `URLError` for routed hosts |
| Live Selenium browser suite with configured credentials | PASS — 31 tests, 0 skipped; all nine routed browser results passed |
| Live browser evidence | PASS — `.tiny-swarm-world/evidence/solid-lxc-swarm-runtime/e2e/suite-summary.json` reports `passed`; generated route evidence is redacted |
| SonarCloud public quality-gate status | FAIL — project status `ERROR`; New Code Security Rating is `2` against threshold `1` |
| SonarCloud finding remediation preparation | PASS locally — insecure URL literals were replaced by structured scheme parsing/composition without changing local HTTP behavior |
| SonarCloud branch/issue observation | BLOCKED for Issue #183 comparison — only `main` is exposed at `50733ea`; it reports `425` open code smells and has no analysis for the current workflow commit |

## Explicitly not run

* Incus, Docker Swarm, Portainer, Nexus, or credential-backed commands: not
  run as mutation/bootstrap operations. The approved live browser checks did
  use the configured credential sources without printing their values.
* SonarQube/SonarCloud accepted gate: not achieved; the observable SonarCloud
  result is `ERROR`, and the local SonarQube project is empty.
