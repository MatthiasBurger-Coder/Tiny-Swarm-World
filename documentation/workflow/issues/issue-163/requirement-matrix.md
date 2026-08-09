# Requirement Matrix — Issue #163

Source: [GitHub Issue #163](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/163)

Status at workflow authoring: `PLANNED`; this matrix is the implementation
baseline and is not evidence of completion.

| ID | Requirement | Type | Planned implementation area | Slice | Verification/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-163-01 | Address all three consolidated `python:S1313` findings in the one focused test fixture change. | quality/security | `tests/domain/network/test_port_forwarding_plan.py` | S163-02/S163-03 | targeted test, quality gate, finding inventory | PLANNED |
| REQ-163-02 | Keep test intent clear when representing the sample addresses. | maintainability | named test constants/fixture helpers | S163-02/S163-03 | focused test review and output | PLANNED |
| REQ-163-03 | Do not change runtime configuration or production behavior. | architecture constraint | tests only; no `src/` or `infra/` changes | S163-01/S163-03 | changed-files check | PLANNED |
| REQ-163-04 | Preserve Linux/WSL semantics and avoid host-specific addresses as defaults. | platform constraint | test fixture values and documentation | S163-02/S163-03 | static scan and focused unittest | PLANNED |
| REQ-163-05 | Run the focused port-forwarding test. | quality gate | `tests/domain/network/test_port_forwarding_plan.py` | S163-04 | `PYTHONPATH=src python3 -m unittest tests.domain.network.test_port_forwarding_plan` | PLANNED |
| REQ-163-06 | Run the full local quality gate or record an exact environment blocker. | quality gate | repository gate | S163-04/S163-05 | `python3 tools/quality_gate.py quality` and evidence | PLANNED |
| REQ-163-07 | Keep external Sonar state separate from local verification and never claim unavailable remote success. | evidence integrity | issue evidence package | S163-01/S163-04/S163-05 | external state classification | PLANNED |

