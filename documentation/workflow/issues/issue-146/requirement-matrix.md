# Requirement Matrix — Issue #146

Source: [GitHub Issue #146](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/146)

Status at workflow authoring: `PLANNED`.

| ID | Requirement | Type | Planned implementation area | Slice | Verification/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-146-01 | Confirm node-level Docker operations are independent and do not share mutable host state. | architecture | node runtime contract | S146-01 | independence matrix | PLANNED |
| REQ-146-02 | Extract inspect → install-if-needed → verify into a per-node coroutine. | functional | `application/services/platform/incus/lxc_docker_install.py` | S146-02 | unit tests | PLANNED |
| REQ-146-03 | Run node operations concurrently with bounded concurrency. | performance/resilience | service scheduler/semaphore | S146-03 | concurrency-limit test | PLANNED |
| REQ-146-04 | Preserve deterministic node-name/configured-order result aggregation. | behavior | aggregation helpers | S146-04 | out-of-order fixture test | PLANNED |
| REQ-146-05 | Preserve manager/worker role semantics in evidence. | observability | verification evidence | S146-04 | evidence assertions | PLANNED |
| REQ-146-06 | Isolate one node failure and report node, role, operation phase and original error. | resilience | per-node failure result | S146-04 | mixed success/failure tests | PLANNED |
| REQ-146-07 | Keep Swarm-level operations and shared host package-manager work outside the scope. | non-goal/safety | workflow boundary | S146-01/S146-06 | changed-files audit | PLANNED |
| REQ-146-08 | Produce timing evidence comparing serial-equivalent assumptions with concurrent duration where practical. | performance evidence | shared #152 contract | S146-05 | evidence artifact | PLANNED |
