---
name: migration-workflow
description: Plans and executes repository, module, or cross-repo migrations in small, verifiable slices while preserving architecture, evidence integrity, and quality rules.
---

# Skill: Migration Workflow

## Description
Plans and executes repository, module, or cross-repo migrations in small, verifiable slices while preserving architecture, evidence integrity, and quality rules.

## Instructions
1. Inspect the source project.
2. Inspect the target project.
3. Identify reusable implementation parts.
4. Identify incompatible assumptions.
5. Create a migration slice plan.
6. Preserve architecture boundaries and evidence semantics.
7. Run the narrowest meaningful verification after each implementation slice.
8. Document risks and open points.

## Expected Inputs
- source repository
- target repository
- migration task
- AGENTS.md
- QUALITY.md
- migration workflow if present

## Expected Outputs
- migration plan
- ordered slices
- files to move or adapt
- verification plan
- risks and unresolved questions

## Stop Conditions
Stop if:
- source and target architecture conflict
- required source files cannot be found
- target quality gate is unclear
- migration would require speculative behavior changes
- evidence or runtime facts would need to be invented
