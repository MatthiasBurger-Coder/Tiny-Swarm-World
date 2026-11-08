# Native R3 inventory accounting and own-recovery correction

Base: 1e9a65a9; isolated worker branch. Historical real R3 artifacts remain unchanged.
Root reports 119 commands,151822 stdout bytes, preserved cleanup and subsequent full
RECOVERED proof. Qualification stopped INCUS_INVENTORY_UNREADABLE; initial finally
recovery stopped SNAP_WRAPPER_PROC_INVALID immediately after its owned daemon start.
Worker performs no hosts, tests, project imports, quality gates or commits.

## Requirement/design matrix (Root approved before source edits)

| Contract | Bounded implementation | Evidence to author |
|---|---|---|
| Complete fresh foreign graph before EVERY effect | Keep every command/read/checkpoint/ownership/preservation predicate. Account unique read-scope+JSON structural slots, not repeated visits to identical fields. | Real before-write fixture pipeline with realistic ~9461-byte foreign full metadata; repeated list/detail reads, task profile writes and cleanup. |
| Existing10000 entity cap and5000 cleanup reserve | In-RAM set keyed by exact allowlisted canonical argv (including project/object) and typed JSON key/index path. Each dict container,key,value,list/container/array position has a distinct slot. New fields/positions consume budget; scalar changes never skip validation. Both command() and default-profile direct reads use the same scope. No raw response/content hash or slot data is emitted. | Same-scope repeats reuse cardinality; new scopes/projects/objects/fields/array positions debit; over-limit refuses; cleanup retains its exact reserve. |
| Bounded repeated structural work | Each JSON observation independently ≤10000 structural nodes and maximum depth32 before accounting; existing perresponse2MiB, aggregate16MiB (8MiB active qualification),256 commands (146 active; see atomic transport amendment),300s (240 active) remain unchanged. Full bytes/commands/time charged EVERY read. | Large response/repeated metadata still charged on each read; depth/node/bytes/command/time exhaustion fail closed; no malformed JSON/secret logging regression. |
| No startup proof relaxation | Only the existing post-owned-start, recovering=true wait_ready window may retry SNAP_WRAPPER_PROC_INVALID as an unknown read-only observation. Existing25s proof deadline+5s cleanup remains. Each attempt repeats complete installed/source/Incus/package/process/root-API proof; only a full pass returns. | PROC_INVALID→fullpass succeeds, persistent invalid reaches timeout with no node effect, installed/source/Incus/API drift stays immediately fatal, timer restored and commands never retried. |
| Recovery reserve does not authorize qualification | Approval schema2 requires exact operation execute/recover. CLI supplies expected operation at both pre-lock/under-lock checks. Execute keeps1740s minimum; recover uses existing600s own-recovery reserve; maximum1800s unchanged. |600..1739s recovery accepted; same GO execute denied, operation mismatch/schema1/expired/malformed refused before effects; existing binding/hash/reviews stay strict. |

Slot accounting is a resource bound, NOT ownership/freshness evidence. Reordering
or changing a scalar cannot reuse a previous observation as proof: the complete
current response still passes every existing parser and preservation check. Array
positions are structural positions, not inferred entity IDs. Keys/positions remain
RAM-only under existing bounded outputs; no credential/configuration payload or
content digest is newly persisted. Standalone project capture resets its own
accounting epoch as before; live fixture accounting resets once at attempt start,
never before an effect or during cleanup. Existing capture typed-row accounting
continues to debit the same numeric resource limit; no graph validator is removed.

The existing recursive scalar counter conflates repeated parsing work with unique
metadata cardinality. R3 is far below byte/command bounds; raising10000 or dropping
foreign rows would hide the error rather than model it. The replacement uses one
bounded traversal per response; atomically check the complete prospective new-slot
count before updating counters/set. Failed over-limit reads cannot create partial
accepted budget state. JSON depth/node checks precede any write decision.

