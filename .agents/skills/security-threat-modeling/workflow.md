# Workflow

## Phase 1 - Identify Security Scope

Check whether the slice affects:

- API or gRPC entry points
- authentication or authorization
- secrets or credentials
- logging or telemetry
- containers or deployment
- dependency or supply-chain metadata
- untrusted repository processing
- runtime traces, stack traces or source data

## Phase 2 - Define Trust Boundaries

Identify:

- caller
- callee
- network boundary
- process boundary
- filesystem boundary
- data sensitivity
- privilege level

## Phase 3 - Review Threats

Review:

- spoofing
- tampering
- repudiation gaps
- information disclosure
- denial of service
- privilege escalation
- supply-chain compromise
- evidence poisoning

## Phase 4 - Define Controls

Controls may include:

- authentication and authorization
- input validation
- size and time limits
- sandboxing
- secret redaction
- structured safe logging
- dependency verification
- container hardening
- audit and correlation IDs

## Phase 5 - Decision

Return `APPROVED`, `CHANGES_REQUESTED` or `BLOCKED`.

Any unresolved secret, sandbox, privilege, sensitive-data or trust-boundary issue is `BLOCKED`.
