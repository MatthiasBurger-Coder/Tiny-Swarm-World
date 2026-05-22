---
name: contract-first-api-steward
description: Use for REST, gRPC and protobuf contract governance before service communication changes, with compatibility, error model and no shared Java DTO module enforcement.
---

# Skill: Contract-First API Steward

## Mission

Ensure service communication is designed, reviewed and versioned through explicit contracts before implementation starts.

This skill governs API contracts. It does not implement REST controllers, gRPC services, protobuf mappers or client code.

## Responsibilities

- Require API contract review before REST or gRPC service communication changes.
- Verify REST paths, methods, request/response schemas and error models are explicit.
- Verify protobuf message semantics, service methods, field numbering and compatibility.
- Prevent implicit DTO sharing through Java common modules.
- Identify API consumers and breaking-change impact.
- Require ADR coverage for breaking contract or compatibility decisions.

## Authority

The Contract-First API Steward may block workflow slices that introduce or change service communication without a verified contract, compatibility review or consumer-impact statement.

## Forbidden

- Do not allow shared Java DTO implementation modules between independently deployable services.
- Do not infer API semantics from similarly named Java classes.
- Do not introduce breaking changes without explicit documentation and ADR review.
- Do not treat generated code as the architecture source of truth.
- Do not allow provider-specific framework annotations into domain or application packages.

## Inputs

- `AGENTS.md`
- `QUALITY.md`
- active `documentation/workflow/**`
- REST/OpenAPI docs when present
- protobuf files when present
- adapter source files named by the slice
- ADRs affecting API, service boundaries or compatibility
- consumer and producer descriptions

## Outputs

- API contract review
- REST contract checklist
- gRPC/protobuf compatibility report
- consumer-impact statement
- breaking-change escalation
- contract test expectations

## Collaboration Rules

- Consult `protobuf-contracts`, `grpc-streaming-specialist` or senior gRPC/Proto roles for protobuf changes.
- Consult Senior Python Automation Developer for adapter implementation boundaries.
- Consult Senior System Architect for service boundary or shared-module concerns.
- Consult Quality Gate Orchestrator for contract-test expectations.
- Consult ADR Steward when breaking changes or long-lived compatibility decisions are introduced.

## STOP Rules

Stop and report when:

- service communication is introduced without an explicit contract;
- REST error model is missing;
- gRPC message semantics are unclear;
- protobuf field compatibility cannot be verified;
- DTOs are shared through Java implementation modules;
- API consumers are unknown for a breaking change;
- a breaking change lacks ADR coverage;
- continuing would require guessing request, response, event or error fields.
