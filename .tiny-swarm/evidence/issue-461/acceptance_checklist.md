# Acceptance checklist

## Current operator-accepted scope — 2026-10-17

The operator explicitly deferred the remaining live hardening scenarios due to
test-setup limits. The amended scope is the evidenced existing-host repairs,
qualification and operator guidance. See the authoritative requirement mapping
in [the current requirement scope](requirement_matrix.md#current-operator-accepted-scope--2026-10-17).
These deferred scenarios no longer block this agreed delivery; their unverified
results and residual risks remain. Earlier whole-campaign BLOCKED/INCOMPLETE
statements below are historical and do not describe the amended scope. No
fresh-host, full fault-matrix or global release qualification is claimed.


- [x] Explicit operator deferrals mapped to stable requirement/scenario IDs.
- [x] Existing-host repairs, executed checks and operator guidance retained.
- [x] Independent amended-scope audit PASS; deferred cases remain unverified.

## Historical scoped acceptance before operator deferral — 2026-10-17

- [x] Combined product fixes independently reviewed and frozen at d2fd89be; full quality gate PASS2631 tests/18 existing skips.
- [x] Ordinary full installation/rerun on both supplied existing26 hosts; node/volume/marker/service/TLS preservation verified.
- [x] Native actual host reboot and selected WSL restart; final nine TLS routes and seven positive/negative API checks per target.
- [x] Managed root-disk recovery verified, with native4f/d2 source boundaries explicit.
- [x] Isolated dependency-stage download/interruption and connected resume/rerun on both hosts; scope remains stage-only.
- [x] Manual certificate/trust, sudo/group, Git checkout, provider, restart/warmup and recovery guidance updated and reviewed.
- [x] S08 existing-WSL exposure collision blocks with exit2; exact provider/checkpoint restoration, restored preflight0 and postrestore API/data checks PASS.
- [ ] S07 actual address drift (address unchanged); no native-collision or foreign-executable rejection PASS inferred.
- [ ] Fresh Ubuntu26.04 hosts on both families, group transition and full CLI fault cases; no release qualification or full DONE.
- [ ] Final independent issue audit decision after remaining scenario disposition.


- [ ] AC1: Both host families have actual fresh/rerun/recovery results.
  Fresh/rerun/recovery remain BLOCKED; native preflight exit 2 is recorded.
- [ ] AC2: Real ordinary WSL preservation and separately authorized reset
  isolation results. Sourceef7 preflight/dry-run preserves measured registration,
  configuration, hosts and bootstrap-state fingerprints. Separate reset consent
  exists only for Ubuntu in the secured owned VM. Current30 checkpoint actual restore and scoped Ubuntu unregister/empty
  inventory/restore were verified with primary WSL registration/config unchanged;
  ordinary full-apply preservation and remaining bootstrap scenarios remain open.
- [x] AC3: Each eligible release explicitly marked UNQUALIFIED in the release
  matrix; excluded target families identified. No new release is qualified.
- [x] AC4: Targeted regressions and applicable local quality/security checks
  pass for the integrated candidate. Current frozen source
  `e01e1dd5dab2ff7390d782d891a47e2191c1c7a9`: full Python3.12 gate PASS2555 tests,
  43 architecture tests, 7 import contracts, 799 typed files; hosts real-file
  regression red/green PASS after correction. Prior resource assertions77 PASS. Strict dependency audit PASS. Concrete
  architecture/security reviews approve R461-24. Historical storage trust was
  resolved in source806; current live prerequisites are bridge installation and missing full live scenarios;
  corrected inventory passes and confirmed prior-source state is safely archived. Current30 resource and reset isolation cases pass.
- [ ] Exact target/source consent, observed versions, commands/exits and
  redacted per-scenario evidence with AC mapping.
- [ ] Independent completion audit permits DONE. Live blockers prevent PASS.

All scenario IDs map to requirements in requirement_matrix.md. Local checks
support AC4 and safety regression coverage only; they cannot close AC1/AC2.


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
# Latest SSH continuation, 2026-10-17 Europe/Berlin

AC1/AC2 remain OPEN; AC3 keeps every target UNQUALIFIED. No product source change
or new full-quality result is claimed for AC4. See the distinct-target results in
[ssh_qualification_20261017.json](ssh_qualification_20261017.json): native active
LXD refusal, WSL Python/Incus progress followed by network listener-exposure
refusal, and preserved archived checkpoints. Installation/restarts authorized;
reset not authorized. No completion PASS or release qualification follows.

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

The operator clarified that Ubuntu24.04 is not a required live target for #461;
Ubuntu26.04 is the current LTS target. This supersedes the original dual-release
live-target expectation. Ubuntu24.04 remains supported but explicitly UNQUALIFIED
for live use; it is not itself a #461 blocker. Fresh Ubuntu26.04 hosts on both
native and WSL2 families remain required and unavailable. Other open scenarios
remain unchanged.

Final independent audit: BLOCKED for whole issue; scoped exercised scenarios VERIFIED. Final S08 and twelve-block documentation continuation supersedes earlier pending entries. No DONE/release qualification.
