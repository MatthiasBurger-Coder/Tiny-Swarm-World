# Remaining risks and blockers

1. WSL2 preflight now passes with the original 20 GB `.wslconfig` setting and
   the protected operator environment. WSL2 live setup still failed after
   mutation: one run at Traefik GUI input verification and the next at
   Infisical secret synchronization. The managed nodes and reported Infisical
   services were healthy in read-only checks, but authenticated Infisical login
   returned HTTP 400. The precise credential or API cause remains unresolved.
2. Native Ubuntu 26.04 passed the full 14-operation Classic live chain after
   Firefox and Selenium were provisioned in a separate test environment. The
   earlier nine browser skips remain retained as an explicit non-success run.
3. Native controlled Jenkins restart, post-restart authenticated checks and
   confirmed destroy passed. WSL2 did not reach reconcile, update, recovery,
   restart or cleanup because deployment apply failed.
4. A native installer rerun from an empty managed state passed. That is not a
   factory-clean first install because host packages and Incus preparation
   remained. Its first post-install authenticated check was `LIVE_PARTIAL` on
   Jenkins, despite the installer exit 0. The bounded retry confirmed the
   failure. The deployed Jenkins image contained an unreadable `600 root:root`
   initialization file. The corrected image used `644 jenkins:jenkins`; a
   guarded update completed and the authenticated browser/API suite then
   returned `LIVE_VERIFIED` with no skips. A clean-host qualification still
   needs separate current-candidate evidence if required by the issue acceptance.
5. September RC1 and issue #427 live runs precede later refactor commits and
   cannot be reused as current-candidate acceptance. Python 3.12 targeted
   tests passed locally, while the native live host used Python 3.14.

No failure or skip has been reclassified as success. Issue #363 remains open
until the live scenarios pass and independent completion review accepts the
evidence.
