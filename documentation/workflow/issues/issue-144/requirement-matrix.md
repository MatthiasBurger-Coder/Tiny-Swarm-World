# Requirement Matrix — Issue #144

Source: [GitHub Issue #144](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/144)

Status at workflow authoring: `PLANNED`.

| ID | Requirement | Type | Planned implementation area | Slice | Verification/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-144-01 | Inventory every install-path retry loop that can execute under setup/deployment and artifact preparation. | functional | named services plus verified search inventory | S144-01 | source inventory | PLANNED |
| REQ-144-02 | No install-path workflow blocks the event loop with `time.sleep()`. | functional | Nexus, SonarQube and Infisical readiness paths | S144-02/S144-03/S144-04/S144-05 | source scan and tests | PLANNED |
| REQ-144-03 | Retry semantics remain functionally equivalent with explicit timeout, interval, attempt and result behavior. | resilience | async readiness contracts | S144-02/S144-03/S144-04/S144-05 | unit tests | PLANNED |
| REQ-144-04 | Progress/event publication continues during readiness waits. | UX/observability | progress port and orchestration | S144-06 | callback interleaving test | PLANNED |
| REQ-144-05 | Blocking transport fallback, if needed, is isolated behind a named async boundary such as `asyncio.to_thread()`. | architecture | infrastructure clients/application wrappers | S144-02/S144-05 | boundary review | PLANNED |
| REQ-144-06 | Targeted tests cover Nexus, SonarQube and Infisical readiness/bootstrap paths. | quality gate | corresponding test modules | S144-07 | unittest commands | PLANNED |
| REQ-144-07 | Tests prove at least one progress callback runs between two retry waits. | testability | deterministic test doubles | S144-06/S144-07 | async test evidence | PLANNED |
| REQ-144-08 | Performance evidence records old/new wait-loop behavior or new non-blocking timing behavior. | performance evidence | shared #152 contract | S144-07 | evidence artifact | PLANNED |
| REQ-144-09 | Do not add nested event loops, busy waiting or ad hoc background threads. | architecture constraint | async implementation | S144-02/S144-08 | architecture/test review | PLANNED |

