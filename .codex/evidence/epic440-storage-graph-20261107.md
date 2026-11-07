# EPIC 440 / S449-02F — bounded global storage graph

State: DESIGN_REVIEW_REQUIRED. Baseline
`42ce5e00a6586992ec57910a49383c25053a3686`; isolated worktree
`/home/micro/tsw440-storage-graph`, branch `fix/epic440-storage-graph-20261107`.
Only this record is written. No source/tests/hosts/commits or live readiness.
Future locks: collector `tools/linux/qualification/native_runtime_inventory.py`,
`tests/tools/test_native_runtime_inventory.py`, this record. Root owns workflow
v1.46, independent exact-plan review/GO, integration and approved PC WSL gates.

Observed normal capture failed POOL_VOLUME_OWNERSHIP_MISMATCH without artifact.
That condition currently assumes pool.used_by contains every volume URL. This is
a collector contract error, not proof that observed resources are foreign.

| ID | Requirement and owner | Current gap | Planned change/evidence | Status |
| --- | --- | --- | --- | --- |
| S01 | Global pool identity, collector/reader | per-project pool assumption | canonical all-project metadata/users, hidden/drift denials | OPEN |
| S02 | Type-dependent Pool versus Project membership | root volume wrongly expected as pool volume URL | roots→instance; custom→volume; Project retains all owned volume URLs | OPEN |
| S03 | API versus effective consumers | current local/expanded union incorrect | raw-profile/local-instance API graph and separate expanded-instance graph | OPEN |
| S04 | Preserve actual returned volume ownership | no inherited-owner inference permitted | unchanged owner==query admission, typed feature boundary | OPEN |
| S05 | Authoritative noncluster scope | location tokens cannot prove this | two fixed typed server-root GETs per active family | OPEN |
| S06 | Independent retained graph | schema2 omits storage producer evidence | schema3 canonical pools, typed disk evidence and admission | OPEN |
| S07 | Fail closed unsupported edges | images/snapshots/buckets/member/daemon not modeled | explicit fixed blockers, preserve observations until rejection | OPEN |

All tests below are planned NOT_RUN. Earlier quality results do not qualify a
changed graph. Worker role passes are not independent approvals. Both reviewers
corrected their initial expanded-only API consumer advice after primary research;
this proposal uses the corrected raw/local API semantics.

## Primary contract

Both pinned Pool UsedBy implementations enumerate all projects without a project
filter: container/VM volumes become instance URLs (snapshot URLs when applicable),
custom volumes become volume URLs, images become project image URLs or orphan
volume URLs; buckets and raw-profile disk-pool users are also included.
[LXD storage.go](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/storage/storage.go),
[Incus storage.go](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/storage/storage.go)

Pool list/detail call that global function with memberSpecific false for current
untargeted requests. Project visibility can hide pools; such views cannot be
unioned into a supposed complete observation.
[LXD pool handlers](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/storage_pools.go),
[Incus pool handlers](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/storage_pools.go)

Returned custom volume used_by uses raw profiles and LOCAL instance devices
(expandDevices=false), not effective expanded attachments. Incus container/VM
returns its owning instance immediately. LXD container does likewise; VM passes
through daemon/local/profile matching then guarantees the owning VM. Under the
bounded selectors below, supported VM roots have only that owning instance.
[LXD volume consumers](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/storage_volumes_utils.go),
[Incus volume consumers](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/storage_volumes_utils.go)

Matchers resolve effective storage project and location; LXD supports source.type
and source.snapshot, whereas Incus splits source at '/'. The bounded common case
is a literal bare custom source, without selectors/subpaths.
[LXD matchers](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/storage/utils.go),
[Incus matchers](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/storage/utils.go)

Root volumes remain project-local; custom volumes map to default when the
storage-volume feature is false/absent; image volumes map to default. Project
UsedBy still contains owned volume URLs, including roots; its meaning differs
from Pool UsedBy.
[LXD project mapping](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/project/project.go),
[Incus project mapping](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/project/project.go),
[LXD owned volume URLs](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/db/cluster/entity_type_storage_volume.go),
[Incus Project UsedBy](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/api_project.go)

## 1. New fixed server admission (proposed query expansion)

- Per already-active queried family, invoke existing force-local prefix plus
  `query --request GET --raw /1.0` immediately after existing CLI version and again
  after all graph queries. IDs: `lxd_server_root_initial/final` and
  `incus_server_root_initial/final`. No inactive daemon query or activation.
