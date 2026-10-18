# Test results — #442

Tested baseline SHA: `4ddc2d7d50e371922f04cd59b8340070a76dc8f1` plus the
uncommitted issue-442 patch on `feat/442-installation-manifest`.
At local verification time, no new commit had been created. Host: WSL2 Linux
`6.18.33.2-microsoft-standard-WSL2`; interpreter Python 3.14.4; Classic contract.
No installed product/component runtime or live service selection is claimed.
Catalog baseline is the checked-out ContainerImageContract and Compose assets;
per-test selections are synthetic Incus/Portainer inventories, not deployed hosts.

| Command | Result / exit |
|---|---|
| `PYTHONPATH=src python3 -m unittest tests.domain.lifecycle.test_models tests.infrastructure.adapters.lifecycle.test_manifest tests.infrastructure.adapters.lifecycle.test_catalog tests.application.services.test_lifecycle tests.test_lifecycle_cli` | PASS, 30 tests, exit 0; /tmp/issue442-targeted.log |
| `python3 tools/quality_gate.py complexity` after routing extraction | PASS, 319 orchestration modules, exit 0 |
| `python3 tools/quality_gate.py lint` | PASS, exit 0 |
| `python3 tools/quality_gate.py typecheck` | PASS, 823 files, exit 0; /tmp/issue442-typecheck-final.log |
| `python3 tools/quality_gate.py quality` initial | FAIL, exit 1, dispatcher main newly critical; resolved by extracting early routing helper; no threshold changes |
| `python3 tools/quality_gate.py quality` second | Interrupted deliberately during test stage to use prepared environment; NOT PASS. W01 evidence documents system user-site dependency isolation problem. Earlier sub-gates passed; final result is not reused |
| `.venv/bin/python tools/quality_gate.py quality` first prepared run | FAIL, exit 1; 2661 tests in 696.447s, exactly 2 failures (stale README hash and old declared-command tuple), 18 skipped. Both corrected with focused passes; /tmp/issue442-quality-final.log |
| `git diff --check` | PASS, exit 0; repeated after final evidence construction |

Final prepared rerun: `.venv/bin/python tools/quality_gate.py quality` PASS,
exit 0, all seven gates. 319 orchestration modules; Ruff PASS; 7 import contracts
kept, 0 broken; 43 architecture tests PASS; mypy 823 files PASS; full suite
2661 tests in 579.548s, OK (skipped=18). Log: /tmp/issue442-quality-verified.log.
All source/test corrections were in place before this run. Eighteen skips remain
skips, not live/browser/external evidence. Local test
skips remain skips; no live/browser/SonarQube success is implied. No production
commands, registry queries, infrastructure deployments or credential calls run.

Independent review found malformed YAML map-shape and exact catalog-version type
validation gaps; both were fixed with meaningful negative regressions before the
final prepared-environment gate. No test/architecture/safety guard was weakened.

Additional focused checks: prepared-env `tests.test_package_entrypoint`: PASS,
69 tests, exit 0 (/tmp/issue442-entrypoint.log);
`tests.architecture.test_skill_registry_integrity`: PASS, 5 tests, exit 0.
README hash synchronization changes exactly one registry value; command-name
expectation adds only the two implemented read-only commands.
Prepared-env `--help` and `--list-workflows`: PASS, exit 0.
Python 3.12 AST syntax validation: PASS for seven new model/service/port/adapter
modules; this is syntax evidence, not a Python 3.12 runtime qualification.

Final documentation checks: verification-policy PASS, git diff --check PASS,
changed/new-file whitespace and local Markdown links PASS (all exit 0).

Publication preflight: fresh 30 focused tests, lint, verification-policy and
diff checks PASS. Source/test behavior is unchanged from the full-gate run.
