# Live Greenpath Repair Report

Status: stopped

Date: 2026-06-06
Branch: `feature/live-greenpath-repair-loop-20260606`
Final evidence directory: `.tiny-swarm-world/evidence/installation-tests/wsl2/20260606T220100Z`
Final state snapshot: `.tiny-swarm-world/evidence/final-state-20260606T222241Z.txt`

## Stop Reason

The controlled repair loop stopped before a complete greenpath because the final live run failed at `deployment verify` for `deployment:swagger-service-readiness`.

Classification: `deployment_verify_failed`

Observed evidence:

- `swagger_swagger-api`: `0/1`, rejected with `No such image: danielgtaylor/apisprout:latest`
- `swagger_swagger-editor`: `0/1`, rejected with `No such image: docker.swagger.io/swaggerapi/swagger-editor:latest@sha256:...`
- `swagger_swagger-ui`: `0/1`, rejected with `No such image: docker.swagger.io/swaggerapi/swagger-ui:latest@sha256:...`
- `swagger_swagger-nginx`: `0/1`, rejected with `No such image: nginx:mainline-alpine`
- Manual pull diagnostic on `swarm-manager` returned Docker registry rate limiting: `You have reached your unauthenticated pull rate limit.`
- No cached Swagger images were present on the WSL host, on `swarm-manager`, or in the local Nexus registry.

This requires external registry quota recovery or authenticated image access. The workflow stopped under the guard: stop if a blocker would require manual secrets or unknown external host changes. No safety guard was bypassed.

## Final Live Run

Command:

```bash
printf '%s\n' RESET_TINY_SWARM_PLATFORM | ./install.sh
```

Evidence:

- Reset log: `.tiny-swarm-world/evidence/installation-tests/wsl2/20260606T220100Z/reset-run.log`
- Setup log: `.tiny-swarm-world/evidence/installation-tests/wsl2/20260606T220100Z/setup-run.log`
- Wrapper log: `.tiny-swarm-world/evidence/install-run-20260606T220100Z.log`

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

## Runtime State At Stop

Observed from `.tiny-swarm-world/evidence/final-state-20260606T222241Z.txt`:

- Docker Swarm exists with `swarm-manager` as leader.
- Stacks registered: `portainer`, `nexus`, `jenkins`, `rabbitmq`, `sonarqube`, `swagger`, `service-access`.
- Running service groups: Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, Service Access.
- Blocked service group: Swagger, all four services rejected due missing external images after Docker Hub rate limit.

## Repairs Applied

1. `e8dff6b fix: prevent install consent pipe hang`
   - Blocker: install wrapper hung after piping consent because `sleep 86400` kept stdin open.
   - Fix: make the recorded command pipe finite.
   - Tests: `PYTHONPATH=src python3 -m unittest tests.test_install_script`; full test gate.

2. `92b9177 test: select latest install evidence deterministically`
   - Blocker: debugger test selected latest evidence by mtime, unstable with live evidence.
   - Fix: select latest evidence directory by timestamped name.
   - Tests: full test gate.

3. `e735a09 fix: use bearer-only Portainer API requests`
   - Blocker: `deployment:portainer-local-endpoint` failed with Portainer CSRF rejection.
   - Fix: clear session cookies after JWT auth so API calls use bearer auth only.
   - Tests: Portainer client tests; full test gate.

4. `ebdd5f2 fix: align local registry image endpoint`
   - Blocker: Jenkins service rejected `swarm-manager:5000/jenkins:latest` as unavailable.
   - Fix: use provider-safe local registry endpoint `127.0.0.1:5000` consistently.
   - Tests: composition/config tests; full test gate.

5. `cd5d398 fix: prepare swagger stack bind assets`
   - Blocker: Swagger services rejected missing bind sources under `/var/lib/tiny-swarm-world/stacks`.
   - Fix: prepare stack assets before Portainer deployment through the LXC Swarm runtime.
   - Tests: LXC runtime and composition tests; full test gate.

6. `e83d752 fix: route local nginx upstreams via swarm tasks`
   - Blocker: Swagger and service-access NGINX upstreams used VIPs that refused connections in the LXC Swarm path.
   - Fix: route NGINX upstreams through `tasks.*` DNS names.
   - Tests: architecture/config assertions; full test gate.

7. `3f9d4f5 fix: wait for sonarqube database readiness`
   - Blocker: SonarQube started before PostgreSQL was accepting TCP connections and exited repeatedly.
   - Fix: add an idempotent TCP readiness wait before SonarQube entrypoint.
   - Tests: compose config regression; full test gate.

8. `908b82a fix: route sonarqube database via swarm tasks`
   - Blocker: SonarQube DB wait and JDBC URL used the service VIP, which refused connections in this LXC Swarm path.
   - Fix: use `tasks.sonar_db` for wait and JDBC URL.
   - Tests: compose config regression; full test gate.

9. `319d7d0 fix: retry transient platform verify preflight`
   - Blocker: final platform verify could run before expected-service detection settled, then pass moments later.
   - Fix: add a bounded retry window only for non-mutating `platform:preflight` verification failures.
   - Tests: platform workflow retry regression, composition tests, full test gate.

## Quality Evidence

For each repair commit, targeted tests were run before the full test gate. The latest full test gate before the final live run was:

```bash
python3 tools/quality_gate.py test && git diff --check
```

Result: 681 tests passed. `git diff --check` reported only existing CRLF conversion warnings and no whitespace errors.

## Acceptance Criteria Status

Not met:

- A fresh reset followed by `./install.sh` did not complete successfully.
- Swagger services did not reach `1/1` because required public images could not be pulled after Docker Hub unauthenticated rate limiting.
- Final platform verify did not run in the last install because deployment verify stopped first.

Partially met:

- Managed LXC/LXD platform initialized and reconciled.
- Docker Swarm initialized with `swarm-manager` as leader during the final run.
- Stacks were registered for all expected stack names.
- Non-Swagger services reached desired replicas during the final run.

## Required Follow-Up

Provide a safe external image source before retrying the live greenpath:

1. Authenticate Docker pulls on the LXC manager and workers using approved local credentials, then rerun `./install.sh`.
2. Preload and publish the Swagger images into the local Nexus registry using an approved, documented image-source workflow.
3. Replace Swagger image references with provider configuration pointing to an approved internal registry mirror.

Do not commit registry credentials or bypass preflight/deployment validations.
