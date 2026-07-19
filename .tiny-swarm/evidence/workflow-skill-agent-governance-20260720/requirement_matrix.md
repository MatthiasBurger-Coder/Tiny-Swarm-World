# Requirement Matrix

| ID | Requirement | Planned verification/evidence | Status |
|---|---|---|---|
| GOV-001 | Inventory all entries under the mandated governance paths. | `current_skill_inventory.md`, `rg --files` inventory command, Registry Conflict Auditor review. | IN_PROGRESS |
| GOV-002 | Preserve `workflow create` semantics and boundaries. | `workflow_create_regression.md`, routing characterization tests. | OPEN |
| GOV-003 | Preserve `workflow execute` semantics and boundaries. | `workflow_execute_regression.md`, executor compatibility tests. | OPEN |
| GOV-004 | Preserve `push auto` semantics and merge guards. | `push_auto_regression.md`, publication-rule tests. | OPEN |
| GOV-005 | Preserve `skills update` as the skills-agents strand. | routing audit and governance review. | OPEN |
| GOV-006 | Classify every discoverable skill as core, conditional or external. | `classification_decisions.md`, registry audit. | OPEN |
| GOV-007 | Add complete machine-readable activation metadata. | schema audit and metadata tests. | OPEN |
| GOV-008 | Implement a resolver that cannot change command strands or mandatory gates. | resolver tests and negative cases. | OPEN |
| GOV-009 | Internally separate orchestration responsibilities without public behavior changes. | `orchestrator_compatibility_analysis.md`, golden-master tests. | OPEN |
| GOV-010 | Implement a semantic registry audit with blocking errors. | `semantic_audit_results.md`, `tools/skill_audit.py`. | OPEN |
| GOV-011 | Keep external skills from implicit activation. | resolver negative tests and registry audit. | OPEN |
| GOV-012 | Keep registry, owner map and organigramm consistent. | parity audit and documentation review. | OPEN |
| GOV-013 | Generate all required evidence and receive independent completion PASS. | evidence directory, Issue Completion Auditor. | OPEN |
| GOV-014 | Do not change `src/tiny_swarm_world/infrastructure/composition.py`. | changed-files review and git diff. | VERIFIED_SCOPE_BOUNDARY |

Open requirements intentionally block DONE until later slices provide implementation and evidence.
