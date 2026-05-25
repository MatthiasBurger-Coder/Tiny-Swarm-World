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
- Default full setup service-access management profile
- Setup-managed runtime/image assets under `infra/compose`
- Setup preflight ports and credential-source requirements
- NGINX-first HTTP routing and port allocation
- Vaultwarden credential-source handling
- Service-access dashboard content and reachability evidence
- Idempotent setup preflight for already-running expected services
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
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
PYTHONPATH=src python3 -m unittest tests.domain.artifacts.test_container_image_contract
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_multipass_container_image_publisher
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
| `README.md` | `3056973D06CA8E073FE0B4DE1C6947AD7FDFC759A178DFF84224D1A0C50F159C` |
| `.agents/skills/workflow-authoring/SKILL.md` | `087658240296E3B1EC74205C60A96A9A4C67A17CF653F7867E6F316BD9AFA94E` |
| `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md` | `23DE7D9AAC9D2694EAE26FAC2765D65F369C101AC348DAC24D5F3BBE9E2D3BA4` |
| `.agents/skills/agent-swarm-coordination-specialist/SKILL.md` | `5C5269735D277E74A1ACAD8D89479E239247102F9B1F95BD6A1CFA10C157F14E` |
| `.agents/skills/execution-profile-router/SKILL.md` | `B554FFD4C3C8DE9B313B55D8A9C99DEDA8C3BF3910F559105000E338680263E9` |
| `.agents/orchestrator/routing-rules.md` | `C11B3DF9E77717BAD7CAACB464B74DB4566B00C7794CEA53E2DBE39A8065E71A` |
| `documentation/process/workflow-create.md` | `DAE7115594172E159C051C3ECE15C0B535F1570EFBB28FC67440AEF0BBADC9C9` |
| `documentation/process/branch-governance.md` | `2D75AFACED2C8C68FC8071A6B1C9782D6B3A931264562F2F43FDF05F0CED24F5` |
| `documentation/epics/system-unification.md` | `0883AE0E1ED9AF160E4467B30256A54688BCC626F924C155C1E7C4DA3E038183` |
| `documentation/epics/autonomous-runnable-setup.md` | `07A73989E4E4246C141636D7D7FF4103E51BB84BA76D1A5B381B3A83ADF62626` |
| `documentation/epics/service-access-dashboard-vaultwarden.md` | `E83911993B7B8FFD65A2D87E45B287E6D05ABBBBCB1DBC5172FBD38A7BD3B714` |
| `documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc` | `E45990C6CFD366619A748C862644D5A2F4E6FFD88E8EE6B9B36D58A9A5327415` |
| `documentation/arc42/05_building_blocks.adoc` | `7BD7159961EA5C027020031DE219CDCC6C6AFE738BA2E0F4BB3B1DDDBDCB852D` |
| `documentation/arc42/07_deployment_view.adoc` | `9E4A931D94F8C8FC5BEC798BFB3277A49237E7D4BD96FE36D0572B4F8EA2C35E` |
| `documentation/arc42/09_architecture_decisions.adoc` | `AC69160A2EE3773B48857481EE9C67199F82AC9512B6751DBFA7BCEADFC80BE4` |
| `documentation/arc42/10_quality_requirements.adoc` | `069115EB50468E1264566BEE78E2E0AEFD9A7F008A82A6FF87F887BED9023CCB` |
| `documentation/arc42/11_risks_and_debt.adoc` | `6595B4F8C033A68A5F8BB3D22B1E79C75D123E315BE46B92F098D2499B643256` |
| `documentation/architecture/adr-autonomous-setup-safety.adoc` | `0B356E6C6890E4F9011D8EA20A451178A52FDDE9E386F6EC3B3FB1E0AB6BB9AF` |
| `documentation/deployment/system.adoc` | `FD942F33C1D5B0CF23498A63B09980335EAE5461A663A55CD460285C16CF0FC6` |
| `documentation/user_guide/installation.adoc` | `21B48B802E572265B86A7FD63E750F4563CC759DDAD8EDAEAFD49BB26F304BB8` |
| `documentation/user_guide/usage.adoc` | `77F37D72AC5E556C2F386306B77F01EFDD663B5A4659AE22163EA9633F1ACCF8` |
| `documentation/user_guide/troubleshooting.adoc` | `B75DA3AEC271D59C78F2269E949213E34237B36AE166EE8EC1D6D2DD52F3067B` |
| `documentation/system/live-operation-surfaces.adoc` | `E89987122D152D2326870665DCDEC9D46C3E13185F849DC6A7BBFB63A1DC1D36` |
| `infra/compose/README.md` | `82537B6B32BD4CDC6FA8E4F948BD7B8F1554F3E13ACC9AA943B56664E2ABF33F` |
| `infra/config/compose/service-access/docker-compose.yml` | `B9A2BF909AF680243958CE54E058EA29B3EE32BD08CAB2FABA232ED1E05C1523` |
| `infra/compose/service-access/dashboard/Dockerfile` | `EDDF37ADD4DBB61F317920E55DD221A07348DAD7FAD29E8445BEBA7A4871A9B9` |
| `infra/compose/service-access/dashboard/index.html` | `7CA4B98A06E5F51CD31DD9D18166EE7B2968DDAA692F030F9537412ED38810C9` |
| `infra/compose/service-access/nginx/Dockerfile` | `FBFC1750D9179E4F7EF83116221EDACF129823CF55D12ADF36FA559F007B657B` |
| `infra/compose/service-access/nginx/default.conf` | `813726048E7D562A69EE9EA7CE1BD00B2EDA679AA7D54119B802D70252A22A28` |
| `src/tiny_swarm_world/domain/deployment/service_stack_contract.py` | `E9774248959404F3F21184CDD806E68B370D76022DDDCB0379C799F1FC754471` |
| `src/tiny_swarm_world/domain/deployment/__init__.py` | `55CEF5099776F2AC1910F01FE3275754EFF419E946241947F58B3CFF62FDA2F9` |
| `src/tiny_swarm_world/domain/preflight/setup_manifest.py` | `230EDD192536D471C79C5E050AEBDFF61BA90FF75255D60200386541BC371C95` |
| `src/tiny_swarm_world/domain/preflight/preflight_configuration.py` | `B0E05855978875C97195019692B102738F67E7B7DA8EC61954E579CF91A1399B` |
| `src/tiny_swarm_world/application/ports/preflight/port_host_preflight_probe.py` | `F2523F7398B05458A5BDC7752C0821907A8088E79243D409ACEE5D6AD1BA1D16` |
| `src/tiny_swarm_world/application/services/platform/preflight_service.py` | `748DF314F2146338670E1CD4F1908EE69423BD9ED60F3786878874B0182CA07C` |
| `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py` | `3644D47F6C8AF233EEA80D213CF31FD57F0753109859062D3E6BF288D007107E` |
| `src/tiny_swarm_world/application/services/deployment/service_stack_plan.py` | `EF476E2416A2B002DC940FFAD54C2C1FF20601395F24014B3567DFF87EEF5015` |
| `src/tiny_swarm_world/application/services/deployment/ensure_service_stack.py` | `CEEB7A9C9692C4D3A82BEE577DEAE9CDD6AADA1A16BEEA60147BD9F09D0B1D7F` |
| `src/tiny_swarm_world/application/services/deployment/verify_swarm_service_readiness.py` | `6DE065BA3999B7F35B0D5D36D5FC8A4EFC6647C90E41B1507BAB407DFAB1AE7B` |
| `src/tiny_swarm_world/infrastructure/composition.py` | `0E3006941C57B0FEE78517BD6041A2D61D9E3949EA8E47DB816674885697CB0B` |
| `tests/domain/deployment/test_service_stack_contract.py` | `E81BEF67074EB37A3524581A4401511C02BB67F4812C1F91E70BABC7BF920961` |
| `tests/domain/preflight/test_preflight_result.py` | `651BD955A18A2639A6A66C7AF04466DCF2DBB707CC5DF837BE0C2A70D8413AAA` |
| `tests/application/services/platform/test_preflight_service.py` | `30F8975067608E262AC4692E539375D64429FEDD7742678C7C389AA7EE7BED8B` |
| `tests/infrastructure/adapters/preflight/test_host_preflight_probe.py` | `D57162D22610DA6282002307F3CBDE76793863825C732133771C6B81D70EA139` |
| `tests/application/services/deployment/test_service_stack_plan.py` | `133D18E02EBCEFDCCEB327C7A758048DC40D2B944451D6ECFA43768813549503` |
| `tests/application/services/deployment/test_ensure_service_stack.py` | `709D883551E66FBDB73D31F8B8219C0D22C7EB14D2C33E835478A69E5A37C91E` |
| `tests/application/services/deployment/test_verify_swarm_service_readiness.py` | `EF65C7A7637CE81F56D5E86018578AFB9F29D00F86D7C15C56EBB11A9A5B80FA` |
| `tests/infrastructure/test_composition.py` | `45140A9F25EBF32A72DA07711F79014DD4FB7DA10B8797BCD399B92744817DD0` |
| `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py` | `77A9674EA103D092DD9DFFE5CC91C959C1B1F08B01C8D8A54BFF8515B96EC4BB` |
| `tests/architecture/test_legacy_surface_documentation.py` | `2054D9102D7673D0D1059F50552E1B39A2B766C2AEEA25EF71FC96987B95B6F1` |
| `documentation/workflow/reports/02-routing-security-quality-notes.md` | `E1AFBA162A0849ED30A6916536DB79239270796F2EB9A003645D2C2F1127BF96` |
| `documentation/workflow/workflow.md` | `CD43C417BD16AEF9C30285FFD6F2C9EF53FA5D530748D7713D60DF76C8C0CEE6` |
| `documentation/workflow/execution-report.md` | `D92BEFE4FDB41469DA5B0D54E3F0BE10136DACEABD21D6053171850E16E2372C` |
| `documentation/Howto.adoc` | `81432263BEB030B1675072D62657A073AA96A143BF8E8D57D9C91E0B918212EB` |
| `src/tiny_swarm_world/__main__.py` | `CDCF97A52088C936D0808FADC51D0B39D5F6CE8F2131FE4C2C7C2645E772B27C` |
| `src/tiny_swarm_world/domain/artifacts/container_image_contract.py` | `558C8901449F5145B2DB53562A5990CA889EB829D8F80D52847B197DA420E167` |
| `src/tiny_swarm_world/infrastructure/adapters/clients/multipass_container_image_publisher.py` | `A13E28DA44E4B87B38A89A01689667B80638C701DBEA48ACE58A0AF4BA5B74DC` |
| `tests/domain/artifacts/__init__.py` | `01BA4719C80B6FE911B091A7C05124B64EEECE964E09C058EF8F9805DACA546B` |
| `tests/domain/artifacts/test_container_image_contract.py` | `08BB7179FDF6F74E834E799F55ED7E6C72947583DE78DD2E0C5A332D586F7533` |
| `tests/infrastructure/adapters/clients/test_multipass_container_image_publisher.py` | `3EF716BFB2325CAA9ABE2192639A643F975734F0A9D659938262145BF6897B6E` |
| `tests/test_package_entrypoint.py` | `0315B3C23627AB9129ED1A67EB7119D848E47713C0114D246675D319DDCB4279` |

## Stale When

- Any recorded governing file hash changes.
- `documentation/workflow/**` changes outside this workflow branch.
- `documentation/epics/**`, `documentation/architecture/**`, or
  `documentation/arc42/**` changes in a way that affects service access,
  routing, credential handling, setup, deployment, or quality gates.
- Branch context changes.
- A conflict is detected.
- A slice requires live infrastructure behavior not described in the workflow.
