# Workflow Context Pack: System Unification

## Purpose

This context pack is the navigation aid for the active workflow:

```text
Unify Tiny Swarm World System Boundaries
```

It does not replace root `AGENTS.md`, root `QUALITY.md`, arc42 documentation,
architecture decision files, routing rules, skills, roles, or the active
workflow file.

## Active Workflow

- Workflow file: `documentation/workflow/workflow.md`
- Workflow version: `system-unification-v1.0.0`
- Branch: `codex/workflow-system-unification-20260524`
- Date created: `2026-05-24`
- Process strand: `system-unification`
- Execution profile: `FULL_PATH`
- Release status: `WORKFLOW_EXECUTION_IN_PROGRESS`

## Execution Status

| Slice | Status |
| --- | --- |
| 01 | `COMPLETED_PUSHED` |
| 02 | `COMPLETED_PUSHED` |
| 03 | `COMPLETED_PUSHED` |
| 04 | `COMPLETED_PUSHED` |
| 05 | `PENDING` |
| 06 | `PENDING` |
| 07 | `PENDING` |
| 08 | `PENDING` |
| 09 | `PENDING` |

## Governing Files Checked

| File | SHA-256 |
| --- | --- |
| `AGENTS.md` | `F0FA2387DFA023B968A0F474971BACDA12EBF05FEA4A03B5D6D098F1701D4601` |
| `QUALITY.md` | `D327E4060FF1729F17FFDE844B1A2D6208FE203E149AE9D1AF185BEF0AED2155` |
| `README.md` | `31C6AA7F2907D2C773C4ADD14F31235AB620F3A11B3D9DB913004A69D8650A24` |
| `.importlinter` | `4C5C879DDC20BF7CCB8ADCA2B907538264F9C3CF9C1C54E3076E7C008F1A62B4` |
| `.agents/orchestrator/routing-rules.md` | `4EE4C2C198471962EB48F66E53A9C4B4F15C40343420C200E7081103820757AB` |
| `documentation/process/workflow-create.md` | `DAE7115594172E159C051C3ECE15C0B535F1570EFBB28FC67440AEF0BBADC9C9` |
| `documentation/process/workflow-execute.md` | `E34ED8E85753002D62D11EDE7DF44C2FC8B84F2D7CD88694633EC0232F4C7FED` |
| `documentation/architecture/responsibility-separation-analysis.md` | `38B08D772951F87B168F9432A8AADBD8B3705D5FEDD2CC8511C8AD4A36EEC078` |
| `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc` | `7DC5D3B510CDA2BFD4ABA0AB57C963FE950CF6D0ACA07D6EC70B8287D78C5526` |
| `documentation/architecture/migration-plan.md` | `DBF5618E62B96935B669CF880B3BE84710C8A29BA7CE9A4F4AAF08CCF5A21E2F` |
| `documentation/arc42/05_building_blocks.adoc` | `7C75DD678D9153979979EF7F31759519FD3779F99B106B9EA73758D722140DDD` |
| `documentation/arc42/06_runtime_view.adoc` | `DC88271ED400A0FC4D0C40EB94D75B90BC4B060FDE264529D947D3FB6A88FCE2` |
| `documentation/arc42/08_concepts.adoc` | `2BC78C86901D5CE98F210AC6F6DA0D3FBDA3F7A59723231C040A0C9919584F51` |
| `documentation/arc42/10_quality_requirements.adoc` | `DDE1208E83235F36DB22700039B008C84AAEFCA28DFA53E57CF0E936C05BAB9B` |
| `documentation/arc42/11_risks_and_debt.adoc` | `F445736A8C94D6CCC2870C6B1A981AF6EBF7BFE6FAB42242BF4EC6320DD06433` |

This context pack is stale when any listed hash changes, when
`documentation/workflow/**` changes outside workflow execution, when
`documentation/epics/**` is introduced or changed, when architecture
documentation changes, or when branch context changes.

## Affected Areas

- System-unification EPIC and workflow reports.
- Platform, Artifacts, Deployment, Shared, and Console/status UI boundaries.
- CLI workflow declarations and composition wiring.
- Verify-after-apply contracts and verification evidence.
- Legacy live-operation script classification.
- README, architecture docs, arc42, deployment docs, system docs, user guide.
- Tests and quality gates.

## Forbidden Areas

- `src/main/java/**`
- `pom.xml`
- generated caches
- local virtual environments
- logs
- IDE state
- live infrastructure execution

## Required Roles

- `senior_workflow_architect`
- `senior_requirement_engineer`
- `senior_system_architect`
- `senior_python_automation_developer`
- `senior_react_frontend` as React/browser scope guard
- `senior_tester`
- `senior_documentation_engineer`

## Conditional Roles

- `senior_devops`
- `senior_security_sandbox_engineer`
- `console-status-ui-developer`
- `resilience-engineering`
- `adr-steward`
- `git_commit_reviewer`
- `git_commit_operator`

## Quality Commands

Minimum workflow-creation command:

```bash
git diff --check
```

Preferred full gate:

```bash
python3 tools/quality_gate.py quality
```

Targeted commands are defined per slice in `workflow.md`.

## Stop Rules

Stop when:

- active branch is not `codex/workflow-system-unification-20260524`;
- local branch ref is missing;
- unrelated or unclear changes exist;
- workflow or context-pack branch names are stale;
- live infrastructure execution would be required;
- EPIC baseline cannot align with architecture docs;
- ADR convention blocks architecture decision changes;
- `QUALITY.md` commands cannot be verified or documented;
- application imports infrastructure;
- React/browser, Spring Boot, Kubernetes-first, Java example, or unrelated
  analytics scope starts driving Python automation architecture.

## Slice Summary

| Slice | Owner | Purpose |
| --- | --- | --- |
| 01 | `senior_requirement_engineer` | EPIC baseline and completeness criteria |
| 02 | `senior_system_architect` | ADR and arc42 alignment |
| 03 | `senior_tester` | Responsibility boundary quality coverage |
| 04 | `senior_python_automation_developer` | Command catalog, inventory, and evidence foundation |
| 05 | `senior_python_automation_developer` | Platform verify-after-apply contracts |
| 06 | `senior_python_automation_developer` | Artifact and deployment workflow contracts |
| 07 | `senior_python_automation_developer` | Console status UI consistency |
| 08 | `senior_devops` | Legacy live-surface quarantine |
| 09 | `senior_documentation_engineer` | Documentation sync, quality gate, execution report |
