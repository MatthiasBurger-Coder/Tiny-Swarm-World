# Workflow Context Pack

Workflow: `installation-phases-port-registry-v1.0.0`
Workflow ID: `workflow-install-order-and-port-allocation-20260620`
Branch: `feature/workflow-installation-phases-port-registry-20260620`
Created: `2026-06-20`
Status: `READY_FOR_WORKFLOW`
Evidence Root: `.codex/evidence/workflow-install-order-and-port-allocation-20260620/`

## Purpose

This context pack is a workflow-local navigation aid for executing the installation phases and port registry workflow. It does not replace root `AGENTS.md`, `QUALITY.md`, ADRs, arc42 files, or active workflow files.

## Process Strand

- Active command: `workflow create`
- Execution profile: `FULL_PATH`
- Workflow target: deterministic setup phase ordering and central port registry.

## Affected Areas

- `infra/config/**`
- `infra/config/compose/**`
- `src/tiny_swarm_world/domain/preflight/**`
- `src/tiny_swarm_world/domain/network/**`
- `src/tiny_swarm_world/domain/deployment/**`
- `src/tiny_swarm_world/application/ports/repositories/**`
- `src/tiny_swarm_world/application/services/setup/**`
- `src/tiny_swarm_world/application/services/platform/**`
- `src/tiny_swarm_world/application/services/deployment/**`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/**`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `tests/**`
- `documentation/**`

## Forbidden Areas

- Java, Maven, Spring Boot project structure.
- Browser React frontend project structure.
- Kubernetes-first deployment behavior.
- Multipass provider support.
- Live infrastructure mutation during default quality gates.
- Committed secrets, tokens, host IP addresses, local absolute paths, raw command output, or credential-bearing URLs.

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer impact check
- Senior Tester

## Conditional Roles

- Senior DevOps Engineer for compose, Docker Swarm, LXC exposure, and runtime stack changes.
- Senior Documentation Engineer for README, arc42, deployment, and system docs.
- Security/secrets reviewer for credential references, exposed ports, and evidence.
- Quality Gate Orchestrator for final quality classification.

## Quality Commands

Targeted:

- `git diff --check`
- `PYTHONPATH=src python3 -m unittest <nearest test modules>`

Required final:

- `python3 tools/quality_gate.py quality`

## Evidence Governance

- Evidence files for this workflow must be written only below `.codex/evidence/workflow-install-order-and-port-allocation-20260620/`.
- Generic evidence paths such as `.codex/evidence/slice-01-distribution.md` and `.codex/evidence/slice-01-consolidation.md` are forbidden.
- Before writing evidence, verify that the target file is absent or belongs to this workflow.
- If an evidence file exists and belongs to another workflow, stop and report a blocker instead of overwriting it.

## Governing File Hashes

| File | SHA256 |
|---|---|
| `AGENTS.md` | `FB1EE9B2A878D4662C96B9BC7255F3D7EC151FB2D1997FD981D4D1A34F54EC3F` |
| `QUALITY.md` | `458E5F4D8FBDEDEA1C413E1FF135EC91392A4BB5A5AEA20300DCAC8E209414B6` |
| `.agents/skills/workflow-authoring/SKILL.md` | `5EF238CA8A98D08A3594906E5A30100649D4C09E64A01B377D690F6580B1CA03` |
| `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md` | `23DE7D9AAC9D2694EAE26FAC2765D65F369C101AC348DAC24D5F3BBE9E2D3BA4` |
| `.agents/orchestrator/routing-rules.md` | `BA3563181DB98DF3F6A1872D676006CF57CC1603C1B0B74D4C41CD3DB02A60A5` |
| `documentation/process/branch-governance.md` | `3332F0FB56E7A72FEE3A9B6E89C4D9D5C3BF1198B375CE4D2BBD5C7350588A83` |
| `documentation/epics/autonomous-runnable-setup.md` | `758F291E311CF8232937B6820CE6122126C3C8353276E3D38FFF6C5EDE079691` |
| `documentation/epics/service-access-dashboard-vaultwarden.md` | `9C93D460A92630F485C0672F26810ECB4832C69D21A8F6F0941DFFA4AACD1606` |
| `documentation/arc42/07_deployment_view.adoc` | `8CC484BBB06C42CFEF2E933AB047716B54AEE655E5C62D711E2485151F07BF5C` |
| `documentation/arc42/08_concepts.adoc` | `6AD298D14F6AA4BEF530A25C88EA1AB171AC8EF48A295089025D0B716BF78C0F` |
| `documentation/arc42/09_architecture_decisions.adoc` | `2C9811C38F1AD2AE4E516C6A4C3C7DBA808FC208B687242C965EB43CCF3FD051` |
| `documentation/arc42/10_quality_requirements.adoc` | `F2F824FC64B1DC05AEB8CE49A30833E2F426AED397F1193470ED2DC43BAAB865` |

## Staleness Rules

This context pack is stale when:

- any governing hash changes;
- `documentation/workflow/workflow.md` changes without updating this pack;
- any branch mismatch is detected;
- an ADR changes the Traefik ingress or setup safety baseline;
- a workflow execution slice changes quality commands or allowed file locks.

## Branch Evidence

- Dedicated branch: `feature/workflow-installation-phases-port-registry-20260620`
- Branch ref verification: `git show-ref --verify --quiet refs/heads/feature/workflow-installation-phases-port-registry-20260620`
- Active branch verification: `git branch --show-current`

## arc42 Check

Checked during workflow creation:

- `documentation/arc42/05_building_blocks.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/08_concepts.adoc`
- `documentation/arc42/09_architecture_decisions.adoc`
- `documentation/arc42/10_quality_requirements.adoc`

No arc42 file was modified during workflow creation. Slice 01 and Slice 07 own execution-time synchronization.
