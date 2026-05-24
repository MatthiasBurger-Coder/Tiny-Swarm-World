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
| `README.md` | `9165A11D60B16E5B73970248360558CAC8A817926623A9E90637DE047713DD9D` |
| `.importlinter` | `4C5C879DDC20BF7CCB8ADCA2B907538264F9C3CF9C1C54E3076E7C008F1A62B4` |
| `documentation/epics/system-unification.md` | `6A488D85AAB23B65B26CE927985D636FB5457977319EFA1F6A6DBF3C1E4F40D3` |
| `documentation/epics/autonomous-runnable-setup.md` | `032EE1C19307457F72410BEF6A7B00C6BBC07D7F73F802393D7EA4DFB5E2C312` |
| `documentation/architecture/adr-autonomous-setup-safety.adoc` | `489949926E416D15F372BFE38040709876CFDBA3C3A942178BD0202716622BAD` |
| `documentation/arc42/05_building_blocks.adoc` | `60DDB9811AB3CD2D404C16592AFEBE62872223EE7CD00EAC9586A6A41490B201` |
| `documentation/arc42/06_runtime_view.adoc` | `4EEFE086470FC4ABC7235F1570E0AA528889BA5408BC6839FF8AFC173B2C5A3E` |
| `documentation/arc42/07_deployment_view.adoc` | `2F4046D7D1BC1F4189C3B71B02A8DB4342945E27C149AD8F828C7F2B7A859CCC` |
| `documentation/arc42/09_architecture_decisions.adoc` | `50D16962A712E10E3FA48BCF35DCBEB9D1DF93FA7764AF2C333DC0A9DE10082E` |
| `documentation/arc42/10_quality_requirements.adoc` | `E80E6187EACB4485BBB446C3070485606657BB4E127676A589E6A4B39401E072` |
| `documentation/arc42/11_risks_and_debt.adoc` | `6BA24B09A4F6F9448E36D475E59F4DEE6C1D3CF23DDF46B45872E7FDAB28F901` |
| `documentation/system/live-operation-surfaces.adoc` | `24E88A98ECF7F21B08599242F1EB5D7606F77C9EB487186FBA6FCB692BF2412E` |
| `documentation/user_guide/installation.adoc` | `C2C6902FBF67D03375F64D078EB2D00516F349EAF9330CD4B628A076A608D3FE` |
| `documentation/user_guide/usage.adoc` | `8A7710E805C55A30DA96581F5D13032D54A2677D67FB61286E3B43200E5F8C7D` |
| `documentation/user_guide/troubleshooting.adoc` | `0454C2BFECAA74F65F3E54B0DB4FBF348109360FE4B5A69FD6877C2948218A63` |
| `documentation/deployment/system.adoc` | `3630F668F4F5A530950AF3834546B7C72D8EA33249EA54DF86ECF1C5EEE3068A` |
| `documentation/workflow/reports/11-documentation-sync-quality-live-smoke.md` | `FA103DE1C6DB6B3CDA71D2F1059DF1053D4901940B18EDBF6E2952C85C9A870E` |
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
