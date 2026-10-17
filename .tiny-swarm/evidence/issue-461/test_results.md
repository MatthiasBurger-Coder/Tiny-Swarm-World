# Test results

## Current operator-accepted scope — 2026-10-17

The operator explicitly deferred the remaining live hardening scenarios due to
test-setup limits. The amended scope is the evidenced existing-host repairs,
qualification and operator guidance. See the authoritative requirement mapping
in [the current requirement scope](requirement_matrix.md#current-operator-accepted-scope--2026-10-17).
These deferred scenarios no longer block this agreed delivery; their unverified
results and residual risks remain. Earlier whole-campaign BLOCKED/INCOMPLETE
statements below are historical and do not describe the amended scope. No
fresh-host, full fault-matrix or global release qualification is claimed.


Current frozen runtime candidate: `51bac77cd94e210a3b8640f4e83688180e520057`.
Combined local quality and native fixtures PASS; affected original-budget live rerun pending.
Latest guest Apply used51bac and returned4/PARTIAL with confirmed bridge_install;
independent default15-second bridge inventories are ready. Linux checkout is required.
Scoped VM-only Ubuntu reset/restore
was executed and verified; latest bridge failure recovery is being prepared.
Historical and current executed results appear below.

## Historical baseline and first frozen candidate

Historical candidate: `3da77f8908d598688ed46dd6eab74c5f32a7ac50`.
Initial baseline checks used Python 3.14.4; corrected-candidate quality used
supported Python 3.12.14. Initial failures and later successes are retained below.

- `PATH="$PWD/.venv/bin:$PATH" PYTHONPATH=src python3 -m unittest tests.test_bootstrap_recovery tests.test_install_handoff tests.test_ubuntu_bootstrap_integration tests.test_prepare_windows tests.test_security_gate`: PASS, exit 0, 35 tests in 27.226s, no skips reported. Log: `/tmp/issue-461-targeted.log` (local transient artifact).
- `PATH="$PWD/.venv/bin:$PATH" python3 tools/security_gate.py dependencies`: FAIL, exit 1. pip_audit found 3 known vulnerabilities in locked urllib3 2.7.0: PYSEC-2026-4175, PYSEC-2026-4176, PYSEC-2026-4177; tool-reported fix version 2.8.0. Log: `/tmp/issue-461-dependencies.log`. This initial failure was remediated below.
- `PATH="$PWD/.venv/bin:$PATH" python3 tools/quality_gate.py quality`: FAIL, exit 1: 2,554 tests in 644.359s, 18 skips, one subprocess timeout in `tests.test_install_script.TestInstallScript.test_install_uses_private_configured_evidence_root` (fixture deadline 10s on the mounted checkout). Policy, complexity, lint, 7 import contracts, 43 architecture tests and typecheck of 799 files passed. This used the existing Python 3.14.4 environment; it is not an exact clean final-candidate run. Log: `/tmp/issue-461-quality.log`.
- `git diff --check`: PASS at evidence preparation; repeat after finalization.

At that historical point, the focused suite preceded the first full gate. The corrected lock was being
verified in a separate Linux-native checkout with an isolated Python 3.12
environment and PowerShell 7.6.6; no shared test fixture files are used.
The dependency audit is independent of regression verification.
Container image/config scanning is not claimed: no container configuration change
and no local trivy executable observed. External result unavailable, not verified.

Read-only target inspection: native password-authenticated SSH OS/kernel/PID1/
executable inventory exit 0; initial key-only attempt exit 255 (authentication
not accepted), not a qualification failure. Local OS/kernel/PID1 inspection and
Windows OS/WSL version/distribution inventory exit 0. Redacted facts are in
qualification_matrix.md; no passwords or remote address stored here.

Native tests and owned Windows VM preparation are authorized. Required fresh/recovery
scenarios then lacked prerequisites; destructive WSL reset then lacked separate consent.
Later scoped consent supersedes that historical missing-consent state.
No current external CI/SonarQube result accessed.

## AC4 remediation verified

- Supported Python 3.12.14 lock generation with pip-tools 7.5.3 changed only urllib3 2.7.0 -> 2.8.0 and its two artifact hashes. No audit ignores or policy changes. Upstream source: [urllib3 2.8.0 release](https://pypi.org/project/urllib3/2.8.0/).
- `PATH="$PWD/.venv/bin:$PATH" python3 tools/security_gate.py dependencies` after lock remediation: PASS, exit 0, no known vulnerabilities found. Log: `/tmp/issue-461-dependencies-fixed.log`. This does not erase the original failed audit.
- Clean Python 3.12 environment hash-verified runtime lock installation: PASS, exit 0. `python -m pip check`: PASS, no broken requirements.
- `PATH="/tmp/tsw-issue461-runtime312/bin:/tmp/tsw-powershell-7.6.6:$PATH" python3 tools/quality_gate.py quality` in `/home/micro/tsw-issue461-verification`: PASS, exit 0, 2,554 tests in 137.523s with 18 existing skips; 43 architecture tests, 7 import contracts, typecheck 799 files, lint, complexity and verification-policy passed. Tested base candidate plus byte-identical corrected lock; Frozen as `3da77f8908d598688ed46dd6eab74c5f32a7ac50`; runtime source and lock are byte-equivalent to the verified checkout.
- Hyper-V administrator inventory: initial unelevated `Get-VM` denied (exit 1); UAC-elevated inventory succeeded. Owned VM creation succeeded with no other VM/switch changes; full bootstrap is unverified.

Final corrected-candidate gate used Python 3.12.14 and PowerShell 7.6.6.
The earlier mounted-checkout timeout is retained as a failed invocation; the
new Linux-native checkout result is a separate success. No test deadline,
assertion, complexity threshold, import rule or audit rule was weakened.

## Executed native preflight

Run N26-existing-preflight-20261010 used the frozen candidate release archive
SHA-256 `de05f717305c5328c51d1488fb1c3d5f40b07ccacf8caa7bc04bf931e8788eba`.
`./prepare_linux.sh --preflight`: exit 2 at 21:48:39–21:48:40 UTC. Ubuntu/package
preflight passed; Python dependencies absent. No installation executed. Nine
protected file scopes were byte/owner/mode unchanged, with no inaccessible
entries; all three existing Incus node identities/status/limits were unchanged.
S13 preservation observation is PARTIAL; fresh installation/recovery remains
LIVE_PREREQUISITE_MISSING. Portable evidence: native_preflight_result.json.

## Executed bounded native Python preparation

`./prepare_linux.sh` with one Python-stage `yes` followed by EOF: exit 2,
21:55:14–21:55:23 UTC. Hash-locked dependencies and editable project installed
into the candidate-owned venv using native Python 3.14. Existing Incus resources
were observed READY. Network preparation refused the existing IPv6-enabled
bridge policy; no bridge policy was changed. A subsequent `--preflight` also
exited 2 (21:55:23–21:55:27 UTC), with Python ready and the same network blocker.
Eight existing protected file scopes and all three node inventories remained
unchanged; original candidate files remained byte-identical. Checkpoints use
an explicitly isolated owned XDG_STATE_HOME. These are PARTIAL existing-host
observations, not fresh-host or install/recovery success.
Portable evidence: native_python_result.json. Native network stage remains
LIVE_PREREQUISITE_MISSING; preserve existing IPv6 policy.

## Executed owned Windows image provisioning

Official Microsoft EN-US evaluation ISO SHA-256 matched
`BC3F24086EBADC94489066B5AD78089E2CF5C3491E90E790BB81A2B199C10E38`;
setup signature was valid Microsoft. Owned disk was verified RAW and only that
VHD was partitioned. DISM `/Apply-Image /CheckIntegrity`: exit 0. Guest-targeted
BCDBoot `/s <owned EFI> /f UEFI`: exit 0. Provisioning script exited 1 before
credential creation/first boot; post-image free host RAM was 33.6 GiB versus
34 GiB required. VM remains off, no answer file or guest credential created,
no checkpoint/WSL/product success claimed. This is LIVE_DEGRADED / PARTIAL
provisioning with a guarded stop, not completed installation.
No image reapplication is planned; bounded owned-image resume is prepared.
Portable evidence: windows_image_result.json.

Owned-image resume attempt: exit 1 at RESUME_PRECHECK; no credentials/boot
executed. This invocation's generic exception does not identify the exact guard.
Later read-only VHD diagnosis confirmed owned VM off, 32-GiB RAM, correct disk,
valid Microsoft kernel signature and Windows volume. It observed four partitions:
Initialize-Disk had automatically added a reserved partition before the three
explicitly created partitions. The resume helper's three-partition assumption
was corrected to the measured owned layout and unique typed Windows volume;
no repartitioning occurred. Rechecked free RAM was 33.682 GiB, below 34 GiB.
Corrected resume is unexecuted. Portable evidence: windows_resume_result.json,
windows_image_diagnostic.json. These observations do not prove guest readiness
or recovery success.

## Windows OS-only provisioning continuation

The operator reported more memory available. A fresh measurement was 33.61 GiB,
still below the 34-GiB free-host guard for a 32-GiB guest. The previously planned
separate Windows OS provisioning phase now uses 24 GiB guest RAM and 26 GiB
free-host guard (the same 2-GiB margin). The original 32-GiB/34-GiB guard and
all product resource checks are unchanged. No WSL workload runs in this phase.
Independent static review found no concrete safety blocker. At that point first boot was in
progress; this is not clean-guest readiness, restoration or qualification PASS.
The checkpoint configuration will be recorded as 24 GiB; full WSL qualification
requires a later observed 32-GiB guest with the original capacity checks.

24-GiB OS-only first boot reached PowerShell Direct: Windows 11 Enterprise
Evaluation, version 10.0.26300/build 26300, WSL absent, VirtualMachinePlatform
Disabled. Guest answer files were removed and verified absent. Guest stopped
normally. Checkpoint creation then failed with access-denied 0x80070005 in the
owned VM storage; provisioning exited 1. This preserves an actual partial
result rather than claiming checkpoint readiness. The scoped remedy grants
only this VM's SID to its own storage subdirectory and leaves the protected
credential-parent ACL unchanged. Original failure retained in
windows_provision_only_result.json. Restoration was unverified at that point; later verification follows.

Scoped owned-VM directory permission repair left the private credential parent
ACL unchanged. Checkpoint creation returned, but its immediate identity check
failed (helper exit 1), retained in windows_checkpoint_attempt.json. A later
read-only inventory through the bound VM object observed exactly one
W09-CleanWindowsPreWSL checkpoint with matching VM GUID, 24-GiB configuration
and VM off (windows_checkpoint_inventory.json). The checkpoint is now observed;
restoration was unverified at that point; later verification follows. Earlier creation/verification failures are not
erased. Candidate read-only dry-run in the 24-GiB guest was pending at that point;
its actual result follows.

First executed Windows candidate dry-run: exit 2, prerequisite_missing,
enable_features planned; .wslconfig/hosts hashes and selected WSL registration
fields unchanged. Windows guest exact build 26300.9457 (26H2), PowerShell
5.1.26100.9444, WSL absent. The helper omitted the independently chosen
QualificationRevision, so offline source verification correctly remained false;
this is retained in windows_guest_dry_run_unbound.json. A new source-bound
read-only invocation includes the exact frozen SHA and preserves existing
extracted files for verification. No apply or qualification bypass occurs.

Source-bound Windows dry-run with explicit frozen QualificationRevision: exit 2,
prerequisite_missing and enable_features planned. Offline source proof verified
commit 3da77f8908d598688ed46dd6eab74c5f32a7ac50. The measured file-hash and
selected registration invariants remained unchanged. This is partial S13
observation; full Windows feature/firewall/state ownership coverage is absent.
Guest stopped and RAM was set/observed 32 GiB while off. Host free RAM then
measured 34.86 GiB. Portable record: windows_guest_dry_run_source_bound.json.
The owned pre-WSL checkpoint restoration test was pending at that point with the
checkpoint's 24-GiB configuration; later full-guest boot retains the 34-GiB guard.

Owned pre-WSL checkpoint restoration executed successfully: restored the exact
selected checkpoint, booted its 24-GiB configuration and observed the post-
checkpoint candidate directory absent, exact Windows build 26300.9457 unchanged,
answer files absent, WSL absent and VirtualMachinePlatform Disabled. Guest
stopped normally, then 32-GiB RAM was set and observed while off. This verifies
only Windows environment recovery before WSL, not bootstrap/WSL recovery or
full WSL capacity. Portable record: windows_pre_wsl_restore_result.json.

The host UAC-elevated feature-only helper launch exited 1: Windows reported the
operation canceled by the user. No helper result was created, no full-guest
boot or product feature apply occurred. A platform elevation decision is still
needed; existing task authorization does not turn this canceled launch into
executed evidence. Portable record: windows_feature_elevation_result.json.

### Host memory recheck (2026-10-10T22:25:17+00:00)

Windows CIM reported 31.64817 GiB free; the unchanged 34-GiB full-guest guard is not met. No elevated helper was relaunched, and no guest or WSL mutation occurred during this recheck. All 12 portable evidence JSON files parsed successfully; documentation diff whitespace check passed.

### Authorized feature retry and partial-state inspection

User requested continuation after the canceled UAC launch. Fresh host memory was 34.80497 GiB; the full guest helper passed its unchanged guard at 34.676 GiB, booted the owned 32-GiB VM and observed 31.999 GiB guest RAM. Source-bound preflight exit 2; actual apply exit 4 PARTIAL, enable_features confirmed, no uncertain actions. Product effect evidence reports confirmed enable_features / exit 3010 / RESTART_REQUIRED, but bootstrap state remains pending: evidence_or_action_failed is preserved. Independent fresh inventory observes exactly both required features Enabled, source verified at the frozen candidate, preflight exit 3 and reboot_pending, next stage install_wsl. This permits owned-guest recovery restart; it does not establish successful bootstrap persistence or service readiness. Portable records: windows_feature_apply_result.json and windows_feature_partial_inspection.json.

### Actual recovery restart and checkpoint-writer reproduction

Owned guest restart requested 22:42:16Z, verified complete 22:43:22Z. LastBootUpTime advances from 22:38:46Z to 22:42:32Z; exactly both named features Enabled. Source-bound post-restart dry-run exit 2, next install_wsl, only prerequisite_missing. Original apply remains PARTIAL/4.

Initial writer diagnosis could not import the guest module under its default execution policy; a process-only bypass allowed the diagnostic. A scratch directory under the candidate checkout failed the unchanged ACL guard (untrusted_evidence_acl); relocating scratch beneath the protected evidence directory allowed the actual writer reproduction. Canonical pending checkpoint unchanged. Actual Windows PowerShell 5.1 creates pending successfully but raises ArgumentException (-2147024809) on the second write; direct $null replacement fails and explicit NullString replacement succeeds.

New real-filesystem regression failed before fix with empty-path ArgumentException, and passes after NullString correction under pwsh 7.6.6. Initial Windows PowerShell regression encountered prior test-fixture Test-Path pollution; a fresh module isolates the new IO test. Corrected Windows PowerShell 5.1 suite PASS (130 mocked lifecycle assertions plus actual state-file create/replace contracts); it is local regression evidence, not live source qualification.

First revised full quality attempt had a copy SameFileError before an unintended gate on old files; only that task-owned run was stopped and discarded. Byte-equal files were then copied and the revised full Python 3.12 gate ran 2554 tests in 137.691s, 18 skips, one error in unchanged test_failed_postcheck_preserves_attempted_effect_and_backup: Protected file changed during observation. Required gate remains FAILED pending targeted classification and full retry; no threshold or protected observation guard changed.

### Corrected candidate local verification and operator-installed guest WSL

Targeted Python 3.12 rerun PASS 38 tests in 24.481s (unchanged protected file tests and revised Windows preparation contract). The full quality retry PASS: 2554 tests in 137.679s, 18 skips; 43 architecture tests in 3.314s; lint, complexity, verification-policy, import contracts and type checks passed. Source adapter, lock and final regression test are byte-equal between working checkout and Linux-native verification worktree. Original transient gate failure remains above.

Owned guest was gracefully stopped at 22:49:59Z for verification. Operator later reported manual WSL + Ubuntu installation and confirmed it was in the test VM. Fresh read-only inspection finds the owned VM Running with 32 GiB, Windows 26300.9457, WSL 3.0.1.0/kernel6.18.40.1, one default Ubuntu registration Running generation2, Ubuntu26.04.1LTS/x86_64/systemd. Observed WSL MemTotal16377308kB and12 processors do not establish the required21GiB/8-processor budget. This is manual prerequisite evidence, not candidate-executed WSL/distro installation. Preserve operator installation; do not restore the old clean checkpoint over it.

### Corrected frozen source, actual writer and resource permission blocker

Local source freeze bce63aafb6990e9157c8ddb3eb12e4aa9fd1f440; no remote publication. Clean release membership manifest built before evidence continuation; archive SHA48326e2e486f4fb1c34287dc274a445b7438782a4b0d27de1616b2afa01dcb18 verified in owned guest. Exact command in windows_revised_plan_result.json: custom observed Ubuntu/explicit26.04, source-bound dry-run,21GiB/8CPU/6GiBswap. Exit2, source verified, no actions, blockers resource_inventory_unknown and bootstrap_state_invalid. Actual corrected writer creates pending and replaces it with effect in a protected disposable sibling using real ACL guards; canonical old checkpoint and .wslconfig hashes unchanged. Original checkpoint remains bound to3da77/Ubuntu-26.04, pending enable_features.

Read-only resource core diagnosis observes guest memory34358579200bytes/12CPUs and valid projection/safe current config; fails before storage/effective limits with untrusted_evidence_acl. Selected registration directory grants only current-user/SYSTEM/Administrators. Selected VHD has additional explicit FullControl grants classified by SID family as VirtualMachineInstance and AppCapability. No trust exception or ACL change was attempted; security/architecture review is needed before resource apply. Planned clean-snapshot replay was superseded by the operator manual installation and was not executed. No state archive, WSL config write, selected-distro restart or package/distro replacement occurred.

VHD correction regression history: original source fails new actual Windows5.1
fixture at missing helper (red). Revised source passes actual disposable Win5.1
30 assertions. Windows7.6.6 full legacy fixture cannot use .NET Framework-only
File.SetAccessControl; metadata-only fixture uses the supported filesystem ACL
extension and passes10 assertions. A Set-Acl portable fixture privilege failure
is retained in private logs; corrected fixture setup does not change product guards.
Targeted prepare_windows/resource_projection/source_proof PASS18 (42.243s).
Full Python3.12 required gate is pending.

Final R461-23 validation: disposable Windows5.1 PASS30, modernWindows7.6.6
metadata-only PASS10; targeted resource_projection PASS7/16.407s. Required full
Python3.12 quality retry PASS (2554 tests,18 existing skips;43 architecture tests).
First complete gate failed with Windows child-output UnicodeDecodeError, preserved
in /tmp/issue461-vhd-quality.log; explicit decoding and compatible fixture-only ACL
APIs fix test reporting/setup without relaxing success assertions or product guards.
Final gate log: /tmp/issue461-vhd-quality-final.log. Strict dependency audit carries
forward on unchanged requirements.lock.

Owned operator-Ubuntu checkpoint actual restore PASS at 2026-10-10T23:29:51Z:
registration identity, Ubuntu26.04 generation2, original pending state SHA and
configuration ABSENT preserved, recovery marker exact. Host free before32GiB boot
40.966GiB. Candidate806 extracted membership/source proof verified; metadata
inventory storage/effective known, no ACL/config/canonical state mutation by that
observation. Product plan first saw distro_stopped; later operator diagnostic started
owned Ubuntu. Initial operator resource helper archived exact old checkpoint under
canonical lock with byte/ACL equality but subsequent CLI parameter -Apply was invalid;
configuration apply did not start. A corrected separately inspected resume is running.
Keep this helper failure distinct from a product executed-stage result.

R461-24 regression: original runtime rejects added required physical signal
(red); corrected runtime PASS77 resource assertions and strict shell regressions.
Actual source806 apply exit3 and owned WSL restart result remain preserved in
windows_resource_apply_result.json / windows_resource_postrestart_result.json.
Read-only zone/kernel facts: windows_memory_accounting_observation.json.
The first new full-gate invocation accidentally used older verification-copy
bytes; it was terminated and is not accepted. Correct source byte copies were
asserted before the corrected full-gate invocation; its result remains pending.

R461-24 corrected full gate PASS:2555 tests136.568s,18 existing skips;
43 architecture tests3.150s,7 import contracts,799 typechecked files and all
other required gates. Runtime/ADR bytes matched verification copy. Final test-only
boundary/aggregate-overflow additions: targeted19 tests42.193s PASS; standalone
resource assertions77 PASS. No runtime changes followed the full gate.
Logs:/tmp/issue461-memory-quality-corrected.log and
/tmp/issue461-memory-targeted-final.log. Independent architecture/security and
completion-auditor concrete reviews APPROVE; overall issue incomplete.

## Physical Linux continuation after user target steering

Sourceef7 clean Git/archive verified on supplied native26.04.1/kernel7.0.0-34.
Own locked Python venv preparation succeeded; aggregate prepare exit2 on preserved
existing IPv6 bridge. Rerun sees prepared venv, no Python change, exit2. Installer
preflight/dry-run exit0. Repeated read-only probe confirms9 protected file scopes
unchanged, zero inaccessible entries and3 Incus identities/limits preserved.
Full node config, networks and profiles also compare equal. Existing services
were inventoried read-only; they are not attributed to an unexecuted candidate
installation. New native full install/reboot/fault/fresh qualification is not
claimed. No password or SSH address is stored in public evidence.

Windows resource rerun/reset remains pending: after owned native fixture stopped,
host has38.77GiB physical available but only28.725GiB commit headroom.
Both>=34GiB are required before restarting32GiB Windows fixture. User was asked
to close further Windows applications; no host pagefile policy was changed.

Existing-host anonymous route baseline is recorded separately in
native_existing_route_baseline.json, not candidate service authentication.
Sourceef7 full install remains unexecuted. Latest physical-host capacity refresh
still has29.238GiB commit headroom despite39.041GiB free physical RAM; Windows32
fixture cannot be restarted safely under the observed resource constraint.

## User-requested Windows VM reduction to 26 GiB

On 2026-10-11 the operator explicitly requested 26 GiB. Exact owned VM identity
and Off state were checked before changing fixed startup memory to 26 GiB.
Observed physical headroom 38.526 GiB and commit headroom 29.036 GiB exceeded
the 28-GiB start guard; actual Hyper-V start succeeded and state is Running.
See windows26_resize_start_result.json. Historical 32-GiB start blockage remains
valid for that prior allocation. This change does not reduce product thresholds:
standard WSL allocation 21 GiB plus Windows reserve 7 GiB exceeds the 26-GiB
guest. Standard profile qualification therefore remains open.

Post-start PSDirect observation PASS: Windows reports 27916128256 bytes of
physical guest memory. Selected Ubuntu 26.04.1 remains registered and starts
with systemd, kernel 6.18.40.1-microsoft-standard-WSL2; probe exit0.
See windows26_guest_verification_result.json. No candidate install or reset
is claimed by this reachability observation.

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

28-GiB post-start verification PASS: Windows reports 30063611904 physical
bytes; preserved Ubuntu26.04.1 starts with systemd and kernel
6.18.40.1-microsoft-standard-WSL2, probe exit0. Nominal allocation arithmetic
is not a candidate resource-preflight result. See
windows28_guest_verification_result.json.

## Source-ef7 actual preflight and dry-run at 28 GiB

Exact frozen archive/hash and product source proof verified. Initial selected
Ubuntu stopped result: both modes exit2, distro_stopped and
bootstrap_state_invalid. Operator started only selected owned Ubuntu separately.
Repeated actual modes exit2, insufficient_host_capacity plus
bootstrap_state_invalid (prior source806 canonical state retained unchanged).
Windows measured30063611904bytes versus required30064771072bytes: deficit
1159168bytes. Config/state/registration/hosts fingerprints unchanged.
WSL physical22547132416bytes versus configured22548578304bytes; usable
22033059840bytes, CPU8, swap6442450944bytes. Resource inventory known; whole
effective verification remains false because host allocation is blocked.
No apply, state-identity edit or tolerance reduction was performed.
See windows_ef7_preflight_result.json and
windows_ef7_running_preflight_result.json.

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

Read-only bridge diagnosis: actual unmodified bridge inventory subprocess
exit124 at45seconds, cause timeout; no bridge installation executed.
Independent read-only service/firewall/listener/portproxy dependency probes
all exit0 (2211/2906/2226/874ms), so individual inventories alone do not
establish bridge readiness. See windows30_bridge_diagnostic_result.json and
windows30_bridge_dependencies_result.json. Default preparation's15s inventory
refusal remains recorded; no timeout default or safety guard was changed.

## R461-25 hosts-observation regression and quality

Declared before implementation. Actual WinPS5.1 real-file metadata regression
FAIL before correction (1.023s, changed fingerprint), PASS after explicit
string observation normalization (1.632s). Full provider graph now excluded;
equivalent decoded contents match fingerprints, content/newline changes
still invalidate, read errors propagate, fixture contents remain unchanged.
Full Python3.12 gate PASS:2555 tests135.842s,18existing skips;43architecture
tests3.243s;7import contracts,799typed files and all other gates. Exact changed
runtime/test/guide bytes matched Linux verification copy before/after execution.
Logs:/tmp/issue461-hosts-regression-red.log,
/tmp/issue461-hosts-regression-green.log,/tmp/issue461-hosts-quality.log.
Independent architecture/security and completion reviews approve concrete scope;
New source freeze and affected live inventory rerun are recorded below.

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

## Real-dialog operator helper launch pending host elevation

Independent security review accepted the scoped private operator helper after
fixing preparation-directory and process-proof ancestor validation when the
temporary credential leaf is absent. Updated helper AST parsing passed. The
helper targets the real source-bound credential dialog and exact current guest
owner/session/process; it does not replace product credential collection. The
180-second UI deadline is cooperative, with a separately registered five-minute
SYSTEM cleanup trigger. No autologon/LSA/Winlogon changes are implemented.

The host elevated helper was launched, but actual Windows UAC consent is still
pending. No new attempt-start result exists and no product Apply success is
claimed. The retained previous observer is historical, not evidence of this
launch. Once elevation completes, the helper starts the owned task and observes
results within the same elevated host process. Issue remains INCOMPLETE.

## UAC retry and actual real-dialog attempt start

The previous pending host UAC request returned canceled before the helper ran.
A new launch was accepted and actual owned guest task start was recorded at
11:13:43Z. See windows30_real_credential_ui_start_result.json. The first fresh
observation at11:14:07Z shows task Running, service absent and no checkpoint
yet. This is attempt-start evidence only; prior historical observer files are
not reused as a current product result.

## Actual bridge Apply returned PARTIAL; running service is not qualification

At11:16:04Z actual unchanged e01 product Apply returned exit4 PARTIAL with
bridge_postcheck_failed. By11:17:20Z task was Ready; actual service Running,
checkpoint effect/uncertain/unconfirmed. Fresh source-bound Preflight and
DryRun exit2 bridge_inventory_unavailable, resources VERIFIED. Temporary guest
credential blob absent. No UI submission proof was produced, so neither
automated credential entry nor its cause is inferred. The action.after
bridge_ready=true is a desired plan target, not an actual observation.

See windows30_real_ui_bridge_partial_result.json. Existing account-match
observer false is unverified until relative SCM account normalization is
checked; it is not evidence of a wrong service account. Read-only bounded
exact-source inventory diagnostics are prepared and launched behind host UAC.
The uncertain checkpoint is preserved; no new Apply/adopt/refresh is run.
Issue remains INCOMPLETE.

## Concrete read-only blocker and independent credential cleanup

At11:18:58Z exact-source direct read-only inventory with separately labelled
45-second diagnostic budget returned0 and valid schema: ownership owned,
bridge/routing/agent readiness false, blocker foreign_or_unknown_listener.
This diagnostic does not change the original postcheck result or timeout.
Normalized SCM identity is CURRENT_OWNER; earlier relative-account comparison
false is corrected without changing the service. Canonical checkpoint bytes
unchanged. See windows30_bridge_readonly_diagnosis_result.json.

At11:18:45Z independent SYSTEM expiry task actually reported temporary
credential absent; no matching UI process required termination. Current
observer verifies same-owner service and measured preservation, while
source-bound Preflight/DryRun still exit2 bridge_inventory_unavailable. See
windows30_bridge_credential_cleanup_result.json. No automated dialog-submission
proof exists. Next read-only diagnostics distinguish listener owner and
original15-second budget from longer diagnostic budget; no state repair.

Independent completion review confirms the latest scoped evidence is consistent
and overall issue remains INCOMPLETE/UNQUALIFIED. Product result envelopes
emit live_state LIVE_CONSENT_MISSING; this raw product field is retained as
emitted and does not negate the explicit operator authorization for these
owned-VM attempts. Scheduled task exit0 is not product Apply exit0: actual
Apply returned4.

## Listener diagnostic launch still requires host elevation

The preceding listener-only diagnostic launch returned host UAC cancellation
before helper execution. No listener diagnostic result exists. A fresh retry
created a consent process in actual host console Session1, matching the host
interop caller's session; this process observation does not prove a dialog was
visible to the operator. The latest helper remains pending elevation. No
listener owner attribution or new qualification is inferred from this launch.

## Listener read-only diagnostic actually completed

At11:56:07Z owned listener diagnostics completed. Original15-second bounded
inventory exits124 after15.0649seconds; separately labelled45-second read-only
probe exits0 after20.0964seconds. All24mapped listeners are hosted by svchost
with iphlpsvc attached, whereas the current ownership predicate accepts only
PID4. Exact netsh endpoint/protected-state mapping comparisons are recorded
per listener in windows30_listener_identity_and_timing_result.json. The
heartbeat reports windows-service/ready; this is not bridge readiness.

No further UAC approval is needed to obtain this completed observation. A
security/architecture review is examining a narrow modern IP Helper ownership
correction and bounded firewall inventory optimization. No product guard or
probe budget has been changed, and uncertain state remains preserved.

## R461-26 local listener identity correction

Independent architecture/security review approved the narrow adapter
observation correction, with no new ADR. The new branch requires unique
running IP Helper SCM identity, its exact System32 svchost image, SYSTEM
process ownership and repeated typed creation/PID/service identity. Native
SCM LocalSystem is handled as the built-in account name because NTAccount
translation of that alias was actually unavailable; live process SID still
must equal SYSTEM. Protected state, exact endpoint/mapping uniqueness and
legacy PID4 remain required; observed identity participates in consent hash.

Actual Windows PowerShell5.1 targeted fixture PASS109. A private controlled
baseline overlay restoring only the old PID4 ownership predicate exits1 at
'exact mapping and live IP Helper listener ready'. Negative cases cover wrong
service/process/name/image/owner, probe failures, initial/rechecked creation
type, recycled PID, duplicate records/mappings, absent mapping and mismatched
forwarding endpoints. Full quality is running; no affected live candidate
qualification is claimed and budgets/service/state remain unchanged.

## Read-only component timing identifies policy-filter bottleneck

Corrected private profiling harness actually completed12:07:04Z with unchanged
canonical checkpoint bytes. The first harness invocation failed after its reads
on an absent timed_out property; no result was counted before the corrected
run. Standalone component measurements, not an exact in-call profile:
all506firewall rules1.2932s; existing24-rule snapshot2.3911s; seven policy
filter groups12.7673s; second snapshot2.2276s; TCP listeners0.4586s; portproxy
records0.0868s. See windows30_bridge_component_timing_result.json.

Existing per-rule associations dominate the observed budget. A separate private
read-only experiment compares all-filter retrieval restricted to exact rule
identities with existing projections; product retrieval/timeout remain unchanged
until equivalence, timing and independent safety review are demonstrated.

## Read-only complete projection comparison supports separate performance slice

At12:11:02Z repeated existing seven-group retrieval measured12.7286s. Seven
native -All filter-family reads restricted to exact owned rule InstanceIDs
total0.9699s. For each family506objects were observed and24matched; all full
sorted projected JSON observations exactly equal the existing per-rule
association projections, including PackageObserved and restriction fields.
Canonical checkpoint bytes unchanged. See
windows30_firewall_filter_batch_comparison_result.json.

This is a diagnostic equivalence/timing experiment, not a passing product
postcheck. Proposed R461-27 performance change remains separately declared
and under independent review; no timeout or product retrieval changes yet.

R461-26 full Python3.12quality completed exit0:2555tests469.014s,18existing
skips;43architecturetests27.230s;7importcontractskept;799typedfilesPASS.
Native WinPS5.1targeted109PASS and controlled PID4predicate overlayRED retained.
See windows_iphelper_local_verification.json for tested-file/log hashes. Local
verification is not live qualification; new source freeze and15-second live
verification remain outstanding.

R461-26 source freeze committed08a7948356a47eea2379925cacd5d38df5881a15
and integrated fast-forward without disturbing pending evidence. R461-27
concrete security/architecture review approves exact identity batching and
unchanged complete projections. Native WinPS5.1GREEN161checks; original08
association readerRED at 'one query covers all owned rules ports'. Full
Python3.12quality on byte-matched separate Linux checkout passed exit0:
2555tests129.767s/18existing skips;43architecturetests3.329s;7contracts;
799typedfiles. See windows_firewall_batch_local_verification.json.
New combined source freeze and actual15-second live verification still pending.


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

Independent Issue Completion Auditor reviewed the actual timeout record and
latest six-file evidence continuation: R461-28 LOCAL_VERIFIED / LIVE_BLOCKED;
#461 INCOMPLETE/UNQUALIFIED. Redaction and scoped cleanup/Windows preservation
claims accepted; no Linux authentication or native after-hash proof exists.


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

Final independent Issue Completion Auditor delta review accepted redaction,
actual sudo-timeout provenance and PREPARED_NOT_EXECUTED guard status. Decision
INCOMPLETE; R461-28 LIVE_BLOCKED. No Apply/adoption/release qualification supported.
# SSH continuation, 2026-10-17 Europe/Berlin

Executed results and source/command/exit details:
[ssh_qualification_20261017.json](ssh_qualification_20261017.json).
Initial preparation preflight/dry-run: 2/2 on both targets (old source checkpoint).
After explicit locked archival: native 1/1 (active LXD), WSL 2/2 (Python needed).
All four read-only invocations per target preserved their measured source,
selected host configuration and user bootstrap scopes; no unreadable entries.
WSL `sudo -v && ./prepare_linux.sh`: 2, with Python prepared and Incus READY,
network blocked on exposure mismatch. Independent venv import probe: 0.
Listener-family observation: 0; ports 80/443 appear only in IPv6 listing.
These are existing-host partial observations, never fresh/rerun/recovery PASS.
No product changes; full local gate not repeated for this evidence-only update.
Prior full-quality results remain historical. Post-Apply host preservation was
not measured and is not inferred from the earlier read-only snapshots.

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

## Scope-amendment verification — 2026-10-17

Documentation/evidence-only amendment: `git diff --check` PASS; current JSON
parses successfully. Full product quality and live tests were not rerun because
source, tests, configuration and runtime behavior did not change. The prior
2,631-test gate applies to the unchanged product candidate, not a new test run.

## Publication verification — 2026-10-17

The initial mounted-checkout publication gate ran 2,631 tests with 18 existing
skips and failed two installer cases with ENOSPC plus one source-proof copy
with ENOMEM. `/tmp` was a nearly full RAM filesystem (9.4GiB used of 9.8GiB);
those failed observations are retained. This is not a timeout repair or a
product-source change.

The same three cases passed unchanged with a task-private disk-backed TMPDIR
(3 tests, 66.888 seconds). Full quality was then rerun in a clean detached
Linux-filesystem worktree of exact product candidate `d2fd89be`, using the same
Python3.14.4 interpreter/dependencies and a disk-backed TMPDIR: **exit0 PASS**,
2,631 tests in 257.069 seconds, 18 existing skips, 43 architecture tests,
seven import contracts, 808 typed files. Root product/test/configuration bytes
match that candidate. No assertion, timeout or guard was changed. Final changes
are documentation/evidence only; their whitespace and JSON checks pass.

Retained private log SHA256 identities:
- `quality.log`: `c1e4bdf4b3063b2d0241e2f085f653bcb12e0d8b9500e5d20c9daaec42f502ec`
- `quality-mounted-failed.log`: `cd9e976c61d6c6451d7ceab38177b7e5ea63b464197e692ffff3b056ccec03a8`
- `targeted.log`: `74c910cb9cb6b8d45db7055f14b82c34cad9b3639fc93d36b23a6fdf587a531f`
