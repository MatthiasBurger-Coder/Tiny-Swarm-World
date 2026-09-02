# Change-Specific Branch Coverage: #282 / CRED-04

Command:

```text
python3 -m coverage erase
PYTHONPATH=src python3 -m coverage run --branch -m unittest tests.infrastructure.test_composition tests.infrastructure.adapters.clients.test_infisical_cli_client tests.application.services.deployment.test_secret_management tests.test_simple_installer tests.test_install_script tests.test_installer tests.domain.configuration.test_credential_resolution tests.infrastructure.test_composition_configuration tests.application.services.deployment.test_infisical_silent_install
python3 -m coverage json -o /tmp/tsw-cred04-coverage-full-final.json
python3 tools/coverage_diff.py --base main --coverage-json /tmp/tsw-cred04-coverage-full-final.json
```

The resulting coverage data was compared with the zero-context Git diff for
the changed production modules by the versioned `tools/coverage_diff.py`
utility. Deleted legacy lines are excluded. The change-specific metric counts
added executable production statement lines reported by Coverage.py and
branch arcs whose source is an added executable line; comments, imports,
multiline expression continuations, and deleted legacy lines are not counted.

| Metric | Covered | Total | Result |
|---|---:|---:|---:|
| Added executable production lines | 56 | 56 | 100.0% |
| Added source branch arcs | 16 | 16 | 100.0% |

The result exceeds the CRED-04 threshold of 95%. The complete repository
branch-aware run is recorded in `test_results.md`.
