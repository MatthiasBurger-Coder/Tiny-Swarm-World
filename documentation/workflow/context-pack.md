# Workflow Context Pack: Tiny Swarm Skills And Agents

## Purpose

This context pack is the navigation aid for the active workflow:

```text
Consolidate Tiny Swarm World Skills and Agents
```

It does not replace root `AGENTS.md`, root `QUALITY.md`, arc42 documentation,
`.agents/`, `.codex/`, or the active workflow file.

## Active Workflow

- Workflow file: `documentation/workflow/workflow.md`
- Branch: `feature/workflow-tiny-swarm-skills-agents-20260523`
- Date created: `2026-05-23`
- Process strand: `skills-agents`
- Execution profile: `FULL_PATH`
- Release status: `WORKFLOW_EXECUTION_COMPLETED`

## Execution Status

| Slice | Status |
| --- | --- |
| 01 | `COMPLETED` |
| 02 | `COMPLETED` |
| 03 | `COMPLETED_NO_CHANGES_REQUIRED` |
| 04 | `COMPLETED` |
| 05 | `COMPLETED` |
| 06 | `COMPLETED` |
| 07 | `COMPLETED` |
| 08 | `COMPLETED` |

## Governing Files Checked

| File | SHA-256 |
| --- | --- |
| `AGENTS.md` | `F0FA2387DFA023B968A0F474971BACDA12EBF05FEA4A03B5D6D098F1701D4601` |
| `QUALITY.md` | `D327E4060FF1729F17FFDE844B1A2D6208FE203E149AE9D1AF185BEF0AED2155` |
| `README.md` | `31C6AA7F2907D2C773C4ADD14F31235AB620F3A11B3D9DB913004A69D8650A24` |
| `documentation/arc42/05_building_blocks.adoc` | `29460A5324C6675DF4F731686733A4369828C42DE2AC485967D25B5A8429BE32` |
| `documentation/arc42/08_concepts.adoc` | `6736AFC526995312EE33D64D7B9E1853CD5AE509293DF5EB518AF1F200EEA857` |
| `documentation/arc42/10_quality_requirements.adoc` | `687988FCBC74CF6573136570486E22E9CC9E6573B11385307BBEFBE1436AD144` |
| `documentation/skill-audit/skill-registry.md` | `E231255A840818A92D3AC49692636FB0BE2F46651E370080AF3196EB529BD3FA` |
| `documentation/skill-audit/skill-registry.json` | `7628D2FB431880C3CD901433AC6F0B6B82F5565FD4861FAE259E00220F1606C3` |
| `documentation/skill-audit/organigramm.md` | `542F1E8FC0E9311DEF5B0D456D31F7F19B09B8A17F621CF4F26006CD81CA7190` |
| `documentation/skill-audit/owner-map.md` | `19E2AE03E5A120E8244A7904A59BB78C53EDA42959428220E101F4CCFAFE1A46` |

This context pack is stale when any listed hash changes, when governance files
change, when `.agents/` or `.codex/` structure changes, or when a conflict is
detected during workflow execution.

The baseline notes in `documentation/workflow/workflow.md` describe the
workflow creation state. The current execution state is recorded here and in
`documentation/workflow/execution-report.md`.

## Affected Areas

- Root agent and subagent governance.
- `.agents/skills/` target structure.
- `.agents/roles/` references.
- `.agents/prompts/` and `.agents/orchestrator/` process routing references.
- `.codex/agents/`, `.codex/subagents/`, `.codex/skills/`, and
  `.codex/workflow/` references.
- `AGENTS.md`, `README.md`, `documentation/process/`,
  `documentation/skill-audit/`, and `documentation/`.

## Forbidden Areas

- Runtime Python source under `src/tiny_swarm_world/**`.
- Java deployment example under `src/main/java/**`.
- Infrastructure assets under `infra/**`.
- Runtime scripts, Dockerfiles, compose files, stack files, `tools/**`,
  `requirements.txt`, `setup.py`, and `pom.xml`.

Only non-executable metadata reference corrections may cross this boundary,
and only when recorded by the executing slice. Executable Python source,
`tools/**`, `requirements.txt`, or `setup.py` changes require a STOP and a
separate implementation workflow.

## Required Roles

- `senior_workflow_architect`
- `senior_requirement_engineer`
- `senior_system_architect`
- `senior_python_automation_developer`
- `senior_react_frontend` with read-only scope limited to frontend exclusion
  and console-status UI clarification
- `senior_documentation_engineer`
- `senior_tester`

## Conditional Roles

- `git_commit_reviewer`
- `git_commit_operator`
- `quality_reviewer`
- `security_reviewer` when secret/config skill text changes
- `senior_devops` when Docker Swarm or setup/bootstrap responsibilities need
  operational review

## Quality Commands

Minimum:

```bash
git status
find .agents -type f | sort
find .codex -type f | sort
find .agents/skills -name SKILL.md -type f | sort
grep -R "spring-boot-expert\|forensic-analytics-expert\|react-developer" AGENTS.md README.md documentation .agents .codex || true
grep -R "python-senior-developer\|python-pip-packaging-expert\|setup-bootstrap-expert" .agents AGENTS.md documentation .codex README.md || true
grep -R "^## Purpose\|^## Responsibilities\|^## Inputs\|^## Outputs\|^## Boundaries\|STOP" .agents/skills || true
grep -R "documentation/agents\|documentation/skill-audit\|Organigramm Maintainer\|Process Governance Maintainer\|Typed Error Router" .agents documentation .codex AGENTS.md README.md || true
git diff --check
```

Preferred full gate:

```bash
python3 tools/quality_gate.py quality
```

## Stop Rules

Stop when:

- active branch is not `feature/workflow-tiny-swarm-skills-agents-20260523`;
- unrelated or unclear changes exist;
- confidence drops below 95 percent;
- `.agents/` or `AGENTS.md` is missing;
- a skill deletion candidate is still referenced with no safe replacement;
- registry, organigramm, Root Architect, or Typed Error Router ownership is
  still ambiguous after Slice 01;
- skill-file format remains ambiguous between grouped `.md` files and
  `<skill>/SKILL.md` entrypoints after Slice 01;
- executable Python source, `tools/**`, `requirements.txt`, or `setup.py`
  would need to change;
- `frontend-developer` work would require `package.json`, React, Vite, Next.js,
  browser routes, API clients, `.tsx`, or `.jsx` files;
- documentation and actual skill files disagree;
- execution would require live infrastructure commands or product source
  changes.

## Slice Summary

| Slice | Owner | Purpose |
| --- | --- | --- |
| 01 | `senior_requirement_engineer` | Inspect existing skill and agent landscape |
| 02 | `senior_python_automation_developer` | Create missing required skills |
| 03 | `senior_system_architect` | Update retained skills |
| 04 | `senior_workflow_architect` | Remove unrelated skills after reference checks |
| 05 | `senior_documentation_engineer` | Update root `AGENTS.md` |
| 06 | `senior_documentation_engineer` | Update workflow, README, workplan, and Codex docs |
| 07 | `senior_tester` | Execute quality gate |
| 08 | `senior_workflow_architect` | Write final report |
