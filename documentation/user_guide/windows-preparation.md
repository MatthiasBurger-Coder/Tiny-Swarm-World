# Windows / WSL2 lifecycle and resource preparation

`prepare_windows.ps1` prepares the selected Windows/WSL2 lifecycle baseline and
plans global WSL2 memory, processors and swap against the selected fixed profile
and configured managed nodes. Product commands and Python still run in Linux/WSL.
Incus, Windows browser routing and installation retain their separate owners.
A completed lifecycle baseline does not mean aggregate installation readiness or
verified services.

Use the trusted complete release or repository checkout. Help needs neither
Python nor elevation and performs no host probes:

```powershell
./prepare_windows.ps1 -Help
./prepare_windows.ps1 -Distro Ubuntu-24.04 -Preflight
./prepare_windows.ps1 -Distro Ubuntu-24.04 -DryRun -Json
./prepare_windows.ps1 -Distro Ubuntu -UbuntuRelease 26.04 -Preflight
```

Windows-side preparation requires elevated PowerShell on a candidate Windows 11
x86_64 host with observed virtualization. Select `Ubuntu-24.04` or `Ubuntu-26.04`
explicitly; a registration name alone does not prove its actual release or WSL2
status. An existing WSL1 selection is blocked, never automatically converted.
An existing custom registration such as `Ubuntu` requires an explicit supported
`-UbuntuRelease`. Its actual release must match. Missing custom registrations block;
the script installs only explicitly selected canonical catalogue registrations.
Preflight and dry-run do not change features, create/start a distro, write
configuration, download artifacts or write evidence. If the selected distro is
stopped, start it yourself using the reported selected-distro command, then rerun.

## Preparation-to-install handoff

Place the complete trusted release/checkout under the selected ordinary account's
Linux home (`~/Tiny-Swarm-World` by default). A Windows-mounted checkout is not the
standard product execution path. Existing checkouts can be selected explicitly:

```powershell
./prepare_windows.ps1 -Distro Ubuntu-24.04 -LinuxCheckout /home/operator/Tiny-Swarm-World -Preflight
```

The bounded read-only probe checks an already-running registration, ordinary account,
owned native filesystem and matching verified product source. A supplied dependency-light
probe checks raw Git commit/tree/blob membership (including edits hidden from Git
status) or the trusted extracted-release proof, without importing checkout code.
The read-only source probe needs system Python; if absent, prepare the Linux
prerequisites separately first, then rerun Windows preflight.
It neither copies nor executes checkout code. Missing, symlinked, foreign-owned or
Windows-mounted checkouts produce a blocked handoff with a placement remedy.

After Windows lifecycle/resources/bridge readiness, `handoff.operator_command`
selects the exact distribution and observed user, changes to the quoted Linux
checkout, runs `prepare_linux.sh`, and runs `install.sh` only after preparation exits
zero. It preserves the selected fixed service profile. Copy the printed command
into the interactive PowerShell console: WSL inherits its stdin for stage consent
and returns the Linux exit code in `$LASTEXITCODE`. There is no automated install
switch and no Windows Python execution. Windows `READY` is capability readiness;
`handoff.status=LINUX_PREPARATION_REQUIRED` leaves `preparation_ready=false` and
`services_verified=false`. A missing checkout cannot be an executable ready handoff.

Preparation prints the final Linux install command only after packages, Python,
Incus and network stages succeed. Restart/blocked/partial/timeout/interruption states
stop dependent installation; rerun preflight, resolve the stated blocker, then give
fresh consent. Ordinary native and WSL installs reconcile existing state. Explicit
WSL `--confirm-reset` remains deprecated destructive compatibility, separate from
live consent; prefer a separately confirmed platform reset followed by normal install.
No new live qualification is claimed by these commands or mocked tests.

## Qualification and consent

Ordinary Apply is blocked until the exact target has applicable reviewed
qualification. The initial qualified list is empty. Candidate eligibility is a
separate state, not a live pass or release-support promise.

