# Native fixture state-query and causal readiness correction

Base7523f85b, isolated fix/epic440-native-state-query-20261108. Root reviewed and
released exact five locks: fixture+fixture test, maintenance+maintenance test,
this record. Source-only worker: no tests/hosts/commits.

Actual Native R5 reached three own objects, then Incus6.0.5 rejected instance
info --format json. Cleanup used the same unsupported command. Original LXD
nodes recovered Running, but three own Stopped resources remain; Root owns
separate constrained reconciliation. This patch does not alter the old host
checkout, delete those objects, or upgrade historical failure into success.

| Requirement | Exact implementation/regressions |
|---|---|
| Actual supported state transport | Read fixed existing /1.0/instances/{name}?project=default query; strict dict/name/default/container/status Running or Stopped, explicit internal mapping. No state fallback, str coercion or case folding. Remove obsolete instance info JSON admission. Test actual DTO and each identity/type/status denial. |
| Cleanup same strict transport | Existing lifecycle/whole-graph fixtures answer Instance API DTOs for init/running/stopped and cleanup. Remove impossible info responses; full-flow and failure cleanup regressions retain ownership/UUID/proxy checks. |
| Causal provenance retry only | Exact FILE/PROC/CHILD symbolic errors may retry only after own start. InventoryError requires direct __cause__ actual ProvenanceError with identical admitted code. Unchained or different class/code refuses. Test real _resolve_executable wrapping, then full binding success; negative source/cause/gate/timeout cases. |
| No widened authority | Shared parser/provenance/Runner unchanged, no generic retry, no state accepted from an exception. Same25+5 observation/600 recovery, fresh full proof each attempt, original binding mandatory. |

Root approved plan before source edits. No new effects, names/paths, source authority,
query budgets, image/alias handling or cleanup ownership exception is introduced.

## Source-only frozen handoff

State reads now execute only the canonical instance query and map exactly two
validated status literals. The generic command path also refuses instance info,
so removal from the read allowlist cannot accidentally dispatch it as an effect.
Existing receipt/UUID/spec/consumer checks around cleanup remain unchanged.
Lifecycle and full-graph fake transports no longer contain impossible status-only
info responses; their existing actual API DTOs drive all state observations.

Readiness separates MaintenanceError, InventoryError and ProvenanceError. The
three wrapper codes no longer pass a broad textual transient list. An inventory
wrapper requires its direct typed same-code cause and own-start authority in both
readiness and recovery-state observation. Other existing API/unit startup codes
retain their prior bounded treatment. A retry still needs a later complete actual
ready_binding/root-authority comparison before success, never exception-as-proof.

Authored regressions exercise actual inventory._resolve_executable chaining into
real NativePort.ready_binding, requiring the final root read and binding check;
raw string-only, wrong-cause/type/code and no-own-start errors refuse immediately.
Existing permanent causal-unknown timeout tests keep their25+5 bound and no effects.
New state tests cover API DTOs, all identity/status field denials, malformed JSON,
unsupported CLI refusal before spawn and actual full fixture cleanup after a lost
start. Existing full successful transport and each cleanup-failure regression now
use the real query shape rather than supporting an invalid CLI command.

AST parse and git diff --check PASS. All test execution, typecheck, quality gates,
host effects and commits NOT_RUN by worker. Root owns exact independent review,
PC gates, constrained reconciliation of old R5 objects and any new live attempt.

## Root verification of combined native corrections

PC SSH/WSL `epic440-native-r5-correction-20261108-r1`, base7523f85b with
exact native-state5 plus reader-cleanup2:348 focused tests PASS18.024s,
type978 PASS, all7 quality PASS,3626 tests/36 skipped/288.815s. Quality log
SHA256`d32db48eadfd55fd30840e96f5affce94523f7dd6040a1bf0f4ee32dc0b8fb92`.
Independent source reviewer preflight_review checked both exact candidates.
Real NativeR5 remains FAILED with own stopped fixture resources pending scoped
cleanup; original three LXD nodes were restarted. Do not reinterpret that run
as qualified or apply this code to its immutable checkout. Fresh S02 required.
