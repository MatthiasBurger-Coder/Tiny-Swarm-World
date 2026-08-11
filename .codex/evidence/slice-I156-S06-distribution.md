# Slice Distribution — I156-S06

Workflow: issue-156-20260809
Workflow version: issue-156-v1.0.0
Slice ID: I156-S06
Slice title: Remove or classify unsupported legacy direct-port artifacts

## Execution decision

- Serial cleanup execution after I156-S05.
- Streams reviewed: architecture, requirements, documentation, DevOps, tests, quality and security/evidence.
- No real subagent tool is visible; explicit role-based fallback review will be recorded.
- No parallel streams: the cleanup changes shared service metadata and deployment documentation and must preserve the inventory classification.
- The active `service-access` NGINX `8086` listener remains a documented compatibility/rollback path because it is still a valid NGINX target; it is not treated as a registry-backed direct port.
- Stale documentation claims for Pulsar `8087` and Swagger published `8084` will be corrected to distinguish registry-backed published ports from internal targets.
- Add deterministic negative/classification coverage for the compatibility mapping and absence of RabbitMQ in active configuration.
- No provider, Docker/Swarm, Traefik redesign, local DNS or live deployment action is in scope.

## Locks and gates

- File locks: `infra/config/services.yml`, `infra/config/compose/**` only where classification is verified, `documentation/system/network.adoc`, `documentation/arc42/07_deployment_view.adoc`, and focused Compose/config tests.
- Contract lock: `I156-legacy-exclusion`.
- Architecture locks: no provider change, no Traefik redesign, no removal of valid internal targets.
- Targeted gates: focused Compose repository/config tests and `git diff --check`.
- Required gate: `python3 tools/quality_gate.py quality` after implementation.

## Role review

- Senior System Architect: approve target-vs-published corrections and retain only explicit compatibility evidence.
- Senior Requirement Engineer: trace each retained legacy value and confirm no unsupported artifact is silently invented.
- Senior DevOps Engineer: verify Pulsar remains the active messaging stack and no live action is needed.
- Senior Tester: assert compatibility classification, internal target preservation and RabbitMQ absence.
- Documentation review: update only verified facts and preserve local-vs-live evidence wording.

## Consolidation plan

Review the inventory-approved metadata/documentation corrections, run targeted and full gates, inspect all staged paths, then commit exactly I156-S06. Any unclassified direct port or source/documentation contradiction remains a stop condition.
