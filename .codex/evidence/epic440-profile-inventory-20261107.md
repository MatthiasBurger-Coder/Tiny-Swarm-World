# EPIC 440 / S449-02F — bounded inherited profile inventory

State: DESIGN_REVIEW_REQUIRED. Baseline
`d641762ff4859cfc9a14fbd6a829b57cfdb8b31c`; worktree
`/home/micro/tsw440-profile-inventory`, branch
`fix/epic440-profile-inventory-20261107`. Only this record is written; no
source/tests/hosts/commits or profile/feature mutation. Root owns v1.47,
independent exact-plan/normative review, code GO, integration and PC verification.
Future locks: `tools/linux/qualification/native_runtime_inventory.py`,
`tests/tools/test_native_runtime_inventory.py`, this record.

Observed native capture stopped PROJECT_PROFILE_INHERITANCE_UNSUPPORTED without
artifact. This is the existing intentional unsupported boundary. Its removal
requires the complete owner/view model below, not feature changes or a bypass.
Baseline schema3 typecheck/297-focused/full-quality success does not qualify a
changed candidate or actual inherited-profile readiness.

| ID | Requirement/source | Owning path/current gap | Proposed implementation/evidence | Status |
| --- | --- | --- | --- | --- |
| P01 | Effective profile scope and actual DTO owner | collector project/profile admission rejects false/absent | config-derived scope, mandatory owner in both families; real adapter flags/owner tests | OPEN |
| P02 | Complete canonical/inherited views | no profile owner/digest retained | exact full view sets/raw metadata/users/projections; drift/hidden denials | OPEN |
| P03 | Cross-project users and ordered membership | current same-project users and sorted-set membership | canonical global profile users; exact ordered unique instance lists | OPEN |
| P04 | Producer owner differs from instance scope | profile views currently act as request-project producers | count raw profiles once in owner feature scope; instance graphs unchanged | OPEN |
| P05 | Independent serialized graph | schema3 lacks profile scope/owner metadata | schema4 retained scope/owner/digest, recheck all profile/graph invariants | OPEN |
| P06 | Preserve bounded read-only authority | schema3 root/storage/network invariants already reviewed | unchanged queries/limits/owner boundaries, focused/full PC regression | OPEN |

Worker requirement/architecture/automation/tester passes are not independent
approvals. Reviewers support the concept; this exact record still needs review.
All new verification described below is planned NOT_RUN.

## Primary findings

Both ProfileProject mappings use the requested project only when
features.profiles is true, otherwise default. Existing observed absence is not
new-project creation default. Profile DB ToAPI returns Project=p.Project in
BOTH families, so this field is actual owner, never a request echo.
[LXD mapping](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/project/project.go),
[Incus mapping](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/project/project.go),
[LXD ToAPI](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/db/cluster/profiles.go),
[Incus ToAPI and expansion](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/db/cluster/profiles.go)

Both list/detail resolve effective profiles; profileUsedBy queries profile ID
and returns actual instance URLs across projects. Consumer project stays the
instance's own project. URL builders omit project for default. Neither filtered
views nor missing consumers may be repaired by union.
[LXD profile handlers](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/profiles.go),
[Incus profile handlers](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/profiles.go),
[LXD URL](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/shared/api/url.go),
[Incus URL](https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/api/url.go)

GetProfilesIfEnabled preserves supplied name order; expansion applies profiles
in order then replaces same-name devices with local devices as WHOLE maps.
There is no missing-property merge. Production continues to trust validated
observed expanded DTOs, without implementing an expansion engine.
[LXD expansion](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/instance/instancetype/instance_utils.go),
[Incus expansion](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/db/cluster/profiles.go)

Raw-profile network and storage matchers use its DB owning project's feature
scope, while instance matchers use the instance project. Global pool profile
links also enumerate actual profiles once. Project UsedBy contains owned profile
URLs, not inherited duplicate views.
[LXD network matcher](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/network/network_utils.go),
[Incus network matcher](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/network/network_utils.go),
[LXD storage matcher](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/storage/utils.go),
[Incus storage matcher](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/storage/utils.go),
[LXD global pools](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/storage/storage.go),
[Incus global pools](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/storage/storage.go),
[Incus Project UsedBy](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/api_project.go)

