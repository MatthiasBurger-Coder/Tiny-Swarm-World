# S449-PORTAINER-ENDPOINT-STACK consolidation

Status: IMPLEMENTED AND SSH QUALITY VERIFIED; CHECKPOINT PENDING.

Both direct and LXC apply paths use a shared resolver to compare two visible endpoint and stack inventories before stack or overlay-network effects. Malformed identities, visible duplicate or foreign-endpoint target names, ambiguous endpoint selection and snapshot drift block with fixed errors. Inventory reads require HTTP 200 and do not follow redirects. Endpoint URL, type and status participate in drift checking; local fallback rejects multiple visible alias/socket candidates. Existing no-prune updates, create and 404/405 fallback remain. Direct raw `update_stack` bypasses this lookup.

This is a visibility-limited improvement: list responses may omit stacks. It does not establish global absence, ownership, atomicity, convergence or host admission; concurrent changes can occur after recheck. The guide records these limitations and the unproven legacy create fallback.

## Reviews and verification

Six roles reviewed the v1.70 design and S3D issued EXECUTION_PLAN on clean `ad7571932bf97a5d0b0472e8c0fb4ecba529ee04`. Final Security and Architecture GO cover the HTTP client and helper hashes below; Architecture also covers the LXC client. Tester GO covers final HTTP/helper and reviewed tests including the LXC test. Requirement GO covers the final source tuple. Python GO covers the final HTTP client and helper; DevOps GO covers slice scope and those same two hashes. See distribution for exact scope.

Independent reviews identified incomplete snapshot error tests, ambiguous alias/socket fallback, omitted URL/type/status fingerprinting, permissive inventory status and implicit HTTP redirect following. The candidate addresses these, with tests across both apply paths, four inventory read positions, raw-update bypass and legacy create/fallback. The previous full quality run failed grown-critical-class and grown-module-complexity. Splitting the resolver into a dedicated infrastructure helper preserved behavior without changing quality thresholds or baselines.

The integration owner reports exact-candidate SSH PC WSL Python 3.14 tar SHA-256 prefix `856c5e4a`: targeted 113 tests PASS; Ruff PASS; `python3 tools/quality_gate.py quality` exit 0, 3,443 tests run, 37 skipped, 206.805 seconds. `git diff --check` passed. Python 3.12 and live host execution were not tested; implementation tests used mocks and an isolated Requests transport.

## Candidate SHA-256

- HTTP client: `26369f497da6d8e3018a5d80b6a2cbd261f65b8590b419f8510f5ff4081ddfe5`
- Resolution helper: `92234b036d8b8f0b1aa447f627405b3fd073fc5941bc10762dc29c1d7dd5b6cb`
- LXC client: `3b90241b116ad6a721d0475938f19038d62281d1d56121b70ea9b522d9134f1f`
- HTTP tests: `7d6e190d991abdf444f660e5928f005cc56f8c4301e1b5f837af657f5b4f000b`
- LXC tests: `39b8f8dcf9f55476df56c709e6421944d9f48e9941a980170ec0ab70a9199780`
- Runtime tests: `fed3bdbb4614a8fb54e4360ff20a7d80d5cd7fb732d811d637d2e065864404f9`
- User guide: `c8e66de7199d09366b88bba307f7ebb718dedd7904db00abd86f241ceae4cd43`

## CP_RECORD

- sliceId: S449-PORTAINER-ENDPOINT-STACK
- workflowVersion: 1.70
- sliceTitle: Visible Portainer endpoint and stack conflict rejection
- responsibleRole: Senior Python Automation Developer; root integration owner
- changedFiles: src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py,
  src/tiny_swarm_world/infrastructure/adapters/clients/portainer_apply_resolution.py,
  src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_portainer_http_client.py,
  tests/infrastructure/adapters/clients/test_portainer_http_client.py,
  tests/infrastructure/adapters/clients/lxc/services/test_lxc_service_clients.py,
  tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py,
  documentation/user_guide/component-updates.md,
  .codex/evidence/slice-449-portainer-endpoint-stack-distribution.md,
  .codex/evidence/slice-449-portainer-endpoint-stack-consolidation.md
- qualityCommands: PYTHONPATH=src python3 -m unittest
  tests.infrastructure.adapters.clients.test_portainer_http_client
  tests.infrastructure.adapters.clients.lxc.services.test_lxc_service_clients
  tests.infrastructure.adapters.clients.test_lxc_swarm_runtime
  tests.application.services.deployment.test_ensure_portainer_endpoint
  tests.infrastructure.adapters.exceptions.test_operation_failure_mapping;
  direct Ruff on changed Python files; python3 tools/quality_gate.py quality;
  git diff --check
- qualityResult: PASS on designated SSH PC WSL Python 3.14; 113 targeted tests,
  Ruff, full quality exit 0, 3,443 tests run, 37 skipped, 206.805 seconds
- rollbackReference: ad7571932bf97a5d0b0472e8c0fb4ecba529ee04
- arc42Updated: false
- adrUpdated: false
- commitSha: pending checkpoint commit
- limitations: Python 3.12 and live host execution untested. No global absence, ownership, atomicity, convergence or live admission established.
