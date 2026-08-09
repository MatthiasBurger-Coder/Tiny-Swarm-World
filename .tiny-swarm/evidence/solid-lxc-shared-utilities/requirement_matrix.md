# Requirement Matrix — Issue #189

Source: [Issue #189](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/189)

Authoring status: extracted before executable slices. S189-02 implementation,
local test evidence and S189-03 audit evidence are now recorded; live and
external evidence is not required for this local completion claim.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-189-001 | Maintain one authoritative Incus/LXD backend CLI mapping. | architecture/functional | `infrastructure/adapters/clients/lxc/command/backend_cli.py`, LXC clients, composition | Incus -> `incus`, LXD -> `lxc` tests and static duplicate-mapping guard | VERIFIED_LOCAL |
| REQ-189-002 | Centralize shared command-failure checks without absorbing adapter policy. | architecture/resilience | LXC command utilities and callers | focused failure classification tests | VERIFIED_LOCAL |
| REQ-189-003 | Centralize safe log truncation/sanitization. | security/observability | LXC diagnostics utility | redaction/truncation regression tests | VERIFIED_LOCAL |
| REQ-189-004 | Centralize manager-IP lookup only at the verified LXC responsibility boundary. | architecture/functional | LXC command/services utility and callers | manager-IP and failure-path tests | VERIFIED_LOCAL |
| REQ-189-005 | Centralize quote/path and JSON/YAML helpers only where ownership is shared. | architecture/functional | LXC command/services utilities | helper contract tests and import checks | VERIFIED_LOCAL |
| REQ-189-006 | Preserve existing public behavior and avoid circular imports. | architecture/quality | infrastructure adapters | architecture tests and full local quality gate | VERIFIED_LOCAL |
| REQ-189-007 | Create the required Three-Amigos and before/after duplicate inventory evidence. | evidence/governance | `.tiny-swarm-world/evidence/solid-lxc-shared-utilities/` | evidence package and audit review | VERIFIED_LOCAL |
| REQ-189-008 | Treat live/browser and external gates according to verification-state policy; do not claim skipped Selenium or Sonar success. | quality/live-evidence | workflow evidence | explicit state plus observable evidence if authorized | VERIFIED_LOCAL |

## Execution evidence mapping

| Requirement | Implementation evidence | Verification evidence |
|---|---|---|
| REQ-189-001 | `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/backend_cli.py` and migrated consumers | `tests/infrastructure/adapters/clients/lxc/command/test_backend_cli.py`, `tests/architecture/test_lxc_runtime_boundaries.py`, full quality gate |
| REQ-189-002 | `command_failed` in `lxc/command/diagnostics.py` with adapter compatibility wrappers | `tests/infrastructure/adapters/clients/lxc/command/test_diagnostics.py`, targeted LXC suites |
| REQ-189-003 | canonical `safe_log_text` and delegated legacy wrappers | diagnostics redaction/truncation test and full quality gate |
| REQ-189-004 | `lxc/services/common.py` manager-IP implementation and legacy delegation | common-service and Swarm runtime regression suites |
| REQ-189-005 | canonical Swarm path/port helpers with asset-transfer and legacy delegations; consumer-specific JSON/YAML retained | Swarm/path tests, import-linter and architecture tests |
| REQ-189-006 | compatibility facades, composition policy and infrastructure-only imports | full quality gate, Mypy, import-linter and LXC boundary guard |
| REQ-189-007 | `.tiny-swarm-world/evidence/solid-lxc-shared-utilities/{three-amigos,duplicate-inventory-before,duplicate-inventory-after}.md` | S189-03 completion evidence and independent audit |
| REQ-189-008 | workflow/context state explicitly marks live/browser/external checks not run | verification-policy consistency PASS and no live/external claim |
