# Requirement Matrix — Issue #186

Source: [Issue #186](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/186)

Final status: `VERIFIED_LOCAL`. The repository-wide audit confirmed that the
named global DI scope is absent; explicit composition wiring is guarded and no
new container was introduced.

| ID | Requirement | Type | Likely implementation area | Verification expectation | Status |
|---|---|---|---|---|---|
| REQ-186-001 | Audit all usages of the named global container and DI decorators. | architecture/evidence | repository-wide source/test scan | complete usage inventory | VERIFIED_LOCAL |
| REQ-186-002 | Prefer explicit composition-root wiring for workflow/runtime dependencies. | architecture | `infrastructure/composition*.py` | composition wiring tests | VERIFIED_LOCAL |
| REQ-186-003 | If a container remains necessary, support deterministic instance, type and factory bindings and clear failures. | functional/resilience | verified DI module only if found | binding/lifetime tests | VERIFIED_LOCAL (NOT_APPLICABLE: no container remains) |
| REQ-186-004 | Do not allow infrastructure/application services to resolve dependencies globally at runtime. | architecture | application/infrastructure boundaries | architecture/static guard | VERIFIED_LOCAL |
| REQ-186-005 | Preserve required backwards-compatible imports only when justified. | compatibility | verified compatibility surfaces | import tests and deprecation evidence | VERIFIED_LOCAL (NOT_APPLICABLE: no DI compatibility surface exists) |
| REQ-186-006 | Create the required Three-Amigos and before/after dependency map evidence. | evidence/governance | `.tiny-swarm-world/evidence/solid-di-container/` | evidence audit | VERIFIED_LOCAL |
| REQ-186-007 | If the audit confirms no remaining issue scope, record a bounded no-op/residual decision rather than inventing a container. | scope/quality | issue evidence and workflow handoff | auditor review | VERIFIED_LOCAL |

Final matrix decision: all requirements are `VERIFIED_LOCAL`; requirements
REQ-186-003 and REQ-186-005 are explicitly classified `NOT_APPLICABLE` because
the audited repository contains no DI container or compatibility surface.