The startup error is never treated as successful or trustworthy. Delaying failure
for at most25s in this already admitted read-only wait does not add an effect or
permit package/source identity drift. The provenance helper itself is unchanged.
Explicit recovery approvals cannot be replayed as execute even with a long expiry;
internal finally recovery remains authorized by its original executed transaction.

## Locks and normative integration

Only tools/linux/qualification/incus_profile_listener_fixture.py,
tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py,
tools/linux/qualification/native_lxd_maintenance.py,
tests/tools/test_native_lxd_maintenance.py and this record are worker-owned here.
Root owns corresponding workflow/context/ADR amendment, source pins, exact review,
PC verification and any later fresh live authorization. Required normative change:
10000/5000 are unique observed structural-slot cardinality limits; perresponse10000
node/depth32 plus unchanged bytes/commands/time bound repeated work. Approval schema2
has an operation discriminator and separate600 recover/1740 execute validity floor.
No old qualification, approval, artifact or failure record becomes PASS retroactively.

Implementation release: Root message approved this exact direction and authorized
source/tests after this record. Independent exact candidate review precedes tests/
effects under Root orchestration. AST/diff-only worker verification will be recorded.


## Atomic fixture transport and exact native cost amendment (Root approved)

Pinned Incus6.0.5 PRIMARY CLI contracts:
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incus/profile.go : create reads non-TTY stdin into api.ProfilePut before CreateProfile.
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incus/create.go : init aliases create without launch; -c/--config accepts key=value at initial creation.
Root separately observed the installed6.0.5 help documenting profile create with redirected configuration; this worker made no host query.

Create the full GO-derived base config/root/NIC and full run-marked proxy profile
atomically instead of separate profile set/device add effects. JSON is valid YAML
for the pinned CLI. Canonical body has exactly config/devices, existing typed
allowlists, at most64KiB; an anonymous RAM memfd is populated before spawn and
supplied explicitly as stdin. No blocking parent-to-child pipe write, ambient stdin,
body logging or new file persistence. The child output reader retains bounded
selectors, deadline, kill/reap. Init receives the run marker via -c. Uncertain
create reconciliation accepts only the exact full intended body/name/project and
empty consumers; collisions/foreign state remain refused. Existing interrupted
cleanup-prefix guards are retained; no adoption, force or deletion broadening.

Every actual effect still performs the complete fresh graph/default/listener/route
checkpoint. A genuine read-only instance query no longer invokes a write checkpoint;
it remains guarded/allowlisted/read fully. The pre-start no-listener predicate uses
the same fresh ss observation taken by that start's own checkpoint. Two digest-only
metadata observations reuse already checked bytes rather than execute new ss reads.
Both independent final listener reads and the final complete graph remain.

Native observed-shape command model: three projects, three original owner profiles,
two inherited views, one full foreign instance list+detail (synthetic test payload
>9461bytes), plus the temporary two profiles/one instance. Baseline graph G=12 reads;
with created resources its maximum is G+3=15. Authored transport regression exercises
real counters/parsers/checkpoints and every full foreign read (no command/inventory
mock), with subprocess transport replaced by bounded in-memory pipes only.

| Phase | Commands (static exact model; execution pending) |
|---|---:|
| JIT including initial full graph |25|
| First complete profile create/check/readback |17|
| Second complete profile create/check/readback |18|
| Pre-init checks, guarded init and stopped readback |23|
| Before-start proof, guarded start and full after-start proof |28|
| Guarded exec, nonce HTTP, final live listener+full graph |35|
| Active peak |146|
| Owned cleanup stop/delete/profile deletes, absence and full checkpoint |93|
| Main final two listener reads and complete graph |14|
| Complete total |253|

Thus reserve110 leaves146 active and covers107 remaining modeled cleanup/final
commands, within unchanged256. Static sums, not a test result. For this native
shape active=7G+62, cleanup/final=6G+35, total=13G+97. No cap is raised or spent quota
reclaimed; a larger/drifting inventory can still refuse rather than promise that
any arbitrary shape fits. Full fresh observations, unknown ownership and limits
remain authoritative. Windows snapshots incur their existing extra costs and are
not claimed to satisfy this native arithmetic.

