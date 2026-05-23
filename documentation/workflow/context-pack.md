# Workflow Context Pack

## Workflow Identity

- Workflow version: `tasklist-remediation-20260523`
- Workflow branch: `architecture/workflow-tasklist-remediation-20260523`
- Process strand: `workflow create`
- Execution profile: `FULL_PATH`
- Created on: `2026-05-23`

## Purpose

This context pack records the governing inputs used to convert `TASKLIST.md`
into the active remediation workflow and remove the stale task-list artifact.
It is a navigation aid only. Root `AGENTS.md`, `QUALITY.md`, the active workflow
and repository files remain authoritative.

## Converted Source Artifacts

| Artifact | Status | SHA-256 |
|---|---|---|
| `TASKLIST.md` | converted and deleted | `96295c760ceaee6217e7987ff0b7bbd034479332d3f3d8341d2bcc4e55df9f48` |
| `AUDIT_REPORT.md` | retained as audit evidence | `b6714f0898a5ae2eca750516e920a1f412584f43ebc6e195b5d5d61c741c0816` |

## Affected Areas

- `documentation/workflow`
- `src/tiny_swarm_world`
- `infra`
- `tests`
- `README.md`
- `documentation`
- `QUALITY.md` only if a later slice explicitly changes quality policy
- `tools/quality_gate.py` only if a later slice explicitly changes gate
  behavior

## Forbidden Areas Without Refinement

- `src/main/java/**`
- live Multipass execution
- live Docker Swarm execution
- compose deployments
- netplan mutation
- `socat` forwarding
- service bootstrap scripts
- frontend package/tooling creation
- restoring `TASKLIST.md` as an active planning artifact

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer
- Senior Tester
- Senior DevOps Engineer
- Senior Documentation Engineer

## Conditional Roles

- Senior Security Sandbox Engineer for secret handling and live-infra safety.
- Senior Bash Specialist if the previous Bash specialist workflow has been
  executed and the role exists.

## Quality Commands

```bash
git diff --check
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

Optional shell syntax check for shell slices:

```bash
find infra -name '*.sh' -print0 | xargs -0 bash -n
```

## Governing Hashes

| Path | SHA-256 |
|---|---|
| `AGENTS.md` | `6c0995195e99a2a748ad63d065706c35341977388d3c1c4402a548b388a4755e` |
| `QUALITY.md` | `d327e4060ff1729f17ffde844b1a2d6208fe203e149ae9d1af185bef0aed2155` |
| `AUDIT_REPORT.md` | `b6714f0898a5ae2eca750516e920a1f412584f43ebc6e195b5d5d61c741c0816` |
| `.agents/orchestrator/routing-rules.md` | `a524843f96fa91adc56cbe8b02156abc56a299b263eb8ad6715204bee52cfd31` |
| `.agents/skills/workflow-authoring/SKILL.md` | `087658240296e3b1ec74205c60a96a9a4c67a17cf653f7867e6f316bd9afa94e` |
| `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md` | `23de7d9aac9d2694eae26fac2765d65f369c101ac348dac24d5f3bbe9e2d3ba4` |
| `.agents/skills/execution-profile-router/SKILL.md` | `a1e1195387d55b8ba3baa6b5a891aac982f6ffc734a80c1ab32dc594d4cfc51b` |
| `.agents/skills/quality-gate/SKILL.md` | `90fe1c9de050f21cb8635fab1b498b93439fffdc050d3b7ceb04bd8d2deea174` |
| `.agents/skills/quality-architecture-validation/SKILL.md` | `a00a8e7e2ea24c4878533272f0f98b687156e0279a8fa84f67676248b8000e78` |
| `.importlinter` | `4c5c879ddc20bf7ccb8adca2b907538264f9c3cf9c1c54e3076e7c008f1a62b4` |
| `tools/quality_gate.py` | `89425bfc2348fcbc9948a6f654d00fa80aeaa03ce46403912fbb207d137fe0ea` |

## Staleness Rules

This context pack is stale when:

- any recorded governing hash changes;
- `documentation/workflow/**` changes outside the active slice;
- `AGENTS.md` or `QUALITY.md` changes;
- a deleted `TASKLIST.md` entry cannot be traced through the workflow;
- workflow execution changes architecture, quality, live-infra or secret
  handling policy without updating the workflow.
