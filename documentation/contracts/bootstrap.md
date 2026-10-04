# BOOT-W01 bootstrap command, host plan and readiness contract

Contract version: 1. Issue: [#453](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/453),
parent [#452](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/452).
Source baseline: `346f4a43dbdc43380e7bc703ab185bc06746965b`.

This defines the implementation contract for BOOT-W02–W10. It does not make
those commands or capabilities available. W01 delivers the inventory, interface,
plan and readiness definitions. Existing behavior remains governed by the
[accepted native preparation ADR](../arc42/09_decisions/adr-native-linux-preparation-and-install-lifecycle.adoc)
and [bridge ADR](../arc42/09_decisions/adr-windows-wsl-bridge-service-agent.adoc).
W02, W04 and W07 must record their respective narrow ADR supersessions before
changing the manual-Python prerequisite, WSL preparation exclusion or WSL reset
behavior. The future departures are recorded in the
[proposed bootstrap ADR](../arc42/09_decisions/adr-bootstrap-command-readiness-contract.adoc).
There is no new runtime orchestrator or provider decision here.

## 1. Delivered behavior and implementation owners

All paths below are relative to the repository root. A successful existing
capability check proves only that capability, never complete installation readiness.

| Surface / requirement | Delivered owner and behavior | Gap / follow-up owner |
|---|---|---|
| `prepare_linux.sh`, BOOT-01/04 | `prepare_linux.py`, `infrastructure/composition_native_preparation.py`, `application/services/native_preparation.py`; qualify native Ubuntu, list/install missing profile packages after confirmation | W02: clean-host Python and WSL Ubuntu bootstrap; W01: full host-plan contract |
| Package facts/policy | `domain/native_preparation.py`, `application/ports/native_preparation.py`, `infrastructure/adapters/host/native_preparation.py`, `infrastructure/adapters/native_package_manager.py`; recheck before APT | W02 extends existing inspector/package ports; no parallel package service |
| Python dependency bootstrap | `composition_installation.py` facade and `infrastructure/adapters/installation/process.py`; user-local venv, hash-checked `requirements.lock`, editable install without dependency resolution | W02 supplies interpreter/venv prerequisites before dependency imports |
| `install.sh`, BOOT-07 | `simple_installer.py`, `composition_installation.py`, `application/services/installation.py`, installation ports/adapters; native reconcile without reset, WSL confirmed fresh reset | W07: ordinary non-destructive WSL install and handoff; keep explicit reset separate |
| `tsw`, `host prepare` | `__main__.py`, CLI registry/parser/consent/commands, `PrepareHostWithPreflight`, `HostPreparationService`, `PortHostPreparation` | Already consent-guarded; not a bare-host package bootstrap command |
| Native `host prepare` | `NativeLinuxHostPreparation` verifies kernel controls; does not change them | W03: Incus daemon/current-user/storage/network/profile preparation; W06: kernel/network adapters |
| `host verify` | CLI command calls read-only hang diagnostics; capability-level diagnostics, not aggregate installation readiness | W01 defines aggregate below; implementation integration in W07 |
| Windows bridge, BOOT-06 | `tools/windows/tws-wsl-bridge.ps1`, service script, config, `WslHostPreparation`, `PortWindowsCommandRunner`; verify before refresh, protected ownership/ACL/collision lifecycle | W06 reuses bridge and canonical `infra/config/ports.yaml`; no second portproxy/firewall owner |
| Windows preparation, BOOT-02/03 | No root `prepare_windows.ps1` delivered | W04: Windows features/WSL2/distro/systemd; W05: capacity and preserved WSL configuration |
| Recovery/evidence, BOOT-08 | Native preparation re-inventories packages after failure; `native_preparation_evidence.py` writes protected, redacted evidence; installer phase timeout/interruption handling exists | W08: shared resumable stage records and protected cross-host recovery |
| Qualification/help, BOOT-09 | #427 delivered native lifecycle and its recorded Ubuntu 26.04 scenarios; Ubuntu 24.04 qualification is separate | W09: fresh/repeat/restart/recovery qualification on both families; W10: final copyable guide |

BOOT-01 maps to sections 2–6, BOOT-07 to sections 2/3/7, BOOT-08 to
sections 4–8. W01 defines these contracts; implementation belongs to the
named packages. Do not duplicate #427, add distributed DNS, Podman, K3s,
Kubernetes-first behavior or multi-host provisioning.

## 2. Target commands and consent

The following interface is specified for later implementation. New switches
are not accepted by today's scripts. Current native preparation accepts
`--preflight`, `--dry-run`, `--service-profile`; apply prompts for `yes` before
APT and Python preparation. Current installer read-only modes support native
Linux only; WSL still uses the confirmed-reset path. `tsw` needs installed
product dependencies and is not the bare-host entrypoint.

| Target entrypoint | Read-only | Apply / handoff |
|---|---|---|
| Elevated Windows PowerShell: `./prepare_windows.ps1 -Distro Ubuntu-24.04` | `-Preflight` or `-DryRun`; `-Json` for machine output; `-Help` without elevation/probes | Default invocation shows plan then asks exact `yes`; unattended `-ApproveApply` explicitly consents to that preparation plan |
| Linux/WSL: `./prepare_linux.sh` | `--preflight` or `--dry-run`; `--json`; `--help` without Python/probes | Default invocation shows plan then asks exact `yes`; unattended `--approve-apply` explicitly consents to that preparation plan |
| Selected Linux/WSL shell: `./install.sh` | `--preflight` or `--dry-run`; preserve selected profile | Ordinary setup/reconcile, no implicit reset; existing live approval remains required; preparation approval is not install approval |

`--service-profile default|service-access` / `-ServiceProfile` selects the
existing fixed profile, default `service-access`. Read-only flags are mutually
exclusive and cannot be combined with apply approval. Invalid combinations
fail before probes/mutation. Non-interactive apply without explicit approval
returns BLOCKED. JSON emits one envelope to stdout, diagnostics to stderr;
it never prompts and therefore needs explicit approval for apply.
Help is read-only and explains supported targets, modes, privilege/restart
boundaries and that READY means preparation only. It includes a concrete
first command, for example `./prepare_linux.sh --preflight` or
`./prepare_windows.ps1 -Distro Ubuntu-24.04 -Preflight`.

An apply invocation recomputes inventory and displays the entire plan before
consent. Recheck immediately before each stage. A changed target, selection,
privilege, configuration fingerprint or proposed action invalidates consent:
stop BLOCKED and request a new invocation/plan. Do not persist approvals, load
consent from local env files, infer approval from issue creation, or execute
`next_command` automatically. Preparation never launches installation implicitly.
W07 may add an explicit PowerShell install handoff; it must invoke WSL in the
selected distro/account/checkout and preserve installer exits and consent.

## 3. Targets, release files, accounts and privileges

| Target | Existing delivery | Target qualification policy |
|---|---|---|
| Native Ubuntu 24.04 LTS x86_64 | Preparation allowlist and local tests; live qualification tracked separately | W02/W03/W06 implement extensions; W09 records exact host/kernel/tool versions |
| Native Ubuntu 26.04 LTS x86_64 | #427 recorded clean/rerun/recovery qualification for its scope | New bootstrap stages require their own W09 evidence; no inherited live success |
| Windows 11 x86_64 + selected Ubuntu 24.04/26.04 x86_64 WSL2 | Bridge exists; complete Windows preparation absent | W04/W09 publish exact qualified Windows build, WSL version, distro release and kernel; unknown/unqualified combinations block mutation |
| Windows 10, WSL1, other distros/releases, ARM, macOS | Outside initial bootstrap target | BLOCKED before package/configuration changes; no automatic replacement |

The distro registration name (for example `Ubuntu-24.04`) is not proof of its
OS release or WSL generation. Inspect both. Require systemd in the selected
Linux environment, virtualization/WSL2 features on Windows and capacity for
the resolved selection. Unsupported or unreadable Linux facts block Linux prerequisite mutation.
Unknown Windows build/WSL version qualification blocks Windows-affecting and
aggregate bootstrap stages, rather than the independent W02 Linux package/Python
substage. W02 requires observed supported Ubuntu x86_64, WSL2/systemd, an
ordinary account, owned Linux-native checkout and the WSL resource floor.
Do not invent a qualified Windows version before W09 executes evidence.
See the accepted `adr-shared-ubuntu-prerequisite-bootstrap.adoc` for this narrow
W02 amendment; full bootstrap and live qualification remain separate.

An extracted, versioned release must contain executable Linux scripts,
`prepare_windows.ps1`, the dependency-light source used by preparation,
`pyproject.toml`, `requirements.lock`, `requirements.build.lock`, `infra/config`, and the existing bridge
assets. The trusted release is downloaded/extracted using OS-provided tools;
Git, Python and pip are not prerequisites to locating scripts or printing help.
Missing assets produce BLOCKED with an asset-specific remedy; no remote
pipe-to-shell, silent download/execution or clone is permitted. Today's source
archive lacks the Windows entrypoint; W04 supplies it. W10 documents extraction.

Before Python exists, the shell boundary performs only OS identification,
read-only package/interpreter inspection and an explicitly approved minimal
Ubuntu interpreter/venv prerequisite step (W02). Before dependencies exist,
Python preparation imports only standard-library/dependency-light owners;
never import full CLI composition, YAML/HTTP/UI libraries or create a venv
just to render a plan. Reuse existing locked installer dependency setup once
Python is available. Verify the lock before pip; install with hashes and
editable `--no-deps`, without dependency re-resolution.

Use the invoking non-root Linux account. Elevated PowerShell selects the
specified distro's configured ordinary default account; if absent or root,
BLOCKED and guide account creation/selection, never create a guessed identity.
A future explicit `-LinuxUser` override must resolve an existing ordinary user.
Native Linux must not construct Windows adapters.
Package/configuration operations elevate only the required stage; venv,
checkout, credentials and runtime state stay user-owned. Never run the whole
installer with sudo or run product Python on Windows. Changes to user/group
access require a new login when necessary; do not report current-shell access
as verified from a modified group database.

Use an existing user-owned Linux-native checkout/release directory. Windows
extraction is a source, not the execution target. W04/W07 may copy to the
selected Linux user's `~/Tiny-Swarm-World` only after an exact copy plan and
approval. Reuse a matching verified release; block on a different revision,
foreign ownership, symlink, nonempty unknown directory or local edits. Never
replace/reset an existing checkout. Show the selected distro, user and absolute
source/target paths in the local plan; redact host-identifying paths in shared
evidence. No fixed username or host path belongs in product configuration.

## 4. Read-only inventory and exact plan

Preflight validates observed readiness; dry-run additionally renders ordered
proposed changes. Both use the same complete in-memory plan and result rules.
Neither writes host, configuration, state, evidence, cache, bytecode, temporary
managed files or venvs. Neither refreshes APT indexes, acquires mutation locks,
starts/enables services, creates a distro/account, refreshes the bridge or
loads kernel modules. Do not start a stopped WSL distro merely to inspect it:
report required Linux facts as unknown and a concrete operator start command.
JSON goes to stdout only; an operator may redirect it externally.

Every plan uses `schema_version: 1` and contains:

| Field | Required meaning |
|---|---|
| `mode`, `read_only`, `target` | preflight/dry_run/apply; OS/build/distro/WSL/kernel/architecture, account, checkout and release identity, with unknown facts explicit |
| `selection` | requested profile/services, resolved service IDs and dependencies, catalog revision/source, existing vs requested selection |
| `observations` | named facts, observed values, source, known/unknown; never credentials/raw command output |
| `actions` | ordered stable IDs; owner, exact target, create/update/reuse operation, before/after values, prerequisites, privilege, timeout, restart scope, preservation rule, verification probe |
| `resources` | observed CPU/RAM/disk, required amounts/units, proposed allocation and Windows reserve; capacity failure reason |
| `blockers`, `restart` | safe cause codes, affected stage, remedy; none/login/distro/WSL/Windows restart scope and operator command |
| `result` | readiness outcome, process exit, changed/completed/uncertain actions, preparation_ready, services_verified, next_command, evidence_path |

A package action lists exact missing package names and Ubuntu source, never
"install dependencies" alone. Configuration changes name the exact keys and
old/new values (or absence), file and ownership; unrelated keys are preserved.
Incus actions name daemon/access/storage/network/profile identities and desired
properties. Bridge actions identify only TSW-owned routes/ports from the
canonical registry. Unknown inventory is a blocker, not an empty/no-op plan.
Package candidate versions must be shown when available; unavailable resolution
blocks installation, rather than inventing a pin. For W02 fresh APT caches,
index refresh is a separately approved bounded action; its completion permits
candidate review and a new exact installation consent. Declined consent after
refresh reports index changes rather than no changes. Apply re-resolves and requires
review if candidates drift. Bound all inventory and mutation calls by a positive
per-action timeout and finite retry budget stated in the plan; exhausted locks,
connectivity or probes stop the stage without infinite retry.

Fresh resources are proposed, existing compatible resources are verified and
reused, incompatible or foreign resources block. Never silently initialize or
reset the Incus daemon, delete storage/instances, replace a global profile,
shut down unrelated WSL distros, overwrite `.wslconfig`/`wsl.conf`, take occupied
ports, disable host runtimes, change credentials or weaken bridge ACLs.
Windows restart or `wsl --shutdown` affects more than TSW: disclose that scope
and leave the action to the operator after preserving partial progress.

For #440/#444, consume their canonical persisted resolved selection/catalog;
do not introduce another service graph or arbitrary bootstrap-only selection.
Until selective setup is delivered, use existing fixed-profile floors and
label their source. Current native preparation floors (`domain/native_preparation.py`): default 4 threads/16 GiB/60 GiB;
service-access 8 threads/15 GiB/150 GiB. Shared setup has a separate default 8 GiB floor; WSL service-access uses
16 GiB (`domain/preflight/resources.py`); do not apply the native amendment to WSL.
W05 defines capacity adaptation from the catalog while preserving Windows
reserve and unrelated settings; insufficient capacity blocks, it never silently
omits requested services. Incus/LXC and Portainer remain mandatory Classic
foundations; host Docker is not a substitute for Docker inside managed nodes.

## 5. Stable readiness and exit semantics

These are target preparation envelope states, not a replacement for existing
`HostPreparationStatus`, shared `OperationResult` or installer child exits.
Preflight/dry-run can return BLOCKED with a valid actionable plan; valid plan
construction alone is not READY. Missing prerequisites are blockers even if
apply could install them. Read-only commands always report `changed: false`,
empty completed/uncertain actions and `evidence_path: null`.

| Outcome | Exit | Meaning and next step |
|---|---|---|
| READY | 0 | All preparation prerequisites observed satisfied, no pending restart; next `./install.sh --preflight` in the selected Linux shell |
| BLOCKED | 2 | Unsupported/unknown facts, collision, missing prerequisite or declined/missing consent before changes; show the single command addressing the first dependent blocker |
| RESTART_REQUIRED | 3 | Completed prerequisite work requires operator restart/login; remaining stages stop, readiness false; give exact restart scope/command, then reinventory on rerun |
| PARTIAL | 4 | Some confirmed work completed but another stage failed or effects remain uncertain; stop dependents, preserve observations; rerun read-only plan before separately approved resume |
| FAILED | 1 | Executed attempt failed with no confirmed completed work and no uncertain mutation effects; safe cause and concrete inspection/retry command |

Timeout exits 124 and interruption exits 130 remain distinct transport results;
JSON still reports PARTIAL when confirmed/uncertain effects exist, otherwise
FAILED if an attempt started or BLOCKED before it. Invalid arguments use exit
2 with BLOCKED when an envelope can be rendered. Help exits 0 without claiming
READY. Installer setup/reset/phase exits stay unchanged and must not be mapped
to preparation success.

Precedence: unexpected failure/uncertain effects after mutation -> PARTIAL;
failed attempt without effects -> FAILED; successful checkpoint needing restart
-> RESTART_REQUIRED; pre-mutation guard -> BLOCKED; all verified -> READY.
A restart requirement may coexist with PARTIAL and remains in `restart`.
Use confirmed post-action observations, never return code alone, to populate
completed actions. Re-observe after failure; if observation fails, affected
actions are uncertain. Do not claim rollback from an attempted cleanup.

Existing `SUCCESS` maps only to a successful capability observation; aggregate
READY requires all prerequisites. `BLOCKED` maps to BLOCKED before mutation;
`FAILED` maps according to completed/uncertain effects; `TIMED_OUT` and
`INTERRUPTED` retain 124/130. No legacy adapter proves full preparation readiness.
Preparation never verifies deployed services: `services_verified` is false in
this envelope. Runtime/setup service verification has its own result/evidence.

## 6. Console and machine examples

Illustrative target output, not an output captured from an implemented command:

```text
Preparation: BLOCKED (packages_missing); services have not been verified.
Plan: install missing incus from Ubuntu APT; requires package-stage sudo.
Preserve: existing Incus daemon, storage, networks, profiles and credentials.
Next: ./prepare_linux.sh
```

Minimal illustrative JSON projection for an unchanged, already prepared host;
actual plans also include the target, selection, resources and observations
listed above. `actions: []` here means every prerequisite was observed ready,
not that inventory was skipped.

```json
{
  "schema_version": 1,
  "mode": "preflight",
  "read_only": true,
  "actions": [],
  "blockers": [],
  "restart": {"scope": "none", "command": null},
  "result": {
    "status": "READY",
    "exit_code": 0,
    "changed": false,
    "completed_actions": [],
    "uncertain_actions": [],
    "preparation_ready": true,
    "services_verified": false,
    "next_command": "./install.sh --preflight",
    "evidence_path": null
  }
}
```

Each diagnostic includes stage, safe cause code, observed vs required state,
whether changes occurred, restart scope, and exactly one concrete next command.
Use the selected distro/user/checkout in Windows handoffs, rather than unresolved
placeholders. For a stopped selected distro: `wsl.exe -d Ubuntu-24.04`.
For an apply-capable Windows preparation blocker:
`./prepare_windows.ps1 -Distro Ubuntu-24.04` in elevated PowerShell.
For Windows reboot: `Restart-Computer` with explicit whole-host scope.
For Linux package recovery: `./prepare_linux.sh --dry-run`; do not automatically
remove packages or run blanket APT repair. Commands are advice only and must
not contain credentials. Failed/blocked messages never say services are ready.

## 7. Rerun, preservation and recovery

Reinventory on every run; skip only verified satisfied steps. Consent covers
only unsatisfied actions in this invocation. Do not trust a stage log as proof
of current readiness, persist live approval, replay a command blindly or reset
to make recovery easier. Existing protected credentials, configuration and
healthy managed workloads survive preparation and ordinary install.

W08 stage records include release/contract version, target/selection identity,
configuration fingerprints, action IDs, before/after observations, confirmed
and uncertain effects, timestamps, exits, restart boundary and safe cause.
Write only after apply approval, atomically to owner-controlled storage;
Linux directories 0700/files 0600, Windows equivalent restrictive ACLs. Refuse
symlinks/foreign ownership. Evidence storage preflight must succeed before
mutation. Evidence write failure after mutation is PARTIAL, never READY.
No raw command output, tokens, passwords or credential values in records.
Interruption records recoverable observations if possible and propagates exit
130. A failed evidence write cannot erase known successful earlier stages.

After restart/interruption/failure, read-only planning must work without
repairing state or writing evidence. A separately approved apply re-observes,
resumes only missing safe steps and halts dependents on failure. Nontransactional
APT/Windows features do not trigger automatic removal or whole-host rollback.
An explicit destructive install reset remains outside preparation, using the
existing exact confirmation/consent boundaries; ordinary WSL install migration
is W07, not a delivered W01 capability.

## 8. Acceptance and verification handoff

| Acceptance | W01 verification | Later implementation acceptance |
|---|---|---|
| BOOT-W01-AC1 | Source inventory/ownership table and independent architecture review | Each work package extends its named owner |
| BOOT-W01-AC2 | Plan field/scenario review; existing native no-write tests | W02–W08 prove all host/config/state/evidence writes absent in read-only modes |
| BOOT-W01-AC3 | Existing `test_entrypoint_imports_without_third_party_dependencies` (`python -S`) and shell/source inspection | W02/W04 missing-interpreter/help/archive tests, no third-party imports before bootstrap |
| BOOT-W01-AC4 | Concrete diagnostic examples and readiness/exit decision table | W07/W10 assert actual help/console/JSON commands and truthful service states |

Required deterministic scenarios for consuming packages: unsupported target;
fresh supported host; satisfied no-op; missing consent/EOF; stale plan; foreign
resource/configuration collision; missing Python; package lock/network timeout;
partial package installation; restart boundary; interrupted resume; failed
postcheck; evidence failure before/after mutation; credential redaction;
matching and edited checkout reuse; stopped distro; profile/selection capacity
failure. Assert no writes or mutating calls for read-only modes, preserved
unrelated state on rerun, finite timeouts and halted dependent stages.

W01 is documentation/contract work: local static and existing mocked regression
checks are APPLICABLE_LOCAL. Installation/browser checks are NOT_APPLICABLE /
LIVE_NOT_APPLICABLE for this change; no product behavior changes. W09 owns live
bootstrap qualification. Its approval must identify an authorized recoverable
host/snapshot and each scenario's committed SHA, host/build/distro/kernel,
profile/selection, product/tool versions, commands, exit codes and redacted
before/after evidence. Unit, mock, skipped, stale or existing #427 observations
are not new live bootstrap proof. External checks are
EXTERNAL_GATE_NOT_APPLICABLE to local contract completion; reassess publication
requirements separately. Follow the canonical
[verification-state policy](../process/verification-state-policy.md) and
[issue completion discipline](../process/issue-completion-discipline.md).

## BOOT-W02 delivered Linux prerequisite substage

The shared package/Python command now accepts supported native/WSL2 Ubuntu.
It does not project the full aggregate bootstrap envelope yet. Read-only modes
return BLOCKED/2 for missing prerequisites and write nothing. An unchanged
prepared host performs no writes. Apply shows separately approved bounded index
refresh, then exact candidate installation consent, and separate user Python
consent. Declining after refresh reports possible index changes. The shell's
protected interpreter record precedes missing-interpreter APT; the existing
protected preparation writer records full package attempts and observed state.
Runtime and build locks are hash-checked before pip; editable installation uses
--no-deps --no-build-isolation. No installer/reset, Windows, Incus daemon or
kernel/network configuration is changed by this substage. Live qualification
remains LIVE_CONSENT_MISSING for the new bootstrap behavior.

## BOOT-W03 delivered Incus capability

After the W02 package/Python substage, `prepare_linux.sh` delegates to the
prepared user Python runtime for canonical YAML/provider policy. Separate exact
stage consent covers daemon startup, ordinary-user access, then absent resolved
storage/bridge/profiles. This is create-only explicit initialization, without
`admin init`, global default profile changes or existing resource edits. A new
bridge receives an explicitly planned private IPv4 subnet checked against host
routes/addresses and Incus networks. Compatible existing resources retain their
identity/configuration; incompatible collisions block with remediation.

Read-only inspection checks systemd first and never queries a stopped daemon
through a socket that could activate it. Missing user access is not verified
using sudo. New persisted group membership requires logout/login (exit 3), then
reinventory. `sudo -v` may be needed before narrowly elevated startup/group actions.
Each mutation rechecks the plan and verifies its effect and preservation of
unrelated inventory; changed target/configuration/resources invalidate consent.
Calls have finite deadlines and zero automatic retries. Failures halt dependents,
record redacted confirmed/uncertain actions, preserve transport exits 124/130 and
require a fresh plan before resume. Read-only/refused/no-op stages write no evidence.

READY/0 proves only current-user Incus version/info and all declared resources.
BLOCKED/2 covers pending actions/collisions/refusal, RESTART_REQUIRED/3 pending
login, PARTIAL/4 observed or uncertain mutation effects, FAILED/1 no-effect
attempt failure. Kernel/bridge access integration and aggregate install handoff
remain W06/W07; JSON/unattended full bootstrap envelope remains a later integration.
The fixed profiles retain their existing #440/#444 selection authority. New
bootstrap live qualification remains LIVE_CONSENT_MISSING. See the accepted
[Incus preparation ADR](../arc42/09_decisions/adr-explicit-incus-preparation.adoc).
