# Independent issue completion audit

## Current operator-accepted scope — 2026-10-17

The operator explicitly deferred the remaining live hardening scenarios due to
test-setup limits. The amended scope is the evidenced existing-host repairs,
qualification and operator guidance. See the authoritative requirement mapping
in [the current requirement scope](requirement_matrix.md#current-operator-accepted-scope--2026-10-17).
These deferred scenarios no longer block this agreed delivery; their unverified
results and residual risks remain. Earlier whole-campaign BLOCKED/INCOMPLETE
statements below are historical and do not describe the amended scope. No
fresh-host, full fault-matrix or global release qualification is claimed.


Earlier reviews below are historical. Current verified Windows environment
progress is recorded in the latest section; no product qualification is implied.

Decision: **BLOCKED**.
Reviewer: Codex subagent `/root/issue_461_completion_audit`, read-only audit,
independent of the evidence author. Reviewed complete #461, parent #452,
AGENTS.md, QUALITY.md, completion/verification policy, requirement matrix,
seven evidence files and historical #363 validation.

Requirement perspective: R461-01–19 capture the issue scope. Exact versions and
all required live observations are open. BOOT-01–09 traceability was requested
and subsequently added to qualification_matrix.md.

Architecture perspective: evidence-only scope preserves the existing
hexagonal architecture and guarded provider/Windows boundaries. No unrelated
product or host changes were found. #363 retains actual historical sources and
managed-state freshness limits; no W09 qualification is inherited.

Test/evidence perspective: all six mandatory evidence files exist. Focused
local tests passed; dependency security failed. The full quality gate was
pending at independent review. Actual local results and the security blocker
were subsequently recorded consistently in test_results.md, R461-15, the
acceptance checklist and remaining risks.

Verified requirements: R461-11, R461-14, R461-17, R461-19 by static source,
history and scope review. Open/partial: all other rows, including AC1/AC2/AC4.
No TODO/scaffolding-only completion, hidden scope reduction or unrelated edits
were found. No live or external success claimed.

Missing explicit target/source/snapshot consent and required live executions
prevent PASS regardless of any later local regression result. Live state:
LIVE_CONSENT_MISSING. Do not mark DONE or qualify any release.

## Subsequent progress (author record; independent audit to be refreshed)

Operator authorized native tests and isolated Hyper-V construction. Version
inventory and owned VM shell creation succeeded. Narrow lock repair passes
strict audit and the complete Python 3.12 gate (2,554 tests, 18 skips). Native
freshness/restoration, Windows clean guest/WSL installation, required live scenarios remain open. VM RAM is now 32 GiB. The previously verified RAW disk is now the
owned installed GPT disk with four observed partitions; Windows image/boot files applied (exits 0/0); first boot is blocked on host RAM. Historical missing-consent/security
findings above describe the earlier review, not these later results.

## Refreshed independent review

Reviewer: `/root/issue_461_completion_audit`, read-only, after frozen source,
full corrected Python 3.12 quality, native actual partial observations and
Windows image application. Decision: **BLOCKED**. AC3 and AC4 are supported;
fresh installation, reruns, recovery, ordinary WSL preservation/explicit reset
and clean guest readiness remain unverified. Native preparation preserves
existing protected resources but blocks on bridge IPv6 policy.

Windows DISM/boot-file application passed (0/0), followed by a guarded RAM
refusal before credentials/boot. Static owned-VM resume safety review found no
remaining destructive-operation blocker; inherited prior command exits were
corrected to null until prior proof validates. The first resume attempt exited 1 before credentials/boot; its exact precheck
cause remains undiscriminated. Only the corrected resume and guest preflight
remain unexecuted. No release is qualified and #461 must remain open.

Final independent refresh found no new safety blocker in the corrected helper.
It retains the 34-GiB guard, validates the measured owned GPT layout and selects
the unique Windows data volume without repartitioning. Actual free RAM was
33.682 GiB. Overall decision remains BLOCKED; AC1/AC2 and clean guest readiness
are unverified. The final layout and failed resume are recorded separately from
historical RAW-disk evidence and the unexecuted corrected helper.

## Latest Windows environment continuation

Independent reviewer `/root/issue_461_completion_audit` reviewed the separate
24-GiB OS-only provisioning phase, checkpoint ACL repair, source-bound dry-run,
owned checkpoint restoration test and guarded 32-GiB feature-only apply helper.
No concrete safety blocker was found for their authorized owned-VM scope.
Actual first boot reached Windows, answer removal was verified, and the exact
pre-WSL checkpoint was restored and booted with clean invariants. Guest then
stopped and 32-GiB RAM was set/observed. Source-bound dry-run verified the frozen
SHA, with only partial S13 invariant coverage. Historical first-boot/RAM and
checkpoint/verification failures remain in portable records.

These results establish an isolated recoverable Windows environment, not WSL
or bootstrap qualification. Full-guest feature apply launch was canceled by Windows UAC (host exit 1);
the helper did not start and no guest apply result exists. All AC1/AC2 product scenarios remain
open and #461 remains BLOCKED. AC3/AC4 retain supported evidence. Final audit
must assess the actual feature/apply result if execution proceeds.

## Final independent decision after Windows continuation

Reviewer `/root/issue_461_completion_audit`: **BLOCKED**. Mandatory evidence
files exist; AC3/AC4 are supported. Actual Windows OS boot, source-bound dry-run
and exact pre-WSL checkpoint restoration are recorded without claiming bootstrap
qualification. Canceled UAC launch records host exit 1, no helper/guest apply
and null guest exit. No new safety or scope violation was found. Historical
wording was reconciled to the current Windows OS/GPT/checkpoint observations.
AC1/AC2 remain open; keep #461 open and every release UNQUALIFIED.

## Independent review of live checkpoint defect and correction

Reviewer /root/issue_461_completion_audit found no safety/architecture blocker in the narrow NullString fix and real create/replace regression. Reproduction under WindowsPowerShell5.1 confirms first pending creation succeeds, second replacement raises ArgumentException with ordinary $null, and explicit NullString replacement succeeds; canonical pending state remains unchanged. Recovery reboot was independently reviewed and actually verified. Original PARTIAL/4 result, pending checkpoint and failed full quality run remain evidence. Reviewer requires corrected full quality and new committed/archive source proof before further qualification; full quality retry now PASS. Overall BLOCKED: original AC1/AC2/native/24.04/reset/runtime scenarios remain open. Operator manual WSL/Ubuntu installation is preserved and recorded separately from candidate actions.

## Historical independent completion decision for source bce

Reviewer /root/issue_461_completion_audit: BLOCKED. Mandatory evidence exists; AC3/AC4 and R461-22 are supported. Frozen bce63aaf is source-verified; actual protected disposable create/replace writer succeeds. Resource inventory fails with untrusted_evidence_acl on additional explicit selected-VHD SID grants, leaving storage/effective resources unknown. Categorization does not establish the grants legitimacy or owner; a security/architecture decision is required before changing principal trust. AC1/AC2 remain open and all releases UNQUALIFIED. Manual Ubuntu installation/configuration and the original checkpoint are preserved; no automatic archive, ACL weakening or reset occurred. Stale current summaries were corrected and owned Enterprise Evaluation vs preserved local Pro/WSL targets separated in the release matrix. Stopping on this design blocker follows AGENTS.md; keep #461 open.

2026-10-11 independent System Architect and Completion Auditor accept the
specific metadata-only VHD correction on static security review. Actual disposable
Windows5.1/modern7 regressions pass and full local quality retry passes. This is
local change acceptance; overall AC1/AC2 remain open, all releases UNQUALIFIED.
A virtualized native Linux Hyper-V guest satisfies the Linux host-family contract
(actual non-WSL Linux kernel); physical-host observations remain separate.
Reset consent is now owned-VM-only, conditional on new verified restore point.

## Current sourceef7 independent completion review

Reviewer /root/issue_461_completion_audit verified corrected summaries after
actual28GiB continuation: **INCOMPLETE**. Sourceef7 local gates pass and
exact-source Preflight/DryRun preserve observed state but exit2 on measured
Windows capacity and prior-source canonical state. VHD trust correction and
original operator checkpoint restore are historical successful results, not
current blockers. Scoped VM-only reset consent exists, but the current28
checkpoint elevation was canceled; no new checkpoint or reset executed.
Independent guard review found no concrete scope blocker in the proposed
current snapshot/reset helpers, conditional on actual verified snapshot proof.
That prerequisite has not been achieved. Required live scenarios and AC1/AC2
remain open; every release remains UNQUALIFIED. No DONE, publication or issue
closure is authorized by these results.

## Current30 resource and reset-isolation audit

Independent reviewer /root/issue_461_completion_audit accepts actual30GiB
resource verification and scoped reset/recovery evidence. Exact current
checkpoint restore09:25:26 preceded terminate/unregister/empty inventory and
second recovery09:26:49. Recorded registration and identity/config/state/marker
hashes restored; primary WSL registration/config fingerprints unchanged.
Preservation is bounded to these observations, not every distro file.
R461-24 VERIFIED for resource case only. AC2 ordinary full-apply preservation
and remaining live scenarios remain open. Overall INCOMPLETE, no qualified
release, no product-install success. New bridge inventory timeout remains open.
# Three-Amigos remediation audit, 2026-10-17

Independent reviewer: `/root/remediation_completion_audit`, read-only, applying
the issue-completion-auditor contract. Decision: **BLOCKED** for whole issue #461.
Scoped R461-29–32 are verified within their declared boundaries: owned dual-stack
listener observation, exact namespace-bound mapped-root process identity,
actionable preserved LXD guard, and manual certificate/host/recovery guidance.

Reviewed 85 targeted passing tests and final full project-venv quality: 2,591
tests, 18 existing skips, 43 architecture tests, seven import contracts and 801
typed files. Twenty persisted product/documentation/log hashes match. The
persisted source-hashed read-only WSL counterprobe equals the original result:
two actual canonical listeners accepted, original parser rejects, eleven scoped
files unchanged. No committed-source installation qualification is inferred.

All six mandatory issue evidence files exist. No gate weakening, unrelated
runtime change or hidden scope reduction was found. Documentation and final
independent documentation review distinguish manual OS trust actions from product
automation and from unexecuted TLS/authentication results. The initial failed
system-interpreter gate and subsequent environment correction remain recorded.

Open: fresh-host installation, full rerun/recovery, post-install preservation,
routes/service authentication and native LXD coordination. Releases remain
UNQUALIFIED. See `three_amigos_remediation_20261017.md` and
`three_amigos_verification_20261017.json`; earlier audit sections remain historical.

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

## Independent final issue audit — 2026-10-17

Reviewer `/root/remediation_completion_audit`, independent read-only role;
decision **BLOCKED for whole #461**, scoped remediation and exercised existing-host
scenarios **VERIFIED**. Reviewed source d2fd89be, final2631/18skip local quality,
actual install/rerun, native host and selected WSL restarts, source-separated cold
root recovery, stage-only download/interruption/resume, S08 raw transaction and
postrestore HTTPS/API/data. No weakened checks, source-scope reduction or
uncommitted product/test/tooling changes were found. Native default-CA trust,
browser/Selenium, SonarQube, fresh OS or new reset success is not inferred.

The final S08 continuation above supersedes its earlier pending entry. The final
guide has **12** checked bash blocks; the earlier eleven-block record is historical.
All mandatory issue evidence files exist. Missing fresh Ubuntu26.04 targets and remaining
group, address, full CLI fault and per-release cases prevent DONE and release
qualification. The redacted current machine-readable rollup is
`combined_qualification_20261017.json:latest_campaign`.

## Operator scope clarification — 2026-10-17

The operator clarified that Ubuntu24.04 is not a required live target for #461;
Ubuntu26.04 is the current LTS qualification target. The original dual-release
expectation is superseded. Ubuntu24.04 remains supported but explicitly
UNQUALIFIED for live use and is not itself a #461 blocker. The prior independent
audit remains valid for its reviewed scope; this requirement amendment does not
resolve its other blockers, including fresh-host evidence on both families.

## Independent amended-scope completion audit — 2026-10-17

Reviewer `/root/remediation_completion_audit`, independent read-only review.
Decision: **PASS for the operator-amended scope only**. The explicit operator
acceptance removes the listed deferred live scenarios from the current delivery
criteria; their unexecuted and partial results remain unchanged. Historical
blocker statements are distinguished from current acceptance. Implemented
repairs, exercised existing-host scenarios and operator guidance satisfy the
amended delivery. Unchanged product candidate `d2fd89be` retains its recorded
2,631-test passing quality gate. Documentation-only amendment: `git diff --check`
PASS; no new live or product test run. No complete original-matrix, fresh-host
or global release qualification is established. Residual risks remain in the
requirement matrix and remaining_risks.md.
