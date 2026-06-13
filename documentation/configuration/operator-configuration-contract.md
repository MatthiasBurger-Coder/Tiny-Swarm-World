# Operator Configuration Contract

Workflow: `config-contract-validation-issue-24-20260613`

Tiny Swarm World validates operator-facing `TSW_*` configuration before setup
execution. The committed template is `.env.example`; local secret-bearing
values belong in `.tiny-swarm-world/local/live-installation.env` or in the
process environment.

## Source Precedence

Configuration sources are loaded in this order:

1. `.tiny-swarm-world/local/live-installation.env`
2. process environment variables

Later sources override earlier sources. The local env file is operator-owned,
ignored by Git, and must not be committed. The parser accepts simple
`KEY=value` and `export KEY=value` assignments, ignores non-`TSW_*` keys, and
fails closed on duplicate `TSW_*` keys or unsupported shell syntax.

## Required Values

The default contract requires these keys before setup execution:

| Key | Kind | Scope |
|---|---|---|
| `TSW_PORTAINER_ADMIN_PASSWORD` | secret value | Portainer |
| `TSW_NEXUS_ADMIN_PASSWORD` | secret value | Nexus |
| `TSW_JENKINS_ADMIN_PASSWORD` | secret value | Jenkins |
| `TSW_RABBITMQ_PASSWORD` | secret value | RabbitMQ |
| `TSW_SONARQUBE_ADMIN_PASSWORD` | secret value | SonarQube |
| `TSW_POSTGRES_PASSWORD` | secret value | SonarQube |
| `TSW_SONARQUBE_POSTGRES_PASSWORD` | secret value | SonarQube |
| `TSW_INFISICAL_LOGIN_EMAIL` | text | Infisical |
| `TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD` | secret value | Infisical |
| `TSW_INFISICAL_ENCRYPTION_KEY` | secret value | Infisical |
| `TSW_INFISICAL_AUTH_SECRET` | secret value | Infisical |
| `TSW_INFISICAL_POSTGRES_PASSWORD` | secret value | Infisical |
| `TSW_INFISICAL_REDIS_PASSWORD` | secret value | Infisical |

## Optional Overrides

| Key | Default | Kind | Purpose |
|---|---|---|---|
| `TSW_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS` | `180` | positive integer | Portainer stack request timeout in seconds. |
| `TSW_SEED_INFISICAL_ITEMS` | `0` | boolean flag | Enables optional legacy Infisical item seeding. |
| `TSW_LXC_DOCKER_REGISTRY_MIRROR` | unset | URL | Docker registry mirror reachable from managed LXC nodes. |
| `TSW_TRAEFIK_TLS_CERT_SECRET_NAME` | `tsw_traefik_tls_cert` | secret name | External Docker secret name for Traefik TLS certificate material. |
| `TSW_TRAEFIK_TLS_KEY_SECRET_NAME` | `tsw_traefik_tls_key` | secret name | External Docker secret name for Traefik TLS private key material. |

## Redaction

Preflight reports configuration status, key names, scopes, value kinds,
requiredness, and source classification only. It does not report raw secret
values, full environment payloads, or local file contents. Parser failures are
reported as configuration source errors without echoing the rejected line.
