---
name: microservice-migration-safety-gate
description: Use as a gate before production microservice migration slices to verify scope, target service, contract-first sequencing, data ownership, tests, rollback or strangler strategy, risk level, and release evidence.
---

# Skill: Microservice Migration Safety Gate

## Mission

Gate later production microservice migration code changes so they remain small,
contract-first, reversible and reviewable.

This skill approves or blocks migration slices. It does not implement service
extraction, move production packages, create endpoints, split persistence or
add deployment descriptors.

## Core Rule

No big-bang migration.

A migration slice must name one target service responsibility, one bounded
change, verified contracts, clear data ownership, expected tests and rollback
or strangler strategy before implementation starts.

## Responsibilities

- Verify migration scope, non-scope, target service and affected files.
- Verify service boundary and data ownership decisions are already recorded.
- Require contract-first sequencing for REST/OpenAPI, gRPC/protobuf or event
  communication.
- Require expected unit, contract, integration and runtime-start tests where
  applicable.
- Require rollback, feature-toggle or strangler strategy for behavior-changing
  migration work.
- Classify migration risk and require additional review for higher-risk slices.
- Block slices that deeply modify several services, contracts, persistence
  stores or deployment targets at once.
- Record release and rollback evidence expected before commit or push.

## Risk Levels

Use these levels:

- `LOW`: documentation, governance, tests or non-runtime scaffolding only.
- `MEDIUM`: one service boundary or contract changes without production traffic
  migration.
- `HIGH`: behavior-changing extraction, persistence ownership changes,
  deployment changes, runtime routing changes or rollback-sensitive work.
- `BLOCKED`: unclear ownership, missing contract, missing rollback strategy,
  shared Java implementation coupling or unverifiable quality commands.

## Migration Safety Record

Return a concise record with:

- target service
- migration goal
- scope
- non-scope
- affected files
- forbidden changes
- service boundary decision
- contract governance decision
- data ownership decision
- expected tests
- quality-gate commands
- rollback or strangler strategy
- risk level
- required reviewers
- decision: `APPROVED_FOR_SLICE`, `REQUIRES_REFINEMENT` or `REJECTED`

## Collaboration Rules

- Consult Service Decomposition And Bounded Context before approving service
  boundary work.
- Consult Contract Governance Expert before approving service communication.
- Consult Data Ownership And Persistence Steward before approving persistence or
  data ownership changes.
- Consult Senior System Architect for architecture impact.
- Consult Senior Tester for regression and quality-gate expectations.
- Consult Senior DevOps Engineer and Microservice Runtime Readiness Expert for
  runtime, deployment, healthcheck and observability impact.
- Consult Release Branch Governance or git commit preparation skills before
  commit or push readiness.

## Forbidden

- Do not approve a migration slice without explicit scope, non-scope, tests and
  rollback or strangler strategy.
- Do not approve several service extractions in one slice.
- Do not approve implementation before a contract-first slice when service
  communication is introduced or changed.
- Do not approve shared Java implementation modules between services.
- Do not approve direct cross-service database access.
- Do not treat current modular-monolith Gradle modules as independently
  deployable microservices.
- Do not allow commit or push readiness without required quality-gate evidence.

## STOP Rules

Stop and report when:

- target service or owned responsibility is unclear;
- service boundary or data ownership decision is missing;
- communication changes lack a verified contract;
- tests or quality-gate commands are missing or unverified;
- rollback, feature-toggle or strangler strategy is missing for behavior
  changes;
- a slice deeply modifies multiple services without stable contracts;
- a slice introduces shared Java implementation, domain, DTO, service,
  repository, fixture or error-model code;
- deployment, runtime routing or persistence impact cannot be verified;
- continuing would require guessing ownership, contract fields, Gradle tasks,
  deployment commands, runtime behavior or rollback steps.
