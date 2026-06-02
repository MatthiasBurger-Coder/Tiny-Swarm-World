# Swarm Legacy Helper Area

This directory contains transitional helper notes from the pre-boundary layout.
Treat them as legacy support material, not as the canonical orchestration entry
point.

Canonical Python orchestration starts at:

- `src/tiny_swarm_world/__main__.py`
- `src/tiny_swarm_world/infrastructure/composition.py`

Remaining transitional files:

- `file_copy.py` is retained as inert legacy material only. It is not a
  supported workflow entry point.

Do not run these scripts during normal development quality checks. They can
change copied file state when adapted or executed manually.
The canonical classification is maintained in
`documentation/system/live-operation-surfaces.adoc`.
