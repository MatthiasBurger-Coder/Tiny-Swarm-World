---
name: grpc-ingestion
description: Use for gRPC ingestion adapter work, service mapping, transport validation, and correlation preservation.
---

# gRPC

## Purpose

Guide inbound gRPC adapter work while keeping transport concerns outside the domain and application core.

## Practices

- Keep Protobuf DTO mapping inside the gRPC adapter.
- Validate transport-level fields before creating application requests.
- Preserve correlation, session and evidence identifiers exactly.
- Apply `.agents/skills/resilience-engineering/SKILL.md` for gRPC deadlines, cancellation, bounded retries, idempotency, retry provenance and degraded transport behavior.
- Do not treat transport metadata as domain evidence unless the contract says so.
- Keep service methods thin and delegate use cases to application ports.

## Verification

- Inspect existing service and mapper classes before changing contracts.
- Add adapter tests for DTO mapping and validation behavior.
- Run affected module tests and the relevant quality gate from `QUALITY.md`.
