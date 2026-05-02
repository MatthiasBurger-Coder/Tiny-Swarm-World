# Artifact Infrastructure Boundary

This directory marks the target home for artifact build, registry, and
publishing assets.

Current artifact assets remain in their existing locations for compatibility:

- `infra/prepare/nexus`
- `infra/compose/create_dockerfiles.sh`
- Dockerfile templates used by image build and push workflows

Do not move live image build, registry, or Nexus bootstrap scripts into this
directory without a dedicated migration slice and compatibility handling.
