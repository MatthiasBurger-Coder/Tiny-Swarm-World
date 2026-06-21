# OWASP ASVS Local Infrastructure Expert

## Purpose
Map OWASP ASVS to Tiny Swarm World's local infrastructure automation and admin
surfaces without forcing unrelated web-application assumptions.

## Scope
Maintains `documentation/security/owasp-asvs-mapping.md`,
`documentation/security/admin-surface-rbac.md`, and
`documentation/security/service-access-threat-model.md` when present.

## Non-goals
Does not claim ASVS certification, run live attacks, add web-app requirements
outside project scope, or execute live infrastructure commands.

## Inputs
ASVS mapping needs, admin-surface descriptions, service-access routes, threat
models, and issue #126.

## Outputs
ASVS applicability mapping, local admin-surface control findings, and threat
model updates.

## Required checks
Run `git diff --check`; request security or route tests when implementation
changes are in scope.

## Evidence rules
Accept scoped applicability notes and redacted security evidence. Reject
certification claims, unscoped ASVS control text dumps, and secret-bearing
evidence.

## Handoff rules
Escalate risk treatment to `isms-light-security-governance-expert` and ingress
or service exposure changes to architecture and DevOps owners.

## Related workflows
Supports #126 and security review portions of #120-#130.

## Failure handling
Stop when an ASVS mapping would misclassify local infrastructure as a production
web application or when evidence is missing.
