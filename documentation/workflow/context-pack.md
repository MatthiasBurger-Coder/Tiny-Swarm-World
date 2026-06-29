# Workflow Context Pack

Workflow ID: `workflow-service-access-dashboard-html-20260629`
Version: `workflow-service-access-dashboard-html-v1.0.0`
Branch: `fix/workflow-service-access-dashboard-html-20260629`
Issue: `local-high-service-access-dashboard-html-deployment-sync`
Process Strand: `workflow create -> workflow execute`
Execution Profile: `NORMAL_PATH`
Status: `EXECUTED_LOCAL_QUALITY_PASSED_REMOTE_PUBLICATION_BLOCKED`

## Orientation

This context pack supports the Service Access dashboard HTML deployment asset
synchronization workflow. It is a navigation aid only; source files,
`AGENTS.md`, `QUALITY.md`, ADRs, arc42 and the active workflow remain
authoritative.

## Affected Areas

- Service Access dashboard HTML generation.
- Service Access compose config file path under `TSW_REMOTE_STACK_ROOT`.
- LXC Swarm stack asset transfer before `docker stack deploy`.
- Deployment workflow pre-apply sequencing and composition visibility.
- Static tests for stale dashboard asset protection.
- Deployment documentation that distinguishes generated remote assets from
  live reachability evidence.

## Forbidden Areas

- Live Incus, LXC, Docker, Swarm, Portainer, DNS, hosts-file, service or
  network mutation without explicit operator opt-in.
- Reading or committing `.tiny-swarm/secrets/generated.local.env`.
- Kubernetes-first behavior.
- React frontend implementation.
- Java, Maven or Spring Boot project structure.
- Raw secrets, password values, tokens, certificate material, local IP
  addresses or host-specific paths in committed files or evidence.

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer as N/A impact check
- Senior Tester
- Senior DevOps Engineer
- Senior Documentation Engineer
- Issue Completion Auditor before final DONE

## Quality Commands

Targeted:

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_swarm_runtime`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition`
- `PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_deployment_workflows`
- `git diff --check`

Required final:

- `python3 tools/quality_gate.py quality`

Windows host wrapper:

- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World_2 && <command>'`

Live opt-in:

- None for this workflow. Live deployment validation is out of scope unless a
  later user request explicitly authorizes it.

## Governing Inputs

- `AGENTS.md`
- `QUALITY.md`
- `documentation/process/issue-completion-discipline.md`
- `.agents/skills/workflow-authoring/SKILL.md`
- `.agents/roles/senior-workflow-architect/SKILL.md`
- `.agents/roles/senior-requirement-engineer/SKILL.md`
- `.agents/roles/senior-system-architect.md`
- `.agents/roles/senior-python-automation-developer.md`
- `.agents/roles/senior-tester.md`
- `.agents/roles/senior-devops.md`
- `.agents/roles/senior-documentation-engineer.md`
- `.agents/roles/senior-react-frontend.md`
- `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `src/tiny_swarm_world/infrastructure/composition_lxc_runtimes.py`
- `infra/config/compose/service-access/docker-compose.yml`
- `infra/config/compose/service-access/dashboard/index.html`
- `documentation/arc42/07_deployment/system.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/08_configuration/config-contract-inventory.md`
- `documentation/arc42/09_decisions/adr-service-access-dashboard-vaultwarden.adoc`
- `documentation/system/live-operation-surfaces.adoc`
- `documentation/user_guide/usage.adoc`
- `documentation/user_guide/troubleshooting.adoc`

## Hash Provenance

Recorded in `context-pack.json`.

## Publication Note

Workflow authoring is local on
`fix/workflow-service-access-dashboard-html-20260629`. Remote publication to
`origin` is blocked because GitHub SSH authentication failed with
`Permission denied (publickey)`. The workflow remains locally authored until
credentials are fixed and the branch is pushed.

## Execution Note

Local workflow execution completed with targeted tests, `git diff --check`,
and the repository quality gate passing through the WSL `.venv`. Remote branch
publication remains blocked by GitHub SSH authentication.
