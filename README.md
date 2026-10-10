# Tiny Swarm World

Tiny Swarm World creates a local development and test environment with Docker
Swarm, Portainer, Infisical, Nexus, Jenkins, Pulsar, SonarQube and supporting
services. It provisions managed Linux containers through Incus and runs Docker
Engine inside those containers.

The current implementation is the **Classic profile**. The
[RC1 decision](documentation/release/rc1-decision.md) records acceptance on
2026-09-13 for its named candidates; the
[October lifecycle validation](documentation/evidence/issue-363-final-validation-20261003.md)
records later scoped results. These results do not qualify the current bootstrap
changes or every supported host. See the
[bootstrap contract](documentation/contracts/bootstrap.md) for delivered stages
and remaining integration/live qualification work.

## Start here

| What you want to do | Read |
|---|---|
| Prepare a machine and install for the first time | [Installation guide](documentation/user_guide/installation.adoc) |
| Find service URLs and sign in | [Default logins](#default-logins-after-a-fresh-installation), [Service access and login](documentation/user_guide/usage.adoc#open-the-services) and [credential catalog](documentation/arc42/08_configuration/internal-test-credential-catalog.md) |
| Inspect or reconcile an existing installation | [Daily operation](documentation/user_guide/usage.adoc#daily-operation) |
| Diagnose a failed run | [Troubleshooting](documentation/user_guide/troubleshooting.adoc#first-response) |
| Change code or run development tests | [Developer Manual](documentation/manuals/developer-manual.md) |
| Understand architecture or extend runtime support | [Resulting architecture and runtime extension guide](documentation/arc42/05_analysis/arch-03-21-resulting-architecture.md) |
| Find architecture, security or audit references | [Documentation index](documentation/README.adoc) |

## Default logins after a fresh installation

For a successful fresh `./install.sh` installation using the standard
`internal-test` defaults, use these browser logins:

| Service | Username / email | Default password |
|---|---|---|
| Portainer | `admin` | `TSW1234STW5678` |
| Jenkins | `admin` | `TSW1234STW5678` |
| Nexus | `admin` | `TSW1234STW5678` |
| SonarQube | `admin` | `TSW1234STW5678!a` |
| Pulsar Manager | `admin` | `TSW1234STW5678` |
| Infisical | `admin@tiny-swarm-world.local` | `TSW1234STW5678` |
| Traefik dashboard | `admin` | `TSW1234STW5678` |

**INTERNAL/TEST ONLY:** These are public, disposable test credentials. Use them
only in an isolated, disposable test environment. Production, shared systems
and normal local operation require operator-owned credentials.

**Your own credentials take precedence.** If you supplied overrides, use the
values from your configured credential source. The documented location for
the protected `live-installation.env` override file is:

```text
~/.local/state/tiny-swarm-world/live-installation.env
```

This is `$HOME/.local/state/tiny-swarm-world/live-installation.env` for the
Linux/WSL user who ran the installer. If you selected another location through
`TSW_INSTALL_ENV_FILE`, use that path instead. In the installation shell, show
the selected path without printing any passwords:

```bash
printf '%s\n' "${TSW_INSTALL_ENV_FILE:-TSW_INSTALL_ENV_FILE is not set in this shell}"
```

Open the existing file in a private editor to look up your overrides. Exported
`TSW_*` credential values take precedence over file entries. The file is an
optional input; the installer does not automatically create it or save
environment-only overrides into it. In a new shell, an unset variable does not
tell you which file was selected during an earlier installation; check the
path you exported for that run.

Passwords changed in a service remain that service's current passwords and
are not automatically written back to this file; this table does not reset
existing accounts.

Start at [Service Access](https://service-access.tsw.local) for configured
service links. The installer does not print passwords, and the default
installation does not create a separate password file. You can use the
Infisical login above without first retrieving it from Infisical itself.
Service entries in Infisical are available only after synchronization.

The [canonical credential catalog](documentation/arc42/08_configuration/internal-test-credential-catalog.md)
documents all test values, API tokens and component-specific exceptions.
For custom credentials, follow the
[optional credential setup](documentation/user_guide/installation.adoc#operator-credential-overrides).

## Before you install

Use a native Linux or WSL2 shell. WSL2 needs systemd; Windows-native product
execution is not supported.

Prepare these prerequisites in the same shell and user account that will run
the installer:

- Python **3.12 or newer**, with virtual-environment support, and Git. The
  [compatibility workflow](.github/workflows/python-compatibility.yml) currently
  tests Python 3.12, 3.13 and 3.14.
- Incus installed and initialized, with usable storage, networking and profiles.
  `incus version` and `incus info` must work without `sudo`.
- Host networking and capacity checked against the
  [ready-for-install checklist](documentation/user_guide/installation.adoc#ready-for-install-checklist).
  Review kernel, scoped firewall and local-name preparation with
  `./prepare_linux.sh --dry-run`; see [network preparation](documentation/user_guide/network-preparation.md).
- For WSL2 Windows-browser access, the existing
  [Windows bridge prework](documentation/user_guide/installation.adoc#windows-wsl-prework).
  Native Linux does not need that bridge.

Windows-side lifecycle planning is available separately from product execution:
run `./prepare_windows.ps1 -Distro Ubuntu-24.04 -Preflight` in elevated Windows
PowerShell. The [Windows preparation guide](documentation/user_guide/windows-preparation.md)
explains selected-distro/systemd preparation, explicit candidate qualification consent,
account/restart boundaries and preserved state. Ordinary Apply remains blocked until
applicable live qualification; local tests do not qualify Windows versions.

If WSL setup reports `windows-wsl-bridge` / `state_invalid`, prepare the bridge
in Windows PowerShell as Administrator. If that preparation passes all
prerequisites but fails with `The Windows bridge service ACL did not reach the
required exact state.`, a leftover `.bridge-state.json.<id>.bak` file can be
the cause. Follow the [step-by-step bridge recovery](documentation/user_guide/troubleshooting.adoc#windows-wsl-bridge-acl)
to inspect and delete only the confirmed leftover backup, reinstall the bridge,
and return to the WSL installer. `--allow-wsl-windows-filesystem` only permits
the checkout location; it does not prepare the bridge.

The installer creates managed nodes and their Docker runtime. **It does not
install or initialize the host's Incus daemon.** A host Docker installation
does not replace Docker inside the managed nodes.

Prefer a checkout under the Linux home directory. A deliberate WSL2 checkout
under `/mnt/c`, `/mnt/d` or another Windows mount requires the explicit
filesystem exception described in the installation guide.

## Prepare the checkout

Run these commands after the host prerequisites are ready:

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World.git
cd Tiny-Swarm-World

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --require-hashes -r requirements.lock
python3 -m pip install --no-deps -e .
```

Install the runtime dependencies before calling the installer. The wrapper
imports Python modules before its internal dependency-bootstrap fallback can
run; cloning the repository alone is not a complete setup.

Inspect the available workflows and run static preflight:

```bash
tiny-swarm-world --list-workflows
tiny-swarm-world --preflight
```

For a checkout on the Linux filesystem (for example
`~/projects/Tiny-Swarm-World`), use the commands above. If you deliberately keep
the checkout on a Windows mount under WSL2 (for example `/mnt/d/Projects/`),
use the explicit filesystem exception:

```bash
tiny-swarm-world --allow-wsl-windows-filesystem --preflight
```

For **either checkout location**, if preflight reports missing `SECRET-TSW_*`
values, prepare or select a protected credential file before rerunning preflight:

```bash
export TSW_INSTALL_ENV_FILE="$HOME/.local/state/tiny-swarm-world/live-installation.env"
install -d -m 700 "$(dirname "$TSW_INSTALL_ENV_FILE")"
PYTHONPATH=src python3 tools/create_internal_test_env_file.py "$TSW_INSTALL_ENV_FILE"

# Linux filesystem checkout:
tiny-swarm-world --preflight

# Alternatively, a deliberate Windows-mounted checkout under WSL2:
tiny-swarm-world --allow-wsl-windows-filesystem --preflight
```

The command creates a protected file with the documented `INTERNAL/TEST ONLY`
catalog values only when no file exists; it preserves existing credentials.
These public default passwords and tokens are suitable only for an isolated,
disposable test system. A future production or shared deployment must use
operator-owned credentials instead. If an existing file has empty entries,
edit those entries locally before rerunning preflight. Keep
`TSW_INSTALL_ENV_FILE` exported in the same terminal for subsequent setup
commands, and repeat it in a new terminal. Preflight reads the selected file
directly; sourcing it is not necessary. Exported `TSW_*` values take precedence
over file entries. For guidance on which values to set, follow the
[optional credential setup](documentation/user_guide/installation.adoc#operator-credential-overrides).
The credential file must remain on the Linux filesystem with mode `0600` in
a user-owned `0700` directory, even when the checkout is on a Windows mount.
The filesystem exception does not provide missing secrets. The standard
`./install.sh` internal-test defaults described below are a separate installer
path; standalone preflight can require an explicit secret source.

Resolve reported blockers before installing. Static preflight does not prove
that services are running. Development tools and the full quality gate are
described in the [Developer Manual](documentation/manuals/developer-manual.md);
they are separate from preparing the runtime package.

## Install a fresh test environment

Review the [live-operation surface catalog](documentation/system/live-operation-surfaces.adoc)
for the commands that change nodes, networking, Docker, Swarm and service stacks.

The planned complete host bootstrap interface and delivery gaps are defined in
the [BOOT-W01 contract](documentation/contracts/bootstrap.md). Windows preparation
now includes W04 lifecycle and W05 capacity planning/configuration; aggregate
readiness and live qualification remain separate. BOOT-W02 provides the shared
Linux package/Python prerequisite stage.

On native Ubuntu 24.04 or 26.04 x86_64, prepare the host separately, then run the
non-destructive installer. The installer does not invoke host preparation:

Issue #427 uses a clean Ubuntu 26.04 host for installation qualification;
Ubuntu 24.04 remains a supported host path with separate live qualification.

```bash
./prepare_linux.sh --preflight
./prepare_linux.sh
./install.sh --preflight
./install.sh
```

`prepare_linux.sh` shows its package plan and requires the operator to type
`yes` before APT changes or local Python dependency bootstrap. From a complete
trusted release, missing Python >=3.12 and venv support are bootstrapped by the
shell boundary; Git is not needed to start preparation. Run as an ordinary user
from an owned Linux-native directory: only package, daemon startup and group
access actions elevate. The same preparation
command supports Ubuntu 24.04/26.04 x86_64 under WSL2 with systemd and the WSL
resource floor. After Python preparation, it shows and separately confirms
Incus startup/access and missing resolved storage, bridge and Swarm profiles.
Compatible resources are reused; collisions block without replacing them.
New `incus-admin` membership requires logout/login and a rerun before current-user
access is verified. If elevation fails, run `sudo -v` and review the plan again.
Incus readiness does not verify kernel controls, Windows configuration or services. `--dry-run` is
read-only for either script. The installer checks host, configuration,
credentials and setup readiness before creating installation evidence. The
installer reconciles on native Linux and WSL2 without resetting managed nodes,
data or credentials. WSL `--confirm-reset` explicitly requests the deprecated
destructive compatibility path; live approval alone never requests reset. See the
[installation guide](documentation/user_guide/installation.adoc) for recovery.

Windows preparation prints the selected registration/account handoff after its
lifecycle, resources and bridge are ready. Keep the trusted checkout in the
ordinary Linux account's `~/Tiny-Swarm-World`, or select its absolute Linux path:

```powershell
./prepare_windows.ps1 -Distro Ubuntu-24.04 -LinuxCheckout /home/operator/Tiny-Swarm-World -Preflight
```

Run the printed command to prepare Linux and then install with the same profile.
Each preparation stage keeps its own consent; a failed stage stops installation.
A missing/unsafe checkout blocks the handoff. Windows preparation never copies a
checkout or runs product Python on Windows. Windows capability readiness is
separate from Linux preparation and live service verification.

After completing the installation guide's host and networking checklist:

```bash
./install.sh
```

The default service profile is `service-access`. WSL installation asks for the
reset phrase `RESET_TINY_SWARM_PLATFORM`; both host modes require governed
live-operation consent.
`--headless` changes presentation; it does not make the operation read-only.

Native `service-access` requires at least **15 GiB host RAM**; WSL2 retains
a 16 GiB service-access profile floor. The W05 Windows plan also counts the
19 GiB default managed-node budget and 2 GiB WSL overhead: it needs at least
21 GiB configured WSL RAM while retaining Windows reserve. A 16 GiB physical
Windows host is therefore insufficient for the current node configuration.
See the [resource plan and overrides](documentation/user_guide/windows-preparation.md#capacity-plan-and-resource-overrides).
Managed-node capacity is checked separately. A local 8/6/3 GiB node configuration was installed and functionally
tested on an 18.73 GiB native host. The manager reached its 8 GiB limit, so this
run establishes limited operation with little manager reserve. See the
[native installation and memory results](documentation/evidence/issue-363-native-fresh-install-20261003.md)
and the [local configuration procedure](documentation/user_guide/installation.adoc#native-node-memory-budget).

The standard internal-test path needs **no credential file**. It uses
deterministic catalog values. These defaults are for isolated, disposable
internal testing; use the documented access boundary before exposing services.

If an override is needed, follow the
[optional credential setup](documentation/user_guide/installation.adoc#operator-credential-overrides).
A credential file must be user-owned, mode `0600`, inside a user-owned
`0700` directory on a Linux-native filesystem. The WSL source-path exception
does not relax that requirement.

## Open services and verify the result

After successful setup, the installer prints access targets and login
identifiers. Start with the configured Service Access route, normally
[https://service-access.tsw.local](https://service-access.tsw.local), when local
name resolution, forwarding and TLS trust are configured.

Use the [default login table above](#default-logins-after-a-fresh-installation)
for browser logins, or your protected source for an explicit override.
Portainer uses `admin`; Infisical uses an email address. Service-specific
exceptions are listed in the catalog. Passwords are not printed by the
installer, and a dashboard secret reference does not prove the item exists in
Infisical.

Check the platform:

```bash
tiny-swarm-world --service-profile service-access platform verify
```

Then sign in to the required services from the browser you intend to use.
An HTTP 200 response or a login page proves neither authentication nor a fully
working installation. See the
[verification steps](documentation/user_guide/installation.adoc#verify-installed-runtime).

If a route is unavailable, distinguish name resolution, forwarding, TLS,
service readiness and authentication using the
[troubleshooting guide](documentation/user_guide/troubleshooting.adoc#first-response).
Use the evidence directory printed for your run, inspect exit codes first,
and redact diagnostics before sharing them.

## Reconcile, reset and update are different operations

| Operation | Meaning |
|---|---|
| `platform verify` | Inspect the existing platform without repairing it. |
| `platform reconcile --live` | Reconcile managed platform state with explicit consent; it is not a complete application update. |
| `setup run --live` | Run the broader setup workflow without a reset; it still changes infrastructure. |
| `./prepare_linux.sh` | Prepare shared native/WSL2 Ubuntu prerequisites and Incus access/resources with staged confirmation. |
| `./install.sh` on native Linux | Verify preparation, then run setup without a reset. |
| `./install.sh` on WSL2 | Reconcile existing managed state; explicit WSL `--confirm-reset` alone selects deprecated destructive compatibility. |
| Product update | Preview and apply one supported stack/service image transition with the documented `platform update` contract. |

Use `platform update --stack ... --service ... --from-image ... --to-image ... --preview`
before an explicitly consented live apply. Use `platform update --recover
--stack ... --service ...` for the last recorded rollback transition. Pulling
new source code and running reconcile does not establish a supported upgrade.

See [Daily operation](documentation/user_guide/usage.adoc#daily-operation) for
commands, configuration continuity and recovery choices. The
[live operation surface catalog](documentation/system/live-operation-surfaces.adoc)
identifies supported workflow boundaries and retained compatibility assets.

## For contributors

The Python code follows a domain/application/infrastructure split.
Start with the [Developer Manual](documentation/manuals/developer-manual.md),
[AGENTS.md](AGENTS.md) and [QUALITY.md](QUALITY.md).

The future [multi-runtime vision](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/251)
covers Podman and Kubernetes. Those profiles are separate from the current
Classic implementation.
