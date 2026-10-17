# BOOT-W09 requirement matrix

## Current operator-accepted scope — 2026-10-17

The operator explicitly accepts deferring the remaining live hardening scenarios
because the available test setup cannot provide them. This supersedes earlier
BLOCKED/INCOMPLETE conclusions caused solely by those missing scenarios. The
agreed delivery consists of the implemented repairs, existing-host live checks
and operator documentation already evidenced for candidate `d2fd89be`.

`DEFERRED_BY_OPERATOR` below is a scope disposition, not a live verification
state. Existing raw LIVE_PARTIAL, prerequisite-missing and unexecuted results
remain unchanged; no missing scenario becomes LIVE_VERIFIED.

| Requirement / scenario | Accepted disposition and residual risk |
|---|---|
| R461-02 / S01; original AC1 fresh-host portion | DEFERRED_BY_OPERATOR: clean native Ubuntu26.04 and clean Ubuntu26.04 WSL2 first installation not verified; initialized-host reconciliation is the tested scope |
| R461-04, R461-13 / S03, S12; original AC2 remaining portion | DEFERRED_BY_OPERATOR: broader unrelated-resource fixtures and new-target reset isolation not verified; historical separately owned-VM reset is not transferred and no new reset is authorized |
| R461-05 / S04 | DEFERRED_BY_OPERATOR: complete insufficient/minimum/adequate resource-boundary matrix not executed on the supplied targets |
| R461-06 / S06 | DEFERRED_BY_OPERATOR: actual stale-session/new-group-membership transition not executed |
| R461-07 / S07 and remaining S08 cases | DEFERRED_BY_OPERATOR: actual IP drift, native port collision and foreign-executable rejection not live verified; existing WSL exposure collision remains verified |
| R461-08 / remaining S09/S10 | DEFERRED_BY_OPERATOR: full entrypoint download and interruption/recovery cases beyond the verified dependency stage, including APT/Incus/bridge boundaries, not executed |
| R461-18 / remaining S13 | DEFERRED_BY_OPERATOR: aggregate read-only/consent inventory comparison not completely exercised; existing targeted evidence remains valid |

No further live execution is required for this operator-accepted scope. This
accepts a coverage limitation; it does not remove runtime guards, change product
support, establish whole-OS/external-volume recovery, or qualify an untested
release/scenario. Ubuntu24.04 remains outside the required live target scope.
The completed product source and its full local quality result are unchanged.
Historical requirements and audit conclusions below describe their original
scope. Independent reviewer `/root/remediation_completion_audit` returns PASS
for this amended scope only; see completion_audit.md.


## Historical requirement rollup before operator deferral — 2026-10-17, d2fd89be

Historical requirement rows below retain their original evidence/status. Current
source-bound observations are in `combined_qualification_20261017.json` under
`latest_campaign`; they do not qualify a missing target or scenario.

| Requirement / scenario | Current supplied-target result | Remaining boundary |
|---|---|---|
| R461-01 / release scope | Ubuntu26.04 is the user-selected live qualification release | Ubuntu24.04 remains supported but explicitly unqualified; it is not an issue blocker |
| R461-02 / S01 fresh hosts | BLOCKED | Both supplied Ubuntu26.04 hosts already initialized; fresh 26.04 targets remain unavailable |
| R461-03 / S02 rerun | Both ordinary full installers and reruns exit0; WSL preparation and postrestart reruns exit0 | Native clean preparation retains intentional LXD/IPv6 guards |
| R461-04, R461-13 / S03 preservation | Three node configs, markers, volumes, service IDs and TLS preserved; WSL registration/settings preserved | No new-target reset; no arbitrary unrelated-resource fixture claim |
| R461-06 / S05, S06 | Native actual host reboot and selected-WSL restart LIVE_VERIFIED; identities and postrestart TLS/auth/data verified | Actual stale/new group-membership transition unexecuted |
| R461-07 / S07, S08 | WSL observed IPv4 unchanged; S08 WSL exposure collision LIVE_VERIFIED with guarded restoration and API/data checks | No address-drift, native collision or foreign-executable rejection PASS inferred |
| R461-08 / S09, S10 | Real Python dependency-stage offline failure/interruption and connected resume/no-action rerun verified on both hosts | Supplementary stage proof; full installer/CLI fault recovery open |
| R461-09 / S11 | Nine TLS routes and seven real API positive/negative auth checks on each supplied26 target | No browser/Selenium or strict Windows revocation success inferred |
| R461-10, R461-11 | Exact source, aliases/versions, commands/exits and redacted hashes retained; 4f native coldrestore vs d2 subsequent runs explicitly separated | No dirty-source or transplanted historical qualification |
| R461-14, R461-15 / AC3, AC4 | All releases explicitly UNQUALIFIED; final local full gate2631 tests/18 existing skips, arch43/contracts7/type808 PASS | Local gate does not close missing live scenarios |
| R461-16, R461-18 / completion | Required evidence package updated; independent final audit requested after successful scoped S08 | Whole issue INCOMPLETE; no DONE authority |


## Three-Amigos remediation scope, 2026-10-17

R461-33, later user authorization: no other session is active; combine the
additional local bootstrap/network/certificate worktrees and qualify the combined
candidate. Integration takes place only in the isolated live-source worktree;
original worktrees and pending changes remain untouched. The branches diverge
at 0528aac9, so merge changes by ancestry and purpose, never replace the source by
the tip-to-tip diff. Retain accepted root-baseline metadata, resource, IP Helper,
firewall, sudo-session and R461-29/31 ownership guards. Review incoming nftables,
asset-transfer, port-selection, Windows identity and explicit TLS trust changes
before integration. Repeat focused/full quality and independent security review
for the combined source, freeze an exact local commit, then run serialized live
scenarios. Prior full-gate/counterprobe results are not combined-source results.
Installation/restarts remain authorized on supplied hosts; fault/reset scenarios
still require a concrete reviewed restoration boundary and their applicable scope.

