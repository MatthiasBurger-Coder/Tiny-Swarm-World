# Swarm Legacy Helper Area

This directory contains transitional helper scripts from the pre-boundary
layout. Treat them as legacy support material, not as the canonical
orchestration entry point.

Canonical Python orchestration starts at:

- `src/tiny_swarm_world/__main__.py`
- `src/tiny_swarm_world/infrastructure/composition.py`

Known transitional files:

- `prepere.py` imports helper modules that are not fully present in this
  directory and must not be treated as a supported entry point without a
  dedicated cleanup slice.
- `multipass/multipass_setup.py` and `multipass/multipass_socat_setup.py`
  duplicate parts of the platform provisioning behavior.
- `network/network_manager.py` mixes WSL, Windows port forwarding, Multipass
  discovery, and iptables behavior.

Do not run these scripts during normal development quality checks. They can
change Multipass, networking, socat, iptables, or Docker state.
The canonical classification is maintained in
`documentation/system/live-operation-surfaces.adoc`.
