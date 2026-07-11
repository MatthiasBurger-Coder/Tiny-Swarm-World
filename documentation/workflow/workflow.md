# Workflow: Issue #157 Final Routing Gaps

Version: `workflow-issue-157-final-gaps-v1.0.0`
Workflow ID: `workflow-issue-157-final-gaps-20260711`
Created: `2026-07-11`
Issue: `#157 Gateway: Route HTTP services through Traefik using central access configuration`
Issue URL: <https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/157>
Baseline Branch: `main`
Baseline Commit: `3e0d28db0e59fc3f38929c4b91cac0566ed39fb6`
Branch: `fix/issue-157-final-gaps-20260711`
Status: `AUTHORED_PUBLISHED_PENDING_EXECUTION`
Execution Profile: `FULL_PATH`
Workflow Evidence Root: `.codex/evidence/workflow-issue-157-final-gaps-20260711/`
Issue Evidence Root: `.tiny-swarm/evidence/issue-157-final-gaps-20260711/`
Product Routing Evidence Root:
`.tiny-swarm-world/evidence/solid-typed-evidence/routing/`

## Executive Summary

Close only the repository-verifiable gaps that remain for GitHub Issue #157.
Preserve the implemented Traefik `80/443` ingress, internal upstream ports,
routed `*.tsw.local` Service Access links, effective-model dashboard rendering,
pre-deploy dashboard asset transfer, opt-in Selenium behavior, per-route E2E
evidence, explicit skip evidence, and the Apache Pulsar-only messaging model.

The workflow adds a productive, redacted effective-access-model evidence use
case; proves enabled Prometheus, Grafana, app and API routes with isolated YAML
fixtures; derives browser expectations and suite completion from the effective
model; and makes renderer output the dashboard-test source of truth.

This authoring run does not implement product behavior and does not run live
Incus, LXC, Docker, Swarm, DNS, Traefik, browser or service operations.

## Verified Baseline

- Public `main` was fetched read-only over HTTPS and resolved to
  `3e0d28db0e59fc3f38929c4b91cac0566ed39fb6`.
- `origin/main`, `public/main` and the starting commit were identical.
- The original worktree contained unrelated user-owned WSL bridge changes.
  Workflow authoring therefore uses a dedicated isolated worktree. Its
  host-specific absolute path is intentionally not persisted.
- The active branch is `fix/issue-157-final-gaps-20260711` and its local ref
  was verified before workflow files were regenerated.
- The requested branch did not exist locally or on the public remote at
  authoring time.
- The previous active workflow was
  `workflow-service-access-dashboard-html-20260629`. It was already executed
  locally and is unrelated to these final gaps. This request explicitly
  replaces it.
- No `documentation/epics/` directory exists. The complete GitHub issue and
  the user's explicit final-gap refinement are the requirement authority.
- `.gitignore` ignores both `/.tiny-swarm-world/` and `/.tiny-swarm/`.

Baseline command:

```bash
PYTHONPATH=src python3 -m unittest \
  tests.domain.ingress.test_desired_state \
  tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml \
  tests.integration.test_service_access_routing \
  tests.integration.test_observability_routing \
  tests.integration.test_tiny_swarm_app_routing \
  tests.live.browser_e2e_contract \
  tests.live.test_post_install_browser_live.StaticPostInstallLiveSuiteTest
```

Baseline result: `PASS`, 77 tests, no live infrastructure.

Verified open gaps:

1. `DesiredHttpsIngress.to_dict()` produces the model, but no productive use
   case persists `effective-access-model.json`.
2. The compose renderer maps one route per upstream service. Enabled `app` and
   `api` both target `tiny-swarm`, so simultaneous labels currently collide.
3. Enabled conditional routes are rendered but can also be reported as
   `service_not_in_active_profile`, producing contradictory skip semantics.
4. Browser suite completion is based on static `ROUTE_EXPECTATIONS` and turns
   missing route evidence into a skipped route result.
5. Several dashboard and post-install static tests still parse the committed
   HTML instead of renderer output or the effective model.

## Execution Profile

```text
executionProfile=FULL_PATH
reason=The workflow affects runtime evidence persistence, application ports,
       infrastructure adapters, deployment pre-apply wiring, route rendering,
       browser evidence semantics, tests, documentation and PR publication.
requiredFullReviews=Senior Requirement Engineer, Senior System Architect,
                    Senior Python Automation Developer, Senior Tester,
                    Senior DevOps Engineer, Senior Documentation Engineer,
                    security/evidence review, Issue Completion Auditor
allowedImpactChecks=Console/status UI N/A; React frontend N/A; API/database N/A
requiredQualityChecks=all commands from QUALITY.md plus git diff --check
stopConditions=unresolved source-of-truth, evidence-safety, lock, branch,
               quality-authority or publication ambiguity
```

## Requirement Clarification Gate

### Original Request

Create a complete, directly executable Codex workflow from `main` on
`fix/issue-157-final-gaps-20260711` that closes only the remaining requirements
of Issue #157, executes all repository quality gates, records the required
evidence, publishes implementation through a pull request, checks CI and
SonarCloud, and resolves in-scope findings in the same branch.

### Interpreted Intent

Retain the central effective access model and close four narrow gaps:
productive routing evidence, positive optional-route proof, dynamic browser
expectations, and renderer-centric dashboard tests.

### Change Type

Python domain/application/port/adapter changes, deployment pre-apply
integration, deterministic evidence persistence, static/live-test contract
changes, documentation synchronization and guarded publication.

### Affected Process Strand

`workflow create -> workflow execute -> issue completion audit -> PR readiness`

### Affected Architecture Area

- ingress desired state;
- compose/config repository adapter;
- application evidence use case and ports;
- local evidence persistence adapter;
- deployment composition and pre-apply sequence;
- integration, live-contract and dashboard tests;
- arc42 runtime/deployment/quality documentation.

### Explicit Requirements

- Persist a redacted effective access model productively under the exact
  routing evidence path.
- Cover enabled Prometheus, Grafana, app and API routes with temporary
  `services.yml` and `ports.yaml` fixtures.
- Derive browser expectations and suite summary from current
  `service_access_links`.
- Test dashboard renderer output for default and optional configurations.
- Run every requested local quality command, then publish implementation and
  validate the pull request.

### Implicit Requirements

- Do not duplicate route sources or load credentials from environment
  variables for routing evidence.
- Fail closed before stack deployment if safe atomic evidence persistence
  fails.
- Preserve setup phase order and all live-consent boundaries.
- Keep the default quality gate static and infrastructure-free.
- Record missing live prerequisites as skip evidence without claiming a live
  pass.

### Assumptions

- Routing evidence `result: generated` means the model was safely serialized;
  it is not a service-readiness or reachability claim.
- `generated_at` is a UTC ISO-8601 value supplied through an injectable clock;
  list ordering and JSON keys remain deterministic around that timestamp.
- Enabled conditional services are active route extensions even when they are
  not static members of `ServiceStackProfile.SERVICE_ACCESS`; they must not be
  simultaneously emitted as skipped.
