"""Read Swagger through its running NGINX task, with no published-port fallback."""
from collections.abc import Callable
from typing import Any

SCRIPT = r'''set -eu
overlay_id=''
assert_internal() {
  for service in swagger_swagger-editor swagger_swagger-ui swagger_swagger-api swagger_swagger-nginx; do
    [ "$(docker service inspect --format '{{index .Spec.Labels "com.docker.stack.namespace"}}' "$service")" = swagger ]
    for template in '{{json .Spec.EndpointSpec.Ports}}' '{{json .Endpoint.Ports}}'; do
      ports="$(docker service inspect --format "$template" "$service")"
      case "$ports" in null|'[]') ;; *) exit 1;; esac
    done
    labels="$(docker service inspect --format '{{range $key, $value := .Spec.Labels}}{{println $key}}{{end}}{{range $key, $value := .Spec.TaskTemplate.ContainerSpec.Labels}}{{println $key}}{{end}}' "$service")"
    if printf '%s\n' "$labels" | grep -qi '^traefik\.'; then exit 1; fi
    target="$(docker service inspect --format '{{range .Spec.TaskTemplate.Networks}}{{println .Target}}{{end}}' "$service")"
    case "$target" in ''|*[!0-9a-z]*) exit 1;; esac
    [ "${#target}" -eq 25 ]
    [ "$(docker network inspect --format '{{.Id}} {{.Name}} {{.Driver}} {{.Scope}}' "$target")" = "$target service_access_link overlay swarm" ]
    if [ -z "$overlay_id" ]; then overlay_id="$target"; else [ "$target" = "$overlay_id" ]; fi
  done
}
assert_task() {
  [ "$(docker ps --no-trunc --filter status=running --filter label=com.docker.swarm.service.name=swagger_swagger-nginx --format '{{.ID}}')" = "$container_id" ]
  [ "$(docker inspect --format '{{.Id}} {{index .Config.Labels "com.docker.swarm.service.name"}} {{.State.Running}}' "$container_id")" = "$container_id swagger_swagger-nginx true" ]
  mode="$(docker inspect --format '{{.HostConfig.NetworkMode}}' "$container_id")"
  case "$mode" in default|bridge|service_access_link|"$overlay_id") ;; *) exit 1;; esac
  [ "$(docker inspect --format '{{range $name, $network := .NetworkSettings.Networks}}{{println $name $network.NetworkID}}{{end}}' "$container_id")" = "service_access_link $overlay_id" ]
}
assert_internal
container_id="$(docker ps --no-trunc --filter status=running --filter label=com.docker.swarm.service.name=swagger_swagger-nginx --format '{{.ID}}')"
case "$container_id" in ''|*[!0-9a-f]*) exit 1;; esac
[ "${#container_id}" -eq 64 ]
assert_task
for url in http://127.0.0.1:8084/status http://tasks.swagger-ui:8080/ http://tasks.swagger-editor:8080/; do
  code="$(docker exec "$container_id" /usr/bin/curl --disable --noproxy '*' --proto '=http' --connect-timeout 2 --max-time 5 --max-redirs 0 --silent --show-error --output /dev/null --write-out '%{http_code}' "$url")"
  [ "$code" = '200' ]
done
assert_task
assert_internal
printf 'SWAGGER_INTERNAL_READY\n'
'''


def probe_internal_swagger(run_manager_shell: Callable[..., Any]) -> bool:
    result = run_manager_shell(SCRIPT, check=False, timeout_seconds=30, retry_safe=True)
    return result.returncode == 0 and result.stdout == 'SWAGGER_INTERNAL_READY\n'
