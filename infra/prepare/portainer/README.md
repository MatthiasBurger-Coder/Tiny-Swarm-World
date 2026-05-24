# Portainer Preparation Scripts

This directory contains live Portainer preparation scripts.

Transitional supported live script:

- `prepare.sh` deploys and initializes Portainer for a local Swarm environment.
  It is a direct operator script and is not protected by the workflow-level CLI
  consent guard.

Deprecated duplicate:

- `portain_setup.py` overlaps with platform networking, Multipass access,
  Docker cleanup, Portainer stack deployment, and admin initialization. Treat it
  as transitional until a dedicated cleanup slice either replaces, quarantines,
  or removes it.

Do not run these scripts during normal development quality checks. They can
modify Docker, Portainer, socat, iptables, volumes, and stack state.
The canonical classification is maintained in
`documentation/system/live-operation-surfaces.adoc`.
