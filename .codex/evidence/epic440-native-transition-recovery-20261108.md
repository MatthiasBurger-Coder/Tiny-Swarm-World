# Native own-transition recovery correction — reviewed implementation

Base10aa0a57; isolated fix/epic440-native-transition-20261108. Locks only
native_lxd_maintenance.py, tests/tools/test_native_lxd_maintenance.py, this record.
No source/test edits before Root design release; no hosts/tests/commits by worker.

Root actual R4: own three stops and graceful shutdown occurred; strict service parser
refused the temporary deactivating state with UNIT_STATE_BLOCKED. Finally recovery
hit the same transition. Later strict inactive/dead observation was valid. After a
separately approved own start, provenance temporarily reported
SNAP_WRAPPER_FILE_UNVERIFIED; later complete original binding passed. No fixture
objects were created. Historical failures and Root recovery artifacts remain intact.

| Requirement | Exact bounded design | Tests to author |
|---|---|---|
| Pending service state is never authority | Keep shared _unit_state and NativePort.unit STRICT and unchanged. A private own-transition observer catches only InventoryError UNIT_STATE_BLOCKED as UNKNOWN, never inactive. A later strict stable state plus complete matching binding is required. Other schema/value/load/failed/unsupported errors remain fatal. | Real systemctl parser/Runner: deactivating→inactive; unknown forever timeout; malformed/failed/load drift immediate refusal. |
| Only admitted own transition waits | Native wait_inactive requires a baseline and own shutdown attempt. Recovery first observation uses durable shutdown/start-daemon intent flags from this private journal; no new effect/replay. Without own transition, keep immediate strict observation behavior. | No intent/no attempt rejects or keeps strict behavior; event schema/unknown intent/foreign node refuses. |
| Recovery can begin while shutdown settles | Add Port.recovery_state(transition_owned,start_owned), called after begin_recovery instead of the first direct unit(). Poll read-only stable environment+strict unit; inactive must pass full inactive binding, active must pass complete ready_binding/API authority before return. | Real Transaction+NativePort path never starts a daemon/node/fixture during pending observation; exact one start only after proven inactive. |
| Startup file uncertainty is bounded, never accepted | wait_ready catches provenance.ProvenanceError only for exact SNAP_WRAPPER_FILE_UNVERIFIED (plus existing exact transient codes). The special file retry is allowed only after this own start or a durable start-daemon intent from a prior uncertain recovery. Every retry repeats full installed/source/Incus/process/socket/root-API proof; matching original binding is mandatory to return. Known mismatches remain fatal. | Exact exception class→full success; permanent file unknown timeout; wrong class/code or installed/source/Incus/API drift immediate refusal; no action on unknown. |
| Existing budgets and cleanup hold | One private read-window context, no nested/existing alarm. Keep25s full proof/read deadline plus5s own child cleanup, within existing30s observation cap; keep600s recovery. Absolute monotonic deadline and SIGALRM bound all fresh Runner work, restore handler/timer in finally. Clip fixed read-only self.command timeout to window remainder; no effects allowed through that context. | Actual inventory.Runner client interrupted/killed/reaped; hanging bounded client; clipped last-read timeout; timer restored on success/failure/interrupt; no budget reset. |

Implementation details:
- Extract only the existing installed/Incus half of check_binding into a private
  stable-environment method, reused unchanged by check_binding and each pending poll.
  It checks installed file bindings and Incus unit/socket/executable authority before
  consulting a potentially transitioning LXD service. Shared parsers/provenance module
  are not edited or relaxed.
- Journal derives bounded validated transition intents from existing event records;
  no event format migration, new approval fields, blanket restart or journal rewrite.
  A start intent is an uncertain own attempt, never success. Protocol/FakePort/Events
  gain only this explicit observation/intent interface.
- Recovery active return performs full ready_binding even when a previous own start
  already made the daemon active, so nodes cannot race its process-view readiness.
- File unknown may originate at a package or process view. It remains UNKNOWN while
  waiting; only later full comparison of the original package/inode/hash bindings
  can succeed. A known INSTALLED_BINDING_DRIFT or API/Incus/source mismatch is never
  retried as file uncertainty.
- Existing inventory.Runner in10aa already kills/reaps on BaseException; retain it.
  Alarm interruption and bounded() finally cleanup must settle only the owned reader,
  never kill a daemon/process group selected by name. No force, broad kill, pause,
  shutdown replay or restart retry is added.
- Source-private NativePort read-window state admits only its fixed systemctl show
  metadata command. Effect methods remain outside the read window with original
  admission/deadline checks. Symbolic provenance failure codes may be journaled through
  the existing redaction policy; no raw paths/file contents/metadata are emitted.

Root must review/release this exact design before implementation. After source/tests
are frozen, Root owns independent exact review, PC verification and any fresh live
window. Passing retries in mocks is not actual recovery or qualification evidence.


## Released implementation and static handoff

Root reviewed original design SHA
b7c1c57fdd426010e507f62e717c56a0c964297e9790b40ba239300099a6633e
and released the three declared locks. Root explicitly clarified the retry class:
exact ProvenanceError FILE_UNVERIFIED, PROC_INVALID and CHILD_ABSENT symbolic
codes under the SAME own-start/durable-start gate, never arbitrary provenance
failures. Their full SNAP_WRAPPER_* spellings are closed in the implementation.
All retries must finish complete matching original binding; persistent unknown
never becomes readiness or authority for a subsequent effect.

Implemented private read windows for shutdown settlement, first recovery state and
post-start readiness. Durable journal events supply only attempted-transition
attribution. Shared unit/parser/Runner/provenance implementations are untouched.
UNIT_STATE_BLOCKED remains unknown (including any unsupported state represented by
that strict code), never a synthetic inactive row; malformed/schema/load/binding
errors retain their refusal. Every poll checks stable installed/Incus authority.
No shutdown/start replay, approval changes, force operation or new effect exists.
The fixed read-only stop-metadata command alone is clipped inside the window;
effect command timeouts outside it retain their existing admission semantics.

Authored regression coverage includes actual Runner + strict parser + synthetic
systemctl child observations, deterministic interruption of a genuinely blocked
owned child with kill/reap, real Transaction reconciliation before its one admitted
start, durable intent correlation, no-intent refusal, each allowed provenance code,
known-drift immediate refusal, persistent unknown timeout, clipped read timeout,
fixed-command effect denial, timer restoration and symbolic error redaction.
These synthetic children never invoke a host service or client.

Worker verification is limited to AST parsing and git diff --check. Test execution,
typecheck, quality gates, host operations and commits are NOT_RUN by worker. Root
owns exact candidate review, protocol integration into inherited ProductSuite ports,
PC verification and any separately approved actual recovery/qualification window.
Historical actual R4 qualification/recovery failures remain historical failures;
this source candidate makes no live success or capability claim.

## Root PC nearest fixture correction

R1 actual nearest336 tests stopped only on one redaction expectation (log
9c67eadfbd3d3c6109b9decdb2e4e0270b758705a2a55059d6be59883d066f5d).
Existing ProvenanceError constructor already normalizes unknown input to safe
SNAP_WRAPPER_FILE_UNVERIFIED. Assert that actual behavior, then explicitly mutate
the exception args to unsafe text and require UNCLASSIFIED_FAILURE_REDACTED.
Both redaction boundaries remain covered; production source unchanged. R2 gates
remain pending.
