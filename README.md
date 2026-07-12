# Tiny Swarm World

Tiny Swarm World is a local development and test infrastructure for simulating a production-like Docker Swarm microservices environment on a developer machine.

The default node-provider direction is **managed LXC through Incus**. Tiny Swarm World provisions Docker Swarm nodes as managed LXC instances and then bootstraps Docker Engine, Swarm, and the selected service stacks behind guarded workflow boundaries.

The live-operation surface catalog is maintained in `documentation/system/live-operation-surfaces.adoc`.

This README gives you a practical operator entry point:

1. Prepare WSL2 or Linux.
2. Install and initialize Incus.
3. Prepare the Python runtime.
4. Run the guarded Tiny Swarm World installer.
5. Diagnose common local setup problems.

---

## Overview

Use Tiny Swarm World to:

- Develop and test Docker Swarm-oriented automation boundaries.
- Keep compose stack deployment behind reviewed setup contracts.
- Model service management and observation through Portainer-facing contracts.
- Recreate cloud-like environments locally from a WSL2 or Linux shell without cloud costs.
- Validate local infrastructure workflows before applying them to more expensive or remote targets.

The system follows a hexagonal architecture and provides Python automation for provisioning, orchestration, deployment, and verification.

---

## Features

- LXC-native node-provider selection through Incus.
- LXC-native Docker Engine setup inside managed LXC nodes.
- Docker Swarm bootstrap for manager and worker nodes.
- Fail-closed workflow boundaries for provider-native platform, artifact, and deployment behavior.
- Portainer-facing service management contracts and compose assets.
- Component configuration assets for:
  - Portainer
  - Nexus
  - Jenkins
  - Apache Pulsar
  - SonarQube
  - Swagger + NGINX
  - Infisical
  - Service-access dashboard
- WSL2 capability checks for managed LXC providers.
- Optional WSL2 `socat` forwarding for selected host access cases.
- Rich test suite and enforced separation between domain, application, and infrastructure layers.

---

## Supported Local Runtime

Tiny Swarm World is intended to run from:

- Native Linux shell, or
- Ubuntu on WSL2 with systemd enabled.

The default provider is:

```text
lxc_native
```

The preferred backend is:

```text
incus
```

---

## Prerequisites

Required:

- Windows with WSL2, or native Linux
- Ubuntu-based shell recommended
- systemd enabled when running under WSL2
- Python 3.12 or newer
- Git
- Incus installed and initialized
- `incus` client access for the current user
- Enough disk space for LXC images, Docker images, and service data

Recommended:

- At least 20 GiB free disk space
- 16 GiB RAM or more for the full service-access profile
- `socat` when WSL2 host port-forwarding is required
- Docker CLI for local diagnostics
- PyCharm or IntelliJ IDEA

---

# WSL/Linux Preinstall

This section describes the host preparation expected before running the Tiny Swarm World installer.

> In this project context, “LXC installation” means installing **Incus** and using the `incus` CLI to create managed Linux containers.

---

## 1. WSL2 Preparation

Run setup commands from inside the Linux/WSL shell. Verify the runtime from the
distribution itself:

```bash
uname -a
ps -p 1 -o comm=
```

Expected:

```text
VERSION 2
```

If the distribution is not WSL2, convert or recreate it as WSL2 outside this
repository workflow, then return to the Linux shell.

Restart Ubuntu:

Restart the WSL distribution from your normal host workflow, then continue in
the Linux shell.

---

## 2. Enable systemd in WSL2

Incus, Docker, and several service workflows expect a systemd-based environment.

Inside Ubuntu/WSL:

```bash
sudo tee /etc/wsl.conf >/dev/null <<'EOF'
[boot]
systemd=true
EOF
```

Exit Ubuntu:

```bash
exit
```

Restart the WSL distribution so systemd is enabled for the next Linux shell.

Verify:

```bash
ps -p 1 -o comm=
```

Expected:

```text
systemd
```

If this does not show `systemd`, do not continue with Incus setup yet.

---

## 3. Install Base Packages

Inside Ubuntu/WSL or native Ubuntu:

```bash
sudo apt update
sudo apt install -y \
  ca-certificates \
  curl \
  git \
  jq \
  make \
  unzip \
  zip \
  rsync \
  socat \
  build-essential \
  python3 \
  python3-venv \
  python3-pip \
  snapd
```

Start and verify Snap:

