# Slice 03 Consolidation

Workflow ID: `workflow-traefik-service-routing-20260627`
Slice ID: `03`
Slice title: Service Access Links, Evidence And Live Suite Structure

Stream results:

- Service Access dashboard preferred URLs now use `https://*.tsw.local`
  route hostnames.
- Service Access dashboard joins `traefik_ingress` and exposes
  `service-access.tsw.local` through Traefik labels.
- Swagger, Pulsar Manager and Pulsar Admin API now have host-based Traefik
  labels on internal HTTP target ports.
- Live-suite static tests parse routed hostnames and keep live tests skipped
  without explicit opt-in.
- New integration tests verify preferred links, route labels and redacted
  evidence shape.

Accepted findings:

- Pulsar Manager GUI and Pulsar Admin API are HTTP routes.
- Pulsar broker remains TCP and is not routed as normal HTTP.
- RabbitMQ routes are not generated.

Rejected findings:

- Direct localhost links as preferred dashboard links were rejected.

Files changed per stream:

- `infra/config/compose/service-access/dashboard/index.html`
- `infra/config/compose/service-access/docker-compose.yml`
- `infra/config/compose/swagger/docker-compose.yml`
- `infra/config/compose/pulsar/docker-compose.yml`
- `tests/integration/test_service_access_routing.py`
- `tests/live/test_post_install_browser_live.py`
- related compose tests

Conflicts found:

- Existing live static tests only recognized localhost URLs.

Conflicts resolved:

- Parser now accepts routed `.tsw.local` hosts for static link checks.

Tests executed:

- Targeted WSL test bundle: 125 tests, 8 skipped, passed.
- Full quality gate later passed.

SonarQube findings and fixes:

- Not run locally.

Documentation updates:

- Deferred to Slice 04.

Final integration decision:

- Accepted.
