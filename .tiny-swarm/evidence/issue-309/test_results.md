# RC1-R08 Test Results

R04 records actual candidate-matched pip-audit 2.10.1 dependency audit (13 locked
packages, no known reported vulnerabilities), CycloneDX 1.4 SBOM and Trivy 0.74.0
container-configuration scan (three Dockerfiles, 60 successful checks, zero
HIGH/CRITICAL findings). Tool image digests, input checksums and actual dates are
in [R04 provenance](../issue-300/candidate-c921e695/provenance.json).

Live snapshot timestamps: WSL 20260913T004035, native 20260913T004502, both c921.
Each follows a complete successful authenticated reboot suite and records:

- All 20 running task image IDs and resolved digests on that host.
- Worker-to-manager Docker TCP 2375/2376 refused; expected Swarm 2377 connected.
- Direct database/cache 5432/6379 refused from the worker vantage point.
- Root Docker socket access succeeds; nobody UID 65534 receives permission denied.
- Unprivileged dashboard has no socket mount.
- Internal Portainer agent ping returns 204; anonymous container inventory returns 403.

These eight checks pass on both hosts. Full canonical direct/routed service
readiness/browser/API acceptance is recorded in R01/R02/R03/R05, including seven
successful authentications with invalid-credential rejection. Internal agent TLS
identity is explicitly not part of the authorization-only probe. A few refused
ports do not establish blanket LAN or overlay isolation.

Validation for this evidence-only change: JSON result/digest assertions, artifact
checksums, redaction/link/diff and verification-policy checks. Full candidate quality
(2066 tests, 18 declared live/optional skips) is reused under QUALITY.md because no
product input changes; no duplicate full-suite execution is claimed. Exact-head
hosted quality/compatibility/Sonar must pass before merge.
