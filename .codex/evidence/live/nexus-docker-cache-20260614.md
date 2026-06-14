# Live Evidence: Nexus Docker Cache

Date: 2026-06-14

## Request

User explicitly approved live execution:

```text
run live nexus-docker-cache.sh der läuft schon. Da kannst du gerne artefakte anlegen
```

## Safety Classification

- Live infrastructure operation.
- Script: `tools/live/nexus-docker-cache.sh`.
- Potential mutations from script:
  - Docker container and volume creation/start.
  - Nexus REST configuration.
  - Nexus Community EULA acceptance.
  - Anonymous read access enablement.
  - Docker daemon mirror config under `/etc/docker/daemon.json`.
  - Docker daemon restart through `sudo`.
  - Docker image pulls through the configured cache.

## Preflight Observations

- Git state before live check: `main...origin/main`, clean.
- WSL default distribution: Ubuntu, WSL version 2.
- Required tools in WSL:
  - `docker`: present at `/usr/bin/docker`.
  - `curl`: present at `/usr/bin/curl`.
  - `python3`: present at `/usr/bin/python3`.
- Script file exists: `tools/live/nexus-docker-cache.sh`.
- Script executable bit is not set in WSL view; it can be run with `bash`.
- Running Nexus-like container:
  - Name: `tiny-swarm-nexus-cache`.
  - Image: `sonatype/nexus3:latest`.
  - Status: `Up 14 hours`.
- Published ports from Docker:
  - container `8081/tcp` -> host `8082`.
  - container `5001/tcp` -> host `5001`.
- Script defaults do not match the running container:
  - Default `NEXUS_WEB_PORT=8081`, observed host port is `8082`.
  - Default `NEXUS_DOCKER_PROXY_PORT=5000`, observed host port is `5001`.
- `NEXUS_ADMIN_PASSWORD` was not present in the WSL environment.
- Nexus status endpoint on host port `8082` was reachable by `curl`.
- Follow-up check:
  - `/nexus-data/admin.password` is not present in the running container.
  - This indicates the initial admin password has already been consumed or
    removed.
  - Nexus status endpoint on host port `8082` remains reachable.

## Result

The script was not continued past preflight because required authentication
input was missing and the running container uses non-default ports. Continuing
without explicit redacted configuration would either fail closed or target the
wrong host ports.

Follow-up live configuration is still blocked until the current Nexus admin
password is supplied by the operator or exported in the WSL environment.

## Continued Run After Operator Access Grant

The operator supplied the current Nexus admin password in chat and then
confirmed access. The value was used only as a process environment value and
is intentionally not recorded here.

The interrupted script process was still running and was blocked at:

```text
sudo mkdir -p /etc/docker
```

Passwordless sudo was not available, so the blocked script process was stopped
to avoid a hidden long-running live operation.

Observed successful script effects before the sudo block:

- Nexus authentication with the supplied admin password succeeded.
- Docker Bearer Token Realm is active.
- Anonymous read access is enabled.
- `docker-hub-proxy` repository exists.

Observed Docker host state:

- `/etc/docker/daemon.json` already contains:

```json
{
  "registry-mirrors": [
    "http://127.0.0.1:5001"
  ],
  "insecure-registries": [
    "127.0.0.1:5001"
  ]
}
```

- Docker daemon reports registry mirror:

```json
["http://127.0.0.1:5001/"]
```

Because the daemon was already configured and loaded with the mirror, the image
cache step was run manually instead of re-running the full script and blocking
again on sudo.

## Image Cache Result

The following image pulls completed successfully:

```text
danielgtaylor/apisprout:latest
docker.swagger.io/swaggerapi/swagger-editor:latest
docker.swagger.io/swaggerapi/swagger-ui:latest
nginx:mainline-alpine
```

Local Docker images after pull:

```text
danielgtaylor/apisprout:latest
docker.swagger.io/swaggerapi/swagger-editor:latest
docker.swagger.io/swaggerapi/swagger-ui:latest
nginx:mainline-alpine
```

Nexus `docker-hub-proxy` search returned cached components including:

```text
danielgtaylor/apisprout
library/nginx
swaggerapi/swagger-editor
swaggerapi/swagger-ui
```

## Final Live Status

- Nexus container is running.
- Nexus UI is reachable through host port `8082`.
- Docker proxy cache is exposed through host port `5001`.
- Docker daemon mirror is configured as `http://127.0.0.1:5001/`.
- The required service-access images were pulled successfully.
- Full script completion remains partially blocked in non-interactive mode by
  sudo for `/etc/docker`, but the intended Nexus cache and image pull state is
  present.

## Required Command Shape For Next Live Run

Run from WSL/Linux with the operator-provided password in the environment:

```bash
cd /mnt/d/Projects/Tiny-Swarm-World
NEXUS_ADMIN_PASSWORD='<redacted>' \
NEXUS_WEB_PORT=8082 \
NEXUS_DOCKER_PROXY_PORT=5001 \
NEXUS_REGISTRY_HOST=127.0.0.1 \
bash tools/live/nexus-docker-cache.sh
```

If LXC nodes must use the cache, `NEXUS_REGISTRY_HOST` must be set to a host or
IP address reachable from inside those nodes instead of `127.0.0.1`.

## Images-To-Cache File

Detected `tools/live/images-to-cache.txt` entries:

```text
danielgtaylor/apisprout:latest
docker.swagger.io/swaggerapi/swagger-editor:latest
docker.swagger.io/swaggerapi/swagger-ui:latest
nginx:mainline-alpine
```

## Follow-Up

- Provide or export `NEXUS_ADMIN_PASSWORD` in WSL before the live script run.
- Use the observed port overrides unless the running container is intentionally
  recreated with the script defaults.
- Expect the script to require `sudo` when writing Docker daemon config and
  restarting Docker.
