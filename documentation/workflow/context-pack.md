# Workflow Context Pack: Issue #183

This is a navigation aid for `issue-183-20260808`; repository source files,
process policies, ADRs, skills, roles, and the active workflow remain the
authorities. The pack is stale if any recorded governing hash changes.

## Identity

* Workflow ID: `issue-183-20260808`
* Workflow version: `issue-183-v1.0.0`
* Authoring branch: `feature/workflow-issue-183-lxc-runtime-solid-20260808`
* Issue implementation branch requested by #183: `feature/split-lxc-swarm-runtime-solid`
* Process strand: `workflow-create-to-workflow-execute`
* Execution profile: `FULL_PATH`
* Status: `READY_FOR_EXECUTION`

## Affected areas

* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
* new `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/{command,swarm,docker,services,images}/`
* `src/tiny_swarm_world/infrastructure/composition.py`
* `src/tiny_swarm_world/infrastructure/composition_lxc_runtimes.py`
* infrastructure adapter, architecture, composition, and live browser tests
* `.tiny-swarm/evidence/solid-lxc-swarm-runtime/`
* planned Arc42 building-block and risk documentation

## Forbidden areas

* `PortLocalFileStorage` without a verified requirement
* application-port redesign, new deployable services, REST/gRPC/Protobuf
  contracts, Kubernetes-first work, React frontend, Java/Maven/Spring Boot
* live Incus, Docker Swarm, networking, Portainer, Nexus, or credential-backed
  mutation during local implementation and quality gates
* raw credentials, tokens, command output, HTTP payloads, or unredacted browser
  evidence
* claims that SonarQube or Selenium succeeded without actual observable evidence

## Required roles

Senior Requirement Engineer, Senior System Architect, Senior Python Automation
Developer, Senior Tester, Senior Workflow Architect, Senior DevOps Engineer,
Senior Documentation Engineer, Senior Security Sandbox Engineer, and Issue
Completion Auditor. Console/status UI is `NOT_APPLICABLE`; Browser React is
forbidden for this repository scope.

## Required commands

* `python3 tools/quality_gate.py lint`
* `python3 tools/quality_gate.py arch-lint`
* `python3 tools/quality_gate.py arch-tests`
* `python3 tools/quality_gate.py typecheck`
* `python3 tools/quality_gate.py test`
* `python3 tools/quality_gate.py quality`
* `git diff --check`

## Verification classification

* Local adapter, architecture, composition, and quality tests:
  `APPLICABLE_LOCAL`.
* Issue-specific browser E2E: `APPLICABLE_LIVE`; explicit consent and
  prerequisites are required, and missing consent is not success.
* SonarQube: `APPLICABLE_EXTERNAL`; only an actual observable passing result
  is accepted.
* Live infrastructure mutation during default gates: `NOT_APPLICABLE`.

## Navigation

* Active workflow: `documentation/workflow/workflow.md`
* Requirement matrix: `.tiny-swarm/evidence/solid-lxc-swarm-runtime/requirement_matrix.md`
* Three-Amigos note: `.tiny-swarm/evidence/solid-lxc-swarm-runtime/three-amigos.md`
* Before map: `.tiny-swarm/evidence/solid-lxc-swarm-runtime/responsibility-map-before.md`
* Live E2E target: `.tiny-swarm-world/evidence/solid-lxc-swarm-runtime/e2e/`
* Arc42 planned architecture: `documentation/arc42/05_building_blocks.adoc`
* Arc42 risk note: `documentation/arc42/11_risks_and_debt.adoc`

## Governing file hashes

The hashes below are SHA-256 values captured during workflow authoring. Recheck
them before execution and regenerate this context pack if they change.

| File | SHA-256 |
| --- | --- |
| `AGENTS.md` | `bc0e6e0c09ac3d61a450a7fe16c3e4de9e6fbb8bdc688aad58f10a3d18b31041` |
| `QUALITY.md` | `7f8dd247fd989fbb72588a48b00846edcb2a9aa748bb1954dc22b75952efaa4c` |
| `documentation/process/issue-completion-discipline.md` | `3db2d080b7cfbbc3737907a61c67ce6a361485c8993cf4a20c1c5fe2dc743bc3` |
| `documentation/process/workflow-create.md` | `5df5fb70ddc25ef2d8ad2129590e780bfee610521860fb0991e57c38dab3542f` |
| `documentation/process/verification-state-policy.md` | `5b6e2eefde66a1b8492afafc2976e59ac40f16e7100f79f730b97b254febdcfd` |
| `documentation/process/branch-governance.md` | `1472428b96f84aacb988d55a06c310dca38b64dc12c146c4f5d81dafb1e8375c` |
| `.agents/prompts/workflow-create.md` | `45c5c8e585c50b7fcb6892b5fbfb952aa29ef27c3df34f177ad579ba65542296` |
| `.agents/orchestrator/routing-rules.md` | `3accea3112bc207eda96e02b3fe4831b79669f7c8f6a5668f577fca7d0fed050` |
| `.agents/skills/workflow-authoring/SKILL.md` | `5733f64086f113d578544b4d2d0297554237296adf0dc2df5ebe641e50dec9e5` |
| `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md` | `76659e618cb706e8990cdf44441aeaed219465044175826adca5357ae8acc5b4` |
| `.agents/skills/execution-profile-router/SKILL.md` | `45cf509082e3d9036379228a4c1a195cb22a05f11487e10a5c4000e8aad9608e` |
| `documentation/arc42/05_building_blocks.adoc` | `17ab5eba08c0fef5a0d9e57f20be03b322ffaf92e7658fa0810509818ad3157e` |
| `documentation/arc42/11_risks_and_debt.adoc` | `c3d55c559ab92d5c630ba123520fbd2b3e316630f3dd19daf8de9b0d182a350d` |
| `documentation/workflow/workflow.md` | `5e553220c5e0b7f5693252d73b739effb78c0a7705a15e6e9879a6144e393dee` |
| `.tiny-swarm/evidence/solid-lxc-swarm-runtime/requirement_matrix.md` | `746b97c6a2a4b9d4f67f42647ec304c875d15a2f2a0f3e244ac632824e932e76` |
