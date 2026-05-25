# Routing, Security, And Quality Notes

## Routing Decision

Accepted routing decision:

```text
NGINX_FIRST_DEDICATED_PORT
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

Port decision:

- Swagger/NGINX currently publishes port `80`.
- Swagger/NGINX keeps published port `80`.
- Service access owns a dedicated NGINX ingress.
- The service-access dashboard route uses published port `8085`.
- The Vaultwarden route uses published port `8086`.
- Shared ingress is deferred until a later ADR defines route ownership,
  Swagger migration, tests, and rollback.
- A compose file must not silently publish another service on port `80`.

Asset decision:

- For the Portainer-managed path, service-access dashboard and NGINX assets
  must be image-packaged or image-native.
- Bind-mounted repository files are not accepted unless a later slice adds a
  tested asset-preparation port or adapter.

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
