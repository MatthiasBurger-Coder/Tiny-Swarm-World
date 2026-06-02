# Workflow Context Pack

## Identity

- Workflow: Remove Multipass Legacy Provider
- Version: remove-multipass-legacy-v1.0.0
- Branch: `feature/workflow-remove-multipass-legacy-20260602`
- Created: 2026-06-02
- Process strand: S3D
- Execution profile: FULL_PATH

## Request

Remove the complete Multipass legacy/fallback provider surface, including the
explicit `--node-provider multipass_legacy` mode.

## Affected Areas

- `src/tiny_swarm_world/domain/node_provider`
- `src/tiny_swarm_world/domain/preflight`
- `src/tiny_swarm_world/application/services/platform`
- `src/tiny_swarm_world/application/services/multipass`
- `src/tiny_swarm_world/infrastructure/adapters`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `infra/config/multipass`
- `infra/config/docker/command_multipass_*.yaml`
- `infra/config/node-providers/provider_config.yaml`
- `tests`
- `README.md`
- `documentation`
- `.agents/skills` and skill-audit references where they describe current
  Multipass support

## Forbidden Areas

- Java, Maven, Spring Boot project structure.
- Browser React frontend implementation.
- Kubernetes-first reorientation.
- Live infrastructure mutation.
- Unrelated legacy cleanup outside the Multipass removal surface.

## Required Roles And Subagents

- Senior Requirement Engineer: requirement classification and blocker routing.
- Senior System Architect: architecture and arc42 review.
- Senior Python Automation Developer: sequential implementation worker.
- Senior React Frontend Developer: N/A impact check.
- Senior Tester: regression and quality gates.
- Senior Documentation Engineer: docs and governance synchronization.
- Senior DevOps Engineer: command and no-live-infrastructure review.
- Senior Execution Orchestrator: dependency graph and file locks.

## Quality Commands

Targeted:

- `PYTHONPATH=src python3 -m unittest tests.domain.node_provider.test_provider_model`
- `PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_node_provider_selection`
- `PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository`
- `PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint`
- `python3 tools/quality_gate.py arch-tests`
- `python3 tools/quality_gate.py test`
- `git diff --check`

Required final:

- `python3 tools/quality_gate.py quality`
- `git diff --check`

## Governing File Hashes

```text
131aa2183b9598aeb86fed0af1e66b09ed6b29e5b54a4993a898d3c2782d3856  AGENTS.md
458e5f4d8fbdedea1c413e1ff135ec91392a4bb5a5aea20300dcac8e209414b6  QUALITY.md
087658240296e3b1ec74205c60a96a9a4c67a17cf653f7867e6f316bd9afa94e  .agents/skills/workflow-authoring/SKILL.md
bae552d4860614879871413918870df6940b95af185f6c1077a023caa88e3ddb  .agents/skills/workflow-slice/SKILL.md
fad1651bb25b5dbd3ba5c98174aea0b24ff41b42b1bbf78926140304be44af95  .agents/skills/swarm-orchestration/SKILL.md
b554ffd4c3c8de9b313b55d8a9c99deda8c3bf3910f559105000e338680263e9  .agents/skills/execution-profile-router/SKILL.md
23de7d9aac9d2694eae26fac2765d65f369c101ac348dac24d5f3bbe9e2d3ba4  .agents/skills/three-amigos-requirement-gatekeeper/SKILL.md
c11b3df9e77717bad7caacb464b74db4566b00c7794cea53e2dbe39a8065e71a  .agents/orchestrator/routing-rules.md
dae7115594172e159c051c3ece15c0b535f1570efbb28fc67440aef0bbadc9c9  documentation/process/workflow-create.md
2d75afaced2c8c68fc8071a6b1c9782d6b3a931264562f2f43fdf05f0ced24f5  documentation/process/branch-governance.md
```

## Staleness Rules

This context pack is stale when:

- any governing hash changes;
- the active branch is not `feature/workflow-remove-multipass-legacy-20260602`;
- slice metadata changes without updating this pack;
- new Multipass references are discovered in current support paths;
- root `AGENTS.md`, `QUALITY.md`, ADRs, arc42, routing rules, or workflow
  process documents conflict.
