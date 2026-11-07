# W09 generic component transition proposal

Status: implementation candidate; historical bounded native single, batch, recovery and persistence runs were executed against the earlier transition-module hash recorded below. The current source candidate was not run live, so these targets remain non-executable `candidate-transition` entries until exact-source live qualification is complete. The later [qualification matrix](lcm-w09-qualification.md) is authoritative for historical WSL scenario results: bounded WSL transition scenarios have evidence, while exact Q07–Q10 operation-to-artifact attribution, remaining variants and aggregate #449 acceptance remain open.

The historical live source identity recorded for `component_transitions.py` is
SHA-256 `5648db46fcb5159e6279d1d6dd3ebf6da0bb905a5e9e61cd5074e1a35cd80246`.
The current source snapshot has a different hash and was not run live in this
publication. Its current SHA-256 is
`0437fd613ada57f71fae2f2829275214ad8a12a2cbd553a2f85686ef0ff63c9a`.
Historical results are retained as historical evidence; they do
not establish live qualification for the current source snapshot. No new live
evidence is claimed, and #449 remains incomplete.
Operator requested transition proposals for review on 2026-10-24.
Use the existing NativeComponentCatalog, ComponentUpdateTransition and #297-backed
executor; candidate targets remain excluded by planning until exact-source live
qualification promotes them. No alternate catalog, orchestrator or arbitrary-tag CLI is proposed.
Independent architecture review found that the original baseline lacked Classic
image override mappings. Consequently this is a catalog **and bounded adapter
extension** proposal; the earlier baseline rejected Swagger before mutation.

## Bounded candidates

| Service | Source → target | Proposed target ID | Changed bundle member |
|---|---|---|---|
| traefik | v3.7.4 → v3.7.5 | traefik-3-7-5 | traefik |
| swagger | UI v5.32.6 → v5.32.7 | swagger-ui-5-32-7 | swagger-ui; retain editor/API/NGINX identities |

Both source tags match current native assets. Proposed scope is x86_64 Classic
on native Linux and WSL2, default/service-access presets, only when the selected
services are already installed with matching immutable desired/observed sources.
Single: swagger. Batch: explicit `swagger,traefik`; dependencies remain installed
and are not updated implicitly. A selection without Traefik cannot run that batch.
Other generic stack-service transitions remain unadmitted; Portainer retains its separate W07 lifecycle.

