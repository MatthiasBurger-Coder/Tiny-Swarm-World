# Tiny Swarm World

The [Product Handbook](documentation/README.adoc) is the master documentation
index for product foundations, architecture, usage, operations, development,
quality, security, audits and release evidence. Read the
[continuous edition](documentation/document.adoc) for the assembled handbook.

Installation prerequisites live in [`modules/tsw_native_linux/boostrap`](modules/tsw_native_linux/boostrap).
Quality, audit and developer tools live in [`modules/tsw_core/tools/linux`](modules/tsw_core/tools/linux).
See [directory responsibilities and system handoff](documentation/handbook/05-development/manuals/tools-layout.md).

Tiny Swarm World creates a local development and test environment with Docker
Swarm, Portainer, Infisical, Nexus, Jenkins, Pulsar, SonarQube and supporting
services. It provisions managed Linux containers through Incus and runs Docker
Engine inside those containers.

## Native Linux quick start

Guided Classic setup is available from a trusted Git checkout on native Ubuntu
24.04 or 26.04 x86_64. Clean-host release qualification is still open.
See the [release acceptance matrix](documentation/handbook/07-evidence-release/evidence/issue-496-native-setup-acceptance.md)
for the exact evidence and open qualification checks.

Run from an ordinary sudo-capable account in an interactive terminal with Git
and internet access. The default preset targets eight CPU threads, at least
18 GiB RAM and 120 GiB free on the repository filesystem:

```bash
git clone https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World.git ~/Tiny-Swarm-World
cd ~/Tiny-Swarm-World
./setup_linux.sh
```

