---
name: distributed-systems-architect
description: Use for distributed analysis-platform design, long-running job orchestration, worker lifecycle, backpressure, retry, consistency, and failure recovery planning.
---

# Skill: Distributed Systems Architect

## Description

Guides distributed project platform design while keeping orchestration in application services and concrete infrastructure in adapters.

## Instructions

1. Verify the current module layout, `AGENTS.md`, `QUALITY.md`, and relevant workflow documentation before proposing changes.
2. Model long running analysis jobs with explicit lifecycle states, idempotent processing, retry strategies, worker leasing, backpressure, and failure recovery.
3. Keep consistency models explicit. Do not hide eventual consistency, partial failure, duplicate delivery, or unavailable worker output.
4. Prefer event-driven architecture only when the event contract, ordering, idempotency key, and replay behavior are documented.
5. Keep queue, worker-runtime, scheduler, and transport products outside domain and application. Represent them behind ports.
6. Preserve evidence provenance, job attempts, worker identity, input artifact references, output artifact references, and completeness state.
7. Plan worker/workspace interaction before parser, Joern, graph, replay, or LLM execution work.
8. Apply `.agents/skills/resilience-engineering/SKILL.md` for retries, backoff, circuit breakers, bulkheads, idempotency, dead-letter handling, retry provenance and graceful degradation.

## Expected Inputs

- `AGENTS.md`
- `QUALITY.md`
- `settings.gradle.kts`
- workflow or workflow files
- analysis job and worker domain models
- ingestion, workspace, persistence, and adapter contracts

## Expected Outputs

- distributed job orchestration plan
- worker leasing and retry model
- backpressure and failure recovery notes
- consistency and idempotency decisions
- quality-gate and integration-test plan

## Boundaries

- Do not choose a concrete queue, scheduler, service mesh, or worker runtime without an approved implementation slice.
- Do not implement parsers, Joern execution, BTM generation, graph engines, replay engines, or UI work from this skill.
- Do not infer missing runtime facts from static source or worker status.

## Stop Conditions

Stop if:

- job state names, worker contracts, or storage contracts cannot be verified;
- a proposed retry would duplicate evidence or overwrite raw inputs;
- failure recovery would require fabricating missing facts or hiding incomplete evidence;
- architecture decisions conflict with `AGENTS.md` or `QUALITY.md`.
