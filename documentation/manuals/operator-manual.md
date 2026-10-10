# Operator Manual

Use this page to choose the next task. Commands run from the repository root
in a Linux or WSL2 shell with the project's Python environment active.

| Task | Instructions | Effect |
|---|---|---|
| First installation | [Installation guide](../user_guide/installation.adoc) | Separate host preparation, then native reconciliation or confirmed WSL2 reset and setup. |
| Open services and sign in | [Service access and login](../user_guide/usage.adoc#open-the-services) | Uses the configured routes and effective credentials. |
| Inspect an installation | [Daily operation](../user_guide/usage.adoc#daily-operation) | Read-only platform verification. |
| Reconcile or recover | [Daily operation](../user_guide/usage.adoc#daily-operation) | Explicitly changes managed state; preserves the distinction from fresh reset. |
| Diagnose a failure | [First response](../user_guide/troubleshooting.adoc#first-response) | Starts with the first failed phase and exit codes. |
| Change credentials | [Optional overrides](../user_guide/installation.adoc#operator-credential-overrides) | Supplies an explicit input; it is not an automatic rotation procedure. |

## Before the first live run

Run `./prepare_linux.sh --dry-run` to inspect the preparation plan on supported
Ubuntu 24.04/26.04 x86_64 Linux or WSL2 hosts. `./prepare_linux.sh` separately
requests consent for package/Python preparation, Incus startup/access and absent
configured resources, then kernel/network preparation. Compatible resources are
reused; collisions block. New group membership requires logout/login and a rerun.
See [network preparation](../user_guide/network-preparation.md) for firewall and
browser-access boundaries.

The installer requires a prepared host and does not invoke host preparation.
Tiny Swarm World installs Docker inside managed LXC nodes. On WSL2, Windows
lifecycle and capacity planning use the separate
[Windows preparation guide](../user_guide/windows-preparation.md); ordinary
Windows Apply remains blocked pending applicable live qualification.

An empty Incus project can still share a host network with another project.
Check that the configured node names and published ports are available across
that shared network. Stopped containers can retain their DNS names: a second
`swarm-manager` can therefore fail to start even when its project is empty.
Use an isolated prepared target or have the host operator resolve the ownership
conflict while preserving existing data before starting the installation.

On a dedicated WSL distribution, qualify the Windows bridge from that same
distribution and retain the Windows interoperability tools in the protected
runner's command search path. Follow the
[host preparation instructions](../user_guide/installation.adoc); a bridge
configuration selecting another distribution does not qualify the new target.

**On native Linux, the installer reconciles without a reset. On WSL2, it resets
the managed environment after confirmation before setup.** Read the reset scope
before running the WSL2 installer on a machine with data you want to keep. Use
`platform verify` to inspect an existing installation first. A deliberate native
reset is a separate, explicitly confirmed operation.

## Credentials and evidence

The standard internal-test installation uses the
[credential catalog](../arc42/08_configuration/internal-test-credential-catalog.md)
without a manually prepared password file. Overrides are optional and require
a protected Linux-native file/directory when file-based. Infisical bootstrap
login and synchronized service items are separate concerns.

Use the evidence path printed by your run. Redact diagnostics before sharing;
keep credentials, session tokens and private material out of reports.
For exposure policy or an incident, use the
[Security Manual](security-manual.md).

## What is verified

Static preflight and local tests do not prove live service access. A usable
installation also needs successful platform verification and actual service
logins. The [RC1 decision](../release/rc1-decision.md) and
[October lifecycle validation](../evidence/issue-363-final-validation-20261003.md)
record results for their named candidates. They do not qualify subsequent
bootstrap changes or every supported host.
Do not treat reset or reconcile as a product upgrade. For one reviewed image transition, use the
`platform update` preview/apply contract in the
[Usage guide](../user_guide/usage.adoc#daily-operation), or use its
`--recover` form for the last recorded rollback state.
