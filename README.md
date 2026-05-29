# Tiny Swarm World

Tiny Swarm World is a local development and test infrastructure to simulate a production-like microservices environment on your machine. Its default node-provider direction is managed LXC through LXD or Incus for Docker Swarm nodes, and it includes guarded workflow boundaries plus configuration for developer services such as Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, and Swagger + NGINX. Multipass remains available only as an explicit legacy/fallback provider.

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
- Explicit Multipass legacy/fallback mode through `--node-provider multipass_legacy`.
- Fail-closed workflow boundaries for provider-native platform, artifact, and
  deployment behavior.
- Portainer-facing service management contracts and compose assets.
- Component configuration assets for:
  - Nexus (local Docker + Maven repository)
  - Jenkins (CI/CD with configuration-as-code)
  - RabbitMQ (message broker)
  - SonarQube (static code analysis)
  - Swagger + NGINX (API documentation)
- Service-access management assets:
  - static landing page content for server links and credential references
  - Vaultwarden and service-access NGINX stack configuration
  - password-value visibility restricted to Vaultwarden's authenticated UI
- Modular infrastructure assets in `infra/config` and `infra/compose`, driven by the Python setup workflow.
- WSL2 capability checks for managed LXC providers, with optional `socat` forwarding where needed.
- Rich test suite and enforced separation between domain, application, and infrastructure layers.

---

## Prerequisites

- Linux host or WSL2 shell on Windows
- Python 3.12
- Git
- Incus or LXD installed and initialized for the default `lxc_native` provider
- WSL2 with systemd, cgroup, and user-namespace support when running under WSL
- Multipass with the QEMU backend only for explicit legacy/fallback runs
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
python3 -m pip install ruff mypy import-linter
```

4. Run the development quality gate

```bash
python3 tools/quality_gate.py quality
```

5. Inspect the current workflow entry point

```bash
PYTHONPATH=src python3 -m tiny_swarm_world --list-workflows
```

6. Run the static preflight check for the default node provider

```bash
PYTHONPATH=src python3 -m tiny_swarm_world --preflight
```

Running the module without arguments does not execute infrastructure commands.
Use an explicit workflow selection before running automation:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world platform verify
```

Mutating workflows can call LXD/Incus/LXC, Multipass legacy, Docker,
networking, or other local infrastructure commands. They require the
live-infrastructure consent controls. Destructive workflows also require the
exact `--confirm` phrase shown by the workflow contract.

The safe setup probe is `setup run` without `--live`:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run
```

Without the full live-consent contract this command refuses before setup
services are constructed and prints `REFUSED_LIVE_CONSENT_MISSING`. The
canonical live operator command uses the default `lxc_native` provider:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --live
```

Operators may select a managed LXC backend explicitly:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world --lxc-backend lxd setup run --live
PYTHONPATH=src python3 -m tiny_swarm_world --lxc-backend incus setup run --live
```

Multipass is a legacy/fallback path and must be requested explicitly:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world --node-provider multipass_legacy setup run --live
```

For repeatable WSL/Linux operator runs with evidence capture, use the repository
wrapper:

```bash
./install.sh
```

The wrapper records run context, setup logs, and the setup exit code under
`.tiny-swarm-world/evidence/installation-tests/`. It loads or generates local
`TSW_*` secrets in `.tiny-swarm-world/local/live-installation.env` without
printing secret values, then asks for an explicit live-installation confirmation
before calling the canonical setup workflow.

With live consent, it sequences setup preflight, platform, artifact,
deployment, and final verification phases. Current live behavior remains
fail-closed where verification, readiness, credentials, or resource
requirements are incomplete.

---

## Operator Safety Model

Normal `platform init`, `platform reconcile`, and `setup run` are
non-destructive: they do not select destructive cleanup catalogs. Mutating
workflows are still live infrastructure operations. They require all of these
controls before application services are constructed:

- `--live`
- answering `y` at the short live-infrastructure confirmation prompt

