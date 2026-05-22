---
name: analysis-storage-architect
description: Use for raw ingestion storage, normalized analysis stores, session storage, object storage, graph projection boundaries, indexing, partitioning, and trace correlation.
---

# Skill: Analysis Storage Architect

## Description

Guides evidence-first storage architecture for analysis sessions, raw inputs, normalized stores, artifacts, and projections.

## Instructions

1. Verify existing analysis store, artifact store, ingestion session, persistence, and workspace storage contracts.
2. Separate raw ingestion storage from normalized analysis stores, relational persistence, object storage, graph projection, and event-sourcing-style records.
3. Preserve analysis session storage, workspace IDs, repository references, payload identity, checksums, ordering, provenance, trace correlation, and completeness state.
4. Plan large payload handling, storage partitioning, indexing strategies, retention, and cleanup as explicit policies.
5. Treat graph databases, vector databases, reports, and LLM packages as projections unless repository documentation says otherwise.
6. Keep persistence implementation details in outbound adapters or infrastructure.
7. Ensure unknown, incomplete, unresolved, or unavailable evidence remains explicit in stored state.
8. Apply `.agents/skills/resilience-engineering/SKILL.md` for storage retry idempotency, dead-letter handling, retry provenance, cleanup, health checks and partial-write diagnostics.

## Expected Inputs

- domain analysis and ingestion models
- application storage ports
- persistence adapters
- workspace storage boundaries
- graph and report projection plans

## Expected Outputs

- storage responsibility map
- raw and normalized storage plan
- analysis session persistence plan
- payload and artifact indexing notes
- storage quality and migration risks

## Boundaries

- Do not choose a database product without an approved architecture slice.
- Do not store LLM output as verified evidence.
- Do not collapse raw payloads, normalized facts, and projections into one ambiguous structure.

## Stop Conditions

Stop if:

- storage table, port, or model names cannot be verified;
- persistence would overwrite raw inputs or lose provenance;
- graph projection would become the source of truth;
- large payload handling lacks deterministic identity.
