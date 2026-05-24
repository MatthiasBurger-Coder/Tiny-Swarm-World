# Workflow Context Pack: Autonomous Runnable Setup

## Purpose

This context pack is the navigation aid for the active workflow:

```text
Autonomous Runnable Setup
```

It does not replace root `AGENTS.md`, root `QUALITY.md`, arc42 documentation,
architecture decision files, routing rules, skills, roles, or the active
workflow file.

## Active Workflow

- Workflow file: `documentation/workflow/workflow.md`
- Workflow version: `autonomous-runnable-setup-v1.0.0`
- Branch: `codex/workflow-autonomous-setup-20260524`
- Date created: `2026-05-24`
- Process strand: `autonomous-runnable-setup`
- Execution profile: `FULL_PATH`
- Release status: `WORKFLOW_COMPLETED`

## Execution Status

| Slice | Status |
| --- | --- |
| 01 | `COMPLETED` |
| 02 | `COMPLETED` |
| 03 | `COMPLETED` |
| 04 | `COMPLETED` |
| 05 | `COMPLETED` |
| 06 | `COMPLETED` |
| 07 | `COMPLETED` |
| 08 | `COMPLETED` |
| 09 | `COMPLETED` |
| 10 | `COMPLETED` |
| 11 | `COMPLETED` |

## Governing Files Checked

| File | SHA-256 |
| --- | --- |
| `AGENTS.md` | `F0FA2387DFA023B968A0F474971BACDA12EBF05FEA4A03B5D6D098F1701D4601` |
| `QUALITY.md` | `D327E4060FF1729F17FFDE844B1A2D6208FE203E149AE9D1AF185BEF0AED2155` |
| `README.md` | `87DE7E5F2F1C1A2B0D2B7E9EFB83085AE1E4C740B71C83656AB53F841F8031F0` |
| `.importlinter` | `4C5C879DDC20BF7CCB8ADCA2B907538264F9C3CF9C1C54E3076E7C008F1A62B4` |
| `documentation/epics/system-unification.md` | `6A488D85AAB23B65B26CE927985D636FB5457977319EFA1F6A6DBF3C1E4F40D3` |
| `documentation/epics/autonomous-runnable-setup.md` | `42B9A7C7FE4BF53B3CFFCFCA22229AD923B3F20BBA1CE88F4049D9087AABFB36` |
| `documentation/architecture/adr-autonomous-setup-safety.adoc` | `09F2F6C23346A59596965E9EA8605020FFE8A7818E178A5648206ABF6E82DCC2` |
| `documentation/arc42/05_building_blocks.adoc` | `60DDB9811AB3CD2D404C16592AFEBE62872223EE7CD00EAC9586A6A41490B201` |
| `documentation/arc42/06_runtime_view.adoc` | `4EEFE086470FC4ABC7235F1570E0AA528889BA5408BC6839FF8AFC173B2C5A3E` |
| `documentation/arc42/07_deployment_view.adoc` | `2F4046D7D1BC1F4189C3B71B02A8DB4342945E27C149AD8F828C7F2B7A859CCC` |
| `documentation/arc42/09_architecture_decisions.adoc` | `76C58BBAF9FD957ECD2F46B69C4BC7FEE02DED6A20E26C8961A97604CE2D548F` |
| `documentation/arc42/10_quality_requirements.adoc` | `E80E6187EACB4485BBB446C3070485606657BB4E127676A589E6A4B39401E072` |
| `documentation/arc42/11_risks_and_debt.adoc` | `6BA24B09A4F6F9448E36D475E59F4DEE6C1D3CF23DDF46B45872E7FDAB28F901` |
| `documentation/arc42/12_glossary.adoc` | `D272FF4BE21CF73E48F700A563A4FA05F6163F1F99D12A00C2A3BD90D5F4B216` |
| `documentation/system/live-operation-surfaces.adoc` | `C1400625A1D66F184B35C156763784614563E90E8A806AC5FF4F673416854CCD` |
| `documentation/user_guide/installation.adoc` | `A82BB7E82920E8310E0C5822A6CABAAD5D7E4479719606B5D3E573381B8C00AE` |
| `documentation/user_guide/usage.adoc` | `D781C867F82BA21AB7BD9FA1CE1B765C151127F830FF6C404B3BE4DDB6A111C8` |
| `documentation/user_guide/troubleshooting.adoc` | `0A937265E331B248DD4E5222166168431B9DE4623EB6FFE197EEB1EC42A3CFE7` |
| `documentation/deployment/system.adoc` | `8FFDF7B9D3ADC1D9F6BB8BC10665469BA1C90A9711BAABC48C0C7B0E855382C4` |
| `documentation/workflow/reports/11-documentation-sync-quality-live-smoke.md` | `633600D2DE4DA8838EB12BE0E52234586496E5019672F3F59217444AA4B90752` |
| `.agents/skills/workflow-authoring/SKILL.md` | `087658240296E3B1EC74205C60A96A9A4C67A17CF653F7867E6F316BD9AFA94E` |
| `.agents/skills/setup-bootstrap-expert/SKILL.md` | `37476A7B553A5E63B7E2B1F074D7DD697B2BD138A9EA745E6AC83A81C57CB5AC` |
| `.agents/skills/swarm-orchestration/SKILL.md` | `FAD1651BB25B5DBD3BA5C98174AEA0B24FF41B42B1BBF78926140304BE44AF95` |

