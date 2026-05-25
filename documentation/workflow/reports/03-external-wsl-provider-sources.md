# External WSL And Provider Source Baseline

This workflow report records external documentation checked for the
LXC-native provider direction. It is a planning source baseline, not proof
that Tiny Swarm World has implemented or live-validated WSL2, LXD, Incus,
Docker-in-container, or Docker Swarm behavior.

## Official Sources Checked

- Microsoft Learn: Use systemd to manage Linux services with WSL
  - `https://learn.microsoft.com/en-us/windows/wsl/systemd`
- Ubuntu WSL documentation
  - `https://documentation.ubuntu.com/wsl/stable/`
- LXD documentation: How to install LXD
  - `https://documentation.ubuntu.com/lxd/default/installing/`
- LXD documentation: How to initialize LXD
  - `https://documentation.ubuntu.com/lxd/latest/howto/initialize/`
- Ubuntu tutorial: How to run Docker inside LXD containers
  - `https://ubuntu.com/tutorials/how-to-run-docker-inside-lxd-containers`
- Ubuntu Server documentation: LXD containers and virtual machines
  - `https://ubuntu.com/server/docs/how-to/virtualisation/lxd/`
- Incus documentation: About containers and VMs
  - `https://linuxcontainers.org/incus/docs/main/explanation/containers_and_vms/`
- Incus documentation: About security
  - `https://linuxcontainers.org/incus/docs/main/explanation/security/`
- LXC security documentation
  - `https://linuxcontainers.org/lxc/security/`

## Planning Facts

- WSL2 must be detected explicitly. WSL1 remains unsupported for this provider
  workflow.
- systemd is required for daemon-managed provider behavior in WSL.
- LXD's documented install path is the Snap package, which requires `snapd`.
- LXD local daemon access is controlled through root or membership in the
  `lxd` group.
- LXD can be initialized with `lxd init --minimal` for a default local setup.
- Docker inside LXD requires explicit Docker-compatible profile settings such
  as nesting and syscall interception.
- Privileged containers are security-sensitive and must never become a silent
  default.

## Workflow Impact

- Add a WSL2 capability gate before any LXD/Incus-backed live setup is claimed.
- Require preflight to check WSL version, systemd, provider daemon access,
  backend ambiguity, and Docker-in-container profile requirements.
- Keep WSL2 live validation evidence separate from native Linux evidence.
- Keep Multipass fallback explicit; it must not hide a failed WSL2 LXD/Incus
  readiness check.
