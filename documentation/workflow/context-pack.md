# Workflow Context Pack

## Active Workflow

```text
workflow_id=portainer-local-endpoint-bootstrap-diagnostics-v1.0.0
workflow_version=1.0.0
branch=work/fix-workflow-portainer-local-endpoint-20260606
execution_profile=FULL_PATH
decision=READY_FOR_WORKFLOW
```

## Navigation

Primary workflow:

* `documentation/workflow/workflow.md`

Role reports:

* `documentation/workflow/reports/01-requirement-agent-findings.md`
* `documentation/workflow/reports/02-architecture-agent-findings.md`
* `documentation/workflow/reports/03-python-automation-agent-findings.md`
* `documentation/workflow/reports/04-frontend-impact-agent-findings.md`
* `documentation/workflow/reports/05-test-agent-findings.md`

Primary source files:

* `src/tiny_swarm_world/application/services/deployment/ensure_portainer_endpoint.py`
* `src/tiny_swarm_world/application/services/deployment/workflows.py`
* `src/tiny_swarm_world/application/ports/clients/port_portainer_client.py`
* `src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py`
* `infra/config/compose/portainer/docker-compose.yml`

Primary tests:

* `tests/infrastructure/adapters/clients/test_portainer_http_client.py`
* `tests/application/services/deployment/test_ensure_portainer_endpoint.py`
* `tests/application/services/deployment/test_deployment_workflows.py`

Documentation sync targets:

* `documentation/deployment/system.adoc`
* `documentation/arc42/06_runtime_view.adoc`
* `documentation/arc42/07_deployment_view.adoc`
* `documentation/system/live-operation-surfaces.adoc`

## Process Strand

Deployment bootstrap and setup live-installation workflow.

## Affected Areas

* Portainer endpoint bootstrap.
* Portainer HTTP adapter diagnostics.
* Deployment apply failure evidence.
* Retry/backoff for transient endpoint readiness.
* Deployment and arc42 documentation.

## Forbidden Areas

* Domain imports of HTTP, Portainer, Docker, LXC, logging, or request details.
* Java, Maven, Spring Boot, Gradle, JUnit, ArchUnit, or React/browser frontend
  additions.
* Kubernetes-first behavior.
* Multipass provider restoration.
* Live infrastructure commands without explicit user approval.

## Required Roles

* Senior Requirement Engineer.
* Senior System Architect.
* Senior Python Automation Developer.
* Senior React Frontend Developer for no-impact review.
* Senior Tester.
* Senior Documentation Engineer for Slice 04.
* Senior DevOps Engineer for optional live validation only.

## Quality Commands

Targeted:

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_endpoint tests.application.services.deployment.test_deployment_workflows
git diff --check
```

Required before commit or push when practical:

```bash
python3 tools/quality_gate.py quality
```

Optional live validation only after explicit user request:

```bash
./install.sh
```

## Governing File Hashes

```text
AGENTS.md ecba0ffcfb5ae1d2db209cbecff34d77fd79a60593e866d881f7e31c40907964
QUALITY.md 458e5f4d8fbdedea1c413e1ff135ec91392a4bb5a5aea20300dcac8e209414b6
.agents/skills/workflow-authoring/SKILL.md 087658240296e3b1ec74205c60a96a9a4c67a17cf653f7867e6f316bd9afa94e
.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md 23de7d9aac9d2694eae26fac2765d65f369c101ac348dac24d5f3bbe9e2d3ba4
.agents/skills/execution-profile-router/SKILL.md b554ffd4c3c8de9b313b55d8a9c99deda8c3bf3910f559105000e338680263e9
.agents/orchestrator/routing-rules.md c11b3df9e77717bad7caacb464b74db4566b00c7794cea53e2dbe39a8065e71a
documentation/epics/autonomous-runnable-setup.md fc7ec746446faa756306e459b54d700052eea0869c6dc2b1ef8a9e3b15be554a
documentation/arc42/06_runtime_view.adoc 91e423c4cbadd835d915573d972377bf3381eb888627525c3c1d7fc07d8c12ba
documentation/deployment/system.adoc 0a8b440e9bd080ba96a1d09e006df1548ddd8a788cede0b7f1d302ecdf12f1ff
src/tiny_swarm_world/application/services/deployment/ensure_portainer_endpoint.py 783f31ce2b0fe1db75413992b7b0a7ccb1126156dee3804129676787eb5df05f
src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py 6e00a50950275c41c61c85c9dd6832bfd93940d604bf002195eeee6baa4f96d0
infra/config/compose/portainer/docker-compose.yml 1f4e8010e753e6d4ae2140aa7bff875ddcd468cf25975bb5c01d8e170fce847d
```

Context pack is stale when any hash above changes, when branch differs from
`work/fix-workflow-portainer-local-endpoint-20260606`, or when a slice lock
conflict is detected.
