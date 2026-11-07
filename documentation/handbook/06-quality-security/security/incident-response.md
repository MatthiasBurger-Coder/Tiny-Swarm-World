# ISMS-light Incident Response

This process preserves evidence without exposing secrets. It is a local
governance runbook, not a promise that an incident detector or responder is
deployed.

## Common response

1. Detect and classify the event without copying sensitive payloads.
2. Contain: stop the affected workflow or access surface; do not improvise
   live commands without consent.
3. Preserve a redacted timeline, affected risk/control IDs, commit or workflow
   reference and decision state.
4. Correct and recover through an approved change or authorized live-validation
   procedure.
5. Open or update a QMS CAPA and link the evidence.
6. Perform an independent post-incident review and record residual risk.

## Scenario runbooks

| Scenario | Detection | Containment | Correction/recovery | Evidence/CAPA/follow-up |
| --- | --- | --- | --- | --- |
| Secret committed | secret scan, reviewer or report | stop publication; revoke/rotate through approved owner; do not repeat value | remove from history through approved repository process and update source | redacted finding, rotation evidence, CAPA, post-incident review |
| Secret in logs/evidence | reviewer or redaction scan | quarantine artifact and restrict access | replace with redacted summary; rotate if exposure is plausible | artifact hash/status, CAPA and effectiveness check |
| Unexpected admin exposure | route/config review or authorized observation | stop the workflow and isolate the route under approved procedure | apply #126/#150 auth/TLS decision or revert safely | route evidence, risk update, CAPA and follow-up audit |
| Docker socket event | security review or observed unauthorized mutation | stop affected automation and preserve state; do not destroy evidence | assess host/Swarm impact, reduce exposure and rotate credentials as needed | RISK-123-DOCKER-SOCKET, redacted timeline and CAPA |
| Failed or partial live setup | readiness/evidence result | stop/reconcile/rollback only under explicit live consent | use idempotent recovery and record drift; do not call a failed run green | scenario result, commands summarized, CAPA and re-run evidence |
| Infisical bootstrap issue | bootstrap validation or access failure | stop bootstrap and protect/revoke material | rotate/reissue through approved secret owner and reconcile references | redacted status, rotation evidence, CAPA and post-incident review |

## Escalation and closure

Critical events go to the Security Owner and Lead Architect immediately. Major
events also involve Senior Tester and Senior DevOps Engineer. An incident is not
closed until containment, correction/recovery, evidence preservation, CAPA
handoff and post-incident review are recorded. Missing, blocked or failed
evidence leaves the incident open.
