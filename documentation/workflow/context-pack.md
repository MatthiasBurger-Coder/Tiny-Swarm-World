# Workflow Context Pack

This context pack is a navigation aid for the active workflow. It does not
replace root `AGENTS.md`, root `QUALITY.md`, EPICs, ADRs, arc42, skill files,
or the workflow itself.

## Active Workflow

- Version: `lxc-native-node-provider-v1.0.0`
- Branch: `feature/workflow-lxc-node-provider-20260526`
- Source: user request in current thread: LXC/LXD/Incus default provider,
  Multipass legacy/fallback
- Source SHA256: not applicable, no repository source file was provided
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS`
- Execution profile: `FULL_PATH`
- Process strand: workflow authoring, provider architecture, setup preflight,
  platform setup, LXD/Incus readiness, Docker Swarm node lifecycle, Multipass
  legacy fallback, evidence, documentation, quality validation

## External Source Baseline

The workflow includes an external WSL and provider source report:

```text
documentation/workflow/reports/03-external-wsl-provider-sources.md
```

The report records official Microsoft, Ubuntu, LXD, Incus, and LXC
documentation used to harden the WSL2 capability gate, systemd requirement,
provider daemon access model, Docker-in-container profile requirements, and
privileged container risk handling.

## Affected Areas

- `src/tiny_swarm_world/domain/node_provider`
- `src/tiny_swarm_world/domain/preflight`
- `src/tiny_swarm_world/domain/network`
- `src/tiny_swarm_world/domain/multipass`
- `src/tiny_swarm_world/application/ports/node_provider`
- `src/tiny_swarm_world/application/ports/preflight`
- `src/tiny_swarm_world/application/services/platform`
- `src/tiny_swarm_world/application/services/setup`
- `src/tiny_swarm_world/application/services/multipass`
- `src/tiny_swarm_world/infrastructure/adapters/preflight`
- `src/tiny_swarm_world/infrastructure/adapters/clients`
- `src/tiny_swarm_world/infrastructure/adapters/repositories`
- `src/tiny_swarm_world/infrastructure/composition.py`
- `src/tiny_swarm_world/__main__.py`
- `infra/config/node-providers`
- `infra/config/multipass`
- `infra/config/docker`
- `tests/domain`
- `tests/application/services/platform`
- `tests/application/services/setup`
- `tests/application/services/multipass`
- `tests/infrastructure/adapters/preflight`
- `tests/infrastructure/adapters/clients`
- `tests/infrastructure/adapters/repositories`
- `documentation/architecture`
- `documentation/system`
- `documentation/user_guide`
- `documentation/deployment`
- `documentation/arc42`
- `AGENTS.md`
- `README.md`

## Forbidden Areas

- Java, Maven, Spring Boot, Gradle, JUnit, or ArchUnit build surfaces.
- Browser React/frontend modules, package managers, `.tsx`, `.jsx`, Vite,
  Next.js, TypeScript frontend configs, or browser routes.
- Kubernetes-first implementation.
- Raw low-level LXC-only provider as the first implementation.
- Direct execution or promotion of `infra/swarm` scripts.
- Live LXD, Incus, Multipass, Docker Swarm, compose, netplan, `socat`,
  `iptables`, `netsh`, Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, or
  Swagger/NGINX commands during normal tests or quality gates.
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

- Senior DevOps Engineer for LXD/Incus, Docker-in-container, and live platform
  validation planning.
- Security/Sandbox Engineer for provider profile, host mutation, and evidence
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

Targeted commands planned by implementation slices:

```bash
PYTHONPATH=src python3 -m unittest tests.domain.node_provider
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_node_provider_selection
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_lxc_provider_preflight
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider
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
| `documentation/process/workflow-create.md` | `78f2b31e96ab0731ee7b61cc2066f3446f3e1bcf` |
| `.agents/skills/workflow-authoring/SKILL.md` | `6ccd9a0e322437fbca49e388ae3b387ac515758b` |
| `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md` | `a11ed5c6b901e8a5ad5f9c13ce37bfc67886e1b0` |
| `.agents/skills/execution-profile-router/SKILL.md` | `007dd37d35028e99a119219084ad321ffb4da25e` |
| `.agents/orchestrator/routing-rules.md` | `3d7998b6413102c3dd69e4299d70b63a06323923` |
| `documentation/process/branch-governance.md` | `1b4479ac69e659ebfe236fa662c54e6c325412e5` |

## Staleness Rules

This context pack is stale when:

- any governing hash changes;
- branch is not `feature/workflow-lxc-node-provider-20260526`;
- `documentation/workflow/workflow.md` changes without updating
  `context-pack.json`;
- external WSL/LXD/Incus source assumptions change without updating
  `reports/03-external-wsl-provider-sources.md`;
- implementation touches architecture, quality, provider, or live-consent
  semantics not covered by the workflow;
- workflow execution changes slice order, locks, or required quality gates.

## Live Validation Reminder

Sandbox validates only mocked/static behavior. Native Linux validates the first
LXC-native live path. WSL2 validates only WSL2-specific LXD/Incus capability
when operator-approved evidence exists. Multipass fallback evidence is separate
legacy evidence and must not be reported as default-provider success.
