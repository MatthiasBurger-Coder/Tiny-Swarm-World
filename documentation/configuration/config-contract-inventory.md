# Configuration Contract Inventory

Workflow: `config-contract-validation-issue-24-20260613`
Slice: `S01`
Issue: `https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/24`

## Purpose

This inventory records the current repository evidence for operator-facing
configuration contracts. It is an implementation input for the typed config
loader, preflight validation, example template, and documentation slices.

The inventory intentionally records key names, defaults, source files, value
kinds, and requiredness only. It must not contain local secret values, local
host paths, local IP addresses, user names, raw environment payloads, or live
evidence.

## Repository Evidence

The current configuration surface is spread across these repository areas:

- `src/tiny_swarm_world/installer.py`: installer-local env file paths,
  generated secret behavior, required secret bootstrap derived from the secret
  manifest, default Traefik secret names, and setup invocation flags.
- `src/tiny_swarm_world/infrastructure/composition.py`: deployment and
  artifact wiring that reads operator config through helper functions or direct
  environment access.
- `src/tiny_swarm_world/domain/preflight/setup_manifest.py`: required setup
  secret names by service profile.
- `src/tiny_swarm_world/application/services/deployment/secret_management.py`:
  secret manifest loading, redaction, local generated-secret file handling, and
  tracked-file secret discovery.
- `src/tiny_swarm_world/infrastructure/project_paths.py`: repository and infra
  root overrides.
- `src/tiny_swarm_world/infrastructure/adapters/clients/infisical_cli_client.py`:
  Infisical URL, token, login email, and bootstrap password reads.
- `infra/config/compose/**/docker-compose.yml`: compose-time environment
  placeholders for service images, credentials, secret names, stack paths, and
  service-specific defaults.
- `infra/config/compose/**`: image-context scripts and service configuration that
  consume environment values.
- `documentation/deployment/**`, `documentation/user_guide/**`, and
  `README.md`: partial override documentation.
- `tests/**`: synthetic and live-test-only environment keys that must be
  distinguished from supported operator contracts.

## Existing Validation

The repository already validates several configuration-related contracts:

| Area | Current validation | Gap for Issue 24 |
|---|---|---|
| Node-provider config | `NodeProviderConfigYamlRepository` validates schema version, allowed fields, provider/backend values, safety restrictions, profiles, nodes, resource mappings, and evidence policy. | Specific to `infra/config/node-providers/provider_config.yaml`; not a general operator override contract. |
| Command catalog YAML | `PortCommandRepositoryYaml` validates command catalog structure and typed command entities. | Product command YAML files are currently retired and this does not cover active env overrides. |
| Desired inventory | `DesiredInventoryYamlRepository` loads host-neutral desired inventory through domain value objects. | Inventory validation is separate from env override validation. |
| Setup manifest secrets | `default_setup_manifest` defines required secret names by service profile. | Required non-secret config values and many optional overrides are outside this contract. |
| Preflight | `PreflightService` checks host, dependencies, resources, ports, secrets, ignore policy, and forbidden secret fingerprints. | It does not yet run one typed config-contract check for all supported overrides before execution. |
| Secret management | Secret discovery and redaction classify secret-like tracked values and generated local secrets. | It does not define full `TSW_*` source precedence or non-secret value validation. |

## Product YAML Files

These files are committed product configuration and must be covered by typed
loading, schema checks, or explicit pass-through handling:

| File | Current role | Current validation status |
|---|---|---|
| `infra/config/node-providers/provider_config.yaml` | Managed LXC provider selection, nodes, profiles, resource resolution, evidence metadata. | Strong typed repository validation exists. |
| `infra/config/inventory/desired_inventory.yaml` | Host-neutral desired inventory. | Domain loading rejects unknown fields and invalid collection shapes. |
| `infra/config/services.yml` | Service catalogue material. | Needs explicit contract review before being included in the typed config loader. |
| `infra/config/cloud-init-manager.yaml` | Cloud-init manager configuration. | Legacy/specialized surface; include only after consumer ownership is verified. |
| `infra/config/compose/*/docker-compose.yml` | Stack definitions and compose placeholders. | Parsed by compose repository tests for stack content, service names, and published ports; placeholder variables need inventory and template coverage. |
| `infra/config/secrets/infisical-secrets.yaml` | Managed secret manifest for Infisical synchronization. | `SecretManifestRenderer` validates schema, duplicate keys, key pattern, type, and policy. |

## Required Setup Secrets

These are required by the setup manifest for current service profiles. They
are secret values unless explicitly noted otherwise.