- The referenced ignored `live-installation.env` file is not authoring input
  and does not itself grant live-test or live-infrastructure consent.
- The later Traefik ADR supersedes the older NGINX-only routing baseline for
  this scope. ADR history remains unchanged.

### Non-Goals

- Incus/LXC installation or node lifecycle.
- Docker installation, Swarm bootstrap or setup phase reordering.
- Issue #156 direct published-port redesign.
- Kubernetes implementation or Kubernetes-first behavior.
- DNS, hosts-file or resolver mutation.
- TLS/certificate lifecycle changes.
- Messaging architecture, RabbitMQ or unsupported legacy messaging.
- Infisical bootstrap or credential-value handling changes.
- Browser selector redesign beyond what dynamic route discovery requires.
- General Service Access redesign or opportunistic refactoring.

### Risks

- A generic mapping serializer could persist untrusted secret-like fields.
- A second route builder could drift from compose/dashboard/health behavior.
- Multiple routes sharing one upstream service can overwrite labels.
- Stale per-route E2E files can make disabled routes appear expected.
- A `missing` route can be accidentally normalized to `skipped` or success.
- Committed HTML can conceal renderer drift.
- Parallel streams can conflict on `compose_file_repository_yaml.py` or shared
  test helpers unless Slice 01 completes first.

### Open Questions

- None blocking.

### Blocking Questions

- None.

### Confidence Level

- 97 percent.

### Decision

- `READY_FOR_WORKFLOW`

## Four-Role Three Amigos Gate

Requirement Lead:

- The complete issue, the user's preservation list, all four final-gap groups,
  18 minimum tests, evidence files, lifecycle requirements, non-goals and stop
  rules are represented below.
- No requirement is silently deferred. Live execution is conditional by
  requirement, not omitted.
- The lack of a repository EPIC is a traceability gap, not a blocker, because
  the issue and user refinement are explicit requirement sources.

System Architect:

- Keep `DesiredHttpsIngress` I/O-free.
- Expose the already-computed effective model through an application port
  implemented by the existing compose/config repository adapter.
- Add an application evidence use case and a dedicated routing-evidence
  persistence port plus local infrastructure adapter.
- Reuse the same effective model method for compose labels, dashboard, health
  targets, evidence and browser expectations.
- Wire the evidence use case in `infrastructure/composition.py` as a deployment
  pre-apply step without changing setup phase order.
- Group routes per upstream service so app and API labels can coexist.
- No new ADR is required; current Traefik, setup-safety and live-consent ADRs
  already govern the change.

Senior Python Automation Developer:

- Use typed model objects and fixed allowlisted evidence projections.
- Do not inspect process credentials or serialize arbitrary mappings.
- Inject the clock and evidence repository for deterministic unit tests.
- Perform atomic replacement in the infrastructure adapter, create parents,
  set private local permissions, and clean temporary files on failure.
- Load optional route configuration only from isolated structured YAML
  fixtures through existing repositories.

Test Lead:

- Use regression-first changes inside each implementation slice.
- Prove all four optional routes in positive and negative states.
- Test shared-upstream app/API labels together.
- Test pure deterministic browser-summary generation with missing precedence.
- Use renderer output for dashboard assertions and retain one explicit
  committed-default drift test.
- Keep Selenium opt-in and exercise skip paths without requiring a browser.

Dependency / Deadlock Validator:

- The graph is acyclic.
- Slice 01 owns the shared model/renderer seam and must finish first.
- Slices 02, 03 and 04 have disjoint write scopes after Slice 01 and may run
  in isolated worktrees.
- Live validation and final publication are serialized.

Gate evidence:
`.codex/evidence/workflow-issue-157-final-gaps-20260711/three-amigos-gate.md`.

## Requirement Matrix

