# Issue #189 — S189-01 Consolidation

- Workflow: `issue-189-20260809` / `issue-189-v1.0.0`
- Slice: `S189-01` — Consumer inventory and Three-Amigos contract
- Branch: `feature/centralize-lxc-shared-utilities-solid`
- Real subagents: not available in the current tool surface.
- Fallback review: completed by Codex using the required role and skill
  instructions; Codex remains the final integration owner.
- Result: `S189-01_READY_FOR_S189-02`

## Stream results

| Stream / role | Result |
|---|---|
| Senior Requirement Engineer | Accepted the eight-row Issue #189 matrix, recorded the requested chain order, and confirmed the before-inventory covers the broader current consumer set. |
| Senior System Architect | Accepted the infrastructure-only target and required separate ownership review for composition, preflight, legacy compatibility and extracted LXC packages. |
| Senior Python Automation Developer | Accepted a single resolver/helper direction for S189-02, with adapter-owned retry, failure, Docker byte-stream and preflight policy preserved. |
| Senior Tester | Accepted deterministic inventory evidence, required focused regression tests for S189-02/S189-03, and the local quality gate result. |
| Senior Execution Orchestrator | Accepted S3/S3D branch, scope, metadata and serial topological order. |
| Senior Security Sandbox Engineer | Accepted the existing diagnostic redaction boundary and the prohibition on raw command output, credentials or live commands in evidence. |
| Senior Documentation Engineer | Accepted planned-only Arc42 wording and explicit distinction between local quality and live/external evidence. |

## Accepted findings

- Twelve backend mapping definitions or mapping-like tables are present in
  infrastructure production code, not only the two named in the authoring
  baseline note.
- Three private command-failure predicates share the same timeout/non-zero
  semantics.
- `lxc/command/diagnostics.py` is the current canonical safe-log boundary;
  three adapters still carry weaker private truncation-only copies.
- Manager-IP lookup has two implementations and three injected resolver
  seams; the legacy runtime seam must remain compatible.
- Remote-path quoting has one extracted implementation, one duplicate and one
  compatibility delegation. Published-port JSON parsing follows the same
  extracted-plus-delegation pattern.
- JSON/YAML parsing contracts are consumer-specific and must not be merged by
  textual similarity alone.
- Composition and preflight mappings are known consumers requiring ownership
  review; they are not silently added to the S189-02 migration scope.

## Rejected findings

- No additional production mapping was migrated solely because it appeared in
  the inventory.
- No new public boundary, ADR, domain/application import or service
  decomposition was invented in S189-01.
- No live Incus/LXD/Docker/Swarm, network, service, browser or external gate
  operation was run.
- Historical global `.codex/evidence/slice-01-*` files from Issue #188 were
  not modified; #189 uses the workflow-specific evidence directory.

## Files/evidence produced

- `.tiny-swarm-world/evidence/solid-lxc-shared-utilities/three-amigos.md`
- `.tiny-swarm-world/evidence/solid-lxc-shared-utilities/duplicate-inventory-before.md`
- `.codex/evidence/issue-189-20260809/slice-01-distribution.md`
- `.codex/evidence/issue-189-20260809/slice-01-consolidation.md`

The tracked requirement matrix remains open for implementation and final
verification evidence. No product Python source or test file changed in this
slice.

## Checks executed

- S3 status/branch/scope/classification — PASS.
- S3D metadata/dependency/topology/lock decision — PASS; three concrete slices,
  acyclic `S189-01 -> S189-02 -> S189-03`, serial execution.
- Static infrastructure inventory with `rg` — PASS; findings recorded above.
- `git diff --check` — PASS.
- `python3 tools/quality_gate.py quality` in WSL — PASS; policy consistency,
  Ruff, import-linter, architecture tests, mypy and `1678` tests passed with
  `28` skips.
- Live/browser/SonarQube checks — `NOT_APPLICABLE`/not run for this inventory
  slice; no success claim is made.

## Handoff decision

S189-02 may start after this checkpoint commit. It must first convert the
inventory into an explicit consumer/ownership decision, then implement only
the verified shared resolver/utilities and their tests. Any circular import,
public behavior drift, unclassified consumer or new ADR requirement remains a
stop condition.
