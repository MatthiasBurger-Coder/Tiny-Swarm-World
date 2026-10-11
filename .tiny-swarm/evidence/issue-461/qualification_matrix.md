# BOOT-W09 qualification campaign

Status: **BLOCKED**. Live qualification state: **LIVE_PREREQUISITE_MISSING**
for authorized native tests and the new Windows test environment. Explicit
destructive Ubuntu reset is now authorized only inside the owned secured VM. Execution remains pending.
Current corrected candidate: `806a58c36aabf8a95601f2bbfb2978e2d6ee2995` (metadata-only registered VHD observation, following checkpoint persistence fix at bce63aaf). Historical native/feature runs used `3da77f8908d598688ed46dd6eab74c5f32a7ac50` (integrated W07/W08 plus urllib3 security repair).
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
