# Change-Specific Branch Coverage: #282 / CRED-04

Command:

```text
python3 -m coverage erase
PYTHONPATH=src python3 -m coverage run --branch -m unittest tests.infrastructure.test_composition tests.infrastructure.adapters.clients.test_infisical_cli_client tests.application.services.deployment.test_secret_management tests.test_simple_installer tests.test_install_script tests.test_installer tests.domain.configuration.test_credential_resolution tests.infrastructure.test_composition_configuration tests.application.services.deployment.test_infisical_silent_install
```

The resulting coverage data was compared with the zero-context Git diff for
the changed production modules. Deleted legacy lines are excluded. The
change-specific metric counts non-comment added production lines and branch
arcs whose source is an added line.

| Metric | Covered | Total | Result |
|---|---:|---:|---:|
| Added non-comment production lines | 89 | 89 | 100.0% |
| Added source branch arcs | 12 | 12 | 100.0% |

The result exceeds the CRED-04 threshold of 95%. The complete repository
branch-aware run is recorded in `test_results.md`.