- Before EVERY new GET run existing all-service/socket/executable/full-access
  provenance guard. Keep 2048 commands, 16MiB aggregate bytes, 2MiB per stream,
  30s process and 300s wall limits unchanged; rechecks count too. Up to four new
  GETs total plus their existing guard calls; budget exhaustion remains BLOCKED.
- Require existing exact seven-key sync-success envelope. Metadata must satisfy
  the full family-specific known Server/Environment DTO shape below. Admission:
  auth=trusted, public=false, api_version=1.0, api_status=stable,
  environment.server=lxd|incus matching family, project=default,
  server_clustered exact bool false. Wrong/missing/null authority denies before
  project graph queries with SERVER_ADMISSION_BLOCKED; malformed DTO gives
  SERVER_SCHEMA_INVALID. No user-config project fallback or arbitrary root URI.
- Compare initial/final stable admission projection only: auth/public/API fields,
  family/default project/server_version/cluster flag, plus LXD server_lts. Match
  CLI version by exact pinned rendering: Incus uses API server_version unchanged;
  LXD appends literal ` LTS` only when API server_lts is true. Never infer or
  strip another suffix. CLI remains persisted version authority. Changed admission gives
  SERVER_ADMISSION_DRIFT and no artifact. Ignore validated volatile metadata for
  comparison. server_pid is typed only; never equate it to wrapper MainPID.
- This is a bounded before/after proof, not atomic or continuous observation.
  Raw root config/certificates/addresses/auth user/server name stay in RAM only;
  errors are fixed codes. Location equality below is additive, not cluster proof.

DTO field policy, pinned [LXD server.go](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/shared/api/server.go)
and [Incus server.go](https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/api/server.go):

| Object | Exact common fields/types | LXD-only additions |
| --- | --- | --- |
| Server | strings api_status/api_version/auth/auth_user_name/auth_user_method; public bool; api_extensions/auth_methods string arrays; config object; environment object | client_certificate bool; optional access_entitlements string array |
| Environment | strings certificate/certificate_fingerprint/driver/driver_version/firewall/kernel/kernel_architecture/kernel_version/os_name/os_version/project/server/server_event_mode/server_name/server_version/storage/storage_version; server_clustered bool; server_pid exact nonnegative int; addresses/architectures string arrays; kernel_features/lxc_features string maps; storage_supported_drivers array of exact {Name:string,Version:string,Remote:bool} | backup_metadata_version_range uint32 array; instance_types string array; server_lts bool |

All non-omitempty scalar/object fields are required, never null. Unknown and
cross-family fields deny. Discarded Go nil metadata arrays and kernel/lxc maps
may be explicit null; authority/environment/config never are. Optional LXD
access_entitlements may be absent or a string array, not null. Array/map size
<=MAX_ENTITIES, keys <=256 chars, strings <=65536 UTF-8 bytes, total stream/budgets
unchanged; integer ranges checked without bool coercion. Incus config values are
strings; LXD config values are strings or exact True, never False/numbers/nested
objects/arrays/null. This narrower emitted union is backed by
[daemonConfigRender](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/daemon_config.go)
and [config.Map.Dump](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/config/map.go).
[WithEntitlements](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/shared/api/auth.go)
provides the one optional field. No generic nullable DTO relaxation. Version
cross-check is primary-backed by [LXD CLI rendering](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxc/version.go)
and [Incus CLI rendering](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incus/version.go);
API server_version remains bounded to the current CLI base-version token syntax.

## 2. Global pools and unchanged ownership admission

- Keep every existing per-project pool/volume query. Require identical pool name
  sets across ALL collected projects; no filtered/hidden/missing views, no union.
  For each pool compare list/detail and all views' complete validated known
  metadata (driver/config/description/status/locations, including field presence)
  and exact normalized used_by. Optional request-project echo is validated but
  excluded from global identity. Block POOL_GLOBAL_VIEW_MISMATCH on divergence.
- Retain a canonical family-global pool record from the first sorted project
  view and all project views; that deterministic source is not an owner. Compare
  complete metadata in RAM and retain its canonical JSON SHA256 metadata_digest
  for independent equality checks. Digest is comparison, not confidentiality.
- Pool expected users = raw-profile disk-pool refs + owner instance URLs derived
  from all container/VM volumes + custom volume URLs across all projects. An
  instance's custom attachment in pool B does NOT add a Pool B instance URL when
  its root resides in A. Exact complete equality remains; no dropped users.
