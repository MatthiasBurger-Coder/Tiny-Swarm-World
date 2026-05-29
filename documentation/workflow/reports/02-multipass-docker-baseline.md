# Report 02: Multipass Docker Baseline

## Source Files Reviewed

- `src/tiny_swarm_world/application/services/multipass/multipass_docker_install.py`
- `src/tiny_swarm_world/application/services/multipass/multipass_docker_swarm_init.py`
- `infra/config/docker/command_multipass_docker_install_yaml.yaml`
- `infra/config/docker/command_multipass_docker_prepare_repository_yaml.yaml`
- `infra/config/docker/command_multipass_docker_verify_yaml.yaml`

## Behavior To Preserve

- Run installation for the manager and all workers.
- Prepare the Docker apt repository before package installation.
- Install Docker Engine and required plugin packages.
- Verify Docker after install.
- Initialize the manager before workers join.
- Retrieve the worker join token after manager initialization.
- Join workers with the token.
- Verify final Swarm state.
- Stop on failed apply or verification before later phases run.

## Behavior To Adapt

| Multipass behavior | LXC-native adaptation |
| --- | --- |
| `multipass exec <vm> -- ...` | selected backend exec: `lxc exec <container> -- ...` or `incus exec <container> -- ...` |
| VM instance names | provider-configured LXC node names |
| Multipass IP lookup | LXD/Incus container network identity lookup |
| Multipass readiness | LXD/Incus readiness and Docker-in-container profile guard |
| Multipass legacy selection | remains explicit `multipass_legacy` only |

## Behavior To Reject

- Using Multipass command YAML on the default provider path.
- Embedding LXD/Incus command strings in domain or application services.
- Persisting Swarm join tokens or raw command output.
- Treating Docker-in-container profile gaps as host repair work.
