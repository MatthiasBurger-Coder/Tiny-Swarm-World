# Workflow Context Pack: Service Access Dashboard And Vaultwarden

This context pack is a workflow-local navigation aid. It does not replace
`AGENTS.md`, `QUALITY.md`, ADRs, arc42, routing rules, active workflow files,
or skill files.

## Workflow

- Name: Service Access Dashboard And Vaultwarden
- Version: `service-access-vaultwarden-dashboard-v1.0.0`
- Branch: `feature/workflow-access-vaultwarden-dashboard-20260525`
- Created: `2026-05-25`
- Process strand: `service-access-vaultwarden-dashboard`
- Execution profile: `FULL_PATH`
- Release status: `WORKFLOW_CREATED`

## Affected Areas

- Deployment service stack contracts
- Portainer-managed post-bootstrap stack planning
- Compose stack definitions under `infra/config/compose`
- Optional runtime/image assets under `infra/compose`
- Setup preflight ports and credential-source requirements
- NGINX-first HTTP routing and port allocation
- Vaultwarden credential-source handling
- Service-access dashboard content and reachability evidence
- Documentation, arc42, ADRs, and workflow handoff

## Forbidden Areas

- Java, Maven, Spring Boot
- Kubernetes-first deployment
- React, TypeScript, Vite, TSX, JSX, or browser frontend project setup
- Live Multipass, Docker Swarm, compose, netplan, socat, Portainer,
  Vaultwarden, NGINX, Traefik, or bootstrap execution during default gates
- Committed passwords, tokens, Vaultwarden admin tokens, host IPs, local paths,
  raw command output, or credential-bearing URLs
- Direct promotion of legacy scripts as canonical deployment entry points

## Required Roles

- Senior Workflow Architect
- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior DevOps Engineer
- Senior Tester
- Senior Documentation Engineer

## Conditional Roles

- Senior React Frontend Developer: N/A impact guard unless a later approved
  workflow verifies a frontend module.
- Senior Security Sandbox Engineer: required for Vaultwarden secret handling,
  credential display, redaction, and local evidence safety.
- Senior UX Designer: optional if dashboard information architecture becomes
  complex.

## Quality Commands

Workflow creation:

```bash
git diff --check
```

Targeted implementation checks:

```bash
PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract
PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result
PYTHONPATH=src python3 -m unittest tests.application.services.deployment
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

## Governing File Hashes

| Path | SHA-256 |
|---|---|
| `AGENTS.md` | `E09BCBE872EDF6FC64791AEFEB8CEB539067BE1A1A4D1E091C76354FC10FB4D8` |
| `QUALITY.md` | `458E5F4D8FBDEDEA1C413E1FF135EC91392A4BB5A5AEA20300DCAC8E209414B6` |
| `.agents/skills/workflow-authoring/SKILL.md` | `087658240296E3B1EC74205C60A96A9A4C67A17CF653F7867E6F316BD9AFA94E` |
| `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md` | `23DE7D9AAC9D2694EAE26FAC2765D65F369C101AC348DAC24D5F3BBE9E2D3BA4` |
| `.agents/skills/agent-swarm-coordination-specialist/SKILL.md` | `5C5269735D277E74A1ACAD8D89479E239247102F9B1F95BD6A1CFA10C157F14E` |
| `.agents/skills/execution-profile-router/SKILL.md` | `B554FFD4C3C8DE9B313B55D8A9C99DEDA8C3BF3910F559105000E338680263E9` |
| `.agents/orchestrator/routing-rules.md` | `C11B3DF9E77717BAD7CAACB464B74DB4566B00C7794CEA53E2DBE39A8065E71A` |
| `documentation/process/workflow-create.md` | `DAE7115594172E159C051C3ECE15C0B535F1570EFBB28FC67440AEF0BBADC9C9` |
| `documentation/process/branch-governance.md` | `2D75AFACED2C8C68FC8071A6B1C9782D6B3A931264562F2F43FDF05F0CED24F5` |
| `documentation/epics/system-unification.md` | `6A488D85AAB23B65B26CE927985D636FB5457977319EFA1F6A6DBF3C1E4F40D3` |
| `documentation/epics/autonomous-runnable-setup.md` | `0D9547C6048834EE655B02B29C526CF7DAC56A3ABC5D60468D01A3378CFB4A0C` |
| `documentation/arc42/05_building_blocks.adoc` | `A3CFFAF5BD4E40F7688D72B41A3B4B81FF210393D5C1A69E8CB6AE1B8F9DEAD7` |
| `documentation/arc42/07_deployment_view.adoc` | `2F4046D7D1BC1F4189C3B71B02A8DB4342945E27C149AD8F828C7F2B7A859CCC` |
| `documentation/arc42/09_architecture_decisions.adoc` | `76C58BBAF9FD957ECD2F46B69C4BC7FEE02DED6A20E26C8961A97604CE2D548F` |
| `documentation/arc42/10_quality_requirements.adoc` | `E80E6187EACB4485BBB446C3070485606657BB4E127676A589E6A4B39401E072` |
| `documentation/arc42/11_risks_and_debt.adoc` | `54E11723EC25E0D145C482BE1C9F82603D32D42FBE26410A075410E931D03349` |
| `documentation/architecture/adr-autonomous-setup-safety.adoc` | `0B356E6C6890E4F9011D8EA20A451178A52FDDE9E386F6EC3B3FB1E0AB6BB9AF` |

## Stale When

- Any recorded governing file hash changes.
- `documentation/workflow/**` changes outside this workflow branch.
- `documentation/epics/**`, `documentation/architecture/**`, or
  `documentation/arc42/**` changes in a way that affects service access,
  routing, credential handling, setup, deployment, or quality gates.
- Branch context changes.
- A conflict is detected.
- A slice requires live infrastructure behavior not described in the workflow.
