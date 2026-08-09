# Requirement Matrix — Issue #184

Source: [Issue #184](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/184)

Execution status: `COMPLETED_LOCAL_AUDITED`; live/browser/external evidence is
not claimed.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-184-001 | Separate command execution/result, node lifecycle, lookup, profile, resource, failure, teardown and evidence responsibilities. | architecture/functional | `clients/lxc/{command,node,profile,resource}/` | responsibility maps, focused tests and full architecture gate | VERIFIED_LOCAL |
| REQ-184-002 | Keep `LxcNodeProvider` as lifecycle orchestration only. | architecture | `lxc_node_provider.py` facade plus extracted boundaries | legacy-module AST guard and import architecture gate | VERIFIED_LOCAL |
| REQ-184-003 | Preserve old imports or provide intentional compatibility shims. | compatibility | legacy module and package exports | legacy command-result import test and full regression | VERIFIED_LOCAL |
| REQ-184-004 | Preserve verify/ensure/reset/destroy behavior and public evidence classifications. | functional/evidence | node provider and extracted policy/resolution modules | 64 focused tests plus 1685-test quality gate | VERIFIED_LOCAL |
| REQ-184-005 | Reuse the #189 authoritative backend mapping and do not create a duplicate. | architecture | `lxc/command/backend_cli.py` | backend duplicate guard and import architecture checks | VERIFIED_LOCAL |
| REQ-184-006 | Create the required Three-Amigos, responsibility and evidence packages. | evidence/governance | `.tiny-swarm-world/evidence/solid-lxc-node-provider/` and `.tiny-swarm/evidence/solid-lxc-node-provider/` | required evidence package and completion audit | VERIFIED_LOCAL |
| REQ-184-007 | Keep live/browser verification opt-in and state-classified. | live-evidence | workflow and evidence records | verification-policy PASS; no live/browser/external green claim | VERIFIED_LOCAL |

## Execution evidence mapping

- REQ-184-001: `responsibility-map-before.md`, `responsibility-map-after.md`,
  extracted command/node/profile/resource modules, architecture tests.
- REQ-184-002: `tests/architecture/test_lxc_runtime_boundaries.py` and the
  legacy module's compatibility-only command imports.
- REQ-184-003: `tests/infrastructure/adapters/clients/lxc/command/test_node_command.py`
  plus the full local regression gate.
- REQ-184-004: `tests/infrastructure/adapters/clients/test_lxc_node_provider.py`,
  focused 64-test run and final 1685-test quality run.
- REQ-184-005: `tests/architecture/test_lxc_runtime_boundaries.py` backend-map
  guard and `lxc/command/backend_cli.py`.
- REQ-184-006: all required files in this directory, Three-Amigos and
  responsibility evidence under `.tiny-swarm-world/`, and the auditor report.
- REQ-184-007: `verification-state-policy` consistency check and explicit
  local-only state in `remaining_risks.md` and `issue-completion-audit.md`.