R461-32, user-added documentation scope before editing: update operator guidance
with verified findings and all applicable manual certificate/trust, sudo/group,
LXD preservation, Windows bridge-owner interaction and restart/recovery steps.
Allowed additional files: new manual-host-steps.md, existing troubleshooting.adoc,
tools/windows/README.windows-wsl-bridge.md, navigation links in README.md and
installation.adoc, plus issue evidence. Correct the observed stale automatic-reset
and Windows-mounted normal-install examples. Acceptance: commands match effective
TLS resolver/configuration and existing guarded entrypoints; public CA only;
Linux/WSL and browser/Windows trust separated; manual OS actions not described as
automatic project behavior or executed live success. Documentation review and
verification-policy/diff checks follow final product gate; no new runtime behavior.

R461-31, approved before implementation: the source-hashed read-only WSL overlay
exposed a second trust defect: a genuine Incus proxy has mapped container-root
credentials, not host UID 0. Actual API-selected manager init and listener share
complete UID/GID maps and user/network namespaces; both match namespace root,
and the listener executes the same safe host-root Incus inode as the daemon.
Independent architecture and security reviewers accept only this precise bound
path, retaining host-root support, before/after process/API/device revalidation
and full fingerprint evidence. Allowed additional files: existing trusted_process.py,
new tests/test_network_process_identity.py, related network tests/ADR/guide and
issue evidence. No arbitrary nonroot executable allowance or guessed PID-file path.
Regression must reject foreign namespaces/maps, nonroot credentials, invalid API
PID, changed process/init/daemon/device and unsafe executable identity. Full quality
must be repeated after integration. No new full live qualification is claimed.

| ID | Requirement | Allowed files | Acceptance evidence | Status |
|---|---|---|---|---|
| R461-29 | Recognize an owned Incus dual-stack wildcard only with per-socket `v6only:0`, exact configured IPv4-wildcard proxy and trusted process; preserve raw family evidence | network_preparation/configuration.py, inventory.py; tests/test_network_preparation.py; existing network ADR/user guide; issue evidence | Red/green and negatives, raw fingerprint drift, full quality PASS; source-hashed read-only counterprobe accepts both real listeners; committed-source installation rerun remains open | LOCAL_VERIFIED; COUNTERPROBE_VERIFIED |
| R461-30 | Make the intended active/unverified LXD guard actionable without automatic runtime replacement or instance changes | domain/native_preparation.py; tests/test_prepare_linux.py; installation.adoc; issue evidence | Regression verifies LXD diagnosis, blocked apply/no package installation and active daemon/socket guard retained; full quality PASS. Actual LXD coordination not executed | LOCAL_VERIFIED |

User explicitly requested Three Amigos diagnosis and repairs. Four independent
read-only roles (Requirement Engineer, System Architect, Python Automation
Developer and Tester) agree on narrow remediation. EPIC #452 still applies;
automatic runtime replacement remains excluded. Senior System Architect approves
the dated network ADR amendment before production edits. Gate:
READY_FOR_WORKFLOW for these two sequential, nonoverlapping remediations, without
reopening the historical completed #355 workflow. Root owns integration; roles
are read-only. No reset, LXD shutdown/removal, IPv6 firewall change or new IPv6
endpoint support is authorized by this correction. Local checks APPLICABLE_LOCAL;
source-bound existing-host verification APPLICABLE_LIVE under existing supplied-
host consent. Fresh-host/recovery qualification and external checks remain open.

Latest continuation (2026-10-17 Europe/Berlin): see
[SSH qualification record](ssh_qualification_20261017.json). Operator authorized
installation and restarts on the supplied native/Windows hosts and asserted
restoration availability; reset was not authorized. R461-01/10 gained exact
N26-SSH/W26-SSH observations on committed `8d05d690`; neither is a fresh host.
R461-02/12/13/18 remain open: native preparation refuses active LXD, and WSL
preparation completes Python/Incus but blocks on canonical listener exposure.
The old confirmed source-mismatched checkpoint on each host was preserved by
explicit locked archival; no old success was adopted. F461-SSH-01 requires
resolution of the existing LXD conflict without losing its three instances;
F461-SSH-02 requires architecture/security review of IPv6 wildcard listeners
before any validation change. R461-28 gains an authentication-success observation
on this distinct WSL target; it does not qualify the historical owned-VM probe.
No source fix, installation, restart or reset was executed in this continuation.

