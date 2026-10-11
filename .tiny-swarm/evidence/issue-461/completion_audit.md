# Independent issue completion audit

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