```bash
sudo systemctl enable --now snapd
sudo systemctl status snapd --no-pager
```

Ensure `/snap/bin` is available:

```bash
echo 'export PATH="$PATH:/snap/bin"' >> ~/.bashrc
source ~/.bashrc
```

---

## 4. Install And Initialize Incus

Install Incus using the package source recommended for your Linux distribution,
then initialize the local daemon before running Tiny Swarm World. For a WSL2
developer setup, use a simple `dir` storage backend first.

Verify the selected backend from the same shell that will run setup:

```bash
incus version
incus info
```

Expected project defaults:

```text
bridge: incusbr0
storage pool: default
```

---

## 5. Verify Incus Profile And Storage

Run:

```bash
incus storage list
incus network list
incus profile show default
```

The important default profile parts are:

```yaml
root:
  path: /
  pool: default
  type: disk
```

and:

```yaml
eth0:
  name: eth0
  network: incusbr0
  type: nic
```

---

## 6. Fix Missing Incus Root Device

If this error appears:

```text
Failed instance creation: Failed creating instance record:
Failed initialising instance: Failed getting root disk:
No root device could be found
```

then the default profile has no root disk device.

Check:

```bash
incus storage list
incus profile show default
```

If the storage pool `default` exists, add the root disk:

```bash
incus profile device add default root disk path=/ pool=default
```

If the network device is missing, add it:

```bash
incus profile device add default eth0 nic name=eth0 network=incusbr0
```

Verify again:

```bash
incus profile show default
```

---

## 7. Test Incus Container Creation

Create a temporary test container:

```bash
incus launch images:ubuntu/24.04 test-incus
incus list
```

Open a shell inside the container:

```bash
incus exec test-incus -- bash
```

Inside the container:

```bash
cat /etc/os-release
exit
```

Delete the test container:

```bash
incus delete test-incus --force
```

If this succeeds, the Incus baseline is ready.

---

## 8. Host Kernel and Bridge Settings

For LXC, Docker, and Swarm networking, enable forwarding and bridge netfilter settings where available.

```bash
sudo modprobe br_netfilter 2>/dev/null || true

sudo tee /etc/sysctl.d/99-tiny-swarm-world.conf >/dev/null <<'EOF'
net.bridge.bridge-nf-call-iptables=1
net.bridge.bridge-nf-call-ip6tables=1
net.ipv4.ip_forward=1
EOF

sudo sysctl --system
```

Verify:

```bash
sysctl net.ipv4.ip_forward
sysctl net.bridge.bridge-nf-call-iptables
```

Expected:

```text
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
```

If bridge sysctls are unavailable in WSL, document the host evidence and continue only if the Tiny Swarm World preflight accepts the environment.

---

## 9. Optional Docker CLI on Host

The default `lxc_native` path installs and verifies Docker Engine inside managed LXC nodes after live consent. Host Docker is still useful for diagnostics.

Install host Docker tools only if needed:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Restart WSL or log out and back in.

Verify:

```bash
docker version
docker ps
```

If Docker reports permission errors:

```bash
groups
ls -l /var/run/docker.sock
```

The current user must be in the `docker` group.

---

# Python Runtime Setup

Tiny Swarm World supports Python 3.12 or newer. CI validates the minimum
supported version, while newer Linux/WSL runtimes remain supported through the
declared dependency ranges.

The runtime dependencies use Python-3.12+-compatible ranges:

```txt
pydantic>=2.12,<3
PyYAML>=6.0.3,<7
requests>=2.34.2,<3
ruamel.yaml>=0.18.16,<0.19
```

Create a clean virtual environment:

```bash
cd /mnt/d/Projects/Tiny-Swarm-World

deactivate 2>/dev/null || true
rm -rf .venv

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install --require-hashes -r requirements.lock
python -m pip install --no-deps -e .
```

Verify imports:

```bash
python - <<'PY'
import pydantic
import pydantic_core
import yaml
import requests
import ruamel.yaml

print("pydantic", pydantic.__version__)
print("pydantic_core", pydantic_core.__version__)
print("PyYAML", yaml.__version__)
print("requests", requests.__version__)
print("ruamel.yaml", ruamel.yaml.__version__)
print("OK")
PY
```

---

# Quick Start

## 1. Clone the repository

```bash
git clone https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World.git
cd Tiny-Swarm-World
```