Generic effects/host observations now enforce the same command/byte/time budgets
immediately and use the existing bounded output transport with explicit DEVNULL
stdin, rather than discovering overrun only at a subsequent inventory read. The
per-read limits, aggregate16MiB/300s and reserved8MiB/60s remain unchanged.

Authored regressions include full successful phase accounting and fresh graph before
all9effects; all4cleanup transport failures preserve exact owned remainders without
force/retry; active-budget refusal before create and after verified create; ambiguous
atomic create acknowledgements; repeated large foreign rows charge bytes/commands
but only unique slots; new project/object/key/index debit; malformed/deep/oversized
current responses; canonical RAM-only input; schema2 execute/recover distinction;
full-proof readiness retry/timeout with permanent drift unchanged.

Worker static verification only: AST parsing and git diff --check. Project tests,
typecheck, quality and host actions are NOT_RUN by worker. Exact final review and
Root PC gates are required before any later fresh live attempt. Historical R3
failure and successful recovery records remain unchanged.


## Shared Windows snapshot asset integration (additional Root source-pin decision)

Root approved the fixed shared pure PowerShell asset
`tools/windows/qualification/windows_firewall_snapshot.ps1`, owned exclusively by
preflight worker. This stream edits only its consumers; it does not write the asset,
Windows controller or Adapters.ps1. Fixture GO now requires windows_snapshot_sha256
on BOTH hosts. Static native fixture intents inherit that mandatory field and must
validate its exact bytes before maintenance; old GO/intent shapes cannot qualify the
new source. Native FILES appends the asset without shifting prior index positions.

The consumer opens only the fixed ROOT-relative path, checks all asset ancestors
plain, uses O_NOFOLLOW/CLOEXEC plus fstat/length/identity/time stability and a64KiB
bound, strict UTF8/noBOM/NUL, then verifies the approved SHA. Snapshot invocation
executes the loaded body as the existing fixed PowerShell -Command, without sourcing,
imports, arbitrary paths or ambient stdin. Each live snapshot receives the GO SHA
explicitly; read-only route capture remains clean-source-bound without a live GO.
The exact separate pre-existing Windows IPv4 identity query stays allowlisted.
Unknown PowerShell command shapes refuse before spawn.

Source/test work remains mutable until preflight supplies its stable asset bytes
and exact DTO-v2 contract. Root owns the corresponding v1.x workflow/context/ADR
and source-pin amendment, assembled candidate and actual bounded Windows evidence.
No claimed Windows snapshot success or readiness follows from this source work.


## Full-list observation amendment (additional explicit Root code GO)

The preceding atomic-only253-command native estimate is superseded for the final
candidate by complete list DTO reuse. The analogous WSL two-project/four-existing-
instance model would have required293 commands with redundant per-object GETs;
therefore the atomic-only design is not sufficient for WSL. No cap is raised.

Pinned PRIMARY transport chain:
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incus/profile.go : filtered profile list renders the full api.Profile collection as JSON.
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/client/incus_profiles.go : the collection request uses recursion=1.
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incus/list.go : JSON renders api.InstanceFull rows, either fetched full or composed from Instance plus state/snapshots; no instance name filter is supplied here.
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/api/instance.go : local config/devices/profiles are fields; expanded maps use omitempty.

Only the fixture route-checkpoint reader reuses these fully typed current list
rows. Every complete project collection and project detail remains read, canonical
owner profile sets are read once from their actual profile scope, and all foreign
instances/local+expanded metadata remain in each fresh JSON observation. Known-field
sets/config maps/devices/profile names/status/types/optional metadata are validated;
names-only rows, null maps and unknown DTO fields refuse. No fallback GET repairs
an incomplete row. A missing expanded map is admitted only when the corresponding
local map AND every actually resolved referenced profile map are observed empty;
unknown profiles/nonempty inputs refuse. No expansion is reconstructed. Direct
queries for the own default/base/task profile, own instance run/profile binding,
stopped/running/effective proof, uncertain create and cleanup remain unchanged.
JIT also requires actual client6.0.5, matching the source-specific list contract.
Default is observed before inherited profile users even if supplied last.

