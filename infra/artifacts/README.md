# Artifact Infrastructure Boundary

This directory marks the target home for artifact build, registry, and
publishing assets.

Current artifact assets remain in their existing locations for compatibility:

- `infra/compose/**/Dockerfile`
- service configuration files used as image build contexts

Former direct helpers under `infra/prepare/nexus` have been retired. Live image
build and registry publish behavior is owned by the Python artifact workflow
behind the setup command. Do not add host-side image build or push scripts
without a dedicated migration slice and compatibility handling.