| ID | Requirement | Type | Likely implementation | Verification | Initial status |
|---|---|---|---|---|---|
| BASE-001 | Preserve Traefik as preferred public ingress on 80/443. | Functional / architecture | No redesign; regression tests | Existing and final core-route tests | BASELINE_VERIFIED |
| BASE-002 | Preserve internal container target ports behind routes. | Functional | Compose renderer | Core and optional route assertions | BASELINE_VERIFIED |
| BASE-003 | Preserve routed `https://*.tsw.local` Service Access links without high ports. | UX / functional | Effective model | Link and dashboard tests | BASELINE_VERIFIED |
| BASE-004 | Preserve dashboard rendering from the effective model. | Architecture | Compose repository renderer | Renderer and drift tests | BASELINE_VERIFIED |
| BASE-005 | Preserve pre-deploy dashboard transfer to the manager. | Deployment | Existing LXC runtime/composition | Existing runtime/composition tests | BASELINE_VERIFIED |
| BASE-006 | Keep Selenium live checks opt-in. | Safety | Browser test contract | Static skip tests; optional live evidence | BASELINE_VERIFIED |
| BASE-007 | Preserve per-route E2E evidence and suite summary. | Evidence | Browser evidence contract | Browser static tests | BASELINE_VERIFIED |
| BASE-008 | Preserve explicit skip evidence for consent, Selenium and credential prerequisites. | Evidence / safety | Browser evidence contract | Skip-path tests | BASELINE_VERIFIED |
| BASE-009 | Exclude RabbitMQ and unsupported legacy messaging. | Scope / architecture | No messaging change | Route/config drift search | BASELINE_VERIFIED |
| EVD-001 | Add a productive application/runtime use case for effective access evidence. | Functional | New deployment application service | Unit and composition integration tests | OPEN |
| EVD-002 | Write `effective-access-model.json` under the exact routing evidence root. | Functional / storage | Dedicated local evidence adapter | Temporary-directory adapter test | OPEN |
| EVD-003 | Include every required top-level evidence field. | Evidence contract | Fixed evidence projection | Exact schema assertion | OPEN |
| EVD-004 | Include the selected service profile and distinguish model generation from live readiness. | Evidence integrity | Evidence use case | `service_profile` and `result` assertions | OPEN |
| EVD-005 | Persist no passwords, tokens, secret values, private keys or environment credentials. | Security | Allowlisted projection; no env input | Sentinel and forbidden-fragment tests | OPEN |
| EVD-006 | Persist only credential labels and Infisical item references. | Security | Credential projection | Exact credential shape assertion | OPEN |
| EVD-007 | Sort routes, skips and other list output deterministically. | Non-functional | Evidence builder | Permuted-input equality test | OPEN |
| EVD-008 | Create parents and replace the JSON atomically, preserving an old target on failure. | Resilience / storage | Infrastructure adapter | Replace and failure-cleanup tests | OPEN |
| EVD-009 | Integrate evidence writing before actual deployment stack apply without changing phase order. | Runtime / deployment | Composition pre-apply step | Composition and deployment workflow tests | OPEN |
| EVD-010 | Keep routing and issue evidence under ignored local trees. | Security / repository | Existing `.gitignore` | `git check-ignore` and test assertion | OPEN |
| OPT-001 | Generate a positive Prometheus route only when enabled. | Functional | Effective model/compose renderer | Isolated YAML fixture test | OPEN |
| OPT-002 | Generate a positive Grafana route only when enabled. | Functional | Effective model/compose renderer | Isolated YAML fixture test | OPEN |
| OPT-003 | Generate a positive app route only when configured. | Functional | Effective model/compose renderer | Isolated YAML fixture test | OPEN |
| OPT-004 | Generate a positive API route only when configured. | Functional | Effective model/compose renderer | Isolated YAML fixture test | OPEN |
| OPT-005 | Render correct host, upstream service, internal port, Traefik enable/network, websecure and TLS labels for every optional route. | Functional | Compose renderer | Per-route label assertions | OPEN |
| OPT-006 | Support app and API simultaneously when they share the `tiny-swarm` upstream. | Functional / regression | Group routes by upstream | Shared-upstream compose test | OPEN |
| OPT-007 | Use routed HTTPS links and effective-model health targets for enabled optionals. | Functional | Effective model | Link/health assertions | OPEN |
| OPT-008 | Report disabled optionals as `service_not_enabled` and do not report active routes as skipped. | Evidence semantics | Domain skip calculation | Positive/negative model tests | OPEN |
| OPT-009 | Use temporary `services.yml`, `ports.yaml` and compose fixtures without changing repository config. | Test isolation | Test support fixture | Path and post-test integrity assertions | OPEN |
| E2E-001 | Derive browser expectations from current effective-model `service_access_links`. | Test architecture | Browser contract helper | Dynamic-expectation test | OPEN |
| E2E-002 | Include every generated routed URL, including enabled optionals. | Functional test contract | Dynamic expectation matrix | Optional fixture test | OPEN |
| E2E-003 | Exclude disabled or non-applicable routes from expected failures. | Evidence semantics | Expected-set-driven summary | Disabled/stale evidence test | OPEN |
| E2E-004 | Give every expected route exactly one of passed, failed, skipped or missing. | Evidence contract | Pure summary builder | Matrix partition assertion | OPEN |
| E2E-005 | Record absent evidence as `missing`, never as success or a skipped route result. | Evidence integrity | Summary builder | Missing regression test | OPEN |
| E2E-006 | Make final suite status and ordering deterministic. | Non-functional | Sorted expected-set evaluation | Permuted-file/order test | OPEN |
| E2E-007 | Preserve service-specific login checks without making them the route source of truth. | Scope / regression | Existing login maps | Existing login contract tests | OPEN |
| E2E-008 | Keep browser, DNS, Traefik and Docker out of standard quality gates. | Safety / quality | Opt-in guards | Static test run and skip evidence | OPEN |
| DASH-001 | Test `render_service_access_dashboard()` output as the primary source. | Test architecture | Dashboard tests | Default renderer test | OPEN |
| DASH-002 | Show optional links only for enabled services. | Functional | Renderer + effective model | Optional fixture dashboard test | OPEN |
| DASH-003 | Exclude 10080/10443 from preferred dashboard links. | UX / regression | Renderer | Parsed URL assertion | OPEN |
| DASH-004 | Render no password values while retaining labels and Infisical references. | Security / UX | Renderer | Sentinel and reference assertions | OPEN |
| DASH-005 | Match rendered row count to `service_access_links` count. | Functional | Renderer | HTML row parser assertion | OPEN |
| DASH-006 | Keep committed HTML only as fallback/build material and add default-profile drift proof. | Documentation / regression | Explicit drift test | committed == renderer | OPEN |
| ARC-001 | Preserve inward hexagonal dependencies and keep domain free of I/O. | Architecture | Ports/application/adapter split | arch-lint and arch-tests | OPEN |
| ARC-002 | Add no global singleton or product dependency on test modules. | Architecture | Composition-local wiring | Static review and import tests | OPEN |
| ARC-003 | Keep one effective access model as source for labels, links, health, evidence and E2E. | Architecture | Public effective-model port method | Cross-consumer tests | OPEN |
| ARC-004 | Keep setup phase order, provider, direct-port, DNS, TLS, messaging and Infisical behavior unchanged. | Scope constraint | No changes outside allowed files | Diff and regression review | OPEN |
| TST-001 | Cover productive writer, redaction, sorting, atomicity and runtime integration. | Quality | Slices 02 and 05 | Named unit/integration tests | OPEN |
| TST-002 | Cover four positive optionals and disabled optionals. | Quality | Slice 01 | Named integration tests | OPEN |
| TST-003 | Cover dynamic expectations, optional summary and missing failure. | Quality | Slice 04 | Browser static tests | OPEN |
| TST-004 | Cover default/optional renderer, secret safety, no high ports and core routes. | Quality | Slices 03 and 05 | Dashboard/core regression tests | OPEN |
| GOV-001 | Create the required Three Amigos, plan, file, test, quality, routing, browser and final-status evidence. | Governance | Workflow evidence root | Evidence file audit | OPEN |
| GOV-002 | Maintain issue-level matrix, implementation, changed files, tests, risks and acceptance evidence. | Governance | Issue evidence root | Issue Completion Auditor | OPEN |
| GOV-003 | Run lint, arch-lint, arch-tests, typecheck, test and quality exactly as requested. | Quality gate | WSL/Linux | Recorded command results | OPEN |
| GOV-004 | Commit and push only slice-scoped changes, then create a PR against `main`. | Release | Git workflow | Branch/commit/PR evidence | OPEN |
| GOV-005 | Inspect required CI and SonarCloud results and repair in-scope failures. | CI / quality | PR fixing loop | Check URLs/status evidence | OPEN |
| GOV-006 | Resolve actionable review comments in the same branch. | Review | PR fixing loop | Thread disposition evidence | OPEN |
| GOV-007 | Require independent issue-completion audit before DONE. | Governance | Auditor handoff | PASS decision | OPEN |
| LIVE-001 | Run live Selenium only with explicit consent and all prerequisites. | Safety | Optional serialized validation | Consent/prerequisite record | OPEN |
| LIVE-002 | Record missing live prerequisites as skip evidence and do not block static gates. | Evidence / quality | Browser evidence contract | Skip-path tests/evidence | OPEN |
| LIVE-003 | Never read or publish raw `live-installation.env` content. | Security | Workflow restriction | Diff and evidence review | OPEN |

Implementation may not start until the same IDs are copied into
`.tiny-swarm/evidence/issue-157-final-gaps-20260711/requirement_matrix.md`.
No ID may be silently dropped, merged away or marked complete without both
implementation and verification evidence.

## Minimum Test Mapping

