# EPIC 440 / S449-02F — parent-bound storage snapshot leaves

State: DESIGN_REVIEW_REQUIRED; no implementation or qualification claim.
Baseline `e8961e99cacdde655ac03dff3ca78af48307a513`; isolated worktree
`/home/micro/tsw440-snapshot-inventory`, branch
`fix/epic440-snapshot-inventory-20261107`. Only this record is written.
Future three locks: collector `tools/linux/qualification/native_runtime_inventory.py`,
`tests/tools/test_native_runtime_inventory.py`, this record. Root owns v1.48,
independent exact-plan/normative review, code release, integration and PC gates.

Actual normal capture stopped STORAGE_SNAPSHOT_OR_SELECTOR_UNSUPPORTED with no
artifact. A separately approved bounded shape diagnostic observed a relative
subpath name at volume DTO validation, ordinary known volume fields, count 1295;
last command was incus_storage_volume_show exit 0. That last command does not
prove whether the failing row was detail or the next cached list item. No raw
name, snapshot type, ownership, or live completeness is established by it.
Schema4 PC success (901-file typecheck, 306 focused, all seven gates, 3302 discovery)
is baseline evidence only.

| ID | Requirement/current gap | Proposed implementation and evidence | State |
| --- | --- | --- | --- |
| S01 | Real flat snapshot rows currently denied | Exact parent/leaf partition, typed actual-owner DTO, validated parent closure; family real-flow fixtures | OPEN |
| S02 | Leaf detail differs from parent DTO | Fixed snapshot GET/strict six-field DTO/raw common-map equality; path/shape/drift denials | OPEN |
| S03 | Snapshot references differ from current users | Separate finite leaf reference kinds; global pool reciprocity, no active producer expansion | OPEN |
| S04 | Project volume membership is family-specific | LXD all owned parent types; Incus owned custom parents only; neither includes children | OPEN |
| S05 | Independent retained leaf proof | Schema5 typed leaf identity/metadata and parent/edge reader checks; tampering tests | OPEN |
| S06 | Preserve read-only bounded authority | Same provenance/root/owner/graph/limits, exact query admission review and PC regression | OPEN |

## Pinned primary semantics

Both daemon volume-list implementations return flat StorageVolume records,
including names parent/snapshot from the underlying all-volume view. The CLI
renders those existing API records; snapshot rows are not a CLI invention.
List rows keep original type, actual Project, location, config and used_by;
LXD also requires Pool, Incus forbids that DTO key under the existing contract.
[Incus daemon list](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/storage_volumes.go),
[LXD daemon list](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/storage_volumes.go),
[Incus CLI](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incus/storage_volume.go),
[LXD CLI](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxc/storage_volume.go).

Dedicated snapshot GET takes pool/type/parent/leaf and resolves effective storage
project. It returns leaf name, description, config, content_type, created_at and
expires_at; it does NOT return owner, pool, type, location or consumers. The
expiry pointer permits explicit null; no generic null coercion follows. Snapshot
list has different population details and is unnecessary for this bounded model.
[Incus handler](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/storage_volumes_snapshot.go),
[LXD handler](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/storage_volumes_snapshot.go),
[Incus snapshot DTO](https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/api/storage_pool_volume_snapshot.go),
[LXD snapshot DTO](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/shared/api/storage_pool_volume_snapshot.go).

