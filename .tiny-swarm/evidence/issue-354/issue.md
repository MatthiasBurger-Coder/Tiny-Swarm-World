# [ARCH-03.11] Centralize External Process Execution (#354)

Parent: #313

## Goal
Reduce scattered direct subprocess execution and provide one controlled execution boundary where command execution affects application behavior.

## Scope
- inventory direct subprocess/process calls
- introduce or harden a common process runner abstraction where justified
- centralize timeout, redaction, exit-code handling and structured results
- keep trivial/internal pure operations out of unnecessary abstraction

## Acceptance Criteria
- Architecturally significant process execution is centralized.
- Application services do not directly invoke subprocess for infrastructure behavior.
- Command results and failures are represented explicitly.
- Sensitive arguments/output are redacted.
- Tests cover success, timeout, non-zero exit and command-not-found paths.
