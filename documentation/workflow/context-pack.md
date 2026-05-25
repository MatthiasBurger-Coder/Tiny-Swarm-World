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
- Release status: `LIVE_SMOKE_PASSED_WITH_HOST_FORWARDING_GAP`

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
| `README.md` | `56E75614A23DECB2C6F8E5C2C228F5CB030A5485FFF941BA2CC4C5529E42CA54` |
| `.agents/skills/workflow-authoring/SKILL.md` | `087658240296E3B1EC74205C60A96A9A4C67A17CF653F7867E6F316BD9AFA94E` |
| `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md` | `23DE7D9AAC9D2694EAE26FAC2765D65F369C101AC348DAC24D5F3BBE9E2D3BA4` |
| `.agents/skills/agent-swarm-coordination-specialist/SKILL.md` | `5C5269735D277E74A1ACAD8D89479E239247102F9B1F95BD6A1CFA10C157F14E` |
| `.agents/skills/execution-profile-router/SKILL.md` | `B554FFD4C3C8DE9B313B55D8A9C99DEDA8C3BF3910F559105000E338680263E9` |
| `.agents/orchestrator/routing-rules.md` | `C11B3DF9E77717BAD7CAACB464B74DB4566B00C7794CEA53E2DBE39A8065E71A` |
| `documentation/process/workflow-create.md` | `DAE7115594172E159C051C3ECE15C0B535F1570EFBB28FC67440AEF0BBADC9C9` |
| `documentation/process/branch-governance.md` | `2D75AFACED2C8C68FC8071A6B1C9782D6B3A931264562F2F43FDF05F0CED24F5` |
| `documentation/epics/system-unification.md` | `0883AE0E1ED9AF160E4467B30256A54688BCC626F924C155C1E7C4DA3E038183` |
| `documentation/epics/autonomous-runnable-setup.md` | `551DBD491BD2774DE74F0E8023E5AF2426F73A2C8DD3AF0DBD5B0D14F395ACA9` |
| `documentation/epics/service-access-dashboard-vaultwarden.md` | `E83911993B7B8FFD65A2D87E45B287E6D05ABBBBCB1DBC5172FBD38A7BD3B714` |
| `documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc` | `AE8360BBD3E4145120CDA8DBE7147FA2A1D7487EE9C0E4B0292FE71BD367382D` |
| `documentation/arc42/05_building_blocks.adoc` | `B7DA30B3CCBCE743BFBCF8F0B460E8C0755B41523834D5B953CA0C6A1FE29CC0` |
| `documentation/arc42/07_deployment_view.adoc` | `11AF0B7C3C5707D45718F0A0D2000D59D0BF66DBBDD45A885259148616150243` |
| `documentation/arc42/09_architecture_decisions.adoc` | `15E635E67AC67232E12FF86DD89B6142B046624F4F7A65DE2CDC7323963DE4C4` |
| `documentation/arc42/10_quality_requirements.adoc` | `472ED1C7C09E9E3C84C88146E3A1BA0F521F70BEFAC665A9A9C12CA934F25555` |
| `documentation/arc42/11_risks_and_debt.adoc` | `4C9F4638689295B4C0A78101D7D1FD2C5B95E9C1D6834938CE7BDC0369B2F0EE` |
| `documentation/architecture/adr-autonomous-setup-safety.adoc` | `0B356E6C6890E4F9011D8EA20A451178A52FDDE9E386F6EC3B3FB1E0AB6BB9AF` |
| `documentation/deployment/system.adoc` | `5EE8781DC8CE1AAF3319D82D56ADD01088F7690B9ED6E1F0673AB8F8F9545CB9` |
| `documentation/user_guide/installation.adoc` | `8BE2FEF5184D881D7760568AEDF075848D43D96736F62B8E324D25265F8C110A` |
| `documentation/user_guide/usage.adoc` | `0CE90424661F174FA7AB57294318C016A0AE81BAE95732588BDC75AB4330DBE3` |
| `documentation/user_guide/troubleshooting.adoc` | `FA753A257A8EB18A5065E356580125FA229788F81B86869A86EEC94FC4E55278` |
| `documentation/system/live-operation-surfaces.adoc` | `40324CAC8973E444EF31A60E604CC965F3EFAD521E42D17E97B6FFDCF46B4E8A` |
| `infra/compose/README.md` | `82537B6B32BD4CDC6FA8E4F948BD7B8F1554F3E13ACC9AA943B56664E2ABF33F` |
| `infra/config/compose/service-access/docker-compose.yml` | `851D189D3AC55487A80FDC923BED6F5B31118F9463048E4E7DCDCAB0B94CE5F6` |
| `infra/compose/service-access/dashboard/Dockerfile` | `EDDF37ADD4DBB61F317920E55DD221A07348DAD7FAD29E8445BEBA7A4871A9B9` |
| `infra/compose/service-access/dashboard/index.html` | `7CA4B98A06E5F51CD31DD9D18166EE7B2968DDAA692F030F9537412ED38810C9` |
| `infra/compose/service-access/nginx/Dockerfile` | `FBFC1750D9179E4F7EF83116221EDACF129823CF55D12ADF36FA559F007B657B` |
| `infra/compose/service-access/nginx/default.conf` | `813726048E7D562A69EE9EA7CE1BD00B2EDA679AA7D54119B802D70252A22A28` |
| `src/tiny_swarm_world/domain/deployment/service_stack_contract.py` | `E9774248959404F3F21184CDD806E68B370D76022DDDCB0379C799F1FC754471` |
| `src/tiny_swarm_world/domain/deployment/__init__.py` | `55CEF5099776F2AC1910F01FE3275754EFF419E946241947F58B3CFF62FDA2F9` |
| `src/tiny_swarm_world/domain/preflight/setup_manifest.py` | `601D231D307C6A5D9FA43A0C75CAE8B192B65F6B68EDB53FCB2574C7BBEEF545` |
| `src/tiny_swarm_world/domain/preflight/preflight_configuration.py` | `0CB902DDDA476BC10DC1D16DAC2B922A914E5936FB6793E007FAB3BA7DC052C3` |
| `src/tiny_swarm_world/application/services/deployment/service_stack_plan.py` | `EF476E2416A2B002DC940FFAD54C2C1FF20601395F24014B3567DFF87EEF5015` |
| `src/tiny_swarm_world/application/services/deployment/ensure_service_stack.py` | `CEEB7A9C9692C4D3A82BEE577DEAE9CDD6AADA1A16BEEA60147BD9F09D0B1D7F` |
| `src/tiny_swarm_world/application/services/deployment/verify_swarm_service_readiness.py` | `6DE065BA3999B7F35B0D5D36D5FC8A4EFC6647C90E41B1507BAB407DFAB1AE7B` |
| `src/tiny_swarm_world/infrastructure/composition.py` | `0A56295B57E43487A6F4644BAC8291A3187ADA2B8D2F60C45109DE38ED618ABD` |
| `tests/domain/deployment/test_service_stack_contract.py` | `E81BEF67074EB37A3524581A4401511C02BB67F4812C1F91E70BABC7BF920961` |
| `tests/domain/preflight/test_preflight_result.py` | `84AC123A4B547DD1BBC9A3065351D592CDBA24FDC58C8709BC6195D107179E47` |
| `tests/application/services/deployment/test_service_stack_plan.py` | `133D18E02EBCEFDCCEB327C7A758048DC40D2B944451D6ECFA43768813549503` |
| `tests/application/services/deployment/test_ensure_service_stack.py` | `709D883551E66FBDB73D31F8B8219C0D22C7EB14D2C33E835478A69E5A37C91E` |
| `tests/application/services/deployment/test_verify_swarm_service_readiness.py` | `EF65C7A7637CE81F56D5E86018578AFB9F29D00F86D7C15C56EBB11A9A5B80FA` |
| `tests/infrastructure/test_composition.py` | `FB4FA7FD2969D378FA7C7CEF7A1E0DF3D8D77AEA95D34E9B460CA8866EC80C13` |
| `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py` | `BD2961CCFA530A9CE33D570DA497668ADF355523BD92C8B5FAC18F517D3FC216` |
| `tests/architecture/test_legacy_surface_documentation.py` | `2054D9102D7673D0D1059F50552E1B39A2B766C2AEEA25EF71FC96987B95B6F1` |
| `documentation/workflow/reports/02-routing-security-quality-notes.md` | `E1AFBA162A0849ED30A6916536DB79239270796F2EB9A003645D2C2F1127BF96` |
| `documentation/workflow/workflow.md` | `F0DC3746629B1836855EE796D859E8C61ADFFBAADF19FD3036B9A94E793CF40F` |
| `documentation/workflow/execution-report.md` | `6F988471859F9D053A73DA07339C2A6EA66135D4BAE88C78BDBC09AF5E8467C3` |

## Stale When

- Any recorded governing file hash changes.
- `documentation/workflow/**` changes outside this workflow branch.
- `documentation/epics/**`, `documentation/architecture/**`, or
  `documentation/arc42/**` changes in a way that affects service access,
  routing, credential handling, setup, deployment, or quality gates.
- Branch context changes.
- A conflict is detected.
- A slice requires live infrastructure behavior not described in the workflow.
