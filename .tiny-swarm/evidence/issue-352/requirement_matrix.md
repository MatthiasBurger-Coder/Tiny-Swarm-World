# Issue #352 requirement matrix

All requirements are OPEN: planning is not implementation or verification. Parent: EPIC #313.

| ID | Requirement from issue | Type | Files likely affected | Implementation evidence | Test evidence | Status |
|---|---|---|---|---|---|---|
| R01 | Parse and validate external YAML/configuration before core consumption. | Architecture / functional | Slice 01–05 exact scopes in workflow.md | PLANNED: slice 01–05 | PLANNED: Surface inventory and adapter-to-consumer tests | OPEN |
| R02 | Isolate ruamel.yaml concerns. | Architecture | Slice 02,03,04,06 exact scopes in workflow.md | PLANNED: slice 02,03,04,06 | PLANNED: Parser ownership scan and negative import probes | OPEN |
| R03 | Isolate raw external mapping concerns. | Architecture | Slice 02–05 exact scopes in workflow.md | PLANNED: slice 02–05 | PLANNED: Typed port contracts and recursive boundary assertions | OPEN |
| R04 | Validate required values before mutation starts. | Resilience / security | Slice 03–05 exact scopes in workflow.md | PLANNED: slice 03–05 | PLANNED: Missing-value fixtures and zero-mutation spies | OPEN |
| R05 | Convert external config into typed/internal models. | Functional / architecture | Slice 02–04 exact scopes in workflow.md | PLANNED: slice 02–04 | PLANNED: Direct model and adapter conversion tests | OPEN |
| R06 | Prevent unchecked raw configuration propagating through orchestration. | Architecture | Slice 02–05 exact scopes in workflow.md | PLANNED: slice 02–05 | PLANNED: Consumer inventory and snapshot tests | OPEN |
| R07 | Application services do not depend on ruamel.yaml objects. | Architecture / quality | Slice 02,06 exact scopes in workflow.md | PLANNED: slice 02,06 | PLANNED: Import regression probes and nested returned-object assertions | OPEN |
| R08 | Invalid configuration fails before mutating lifecycle operations. | Resilience | Slice 05 exact scopes in workflow.md | PLANNED: slice 05 | PLANNED: Malformed later-phase input prevents all earlier mutation | OPEN |
| R09 | Internal configuration models are explicit and testable. | Architecture / quality | Slice 02–04 exact scopes in workflow.md | PLANNED: slice 02–04 | PLANNED: Direct invariant and model contract tests | OPEN |
| R10 | Supported configuration stays compatible or migration is documented. | Compatibility | Slice 01–06 exact scopes in workflow.md | PLANNED: slice 01–06 | PLANNED: Committed/synthetic fixtures, defaults and migration record | OPEN |
| R11 | Parsing/validation tests cover malformed and valid configurations. | Quality | Slice 02–06 exact scopes in workflow.md | PLANNED: slice 02–06 | PLANNED: Syntax, schema, required-field and supported-fixture tests | OPEN |

At execution, copy this matrix to .tiny-swarm/evidence/issue-352/requirement_matrix.md and replace planned entries with exact files, symbols, test names, commands and results. Inherited EPIC constraints: preserve supported Classic behavior, Linux/WSL, Incus/Swarm, consent, destructive-operation guards, credential precedence, redaction, exit/evidence semantics and hexagonal ownership. No unrelated domain redesign or generic framework.
