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
- Service-access management surface:
  - static landing page for server links and credential references
  - Vaultwarden credential store behind service-access NGINX
  - password values available only through Vaultwarden's authenticated UI
- Modular infrastructure assets in `infra/config` and `infra/compose`, driven by the Python setup workflow.
- WSL2 networking support via socat and netplan helpers.
- Rich test suite and enforced separation between domain, application, and infrastructure layers.

---

## Prerequisites

- Linux host or WSL2 shell on Windows
- Python 3.12
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

Running the module without arguments does not execute infrastructure commands.
Use an explicit workflow selection before running automation:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world platform verify
```

Mutating workflows can call Multipass, Docker, networking, or other local
infrastructure commands. They require the live-infrastructure consent controls.
Destructive workflows also require the exact `--confirm` phrase shown by the
workflow contract.

The safe setup probe is `setup run` without `--live`:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run
```

Without the full live-consent contract this command refuses before setup
services are constructed and prints `REFUSED_LIVE_CONSENT_MISSING`. The
canonical live operator command is:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --live
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
non-destructive: they do not select the Multipass cleanup catalog that contains
VM delete/purge commands. Mutating workflows are still live infrastructure
operations. They require all of these controls before application services are
constructed:

- `--live`
- answering `y` at the short live-infrastructure confirmation prompt

At the current system-unification baseline, `platform init` and
`platform reconcile` still return `blocked` before live steps until
command-backed verification contracts are implemented. `setup run` is the
supported setup orchestrator and preserves the same fail-closed behavior across
preflight, platform, artifact, deployment, and final verification phases.

`platform reset` and `platform destroy` additionally require
`RESET_TINY_SWARM_PLATFORM` or `DESTROY_TINY_SWARM_PLATFORM` through
`--confirm`. The confirmation contracts are implemented, but destructive
reset/destroy steps remain blocked until retention semantics are implemented.

These behaviors are verified by unit tests, architecture checks, and static
quality gates. This repository workflow did not run live Multipass, Docker
Swarm, compose, netplan, socat, Portainer, Nexus, Jenkins, RabbitMQ,
SonarQube, Swagger/NGINX, Vaultwarden, image build, image push, or stack
deployment commands.

Optional live smoke validation is a separate operator action, not part of the
default quality gate. Run it only on a disposable or recoverable local target
after reviewing the live-operation surface catalog:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --live
```

When prompted, answer `y` only if changing the local Multipass, Docker Swarm,
networking, Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, and Swagger/NGINX
environment is intentional.

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

Image publication and stack deployment are handled by the workflow-level setup
command. Stack definitions live under `infra/config/compose`; image build
contexts live under `infra/compose`.

The full guided setup now includes the `service-access` management stack. Its
compose definition lives under
`infra/config/compose/service-access/docker-compose.yml`, and its dashboard
and NGINX assets are image-packaged under `infra/compose/service-access/**`.
The dashboard is the installed landing page at `http://localhost`. A central
service-access NGINX owns the local root route and redirects stable paths such
as `/jenkins`, `/nexus`, `/portainer`, `/rabbitmq`, `/sonarqube`, `/swagger`
and `/vaultwarden` to the matching local service route. The table shows users
and Vaultwarden item references; password values are visible only in
Vaultwarden's authenticated UI. Operators who intentionally want the older base
service set can pass `--service-profile default`.

The service-access stack needs a pre-existing external Swarm secret for the
Vaultwarden administrator token. The default secret name is
`tsw_vaultwarden_admin_token`, and operators may override the name with
`TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET`. The setup checks that the configured
external Swarm input is observable before uploading the stack and records only
redacted presence/source evidence.

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
- Desired product configuration may live under `infra/config`.
- Observed inventory and verification evidence are local runtime artifacts
  under `.tiny-swarm-world/`; this path is ignored and must not be committed.
- Networking helpers and netplan templates: `infra/config/network`.
- VM definitions and templates: `infra/config/vm`.
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

No license has been declared in this repository. Do not assume reuse rights
until a `LICENSE` file or explicit license statement is added.

---

## Links

- Portainer: https://www.portainer.io/
- Multipass: https://multipass.run/
- Docker Swarm: https://docs.docker.com/engine/swarm/
