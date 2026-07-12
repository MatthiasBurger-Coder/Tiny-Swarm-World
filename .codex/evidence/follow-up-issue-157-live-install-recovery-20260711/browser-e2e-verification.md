# Browser E2E Verification

- Consent: explicit `TSW_RUN_POST_INSTALL_BROWSER_LIVE=1` for this invocation only
- Matrix source: effective access model `service_access_links`
- Browser: real headless Firefox through Selenium
- Final result: PASS

The first current-head live run intentionally remains in ignored evidence and failed one route: Pulsar Manager had no admin user because its bootstrap container was externally terminated with exit 137. Worker 1 had no OOM. The bootstrap restart policy was changed to bounded `on-failure`; the replacement task completed with exit 0, and API login returned success.

The final discovery run passed 31/31 tests. Its suite summary contains exactly these nine passed routes:

- infisical
- jenkins
- nexus
- portainer
- pulsar-admin-api
- pulsar-manager
- service-access
- sonarqube
- swagger

Final status matrix:

- passed: 9
- failed: 0
- skipped: 0
- missing: 0
- suite result: `passed`

Independent summary validation: `LIVE_E2E_PASS routes=9`.