Both pool UsedBy DB helpers read storage_volumes_all (parents UNION children),
and internal helpers construct root-child instance-snapshot URLs and custom-child
storage-volume-snapshot URLs. RETURNED API edges differ: Incus URLToEntityType
recognizes both snapshot entity types, but project.FilterUsedBy excludes both in
its finite switch. Both pool handlers AND flat volume used_by population apply
this filter. Thus returned Incus pools omit all child edges, and returned Incus
root-child used_by is empty. LXD generic entity permission filtering supports
snapshot types; its returned root-child used_by is the owning instance-snapshot
singleton, and pools include root/custom child URLs. No collector may erase an
unexpected supplied relation to mimic protocol filtering or fabricate a missing
Incus consumer. Custom child consumers remain observed empty under the retained
bare-source/no-selector subset in both families.
[Incus pool helper](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/storage/storage.go),
[LXD pool helper](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/storage/storage.go),
[Incus all-volume DB](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/db/storage_volumes.go),
[LXD all-volume DB](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/db/storage_volumes.go),
[Incus pool API](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/storage_pools.go),
[LXD pool API](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/storage_pools.go),
[Incus entity parser](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/db/cluster/entities.go),
[Incus returned-edge filter](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/project/permissions.go),
[LXD returned-edge filter](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/project/permissions.go),
[Incus volume UsedBy](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/storage_volumes_utils.go),
[LXD volume UsedBy](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/storage_volumes_utils.go).
Earlier internal-helper-only conclusions claiming both returned families expose
child edges were superseded by this independently traced parser/filter chain.
This resolves the source-level failure-order consistency concern without claiming
additional live facts or changing the observed diagnostic classification.

Necessary adjacent correction: Project.used_by is not family-equivalent. Incus
GetStorageVolumeURIs calls GetCustomVolumesInProject and includes only owned
CUSTOM PARENT rows. LXD entity query includes owned PARENT rows of every volume
type. Both query base storage_volumes, excluding snapshot children. Prior shared
root-volume Project expectations were incorrect; live root bijection and global
pool edges remain necessary and unchanged.
[Incus project volume query](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/db/storage_volumes.go),
[LXD project entity query](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/db/cluster/entity_type_storage_volume.go).
Both independent reviewers explicitly verified this correction; it requires new
normative approval rather than being treated as evidence that prior logic passed.

## Proposed exact contract

1. Partition each existing complete flat list into parent rows (one validated
   name component) and leaf rows (EXACTLY two validated components parent/leaf).
   Existing NAME grammar applies independently; deny empty, dot, third segment,
   percent/encoded slash, URI, traversal and option-like shapes before new spawn.
   Validate each row's existing family DTO allowlist/types, mandatory actual
   owner==query, LXD exact pool, supported type/content/location and consumers.
   Never reinterpret an active disk source or selector as snapshot admission.
2. Keep parent volumes and snapshot leaves separate. Resolve all parents before
   leaves regardless list order. Each leaf must have exactly one collected parent
   in the SAME pool/type/actual owner with matching content_type and exact raw
   supported location. Parent itself gets the unchanged real detail validation;
   root parent still has its live instance type/location/bijection checks. No
   synthetic parent, owner fallback, union or pruning. Duplicate (type,parent,leaf),
   orphan, wrong type/owner/pool/content/location or missing parent blocks.
3. Add only detail kind storage-snapshots, arity four (pool,type,parent,leaf),
   validated before provenance/spawn. Exact command:
   fixed family executable + --force-local query --request GET --raw
   /1.0/storage-pools/{pool}/volumes/{type}/{parent}/snapshots/{leaf}?project={owner}.
   Every component independently validated then encoded; no raw slash component,
   remote, target, arbitrary root/URI/method/arity or new environment authority.
   Command IDs lxd_storage_snapshot_show / incus_storage_snapshot_show; safe_args
   exactly [pool,type,parent,leaf,owner]. Existing strict seven-key envelope and
   duplicate-JSON checks apply. One new GET per observed leaf, no recursive list.
4. Detail requires exactly six fields: name (exact validated LEAF), description
   (string), config (bounded string map), content_type (existing supported enum),
   created_at (1–128 printable ASCII characters), expires_at (the same bounded
   string type or explicit null). These are typed observed timestamp metadata;
   no date arithmetic or temporal readiness claim is introduced.
   Compare complete config/description/content_type/created_at raw values against
   the flat leaf row in RAM, including field presence; require those common fields
   present. Never compare historical config with live-parent config. Expiry has
   no list counterpart: validate the observed detail field without inventing one.
   Detail has no owner/type/pool/location/used_by: bind these only through validated
   flat leaf + verified parent + exact query/provenance; never synthesize observed
   DTO fields. Historical config remains RAM-only; identity digest is not secrecy.
