# Tiny Swarm World

Tiny Swarm World is a local development and test infrastructure to simulate a production-like microservices environment on your machine. Its node-provider direction is managed LXC through LXD or Incus for Docker Swarm nodes, and it includes guarded workflow boundaries plus configuration for developer services such as Portainer, Nexus, Jenkins, Apache Pulsar, SonarQube, and Swagger + NGINX.

This README gives you a clear entry point: what it is, how to set it up, how to run it, and where to find more documentation.

---

## Overview

Use Tiny Swarm World to:
- Develop and test Docker Swarm-oriented automation boundaries.
- Keep compose stack deployment behind reviewed setup contracts.
- Model service management and observation through Portainer-facing contracts.
- Recreate cloud-like environments locally from a WSL2 or Linux shell without cloud costs.

The system follows a hexagonal architecture and provides async Python automation for provisioning and orchestration.

---

## Features

- LXC-native node-provider selection, readiness checks, and node lifecycle through LXD or Incus.
- LXC-native Docker Engine setup and Docker Swarm bootstrap inside the managed
  LXC nodes after accepted live consent.
- Fail-closed workflow boundaries for provider-native platform, artifact, and
  deployment behavior.
- Portainer-facing service management contracts and compose assets.
- Component configuration assets for:
  - Nexus (local Docker + Maven repository)
  - Jenkins (CI/CD with configuration-as-code)
  - Apache Pulsar standalone (platform messaging broker)
  - SonarQube (static code analysis)
  - Swagger + NGINX (API documentation)
- Service-access management assets:
  - static landing page content for server links and credential references
  - Infisical and service-access NGINX stack configuration
  - password-value visibility restricted to Infisical's authenticated UI
- Modular infrastructure assets in `infra/config`, driven by the Python setup workflow.
- WSL2 capability checks for managed LXC providers, with optional `socat` forwarding where needed.
- Rich test suite and enforced separation between domain, application, and infrastructure layers.

---

## Prerequisites

- Linux host or WSL2 shell on Windows
- Python 3.12
- Git
- Incus or LXD installed and initialized for the default `lxc_native` provider
- WSL2 with systemd, cgroup, and user-namespace support when running under WSL
- Docker CLI access for local diagnostics; the default `lxc_native` platform
  path installs and verifies Docker Engine inside managed LXC nodes only after
  accepted live consent
- socat if using WSL2 port-forwarding

Optional but recommended:
- An IDE such as PyCharm or IntelliJ IDEA

---

## Quick Start (Linux or WSL shell)

1. Clone the repository

```bash
git clone https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World.git
cd Tiny-Swarm-World
```

