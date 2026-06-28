# Operator Configuration Contract

Workflow: `config-contract-validation-issue-24-20260613`

Tiny Swarm World validates operator-facing `TSW_*` configuration before setup
execution. The committed template is `.env.example`; local secret-bearing
values belong in `.tiny-swarm-world/local/live-installation.env` or in the
process environment.

Secret synchronization is controlled by `TSW_SECRETS_MODE` or
`./install.sh --secrets-mode`. Supported modes are `generated`, `fixed`, and
`infisical`.

## Source Precedence

Configuration sources are loaded in this order:

1. `.tiny-swarm-world/local/live-installation.env`
2. process environment variables

Later sources override earlier sources. The local env file is operator-owned,
ignored by Git, and must not be committed. The parser accepts simple
`KEY=value` and `export KEY=value` assignments, ignores non-`TSW_*` keys, and
fails closed on duplicate `TSW_*` keys or unsupported shell syntax.

## Ownership And Lifecycle

| Value group | Owner | Storage | Lifecycle |
|---|---|---|---|
| Operator runtime secrets | Operator | `.tiny-swarm-world/local/live-installation.env` or process environment | Created before install, reused across reruns, edited or rotated by the operator. |
| Fixed local secrets | Operator | `.tiny-swarm-world/local/fixed-secrets.env` by default | Used only when `secrets.mode=fixed`; every required manifest key must exist and contain a non-empty value. |
| Generated local bootstrap secrets | Python installer | `.tiny-swarm-world/local/live-installation.env` | Generated only when missing and secret generation is enabled; existing values are kept. |
| Infisical bootstrap runtime file | Python installer | `.tiny-swarm/secrets/bootstrap.local.env` | Rewritten from the resolved local values for the self-hosted Infisical stack; ignored by Git. |
| Generated recovery file | Secret sync service | `.tiny-swarm/secrets/generated.local.env` | Stores generated values needed for idempotent Infisical sync or recovery; ignored by Git and mode `0600` when written by automation. |
| Infisical-managed values | Infisical sync service | Infisical project/environment | Synchronized from generated or operator-supplied local values; existing Infisical values are kept unless a manifest entry explicitly requests rotation. |
| External Docker secret names | Operator | `.tiny-swarm-world/local/live-installation.env`, process environment, or defaults | Names identify externally managed Docker secrets and are not secret material. |

The Python installer derives required local bootstrap values from
`infra/config/secrets/infisical-secrets.yaml`. Installer code must not keep a
separate required-secret list. Values whose manifest source is
`generated_local_secret` or `placeholder_only` and whose entry is required must
be present before live setup; missing generated values may be created locally
when secret generation is enabled. Values whose source is
`external_user_secret` identify external resources and are not generated as
secret values by the installer.

In `fixed` mode, the installer reads fixed values from
`TSW_FIXED_SECRET_ENV_FILE` or `.tiny-swarm-world/local/fixed-secrets.env`,
fails if the file is missing, fails if any required manifest key is missing or
empty, and passes the same mode to setup so the pre-deployment Infisical sync
writes those fixed values. Evidence records the mode, checked key names, and
synchronized key names only.

## Required Values

The default contract requires these keys before setup execution:

| Key | Kind | Scope |
|---|---|---|
| `TSW_PORTAINER_ADMIN_PASSWORD` | secret value | Portainer |
| `TSW_NEXUS_ADMIN_PASSWORD` | secret value | Nexus |
| `TSW_JENKINS_ADMIN_PASSWORD` | secret value | Jenkins |
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
| `TSW_SECRETS_MODE` | `generated` | enum | Selects `generated`, `fixed`, or `infisical` secret handling. |
| `TSW_FIXED_SECRET_ENV_FILE` | `.tiny-swarm-world/local/fixed-secrets.env` | local path | Fixed-mode local secret source; ignored by Git. |
| `TSW_LXC_DOCKER_REGISTRY_MIRROR` | unset | URL | Docker registry mirror reachable from managed LXC nodes. |
| `TSW_PULSAR_ADMIN_URL` | unset | URL | Internal Pulsar Admin API URL for local standalone mode. |
| `TSW_PULSAR_PUBLIC_ADMIN_URL` | unset | URL | Host-accessible Pulsar Admin API URL for browser/live checks. |
| `TSW_PULSAR_TOKEN_SECRET_KEY` | generated | secret value | Base64 encoded signing key for local Pulsar Admin API tokens. |
| `TSW_PULSAR_ADMIN_TOKEN` | generated | secret value | JWT bearer token used by live checks and operators for the local Pulsar Admin API. |
| `TSW_PULSAR_MANAGER_ADMIN_PASSWORD` | generated | secret value | Pulsar Manager UI admin password. |
| `TSW_TRAEFIK_TLS_CERT_SECRET_NAME` | `tsw_traefik_tls_cert` | secret name | External Docker secret name for Traefik TLS certificate material. |
| `TSW_TRAEFIK_TLS_KEY_SECRET_NAME` | `tsw_traefik_tls_key` | secret name | External Docker secret name for Traefik TLS private key material. |

Pulsar runs in local standalone mode with token authentication enabled. The
Admin API credential is a generated bearer token stored as `platform/pulsar`.
The Pulsar Manager UI uses a separate generated admin password stored as
`platform/pulsar-manager` when item seeding is enabled.

## Redaction

Preflight reports configuration status, key names, scopes, value kinds,
requiredness, source classification, and redaction-safe parser details such as
duplicate key names and line numbers only. It does not report raw secret
values, full environment payloads, or local file contents. Parser failures are
reported as configuration source errors without echoing the rejected line.
