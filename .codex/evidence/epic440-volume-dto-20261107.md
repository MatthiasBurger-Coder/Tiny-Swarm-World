# EPIC 440 / S449-02F — volume Pool DTO admission

State: DESIGN_REVIEW_REQUIRED; no code/tests/hosts/commits. Baseline
`b7f5fad949b42ba05e9c8fbb3f7ab3e009bb8170`; isolated worktree
`/home/micro/tsw440-volume-dto`, branch `fix/epic440-volume-dto-20261107`.
Root owns independent review/GO, workflow v1.45, integration and PC verification.

Observed: root's schema2 capture failed RESOURCE_SCHEMA_INVALID; its separately
approved diagnostic isolated a returned volume list DTO containing string `pool`.
No raw host values are included. Current volume list/detail allowlists lack it.

| ID | Requirement/source | Path/owner and current gap | Implementation and planned evidence | Status |
| --- | --- | --- | --- | --- |
| V01 | LXD returned DTO pool | collector list/detail reject known field | exact family allowlist; real adapter positive/negative fixtures | OPEN |
| V02 | Pool identity matches request | expected pool already known from argv/URI | mandatory typed exact identity at both boundaries; malformed/drift denials | OPEN |
| V03 | Incus returned DTO excludes pool | maintain unknown-key guard | no global relaxation; Incus unchanged positive and pool-present negative | OPEN |
| V04 | Preserve owner/graph/schema2/bounds | existing collector/reader safety | keep project and consumer rules, schema and commands; regressions + PC gates | OPEN |

## Pinned evidence

LXD 5.21.9 returned StorageVolume has non-omitempty Pool. Its database query joins
storage_pools, selects its name and scans directly into vol.Pool. Detail lookup
filters PoolID and delegates to the same population path; empty Pool is not a
supported per-pool placeholder. [DTO](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/shared/api/storage_pool_volume.go),
[database population](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/db/storage_volumes.go)

Recursive list and detail endpoints return those populated api.StorageVolume
objects. Client per-pool GETs decode them; CLI JSON renders their pointers
without clearing Pool. [Server](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/storage_volumes.go),
[client](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/client/lxd_storage_volumes.go),
[CLI](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxc/storage_volume.go)

Incus 6.0.5 returned StorageVolume has no Pool. The optional Pool on a migration
request is a different DTO and supplies no returned-field authority.
[Incus DTO](https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/api/storage_pool_volume.go)

## Exact proposed change

- Future three-file locks: `tools/linux/qualification/native_runtime_inventory.py`,
  `tests/tools/test_native_runtime_inventory.py`, and this evidence record only.
- Use existing `incus` family selection, never infer family from DTO shape or
  marketing version. One shared volume-key/pool helper serves list and detail.
- LXD allowlist gains only `pool`; require a present literal string satisfying
  existing identifier syntax and case-sensitive equality to the queried pool.
  Missing/null/bool/number/array/map/empty/whitespace/URL-escaped/path-shaped or
  foreign pool fails `VOLUME_POOL_IDENTITY_MISMATCH`. No coercion/URI fill/fallback.
- Incus retains its current allowlist; any pool key remains unknown and denied,
  including an empty or matching value. `_validate_volume_show` gains an explicit
  required keyword-only family argument, passed by production and test callers.
- Keep mandatory Project/owner/name/type/config/used_by validation and exact
  list/detail consumers; preserve inherited/shared owner denials, duplicate IDs,
  supported content types, unresolved edges and pool/volume reciprocity. Pool
  identity never establishes ownership.
- Validate source Pool then discard it. Schema2 normalized volume/pool records,
  reader, storage, limits, server-version source, provenance, activation guards
  and command/GET set remain unchanged. No storage topology or policy expansion.
- Older LXD missing mandatory Pool and future Incus containing Pool stay blocked
  until separately reviewed; this slice models inspected 5.21.9/6.0.5 shapes.