Authored native full-counter transport case now asserts106 active/180 total;
WSL case models two projects with three existing default nodes and one existing
Issue447 manager, four independent large full rows, and asserts107 active/181 total.
WSL additionally performs13 fresh complete shared-firewall observations plus13 exact
PortProxy reads; all9effects retain a new complete graph and appropriate Windows
comparison. Entity/byte/command caps and elapsed monotonic budget remain unchanged.
The Windows elapsed-time feasibility is NOT established by synthetic transports;
Root must measure actual full getter cost for the complete count before live GO.

## Full firewall certificate transport amendment (additional explicit Root code GO)

The shared asset still emits the entire canonical DTO-v2 JSON from complete current
ActiveStore getters. Fixture's fixed, source-pinned PowerShell wrapper executes the
exact SHA-bound shared source, accepts exactly one pipeline string, strict UTF8 and
at most14680064 full bytes, validates closed root/layout/identity/count structure,
and hashes that ENTIRE string inside Windows RAM. It emits only one closed JSON
certificate. No filter/config/address/SID/ACL data crosses into fixture evidence.
The producer guards duplicate native/adapted/map names before serialization; the
wrapper does not claim WinPS5 ConvertFromJson independently detects duplicate JSON
keys. Source-bound typed producer+serializer is part of this observation contract.

Certificate exact fields: schema_version='tsw.windows-firewall-certificate.v1',
query_sha256, snapshot_sha256, snapshot_bytes, snapshot_schema_version=2,
store='ActiveStore', association_model='PROVIDER_IDENTITY_ONE_TO_ONE', counts.
Counts have exactly rules/profiles/settings and the7filter kinds; bounds8192/16/128
respectively, each filter8192 and equal to rule count. Hashes are lowercase64hex;
all numeric fields are exact ints (booleans refused). Query SHA must equal fresh
fixed asset bytes and the live GO. No time/host/raw values are included. This is a
source-bound read observation, not an independent authentication of a host.

The fixed wrapper validates source SHA before execution and uses no arbitrary
path/import/sourcing. Query bytes are encoded into the exact wrapper argument;
a conservative30000UTF16-unit Windows commandline bound refuses before spawn.
Certificate stdout and stderr retain the existing2MiB-per-stream transport caps,
8MiB active/16MiB aggregate, and240s active/300s total. Certificate stderr refuses;
PortProxy remains a separately captured complete exact byte sequence. Every prior
snapshot checkpoint still runs the FULL actual getter, no cached digest/sampling.
Canonical certificate+PortProxy forms the comparison payload; metadata records full
snapshot digest/bytes/querySHA/counts, never a raw-state export.

Authored synthetic WindowsPowerShell tests execute only a local constant query,
not firewall cmdlets: exact full-string hash/size, changed opaque canary retained in
hash but absent output, invalid schema/layout/identity/multiple outputs/fixed error
redaction, closed Python certificate reader and commandline refusal. Tests skip
explicitly where the Windows transport is unavailable; only Root runs them on the
authorized WSL host. Actual source asset size/runtime remain preflight-worker/Root
responsibility. Shared asset source is an additional Root-owned input, not one of
this worker's five edited files.


## New-instance receipt amendment (explicit Root source GO; no host create)

Static inspection found the previous marker-only cleanup rejected real daemon
volatile/image metadata and lacked a UUID receipt. Existing R3 never reached init;
this is a newly found delivery boundary, not evidence that any prior host object
was owned. Root explicitly authorized this necessary correction before a new pause.

