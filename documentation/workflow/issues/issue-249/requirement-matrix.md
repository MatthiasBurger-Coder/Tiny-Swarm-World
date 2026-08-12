# Requirement Matrix — Issue #249

| ID | Requirement from issue/request | Type | Files likely affected | Implementation evidence | Test/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-249-01 | Create and track a new GitHub issue for the remaining composition-root block. | process | GitHub issue #249, workflow | Issue #249 exists and is open. | Connector result and workflow reference. | VERIFIED |
| REQ-249-02 | Keep `tiny_swarm_world.infrastructure.composition` as the public facade. | architecture/compatibility | `composition.py`, callers/tests | Public builder functions and compatibility imports remain available. | Facade import tests and full composition tests. | VERIFIED |
| REQ-249-03 | Move operator environment configuration and validation out of the facade. | maintainability/configuration | `composition_configuration.py`, `composition.py` | Focused configuration module owns constants/accessors/validation. | Positive and invalid configuration tests. | VERIFIED |
| REQ-249-04 | Move detailed platform, artifact, deployment, and setup runtime wiring into focused modules. | architecture | `composition_platform.py`, `composition_artifacts.py`, `composition_deployment.py`, `composition_setup.py`, `composition.py` | Boundary modules own the concrete builder bodies; runtime retains only compatibility bridges and shared helpers. | Wiring and architecture tests. | VERIFIED |
| REQ-249-05 | Move synchronous readiness and direct host/registry probing out of the facade. | architecture/resilience | `composition_probes.py`, `composition.py` | Probe/readiness implementation lives in focused module and remains bounded/async-aware. | Fake-session readiness tests and negative-path tool/file behavior tests. | VERIFIED |
| REQ-249-06 | Preserve defaults, errors, placeholder secrets, provider selection, live consent, deployment order, service-access behavior, and evidence semantics. | compatibility/safety | extracted modules, deployment composition, tests | Existing behavior is preserved, including facade patch seams and async setup. | 111 focused tests plus full regression suite. | VERIFIED |
| REQ-249-07 | Preserve hexagonal dependency direction and avoid live mutations during construction. | architecture/safety | infrastructure modules, architecture tests | Concrete adapters stay in infrastructure and constructors remain non-mutating. | import/process-spawn architecture tests; mocked tests. | VERIFIED |
| REQ-249-08 | Update tests and relevant arc42 documentation, then run local quality verification. | quality/documentation | tests, `documentation/arc42/05_building_blocks.adoc`, `documentation/arc42/06_runtime_view.adoc`, evidence | Documentation matches verified structure and evidence records exact commands/results. | focused tests, `python3 tools/quality_gate.py quality`, `git diff --check`. | VERIFIED |
| REQ-249-09 | Do not claim live Docker/Swarm/LXC/Incus/browser/SonarQube success from local checks. | verification governance | workflow/evidence | Live/external states are classified honestly. | verification-state evidence. | VERIFIED |

Requirement Lead: Senior Requirement Engineer

System Architect Reviewer: Senior System Architect

Test / Evidence Reviewer: Senior Tester

Completion Auditor: issue-completion-auditor, independent of implementation.

Any `OPEN`, guessed, conflicting, or unverified row blocks `DONE`; no such row
remains after implementation and evidence review.
