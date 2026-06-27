# Review: Issue #157 Traefik Access Model

Source: <https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/157>

Branch: `fix/issue-157-access-model-20260627`

## Requirement Classification

- Functional requirement: route enabled HTTP services through Traefik hostnames.
- Architecture constraint: central access model is the source for routes, labels,
  Service Access links, health targets, skipped routes and evidence.
- Observability requirement: evidence includes route map, fallback classes,
  health targets and skipped-route reasons without sensitive values.
- Quality-gate requirement: static and mocked checks remain default; live
  Selenium E2E remains opt-in.
- Security requirement: Service Access displays credential references only, not
  password, token or secret values.

## Defect Review

| Severity | Finding | Current status |
|---|---|---|
| Blocker | Requested `feature/feature/...` branch was not present remotely. | Mitigated by creating `fix/issue-157-access-model-20260627` from clean `main`; `git ls-remote` did not show either referenced workflow branch. |
| Blocker | Central access model was required as source of truth. | Addressed in current baseline through `DesiredHttpsIngress` from `ports.yaml`, profile membership and fallback/skipped-route evidence. |
| Blocker | Traefik routes were statically maintained in service compose files. | Fixed in this branch: service compose sources no longer contain `traefik.http.*`, `traefik.enable` or `traefik.swarm.network` labels; labels are renderer-owned. |
| Blocker | Service-oriented route tests were incomplete. | Addressed in current baseline by per-service integration tests for Service Access, Portainer, Jenkins, SonarQube, Nexus, Swagger, Infisical and Pulsar routes. |
| Blocker | Live E2E needed Selenium imports and browser flows. | Addressed in current baseline by `tests/live/browser_e2e_contract.py` using `from selenium import webdriver` and `from selenium.webdriver.common.by import By`; live execution remains opt-in. |
| High | Evidence path differed from Issue #157 target. | Fixed in this branch: post-install live evidence now uses `.tiny-swarm-world/evidence/solid-typed-evidence/e2e`. |
| High | Evidence was test-local instead of product/model output. | Addressed by `DesiredHttpsIngress.to_dict()` evidence, consumed by routing tests and dashboard rendering. |
| High | Skipped-routes model was missing. | Addressed in current baseline by `SkippedRoute` and evidence entries such as `service_not_enabled`. |
| High | Health-check expectations needed route model support. | Addressed in current baseline by `health_check_targets` in the effective access model. |
| High | Prometheus/Grafana/App/API needed complete route candidates. | Addressed as conditional route candidates from `ports.yaml`; skipped when not enabled/configured. |
| High | `pulsar-api` needed explicit HTTP endpoint modelling. | Addressed as `pulsar-admin-api` route with `pulsar-api.tsw.local` and upstream port `8080`; broker TCP is not routed as HTTP. |
| High | Infisical route included ``Host(`localhost`)``. | Fixed by renderer-owned labels and regression checks rejecting localhost fallback host labels. |
| Medium | Service Access dashboard was static. | Addressed in current baseline by `render_service_access_dashboard_html()` from the effective model; compose mounts generated dashboard config. |
| Medium | Fallback classification was inconsistent. | Addressed by diagnostic fallback evidence from `PortRegistry` exposure classes. |
| Medium | Direct published ports remained unclassified in compose. | Addressed by `services.yml`/`ports.yaml` classification and compose published-port registry alignment tests. |
| Medium | User-facing docs still showed direct localhost ports as primary routes. | Fixed in the second loop by updating user handbook, Howto, troubleshooting, network and Infisical setup docs to prefer Traefik host routes and classify direct ports as diagnostic/compatibility access. |
| Medium | Route rendering was not profile-driven enough. | Addressed by profile contracts plus route definitions and conditional services. |
| Medium | RabbitMQ/legacy messaging must not be generated. | Covered by unsupported/skipped route evidence and absence from route candidates. |
| Medium | 80/443 preflight blockers must remain explicit. | Addressed by setup manifest and Traefik public ingress tests for required ports 80 and 443. |
| Low | Traefik insecure API mode needed broader protection. | Addressed by desired-state validation and Traefik compose tests forbidding `--api.insecure=true`. |

## Current Loop Result

- Targeted route/model/browser-static tests pass.
- Full `QUALITY.md` gate passes:
  `python3 tools/quality_gate.py quality`.
- Second static review confirms service compose sources no longer contain
  static `traefik.enable`, `traefik.swarm.network`, `traefik.http.routers.*`,
  `traefik.http.services.*` or ``Host(`localhost`)`` route labels.
- Fixing loop evidence is recorded in
  `documentation/reviews/issue-157-fixing-loop-20260627.md`.
- Sonar/SonarCloud execution is blocked in this environment because
  `sonar-scanner` is not available in WSL and `SONAR_TOKEN` is not set.
  No Sonar result is claimed.
