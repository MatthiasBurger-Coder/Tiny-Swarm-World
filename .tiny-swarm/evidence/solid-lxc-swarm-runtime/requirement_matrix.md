# Issue #183 Requirement Matrix

Issue: [#183 SOLID: Split lxc_swarm_runtime.py into cohesive LXC client modules](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/183)
Workflow: `issue-183-20260808`
Status at final audit: `BLOCKED_EXTERNAL`; local and approved live browser
verification are complete where marked, but external acceptance is not green.

| ID | Requirement from issue | Type | Files likely affected | Implementation evidence | Test/evidence verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | Keep public ports and observable behavior stable. | Contract | Existing application ports; extracted adapters; compatibility facade | No application-port diff; compatibility facades and extracted adapters | Full local suite `1,633` passed; composition/runtime tests | VERIFIED_LOCAL |
| REQ-002 | Extract LXC manager shell execution into a reusable command gateway/runner. | Architecture/functional | `lxc/command/`, legacy module | `manager_shell_gateway.py`, diagnostics, legacy delegation | Slice 02 focused suite `65` passed | VERIFIED_LOCAL |
| REQ-003 | Move Swarm stack deployment logic into a cohesive Swarm runtime module. | Architecture/functional | `lxc/swarm/swarm_stack_runtime.py` | `LxcSwarmStackRuntime` | Slice 03 direct/legacy suites `71` passed | VERIFIED_LOCAL |
| REQ-004 | Move stack asset handling into a dedicated asset-transfer module. | Architecture/functional | `lxc/swarm/stack_asset_transfer.py` | `StackAssetTransfer` | Direct asset tests and runtime regression tests | VERIFIED_LOCAL |
| REQ-005 | Move stack prerequisite handling into a registry with Strategy-style handlers for Traefik, SonarQube, and Swagger. | Architecture/functional | `lxc/swarm/stack_prerequisite_registry.py` | Ordered registry with network, Traefik TLS, SonarQube, and Swagger strategy hooks | Registry strategy tests; no live commands | VERIFIED_LOCAL |
| REQ-006 | Move `LxcContainerRuntime` into an LXC Docker runtime module. | Architecture/functional | `lxc/docker/lxc_container_runtime.py` | Extracted `LxcContainerRuntime` | Direct Docker runtime tests and regression suite | VERIFIED_LOCAL |
| REQ-007 | Move Portainer admin/client and Nexus HTTP wrappers into `lxc/services/`. | Architecture/functional | `lxc/services/` | Extracted Portainer/Nexus adapters and common address helper | Direct service tests and regression suite | VERIFIED_LOCAL |
| REQ-008 | Move image publisher and `PublicImagePullRejected` into `lxc/images/`. | Architecture/functional | `lxc/images/` | Extracted image publisher, errors, diagnostics | Direct image tests and regression suite | VERIFIED_LOCAL |
| REQ-009 | Introduce the requested package structure under `lxc/command`, `lxc/swarm`, `lxc/services`, `lxc/images`, and `lxc/docker`. | Architecture | New infrastructure package files | All requested packages and exports exist | Mypy, Ruff, import-linter, architecture tests | VERIFIED_LOCAL |
| REQ-010 | Keep compatibility imports in `lxc_swarm_runtime.py` so existing code and tests do not break. | Compatibility | Legacy module and consumers | `__all__`, facades, aliases, dynamic patch seams | Existing imports, composition, and runtime tests | VERIFIED_LOCAL |
| REQ-011 | Do not change application ports unless absolutely required. | Architecture/constraint | `src/tiny_swarm_world/application/ports/**` | No application-port changes | Diff review and full quality gate | VERIFIED_LOCAL |
| REQ-012 | Do not change external runtime behavior. | Functional/safety | Extracted adapters and composition | Compatibility delegation and unchanged command/error behavior | Local regression suite passed; live behavior unverified | VERIFIED_LOCAL_WITH_LIVE_GAP |
| REQ-013 | Update composition imports gradually. | Architecture | `composition.py`, `composition_lxc_runtimes.py` | Composition imports extracted concrete modules | `157` targeted composition/runtime tests | VERIFIED_LOCAL |
| REQ-014 | Add focused unit tests for each extracted module. | Quality | `tests/infrastructure/adapters/clients/lxc/**` | Direct command, Swarm, Docker, service, and image tests | Focused suites plus full test gate | VERIFIED_LOCAL |
| REQ-015 | Add architecture tests preventing unrelated growth in the legacy runtime module. | Quality/architecture | `tests/architecture/test_lxc_runtime_boundaries.py` | Composition ownership and public facade guard | Targeted and full architecture tests | VERIFIED_LOCAL |
| REQ-016 | Store a before/after module responsibility map in issue evidence. | Evidence | `.tiny-swarm/evidence/solid-lxc-swarm-runtime/` | Before map exists; after map added in Slice 07 | Evidence package review | VERIFIED_LOCAL |
| REQ-017 | Reduce `lxc_swarm_runtime.py` to compatibility exports or a thin facade. | Acceptance/architecture | Legacy module | Public Swarm facade, three service facades, and compatibility aliases only | Boundary test now rejects every non-approved class definition; 69 focused tests passed | VERIFIED_LOCAL |
| REQ-018 | Ensure each extracted class has one clear reason to change. | Acceptance/architecture | All extracted modules | Responsibility map and package boundaries | Architecture review and tests | VERIFIED_LOCAL |
| REQ-019 | Implement stack-specific behavior through Strategy/registry-like modules, not hard-coded growth in the runtime. | Acceptance/architecture | Swarm prerequisite modules | Registry and ordered strategies | Strategy tests and boundary review | VERIFIED_LOCAL |
| REQ-020 | Preserve the issue-specified Selenium imports exactly. | Live test contract | `tests/live/` | Selenium `webdriver` and `By` imports retained | Static browser contract collection | VERIFIED_LOCAL |
| REQ-021 | Use Selenium to open/reuse a live LXC-backed installation and the service-access/dashboard gateway URL. | Live E2E | `tests/live/`; live evidence | Consent-gated live harness executed against the configured installation | Browser suite `31` tests passed | VERIFIED_LIVE |
| REQ-022 | Locate at least one visible service link or status element with `By`, and assert the page is not blank with expected content visible. | Live E2E | `tests/live/` | Selenium route contract and authenticated flows executed | All nine routed browser results passed | VERIFIED_LIVE |
| REQ-023 | Store E2E evidence under `.tiny-swarm-world/evidence/solid-lxc-swarm-runtime/e2e/`. | Evidence/live | Local evidence writer/config | Issue-specific root configured | `e2e/suite-summary.json` and route evidence; all nine passed | VERIFIED_LIVE |
| REQ-024 | Existing test suite and new extracted-module tests must pass. | Quality | Repository tests | Full local quality result | `1,633` passed, `28` skipped | VERIFIED_LOCAL |
| REQ-025 | SonarQube quality gate must return an accepted passing result. | External quality | CI/SonarQube result | Baseline HTTP findings were remediated locally; SonarCloud still needs a fresh branch analysis | Public status remains `ERROR` on `main`; workflow branch has no analysis | BLOCKED_EXTERNAL |
| REQ-026 | No new critical/high code smells may be introduced. | External quality | Extracted source and SonarQube | Local quality and boundary gates pass; external before/after comparison is still unavailable | Branch API exposes only `main` at `50733ea`; no issue-specific comparison | BLOCKED_EXTERNAL |
| REQ-027 | Three-Amigos note must cover stable ports/behavior, extraction design, and unit/integration/E2E proof, and disagreement stops implementation. | Governance | `three-amigos.md` | Three-Amigos gate records stable contracts, design, and verification plan | Review recorded with no disagreement | VERIFIED_LOCAL |
| REQ-028 | Complete issue evidence and independent completion audit before DONE. | Governance | Evidence package | Slice 07 evidence package and independent audit | Audit result is `BLOCKED`, not PASS | BLOCKED |

Implementation may not begin while a requirement is missing from this matrix,
while a public-contract disagreement remains, or while the Three-Amigos gate
has not been recorded.
