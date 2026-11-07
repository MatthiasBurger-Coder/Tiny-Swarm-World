# EPIC 440 / S449-02F — network inventory contract refinement

State: DESIGN_REVIEW_REQUIRED. No implementation, tests, host access, runtime
changes, or readiness claims. This is a proposed normative contract, not shipped
behavior. Root owns independent architecture/test review, S3D release,
integration, remote verification and workflow/context updates.

Baseline: `4d004d0703ad0fc971ae5bc19696d20cecbfb73e`.
Branch: `fix/epic440-network-inventory-20261107`.
Isolated worktree: `/home/micro/tsw440-network-inventory`.

## Scope and locks

Only these files may change after separate code GO:

- `tools/linux/qualification/native_runtime_inventory.py`.
- `tests/tools/test_native_runtime_inventory.py`.
- `.codex/evidence/epic440-network-inventory-20261107.md`.

This design record is the only current edit. No changes to volume ownership,
profile/storage reciprocity, provenance, allowed commands, budgets, package or
server version source, socket activation guards, artifact redaction/storage,
Apply/maintenance admission, host state, or Windows modules. Root may update
workflow metadata independently. This work is serial across collector/tests.

Governance inspected: root and `.codex/AGENTS.md`, `QUALITY.md`, issue-completion
discipline, active #449 workflow/context. Three-Amigos skill applied as explicit
requirement/architecture/developer/tester role passes by this worker; these are
not independent approvals. Root supplies independent reviews before code.

## Requirement matrix

| ID | Requirement/source | Production owner/path | Dependency/current gap | Planned implementation | Planned verification/evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| N01 | Observed unmanaged Network status is empty; exact DTO safety | collector network list/detail validators | generic status enum rejects legitimate unmanaged DTO | explicit network-only empty-status condition and mandatory bool managed | real `_inventory_client` fixture; managed-empty and malformed denials | OPEN |
| N02 | Management is not TSW ownership | collector normalized artifact | current rows drop managed and count every interface as project-owned | schema 2 managed/nullable owner plus canonical scope | capture + independent artifact tamper tests | OPEN |
| N03 | Effective network project comes from validated Project config | collector project admission | current users indexed by request project | matched config list/detail; exact feature normalization; effective scope | default/own/inherited/invalid cases, order independence | OPEN |
| N04 | Preserve inherited views and compare canonical default, no union | full collected graph | inherited rows currently mislabeled | compare managed/type/config digest/exact normalized consumers | missing default/canonical and drift denied | OPEN |
| N05 | Project used_by contains only managed networks actually owned there | project reciprocity | unmanaged/inherited rows included currently | change network portion only; preserve all other resource rules | positive mixed interfaces and forged project links denied | OPEN |
| N06 | Consumer projection matches upstream | network graph | current local+expanded instance union creates false users | profile raw and instance expanded network refs only | overridden NIC, multiple NIC, foreign/missing consumer cases | OPEN |
| N07 | Simple parent supported without host inspection | NIC adapter/graph | parent currently ignored | literal non-VLAN parent to one existing scoped non-OVN/non-loopback target | positive managed/unmanaged target and explicit unsupported cases | OPEN |
| N08 | Unsupported transforms/uplinks/peer edges fail explicitly | network adapter/graph | generic parser rejection or silent omitted producers | fixed blocker codes; retain all returned used_by before classification | VLAN/OVN/loopback/ambiguous/uplink/peer denial, no artifact | OPEN |
| N09 | Schema 2 reader independently checks graph and scope | `validate_artifact` | current artifact drops config and producer reference information | typed flags, scope, managed/owner, config digests and producer refs; canonical graph checks | forged/missing/duplicate/legacy schema tests; durable writer checks | OPEN |
| N10 | Preserve bounded read-only safety and unrelated policies | Runner/capture/storage | existing verified boundary | no new queries/commands; same limits/rechecks; untouched volumes | exact command traces, historical regressions and parent full gate | OPEN |

