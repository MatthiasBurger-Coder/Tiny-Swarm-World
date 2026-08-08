# Issue #183 Requirement Matrix

Issue: [#183 SOLID: Split lxc_swarm_runtime.py into cohesive LXC client modules](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/183)
Workflow: `issue-183-20260808`
Status at workflow creation: `READY_FOR_WORKFLOW`; implementation has not started.

| ID | Requirement from issue | Type | Files likely affected | Implementation evidence | Test/evidence verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | Keep public ports and observable behavior stable. | Contract | Existing application ports; extracted adapters; compatibility facade | Stable port implementations and compatibility exports | Port contract tests, regression suite, composition tests | OPEN |
| REQ-002 | Extract LXC manager shell execution into a reusable command gateway/runner. | Architecture/functional | `lxc/command/`, legacy module | Gateway implementation and legacy delegation | Command gateway tests for backend, quoting, retry, timeout, diagnostics | OPEN |
| REQ-003 | Move Swarm stack deployment logic into a cohesive Swarm runtime module. | Architecture/functional | `lxc/swarm/swarm_stack_runtime.py` | Extracted `PortSwarmStackRuntime` implementation | Stack deployment/readiness regression tests | OPEN |
| REQ-004 | Move stack asset handling into a dedicated asset-transfer module. | Architecture/functional | `lxc/swarm/stack_asset_transfer.py` | Extracted asset transfer and rendering behavior | Tar/path/asset-content tests with temporary files | OPEN |
| REQ-005 | Move stack prerequisite handling into a registry with Strategy-style handlers for Traefik, SonarQube, and Swagger. | Architecture/functional | `lxc/swarm/stack_prerequisite_registry.py` | Registry and stack-specific handlers | Strategy selection/order/idempotency tests | OPEN |
| REQ-006 | Move `LxcContainerRuntime` into an LXC Docker runtime module. | Architecture/functional | `lxc/docker/lxc_container_runtime.py` | Extracted container runtime adapter | Container lookup/file-read tests | OPEN |
| REQ-007 | Move Portainer admin/client and Nexus HTTP wrappers into `lxc/services/`. | Architecture/functional | `lxc/services/` | Extracted service adapters | HTTP mapping, auth, endpoint, stack, repository tests | OPEN |
| REQ-008 | Move image publisher and `PublicImagePullRejected` into `lxc/images/`. | Architecture/functional | `lxc/images/` | Extracted image adapter and error types | Image availability/publish/rate-limit/context tests | OPEN |
| REQ-009 | Introduce the requested package structure under `lxc/command`, `lxc/swarm`, `lxc/services`, `lxc/images`, and `lxc/docker`. | Architecture | New infrastructure package files | Package layout and exports | Import/type/architecture checks | OPEN |
| REQ-010 | Keep compatibility imports in `lxc_swarm_runtime.py` so existing code and tests do not break. | Compatibility | Legacy module and consumers | Explicit `__all__`/re-exports or thin facade | Existing imports, patch targets, and composition tests | OPEN |
| REQ-011 | Do not change application ports unless absolutely required. | Architecture/constraint | `src/tiny_swarm_world/application/ports/**` | No port diff, or separately approved blocker evidence | `git diff`, architecture review, port contract tests | OPEN |
| REQ-012 | Do not change external runtime behavior. | Functional/safety | Extracted adapters and composition | Behavior-preserving delegation | Full focused and regression suites; live evidence if required | OPEN |
| REQ-013 | Update composition imports gradually. | Architecture | `composition.py`, `composition_lxc_runtimes.py` | Concrete extracted imports and compatibility transition | Composition construction and provider-selection tests | OPEN |
| REQ-014 | Add focused unit tests for each extracted module. | Quality | `tests/infrastructure/adapters/clients/lxc/**` | Module-specific test files | Targeted unittest commands and full test gate | OPEN |
| REQ-015 | Add architecture tests preventing unrelated growth in the legacy runtime module. | Quality/architecture | `tests/architecture/test_lxc_runtime_boundaries.py` | Responsibility/import/class-count guard | `arch-tests`, targeted architecture test | OPEN |
| REQ-016 | Store a before/after module responsibility map in issue evidence. | Evidence | `.tiny-swarm/evidence/solid-lxc-swarm-runtime/` | `responsibility-map-before.md`, `responsibility-map-after.md` | Evidence review and changed-file mapping | OPEN |
| REQ-017 | Reduce `lxc_swarm_runtime.py` to compatibility exports or a thin facade. | Acceptance/architecture | Legacy module | Thin facade with no new mixed implementation | Static module inspection and architecture test | OPEN |
| REQ-018 | Ensure each extracted class has one clear reason to change. | Acceptance/architecture | All extracted modules | Responsibility map and package boundaries | System Architect review; architecture tests | OPEN |
| REQ-019 | Implement stack-specific behavior through Strategy/registry-like modules, not hard-coded growth in the runtime. | Acceptance/architecture | Swarm prerequisite modules | Registry/strategies and slim runtime | Strategy tests and static boundary check | OPEN |
| REQ-020 | Preserve the issue-specified Selenium imports exactly. | Live test contract | `tests/live/` | Test source imports `webdriver` and `By` | Static test and test collection | OPEN |
| REQ-021 | Use Selenium to open/reuse a live LXC-backed installation and the service-access/dashboard gateway URL. | Live E2E | `tests/live/`; live evidence | Authorized live test execution | Redacted E2E evidence and run result | OPEN |
| REQ-022 | Locate at least one visible service link or status element with `By`, and assert the page is not blank with expected content visible. | Live E2E | `tests/live/` | Browser flow and assertions | `LIVE_VERIFIED` evidence | OPEN |
| REQ-023 | Store E2E evidence under `.tiny-swarm-world/evidence/solid-lxc-swarm-runtime/e2e/`. | Evidence/live | Local evidence writer/config | Issue-specific evidence root | Evidence path and redaction check | OPEN |
| REQ-024 | Existing test suite and new extracted-module tests must pass. | Quality | Repository tests | Test result evidence | `python3 tools/quality_gate.py test` | OPEN |
| REQ-025 | SonarQube quality gate must return an accepted passing result. | External quality | CI/SonarQube result | Observable external status | `EXTERNAL_GATE_VERIFIED` result linked in evidence | OPEN |
| REQ-026 | No new critical/high code smells may be introduced. | External quality | Extracted source and SonarQube | Before/after quality comparison | SonarQube result and review evidence | OPEN |
| REQ-027 | Three-Amigos note must cover stable ports/behavior, extraction design, and unit/integration/E2E proof, and disagreement stops implementation. | Governance | `three-amigos.md` | Reviewed note with decisions | Four-role review and no-disagreement record | OPEN |
| REQ-028 | Complete issue evidence and independent completion audit before DONE. | Governance | Evidence package | Required evidence files and audit decision | Issue Completion Auditor returns `PASS` | OPEN |

Implementation may not begin while a requirement is missing from this matrix,
while a public-contract disagreement remains, or while the Three-Amigos gate
has not been recorded.
