# Requirement Matrix — ARCH-03.06

Issue: [ARCH-03.06] Introduce Runtime Port and Docker Swarm Adapter (#349)

| ID | Requirement | Type | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| REQ-001 | Application services depend on a runtime abstraction, not concrete Docker code. | Architecture constraint | Deployment use cases consume `PortSwarmStackRuntime`; `DockerSwarmRuntime` implements the boundary. | Import-linter, architecture tests, focused adapter tests. | DONE |
| REQ-002 | Existing Docker Swarm behavior is preserved. | Functional requirement | `DockerSwarmRuntime` delegates all proven operations to `LxcSwarmRuntime`. | 114 focused tests and 2079 full tests pass. | DONE |
| REQ-003 | Concrete runtime wiring occurs only in composition/bootstrap. | Architecture constraint | Composition constructs the LXC transport and injects it into `DockerSwarmRuntime`. | Composition tests and mypy pass. | DONE |
| REQ-004 | Port operations reflect proven current use cases rather than speculative future APIs. | Architecture constraint | Port surface remains limited to deployment, inspection, and external-secret operations. | Port implementation review and application call-site inspection. | DONE |
| REQ-005 | Runtime adapter tests cover success and failure translation. | Quality requirement | Adapter tests cover successful delegation and propagation of transport failures for workflow translation. | Focused tests and full quality gate pass. | DONE |
