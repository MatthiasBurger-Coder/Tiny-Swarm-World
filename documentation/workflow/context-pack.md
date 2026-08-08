# Workflow Context Pack: Issue #188

This is a navigation aid for `issue-188-20260809`. Repository source files,
process policies, ADRs, Arc42, skills, roles, and the active workflow remain
authoritative. The pack is stale if a recorded governing hash changes.

## Identity

- Workflow ID: `issue-188-20260809`
- Workflow version: `issue-188-v1.0.0`
- Authoring branch: `feature/workflow-issue-188-shared-command-runners-20260809`
- Implementation branch requested by Issue #188: `feature/issue-188-shared-command-runners`
- Process strand: `workflow-create-to-workflow-execute`
- Execution profile: `FULL_PATH`
- Status: `READY_FOR_EXECUTION`

## Affected areas

- New infrastructure-only shared process runner package and tests.
- `src/tiny_swarm_world/infrastructure/composition.py` wiring.
- Docker, LXC gateway, LXC container, LXC image publisher, and host preflight
  adapters plus nearest regression tests.
- Production process-spawn architecture enforcement.
- `.tiny-swarm/evidence/solid-command-runner/` and the issue-requested
  `.tiny-swarm-world/evidence/solid-command-runner/`.
- Planned Arc42 building-block, concept, quality, and risk notes.

## Forbidden areas

- application/domain port redesign;
- new LXC gateway or rework of Issue #183;
- Issue #187, #189, #190, #192, #184, or #195 scope;
- Java/Maven/Spring Boot and browser React;
- live Incus/LXC, Docker, Swarm, networking, registry, service bootstrap,
  browser, or credential-backed mutation;
- raw credentials, tokens, environment payloads, command output, HTTP bodies,
  or unredacted evidence;
- claims that local checks establish live or SonarQube success.

## Required roles

Senior Requirement Engineer, Senior System Architect, Senior Python Automation
Developer, Senior Tester, Senior Workflow Architect, Senior Security Sandbox
Engineer, Senior DevOps Engineer, Senior Documentation Engineer, and Issue
Completion Auditor. Dependency/deadlock validation is required. Console/status
UI is `NOT_APPLICABLE`; Browser React is `FORBIDDEN_UNLESS_SEPARATE_FRONTEND_WORKFLOW`.

## Required commands

- `python3 tools/quality_gate.py lint`
- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`
- `python3 tools/quality_gate.py typecheck`
- `python3 tools/quality_gate.py test`
- `python3 tools/quality_gate.py quality`
- `git diff --check`

## Verification classification

- Shared runner, adapter, architecture, composition, and quality tests:
  `APPLICABLE_LOCAL`.
- Live installation/browser verification: `NOT_REQUIRED_BY_ISSUE`; if later
  authorized, classify through the canonical live state policy.
- SonarQube: `NOT_REQUIRED_BY_ISSUE`; no external result is claimed.
- Live infrastructure mutation during default gates: `NOT_APPLICABLE` and
  forbidden without explicit authorization.

## Navigation

- Active workflow: `documentation/workflow/workflow.md`
- Requirement matrix: `.tiny-swarm/evidence/solid-command-runner/requirement_matrix.md`
- Three-Amigos note: `.tiny-swarm-world/evidence/solid-command-runner/three-amigos.md`
- Before inventory: `.tiny-swarm/evidence/solid-command-runner/process-spawn-inventory-before.md`
- After inventory target: `.tiny-swarm/evidence/solid-command-runner/process-spawn-inventory-after.md`
- Arc42 building blocks: `documentation/arc42/05_building_blocks.adoc`
- Arc42 concepts: `documentation/arc42/08_concepts.adoc`
- Arc42 quality: `documentation/arc42/10_quality_requirements.adoc`
- Arc42 risks: `documentation/arc42/11_risks_and_debt.adoc`

## Governing file hashes

Hashes are captured after workflow and Arc42 authoring validation. Recheck
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
| `documentation/arc42/05_building_blocks.adoc` | `172fef095693bae325a54f45abc3774ffc3b61377f73f66025c8d59a4ccba5b8` |
| `documentation/arc42/08_concepts.adoc` | `66a71541982d656719946016334371db08feae223db33526c5297ca68ebc5ae7` |
| `documentation/arc42/10_quality_requirements.adoc` | `e91bfcb7b925fa727240fee02b4cc20680f26460137fb600ca4e4584f4c07fdc` |
| `documentation/arc42/11_risks_and_debt.adoc` | `368483cde864b7d35a8319ebf37fe9bd37c08eeb5bb7f36d6e0e2fe835146426` |
| `documentation/workflow/workflow.md` | `87e059f16c3c2153cd566fbf6bdd64995c1de9a4f2365a528676fc580f85ffe9` |
| `.tiny-swarm/evidence/solid-command-runner/requirement_matrix.md` | `73727bf42fef5ed649a9826d159e8e472c339499b9102bd7103c98d8a4ce4a18` |
| `.tiny-swarm-world/evidence/solid-command-runner/three-amigos.md` | `d1fabe5558bd5b4c86ec644a04fce303e4fe846114896fdfcb28667608f15a23` |
