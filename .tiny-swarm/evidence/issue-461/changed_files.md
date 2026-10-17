# Changed files

## Current operator-accepted scope — 2026-10-17

The operator explicitly deferred the remaining live hardening scenarios due to
test-setup limits. The amended scope is the evidenced existing-host repairs,
qualification and operator guidance. See the authoritative requirement mapping
in [the current requirement scope](requirement_matrix.md#current-operator-accepted-scope--2026-10-17).
These deferred scenarios no longer block this agreed delivery; their unverified
results and residual risks remain. Earlier whole-campaign BLOCKED/INCOMPLETE
statements below are historical and do not describe the amended scope. No
fresh-host, full fault-matrix or global release qualification is claimed.


Evidence scope is `.tiny-swarm/evidence/issue-461/`:
requirement_matrix.md, qualification_matrix.md, implementation_summary.md,
changed_files.md, test_results.md, remaining_risks.md, acceptance_checklist.md.
commit_readiness.md records local source-freeze readiness.
completion_audit.md records the independent read-only review.
Additional scope: requirements.lock, narrow urllib3 security remediation for
AC4; tools/windows/preparation/Adapters.ps1, tests/windows/prepare-windows.Tests.ps1 and documentation/user_guide/windows-preparation.md for R461-22. The existing workflow and product Python/configuration are unchanged. Historical results are retained and clearly separated from current observations. Ignored local VM scripts/images/logs/credentials are not commit content.

Portable redacted live observations: native_preflight_result.json and
native_python_result.json. No raw remote logs or credentials are included.

windows_image_result.json records the actual successful image/boot steps and
RAM-guarded stop; guest boot/checkpoint was unverified at that historical attempt; later Windows
OS-only boot and checkpoint restoration are now verified.

windows_resume_result.json and windows_image_diagnostic.json preserve the
failed resume attempt and read-only owned-image observations.

windows_provision_only_result.json records actual 24-GiB first boot and the
checkpoint ACL failure, with private error paths excluded.

Continuation records: windows_checkpoint_attempt.json,
windows_checkpoint_inventory.json, windows_guest_dry_run_unbound.json,
windows_guest_dry_run_source_bound.json, windows_pre_wsl_restore_result.json.
Historical failed attempts and actual successful environment checks remain
separate; private helper scripts and credentials are excluded.

windows_feature_elevation_result.json records the actual host elevation failure
and absence of guest feature execution.

R461-22 live blocker remediation: tools/windows/preparation/Adapters.ps1 uses explicit PowerShell NullString for the existing atomic state replacement; tests/windows/prepare-windows.Tests.ps1 adds real create/replace IO regression with isolated mocked ACL boundaries; documentation/user_guide/windows-preparation.md explains retained pending evidence after persistence failure. No source qualification guard or atomic-write requirement is relaxed. New portable evidence includes feature apply, partial inspection, recovery reboot and disposable writer diagnosis.

Corrected local freeze bce63aaf contains the reviewed adapter/regression/guide changes and five redacted actual records. Subsequent evidence-only continuation records preserved manual Ubuntu installation, corrected committed source/archive proof, real-ACL disposable writer success, and the storage ACL blocker. New portable records windows_revised_plan_result.json/windows_resource_acl_diagnostic.json contain no private paths, usernames, raw SIDs or credentials.

Additional R461-23 scope: tools/windows/preparation/ResourceAdapters.ps1;
tests/windows/resource-files.Tests.ps1; existing capacity ADR dated amendment;
windows-preparation.md clarification. Protected local portable PowerShell and VM
checkpoint helpers are ignored/private, never committed.

R461-24 freeze: two runtime resource helpers, three targeted regression files,
existing capacity ADR/user guide and issue461 evidence. Redacted live result JSONs
retain source806 resource application/refusal, operator checkpoint actual restore,
metadata plan, physical/usable diagnosis and owned Ubuntu24/26 provisioning.
No private helpers, VM images, credentials, local paths or generated runtime cache
are staged. Existing completed workflow remains unchanged.

Read-only commit reviewer contract: READY for local source freeze only. Scope:
all staged files classify as issue461 runtime/tests/docs/evidence; no unrelated
change. Full quality PASS and final targeted PASS; final bytes match, diff-check
clean. Independent architecture/security/completion review approves correction;
issue acceptance/live reruns remain OPEN. Message derived from staged correction:
fix(bootstrap): distinguish physical and usable WSL memory. No publication.

Evidence continuation adds redacted nativeef7 preservation/route baseline,
Windows host capacity, actual26/28GiB resize/start and guest reachability,
sourceef7 preflight/dry-run, and canceled recovery elevation records.
Runtime source remains frozenef7; no product thresholds or host settings changed.

R461-25 local freeze scope: one explicit decoded-hosts string cast in
tools/windows/tws-wsl-bridge.ps1, real-file regression in
tests/windows/bridge-preparation.Tests.ps1, Windows preparation guide and
redacted issue461 evidence continuation. Timeout/ownership/ACL/credential
boundaries unchanged. Raw bridge traces/transcripts/helpers remain private.

R461-28 source freeze8d05 includes the reviewed process/Incus/network adapters,
three scoped regression files, process architecture, two existing decision
amendments, user guide and three portable verification JSON records. The later
authentication-only retry adds linux_sudo_login_session_wsl_probe_result.json
and updates aggregate evidence. All VM launcher/staging helpers, archives, raw
results and credentials remain private/ignored. No preparation Apply or new
product change accompanies the actual task timeout.

Observed authentication/desktop diagnostic continuation adds portable
linux_sudo_login_session_wsl_observed_probe_result.json and
linux_sudo_login_session_desktop_observation_result.json. Only ignored private
fixture helpers changed; frozen product8d05 and its full-quality evidence are
unchanged. New helper Python/bash/WindowsPowerShell syntax checks passed; no
product behavior change justifies repeating the full gate.

Future guarded authentication fixture plan adds
linux_sudo_login_session_observed_probe_plan.json; all new helper/API validation
assets remain ignored/private and unexecuted on the guest. No product source
change or new live qualification is included.
# SSH continuation, 2026-10-17 Europe/Berlin

Added `ssh_qualification_20261017.json`; updated the seven aggregate evidence
documents with distinct-target versions, actual commands/exits, authorization,
checkpoint archival and native LXD/WSL listener blockers. Existing pending evidence
was preserved. No product source, tests or committed configuration changed.


## Three-Amigos remediation, 2026-10-17

Product: domain/native_preparation.py and network_preparation/configuration.py,
inventory.py, trusted_process.py. Tests: test_network_preparation.py,
test_prepare_linux.py and new test_network_process_identity.py. Documentation:
existing network ADR, README.md, installation.adoc, network-preparation.md,
troubleshooting.adoc, Windows bridge README and new manual-host-steps.md.
Evidence: aggregate continuation plus new three_amigos_remediation_20261017.md
and three_amigos_verification_20261017.json. Earlier SSH observation is preserved.
No dependency, runtime configuration, host trust-store or publication change.
Existing pending user evidence was retained; no commit/push was performed.

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

Full issue remains INCOMPLETE; missing fresh/24.04 targets and open group, address,
resource-boundary, unrelated-resource and full CLI fault scopes remain explicit.
Independent final audit is required; no release is qualified or issue DONE claimed.

## Operator scope clarification — 2026-10-17

Ubuntu24.04 is not a required live target for #461; Ubuntu26.04 is the current
LTS qualification target. This supersedes the original dual-release live-target
expectation. Ubuntu24.04 remains supported but explicitly UNQUALIFIED for live
use; that status alone does not block #461. Fresh Ubuntu26.04 hosts on both
native and WSL2 families remain required and unavailable. Other open scenarios
remain unchanged.
