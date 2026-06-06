# Senior System Architect Findings

## Boundary Review

The target belongs to the Deployment boundary:

* Application service: `EnsurePortainerEndpoint`.
* Application port: `PortPortainerClient`.
* Infrastructure adapter: `PortainerHttpClient`.
* Runtime wiring: `composition.py`.

Domain modules must not receive HTTP, Portainer, Docker, LXC, logging, or
request dependencies.

## Endpoint Model

Creation-time evidence:

* `infra/config/compose/portainer/docker-compose.yml` mounts
  `/var/run/docker.sock` into the Portainer server.
* The same compose file also deploys `portainer/agent:2.39.2`.
* Documentation currently says deployment bootstrap registers the local Docker
  endpoint named `local`.

Architecture decision for this workflow:

```text
The current authoritative endpoint model is the socket-backed local Docker endpoint.
```

The agent remains deployed for compatibility and Swarm/agent behavior, but it is
not the endpoint registration target unless Slice 02 verifies that Portainer
2.39.x requires a different contract.

## Architecture Risks

* A typed diagnostic exception is acceptable if it remains an application-port or
  infrastructure-adapter contract and does not pull HTTP details into domain.
* Documentation must not claim live setup success from endpoint registration
  alone.
* Arc42 updates should wait until implementation evidence exists.

## Decision

No architecture blocker for workflow execution.
