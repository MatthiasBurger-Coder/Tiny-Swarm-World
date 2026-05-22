# gRPC And Protobuf Rules

## Required Protobuf Review

- package name
- service name
- RPC method names
- request and response message semantics
- field numbers
- reserved fields or names for removals
- optional, repeated and oneof semantics
- deadlines, cancellation and retry expectations
- payload size and streaming expectations
- compatibility impact

## Rules

- Protobuf contracts must be reviewed before adapter implementation.
- Field numbers must never be reused for different semantics.
- Removed fields require reserved numbers or names when the contract is published.
- Transport validation belongs in inbound adapters.
- Domain and application packages must not depend on generated transport classes.
- Shared Java DTO modules are not allowed as a substitute for protobuf contracts.

## STOP Rules

Stop when:

- message semantics are unclear;
- field numbering or reserved-field behavior is unsafe;
- generated classes would leak inward into domain or application;
- streaming, retry or deadline behavior is required but undefined;
- compatibility cannot be determined.
