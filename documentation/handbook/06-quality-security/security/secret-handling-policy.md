# Secret-Handling Policy

## Secret classes

- Bootstrap material for Infisical or another secret source.
- Service/admin credentials for Portainer, Nexus, Jenkins, Pulsar or related
  surfaces.
- API tokens, registry credentials, Docker/Swarm join material and managed
  cryptographic material such as TLS keys.
- Local environment values and short-lived command authentication material.

## Allowed storage

Use the approved external secret/configuration mechanism and local runtime
inputs that are excluded from version control. Use placeholders in examples.
When automation writes a local secret file, apply restrictive permissions and
record only a redacted status/evidence summary.

## Forbidden storage

Do not commit real values to source, YAML, compose files, workflow documents,
tests, screenshots, logs, issue/PR text or evidence. Do not place raw .env
content, authorization headers, join tokens, private host data or credentials
in diagnostics. Do not invent credentials or host-specific endpoints.

## Redaction

Replace values with stable markers such as REDACTED or SECRET_PRESENT. Redact
tokens, passwords, key material, cookies, authorization headers, private
paths/IPs, join tokens and raw environment payloads before evidence is stored.
A redaction check must record what was checked without retaining the secret.

## Rotation triggers

Rotate or revoke when a secret is committed, appears in logs/evidence, is
suspected exposed, an administrator leaves the operating context, an external
service reports compromise, or a bootstrap material lifecycle ends. Preserve a
redacted incident/CAPA record and never repeat the old value.

## Infisical bootstrap and local credential lifecycle

Bootstrap material is short-lived, sourced only through the approved operator
flow and never copied into repository evidence. The normal installer resolves
deterministic catalog defaults or explicit operator overrides; it does not
generate, print, or persist credential recovery files. Dedicated cryptographic
lifecycles, such as managed TLS state, remain protected and are not confused
with credential defaults. Recovery or rotation requires explicit owner approval
and a verifiable, redacted result.

## Evidence and review

Security evidence identifies control/risk IDs, status, source, reviewer and
redaction treatment. Planned, missing, blocked, refused, resource-gated and
failed states remain non-pass. The policy does not authorize live secret
creation, bootstrap or rotation by itself.
