---
name: joern-semantic-analysis
description: Reviews and plans optional Joern Docker / CPG semantic enrichment without breaking the default analytics quality gate.
---

# Skill: Joern Semantic Analysis

## Description
Reviews and plans optional Joern Docker / CPG semantic enrichment without breaking the default analytics quality gate.

## Instructions
1. Locate Joern adapter files.
2. Verify that Joern remains optional in the default gate.
3. Check command construction and process execution boundaries.
4. Check generated Joern artifacts and artifact collection.
5. Check application-port isolation.
6. Check deterministic artifact references, summaries, and checksums where present.
7. Define tests that do not require a real Joern installation unless explicitly marked integration-only.
8. Apply `.agents/skills/resilience-engineering/SKILL.md` for Joern timeout, retry, cleanup, optional-runtime health, dead-letter and degraded-mode decisions.

## Expected Inputs
- Joern adapter files
- application semantic analysis port files
- testbed files
- README and migration documentation
- related tests

## Expected Outputs
- semantic enrichment impact analysis
- optional-runtime risk assessment
- adapter-boundary checklist
- test plan
- verification commands

## Stop Conditions
Stop if:
- Joern would become required for normal verification
- tests would require unavailable Docker or Joern without an explicit opt-in marker
- artifact paths or checksums cannot be verified
- Joern APIs would leak into domain or application code