All verification above is planned, NOT_RUN. Parent's earlier 266-focused /
3262-test quality result applies to baseline only, not this proposed contract.

## Pinned primary-source findings

LXD 5.21.9 `doNetworkGet` sets DTO Project to the request project. It populates
Managed/status/locations only for daemon-managed networks, and obtains UsedBy
using the effective project. Unmanaged loopback skips UsedBy computation.
[LXD networks.go](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/networks.go)

Incus 6.0.5 passes the effective result of NetworkProject into `doNetworkGet`;
DTO Project therefore identifies that effective scope. Status/locations are
likewise populated only for managed networks; loopback skips UsedBy.
[Incus networks.go](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/networks.go)

Both NetworkProjectFromRecord functions select the requested project when its
network feature is true, otherwise default. NetworkAllowed also filters
restricted projects. This bounded plan supports unrestricted projects and
rejects restricted projects explicitly rather than guessing filtered views.
[LXD project.go](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/project/project.go),
[Incus project.go](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/project/project.go)

Both UsedBy implementations collect profile NICs, expanded instance NICs,
network configuration references and created peer links. Device matching first
checks network; parent matching is disabled for OVN and otherwise applies
GetHostDevice. Empty VLAN leaves parent literal; nonempty VLAN can require host
VLAN inspection. Consumer project remains the profile/instance's own project.
[LXD network_utils.go](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/network/network_utils.go),
[Incus network_utils.go](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/network/network_utils.go)

Both API URL builders omit the project parameter for default. Therefore an
omitted project in a network UsedBy URL means default, including when observed
through an inherited nondefault view; it never means that requesting view.
[LXD url.go](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/shared/api/url.go),
[Incus url.go](https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/api/url.go)

