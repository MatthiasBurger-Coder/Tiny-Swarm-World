# Workflow Context Pack

## Workflow Identity

- Workflow version: `init-safety-boundary-separation-20260523`
- Workflow branch: `architecture/workflow-init-service-boundaries-20260523`
- Process strand: `workflow create`
- Execution profile: `FULL_PATH`
- Created on: `2026-05-23`

## Execution Precedence

This context pack belongs to the broader roadmap workflow. On branch
`docs/workflow-init-safety-first-control-plane-20260523`,
`documentation/workflow/workflow-init-safety-first-control-plane.md` is the
active workflow-execute authority because `workflow.md` explicitly gives that
file execution precedence before broader roadmap work.

## Purpose

This context pack records the governing inputs used to create the workflow for
non-destructive init, separated reconcile/reset/destroy workflows, real
Platform/Artifacts/Deployment service boundaries, workflow-level CLI, Nexus
stack deployment extraction, typed command YAMLs, state/inventory modeling and
verify-after-apply enforcement.

It is a navigation aid only. Root `AGENTS.md`, `QUALITY.md`, ADRs, arc42,
repository source and workflow files remain authoritative.

## Requirement Source

The workflow was created from the user request:

- remove destructive VM cleanup from normal init;
- introduce reconcile/reset/destroy as separate workflows;
- truly separate PlatformServices, ArtifactServices and DeploymentServices;
- rebuild the CLI around workflow-level commands;
- extract Nexus stack deployment from Artifacts/Nexus;
- strengthen command YAML typing;
- introduce a state/inventory model;
- force verify steps after every apply;
- use subagent review during workflow creation.

No dedicated EPIC exists under `documentation/epics`. The temporary baseline is
the user request, `AGENTS.md`, `QUALITY.md`, subagent review output, current
architecture docs, arc42 and the Platform/Artifacts/Deployment responsibility
ADR. That ADR is now accepted as a responsibility direction and partially
implemented.

## Verified Baseline At Workflow Creation

This baseline is historical. It records the state used to create the broader
roadmap workflow before the safety-first workflow execution branch applied
Slices 01 through 09.

- Default quality gate: `python3 tools/quality_gate.py quality`.
- Default quality gate must not run live infrastructure.
- Normal init currently calls the Multipass cleanup command YAML.
- The cleanup command YAML contains `multipass delete --all` and
  `multipass purge`.
- Composition currently exposes platform services only.
- At workflow creation, the CLI exposed low-level service choices.
- Nexus stack deployment currently lives under Nexus service code.
- At workflow creation, command YAML validation was not yet a typed schema
  contract.
- At workflow creation, desired inventory and observed runtime state were not
  yet separated.
- Netplan apply has no mandatory typed verification gate.

## Safety-First Execution Status

On branch `docs/workflow-init-safety-first-control-plane-20260523`, the
safety-first workflow is the active execution authority. Checkpoint commits
through Slice 09 have implemented:

* non-destructive normal init;
* workflow taxonomy and workflow-level CLI routing;
* Platform, Artifacts, and Deployment service bundles;
* Deployment namespace ownership for `EnsureNexusStack`, with deployment
  workflow composition still pending;
* typed command YAML contracts and workflow allow-lists;
* desired inventory, observed inventory, and verification evidence separation;
* verify-after-apply behavior for mutating platform workflows.

This context pack remains a navigation aid, not the current execution status
report.

## Affected Areas

