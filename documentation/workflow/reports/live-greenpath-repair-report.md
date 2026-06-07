# Live Greenpath Repair Report

Status: stopped

Date: 2026-06-07
Branch: `feature/live-greenpath-repair-loop-20260606`
Latest evidence directory: `.tiny-swarm-world/evidence/installation-tests/wsl2/20260607T005001Z`
Latest reset exit: `0`
Latest setup exit: `1`

## Stop Reason

The controlled repair loop stopped before a complete greenpath because the latest live run failed at `deployment verify` for `deployment:swagger-service-readiness`.

Classification: `deployment_verify_failed`

Precise blocker:

- Phase: `deployment verify`
- Target: `deployment:swagger-service-readiness`
- Stack: `swagger`
- Failed services: `swagger-editor`, `swagger-ui`
- Observed replicas after 60 attempts: `swagger-api=1/1,swagger-editor=0/1,swagger-nginx=1/1,swagger-ui=0/1`
- Runtime error from Swarm task history: `No such image: docker.swagger.io/swaggerapi/swagger-editor:latest` and `No such image: docker.swagger.io/swaggerapi/swagger-ui:latest`

This is not safely repairable by bypassing readiness verification or replacing the stack with a placeholder. It requires an approved external image source, authenticated registry access, or documented provider configuration for a reachable mirror/cache. The workflow stopped under the guard: stop if a blocker would require manual secrets or unknown destructive host changes.

## Latest Live Run

Command:

```bash
printf '%s\n' RESET_TINY_SWARM_PLATFORM | ./install.sh
```

Evidence:

- Reset log: `.tiny-swarm-world/evidence/installation-tests/wsl2/20260607T005001Z/reset-run.log`
- Setup log: `.tiny-swarm-world/evidence/installation-tests/wsl2/20260607T005001Z/setup-run.log`
- Context: `.tiny-swarm-world/evidence/installation-tests/wsl2/20260607T005001Z/context.txt`

Result:

- `preflight`: passed
- `platform init`: completed
- `platform reconcile`: completed
- `platform expose`: completed
- `deployment bootstrap`: completed
- `artifacts prepare`: completed
- `artifacts verify`: completed
- `deployment apply`: completed
- `deployment verify`: failed_to_verify
- `platform verify`: not_run

Final setup status: `failed_to_verify`

## Runtime State At Stop

Live diagnostic commands showed:

- LXD instances exist and are running: `swarm-manager`, `swarm-worker-1`, `swarm-worker-2`.
- Docker Swarm manager exists: `swarm-manager` is `Leader`.
- Docker Swarm worker membership is not complete: `docker node ls` reported only the manager.
- Worker Docker Swarm states are `inactive` on `swarm-worker-1` and `swarm-worker-2`.
- Expected stacks are registered: `portainer`, `nexus`, `jenkins`, `rabbitmq`, `sonarqube`, `swagger`, `service-access`.
- Non-Swagger services reached desired replicas in the latest setup evidence.
- `swagger_swagger-editor` and `swagger_swagger-ui` continuously rejected because their public images were unavailable to the Swarm node.

The worker membership gap is an additional acceptance blocker classified as `swarm_join_failed`, but it was not the first blocker in the latest setup evidence because the setup stopped earlier at `deployment verify`.

## Repairs Applied On This Branch

Existing repair commits already present on the workflow branch:

1. `e8dff6b fix: prevent install consent pipe hang`
2. `92b9177 test: select latest install evidence deterministically`
3. `e735a09 fix: use bearer-only Portainer API requests`
4. `ebdd5f2 fix: align local registry image endpoint`
5. `cd5d398 fix: prepare swagger stack bind assets`
6. `e83d752 fix: route local nginx upstreams via swarm tasks`
7. `3f9d4f5 fix: wait for sonarqube database readiness`
8. `908b82a fix: route sonarqube database via swarm tasks`
9. `319d7d0 fix: retry transient platform verify preflight`
10. `a4a755a feat: implement WSL port forwarding and Docker registry mirroring capabilities`

No new blocker fix was committed for the latest run because the first current blocker requires approved external image access or provider mirror configuration, not a code change that can be made safely inside the repository.

## Quality Evidence

Command:

```bash
python3 tools/quality_gate.py test
```

Result: `694` tests passed.

Git state before report update was clean. Raw local evidence remains under `.tiny-swarm-world/evidence` and is not committed.

## Acceptance Criteria Status

Not met:

- A fresh reset followed by `./install.sh` did not complete successfully.
- Docker Swarm does not currently contain one manager and two workers.
- Swagger deployment verification did not pass because two public Swagger images were unavailable to the Swarm node.
- Final `platform verify` did not run because setup stopped at `deployment verify`.

Met or partially met:

- Fresh reset succeeded.
- All three LXD instances exist and are running.
- Expected stacks are registered.
- Non-Swagger services reached desired replicas in the latest run.
- Final evidence exists under `.tiny-swarm-world/evidence/installation-tests/wsl2/20260607T005001Z`.

## Required Follow-Up

Choose one approved image-source path before rerunning the live greenpath:

1. Configure authenticated Docker/Swagger registry access for the LXC nodes without committing credentials.
2. Configure `TSW_LXC_DOCKER_REGISTRY_MIRROR` to a reachable, approved local mirror/cache and ensure Swagger images are available there.
3. Replace Swagger image references only with documented provider configuration pointing to an approved internal registry source.

After the image-source blocker is resolved, rerun `./install.sh`. If deployment verify passes, the next blocker to repair is expected to be worker join verification (`swarm_join_failed`) unless the rerun joins both workers successfully.