The accepted [W04 ADR](../arc42/09_decisions/adr-windows-wsl-lifecycle-preparation.adoc)
and [W05 resource ADR](../arc42/09_decisions/adr-wsl-capacity-adaptation.adoc)
allow only an explicit `-QualificationRun` on an identified disposable/restorable
host. Before that run, the operator must authorize that actual host, distro,
committed source revision and recovery/snapshot reference. Declaration parameters
must match observed inventory and source identity. The entire current plan is
shown before exact `yes`; unattended apply additionally requires `-ApproveApply`.
JSON never prompts. These flags cannot create consent for installation/reset or
bypass unknown/unsupported target facts. Saved approvals and local env files
never authorize another invocation.

Plans specify ordered actions, exact pinned official sources/checksums, finite
timeouts, restart scope and preservation. Apply rechecks source, configuration,
target and actions; changes require a new plan/approval. Newly observable WSL,
distro or account facts are examined in a subsequent invocation before dependent
stages. Dirty or unverifiable source cannot produce exact-commit qualification. For an
extracted release, its offline `release-manifest.json` proof must bind all executable
preparation assets to the independently trusted `-QualificationRevision`. The SHA
must come from the trusted release channel, never from the manifest itself. Git
commit/tree/blob hashes prove membership and integrity, not publisher authenticity.

Release packaging on Linux/WSL creates the proof from a clean committed checkout:

```bash
python3 tools/build_windows_preparation_manifest.py --repository . --output /tmp/tsw-release-manifest.json
```

Include that file as `tools/windows/preparation/release-manifest.json` in the complete
extracted release. Proof verification on Windows needs neither Git nor Python.
An altered asset, wrong expected revision, malformed proof or unsafe path blocks
qualification. A Git checkout uses clean HEAD and current raw blob comparisons.
The command reports the next step; it never executes the reported command itself.

## Stages and operator boundaries

Windows prerequisite features and a pinned Microsoft WSL installer are separate
stages. The selected Ubuntu image is installed explicitly without automatic first
launch. Downloads happen only during approved apply, use official pinned URLs and
must match SHA-256; the Microsoft installer must also have a valid Microsoft
signature. No uncontrolled latest update or implicit default Ubuntu installation
is used. Existing distro/default/global settings are preserved.

Initial Linux account creation remains interactive operator work. Choose an
ordinary default account in that selected distro; no password is stored or guessed.
Missing systemd packages produce an operator remedy rather than an automatic
package installation. The selected `wsl.conf` change preserves unrelated sections,
settings and file ownership/mode, rejects ambiguous/unsafe files, and requires
reinspection before apply. PID 1 must actually be systemd after restart.

A Windows reboot or selected-distro restart is always an operator action. The
script returns a concrete next command and restart scope. It never performs
whole-host reboot, WSL-wide shutdown, unrelated distro termination, unregister,
reset, replacement or conversion. After restart/account work, rerun the same
preparation command; state is reinventoried and approval must be renewed.

| Result | Exit | Operator meaning |
| --- | --- | --- |
| READY | 0 | Lifecycle and effective resource capacity are observed ready; aggregate preparation remains separate. |
| BLOCKED | 2 | No dependent mutation; resolve the reported fact, authorization or ownership blocker. |
| RESTART_REQUIRED | 3 | A verified checkpoint needs the reported operator restart/login; not ready. |
| PARTIAL | 4 | Confirmed/uncertain effects exist, or a successful checkpoint needs fresh consent; inspect the new plan. |
| FAILED | 1 | Failed attempt with no confirmed/uncertain mutation effects. |
| Timeout / interruption | 124 / 130 | Transport result retained; dependent stages stopped, effects reported separately. |

Protected Windows-side evidence is checked before the first host mutation and
written only after approval, with restrictive ownership/ACLs and redacted atomic
intent/effect records. Unsafe ownership/reparse paths block. Evidence failure
after host mutation is PARTIAL. No automatic removal or whole-host rollback is
attempted. W08 later integrates shared durable recovery; reruns already use
observed state instead of blindly replaying logs.

## Capacity plan and resource overrides