5. Admit finite reference kinds instance-snapshots (name parent/leaf) and
   storage-volume-snapshots (name pool/type/parent/leaf). Recognize ONLY their
   exact URL paths; omitted project means default, explicit project must be one
   valid value, target/extra query/fragment/remote remain denied. Preserve all
   distinct consumers; no repair by dropping, merging with active users, or
   assuming empty. LXD container/VM leaf used_by must equal exactly its owning
   instance-snapshot reference; Incus container/VM leaf used_by must be observed
   empty because of its pinned returned-edge filter. Custom leaf used_by must be
   observed empty under the existing supported bare-source/no-selector subset. Any daemon/unknown/
   external/nonmatching additional relation blocks.
6. Canonical global pools remain derived from complete equal project views.
   LXD expected pool users add each root leaf's instance-snapshot identity or
   custom leaf's storage-volume-snapshot identity exactly once. Incus expected
   pool users add NO child identity: the stored leaves remain explicit inventory
   despite absence of returned child edges. Supplied unexpected Incus child edges,
   missing LXD child edges, extras or wrong-project/root-vs-custom edges block.
   Do not add leaf users to current
   parent volume.used_by, current instances, current root bijection, profile/NIC
   producers, API-local or effective-expanded device graphs.
7. Parameterize storage graph family explicitly at capture and reader callsites.
   Project expected volume refs are owned PARENTS only: all admitted parent types
   for LXD, CUSTOM only for Incus. No snapshot Project users in either family.
   Existing owned profiles/instances/managed networks and all actual returned
   volume-owner rules remain. This correction changes Project reciprocity only;
   do not weaken root existence, pool equality, owner authority, or consumer checks.

## Schema5 and bounded claims

Per pool, retain existing volumes for parents and add snapshots, sorted uniquely
by (type,parent,name). Leaf fields exactly:
parent, name, type, content_type, owner_project, storage_location, created_at,
expires_at, metadata_digest, used_by. Parent/name are separate valid components;
owner/location/content bind to the existing parent. Digest is canonical JSON
SHA256 of the complete validated six-field detail with field presence, after RAM
common-metadata equality. created_at and expires_at remain typed observed values;
config/description are not serialized. Empty snapshots is mandatory for pools
without leaves. All leaves count toward the existing entity limit once through
flat list; each detail counts command/output/time limits normally.

Reader accepts schema5 only; old artifacts stay untouched. Independently enforce
exact keys/types/order/duplicates, parent closure/type/content/owner/location,
finite URL/ref identity, LXD-root-singleton versus Incus-root-empty and
custom-empty leaf consumers, canonical pool view equality including the exact
family-specific returned child-edge policy, family-specific Project parent
membership and exact one-to-one leaf command evidence: snapshot-show safe_args
multiset equals retained leaf keys, without missing/extra/duplicate commands;
each follows the matching parent-volume detail and lies inside existing guarded
version→initial→graph→final phases. It validates digest shape, not hidden raw
metadata. Root proof/CLI version/family authority remains unchanged.

For LXD, the instance-snapshot URL is an API-returned relation supported by
stored leaf detail and independently validated live-parent/root identity. Incus
returns no such relation; only the stored leaf's structural parent/type/owner
binding is established. Never serialize an inferred Incus relation as observed.
Neither family independently queries historical InstanceSnapshot DTOs or proves
historical profile/device/config safety. No hidden expansion reconstruction,
attachment engine, snapshot restore/delete or preservation-effect claim. Snapshot inventory
cannot authorize maintenance from historical device safety assumptions.

Unchanged unsupported boundaries: disk source.type/source.snapshot and subpath
selectors, images, buckets, clustered/member/target views, shared custom volume
inheritance and foreign actual owner. Existing schema4 profile inheritance,
network graphs, global pools, local/API versus expanded storage projections,
root admission twice per family, provenance and all fixed limits remain. No new
server query, executable or budget raise; max 2048 commands and existing aggregate
bytes/process/wall/entity bounds remain, so larger inventories can still block.

