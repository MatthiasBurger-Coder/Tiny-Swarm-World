# Workflow Context Pack

Workflow: `workflow-project-paths-di-v1.0.0`
Workflow ID: `workflow-project-paths-di-20260627`
Branch: `architecture/workflow-project-paths-di-20260627`
Created: `2026-06-27`
Status: `EXECUTED_WITH_EVIDENCE`
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
| `documentation/arc42/05_building_blocks.adoc` | `94676ffcd8f62b447d1a44df1e6c115e0055f663` |
| `documentation/arc42/08_concepts.adoc` | `26209aebff8ee7aa7401b0981cdc9135f387db40` |
| `documentation/configuration/config-contract-inventory.md` | `487f2d987a7051a31210f3bd6c2aa13b59057f80` |
| `documentation/architecture/responsibility-separation-analysis.md` | `f0106e7456f96a5ed6b9c9f75b7aee7ea1469a8e` |
| `src/tiny_swarm_world/infrastructure/project_paths.py` | `777923ad14fde59bfdc49c0794c52cceaebaa458` |
| `src/tiny_swarm_world/infrastructure/composition.py` | `5475373612d26eca886cce6e5e18e345cfa0f3eb` |
| `src/tiny_swarm_world/infrastructure/dependency_injection/infra_core_di_container.py` | `f6443574352f01235eceac90b7fe8a3f77e5f8bb` |

## Execution Result

- Slice 01 recorded path contract baseline tests.
- Slice 02 added immutable `ProjectPaths` and compatibility facade delegation.
- Slice 03 wired `ProjectPaths` into targeted infrastructure adapters through
  the composition root.
- Slice 04 synchronized documentation and final quality evidence.
- Live infrastructure commands were not run.

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
