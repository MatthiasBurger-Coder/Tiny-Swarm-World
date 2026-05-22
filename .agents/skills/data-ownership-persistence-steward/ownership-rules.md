# Ownership Rules

## Core Rules

- Every data type has exactly one owner.
- Every write path has exactly one owner service or module.
- Non-owner reads use API, event, projection or documented query interface.
- Cross-service database access is forbidden.
- Shared tables must not be used as hidden service coupling.
- Runtime events must preserve correlation and ordering information where available.
- Evidence records must preserve provenance and completeness state.

## Owner Responsibilities

The owner defines:

- canonical schema or model;
- write validation rules;
- retention and cleanup expectations;
- provenance requirements;
- compatibility rules;
- read interfaces for other services.

## Reader Responsibilities

Readers must:

- treat projections as copies, not canonical ownership;
- preserve source owner identity where relevant;
- not mutate owner data indirectly;
- document staleness and consistency expectations.

## STOP Rules

Stop when:

- owner cannot be named;
- write path is shared;
- read path bypasses owner boundary;
- retention or sensitive-data handling is unclear for runtime or source evidence.