| Key | Service | Requiredness | Value kind | Source |
|---|---|---|---|---|
| `TSW_PORTAINER_ADMIN_PASSWORD` | Portainer | Required | secret value | `setup_manifest.py`, `installer.py`, composition |
| `TSW_NEXUS_ADMIN_PASSWORD` | Nexus | Required | secret value | `setup_manifest.py`, `installer.py`, composition |
| `TSW_JENKINS_ADMIN_PASSWORD` | Jenkins | Required | secret value | `setup_manifest.py`, `installer.py`, compose |
| `TSW_RABBITMQ_PASSWORD` | RabbitMQ | Required | secret value | `setup_manifest.py`, `installer.py`, compose |
| `TSW_SONARQUBE_ADMIN_PASSWORD` | SonarQube | Required | secret value | `setup_manifest.py`, `installer.py`, composition |
| `TSW_POSTGRES_PASSWORD` | SonarQube PostgreSQL | Required | secret value | `setup_manifest.py`, `installer.py`, compose |
| `TSW_SONARQUBE_POSTGRES_PASSWORD` | SonarQube PostgreSQL | Required by installer/deployment env | secret value | `installer.py`, composition, compose |
| `TSW_INFISICAL_LOGIN_EMAIL` | Infisical admin login | Required for service-access profile | non-secret identity value | `setup_manifest.py`, `installer.py`, composition, compose |
| `TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD` | Infisical admin login | Required for service-access profile | secret value | `setup_manifest.py`, `installer.py`, composition, compose |
| `TSW_INFISICAL_ENCRYPTION_KEY` | Infisical | Required for service-access profile | secret value | `setup_manifest.py`, `installer.py`, composition, compose |
| `TSW_INFISICAL_AUTH_SECRET` | Infisical | Required for service-access profile | secret value | `setup_manifest.py`, `installer.py`, composition, compose |
| `TSW_INFISICAL_POSTGRES_PASSWORD` | Infisical PostgreSQL | Required for service-access profile | secret value | `setup_manifest.py`, `installer.py`, composition, compose |
| `TSW_INFISICAL_REDIS_PASSWORD` | Infisical Redis | Required by installer/deployment env | secret value | `installer.py`, composition |

## Runtime And Deployment Overrides

These keys are consumed by production source, compose assets, or installer
logic. Defaults are listed only when visible from committed source.

| Key | Default | Requiredness | Value kind | Source |
|---|---|---|---|---|
| `TSW_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS` | repository default constant | Optional | positive integer seconds | `composition.py`, installation docs |
| `TSW_PORTAINER_USERNAME` | `admin` | Optional | identifier | `composition.py`, docs |
| `TSW_SONARQUBE_ADMIN_USERNAME` | `admin` | Optional | identifier | `composition.py` |
| `TSW_JENKINS_ADMIN_USERNAME` | `admin` | Optional | identifier | `composition.py` |
| `TSW_NEXUS_ADMIN_USERNAME` | `admin` | Optional | identifier | `composition.py`, docs |
| `TSW_RABBITMQ_USERNAME` | `admin` | Optional | identifier | `composition.py` |
| `TSW_SEED_INFISICAL_ITEMS` | `0` in installer | Optional | boolean flag as `0`/`1` | `installer.py`, `composition.py` |
| `TSW_LXC_DOCKER_REGISTRY_MIRROR` | auto-detected when possible | Optional | URL reachable from managed nodes | `install.sh`, `composition.py`, docs |
| `TSW_LXC_PROXY_LISTEN_ADDRESS` | implementation default | Optional | listen address | `composition.py` |
| `TSW_SWARM_REGISTRY_ENDPOINT` | implementation default | Optional | registry endpoint | `composition.py` |
| `TSW_NEXUS_DOCKER_HUB_PROXY_REPOSITORY` | implementation default | Optional | repository name | `composition.py`, docs |
| `TSW_NEXUS_DOCKER_HUB_PROXY_PORT` | implementation default | Optional | positive integer port | `composition.py`, docs |
| `TSW_NEXUS_DOCKER_HUB_PROXY_REMOTE_URL` | implementation default | Optional | URL | `composition.py`, docs |
| `TSW_NEXUS_CACHE_CONTAINER` | repository default constant | Optional | container name | `composition.py` |
| `TSW_NEXUS_CACHE_DOCKER_PROXY_PORT` | repository default constant | Optional | positive integer port | `composition.py` |
| `TSW_INFISICAL_URL` | `http://localhost:8086` | Optional | URL | `infisical_cli_client.py`, `composition.py` |
| `TSW_INFISICAL_INTERNAL_URL` | implementation default | Optional | URL | `composition.py` |
| `TSW_INFISICAL_ORGANIZATION` | implementation default | Optional | identifier | `composition.py` |
| `TSW_INFISICAL_ADMIN_FIRST_NAME` | `Tiny` | Optional | text | `composition.py`, compose |
| `TSW_INFISICAL_ADMIN_LAST_NAME` | `Admin` | Optional | text | `composition.py`, compose |
| `TSW_INFISICAL_TOKEN` | none | Optional | secret token | `infisical_cli_client.py` |
| `TSW_INFISICAL_BOOTSTRAP_TOKEN` | generated at runtime | Optional | secret token | `infisical_cli_client.py` |
| `TSW_REPOSITORY_ROOT` | current/project root detection | Optional | path | `project_paths.py` |
| `TSW_INFRA_ROOT` | `infra` under repository root | Optional | path | `project_paths.py` |
| `TSW_LIVE_INFRASTRUCTURE_CONSENT` | none | Required only for live mutation | consent token | `live_consent.py`, docs |

