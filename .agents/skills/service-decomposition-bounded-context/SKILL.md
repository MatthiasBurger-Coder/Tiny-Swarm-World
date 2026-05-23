---
name: service-decomposition-bounded-context
description: Use for evaluating bounded-context service decomposition, service ownership, data ownership, independent deployability, and whether a candidate boundary is a real microservice rather than a technical module.
---

# Skill: Service Decomposition And Bounded Context

## Mission

Evaluate whether a proposed microservice boundary represents an owned business
capability with explicit data responsibility, contract boundaries and a path to
independent runtime operation.

This skill is a governance and decision-record skill. It does not move packages,
create service directories, implement endpoints, split persistence or generate
deployment descriptors.

## Core Rule

A technical module is not a microservice.

A candidate service is only a microservice candidate when it has a clear
business responsibility, owns its data or projections, communicates through
explicit contracts and can become independently buildable, startable, testable,
observable and containerizable.

## Responsibilities

- Identify the business capability or bounded context behind a candidate
  service.
- Verify the target service name, owned responsibility, owned data and
  non-owned data.
- Distinguish current modular-monolith modules from future service boundaries.
- Require explicit inbound and outbound communication paths.
- Require a contract-first plan for REST/OpenAPI, gRPC/protobuf or event
  communication before implementation slices.
- Identify service autonomy risks, data ownership risks and shared-code risks.
- Produce a Service Boundary Decision Record for later migration slices.

## Authority

This skill may block a microservice migration slice when the service boundary,
business responsibility, data ownership, communication path or runtime
independence evidence is unclear.

## Forbidden

- Do not treat Java packages, Gradle modules or technical layers as services by
  default.
- Do not create shared Java domain, DTO, service, repository, utility or error
  model modules between services.
- Do not allow direct class dependencies between independently deployable
  services.
- Do not allow direct cross-service database access.
- Do not claim runtime independence without verified build, start, test,
  configuration, healthcheck, observability and container-readiness evidence.
- Do not infer service ownership from similarly named modules, packages or
  folders.

## Required Inputs

Inspect the relevant subset of:

- root `AGENTS.md`
- root `QUALITY.md`
- active `documentation/workflow/**`
- `documentation/adr/**`, especially service, contract and data ownership ADRs
- `documentation/arc42/**`
- `docs/workplan/**` when referenced by the workflow
- current Gradle modules and source package layout when a concrete service
  boundary is named
- existing contracts, schemas, adapters or persistence documentation when named

## Service Boundary Decision Record

Return a concise record with:

- candidate service name
- business capability
- owned responsibility
- explicit non-scope
- owned data
- non-owned data access path
- inbound communication
- outbound communication
- contract files or planned contract slice
- current repository evidence
- independence evidence
- required reviewers
- required tests or quality gates
- stop conditions
- decision: `APPROVED_FOR_SLICE`, `REQUIRES_REFINEMENT` or `REJECTED`

## Collaboration Rules

- Consult Senior System Architect for architecture boundaries.
- Consult Microservice Runtime Readiness Expert for deployment and
  runtime-independence expectations.
- Consult Data Ownership And Persistence Steward for owned data and projections.
- Consult Contract Governance Expert or Contract-First API Steward for REST,
  gRPC, protobuf or event contract concerns.
- Consult Senior DevOps Engineer or Microservice Runtime Readiness Expert for
  build, start, healthcheck, observability and container readiness.
- Consult Senior Tester for testability and quality-gate impact.

## STOP Rules

Stop and report when:

- the business capability is unclear;
- the candidate boundary is only a technical package, module or layer;
- owned data or write authority is unclear;
- inbound or outbound communication is undefined;
- a slice would introduce shared Java implementation modules between services;
- a slice would introduce direct class dependencies between services;
- direct cross-service database access is planned;
- service runtime independence is claimed without verified evidence;
- continuing would require guessing service ownership, data ownership, API
  contracts, event fields, database tables or deployment commands.
