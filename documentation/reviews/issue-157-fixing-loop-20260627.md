# Fixing Loop: Issue #157 Traefik Access Model

Source: <https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/157>

Branch: `fix/issue-157-access-model-20260627`

## Loop Contract

Each loop iteration uses the current Issue #157 API body as the requirement
baseline:

1. Review requirements against repository evidence.
2. Record concrete findings.
3. Fix in-scope code, configuration, tests or documentation.
4. Run targeted checks.
5. Run the full `QUALITY.md` gate when code/config/test changes are present.
6. Attempt Sonar/SonarCloud only when scanner and token prerequisites exist.
7. Repeat until no repository-verifiable findings remain.

Live Docker, Swarm, DNS, hosts-file and browser execution remain out of scope
unless explicitly opted in by an operator.

## Iteration 1

Findings:

- Service compose source files still contained static Traefik route labels.
- Live post-install evidence used `.tiny-swarm-world/evidence/post_install_browser_live`
  instead of `.tiny-swarm-world/evidence/solid-typed-evidence/e2e`.

Fixes:

- Removed static `traefik.enable`, `traefik.swarm.network`,
  `traefik.http.routers.*` and `traefik.http.services.*` labels from service
  compose sources.
- Kept route label generation in the central compose renderer.
- Added a regression test that raw service compose sources stay renderer-owned.
- Changed post-install live evidence root to
  `.tiny-swarm-world/evidence/solid-typed-evidence/e2e`.

Verification:

- Targeted route/model/browser-static suite: passed.
- Full `python3 tools/quality_gate.py quality`: passed.

## Iteration 2

Findings:

- User-facing documentation still presented direct localhost ports as primary
  access in `documentation/user-handbook.adoc`.
- `documentation/Howto.adoc` listed obsolete direct ports such as `9000`,
  `8081`, `9001` and `8087`.
- `documentation/deployment/infisical-silent-setup.adoc` still used the old
  Infisical direct URL `http://localhost:8086`.
- Troubleshooting and configuration inventory docs still contained stale direct
  route examples.

Fixes:

- Updated user handbook and Howto docs to list preferred Traefik host routes.
- Reclassified direct localhost ports as diagnostic or compatibility access in
  user-facing docs.
- Updated Infisical silent setup documentation to the current direct diagnostic
  URL `http://localhost:17080` and preferred route `https://infisical.tsw.local`.
- Updated troubleshooting curl examples to preferred Traefik host routes.
- Updated Pulsar public admin URL inventory from old `8087` to current direct
  diagnostic `14080` with preferred `https://pulsar-api.tsw.local`.

Verification:

- Targeted documentation/route tests:
  `PYTHONPATH=src python3 -m unittest tests.architecture.test_legacy_surface_documentation tests.domain.ingress.test_desired_state tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml tests.integration.test_service_access_routing tests.live.browser_e2e_contract tests.live.test_post_install_browser_live`
- Result: passed.
- Drift search for old primary ports `9000`, `8081`, `8087` and old evidence
  path: no remaining source/documentation hits.
- `git diff --check`: passed.

## Sonar/SonarCloud

Sonar execution is not completed in this environment:

- `sonar-scanner` is not available in WSL.
- `SONAR_TOKEN` is not set.

No Sonar pass is claimed. Once scanner and token prerequisites are present, the
next loop step is to run the configured Sonar/SonarCloud analysis and repair any
reported in-scope findings without weakening tests or gates.

## Current Repository-Verifiable Status

- Preferred public Traefik ingress is `80/443`.
- `10080/10443` remain diagnostic fallback evidence, not preferred links.
- Service routes are generated from the effective access model.
- Service Access links prefer `https://*.tsw.local` host routes.
- Pulsar broker TCP is not generated as an HTTP route.
- Live Selenium structure is opt-in and records pass/fail/skip evidence under
  the Issue #157 evidence path.
- Remaining blocker: external Sonar/SonarCloud tooling is unavailable here.