## Proposed exact contract

1. Preserve exact true/false/absent normalization of features.profiles. Add
   effective_profile_project: default for default itself, own project for
   nondefault true, otherwise default. Malformed flags still deny. Replace only
   PROJECT_PROFILE_INHERITANCE_UNSUPPORTED after this complete model exists.
   Existing active-family exactly-one-default prerequisite remains.
2. Require Profile.Project present, typed valid name and equal to derived scope
   at BOTH list and detail boundaries, for BOTH families. Missing/foreign owner
   gives PROFILE_OWNER_PROJECT_MISMATCH. Never coerce/fill owner from query URI.
   Keep the existing DTO key allowlist and typed config/devices/description/users;
   no unknown-key or generic null relaxation. List/detail must agree exactly on
   owner/name/config/raw devices/description including optional field presence,
   and complete normalized used_by. Metadata mismatch gives
   PROFILE_METADATA_LIST_MISMATCH; consumer mismatch retains existing code.
3. Canonical key is (owner_project, profile_name), taken only from that actual
   owner's queried view. Retain every view. An inherited view must have the
   EXACT default profile-name set and identical complete canonical row, including
   metadata digest, all consumers and derived producer evidence. Missing/extra/
   filtered/drifting rows give PROFILE_INHERITED_VIEW_MISMATCH; missing canonical
   owner/default resolution gives PROFILE_CANONICAL_SCOPE_UNRESOLVED. No unions,
   intersections, invented canonical row or assumed named 'default' profile.
4. Normalize Profile.used_by omitted URL project to default. Do the same for
   profile URLs in Project.used_by; existing storage URL default handling stays.
   Network/storage profile links already use default-aware URL interpretation.
   Preserve unrelated URL behavior. Canonical profile expected users span ALL
   collected instances whose effective_profile_project equals its owner and
   whose profiles list contains its name; instance identity stays its own project.
   Every actual consumer must resolve; exact missing/extra users deny.
5. Instance profiles is an ordered unique list of valid names. Preserve exact
   order from the API; require identical sequence across instance list and both
   detail observations. Do not sort or deduplicate before comparison/output.
   Duplicate/invalid sequences give PROFILE_LIST_INVALID; differing sequence
   gives INSTANCE_PROFILE_LIST_MISMATCH. Sets are allowed only for membership/
   consumer calculation. Resolve each name against the canonical effective owner.
   The existing ordered names suffice; no extra membership field is needed.
6. Count raw canonical profile producers ONCE, in actual owner scope. A profile
   raw NIC resolves through owner.effective_network_project and emits owner
   profile identity. An inherited view cannot retarget it to requesting project's
   networks. Expanded instance NICs remain in instance scope. Canonical profile
   network refs/projections must be identical in inherited rows; existing NIC
   bounds and unsupported cases remain.
7. Raw profile storage/API devices use owner features.storage.volumes and owner
   identity, once. Global pool/profile users include only canonical actual
   profiles, not inherited-view copies. Instance LOCAL API devices and EXPANDED
   effective devices remain in instance scope. Same bare custom name may resolve
   to different owner/instance volumes; never union the graphs or relabel owners.
   Preserve returned volume owner==query, shared custom false/absent unsupported,
   root bijection/Project root URLs, global pool equality, locations and all other
   schema3 storage boundaries. Profile ownership is not TSW ownership.

## Schema4 and reader

Schema4 adds only project.effective_profile_project and profile.owner_project /
metadata_digest. Digest is canonical JSON SHA256 over the complete validated
profile description/config/raw devices with field presence; compare full maps
in RAM first. No raw config, paths or secrets are emitted; digest is identity
comparison, not encryption/confidentiality. Existing type-only devices,
network_refs, api_storage_devices and used_by remain and must match canonical
owner row. No family-global profile table is necessary: canonical owner rows
already exist in complete project views.

