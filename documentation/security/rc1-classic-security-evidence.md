# Classic RC1 Security Evidence Procedure

This procedure qualifies the internal-test Classic profile at a declared
candidate SHA. It records image references, administrative surfaces, socket
mounts, network/port contracts, credential boundaries and scan outcomes
without storing secret values or fingerprints.

## Static inventory

| Area | Current contract | Evidence source |
|---|---|---|
| Image references | Compose service images and approved overrides; immutable digest where configured | infra/config/compose and services.yml |
| Python dependencies | requirements.lock | requirements.lock |
| Admin surfaces | Portainer, Nexus, Jenkins, SonarQube, Pulsar Manager, Infisical and Service Access routes | infra/config/ports.yaml and services.yml |
| Docker socket | Portainer and agent mount the socket; Traefik uses a read-only socket mount | compose files for portainer and traefik |
| Credential source | Operator overrides or internal-test catalog/Infisical contracts | arc42 credential contracts and secret manifest |
| Reachability | Published ports and routed hostnames are profile-specific | ports.yaml and access-model evidence |

A read-only socket mount does not provide Docker API authorization. The
socket and administrative surfaces therefore remain explicit residual risks
for the isolated internal-test profile.

## Reproducible checks

Run from the candidate checkout:

    python3 tools/security_gate.py dependencies
    python3 tools/security_gate.py sbom
    python3 tools/security_gate.py container-config

Record tool versions, candidate SHA, date, result and redacted output location.
The first two checks are local prerequisites; the container-config check
requires Trivy. Missing tools and scans are non-success states.

## Disposition rules

Applicable release-blocking findings require a focused correction and a
candidate-matched rescan. Internal-test-only deterministic credentials may be
retained only with their non-production scope and override boundary recorded.
No scanner rule is disabled and no external scanner is added to the default
quality gate by this procedure.


## Candidate c921e695 observations (2026-09-13)

The [candidate inventory](../../.tiny-swarm/evidence/issue-309/candidate-c921e695/image-inventory.json)
contains each actual running task's host/node/service, image ID, resolved digest,
user, socket mounts and network names. The paired native/WSL snapshots were taken
after complete authenticated reboot acceptance. This records retained version tags
at observation time; it does not pin every future deployment automatically.

For a repeat authorized release check, qualify the target and exact source revision,
execute the existing three security_gate commands above, and capture only selected
fields from managed-node Docker service/task/image inspection. Never publish raw
container inspection, environment, credentials or credential fingerprints. Compare
root/unprivileged socket access, intended worker-to-manager ports and an anonymous
agent administrative request against a reachable positive control; retain source,
time, exit/status and the specific network vantage point. Run the canonical complete
authenticated suite separately for actual direct/routed service access.

The required Trivy gate here scans container configuration, not all packages inside
built images. A missing applicable check remains non-pass. The current [reviewed
residuals](../../.tiny-swarm/evidence/issue-309/risk-dispositions.md) include powerful
admin sockets, retained tags and the intentionally isolated credential/exposure
scope. No production-hardening, blanket network isolation or vulnerability-free
image claim follows from these checks. Reassess on input, exposure or scope changes.
