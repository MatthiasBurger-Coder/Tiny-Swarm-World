# Workflow Context Pack

Workflow: `workflow-remove-netplan-repository-v1.0.0`
Workflow ID: `workflow-remove-netplan-repository-20260627`
Branch: `feature/workflow-remove-netplan-repository-20260627`
Created: `2026-06-27`
Status: `EXECUTED_WITH_EVIDENCE`
Evidence Root: `.codex/evidence/workflow-remove-netplan-repository-20260627/`

## Purpose

Navigation context for removing the unused legacy Netplan repository adapter,
its adapter-only tests, and active documentation references to that adapter.

## Process Strand

- Active command: `workflow create`
- Execution profile: `NORMAL_PATH`
- Workflow decision: `READY_FOR_WORKFLOW`

## Affected Areas

- `src/tiny_swarm_world/infrastructure/adapters/repositories/netplan_repository.py`
- `tests/infrastructure/adapters/repositories/test_netplan_repository.py`
- `documentation/architecture/responsibility-separation-analysis.md`
- `documentation/configuration/config-contract-inventory.md`
- `documentation/workflow/**`
- `.codex/evidence/workflow-remove-netplan-repository-20260627/**`

## Forbidden Areas

- live infrastructure mutation
- live `netplan`, LXD, Incus, LXC, Docker Swarm, compose, socat, or service
  bootstrap commands
- broad removal of generic `netplan` safety references
- Java, Maven, Spring Boot, Multipass reintroduction, or Kubernetes-first scope
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
- Security reviewer if execution touches sanitizer behavior

## Quality Commands

Targeted:

- `rg -n "PortNetplanRepositoryYaml|netplan_repository|GENERATED_NETPLAN_PATH|DEFAULT_NAMESERVERS" src tests documentation infra README.md AGENTS.md QUALITY.md -g '!**/__pycache__/**'`
- `python3 tools/quality_gate.py test`
- `git diff --check`

Required final:

- `python3 tools/quality_gate.py quality`

## Governing Inputs

| Path | Hash |
| --- | --- |
| `AGENTS.md` | `335a60cd362e40090b09fdd9b982cfce87912aae` |
| `QUALITY.md` | `17002150bab9f168eb60be85d55b7a0c1cb441e5` |
| `documentation/architecture/adr-retire-multipass-legacy-provider.adoc` | `8652b1c7d1dcdb9dddd7ad3ce39c8796214009d3` |
| `documentation/system/network.adoc` | `25f068878c3ac16377017a9df5a62d89d1d7766c` |
| `documentation/architecture/responsibility-separation-analysis.md` | `123d76426e91bc2cec551cbee59a4fc0c9f95aee` |
| `src/tiny_swarm_world/infrastructure/adapters/repositories/netplan_repository.py` | Removed by Slice 02. |
| `tests/infrastructure/adapters/repositories/test_netplan_repository.py` | Removed by Slice 02. |

## Execution Result

- Slice 01 audit evidence recorded no active product consumer.
- Slice 02 removed the adapter and adapter-only tests.
- Slice 03 synchronized active documentation references.
- Generic `netplan` safety references were preserved.

## Branch Evidence

- `git show-ref --verify --quiet refs/heads/feature/workflow-remove-netplan-repository-20260627`
  returned `ref-ok`.
- `git branch --show-current` returned
  `feature/workflow-remove-netplan-repository-20260627`.

## Staleness Conditions

This context pack is stale if any governing input hash changes, if the active
branch changes, if new imports of `PortNetplanRepositoryYaml` appear, or if a
documentation conflict requires ADR or arc42 changes before execution.
