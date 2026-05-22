# Workflow

## Phase 1 - Identify Contract Scope

Determine whether the slice affects:

- REST endpoints
- gRPC services
- protobuf messages
- event or messaging contracts
- generated client/server code
- API error models
- API consumers

## Phase 2 - Verify Existing Contracts

Inspect source, schemas, protobuf files, README docs, ADRs and tests. Do not infer missing contracts from implementation names.

## Phase 3 - Review Contract-First Readiness

Require:

- contract path or schema location
- producer owner
- known consumers
- versioning or compatibility plan
- error model
- validation rules
- test expectations
- breaking-change decision status

## Phase 4 - Route Specialist Review

Route:

- REST semantics to Senior Python Automation Developer and Senior System Architect;
- protobuf or streaming semantics to Senior gRPC/Proto Specialist;
- compatibility and breaking changes to ADR Steward and Skill Registry & Conflict Auditor;
- security-sensitive APIs to Security & Threat Modeling;
- contract tests to Quality Gate Orchestrator.

## Phase 5 - Decision

Return:

- `APPROVED` when contract, compatibility and tests are clear;
- `CHANGES_REQUESTED` when contract details are incomplete but fixable;
- `BLOCKED` when continuing would require guessing or violate microservice rules.
