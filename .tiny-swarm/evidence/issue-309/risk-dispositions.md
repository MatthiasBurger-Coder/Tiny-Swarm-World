# RC1-R08 Risk Dispositions

Decision owner: RC1 integration owner under existing user approval for an isolated
internal test system. Requirement, architecture and QA review use the explicit
root-AGENTS sequential fallback after real-agent limits; no independent human or
new agent approval is invented. Reviewed 2026-09-13 for c921e695 only.

| Risk / finding | Severity and concrete effect | Disposition and evidence | Owner / review condition |
|---|---|---|---|
| Custom Dockerfiles DS-0002 | HIGH scanner finding: unnecessary root process in custom images. | Corrected and rescanned; three Dockerfiles have no HIGH/CRITICAL configuration findings; live custom users nginx/jenkins and full startup observed. | Supply-chain owner; rescan on Dockerfile/base-image changes. |
| Administrative Docker socket capability | HIGH impact if Portainer/agent/Traefik is compromised: Docker control remains powerful; a read-only mount is not API authorization. | Accepted residual only for the isolated internal-test profile. Root socket connects, nobody is denied, dashboard has no socket, anonymous agent inventory returns 403 with 204 ping positive control. No blanket privileged-admin isolation claim. | Security Architecture Owner / RC1 integration owner; review before wider exposure or socket/integration changes. |
| Mutable version tags | MEDIUM reproducibility risk: upstream or local tags can move. | Accepted for this test candidate with every observed running image ID and resolved repository digest captured separately for each host. No universal future tag reproducibility claim. | Release/Supply-chain owner; recapture after rebuild, pull or dependency changes. |
| Deterministic internal-test credentials and direct/routed admin ports | HIGH impact outside intended isolated test context. | Intentional bounded profile, existing protected override contract and complete positive/invalid authentication tests. No credential values/fingerprints are published. Direct and routed service access remains intentionally available. | Operator / Security Architecture Owner; review before shared/public/production exposure or credential-contract changes. |
| Built-image dependency vulnerability coverage | Unassessed beyond locked Python dependency and required Dockerfile configuration scans. | Explicit scope limitation, not a clean-image claim. Existing issue scope requests dependency/SBOM/container-config checks; all were executed with observed results. | Supply-chain owner; require a separate image-vulnerability assessment before a broader production/security claim. |
| Internal agent TLS identity | Outside this authorization probe: self-signed endpoint identity not checked by the 403 test. | Accepted probe limitation; it proves endpoint authorization only. Normal canonical service-route HTTPS checks are separate. | Security Architecture Owner; review for remote/untrusted-network agent communication. |

No applicable unresolved release-blocking finding remains within these declared
checks. Final R06 review must retain these conditions rather than describing the
system as universally hardened or vulnerability-free.
