---
name: microservice-architecture-expert
description: Use for microservice planning, service extraction, independent service applications, no shared implementation modules, contract-only integration, containerization, orchestration, and independent deployability.
---

# Microservice Architecture Expert

Use this skill for service-split work, microservice reviews, deployment autonomy, or no-shared-implementation boundary checks.

## Authoritative Sources

Read, when present:

- root `AGENTS.md`
- root `QUALITY.md`
- project deployment documentation
- project-specific microservice, container, REST, messaging, gRPC, or Protobuf roles and skills under `.agents/`
- build files and service manifests

## Default Guardrails

- Do not introduce shared implementation modules between independently deployable services.
- Do not share domain models, event implementation classes, service fixtures, or direct class dependencies between services.
- Allow integration only through explicit external contracts such as REST/OpenAPI, gRPC/protobuf, or message contracts.
- Keep contracts as interface descriptions, not shared implementation modules.
- Require every service to own its application entrypoint, configuration, ports, adapters, tests, health checks, documentation, and internal domain model unless the project architecture documents a different pattern.
- Require every service to be independently runnable, testable, and deployable through the project's documented deployment targets.

## Stop Conditions

Stop when service ownership, module boundaries, contract shape, deployment target, or independent startability cannot be verified.