## 2. Create and activate the virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install runtime dependencies

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install --require-hashes -r requirements.lock
python -m pip install --no-deps -e .
```

## 4. Install development tools

```bash
python -m pip install -r requirements-dev.txt
```

## 5. Run the quality gate

```bash
python tools/quality_gate.py quality
```

## 6. Inspect available workflows

```bash
tiny-swarm-world --list-workflows
```

## 7. Run static preflight

```bash
tiny-swarm-world --preflight
```

Running the module without explicit workflow arguments does not execute infrastructure commands.

---

# Running the Installer

The repository wrapper is:

```bash
./install.sh
```

For a deliberate fresh test-system reset and headless run:

```bash
source .venv/bin/activate

PATH="$PWD/.venv/bin:$PATH" \
PYTHONPATH="$PWD/src" \
./install.sh --headless --confirm-reset --non-interactive-live-approval
```

The wrapper delegates policy, secret handling, host-runtime detection, evidence layout, reset sequencing, and headless execution to the Python installer entry point.

Evidence is written below:

```text
.tiny-swarm-world/evidence/installation-tests/<host-runtime>/
```

where `<host-runtime>` is usually:

```text
wsl2
```

or:

```text
native_linux
```

Local generated secrets are stored in:

```text
.tiny-swarm-world/local/live-installation.env
```

This file must not be committed.

---

# Live Consent and Safety Model

Mutating workflows can call Incus, Docker, networking, Portainer, Nexus, Jenkins, Pulsar, SonarQube, Swagger/NGINX, Infisical, image build, image push, and stack deployment commands.

Normal mutating workflows require live consent before application services are constructed.

Examples:

```bash
tiny-swarm-world setup run --live
tiny-swarm-world platform init --live
tiny-swarm-world platform reconcile --live
tiny-swarm-world platform expose --live
```

Destructive workflows require additional confirmation phrases.

Reset:

```bash
tiny-swarm-world platform reset --live --confirm RESET_TINY_SWARM_PLATFORM
```

Destroy:

```bash
tiny-swarm-world platform destroy --live --confirm DESTROY_TINY_SWARM_PLATFORM
```

The install wrapper maps deliberate test-system automation to the governed reset/setup flow:

```bash
./install.sh --headless --confirm-reset --non-interactive-live-approval
```

---

# Provider Backend Selection

Default provider:

```text
lxc_native
```

Backend selection order:

1. Explicit `--lxc-backend`
2. `backend_selection.preferred_backend`
3. Ordered `backend_selection.candidates` from `infra/config/node-providers/provider_config.yaml`

Explicit Incus:

```bash
tiny-swarm-world --lxc-backend incus setup run --live
```

---

# Service Profile

The guided setup selects the `service-access` management stack profile by default.

Default installer command:

```bash
./install.sh --headless --confirm-reset --non-interactive-live-approval
```

Alternative base service set:

```bash
./install.sh --service-profile default --headless --confirm-reset --non-interactive-live-approval
```

---

# Configuration Files

Important configuration locations:

```text
infra/config/node-providers/provider_config.yaml
infra/config/installation-plan.yaml
infra/config/ports.yaml
infra/config/services.yml
infra/config/health-checks.yaml
infra/config/validation-plan.yaml
infra/config/compose/
infra/config/secrets/infisical-secrets.yaml
```

Local runtime artifacts:

```text
.tiny-swarm-world/
.tiny-swarm-world/logs/
.tiny-swarm-world/evidence/
.tiny-swarm-world/local/live-installation.env
```

Do not commit local runtime artifacts or secret-bearing files.

---

# Minimal Preinstall Smoke Test

Run this from the repository root after creating `.venv`.

```bash
set -e

echo "[1] systemd"
test "$(ps -p 1 -o comm=)" = "systemd"

echo "[2] incus"
incus version >/dev/null
incus storage list >/dev/null
incus profile show default | grep -q "root:"

echo "[4] test container"
incus launch images:ubuntu/24.04 tsw-smoke-test
incus exec tsw-smoke-test -- true
incus delete tsw-smoke-test --force

echo "[5] python"
source .venv/bin/activate
python -c "import pydantic; print('pydantic ok')"

