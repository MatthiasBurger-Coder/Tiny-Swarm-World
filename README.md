# Tiny Swarm World

Tiny Swarm World creates a local development and test environment with Docker
Swarm, Portainer, Infisical, Nexus, Jenkins, Pulsar, SonarQube and supporting
services. It provisions managed Linux containers through Incus and runs Docker
Engine inside those containers.

The current implementation is the **Classic profile** for internal development
and testing. Native Ubuntu 24.04/26.04 x86_64 and Windows 11 with Ubuntu WSL2
are bootstrap candidates. W09 verified selected **existing Ubuntu 26.04 hosts**;
clean-host installation and global release qualification remain unverified.
See the [bootstrap completion audit](documentation/evidence/issue-462-bootstrap-completion-audit.md)
for exact versions, source revisions and deferred scenarios.

## Prepare, then install

Use a complete trusted checkout or release. Enter its root before running these
commands. For the currently exercised install path, retain Git metadata; a plain
source archive is insufficient for the installer's secret-ignore check. On Linux,
clone into your ordinary account's home when Git is available:

```bash
git clone https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World.git ~/Tiny-Swarm-World
cd ~/Tiny-Swarm-World
```

**Native Ubuntu:** run as an ordinary sudo-capable user on Ubuntu 24.04 or 26.04
x86_64. Preparation installs missing packages/Python and its local environment;
manual pip/venv steps are unnecessary.

```bash
./prepare_linux.sh
./install.sh
```

**Windows 11 / WSL2:** from the complete trusted Windows checkout, open elevated
PowerShell and select the exact distribution. For example:

```powershell
./prepare_windows.ps1 -Distro Ubuntu-26.04
```

Before the handoff, create the ordinary Ubuntu account interactively when
prompted and place the matching checkout in its Linux home (`~/Tiny-Swarm-World`
by default); Windows preparation does not copy it. If the source probe reports
missing system Python, first run `./prepare_linux.sh` from that Linux checkout,
then rerun Windows preparation. This boundary can add commands to the short path.
Use `-LinuxCheckout` for another Linux-native location; custom distro names also
need the matching `-UbuntuRelease`.

Once available, copy the printed `handoff.operator_command` into the interactive
PowerShell console. That second command selects the observed Linux user and
checkout, runs Linux preparation, and starts installation only when preparation
succeeds. Product Python runs entirely in WSL.

**Current Windows limitation:** ordinary Apply is unqualified and blocked.
The short path describes the delivered handoff, not an unattended clean-host
success promise. `-Preflight` / `-DryRun` inspect without mutation. Qualification
requires a separately authorized recoverable target and exact source/plan binding;
see [Windows preparation](documentation/user_guide/windows-preparation.md#qualification-and-consent).
A closed W09 issue does not remove this guard. A plain extracted archive also
needs the trusted release source proof for Windows qualification and does not
resolve the installer's Git-metadata limitation.

Review each plan before typing exact `yes`; installation has its own live approval.
Use `./prepare_linux.sh --dry-run` or `./install.sh --preflight` for read-only checks.
Do not run the whole installer with sudo. Internet access to Ubuntu packages,
locked Python dependencies and container registries is required. The current
service-access plan needs at least 21 GiB WSL RAM for configured nodes/overhead,
plus Windows reserve, eight allocated CPU threads and 150 GiB usable disk; a
16 GiB Windows host cannot fit it. Inspect the actual capacity plan; customized
nodes/profiles can differ. Docker runs inside managed Incus nodes.

A reboot, selected-distro restart or new `incus-admin` membership pauses the path.
Perform only the reported restart/logout action, reopen the ordinary-user shell,
and rerun preparation with the same distribution, profile and credential/config
selection. Fresh observation and consent are required; dependent installation
stays stopped. Ordinary install reconciles and preserves managed data/credentials.
WSL `--confirm-reset` is a separate deprecated destructive operation, never a
routine recovery flag.

If blocked, follow the named stage and next command: authenticate with `sudo -v`
in the preparation terminal for elevation failures; log out/in for stale groups;
resolve active LXD conflicts without deleting instances; free capacity or choose a
fitting reviewed profile for resource failures. Do not overwrite foreign Incus,
firewall or bridge resources. See the [installation guide](documentation/user_guide/installation.adoc),
[manual host and certificate checklist](documentation/user_guide/manual-host-steps.md)
and [troubleshooting](documentation/user_guide/troubleshooting.adoc#first-response)
for stage-specific recovery and CA trust. APT/features are not transactional;
resumption does not promise whole-host rollback.

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

Check the platform from the prepared checkout. Activate the environment that
preparation created, if present (use the same `TSW_NATIVE_LINUX_VENV` override
if selected). If preparation reused available system dependencies, use that
Python instead. The module command also works without a CLI script on PATH:

```bash
if [ -f "${TSW_NATIVE_LINUX_VENV:-.tiny-swarm-world/install-venv}/bin/activate" ]; then
  source "${TSW_NATIVE_LINUX_VENV:-.tiny-swarm-world/install-venv}/bin/activate"
fi
PYTHONPATH=src python3 -m tiny_swarm_world --service-profile service-access platform verify
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

Inspect recorded installation identity and component versions with
`tiny-swarm-world product version --json` and `tiny-swarm-world services list --json`
from the prepared environment. These commands write nothing; legacy installations
without a manifest report adoption required. See the
[manifest, catalog and adoption contract](documentation/contracts/installation-manifest.md)
for schema ownership, drift diagnostics and current support limits.
