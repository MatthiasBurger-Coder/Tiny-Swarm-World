# S449 native paused admission socket DTO correction

Base: `c4ca086a38131c26cb416243bfc70862f22103d4`.
Author scope: native maintenance controller, its existing test module, this record.
Root explicitly authorized implementation after finding the missing-field defect
before any native maintenance effects. The former execution review was withdrawn.
The read-only proposal from that source is historical, not an execution approval
for these new bytes. No host, fixture or capability pass is claimed here.

## Concrete defect and correction

`await_admission` incorrectly accessed `binding.incus_unit.listen`. That binding
is the actual `incus.service` DTO, which has no `listen` field. The validated
schema6 artifact separately retains the real `incus.socket` DTO in
`baseline.preserve.incus_units`. The previous source could therefore stop LXD and
then fail admission with a missing-key error rather than reach the fixture.
Root found this statically before executing maintenance; no such runtime outcome
is asserted.

The correction selects exactly one retained `incus.socket` observation, requires
the closed socket field set, loaded state, integer zero PID and the canonical
`incus_run` or `incus_var_lib` endpoint. There is no service-field or path fallback.
The surrounding artifact validator remains the authority for the complete unit
state DTO. `check_binding` now rereads the fixed `incus.socket` with the existing
collector protocol and compares its entire observed row to the saved row before
proceeding to the unchanged service/executable checks. `await_admission` derives
its version-query socket from that retained socket row. Preservation snapshots,
source/provenance checks, phase budgets, exact fixture admission and recovery
remain unchanged. This adds one fixed read-only unit observation at each binding
check; there is no new effect or endpoint scope.

## Authored meaningful regressions

The positive regression calls the actual `NativePort.await_admission` through the
resource capture, version query, route capture and activation branches. Its real
service-shaped DTO deliberately has no `listen`. Both canonical socket paths are
covered. Only fixed child/host observation and private IO boundaries are mocked;
actual binding checks and endpoint derivation run. Assertions bind the version
query's exact argv/socket, actual captured version facts, fixed child count and
three complete socket observations.

Separate negative regressions require refusal before client queries for missing,
duplicate, unloaded, noncanonical, wrong-type or extra-field socket observations,
and for full current-row drift even when its endpoint has not changed. Existing
transaction and preservation regressions remain intact.

## Validation and next gate

Author performed AST parsing of these two Python files and `git diff --check`.
No imports, tests, host commands, maintenance effects or commits were executed.
Root must independently review exact source/test pins, run PC typecheck, focused
and all required gates, then commit/stage clean accepted source. A new intent,
read-only proposal and fresh phase-specific approval are required; the old
proposal/approval cannot be reused. Final fixture approval still requires real
paused resource and route observations.

## Root independent source review and PC qualification

Root reviewed every source/test delta independently from author: socket sourceexactone/closedkeys/rootactualrow and live fullsocket equality before Incusservice/version, actualawait regression with servicewithoutListen and both realcanonicalpaths; missing/duplicate/unknown/currentdrift denied. PC596base+exact3pins typecheck912 PASS6ca7cbb714c8ee6306c9b6f7f100399a58d175e393946faebad1d47c31e4eda6; focused289 in6.141s PASS49ccc93f883f0a2b400f33e6bdd01f5bd4f33fa33cc57ffa820ec2d76e52451a; all7 QUALITY PASS3395 in198.742s/36skips, quality941ad894fa51fcc79c0aa442dda6c71306a1f7372046cf354877a8abad3cb4db. Logs remain PC privateext4. This record updated afterward only for actualresults. Prior c4proposal remains unexecuted/obsolete; fresh committedsource/intent/proposal required.
