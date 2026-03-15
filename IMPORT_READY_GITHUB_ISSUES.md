# IMPORT_READY_GITHUB_ISSUES

## [Critical][Python/Entrypoint][F-001] Python package/import model is not runnable from repository root
- Labels: audit, critical, python
- Severity: Critical
- Area: Python/Entrypoint
- Finding ID: F-001

### Summary
Core modules import `application`, `domain`, and `infrastructure` as top-level packages, but repository layout places them under `docker/`, so default execution/test discovery from repo root fails without PYTHONPATH hacks.

### Evidence
- docker/tiny_swarm_world.py uses `from application...` imports
- setup.py maps packages from `docker` but no console entrypoint
- pytest from repo root fails with ModuleNotFoundError for `application`/`infrastructure`

### Recommended remediation
Define canonical execution mode (installable package + console script or explicit module path), add pyproject/setup entrypoint, and make tests pass without manual PYTHONPATH.

### Acceptance criteria
- `python -m tiny_swarm_world` or documented CLI works from repo root
- `pytest` runs from root without import errors
- README and docs reflect one canonical command

### Dependencies
- None

## [Critical][Multipass][F-002] Canonical orchestration hard-resets all VMs on every run
- Labels: audit, critical, multipass
- Severity: Critical
- Area: Multipass
- Finding ID: F-002

### Summary
Startup sequence always executes cleanup (`multipass delete --all` + `multipass purge`) before provisioning.

### Evidence
- docker/application/services/multipass/multipass_init_vms.py executes clean then init
- docker/config/multipass/command_multipass_clean_repository_yaml.yaml deletes/purges all VMs

### Recommended remediation
Split destructive reset into explicit command; default workflow should detect existing VMs and reconcile state.

### Acceptance criteria
- Default run does not delete running VMs
- Optional `--reset` path performs cleanup explicitly
- Rerun keeps cluster state unless reset requested

### Dependencies
- F-001

## [High][Maintainability][F-003] Repository mixes active and dead orchestration implementations
- Labels: audit, high-priority, maintainability
- Severity: High
- Area: Maintainability
- Finding ID: F-003

### Summary
`docker/swarm/prepere.py` imports non-existent modules and contains commented execution paths, while `docker/tiny_swarm_world.py` contains different active flow.

### Evidence
- docker/swarm/prepere.py imports `multipass_swarm_setup`/`multipass_network_setup`/`multipass_docker_setup` files not present under docker/swarm/multipass
- Many setup steps are commented out in PrepareMultipass.setup()

### Recommended remediation
Archive or remove dead scripts; document one canonical orchestrator and add CLI help output.

### Acceptance criteria
- Only supported startup scripts remain
- Deprecated scripts marked clearly or removed
- Docs point to single entrypoint

### Dependencies
- F-001

## [High][Networking][F-004] Netplan generation and transfer path assumptions are fragile
- Labels: audit, high-priority, networking
- Severity: High
- Area: Networking
- Finding ID: F-004

### Summary
Netplan YAML is generated as `cloud-init-manager.yaml` in CWD-dependent path, but transfer command assumes `config/cloud-init-manager.yaml` relative to execution directory.

### Evidence
- PortNetplanRepositoryYaml default file is `cloud-init-manager.yaml`
- network setup command uses `multipass transfer config/cloud-init-manager.yaml ...`

### Recommended remediation
Introduce absolute repository-root-aware path resolution and validate file existence before transfer.

### Acceptance criteria
- Netplan file saved into deterministic location
- Transfer command references the same resolved path
- Preflight check fails fast with actionable message

### Dependencies
- F-001

## [High][Networking][F-005] WSL2/Linux networking procedure is incomplete and non-idempotent
- Labels: audit, high-priority, networking
- Severity: High
- Area: Networking
- Finding ID: F-005

### Summary
Networking relies on ad-hoc socat/iptables commands without lifecycle management or cleanup guarantees.

### Evidence
- docker/config/network/command_network_setup_yaml.yaml installs socat and applies netplan twice
- docker/utils.sh adds iptables rules without idempotent checks
- documentation/system/network.adoc is minimal and lacks procedures

