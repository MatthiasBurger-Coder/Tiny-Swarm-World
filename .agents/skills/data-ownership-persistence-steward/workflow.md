# Workflow

## Phase 1 - Identify Data Scope

Classify affected data as:

- relational data
- graph projection
- event stream
- vector index
- file/object artifact
- runtime trace data
- read model or projection

## Phase 2 - Assign Ownership

For each data type, identify:

- owner service or module
- writer
- readers
- access path
- retention or cleanup expectation
- evidence provenance requirements

## Phase 3 - Choose Persistence Model

Use `persistence-decision-matrix.md`.

The storage choice must be justified by access pattern, evidence semantics, consistency needs, query model and operational risk.

## Phase 4 - Review Cross-Service Access

Non-owner services may read through:

- owner API
- published event
- documented projection
- defined query interface

Direct database access to another service's private store is forbidden.

## Phase 5 - Validate Quality And Security

Require:

- deterministic tests for mapping or projection behavior;
- security review for sensitive source, stack trace, runtime or personal data;
- observability review when correlation identifiers are stored or propagated;
- ADR review for durable architectural decisions.

## Phase 6 - Report

Produce a data ownership report with decision, risks, blockers and required follow-up.
