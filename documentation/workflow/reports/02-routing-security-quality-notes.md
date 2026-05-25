# Routing, Security, And Quality Notes

## Routing Decision

Accepted routing decision:

```text
SERVICE_ACCESS_CENTRAL_NGINX
```

Rationale:

- Existing Swagger/NGINX assets use `nginx:mainline-alpine` with mounted
  config.
- The service-access dashboard is the installed landing page and must be
  reachable at `http://localhost` after the full setup applies the updated
  stack.
- No Traefik configuration, labels, provider wiring, or tests are present.
- Introducing Traefik would add routing architecture, labels, provider, TLS,
  dashboard exposure, and security decisions that need ADR coverage.

Portainer preference:

- Portainer should manage post-bootstrap stack create/update when it is
  reachable.
- Portainer is not the HTTP router.
- Portainer must not be made a prerequisite for bootstrapping Portainer.

Port decision:

- Service access owns the central NGINX ingress and publishes port `80`.
- The service-access dashboard route is `http://localhost`.
- The Vaultwarden route uses published port `8086`.
- Swagger/NGINX no longer owns host port `80`; its proxy endpoint publishes
  `8084`.
- Service shortcut routes such as `/jenkins`, `/nexus`, `/portainer`,
  `/rabbitmq`, `/sonarqube`, `/swagger` and `/vaultwarden` are owned by
  service-access NGINX.
- The setup preflight allows legacy local listeners for old Swagger `80` and
  old Swagger API `8084` when the same live run will reassign those routes.
- Traefik, TLS automation and wider-than-local exposure remain behind later
  ADR and test scope.
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
