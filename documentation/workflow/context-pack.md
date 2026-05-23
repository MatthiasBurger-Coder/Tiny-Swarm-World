# Workflow Context Pack

## Workflow Identity

- Workflow version: `agents-skills-python-quality-bash-20260523`
- Workflow branch:
  `architecture/workflow-agents-skills-python-quality-bash-20260523`
- Process strand: `workflow create` for skills and agents governance
- Execution profile: `FULL_PATH`
- Created on: `2026-05-23`

## Purpose

Provide a workflow-local navigation aid for the agent and skill alignment
workflow. This context pack does not replace root `AGENTS.md`, `QUALITY.md`,
active workflow files, ADRs, arc42 documents or skill files.

## Affected Areas

- `.agents/roles`
- `.agents/skills`
- `.agents/orchestrator`
- `.agents/prompts`
- `.codex/agents`
- `.codex/subagents`
- selected `.codex/skills` Java guards
- `documentation/process`
- `documentation/arc42`
- `documentation/workflow`

## Forbidden Areas

- `src/tiny_swarm_world/**`
- `src/main/java/**`
- `infra/**/*.sh` behavior changes
- live infrastructure commands
- default quality-gate behavior changes without explicit approval
- required shellcheck/shfmt gates without `QUALITY.md` authority

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer
- Senior Tester
- Senior DevOps Engineer
- Senior Documentation Engineer

## Conditional Roles

- Senior Security Sandbox Engineer for Bash safety and secret handling.
- Future Senior Bash Specialist after Slice 03 creates the role, skill and
  callable agent.

## Quality Commands

```bash
git diff --check
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py quality
```

Targeted gates from `QUALITY.md`:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
```

Optional Bash diagnostics only:

```bash
shellcheck infra/**/*.sh
shfmt -d infra/**/*.sh
```

## Governing Hashes

| Path | SHA-256 |
|---|---|
| `AGENTS.md` | `6C0995195E99A2A748AD63D065706C35341977388D3C1C4402A548B388A4755E` |
| `QUALITY.md` | `D327E4060FF1729F17FFDE844B1A2D6208FE203E149AE9D1AF185BEF0AED2155` |
| `.agents/orchestrator/routing-rules.md` | `A524843F96FA91ADC56CBE8B02156ABC56A299B263EB8AD6715204BEE52CFD31` |
| `.agents/prompts/workflow-create.md` | `BCBAFB53A543D66B660DC50FC9E85712FEFCC07568388192FC8E89B3625D808A` |
| `.agents/skills/workflow-authoring/SKILL.md` | `087658240296E3B1EC74205C60A96A9A4C67A17CF653F7867E6F316BD9AFA94E` |
| `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md` | `23DE7D9AAC9D2694EAE26FAC2765D65F369C101AC348DAC24D5F3BBE9E2D3BA4` |
| `.agents/skills/execution-profile-router/SKILL.md` | `A1E1195387D55B8BA3BAA6B5A891AAC982F6FFC734A80C1AB32DC594D4CFC51B` |
| `.agents/skills/skill-registry-conflict-auditor/SKILL.md` | `E5101862CF8123F11428F521EA0DAEFBBE35CFFEB72E16E2E811796A8377C05C` |
| `.agents/skills/python-automation/SKILL.md` | `6F79E223C517068DD30452A01837540B0696E486C8BE75031D5023F901D98721` |
| `.agents/skills/quality-gate/SKILL.md` | `90FE1C9DE050F21CB8635FAB1B498B93439FFFDC050D3B7CEB04BD8D2DEEA174` |
| `.agents/skills/quality-architecture-validation/SKILL.md` | `A00A8E7E2EA24C4878533272F0F98B687156E0279A8FA84F67676248B8000E78` |
| `.importlinter` | `4C5C879DDC20BF7CCB8ADCA2B907538264F9C3CF9C1C54E3076E7C008F1A62B4` |
| `tools/quality_gate.py` | `89425BFC2348FCBC9948A6F654D00FA80AEAA03CE46403912FBB207D137FE0EA` |

## Staleness Rules

This context pack is stale when:

- any recorded hash changes;
- `.agents/**`, `.codex/**`, `AGENTS.md`, `QUALITY.md`,
  `documentation/process/**`, `documentation/arc42/**` or
  `documentation/workflow/**` changes outside the active slice;
- any quality command, role owner, routing rule or stop condition conflicts
  with an authoritative source.
