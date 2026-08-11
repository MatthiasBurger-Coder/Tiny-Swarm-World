# Slice Distribution — I156-S04

Workflow: issue-156-20260809
Workflow version: issue-156-v1.0.0
Slice ID: I156-S04
Slice title: Apply registry ports to messaging, observability and gateway stacks

## Execution decision

- Serial execution after I156-S03; the user requested step-by-step progression even though the workflow marks S03/S04 as parallel-eligible.
- No parallel worktree is used because the shared Compose repository test and registry-resolution contract are explicit coordination locks.
- Streams reviewed: DevOps/Compose, Python infrastructure, architecture, tests, requirements, quality.
- No real subagent tool is visible; explicit role-based fallback review will be recorded.
- Expected product change: regression coverage for Pulsar, Traefik, Swagger, service-access and Infisical registry-backed rendering, plus the negative RabbitMQ path check.
- Existing values were verified against the central registry; no value-only configuration rewrite is authorized where the committed assets are already correct.
- Live deployment, Docker/Swarm commands, provider/bootstrap actions and Traefik redesign are out of scope.

## Locks and gates

- File locks: `infra/config/compose/pulsar/**`, `infra/config/compose/traefik/**`, `infra/config/compose/swagger/**`, `infra/config/compose/service-access/**`, `infra/config/compose/infisical/**`, `infra/config/services.yml`, and the focused Compose repository test.
- Contract locks: `I156-registry-resolution`, `I156-messaging-model`, `I156-ingress-ownership`.
- Architecture locks: Pulsar remains the messaging service; Traefik retains public ingress ownership.
- Targeted gate: `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml`.
- Required gate: `python3 tools/quality_gate.py quality` after implementation.

## Role review

- Senior DevOps Engineer: verify stack-specific mappings and gateway ownership without live deployment.
- Senior Python Automation Developer: exercise the existing central resolver rather than adding a second mapping path.
- Senior System Architect: reject RabbitMQ generation, ingress ownership inversion or invented absent assets.
- Senior Tester: cover direct mappings, compatibility port preservation and negative messaging scan.
- Senior Requirement Engineer: map REQ-156-01, REQ-156-02, REQ-156-06, REQ-156-10, REQ-156-12 and absent-observability classification evidence.

## Consolidation plan

Use the smallest regression-only change if the checked-in Compose assets already match `ports.yaml`. Review staged files, run focused and full quality gates, create consolidation evidence, then commit exactly I156-S04.
