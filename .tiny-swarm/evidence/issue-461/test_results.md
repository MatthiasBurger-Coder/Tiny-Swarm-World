# Test results

Frozen runtime candidate: `3da77f8908d598688ed46dd6eab74c5f32a7ac50`.
Initial baseline checks used Python 3.14.4; corrected-candidate quality used
supported Python 3.12.14. Initial failures and later successes are retained below.

- `PATH="$PWD/.venv/bin:$PATH" PYTHONPATH=src python3 -m unittest tests.test_bootstrap_recovery tests.test_install_handoff tests.test_ubuntu_bootstrap_integration tests.test_prepare_windows tests.test_security_gate`: PASS, exit 0, 35 tests in 27.226s, no skips reported. Log: `/tmp/issue-461-targeted.log` (local transient artifact).
- `PATH="$PWD/.venv/bin:$PATH" python3 tools/security_gate.py dependencies`: FAIL, exit 1. pip_audit found 3 known vulnerabilities in locked urllib3 2.7.0: PYSEC-2026-4175, PYSEC-2026-4176, PYSEC-2026-4177; tool-reported fix version 2.8.0. Log: `/tmp/issue-461-dependencies.log`. This initial failure was remediated below.
- `PATH="$PWD/.venv/bin:$PATH" python3 tools/quality_gate.py quality`: FAIL, exit 1: 2,554 tests in 644.359s, 18 skips, one subprocess timeout in `tests.test_install_script.TestInstallScript.test_install_uses_private_configured_evidence_root` (fixture deadline 10s on the mounted checkout). Policy, complexity, lint, 7 import contracts, 43 architecture tests and typecheck of 799 files passed. This used the existing Python 3.14.4 environment; it is not an exact clean final-candidate run. Log: `/tmp/issue-461-quality.log`.
- `git diff --check`: PASS at evidence preparation; repeat after finalization.

The focused suite preceded the first full gate. The corrected lock is being
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
scenarios still lack prerequisites; destructive WSL reset lacks separate consent.
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
