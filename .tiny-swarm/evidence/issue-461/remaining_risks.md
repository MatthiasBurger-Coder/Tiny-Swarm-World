# Remaining risks and blockers

## Current operator-accepted scope — 2026-10-17

The operator explicitly deferred the remaining live hardening scenarios due to
test-setup limits. The amended scope is the evidenced existing-host repairs,
qualification and operator guidance. See the authoritative requirement mapping
in [the current requirement scope](requirement_matrix.md#current-operator-accepted-scope--2026-10-17).
These deferred scenarios no longer block this agreed delivery; their unverified
results and residual risks remain. Earlier whole-campaign BLOCKED/INCOMPLETE
statements below are historical and do not describe the amended scope. No
fresh-host, full fault-matrix or global release qualification is claimed.


- Native tests and the isolated Windows VM are authorized. The native supplied
  host is an existing installation without a clean OS snapshot/restore proof;
  it cannot establish fresh-host or safe injected-failure recovery results.
- Native Python preparation succeeded in the owned source, preserving existing
  protected scopes and three nodes. Network preparation refused the existing
  IPv6-enabled bridge policy. Preserve that policy; installation needs a
  compatible separately recoverable target.
- Isolated native Ubuntu24/26 fixtures exist, but remain unqualified; Ubuntu26 recovery boot failed and Ubuntu24 has not booted. The isolated Windows guest now has
  observed Windows 11 Enterprise Evaluation 26H2 build 26300.9457 and a verified
  clean pre-WSL checkpoint restore. Manual WSL/Ubuntu prerequisites are observed. Candidate-executed WSL/distro/tool installation and full selected
  service capacity remain unverified.
- Historical 24-GiB Windows OS-only phase was distinct from the then-32-GiB guest. Current guest is30GiB with resource assessment VERIFIED. RAM
  was set/observed 32 GiB while off; a 34-GiB free-host guard precedes its boot.
  Do not infer effective WSL limits or service capacity from VM settings.
- User separately authorized destructive Ubuntu reset only inside the owned VM after a new verified recovery snapshot; current30 scoped reset/recovery executed and passed. Existing local WSL
  distributions and native resources are preserved. Host-wide shutdown/reset
  or native fault/reboot injection must not be inferred from access details.
- All required AC1/AC2 product fresh/rerun/recovery, ordinary WSL preservation,
  remaining scenarios, routes and authentication results remain open. Scoped reset isolation passes for recorded identity/hash scope. No release
  support guard or qualified list is changed; #461 remains BLOCKED.
- AC4 is verified locally: urllib3 2.8.0 strict audit and complete Python 3.12
  quality passed at the frozen runtime candidate. Historical failed audit and
  mounted-checkout timeout remain in test_results.md.
- Historical #363 source/scenario results do not qualify this new candidate.
- Authentication requires protected credentials and redacted evidence. Raw
  VM files, credentials, paths and logs remain private ignored artifacts.
- The source-bound Windows dry-run measured only file hashes and selected
  registry fields; it is partial S13 evidence, not comprehensive no-write proof.

No product quality rule, source guard or selected-service capacity requirement
was weakened. Windows OS provisioning at 24 GiB does not qualify WSL capacity.

The first feature-only UAC launch was canceled; the authorized retry confirmed
features but returned exit 4 PARTIAL when the effect checkpoint replacement
failed. The pending checkpoint and effect records are preserved. A separate
owned-guest reboot was verified and fresh source-bound inventory requests
install_wsl. The revised NullString fix has a passing Windows PowerShell 5.1
filesystem regression, and the full Python 3.12 quality retry passes. Corrected source is frozen at bce63aaf and verified in the owned guest.
Protected disposable actual writer create/replace passes; revised product apply
is blocked by storage ACL trust and the retained old-source checkpoint. The operator-installed
Ubuntu registration must be preserved; its observed WSL allocation needs
21-GiB/8-processor reconciliation. Do not upgrade the original partial result.

Current concrete blocker: the selected WSL VHD carries additional explicit
FullControl grants categorized from SIDs as a VM instance and an app capability.
The existing resource path ACL guard refuses them (untrusted_evidence_acl),
leaving storage/effective resource inventory unverified. Independent architecture/security review accepts a narrowly scoped metadata-only VHD role correction with trusted owner/type/path checks; implementation is under verification. Do not remove
WSL-managed grants or permit arbitrary SID families to make the plan pass.
The exact known old-source checkpoint could be deliberately archived with
verified bytes/ACLs and the canonical lock, as independently reviewed; it was
not archived because the independent storage blocker remains. Operator manual
Ubuntu installation, current .wslconfig and canonical pending state are preserved.

Current external prerequisites, 2026-10-11: sourceef7 physical native existing-host
read-only checks and own-venv preparation/rerun are recorded; full installation
and destructive reboot/fault recovery are not authorized on a verified clean
recoverable scope. Existing IPv6 bridge and three nodes remain protected.
The additional native26 fixture failed its recovery boot and is now Off with
clean checkpoint retained; it is not substituted for successful Linux results.
Windows32 fixture remains Off pending both physical and commit headroom. Latest
read-only Windows observation:39.041GiB physical available,29.238GiB commit
available; total commit limit72.291GiB, automatically managed pagefile8806MiB.
User capacity question was answered with actual measured values; no physical-host
pagefile policy or application state was changed. Existing VM-only Ubuntu reset
consent remains valid, but execution has not occurred.

The subsequent operator-authorized 26-GiB resize supersedes the current
Windows32/Off prerequisite above: owned Windows VM now runs at fixed 26 GiB.
Standard WSL 21 GiB plus Windows reserve 7 GiB cannot fit this guest; resource
policy is unchanged. Reset consent remains confined to the protected test VM.

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

Capacity planning from the unchanged reserve formula: at nominal29GiB the
Windows reserve rises to8GiB, requiring29GiB observed; if the same small guest
reservation remains, exact29 also misses the boundary. Nominal30GiB is the
next whole-GiB setting with arithmetic margin (29GiB required). This is a
planning calculation, not an executed30GiB qualification or operator-approved
resize; current explicit28GiB allocation remains unchanged.

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

Read-only bridge diagnosis: actual unmodified bridge inventory subprocess
exit124 at45seconds, cause timeout; no bridge installation executed.
Independent read-only service/firewall/listener/portproxy dependency probes
all exit0 (2211/2906/2226/874ms), so individual inventories alone do not
establish bridge readiness. See windows30_bridge_diagnostic_result.json and
windows30_bridge_dependencies_result.json. Default preparation's15s inventory
refusal remains recorded; no timeout default or safety guard was changed.

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

## Interactive bridge installation prerequisite

Owned guest session query reports no logged-on user. No hidden-session apply
was attempted: the unmodified source requires the WSL-owner Windows credential
dialog before bridge service installation. An owned, highest-runlevel interactive
task was registered only in the verified30GiB test VM for that account's next
logon. Its protected runner rejects existing canonical state, reobserves exact
source/effective resources, requires exactly bridge_install and no unexpected
blockers, then approves that fresh plan with the actual verified current recovery
reference. No credential is stored in the runner or task arguments.
Task registration is preparation evidence, not Apply or bridge-install success.
Awaiting interactive owner logon/credential dialog; no Apply has executed as of
09:53:33Z. The first task preparation refused untrusted ACL ancestry outside
the canonical protected store; it did not install a task or execute Apply.
The runner was moved to the existing protected preparation store and both
private ACL setup/path assertion passed before the task was registered.
See windows30_interactive_bridge_task_result.json.

## Interactive logon attempt and guarded starter correction

Operator reported guest logon/confirmation. Actual task first run at10:06:23Z
returned1 before Apply: operator helper placed a PowerShell host argument after
-File, causing JSON parsing failure. At10:09:25Z the bridge service and canonical
checkpoint were both absent; independent product source-bound preflight/dry-run
again had resource VERIFIED and only prerequisite_missing/bridge_install.
This is an operator-harness failure, not product Apply or installation evidence.
First failure retained privately and classified in
windows30_interactive_bridge_first_attempt_result.json.

Corrected only the ignored operator starter: host argument precedes -File, and
raw plan is saved before parsing. Retry verifies exact old-runner hash, old
pre-apply failure, task not running, service/checkpoint absent and retained
verified snapshot. Protected runner ACL/path revalidated. Actual child argument
probe returns source-verified bridge-only plan (exit2), then existing interactive
task was started at10:11:34Z. See
windows30_interactive_bridge_retry_start_result.json. This is retry-start evidence;
installation/result remains pending observation. Frozen product source e01 and
all product timeout, credential, ACL, consent and state guards are unchanged.

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

## Recovery execution prerequisite at current stop

Interrupted payload and uncertain checkpoint are exported/hash-preserved outside
the VM. First whole-VM recovery helper stopped the owned VM normally and
requested an offline failure snapshot, but failed to observe that new snapshot
immediately; no restoration success is claimed. Error retained privately.
The corrected operator helper uses fresh VM-name snapshot inventory with a
bounded wait, preserves/reuses the exact owned offline failed-state snapshot,
and can resume from Off. It retains the actually verified original checkpoint
reference and all restore identity/primary-WSL checks. The corrected launch
waited on real host Windows UAC, then returned Windows cancellation before
helper execution; no corrected restore result exists. This is an OS interaction
result, not an auto-review rejection or revoked live scope. A newly announced
retry is being launched for the same concrete owned-VM restoration.
The VM is not claimed ready. Pending product checkpoint is not rewritten;
whole-VM recovery and product bridge recovery remain separate claims.

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

## Restored candidate preparation and existing interactive owner

Actual source-bound e01 preflight/dry-run rerun afterwholeVM recovery verified
source/resource inventory and preserved protected-state fingerprints. Exact
confirmed old806 resource state from restored snapshot then archived again
under canonical lock with byte/ACL equality and fresh source/host/distro/config
checks; no pending uncertain state is rewritten. Fresh plan only bridge_install
and prerequisite_missing. At10:34:07Z service/canonical checkpoint absent and
one existing same-owner console Session1 Active. No autologon/LSA/Winlogon
change is needed or implemented; observed AutoAdminLogonfalse and no plaintext
WinlogonDefaultPassword. See windows30_postrecovery_bridge_preparation_result.json.
The first combined operator helper exited on an invalid parent LASTEXITCODE
check despite actual child inventory PASS; corrected to require actual saved
result contract, then complete preparation returned0. No product code changed.
A reviewed bounded exact-dialog operator-input helper is being prepared;
its preparation cannot be counted as authenticated service installation.


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
# Current SSH-target blockers, 2026-10-17 Europe/Berlin

See [ssh_qualification_20261017.json](ssh_qualification_20261017.json).
Installation/restarts are now authorized on the two supplied targets, with
operator-asserted restoration availability; reset remains unauthorized. Actual
snapshot identity/restore proof and clean-host proof are absent for these targets.
Native preparation refuses active LXD, which manages three stopped instances;
three Incus instances are running. Do not remove or stop these implicitly.
WSL Python/Incus preparation progressed, but canonical proxy listeners are
IPv6 wildcards despite IPv4 configured endpoints. Do not normalize away this
observation or weaken listener ownership/exposure checks without review.
No installation, restart, recovery or authenticated service result exists for
this continuation. Earlier owned-VM authentication timeout remains historical,
not the blocker on this separately inventoried WSL target. Issue BLOCKED.

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
