# Requirement Matrix — ARCH-03.07

Issue: [ARCH-03.07] Separate Desired State, Current State and Reconcile Planning (#350)

| ID | Requirement | Type | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| REQ-001 | Desired and current state are represented explicitly for reconciliation. | Architecture constraint | Typed `DesiredState` and `CurrentState` domain models project existing inventory models. | Domain model tests and full quality gate. | DONE |
| REQ-002 | Planning can be unit-tested without live infrastructure. | Quality requirement | Pure `ReconcilePlanner` accepts only state values and returns a plan. | Planner unit tests with in-memory fixtures. | DONE |
| REQ-003 | Plan output is deterministic for equivalent inputs. | Non-functional requirement | Planner sorts resource kinds/names and emits immutable tuples. | Determinism and ordering tests. | DONE |
| REQ-004 | Execution remains a separate responsibility. | Architecture constraint | `ReconcilePlan` is data-only; no command runner, Docker, filesystem, or mutation dependency. | Import-linter, architecture tests, and source inspection. | DONE |
| REQ-005 | Existing Classic reconcile behavior is preserved or explicitly documented where corrected. | Functional/architecture requirement | Existing platform reconcile workflow is unchanged; new planner is additive and not wired into live execution. | Existing platform tests, full quality gate, and Arc42 scope note. | DONE |
