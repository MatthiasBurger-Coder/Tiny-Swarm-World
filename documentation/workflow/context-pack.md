# Workflow Context Pack

Workflow: `workflow-project-paths-di-v1.0.0`
Workflow ID: `workflow-project-paths-di-20260627`
Branch: `architecture/workflow-project-paths-di-20260627`
Created: `2026-06-27`
Status: `CREATED_READY_FOR_EXECUTION`
Evidence Root: `.codex/evidence/workflow-project-paths-di-20260627/`

## Purpose

Navigation context for centralizing Tiny Swarm World project path resolution
through an immutable `ProjectPaths` infrastructure configuration object and
composition-root wiring.

## Process Strand

- Active command: `workflow create`
- Execution profile: `NORMAL_PATH`
- Workflow decision: `READY_FOR_WORKFLOW`

## Affected Areas

- `src/tiny_swarm_world/infrastructure/project_paths.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `src/tiny_swarm_world/infrastructure/adapters/file_management/**`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/**`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
- `src/tiny_swarm_world/infrastructure/logging/logger_factory.py`
- `tests/infrastructure/**`
- `tests/architecture/test_local_state_storage.py`
- `documentation/configuration/config-contract-inventory.md`
- `documentation/architecture/responsibility-separation-analysis.md`
- `documentation/arc42/05_building_blocks.adoc`
- `documentation/workflow/**`
- `.codex/evidence/workflow-project-paths-di-20260627/**`

## Forbidden Areas

- domain or application imports from infrastructure path configuration
- live LXD, Incus, LXC, Docker Swarm, compose, netplan, socat, or service
  bootstrap commands
- Java, Maven, Spring Boot, Multipass reintroduction, or Kubernetes-first scope
- browser React frontend work
- broad DI-container rewrite
- removal of compatibility functions before all callers are safely migrated
- push, PR creation, merge, or branch cleanup

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer
- Senior Tester

## Conditional Roles

- Senior Documentation Engineer for documentation synchronization
- Senior DevOps Engineer for live-operation safety review
- ADR Steward if implementation changes architecture policy
- Security reviewer if host-specific paths or secret-like configuration are
  introduced

## Quality Commands

Targeted:

- `rg -n "project_paths|ProjectPaths|TSW_REPOSITORY_ROOT|TSW_INFRA_ROOT|config_root\\(|infra_root\\(|repository_root\\(|logs_root\\(" src tests documentation infra README.md AGENTS.md QUALITY.md`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_project_paths`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_command_repository_yaml_contract`
- `PYTHONPATH=src python3 -m unittest tests.architecture.test_local_state_storage`
- `python3 tools/quality_gate.py arch-tests`
- `git diff --check`

Required final:

- `python3 tools/quality_gate.py quality`

## Governing Inputs

| Path | Hash |
| --- | --- |
| `AGENTS.md` | `335a60cd362e40090b09fdd9b982cfce87912aae` |
| `QUALITY.md` | `17002150bab9f168eb60be85d55b7a0c1cb441e5` |
| `documentation/epics/system-unification.md` | `c46629b0ba95e8b0efc488548d0d9755663fcd9a` |
| `documentation/arc42/05_building_blocks.adoc` | `3126d1f992c6cdabcda0dc701306bda1d4a9e6e7` |
| `documentation/arc42/08_concepts.adoc` | `26209aebff8ee7aa7401b0981cdc9135f387db40` |
| `documentation/configuration/config-contract-inventory.md` | `c86d3798e6704dca5832bc55824df96d1c0d11c1` |
| `documentation/architecture/responsibility-separation-analysis.md` | `14b686b4afd34dc8e2c1e1af9320dc1d07e94437` |
| `src/tiny_swarm_world/infrastructure/project_paths.py` | `949844b34b4333c108ea7350b2097114f45dfe39` |
| `src/tiny_swarm_world/infrastructure/composition.py` | `b43d5c63320266bc574bc32a63c9b40e1dc710ef` |
| `src/tiny_swarm_world/infrastructure/dependency_injection/infra_core_di_container.py` | `f6443574352f01235eceac90b7fe8a3f77e5f8bb` |

## Branch Evidence

- `git show-ref --verify --quiet refs/heads/architecture/workflow-project-paths-di-20260627`
  returned `ref-ok`.
- `git branch --show-current` returned
  `architecture/workflow-project-paths-di-20260627`.

## Staleness Conditions

This context pack is stale if any governing input hash changes, if the active
branch changes, if new direct users of `project_paths.py` appear outside
infrastructure/tests/documentation, if documentation conflicts require an ADR,
or if quality-gate commands change in `QUALITY.md`.