2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
python3 -m pip install pytest ruff mypy import-linter types-PyYAML types-requests
```

4. Run the development quality gate

```bash
python3 tools/quality_gate.py quality
```

5. Inspect the current workflow entry point

```bash
tiny-swarm-world --list-workflows
```

6. Run the static preflight check for the default node provider

```bash
tiny-swarm-world --preflight
```

Running the module without arguments does not execute infrastructure commands.
Use an explicit workflow selection before running automation:

```bash
tiny-swarm-world platform verify
```

Mutating workflows can call LXD/Incus/LXC, Docker, networking, or other local
infrastructure commands. They require the
live-infrastructure consent controls. Destructive workflows also require the
exact `--confirm` phrase shown by the workflow contract.

The safe setup probe is `setup run` without `--live`:

```bash
tiny-swarm-world setup run
```

Without the full live-consent contract this command refuses before setup
services are constructed and prints `REFUSED_LIVE_CONSENT_MISSING`. The
canonical live operator command uses the default `lxc_native` provider:

```bash
tiny-swarm-world setup run --live
```

Backend selection first honors an explicit `--lxc-backend` override, then
`backend_selection.preferred_backend`, then the ordered
`backend_selection.candidates` list in
`infra/config/node-providers/provider_config.yaml`. Operators may select a
managed LXC backend explicitly:

```bash
tiny-swarm-world --lxc-backend lxd setup run --live
tiny-swarm-world --lxc-backend incus setup run --live
```

For repeatable WSL/Linux operator runs with evidence capture, use the repository
wrapper:

```bash
./install.sh
```

`install.sh` is intentionally only a Linux/WSL bootstrapper. Installer policy,
secret handling, host-runtime detection, evidence layout, reset sequencing, and
headless execution live in the Python entry point
`python3 -m tiny_swarm_world.installer`, which the wrapper delegates to.

For deliberate test-system automation, use `./install.sh --confirm-reset` to
confirm the wrapper's reset prompt with an explicit flag. The underlying reset
workflow still uses `--confirm RESET_TINY_SWARM_PLATFORM`.
Use `./install.sh --non-interactive-live-approval` only for deliberate
automation that must pass the CLI live-consent prompt without terminal input;
otherwise the recorded live commands ask for interactive confirmation.
Use `./install.sh --headless` or `TSW_INSTALL_HEADLESS=1 ./install.sh` when the
same governed reset/setup flow must run without the terminal recorder/TUI
presentation. Headless mode still writes reset/setup logs and preserves command
exit codes.

The wrapper records run context, reset logs, setup logs, and exit codes under
`.tiny-swarm-world/evidence/installation-tests/<host-runtime>/`, where the
stable host directory is `wsl2` or `native_linux`. It loads or generates local
`TSW_*` secrets in `.tiny-swarm-world/local/live-installation.env` without
printing secret values, records the detected host type and selected evidence
directory in `context.txt`, records whether live approval came from an operator
prompt or explicit automation flag, records whether command output came from
the terminal recorder or headless logging, runs the governed reset prelude, then
calls the canonical setup workflow.
Required local bootstrap values are derived from
`infra/config/secrets/infisical-secrets.yaml`; the installer does not keep a
separate required-secret list.

With live consent, it sequences setup preflight, platform, artifact,
deployment, and final verification phases. Current live behavior remains
fail-closed where verification, readiness, credentials, or resource
requirements are incomplete.

The setup order is mirrored as product configuration in
`infra/config/installation-plan.yaml` and represented by typed Python domain
objects. Runtime wiring currently uses the typed `default_installation_plan()`
and `SetupWorkflow` enforces typed plans when provided. The implemented order
covers preflight, platform, cluster, network/routing, secrets, artifacts,
CI/CD, quality, messaging, observability, control, docs, and validation.
Cycles, missing required phases, missing required services, and missing
required workflow phases fail closed in tests before setup can report success.

Ports are centrally recorded in `infra/config/ports.yaml`. Traefik owns the
public ingress baseline on ports `80` and `443`; higher-numbered service ports
are direct, diagnostic, compatibility, or deferred allocations unless a later
ADR changes the ingress model. Current compose files still publish some legacy
compatibility ports, and those are documented in `infra/config/services.yml`
instead of being treated as registry-backed runtime migrations.

---

## Operator Safety Model

Normal `platform init`, `platform reconcile`, `platform expose`, and `setup run` are
non-destructive: they do not select destructive cleanup catalogs. Mutating
workflows are still live infrastructure operations. They require all of these
controls before application services are constructed:

- `--live`
- answering `y` at the short live-infrastructure confirmation prompt

Non-interactive automation may replace the prompt with `--approve-live` on the
CLI or `--non-interactive-live-approval` on `install.sh`. The flag is a separate
explicit approval source; it does not remove the `--live` requirement.

The current default provider is `lxc_native`. `platform init` selects the
LXD/Incus provider path after provider readiness checks and blocks before
mutation when backend selection, daemon access, WSL2 capability, or profile
requirements are not satisfied. After accepted live consent, default
`platform init` continues from LXC node lifecycle into Docker Engine setup and
Docker Swarm bootstrap inside `swarm-manager`, `swarm-worker-1`, and
`swarm-worker-2`. Default `platform reconcile` uses the same guarded
LXC-native node lifecycle contracts to verify configured nodes and converge
managed node drift such as missing or stopped nodes when live consent and
provider readiness allow mutation. Its JSON output reports whether mutation
was a verified `no_op`, `converged`, or `blocked`. Default `platform expose`
configures idempotent profile-level LXC proxy devices in the manager-specific
`docker-swarm-manager` profile for the published setup-manifest service ports,
so host traffic reaches the Swarm ingress mesh through the manager gateway.
Direct instance-level `tsw-proxy-*` devices on `swarm-manager` are drift and
can be removed only through the explicit live-consent-gated
`platform repair-lxc-proxy-drift` workflow after equivalent manager-profile
devices are verified. Default artifact and deployment workflows use guarded
provider-native publication, deployment, external-input, and
observed-state contracts and report blocked or failed phase evidence when live
prerequisites are unavailable.
Deployment bootstrap starts Portainer, activates admin access, and registers
the local Docker endpoint before later stacks use Portainer as the deployment
gateway implementation behind the deployment gateway port.

`platform reset` and `platform destroy` additionally require
`RESET_TINY_SWARM_PLATFORM` or `DESTROY_TINY_SWARM_PLATFORM` through
`--confirm`. They act only on configured managed LXC-native nodes whose Tiny
Swarm World ownership evidence is verified before mutation.

These behaviors are verified by unit tests, architecture checks, and static
quality gates. This repository workflow did not run live LXD, Incus, LXC
container, Docker Swarm, compose, netplan, socat, Portainer, Nexus,
Jenkins, Apache Pulsar, SonarQube, Swagger/NGINX, Infisical, image build, image
push, or stack deployment commands.

Optional live smoke validation is a separate operator action, not part of the
default quality gate. Run it only on a disposable or recoverable local target
after reviewing the live-operation surface catalog:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --live
```

