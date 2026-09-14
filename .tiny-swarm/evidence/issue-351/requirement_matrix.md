# ARCH-03.08 Requirement Matrix

| ID | Requirement | Type | Implementation | Verification | Status |
|---|---|---|---|---|---|
| REQ-351-01 | Lifecycle responsibilities are decomposed into cohesive application orchestration. | architecture | `PlatformLifecycleOrchestrator` owns dispatch only; existing capability workflows retain their responsibilities. | Focused lifecycle dispatch tests. | PASS |
| REQ-351-02 | Extracted services use explicit input/output models. | architecture | `PlatformLifecycleRequest` and existing `PlatformWorkflowResult`; `PlatformLifecycleWorkflows` models dependencies. | Typecheck and focused tests. | PASS |
| REQ-351-03 | Dependencies are injected through existing/new justified ports. | architecture | Orchestrator receives `PlatformLifecycleWorkflows` protocols; Composition performs concrete binding. | Architecture gate and composition test. | PASS |
| REQ-351-04 | Orchestration remains a readable workflow, not a technology script. | quality | Typed `match` dispatch contains no provider, shell, filesystem, or YAML logic. | Static inspection and architecture tests. | PASS |
| REQ-351-05 | Install/setup/reconcile behavior remains compatible. | functional | Existing workflow implementations and setup phase ordering unchanged; CLI delegates through compatibility-aware orchestrator. | 208 focused regression tests. | PASS |