Pinned PRIMARY sources:
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/instance/instance_utils.go : CreateInternal assigns random UUID, sets generation EQUAL to that new UUID, and separately generates cloud-init.instance-id for nonsnapshots. Current raw lines730–734/759–760 (web rendering682–686/709–710). The new-create equality is not inferred from old host values.
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/instance.go : instanceCreateFromImage copies exact image properties as image.KEY and binds BaseImage to the image fingerprint.
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/instance/drivers/driver_lxc.go : setup idmap, initial empty last_state map, current/last map updates, UUID fallback, template consumption, power/ready stop state and generated NIC metadata.
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/instance/drivers/driver_common.go : running power, finite NUMA nodes, volatile deletion semantics.
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/device/nic_bridged.go : generated host veth and removal of host_name after stop.
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/idmap/entry.go : exact Isuid/Isgid boolean and Hostid/Nsid/Maprange int64 JSON fields.

JIT retains the complete typed properties from its fixed approved image-fingerprint
GET in RAM. All instance image.KEY fields must equal that exact map, no additional
image prefix keys. base_image equals the GO fingerprint. Immediate stopped init
readback requires atomic run marker, exact name/project/container/profiles/local
empty devices/full intended expanded config+devices and canonical UUIDv4 values.
UUID+generation(new-create equal) and independent cloud UUID bind once; identity
changes never rebind. The receipt is used by every subsequent own readback, expanded
verification, uncertain-init reconciliation and cleanup before destructive effects.
Only UUID/receipt digests are added to evidence; raw UUID/MAC/idmap/properties stay RAM.
No new commands or image/snapshot/node adoption are introduced.

Closed15 volatile keys: base_image, uuid, uuid.generation,
cloud-init.instance-id; idmap.base/current/next, last_state.idmap;
last_state.power/ready, apply_template; eth0.hwaddr/name/host_name; cpu.nodes.
All are exact strings with bounded typed formats. NIC keys require the actual
intended eth0; generated MAC uses pinned10:66:6a prefix, explicit name eth0 and host
veth namespace. ID maps have bounded16-entry exact field sets, booleans/exact
positive-range int64s; map-next/base and every stable observed field are preserved.
Initial empty last_state/current may move forward only to the observed next map,
never regress. New stable generated fields can appear only during start prefixes,
not by an unrelated pre-start/stopped observation. Unknown metadata refuses.

Phases: init accepts stopped power absent/STOPPED, readiness absent/false and
apply_template absent/create. Successful running requires RUNNING and consumed
create template; current/last maps equal observed next, intended NIC has generated
MAC/one bound veth. Stopping permits known running/stopped prefixes; successful
stopped requires STOPPED, readiness absent/false and host_name removed. Only finite
starting/stopping prefixes are admissible after an uncertain effect; unchanged
UUID/image/marker/fullspec remain mandatory. No force deletion of unknown state.

Root separately queried only an EXISTING stopped Ubuntu Incus instance and reported
key/format classes (UUID/MAC/SHA/idmap/decimal/STOPPED), no raw values. This supports
that old marker-only guard was insufficient; it is not an Alpine3.21 init result,
new-instance equality proof, ownership proof or qualification. Synthetic full native/
WSL DTO transports now include real image properties, UUIDs, MAC, idmap and lifecycle
transitions. Authored regressions cover wrong/changed UUID, image/unknown metadata,
invalid maps/MAC/NUMA/power, lost init acknowledgement, and cleanup identity drift
retaining unknown resources without stop/delete. Root must run tests then separately
review a fresh actual fixture before any capability entry.

Final shared source input supplied by preflight owner: asset9754bytes, SHA256
7f06807a54bce7b447d0da6eaf9c4a77b5cc53c865a525b46dea6b425d554e2b.
It fits the encoded wrapper argument bound; worker did not edit/copy the asset.
Actual optimized full-getter runtime/size remains unverified here.


## Frozen worker handoff

Five edited paths only. AST parsing of the four Python sources/tests and
`git diff --check` PASS; no project imports/execution, host commands, tests, gates or
commits by worker. Test/typecheck/live status NOT_RUN here. Root must independently
review this exact candidate, overlay the separately frozen shared asset unchanged,
amend normative source/query/approval/certificate/receipt semantics and pins, then
run authorized PC checks before considering a new live maintenance window.

