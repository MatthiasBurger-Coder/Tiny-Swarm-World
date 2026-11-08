# New ORIGINAL runtime-window driver R3 — source proposal only

Original71d2/df30 and versioned92b4/a814 plus deployed/history files stay immutable.
No implementation is authorized by this document. Root reviews/releases exact
new driver/test/record paths and normative binding before code; Root owns tests,
host writes/effects, fresh proposal/GO and guest-switch fixed path/hash repin.
Suggested new deployment /root/tsw440-wsl-r5-20261108, never overwrite r2/r4.

## Actual diagnosis, causal limit

Root authorized ONE bounded read-only diagnosis of two actual immutable92b4
RealPort.snapshot calls. An observational Runner subclass returned original
commands/results unchanged; raw detail metadata remained RAM-only and was
released at exit. No stop/start/service/network/config/file writes occurred in
the guest. Both captures completed635 commands and produced exactly35 detail keys;
binding/graph/all four node identities and the ENTIRE snapshot were equal.
Snapshot SHA2ec4c27dcfb1fbf718dea9ace1566412f8b7a8905be5bfdc665b14185718ece9;
detail SHA8b87aa9a3593b1380f7059e1cb90d0d875e91015a72616283ab120deb18dc273.
The observed raw-normalized detail projections reproduced both driver hashes;
changed detail list was EMPTY. Safe local artifact SHA
9ce3a4491b4890697e9ccf76d0d3619364e251ab05c60c64a68dbe5a888af5d9.
The first oversized SSH encoded-command failed immediately at the Windows
transport; only the compressed identical RAM payload ran the two snapshots.

Therefore the historical baseline feb94982 versus current8b87 detail drift cause
is NOT proven to be used_by ordering, image ordering or any configuration change.
Old baseline persists only one aggregate detail digest; raw historical details
and per-detail hashes are unavailable. Do NOT claim that a guessed normalization
fixed that observed drift or accept old stale GO. Root's comparison independently
shows original binding/graph/all4UUID-inclusive identities/statuses unchanged.

## Independently proven source defects / proposed bounds

1. Raw Project.used_by has no lexical-order contract. Incus6.0.5
   cmd/incusd/api_project.go projectUsedBy223–295 appends resource families,
   then returns unsorted. Native schema6 already validates/canonicalizes the
   complete reference graph, but old runtime driver hashes raw known used_by
   sequence order. This is a contract defect independent of the unproven stale
   baseline cause. Normalize ONLY this known field on validated detail resource
   DTOs: list of bounded unique strings -> sorted COPY. Reject null/mixed/duplicate
   or over-limit references wherever the underlying required DTO forbids them;
   preserve explicitly absent fields. No generic list sort, profile-order sort,
   alias/addresses normalization, raw config omission or set union. Every supplied
   consumer remains in the hash and independent complete graph.
2. Old normalize_detail retains volatile.eth0.host_name in node/config identity,
   although pinned nic_bridged.go postStop997–1000 clears it. That would make an
   owned stop fail immutable identity equality. Start662–685 creates a veth name;
   a later start may rebind it. Do NOT drop all volatile metadata. Separate ONLY
   this exact known NIC runtime field into typed intent-bound evidence, retaining
   all other original persistent fields, MAC, idmaps, UUID/generation, image,
   profiles, local and expanded devices/config and all foreign metadata.

Primary sources:
https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/api_project.go
https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/device/nic_bridged.go
https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/instance/drivers/driver_lxc.go
No new status/volatile-default relaxation is proposed. Existing power/status-code,
autostart and read-only process/socket/source proof remains mandatory for ALL4
original nodes, including both workers originally Stopped.

## Typed baseline, runtime field and journal decisions

New baseline schema/source namespace, never decode old92b proposal as a new
baseline. Retain complete graph digest and stable per-node identity; additionally
retain bounded per-detail records (command identity, safe-argument identity hash,
full canonical normalized detail hash), not raw config/DTO/UUID values. This makes
future drift locatable without exporting private metadata. Reject absent/duplicate
records and require exact coverage of actual capture commands as old driver does.

For each of the four exact original nodes retain nic_runtime evidence separately:
exact NIC key eth0, present bool, host-name SHA256 or null, typed node status.
Admission proves eth0 is an actual validated expanded NIC; every other volatile
key stays in stable detail/config identity. Unknown extra NIC runtime fields are
not automatically exempted. Veth value, when admitted, is bounded exact veth
format from pinned producer; store only its hash. Running baseline managers require
its valid presence; originally Stopped workers require absence. Record the actual
stable MAC/UUID/profile/device identity through unchanged full stable digests.