## Planned verification and release

- Real `_inventory_client` response fixture emits Pool for LXD list/detail only;
  Incus remains unchanged. Assert exact query argv and equivalent normalized
  volume/pool graphs, leaving family command/executable envelopes distinct.
- Both boundaries deny every malformed/missing/foreign Pool class; wrong list
  stops before detail GET, wrong detail before successful graph/artifact return.
  Incus rejects pool-present variants and both families retain unknown-key denial.
- With valid LXD Pool retain owner, missing/typed config/used_by, unresolved or
  drifting consumers, duplicate IDs, type/content and reciprocity denial cases.
  Preserve schema2/private writer/no-overwrite and existing budget/provenance tests.
- Root obtains independent exact-hash plan approval then code GO; worker returns
  candidate hashes without tests/hosts/commits. Root runs focused native inventory
  tests and all seven quality gates on approved PC WSL exact bytes. A new bounded
  read-only native capture requires separate root review after those checks.

All evidence above is planned NOT_RUN. No live readiness is inferred. Estimate:
0.25–0.5 engineer-day implementation plus 0.25–0.5 review/PC verification, high
confidence; excludes maintenance/unrelated DTOs. READY_FOR_WORKFLOW is proposed
only after independent approval and root release.

## Candidate handoff

Root released code after both independent reviews of exact design SHA256
`04282f0daba11aec9ca000dfec3040938838ec784455a5d9f34603bef1a1e208`
and workflow v1.45 normative GO. Only the collector/test paths above changed.
Shared `_validate_volume_dto` validates family keys and mandatory LXD Pool before
existing list/detail validation. Family argument is explicit at every detail
call. Owner, consumer graph, normalized schema2 and command/limit code are intact.

The fixture now emits Pool only for LXD list/detail. New real-flow tests cover
system/snap LXD equivalence to Incus normalized rows, exact existing argv,
malformed Pool at both boundaries, missing Pool through actual main with no
artifact write, Incus unknown-pool denial, and unchanged owner/consumer/config/
content/duplicate denials when LXD Pool is valid. No raw DTO fields are persisted.

Worker performed syntax parsing without module execution and `git diff --check`
only. Tests/quality/hosts/commits remain NOT_RUN by worker; V01–V04 await exact
candidate review and root's PC WSL gates. Historical pass evidence does not
qualify this changed candidate. Inspected family compatibility limits remain.

## Root integration checkpoint — 2026-11-07

This checkpoint supersedes the historical DESIGN_REVIEW_REQUIRED/NOT_RUN state
above. Both independent reviewers approved the exact plan, v1.45 normative
amendments and original implementation, then the annotation-only test delta.
Current source SHA256 `ef646f3684af17f78f69af15ad95abb5fed17ef4486d5d84e477cd2d0faeff6f`;
tests `3fcf3506e1be379d2783d6ee4e8bdb5d1e134fd6fdf527557af4745898df680b`.
No production changes followed the implementation review. The first PC attempt
passed focused tests but failed one missing test-variable annotation; that
nonpass remains separately preserved, with no values/assertions suppressed.

Final PC Ubuntu WSL exact-pinned run: 283 focused tests PASS in 20.307s; all
seven QUALITY.md gates PASS, 43 architecture tests in 3.467s, 3,279 discovery
tests in 189.752s (36 skipped), process exit 0. Focused log SHA256
`0314b976415d6dd17a10174a02c3c107e241913e8ce8dc3cc163c2f326b5163a`;
full log `c52217e3de74529255f7f5659f3db679780e5c711a16db5fcff0eb73f5b1c6b6`.
Owner-only ext4 copies match. These verify V01–V04 implementation through
mocked regressions, not live host ownership or qualification. A fresh native
capture requires separately reviewed committed-source pins/driver/S3D and may
still fail other unsupported state. No runtime effect or capture authority is
released by this record.
