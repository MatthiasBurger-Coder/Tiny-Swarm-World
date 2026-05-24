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
- Release status: `SLICE_07_COMPLETED`

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
| 08 | `PLANNED` |
| 09 | `PLANNED` |
| 10 | `PLANNED` |
| 11 | `PLANNED` |

## Governing Files Checked

| File | SHA-256 |
| --- | --- |
| `AGENTS.md` | `F0FA2387DFA023B968A0F474971BACDA12EBF05FEA4A03B5D6D098F1701D4601` |
| `QUALITY.md` | `D327E4060FF1729F17FFDE844B1A2D6208FE203E149AE9D1AF185BEF0AED2155` |
| `README.md` | `C0E731EF69795EC8DFFB7E19A3C540F9F9EBC96996FB0974CFE5756DC6B0A3AF` |
| `.importlinter` | `4C5C879DDC20BF7CCB8ADCA2B907538264F9C3CF9C1C54E3076E7C008F1A62B4` |
| `documentation/epics/system-unification.md` | `7F8B87A904676CC107FEF217987E6A3C419CD64EA533A29FD1D444BEEBD9721D` |
| `documentation/epics/autonomous-runnable-setup.md` | `6B464ADF0672012D5AD14CC5C27FC654E32D50DC5CB12D1C2756381B2E0E9FEB` |
| `documentation/architecture/adr-autonomous-setup-safety.adoc` | `0CA708C87E68348254C91FB662B1A78D8577859BEBED2C92B420785AF74B6DE0` |
| `documentation/arc42/05_building_blocks.adoc` | `B7AB1FC45643660CDCAEE86B1D01E339232C5768936047EB02D199F50D43F46C` |
| `documentation/arc42/06_runtime_view.adoc` | `02DA2C5C0032F6CCB798CE4B0B02F12AB3378A7C96139BA9E3CDE17B9BCFBB50` |
| `documentation/arc42/07_deployment_view.adoc` | `C6B7DF4B4216D26170F9E62D2681B2BBC1D64F8A1A2249A9E5049971BF09BAD8` |
| `documentation/arc42/09_architecture_decisions.adoc` | `8B9BE723ACF350193F8E6B8FD70412776AB3EA7888F43DFEDA4A4F0249871EF9` |
| `documentation/arc42/10_quality_requirements.adoc` | `E80E6187EACB4485BBB446C3070485606657BB4E127676A589E6A4B39401E072` |
| `documentation/arc42/11_risks_and_debt.adoc` | `815788E53B3E872304FAE6EBECC17F2DF8BF03A3D27C0962675F4ECC68C2AB6D` |
| `documentation/system/live-operation-surfaces.adoc` | `216CFDB00183FC64BC7E35F0FDFEB59FD1C75DAAC9F636317D46EB59FB47C791` |
| `documentation/user_guide/installation.adoc` | `8F26FD0C8C217886784DC2B4A32EA2B89BFE88DE42A814A45A70486E338FD1D4` |
| `documentation/deployment/system.adoc` | `67AC2F7C80397876BE1610FF76318C792A9232F0E8C847077CBEB1509D4E3757` |
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