When prompted, answer `y` only if changing the local LXD/Incus/LXC provider
state, Docker Swarm, networking, Portainer, Nexus,
Jenkins, Apache Pulsar, SonarQube, and Swagger/NGINX environment is intentional.

---

## Provisioning and Running the Stack

The repository contains Python services for preparing a local swarm cluster on
provider nodes. The default provider-node direction is managed LXC through LXD
or Incus. Current default flow is fail-closed:

- Select and verify the node provider (`lxc_native` by default)
- Ensure provider nodes from `infra/config/node-providers/provider_config.yaml`
  only when live consent and provider guards allow mutation
- Install and verify Docker Engine inside the managed LXC nodes when provider
  checks, profile contracts, and live consent allow mutation
- Initialize or verify the Docker Swarm manager and join or verify the worker
  nodes from inside those managed LXC containers
- Run guarded artifact publication, stack deployment, external-input, and
  service-readiness contracts when live prerequisites are observable

Where to find the scripts/services:
- `src/tiny_swarm_world/application/services/platform`
- `src/tiny_swarm_world/application/ports/node_provider`
- `infra/config/node-providers`
- `src/tiny_swarm_world/application/services/network`
- `src/tiny_swarm_world/application/services/commands`
- `infra/config/compose`

List the supported workflow-level commands first:

```bash
tiny-swarm-world --list-workflows
```

Run only the workflow you explicitly intend to execute, for example:

```bash
tiny-swarm-world platform verify
```

For the autonomous setup flow, `setup run` without `--live` is the safe refusal
probe:

```bash
tiny-swarm-world setup run
```

The canonical live operator command is:

```bash
tiny-swarm-world setup run --live
```

Platform workflows are constructed through the infrastructure composition root
in `src/tiny_swarm_world/infrastructure/composition.py`. Mutating workflows
such as `platform init`, `platform reconcile`, `platform expose`, and `setup run` require
live-infrastructure consent before services are constructed. `setup run`
orchestrates only non-destructive setup phases and reports refused, blocked,
resource-gated, failed-to-apply, failed-to-verify, failed, or completed states
without treating missing verification as success. `platform reset` and
`platform destroy` additionally require the exact reset or destroy confirmation
phrase and act only on configured managed LXC-native nodes whose Tiny Swarm
World ownership evidence is verified before mutation. Already absent managed
nodes count as reset/destroy evidence; unrelated provider resources are never
a supported cleanup target. Direct no-argument construction from the old
`docker` layout is no longer supported. Use `build_application_services()` for
the standard local wiring, or pass compatible port implementations in tests.
The composition root remains the public facade; focused
`src/tiny_swarm_world/infrastructure/composition_*.py` modules hold
service-bundle models, fail-closed workflow stubs, and provider-selected LXC
runtime wiring.
Console/status rendering consumes the application-level `ConsoleStatusEvent`
contract from `tiny_swarm_world.application.ports.ui.port_ui`. The event carries
workflow command, result status, recovery hint, evidence path, and correlation
or trace IDs when available, keeping terminal adapters presentation-only.