Issue: [#461](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/461).
Baseline: `0528aac913c37ddfd66fc8f326d5f92505bdd7dd`.
Current frozen Linux sudo-session candidate: `8d05d690aced18c07162162bc86106d2ac85b8a5`. Current frozen Windows bridge candidate: `51bac77cd94e210a3b8640f4e83688180e520057`; corrected bridge live milestone verified. Latest guest Apply and preflight candidate: `51bac77cd94e210a3b8640f4e83688180e520057`; bridge milestone verified, aggregate qualification incomplete. Historical earlier Apply: `e01e1dd5dab2ff7390d782d891a47e2191c1c7a9`. Previous corrected candidate: `bce63aafb6990e9157c8ddb3eb12e4aa9fd1f440`. Historical native/feature runtime: `3da77f8908d598688ed46dd6eab74c5f32a7ac50`.
Dependencies #459 and #460 are CLOSED and integrated. Status: BLOCKED pending
native freshness/restoration and complete live scenario evidence.
This matrix precedes implementation; subsequent live findings extend the explicit remediation scope below.

| ID | Requirement | Type / likely files | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| R461-01 | Define native Ubuntu 24.04/26.04 x86_64 and Windows 11 + Ubuntu WSL2 matrix with exact Windows/WSL versions | Qualification / qualification_matrix.md | Four release rows and required version fields | Read-only N26/W26 version observation; 24.04 targets absent | PARTIAL |
| R461-02 | Run clean-host preparation and install on both families | Live / per-run evidence | S01 in qualification matrix | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-03 | Run repeated preparation and install | Live / per-run evidence | S02 | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-04 | Preserve unrelated Incus and WSL resources | Live / per-run evidence | S03 | Native protected scopes/nodes unchanged; ordinary WSL preservation pending | PARTIAL |
| R461-05 | Exercise resource limits with #440/#444 selection semantics | Live / per-run evidence | S04 | Sourceef7 actual30GiB guest resource assessment VERIFIED: selected21GiB/8CPU/6GiB swap and effective physical/usable RAM independently verified; actual28 refusal retained historically | PARTIAL |
| R461-06 | Cover reboot, selected WSL restart and group refresh | Live / per-run evidence | S05/S06 | Owned Windows guest boot transition verified after confirmed features; selected WSL restart/group refresh still unverified | PARTIAL |
| R461-07 | Cover IP drift and port collision | Live / per-run evidence | S07/S08 | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-08 | Cover unavailable downloads and interrupted-run recovery | Live / per-run evidence | S09/S10 | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-09 | Verify routes and service authentication | Live / per-run evidence | S11 | Not run; credentials/service target unavailable | BLOCKED |
| R461-10 | Record exact committed SHA, host/tool versions, commands, exits and redacted evidence on authorized restorable targets | Evidence / per-run package | Run record contract in qualification matrix | Native preflight/Python preparation records exist; remaining live runs absent | BLOCKED |
| R461-11 | Reuse #363 only with exact scenario/source applicability; reject dirty/mock qualification | Evidence / applicability review | Historical applicability section | #363 source/scenario differ; no live pass inherited | VERIFIED |
| R461-12 | AC1: Both families have fresh/rerun/recovery results with PASS/PARTIAL/BLOCKED | Acceptance / qualification matrix | Explicit BLOCKED rows | Partial native existing-host results; required fresh/rerun/recovery absent | BLOCKED |
| R461-13 | AC2: Ordinary WSL preservation and separately explicit reset isolation have real evidence | Acceptance / per-run evidence | S03/S12 | Ordinary sourceef7 preflight/dry-run preserves registrations/config/state hashes; Current30 checkpoint actual restore and separately authorized Ubuntu terminate/unregister (exit0, empty guest registration inventory) then exact restore PASS; primary WSL registration/config fingerprints unchanged; ordinary full-apply preservation still open | BLOCKED |
| R461-14 | AC3: Each supported release qualified or explicitly unsupported/unqualified | Acceptance / qualification matrix | Four UNQUALIFIED rows; excluded target families | Static release classification | VERIFIED |
| R461-15 | AC4: Targeted regressions and applicable quality/security gates pass on integrated candidate | Local / test_results.md | Existing unchanged regression suites | Focused 35 tests PASS; original audit FAIL, corrected lock strict audit PASS; full Python 3.12 quality PASS; source/lock frozen byte-equivalent | VERIFIED |
| R461-16 | Map acceptance IDs to meaningful tests/redacted evidence and follow repository completion policy | Governance / six-file package | acceptance_checklist.md and this matrix | Completion audit required; issue stays BLOCKED | PARTIAL |
| R461-17 | Thin entrypoints, application/port reuse, Linux execution; Windows preparation explicitly in scope | Architecture / existing entrypoints | Narrow existing Windows persistence fix; Python boundaries unchanged | Static scope check | VERIFIED |
| R461-18 | Cover plan/apply consent, preservation, rerun, bounded failure and write-free preflight/dry-run | Live and local / existing regression tests, per-run evidence | S02/S03/S08/S09/S10/S13 | Local regressions cannot replace live observations | BLOCKED |
| R461-19 | Avoid duplicating #427, DNS, K3s, Podman or multi-host provisioning | Scope / existing evidence | New bootstrap stages and exact release scenarios only | Static scope check | VERIFIED |

Required live acceptance remains unverified. Actual native exit-2 results are
recorded separately from absent executions; no release is qualified.

## Operator steering and qualification blocker remediation

Historical initial steering, superseded by the later scoped reset consent:
on 2026-10-10 the operator identified the native SSH and local WSL targets,
then authorized tests directly on native Linux and creation of a Hyper-V
Windows test environment. No destructive reset authorization or native clean
snapshot was supplied. Live state must now distinguish granted test scope
from missing recovery/cleanliness prerequisites.

| ID | Requirement | Type / likely files | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| R461-20 | Remediate observed runtime dependency audit blocker for AC4 without weakening audit | Dependency / requirements.lock | Narrow urllib3 update using Python 3.12 lock generation | New strict audit PASS and full Python 3.12 gate PASS | VERIFIED |
| R461-21 | Use the supplied native target for authorized testing and provision isolated Hyper-V Windows target | Operator scope / protected local VM assets and run evidence | Native bounded Python preparation; isolated Windows OS provisioned | Win boot/source-bound dry-run/checkpoint restore verified; disk now GPT; First feature UAC launch canceled; retry confirmed features with partial checkpoint failure; owned guest recovery reboot verified | PARTIAL |

Declared additional write scope: requirements.lock for the AC4 security
remediation; tools/windows/preparation/Adapters.ps1 and tests/windows/prepare-windows.Tests.ps1 for the reproduced atomic checkpoint replacement failure; protected ignored VM preparation assets/evidence and documentation/user_guide/windows-preparation.md. Product
Python, architecture and bootstrap authorization contracts remain unchanged. A runtime lock
change requires a new committed candidate before qualification. No live mutation
may bypass the requirement for a recoverable target.

| R461-22 | Repair the live-observed durable checkpoint replacement failure so reruns/recovery retain confirmed effect evidence | Live blocker remediation / Adapters.ps1 and prepare-windows.Tests.ps1 | Narrow NullString fix; existing atomic replace and ACL guards retained | Windows PowerShell 5.1 isolated actual writer creates pending but effect replacement raises ArgumentException; direct NullString replacement succeeds; canonical pending state unchanged. Real-filesystem regression fails before fix, passes after fix under pwsh7 and WindowsPowerShell5.1; corrected full Python3.12 quality PASS. Corrected frozen source-bound protected disposable actual writer create/replace PASS with real ACL guards. Product full-stage qualification remains separate. | VERIFIED |

| R461-23 | Resolve the observed selected WSL VHD trust compatibility before resource apply; preserve manual Ubuntu and all guards | Live prerequisite / storage permission trust finding | Metadata-only VHD role correction independently accepted and verified; historical pre-correction refusal retained | Revised source-bound preflight exit2; resource inventory cause untrusted_evidence_acl; canonical state/config unchanged | VERIFIED: source806 full quality/resource apply exit3; historical memory mismatch resolved by sourceef7 actual30GiB resource assessment VERIFIED |

2026-10-11 authorized continuation: R461-23 remediation scope includes
ResourceAdapters.ps1, tests/windows/resource-files.Tests.ps1, the existing
wsl-capacity-adaptation ADR amendment and windows-preparation user guide.
Independent System Architect and Completion Auditor accept metadata-only selected
VHD path-role correction: retain trusted owner, regular-file/no-reparse and strict
BasePath/ancestor checks; no VHD content IO, ACL rewrite or SID-family whitelist.
Evidence/config/swap guards stay unchanged. User separately authorizes destructive
Ubuntu reset ONLY inside the owned test VM AFTER a new verified recovery snapshot.
Primary/local WSL remains outside that authorization. New runtime changes require
new passing gates and frozen committed source before live qualification.

R461-23 test reporting scope also includes tests/test_wsl_resource_projection.py: explicit Windows child-output decoding keeps native localized errors visible rather than raising UnicodeDecodeError. Return-code and PASS assertions stay strict.

| R461-24 | Correct observed WSL physical-versus-usable RAM accounting without weakening capacity limits | Actual source806 restart blocker / architecture approved 2026-10-11 | Two independent observations; normal-zone present pages exclude holes, MemTotal/cgroup clamp retained; exact five-key parser | Full gate PASS2555; targeted19 tests PASS; independent concrete reviews approve; sourceef7 live physical/usable inventory observed, actual30GiB sourceef7 Preflight and DryRun resource_state VERIFIED, effective_verified=true; full install remains blocked on bridge/state | VERIFIED (resource case only) |

R461-24 scope: tools/windows/preparation/linux-resources.sh, Resources.ps1,
tests/windows/resources.Tests.ps1, tests/windows/prepare-windows.Tests.ps1,
tests/test_wsl_resource_projection.py, existing capacity ADR and user guide,
issue461 evidence. Branch fix/boot-w09-live-qualification-20261010; completed
workflow355 is not reopened. No active overlapping execution lock observed.
Architecture reviewer approves based on actual page-size4096 and normal RAM
present5504671 pages; physical22547132416 versus configured22548578304 bytes.
No tolerance increase, node-budget reduction, primary-WSL reset or release claim.

| R461-25 | Normalize actual hosts text observation before bridge inventory fingerprint serialization; retain content-sensitive consent and all ownership/read-only guards | Live timeout remediation / tws-wsl-bridge.ps1 and bridge-preparation.Tests.ps1 | Declared before implementation; exactef7 trace stops at digest ConvertTo-Json depth12 on extended Get-Content string | Direct inventory124/45s; bounded real-file red/green regression; full quality2555PASS; independent concrete reviews approve | LOCAL_VERIFIED / LIVE_INVENTORY_VERIFIED |

R461-25 authorized issue remediation scope: tools/windows/tws-wsl-bridge.ps1,
tests/windows/bridge-preparation.Tests.ps1, existing Windows preparation guide
and issue461 evidence. Existing Python test runner suffices. No workflow355
execution/replacement, timeout increase, ACL/ownership guard change or
credential dialog bypass. Independent architecture review accepts observation
normalization with unchanged encoding/failures; no new ADR needed. Meaningful
regression must compare metadata-bearing equivalent file content and plain
content fingerprints, and retain actual content/newline sensitivity. New
quality/source freeze is required before affected live qualification.

| R461-26 | Recognize a proven Windows IP Helper portproxy listener without accepting foreign processes or mismatched proxy mappings | Actual owned Windows guest listener diagnosis 2026-10-11 | Declared before implementation; narrow security/architecture review accepted, including concrete type-check amendment | Actual24listeners iphlpsvc/svchost; existing PID4-only predicate rejects them; actual WinPS5.1 red/green plus109initialchecks including trust-negative cases,161combinedchecks; full quality2555PASS; frozen51bac77c; actual bridge install confirmed and independent original15s inventories ready | LOCAL_VERIFIED / LIVE_BRIDGE_VERIFIED |

Proposed R461-26 scope: tools/windows/tws-wsl-bridge.ps1,
tests/windows/bridge-preparation.Tests.ps1, existing Windows preparation guide
and issue461 evidence. Protected heartbeat/state and exact netsh endpoint
matching remain mandatory. No PID/name-only exemption, foreign-listener
termination, ACL relaxation, uncertain-checkpoint rewrite or timeout increase.
The independent15-second inventory timeout remains a separate observed issue;
optimization must be supported by measured component timings before changes.
No active overlapping execution lock observed; completed workflow355 untouched.
New passing regression/quality evidence and frozen source are required before
a new candidate can be live qualified.

| R461-27 | Remove measured per-rule policy-filter query overhead without dropping firewall restrictions or changing deadlines | Owned guest read-only full-projection equivalence/timing experiment | Declared before implementation; concrete performance slice security review accepted | Seven families each506total/24matched, full projected observations equal; old12.7286s vs proposed0.9700s; native161checks and meaningful24-rule query-count RED/GREEN; full quality2555PASS; frozen51bac77c; actual bridge install confirmed and independent original15s inventories ready | LOCAL_VERIFIED / LIVE_BRIDGE_VERIFIED |

R461-27 proposed scope: tools/windows/tws-wsl-bridge.ps1,
tests/windows/bridge-preparation.Tests.ps1, existing Windows preparation guide
and issue461 evidence. Retrieve complete native filter families read-only,
select exact rule identities and retain all existing properties, cardinality,
duplicate, unknown-shape and administrator-restriction checks. Preserve firewall
availability guard, protected-state authority and original15-second deadline.
No cache across inventories and no service/firewall/portproxy/state mutation.
R461-26 listener correction remains a separate slice; no multi-slice commit.


## Combined corrected source freeze (R461-26 / R461-27)

Local candidate `51bac77cd94e210a3b8640f4e83688180e520057` contains the
separately reviewed and committed listener identity and firewall observation
corrections. Full quality PASS: 2,555 tests, 18 existing skips, 43 architecture
tests, seven import contracts and 799 typed files. Native Windows fixture
PASS: 161 checks; the prior per-rule reader fails the controlled 24-rule
regression. Clean committed candidate archive and offline membership proof
were produced; tested source hashes match. At this historical source-freeze point, source-bound original-budget live
qualification was still pending; later actual bridge results are recorded below. Historically the guest retained the earlier e01 failure before the subsequent
verified whole-VM recovery and51bac candidate transfer recorded below.
No additional dialog is needed for the already completed diagnostics.
Issue #461 remains INCOMPLETE and releases UNQUALIFIED.


Actual corrected51bacApply returned4/PARTIAL12:48:13Z with completed action
bridge_install, no uncertain actions, and next_stage_consent_required. Canonical
effect is confirmedtrue/uncertainfalse. Independent12:49:13Z preflight and
dry-run use the unchanged15-second probe budget: bridge/agent/routingreadytrue,
ownershipowned, no bridge blockers, no bridge actions; resourcesVERIFIED.
Both aggregate checks exit2 only linux_checkout_required. Endpoint/login remain
UNVERIFIED. The real-dialog automation refused after180s without submission;
service subsequently runs under the verified current WSL owner. Credential
submission mechanism is not inferred. Cipher deletion and independentSYSTEM
expiry actual12:47:34Z verified. OverallissueINCOMPLETE; Linux handoff preparation
and release-matrix scenarios remain open.


Actual12:54:17Z staging completed: exact trusted51bacarchive extracted by
ordinaryUID1000 into an absent ownednativeext4checkout. Windowsconfirmedbridge
checkpoint bytes unchanged. Linux preflight/dryrun both exit1 because active
sudo APT authentication is unavailable; sudo-ntrue exits1; no host packages
changed. Staging-wrapper0 is not preparation success. WindowsPreflightexit2
bridge_inventory_unavailable retains an intermittent original15-second timeout;
subsequentDryRunexit0 sourceverified, bridgeREADY/noactions/blockers, verified
checkout handoffLINUX_PREPARATION_REQUIRED. Windowscapability/hand-off does not
prove Linux preparation/install or service/endpoint/login readiness. Operator
asked to authenticate and run approved preparation in the same UbuntuTerminal.
Read-only timing diagnostics continue; stable original-budget behavior is not
claimed from one passing sample. IssueINCOMPLETE/releasesUNQUALIFIED.


Independent read-only inspection completed at 2026-10-11T13:13:44Z after the
operator reported preparation finished. Ten protected ordinary-user records
show package verification and Python environment succeeded (exit 0), but Incus
preparation stopped at daemon:start with PARTIAL/exit 4 and an uncertain action.
Active and registered account groups lack incus-admin. Installer Preflight and
DryRun both exit 1: required bridge and IPv4 forwarding controls unavailable.
The diagnostic Incus info --format argument is unsupported; that exit is not a
valid daemon/access observation. A corrected bounded read-only diagnosis is
prepared; no Apply, authentication policy change or uncertain-state rewrite.
Windows source-bound Preflight and DryRun both exit 0, original 15-second probe
budget, bridge/agent/routing ready, no actions/blockers, resources VERIFIED;
handoff remains LINUX_PREPARATION_REQUIRED and services unverified. Confirmed
bridge checkpoint bytes unchanged. Two further passing samples do not establish
stable timing or erase the earlier timeout. No manual command repeat requested.
See windows30_linux_preparation_inspection_result.json. Issue remains INCOMPLETE
and all releases UNQUALIFIED; endpoints/login and full installation unverified.

The single bundled corrected diagnostic launch subsequently failed at Windows
Start-Process -Verb RunAs: elevation was canceled before helper execution.
No corrected diagnostic result exists. No repeated command/UAC request is made;
current daemon state and recovery plan remain unverified. Host elevation is an
execution prerequisite, not missing live-scope authorization. No UAC/sudo policy
change, automatic login or unrelated privileged channel is used.


## R461-28: live preparation loses authenticated sudo session

| ID | Requirement | Type / allowed files | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| R461-28 | Preserve an authenticated ordinary login session for explicit trusted noninteractive sudo preparation calls while isolating child process groups and retaining bounded cleanup, consent and fail-closed authorization | Live blocker remediation / process async runner, Incus runtime/adapter, network runtime/files; scoped tests, process architecture, accepted Incus/network decision amendments and user guide | Declared before implementation; independent architecture/security decision consultation | Native same-TTY sudo-rs comparison: direct 0, new session 1 authentication required, new process group in original session 0; actual owned WSL diagnosis plans only daemon:start after package/Python success. Corrected source was unimplemented/unverified at declaration; now focused85/full2563 PASS, source bytes match isolated gate, concrete architecture/security review accepted; frozen8d05d690; initial owned task exit124/no Linux result; later phase-instrumented retry proves sudo-v exit124 BEFORE runner, realTTY and console-visible metadata, Windows/native checkpoint hashes unchanged and scoped cleanup verified. Desktop diagnostic did not start after cancelled host elevation; next input-desktop guard is prepared/unexecuted. | LOCAL_VERIFIED / LIVE_BLOCKED |

R461-28 changes are limited to `src/tiny_swarm_world/infrastructure/process/async_runner.py`,
`infrastructure/adapters/incus_preparation/{runtime,adapter}.py`,
`infrastructure/adapters/network_preparation/{runtime,files}.py` under that package,
`tests/infrastructure/process/test_execution_contract.py`,
`tests/test_{incus_preparation,network_preparation_files,preparation_login_session}.py`,
`documentation/arc42/05_analysis/arch-03-11-process-execution.md`, the existing
explicit Incus and scoped network preparation ADRs, `documentation/user_guide/network-preparation.md`
and issue461 evidence. Default new-session isolation stays unchanged. The new
keyword-only direct-argv option retains the caller's login session and creates
a distinct child group, with no shell opt-in or interactive fallback. No password
capture, timestamp/sudoers policy change, whole-process root execution, deadline
change, retry or consent bypass. WSL live verification requires a newly frozen
candidate in the selected ordinary user's authenticated Ubuntu TTY. Native
authentication comparison alone does not qualify that patch. Active branch remains
fix/boot-w09-live-qualification-20261010; completed workflow355 untouched, no
active overlapping lock found. See native_sudo_login_session_comparison.json and
windows30_linux_preparation_diagnosis_result.json.


The operator-authorized retry completed the bundled diagnosis at 13:32:09Z.
Incus service is loaded but inactive/dead; its socket listens and no journal
entries were observed. Incus info was deliberately skipped to avoid socket
activation. Bridge sysctls exist at 1; IPv4 forwarding is 0. Package/Python
preparation is already ready, and actual dry-run exits 2 planning only
consented daemon:start (60s). Exact-source Windows Preflight and DryRun both
exit 0/resources VERIFIED, with confirmed bridge checkpoint unchanged. See
windows30_linux_preparation_diagnosis_result.json; earlier elevation cancellation
is historical, and no Linux mutation was executed by this diagnostic.

R461-28 root-cause mechanism was independently reproduced on the authorized
native Ubuntu26 target: in one authenticated SSH TTY sudo-rs0.2.13 accepts
sudo -n true (0), refuses a new-session child (1 authentication required), and
accepts a separate-process-group child retaining that session (0). This does
not retrospectively prove the exact WSL failed transport or qualify the patch.
Source inspection finds async preparation detached every sudo child while
successful APT used the synchronous owner. Independent System Architect,
Security/DevOps and Requirement/Test concurred with the narrow exception;
accepted dated Incus/network ADR amendments preceded implementation.

R461-28 is implemented with default isolation unchanged, direct-argv opt-in
for trusted noninteractive sudo calls only, shell opt-in rejected and separate
group cleanup retained. Focused85 tests PASS. Frozen51 baseline regression
fails4 subcases across2 tests; corrected fullquality PASS2563 tests/18existing
skips,43architecture tests,7importcontracts,800typedfiles. First fullgate2mypy
errors were retained and corrected without ignores or threshold changes.
Concrete security/architecture review has no blockers; root and isolated tested
file bytes match. Source-freeze review is pending; owned WSL candidate execution,
provider/access/network preparation and full installation remain unverified.
See linux_sudo_login_session_local_verification.json and
native_sudo_login_session_comparison.json. Issue INCOMPLETE; all releases UNQUALIFIED.


R461-28 is locally frozen as 8d05d690aced18c07162162bc86106d2ac85b8a5,
parent51bac, in a separately reviewed exact15-file commit. The isolated source
was clean; archive/hash and tested file bytes are verified. Root integration
verified identical committed/index trees and preserved all six aggregate evidence
files byte-for-byte. No push/PR/merge/issue closure. Existing Windows bridge remains
confirmed on51bac; do not relabel that milestone as8d05 qualification. An ordinary
owner, real-TTY, authentication-only WSL proof is prepared with no preparation
Apply/provider/group/network/package action, checkpoint adoption or reset. It
has not executed yet. OverallissueINCOMPLETE and all releasesUNQUALIFIED.


Actual R461-28 owned WSL authentication-only retry on frozen8d05 started at
2026-10-11T14:04:12Z after exact-source ordinary-owner staging (exit0).
The LIMITED interactive task actually ran and ended Ready/exit124 at14:07:19Z;
Linux result remained RESULT_ABSENT. The bounded sudo validation/outer WSL
limits were180/240seconds. No successful authentication or candidate session
compatibility result is established. The confirmed Windows51bac checkpoint
hash remained unchanged. Native checkpoint after-hashes were not observed;
do not infer preservation verification from absence of an Apply operation.
Exact scoped temporary-task removal was verified14:07:21Z. No preparation
Apply, checkpoint archival, source adoption, reset or provider/network action
was executed. See linux_sudo_login_session_wsl_probe_result.json.
R461-28 remains LOCAL_VERIFIED / LIVE_BLOCKED (timeout); overall issue INCOMPLETE,
all releases UNQUALIFIED. No automatic repeated launch or authentication-policy
change follows this timeout. Independent architecture review confirms BOOT-W08
supports deliberate protected old-source checkpoint archival after investigation,
then fresh planning; that continuation is reviewed but unexecuted, and the original
Incus daemon:start remains PARTIAL/effect_uncertain historical evidence.

R461-28 observed retry plan: user renewed execution instruction. Retain prior
actual timeout record; a new absent owned checkout and LIMITED task will record
Windows console visibility, Linux real-TTY and individual sudo-validation exits,
without password/input capture. Same frozen8d05 candidate and original auth
timeouts apply. No preparation Apply/archival/adoption is part of this probe.
Windows/native preservation comparisons and exact task cleanup remain required;
prepared helpers and syntax checks alone establish no live result.


The renewed observed R461-28 retry actually staged frozen8d05 and ran at
2026-10-11T14:51:42Z. Private immutable phases verify LIMITED launcher,
console-visible/foreground-request-accepted and real Linux TTY, then
SUDO_VALIDATION_PENDING. Actual SUDO_VALIDATION_EXIT124 at14:54:44Z proves
the180-second sudo-v phase timed out before the candidate runner probe.
Windows WSL exit124 is separate from conhost task exit0; the latter grants
no authentication success. Native package/Python/Incus checkpoint before/current
hashes and confirmed Windows51bac checkpoint were unchanged. Exact scoped
probe task removal was verified14:54:47Z. Existing owned VM connection window
was restored/foregrounded without input synthesis or credential capture.
Console visibility alone does not prove an unlocked active input desktop;
at that observation a separately prepared metadata-only desktop observation
was pending host UAC (later cancelled, as recorded below),
with no WSL/authentication/Apply/archive action. No further auth retry follows
this timeout. See linux_sudo_login_session_wsl_observed_probe_result.json.
R461-28 LOCAL_VERIFIED/LIVE_BLOCKED; #461 INCOMPLETE, all releases UNQUALIFIED.


The separate metadata-only desktop diagnostic did not execute: native Windows
Start-Process RunAs reported user cancellation (wrapperexit1) before starting
the elevated helper. No guest task, authentication or WSL invocation was started.
Do not infer a locked desktop from this missing observation; console-visible
metadata from the earlier observed retry remains distinct from an unlocked-input-
desktop proof. No automatic re-elevation/authentication retry follows cancellation.
See linux_sudo_login_session_desktop_observation_result.json. Actual observed
sudo validation timeout remains the current blocker; #461 INCOMPLETE/UNQUALIFIED.


The next fixture-only helper is now prepared with a point-in-time interaction
prerequisite guard: own active WTS session, readable matching Default input
desktop, and own visible console are required BEFORE any WSL/sudo invocation.
Unknown/inaccessible/inactive observations fail closed with private phase/error
records. Exact C# interop compiled and read-only host API validation passed;
Python/bash/WindowsPowerShell5.1 syntax passed and independent Security review
has no blockers. This is PREPARED_NOT_EXECUTED after Windows elevation cancellation,
not guest execution, proof of attention/lock state or live sudo compatibility.
No repeated elevation/authentication launch, preparation Apply or state adoption
occurred. Product8d05 source/fullquality remain unchanged. See
linux_sudo_login_session_observed_probe_plan.json. Current actual blocker remains
observed sudo-v timeout and unavailable desktop diagnosis; #461 INCOMPLETE.

## Three-Amigos fixes and manual guidance, 2026-10-17

R461-29/30/31 are locally verified; R461-32 documentation is statically verified.
Two actual WSL observation defects are repaired: owned dual-stack wildcard parsing
and mapped manager-root Incus process identity. The LXD guard remains intentional
and now reports its owner/preservation requirement. Full integrated project-venv
quality PASS: 2,591 tests/18 existing skips, 43 architecture tests, seven import
contracts and 801 typed files; targeted 85 PASS. All seven final product/test
hashes match the tested Linux snapshot. The first failed system-interpreter gate
and three-test virtual-environment environment diagnosis remain recorded.

A source-hashed, read-only in-memory WSL counterprobe accepts both real canonical
listeners with actual process/API proof while the original parser rejects the
same inventory; eleven measured scoped files remain unchanged. This is not
committed-source installation qualification. No target source replacement,
network Apply, restart, reset, CA import or service-authentication success follows.

Manual host/certificate/trust/recovery steps are in
`documentation/user_guide/manual-host-steps.md`, linked from README/installation/
network/troubleshooting/bridge docs. Stale ordinary-install-reset assertions were
corrected. Post-gate documentation has separate policy, diff, bash syntax and link
checks; full quality is claimed for matching product/test bytes. See
[verification record](three_amigos_verification_20261017.json) and
[Three-Amigos review](three_amigos_remediation_20261017.md).

#461 remains BLOCKED/INCOMPLETE; all releases UNQUALIFIED. Fresh installation,
complete rerun/recovery, post-install preservation, service login and native LXD
coordination remain open. Historical source-bound runs retain their original
results and were not retroactively marked successful.

## R461-34 — observed exact-plan drift during combined-source WSL preparation

Before implementation: committed candidate `4f2e1751` was verified on both
supplied existing hosts (2,469 regular archive files). WSL package/Python/Incus
checks passed. The consented network stage printed `windows:install`, then
blocked because its fresh observation differed from the approved plan. No network
effect was executed. Diagnose the differing observations with a read-only,
source-bound two-snapshot probe before any normalization; preserve ownership,
foreign state, real configuration drift and exact consent checks. Add a regression
for the observed volatile field only, obtain Three-Amigos review, run the combined
quality gate and freeze a new source if a product repair is required. Previous
candidate results remain attached to their original source.

## Combined-source qualification update — 2026-10-17, candidate d2fd89be

The user confirmed no concurrent session and authorized integration of the other
bootstrap/network/certificate worktrees. Combined candidate `4f2e1751` was
committed after independent architecture/security/commit review; the observed
WSL exact-plan drift was traced to permutation of Incus `network.used_by` only.
Regression-first repair R461-34 sorts that relation alone, preserving membership,
duplicates and every other configuration/ownership check. Final source is
`d2fd89be9b2274eeb0c210d140ebee358a1324c4`, verified clean on both targets using
real Git metadata and 2,470 archive-file hashes. An archive without `.git` was
rejected by installer preflight; it was replaced with verified real Git staging.

Final local project-venv quality: **PASS 2,631 tests, 18 existing skips, 43
architecture tests, seven import contracts, 808 typed files**. One first-run
unchanged fixture timeout was retained; the unchanged isolated test and full
rerun passed. No timeout or assertion was weakened. Manual guide syntax, links
and verification-state checks passed.

On the supplied existing native Linux target, ordinary full installation and
its exact-source rerun both exited **0**. Seven real service API positive and
negative authentication checks pass with the managed CA. Operator/TLS file
bytes, modes and inodes are preserved; all three node configurations, init
processes, guest sentinels, Docker volume identities and service IDs survive the
rerun unchanged. The separate active LXD daemon was temporarily paused and
restored with its exact original socket/service and three stopped-instance
states; no LXD instance was changed. A stale operator file was rejected with
Portainer HTTP409/422; the verified existing protected credential source was
selected, without reset, credential rotation or volume deletion. Native cold
snapshot/restore/restart of the three managed root disks passed; nine actual
TLS routes recovered after warmup. These same-pool snapshots do not prove host
OS or external-volume restoration. Default native system CA trust is absent;
explicit managed-CA verification passed.

On the supplied existing WSL target, exact-source preparation and no-action
rerun exited **0**; installer preflight and dry-run exited **0**. Seven real
service API authentication/negative checks pass. Windows CurrentUser CA
inspection reports a preexisting trusted CA with the independently verified DER
fingerprint; no CA import/removal was performed. Full WSL installation, cold
restore and selected-distribution restart are being qualified separately.

Historical failed runs retain their original source and result. No browser,
Selenium, SonarQube, fresh-OS, whole-host restore or release qualification is
inferred from these results. #461 remains **INCOMPLETE**; missing clean-host and
Ubuntu24.04 targets and remaining scenario rows prevent DONE. Machine-readable
continuation: [combined qualification](combined_qualification_20261017.json).

## Verified restart and stage-recovery continuation — 2026-10-17

Both supplied existing hosts now pass ordinary full installation and rerun on
committed candidate `d2fd89be`; TLS files, all three node configurations/markers/
volumes and service identities are preserved. Native actual host reboot and
selected-WSL distribution restart are verified with actual identity changes,
protected-file/state preservation and final nine TLS routes plus seven real API
positive/negative authentication checks. Native early inactive-daemon observation
was retained; Incus startup completed autonomously without client activation or
a service-policy change. All original unit and stopped-LXD-instance states match.
WSL init namespaces/start time changed while its kernel boot ID stayed unchanged;
Lxss and `.wslconfig` stayed unchanged. Its managed-hosts/bridge refresh and
subsequent no-action rerun both exited0. The observed WSL IPv4 did not change.

Each host also passes isolated real Python-stage offlinefailure1/interruption130
followed by connectedresume0 and unchanged-checkpoint rerun0. The first detached
sudo wrapper and WSL interruption observer race remain unsuccessful private
harness attempts; later results do not erase them. This is supplementary stage
evidence, not full CLI or full installer interruption recovery. Native managed
root recovery was executed on4f2e1751; WSL root recovery and subsequent native
installation/reboot use d2fd89be. These exact-source boundaries remain explicit.

Manual guidance now additionally covers distribution versus kernel restart
identity, capturing service/socket state before client activation, and bounded
service warmup with retained early failures. Policy, diff, eleven bash-block
syntax and relative-link checks pass for the docs-only followup; product/test
bytes remain those of the 2,631-test passing gate. Final S08 execution/audit is
pending. Fresh OS/24.04, real group-session transition, address drift and full
CLI fault cases remain open. Full #461 stays INCOMPLETE/releases UNQUALIFIED.

## Final S08 and operator handoff — 2026-10-17

Reviewed harness SHA256 `329e147a4cc57c3e6784c83639980b831ecd5d13502d13904f4211c3175d3571`
passed its mandatory privilege-drop rehearsal and actual existing-WSL port80
exposure collision (overall exit0). The unchanged d2 preflight returned2 with
`Canonical-port listener address differs from its exposure contract.` Only the
exclusive manager profile's owned80 device was temporarily removed. The fixed
root helper bound loopback80, dropped every privilege before listening, accepted
no application connection and ran no product code as root. No sysctl, filecaps,
ACL, sudoers or persistent policy was changed. Fresh UUID/ETag guards restored
exactly the original device. Restored preflight0, complete provider inventory
and checkpoint bytes/inodes/modes/mtime comparison, HTTPS200 checks, seven actual
API positive/negative checks and node config/guest markers/volumes/service IDs
all PASS. This verifies S08 exposure guard on WSL only; it does not close S07,
native collision, foreign-executable rejection or fresh-host qualification.

Exact six test-owned guest markers were removed only after hash/inode/type/
owner/mode checks. Root snapshots and private original evidence remain retained;
they are same-pool root-disk recovery points, not OS/disaster backups. Each host
has a protected `~/tsw-qualification/operator-handoff-d2fd89be.md` containing the
reviewed checkout/environment/configuration references and snapshot names,
without any secret values. Native resource/credential selections and intentional
LXD/IPv6 guards remain explicit; Windows CA trust was preexisting. Public manual
guidance includes Git metadata/three effective ignore outputs, retaining reviewed
runtime overrides, certificates/trust, restart identity and bounded warmup.
Final guide has twelve bash blocks; syntax, links, policy and diff checks PASS.

Full issue remains INCOMPLETE; missing fresh Ubuntu26.04 targets and open group, address,
resource-boundary, unrelated-resource and full CLI fault scopes remain explicit.
Independent final audit is required; no release is qualified or issue DONE claimed.

## Operator scope clarification — 2026-10-17

The operator clarified that Ubuntu24.04 is not a required live target for #461;
Ubuntu26.04 is the current LTS target for this qualification. This supersedes
the original R461-01 request to live-qualify both 24.04 and 26.04. Ubuntu24.04
remains a supported product path and is explicitly UNQUALIFIED for live use;
that status alone does not block #461. R461-01 now requires exact version
observations for native Ubuntu26.04 and Windows11 plus Ubuntu26.04 WSL2. R461-02
still requires fresh-host evidence on both families, which existing initialized
hosts do not provide. Other open scenarios and the whole-issue BLOCKED status are
unchanged.
