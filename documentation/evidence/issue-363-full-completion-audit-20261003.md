# ARCH-03.20 / issue 363: full completion audit

> Historical evidence from the 2026-10-03 campaign. Intermediate or pending
> decisions below retain their original scope and are superseded for whole-issue
> completion by the [final validation report](issue-363-final-validation-20261003.md).
> Publication does not rerun or qualify the current repository revision.

Decision: **INCOMPLETE**. This audit checks the complete issue rather than only
the successful WSL fresh-install and two local quality-fix follow-ups.

Authoritative issue: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/363
Read on 2026-10-03. GitHub state is CLOSED / NOT_PLANNED; the closure comment
explicitly declares incomplete acceptance. The original body requires three
target environments, nine lifecycle operations and six acceptance criteria.

| Issue acceptance criterion | Result and evidence |
|---|---|
| Relevant unit/integration/E2E/live tests pass | PARTIAL. Quality-fix worktree: 2374 local tests pass, 18 existing skips. WSL baseline and post-reconcile each25live+7API pass without skips. Required later lifecycle executions are missing. |
| Classic profile remains operational | Baseline VERIFIED on WSL;18continuous services at desired replicas and authenticated checks pass. Native existing baseline passes. Full lifecycle qualification remains partial. |
| WSL2/native supported flows operational | PARTIAL. WSLrestart/update/recovery absent. Native older full lifecycle passes need source/configuration applicability assessment against final candidate. |
| Secret bootstrap and CLI contracts compatible | PARTIAL. Fresh WSLInfisical/configuredadmin/auth and localCLI regressions pass; supported live update/recovery transitions remain unverified. Runtime status snapshots and platformverify executed; dedicated platformstatusCLI not recorded. |
| Invalidated RC1/live evidence rerun | OPEN. Septemberc921/8eb scenario matrices exist, but complete refactor impact→retained evidence or rerun mapping is absent. |
| Failures truthful | VERIFIED for reviewed records. Historical failures/blocked/partial results remain intact; later successful runs are separately scoped. |

## What is already proven

Fresh WSL on clean1bd3dafd passes install,bootstrap,deploy,runtime status,
reconcile and scoped reset cleanup. Empty managed inventory was observed and
three new node UUIDs recorded. Reconcile preserves those identities and usable
credentials. Both authenticated runs passed25tests+7API, including9browser
tests, with zero failures/errors/skips. The Infisical failure in older records
is not the current fresh-install result.

Older native evidence records14successful lifecycle operations, separate
Jenkins service restart, update/recovery, destroy and managed-state reinstall.
Those passes are retained for their recorded candidate. Latest native fresh
functional installation passes, but its formal acceptance remains LIVE_PARTIAL
because the source contained an uncommitted RAM-floor patch. Later commits do
not retroactively convert that result. The clean78e3aa04 retest authenticated
existing services but setup was blocked by the old20GiB floor; main1bd3dafd
contains the later15GiB correction.

The two local findings are fixed and independently PASS on
fix/issue-363-quality-findings. That worktree is based on1bd3dafd with
uncommitted test/registry changes; sharedmain1bd3dafd does not yet contain them.
This audit does not publish, integrate or rerun those changes.

## Exact remaining work

1. Run WSL supported restart, distinct image update and controlled recovery,
   verifying identities/readiness/authentication and preserving unrelated state.
2. Assess native historical source/configuration equivalence against an identified
   final candidate. Rerun affected scenarios; retain unaffected evidence only
   with an explicit documented validity assessment.
3. Map historical RC1/live scenarios to refactor impact and current evidence.
   Execute every invalidated scenario, including host restart and Windows access
   checks where applicable; do not assume old acceptance still applies.
4. Integrate the two verified local quality fixes into the final candidate and
   record final verification with consistent source provenance.

A factory-clean operating-system host is **not** an additional acceptance
criterion in issue363. Managed fresh installation is valid for its declared
scope. Fresh reset already demonstrates scoped cleanup; it does not prove the
separate destroyCLI contract. Missing executions establish an evidence gap,
not a newly demonstrated product defect.

## Evidence and independent review

The new audit package is `.tiny-swarm/evidence/issue-363-completion-audit-20261003/`
in the isolated audit worktree. It contains the complete requirement matrix,
source/results inventory, acceptance checklist and independent INCOMPLETE verdict.
Historical `.tiny-swarm/evidence/issue-363/` and SeptemberRC1issue298/299/300
packages were reviewed alongside the newer native installation report, freshWSL
worktree and quality-fix evidence. Completion reviewer and separate WSL/native
specialists performed read-only review. No live mutations, GitHub state changes
or new test runs were performed during this audit.
