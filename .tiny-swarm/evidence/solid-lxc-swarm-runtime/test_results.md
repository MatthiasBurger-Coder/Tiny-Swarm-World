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
| `python3 tools/quality_gate.py test` | PASS — 1,633 tests, 28 skipped, 117.951s |
| `python3 tools/quality_gate.py quality` | PASS — 148.2s; policy, lint, arch-lint, arch-tests, mypy, and tests |
| `git diff --check` at slice checkpoints | PASS |

## Explicitly not run

* Live Selenium browser execution: `LIVE_CONSENT_MISSING`.
* Incus, Docker Swarm, Portainer, Nexus, or credential-backed commands: not
  run under the local workflow safety policy.
* SonarQube external gate: no observable result available.