Every compare is given EXPLICIT operation state derived from validated durable
stop/start intent+outcome for the exact node/proposal/source/UUID binding:
- Before any stop intent: all original runtime evidence exactly matches baseline.
- After own stop intent: only that exact target may settle Running with original
  host evidence OR Stopped with host field absent and strict STOPPED/false flags.
  Uncertain effect never causes another stop attempt.
- Stop-complete: same original stable spec/UUID, Stopped and no host field.
- After own start intent: only that exact stopped target may become Running with
  a new typed veth observation; no new raw config/device/UUID is allowed. Bind the
  observed veth SHA in a durable post-start observation before using it as future
  runtime evidence; later running observations require exact bound SHA. Unknown
  start outcome is inspected, never retried.
- Originally Stopped workers are NEVER given a start intent, stay Stopped with
  absent runtime veth and unchanged UUID/config throughout.

Stable normalization may omit only that exact typed, separately checked host
field after validation; it cannot make a changed runtime field invisible to the
operation-state validator. Initial/full unrelated foreign details remain exact.
Original restoration still starts only the two managers in existing reverse
order. Read-only quiescent/restored probes must validate the new exact journal
state and runtime evidence, not just reuse baseline stable digest equality.

## Required deterministic tests / implementation scope

New separate driver + matching fake test + source/evidence record. Preserve all14
existing fake tests, update their new schema explicitly, add realistic raw DTO and
actual observational Runner delivery tests. No fake hash-only nodes as sole proof.
Required cases:
- Complete stable used_by permutations produce identical detail hashes while all
  refs survive; duplicate/type/cap/extra-ref/config/description changes refuse.
- Exact raw Running -> owned stop -> Stopped -> own start -> Running DTOs, with
  host-veth absent then rebound; real persistent config/MAC/idmap/UUID/image and
  ordered profiles unchanged; source spec mutation refuses at every boundary.
- Host loss/change before intent, foreign node/worker host changes, malformed
  host, unexpected NIC key, wrong source/UUID/proposal journal, missing outcome,
  tampered post-start binding and unobserved/duplicated start all fail closed.
- Uncertain stop/start reconciliation retains exact before/after observations,
  no effect replay, no workers started, full graph/config refusal before effects.
- Per-detail coverage and error localization are bounded/hash-only; no raw
  UUID/MAC/config/cert/address output, even on failure.

Keep original driver child75s, invocation1800s/128 own command claims,
delegated captureRunner300s and settlement25+5. GuestSwitch outer650s remains
separate and unchanged. Keep two-manager scope, original UUID constants,
source/root/executable/socket/peer proof, private locks and finite GO validity. No budget raise, daemon/network/profile/package
write, permanent lease, adoption, old file edit or outside process kill.

Before any new original effects: exact source review, PC fake+new raw-transport
and quality checks, Root normative/path/hash binding and NEW actual prepare/GO.
Fresh preparation still requires old immutable original node/graph identity
applicability; it is not permission to accept unexplained persistent drift. The
historical pre-effect mismatch remains historical; cause claim stays UNPROVEN.

## Root bounded source authorization

Independent architecture approved this design with the explicit budget correction
above. New SOURCE is cb8c0e27c5890c39c03c45502423f2b8bf372ecc; ROOT is
/root/tsw440-wsl-r5-20261108. Reader pins84db3608/96213743/2b54f412 remain their
full existing exact hashes. New source-only authoring directory is
/tmp/epic440-original-runtime-r3: exactly epic440-wsl-runtime-window.py,
test_epic440_wsl_runtime_window.py and source-record.md. Preserve all old source
and deployed files. Root alone stages/tests/executes. GuestSwitch path/hash/source
repin is serialized with S-U1's current file owner after new exact source tests.

The old failed attempt has ONLY lock/proposal/go, no quiesce-started or stop intent.
It made ZERO original effects and is retired as a rejected stale read-only
precondition, never silently replayed. Current complete graph/binding and allfour
original UUID-inclusive stable identities/statuses match that old proposal; its
aggregate raw-detail difference remains unlocated/unproven. A NEW independently
reviewed Root GO may bind a fresh complete current preserve set in the new
namespace. This proves preservation from the new pre-effect observation; it does
NOT assert equality of unavailable historical raw details or a guessed cause.
No partial/uncertain-effect window may use this zero-effect retirement rule.
Every effect and recovery then uses only its own exact new baseline/receipts.
