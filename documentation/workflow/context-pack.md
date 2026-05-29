# Context Pack: LXC Docker Swarm Bootstrap

## Purpose

This context pack supports workflow
`lxc-docker-swarm-bootstrap-v1.0.0`. The workflow creates the implementation
plan for installing Docker Engine inside managed LXC containers and
initializing Docker Swarm on those containers, using the existing Multipass
Docker install and Swarm flow as the behavioral baseline.

## Request

```text
workflow create:
Überarbeite die stelle damit auf den LXC Container docker installiert wird. Nimm als grundlage die multipass vorgehenweise und passe diese für die LXC an
```

## Active Branch

```text
feature/workflow-lxc-docker-install-20260529
```

## Active Workflow Hash

```text
28cbccd6c52daa32147a58d2e27775b548dc03d768c5af139bee2ea82e23af50  documentation/workflow/workflow.md
```

## Current Repository Baseline

- Tiny Swarm World is Linux/WSL-only and Docker Swarm-first.
- `lxc_native` through LXD or Incus is the default provider direction.
- Multipass remains explicit legacy/fallback behavior.
- LXC node creation and provider readiness are implemented for platform init.
- Docker-in-LXC, Swarm-in-LXC, provider-native reconcile, artifact
  publication, deployment, and live WSL2 proof remain incomplete or blocked.
- `setup run` is already live-consent gated and fail-closed.

## Relevant Existing Source

- Multipass Docker install service:
  `src/tiny_swarm_world/application/services/multipass/multipass_docker_install.py`
- Multipass Swarm service:
  `src/tiny_swarm_world/application/services/multipass/multipass_docker_swarm_init.py`
- Multipass Docker install YAML:
  `infra/config/docker/command_multipass_docker_install_yaml.yaml`
- Multipass Docker verify YAML:
  `infra/config/docker/command_multipass_docker_verify_yaml.yaml`
- LXC provider adapter:
  `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py`
- LXC provider config:
  `infra/config/node-providers/provider_config.yaml`

## Implementation Notes For Executors

- Slice metadata is S3D-ready: every slice has concrete dependencies, affected
  files/modules/contracts, file locks, contract locks, architecture locks,
  targeted quality gates, required quality gates, and stop conditions.
- The execution graph is serial by design. Later slices touch shared Platform,
  adapter, composition, test, and documentation surfaces, so parallel writes
  are not authorized by this workflow.
- Start by reading the Multipass Docker install and Swarm services to preserve
  sequence and failure semantics.
- Do not copy `multipass exec` into application code. The LXC path needs a
  backend-aware infrastructure adapter or structured command configuration.
- Keep Swarm join tokens memory-only.
- Treat local IP addresses as operational facts, not committed configuration.
- Keep Artifacts and Deployment boundaries blocked unless later workflows own
  them.
- Use mocked command runners in tests. Live smoke is a separate explicit step.

## External Source Notes

- Docker Engine on Ubuntu should be installed from Docker's apt repository
  unless a later workflow accepts a version-pinning policy.
- LXD and Incus require Docker-in-container nesting support to be explicit.
- Privileged-container changes are security-sensitive and require explicit
  operator approval and possibly a later ADR.

## Source Hashes

```text
131aa2183b9598aeb86fed0af1e66b09ed6b29e5b54a4993a898d3c2782d3856  AGENTS.md
458e5f4d8fbdedea1c413e1ff135ec91392a4bb5a5aea20300dcac8e209414b6  QUALITY.md
5a36d5fba27af89b134cdb2a3ee25e4a5b9122f92c3287a3462d28435884cc95  documentation/epics/system-unification.md
7d536929ed42f15c720929d13269fa4491c5b9c98f921e16f870a6944b76aa33  documentation/epics/autonomous-runnable-setup.md
150ac249a1e7ecb56a5cefb6051ba2729969523475da0851506b0c15d8607419  documentation/architecture/adr-lxc-native-node-provider.adoc
b350f855f508a083583e6433c494a5abd36c1ed68164d899984acafced0083ca  documentation/architecture/adr-autonomous-setup-safety.adoc
e6223a4adf715acdea0f125ae0aefe0206ecc94b906b60e5091cccd4f3369072  documentation/arc42/06_runtime_view.adoc
22e5ce1b50d43225af70535810b6a0cdd2b0649115b71b074d39c812e582e39d  documentation/arc42/07_deployment_view.adoc
2a39a0eddd1b50747542a6b1757229c34221ea8b245568cce0dfe67c7507b3c1  documentation/arc42/09_architecture_decisions.adoc
caf62007139333fb2e0526a9a9ea0c0dbe203031c41decbaad1e325abf1781f3  src/tiny_swarm_world/application/services/multipass/multipass_docker_install.py
1cd82bb7065e9359e72b19c57ac4b17cb037f9656c39c4e8488cc9652f782ae8  src/tiny_swarm_world/application/services/multipass/multipass_docker_swarm_init.py
da02d975754c936a4af56318287694a201de0c485a0b2aa1c154c20d6af8dc70  src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py
de6d615208b6d05f3c6dba0da75732768b108aa34c0b79f6ce4ec9cd0d2f3cdb  infra/config/docker/command_multipass_docker_install_yaml.yaml
0aea4369f3e46c5aca1a3bdd2b6927e58935152a8c1fe6f7f1df9d8da0491af9  infra/config/docker/command_multipass_docker_prepare_repository_yaml.yaml
4fb24ace0d87767386ef584cb21fcd8134bab715fe53dd041f0f8f87c77a5843  infra/config/docker/command_multipass_docker_verify_yaml.yaml
c832527bc4068f916bae41527e7a1fbabc811e7b62e1298d214860ce6aade012  infra/config/node-providers/provider_config.yaml
```
