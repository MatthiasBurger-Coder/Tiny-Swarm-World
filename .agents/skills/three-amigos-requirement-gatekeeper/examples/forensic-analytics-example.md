# Forensic Analytics Example

## Input Requirement

Add runtime exception replay support for imported trace files and prepare the result for LLM-assisted diagnosis.

## Gate Report

### Normalized Requirement Summary

Business goal:

- Help analysts reconstruct exception context from imported runtime traces.

Technical goal:

- Add replay preparation after trace ingestion while preserving evidence provenance and separating LLM hypotheses from verified facts.

Scope:

- Runtime trace ingestion contract
- Replay input preparation
- LLM evidence package boundary
- Tests and documentation for evidence semantics

Non-goals:

- No live LLM provider call in unit tests
- No graph database migration unless the existing schema requires it
- No service extraction

### Three Amigos Findings

Requirement Analyst:

- Acceptance criteria must state which trace fields are required, optional and explicitly unknown.

System Architect:

- Runtime import remains an adapter concern.
- Replay orchestration belongs in application.
- Domain models must not depend on parser, graph or LLM provider APIs.

Quality Validator:

- Tests must verify missing trace fields remain incomplete, not fabricated.
- LLM prompt tests must use deterministic fake clients or captured prompt assertions.

### Dependency Summary

```text
trace contract
  -> importer mapping
  -> replay input model
  -> LLM evidence package
  -> documentation
```

No parallel implementation is ready until the trace contract is stable.

### Required Skills And Subagents

- `requirement-engineering`
- `architecture-hexagonal`
- `grpc-ingestion` if gRPC trace import is affected
- `replay-runtime-correlation-specialist`
- `quality-testing-strategy`
- Senior Java Backend
- Senior Tester
- Architecture reviewer

### Draft Slice Outline

Slice 01:

- Stabilize trace replay contract and acceptance criteria.

Slice 02:

- Implement importer-to-replay mapping after contract approval.

Slice 03:

- Prepare LLM evidence package without treating model output as evidence.

Slice 04:

- Add documentation and quality gate verification.

### Decision

```text
REQUIRES_REFINEMENT
```

Reason:

- Required trace fields and API ownership are not defined yet.
- Continuing would require guessing runtime event fields and replay contract shape.
