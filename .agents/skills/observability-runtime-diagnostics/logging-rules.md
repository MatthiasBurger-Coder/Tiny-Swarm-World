# Logging Rules

## Rules

- Logs should be structured or structure-ready.
- Logs should include correlation context where available.
- Errors should include enough context for diagnosis without exposing sensitive data.
- Sensitive data must be redacted or omitted.
- Logging adapters must not contain domain decisions.
- Domain and application packages must remain independent from concrete logging providers.

## Sensitive Data

Avoid logging:

- secrets
- credentials
- tokens
- personal data
- raw source content
- raw runtime payloads
- full stack traces from untrusted sources unless explicitly reviewed

## STOP Rules

Stop when logs could expose sensitive data or when error diagnostics cannot be linked to analysis, runtime or incident context.
