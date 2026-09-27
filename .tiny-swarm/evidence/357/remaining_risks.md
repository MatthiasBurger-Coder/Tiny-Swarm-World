# Remaining risks

- Network doctor retains host-specific diagnostic and WSL repair branches because those conditions are its explicit policy. Adding a new host runtime requires reviewing that policy and adding corresponding tests.
- The settled-tree full gate exposed timing sensitivity in an unrelated setup timeout integration test. It passed in isolation and the full-suite retry passed without code changes. Both full-run outcomes remain recorded in `test_results.md`.
- Live host preparation was not applicable to this refactor's local verification and was not run; mocked adapter tests protect selection behavior.
- External SonarQube status was not observed and is not claimed.
