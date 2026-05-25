# Workflow Context Pack

This context pack is a navigation aid for the active workflow. It does not
replace root `AGENTS.md`, root `QUALITY.md`, EPICs, ADRs, arc42, skill files,
or the workflow itself.

## Active Workflow

- Version: `linux-wsl-swarm-setup-v1.0.0`
- Branch: `fix/linux-wsl-swarm-setup-workprocess-20260525`
- Source: user-provided `workflow-linux-wsl-swarm-setup.md`
- Source SHA256:
  `B42CE30106AF8F200284A4FC6C3C9EBAFEAA84FE6CDC2CB31D101889C0C9A9A1`
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS`
- Execution profile: `NORMAL_PATH`
- Process strand: workflow authoring, setup preflight, platform setup,
  Multipass readiness, WSL2 network planning, evidence, documentation,
  quality validation
- Sequencing update: Slice 06 and Slice 07 run serially after Slice 05. Slice
  07 depends on Slice 06 because both may touch infrastructure preflight
  adapter scope.

## Affected Areas

- `src/tiny_swarm_world/domain/preflight`
- `src/tiny_swarm_world/domain/multipass`
- `src/tiny_swarm_world/domain/network`
- `src/tiny_swarm_world/application/ports/preflight`
- `src/tiny_swarm_world/application/services/platform`
- `src/tiny_swarm_world/application/services/setup`
- `src/tiny_swarm_world/application/services/network`
- `src/tiny_swarm_world/infrastructure/adapters/preflight`
- `src/tiny_swarm_world/infrastructure/adapters/command_runner`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `src/tiny_swarm_world/__main__.py`
- `tests/domain`
- `tests/application/services/platform`
- `tests/application/services/setup`
- `tests/infrastructure/adapters/preflight`
- `documentation/architecture`
- `documentation/system`
- `documentation/user_guide`
- `documentation/deployment`
- `documentation/arc42`

## Forbidden Areas

- Java, Maven, Spring Boot, Gradle, JUnit, or ArchUnit build surfaces.
- Browser React/frontend modules, package managers, `.tsx`, `.jsx`, Vite,
  Next.js, TypeScript frontend configs, or browser routes.
- Kubernetes-first implementation.
- Direct execution or promotion of `infra/swarm` scripts.
- Live Multipass, Docker Swarm, compose, netplan, `socat`, `iptables`,
  `netsh`, Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, or Swagger/NGINX
  commands during normal tests or quality gates.
- Committed secrets, host IPs, usernames, local absolute paths, raw command
  strings, raw stdout, raw stderr, environment payloads, or Swarm join tokens.

## Required Roles

- Senior Workflow Architect
- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer as N/A React guard
- Senior Tester
- Senior Documentation Engineer

## Conditional Roles

- Senior DevOps Engineer for live platform validation planning.
- Security/Sandbox Engineer for evidence, host mutation, and live approval
  boundaries.
- Console/status UI skills for CLI/status output semantics.
- Git commit preparation skills before staging, commit, push, or PR work.

## Quality Commands

```bash
git diff --check
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

Targeted commands used by implementation slices:

```bash
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe
PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
```

## Governing File Hashes

Git blob hashes:

| File | Hash |
| --- | --- |
| `AGENTS.md` | `13a61789bff97a4b0b7c99424aca1d79f013d55e` |
| `QUALITY.md` | `17002150bab9f168eb60be85d55b7a0c1cb441e5` |
| `documentation/epics/autonomous-runnable-setup.md` | `cc9c7ae0e5a116395bd4582eb2049a17e54e7e08` |
| `documentation/epics/system-unification.md` | `c1810e090ec3a53938d0a8b1174dc407e0763262` |
| `documentation/system/live-operation-surfaces.adoc` | `007b9c42d1111aa24206f675e81a567685f59fb4` |
| `documentation/system/multipass-setup.adoc` | `ad6a4eff60ad4c46ffe8a8fd05288048d20a275f` |
| `documentation/system/network.adoc` | `e5e7eb7cfb21f023a76b534bbd4febbf226fa5ed` |
| `documentation/arc42/02_constraints.adoc` | `535551ede77e366a78c253583724aa068bb2454b` |
| `documentation/arc42/06_runtime_view.adoc` | `5a16efb85a04e5099b1ba31b84830eb672af0825` |
| `documentation/arc42/07_deployment_view.adoc` | `3e0e76f65979ba7bbc384379def3ffbe795e174b` |
| `documentation/arc42/11_risks_and_debt.adoc` | `0ad988ec0b27d59f82b265a475110e9cddaeb99c` |
| `documentation/architecture/adr-autonomous-setup-safety.adoc` | `3c6c88c479ac3db7aa8d8cdf03e06fc045d074a0` |

## Staleness Rules

This context pack is stale when:

- any governing hash changes;
- branch is not `fix/linux-wsl-swarm-setup-workprocess-20260525`;
- `documentation/workflow/workflow.md` changes without updating
  `context-pack.json`;
- implementation touches architecture, quality, or live-consent semantics not
  covered by the workflow;
- workflow execution changes slice order, locks, or required quality gates.

## Live Validation Reminder

Sandbox validates only Linux/sandbox behavior. A real WSL2 console validates
the WSL2 setup path. These results must be evaluated separately.
