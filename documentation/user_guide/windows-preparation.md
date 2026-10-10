# Windows / WSL2 lifecycle preparation

`prepare_windows.ps1` prepares only the selected Windows/WSL2 lifecycle baseline.
Product commands and Python still run in Linux/WSL. Resource sizing, Incus,
Windows browser routing and installation remain separate preparation stages.
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

## Qualification and consent

Ordinary Apply is blocked until the exact target has applicable reviewed
qualification. The initial qualified list is empty. Candidate eligibility is a
separate state, not a live pass or release-support promise.

The accepted [W04 ADR](../arc42/09_decisions/adr-windows-wsl-lifecycle-preparation.adoc)
allows only an explicit `-QualificationRun` on an identified disposable/restorable
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
| READY | 0 | The W04 capability is observed ready; aggregate preparation remains separate. |
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

## Verification and issue status

The executable PowerShell harness exercises mocked lifecycle/host adapters, without
creating or changing real WSL distributions or Windows features. Run normal
repository quality checks from Linux/WSL:

```bash
PYTHONPATH=src python3 -m unittest tests.test_prepare_windows tests.test_windows_source_proof
python3 tools/quality_gate.py quality
```

Missing/skipped core PowerShell behavior execution is an acceptance gap, not proof
from source text. W09 supplies separately authorized clean/existing-host, restart,
rerun and recovery evidence with exact source revision and observed versions.
Issue #456 remains open while AC1-LIVE lacks that evidence. No local test, ADR or
issue instruction is a live mutation approval. Browser verification does not
apply to this lifecycle-only scope; external results are tracked separately.

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
