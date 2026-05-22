# Secure Coding Rules

## Rules

- Validate external input at adapter boundaries.
- Keep security-sensitive parsing outside domain policy.
- Avoid logging secrets, tokens, credentials, personal data and raw sensitive trace payloads.
- Redact or omit sensitive fields in diagnostics.
- Use explicit size, timeout and resource limits for untrusted input.
- Keep default tests independent from live external services.
- Do not bypass dependency verification.

## API Rules

- Define authentication and authorization expectations before implementation.
- Define error responses that avoid leaking sensitive internals.
- Define upload size, type and timeout constraints when accepting payloads.

## Repository Processing Rules

- Treat external repositories as untrusted.
- Use workspace isolation and cleanup.
- Avoid executing repository build scripts unless explicitly reviewed.
- Preserve provenance for acquired source artifacts.

## STOP Rules

Stop when code would process untrusted data without validation, resource limits or ownership of the security boundary.
