# Live Greenpath Repair Loop 2026-06-06

## Scope

Branch: `feature/live-greenpath-repair-loop-20260606`

Goal: execute a controlled live repair loop for `bash install.sh --confirm-reset`
on the local WSL2 LXD/LXC-native Docker Swarm setup without bypassing safety
guards, disabling validations, using Ansible, or committing local evidence or
secrets.

## Evidence

Live installation evidence is stored under:

```text
.tiny-swarm-world/evidence/installation-tests/wsl2
```

Most recent run inspected:

```text
.tiny-swarm-world/evidence/installation-tests/wsl2/20260608T181239Z
```

That run completed reset, preflight, platform init, platform reconcile,
platform expose, deployment bootstrap, artifacts prepare, and artifacts verify.
It stopped during deployment apply.

## Blockers And Fixes

1. `deployment:infisical-bootstrap` failed with TLS/HTTP readiness ambiguity.
   Fix: added bounded Infisical API readiness polling before bootstrap and
   precise `deployment_apply_failed` evidence fields for unavailable bootstrap
   API responses. Commit: `28cc209`.

2. `deployment:infisical-bootstrap` failed because Service Access and Infisical
   were isolated on stack-scoped overlay networks. Fix: made
   `service_access_link` an explicit external overlay network shared by both
   stacks and added runtime creation for direct Swarm deployment. Commit:
   `06fa382`.

3. `deployment:infisical-stack` failed when Portainer deployment referenced the
   external overlay network before it existed. Fix: made the Portainer stack
   adapter create required external attachable overlay networks idempotently
   before stack create/update. Commit: `6527e51`.

4. `deployment:infisical-bootstrap` still failed after the network fix because
   Infisical first-start migrations exceeded the previous bounded readiness
   window. Fix: added explicit operator-configurable Infisical readiness
   settings with safe validation and a longer local default:
   `TSW_INFISICAL_READINESS_ATTEMPTS` defaults to `180` and
   `TSW_INFISICAL_READINESS_INTERVAL_SECONDS` defaults to `5.0`. Commit:
   `7672e43`.

## Stop Condition

The next live run again surfaced `deployment:infisical-bootstrap` as the visible
failure, but read-only diagnosis showed a different underlying host/provider
blocker: Docker tasks for Infisical dependencies were rejected because public
images could not be pulled from Docker Hub.

Observed pull failure from inside `swarm-manager`:

```text
Error response from daemon: error from registry: You have reached your
unauthenticated pull rate limit.
```

Affected public images observed in rejected Swarm tasks:

```text
infisical/infisical:latest
postgres:14-alpine
redis:7-alpine
```

The loop stopped here because continuing safely requires operator-provided
registry configuration, authenticated Docker Hub access, or an approved
provider-level image mirror/cache. Adding credentials, changing host registry
policy, or selecting a third-party mirror implicitly would violate the
workflow's no-manual-secrets and no-unknown-host-changes stop conditions.

## Verification Run

Targeted verification run for the latest code fix:

```text
PYTHONPATH=src python3 -m unittest \
  tests.infrastructure.test_composition \
  tests.infrastructure.adapters.clients.test_infisical_bootstrap_http_client
```

Result: passed.

Whitespace verification:

```text
git diff --check -- \
  src/tiny_swarm_world/infrastructure/composition.py \
  tests/infrastructure/test_composition.py
```

Result: passed.

## Current Status

The full greenpath is not complete. The active blocker is external registry
rate limiting for public images during deployment apply.

Safe next repair options require explicit operator configuration, for example:

1. Provide authenticated registry access through documented local environment
   configuration.
2. Configure an approved Docker registry mirror through provider configuration.
3. Pre-seed an approved local registry/cache as an idempotent provider setup
   step.

