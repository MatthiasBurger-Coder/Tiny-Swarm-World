---
name: source-analysis-pipeline
description: Reviews and plans changes in repository source ingestion, static source facts, semantic analysis artifacts, and unresolved-reference handling.
---

# Skill: Source Analysis Pipeline

## Description
Reviews and plans changes in repository source ingestion, static source facts, semantic analysis artifacts, and unresolved-reference handling.

## Instructions
1. Locate repository source input configuration.
2. Locate source scanner ports and adapters.
3. Locate source fact and source location models.
4. Locate semantic analysis ports and adapters.
5. Check context preservation for packages, modules, classes, methods, and source locations.
6. Check deterministic output ordering.
7. Check that static facts are not treated as proof of runtime execution.
8. Define regression tests for source facts and semantic artifacts.
9. Apply `.agents/skills/resilience-engineering/SKILL.md` for parser execution timeouts, retry safety, partial source facts, cleanup, diagnostics and degraded behavior.

## Expected Inputs
- repository source adapter files
- domain/application source models
- semantic analysis adapter files
- source fact fixtures or tests
- related issue or finding

## Expected Outputs
- pipeline impact analysis
- correctness risks
- regression test plan
- implementation slices
- verification commands

## Stop Conditions
Stop if:
- source context is lost and no safe propagation model is defined
- unresolved references would be silently dropped
- scanner and adapter responsibilities are unclear
- runtime facts would be inferred from static structure alone
