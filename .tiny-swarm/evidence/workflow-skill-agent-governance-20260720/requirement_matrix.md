# Requirement Matrix

Workflow: `workflow-skill-agent-governance-20260720`

| ID | Requirement | Planned evidence | Status |
|---|---|---|---|
| REQ-001 | Complete inventory of discoverable skills and agents | Inventory report and registry consistency check | OPEN |
| REQ-002 | Classify all project skill entrypoints with valid activation metadata | `tools.skill_audit.audit()` returns 132 classifications across the governed class set | VERIFIED |
| REQ-003 | Implement an activation resolver that cannot alter command-strand gates | `.agents/activation/resolver.py`; `tests.architecture.test_activation_resolver` | VERIFIED |
| REQ-004 | Separate orchestrator responsibilities without public process-strand drift | `.agents/orchestrator/responsibility-model.md`; governance compatibility tests | VERIFIED |
| REQ-005 | Implement semantic registry auditing with blocking findings | Audit tool, fixtures and documented results | OPEN |
| REQ-006 | Provide complete compatibility regression coverage | `tests.architecture.test_governance_compatibility` | VERIFIED |
| REQ-007 | Synchronize registry, ownership and governance documentation | Registry parity tests, owner map and canonical registry documentation | VERIFIED |
| REQ-008 | Complete issue-level evidence and independent completion review | Required evidence package and `completion_audit.md` | VERIFIED |
| REQ-009 | Minimize runtime context and measure activation decisions | Resolver counts, activation audit, normalized evidence references | VERIFIED |

No requirement is marked complete until implementation and verification evidence
are present.
