# Nexus Preparation Scripts

This directory contains live Nexus preparation material.

Transitional direct helper:

- `setup.py` bootstraps Nexus through Portainer, Docker, and Nexus clients. It
  remains a direct operator script until Nexus behavior is wired behind
  workflow-level artifact/deployment contracts.

Deprecated shell helpers:

- `prepare.sh`
- `addMavenMirror.sh`
- `addLocalDockerRepository.sh`
- `test.sh`

These shell helpers retain local compatibility defaults and may print or read
credential material. Do not run them during normal development quality checks.
The canonical classification is maintained in
`documentation/system/live-operation-surfaces.adoc`.