Profile features are separately configured; new-project defaults do not prove
an existing project's observed value. Profile inheritance is explicitly outside
this slice, rather than being mistaken for profile ownership.
[LXD project DTO/defaults](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/db/cluster/projects.go),
[Incus project DTO/defaults](https://raw.githubusercontent.com/lxc/incus/v6.0.5/internal/server/db/cluster/projects.go)

## Proposed normative contract

### 1. Project admission and canonical scope

1. Require project list/detail config to be string maps and compare their full
   maps exactly before deriving scope. Missing config is invalid, not `{}`.
   Existing exact used_by list/detail comparison remains. Reject drift with
   `PROJECT_CONFIGURATION_DRIFT`.
2. Normalize `features.networks` and `features.profiles` independently: absent
   becomes null; literal strings `true` and `false` become corresponding bools.
   Reject empty, whitespace, alternate spelling, numeric aliases and other
   strings with `PROJECT_NETWORK_CONFIG_INVALID`. Bool JSON is already invalid
   under the string-map rule. Do not use Python truthiness or infer defaults.
3. Default is special: effective_network_project is default, independent of its
   absent/true/false normalized network flag. Malformed present flags still
   fail. Nondefault true means own project; false/absent means default.
4. Require a default project whenever any project inherits network scope.
   Effective scope must identify a collected project. Otherwise
   `NETWORK_CANONICAL_SCOPE_UNRESOLVED`. Do not reject all inherited projects.
5. For nondefault projects require `features.profiles=true`; false/absent gives
   `PROJECT_PROFILE_INHERITANCE_UNSUPPORTED`. Default remains special. No
   profile ownership reinterpretation or profile-sharing engine in this slice.
6. `restricted` is absent, exact `false`, or exact `true`; malformed value gives
   `PROJECT_NETWORK_CONFIG_INVALID`. Exact true gives
   `PROJECT_NETWORK_RESTRICTIONS_UNSUPPORTED` before enumerating resources.
   Reject nonempty `restricted.networks.*` or `restricted.devices.nic` settings
   with that same explicit unsupported code, even when restrictions are dormant;
   no partially modeled filtering/policy. Other arbitrary config stays a
   validated string map, is compared for drift and is not emitted.

### 2. Exact network DTO handling

1. Keep the complete returned interface list; reject duplicate names in each
   view. Require managed to be a literal bool in both list and detail. Require
   valid name/type/config/used_by under existing DTO key bounds.
2. Scope-check optional DTO Project using pinned family semantics: LXD equals
   requested project; Incus equals derived effective project. It is validation
   metadata only. Never derive owner from this field. Non-network DTO checks
   remain unchanged. An absent Project retains current compatibility.
3. Special-case only network status: absent keeps existing compatibility;
   present empty string is valid only when managed is explicitly false. Present
   nonempty status retains the existing bounded enum validator. Null/number/bool
   stays invalid. Managed true with empty status is invalid. No generic empty
   enum relaxation for pool, instance, volume or response status.
4. Retain nullable locations validation already shipped. Compare list/detail
   managed, type, complete config maps and normalized used_by exactly. Use
   `NETWORK_METADATA_LIST_MISMATCH` for managed/type/config drift; retain
   `NETWORK_CONSUMER_LIST_MISMATCH` for used_by drift. Status may legitimately
   change and is not an ownership discriminator.
5. Normalize network used_by only with omitted URL project = default. Explicit
   query projects retain exact identity. Do not change URL defaults for pools,
   volumes, profiles or Project reciprocity in this slice. All returned network
   consumers remain present; classify unsupported kinds explicitly, never drop
   edges. Deduplicate identical consumer identities as existing set semantics
   (multiple NICs may emit duplicate instance links upstream).
6. Canonical key is `(effective_network_project, network_name)`. Managed true
   means daemon management only: owner_project is effective scope, never TSW
   ownership. Managed false means owner_project=null. Unmanaged rows are valid
   only in effective default scope; otherwise `UNMANAGED_NETWORK_SCOPE_INVALID`.
7. Any nonempty network config `network` or `parent` is an explicit
   `NETWORK_UPLINK_UNSUPPORTED`; do not discard or resolve it speculatively.
   Any network used_by edge whose kind is networks is
   `NETWORK_PEERING_OR_DEPENDENCY_UNSUPPORTED`, whether peering or config-origin.
   Other unsupported network consumer kinds get `NETWORK_CONSUMER_KIND_UNSUPPORTED`.

### 3. Inherited views and project membership

1. Keep each inherited view row. Resolve it to the existing same-name canonical
   default row, never synthesize it from the inherited row. Require canonical
   uniqueness, effective scope default, identical managed/type/config digest,
   and identical complete normalized used_by. Missing canonical gives
   `NETWORK_CANONICAL_SCOPE_UNRESOLVED`; mismatch gives
   `NETWORK_INHERITED_VIEW_MISMATCH`. No union, intersection, filtered-edge repair
   or silently accepted extras/missing consumers.
2. Unrestricted inherited views should expose the complete default set. Require
   exact network-name sets for an inherited view and default; deny missing/extra
   rows as `NETWORK_INHERITED_VIEW_MISMATCH`. Default may appear later in query
   order; comparisons occur after all existing project queries complete.
3. Modify only the network portion of expected Project used_by: managed rows
   whose owner_project equals that Project. Exclude every unmanaged row and
   every inherited duplicate. Keep profiles/instances/volumes membership and
   storage-pool exclusion unchanged. All actual project edges are still
   compared exactly; an unmanaged/inherited network link is not silently removed.

### 4. Bounded producer graph

1. Collect producer network refs from profile raw devices and instance
   expanded_devices only. Keep original local and expanded device type inventory;
   local NICs do not add users. The existing double instance observation and
   drift comparison remain. Do not reconstruct expansion or union local NICs.
2. Resolve refs using the consumer project's effective scope. Consumer identity
   remains `(profiles|instances, consumer_name, consumer_project)`. Two NICs to
   one network give one consumer relation. Distinct referenced networks remain
   distinct relations. Explicit empty network/parent strings mean absent.
3. Support one explicit nonempty network name resolving to a canonical managed
   network in that scope, with no nonempty parent. Unmanaged explicit network
   target gives `NETWORK_MANAGED_REFERENCE_REQUIRED`.
4. Support a single nonempty literal parent, no explicit network and no VLAN,
   resolving to an existing same-name canonical non-OVN, non-loopback interface
   in the effective scope. Managed and unmanaged targets are supported. No
   network namespace inference, host lookup, VLAN construction or OS command.
5. A nonempty `vlan` on a relevant NIC gives `NETWORK_VLAN_UNSUPPORTED` before
   association, including an explicit network NIC. Allow vlan solely in typed
   NIC parsing so it receives this explicit blocker; reject a vlan key on disk
   or proxy devices, including an empty value. Other unknown device keys retain
   existing denial. Local-only overridden NIC metadata is
   validated but never contributes consumers.
6. Nonempty network+parent gives `NETWORK_DEVICE_AMBIGUOUS`, even if equal.
   Parent to OVN gives `NETWORK_OVN_PARENT_UNSUPPORTED`; any reference to loopback
   gives `NETWORK_LOOPBACK_CONSUMER_UNSUPPORTED`, because upstream skips its
   UsedBy calculation. Missing target gives existing
   `NETWORK_DEVICE_REFERENCE_UNRESOLVED`. A NIC with neither network nor parent
   gives no network edge, preserving upstream unassociated NIC behavior.
7. Reconcile canonical used_by exactly against the producer graph, across all
   projects. Every supported edge must resolve to an actual consumer and every
   producer ref must appear in canonical used_by. Keep existing
   `NETWORK_CONSUMER_RECIPROCITY_MISMATCH` and unresolved consumer protection.

### 5. Artifact schema 2 and independent reader

1. Emit only schema_version=2; `validate_artifact` rejects schema1 (no inference or
   migration that invents missing ownership). Existing historical files remain
   intact; fresh capture still refuses to overwrite its destination.
2. Add mandatory project fields `features_networks` and `features_profiles`
   (bool|null, null means observed absent), plus `effective_network_project`
   (validated name). The reader re-derives scope and the profile boundary.
3. Network records have exactly `name,type,managed,owner_project,config_digest,used_by`.
   managed is strict bool; managed owner is an existing effective scope; unmanaged
   owner is null. config_digest is lowercase SHA256 of UTF-8 canonical JSON of
   the complete validated config string map (sort_keys, separators, ensure_ascii).
   Raw config, addresses, descriptions and paths are not emitted. Digest equality
   lets the reader repeat inherited/canonical config identity checks.
4. Add `network_refs` to profile and instance records: sorted unique list of
   exactly `{project,name}` canonical target keys, names validated by existing
   identifier rules. Profiles derive refs from raw NICs; instances from expanded
   NICs. Existing devices/local_devices/expanded_devices type-only arrays remain
   unchanged, as do all pool/volume records.
5. Reader independently enforces normalized flag typing, effective scope,
   default presence where inherited, canonical uniqueness/default completeness,
   managed/owner consistency, inherited metadata/digest/consumer equality, and
   producer reference existence plus exact network consumer reciprocity. Nonempty
   network_refs require at least one corresponding NIC in the retained producer
   device inventory. Distinct refs cannot exceed the relevant NIC count: raw
   profile devices for profiles, expanded_devices for instances. Local instance
   NICs do not contribute to that count. It must reject forged unmanaged owner,
   managed null/wrong owner, unknown scope,
   unsupported network consumer kinds, missing/extra/duplicate refs and consumers.
6. Raw config is not emitted; its digest supports identity comparison and is
   not encryption or a confidentiality guarantee. Reader proves structural
   self-consistency of the captured graph, including NIC-count sanity; it cannot
   replay hidden raw NIC semantics, authenticate the daemon or independently
   replay a live observation. Capture owns typed DTO validation,
   full config comparison, restriction/uplink detection and NIC adaptation.
   Existing service/socket provenance checks bind that read-only capture.

## Test design (not executed)

- Extend the real command-response fixture for multiple projects, request/effective
  family-specific DTO Project values, per-project config and exact URI traces.
  Existing single-project alpha fixture must explicitly declare own network and
  profile features; do not silently reinterpret its prior config={} as own scope.
- End-to-end `_inventory_client` with managed bridge plus unmanaged loopback,
  physical, bridge and unknown interface rows (empty status, nullable locations),
  all retained; exact Project links contain managed bridge only.
- Reject missing/nonbool managed, managed empty status, unmanaged null/numeric
  status, list/detail management/type/config drift, unknown DTO keys. Assert
  unrelated pool/instance response empty-status cases still fail.
- Positive default special cases and nondefault own/inherited false/absent;
  canonical default last in command order; inherited views retain all rows and
  cross-project used_by with absent URL project normalized to default.
- Distinguish equal network names in two independent network projects. Verify
  LXD requested Project and Incus effective Project pass only their expected
  family shape; foreign Project fails. No added GET/CLI probes.
- Deny malformed feature/restricted values, restricted true/settings,
  nondefault profile false/absent, missing config and list/detail config drift.
- Deny default missing, duplicate canonical/view rows, inherited missing/extra
  row, managed/type/config/consumer mismatch; no consumer union can make them pass.
- Positive profile network refs; expanded NIC inheriting network; local NIC
  overriding profile to another network produces only expanded instance user;
  profile stays a real consumer of its original network. Multiple NIC refs
  deduplicate per identity without dropping distinct targets. Local-only stale
  refs never create a false consumer. Existing profile reciprocity stays intact.
- Positive literal parent to unmanaged physical/bridge and managed bridge;
  explicit network to unmanaged denied. Deny VLAN (including long-name transform),
  parent to OVN, network+parent, loopback references and missing parent target.
  Reject vlan keys on disk/proxy, including empty values; retain unknown-key
  denial outside the NIC-specific vlan parser.
- Deny network config network/parent uplinks and returned network-to-network/peer
  edges with named fixed codes; preserve consumers before denial and emit no
  successful inventory artifact. Unrelated unknown device keys remain denied.
- Independent schema2 validation: valid serialized capture roundtrip; schema1,
  missing/typed managed, forged unmanaged owner, missing/duplicate canonical,
  wrong flags/scope/digest, unresolved refs, added/removed consumers, duplicate
  refs and network-consumer kinds denied. Deny nonempty refs without NIC evidence
  and distinct refs exceeding raw-profile/expanded-instance NIC count; a local
  instance NIC cannot satisfy that bound. Reader must detect changes without
  calling runtime adapters. Keep durable file mode/path/no-overwrite tests.
- Preserve volume owner/used_by/pool reciprocity denial fixtures, profile user
  reciprocity, all old provenance/PID/socket/activation/version/DTO/budget guards.
  Retain exact command allowlist and per-query safety checks; test artifacts stay
  deterministic, under existing size budget and free of raw config/address data.

## Execution and acceptance sequence

1. Root and independent requirement/architecture/test reviewers review this exact
   record hash. Any contract change produces a fresh reviewed record/hash.
2. After explicit root code GO, implement serially within the three locks and
   request review of exact source/test hashes. Worker performs no tests/hosts.
3. Root copies exact approved candidate to approved PC WSL and runs focused
   `tests.tools.test_native_runtime_inventory` plus nearest shared regressions,
   then all seven `quality` gates under repository rules. Root records exact
   source/test hashes and failures; no local fallback host.
4. Only after those pass may root review a new bounded read-only native capture
   bound to the committed source. Unsupported shapes remain explicit BLOCKED,
   no artifact fabrication and no runtime changes. Native readiness/maintenance
   remains a separate decision.

Estimated engineering effort: implementation 0.75–1.5 days, independent review
and PC qualification 0.25–0.75 days; total 1–2.25 engineer-days, medium confidence.
This includes the bounded schema/graph foundation, excludes profile inheritance,
restricted-project filtering, VLAN/OVN-parent/uplink/peer engines and live
maintenance. No calendar-time or runtime-readiness promise.

Proposed decision: READY_FOR_WORKFLOW only after independent exact-hash review
and root release. Current decision remains DESIGN_REVIEW_REQUIRED. No scope
extension to storage/volumes is proven necessary; their policy stays unchanged.

## Code candidate handoff

Root released the exact design SHA256
`32feb15da2e590d92cf9a40d2b1d497ff5a1241e877d067d9aed2a2884ae3e7c`
after both independent reviews approved it. Implementation now exists only in
the two approved collector/test files of this isolated worktree. Matrix items
N01–N10 have reviewable code and planned tests; verification remains NOT_RUN and
none is marked VERIFIED by the worker.

Implemented schema2 flags/scope/nullable managed ownership, full inherited view
comparison including config digest, family-specific DTO scope checks, network
producer projection from profiles and expanded instances, literal parent support
and explicit unsupported boundaries. Capture and artifact reader share the
normalized graph validator. Reader also rejects duplicate producer device names
so repeated NIC entries cannot inflate the reference-count bound. Raw config
comparison remains in capture; hashes are comparison identities only.

The real multi-project command-response fixture exercises inherited default
scope observed last, both family DTO Project shapes, managed/unmanaged rows,
local-only stale NIC/VLAN metadata, duplicate same-consumer NICs and distinct
targets, omitted default consumer URL parameters, and independent schema2
artifact tampering. Existing single-project fixture now explicitly requests
own networks and own profiles. Existing pool/volume behavioral assertions remain;
handmade schema2 fixtures gain required project scope fields only.

Only syntax parsing without module execution and `git diff --check` were used
by this worker. No test, quality gate, runtime client, host access or commit was
performed. Root must run focused and full checks on exact integrated bytes.
Root must amend the workflow artifact schema contract before a fresh native
capture. Old artifacts are neither migrated nor overwritten; schema1 is rejected.

Limitations remain exactly the reviewed plan: nondefault inherited profiles,
restricted-network views, VLAN transforms, OVN parents, loopback consumers,
network uplinks and network peer/dependency consumers are explicitly unsupported.
Daemon-managed never proves TSW ownership. Reader validates retained graph
structure and NIC-count evidence, not hidden raw NIC semantics or live state.
No storage/volume policy change or new command/host query was needed.

## Root integration checkpoint — 2026-11-07

This checkpoint supersedes the historical DESIGN_REVIEW_REQUIRED/NOT_RUN state
of the design and worker handoff above. Both independent Architecture/Security
and Tester/DevOps reviewers approved the design, implementation and the final
behavior-preserving typing-only delta. Current source SHA256
`eb50bb6a9a94b59743585cacddc85383198515e30ecb32b93ba72f1dea46f8de`;
tests `7ecbe7336d0b2c8e283dd01e2efd0cfe2068f701b793f62182c86fd9807e1b21`.
Only two local variable names changed after the original candidate review.
The first PC run passed 277 focused tests but failed seven mypy checks; its
logs remain retained and are not represented as a full pass.

The final exact-pinned PC Ubuntu WSL run passed 277 focused tests in 20.127s,
all seven QUALITY.md gates, 43 architecture tests, and 3,273 discovery tests
in 188.769s (36 skipped), process exit 0. Focused log SHA256
`acab81da1eff19e4cf38fc9d1905970b204bd017d8c331c2928b7837923f60bd`;
full log `d13c7ad22a25c497d73d49a2618618b979dd1dcae43b23b8ea2339c60e85f853`.
Private ext4 copies match. Both reviewers separately approved the workflow
v1.44/F4-design/context amendments. These are mocked/local verification results;
N01–N10 implementation is covered by those regressions, not live ownership or
runtime qualification. No host capture or mutation is authorized by this record.
Any fresh native capture requires a separately exact-reviewed committed-source
schema2 driver and one-shot S3D plan; all unsupported boundaries remain blockers.