## Compose Placeholder Overrides

Compose placeholders must be classified so the template and validation can
distinguish service images, secret values, secret names, paths, and defaults.

| Key | Default | Value kind | Source |
|---|---|---|---|
| `TSW_NEXUS_IMAGE` | `sonatype/nexus3:3.75.1` | image reference | Nexus compose, composition, docs |
| `TSW_JENKINS_IMAGE` | local registry Jenkins image | image reference | Jenkins compose, composition, docs |
| `TSW_SERVICE_ACCESS_DASHBOARD_IMAGE` | local registry dashboard image | image reference | Service-access compose, composition |
| `TSW_SERVICE_ACCESS_NGINX_IMAGE` | local registry nginx image | image reference | Service-access compose, composition |
| `TSW_INFISICAL_IMAGE` | `infisical/infisical:latest` | image reference | Infisical compose, composition, docs |
| `TSW_INFISICAL_POSTGRES_IMAGE` | `postgres:14-alpine` | image reference | Infisical compose, composition, docs |
| `TSW_INFISICAL_REDIS_IMAGE` | `redis:7-alpine` | image reference | Infisical compose, composition, docs |
| `TSW_INFISICAL_SITE_URL` | `http://localhost:8086` | URL | Infisical compose |
| `TSW_INFISICAL_POSTGRES_USER` | `infisical` | identifier | Infisical compose |
| `TSW_INFISICAL_POSTGRES_DB` | `infisical` | identifier | Infisical compose |
| `TSW_REMOTE_STACK_ROOT` | `/var/lib/tiny-swarm-world/stacks` | POSIX path inside managed node | Swagger and Traefik compose, LXC swarm runtime |
| `TSW_TRAEFIK_IMAGE` | `traefik:v3.7.4` | image reference | Traefik compose |
| `TSW_TRAEFIK_TLS_CERT_SECRET_NAME` | `tsw_traefik_tls_cert` | external secret name | Traefik compose, installer |
| `TSW_TRAEFIK_TLS_KEY_SECRET_NAME` | `tsw_traefik_tls_key` | external secret name | Traefik compose, installer |
| `TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET` | legacy/opt-in Vaultwarden surfaces only | external secret name | not part of the current service-access compose contract |

## Documentation-Only Or Drifted Keys

These keys are documented or present in tests but are not consistently wired
through the governed LXC setup/deployment composition path.

| Key | Evidence | Current status |
|---|---|---|
| `TSW_PORTAINER_URL` | deployment docs, user guide, live tests | LXC composition currently constructs Portainer clients from backend-specific adapters rather than this URL. |
| `TSW_PORTAINER_ENDPOINT` | deployment docs, user guide | Deployment composition uses `DEFAULT_PORTAINER_ENDPOINT_NAME`; operator override ownership is unclear. |
| `TSW_NEXUS_URL` | deployment docs, user guide, live tests | LXC artifact client wiring does not consistently consume this documented override. |
| `TSW_NEXUS_INITIAL_PASSWORD_PATH` | deployment docs, user guide | Historical Nexus bootstrap config value; current LXC admin access path needs ownership verification before inclusion. |
| `TSW_NEXUS_MAX_ATTEMPTS` | deployment docs, user guide | Current LXC readiness wiring uses fixed values in composition. |
| `TSW_NEXUS_WAIT_SECONDS` | deployment docs, user guide | Current LXC readiness wiring uses fixed values in composition. |

## Installer-Local Controls

These keys control installer behavior or local file paths. They should be
documented separately from runtime service configuration.

