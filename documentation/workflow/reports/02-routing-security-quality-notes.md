# Routing, Security, And Quality Notes

## Routing Decision

Default routing direction:

```text
NGINX_FIRST
```

Rationale:

- Existing Swagger/NGINX assets use `nginx:mainline-alpine` with mounted
  config.
- No Traefik configuration, labels, provider wiring, or tests are present.
- Introducing Traefik would add routing architecture, labels, provider, TLS,
  dashboard exposure, and security decisions that need ADR coverage.

Portainer preference:

- Portainer should manage post-bootstrap stack create/update when it is
  reachable.
- Portainer is not the HTTP router.
- Portainer must not be made a prerequisite for bootstrapping Portainer.

Port issue:

- Swagger/NGINX currently publishes port `80`.
- Service access must either share ingress deliberately or use a
  non-conflicting published port.
- A compose file must not silently publish a second service on port `80`.

## Credential Safety

Allowed:

- Vaultwarden as credential store.
- Password reveal/copy through Vaultwarden's authenticated UI.
- Dashboard labels for credential names.
- Dashboard links or references to Vaultwarden items.
- Required secret names such as `TSW_VAULTWARDEN_ADMIN_TOKEN`.

Forbidden:

- Raw password display outside Vaultwarden's authenticated UI.
- Static passwords in compose files.
- Vaultwarden admin token defaults in committed files.
- Credential-bearing URLs.
- Raw command output or environment payloads in evidence.
- Local host IPs, local paths, or user names in committed configuration.

## Quality Boundary

Default checks must not run:

- `multipass`
- `docker stack deploy`
- compose deployments
- Docker image build/login/push
- netplan changes
- `socat`
- Portainer HTTP calls
- Vaultwarden bootstrap
- NGINX or Traefik containers
- `setup run --live`

Use fakes, static YAML inspection, and repository quality gates instead.