| Requested test | Requirement IDs | Planned verification |
|---|---|---|
| 1. productive writer | EVD-001..EVD-004 | application use-case test |
| 2. redacted evidence | EVD-005..EVD-006 | forbidden sentinel test |
| 3. deterministic sorting | EVD-007 | permuted-input equality |
| 4. atomic write | EVD-008 | adapter replace/failure tests |
| 5. runtime integration | EVD-009 | composition/pre-apply test |
| 6. Prometheus | OPT-001, OPT-005, OPT-007 | isolated route test |
| 7. Grafana | OPT-002, OPT-005, OPT-007 | isolated route test |
| 8. app | OPT-003, OPT-005..OPT-007 | isolated/shared-upstream test |
| 9. API | OPT-004..OPT-007 | isolated/shared-upstream test |
| 10. disabled optionals | OPT-008..OPT-009 | negative fixture test |
| 11. dynamic browser expectations | E2E-001..E2E-003 | pure expectation test |
| 12. optional suite summary | E2E-002..E2E-004 | optional model summary test |
| 13. missing is non-success | E2E-005..E2E-006 | missing precedence test |
| 14. default dashboard | DASH-001, DASH-005 | renderer test |
| 15. optional dashboard | DASH-002, DASH-005 | fixture renderer test |
| 16. no dashboard password values | DASH-004 | sentinel/ref test |
| 17. no 10080/10443 preferred links | DASH-003 | parsed URL test |
| 18. unchanged core routes | BASE-001..BASE-004, ARC-004 | core regression suite |

## Target Picture

```text
ports.yaml + services.yml + service profile
                 |
                 v
       effective access model port
          /       |       |       \
  Traefik     dashboard  health   productive redacted JSON
   labels       links    targets          |
      \           |        /              v
       dynamic browser expectations   ignored local evidence
```

There is one model computation. Consumers project it for their own purpose;
none reconstructs route truth independently.

## Scope

Expected product and test files:

- `src/tiny_swarm_world/domain/ingress/desired_state.py`
- `src/tiny_swarm_world/application/ports/repositories/port_effective_access_model_repository.py`
- `src/tiny_swarm_world/application/ports/repositories/port_routing_evidence_repository.py`
- `src/tiny_swarm_world/application/services/deployment/write_effective_access_model_evidence.py`
- `src/tiny_swarm_world/application/services/deployment/__init__.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/routing_evidence_local_repository.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- focused tests under `tests/domain`, `tests/application`,
  `tests/infrastructure`, `tests/integration` and `tests/live`
- renderer drift/fallback asset only if the default render differs
- directly relevant arc42, system and user documentation
- workflow and evidence artifacts declared by this workflow

Explicitly forbidden:

- product changes outside the requirement matrix;
- live infrastructure mutation during normal execution;
- reading, staging or committing local env/secret files;
- global repository configuration mutation by tests;
- new browser frontend, Java, Maven, Spring or Kubernetes surfaces;
- route duplication in browser/test-only code.

## Architecture Constraints

- Domain owns ingress values and pure calculations only.
- Application owns the evidence use case and depends on explicit ports.
- Infrastructure owns YAML, filesystem paths, atomic replacement and concrete
  composition.
- A dedicated routing-evidence repository port/adapter is preferred over
  direct application filesystem calls.
- `ComposeFileRepositoryYaml` may implement the effective-model repository
  port and must use the same public method for compose labels and dashboard
  rendering.
- Composition remains local and explicit in
  `src/tiny_swarm_world/infrastructure/composition.py`.
- Evidence serialization uses a fixed allowlist. It must not serialize
  arbitrary model mappings, environment variables or exception payloads.
- Constructors remain side-effect free.

## Product Evidence Contract

Target:

```text
.tiny-swarm-world/evidence/solid-typed-evidence/routing/
  effective-access-model.json
```

Required fields:

- `evidence_kind`
- `generated_at`
- `service_profile`
- `public_ports`
- `gateway_public_ingress_ports`
- `diagnostic_fallback_ports`
- `service_access_preferred_url_source`
- `routes`
- `health_check_targets`
- `service_access_links`
- `skipped_routes`
- `result`

Contract decisions:

- `evidence_kind = effective_access_model`
- `result = generated`
- `generated_at` is UTC ISO-8601.
- Routes sort by service name, hostname and upstream service.
- Skips sort by service and reason.
- Health targets, links and fallback ports also sort deterministically.
- Credential projection contains `username_label` and `item_reference` only.
- A safe failure raises before deployment and leaves any prior complete file
  intact.
- Successful reruns atomically replace the same file.
- The artifact does not claim live service readiness.

## Python Automation Assessment

This is a Python automation change. Use small typed ports and services, a
dedicated infrastructure persistence adapter, the current composition root and
`unittest` fixtures. No new dependency is expected.

## Frontend Assessment

No React or browser application module is in scope. The Service Access page is
generated static HTML. Browser work is test-contract work only. Console/status
UI is not affected.

## Test Strategy

- Add regression tests before or in the same slice as the minimal fix.
- Use `TemporaryDirectory` and `ProjectPaths.from_roots()`.
- Write synthetic `infra/config/services.yml`, `infra/config/ports.yaml` and
  compose files inside each temporary repository.
- Never rewrite committed `infra/config/services.yml` or `ports.yaml`.
- Test pure evidence/summary builders separately from filesystem adapters.
- Test atomic storage in infrastructure.
- Test composition wiring without running its pre-apply external commands.
- Preserve all existing core route assertions.
- Run targeted tests first and all final gates through WSL/Linux.

## Resilience Requirements

- Evidence writes are idempotent and atomically replace a stable target.
- Parent creation and temporary-file cleanup are deterministic.
- No retry is needed for validation or local write failures; fail fast before
  stack deployment with a sanitized classification.
- Existing complete evidence survives failed replacement.
- Browser suite outcome precedence is deterministic:
  `failed or missing -> failed`, `only skipped -> skipped`, otherwise
  `passed`.
- Stale evidence for routes not expected by the current model does not make a
  disabled route fail.
- CI retries are allowed only for observable infrastructure-only failures.
- Live checks are serialized and remain opt-in.

## Ordered Slices

### Slice 01 - Effective Model Seam And Positive Optional Routes

Purpose:

- Establish the public effective-model port, fix simultaneous shared-upstream
  route rendering and contradictory skip semantics, and prove all four
  optional routes with isolated fixtures.

Prerequisites:

- Active branch and clean worktree verified.
- Issue requirement matrix copied to the issue evidence root.
- Slice distribution evidence approved before writes.

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/domain/ingress/desired_state.py"
  - "src/tiny_swarm_world/application/ports/repositories/port_effective_access_model_repository.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "tests/domain/ingress/test_desired_state.py"
  - "tests/integration/test_optional_service_routing.py"
  - "tests/support/effective_access_model_fixture.py"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/slice-01-distribution.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/slice-01-consolidation.md"
affected_modules:
  - "tiny_swarm_world.domain.ingress"
  - "tiny_swarm_world.application.ports.repositories"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
  - "tests.integration"
affected_contracts:
  - "Effective access model source of truth"
  - "Conditional route activation"
  - "Traefik labels per upstream service"
dependencies: []
parallel_group: "G1-model-foundation"
file_locks:
  - "src/tiny_swarm_world/domain/ingress/desired_state.py"
  - "src/tiny_swarm_world/application/ports/repositories/port_effective_access_model_repository.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py"
  - "tests/domain/ingress/test_desired_state.py"
  - "tests/integration/test_optional_service_routing.py"
  - "tests/support/effective_access_model_fixture.py"
contract_locks:
  - "One effective access model feeds all consumers"
  - "Enabled conditional routes are not also skipped"
  - "App and API may share one Docker service without label loss"
architecture_locks:
  - "Domain remains infrastructure-free and I/O-free"
  - "YAML parsing stays in infrastructure"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.domain.ingress.test_desired_state"
    - "PYTHONPATH=src python3 -m unittest tests.integration.test_optional_service_routing"
    - "PYTHONPATH=src python3 -m unittest tests.integration.test_service_access_routing"
  required:
    - "python3 tools/quality_gate.py arch-tests"
documentation:
  arc42: "Check source-of-truth and route extension wording; update only after implementation is verified."
  adr: "No ADR change expected."
stop_conditions:
  - "Stop if optional service activation cannot be derived from temporary structured services.yml and ports.yaml."
  - "Stop if app and API require a new service boundary or product compose stack not established by configuration."
  - "Stop if a second route registry would be introduced."
```