The command defaults to `service-access`. Use `./setup_linux.sh --dry-run` to
inspect the plan first. Read each plan before approving it. For a restart or
interrupted run, follow the reported next command from the same checkout and
profile. The [installation guide](documentation/handbook/03-user-guide/user_guide/installation.adoc#native-linux-quick-start)
covers capacity, profiles, elevation, service access and recovery.

## Start here

| What you want to do | Read |
|---|---|
| Prepare a machine and install for the first time | [Installation guide](documentation/handbook/03-user-guide/user_guide/installation.adoc) |
| Find service URLs and sign in | [Default logins](#default-logins-after-a-fresh-installation), [Service access and login](documentation/handbook/03-user-guide/user_guide/usage.adoc#open-the-services) and [credential catalog](documentation/handbook/02-architecture/arc42/08_configuration/internal-test-credential-catalog.md) |
| Inspect or reconcile an existing installation | [Daily operation](documentation/handbook/03-user-guide/user_guide/usage.adoc#daily-operation) |
| Diagnose a failed run | [Troubleshooting](documentation/handbook/03-user-guide/user_guide/troubleshooting.adoc#first-response) |
| Change code or run development tests | [Developer Manual](documentation/handbook/05-development/manuals/developer-manual.md) |
| Understand architecture or extend runtime support | [Resulting architecture and runtime extension guide](documentation/handbook/02-architecture/arc42/05_analysis/arch-03-21-resulting-architecture.md) |
| Find architecture, security or audit references | [Product Handbook](documentation/README.adoc) |

## Default logins after a fresh installation

For a successful fresh `install.sh` installation using the standard
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
values from your configured credential source. The optional installer file
defaults to `.tiny-swarm-world/local/live-installation.env` under the checkout.
Set `TSW_INSTALL_ENV_FILE` to select a protected file outside the repository, for
example `$HOME/.local/state/tiny-swarm-world/live-installation.env`. In the
installation shell, show the configured path without printing credential values:

```bash
printf '%s\n' "${TSW_INSTALL_ENV_FILE:-.tiny-swarm-world/local/live-installation.env}"
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

The [canonical credential catalog](documentation/handbook/02-architecture/arc42/08_configuration/internal-test-credential-catalog.md)
documents all test values, API tokens and component-specific exceptions.
For custom credentials, follow the
[optional credential setup](documentation/handbook/03-user-guide/user_guide/installation.adoc#operator-credential-overrides).

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
PYTHONPATH=. python3 -m tiny_swarm_world --service-profile service-access platform verify
```

Then sign in to the required services from the browser you intend to use.
An HTTP 200 response or a login page proves neither authentication nor a fully
working installation. See the
[verification steps](documentation/handbook/03-user-guide/user_guide/installation.adoc#verify-installed-runtime).

If a route is unavailable, distinguish name resolution, forwarding, TLS,
service readiness and authentication using the
[troubleshooting guide](documentation/handbook/03-user-guide/user_guide/troubleshooting.adoc#first-response).
Use the evidence directory printed for your run, inspect exit codes first,
and redact diagnostics before sharing them.

## Reconcile, reset and update are different operations

| Operation | Meaning |
|---|---|
| `platform verify` | Inspect the existing platform without repairing it. |
| `platform reconcile --live` | Reconcile managed platform state with explicit consent; it is not a complete application update. |
| `setup run --live` | Run the broader setup workflow without a reset; it still changes infrastructure. |
| `setup_linux.sh` | Guided native Ubuntu preparation and installation. |
| `modules/tsw_native_linux/boostrap/prepare_linux.sh` | Prepare Ubuntu prerequisites and Incus access/resources with staged confirmation. |
| `install.sh` on native Linux | Verify preparation, then run setup without a reset. |
| Product upgrade | `product upgrade` controls the bounded TSW release transition; see the [product upgrade guide](documentation/handbook/03-user-guide/user_guide/product-upgrades.md) for prerequisites and qualification limits. |
| Component update | `services updates` and `services update` inspect and plan selected components; `platform update` retains the single stack-service image transition contract. |

Use `platform update --stack ... --service ... --from-image ... --to-image ... --preview`
before an explicitly consented live apply. Use `platform update --recover
--stack ... --service ...` for the last recorded rollback transition. Pulling
new source code and running reconcile does not establish a supported upgrade.

See [Daily operation](documentation/handbook/03-user-guide/user_guide/usage.adoc#daily-operation) for
commands, configuration continuity and recovery choices. The
[live operation surface catalog](documentation/handbook/04-operations/system/live-operation-surfaces.adoc)
identifies supported workflow boundaries and retained compatibility assets.

For a new Classic installation, preview `setup run --minimal --preview` or
`setup run --services jenkins,sonarqube --preview`. Incus/LXC is a host
prerequisite and Portainer is a mandatory managed foundation; the planner
explains added dependencies. Add services later with
`services add --services swagger --preview`. Swagger defaults to published access;
`setup run --services swagger --swagger-exposure internal --preview` plans
container-only Swagger with separately admitted private-profile execution. See [selective setup](documentation/handbook/03-user-guide/user_guide/selective-setup.md)
for prerequisites, live consent and removal limits. Cross-host qualification
remains incomplete; see [W09 evidence](documentation/handbook/07-evidence-release/evidence/lcm-w09-qualification.md).

## For contributors

The Python code follows a domain/application/infrastructure split.
Start with the [Developer Manual](documentation/handbook/05-development/manuals/developer-manual.md),
[AGENTS.md](AGENTS.md) and [QUALITY.md](QUALITY.md).

The future [multi-runtime vision](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/251)
covers Podman and Kubernetes. Those profiles are separate from the current
Classic implementation.

Inspect recorded installation identity and component versions with
`tiny-swarm-world product version --json` and `tiny-swarm-world services list --json`
from the prepared environment. These commands write nothing; legacy installations
without a manifest report adoption required. See the
[manifest, catalog and adoption contract](documentation/handbook/01-product/contracts/installation-manifest.md)
for schema ownership, drift diagnostics and current support limits.

Discover admitted targets with `tiny-swarm-world services updates --json` and
plan an explicit batch with
`tiny-swarm-world services update --services swagger,traefik --preview`.
The catalog records two fixed stateless image-transition candidates, which
remain non-executable pending current-source live qualification:
Traefik 3.7.4→3.7.5 and Swagger UI 5.32.6→5.32.7. Historical bounded live
results used an earlier transition-runner source and do not qualify the current
runner. See [LCM-W09 evidence](documentation/handbook/07-evidence-release/evidence/lcm-w09-qualification.md)
and its [source-hash applicability](documentation/handbook/07-evidence-release/evidence/lcm-w09-transition-proposal.md).
This does not close the broader W09 acceptance. Other generic services have no admitted
upgrade targets and unsupported previews return exit 1. See
[component planning](documentation/handbook/03-user-guide/user_guide/component-updates.md) for the
exact targets, migration restrictions and execution ownership.
