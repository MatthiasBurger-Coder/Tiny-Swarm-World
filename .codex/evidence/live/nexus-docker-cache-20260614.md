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

## Result

The script was not continued past preflight because required authentication
input was missing and the running container uses non-default ports. Continuing
without explicit redacted configuration would either fail closed or target the
wrong host ports.

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