Reader accepts schema4 only; old captures stay untouched, no synthetic migration.
It independently derives scope from typed feature flags, validates owners and
unique canonical rows/default view equality, verifies digest/projection/user
identity, ordered unique instance membership, cross-project consumer closure,
Project-owned profile links and all owner-scoped network/storage producer edges.
Existing producer names/types/counts remain mandatory in their original raw/
local/expanded evidence. Reader proves retained structural consistency, not raw
profile expansion, digest contents or authenticated live state. Root admission,
phase ordering, CLI version authority and all schema3 network/storage semantics
remain independently checked.

## Planned tests and release

- Real family fixtures: false and absent inheritance with default queried last;
  default profile used by default+nondefault instances; own same-name profile in
  another true-feature project remains separate. Mandatory effective-owner DTO
  Project for both families; reject missing/request-echo/foreign/typed owner.
- Exact inherited sets; list/detail/full config/device/description drift and
  canonical digest/users/projection drift, filtered/missing/extra/duplicate views.
  Missing/extra consumer and omitted-default URL mistakes must fail actual main
  without writer, including at least one failing inherited case per family.
- Preserve ordered profiles across all three observations; test reversed order,
  duplicate names and unresolved effective-owner membership. No sort-set repair.
- Raw default-profile NIC uses default network; inherited alpha instance with
  own network scope uses alpha network of same name. Raw profile default custom
  volume API consumer stays default; alpha true custom namespace's expanded
  attachment resolves alpha volume, preserving strict returned volume ownership.
  Global pool/profile user appears once. No new shared-custom support is implied.
- Correct prior schema3 positive fixture/comment claiming partial local device
  inherits omitted pool. A genuinely inherited attachment has NO same-name local
  entry; a complete local override replaces the profile device while original
  raw-profile API user remains. Never invent per-property merge or reconstruction.
- Schema4 independent tampering: flag/scope/owner/digest/default/canonical/set/
  consumers/order/membership/projection owner and extra duplicated producer edges.
  Ensure schema3 rejection and all prior root, storage, network, provenance,
  budgets, fixed-error/redaction and private writer regressions remain.
- No new query, command, URI, client invocation type or budget. Every inherited
  list/detail observation still counts toward unchanged 2048 commands, existing
  entity/byte/process/wall limits and before-query/final provenance checks.
  No feature/profile edit, activation or runtime repair.

Root obtains independent exact-plan plus v1.47 normative approval before code GO;
worker then changes only three locks and returns exact hashes without tests or
hosts. Root runs PC typecheck, focused native inventory tests and all seven gates
on exact bytes before a separately reviewed committed read-only capture.
Estimate: implementation 0.75–1.5 engineer-days plus review/PC qualification
0.25–0.75; medium confidence, excludes unsupported resource engines/maintenance.
Current decision remains DESIGN_REVIEW_REQUIRED.

## Approved implementation handoff — 2026-11-07

The DESIGN_REVIEW_REQUIRED statements above describe the preserved historical
proposal. Root granted code GO after both independent exact-plan approvals of
`b05ec03d298bdaee8098cb19bcfc2b11a1f7062805c23b7812c9d0a60d84051e`
and separate v1.47 normative approval (F4 `7aaf1f8b`, workflow `d12b12a1`,
context MD `dc1363e0`, context JSON `3767a6cb`). Current status:
IMPLEMENTED_PENDING_INDEPENDENT_EXACT_CANDIDATE_REVIEW_AND_PC_VERIFICATION.

P01–P05 are implemented in the two declared source/test locks. Schema4 retains
profile effective scope, actual owner and metadata digest; full raw metadata
maps, including optional-field presence, are compared directly in RAM at both
list/detail and inherited/canonical boundaries before discard. Every inherited
view remains present and equal to its canonical owner view. Ordered unique
instance profile membership, cross-project consumers and canonical raw producer
owner scopes are checked by capture and independently by the schema4 reader.
P06 remains an exact-byte PC regression/release prerequisite; worker makes no
live readiness claim.

