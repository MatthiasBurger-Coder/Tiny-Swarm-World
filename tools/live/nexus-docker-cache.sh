#!/usr/bin/env bash
set -euo pipefail

# Starts a local Nexus Docker proxy cache and configures Docker to use it.
# This is an operator live helper, intentionally separate from the Python
# implementation and the guarded setup workflow.

NEXUS_CONTAINER_NAME="${NEXUS_CONTAINER_NAME:-tiny-swarm-nexus-cache}"
NEXUS_IMAGE="${NEXUS_IMAGE:-sonatype/nexus3:latest}"
NEXUS_VOLUME="${NEXUS_VOLUME:-tiny-swarm-nexus-cache-data}"

NEXUS_WEB_PORT="${NEXUS_WEB_PORT:-8081}"
NEXUS_DOCKER_PROXY_PORT="${NEXUS_DOCKER_PROXY_PORT:-5000}"

NEXUS_ADMIN_PASSWORD="${NEXUS_ADMIN_PASSWORD:-}"
NEXUS_REPOSITORY_NAME="${NEXUS_REPOSITORY_NAME:-docker-hub-proxy}"
JSON_CONTENT_TYPE_HEADER="Content-Type: application/json"

# For normal local Docker use: 127.0.0.1
# For LXC nodes, set this to an IP/hostname reachable from inside the nodes.
NEXUS_REGISTRY_HOST="${NEXUS_REGISTRY_HOST:-127.0.0.1}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_LIST_FILE="${IMAGE_LIST_FILE:-${SCRIPT_DIR}/images-to-cache.txt}"

log() {
  local message="$1"
  printf '[nexus-cache] %s\n' "$message"
}

require_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Missing required command: $command_name" >&2
    exit 1
  }
}

require_admin_password() {
  if [[ -n "${NEXUS_ADMIN_PASSWORD}" ]]; then
    return 0
  fi

  echo "NEXUS_ADMIN_PASSWORD must be supplied by the operator." >&2
  echo "Example: NEXUS_ADMIN_PASSWORD='<local-password>' $0" >&2
  exit 1
}

wait_for_nexus() {
  log "Waiting for Nexus to become reachable..."

  for _ in $(seq 1 120); do
    if curl -fsS "http://127.0.0.1:${NEXUS_WEB_PORT}/service/rest/v1/status" >/dev/null 2>&1; then
      log "Nexus is reachable."
      return 0
    fi
    sleep 2
  done

  echo "Nexus did not become ready in time." >&2
  exit 1
}

get_initial_admin_password() {
  docker exec "${NEXUS_CONTAINER_NAME}" cat /nexus-data/admin.password 2>/dev/null || true
}

set_admin_password_if_needed() {
  local initial_password
  initial_password="$(get_initial_admin_password)"

  if [[ -z "${initial_password}" ]]; then
    log "Initial admin password not found. Assuming password was already changed."
    return 0
  fi

  log "Changing initial Nexus admin password..."

  curl -fsS -u "admin:${initial_password}" \
    -X PUT \
    -H "Content-Type: text/plain" \
    --data "${NEXUS_ADMIN_PASSWORD}" \
    "http://127.0.0.1:${NEXUS_WEB_PORT}/service/rest/v1/security/users/admin/change-password" >/dev/null
}

enable_docker_bearer_token_realm() {
  log "Ensuring Docker Bearer Token Realm is active..."

  local active_realms
  active_realms="$(curl -fsS -u "admin:${NEXUS_ADMIN_PASSWORD}" \
    "http://127.0.0.1:${NEXUS_WEB_PORT}/service/rest/v1/security/realms/active")"

  if printf '%s' "${active_realms}" | grep -q '"DockerToken"'; then
    log "Docker Bearer Token Realm is already active."
    return 0
  fi

  local updated_realms
  updated_realms="$(printf '%s' "${active_realms}" | python3 -c 'import json, sys; realms = json.load(sys.stdin); realms.append("DockerToken"); print(json.dumps(realms))')"

  curl -fsS -u "admin:${NEXUS_ADMIN_PASSWORD}" \
    -X PUT \
    -H "$JSON_CONTENT_TYPE_HEADER" \
    --data "${updated_realms}" \
    "http://127.0.0.1:${NEXUS_WEB_PORT}/service/rest/v1/security/realms/active" >/dev/null
}

accept_community_eula() {
  log "Checking Nexus Community EULA status..."

  local eula_status
  eula_status="$(curl -fsS -u "admin:${NEXUS_ADMIN_PASSWORD}" \
    "http://127.0.0.1:${NEXUS_WEB_PORT}/service/rest/v1/system/eula" || true)"

  if printf '%s' "${eula_status}" | grep -q '"accepted"[[:space:]]*:[[:space:]]*true'; then
    log "Nexus Community EULA is already accepted."
    return 0
  fi

  log "Accepting Nexus Community EULA through the REST API..."

  local accepted_payload
  accepted_payload="$(printf '%s' "${eula_status}" | python3 -c 'import json, sys; payload = json.load(sys.stdin); payload["accepted"] = True; print(json.dumps(payload))')"

  curl -fsS -u "admin:${NEXUS_ADMIN_PASSWORD}" \
    -X POST \
    -H "$JSON_CONTENT_TYPE_HEADER" \
    --data "${accepted_payload}" \
    "http://127.0.0.1:${NEXUS_WEB_PORT}/service/rest/v1/system/eula" >/dev/null
}