The current default provider is `lxc_native`. `platform init` selects the
LXD/Incus provider path after provider readiness checks and blocks before
mutation when backend selection, daemon access, WSL2 capability, or profile
requirements are not satisfied. After accepted live consent, default
`platform init` continues from LXC node lifecycle into Docker Engine setup and
Docker Swarm bootstrap inside `swarm-manager`, `swarm-worker-1`, and
`swarm-worker-2`. Default `platform reconcile` is currently a verified no-op
boundary for `lxc_native`; default artifact and deployment workflows still
block at provider boundaries until provider-native publication and deployment
contracts are wired. Explicit `--node-provider multipass_legacy` keeps the old
Multipass fallback behavior visible and isolated.

`platform reset` and `platform destroy` additionally require
`RESET_TINY_SWARM_PLATFORM` or `DESTROY_TINY_SWARM_PLATFORM` through
`--confirm`. The confirmation contracts are implemented, but destructive
reset/destroy steps remain blocked until retention semantics are implemented.

These behaviors are verified by unit tests, architecture checks, and static
quality gates. This repository workflow did not run live LXD, Incus, LXC
container, Multipass, Docker Swarm, compose, netplan, socat, Portainer, Nexus,
Jenkins, RabbitMQ, SonarQube, Swagger/NGINX, Vaultwarden, image build, image
push, or stack deployment commands.

Optional live smoke validation is a separate operator action, not part of the
default quality gate. Run it only on a disposable or recoverable local target
after reviewing the live-operation surface catalog:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --live
```

When prompted, answer `y` only if changing the local LXD/Incus/LXC or explicit
Multipass legacy provider state, Docker Swarm, networking, Portainer, Nexus,
Jenkins, RabbitMQ, SonarQube, and Swagger/NGINX environment is intentional.

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
- Keep default stack deployment blocked until provider-native deployment contracts are wired

Where to find the scripts/services:
- `src/tiny_swarm_world/application/services/platform`
- `src/tiny_swarm_world/application/ports/node_provider`
- `infra/config/node-providers`
- `src/tiny_swarm_world/application/services/multipass` for explicit legacy/fallback behavior
- `src/tiny_swarm_world/application/services/network`
- `src/tiny_swarm_world/application/services/commands`
- `infra/swarm`
- `infra/compose`

List the supported workflow-level commands first:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world --list-workflows
```

Run only the workflow you explicitly intend to execute, for example:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world platform verify
```

For the autonomous setup flow, `setup run` without `--live` is the safe refusal
probe:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run
```

