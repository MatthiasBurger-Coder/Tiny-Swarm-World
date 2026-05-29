# OPERATIONAL_READINESS_CHECKLIST

## Host environment readiness
- [ ] Host OS and version documented.
- [ ] Python version meets project requirement.
- [ ] LXD or Incus installed, initialized, and accessible for the default
      `lxc_native` provider.
- [ ] Multipass installed and accessible only when validating explicit
      `--node-provider multipass_legacy`.
- [ ] Docker CLI/Engine installed on the host only when needed for local
      diagnostics or explicit legacy/service checks.
- [ ] WSL2 status verified when on Windows.
- [ ] Full-run resources meet the integration contract: 4 vCPU, 16 GiB RAM,
      and 60 GiB free disk available to the Linux/WSL target.

## Python environment readiness
- [ ] Virtual environment creation documented.
- [ ] Dependencies installed from canonical file.
- [ ] Canonical entrypoint runs from repo root.
- [ ] `python3 tools/quality_gate.py quality` runs as the authoritative
      default quality gate.

## LXC-native provider readiness
- [ ] Backend selection is unambiguous or explicitly set with `--lxc-backend`.
- [ ] `lxc info` or `incus info` works from the same shell that runs setup.
- [ ] Docker-in-container profile requirements are verified before mutation.

## Multipass legacy readiness
- [ ] VM definitions validated against config schema when
      `--node-provider multipass_legacy` is selected.
- [ ] Provisioning is idempotent (no implicit destructive reset).
- [ ] VM state checks and recovery logic documented.

## Provider node readiness
- [ ] Manager and worker creation verified.
- [ ] Node address discovery validated without persisting local IPs as trusted
      repository evidence.
- [ ] Re-run behavior verified.

## Network readiness
- [ ] Netplan file generation path deterministic.
- [ ] Netplan transfer/apply checks pass.
- [ ] WSL2 forwarding procedure verified and reversible.

## Docker readiness
- [ ] Docker installed or detected inside all selected provider nodes.
- [ ] Docker daemon active (`docker info`) inside all nodes.
- [ ] Group/permission model documented.

## Swarm readiness
- [ ] Manager initialized or detected as active.
- [ ] Worker join token retrieval validated without persisting the token.
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
- [ ] Any resource-gated service omission has Three Amigos approval and is
      recorded as `PASS_WITH_RESOURCE_GATES`, not `PASS`.

## Test readiness
- [ ] `python3 tools/quality_gate.py quality` passes from the repository root.
- [ ] Optional `pytest` compatibility, if introduced later, is documented as
      secondary and does not replace `tools/quality_gate.py`.
- [ ] Critical orchestration units have active tests.

## Smoke test readiness
- [ ] Cluster bootstrap smoke test passes.
- [ ] Service reachability smoke test passes.

## Live consent readiness
- [ ] Live runner requires `--live`.
- [ ] Live runner requires
      `TSW_LIVE_INFRASTRUCTURE_CONSENT=I_UNDERSTAND_THIS_CHANGES_LOCAL_INFRASTRUCTURE`.
- [ ] Live runner requires the interactive phrase
      `RUN TINY SWARM WORLD LIVE INSTALLATION`.
- [ ] Non-interactive live execution is refused until a future workflow defines
      a separate consent contract.
- [ ] Missing consent produces `REFUSED_LIVE_CONSENT_MISSING` before any
      Multipass, Docker Swarm, netplan, socat, compose/stack or bootstrap
      command runs.

## Evidence and secret readiness
- [ ] Evidence path is `.tiny-swarm-world/evidence/live-installation/<run-id>/`.
- [ ] Evidence root is ignored by Git before live evidence is written.
- [ ] Evidence bundle includes manifest, summary, preflight, consent/refusal,
      phase results, command results, probes, redaction report and checksums.
- [ ] Evidence redacts secrets, tokens, join tokens, URLs with credentials,
      HTTP authorization headers and service bootstrap credentials.
- [ ] Secrets come only from environment variables or ignored local files.
- [ ] Missing secrets fail during preflight before stack deployment.

## Logging/observability readiness
- [ ] Orchestrator logs clearly indicate phase success/failure.
- [ ] Failure exit codes are non-zero and actionable.
- [ ] Failure reports classify blockers as host prerequisite, configuration,
      secret, deterministic defect, flaky readiness, architecture ambiguity,
      product-scope ambiguity or resource limitation.

## Documentation completeness
- [ ] README includes canonical end-to-end runbook.
- [ ] User/system/deployment docs align with implementation.
- [ ] Troubleshooting includes known failure modes and recovery.
