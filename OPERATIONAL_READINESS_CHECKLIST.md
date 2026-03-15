# OPERATIONAL_READINESS_CHECKLIST

## Host environment readiness
- [ ] Host OS and version documented.
- [ ] Python version meets project requirement.
- [ ] Multipass installed and accessible.
- [ ] Docker CLI/Engine installed and accessible.
- [ ] WSL2 status verified when on Windows.

## Python environment readiness
- [ ] Virtual environment creation documented.
- [ ] Dependencies installed from canonical file.
- [ ] Canonical entrypoint runs from repo root.

## Multipass readiness
- [ ] VM definitions validated against config schema.
- [ ] Provisioning is idempotent (no implicit destructive reset).
- [ ] VM state checks and recovery logic documented.

## VM provisioning readiness
- [ ] Manager and worker creation verified.
- [ ] VM IP discovery validated.
- [ ] Re-run behavior verified.

## Network readiness
- [ ] Netplan file generation path deterministic.
- [ ] Netplan transfer/apply checks pass.
- [ ] WSL2 forwarding procedure verified and reversible.

## Docker readiness
- [ ] Docker installed on all VMs.
- [ ] Docker daemon active (`docker info`) on all nodes.
- [ ] Group/permission model documented.

## Swarm readiness
- [ ] Manager initialized or detected as active.
- [ ] Worker join token retrieval validated.
- [ ] Workers joined and visible in `docker node ls`.

## Compose/stack deployment readiness
- [ ] Swarm-compatible stack files validated.
- [ ] At least Portainer stack deploys successfully.
- [ ] One additional service stack deploys successfully.

## Portainer readiness
- [ ] Portainer UI reachable from host.
- [ ] Admin initialization flow secured and documented.

## Supporting service accessibility
- [ ] Nexus reachable.
- [ ] Jenkins reachable.
- [ ] RabbitMQ reachable.
- [ ] SonarQube reachable.
- [ ] Swagger/NGINX reachable.

## Test readiness
- [ ] `pytest` runs from repo root without manual PYTHONPATH edits.
- [ ] Critical orchestration units have active tests.

## Smoke test readiness
- [ ] Cluster bootstrap smoke test passes.
- [ ] Service reachability smoke test passes.

## Logging/observability readiness
- [ ] Orchestrator logs clearly indicate phase success/failure.
- [ ] Failure exit codes are non-zero and actionable.

## Documentation completeness
- [ ] README includes canonical end-to-end runbook.
- [ ] User/system/deployment docs align with implementation.
- [ ] Troubleshooting includes known failure modes and recovery.