### Recommended remediation
Create explicit network prepare/verify/cleanup commands with idempotent checks per platform.

### Acceptance criteria
- Repeated network setup produces same state
- Rules/processes are verifiable and removable
- Docs include Windows WSL2 and Linux branches

### Dependencies
- F-004

## [High][Docker][F-006] Docker install sequence lacks daemon readiness and robust retry controls
- Labels: audit, high-priority, docker
- Severity: High
- Area: Docker
- Finding ID: F-006

### Summary
Docker installation runs package commands but does not verify daemon active state before swarm operations.

### Evidence
- docker/application/services/multipass/multipass_docker_install.py executes install then group prep only
- command_multipass_docker_install_yaml.yaml checks `docker --version` but not `docker info`/service active

### Recommended remediation
Add daemon startup checks (`systemctl is-active docker`, `docker info`) with retries/timeouts before continuing.

### Acceptance criteria
- Install phase blocks until daemon healthy on all nodes
- Failures emit per-node diagnostics
- Swarm init starts only after readiness success

### Dependencies
- F-002

## [Critical][Swarm][F-007] Swarm bootstrap flow is not idempotent and has weak result parsing
- Labels: audit, critical, swarm
- Severity: Critical
- Area: Swarm
- Finding ID: F-007

### Summary
Manager init always calls `docker swarm init`; token/IP extraction parses positional output structures instead of validated schema.

### Evidence
- multipass_docker_swarm_init.py calls manager init every run
- Token parsed via `result[0][1]`; manager IP via split on first value

### Recommended remediation
Check swarm state before init/join, standardize command result objects, parse with explicit keys/regex validation.

### Acceptance criteria
- Rerun handles already-active swarm cleanly
- Join token parsing validated
- Post-join `docker node ls` verification implemented

### Dependencies
- F-006

## [Critical][Deployment][F-008] No implemented stack deployment in main orchestration
- Labels: audit, critical, deployment
- Severity: Critical
- Area: Deployment
- Finding ID: F-008

### Summary
Main python flow stops after swarm join and does not deploy Portainer/Nexus/Jenkins/RabbitMQ/SonarQube/Swagger/NGINX.

### Evidence
- docker/tiny_swarm_world.py ends after MultipassDockerSwarmInit
- Service deployment exists only in separate shell scripts under docker/prepare and docker/compose

### Recommended remediation
Add deploy phase to canonical orchestrator or explicitly orchestrate shell pipeline with validations.

### Acceptance criteria
- One command provisions cluster and deploys at least Portainer + one supporting service
- Deployment status checks are automated

### Dependencies
- F-007

## [High][Security][F-009] Portainer/Nexus automation uses hardcoded insecure default credentials
- Labels: audit, high-priority, security
- Severity: High
- Area: Security
- Finding ID: F-009

### Summary
Admin credentials and registry password are embedded in scripts.

### Evidence
- docker/prepare/portainer/prepare.sh sets admin/admin1234567890
- docker/compose/upload_all_stacks.sh defaults to same credentials
- docker/compose/create_dockerfiles.sh contains `NEW_PASSWORD` literal

### Recommended remediation
Move credentials to env files/secrets; require explicit user-provided values and avoid defaults in repo.

### Acceptance criteria
- No hardcoded credentials in tracked files
- Sample env template provided
- Scripts fail fast when secrets missing

### Dependencies
- F-008

## [High][Deployment][F-010] Compose assets are inconsistent with swarm/VM execution context
- Labels: audit, high-priority, deployment
- Severity: High
- Area: Deployment
- Finding ID: F-010

### Summary
Several compose files bind services to 127.0.0.1 and use host paths unsuitable for remote VM swarm deployment.