- Project expected used_by remains profiles/instances/managed-owned networks and
  ALL actual owned volume URLs including container/VM roots. Pools remain global,
  not Project consumers. Retain actual Project used_by in schema3 to recheck it.
- Existing volume DTO/family Pool identity, mandatory returned Project and
  owner==queried-project admission remain unchanged. Never relabel a returned
  default custom volume as request-project-owned. Existing mismatch blocker stays.
- Normalize features.storage.volumes as exact true/false/absent (bool|null in
  output), deny malformed values. Default is special. Nondefault false/absence
  with custom rows/refs gives STORAGE_SHARED_CUSTOM_UNSUPPORTED; root-only own
  volumes remain supported. Existing profile inheritance/network restrictions
  and network schema2 semantics remain unchanged.

## 3. Three storage projections, finite supported selectors

- Raw-profile disks create pool users whenever pool is a valid nonempty name;
  bare-source custom disks also create API custom-volume users. Profile root
  disk names never identify instance root volume consumers.
- LOCAL instance disks create API custom-volume users; EXPANDED instance disks
  create the separate effective attachment graph. Never union either projection.
  Effective root is exactly one disk path='/' with pool and no nonempty source;
  custom source is one bare existing name, with non-root path. Raw partial local
  maps may yield pool-only/no volume refs; they cannot invent effective users.
- Match every root volume one-to-one to same-name, same-project, correct-type
  instance and its effective root pool; require converse for every instance.
  Container content is filesystem, VM root content block. Missing, duplicate,
  orphan, wrong pool/type/content/counterpart gives STORAGE_ROOT_MISMATCH.
- Expected root volume used_by is sole owning instance under supported selectors;
  actual API extras still deny. Expected custom API users come only from raw
  profiles + local instances. Every API/effective custom reference must resolve
  to an actual owned custom volume. Effective attachments need not be API users.
- Instance/volume location must be present string '' or 'none'; require EXACT
  raw equality for each matched root/API/effective instance-volume relation.
  Pool locations may be absent/null/[]/['none']; other locations/targets give
  STORAGE_MEMBER_SCOPE_UNSUPPORTED. These tokens never prove noncluster state;
  the authoritative initial/final GET does. Preserve tokens, not arbitrary names.
- Storage URL contexts normalize omitted project to default, including storage
  links in Project.used_by, never current query project. Preserve explicit project
  and strict URL syntax; unrelated profile/network parser behavior stays intact.
- Named unsupported before successful normalization/artifact: image rows/links
  STORAGE_IMAGE_UNSUPPORTED; snapshots/storage source subpaths or selector keys
  source.type/source.snapshot STORAGE_SNAPSHOT_OR_SELECTOR_UNSUPPORTED; buckets
  STORAGE_BUCKET_UNSUPPORTED; target/locality STORAGE_MEMBER_SCOPE_UNSUPPORTED;
  daemon URL /1.0 STORAGE_DAEMON_CONSUMER_UNSUPPORTED. Unknown edges/DTOs retain
  fail-closed validation. Add selector keys to typed DISK parsing only to emit
  their blocker; any presence is unsupported, including empty values. Do not
  broaden NIC/proxy fields. Observe then reject; never discard or repair edges.

## 4. Schema3 retained evidence and independent graph

Schema3 is necessary because schema2's type-only disks cannot prove either
storage projection. Reject schema1/2 in the new reader; never fabricate a migration.

- Add family-level `lxd_pools`/`incus_pools`: sorted unique global records exactly
  name/type/metadata_digest/used_by. Project pool views retain local owned volumes
  plus metadata_digest and must match canonical name/type/digest/users exactly.
- Add family-level `lxd_admission`/`incus_admission`: null for unqueried family;
  otherwise initial/final safe admission projections above, equal and bound to
  corresponding active family/CLI version and exactly two allowed query records.
- Projects retain used_by and features_storage_volumes. Volume records retain
  explicit confirmed owner_project and storage_location (''|'none'); instances
  retain storage_location. These are observed DTO identities, never synthesized
  authority. Previous owner check occurs before output construction.
