# Requirement Matrix — Issue #197

Source: [GitHub Issue #197](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/197)

Status at workflow authoring: `PLANNED`.

| ID | Requirement | Type | Planned implementation area | Slice | Verification/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-197-01 | `composition.py` no longer owns subprocess-based Socat process management. | architecture | new infrastructure adapter plus composition wiring | S197-02/S197-04 | source scan and composition test | PLANNED |
| REQ-197-02 | WSL Socat behavior remains infrastructure-only and does not leak into domain/application services. | architecture | `infrastructure/adapters/network/**` and existing ports | S197-02/S197-04 | architecture tests/import scan | PLANNED |
| REQ-197-03 | Live mutation still requires explicit accepted `LiveConsent`. | safety | Socat adapter/step guard | S197-03/S197-05 | no-consent test and guard evidence | PLANNED |
| REQ-197-04 | Native Linux no-op remains covered. | behavior | Socat adapter tests | S197-05 | targeted unittest | PLANNED |
| REQ-197-05 | Missing consent remains covered. | behavior | Socat adapter tests | S197-05 | targeted unittest | PLANNED |
| REQ-197-06 | Missing `socat`, existing process, and both start outcomes remain covered. | behavior | adapter process boundary | S197-03/S197-05 | mocked subprocess tests | PLANNED |
| REQ-197-07 | Tests do not run live Socat, LXC, Incus or Docker commands. | safety/quality | test doubles and guards | S197-01/S197-05 | command-mutation scan | PLANNED |
| REQ-197-08 | Run focused tests and the full local quality gate. | quality gate | repository gate | S197-05/S197-06 | exact command evidence | PLANNED |
