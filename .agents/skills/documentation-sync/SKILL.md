---
name: documentation-sync
description: Keeps project documentation, examples, workflow files, ADRs, architecture docs, and process instructions consistent with the current implementation.
---

# Skill: Documentation Sync

## Description
Keeps project documentation, examples, workflow files, ADRs, architecture docs, and process instructions consistent with the current implementation.

## Documentation Governance Nodes

`DOCROOT` checks global documentation consistency for process documentation,
role model, organigramm, arc42 structure, governance rules, workflow
conventions and hard boundaries.

Local documentation nodes update concrete artifacts:

- `S1_DOC`: skills-agents documentation.
- `S2_DOC`: workflow-create documentation.
- `S3_DOC`: workflow-execute documentation.

Do not treat `DOCROOT` as a local documentation step or a fourth process
strand.

## Instructions
1. Inspect README files.
2. Inspect AGENTS.md.
3. Inspect QUALITY.md.
4. Inspect workflow files.
5. Inspect ADR, arc42, migration, and example files.
6. Compare documented commands with build files.
7. Identify stale examples, outdated commands, non-English repository documentation, and contradictory instructions.
8. Apply `engineering-governance` when EPIC, arc42, ADR, workflow, skill, role, quality or resilience synchronization is affected.
9. Apply `arc42-architecture-governance` when architecture documentation changes.
10. Apply `requirement-engineering` when requirement assumptions or EPIC consistency are affected.
11. Propose documentation-only slices.

## Expected Inputs
- README files
- AGENTS.md
- QUALITY.md
- workflow files
- ADRs and architecture docs
- examples
- build files
- related governance skills and roles

## Expected Outputs
- documentation findings
- stale sections
- proposed corrections
- documentation-only slice plan
- governance synchronization notes when applicable

## Stop Conditions
Stop if:
- implementation behavior cannot be verified
- documentation contradicts itself
- a documented command cannot be validated
- documentation presents unverified evidence as fact