After lifecycle prerequisites are observed, the resource plan shows Windows
physical capacity and reserve, profile minima, configured managed-node totals,
WSL allocation, usable disk and current/proposed global settings separately.
The current provider configuration totals 19 GiB RAM, 8 CPU limits and 80 GiB
node disks. WSL overhead adds 2 GiB; service-access also requires 150 GiB usable
disk. No node limit or selected service is reduced to make an insufficient host fit.

| Physical RAM class | Windows RAM reserve | Minimum configured WSL RAM | RAM result with current nodes |
| --- | --- | --- | --- |
| 16 GiB | 4 GiB | 21 GiB | BLOCKED: insufficient physical capacity |
| 32 GiB | 8 GiB | 21 GiB | RAM fits; CPU/disk still checked |
| 64 GiB | 16 GiB | 21 GiB | RAM fits; CPU/disk still checked |

Reserve is max(4 GiB, ceil(physical RAM/4)) and max(1, ceil(logical CPU/4)).
CPU sums are conservative planning limits, not dedicated core reservations. Swap
never counts as physical service RAM. Its default is ceil(allocated WSL RAM/4).
Inspect explicit overrides without writing any configuration:

```powershell
./prepare_windows.ps1 -Distro Ubuntu-24.04 -ServiceProfile service-access -DryRun -Json -WslMemoryGiB 24 -WslProcessors 8 -WslSwapGiB 6
```

Memory/processors must be positive integral values; swap can be zero. Overrides
remain subject to profile/node floors and Windows reserve. Use observed plan
capacity, rather than assuming a nominal host RAM class guarantees the example.
Unknown, unsafe or ambiguous configuration/storage facts block. Custom swapfile
locations currently block adaptation; they are preserved rather than relocated.
The selected registered VHD and canonical user TEMP determine actual disk volumes.
Process-only environment redirects and unsafe/reparse/non-local/non-NTFS paths block.

Disk planning reserves the selected profile/node requirement plus swap allocation
and 20 GiB Windows headroom on the appropriate volumes. Co-located budgets are
added once. The full proposed swap remains conservatively reserved when its
physical sparse allocation cannot be established; VHD logical length is not
subtracted from required free space. A near-full host can therefore remain blocked
even when an existing sparse swap file has a large nominal size.

Only wsl2 memory/processors/swap values change. Unrelated entries, comments,
sections, supported UTF-8/UTF-8 BOM/UTF-16 LE encoding and line endings are preserved.
Duplicate sections/keys, unsupported syntax/units, unsafe ownership/ACLs and stale
bytes/metadata block. Approved changes create a unique protected original backup
with protected restoration metadata and retain the actual displaced file, including
any concurrent edit. A concurrent edit or uncertain replacement is reported as
partial, never success. Inspect the returned recovery paths and protected evidence
before any separately approved restore; do not blindly overwrite a later edit.

The configuration affects every WSL2 distro. Apply never runs shutdown itself.
After a confirmed change it returns RESTART_REQUIRED/3 and explains the WSL-wide
scope. Save work in every distro, perform the reported shutdown/start yourself, then
rerun the same preparation command with the same profile/overrides. The generated
next command retains those values and asks for new consent when another change is
needed. A timeout/interruption stops dependent work and preserves uncertainty; a
remaining owned lock/artifact needs inspection, not an automatic retry or deletion.

Readiness requires observed effective memory/CPU/swap and usable disk after resume.
Matching file contents alone never suffice. Memory ceiling accounting allows
max(256 MiB, 2%) tolerance, but usable profile/node RAM minima still apply independently.
Unknown effective facts or insufficient usable RAM/disk block; known settings that
have not taken effect report restart required. Aggregate preparation_ready and
services_verified remain false.

Exact-plan identity excludes only volatile disk-free byte counts. The plan keeps
the observations visible, and bounded fresh inventory must still prove the same
allocation feasible on the same volumes before mutation. Threshold loss, unknown
capacity, changed volume/configuration/source/allocation invalidates consent.

The resource-only projection reuses canonical Python WSL profiles and provider YAML;
there is no additional service graph. Packaging from Linux/WSL verifies it with:

