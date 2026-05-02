# Platform Infrastructure Boundary

This directory marks the target home for platform provisioning assets.

Current platform assets remain in their existing locations for compatibility:

- `infra/config/multipass`
- `infra/config/docker` for Docker daemon installation and Swarm commands
- `infra/config/network`
- `infra/config/vm`
- `infra/swarm`

Do not move live infrastructure scripts into this directory without a dedicated
migration slice and compatibility handling.
