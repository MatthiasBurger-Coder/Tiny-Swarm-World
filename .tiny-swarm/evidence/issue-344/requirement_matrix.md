# Requirement Matrix — #344 / ARCH-03.01

Parent: #313 — EPIC 03

| ID | Requirement from issue | Type | Files likely affected | Implementation evidence | Test/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Inventory `__main__.py`, `installer.py`, `simple_installer.py`, `infrastructure/composition.py`, and root-level mixed-import modules. | Audit | `src/tiny_swarm_world/**` | The audit records all requested modules and identifies the three root-level mixed-import modules. | `dependency-map.md`, source inventory commands in `test_results.md` | DONE |
| REQ-002 | Produce a source-level dependency map. | Audit | `src/tiny_swarm_world/**` | Layer and direct-import maps are documented, including composition submodules. | `dependency-map.md` | DONE |
| REQ-003 | Identify forbidden dependency direction. | Architecture | `src/tiny_swarm_world/**`, `.importlinter`, `tests/architecture/**` | Existing protected-layer rules and edge bypasses are recorded separately. | `test_results.md`, `python3 tools/quality_gate.py arch-lint`, `arch-tests` | DONE |
| REQ-004 | Identify direct Docker/runtime access. | Architecture | `__main__.py`, `installer.py`, composition modules | Runtime/provider construction and command strings are mapped to owners. | `dependency-map.md`, `violation-inventory.md` | DONE |
| REQ-005 | Identify direct subprocess, filesystem, and environment access. | Architecture | `__main__.py`, `installer.py`, `simple_installer.py`, composition modules | Direct access sites and their current responsibilities are inventoried. | `violation-inventory.md` | DONE |
| REQ-006 | Identify runtime-specific branching. | Architecture | `__main__.py`, `installer.py`, composition modules | Linux/WSL, Incus, provider, and Windows bridge branches are classified. | `violation-inventory.md` | DONE |
| REQ-007 | Identify raw configuration objects crossing boundaries. | Architecture | entrypoints, installers, composition | `Namespace`, environment mappings, paths, and raw composition service bundles are recorded as boundary debt where applicable. | `violation-inventory.md` | DONE |
| REQ-008 | Identify duplicated lifecycle behavior. | Maintainability | installer and entrypoint surfaces | Legacy installer/simple-installer delegation and duplicated presentation/orchestration surfaces are documented. | `responsibility-ownership.md` | DONE |
| REQ-009 | Identify circular dependencies. | Architecture | `infrastructure/composition_*.py` | A five-module composition cycle is recorded with its compatibility cause. | `dependency-map.md`, `test_results.md` | DONE |
| REQ-010 | Classify responsibilities using the required categories. | Architecture | audit documents | Every audited surface is classified as one or more required responsibility categories. | `responsibility-ownership.md` | DONE |
| REQ-011 | Give every cross-boundary finding an intended owner and migration path. | Remediation | audit documents | Each finding has an owner boundary, next migration slice, and sequencing note. | `responsibility-ownership.md`, `violation-inventory.md` | DONE |
| REQ-012 | Rank critical violations separately from maintainability debt. | Prioritization | audit documents | Findings use `CRITICAL`, `HIGH`, `MEDIUM`, or `DEBT`; critical/high boundary risks are separated from debt. | `violation-inventory.md` | DONE |
| REQ-013 | Do not propose refactoring solely because of file size. | Constraint | audit documents | Findings are justified by dependency, responsibility, technology access, or lifecycle coupling; line counts are context only. | `architecture-violation-map.md` | DONE |
| REQ-014 | Establish a baseline for later architecture fitness checks. | Governance | audit documents, existing architecture tests | Baseline rules, exception set, and repeatable checks are recorded. | `architecture-violation-map.md`, `test_results.md` | DONE |
| REQ-015 | Document the audit in the repository and relate it to EPIC #313. | Documentation | `documentation/arc42/05_analysis/**`, `.tiny-swarm/evidence/issue-344/**` | The audit links back to #313 and the evidence package contains the requirement trace. | `architecture-violation-map.md` | DONE |