Done criteria:

- A public application port returns the same effective model used by the
  compose renderer and dashboard.
- Positive tests for Prometheus, Grafana, app and API assert hostname,
  upstream, internal port, all Traefik labels/network, routed HTTPS link and
  health target.
- App and API labels coexist on their shared upstream service.
- Disabled optionals are `service_not_enabled`.
- Enabled optionals are not listed as skipped.
- Committed configuration is unchanged.

Requirement mapping: `OPT-001..OPT-009`, `ARC-001..ARC-003`,
`TST-002` and preserved `BASE-001..BASE-004`.

Rollback:

- Revert only Slice 01 files; no persisted runtime or schema migration exists.

### Slice 02 - Productive Redacted Routing Evidence

Purpose:

- Add the application use case, dedicated persistence port/adapter, atomic
  JSON contract and deployment pre-apply wiring.

Prerequisites:

- Slice 01 merged into the workflow branch.
- Effective-model port contract is stable.

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior DevOps Engineer"
  - "Senior Tester"
  - "Security / Evidence Reviewer"
affected_files:
  - "src/tiny_swarm_world/application/ports/repositories/port_routing_evidence_repository.py"
  - "src/tiny_swarm_world/application/services/deployment/write_effective_access_model_evidence.py"
  - "src/tiny_swarm_world/application/services/deployment/__init__.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/routing_evidence_local_repository.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/application/services/deployment/test_write_effective_access_model_evidence.py"
  - "tests/infrastructure/adapters/repositories/test_routing_evidence_local_repository.py"
  - "tests/infrastructure/test_composition.py"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/slice-02-distribution.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/slice-02-consolidation.md"
affected_modules:
  - "tiny_swarm_world.application.ports.repositories"
  - "tiny_swarm_world.application.services.deployment"
  - "tiny_swarm_world.infrastructure.adapters.repositories"
  - "tiny_swarm_world.infrastructure.composition"
affected_contracts:
  - "Effective access model evidence schema"
  - "Atomic local evidence persistence"
  - "Deployment pre-apply evidence generation"
dependencies:
  - "01"
parallel_group: "G2-independent-consumers"
file_locks:
  - "src/tiny_swarm_world/application/ports/repositories/port_routing_evidence_repository.py"
  - "src/tiny_swarm_world/application/services/deployment/write_effective_access_model_evidence.py"
  - "src/tiny_swarm_world/application/services/deployment/__init__.py"
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/routing_evidence_local_repository.py"
  - "src/tiny_swarm_world/infrastructure/composition.py"
  - "tests/application/services/deployment/test_write_effective_access_model_evidence.py"
  - "tests/infrastructure/adapters/repositories/test_routing_evidence_local_repository.py"
  - "tests/infrastructure/test_composition.py"
contract_locks:
  - "Evidence contains only allowlisted route fields and credential references"
  - "Atomic replacement occurs in the destination directory"
  - "Evidence generation precedes stack apply"
architecture_locks:
  - "Application depends on ports, never infrastructure"
  - "Filesystem and JSON persistence details remain in infrastructure"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_write_effective_access_model_evidence"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_routing_evidence_local_repository"
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition"
  required:
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
documentation:
  arc42: "Record productive model evidence and fail-closed pre-apply behavior after tests pass."
  adr: "No ADR change expected; use existing Traefik and setup-safety decisions."
stop_conditions:
  - "Stop if raw mappings or process environment credentials would be serialized."
  - "Stop if evidence cannot be written atomically without changing the target path."
  - "Stop if wiring changes setup phase order or requires live infrastructure in tests."
```

Done criteria:

- The exact file and all required fields are written.
- Only labels and Infisical item references remain in credential projections.
- Sorting is deterministic and the clock is testable.
- Parent creation, atomic replace, private local permissions, old-target
  preservation and temp cleanup are tested.
- Composition includes the use case before stack apply without changing phase
  order.
- The path remains ignored.

Requirement mapping: `EVD-001..EVD-010`, `ARC-001..ARC-004` and
`TST-001`.

Rollback:

- Remove the pre-apply registration and new port/service/adapter. Any ignored
  local JSON can remain as non-authoritative evidence or be removed manually.

### Slice 03 - Renderer-Centric Dashboard Verification

Purpose:

- Make renderer output the dashboard-test source of truth, add optional model
  coverage and preserve one explicit committed-default drift contract.

Prerequisites:

- Slice 01 model/fixture merged.

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior Python Automation Developer"
  - "Senior System Architect"
  - "Security / Evidence Reviewer"
affected_files:
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
  - "tests/integration/routing_contract.py"
  - "infra/config/compose/service-access/dashboard/index.html"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/slice-03-distribution.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/slice-03-consolidation.md"
affected_modules:
  - "tests.infrastructure.adapters.repositories"
  - "tests.integration"
  - "infra.config.compose.service-access.dashboard"
affected_contracts:
  - "Dashboard renderer is test source of truth"
  - "Committed default dashboard drift check"
dependencies:
  - "01"
parallel_group: "G2-independent-consumers"
file_locks:
  - "tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py"
  - "tests/integration/routing_contract.py"
  - "infra/config/compose/service-access/dashboard/index.html"
contract_locks:
  - "Rendered row count equals effective service_access_links count"
  - "Committed HTML changes only when default renderer output changes"
architecture_locks:
  - "Tests do not create an alternate dashboard route source"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml"
    - "PYTHONPATH=src python3 -m unittest tests.integration.test_service_access_routing"
  required: []
documentation:
  arc42: "Check fallback/build-artifact wording."
  adr: "Preserve ADR history; no edit expected."
stop_conditions:
  - "Stop if a renderer defect requires editing a Slice 01 locked product file while Slice 01 is not consolidated."
  - "Stop if a test would read credential values or modify repository YAML."
```

Done criteria:

- Default and optional dashboard assertions call the renderer.
- Optional links appear only when enabled.
- Parsed preferred links contain neither `10080` nor `10443`.
- Sentinel password/token/private-key values are absent.
- Credential labels and Infisical references remain.
- Rendered row count equals model link count.
- A clearly named drift test compares committed HTML to default renderer
  output; committed HTML is changed only if that test proves drift.

Requirement mapping: `DASH-001..DASH-006`, `TST-004` and
`BASE-003..BASE-005`.

Rollback:

- Revert dashboard test/fallback asset changes; no runtime state exists.

### Slice 04 - Dynamic Browser Expectations And Deterministic Summary

Purpose:

- Replace static-suite expectation authority with effective-model links and
  make missing/optional/disabled semantics explicit.

Prerequisites:

- Slice 01 model/fixture merged.

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior Python Automation Developer"
  - "Senior DevOps Engineer"
  - "Live Evidence Validation Reviewer"
affected_files:
  - "tests/live/browser_e2e_contract.py"
  - "tests/live/test_post_install_browser_live.py"
  - "tests/live/test_observability_browser_e2e.py"
  - "tests/live/test_tiny_swarm_app_browser_e2e.py"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/slice-04-distribution.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/slice-04-consolidation.md"
affected_modules:
  - "tests.live"
affected_contracts:
  - "Dynamic routed browser expectation matrix"
  - "Per-route E2E status partition"
  - "Suite final-status precedence"
dependencies:
  - "01"
parallel_group: "G2-independent-consumers"
file_locks:
  - "tests/live/browser_e2e_contract.py"
  - "tests/live/test_post_install_browser_live.py"
  - "tests/live/test_observability_browser_e2e.py"
  - "tests/live/test_tiny_swarm_app_browser_e2e.py"
contract_locks:
  - "Expected routes come from current service_access_links"
  - "Missing remains missing and forces a non-success suite"
  - "Live Selenium remains explicit opt-in"
architecture_locks:
  - "Test code may consume product model but product code never imports tests"
quality_gates:
  targeted:
    - "PYTHONPATH=src python3 -m unittest tests.live.browser_e2e_contract"
    - "PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live.StaticPostInstallLiveSuiteTest"
    - "PYTHONPATH=src python3 -m unittest tests.live.test_observability_browser_e2e tests.live.test_tiny_swarm_app_browser_e2e"
  required: []
documentation:
  arc42: "Document dynamic live expectation and skip/missing semantics after verification."
  adr: "No ADR change; preserve explicit live-consent contract."
stop_conditions:
  - "Stop if static tests need a browser, DNS, Traefik, Docker or live credentials."
  - "Stop if disabled routes remain expected because of stale evidence files."
  - "Stop if missing is normalized to skipped or passed."
```

Done criteria:

- Browser expectations are generated from current model links and sorted.
- Static hardcoded metadata may remain only for service-specific login
  behavior, never suite membership.
- Enabled optionals automatically enter the status matrix.
- Disabled/non-applicable routes do not fail because of stale files.
- Every expected route has exactly one state.
- Missing route entries have `status: missing` and final suite `result:
  failed`.
- Consent, Selenium and credentials still record explicit skips.
- Standard tests run without live dependencies.

Requirement mapping: `E2E-001..E2E-008`, `LIVE-001..LIVE-003` and
`TST-003`.

Rollback:

- Revert browser contract files; ignored E2E evidence is non-authoritative and
  may be retained for diagnosis.

### Slice 05 - Documentation, Complete Evidence And Local Quality

Purpose:

- Synchronize only directly affected documentation, complete both evidence
  packages, run every local gate and obtain an independent issue audit.

Prerequisites:

- Slices 02, 03 and 04 consolidated.
- No open requirement-matrix item lacks planned verification.

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
  - "Senior DevOps Engineer"
  - "Issue Completion Auditor"
affected_files:
  - "documentation/arc42/05_building_blocks.adoc"
  - "documentation/arc42/06_runtime_view.adoc"
  - "documentation/arc42/07_deployment_view.adoc"
  - "documentation/arc42/10_quality_requirements.adoc"
  - "documentation/arc42/11_risks_and_debt.adoc"
  - "documentation/system/live-operation-surfaces.adoc"
  - "documentation/user_guide/installation.adoc"
  - "documentation/user_guide/usage.adoc"
  - "documentation/user_guide/troubleshooting.adoc"
  - "documentation/workflow/workflow.md"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/three-amigos-gate.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/implementation-plan.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/changed-files.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/test-results.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/quality-results.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/routing-evidence-verification.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/browser-e2e-verification.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/issue-completion-audit.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/final-status.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/slice-05-distribution.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/slice-05-consolidation.md"
affected_modules:
  - "documentation"
  - "workflow evidence"
  - "issue completion evidence"
affected_contracts:
  - "Issue #157 traceability and completion"
  - "QUALITY.md local gate"
  - "arc42 planned-versus-implemented accuracy"
dependencies:
  - "02"
  - "03"
  - "04"
parallel_group: "G3-final-local-verification"
file_locks:
  - "documentation/arc42/05_building_blocks.adoc"
  - "documentation/arc42/06_runtime_view.adoc"
  - "documentation/arc42/07_deployment_view.adoc"
  - "documentation/arc42/10_quality_requirements.adoc"
  - "documentation/arc42/11_risks_and_debt.adoc"
  - "documentation/system/live-operation-surfaces.adoc"
  - "documentation/user_guide/installation.adoc"
  - "documentation/user_guide/usage.adoc"
  - "documentation/user_guide/troubleshooting.adoc"
  - "documentation/workflow/**"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/**"
contract_locks:
  - "No DONE with an open or unverified matrix row"
  - "No live pass claim from static evidence"
architecture_locks:
  - "ADR history remains unchanged unless a new decision blocker is proven"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py lint"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py typecheck"
    - "python3 tools/quality_gate.py test"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "Update verified building-block, runtime, deployment, quality and risk consequences only."
  adr: "Checked; no ADR edit expected."
stop_conditions:
  - "Stop if documentation would claim live reachability from static tests."
  - "Stop if any matrix row is open or evidence is inconsistent."
  - "Stop if required gates cannot be executed or a failure cannot be classified."
```

Done criteria:

- Relevant docs describe the productive routing evidence, dynamic browser
  matrix and renderer-source tests as implemented only after verification.
- All requested `.codex/evidence` files contain actual results, not
  placeholders.
- The ignored issue evidence package contains:
  `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`,
  `test_results.md`, `remaining_risks.md` and `acceptance_checklist.md`.
- Every requested local gate passes.
- The Issue Completion Auditor returns `PASS`. Any other result blocks DONE.

Requirement mapping: `GOV-001..GOV-003`, `GOV-007`, all `TST-*` and
documentation evidence for every other ID.

Rollback:

- Documentation/evidence changes can be reverted independently; never revert
  product changes merely to hide a failed gate.

### Slice 06 - Guarded Publication, PR Checks And Review Fixing Loop

Purpose:

- Publish the verified implementation branch, create/reuse the PR against
  `main`, inspect required checks and SonarCloud, resolve actionable review
  findings, and finalize status.

