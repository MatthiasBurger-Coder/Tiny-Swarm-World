---
name: quality-archunit-review
description: Reviews Python regression tests, import-linter contracts, architecture tests, and local quality-gate impact for a planned or completed slice.
---

# Skill: Architecture Quality Review

## Description
Reviews Python regression tests, import-linter contracts, architecture tests, and local quality-gate impact for a planned or completed slice.

## Instructions
1. Read QUALITY.md.
2. Inspect affected production files.
3. Inspect affected tests.
4. Identify required Python regression tests.
5. Identify required import-linter or architecture-test boundary checks.
6. Identify whether broader quality-gate coverage is affected.
7. Select the narrowest meaningful verification command.
8. Escalate to the full quality gate when Python tooling, architecture, command construction, YAML parsing, path handling, repositories, adapters, or deployment automation behavior changes.

## Expected Inputs
- QUALITY.md
- changed files
- related tests
- Python tooling files if quality behavior is affected

## Expected Outputs
- test adequacy review
- missing test list
- architecture-check impact
- coverage risk
- verification commands
- pass/fail summary

## Stop Conditions
Stop if:
- the quality gate is unclear
- coverage would need to be weakened
- architecture rules would need to be relaxed
- verification cannot be executed and no reason is documented
