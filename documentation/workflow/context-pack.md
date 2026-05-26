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
- `documentation/epics`
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
PYTHONPATH=src python3 -m unittest tests.application.services.multipass tests.infrastructure.adapters.clients.test_multipass_swarm_runtime tests.infrastructure.adapters.clients.test_multipass_container_image_publisher tests.infrastructure.adapters.clients.test_multipass_portainer_admin_client tests.infrastructure.test_composition tests.application.services.platform.test_node_provider_selection tests.infrastructure.adapters.repositories.test_node_provider_config_yaml_repository
```

## Governing File Hashes

Git blob hashes:

| File | Hash |
| --- | --- |
| `documentation/workflow/workflow.md` | `64d910a8d0b273b78c1777679e8ec746414241a8` |
| `AGENTS.md` | `05de31b1c980f393d9dd83e744a2debfdc1b6e0a` |
| `README.md` | `794bbdb15674ce45c8fac6b8314eed8a00ff52e4` |
| `QUALITY.md` | `17002150bab9f168eb60be85d55b7a0c1cb441e5` |
| `documentation/arc42/01_introduction.adoc` | `30ab3c65d058fe57c525dff99f15cbede9b4e792` |
| `documentation/arc42/02_constraints.adoc` | `8a39526e30889ebcff4d0afba2a0d712359ace42` |
| `documentation/arc42/03_solution_strategy.adoc` | `83619aaf3d678d8e83490323591d465faaeef044` |
| `documentation/arc42/04_context_and_scope.adoc` | `98e9c614e8dbae284b020aed16367b2a497995da` |
| `documentation/arc42/05_building_blocks.adoc` | `84a80bead3d48cfde0d801a33a129154f44ebc37` |
| `documentation/arc42/06_runtime_view.adoc` | `cc07c5ba4f0428184b4941053e285a9352297cf1` |
| `documentation/arc42/07_deployment_view.adoc` | `ba254a609b9026e23d58c55589d397a7af6e9661` |
| `documentation/arc42/08_concepts.adoc` | `f6f01231a48469b5288009640310ca7961a0e05f` |
| `documentation/arc42/09_architecture_decisions.adoc` | `31501579a175be2a0576a74fa9f3478534949fdd` |
| `documentation/arc42/10_quality_requirements.adoc` | `f7331a4d5a9c78b27b610fb266985652d7196045` |
| `documentation/arc42/11_risks_and_debt.adoc` | `4f54becbf3408ee8622ca2ade1df403843e95292` |
| `documentation/arc42/12_glossary.adoc` | `3eb632b4c513599594cbd66cab1c27ac4766b2c1` |
| `documentation/architecture/adr-autonomous-setup-safety.adoc` | `3c6c88c479ac3db7aa8d8cdf03e06fc045d074a0` |
| `documentation/architecture/adr-lxc-native-node-provider.adoc` | `2446eff28ef1f2477f4c7633b187e2162d934784` |
| `documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc` | `cc718ff1d91b9fe42e968f5da5fc685e87dd7b9c` |
| `documentation/deployment/system.adoc` | `c42fc11b5476bdc3c01a7556aa791ba1b7e90616` |
| `documentation/epics/autonomous-runnable-setup.md` | `1b63126744e4b6044e90eb862b6228e35caf1258` |
| `documentation/epics/service-access-dashboard-vaultwarden.md` | `7755fc1960ecbb076feb5db14aed032fbed76c0c` |
| `documentation/epics/system-unification.md` | `32db9f619ea1b97333e2ed1ac64370bd69a654ae` |
| `documentation/process/workflow-create.md` | `78f2b31e96ab0731ee7b61cc2066f3446f3e1bcf` |
| `documentation/system/live-operation-surfaces.adoc` | `490b65851b74efb109bcfaf44a40dec28350b94d` |
| `documentation/system/lxc-native-setup.adoc` | `e3e33c479e250ea35b40b5fa1cb713901cdc220a` |
| `documentation/system/multipass-setup.adoc` | `b9e6855ce6537dff6b5370c449af17d28bbedc6d` |
| `documentation/system/network.adoc` | `153401597ae96b4c08041f8a9ad296f433507cae` |
| `documentation/system/system.adoc` | `8f25ec014c584b778df668291b3bce875c1df28c` |
| `documentation/user_guide/installation.adoc` | `f4cf28c595470d6bf5b5c8b2242cee870f6af0ed` |
| `documentation/user_guide/troubleshooting.adoc` | `edcfc8f7a4943d06e4b9d21266959c395baddcc7` |
| `documentation/user_guide/usage.adoc` | `e92bb670814447c756d421551246cd6202e168e2` |
| `documentation/workflow/reports/02-architecture-baseline.md` | `c285036e5b9b8fda4b194ad455ddb4eafb5e3f2e` |
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