enable_anonymous_access() {
  log "Enabling anonymous read access..."

  curl -fsS -u "admin:${NEXUS_ADMIN_PASSWORD}" \
    -X PUT \
    -H "$JSON_CONTENT_TYPE_HEADER" \
    --data '{
      "enabled": true,
      "userId": "anonymous",
      "realmName": "NexusAuthorizingRealm"
    }' \
    "http://127.0.0.1:${NEXUS_WEB_PORT}/service/rest/v1/security/anonymous" >/dev/null
}

repository_exists() {
  curl -fsS -u "admin:${NEXUS_ADMIN_PASSWORD}" \
    "http://127.0.0.1:${NEXUS_WEB_PORT}/service/rest/v1/repositories/${NEXUS_REPOSITORY_NAME}" >/dev/null 2>&1
}

create_docker_proxy_repository() {
  if repository_exists; then
    log "Docker proxy repository already exists: ${NEXUS_REPOSITORY_NAME}"
    return 0
  fi

  log "Creating Docker Hub proxy repository: ${NEXUS_REPOSITORY_NAME}"

  curl -fsS -u "admin:${NEXUS_ADMIN_PASSWORD}" \
    -X POST \
    -H "$JSON_CONTENT_TYPE_HEADER" \
    --data "{
      \"name\": \"${NEXUS_REPOSITORY_NAME}\",
      \"online\": true,
      \"storage\": {
        \"blobStoreName\": \"default\",
        \"strictContentTypeValidation\": true
      },
      \"proxy\": {
        \"remoteUrl\": \"https://registry-1.docker.io\",
        \"contentMaxAge\": 1440,
        \"metadataMaxAge\": 1440
      },
      \"negativeCache\": {
        \"enabled\": true,
        \"timeToLive\": 1440
      },
      \"httpClient\": {
        \"blocked\": false,
        \"autoBlock\": true
      },
      \"docker\": {
        \"v1Enabled\": false,
        \"forceBasicAuth\": false,
        \"httpPort\": ${NEXUS_DOCKER_PROXY_PORT}
      },
      \"dockerProxy\": {
        \"indexType\": \"HUB\",
        \"cacheForeignLayers\": false,
        \"foreignLayerUrlWhitelist\": []
      }
    }" \
    "http://127.0.0.1:${NEXUS_WEB_PORT}/service/rest/v1/repositories/docker/proxy" >/dev/null
}

start_nexus() {
  if docker ps --format '{{.Names}}' | grep -qx "${NEXUS_CONTAINER_NAME}"; then
    log "Nexus container is already running."
    return 0
  fi

  if docker ps -a --format '{{.Names}}' | grep -qx "${NEXUS_CONTAINER_NAME}"; then
    log "Starting existing Nexus container..."
    docker start "${NEXUS_CONTAINER_NAME}" >/dev/null
    return 0
  fi

  log "Creating Nexus volume..."
  docker volume create "${NEXUS_VOLUME}" >/dev/null

  log "Starting Nexus container..."
  docker run -d \
    --name "${NEXUS_CONTAINER_NAME}" \
    --restart unless-stopped \
    -p "${NEXUS_WEB_PORT}:8081" \
    -p "${NEXUS_DOCKER_PROXY_PORT}:${NEXUS_DOCKER_PROXY_PORT}" \
    -v "${NEXUS_VOLUME}:/nexus-data" \
    "${NEXUS_IMAGE}" >/dev/null
}

write_docker_daemon_config() {
  local config_file="/etc/docker/daemon.json"
  local backup_file="/etc/docker/daemon.json.tsw-nexus-cache.bak"

  sudo mkdir -p /etc/docker

  if [[ -f "${config_file}" && ! -f "${backup_file}" ]]; then
    log "Creating Docker daemon config backup: ${backup_file}"
    sudo cp "${config_file}" "${backup_file}"
  fi

  sudo tee "${config_file}" >/dev/null <<EOF
{
  "registry-mirrors": [
    "http://${NEXUS_REGISTRY_HOST}:${NEXUS_DOCKER_PROXY_PORT}"
  ],
  "insecure-registries": [
    "${NEXUS_REGISTRY_HOST}:${NEXUS_DOCKER_PROXY_PORT}"
  ]
}
EOF
}

restart_docker_daemon() {
  if command -v systemctl >/dev/null 2>&1 && systemctl is-system-running >/dev/null 2>&1; then
    sudo systemctl restart docker
    return 0
  fi

  sudo service docker restart
}

configure_local_docker_daemon() {
  log "Configuring local Docker daemon registry mirror..."
  write_docker_daemon_config
  restart_docker_daemon
}

cache_images() {
  if [[ ! -f "${IMAGE_LIST_FILE}" ]]; then
    log "No ${IMAGE_LIST_FILE} found. Skipping image pre-cache."
    return 0
  fi

  log "Pre-caching images from ${IMAGE_LIST_FILE}..."

  while IFS= read -r image; do
    [[ -z "${image}" ]] && continue
    [[ "${image}" =~ ^# ]] && continue

    log "Pulling through Nexus cache: ${image}"
    docker pull "${image}"
  done < "${IMAGE_LIST_FILE}"
}

main() {
  require_command docker
  require_command curl
  require_command python3
  require_admin_password

  start_nexus
  wait_for_nexus
  set_admin_password_if_needed
  accept_community_eula
  enable_docker_bearer_token_realm
  enable_anonymous_access
  create_docker_proxy_repository
  configure_local_docker_daemon
  cache_images

  log "Done."
  log "Nexus UI:      http://127.0.0.1:${NEXUS_WEB_PORT}"
  log "Docker cache: http://${NEXUS_REGISTRY_HOST}:${NEXUS_DOCKER_PROXY_PORT}"
}

main "$@"