| Key | Default | Value kind | Notes |
|---|---|---|---|
| `TSW_INSTALL_ENV_FILE` | `.tiny-swarm-world/local/live-installation.env` | local path | Ignored local runtime secret file. |
| `TSW_INFISICAL_SECRET_ENV_FILE` | `.tiny-swarm/secrets/bootstrap.local.env` | local path | Ignored local bootstrap secret file. |
| `TSW_GENERATED_SECRET_ENV_FILE` | `.tiny-swarm/secrets/generated.local.env` | local path | Ignored generated secret recovery file. |
| `TSW_NATIVE_LINUX_VENV` | `.tiny-swarm-world/install-venv` | local path | Installer virtual environment path. |
| `TSW_INSTALL_SKIP_NATIVE_DEPENDENCY_BOOTSTRAP` | `0` | boolean flag as `0`/`1` | Installer-only control. |
| `TSW_INSTALL_SKIP_NATIVE_GROUP_SWITCH` | `0` | boolean flag as `0`/`1` | Installer-only control. |
| `TSW_INSTALL_COMMAND_GROUP` | derived when needed | group name | Installer group-switch control. |

## Live And Test-Only Keys

These keys appear in tests or opt-in live verification and should not be part
of the default setup contract unless a slice explicitly includes their owning
workflow.

| Key group | Examples | Classification |
|---|---|---|
| Post-install browser live tests | `TSW_RUN_POST_INSTALL_BROWSER_LIVE`, `TSW_POST_INSTALL_BROWSER_TIMEOUT`, `TSW_POST_INSTALL_BROWSER_CHANNEL`, `TSW_LIVE_INSTALLATION_ENV`, `TSW_LIVE_TLS_CA_BUNDLE`, `TSW_DASHBOARD_URL`, `TSW_INGRESS_BASE_DOMAIN` | opt-in live-test configuration |
| Vaultwarden live/integration tests | `TSW_RUN_LIVE_VAULTWARDEN_INTEGRATION`, `TSW_VAULTWARDEN_IMAGE`, `TSW_VAULTWARDEN_URL`, `TSW_VAULTWARDEN_LOGIN_EMAIL`, `TSW_VAULTWARDEN_MASTER_PASSWORD`, `TSW_VAULTWARDEN_IT_TIMEOUT`, `TSW_VAULTWARDEN_SIGNUP_PATH`, `TSW_VAULTWARDEN_SIGNUPS_ALLOWED` | opt-in live/integration configuration |
| Synthetic test fixtures | `TSW_CUSTOM_SECRET`, `TSW_TEST_SECRET`, `TSW_EXAMPLE`, `TSW_EXAMPLE_PASSWORD`, `TSW_NEW_PASSWORD`, `TSW_EXISTING_PASSWORD`, `TSW_STABLE_PASSWORD`, `TSW_API_SYNC_PASSWORD`, `TSW_EXTERNAL_API_KEY` | test-only fixture keys |
| Fake installer controls | `TSW_FAKE_SCRIPT_COMMANDS`, `TSW_FAKE_RESET_EXIT`, `TSW_FAKE_SETUP_EXIT`, `TSW_FAKE_IMPORT_CHECK_EXIT` | test-only controls |

## Template Decision

The tracked example template should be the repository-root `.env.example`.
Reasons:

- `.env` is already part of required ignore-policy preflight checks.
- Root `.env.example` is a conventional operator discovery point.
- It can cover installer-local and runtime values without pointing operators
  at ignored live secret files.
- Real local values remain in ignored files such as
  `.tiny-swarm-world/local/live-installation.env`.

The template must use placeholders only, for example
`<operator-supplied-portainer-password>`, and must never include generated
local values from the user's runtime environment.

## Gaps To Close

- Add a typed allowlist for supported operator keys, including requiredness,
  source precedence, value kind, defaults, and redaction classification.
- Reconcile setup-manifest required secrets with installer/runtime-required
  secrets. `TSW_INFISICAL_REDIS_PASSWORD` is now required in the secret
  manifest and consumed by the Python installer; setup-manifest ownership should
  still be reviewed when service-profile validation is expanded.
- Decide whether documented but currently hardcoded or test-only overrides such
  as `TSW_PORTAINER_URL`, `TSW_PORTAINER_ENDPOINT`,
  `TSW_NEXUS_INITIAL_PASSWORD_PATH`, `TSW_NEXUS_MAX_ATTEMPTS`, and
  `TSW_NEXUS_WAIT_SECONDS` should be implemented, deprecated, or documented as
  legacy compatibility surface.
- Add validation for common value kinds: secret value, secret name, URL,
  positive integer, boolean flag, image reference, identifier, local path, and
  managed-node POSIX path.
- Add local shell env parsing with duplicate-key detection for ignored env
  files if those files are read by Python automation.
- Add a preflight configuration check that fails before live mutation.
- Add `.env.example` and keep it checked against the typed contract.
- Synchronize README, deployment docs, user guide, and arc42 after behavior is
  implemented.