- `documentation/workflow`
- `documentation/architecture`
- `documentation/arc42`
- `README.md`
- `documentation/user_guide`
- `src/tiny_swarm_world/__main__.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `src/tiny_swarm_world/domain`
- `src/tiny_swarm_world/application`
- `src/tiny_swarm_world/infrastructure/adapters`
- `infra/config`
- `infra/compose`
- `infra/prepare`
- `infra/swarm`
- `tests`

## Forbidden Areas Without Refinement

- `src/main/java/**`
- Windows-native runtime support
- default CI execution of live Multipass or Docker Swarm
- committed secrets, observed runtime state, local evidence or host-specific
  absolute paths
- implicit VM deletion or purge in `init` or `reconcile`
- treating Platform, Artifacts and Deployment as independently deployable
  microservices without runtime evidence
- live Multipass, Docker Swarm, netplan, socat, compose, Portainer, Nexus,
  Jenkins, RabbitMQ, SonarQube or Swagger/NGINX commands

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer
- Senior Tester
- Senior Security Sandbox Engineer
- Senior Documentation Engineer
- Senior Workflow Architect

## Conditional Roles

- Senior DevOps Engineer for shell/script and live-operation safety review.
- Release and Branch Governance before commit, push or PR.
- Security Threat Modeling if reset/destroy confirmation or secret handling is
  changed.

## Quality Commands

Workflow creation:

```bash
git diff --check
python3 -m json.tool documentation/workflow/context-pack.json
```

Targeted development gates:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
```

Final implementation gate:

```bash
python3 tools/quality_gate.py quality
```

## Slice Summary

| Slice | Name | Dependencies |
| --- | --- | --- |
| 01 | Requirement And Safety Contract | none |
| 02 | ADR And arc42 Baseline | 01 |
| 03 | Typed Command YAML Contract | 01, 02 |
| 04 | State And Inventory Model | 01, 02 |
| 05 | Workflow Taxonomy And Non-Destructive Init | 03, 04 |
| 06 | Service Wiring Separation | 02, 04 |
| 07 | Nexus Stack Deployment Extraction | 06 |
| 08 | Workflow-Level CLI | 05, 06, 07 |
| 09 | Verify After Every Apply | 03, 04, 05, 07, 08 |
| 10 | Documentation, Quality Sync, And Legacy Quarantine | 02-09 |

## Governing Hashes

| Path | SHA-256 |
| --- | --- |
| `AGENTS.md` | `6c0995195e99a2a748ad63d065706c35341977388d3c1c4402a548b388a4755e` |
| `QUALITY.md` | `d327e4060ff1729f17ffde844b1a2d6208fe203e149ae9d1af185bef0aed2155` |
| `.agents/skills/workflow-authoring/SKILL.md` | `087658240296e3b1ec74205c60a96a9a4c67a17cf653f7867e6f316bd9afa94e` |
| `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md` | `23de7d9aac9d2694eae26fac2765d65f369c101ac348dac24d5f3bbe9e2d3ba4` |
| `.agents/skills/swarm-coordination/SKILL.md` | `8e6d032e4b609212ad7229b26fe1aa72af4afc0d6594a01cc945053a0b3e9ba7` |
| `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc` | `e93d07dc6ce9485208a40d77b6a2c52a5d5442f36845192eac0963a86dc00297` |
| `documentation/architecture/migration-plan.md` | `dbf5618e62b96935b669cf880b3be84710c8a29ba7ce9a4f4aaf08ccf5a21e2f` |
| `documentation/architecture/responsibility-separation-analysis.md` | `38b08d772951f87b168f9432a8aadbd8b3705d5fedd2cc8511c8ad4a36eec078` |
| `src/tiny_swarm_world/__main__.py` | `5cf743ac4c186418a2e649458965b917e52f9cd78605c2eb3cf55febd7e7f4e3` |
| `src/tiny_swarm_world/infrastructure/composition.py` | `67aae1f2cf4a769500b16e27d2551981568a01fc24cc3b39d26eee05e111339a` |
| `src/tiny_swarm_world/application/services/multipass/multipass_init_vms.py` | `bc65b41f859e99eb7ff5ce8d6d59c33e062d1358a89588eb133735383f149b79` |
| `infra/config/multipass/command_multipass_clean_repository_yaml.yaml` | `bb483b476e21b225971051c07515948b33ab53a1778bbe1a2d62761361ed2deb` |
| `infra/config/network/netplant/command_netplant_setup_yaml.yaml` | `614f6206b97de2cd0e31c60986cddc5ef5dba759c2856ca8f6eb0e730c4670e4` |
| `tests/architecture/test_hexagonal_imports.py` | `1d9a78e08bc3f8f893ca0343d3bd2aaf544c997e09278345f5472b70114cc0be` |
| `tests/architecture/test_infra_responsibility_boundaries.py` | `973b13559bf11304a0023713a4cf842d223962309198660f710598d37bd97ba8` |

## Worktree Caveat

During workflow creation, uncommitted source/preflight changes appeared outside
`documentation/workflow/**`. This workflow authoring step did not edit those
files. Workflow execution must inspect and resolve ownership before any slice
touches overlapping paths.

## Staleness Rules

This context pack is stale when:

- any recorded governing hash changes;
- `AGENTS.md` or `QUALITY.md` changes;
- the responsibility ADR is accepted, superseded or edited;
- command YAML schema, destructive-operation policy, inventory model or CLI
  workflow contract changes;
- `documentation/workflow/**` changes outside the active workflow branch;
- source/preflight worktree changes overlap an implementation slice without a
  recorded handoff;
- arc42 runtime, deployment, concept, quality or risk sections change without
  checking this workflow.
