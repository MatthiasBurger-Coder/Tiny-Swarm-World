# Image Build Context Assets

This directory contains image source assets used by the workflow-level Python
setup command. Stack definitions live under `infra/config/compose`.

Supported assets:

- service Dockerfiles and service configuration files
- service runtime configuration such as `swagger/nginx/default.conf`.
  The Swagger NGINX service uses the official `nginx:mainline-alpine` image
  with this mounted config; it does not require a custom image or startup
  wait script.

Host-side image build, registry push, and stack deployment orchestration is
owned by `PYTHONPATH=src python3 -m tiny_swarm_world setup run --live`.
Do not add shell scripts here that run Docker, log in to a registry, push
images, authenticate to Portainer, delete stacks, or upload stacks. The
canonical live-operation classification is maintained in
`documentation/system/live-operation-surfaces.adoc`.
