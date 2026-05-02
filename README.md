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
- Modular infrastructure in `docker/prepare` and `docker/compose`.
- WSL2 networking support via socat and netplan helpers.
- Rich test suite and clear separation between domain, application, and infrastructure layers.

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
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install ruff mypy import-linter
```

4. Run the development quality gate

```bash
python docker/quality_gate.py quality
```

5. Run the current application entry point

```bash
PYTHONPATH=docker python docker/tiny_swarm_world.py
```

The entry point currently lists configured Multipass VM IP addresses. Live provisioning steps exist in code, but are intentionally commented until a developer enables the required infrastructure actions.

---

## Provisioning and Running the Stack

The repository contains Python services to prepare your local swarm cluster on Multipass VMs. Typical steps:

- Initialize (create) Multipass VMs
- Configure networking (netplan)
- Install Docker on each VM
- Initialize Docker Swarm and join nodes
- Deploy optional service stacks (Portainer, Nexus, Jenkins, etc.)

Where to find the scripts/services:
- `docker/application/services/multipass`
- `docker/application/services/network`
- `docker/swarm`
- `docker/compose`

In `docker/tiny_swarm_world.py` you can see which infrastructure steps are invoked. Many actions are present but commented. Enable only the steps you need, for example Multipass initialization, Docker installation, or Swarm initialization, then run:

```bash
PYTHONPATH=docker python docker/tiny_swarm_world.py
```

Portainer setup is prepared from the repository root with:

```bash
cd docker/prepare
./prepare.sh
```

Nexus bootstrap can be run directly when Portainer and the target endpoint are available:

```bash
python3 docker/prepare/nexus/setup.py
```

Deploying all compose stacks through Portainer is handled by:

```bash
cd docker/compose
./upload_all_stacks.sh -u admin -p '<password>'
```

---

## Configuration

- Compose files and service configurations live under `docker/compose` and `docker/config`.
- Networking helpers and netplan templates: `docker/config/network`.
- VM definitions and templates: `docker/config/vm`.
- Logs: `docker/logs` and `logs`.
- Python settings can be provided via environment variables or `.env` when supported by specific modules.

---

## Project Structure (high-level)

- `docker/domain`, `docker/application`, `docker/infrastructure` - hexagonal architecture layers
- `docker/prepare` - one-off preparation artifacts, for example Nexus and Portainer
- `docker/compose` - docker-compose stacks ready for deployment
- `docker/swarm` - swarm-related scripts/config
- `documentation` - arc42, user guides, deployment notes
- `tests` - unit and integration tests for adapters, services, and domain logic
- `src/main/java` - auxiliary Java code if needed by the ecosystem

Explore documentation for deeper architecture details:
- `documentation/arc42`
- `documentation/system`
- `documentation/user_guide`
- `documentation/deployment`

---

## Development Quality Gate

The development quality gate is provided by `docker/quality_gate.py`. Run it
from a Linux or WSL shell at the repository root.

Prepare a local environment:

- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `python -m pip install --upgrade pip`
- `python -m pip install -r requirements.txt`
- `python -m pip install ruff mypy import-linter`

Run the full gate before handing off a change:

- `python3 docker/quality_gate.py quality`

Run individual gates while developing:

- `python3 docker/quality_gate.py lint`
- `python3 docker/quality_gate.py arch-lint`
- `python3 docker/quality_gate.py arch-tests`
- `python3 docker/quality_gate.py typecheck`
- `python3 docker/quality_gate.py test`

Notes:

- The runner sets `PYTHONPATH=docker` automatically and uses the repository-root
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
- WSL2 networking/ports: Install `socat` and review `docker/config/network` for port-forwarding helpers.
- Python import errors: Run commands from the repository root and set `PYTHONPATH=docker` for direct script execution.

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

