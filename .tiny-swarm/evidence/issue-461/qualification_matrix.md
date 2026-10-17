# BOOT-W09 qualification campaign

## Current operator-accepted scope — 2026-10-17

The operator explicitly deferred the remaining live hardening scenarios due to
test-setup limits. The amended scope is the evidenced existing-host repairs,
qualification and operator guidance. See the authoritative requirement mapping
in [the current requirement scope](requirement_matrix.md#current-operator-accepted-scope--2026-10-17).
These deferred scenarios no longer block this agreed delivery; their unverified
results and residual risks remain. Earlier whole-campaign BLOCKED/INCOMPLETE
statements below are historical and do not describe the amended scope. No
fresh-host, full fault-matrix or global release qualification is claimed.


## Source-bound results before operator deferral — 2026-10-17

Candidate `d2fd89be9b2274eeb0c210d140ebee358a1324c4`; earlier sections below
remain historical. No historical failure is overwritten by this continuation.

| Existing supplied target | Ordinary full install / rerun | Managed root-disk recovery | Authorized restart | Service proof | Release |
|---|---|---|---|---|---|
| N26-SSH-20261017 | LIVE_VERIFIED / LIVE_VERIFIED | Three cold snapshots restored, original identities preserved (candidate4f2e1751); finald2 installation/reboot separately verified | LIVE_VERIFIED: native host boot identity changed; original units and stopped LXD instances preserved after autonomous startup | Nine managed-CA TLS routes; seven actual API positive/negative checks PASS | UNQUALIFIED |
| W26-SSH-20261017 | LIVE_VERIFIED / LIVE_VERIFIED | LIVE_VERIFIED: exactd2 three cold root snapshots/restores and original identities | LIVE_VERIFIED: selected Ubuntu init recreated; shared kernel boot ID unchanged; Lxss and `.wslconfig` preserved | Nine managed-CA TLS routes; seven actual API positive/negative checks PASS | UNQUALIFIED |

Both install reruns preserve node configurations, init processes, guest markers,
Docker volume identity, service IDs and TLS bytes/inodes/modes. Both restart
cases preserve stable configuration with the four explicitly typed lifecycle
fields, guest markers, volumes and service IDs. Early inactive-daemon/502/503
samples remain retained alongside subsequent bounded readiness. WSL postrestart
managed-hosts/bridge refresh exited0, followed by an actual no-action rerun0.
The WSL IPv4 address did not change: S07 remains open.

S09/S10 supplementary evidence: on each host, the unchanged real dependency
stage failed offline (exit1) or was interrupted during observed hash-locked Pip
(exit130), retained partial state, then resumed connected (exit0) and reran with
no checkpoint change (exit0). Scope is Python-stage integration, not full CLI
or fresh-host qualification. Failed harness attempts are retained separately.
S08 WSL exposure collision is now LIVE_VERIFIED: expected preflight exit2, exact guarded restoration, restored preflight0, unchanged provider/checkpoints and actual postrestore API/data checks.

Clean OS and Ubuntu24.04 targets remain unavailable. No new-target reset, whole
OS/external-volume restoration, browser/Selenium or SonarQube success is claimed.
Full issue status: INCOMPLETE; every release stays UNQUALIFIED. Current redacted
results and hashes: [combined qualification](combined_qualification_20261017.json).


Latest distinct-target continuation (2026-10-17 Europe/Berlin):
[ssh_qualification_20261017.json](ssh_qualification_20261017.json), exact committed
candidate `8d05d690aced18c07162162bc86106d2ac85b8a5` on both targets.

| Target | Observed versions | Preparation | Fresh / rerun / recovery |
|---|---|---|---|
| N26-SSH-20261017 | Ubuntu 26.04.1, kernel 7.0.0-38-generic, x86_64, systemd, Python 3.14.4, Incus 6.0.5 | BLOCKED: active LXD; existing LXD/Incus instances preserved | BLOCKED / BLOCKED / BLOCKED; UNQUALIFIED |
| W26-SSH-20261017 | Windows 11 Pro 10.0.26200.9711, PowerShell 5.1.26100.9711, WSL 3.0.3.0, Ubuntu 26.04.1, kernel 6.18.54.1-microsoft-standard-WSL2, x86_64, systemd, Python 3.14.4 | PARTIAL: Python prepared, Incus READY, network exposure mismatch | BLOCKED / BLOCKED / BLOCKED; UNQUALIFIED |

These hosts have existing installations and no clean-OS proof. Installation and
restarts are explicitly authorized; restoration availability is operator-asserted,
not independently tested in this continuation. No reset authorization exists.
The Windows version differs from the historical owned VM: do not merge target
identities or transplant that VM's recovery/reset proof. Earlier status below is
historical; no full installation or restart was run in this continuation.

Status: **BLOCKED**. Live qualification state: **LIVE_PREREQUISITE_MISSING**
for authorized native tests and the new Windows test environment. Explicit
destructive Ubuntu reset is now authorized only inside the owned secured VM. Scoped reset and restore executed and verified; full scenario qualification remains open.
Current corrected candidate: `51bac77cd94e210a3b8640f4e83688180e520057` (listener identity and batched firewall observations; affected live rerun pending). Earlier metadata-only candidate: `806a58c36aabf8a95601f2bbfb2978e2d6ee2995`. Historical native/feature runs used `3da77f8908d598688ed46dd6eab74c5f32a7ac50` (integrated W07/W08 plus urllib3 security repair).
Use the hash-verified release archive of this committed candidate for runtime
runs; later product fixes require
a new committed candidate, applicability assessment and affected reruns.

## Release matrix

| Target ID | Eligible release / architecture | Exact versions observed | Fresh | Rerun | Recovery | Release qualification |
|---|---|---|---|---|---|---|
| N24 | Native Ubuntu 24.04 LTS / x86_64 | Not supplied | BLOCKED | BLOCKED | BLOCKED | UNQUALIFIED |
| N26 | Native Ubuntu 26.04 LTS / x86_64 | Ubuntu 26.04.1, kernel 7.0.0-34-generic, systemd; SSH inspection exit 0 | BLOCKED | BLOCKED | BLOCKED | UNQUALIFIED |
| W24 | Windows 11 + Ubuntu 24.04 LTS / x86_64 / WSL2 | Windows edition/build, WSL version, distro release/kernel not supplied | BLOCKED | BLOCKED | BLOCKED | UNQUALIFIED |
| W26-local | Preserved local Windows 11 + Ubuntu 26.04 / x86_64 / WSL2 | Windows 11 Pro 26300.9550, WSL 2.7.10.0, Ubuntu 26.04.1, kernel 6.18.33.2-microsoft-standard-WSL2, systemd | BLOCKED | BLOCKED | BLOCKED | UNQUALIFIED |
| W26-owned | Owned Hyper-V Windows 11 + Ubuntu 26.04 / x86_64 / WSL2 | Windows 11 Enterprise Evaluation 26H2/26300.9457, WSL 3.0.1.0, manual Ubuntu 26.04.1, kernel 6.18.40.1-microsoft-standard-WSL2, systemd | PARTIAL prerequisites; product apply BLOCKED | BLOCKED | PARTIAL guest reboot/writer; full recovery BLOCKED | UNQUALIFIED |

Eligibility follows the bootstrap contract; it is not a qualified-release claim.
Windows 10, WSL1, other distributions/releases, ARM and macOS are outside the
initial bootstrap support scope. No Windows or WSL version is invented.
Record OS patch release, kernel, CPU architecture, systemd, Python, Incus,
Docker, PowerShell (Windows), Windows build and WSL package version per run.
Inspect actual distro release and WSL generation, not just registration name.

The operator identified local WSL and a native SSH target on 2026-10-10.
Initial read-only access supplied the N26/W26-local facts; later owned guest observations are separately recorded. Windows inventory confirms
the selected local distro runs with generation 2 and another distribution is
stopped; neither was started, stopped or modified. Native Incus/Docker
executables exist; their runtime health and versions remain unverified. No
24.04 target or clean snapshot/restore reference is supplied. Access credentials
are excluded. Target identification and read access do not establish
recoverability or authorize reset/fault/restart.

## Required scenarios for each applicable target

Required installation/recovery rows remain BLOCKED. Native preparation/S13
observations are PARTIAL. Authorized native and new
Windows guest scenarios lack prerequisites; explicit reset lacks consent.
N26-existing-preflight-20261010 records S13 partial preservation evidence (exit 2);
no installation or recovery is qualified.
Run IDs and evidence links must be added only after actual execution.

| ID | Scenario | Required observation / pass criterion | Applicability |
|---|---|---|---|
| S01 | Clean host preparation and installation | Proven clean OS or verified pre-install snapshot; ordered preparation/apply/install exits and authenticated readiness | All four |
| S02 | Repeat preparation and installation | Observe before/after managed identities, data/configuration/credential continuity and no unintended mutation | All four |
| S03 | Unrelated resource preservation | Pre/post unrelated Incus identities, storage/network/configuration and unrelated WSL distributions/listeners unchanged | Incus on all; WSL on W24/W26 |
| S04 | Resource boundaries | Record resolved service selection/#440/#444 capacity semantics, floor/insufficient/adequate cases, bounded refusal and effective limits | All four |
| S05 | Reboot or selected distro restart | Restorable target; observed boot/PID1 transition, readiness deadline, persisted data and authenticated routes; unrelated WSL remains preserved | Native reboot on N24/N26; WSL restart on W24/W26 |
| S06 | Group refresh | New membership blocks stale session; operator login/session refresh and reinventory enables only authorized stage | All four |
| S07 | Address drift | Observed changed address and canonical bridge/routing convergence, authenticated route checks | Relevant native routing and WSL bridge |
| S08 | Port collision | Controlled disposable listener; safe bounded failure, unrelated listener retained, explicit correction then new-plan recovery | All four |
| S09 | Unavailable download | Controlled unavailable pinned source; finite timeout/exit, redacted failed stage, preservation and separately consented retry | All four; Windows lifecycle sources on W24/W26 |
| S10 | Interruption and recovery | Authorized interruptions around APT/configuration/Incus/bridge; Windows feature/restart boundaries where applicable; observe checkpoint and actual state before fresh consent, no unsafe replay | All four |
| S11 | Service routes and authentication | Resolved installed-service inventory; meaningful authenticated acceptance for every selected service, wrong/absent credentials rejected, TLS verification retained | All four |
| S12 | Explicit reset isolation | Separate destructive reset authorization, exact confirmation and owned scope; prove unrelated distro/resources retained | W24/W26 |
| S13 | Read-only and consent boundaries | Compare host/configuration/state/evidence before/after preflight/dry-run; no writes; no apply without current target/source/plan consent | All four |

Restart/fault/reset operations require their own authorized recoverable scope.
Serialize target mutations. Keep group-refresh/restart boundaries observable;
never execute a printed next command as implicit consent. Select concrete bounded
timeouts and fault points from the current stage plan before approval.

## Run record and evidence acceptance

Parent requirement coverage: BOOT-01 -> S13; BOOT-02 -> S01/S05/S10;
BOOT-03 -> S02/S04; BOOT-04 -> S01/S09/S10;
BOOT-05 -> S01/S02/S03/S06/S10; BOOT-06 -> S05/S07/S08/S11;
BOOT-07 -> S01/S02/S12; BOOT-08 -> S02/S09/S10;
BOOT-09 -> the entire release/scenario qualification matrix. These are coverage
mappings, not verified requirement claims.

Before execution record target alias, consent reference, snapshot/restore
reference, source SHA/cleanliness, exact observed versions, selected services,
resolved resource limits and current approved plan. Use Linux-native checkout,
runtime and evidence storage for WSL. Windows preparation runs only through the
documented explicit candidate qualification mechanism; ordinary Apply remains
guarded. See [Windows preparation](../../../documentation/user_guide/windows-preparation.md).

Record actual command and arguments with secrets redacted, UTC start/end,
exit code (including failed attempts), mutation boundary, before/after invariants,
policy state, AC mapping, restoration result and redacted evidence paths/checksums.
Never insert planned commands or absent exit codes as executed evidence.
Use the existing [run template](../../../documentation/evidence/live-run-template.md)
and [redaction rules](../../../documentation/evidence/redaction-rules.md).
Keep raw credentials, IP/user paths and logs private; publish reviewed summaries.

PASS requires LIVE_VERIFIED with all scenario assertions evidenced; PARTIAL
requires explicit unfinished assertions and their policy states; BLOCKED records
missing consent/prerequisites or guarded refusal. Failed/degraded runs retain
LIVE_FAILED_AFTER_MUTATION/LIVE_DEGRADED and actual exits, never become PASS.
No release target becomes qualified while its required scenarios remain open.

## Historical evidence applicability

[#363 final validation](../../../documentation/evidence/issue-363-final-validation-20261003.md)
records earlier `89357c4a` applicability and executed fresh managed-state runs
at `1bd3dafd`/`bdd73f58`. It explicitly excludes factory-clean OS qualification.
The candidate now includes preparation, handoff and recovery changes from W07/W08.
No reviewed source equivalence to those historical runs has been established.
Retain #363 as historical lifecycle/authentication/restart context; it supplies
no W09 fresh-host, rerun, reset or recovery PASS. #427 is retained for its original
scope; W09 covers new bootstrap stages without relabeling its historical results.

## Gate classification

Local regression/quality/security contracts: APPLICABLE_LOCAL. Installation,
Windows preparation, restart, networking, reset, fault recovery and authenticated
browser/service checks: APPLICABLE_LIVE / LIVE_PREREQUISITE_MISSING for authorized tests; destructive
reset is LIVE_CONSENT_MISSING. External
SonarQube/CI results: EXTERNAL_GATE_UNAVAILABLE for this unsubmitted branch;
historical predecessor checks are not current-candidate results.

The initial dependency security gate failed for the baseline runtime lock.
The corrected lock now passes strict audit and full Python 3.12 quality.
See test_results.md for both actual results; the committed candidate is frozen, and live prerequisites still block overall qualification.

## Operator-authorized environment preparation

The operator subsequently authorized tests directly on the supplied native host
and creation of an isolated Windows Hyper-V environment. Native inventory shows
three running managed containers, Incus 6.0.5, Docker 29.1.3, ext4 root storage,
physical-host classification and no managed-container snapshots. This target
can supply existing-installation observations; its current state cannot supply
fresh-OS evidence or prove fault/recovery safety.

An elevated Hyper-V inventory succeeded. A dedicated owned Generation-2 VM
was created off with nested virtualization, vTPM and Secure Boot, using only the
existing Default Switch. Its empty disk was expanded to 256 GiB and CPUs to 12
after checking the default node/WSL budget. After the operator stopped the firmware-only VM, its owned disk was verified
RAW again. Guest RAM is now 32 GiB; host free RAM was 35.38 GiB at the check.
No unrelated VM, WSL distribution, host switch or adapter was changed.

The official [Windows 11 Enterprise Evaluation download](https://www.microsoft.com/en-us/evalcenter/download-windows-11-enterprise)
download completed (curl exit 0). Installation verifies EN-US 26H2 SHA-256
`BC3F24086EBADC94489066B5AD78089E2CF5C3491E90E790BB81A2B199C10E38`
from Microsoft VerifyWindowsISO and the setup signature. Planned guest image
application was restricted to the owned RAW VHD and completed for image/boot
files (exits 0/0). The initial RAM refusal is historical; current progress follows.
The VM shell is created; Windows, WSL, Incus, installation, routes and login are
not qualified. A clean pre-WSL checkpoint was subsequently observed and actually restored
after successful Windows boot and verified removal of answer-file credentials. All raw VM files,
DPAPI-protected credentials and provisioning logs stay in ignored local storage.

Native preflight result: [portable redacted record](native_preflight_result.json).
Initial Windows image/boot files applied (exits 0/0), then the 32-GiB boot was
refused at 33.6 GiB free host RAM. Later 24-GiB OS boot/checkpoint recovery and
32-GiB configuration results appear below; retain the initial refusal.

## Owned Windows guest executed progress

Separate from the preserved local Windows/WSL environment, the new guest is
Windows 11 Enterprise Evaluation 26H2, exact build 26300.9457, PowerShell
5.1.26100.9444; WSL/distro was absent at that historical pre-WSL stage. OS-only boot used 24 GiB/26-GiB
free-host guard. Credential answer files were verified removed. Initial
checkpoint ACL failure and immediate identity-check failure remain recorded;
a later bound-VM inventory and actual restore verified the owned clean pre-WSL
checkpoint. Candidate archive/source proof was verified at frozen SHA3da77.
The read-only candidate dry-run exited 2 planning enable_features and preserved
its measured .wslconfig/hosts/registration invariants. This is partial S13,
not complete no-write/preservation qualification. Windows checkpoint recovery
is an environment prerequisite, not bootstrap/WSL recovery PASS.

The guest is configured at 32 GiB while off; host free RAM was 34.86 GiB before
the restoration test. Feature-only preparation will independently enforce
34 GiB before its full guest boot. No release or complete WSL capacity is
qualified by these observations.

## Current continuation after checkpoint persistence finding

Original frozen candidate3da77 verified enable_features but returned PARTIAL/4 after effect-state replacement failure. Owned guest recovery reboot was verified; source-bound post-restart preflight requested install_wsl. The operator subsequently manually installed WSL3.0.1.0 and Ubuntu26.04.1LTS, default registration Ubuntu/WSL2/running/systemd/x86_64. This establishes observed manual prerequisites, not candidate-executed package/distro installation. Actual WSL MemTotal16377308kB and12processors still need the selected21GiB/8CPU budget. Preserve the operator installation. Corrected atomic checkpoint persistence passes actual WindowsPowerShell5.1 filesystem regression and full Python3.12 quality retry; bce63aaf is committed and source-verified in the owned guest, and its actual protected disposable writer passes. Corrected full product apply is blocked by the storage trust finding. Every release remains UNQUALIFIED.

Corrected archiveSHA48326e2e486f4fb1c34287dc274a445b7438782a4b0d27de1616b2afa01dcb18 includes a clean committed-source membership proof. Owned-guest read-only plan verifies bce63aaf and exits2 on resource_inventory_unknown/bootstrap_state_invalid. Protected disposable checkpoint writer passes actual create/replace with real ACL guards; canonical old checkpoint/config unchanged. The selected VHD ACL refusal is a resource trust-policy finding, not capacity or service success. No revised product apply, state archive, configuration adaptation, distro restart or VM snapshot restore occurred after the manual install.

2026-10-11 continuation: new operator-Ubuntu checkpoint 419a8422 was restored
and exact registration/configuration/old state/marker were verified. This preserves
manual Ubuntu. The new source806 resource diagnostic observes storage/effective
facts (16-GiB current WSL memory/12CPU/4GiBswap), while product dry-run observes
stopped distro before an explicit operator diagnostic start. Do not call this
full no-start/no-write product qualification. Fresh source-bound resource stage
remains in progress. Native26 own Hyper-V guest provisioned OFF from signed Ubuntu
cloud image; native24 signed image downloaded/converted. Neither is qualified.

Current N26-existing sourceef7 supplemental results: owned Python prepare and
zero-Python-change rerun PARTIAL(exit2 preservedIPv6); install preflight/dry-run
PASS(exit0), read-only9-scope/3-node preservation PASS. Actual full install,
freshness, reboot/fault recovery and post-candidate authentication remain OPEN.
This existing physical host is not a clean disposable baseline. Windows32
fixture restart currently BLOCKED on host commit headroom, despite sufficient
physical free RAM. NativeHyperV26 failed recovery boot is retained as environment
evidence; it does not qualify native26 product execution.

Windows fixture allocation update: operator-requested fixed 26 GiB was applied
and actual Hyper-V start succeeded. This verifies fixture resize/start only;
standard profile capacity and issue qualification remain unverified at 26 GiB.

## Current operator-requested Windows allocation: 28 GiB

The subsequent explicit operator request supersedes the 26-GiB allocation:
owned Windows VM was gracefully shut down, resized to fixed 28 GiB, and actually
started successfully. Physical headroom was 38.583 GiB and commit headroom
28.848 GiB before successful Hyper-V allocation. An initial conservative
30-GiB start check did not attempt startup; actual allocation was subsequently
attempted with measured headroom exceeding 28 GiB, with Hyper-V enforcing
hypervisor overhead. No host pagefile or product capacity policy was changed.
See windows28_resize_start_result.json. This verifies fixture resize/start,
not successful product preflight or full issue qualification. Earlier 26-GiB
insufficient-capacity and Windows32/Off observations are historical.

Actual sourceef7 at28: Preflight and DryRun exit2 with
insufficient_host_capacity and bootstrap_state_invalid; protected fingerprints
unchanged. Windows deficit1159168bytes against exact21+7GiB requirement.
The subsequent current recovery-point helper was not launched: Windows
elevation was canceled. No current28 checkpoint was created or restored and
no Ubuntu unregister/reset executed by that helper. Last verified VM state
Running28; original verified operator checkpoint remains retained. User
interactive Windows availability is requested before another elevation attempt.
See windows_recovery_elevation_result.json.

## Explicit operator-requested 30-GiB retry

Operator explicitly requested30GiB and retry. Exact owned VM was gracefully
stopped, resized to fixed30GiB and actually started. Observed pre-start physical
headroom41.078GiB and commit headroom35.187GiB exceeded30GiB. No host pagefile
policy or product resource threshold was changed. Source-bound candidate
preflight/dry-run is pending; this resize/start alone is not qualification.
See windows30_resize_start_result.json. Prior28GiB observations are historical.

Sourceef7 actual30GiB retry: resource_state VERIFIED and
effective_verified=true in both Preflight and DryRun. Observed Windows
32211095552bytes; WSL physical22547132416/usable22033051648bytes,8CPU,
swap6442450944bytes, storage known. Overall both exit2 on
bridge_inventory_unavailable and bootstrap_state_invalid. Protected config,
registrations, hosts and prior-source canonical state remain unchanged.
Capacity blocker is resolved for this observed30GiB fixture, not for earlier
28GiB. No full installation qualification is claimed. See
windows_ef7_30gib_preflight_result.json.

Current30 snapshot actual restore PASS before destructive testing. Exact
checkpoint eaff8dec-c016-421c-b235-5952d6c7c0a4 restored and selected Ubuntu
registration, machine-id/release hashes, WSL configuration, canonical state
and owned marker matched. Separately authorized VM-only Ubuntu terminate and
unregister both exit0; actual empty guest registration inventory observed.
Exact checkpoint was then restored again: measured identity/config/state
hashes matched; primary host WSL registrations/config fingerprints unchanged.
Reset/recovery isolation PASS for the recorded scope, not every Ubuntu file
and not product installation qualification. Original recovery points retained.
See windows30_current_recovery_result.json and
windows30_ubuntu_reset_recovery_result.json.

## Current source-bound Windows 30GiB follow-up

Frozen source e01e1dd5dab2ff7390d782d891a47e2191c1c7a9, clean checkout
and release-manifest verified archive SHA256
36b5c0973db4e9e3c94df85166d6dcde3c7c03496b607b93cc53413a24d9e7fd.
Actual Windows preflight/dry-run: resource VERIFIED/effective_verified true;
bridge inventory completes at unchanged defaults and plans bridge_install.
Protected state fingerprints unchanged. Initial exit2 blockers were
prerequisite_missing and prior-source bootstrap_state_invalid.

The exact confirmed source806 resource checkpoint was then archived under the
canonical product lock, after matching revision/distro/host, confirmed effect,
current config hash and actual verified current30 recovery/reset proof.
Same-volume move preserved bytes and ACLs; old canonical state is absent;
archival ledger recorded. No prior consent reused. Fresh source-bound plan
exit2 only prerequisite_missing, bridge_install planned. Apply not executed.
See windows_e01_30gib_preflight_result.json and
windows30_resource_state_archive_result.json. Historical bridge timeouts and
old-source state failures remain recorded; they are resolved for this measured
plan only. R461-25 live inventory case verified. Full install, rerun, service
authentication and ordinary full-apply WSL preservation remain unverified.
Issue remains INCOMPLETE; every release remains UNQUALIFIED.

## Actual e01 bridge Apply interruption and logon failure

At10:12:45Z actual task Running, canonical checkpoint pending/uncertain for
bridge_install/currente01, not confirmed. Operator reported no new dialog.
At10:15:35Z task Ready with status0xC000013A; no owned installation processes
and no bridge service. Product Apply envelope/exit were not returned; do not
treat the task status as a product exit. Interruption origin is unknown.
Independent source-bound preflight/dry-run exit2, resourceVERIFIED, no actions
and bridge_recovery_or_adoption_required. Canonical uncertainty retained.

Actual protected payload/journal observation10:18:54Z: activated transaction,
serviceCreateIntent/serviceCreatedtrue; original service/root absent. WinSW
wrapper matches pinned SHA256. SCM7045 records service creation, followed by
SCM7000/7038 at10:14:08Z with explicit incorrect username/password failure.
No successful service start/readiness/authentication is claimed. User
confirmation and a passed credential dialog cannot substitute for service logon
success. Existing host-protected credential still authenticates PSDirect, but
no password/token is printed or committed. All9partial payload files and
canonical uncertain state preserved privately with hash checks.
See windows30_interactive_bridge_interrupted_result.json and
windows30_interrupted_bridge_payload_result.json. This supplies actual partial
interruption/refusal evidence, not controlled fault-injection or recovery PASS.
Whole-owned-VM snapshot recovery prepared with inactive-task/child checks,
preserved failure snapshot and original actually verified recovery reference;
recovery execution/result must be observed separately. Product guards are not
bypassed and uncertain checkpoint is not edited. #461 remains INCOMPLETE.

## Actual interrupted-bridge whole-VM recovery verified

Corrected host UAC retry completed. At10:28:51Z actual whole-owned-VM snapshot
restore verified against original eaff recovery identity/configuration/marker
and Ubuntu machine-id/os-release hashes. Fixed30GiB retained. Bridge root,
service and interactive test task absent. Primary WSL registration/config
fingerprints unchanged. Failed offline snapshot retained as
5cce7e45-fd8d-4ba2-b458-41d42ef54500; partial payload and uncertainty evidence
also hash-preserved privately. Uncertain checkpoint was not edited.
See windows30_interrupted_bridge_snapshot_recovery_result.json.
This is environment snapshot recovery PASS for recorded scope; it is not
product bridge transaction recovery, successful credential/service start,
full install or S10 controlled fault-injection qualification.
Next source-bound plan/preparation is being reobserved after recovery.


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


Corrected candidate51bac77c actual source-bound preflight/dry-run completed at
12:39:59Z with protected fingerprints unchanged and resource verification true.
The restored original CONFIRMED806 resource checkpoint alone was archived under
lock with unchanged bytes/ACLs; fresh plan contains only bridge_install and
prerequisite_missing. Actual12:40:37Z guest query reports no interactive user.
The guarded starter refuses before guest credential export or task registration;
no corrected Apply has started. Operator login as the owned tswtest account in
the test VM is required; no autologon or dialog bypass is introduced.


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
inferred from these results. #461 remains **INCOMPLETE**; missing clean-host
targets and remaining scenario rows prevent DONE. Machine-readable
continuation: [combined qualification](combined_qualification_20261017.json).

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

Ubuntu24.04 is not a required live target for #461; the operator selected
Ubuntu26.04 as the current LTS qualification target. The original dual-release
target expectation is superseded. Ubuntu24.04 remains supported but explicitly
UNQUALIFIED for live use. Both supplied targets are Ubuntu26.04, but are existing
initialized hosts, so fresh-host coverage for native and WSL2 remains BLOCKED.
