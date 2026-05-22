# Compatibility Rules

## Compatibility Classification

Classify changes as:

- `NON_BREAKING`
- `POTENTIALLY_BREAKING`
- `BREAKING`
- `UNKNOWN`

## Non-Breaking Examples

- add optional field with clear default behavior;
- add new REST endpoint without changing existing behavior;
- add new gRPC method without changing existing methods;
- extend error details without removing stable fields.

## Breaking Examples

- rename or remove REST path, method, request field or response field;
- change field meaning;
- reuse protobuf field numbers;
- remove required consumer behavior;
- change error semantics without compatibility plan.

## Required Breaking-Change Evidence

- affected consumers
- migration or compatibility strategy
- ADR or architecture decision
- test plan
- rollback plan

## STOP Rules

Stop when a change is `UNKNOWN` or `BREAKING` and lacks consumer, ADR, test or rollback evidence.