## Planned evidence and release

- Both-family real CLI-list/raw-detail fixtures: root container/VM and custom
  leaves, zero/multiple snapshots, parent after child, multi-project/default URL
  scope, LXD root-child singleton/pool child URLs versus Incus empty child
  used_by/no pool child URLs, parent metadata differs legitimately from historical
  child, expiry string/null. Exact command/arity/typed components/provenance and one GET per leaf.
- Actual main writer refusal for orphan/duplicate/owner/pool/type/content/location
  mismatch, malformed name/DTO/expiry, missing/wrong detail leaf, common-map drift
  with constant mocked digest, malformed/error/duplicate raw envelope, unknown
  consumer, missing LXD/extra Incus/wrong-scope pool leaf edges and forbidden
  Project child.
- Family Project regression: Incus root-only Project has no root-volume refs;
  owned custom parent included; LXD all parent refs included; both exclude leaf
  refs. Existing root and volume actual-owner denials remain meaningful.
- Independent schema5 tampering: reject schema4, missing snapshots, duplicate/
  unsorted leaf, forged parent/owner/type/location/content, metadata digest shape,
  expiry type, missing/wrong LXD root relation, extra Incus root relation,
  nonempty custom consumers, canonical
  pool drift, family Project mismatch and malformed/out-of-phase command args.
- Canary historical config/description must not occur in success bytes/records
  or fixed errors; final root/provenance/budget failure yields no artifact. Existing
  active selector/subpath denials remain, with snapshot-positive fixtures alongside.

No implementation until BOTH independent exact-plan and root v1.48 normative /
query-scope approval. Worker then edits three locks only; no tests, hosts or
commits. Root runs exact-byte PC typecheck, focused suite and all seven gates,
then separately reviews a committed read-only capture. All new evidence NOT_RUN.
Estimate: 1–2 engineer-days implementation plus 0.5–1 review/PC verification;
medium confidence, excluding unsupported selectors/resource changes.

## Approved implementation handoff — 2026-11-07

The DESIGN_REVIEW_REQUIRED statements above preserve the historical proposal.
Root released code after BOTH independent exact-plan approvals of
`00e5317fa446f27dbc87e0e880ad6c909083c9bc60e641a21f5ab018103d0ee6`
and corrected v1.48 normative/query approval: workflow
`ddad7a9047c37b91a011b8e8effa2a34613de4dcaf44e8ef43a48b08a6d6d96f`,
F4 `93e59a39`, context MD `9931463a`, context JSON `6f095f95`.
Status: IMPLEMENTED_PENDING_EXACT_CANDIDATE_REVIEW_AND_PC_VERIFICATION.

S01–S05 are implemented in the two declared source/test locks. Capture validates
all listed actual owners and parent identities, fetches real parent details before
leaf detail, compares historical common metadata directly in RAM, and retains
separate schema5 leaf records. Snapshot detail has exactly the six reviewed
fields; owner/type/location/consumer observations remain bound to the flat row
and validated parent/query, without fabricated DTO fields.

Returned Incus child consumers remain empty and its pool gains no child links;
LXD requires exact owning root-child singleton and pool root/custom child edges.
Family Project membership now admits Incus owned custom parents only versus LXD
all admitted owned parent types; neither includes child snapshots. Existing live
root identity/bijection, actual volume owner, canonical profile and network rules
remain. Current parent/API-local/effective-expanded producer graphs never gain
historical snapshot producers.

Reader independently checks leaf keys/types/order/parent closure, exact family
returned edges and Project semantics, and exact one-to-one leaf command evidence.
A complete first-pass parent command index rejects missing, failed, mistyped,
oversized or duplicated parent proofs even if the duplicate occurs after a leaf.
Matching successful parent detail must precede its leaf, within the unchanged
family admission phases. Capture validates the fixed leaf URI before its
provenance guard. Unsupported consumer kinds now give a fixed ownership refusal
in direct complete-ownership validation instead of an incidental lookup error.

