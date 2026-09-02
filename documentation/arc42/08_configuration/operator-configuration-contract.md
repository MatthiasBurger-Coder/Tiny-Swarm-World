# Operator Configuration Contract

Workflow: `config-contract-validation-issue-24-20260613`

Tiny Swarm World validates operator-facing `TSW_*` configuration before setup
execution. The committed template is `.env.example`; local secret-bearing
values belong in `.tiny-swarm-world/local/live-installation.env` or in the
process environment.

The normal `install.sh` path uses the deterministic `internal-test` catalog
plus explicit operator overrides. It has no secret-source selector and does
not create generated, fixed, or recovery credential files.

## Source Precedence

Credential values use the centralized lifecycle resolver documented in
[`credential-source-precedence.md`](credential-source-precedence.md). Its
precedence is:

1. an applicable ready secure/Infisical source (`vault`);
2. explicit operator values (`operator`), with process environment values
   overriding the approved local file;
3. the deterministic internal-test catalog (`default`) on the normal
   catalog-backed installer path.

The local env file is operator-owned, ignored by Git, and must not be committed.
The parser accepts simple `KEY=value` and `export KEY=value` assignments,
ignores non-`TSW_*` keys, and fails closed on duplicate `TSW_*` keys or
unsupported shell syntax. Self-hosted Infisical is never consulted during its
own bootstrap; it may act as the `vault` source only after readiness.

For an authorized WSL2 live run from a `/mnt/<drive>` checkout,
`TSW_INSTALL_ENV_FILE` must explicitly point to a WSL-native file outside the
checkout. The source-tree override used to qualify that checkout does not make
its DrvFS files safe for credentials. Live evidence must likewise use the
WSL-native path documented in
`documentation/evidence/wsl2-secure-live-path.md`.

## Ownership And Lifecycle

| Value group | Owner | Storage | Lifecycle |
|---|---|---|---|
| Operator runtime secrets | Operator | `.tiny-swarm-world/local/live-installation.env` or process environment; WSL2 live runs use the WSL-native `TSW_INSTALL_ENV_FILE` path | Created before install, reused across reruns, edited or rotated by the operator. |
| Catalog defaults | CRED-01 catalog | Repository Python module | Resolved deterministically for the normal internal-test path; never written to a credential file. |
| Explicit bootstrap override | Operator | Protected file selected by `TSW_BOOTSTRAP_SECRET_ENV_FILE` or its `TSW_BOOTSTRAP_STATE_DIR` alias | Optional input only; the installer never creates it. |
| Infisical-managed values | Infisical sync service | Infisical project/environment | Used only after self-hosted readiness; existing values are retained when compatible, otherwise the resolver fails closed on conflict. |
| Credential source metadata | Credential resolver | Protected run context and sanitized sync evidence | Records only `default`, `operator`, or `vault` by key; never stores raw values. |
| External Docker secret names | Operator | `.tiny-swarm-world/local/live-installation.env`, process environment, or defaults | Names identify externally managed Docker secrets and are not secret material. |
| Canonical TLS state | Python TLS resolver | `TSW_LOCAL_TLS_STATE_ROOT`, otherwise the XDG state directory below `tiny-swarm-world/tls/traefik` | Complete external material takes precedence. Otherwise managed CA and leaf material are created once and reused while valid; private keys require owner-only permissions. |

The Python installer derives required local bootstrap values from
`infra/config/secrets/infisical-secrets.yaml`. Installer code must not keep a
separate required-secret list. Required `internal_test_catalog` entries resolve
from the CRED-01 catalog; `external_user_secret` entries identify resources
that the operator must provide and are never invented by the installer.

The Traefik htpasswd value is intentionally outside the Infisical manifest: it
is required by the configuration contract for fresh-install provisioning but
is not an Infisical-managed item. The internal-test catalog supplies its
deterministic bcrypt record; an operator override may replace it. Evidence
records only key names, source labels, and synchronization status.

## Required Values

The normal catalog-backed contract derives the required values from the
deterministic catalog; an operator override may replace them before setup
execution:

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
| `TSW_TRAEFIK_GUI_USERS_HTPASSWD` | secret value | Traefik |

`TSW_TRAEFIK_GUI_USERS_HTPASSWD` is the complete htpasswd file content, not a
clear-text dashboard password. In `internal-test`, the catalog resolves the
fixed bcrypt test record before reset; custom/legacy profiles must provide it
through an operator-owned local environment or process environment. The
installer and deployment workflow use it only to recreate and verify the
named external Docker secret; it is never generated, logged, committed, or
written to evidence.

## Optional Overrides

