# Retired Service Preparation Surface

This directory is kept only as a navigation note for former direct service
preparation helpers. Executable setup scripts and Python bootstrap entry points
must not live here.

Use the canonical setup workflow from the repository root:

```bash
PYTHONPATH=src python3 -m tiny_swarm_world setup run --live
```

The command is guarded by live-infrastructure consent and owns Portainer,
Nexus, image publication, stack deployment, and final verification sequencing.
The historical surface classification is maintained in
`documentation/system/live-operation-surfaces.adoc`.
