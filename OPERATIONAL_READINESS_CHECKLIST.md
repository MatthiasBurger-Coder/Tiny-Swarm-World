# OPERATIONAL_READINESS_CHECKLIST

Record the target, selected profile, executed revision, evidence and reviewer
for each applicable item. An unchecked box is not a pass. Use the
[installation guide](documentation/user_guide/installation.adoc) for procedures
and the [verification-state policy](documentation/process/verification-state-policy.md)
for local, live and external classifications.

## Host environment readiness
- [ ] Host OS and version documented.
- [ ] Python version meets project requirement.
- [ ] Incus installed, initialized, and accessible for the default
      `lxc_native` provider.
- [ ] Docker CLI/Engine installed on the host only when needed for local
      diagnostics or explicit legacy/service checks.
- [ ] WSL2 status verified when on Windows.
- [ ] Native `service-access` host has at least eight CPU threads, 15 GiB RAM
      and 150 GiB free disk; WSL2 retains a 16 GiB profile RAM floor.
- [ ] `default` host has at least four CPU threads, 16 GiB RAM and 60 GiB free disk.
- [ ] Managed-node capacity is checked separately. Default nodes total 19 GiB;
      Windows capacity planning includes 2 GiB WSL overhead and Windows reserve.
      See [resource planning](documentation/user_guide/windows-preparation.md).

## Python environment readiness
- [ ] Virtual environment creation documented.
- [ ] Dependencies installed from canonical file.
- [ ] Canonical entrypoint runs from repo root.
- [ ] `python3 tools/quality_gate.py quality` runs as the authoritative
      default quality gate.

## LXC-native provider readiness
- [ ] Backend selection is `incus`.
- [ ] `incus info` works from the same shell that runs setup.
- [ ] Docker-in-container profile requirements are verified before mutation.

## Provider node readiness
- [ ] Manager and worker creation verified.
- [ ] Node address discovery validated without persisting local IPs as trusted
      repository evidence.
- [ ] Re-run behavior verified.

## Network readiness
- [ ] Incus bridge `incusbr0` exists and is usable by managed nodes.
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
- [ ] Every required stack in the selected profile deploys and passes its
      observed readiness checks; a subset does not qualify the full profile.

## Portainer readiness
- [ ] Portainer UI reachable from host.
- [ ] Admin initialization flow secured and documented.

## Supporting service accessibility
- [ ] Nexus reachable.
- [ ] Jenkins reachable.
- [ ] Pulsar broker reachable on port `6650` and Pulsar Admin API reachable on port `8087`.
- [ ] SonarQube reachable.
- [ ] Swagger/NGINX reachable.
- [ ] Infisical, Service Access and Traefik routes verified where selected.
- [ ] Required service logins and token-authenticated API checks pass;
      a reachable login page alone does not prove authentication.
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
- [ ] Mutating product CLI workflows require `--live` and interactive approval
      or the explicit `--approve-live` flag.
- [ ] Installer automation uses `--non-interactive-live-approval`. Only WSL2
      fresh-reset automation also uses `--confirm-reset`; native installation
      reconciles without reset. Other destructive CLI operations require their
      exact confirmation phrase separately.
- [ ] `tools/live/run_classic_acceptance.py` requires `--approve-live`, protected
      operator inputs and an explicitly owned authorized target.
- [ ] Preparation stages have their own consent; preparation approval does
      not authorize installation or qualify live services.
- [ ] Missing consent produces `REFUSED_LIVE_CONSENT_MISSING` before any
      mutating product workflow is constructed. The Classic runner separately
      records `LIVE_CONSENT_MISSING` when its approval is absent.

## Evidence and secret readiness
- [ ] Installer evidence uses the printed protected directory under
      `${XDG_STATE_HOME:-$HOME/.local/state}/tiny-swarm-world/evidence/installation-tests/<host-runtime>/<run-id>/`.
- [ ] Classic acceptance evidence uses the protected `live-greenpath/<run-id>/`
      directory under the same XDG application evidence root. An explicit
      `TSW_LIVE_EVIDENCE_ROOT` selects the root for the invoked entrypoint.
- [ ] Evidence root is ignored by Git before live evidence is written.
- [ ] Evidence bundle includes manifest, summary, preflight, consent/refusal,
      phase results, command results, probes, redaction report and checksums.
- [ ] Evidence redacts secrets, tokens, join tokens, URLs with credentials,
      HTTP authorization headers and service bootstrap credentials.
- [ ] Real operator secrets use approved protected inputs; the standard
      internal-test installer may resolve disposable public catalog defaults.
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
