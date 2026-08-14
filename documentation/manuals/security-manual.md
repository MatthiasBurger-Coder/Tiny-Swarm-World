# Security Manual

This is the security review entry point. It summarizes canonical controls and
does not make a certification claim.

## Governance

Read the [ISMS scope](../security/isms-scope.md),
[risk register](../security/risk-register.md),
[statement of applicability](../security/statement-of-applicability.md),
[security controls](../security/security-controls.md) and
[incident response](../security/incident-response.md).

## Admin surfaces

The [OWASP ASVS mapping](../security/owasp-asvs-mapping.md),
[admin-surface RBAC](../security/admin-surface-rbac.md) and
[Service Access threat model](../security/service-access-threat-model.md)
define authentication, authorization, transport, route and role boundaries.
The secure Traefik dashboard uses existing HTTPS ingress and an external
users-file secret; it does not enable `api.insecure` or commit credentials.
See the [Traefik ADR](../arc42/09_decisions/adr-traefik-https-ingress-existing-ca.adoc).

## Secret and evidence rules

Use the [secret-handling policy](../security/secret-handling-policy.md) and
[live redaction rules](../evidence/redaction-rules.md). Evidence may contain
secret references and safe summaries, never secret values, tokens, private
keys, raw environments or unfiltered output.
