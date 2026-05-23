# Tiny Swarm World

Tiny Swarm World is a local development and test infrastructure to simulate a production-like microservices environment on your machine. It combines Multipass-managed virtual machines with Docker Swarm and a set of pre-integrated developer services (Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, Swagger + NGINX).

This README gives you a clear entry point: what it is, how to set it up, how to run it, and where to find more documentation.

---

## Overview

Use Tiny Swarm World to:
- Develop and test distributed systems with real Docker Swarm orchestration.
- Deploy multiple docker-compose stacks into a managed Swarm cluster.
- Manage and observe services via Portainer.
- Recreate cloud-like environments locally from a WSL2 or Linux shell without cloud costs.

The system follows a hexagonal architecture and provides async Python automation for provisioning and orchestration.

---

## Features

- Multipass VMs lifecycle (create, initialize, restart).
- Automated Docker installation and Docker Swarm initialization on VMs.
- Centralized service management via Portainer.
- Pre-integrated components:
  - Nexus (local Docker + Maven repository)
  - Jenkins (CI/CD with configuration-as-code)
  - RabbitMQ (message broker)
  - SonarQube (static code analysis)
  - Swagger + NGINX (API documentation)
- Modular infrastructure in `infra/prepare` and `infra/compose`.
- WSL2 networking support via socat and netplan helpers.
- Rich test suite and enforced separation between domain, application, and infrastructure layers.

---

## Prerequisites

- Linux host or WSL2 shell on Windows
- Python 3.12 recommended; Python 3.10+ may work if the installed dependencies support it
- Git
- Multipass with the QEMU backend
- Docker Engine or Docker CLI access to the target Docker/Swarm environment
- socat if using WSL2 port-forwarding

Optional but recommended:
- An IDE such as PyCharm or IntelliJ IDEA

---

## Quick Start (Linux or WSL shell)

1. Clone the repository

```bash
git clone https://github.com/your-org/Tiny-Swarm-World.git
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

Running the module without arguments does not execute infrastructure commands.
Use an explicit workflow selection before running automation:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world platform verify
```

Mutating workflows can call Multipass, Docker, networking, or other local
infrastructure commands. They require the live-infrastructure consent controls.
Destructive workflows also require the exact `--confirm` phrase shown by the
workflow contract.

---

## Operator Safety Model

Normal `platform init` and `platform reconcile` are non-destructive: they do
not select the Multipass cleanup catalog that contains VM delete/purge
commands. Mutating workflows are still live infrastructure operations. They
require all of these controls before application services are constructed:

- `--live`
- `TSW_LIVE_INFRASTRUCTURE_CONSENT=I_UNDERSTAND_THIS_CHANGES_LOCAL_INFRASTRUCTURE`
- typing `RUN TINY SWARM WORLD LIVE INSTALLATION` at the prompt

`platform reset` and `platform destroy` additionally require
`RESET_TINY_SWARM_PLATFORM` or `DESTROY_TINY_SWARM_PLATFORM` through
`--confirm`. The confirmation contracts are implemented, but destructive
reset/destroy steps remain blocked until retention semantics are implemented.

These behaviors are verified by unit tests, architecture checks, and static
quality gates. This repository workflow did not run live Multipass, Docker
Swarm, compose, netplan, socat, Portainer, Nexus, Jenkins, RabbitMQ,
SonarQube, or Swagger/NGINX commands.

---

## Provisioning and Running the Stack

The repository contains Python services to prepare your local swarm cluster on Multipass VMs. Typical steps:

- Initialize (create) Multipass VMs
- Configure networking (netplan)
- Install Docker on each VM
- Initialize Docker Swarm and join nodes
- Deploy optional service stacks (Portainer, Nexus, Jenkins, etc.)

Where to find the scripts/services:
- `src/tiny_swarm_world/application/services/multipass`
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

Platform workflows are constructed through the infrastructure composition root
in `src/tiny_swarm_world/infrastructure/composition.py`. Mutating workflows
such as `platform init` and `platform reconcile` require live-infrastructure
consent before services are constructed. `platform reset` and
`platform destroy` additionally require the exact reset or destroy confirmation
phrase. Direct no-argument construction from the old `docker` layout is no
longer supported. Use `build_application_services()` for the standard local
wiring, or pass compatible port implementations in tests.

Portainer setup is prepared from the repository root with:

Direct scripts under `infra/prepare` and `infra/compose` bypass the
workflow-level CLI consent guard. Treat them as live operator actions and run
them only after reviewing the target environment and script contents.

```bash
cd infra/prepare
./prepare.sh
```

Nexus bootstrap can be run directly when Portainer and the target endpoint are available:

```bash
python3 infra/prepare/nexus/setup.py
```

Deploying all compose stacks through Portainer is handled by:

```bash
cd infra/compose
./upload_all_stacks.sh -u admin -p '<password>'
```

`upload_all_stacks.sh` talks directly to Portainer and can delete or recreate
stacks.

Legacy and transitional scripts:

| Path | Status |
| --- | --- |
| `infra/swarm/**` | Legacy live-infrastructure surface; not a supported workflow entry point. |
| `infra/prepare/portainer/portain_setup.py` | Transitional script with live Docker, Multipass, socat, and networking behavior. |
| `infra/prepare/nexus/*.sh` | Legacy shell helpers with local defaults; prefer the Python `setup.py` path when intentionally bootstrapping Nexus. |
| `infra/compose/create_dockerfiles.sh` | Direct build/push helper; not part of the default quality gate. |
| `infra/compose/upload_all_stacks.sh` | Direct Portainer uploader; live stack mutation script. |

---

## Configuration

- Compose files and service configurations live under `infra/compose` and `infra/config`.
- Desired product configuration may live under `infra/config`.
- Observed inventory and verification evidence are local runtime artifacts
  under `.tiny-swarm-world/`; this path is ignored and must not be committed.
- Networking helpers and netplan templates: `infra/config/network`.
- VM definitions and templates: `infra/config/vm`.
- Logs: `infra/logs`.
- Python settings can be provided via environment variables or `.env` when supported by specific modules.

---

## Project Structure (high-level)

- `src/tiny_swarm_world/domain`, `src/tiny_swarm_world/application`, `src/tiny_swarm_world/infrastructure` - hexagonal architecture layers
- `infra/prepare` - one-off preparation artifacts, for example Nexus and Portainer
- `infra/compose` - docker-compose stacks ready for deployment
- `infra/swarm` - swarm-related scripts/config
- `documentation` - arc42, user guides, deployment notes
- `tests` - unit and integration tests for adapters, services, and domain logic
- `src/main/java` - example application that can be built and deployed into the prepared local system

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
- Do not run live Multipass, Docker Swarm, netplan, or service-bootstrap
  commands as part of the development quality gate.

---

## Troubleshooting

- Multipass not found: Ensure Multipass is installed and accessible on `PATH`.
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

Add your license information here (e.g., Apache-2.0, MIT). If a LICENSE file exists, it takes precedence.

---

## Links

- Portainer: https://www.portainer.io/
- Multipass: https://multipass.run/
- Docker Swarm: https://docs.docker.com/engine/swarm/
