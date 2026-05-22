---
name: grpc-streaming-specialist
description: Use for gRPC and Protobuf contract design, unary and streaming RPCs, chunked uploads, retries, compression, sizing, and plugin-to-server communication.
---

# Skill: gRPC Streaming Specialist

## Description

Guides gRPC/Protobuf design for plugin-to-analytics communication while keeping transport mapping in adapters.

## Instructions

1. Verify existing `.proto` files, generated package names, gRPC service classes, validators, and mappers before proposing contract changes.
2. Keep Protobuf DTOs and generated gRPC classes out of domain and application.
3. Design protobuf evolution with reserved fields, backward compatibility notes, explicit required-at-application validation, and version fields.
4. Choose unary RPC, server streaming, client streaming, or bidirectional streaming based on verified payload size and lifecycle requirements.
5. Plan chunked uploads, gRPC retries, compression, message sizing, deadlines, cancellation, and performance tuning.
6. Preserve plugin-to-server communication as plugin produces repository/build context and analytics creates sessions, workspaces, and checkout results.
7. Mark future streaming progress events and chunked payload uploads as extensions unless the current slice explicitly implements them.
8. Apply `.agents/skills/resilience-engineering/SKILL.md` for retry, idempotency, deadline, cancellation, circuit-breaker, bulkhead and retry-provenance decisions.

## Expected Inputs

- existing `.proto` contracts
- gRPC adapter services, validators, and mappers
- plugin request and response lifecycle
- workspace and analysis-session models
- expected payload sizes and retry behavior

## Expected Outputs

- gRPC contract plan
- compatibility and evolution notes
- streaming and sizing recommendations
- adapter mapping responsibilities
- integration-test scenarios

## Boundaries

- Do not place gRPC DTOs in domain or application models.
- Do not treat transport acceptance as evidence verification.
- Do not make the plugin the analysis platform.

## Stop Conditions

Stop if:

- a field name, RPC method, package name, or schema version cannot be verified;
- backward compatibility would require hidden aliases or undocumented adapters;
- retry behavior could create duplicate sessions without idempotency keys;
- payload handling would blur raw evidence and generated analysis.
