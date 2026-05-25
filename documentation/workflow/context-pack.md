# Workflow Context Pack: Stable Live Setup

This context pack is a workflow-local navigation aid. It does not replace
`AGENTS.md`, `QUALITY.md`, ADRs, arc42, routing rules, active workflow files
or skill files.

## Workflow

- Name: Stable Live Setup
- Version: `stable-live-setup-v1.0.0`
- Branch: `feature/workflow-stable-live-setup-20260525`
- Created: `2026-05-25`
- Process strand: `stable-live-setup`
- Execution profile: `FULL_PATH`
- Release status: `WORKFLOW_CREATED_IMPLEMENTATION_NOT_STARTED`

## Affected Areas

- Setup live preflight and host runtime readiness
- Multipass daemon/socket/driver diagnostics
- Direct `platform init --live` guard behavior
- Multipass command catalog semantics
- Setup phase fail-fast behavior
- Command runner and terminal diagnostic classification
- Local ignored log evidence and redaction boundary
- Endpoint and WSL localhost forwarding strategy
- IntelliJ Linux/WSL execution documentation
- Credential-source and setup-profile consistency
- Artifact, registry and deployment readiness contracts
- Default static/mocked quality gates
- Optional live smoke evidence handoff

## Forbidden Areas

- Java, Maven, Spring Boot
- Kubernetes-first deployment
- React, TypeScript, Vite, TSX, JSX, browser frontend project setup
- Windows-native runtime support expansion
- Live Multipass, Docker Swarm, compose, netplan, `socat`, Portainer,
  Nexus, Jenkins, RabbitMQ, SonarQube, Swagger/NGINX, Vaultwarden, image
  build, image push or bootstrap execution during workflow creation or
  default gates
- Automatic host package installation, socket permission changes, group
  changes, driver changes or service restarts without later explicit approval
- Committed passwords, tokens, host IPs, local paths, raw command output or
  credential-bearing URLs
- Direct promotion of legacy scripts as canonical setup behavior

## Required Roles

- Senior Workflow Architect
- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer
- Senior Tester

## Conditional Roles

- Senior DevOps Engineer: required for Multipass, Docker, Swarm, artifact and
  deployment readiness slices.
- Senior Documentation Engineer: required for user guide, arc42 and workflow
  synchronization.
- Senior Security Sandbox Engineer: required for credential and redacted
  evidence review.
- Console/status UI skills: required only if terminal status text, recovery
  actions or UI state semantics change.

## Quality Commands

Workflow creation:

```bash
git diff --check
```

Targeted implementation checks:

```bash
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.command_runner.test_command_workflow_configuration
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
| `.agents/skills/swarm-orchestration/SKILL.md` | `FAD1651BB25B5DBD3BA5C98174AEA0B24FF41B42B1BBF78926140304BE44AF95` |
| `.agents/skills/setup-bootstrap-expert/SKILL.md` | `37476A7B553A5E63B7E2B1F074D7DD697B2BD138A9EA745E6AC83A81C57CB5AC` |
| `.agents/skills/platform-verification/SKILL.md` | `FC110A1CBF51494E71DD9C7009034D2B0DEF5F9249EAB53841B84ED67381E018` |
| `documentation/epics/autonomous-runnable-setup.md` | `07A73989E4E4246C141636D7D7FF4103E51BB84BA76D1A5B381B3A83ADF62626` |
| `documentation/arc42/07_deployment_view.adoc` | `68CF3D04B01A5B76A21A7D0FF392ADE2A5E7D6D2285072C53B582F816D6DDA1E` |
| `documentation/arc42/10_quality_requirements.adoc` | `EA57B91A80012601B4B0E1518BA7B1A1D41A7601158FF238EAB6A79C67C0C0B2` |
| `documentation/arc42/11_risks_and_debt.adoc` | `321CAE001C3293F863051E78CC2013E265E31934567CAF2EF2AA8221E42C823F` |
| `documentation/user_guide/installation.adoc` | `EE73DEB90113885A8BDED7395F022414DE8B630A00774ACE23E51C4483DE2B89` |
| `documentation/user_guide/troubleshooting.adoc` | `EB7843EFC2965390072DB12B2D5140A52DB4C050846EBCD995A15F7531CBB216` |
| `src/tiny_swarm_world/domain/preflight/preflight_configuration.py` | `B0E05855978875C97195019692B102738F67E7B7DA8EC61954E579CF91A1399B` |
| `src/tiny_swarm_world/application/ports/preflight/port_host_preflight_probe.py` | `F2523F7398B05458A5BDC7752C0821907A8088E79243D409ACEE5D6AD1BA1D16` |
| `src/tiny_swarm_world/application/services/platform/preflight_service.py` | `6710470928CB195F6DAA2731AB67157A6D9C46FEBF07F053507FAE1F3661AEA9` |
| `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py` | `27FC441CC4136D697D453D53792E6DB69E40F74131EFAAD3182E678CDF32743E` |
| `src/tiny_swarm_world/application/services/multipass/multipass_init_vms.py` | `00A308846658D534D30DF6639BEC2CABFC375BCCB9C6D6C3E4E90C5B08D037AE` |
| `src/tiny_swarm_world/application/services/platform/workflows.py` | `0D5967007B200F1D746806EDEA951A0FE84BB5349574EB2C5792D35B9FCB4EE8` |
| `src/tiny_swarm_world/infrastructure/adapters/command_runner/async_command_runner.py` | `E039D230CB951A34A636D9172CB92ABA9BEF3EC173975B83F2C7B24896CE5611` |
| `src/tiny_swarm_world/application/services/commands/command_executer/command_executer.py` | `83FBD76877516B405287286BB9643A4697560534A5C54499CDE4768B807D74E0` |
| `src/tiny_swarm_world/infrastructure/composition.py` | `0E3006941C57B0FEE78517BD6041A2D61D9E3949EA8E47DB816674885697CB0B` |
| `tests/application/services/platform/test_preflight_service.py` | `BB801C933C6A010D65A2A8BE82A759D278B9F2B321330F82EF37A14C2F436598` |
| `tests/infrastructure/adapters/preflight/test_host_preflight_probe.py` | `08D5B80592F62F4F4055FBCCC101D595440100B479E27CF66C110B2B2FC83840` |
| `tests/application/services/setup/test_setup_workflow.py` | `7F5B1B5B77997DA508BAA27401EA6BD3B60CE5BDD46801E4CEB86D52ADEC784B` |
| `tests/test_package_entrypoint.py` | `AD2A799BB201ACA8801B624D9DF763FEE2BDEFADF8D2A39A7D6BC093993AC922` |

## Stale When

- Any recorded governing file hash changes.
- Branch context changes.
- `documentation/workflow/**` changes outside this workflow branch.
- A slice needs live infrastructure behavior not described in the workflow.
- New `.tiny-swarm-world` evidence changes the failure classification.
- EPIC, ADR, arc42, endpoint, credential or profile decisions change.
- A conflict is detected.
