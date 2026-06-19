# Live Greenpath Not Run

## Reason

Live greenpath validation was not executed in this Codex run because it requires
live infrastructure mutations and host/service inspection commands. Root
`AGENTS.md` prohibits running LXD/Incus, Docker Swarm, compose deployments,
networking changes, service bootstrap scripts, or similar live infrastructure
operations unless the user explicitly approves live execution.

The workflow execution request authorizes repository workflow execution, but it
does not provide separate explicit approval to run the live platform mutation
commands in the current environment.

## Environment

- Repository: `Tiny-Swarm-World`
- Branch: `feature/replace-rabbitmq-with-apache-pulsar-20260616`
- Operating model: Linux/WSL-only project, current execution through WSL from a
  Windows host workspace.
- Live platform commands intentionally not run.

## Commands that would be run

```bash
sudo -v
./install.sh
docker service ls
docker stack ls
docker network ls
curl -f http://localhost:8087/admin/v2/clusters
docker run --rm --network tiny-swarm-world curlimages/curl:latest \
  curl -f http://pulsar:8080/admin/v2/clusters
nc -vz localhost 6650
```

Additional checks after deployment:

```bash
docker service ls | grep -i pulsar
docker service ls | grep -i rabbitmq && exit 1 || true
```

## Remaining risk

- The automated test and static contract gates passed, but the actual local
  platform greenpath has not been exercised in this run.
- Pulsar image pull, startup time, healthcheck behavior, and host port
  reachability still require live validation on a suitable Linux/LXD-native
  Docker Swarm host.
- Service-access dashboard behavior was validated by repository tests, not by a
  running browser against deployed services in this slice.

## Required manual validation

Run the commands above on an approved local Linux or WSL/LXD-native host with
explicit permission for live infrastructure changes. Validation is complete
only when:

- `./install.sh` completes successfully.
- A Pulsar service is deployed.
- No RabbitMQ service is deployed.
- Pulsar healthcheck is healthy.
- `http://localhost:8087/admin/v2/clusters` is reachable where exposed.
- Pulsar broker port `6650` accepts a TCP connection.
- Service-access/dashboard does not show RabbitMQ.
