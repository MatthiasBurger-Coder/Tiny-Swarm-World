# Governance Inventory

Generated for workflow `workflow-skill-agent-governance-20260720`.

- Project skill entrypoints: **132**
- Project skill entrypoints with YAML frontmatter: **132**
- Registry-declared project entrypoints: **132**
- Registry-declared valid metadata: **132**
- Codex/system skill entrypoints: **6** (external to project registry)

Verification commands:

```text
find .agents/skills -name SKILL.md | wc -l
PYTHONPATH=src python3 -m unittest tests.architecture.test_skill_registry_integrity
```

The registry integrity test is the authoritative executable check. Detailed
classification and activation metadata remain open for later slices.
