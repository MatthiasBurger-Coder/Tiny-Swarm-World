# Operator Configuration Contract

Workflow: `config-contract-validation-issue-24-20260613`

Tiny Swarm World validates operator-facing `TSW_*` configuration before setup
execution. The committed template is `.env.example`; local secret-bearing
values belong in `.tiny-swarm-world/local/live-installation.env` or in the
process environment.

The normal `install.sh` path uses the deterministic `internal-test` catalog
plus explicit operator overrides. It has no secret-source selector and does
not create generated, fixed, or recovery credential files.

This is an internal development/test contract. AD/LDAP/SSO, VPN, firewall,
network segmentation, and IAM remain enterprise responsibilities outside the
bootstrap path. Catalog defaults are disposable `INTERNAL/TEST ONLY` material;
public, shared, or untrusted exposure requires an approved stronger override
and the surrounding organization's identity and network controls.

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

## Configuration Parsing and Migration

ARCH-03.09 validates external shapes and scalar types before selected managed
lifecycle mutation. Correct the input at its source when preparation fails; do
not rely on Python truthiness or string conversion to repair malformed YAML.
The checked-in supported configuration remains covered by deterministic tests.

| Input | Accepted form and retained compatibility | Migration for rejected input |
|---|---|---|
| Manifest entries | Required key/type/source are strings; supplied text fields remain strings. `required` is a boolean and defaults to `false`; policy and other optional defaults remain. Unknown source strings retain unknown ownership metadata. | Replace quoted boolean text or numeric flags with YAML booleans; provide missing required strings. Remove duplicate YAML fields and duplicate secret keys. |
| Desired inventory | Text and collection members are strings; CPU counts retain integer/numeric-string support. Schema version accepts integer `1` or string `"1"`. Missing files and empty/null YAML documents retain empty defaults. | Remove boolean CPU counts and other coerced text/container values; use the supported schema version. This is a compatibility repository, not a newly activated runtime inventory loader. |
| Provider configuration | Identifiers are strings; resource values are strings or integers. Existing timeout numeric strings/ranges and schema `1` compatibility remain. | Replace boolean, float or nested resource values with supported strings/integers; do not depend on identifiers being stringified. |
| Port registry | Present registry mappings require both `ranges` and `ports` lists. Port fields are integers; optional port fields retain their existing null semantics. `required_for_preflight` is a boolean. Description/protocol are strings; metadata values may be strings, integers, floats or booleans. Missing files and empty/null YAML documents retain empty defaults. | Replace boolean ports and quoted boolean flags; remove null/container metadata values. |
| Retained command catalogue | Command index supports integer/numeric-string input; evidence flags are booleans. Existing command safety rules still apply. | Replace boolean/float indices and nonboolean evidence flags. Retired catalogue files are not reactivated. |
| Programmatic environment sources | Keys are strings and selected `TSW_*` values are strings. Shell-file precedence and supported assignment syntax remain unchanged. | Convert values explicitly before supplying the source; do not pass booleans or nested objects as environment values. |
| Service catalogue | A present file contains a services mapping with named mapping entries and boolean `enabled` values. Missing files retain the empty selection; absent `enabled` retains disabled behavior. | Repair malformed roots/members or quoted enable flags; a malformed present file is no longer silently treated as an empty catalogue. |
| Selected Compose | TSW requires named service mappings, nonempty image strings and deploy mappings; owned port/renderer fields must have supported shapes. Extensions, aliases, interpolation and short/long port forms remain supported. | Repair malformed selected entries instead of expecting them to be dropped. This boundary does not validate the complete Compose specification. |

Configuration-tree checks reject recursive aliases, non-string mapping keys
and unsupported scalar types such as YAML timestamps; ordinary aliases remain
supported. Quote a date when a configuration field requires text. Unknown-field
policy remains specific to each repository; this is not a blanket ban on
unknown fields or Compose extensions. The manifest still uses PyYAML safe
loading, including its existing boolean/merge semantics. Other YAML adapters
retain their existing parser.

After successful selected Compose preparation, edits to its source files do
not affect that repository's retained definitions. Provider and composed
operator/mirror values are likewise retained for the prepared lifecycle.
Create a new invocation to use a changed selection. Direct deployment workflows
prepare all configured steps before mutating preparation; setup prepares its
selected deployment configuration before host/provider/artifact mutation.

The normal installer validates a private copy before reset, then points reset
and setup at the same staged infrastructure root and operator file. It copies
the configuration tree into a private temporary directory under `/tmp`, keeps
directories owner-only, and makes copied files owner-readable/writable while
preserving an existing owner executable bit. The original operator source must
already satisfy the platform's filesystem/ownership policy; a present file is
checked for the effective owner/group and mode `0600`. Symlinks in traversed
paths and special files are rejected using non-following descriptor reads.
The staged operator file is checked again. Missing optional input remains
absent for that run even if its original path later appears. Temporary copies
are cleaned up when the installer context exits on success or failure; they are
not committed configuration, recovery credentials or published evidence.

For service-access deployment with an actual Infisical sync step and Jenkins
credential callback, static preparation may defer the Jenkins password until
that callback supplies a checked snapshot. Update/custom paths without the
producer require their static value. The normal catalog-backed installer
resolves its required values and validates them before reset without this
deferral. Vault precedence and runtime readiness are unchanged.

Local dependency/bootstrap preparation and protected staging may write files
before managed reset/setup operations. Deterministic validation results do not
establish live installation, service readiness, Selenium or external quality
success. Auxiliary bridge scripts and tool-owned configuration remain
infrastructure pass-through inputs without a new schema-validation claim.