Tests include both pinned family shapes, false/absent inheritance, default queried
last, default/cross-project consumers, an independently owned same-name profile,
list/detail owner denials, hidden/extra/duplicate/drifting views, all three
instance membership observations, profile-owner versus instance network/custom
storage namespaces, writer refusal, raw-metadata canaries and schema4 tampering.
Both raw-map comparison boundaries have regression cases with a deliberately
constant mocked digest, including absent versus empty description at list/detail.
The earlier partial local-device inheritance fixture now uses no local device
for real inheritance and complete device replacement for an override; production
continues to use observed expanded DTOs without an expansion engine.

Unchanged: query/command/URI surface and all budgets; server-root before/after
admission; global pool equality; volume returned-owner boundary and unsupported
shared-custom shapes; network ownership and graph rules; helper/source authority.
No feature, profile, daemon, service or host state was changed.

Frozen candidate SHA256:

- collector: `10f1a2e5a03ba37a499f7da3eb9ccc2873330bfa2e7e84fd4200564b9d4a098d`
- tests: `0d02128b9573a43067339b3224a6a4539c6f868493b5e386d2f5fb3707e8198b`

Worker validation: Python AST syntax parse PASS for both files (no import or
execution); `git diff --check` PASS. Typecheck, focused tests and full quality:
NOT_RUN by worker. No host access, capture, commit or publication. Root owns
independent frozen-candidate review, exact-byte PC typecheck/focused/all-seven
quality gates and a separately approved committed read-only capture. Reader
checks retained structural consistency; it cannot replay hidden raw metadata or
profile expansion and does not authenticate live state. No remaining contract
uncertainty was identified during worker static self-review.

## Root schema4 integration and PC verification checkpoint

This checkpoint supersedes historical pending/NOT_RUN states above for code
verification only. Both independent roles approved exact collector
`10f1a2e5a03ba37a499f7da3eb9ccc2873330bfa2e7e84fd4200564b9d4a098d`,
tests `0d02128b9573a43067339b3224a6a4539c6f868493b5e386d2f5fb3707e8198b`,
and handoff `d14f39655775046e90d7de3244b085d1b5e6e5ff716b04dfb83a9e004035aa9f`.
Root read the source delta and direct RAM metadata/canonical comparison helpers,
integrated exact bytes, and checked all 20 code/contract/workflow asset hashes
on PC WSL before execution. A local staging-controller syntax typo was corrected
before that controller executed any SSH command; it was not a test or host
failure. Subsequent staging completed exit 0 with each child checked and bounded.
No source/test change followed review; no duplicate schema4 test attempt occurred.

PC Ubuntu WSL schema4 r1: nearest typecheck PASS across 901 source files;
306 focused tests PASS in 19.433s; all seven QUALITY.md gates PASS,
43 architecture tests in 3.396s and 3,302 discovery tests in 192.211s
(36 skipped), process exit 0. Typecheck log SHA256
`1a3e21695e40352978f23576f76da72a98e0b64abba6289f71fab3fea854bf28`;
focused `07c2193b389f6e783a180eeee796b7ecc8768ab7f7fc5b13a2ba184ccf006fc7`;
full `905d6122d7b9e76880b31a81c308b02c2d774259fe0e215cfe993b54ac0ef57a`.
Owner-only ext4 copies match; tested-asset manifest/driver are retained privately.
Tests ran under normal umask 022, isolated child HOME/PATH, stdin DEVNULL;
logs/exit records are mode 0600. No tests ran on local/native hosts.

P01–P06 implementation is regression-covered, not live inherited-profile
qualification. Canonical owner/view, direct full metadata equality, ordered
membership, owner-scoped raw producers and instance scopes remain distinct.
Reader rejects schema1/2/3; no synthetic migration or hidden expansion replay.
All root/storage/volume-owner/query/budget guards remain. The actual schema3
profile-inheritance failure remains nonpass and is not reclassified as success.
A fresh committed-source schema4 driver/pin/S3D review is required before ONE
new native capture. No fixture, capability, host mutation, maintenance or Epic
completion is released by these mocked results.