Prerequisites:

- Slice 05 audit decision is `PASS`.
- Full local quality is green.
- Staged and unstaged files are fully classified and task-scoped.

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Git Commit Operator / Senior DevOps Engineer"
secondary_reviewers:
  - "Git Commit Reviewer"
  - "Senior Tester"
  - "Issue Completion Auditor"
affected_files:
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/changed-files.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/test-results.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/quality-results.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/browser-e2e-verification.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/final-status.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/slice-06-distribution.md"
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/slice-06-consolidation.md"
affected_modules:
  - "git branch publication"
  - "GitHub pull request"
  - "CI and SonarCloud"
affected_contracts:
  - "Branch push and PR against main"
  - "Required-check and review-comment fixing loop"
dependencies:
  - "05"
parallel_group: "G4-serialized-publication"
file_locks:
  - ".codex/evidence/workflow-issue-157-final-gaps-20260711/**"
contract_locks:
  - "Never push to main or force-push"
  - "Required checks must be green and review comments dispositioned"
  - "Remediation reacquires the original owning slice lock"
architecture_locks:
  - "CI remediation cannot expand Issue #157 scope"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "No further update unless remediation changes verified behavior."
  adr: "Stop if remediation discovers a decision gap."
stop_conditions:
  - "Stop on missing push/PR permission, unknown mergeability or unverifiable required checks."
  - "Stop if SonarCloud is configured but its required result cannot be verified."
  - "Stop if a review request requires out-of-scope redesign or a new ADR."
```

Execution loop:

1. Reproduce commit-readiness review locally or through the governed reviewer.
2. Commit exactly one slice at each checkpoint and push only
   `HEAD:fix/issue-157-final-gaps-20260711`.
3. Create or reuse a pull request to `main` after Slice 05.
4. Inspect `Python Quality And SonarCloud` and every required check.
5. If an in-scope check or actionable review fails, route it through the Typed
   Error Router, reacquire the original slice's locks, fix only owned files,
   rerun targeted and full gates, commit and push, then return to step 4.
6. Continue until checks are green and actionable comments are resolved, or a
   real stop condition is reached.
7. Update `final-status.md` with PR URL and merge status.

This workflow requests PR creation and readiness, not automatic merge. Record
`Merge status: not merged` unless a later explicit user command authorizes
merge under repository governance.

Requirement mapping: `GOV-004..GOV-006` and final verification of all IDs.

Rollback:

- Revert the task-scoped PR or branch commits. Never delete or rewrite `main`.

## Slice Dependency Graph

```text
01 Effective Model Seam And Positive Optional Routes
  +--> 02 Productive Redacted Routing Evidence --------+
  +--> 03 Renderer-Centric Dashboard Verification -----+--> 05 Docs/Evidence/Quality
  +--> 04 Dynamic Browser Expectations And Summary ----+          |
                                                                  v
                                                      06 PR/CI/Review Loop
