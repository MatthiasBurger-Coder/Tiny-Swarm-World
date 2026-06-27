# Workflow Context Pack

Workflow ID: `workflow-traefik-service-routing-20260627`
Version: `workflow-traefik-service-routing-v1.0.0`
Branch: `feature/workflow-traefik-service-routing-20260627`
Issue: `https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/157`
Process Strand: `workflow create -> workflow execute`
Execution Profile: `FULL_PATH`
Status: `PARTIAL_EXECUTION_REQUIRES_ISSUE_157_COMPLETION`

## Orientation

This context pack supports the Traefik service-routing workflow. It is a
navigation aid only; source files, `AGENTS.md`, `QUALITY.md`, ADRs, arc42 and
the active workflow remain authoritative.

## Affected Areas

- Traefik preferred public ingress ports `80/443`.
- Direct fallback/diagnostic ports including `10080/10443`.
- Service Access preferred routed links.
- Domain ingress route model.
- Compose stack rendering.
- Setup/preflight required port classification.
- Static integration and opt-in live browser tests.
- Effective access evidence and routed health-check expectations.
- Service-oriented integration tests for every enabled or explicitly skipped
  route.
- Opt-in Selenium browser E2E with redacted local evidence.
- README, deployment docs and arc42 deployment view.

## Forbidden Areas

- Live LXC, Incus, LXD, Docker, Swarm, Traefik, DNS, hosts-file or browser
  mutation without explicit live opt-in.
- RabbitMQ metadata or routes.
- Kubernetes-first behavior.
- React frontend implementation.
- Committed `.tiny-swarm-world/evidence/**` runtime evidence.
- Raw secrets, certificate material, local IP addresses or host-specific paths
  in committed evidence.

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer as N/A impact check
- Senior Tester
- Senior DevOps Engineer
- Senior Documentation Engineer

## Quality Commands

Targeted:

- `PYTHONPATH=src python3 -m unittest tests.domain.ingress.test_desired_state`
- `PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml`
- `PYTHONPATH=src python3 -m unittest tests.integration.test_service_access_routing`
- `PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live`
- `PYTHONPATH=src python3 -m unittest discover -s tests/integration -t .`
- `PYTHONPATH=src python3 -m unittest discover -s tests/live -t .`
- `PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint`
- `git diff --check`

Required final:

- `python3 tools/quality_gate.py quality`

Live opt-in only:

- `TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest discover -s tests/live -t .`

## Governing Inputs

- `AGENTS.md`
- `QUALITY.md`
- `.agents/orchestrator/routing-rules.md`
- `.agents/orchestrator/swarm-orchestrator.md`
- `.agents/skills/workflow-authoring/SKILL.md`
- `.agents/skills/workflow-executor/SKILL.md`
- `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md`
- `.agents/skills/s3d-execution-orchestrator/SKILL.md`
- `documentation/architecture/adr-traefik-https-ingress-existing-ca.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/09_architecture_decisions.adoc`
- `infra/config/ports.yaml`
- `infra/config/services.yml`
- `infra/config/compose/traefik/docker-compose.yml`

## Hash Provenance

Recorded in `context-pack.json`.