### Evidence
- docker/compose/*/docker-compose.yml publish `127.0.0.1:...` bindings
- rabbitmq compose mounts `~/.docker-conf/...` host paths
- Portainer stack uses `/var/run/sock` instead of standard `/var/run/docker.sock`

### Recommended remediation
Create swarm-compatible stack manifests with explicit overlay networks, named volumes, and correct socket mounts.

### Acceptance criteria
- Stack deploy succeeds on manager
- Service reachability validated from host
- No invalid bind/socket paths remain

### Dependencies
- F-008

## [High][Documentation][F-011] Documentation is largely placeholder/outdated versus implementation
- Labels: audit, high-priority, documentation
- Severity: High
- Area: Documentation
- Finding ID: F-011

### Summary
Critical docs contain placeholders, typos, or unrelated architecture text not tied to repository automation.

### Evidence
- documentation/user_guide/installation.adoc and usage.adoc are one-line placeholders
- documentation/deployment/system.adoc is generic German arc42 text unrelated to current scripts
- README lacks runnable end-to-end command sequence

### Recommended remediation
Rewrite docs from verified flows, include exact commands, prerequisites, and validation checkpoints.

### Acceptance criteria
- Clean-machine runbook exists and is validated
- Troubleshooting includes known failures and recovery
- Docs identify canonical entrypoint

### Dependencies
- F-001
- F-008

## [High][Tests][F-012] Test suite is not runnable on clean checkout and has low signal
- Labels: audit, high-priority, tests
- Severity: High
- Area: Tests
- Finding ID: F-012

### Summary
Tests fail at collection without PYTHONPATH and dependencies; several tests are duplicated/skipped or not asserting runtime behavior.

### Evidence
- `pytest -q` shows import errors for top-level packages
- Duplicate async command runner tests in two directories
- Service tests marked `@unittest.skip` and commented assertions

### Recommended remediation
Add test config (`pyproject`/`pytest.ini`) for import path, install deps in CI, remove duplicates, and implement actionable smoke/integration tests.

### Acceptance criteria
- `pytest` passes in documented environment
- Critical orchestration units covered
- At least one end-to-end smoke test exists

### Dependencies
- F-001

## [Medium][Configuration][F-013] Configuration contracts are implicit and unvalidated
- Labels: audit, medium-priority, infrastructure
- Severity: Medium
- Area: Configuration
- Finding ID: F-013

### Summary
Many required parameters (VM specs, ports, credentials, repo URLs) are hardcoded in YAML/scripts without schema validation or documented overrides.

### Evidence
- vms_repository.yaml fixed VM names and resources
- scripts hardcode portainer URL and credentials
- no `.env.example` or config validation routine

### Recommended remediation
Introduce typed config loader with validation and environment override support.

### Acceptance criteria
- Config schema validates before execution
- Example env/config template provided
- Overrides documented

### Dependencies
- F-011

## [Medium][Python][F-014] Error propagation in command execution hides failures
- Labels: audit, medium-priority, python
- Severity: Medium
- Area: Python
- Finding ID: F-014

### Summary
Command execution catches exceptions per command and continues; higher-level services do not fail fast when critical steps fail.

### Evidence
- CommandExecuter.execute catches Exception and `continue`
- Async/Sync UI runners gather exceptions but always finalize as success status for `all`

### Recommended remediation
Adopt explicit failure policy: stop on critical errors, aggregate structured failure report, return non-zero process exit.

### Acceptance criteria
- Critical command failure aborts workflow
- Exit status reflects success/failure
- Logs show failed command and node

### Dependencies
- F-007

## [Low][Maintainability][F-015] Repository contains non-production leftovers and mixed-language comments
- Labels: audit, low-priority, maintainability
- Severity: Low
- Area: Maintainability
- Finding ID: F-015

### Summary
Legacy files, typos, and non-English comments reduce clarity and violate stated style expectations.

### Evidence
- `docker/swarm/prepere.py` typo and legacy content
- `docker/setup.py_old` retained
- German comments in Python/Bash (e.g., command runner UI, scripts)

### Recommended remediation
Remove/archive stale files, fix naming, enforce comment language and linting.

### Acceptance criteria
- Legacy files removed or documented as deprecated
- Comments in source code are English-only
- CI lint check enforces repository hygiene

### Dependencies
- None