Official release existence and changes checked at
[Traefik v3.7.5](https://github.com/traefik/traefik/releases/tag/v3.7.5) and
[Swagger UI v5.32.7](https://github.com/swagger-api/swagger-ui/releases/tag/v5.32.7).
These patch releases are candidates, not a vendor guarantee of TSW compatibility.
Traefik release notes include security fixes; do not expose an isolated source
baseline more broadly or infer that this proposal is a complete security update.

## Immutable bundle pins

Read-only anonymous Docker Registry v2 resolution ran on the native target at
2026-10-24T13:35:00Z–13:35:05Z. Original terminal-transcribed values were invalid:
PTY wrapping duplicated characters in eleven digest cells. Those values are
superseded by the corrected table below, independently re-resolved and verified
from raw HTTPS bytes by Security Reviewer at 2026-10-24T13:49:42Z. All seven
config objects independently prove linux/amd64. No string was guessed or trimmed.
Each response's Docker-Content-Digest was checked
against SHA-256 of its actual manifest bytes. Multiarch index identity and its
linux/amd64 child are distinct. The current observer compares digest strings
strictly and performs no index-to-child normalization. Propose the linux/amd64
child identities below as actual source/target pins for this x86_64 campaign.
Before admission prove both service and task observations use the same child
identity. Preserve strict equality; do not add a loose tag/index fallback.

| Repository / tag | Manifest/index SHA-256 | linux/amd64 child SHA-256 |
|---|---|---|
| traefik:v3.7.4 | fcdef599e6259359833dd2e1d49f9e964f66825d69bd3dd468f51102ce013d03 | 580f70e21a5b63503dcbd5690b432b0e78b056e931a1738a5ca2d997bd08bc47 |
| traefik:v3.7.5 | e4d98158c01ad752fc1071d4e9573788747230d902cdde00a772516e692d07c9 | e5491c6c7073c18a2fa8ae48196630d64894b41d877aca1babe4a3ad98bd5cba |
| swaggerapi/swagger-ui:v5.32.6 | 135a9ced4005a947bbb1757bc509309d88519d985aa0f5616f4fdfab1eba6ff6 | 9f5fb4ffc28ad30a01e7fd936203d69e21dcfc8cb565145fc85c11976776cfd2 |
| swaggerapi/swagger-ui:v5.32.7 | d00080cdd83b77241a65f89eb5d3af000c1bd1bd4b0d1ee78cb5ad8b0b549563 | b96d57e3c8c658b2c83ce11e0d87a7ccc7aedcdc20eccd7e83d67dca857a5a27 |
| swaggerapi/swagger-editor:v5.6.2-unprivileged (unchanged) | 12ea42bbfb9e3ef2d3d0cf56d527feed3287970539c5abf4e9911fc97550fd7e | 337d8cf1d92c803bb7a1b47e6953cf21d8cce0da1c7959dc1eed3ebc7745c50a |
| nginx:1.29.8-alpine (unchanged) | 5616878291a2eed594aee8db4dade5878cf7edcb475e59193904b198d9b830de | 3bcf852aed06467cf075c6105892e4d5a6ebbbafa0ce22d35062db9e90ddef4c |
| danielgtaylor/apisprout (unchanged) | 6c07143937e57095d8478efc8ab7eab52b44e67c7673285f8c0a2bf4a7b137ad | Same single manifest; config proves linux/amd64 |

Every value is prefixed `sha256:` when represented as VersionIdentity.image_digest.
No token, registry authorization header or credential-derived digest is retained.
API config blob `sha256:5525e5a317bebdfa056721e6870ccc90eb5dc1bedfc7be82a1c0eec60bd91d77`
was fetched read-only and its content hash verified; its os/architecture are
linux/amd64. No config environment or other sensitive content was printed.
Before admission independently re-resolve pins and validate platform/config identity.
This proposal does not authorize a mixed bundle
or an unknown observed source. Existing mutable baseline manifests may require
reviewed explicit inventory/adoption; do not fabricate observed digest fields.

## Implemented policy and continuing qualification checks

- Implemented four entries to the existing domain Classic override map and wrap
  the matching current Swagger Compose image defaults in the existing environment
  override syntax: `swagger:swagger-editor` → `TSW_SWAGGER_EDITOR_IMAGE`,
  `swagger:swagger-ui` → `TSW_SWAGGER_UI_IMAGE`, `swagger:swagger-api` →
  `TSW_SWAGGER_API_IMAGE`, `swagger:swagger-nginx` → `TSW_SWAGGER_NGINX_IMAGE`.
  Extended `IMAGE_OVERRIDE_ENVIRONMENT_BY_CONTEXT` in the existing Compose repository
  adapter with the same four context names and variables. Desired-image persistence
  uses that second map as well. Preserve all existing image defaults. The runtime validates unchanged bundle
  members too, so all four mappings are required. Trace propagation through
  deployment and desired-image persistence; do not bypass runtime validation.
- Implemented catalog/mapping scope: `domain/update/classic_update.py`, existing
  `infrastructure/adapters/lifecycle/catalog.py`,
  `infrastructure/adapters/repositories/compose_file_repository_yaml.py`,
  Swagger `docker-compose.yml`, their nearest regression tests, and related
  lifecycle/component guides and this evidence package. Confirm exact paths and
  locks before writes; any further behavioral change requires reviewed scope.
- Keep installed service, endpoint, route, config/secret and volume identities.
  Swagger's mounted OpenAPI/configuration and Traefik's TLS/dynamic configuration
  remain unchanged. No schema/data migrations proposed; verify this against actual
  release/config behavior. No automatic deletion, reset or credential rotation.
- One replica can become unavailable during rolling replacement. Record actual
  restart bounds and per-stage failure. Shared-host operations must be serialized.
- No application database backup requirement is proposed for these stateless image
  changes. Retain private configuration/secret references and a verified recoverable
  host baseline. Reverting the exact original image is not a persistent-data restore.
- Verify target images run under current ports/mounts/UID/config and native Classic
  image override mappings before policy entry. Check authenticated Traefik dashboard
  access, TLS/routing and upstream behavior; Swagger has no application login, so
  verify actual OpenAPI/UI/API response behavior and authenticated Portainer stack
  ownership. Explicitly record authentication applicability per surface.
- All four Swagger members need exact source and target pins even though only UI
  changes. Unchanged members must be freshly observed, not restarted unnecessarily.
  Single-manifest API image platform was checked; repeat verification during
  independent pin review before x86_64 admission.
- Implemented meaningful regression tests for real NativeComponentCatalog transition
  admission/rejection, complete bundle mapping, drift, desired-pin persistence,
  repeat no-op, mixed/old tasks, partial batch stop and original-plan recovery.
  Run focused and full QUALITY.md gates on the required SSH/WSL host.
- Qualify both hosts through actual CLI commands and Q07–Q11; inspect source and
  runtime before/after and prove later setup does not restore old desired pins.
  Required checks cannot be replaced with a synthetic catalog or login-page check.

Operator accepted implementation of these two candidates. Independent Security
Reviewer accepted the bounded stateless policy after raw pin corrections, with
live baseline/source/task/auth checks still required. Catalog and mappings are
implemented under R449-23–26; bounded native transitions and persistence checks
are independently accepted. Aggregate WSL qualification and remaining variants remain open, although bounded WSL transition scenarios have verified results. See the
[W09 qualification matrix](lcm-w09-qualification.md) for the wider still-open scope.
