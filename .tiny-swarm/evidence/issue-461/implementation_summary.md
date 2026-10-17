# Implementation summary

## Current operator-accepted scope — 2026-10-17

The operator explicitly deferred the remaining live hardening scenarios due to
test-setup limits. The amended scope is the evidenced existing-host repairs,
qualification and operator guidance. See the authoritative requirement mapping
in [the current requirement scope](requirement_matrix.md#current-operator-accepted-scope--2026-10-17).
These deferred scenarios no longer block this agreed delivery; their unverified
results and residual risks remain. Earlier whole-campaign BLOCKED/INCOMPLETE
statements below are historical and do not describe the amended scope. No
fresh-host, full fault-matrix or global release qualification is claimed.


Issue status: INCOMPLETE. Current51bac bridge installation is confirmed,
with independent default15-second inventories showing agent/routing/bridge ready.
Actual product Apply exit4/PARTIAL completed bridge_install and requires the next
stage. Later checkout staging is verified inside owned WSL ext4. Handoff
DryRun exits0/LINUX_PREPARATION_REQUIRED; its preceding Preflight hits an
intermittent15-second timeout. Independent inspection now verifies packages and
Python succeeded, but Incus daemon:start is PARTIAL with an uncertain action;
installer checks fail on unavailable bridge/forwarding controls. Later Windows
Preflight/DryRun both exit 0. The retry confirms inactive Incus and daemon:start
as the next plan. R461-28 repairs session-sensitive sudo authorization, with full
quality PASS; Linux source is frozen as8d05d690. Its actual authentication-only WSL
initial retry timed out (task exit124/no Linux result). A later observed retry
locates the timeout specifically at sudo-v (exit124), before runner execution;
Windows/native state comparisons and scoped task cleanup are verified.
Live sudo compatibility and preparation Apply remain unverified. The later
metadata-only desktop observation did not start: Windows elevation was cancelled.
No services or release qualification claimed. Historical e01 failure was preserved and environment
restoration verified before this rerun. Temporary credential deletion verified.
Current frozen Windows bridge candidate:
`51bac77cd94e210a3b8640f4e83688180e520057`; listener identity and batched
policy observation locally and live-bridge verified. Aggregate release qualification
remains incomplete. Current frozen Linux sudo-session candidate is
`8d05d690aced18c07162162bc86106d2ac85b8a5`. RAM accounting
was locally and live-resource verified on earlier e01. Current Windows allocation is30GiB.
Earlier hosts-observation correction was live verified: resource assessment VERIFIED,
bridge inventory returns and plans bridge_install. The preceding pre-install fresh dry-run exited2
only prerequisite_missing; confirmed prior-source state was archived under lock
with identical bytes and ACLs. The first actual bridge Apply was interrupted after service creation/logon failure;
at that historical observation service was absent, checkpoint uncertain and replay refused. Whole-VM recorded-scope recovery is verified; see latest test_results.md evidence.
Current30 backup actual restore and separately authorized VM-only Ubuntu
reset/recovery were executed and verified for recorded identity/hash scopes;
primary WSL registration/config fingerprints remained unchanged.
Previous metadata candidate: `806a58c36aabf8a95601f2bbfb2978e2d6ee2995`.
Historical corrected checkpoint candidate: `bce63aafb6990e9157c8ddb3eb12e4aa9fd1f440`. Historical native/feature candidate:
`3da77f8908d598688ed46dd6eab74c5f32a7ac50`, based on integrated #459/#460.
The narrow urllib3 lock correction passes strict audit and full Python 3.12
quality. A live checkpoint persistence defect is implemented, verified and frozen in the existing Windows adapter; product Python is unchanged. The existing completed #355
workflow was not executed or replaced. Branch:
fix/boot-w09-live-qualification-20261010.

Authorized native existing-host tests prepared an owned Python venv and isolated
checkpoint state, preserving eight/nine measured existing file scopes and three
running nodes. Network preparation blocked on existing IPv6-enabled bridges.
Native fresh-host and recoverable fault-test prerequisites remain missing.

## Historical Windows qualification timeline

The authorized isolated Hyper-V Windows environment boots Windows 11
Enterprise Evaluation 26H2 build 26300.9457. Windows OS-only provisioning used
24 GiB; answer credentials were removed and verified absent. A scoped owned-VM
storage ACL repair preserved the private parent ACL. Its clean pre-WSL checkpoint
was subsequently restored and booted with matching version, absent candidate
marker, no WSL and VirtualMachinePlatform Disabled. This verifies environment
recovery only. The guest stopped normally and 32-GiB RAM was set and observed.

Source-bound guest dry-run verified the frozen SHA and exited 2 with only
Windows feature prerequisites pending; measured configuration/registration
invariants were unchanged (partial S13). The prepared full 32-GiB feature-only
phase retains the 34-GiB free-host guard. The first UAC launch was canceled
(host exit 1). The authorized retry passed that guard at 34.676 GiB, booted
the full guest, and confirmed enable_features. Apply returned exit 4 PARTIAL
because effect checkpoint persistence failed. Independent inventory and saved
effect evidence confirmed both features Enabled and a pending Windows reboot.
A separate owned-guest recovery restart verified the boot transition and exact
source; post-restart dry-run exits 2 with only install_wsl pending.

A protected disposable-directory reproduction preserves the canonical pending
checkpoint and identifies PowerShell null argument conversion at File.Replace.
The narrow NullString correction preserves atomic replacement and all ACL/state
guards. A new real-filesystem regression passes under Windows PowerShell 5.1.
The revised candidate passes the full Python 3.12 quality retry and the Windows
PowerShell 5.1 filesystem regression. Corrected source is now locally frozen at bce63aaf; source-bound read-only
plan and actual protected disposable checkpoint writer verification pass.
Corrected product apply remains unexecuted. The original failed gate remains recorded.

The operator then manually installed WSL/Ubuntu in the owned VM. Read-only
inspection confirms WSL 3.0.1.0 and running Ubuntu 26.04.1 LTS/x86_64/systemd.
Its approximately 16-GiB WSL memory and 12 processors still need the selected
21-GiB/8-processor allocation. Preserve this operator-created registration;
manual prerequisites do not count as candidate-executed install qualification.

All releases remain UNQUALIFIED. AC1/AC2 and the required product install,
rerun, recovery, preservation/reset and authentication scenarios remain open.
Separate destructive WSL reset authorization was absent at this historical stage;
the later explicit scoped authorization and verified recovery point are recorded below. No issue close,
push, PR or merge is implied by the local verification/environment progress.

Current revised plan exits 2 with resource_inventory_unknown and
bootstrap_state_invalid, no actions. The old identity-bound pending checkpoint
is retained. Resource diagnosis identifies untrusted_evidence_acl on the selected
WSL VHD: observed extra FullControl grants are categorized from SID families as
VirtualMachineInstance and AppCapability. The selected registration directory
has only current-user/SYSTEM/Administrators grants. Resource trust compatibility
needs a reviewed security/architecture decision; no permission rule, ACL, WSL
configuration, distribution or old state identity was changed to bypass it.

## Authorized VHD metadata correction continuation

Actual WSL-managed VHD access grants triggered the evidence-file ACL guard despite
resource inventory only observing presence/type and capacity on BasePath. Independent
System Architect and Completion Auditor accepted a VHD-specific metadata helper:
local NTFS, strict BasePath/ancestor permissions, regular non-reparse file and trusted
owner remain required. No VHD content IO, permission mutation or SID whitelist.
Evidence/configuration/swap ACL guards remain strict. Existing capacity ADR gains a
dated amendment and operator guide clarifies this role. Actual Windows PowerShell5.1
fixture PASS30; modern portable7.6.6 metadata-only fixture PASS10. The full gate is
pending at this writing; no corrected live source qualification is yet claimed.

New checkpoint preserves operator-created Ubuntu; actual restore verification is
pending. User separately authorizes reset exclusively inside this recovered test VM.

R461-23 final local gate PASS; independently reviewed correction is ready for
new committed source freeze. Actual live resource verification remains pending.

## Current resource and secured recovery evidence

Source806 passes full quality and actual source-bound resource apply: exit3
RESTART_REQUIRED, confirmed durable checkpoint, no uncertain actions, selected
21GiB/8CPU/6GiB swap config. New operator-created Ubuntu checkpoint419a8422
was actually restored and verified before the separately authorized VM-only reset.
The original old-source checkpoint was archived under the canonical lock with
bytes/hash/ACL preserved, not edited or implicitly reused. One private operator
helper supplied an unsupported -Apply switch and failed before configuration
mutation; the corrected default-apply helper recorded the actual result.

An actual owned WSL shutdown/start confirms8CPU and6GiB swap, but the old RAM
comparison refuses kernel reservations. Read-only present-page observation
separates22547132416 physical bytes from22033063936 usable bytes. Independent
architecture/security review approves R461-24 measurement correction with
unchanged tolerance and independent MemTotal/cgroup floor. New exact source/live
verification remains required. No release is qualified.

Fresh isolated Ubuntu24/26 native-kernel Hyper-V test guests were provisioned
from Canonical SHA/signature-verified cloud images, fixed32GiB/12CPU/256GiB.
This is a virtualized native Linux test environment; product provider remains
Incus. Guest boot, fresh preparation/install and recovery evidence remain pending.

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

Earlier pending VHD correction, pending operator checkpoint restore, and
unarchived old checkpoint statements above are historical: source806 correction
and resource apply, actual operator checkpoint restore, and lock-protected
archival are recorded in the later secured recovery section. Sourceef7 local
quality passed; overall issue remains INCOMPLETE pending remaining live cases.

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


Latest e01 PARTIAL attempt whole-owned-VM recovery actually verified at
2026-10-11T12:39:11Z after one transient graceful state-transition failure and
one classified retry. Exact uncertain checkpoint was read/hash-verified,
preserved by a new unique offline whole-VM snapshot, and never rewritten.
Restored eaff reference matches recorded Windows/Ubuntu/configuration/marker
identity; bridge service/root absent; primary host WSL fingerprints unchanged.
This proves environment recovery, not product bridge recovery or installation.
Corrected source transfer/preflight/Apply continue separately.


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
file bytes match. At that observation source-freeze review was pending; the
accepted freeze is recorded below. Owned WSL candidate execution,
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
# SSH continuation, 2026-10-17 Europe/Berlin

Latest record: [ssh_qualification_20261017.json](ssh_qualification_20261017.json).
Operator-authorized installation/restart targets were inventoried without
publishing addresses, logins or passwords. Both staged archives match all 2,459
regular committed files from `8d05d690`. The two confirmed source-mismatched
checkpoints were archived under lock with bytes/inodes/ownership/modes preserved.
Native preparation then refused the active LXD service (three stopped LXD and
three running Incus instances observed). WSL authenticated sudo, prepared the
local Python environment and verified Incus, then returned 2 before network
Apply because configured IPv4-wildcard proxies appear as IPv6-wildcard listeners.
No product code, service stop, installation, reboot, reset or recovery run.
Issue BLOCKED; releases UNQUALIFIED. Earlier sections are historical.

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

Ubuntu24.04 is not a required live target for #461; Ubuntu26.04 is the current
LTS qualification target. This supersedes the original dual-release live-target
expectation. Ubuntu24.04 remains supported but explicitly UNQUALIFIED for live
use; that status alone does not block #461. Both supplied Ubuntu26.04 hosts are
already initialized, so fresh-host evidence on both host families remains open.