Tests use literal family-specific flat-list and six-field raw-detail fixture
shapes. They cover container/VM/custom leaves, parent-after-child input, multiple
and zero leaves, default URL scope, exact family Project differences, malformed
owner/parent/type/location/content/pool/name/DTO/expiry, raw drift with constant
digest, raw envelope errors, missing/extra observed edges and writer refusal.
Independent schema5 mutations cover structural and command-evidence forgery,
including before/after duplicate parent proofs and malformed status/byte types.
Per-request guards, refusal before leaf query on proof drift, canary suppression
and final proof failure remain explicit. An old cross-family whole-row fixture
assertion now retains equality of every other field while asserting the exact
approved Project membership difference; old active selector/subpath denials stay.

Frozen candidate SHA256:

- collector: `1845064c42cf632154e5a2eb9492d0295e49daf3c3fe07b9a09620665f98cc46`
- tests: `cde493da88cee8bc281a81b31f1722aa381d93b6a91f3b92a77c13d5aba98f24`

Worker checks: AST syntax parse of both files PASS, without import/execution;
`git diff --check` PASS. All tests/typecheck/quality: NOT_RUN by worker. No host,
feature/profile/snapshot mutation, runtime action, capture, commit or publication.
S06 remains root's exact-byte PC typecheck/focused/all-seven-gate prerequisite,
followed by separately reviewed committed read-only capture. No budget increase,
new executable or query beyond one approved fixed GET per observed leaf.

No remaining contract uncertainty identified during worker static self-review.
Reader validates retained structural proof, not raw hidden digest contents,
historical instance DTOs/expansion or historical maintenance safety. Incus lacks
returned root-child consumer links by pinned protocol; its stored-leaf parent
binding must not be described as an observed historical-instance consumer edge.

### Static reviewer correction before integration

Tester identified a fixture-order defect in the LXD foreign-pool negative: its
malformed snapshot pool was applied before the generic family fixture injected
the correct pool, overwriting the negative evidence. The snapshot fixture now
reapplies only that explicit malformed pool after family field injection and
updates the returned command byte count. The existing real-main
VOLUME_POOL_IDENTITY_MISMATCH assertion remains unchanged and meaningful.
Collector behavior and approved contract are unchanged.

This supersedes the test hash above with
`5f8cb1f4f3627449af50437475098654e27855bd203627d8668ce7fd1359dcf9`;
collector remains
`1845064c42cf632154e5a2eb9492d0295e49daf3c3fe07b9a09620665f98cc46`.
AST syntax and diff checks PASS only; tests/hosts/commits still NOT_RUN. The
superseding exact test/record bytes require independent review before integration.

### PC r1 typecheck failure and typing-only candidate

Root reports PC WSL r1 matched all 21 exact asset pins, then typecheck failed
with four TEST-only errors: a tuple reused a previously inferred list local;
that list then reached the typed URI argument; a snapshot fixture reused a
previous Mock local; mixed detail-mutation dictionaries needed annotation.
Focused tests and full quality did not run in r1. This failed attempt remains
recorded; no gate success is inferred from static worker checks.

The candidate changes only distinct local names for component list, arity tuple
and detail Mock, plus an explicit tuple[dict[str, object], ...] annotation for
unchanged malformed detail values. Assertions, literals and runtime behavior
remain unchanged. Collector hash stays
`1845064c42cf632154e5a2eb9492d0295e49daf3c3fe07b9a09620665f98cc46`.
Superseding tests SHA256:
`3f88201c027cbac4a214eca1c6f8b6ad4a45d14eb6955fe7127bde46fd80cef7`.
Worker AST syntax and diff checks PASS only; no worker tests, hosts or commits.
Independent exact delta review and root's renewed PC gates remain required.

### PC r2 fixture omission failure and narrow correction

