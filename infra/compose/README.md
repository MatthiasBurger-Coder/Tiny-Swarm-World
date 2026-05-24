# Image Build Context Assets

This directory contains image source assets used by the workflow-level Python
setup command. Stack definitions live under `infra/config/compose`.

Supported assets:

- service Dockerfiles and service configuration files
- image-internal runtime helpers such as `swagger/nginx/wait-for-it.sh`.
  The Swagger NGINX image uses this helper to wait for the API service before
  starting NGINX; it is not a host-side setup script.

Host-side image build, registry push, and stack deployment orchestration is
owned by `PYTHONPATH=src python3 -m tiny_swarm_world setup run --live`.
Do not add shell scripts here that run Docker, log in to a registry, push
images, authenticate to Portainer, delete stacks, or upload stacks. The
canonical live-operation classification is maintained in
`documentation/system/live-operation-surfaces.adoc`.