```

Topological groups:

- `G1`: Slice 01, serial.
- `G2`: Slices 02, 03 and 04 may execute in parallel only in isolated
  worktrees after Slice 01 consolidation.
- `G3`: Slice 05, serial after all G2 slices.
- `G4`: Slice 06, serialized external publication and validation.

## Parallel Execution

- Can this workflow run in parallel? Yes, only Slices 02, 03 and 04 after
  Slice 01.
- Conflicting workflows: any active workflow touching ingress desired state,
  compose route rendering, routing evidence, Service Access dashboard tests,
  browser E2E evidence, `documentation/workflow/**` or the same arc42 files.
- Shared files: Slice 01 model and fixture are read-only inputs for G2.
- Shared infrastructure: Docker Swarm, Traefik, DNS, Selenium and services;
  not used by parallel static streams.
- Requires isolated worktree: yes for every G2 stream.
- Requires serialized live validation: yes.
- Merge-order constraints: consolidate 02, then 03, then 04; run Slice 05 only
  after all three are accepted.

Parallel work is forbidden when file locks overlap, the effective-model
contract is unstable, a generated dashboard conflict appears, secret handling
is unclear, live infrastructure would be shared, or Three Amigos/S3D revokes
parallel eligibility.

## Automatic Work Distribution Policy

Before each slice, `workflow execute` must:

1. inspect the slice for safe backend, test, runtime, documentation, quality,
   architecture and security stream decomposition;
2. create
   `.codex/evidence/workflow-issue-157-final-gaps-20260711/slice-<id>-distribution.md`;
3. use real Codex subagents when supported and authorized by workflow execute;
4. otherwise perform explicit role-based fallback reviews in the main thread;
5. keep stream branches/worktrees isolated;
6. consolidate accepted outputs as the final integration owner;
7. create `slice-<id>-consolidation.md` before the slice checkpoint commit.

Stream map:

- Backend/Python: Slices 01 and 02.
- Frontend/React: not applicable.
- Console/status UI: not applicable.
- Tests: Slices 01, 02, 03 and 04.
- Runtime/DevOps: Slice 02 and Slice 06.
- Documentation: Slice 05.
- Quality: Slices 05 and 06.
- Architecture: all implementation slices.
- Security/evidence: Slices 02, 03, 04 and 05.

Codex remains final owner for consolidation, gates, evidence, PR readiness and
the completion claim.

## Git Worktree Execution Rule

- Main workflow worktree: the isolated worktree where the declared branch and
  baseline commit are verified.
- Active branch must be `fix/issue-157-final-gaps-20260711`.
- Every parallel stream uses a separate worktree and a branch named
  `fix/issue-157-final-gaps-20260711-slice-<id>-<stream>`.
- Stream workers verify branch/ref/status before writing.
- Stream workers do not merge. Codex consolidates.
- Do not switch or clean the original dirty worktree.
- Check for broad line-ending-only changes before staging.

## Role Ownership Map

- Senior Workflow Architect: workflow structure, graph, locks and handoff.
- Senior Requirement Engineer: matrix, scope and traceability.
- Senior System Architect: effective-model source of truth and boundaries.
- Senior Python Automation Developer: Slices 01 and 02 implementation.
- Senior Tester: regression-first tests, Slices 03/04 and quality evidence.
- Senior DevOps Engineer: pre-apply integration, CI and publication.
- Senior Documentation Engineer: Slice 05 documentation/evidence.
- Security / Evidence Reviewer: allowlist, redaction and ignored paths.
- Live Evidence Validation Reviewer: opt-in/skip/missing semantics.
- Issue Completion Auditor: independent final PASS/INCOMPLETE/BLOCKED/REJECTED
  decision.

## Issue Completion Discipline

- Requirement matrix path:
  `.tiny-swarm/evidence/issue-157-final-gaps-20260711/requirement_matrix.md`
- Required evidence path:
  `.tiny-swarm/evidence/issue-157-final-gaps-20260711/`
- Required evidence files:
  `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`,
  `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`
- Requirement Lead review: confirm every matrix ID is captured and mapped.
- System Architect Reviewer review: confirm one model source, application
  ports, infrastructure persistence and unchanged setup phases.
- Test / Evidence Reviewer review: confirm every ID has a test/check/artifact
  and no static result is presented as live proof.
- Issue Completion Auditor review: mandatory after implementation and full
  local quality, before DONE.
- DONE blocking rule: any open or unverified requirement forces `INCOMPLETE`,
  `BLOCKED` or `FAILED`. Only an auditor `PASS` permits DONE.

## Required Workflow Evidence

The committed workflow evidence root must contain:

- `three-amigos-gate.md`
- `implementation-plan.md`
- `changed-files.md`
- `test-results.md`
- `quality-results.md`
- `routing-evidence-verification.md`
- `browser-e2e-verification.md`
- `final-status.md`

`final-status.md` must retain these fields:

- Issue
- Branch
- Commits
- Changed files
- Implemented requirements
- Deferred requirements
- Quality gate results
- Live E2E result
- Known limitations
- Pull request
- Merge status

During authoring, non-applicable execution fields are explicitly `PENDING` or
`NOT_RUN`. Slice 05/06 must replace them with evidence-backed results.

## Quality-Gate Expectations

Run from the workflow worktree inside WSL/Linux:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

On a Windows host, execute the commands through WSL with the verified workflow
worktree as the command working directory. Do not persist its host-specific
absolute path in committed evidence.

Also run `git diff --check` before every checkpoint commit and final
publication. Do not claim any gate passed unless its command executed
successfully.

No live browser, DNS, Traefik, Docker or Incus dependency is permitted in
these commands.

## Live Selenium Contract

Live Selenium may run only after all of these are explicitly evidenced:

- current operator consent to `TSW_RUN_POST_INSTALL_BROWSER_LIVE=1`;
- Selenium and supported browser/driver available;
- reachable approved live infrastructure;
- approved credential sources available;
- safe local evidence path;
- serialized execution.

If any prerequisite is absent:

- write or retain per-route `skipped` evidence with the precise redacted
  reason;
- update `browser-e2e-verification.md`;
- do not claim live pass;
- do not fail the static quality gate merely because the optional live run is
  unavailable.

The ignored `live-installation.env` file may be read only by an explicitly
authorized live run. Its raw content must never enter logs, commits, workflow
evidence or chat output.

## Documentation Synchronization Points

After verified implementation only:

- building blocks: effective-model port and routing evidence adapter;
- runtime view: fail-closed pre-apply evidence generation;
- deployment view: local routing evidence path and no phase-order change;
- quality requirements: optional routes, browser missing semantics and
  renderer source;
- risks/debt: remove only the exact Issue #157 gaps that tests close;
- live operation surfaces/user guides: identify routing JSON as generated
  model evidence, not live readiness.

Do not opportunistically repair unrelated historical Vaultwarden/Infisical or
legacy port wording in this workflow.

## Typed Failure Routing

- `ARCH_VIOLATION` -> Senior System Architect + architecture-hexagonal.
- `BUILD_FAILURE` -> owning Python/Test stream + Senior DevOps.
- `TEST_FAILURE` -> Senior Tester + owning slice.
- `DOC_GOVERNANCE_FAILURE` -> Senior Documentation Engineer + Requirement
  Engineer.
- `LOCK_CONFLICT` -> S3D Execution Orchestrator + Root Architect.
- `SECURITY_EVIDENCE_FAILURE` -> Security/Evidence Reviewer; fail closed.
- `UNKNOWN_FAILURE` -> Root Architect.

Ordinary in-scope lint, test, type, architecture, Sonar or review failures are
fixed in the same branch. They are not stop conditions by themselves.

## Stop Conditions

Stop and report only when:

- repository, issue, governing docs or required source cannot be read;
- the active branch/worktree/ref is unsafe or unclear;
- a new architecture decision is genuinely required;
- the central source of truth cannot be preserved;
- evidence safety would require guessing or could expose secrets;
- the required local quality commands are technically unavailable after
  in-scope environment checks;
- push/PR permission is missing;
- required CI/Sonar state or review state cannot be verified;
- a required fix is outside Issue #157 scope or violates a forbidden area;
- live infrastructure would be required without explicit consent.

Do not stop for an ordinary in-scope failing test, lint/type/architecture
finding, Sonar finding, actionable review comment, or resolvable merge
conflict.

## Workflow Creation Publication

The authoring result itself must:

- stage only `documentation/workflow/**` and the new workflow evidence root;
- commit on `fix/issue-157-final-gaps-20260711`;
- push only `HEAD` to
  `origin/fix/issue-157-final-gaps-20260711`;
- not create, merge or clean up a PR;
- record any authentication failure exactly.

This is guarded workflow publication, not `push auto`. The implementation PR
is created only by Slice 06 after workflow execution.

Authoring publication result:

- WSL Git pushed the workflow branch successfully to
  `origin/fix/issue-157-final-gaps-20260711`.
- No workflow-documentation PR was created.
- No merge, branch deletion or cleanup was performed.

## Definition Of Done

The implementation workflow is complete only when:

- productive central routing evidence is written and runtime-integrated;
- positive Prometheus, Grafana, app and API tests pass;
- dynamic browser expectations and optional-route summary behavior pass;
- missing route evidence is non-success;
- dashboard tests use renderer output and default drift is explicit;
- no secret value reaches dashboard or routing evidence;
- all requested local quality gates pass;
- required workflow and issue evidence are complete;
- the Issue Completion Auditor returns `PASS`;
- the branch is pushed;
- a PR to `main` exists;
- required checks are green, including the configured SonarCloud job result;
- actionable review comments are resolved;
- `final-status.md` contains actual branch, commit, check, live-E2E, PR and
  merge status.

No automatic merge is required by this workflow. A real blocker is recorded
instead of a false DONE.

## Handoff To Workflow Execute

Run exact `workflow execute` only after verifying:

- active branch: `fix/issue-157-final-gaps-20260711`;
- active workflow version:
  `workflow-issue-157-final-gaps-v1.0.0`;
- current context-pack hashes;
- clean task worktree;
- no conflicting active workflow or locks;
- S3/S3D returns `EXECUTION_PLAN`;
- issue matrix and Slice 01 distribution evidence exist;
- no live command is inferred from the attached env-file reference.

## arc42 Check Status

Checked:

- `documentation/arc42/05_building_blocks.adoc`
- `documentation/arc42/06_runtime_view.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/07_deployment/system.adoc`
- `documentation/arc42/09_architecture_decisions.adoc`
- `documentation/arc42/10_quality_requirements.adoc`
- `documentation/arc42/11_risks_and_debt.adoc`
- `adr-traefik-https-ingress-existing-ca.adoc`
- `adr-service-access-dashboard-vaultwarden.adoc`
- `adr-autonomous-setup-safety.adoc`
- `adr-explicit-non-interactive-live-consent.adoc`

Authoring conclusion:

- No ADR edit is needed.
- Planned behavior is not written into arc42 as implemented behavior.
- Slice 05 owns narrowly scoped synchronization after product verification.