echo "Preinstall OK"
```

---

# Diagnostics

## systemd

```bash
ps -p 1 -o comm=
```

## Incus

```bash
incus version
incus info
incus storage list
incus network list
incus profile show default
incus list
```

## Docker

```bash
docker context ls
docker version
docker ps
```

## Python

```bash
which python
python --version
python -m pip --version
python -c "import pydantic; print(pydantic.__version__)"
```

---

# Troubleshooting

## `ModuleNotFoundError: No module named 'pydantic'`

Cause: the installer is not using the project `.venv`, or dependencies are not installed.

Fix:

```bash
cd /mnt/d/Projects/Tiny-Swarm-World
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.lock
python -m pip install --no-deps -e .
```

Run installer with venv and source path forced:

```bash
PATH="$PWD/.venv/bin:$PATH" \
PYTHONPATH="$PWD/src" \
./install.sh --headless --confirm-reset --non-interactive-live-approval
```

## `pydantic-core` build fails on a supported Python version

Cause: an old Pydantic line is pinned.

Use the declared Python-3.12+-compatible dependencies:

```txt
pydantic>=2.12,<3
PyYAML>=6.0.3,<7
requests>=2.34.2,<3
ruamel.yaml>=0.18.16,<0.19
```

Then rebuild the venv:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install --require-hashes -r requirements.lock
python -m pip install --no-deps -e .
```

## `Failed getting root disk: No root device could be found`

Cause: the Incus default profile has no root disk.

Fix:

```bash
incus profile device add default root disk path=/ pool=default
```

If network is missing:

```bash
incus profile device add default eth0 nic name=eth0 network=incusbr0
```

## `snap: command not found`

Fix:

```bash
sudo apt update
sudo apt install -y snapd
sudo systemctl enable --now snapd
```

## `System has not been booted with systemd`

Fix `/etc/wsl.conf`:

```ini
[boot]
systemd=true
```

Then restart the WSL distribution outside this repository workflow and rerun
the Linux shell checks.

## Docker permission denied

Fix:

```bash
sudo usermod -aG docker "$USER"
```

Then restart the shell or WSL.

## WSL distribution disk mounted read-only

Do not continue with installer operations. Back up important data first.

If the distribution still starts read-only, back it up before repair or
deletion and rerun the checks from a fresh Linux/WSL shell.

---

# Project Structure

High-level directories:

```text
src/tiny_swarm_world/domain
src/tiny_swarm_world/application
src/tiny_swarm_world/infrastructure
infra/config/compose
infra/config/node-providers
documentation
tests
tools
```

The architecture follows a domain/application/infrastructure split.

---

# Development Quality Gate

Prepare environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install --require-hashes -r requirements.lock
python -m pip install --no-deps -e .
python -m pip install -r requirements-dev.txt
```

Run full gate:

```bash
python tools/quality_gate.py quality
```

Run individual checks:

```bash
python tools/quality_gate.py lint
python tools/quality_gate.py arch-lint
python tools/quality_gate.py arch-tests
python tools/quality_gate.py typecheck
python tools/quality_gate.py test
```

Run explicit local supply-chain checks separately from the default quality
gate:

```bash
python tools/security_gate.py dependencies
python tools/security_gate.py sbom
python tools/security_gate.py container-config  # requires explicit Trivy installation
```

Dependency and SBOM policy lives under `documentation/security/`. Scanner
absence or missing image evidence is reported as missing, never as a pass.

Do not run live Incus lifecycle, Docker Swarm, image build, image push, or service bootstrap commands as part of the development quality gate.

---

# Skill and Agent Governance

Tiny Swarm World agent and skill work is governed by:

```text
AGENTS.md
QUALITY.md
.agents/
.codex/
documentation/process/skills/audit/
```

Canonical governance navigation:

```text
documentation/process/skills/audit/skill-registry.md
documentation/process/skills/audit/skill-registry.json
documentation/process/skills/audit/organigramm.md
documentation/process/skills/audit/owner-map.md
```

Project-specific skills live as discoverable files:

```text
.agents/skills/<skill-name>/SKILL.md
```

Grouped Markdown files are not authoritative skill entry points unless local discovery rules are changed by a later workflow.

The current agent model keeps Tiny Swarm World:

- Docker Swarm first
- Kubernetes-aware but not Kubernetes-first
- Python automation first
- Console/status UI oriented

It must not be reclassified as forensic analytics, a Spring Boot application, or a React frontend project.

---

# Links

- Incus: https://linuxcontainers.org/incus/
- LXC: https://linuxcontainers.org/lxc/
- Docker Swarm: https://docs.docker.com/engine/swarm/
- Portainer: https://www.portainer.io/
- WSL systemd documentation: https://learn.microsoft.com/windows/wsl/systemd
