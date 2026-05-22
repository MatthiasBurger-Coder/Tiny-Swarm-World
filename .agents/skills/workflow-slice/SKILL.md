---
name: workflow-slice
description: Creates a structured slice-based implementation plan from a task, repository rules, and existing workflow documentation.
---

# Skill: Slice Workflow

## Description
Creates a structured slice-based implementation plan from a task, repository rules, and existing workflow documentation.

## Instructions
1. Read the user task.
2. Read AGENTS.md.
3. Read QUALITY.md.
4. Inspect relevant repository files.
5. Apply `workflow-authoring` when creating or regenerating `documentation/workflow`.
6. Apply `engineering-governance` when EPIC, arc42, requirement, resilience, quality or role synchronization is affected.
7. Identify the smallest meaningful implementation slices.
8. Order slices by dependency and risk.
9. Define done criteria for each slice.
10. Do not implement before the slice plan is complete.

## Expected Inputs
- user task
- AGENTS.md
- QUALITY.md
- existing workflow files
- relevant source files
- EPIC, arc42 and ADR files when governance synchronization is affected

## Expected Outputs
- ordered slice plan
- affected files per slice
- verification commands per slice
- risks and open points
- governance synchronization points when applicable

## Stop Conditions
Stop if:
- requirements are contradictory
- required files cannot be found
- the quality gate is unclear
- the requested change conflicts with architecture rules
- evidence semantics are unclear