The canonical setup path is the workflow-level Python command. Former direct preparation scripts and host-side compose orchestration
scripts have been removed so service bootstrap, image publication, and stack
deployment cannot bypass the CLI consent gate. The
canonical static classification is maintained in
`documentation/system/live-operation-surfaces.adoc`.

Image publication and stack deployment are owned by workflow-level setup
boundaries. On the default `lxc_native` path they run only through guarded
artifact, image-publication, stack, external-input, and readiness contracts,
and they still require explicit live evidence before success is claimed. Stack
definitions live under `infra/config/compose`; image build contexts live under
`infra/config/compose`.

The full guided setup selects the `service-access` management stack profile by
default. The static dashboard and NGINX compose definition lives under
`infra/config/compose/service-access/docker-compose.yml`, and its dashboard
and NGINX assets are image-packaged under `infra/config/compose/service-access/**`.
Infisical is deployed as a separate stack from
`infra/config/compose/infisical/docker-compose.yml`.
After a verified provider-specific live deployment, the dashboard is intended
to be the management landing page at `http://localhost:10000`. It links to
the allocated local service ports for Jenkins `11080`, Nexus `13081`,
Portainer `10001`, Pulsar Manager `14081`, Pulsar Admin API `14080`,
SonarQube `12000`, Swagger `16080`, and Infisical `17080`. The table shows
users and Infisical item references; password values are visible only in
Infisical's authenticated UI. Operators who intentionally want the older base
service set can pass
`--service-profile default`.

Service metadata is declared in `infra/config/services.yml` as a static
selected-service catalogue for cross-file validation and documentation.
Runtime deployment selection still uses `ServiceStackContract` domain
contracts. The catalogue maps selected stacks to installation phases,
service-stack contracts, port-registry IDs, readiness target IDs, and explicit
compatibility published ports. Health and greenpath validation declarations
live in `infra/config/health-checks.yaml` and
`infra/config/validation-plan.yaml`; these files declare required observed
evidence, tests align them with contracts, and runtime success still requires
observed `VerificationResult` evidence.

The Infisical stack runs Infisical with PostgreSQL and Redis. The guided
installer writes `TSW_INFISICAL_ENCRYPTION_KEY`, `TSW_INFISICAL_AUTH_SECRET`,
and `TSW_INFISICAL_POSTGRES_PASSWORD` into the ignored local `0600`
environment file when they are missing. These values are exported only into
the Infisical stack environment during deployment and must not be committed.

Live-operation surface summary:

Pulsar uses local standalone mode for the Docker Swarm greenpath. The broker
uses port `6650`; the Admin API is exposed through the non-conflicting host
port `8087`. A clustered Pulsar topology is future work.

| Path | Status |
| --- | --- |
| `src/tiny_swarm_world/__main__.py` | Supported workflow-level entry point with live-consent and confirmation contracts. |
| `infra/config/compose/**/docker-compose.yml` | Supported stack assets used by the Python setup workflow. |
| `infra/config/compose/**/Dockerfile` | Supported image source assets used by the Python setup workflow. |

See `documentation/system/live-operation-surfaces.adoc` for the full
classification and credential/host-specific data rules.

---

## Configuration

- Compose stack files live under `infra/config/compose`; image build contexts
  and service image configuration live under `infra/config/compose`.
- Node-provider defaults live under `infra/config/node-providers`.
- Desired product configuration may live under `infra/config`.
- Observed inventory and verification evidence are local runtime artifacts
  under `.tiny-swarm-world/`; this path is ignored and must not be committed.
