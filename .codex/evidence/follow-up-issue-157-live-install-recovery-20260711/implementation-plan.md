# Implementation Plan

1. Preserve merged Issue #157 routing, dashboard, evidence, and dynamic browser behavior.
2. Replace the checkout-bound Windows task with a protected, transactional Windows service agent and typed preflight state.
3. Harden service ownership, ACL, journal recovery, checksum validation, redaction, and service-preserving rollback.
4. Repair live deployment blockers for external Traefik secrets, Infisical recovery, SonarQube credentials, Portainer requests, and generated dashboard transfer.
5. Run the approved fresh installation with observable phase evidence and separate outer timeouts.
6. Fix only blockers proven by that run: ignored-tree scan traversal, manager memory, and interrupted Pulsar Manager bootstrap.
7. Run deployment apply, deployment verify, platform verify, Windows bridge verification, routing evidence validation, and opt-in Selenium separately.
8. Run all six quality gates plus Pester and Windows asset tests.
9. Produce follow-up evidence, obtain an independent completion audit, then perform the guarded `push auto` lifecycle.

Steps 1 through 8 are complete. Step 9 is in progress through pull request #219.
