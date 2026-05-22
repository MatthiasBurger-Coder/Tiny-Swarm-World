---
name: replay-graph-llm-review
description: Reviews replay, graph projection, reporting, and LLM evidence-package behavior without treating generated or inferred output as verified evidence.
---

# Skill: Replay Graph LLM Review

## Description
Reviews replay, graph projection, reporting, and LLM evidence-package behavior without treating generated or inferred output as verified evidence.

## Instructions
1. Locate replay, graph, report, or LLM-related code and documentation.
2. Identify the explicit evidence inputs.
3. Check how missing or incomplete evidence is represented.
4. Check deterministic ordering and provenance preservation.
5. Check that graph projections and reports remain derived views.
6. Check that LLM prompts are built from structured evidence and that LLM output is labeled as generated analysis.
7. Define tests that do not require external graph databases or live LLM providers unless explicitly isolated.

## Expected Inputs
- domain and application evidence models
- graph, replay, report, or LLM adapters
- prompt templates or report templates
- related tests
- QUALITY.md

## Expected Outputs
- evidence-integrity findings
- uncertainty-handling risks
- provider-isolation risks
- test plan
- verification commands

## Stop Conditions
Stop if:
- runtime execution would be inferred from static facts alone
- graph edges would be invented
- replay steps would hide missing trace events
- LLM output would be treated as confirmed fact
- live providers would be required for default unit tests