- Profiles add api_storage_devices from raw disks. Instances add separate
  api_storage_devices (local) and effective_storage_devices (expanded). Each
  sorted per-disk record is exactly {device,pool,selector,source}, with validated
  names, selector=root|custom|pool_only, source null except custom bare name.
  Profile root/pool_only entries create pool refs only; local pool_only is no API
  volume relation. Expanded pool_only is unsupported when pool is present.
- Reader checks unique producer names tied to corresponding retained disk-type
  evidence; counts cannot exceed RAW-profile, LOCAL-instance or EXPANDED-instance
  disk count respectively. Duplicate type entries cannot inflate counts.
  No disk path/config/source subpath/host name/certificate/address is emitted.
- Shared graph validation rechecks canonical views, safe admission, feature and
  actual owner bindings, global pool users, Project membership, root bijection,
  custom API reciprocity and effective reference resolution/location equality.
  Keep all schema2 network/consumer safety checks. Reader proves retained graph
  structure/count evidence, not replay of hidden raw disk semantics or live truth.

## Verification/release plan (NOT_RUN)

- Real command fixture: root-only pool with profile+instance but NO root volume
  URL in pool users; Project still contains root volume URL. Container/VM roots,
  unattached/attached custom; custom disk B/root A has no false B instance; two
  projects with global pool users; raw-local versus inherited-expanded custom
  users; stale overridden local fields never union into effective graph.
- Initial/final root GET exact argv/envelope/full family shapes: initial invalid
  stops before projects; final true/drift/proof/budget failure blocks main writer.
  Missing/null/nonbool/true cluster, wrong auth/public/API/family/default/version,
  duplicate keys/unknown/cross-family fields, nested driver lowercasing, malformed
  config and nil metadata boundaries denied appropriately. Inactive family never
  queried. Canary root secrets never reach serialized artifacts or fixed errors.
- Pool metadata/users/set drift and hidden views; missing/extra/orphan/wrong-type
  root, content, counterpart, wrong default URL; missing custom; owner mismatch;
  custom feature malformed/shared; named image/snapshot/bucket/member/daemon
  limits; local API and expanded effective projections must disagree correctly.
- Independent schema3 tampering: canonical pool/view/digest/users, project/root
  URL substitution, owner/scope/type/content/location, producer names/counts/
  projection swaps, API/effective edge deletion/addition, schema2 downgrade,
  forged inactive-family admission or missing final proof all denied. Keep old
  provenance/version/limits/redaction/private-writer and network regressions.
- Root obtains independent exact-plan and normative/query-scope approval before
  code GO, then reviews source hashes, runs focused inventory tests and all seven
  gates on approved PC WSL exact bytes. Only root may authorize another bounded
  native capture. No host/maintenance action is authorized by this design.

Estimate: implementation 1–2 engineer-days plus review/PC qualification 0.5–1;
medium confidence, excludes every unsupported engine and runtime maintenance.
Current decision remains DESIGN_REVIEW_REQUIRED pending exact reviews/root GO.

## Proposed completeness amendment — awaiting independent/root release

The original approved design SHA256
`f7a4999a050dceaeae901b2203b9fedb20281109d9352451c33915de92a7b826`
remains historical approval authority for the ongoing implementation. A new
explicit invariant is proposed before adding its code: every admitted active
family's complete observed project collection contains exactly one `default`.
Empty or own-alpha-only collections without default deny in capture and the
schema3 reader before any complete artifact; existing duplicate/order guards
remain. Inactive families retain empty projects/pools and null admission.
Tests cover active empty/default-missing, duplicate/default-view drift and the
inactive positive; real command fixtures include the actual default project.
No new query, budget, ownership or supported-resource expansion is proposed.
This appended amendment requires new exact-hash independent and root GO before
its invariant is implemented.

Existing approved proof semantics also require command-order binding in the
reader (CLI version, initial root proof, all family graph queries, final proof),
canonical pools derived from observed views, instance list/detail type/location
agreement, and volume list/detail content/location agreement. These are explicit
implementation refinements of retained identity/before-after completeness, not
new queries or ownership policy. Missing/mismatched observations must deny.

## Frozen candidate handoff — verification not executed by worker

Root released the completeness amendment after independent exact-contract
`81174a61a198bc4160ef86ec91de1481e16a5094b19a534a51e206f33c69c656`
and normative/query-scope review. Original f7a4999a approval remains historical;
no unsupported ownership policy or new query beyond the two reviewed root GETs
was introduced. Exactly-one-default is implemented in capture and reader.

