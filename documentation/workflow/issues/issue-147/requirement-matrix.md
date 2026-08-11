# Requirement Matrix — Issue #147

Source: [GitHub Issue #147](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/147)

Status at workflow authoring: `PLANNED`.

| ID | Requirement | Type | Planned implementation area | Slice | Verification/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-147-01 | Apply-failure recovery does not run a redundant full verification pass before normal post-apply verification. | functional | `ensure_service_stack.py` | S147-02 | failure-path test | PLANNED |
| REQ-147-02 | Step-local stack registration data is reused where safe. | performance | deployment workflow state | S147-03 | call-count test | PLANNED |
| REQ-147-03 | Remote/API call count for a single stack apply is measurably reduced. | performance evidence | Portainer/LXC gateway path | S147-03/S147-04/S147-05 | mocked call-count evidence | PLANNED |
| REQ-147-04 | Existing deployment workflow semantics remain unchanged. | regression | deployment service and result contracts | S147-02/S147-05 | regression tests/full gate | PLANNED |
| REQ-147-05 | Cache/snapshot invalidation rules are explicit and step-scoped. | resilience | state object/docs | S147-03/S147-04 | stale-data test and code docs | PLANNED |
| REQ-147-06 | Stale step-local data cannot suppress a required retry refresh. | safety | lookup refresh policy | S147-04/S147-05 | negative test | PLANNED |
| REQ-147-07 | Success and failure paths assert expected stack-registration lookup counts. | quality gate | deployment tests | S147-05 | unit test evidence | PLANNED |
