# Supply Chain Rules

## Required Review

Review supply-chain impact when a slice changes:

- dependencies
- Gradle plugins
- dependency verification metadata
- CI actions
- container base images
- external tool downloads
- generated code tooling

## Rules

- Keep Gradle dependency verification strict.
- Do not add unaudited external downloads to default workflow.
- Pin or verify external tool versions when practical.
- Document optional external tools separately from required local gates.
- Treat generated code as derived output, not trusted evidence.

## STOP Rules

Stop when:

- dependency verification would be disabled or weakened;
- a new external tool is required without version or trust review;
- CI or container supply-chain risk is ignored;
- credentials would be required without secret-handling documentation.
