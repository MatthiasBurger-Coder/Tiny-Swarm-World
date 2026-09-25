# ARCH-03.09 — Configuration Parsing Boundary

Status: PLANNED; workflow authored, implementation not started.
Issue: #352; parent: #313.

## Verified current boundary

YAML libraries reside in infrastructure. Application still consumes untyped
secret-manifest data through PortLocalFileStorage.load_yaml. Existing repository
models cover inventory, provider configuration, ports, commands and Compose,
but permissive coercion and lazy per-stack loading leave validation gaps.
Installer helpers also parse manifest and port-registry inputs and must be
included in the consumer inventory. This is not evidence of direct application
ruamel imports or a new provider/runtime architecture.

## Planned ownership

Infrastructure owns external syntax, schema validation and conversion. Domain
or application contract modules own explicit parser-independent values; ports
expose those values. Application orchestrates validated inputs and preserves
consent and runtime-dependent credential timing. Composition binds adapters.
Complete selected input validation precedes all lifecycle mutation and the
validated snapshot must be the one consumed. Legitimate typed mappings and
validated opaque Compose text remain supported.

## Constraints and verification

Preserve current schema/default behavior or document migration; no generic
schema framework, parser replacement, credential policy change or live action.
The existing ARCH-03.02 layer contracts and building-block ownership apply;
no new ADR is required. A policy or architecture departure requires review.

The active workflow at ../../workflow/workflow.md defines the six sequential
slices, exact allowed files, full surface inventory, requirement matrix,
malformed/valid fixtures, negative architecture probes and zero-mutation tests.
Only executed tests and independent acceptance review may change this note to
implemented. Workflow publication alone does not close #352.