- Networking helpers and legacy netplan templates: `infra/config/network`.
- Logs: `.tiny-swarm-world/logs`.
- Operator-facing `TSW_*` values are documented in
  `documentation/configuration/operator-configuration-contract.md`; start from
  `.env.example` and keep secret-bearing local values in
  `.tiny-swarm-world/local/live-installation.env` or the process environment.

---

## Project Structure (high-level)

- `src/tiny_swarm_world/domain`, `src/tiny_swarm_world/application`, `src/tiny_swarm_world/infrastructure` - hexagonal architecture layers
- `infra/config/compose` - image build contexts and related service image assets
- `documentation` - arc42, user guides, deployment notes
- `tests` - unit and integration tests for adapters, services, and domain logic

Explore documentation for deeper architecture details:
- `documentation/arc42`
- `documentation/system`
- `documentation/user_guide`
- `documentation/deployment`

---

## Skill And Agent Governance

Tiny Swarm World agent and skill work is governed by root `AGENTS.md`,
`QUALITY.md`, `.agents/`, `.codex/`, and the audit artifacts under
`documentation/skill-audit/`.

Canonical governance navigation:

- `documentation/skill-audit/skill-registry.md`
- `documentation/skill-audit/skill-registry.json`
- `documentation/skill-audit/organigramm.md`
- `documentation/skill-audit/owner-map.md`

Project-specific skills live as discoverable
`.agents/skills/<skill-name>/SKILL.md` files. Grouped `.md` files are not
authoritative skill entrypoints unless the local discovery rules are changed by
a later workflow.

The current agent model keeps Tiny Swarm World Docker Swarm first,
Kubernetes-aware but not Kubernetes-first, Python automation first, and
console/status UI oriented. It must not be reclassified as forensic analytics,
a Spring Boot application, or a React frontend project.

---

## Development Quality Gate

The development quality gate is provided by `tools/quality_gate.py`. Run it
from a Linux or WSL shell at the repository root.

Prepare a local environment:

- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `python3 -m pip install --upgrade pip`
- `python3 -m pip install -r requirements.txt`
- `python3 -m pip install -e .`
- `python3 -m pip install ruff mypy import-linter types-requests`

Run the full gate before handing off a change:

- `python3 tools/quality_gate.py quality`

Run individual gates while developing:

- `python3 tools/quality_gate.py lint`
- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`
- `python3 tools/quality_gate.py typecheck`
- `python3 tools/quality_gate.py test`

Notes:

- The runner sets `PYTHONPATH=src` automatically and uses the repository-root
  `tests/` directory.
- `arch-lint` expects an `.importlinter` configuration.
- `arch-tests` expects the architecture test module
  `tests.architecture.test_hexagonal_imports`.
- Do not run live LXD, Incus, LXC container lifecycle, Docker
  Swarm, netplan, or service-bootstrap commands as part of the development
  quality gate.

---

## Troubleshooting

- LXC-native provider not ready: verify `incus version`/`incus info` or
  `lxc version`/`lxc info`, review the configured backend candidate order, and
  use `--lxc-backend` only when an explicit override is required.
- Docker connection issues: Verify Docker Engine or the Docker CLI target is available and your user has permission to access the Docker socket.
- WSL2 networking/ports: Install `socat` and review `infra/config/network` for port-forwarding helpers.
- Python import errors: Use the installed `tiny-swarm-world` CLI after
  `python3 -m pip install -e .`; set `PYTHONPATH=src` only for direct
  source-checkout module execution.

---

## Contributing

Contributions are welcome. Please open an issue or a PR with a clear description. Keep changes small and well-tested.

Code style guidelines:
- Only English comments are allowed in the source code. Please use English for inline comments, docstrings, and annotations.

---

## License

No license has been declared in this repository. Do not assume reuse rights
until a `LICENSE` file or explicit license statement is added.

---

## Links

- Documentation root: `documentation/README.adoc`
- System architecture: `documentation/arc42.adoc`
- User handbook: `documentation/user-handbook.adoc`
- Portainer: https://www.portainer.io/
- LXD: https://documentation.ubuntu.com/lxd/
- Incus: https://linuxcontainers.org/incus/
- LXC: https://linuxcontainers.org/lxc/
- Docker Swarm: https://docs.docker.com/engine/swarm/
