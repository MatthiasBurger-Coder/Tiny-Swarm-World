# Requirement Matrix — #345 / ARCH-03.02

Parent: #313 — EPIC 03

| ID | Requirement from issue | Type | Files likely affected | Implementation evidence | Test/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Document formal dependency contracts for domain, application, ports, infrastructure, interfaces, and bootstrap/composition. | Architecture / documentation | `.importlinter`, `documentation/arc42/05_analysis/arch-03-02-layer-contracts.md` | Layer vocabulary, allowed direction, and exception policy are recorded. | Architecture contract tests; `git diff --check` | DONE |
| REQ-002 | Domain must not import infrastructure or interfaces. | Architecture constraint | `.importlinter`, `tests/architecture/test_hexagonal_imports.py` | Forbidden-import contract and AST regression test. | `arch-lint`, `arch-tests` | DONE |
| REQ-003 | Application must not import concrete infrastructure adapters or CLI code. | Architecture constraint | `.importlinter`, `tests/architecture/test_hexagonal_imports.py` | Concrete-adapter and CLI forbidden-prefix checks. | `arch-lint`, `arch-tests` | DONE |
| REQ-004 | Infrastructure may depend on application/domain contracts; interfaces may depend on application services; bootstrap/composition may know concrete adapters. | Architecture constraint | `documentation/arc42/05_analysis/arch-03-02-layer-contracts.md`, architecture tests | Allowed-owner matrix and positive direction tests document permitted inward dependencies. | `arch-tests` | DONE |
| REQ-005 | Root-level modules must not bypass the layer contracts. | Architecture constraint | `tests/architecture/test_hexagonal_imports.py`, root modules | Root boundary allowlist rejects direct adapter, process, filesystem, and CLI bypasses while preserving named legacy exceptions. | `arch-tests` | DONE |
| REQ-006 | A deliberately introduced forbidden import must fail CI. | Quality-gate requirement | `tests/architecture/test_hexagonal_imports.py` | Tests exercise the contract evaluator against synthetic forbidden imports. | `arch-tests` | DONE |
| REQ-007 | Existing justified exceptions must be explicit and traceable. | Governance | `documentation/arc42/05_analysis/arch-03-02-layer-contracts.md`, tests | Exception registry names owner, rationale, migration slice, and permitted surface; test verifies registry paths exist. | `arch-tests` | DONE |
| REQ-008 | Do not add a new exception merely to keep the build green. | Governance / quality | `.importlinter`, architecture tests, evidence | No new exception is added; tests fail closed for unregistered bypasses. | `arch-tests`, full quality gate | DONE |
