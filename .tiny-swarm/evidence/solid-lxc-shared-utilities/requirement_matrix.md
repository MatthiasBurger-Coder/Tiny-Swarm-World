# Requirement Matrix — Issue #189

Source: [Issue #189](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/189)

Authoring status: extracted before executable slices; implementation evidence
and test evidence remain open until workflow execution.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-189-001 | Maintain one authoritative Incus/LXD backend CLI mapping. | architecture/functional | `infrastructure/adapters/clients/lxc/command/backend_cli.py`, LXC clients, composition | Incus -> `incus`, LXD -> `lxc` tests and static duplicate-mapping guard | OPEN |
| REQ-189-002 | Centralize shared command-failure checks without absorbing adapter policy. | architecture/resilience | LXC command utilities and callers | focused failure classification tests | OPEN |
| REQ-189-003 | Centralize safe log truncation/sanitization. | security/observability | LXC diagnostics utility | redaction/truncation regression tests | OPEN |
| REQ-189-004 | Centralize manager-IP lookup only at the verified LXC responsibility boundary. | architecture/functional | LXC command/services utility and callers | manager-IP and failure-path tests | OPEN |
| REQ-189-005 | Centralize quote/path and JSON/YAML helpers only where ownership is shared. | architecture/functional | LXC command/services utilities | helper contract tests and import checks | OPEN |
| REQ-189-006 | Preserve existing public behavior and avoid circular imports. | architecture/quality | infrastructure adapters | architecture tests and full local quality gate | OPEN |
| REQ-189-007 | Create the required Three-Amigos and before/after duplicate inventory evidence. | evidence/governance | `.tiny-swarm-world/evidence/solid-lxc-shared-utilities/` | evidence package and audit review | OPEN |
| REQ-189-008 | Treat live/browser and external gates according to verification-state policy; do not claim skipped Selenium or Sonar success. | quality/live-evidence | workflow evidence | explicit state plus observable evidence if authorized | OPEN |
