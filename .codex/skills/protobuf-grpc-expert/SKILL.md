---
name: protobuf-grpc-expert
description: Use for Protobuf and gRPC contract changes, API messages, streaming design, DTO mapping, validation, compatibility review, retries, deadlines, cancellation, sizing, and correlation or request identity preservation.
---

# Protobuf gRPC Expert

Use this skill for `.proto` files, generated gRPC contracts, transport mapping, request validation, streaming decisions, payload sizing, retries, deadlines, cancellation, and request identity preservation.

## Authoritative Sources

Read, when present:

- root `AGENTS.md`
- root `QUALITY.md`
- existing `.proto` files
- generated package configuration
- gRPC service, validator, mapper, and adapter code
- project-specific gRPC, Protobuf, resilience, or API skills under `.agents/`

## Rules

- Verify existing `.proto` files, generated package names, service classes, validators, and mappers before changing contracts.
- Keep Protobuf DTOs and generated gRPC classes out of domain and application code unless the project explicitly defines a different boundary.
- Preserve field numbers and names unless the task explicitly requires a contract change.
- Represent missing optional data explicitly.
- Preserve correlation, session, trace, request, tenant, or evidence identifiers exactly when the project defines them.
- Apply project resilience guidance for retries, deadlines, cancellation, idempotency, and retry provenance.

## Stop Conditions

Stop when field names, RPC methods, package names, schema versions, retry behavior, or mapping contracts cannot be verified exactly.
