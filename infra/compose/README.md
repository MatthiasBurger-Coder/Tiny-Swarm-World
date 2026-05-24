# Compose Live Assets

This directory contains stack assets and direct helper scripts for local
Docker/Portainer operation.

Supported assets:

- `jenkins/docker-compose.yml`
- `swagger/docker-compose.yml`
- service Dockerfiles, Dockerfile templates, and service configuration files

Transitional direct helper:

- `upload_all_stacks.sh` talks directly to Portainer and can delete, recreate,
  or upload stacks.

Deprecated direct helper:

- `create_dockerfiles.sh` builds images, logs in to the local registry, pushes
  images, and logs out.

Do not run these scripts during normal development quality checks. The
canonical classification is maintained in
`documentation/system/live-operation-surfaces.adoc`.
