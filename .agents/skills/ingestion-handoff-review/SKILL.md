---
name: ingestion-handoff-review
description: Reviews engine-request, gRPC ingestion, payload descriptors, and cross-repo handoff contracts.
---

# Skill: Ingestion Handoff Review

## Description
Reviews engine-request, gRPC ingestion, payload descriptors, and cross-repo handoff contracts.

## Instructions
1. Locate engine-request reader/importer code.
2. Locate gRPC ingestion DTO mapping and validators.
3. Locate domain payload descriptors and payload kinds.
4. Locate CLI ingest-request behavior and summaries.
5. Compare documented producer fields with verified reader fields.
6. Check relative and absolute payload path handling.
7. Check missing payload, unknown kind, and malformed request diagnostics.
8. Define contract tests using explicit fixtures.

## Expected Inputs
- ingestion-request source files
- ingestion-grpc mapper and validator files
- domain ingestion model files
- CLI ingest-request tests
- producer contract documentation or verified producer fixtures

## Expected Outputs
- contract compatibility report
- unsupported field or kind list
- evidence-integrity risks
- regression test plan
- verification commands

## Stop Conditions
Stop if:
- producer field names cannot be verified
- payload kinds diverge
- missing payload behavior is unclear
- synthetic fixtures would be used as verified producer output