The canonical live operator command is:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --live
```

Platform workflows are constructed through the infrastructure composition root
in `src/tiny_swarm_world/infrastructure/composition.py`. Mutating workflows
such as `platform init`, `platform reconcile`, and `setup run` require
live-infrastructure consent before services are constructed. `setup run`
orchestrates only non-destructive setup phases and reports refused, blocked,
resource-gated, failed-to-apply, failed-to-verify, failed, or completed states
without treating missing verification as success. `platform reset` and
`platform destroy` additionally require the exact reset or destroy confirmation
phrase. Direct no-argument construction from the old `docker` layout is no
longer supported. Use `build_application_services()` for the standard local
wiring, or pass compatible port implementations in tests.

The canonical setup path is the workflow-level Python command. Former direct
preparation scripts under `infra/prepare` and host-side compose orchestration
scripts under `infra/compose` have been retired so service bootstrap, image
publication, and stack deployment cannot bypass the CLI consent gate. The
canonical static classification is maintained in
`documentation/system/live-operation-surfaces.adoc`.

Image publication and stack deployment are owned by workflow-level setup
boundaries. On the default `lxc_native` path they remain blocked until
provider-native artifact and deployment contracts are wired. Stack definitions
live under `infra/config/compose`; image build contexts live under
`infra/compose`.

The full guided setup selects the `service-access` management stack profile by
default. Its compose definition lives under
`infra/config/compose/service-access/docker-compose.yml`, and its dashboard
and NGINX assets are image-packaged under `infra/compose/service-access/**`.
After a verified provider-specific live deployment, the dashboard is intended
to be the management landing page at `http://localhost`. A central
service-access NGINX is the accepted routing design for stable paths such as
`/jenkins`, `/nexus`, `/portainer`, `/rabbitmq`, `/sonarqube`, `/swagger` and
`/vaultwarden`. The table shows users and Vaultwarden item references;
password values are visible only in Vaultwarden's authenticated UI. Operators
who intentionally want the older base service set can pass
`--service-profile default`.

The service-access stack needs a pre-existing external Swarm secret for the
Vaultwarden administrator token. The default secret name is
`tsw_vaultwarden_admin_token`, and operators may override the name with
`TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET`. Provider-native deployment must check
that the configured external Swarm input is observable before uploading the
stack and record only redacted presence/source evidence.

Live-operation surface summary:

| Path | Status |
| --- | --- |
| `src/tiny_swarm_world/__main__.py` | Supported workflow-level entry point with live-consent and confirmation contracts. |
| `infra/prepare/**` | Retired former direct service preparation surface; no executable setup helpers are kept there. |
| `infra/config/compose/**/docker-compose.yml` | Supported stack assets used by the Python setup workflow. |
| `infra/compose/**/Dockerfile` | Supported image source assets used by the Python setup workflow. |
| `infra/swarm/**` | Legacy live-infrastructure surface; not a supported workflow entry point. |

See `documentation/system/live-operation-surfaces.adoc` for the full
classification and credential/host-specific data rules.

---

## Configuration

- Compose stack files live under `infra/config/compose`; image build contexts
  and service image configuration live under `infra/compose`.
- Node-provider defaults live under `infra/config/node-providers`.
- Desired product configuration may live under `infra/config`.
- Observed inventory and verification evidence are local runtime artifacts
  under `.tiny-swarm-world/`; this path is ignored and must not be committed.
- Networking helpers and legacy netplan templates: `infra/config/network`.
- Legacy VM definitions and templates: `infra/config/vm`.
- Logs: `.tiny-swarm-world/logs`.
- Python settings can be provided via environment variables or `.env` when supported by specific modules.

---

## Project Structure (high-level)

- `src/tiny_swarm_world/domain`, `src/tiny_swarm_world/application`, `src/tiny_swarm_world/infrastructure` - hexagonal architecture layers
- `infra/prepare` - retired notes for former direct service preparation helpers
- `infra/compose` - image build contexts and related service image assets
- `infra/swarm` - swarm-related scripts/config
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
- `python3 -m pip install ruff mypy import-linter`

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
- Do not run live LXD, Incus, LXC container lifecycle, Multipass, Docker
  Swarm, netplan, or service-bootstrap commands as part of the development
  quality gate.

---

## Troubleshooting

- LXC-native provider not ready: verify `incus version`/`incus info` or
  `lxc version`/`lxc info`, and select `--lxc-backend` if both backends are
  installed.
- Multipass not found: this matters only for explicit
  `--node-provider multipass_legacy` runs. Ensure Multipass is installed and
  accessible on `PATH` before using the legacy provider.
- Docker connection issues: Verify Docker Engine or the Docker CLI target is available and your user has permission to access the Docker socket.
- WSL2 networking/ports: Install `socat` and review `infra/config/network` for port-forwarding helpers.
- Python import errors: Run commands from the repository root and set `PYTHONPATH=src` for direct script execution.

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

- Portainer: https://www.portainer.io/
- LXD: https://documentation.ubuntu.com/lxd/
- Incus: https://linuxcontainers.org/incus/
- LXC: https://linuxcontainers.org/lxc/
- Multipass: https://multipass.run/
- Docker Swarm: https://docs.docker.com/engine/swarm/