Root reports PC WSL r2 typecheck PASS across 901 files, followed by a 315-test
focused run in 21.492 s with one error; full quality NOT_RUN. Historical malformed
Project list evidence omitted used_by, but the new Incus fixture renderer indexed
that key before the production validator, raising KeyError. Root preserved the
private log SHA256
`964ef2cc67563ea5b3fda2ef3860f4405bd1230902d45b74c93495a7cfc32437`.
This focused failure is retained; r2 is not an acceptance gate PASS.

The fixture filter now runs only for a dictionary row whose used_by is present
and is a list of strings. Non-dictionary rows, absent or malformed evidence remain untouched for the real product validator;
no missing field or consumer is synthesized. Existing negative assertions and
collector source remain unchanged. Superseding tests SHA256:
`ed6ff1eb4c0170addc8e18cd8c3720a297c1475d4d3c1f4ead3ddba8dcd85793`.
AST syntax/diff checks PASS only. No worker tests, hosts or commits. Independent
exact delta review and root's renewed exact-byte PC gates remain required.


## Root integration and PC WSL schema5 verification checkpoint

This checkpoint supersedes the historical pending/NOT_RUN handoff above for
code verification only. Both independent architecture/security and
Tester/DevOps/S3D roles approved final collector
`1845064c42cf632154e5a2eb9492d0295e49daf3c3fe07b9a09620665f98cc46`,
tests `ed6ff1eb4c0170addc8e18cd8c3720a297c1475d4d3c1f4ead3ddba8dcd85793`
and handoff `3bad371c8d8ee44770836e66912a6a61c7ed3145c47182b2c6c040a4c8a2a75d`.
Root copied exact bytes and read source/reader and each subsequent test delta.
All 21 source/contract/workflow asset pins matched on PC WSL before tests.

Attempt r1 failed nearest typecheck on four test-only typing conflicts. Attempt
r2 passed typecheck but focused315 failed one fixture KeyError before the
retained malformed Project-row validator. Full quality did not run in either
attempt. Minimal independently reviewed fixture/type corrections preserve all
values/assertions and malformed evidence; neither changes collector source.
All failed logs, asset manifests and drivers remain private and distinct.

Attempt snapshot-inventory-r3: nearest typecheck PASS901; focused315 PASS in
19.516s; all seven QUALITY.md gates PASS; architecture43 in3.403s;
discovery3311 in186.730s, 36 skipped, controller exit0. Logs SHA256:
- typecheck `1463f11db62e949a63d76c98020d6f54c5de9a0541fe12f69281ffd795b9a7ef`
- focused `3f72eb60aa8fca67ae09a9afd0b51faae9fd65e6ea984796ea04a3e12c61bc0f`
- full `9ab4504d38e7d982a1ba85019edf9eaf74c41421cc10235ddffb48dbc803c2f0`

All logs were copied byte-identically to root private ext4 mode0600. Tested
asset manifest SHA256 `0272cfaa14fe2045eca2dc191d0de523e5c1e8c60b381a9aa91896c6d4feaf97`,
driver `350170957440b10cec5442d2efa52adfc4ee650c1bb1ddbb22f2484098e77cc6`.
Execution used normal umask022, isolated child HOME/PATH, stdin DEVNULL;
logs/exit records remain private0600. No tests ran locally or on native Linux.
Only evidence prose changed after this run; product/test/normative bytes remain
as pinned. Documentation-only diff check is required for the final checkpoint.

These are mocked code regressions, not live snapshot/ownership qualification.
Schema5 rejects older artifacts; no migration or historical expansion replay.
Incus returned leaf consumers remain absent, not synthesized; parent binding
must not imply independently queried historical instance safety. Active disk
snapshot selectors stay unsupported. A fresh committed-source driver/bundle/
14-pin review is required before ONE new native read-only capture. No snapshot,
profile, feature, instance, daemon/service, data or Windows-rule mutation;
fixture acceptance, runtime capability and Epic completion remain unreleased.
