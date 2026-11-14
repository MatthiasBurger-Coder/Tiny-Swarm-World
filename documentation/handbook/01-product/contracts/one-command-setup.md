# UX-01 one-command setup CLI and operator contract

> Current availability: Windows preparation and bridge tooling were removed.
> Windows paths and commands below describe the recorded audit/design revision,
> not runnable interfaces in this checkout. Use the [installation guide](../../03-user-guide/user_guide/installation.adoc)
> for current Linux entry points. Historical acceptance does not qualify current source.

Contract version: **1.0.0**. Status: **specified; wrappers not implemented**.
Issue [#489](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/489),
parent [#488](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/488).
Audited source: `ca6902579f51c2c6d9439bf9c58dec02bfb45a93`, 2026-11-14.
Normative words below constrain future UX-02–UX-08 implementation. They do not
assert that either setup command exists, runs or qualifies a release.
Incompatible flags, state meanings or exit changes require a major version;
additive optional fields require a minor version; clarifications require a patch.

## Baseline audit and compatibility matrix

Repository paths are relative to its root. Baseline inspection reads source;
no preparation, installer, host probe or live command was executed for UX-01.

| Surface | Observed implementation / contract | Compatibility requirement |
|---|---|---|
| `setup_linux.sh`, `setup_wsl.ps1` | Absent at audited source | New interface names reserved by #488; never advertise as runnable until delivered |
| `install.sh` | Forwards to `modules/tsw_native_linux/install.sh`, then `boostrap/install.sh`, then `modules/tsw_core/src/simple_installer.py` | Keep argument forwarding and existing advanced entrypoint |
| `tsw` | Forwards to Linux module CLI | Preserve lifecycle commands; not a bare-host Python bootstrap |
| Linux preparation | `modules/tsw_native_linux/boostrap/prepare_linux.sh` delegates dependency-light prerequisite shell and `modules/tsw_core/src/prepare_linux.py` | Reuse package, Python, Incus, network and protected recovery owners |
| Windows preparation | `modules/tsw_windows_wsl/bootstrap/prepare_windows.ps1` delegates `preparation/Preparation.psm1` and its application/adapters | Preserve existing qualification guard, selected distro/account and source proof |
| Preparation profiles | `default`, `service-access`; selected with `--service-profile` / `-ServiceProfile` | These are existing compatibility presets, not minimal/custom aliases |
| Installer flags | `--preflight`, `--dry-run`, `--service-profile default\|service-access`, `--profile classic`, `--headless`, `--non-interactive-live-approval` | Keep installer meanings; its `classic` alias maps to default and differs from new setup `--profile` vocabulary |
| Installer reset | `--confirm-reset` is explicit deprecated WSL compatibility | Never forward or infer reset through new setup |
| Selective setup | `ServiceSelectionService`, CLI `selection.py` / `selective_setup.py`, manifest/CAS and profile lifecycle | Reuse #440/#444 planner and guarded setup; do not bolt selective flags onto the legacy installer |
| Preparation exits | Existing contracts include readiness/restart/partial outcomes; native package failures and installer child exits vary | Leave old exits unchanged; new wrapper envelope maps observed stage outcomes, retaining original child exit |
| Evidence / consent | Existing preparation records, installation evidence and CLI live consent remain separate | Reference existing records; no stored or transferable approval |

[#427](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/427)
delivered native installation and scoped Ubuntu 26.04 scenarios. It does not
prove the new combined workflow. #452 is closed (`not_planned` at inspection),
while its [BOOT-W10 audit](../../07-evidence-release/evidence/issue-462-bootstrap-completion-audit.md)
records incomplete original fresh-host acceptance and ordinary Windows Apply
remaining unqualified-blocked. Its existing-host observations are historical,
source/scenario-specific evidence. Preserve them without reopening or duplicating
bootstrap work. Closure of #440 or #363 likewise grants no new capability support.

Root preparation scripts do not exist at this baseline. Use the module paths
above when referring to delivered commands. The current operational instructions
remain the [installation guide](../../03-user-guide/user_guide/installation.adoc).

## Proposed entrypoints and options

The future normal invocation is `./setup_linux.sh` on native Ubuntu and
`./setup_wsl.ps1` from PowerShell on Windows. Both display a plan and request
stage-specific consent before apply. PowerShell uses named switches below;
Windows never invokes product Python outside the selected WSL2 environment.
Start from a trusted checkout. Extracted releases require verified complete
assets and must not be presented as end-to-end supported while installer Git
metadata prerequisites remain unresolved.

| Linux flag | PowerShell equivalent | Version 1 meaning |
|---|---|---|
| `--help`, `-h` | `-Help` | Print static usage/options/support limits without dependencies, probes, elevation or writes; exit 0 |
| `--preflight` | `-Preflight` | Bounded read-only inventory and readiness/blockers; no apply |
| `--dry-run` | `-DryRun` | Same inventory plus ordered exact proposed changes; no apply |
| no mode flag | no mode switch | Guided apply: inventory → plan → consent → delegated stages |
| `--profile <name>` | `-Profile <name>` | Service-selection UX: `default`, `service-access`, `minimal`, `custom`; availability follows planner/capability admission below |
| `--services <ids>` | `-Services <ids>` | Canonical comma-separated IDs; requires `custom` |
| `--verbose` | `-Verbose` | Additional redacted stage diagnostics on stderr; no raw command/environment/credential dumps |
| `--json` | `-Json` | One versioned result envelope on stdout; no prompts; apply without fresh explicit consent is blocked |
| none | `-Distro <registration>` | Explicit selected distro; if omitted, prompt only in interactive apply when selection is necessary; read-only ambiguity blocks |
| `--install-dir <path>` | `-LinuxCheckout <path>` | Optional user-owned Linux-native destination, inspected/planned before copy; no overwrite/adoption |
| `--resume` | `-Resume` | Reobserve protected checkpoint, source, selection and host; rerender plan and request new consent; never replay saved approval |

No separate `--apply` flag is defined in v1. Default invocation is guided apply.
No generic unattended `--yes`/`-Force`, reset or qualification bypass is exposed.
Existing advanced preparation/installer consent flags retain their old scope;
they are not forwarded through an unreviewed catch-all argument list. Unknown
options fail with exit 2 before probes. Preflight/dry-run/help are mutually
exclusive. Read-only modes reject resume and any apply approval. Help validates
syntax but never initializes runtime composition. Version 1 does not define a
Linux `--distro` option or an automatic install-and-upgrade mode.

## Targets and fail-closed decisions

| Observed target or selection | New wrapper decision |
|---|---|
| Native Ubuntu 24.04/26.04 x86_64 | Candidate target allowlist; apply still requires current prerequisites, exact source and applicable qualification |
| Windows 11 x86_64 and selected Ubuntu 24.04/26.04 x86_64 WSL2 | Candidate only; exact Windows build/WSL/distro combination must pass existing qualification policy; ordinary guard remains |
| WSL1, Windows 10, ARM, other distributions/releases, macOS, unreadable identity | BLOCKED before dependent mutation; report exact unsupported/unknown fact |
| Stopped selected WSL distro | Do not start for preflight/dry-run; Linux facts UNKNOWN; supply explicit operator start step |
| Ambiguous distro selection without explicit `-Distro`, unknown ordinary account, source mismatch or unsafe destination | BLOCKED; explicit selection may coexist with unrelated distros; no guessed account, replacement checkout or whole-installer sudo |
| Unsupported selection, removed foundation, catalog cycle or capability absent/unknown | BLOCKED; no silent fallback, service omission or reset |
| Missing capacity, occupied port, foreign Incus/bridge resources or changed plan | BLOCKED; preserve unrelated state and show specific remedy |

An allowlist is not a qualified support matrix. There are **no new one-command
qualified release rows** in UX-01. Record exact versions and source SHA for any
future row through UX-07; never infer them from version minimums, distro names,
historical #427/#452 results or current host reachability.

## Profile resolution and lifecycle integration

Use the [canonical selection contract](service-selection.md),
[installation manifest](installation-manifest.md) and
[selective setup guide](../../03-user-guide/user_guide/selective-setup.md).
Runtime remains Incus-managed LXC with Docker Swarm Classic; `--profile` here
selects services, not a provider, host Incus profile identity or runtime engine.

| New UX request | Canonical selection request | Required behavior |
|---|---|---|
| No explicit profile/services, fresh install | Existing compatibility default from canonical policy | Show effective preset and dependency closure; no second wrapper default/catalog |
| No explicit profile/services, existing manifest | Persisted resolved selection | Preserve selection, identity, credentials, versions and management writers |
| `default` / `service-access` | Explicit matching service preset | Planner expands canonical catalog and checks against existing state |
| `minimal` | Canonical `minimal=True` | Mandatory host Incus prerequisite and managed Portainer foundation; no optional applications |
| `custom` plus services | Canonical explicit service IDs | Resolve transitive dependencies and explain automatically included foundations/dependencies |
| `custom` without IDs; IDs without `custom`; minimal plus IDs | Invalid new UX combination | Exit 2 before host inventory; advanced existing CLI precedence stays unchanged |

Do not expose `classic` as a new setup profile alias: it names the runtime and
already has a distinct installer compatibility meaning. Never copy catalog IDs,
dependency graphs or capacity estimates into either wrapper. Validate duplicate,
empty, wildcard and unknown IDs using canonical rules. Do not introduce a second
selection file format; advanced `--selection-config` remains with existing CLI.

Show requested versus resolved services, dependency reasons, catalog/source
revision, existing selection and additions. Missing resource declarations stay
UNKNOWN; minimal is not proof of a smaller qualified machine. Retain provider
capacity floors and ownership/exposure gates. A planner-supported custom profile
can still be blocked for live apply by capability admission.

Fresh selective setup delegates existing guarded setup and commits the manifest
only after full verification. Repeated selection follows existing reconciliation;
additions use its existing admission/lease/CAS path. Deselection remains refused
for apply; offer the existing removal preview without deleting data. A runtime
success followed by manifest failure is PARTIAL, not installation complete.
Unknown legacy state requires explicit inventory/adoption, never inferred identity.
Do not route minimal/custom through `install.sh --service-profile`: that parser
does not accept them. UX-02/04/05 must integrate the existing Python setup service
behind the common installation boundary before enabling these new choices.

## Stage, plan and consent contract

Stable stage IDs: `preflight`, `plan`, `consent.prepare`, `prepare`,
`consent.install`, `install`, `verify`, `report`. Restart is a boundary after a
stage, not a successful installation. Resume uses the same entrypoint and
original target/selection options plus `--resume` / `-Resume`.

Preflight checks source/assets, OS/build/architecture, distro/account, capacity,
privileges, destination, package/Python prerequisites, provider ownership and
selection-dependent network/ports. Unknown facts block dependent actions.
Dry-run renders exact packages, keys, resource identities, dependencies,
before/after values, privilege, timeout, restart scope and verification probes
using the [bootstrap plan](bootstrap.md). Planning missing prerequisites does
not make the host READY. Reinventories after preparation may change the install
plan; render that plan before separate installation consent.

Consent is exact `yes` for the displayed stage plan, bound to target, source,
selection, observed configuration and proposed actions. A drifted identity,
selection, privilege or plan invalidates consent. Never derive approval from
environment variables, saved state, parent issue, preparation approval or resume.
Noninteractive/JSON apply blocks without an explicitly designed stage approval
interface; v1 defines none. No unbounded retry or prompt loop.

Read-only invariants: no files, logs, caches, bytecode, venvs, evidence records,
temporary managed state or mutation locks; no APT refresh, network download,
service activation, WSL startup, Incus initialization or bridge refresh. JSON
may be redirected by the operator; the command does not write it. Dependency
absence reports UNKNOWN/BLOCKED rather than bootstrapping just to inspect.

Prepare delegates existing owners; install reconciles without reset. Stop
dependent stages on failure. Elevate only the bounded stage that needs it.
Guide account creation, login/group refresh, selected-distro restart or Windows
reboot as explicit operator actions; never silently run global WSL shutdown,
reboot, unregister, broad firewall disable, credential rotation or node reset.
Checkpoint observed completed/uncertain effects through existing protected
records. Resume reobserves them; it is not rollback, consent persistence or
permission to repeat uncertain mutations.

## Result envelope, exits and operator report

New envelopes carry `schema_version: 1`, `contract_version: "1.0.0"`, source
revision, mode, target (unknown facts explicit), requested/resolved selection,
stage, outcome, `exit_code`, `child_exit_code` (nullable), `changed`, completed,
pending and uncertain actions, blockers/remedies, restart scope, existing
evidence references, and `next_command`. Use existing OperationResult and
bootstrap records rather than changing their schemas/status vocabulary.

| New wrapper outcome | Exit | Meaning |
|---|---|---|
| HELP / READY / PLAN_READY | 0 | Requested read-only output complete; all prerequisites observed for READY; PLAN_READY never implies installed |
| INSTALLATION_COMPLETE | 0 | Delegated installation and required verification succeeded; service live result remains separate |
| FAILED / PARTIAL | 1 | Stage/verification/persistence failure, including uncertain effects; preserve original stage/child exit |
| BLOCKED | 2 | Invalid input, unsupported/unknown state, declined/missing consent or pre-mutation guard |
| RESTART_REQUIRED | 3 | Explicit login/distro/WSL/Windows boundary; remaining install stages have not completed |
| TIMEOUT | 124 | Bounded stage exhausted; report whether effects occurred/are uncertain |
| INTERRUPTED | 130 | Operator interruption; preserve confirmed progress/uncertainty |

Preflight/dry-run with missing prerequisites returns BLOCKED/2 with the usable
plan, never PLAN_READY/0. Timeout/interruption exit takes precedence over effect
classification; retain PARTIAL/uncertain details. A child nonzero exit never
becomes wrapper success. Keep original child exit and cause in the stage record;
all legacy direct command exits remain unchanged. If a child cannot distinguish
failure from blockage, report FAILED with wrapper exit 1; retain its original
exit only in `child_exit_code` and stage context rather than guessing the cause.

Reports distinguish `host_prepared`, `installation_complete` and per-service
`live_state`. A successful prepare stage cannot set installation complete.
List only resolved services, observation time/probe scope, health and verified
URLs. Label configured URLs as unverified rather than implying reachability.
Report protected credential file/reference and initialization instructions,
never passwords/tokens/private keys/environment dumps. Give local protected
log/evidence paths and one concrete next command including necessary target
options; never execute it automatically. Read-only evidence path is null.
Shared evidence redacts host identities and sensitive path details. If protected
evidence cannot be persisted before a mutating stage, block that stage; after
effects, report failure/partial with the last known protected reference.

## Architecture review and delivery gates

Wrappers parse/translate arguments, hand off selected platform context and render
results. Existing preparation application services, installation/setup services,
ports, infrastructure composition and adapters retain orchestration and writes.
PowerShell owns only its existing pre-Linux boundary; Linux common application
code owns product execution. Bridge adapters retain exclusive network ownership;
manifest/catalog/profile owners retain lifecycle ownership. No second service
registry, package installer, networking engine, state repository or reset flow.
No domain dependency on CLI/PowerShell/filesystem; no concrete adapter wiring in
application services. Existing accepted lifecycle, bootstrap, consent and scoped
profile ADRs remain authoritative; UX-01 changes no runtime ownership decision.

Independent architecture/requirements/evidence review is recorded in the
[issue evidence](../../../../.tiny-swarm/evidence/issue-489/completion_audit.md).
Implementation owners must stop if enabling an option requires a new architectural
decision or weakens an existing guard.

| Follow-up owner | Required new evidence before claiming behavior |
|---|---|
| UX-02 #490 / UX-04 #492 | Actual wrappers, argument/exit forwarding, no second orchestrator; help without interpreter/dependencies |
| UX-03 #491 | Conditional networking, merge/preservation, collisions, explicit restart and existing bridge integration |
| UX-05 #493 | Same canonical planner closure as advanced CLI; minimal/custom/persisted selection; truthful protected report |
| UX-06 #494 | Exact-stage resume, changed plan invalidation, repeated no-op observations, interruption and uncertain effects |
| UX-07 #495, coordinated with #363 and #440/#449 | Exact-SHA fresh-host, rerun/restart/recovery on both target families; browser/DNS/ports, credentials references, capacity and unsupported controls |
| UX-08 #496 | Copyable implemented commands only; qualification/support audit before README one-command promotion |

Targeted implementation tests must cover help and dry-run with filesystem/write,
process/service activation and logging spies; stopped WSL; malformed flags;
unsupported OS/architecture; invalid selection/foundation removal; missing
dependencies; no-consent/plan-drift; timeout/interruption; manifest failure after
runtime success; absent protected evidence; secret-free stdout/stderr/JSON;
correct child-exit mapping and stage-specific next command. These are acceptance
obligations, not executed tests or host evidence for UX-01.

UX-01 verification is static contract/source/architecture review only. No new
workflow is live-qualified. Future implementation runs nearest targeted tests,
then applicable QUALITY.md gates when authorized. Installation/browser/live
applicability must be classified through the canonical
[verification-state policy](../../05-development/process/verification-state-policy.md)
and fresh explicit consent obtained before any host change. Prior closed issues,
unit mocks, configured URLs or external-gate absence cannot count as live success.
Setup success makes no upgrade, runtime-replacement, destructive reset,
multi-host, production or HA guarantee.