This context pack is stale when any listed hash changes, when
`documentation/workflow/**` changes outside workflow execution, when
architecture documentation changes, when setup requirement files change, or
when branch context changes.

## Affected Areas

- Installer-specific EPIC and workflow reports.
- Platform, Artifacts, Deployment, Shared, and Console/status UI boundaries.
- CLI setup workflow declaration and composition wiring.
- Preflight, setup manifest, live consent, and resource gates.
- Command-backed verification, observed inventory, and evidence redaction.
- Portainer, Nexus, registry, compose, and service stack contracts.
- README, installation docs, deployment docs, system docs, arc42, and
  live-operation surface catalog.
- Tests and quality gates.

## Forbidden Areas

- `src/main/java/**`
- `pom.xml`
- external static-analysis CI configuration
- generated caches
- local virtual environments
- logs
- IDE state
- `.tiny-swarm-world/**`
- `.env`
- `.env.local`
- live infrastructure execution during default verification

## Required Roles

- `senior_workflow_architect`
- `senior_requirement_engineer`
- `senior_system_architect`
- `senior_python_automation_developer`
- `senior_react_frontend` as React/browser scope guard
- `senior_tester`

## Conditional Roles

- `senior_devops`
- `senior_documentation_engineer`
- `senior_security_sandbox_engineer`
- `console-status-ui-developer`
- `setup-bootstrap-expert`
- `linux-host-preparation`
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

- active branch is not `codex/workflow-autonomous-setup-20260524`;
- local branch ref is missing;
- unrelated or unclear changes exist;
- workflow or context-pack branch names are stale;
- runnable setup criteria cannot be made testable;
- live infrastructure execution would be required without explicit approval;
- host package installation or non-interactive consent lacks ADR approval;
- manual-only verification would be used for an autonomous live step;
- secrets, tokens, raw command payloads, stdout, or stderr would be persisted;
- application imports infrastructure;
- React/browser, Spring Boot, Kubernetes-first, Java example, or unrelated
  analytics scope starts driving Python automation architecture.

## Slice Summary

| Slice | Owner | Purpose |
| --- | --- | --- |
| 01 | `senior_requirement_engineer` | Installer requirement baseline |
| 02 | `senior_system_architect` | Setup safety ADR and arc42 alignment |
| 03 | `senior_python_automation_developer` | Setup preflight and manifest contract |
| 04 | `senior_python_automation_developer` | Inventory and evidence foundation |
| 05 | `senior_python_automation_developer` | Command-backed platform verification |
| 06 | `senior_devops` | Portainer deployment contract |
| 07 | `senior_python_automation_developer` | Nexus and artifact registry contract |
| 08 | `senior_python_automation_developer` | Service stack deployment and verification |
| 09 | `senior_workflow_architect` | Autonomous setup orchestrator and CLI contract |
| 10 | `senior_python_automation_developer` | Console status and recovery UX |
| 11 | `senior_documentation_engineer` | Documentation sync, quality gate, and optional live smoke handoff |