Frozen collector SHA256:
`e3249d1307d74428ddbcc5dacb3c7e5afd858e8a29de6127c1da7bf5d6ffca31`.
Frozen test SHA256:
`3c38c3a332156e1f7f0055bac077b2e5dafbfad6824803472013cfed78ac6edd`.
Root reports both independent final source/test reviews approved those hashes
for integration and PC checks. No test pass is claimed for these bytes.

Implemented: strict complete family root DTOs and pinned CLI rendering; guarded
initial/final noncluster admission; global canonical pool/view metadata and users;
retained Project root-volume URLs; separate raw-profile/local-instance API and
expanded-instance effective disk evidence; returned ownership admission; root
bijection; named unsupported cases; schema3 independent graph and phase-order
validation. Producer records require their exact name to resolve to a disk-type
entry in the corresponding projection as well as unique/count bounds. List and
detail type/location/content must agree before storage authority is derived.

The existing private inventory-client two-value return remains; capture receives
safe admission/canonical projections through an optional internal output dict.
Omitting that dict does not skip root queries or any validation. Root metadata,
server PID, wrapper PID and secret configuration are never cross-inferred.

Fixtures now model global pools and the actual default project. Tests exercise
real command boundaries, root-only versus Project membership, custom API versus
effective relations, two-project/VM roots, hidden pool views, named unsupported
shapes, malformed root envelopes, final refusal with no writer (both families),
canary success stdout/records/writer and error redaction, and independent schema3
admission/storage/name/type/count tampering. Existing network semantics,
provenance, owner and budget tests remain; obsolete pool-root-volume-URL fixture
expectations were corrected to the pinned type-dependent API contract.

Worker performed only syntax parsing without module execution and
`git diff --check`. No tests, quality gates, host access, runtime client execution,
commits, merge or publication. S01–S07 remain unverified pending root's exact-byte
PC typecheck, focused tests and full seven-gate quality run. A new native capture
requires separate root review; no atomic snapshot or live readiness is claimed.

## Root schema3 integration and PC qualification checkpoint

This checkpoint supersedes historical DESIGN_REVIEW_REQUIRED/NOT_RUN labels
above for implementation verification only. Both independent reviewers approved
exact source `e3249d1307d74428ddbcc5dacb3c7e5afd858e8a29de6127c1da7bf5d6ffca31`,
tests `3c38c3a332156e1f7f0055bac077b2e5dafbfad6824803472013cfed78ac6edd`,
and handoff record `c6c9ec932c7fa234e20f0ad04f60b1e27b8e25b964e78844e36aecaa74b7c1bf`.
Root integrated exact bytes after reading the new source paths and full delta.
All 19 code/contract/workflow assets matched their SHA256 pins on PC WSL before
execution. The delayed first staging command eventually completed exit 0 before
any test; a bounded old-session echo timed out, a fresh SSH master succeeded,
and no process matched the attempted local cancellation. No duplicate staging
or tests were run. Only source files were staged on Windows; actual logs remain
owner-only ext4. No Windows service or rule was changed to recover transport.

PC Ubuntu WSL schema3 r1: nearest typecheck PASS (901 files), focused 297 tests
PASS in 19.128s, all seven QUALITY.md gates PASS, 43 architecture tests in 3.405s,
3,293 discovery tests in 188.067s with 36 skipped, process exit 0. No schema3
source/test changes followed review and no failed schema3 test attempt occurred.
Typecheck log SHA256 `8b95eefd5a06081479f0cdadf2bd460991d29b049becff2cf86cb1e0e213cb2b`;
focused `1a8fc9ad8bf250a541e1c98666375782cd5203179fe75d2a7b9a821a21f42c86`;
full `5db824d333ea89ad13a7fd34ca54ec74b04ad3f985ec6e3861954d91ea8856d7`.
Private copies match; exact tested-asset manifest and driver are also retained
privately. Child commands used isolated HOME/PATH without repurposing shell HOME,
normal umask 022 and stdin DEVNULL; private logs/exit records are mode 0600.

S01–S07 implementation is covered by these mocked regressions, not a live daemon
or ownership/fixture admission. Schema1/2 remain historical and rejected by this
reader. New root queries and storage semantics have not run on the real native
host yet. A fresh committed-source schema3 driver/pin/S3D review is mandatory
before ONE new capture. All previous failed captures remain nonpasses. No host
mutation, capability support, maintenance, fixture or Epic completion follows.
