---
name: replay-runtime-correlation-specialist
description: Use for runtime replay planning, trace stitching, correlation models, temporal sequencing, causality graphs, and stacktrace enrichment review.
---

# Skill: Replay Runtime Correlation Specialist

## Description

Guides runtime correlation and replay planning without fabricating execution facts or implementing a replay engine prematurely.

## Instructions

1. Verify runtime trace, ingestion, exception, correlation, and analysis-session contracts before proposing replay-related changes.
2. Keep runtime replay, execution reconstruction, trace stitching, temporal sequencing, causality graphs, stacktrace enrichment, and runtime path reconstruction evidence-based.
3. Distinguish observed runtime events, derived ordering, static source context, unresolved gaps, and hypotheses.
4. Preserve correlation IDs, trace IDs, span IDs, parent span IDs, process context, timestamps, ordering, and completeness markers when available.
5. Apply distributed tracing concepts only when the required identifiers exist in verified inputs.
6. Plan replay as a later analysis capability after workspace, repository checkout, and session registration are reliable.
7. Keep generated or LLM-produced explanation separate from verified runtime evidence.

## Expected Inputs

- runtime trace schemas or fixtures
- exception and stacktrace models
- analysis session and workspace context
- source snapshot and checkout identity
- replay workflow requirements

## Expected Outputs

- correlation model review
- trace stitching and sequencing plan
- replay input prerequisites
- gap and uncertainty representation
- test scenarios for incomplete traces

## Boundaries

- Do not implement replay engines from this skill.
- Do not infer branch execution, parameters, return values, or causality from source structure alone.
- Do not merge unrelated correlation IDs.

## Stop Conditions

Stop if:

- required correlation fields cannot be verified;
- runtime facts would need to be invented;
- stacktrace enrichment would hide missing source or trace data;
- replay output would present speculative paths as executed paths.