```bash
PYTHONPATH=src python3 tools/build_wsl_resource_projection.py --check
```

After an intentional canonical resource change, regenerate with the same command
without `--check`, review the diff, run quality and commit before producing a release
proof. Stale sources block Windows planning. Fixed profiles remain the selection
authority until #440/#444 provide selective setup.

## Verification and issue status

The executable PowerShell harness exercises mocked lifecycle/host adapters, without
creating or changing real WSL distributions or Windows features. Run normal
repository quality checks from Linux/WSL:

```bash
PYTHONPATH=src python3 -m unittest tests.test_prepare_windows tests.test_windows_source_proof tests.test_wsl_resource_projection
python3 tools/quality_gate.py quality
```

Missing/skipped core PowerShell behavior execution is an acceptance gap, not proof
from source text. W09 supplies separately authorized clean/existing-host, restart,
rerun and recovery evidence with exact source revision and observed versions.
W04 lifecycle evidence is scoped to its recorded scenarios; it does not qualify
W05 resource changes. No local test, ADR or issue instruction is a live mutation
approval. Browser verification does not apply to the W05 capacity-only extension;
W06 bridge/browser applicability is recorded separately below. External results
are tracked separately.

The operator-approved 2026-10-10 amendment requires actual existing-WSL and native
Ubuntu preparation, rerun, preservation and applicable recovery evidence for #456.
The native host uses `prepare_linux.sh`. Clean Windows preparation remains locally
tested and is not live-qualified by these scenarios. Windows feature/WSL/distro
installation is outside this amended live run. Recovery records must cover the
specific selected configuration and service/resource changes, not claim full
Windows recovery from a distro/configuration backup.

Official candidate installation/tool-format constraints come from
[Microsoft WSL commands](https://learn.microsoft.com/en-us/windows/wsl/basic-commands),
[Microsoft systemd guidance](https://learn.microsoft.com/en-us/windows/wsl/systemd),
and [Canonical Ubuntu WSL installation](https://ubuntu.com/wsl/docs/stable/howto/install-ubuntu-wsl2/).
They describe eligibility, not Tiny Swarm World live qualification.

## W06 bridge preparation and browser-access stages

After lifecycle and effective resource prerequisites are ready, preparation
inventories the existing bridge for the explicitly selected running distribution.
The plan delegates `bridge_install` or an owned `bridge_refresh` to the canonical
bridge lifecycle. Ordinary Apply retains the qualification guard and requires
fresh exact-target/source/plan consent and protected evidence; existing W04/W05
qualification does not automatically qualify the new network behavior.

The shared `auto` configuration is preserved. The selected distro is bound in the
protected installed copy through the existing staging transaction. A new service
registration uses the existing credential dialog for the Windows account owning
the distro; an owned registration reuses credentials. A foreign registration or
account mismatch blocks without replacement. Windows hosts, portproxy, Firewall,
WinSW and ACLs retain their existing exclusive bridge owner.

For a strictly read-only diagnostic, use the distro and IPv4 address already
observed in its running WSL shell:

```powershell
./tools/windows/tws-wsl-bridge.ps1 -Action inventory -Distro <selected-distro> -ObservedAddress <observed-IPv4>
```

This emits one JSON inventory without starting a distro, creating mutex/state/
evidence, requesting credentials or probing live TCP endpoints. Preparation uses
registration/configuration/routing and fresh protected-agent heartbeat readiness.
`endpoint_state` and `login_state` remain `UNVERIFIED`; API reachability is a
separate check and does not establish successful login. `services_verified` and
aggregate `preparation_ready` remain false in this capability.

The existing service agent reconciles WSL address changes after restart. No
second agent or scheduled task is installed. Local tests exercise that owner with
mocked address changes; actual restart/browser/login success requires separately
authorized recoverable-host evidence with exact committed SHA, target/tool
versions, commands and exits. Current W06 live state is `LIVE_CONSENT_MISSING`.
See [kernel and browser-access preparation](network-preparation.md) for the Linux
network stage, supported firewall owners and safe rerun/recovery behavior.
