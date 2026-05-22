---
name: analytics-persistence-review
description: Reviews persistence, stored evidence, generated summaries, provenance, and deterministic artifact behavior for the current project.
---

# Skill: Analytics Persistence Review

## Description
Reviews persistence, stored evidence, generated summaries, provenance, and deterministic artifact behavior for the current project.

## Instructions
1. Locate persistence ports, repositories, adapters, and generated output paths.
2. Locate stored ingestion payloads, analysis results, summaries, manifests, checksums, reports, or projections.
3. Check that evidence provenance, ordering, correlation identifiers, and statuses are preserved.
4. Check deterministic output ordering and reproducibility.
5. Check that projections and generated reports are not treated as primary evidence unless explicitly modeled.
6. Define tests for storage integrity and artifact integrity.

## Expected Inputs
- persistence source files
- output adapters
- generated summary/report files
- related tests
- README, QUALITY.md, and migration documentation

## Expected Outputs
- persistence impact analysis
- artifact integrity checklist
- deterministic output risks
- missing test list
- verification commands

## Stop Conditions
Stop if:
- schema or stored model changes are needed without a migration strategy
- generated artifacts cannot be reproduced deterministically
- cleanup or overwrite behavior is unclear
- evidence provenance would be lost