Source/test SHA256 at this handoff:
- tools/linux/qualification/incus_profile_listener_fixture.py: 0ee81463520886674af259814746bcd4cecb0da6a2a998ddd80e332cfb55f004
- tools/linux/qualification/native_lxd_maintenance.py: 1815e2466083a001f8a71399594e11db6b4a4cc54500a2deacacd14bd9045461
- tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py: 370a7738dca3ee3aec4d2bd19210a1810a2370853f99473161a92d26998013ff
- tests/tools/test_native_lxd_maintenance.py: 378fa1fa666173879e88228d8cc1fafe891f78582e1e612c3d837d446dc1fc18


## Root PC R4 failure and test-only correction

Root's exact184-test focused run failed1 assertion/3 errors (17.177s).
Byte-identical local log SHA256 f474c9a89b91981e3f8f3d41f219f3f491cb1b8d5c183012385543ee37c75dc9
was read in full; old result remains FAIL. No worker tests/hosts/commits.
Production sources and maintenance tests remain byte-identical to the original
frozen five-pin candidate; only fixture tests and this record changed.

Corrections: use actual aggregate-byte constant; mock native Popen transport instead
of obsolete subprocess.run seam so no fake executable launches; initial listener
drift occurs on the first fresh checkpoint read (the redundant digest-only read
was removed); expected instance route profile is qa-profile, matching the modeled
full list DTO and owner scope, instead of the obsolete default-profile expectation.
Production validation, route normalization and cleanup policy are unchanged.

Updated fixture-test SHA256 5b41fa149d74ef5c6972961e1aa9765b7cc502a88a064ef79c060d3ac72564b9. AST and diff checks only.
Retest/quality status pending Root. Shared-asset getter correction separately
changed external source SHA to c6cda38ff012ff3d688d529f2f92087977d42a297ce34e03190774d9991943fe
(11222bytes); earlier7f input pin remains historical only. The fixture dynamically
binds the fresh required GO/intent asset SHA; no production hardcoded SHA changed.

## Independent boundedness review correction (Root-authorized source-only)

Independent review identified two adjacent production boundary defects before live
qualification: the Incus inventory reader used a new per-process timeout without
clipping it to the remaining active/cleanup aggregate window, and an external
readiness SIGALRM exception could bypass the collector Runner's owned-process
kill/reap. Both are corrected without changing any command, stream, byte, entity,
approval, or effect allowance. A read at an exhausted aggregate deadline is now
refused before spawn; an in-flight reader uses the minimum process/aggregate deadline.
Runner now kill/reaps its owned process and rethrows external exceptions unchanged.

New fake-port regressions cover active240/cleanup300 deadline clipping, no subsequent
spawn, external alarm and interrupt cleanup, and actual Runner traversal from the
maintenance readiness timer callback. These tests are authored, NOT_RUN by reviewer.
The Receipt's derived profile has an explicit nested-map type; validated string maps
now return a freshly typed mapping used by the Receipt. No casts, ignores, metadata
relaxation or acceptance assertion changes were added for the reported PC typing errors.

All historical PC attempts and records remain applicable only to their exact prior
bytes. This amended candidate requires fresh Root source review and PC verification.
No tests, host actions, commits, or live qualification were performed by this author.
The separate real Windows c6cd getter observation failed FIREWALL_DATA_UNREADABLE;
this source amendment does not qualify or weaken that producer.

### PC bounded-candidate type refinement

Root's R6 nearest325 tests passed. Typecheck retained one inference failure at
allowed_power[phase] (log e0a7838f2419bf6d96c2ebb543e2c30f2bf17e8bb8957bb37858032b4a26fa3d).
Annotate that unchanged literal as dict[str,set[str|None]]; runtime AST expression
and all allowed lifecycle values remain identical. No ignore/cast/guard change.
New R7 verification remains pending.