| Key | Default | Kind | Purpose |
|---|---|---|---|
| `TSW_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS` | `180` | positive integer | Portainer stack request timeout in seconds. |
| `TSW_DEPLOYMENT_VERIFY_TIMEOUT_SECONDS` | `300` | positive integer | Total timeout for read-only deployment verification. |
| `TSW_SEED_INFISICAL_ITEMS` | `0` | boolean flag | Enables optional legacy Infisical item seeding. |
| `TSW_INSTALL_ENV_FILE` | `.tiny-swarm-world/local/live-installation.env` | local path | Optional operator override file; WSL2 live runs must point to a WSL-native `0600` file. |
| `TSW_BOOTSTRAP_SECRET_ENV_FILE` | unset | local path | Optional protected bootstrap override file; mutually exclusive with `TSW_BOOTSTRAP_STATE_DIR`. |
| `TSW_BOOTSTRAP_STATE_DIR` | unset | local path | Supported alias whose `bootstrap-secrets.env` file is an explicit input, never generated. |
| `TSW_INFISICAL_PROVIDER_MODE` | `self_hosted` | enum | Identifies the Infisical deployment boundary. `external` is rejected until a separate external integration is implemented. |
| `TSW_LXC_DOCKER_REGISTRY_MIRROR` | unset | URL | External Docker registry or Nexus proxy reachable from managed LXC nodes; used for Docker daemon mirrors and as the internal Tiny Swarm World Nexus Docker proxy upstream. |
| `TSW_SWARM_REGISTRY_ENDPOINT` | implementation default | endpoint | Registry endpoint used by the selected artifact and deployment contracts. |
| `TSW_NEXUS_READINESS_BASE_URL` | `http://127.0.0.1:13081` | credential-free URL | Base URL for bounded Nexus endpoint and repository readiness observations. |
| `TSW_PUBLIC_PULL_READINESS_URL` | `https://registry-1.docker.io/v2/` | credential-free URL | Endpoint for the bounded public-pull prerequisite check. |
| `TSW_MANAGER_STORAGE_PATH` | `/var/lib/docker` | POSIX directory path | Manager storage directory checked by the bounded artifact readiness gate. |
| `TSW_PULSAR_ADMIN_URL` | unset | URL | Internal Pulsar Admin API URL for local standalone mode. |
| `TSW_PULSAR_PUBLIC_ADMIN_URL` | unset | URL | Host-accessible Pulsar Admin API URL for browser/live checks. |
| `TSW_PULSAR_TOKEN_SECRET_KEY` | catalog-derived | secret value | Base64 encoded signing key for local Pulsar Admin API tokens. |
| `TSW_PULSAR_ADMIN_TOKEN` | catalog-derived | secret value | JWT bearer token used by live checks and operators for the local Pulsar Admin API. |
| `TSW_PULSAR_MANAGER_ADMIN_PASSWORD` | catalog-derived | secret value | Pulsar Manager UI admin password. |
| `TSW_TRAEFIK_TLS_CERT_SECRET_NAME` | `tsw_traefik_tls_cert` | secret name | External Docker secret name for Traefik TLS certificate material. |
| `TSW_TRAEFIK_TLS_KEY_SECRET_NAME` | `tsw_traefik_tls_key` | secret name | External Docker secret name for Traefik TLS private key material. |
| `TSW_TRAEFIK_GUI_USERS_SECRET_NAME` | `tsw_traefik_gui_users` | secret name | External Docker secret name containing operator-provided htpasswd entries for the secure Traefik dashboard. |
| `TSW_TRAEFIK_GUI_USERS_HTPASSWD` | CRED-01 catalog bcrypt record in `internal-test`; unset in custom profiles | secret value | Complete dashboard htpasswd content. Bcrypt is required by the catalog exception and recommended for operator overrides. Recognized legacy hashes remain accepted for compatibility but are a residual hardening concern. |
| `TSW_LOCAL_TLS_STATE_ROOT` | XDG state directory | local path | Optional canonical managed-TLS state root; must be ignored local state, not committed configuration. |
| `TSW_TRAEFIK_CA_CERT_PATH` | unset | local path | External CA certificate. Setting any external TLS path requires the complete external certificate and leaf-key tuple. |
| `TSW_TRAEFIK_CA_KEY_PATH` | unset | local path | Optional external CA private key used only when local signing ownership is required. |
| `TSW_TRAEFIK_TLS_CERT_PATH` | unset | local path | External ingress leaf certificate. |
| `TSW_TRAEFIK_TLS_KEY_PATH` | unset | local path | External ingress leaf private key. |
| `TSW_LIVE_TLS_CA_BUNDLE` | canonical resolved trust bundle | local path | Compatibility alias consumed by live/E2E clients; it must equal the selected CA trust bundle and is not a second authority. |

## Registry Bootstrap Model

Docker Swarm setup uses `TSW_LXC_DOCKER_REGISTRY_MIRROR` when an external local
Nexus or Docker registry proxy is reachable from the managed LXC nodes. After
Swarm is available, the Tiny Swarm World Nexus stack is deployed inside the
Swarm. Its Docker proxy repository uses the same reachable external mirror as
its upstream. Subsequent Tiny Swarm World image references use the internal
Swarm registry endpoint, configured by `TSW_SWARM_REGISTRY_ENDPOINT`.

Artifact image overrides are validated against the selected Compose profile
before live mutation. The readiness-only URLs and manager storage path above
are optional bounded-check inputs; they must not contain credentials, tokens or
secret material. Configuration is not readiness evidence: the gate must observe
each target before the setup workflow may prepare or publish images.

The Traefik certificate and key secret names must differ. Their contents are
reconciled as one owned pair with a shared TLS lifecycle fingerprint, and the
pair plus the dashboard htpasswd are verified before stack apply. Unknown,
unlabelled or mismatched existing TLS secrets fail closed. Errors, logs and
evidence contain neither PEM/private-key material nor htpasswd values.

Pulsar runs in local standalone mode with token authentication enabled. The
Admin API credential is a catalog-derived bearer token stored as
`platform/pulsar`. The Pulsar Manager UI uses a separate catalog-derived admin
password stored as
`platform/pulsar-manager` when item seeding is enabled.

## Redaction

Preflight reports configuration status, key names, scopes, value kinds,
requiredness, source classification, and redaction-safe parser details such as
duplicate key names and line numbers only. It does not report raw secret
values, full environment payloads, or local file contents. Parser failures are
reported as configuration source errors without echoing the rejected line.
