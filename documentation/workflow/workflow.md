# Workflow: Traefik HTTPS Ingress With Existing CA

```yaml
workflow_id: traefik-https-ingress-existing-ca-20260609
workflow_version: 1.0.0
branch: feature/traefik-https-ingress-existing-ca-20260609
execution_profile: FULL_PATH
released_for_workflow_execute: true
created_utc: "2026-06-09T00:00:00Z"
request: "Create and execute a repository-compliant workflow from the external Traefik HTTPS ingress migration plan, using tests/live/test_post_install_browser_live.py as the live browser verification reference."
decision: READY_FOR_WORKFLOW
confidence: 91
```

## Executive Summary

This workflow migrates Tiny Swarm World toward centralized HTTPS ingress with
Traefik and an operator-provided existing CA. The current architecture records
Traefik and TLS automation as deferred, so this workflow starts with governance:
an ADR/arc42 update must authorize Traefik routing ownership, TLS policy,
rollback, and safety constraints before implementation claims Traefik behavior.

The workflow then adds desired-state and reconciliation slices for discovery,
certificate validation, Traefik stack configuration, Swarm service routing,
Infisical-backed secret coverage, LXC public port reconciliation, hostname
resolution, and opt-in live browser verification through
`tests/live/test_post_install_browser_live.py`.

Live LXD/LXC, Docker Swarm, Traefik deployment, certificate validation, DNS or
hosts checks, and `./install.sh --confirm-reset` are live infrastructure
operations. They may run only inside workflow execute after branch, slice,
consent, evidence, and S3D checks pass. Default quality gates stay static or
mocked.

## Requirement Clarification Gate

Original request:

- Create a workflow from
  `C:/Users/micro/Downloads/workflow-traefik-https-ingress-expanded.md`.
- Use `tests/live/test_post_install_browser_live.py` as live browser
  verification reference.
- Execute the workflow only after it is repository-compliant.

Interpreted intent:

- Convert the external Traefik HTTPS ingress plan into the active workflow under
  `documentation/workflow`.
- Preserve Tiny Swarm World governance: branch-first workflow creation,
  executable slice metadata, locks, quality gates, role ownership, stop
  conditions, arc42/ADR synchronization, and live-evidence constraints.
- Keep the project Linux/WSL-only, Docker Swarm-first, LXC-native, and Python
  hexagonal.

Change type:

- Workflow and governance authoring.
- Future architecture decision for ingress ownership.
- Future Python automation for Traefik desired state, certificate validation,
  route validation, LXC reconciliation, and live evidence classification.
- Future Docker Swarm and LXC runtime changes.
- Future opt-in live browser/TLS verification.

Affected process strand:

- Workflow creation and workflow execute.
- Deployment and live greenpath repair.
- Docker Swarm routing and LXC public port exposure.
- TLS/certificate validation with an existing CA.
- Browser route and credential inventory verification.

Affected architecture area:

- `documentation/workflow/**`
- `documentation/architecture/**`
- `documentation/arc42/**`
- `src/tiny_swarm_world/domain`
- `src/tiny_swarm_world/application`
- `src/tiny_swarm_world/infrastructure`
- `infra/config/**`
- `infra/compose/**`
- `tests/**`

Explicit requirements:

- Branch: `feature/traefik-https-ingress-existing-ca-20260609`.
- Use an existing CA; do not generate, replace, or commit operator CA material
  silently.
- Introduce centralized HTTPS ingress with Traefik.
- Keep Docker Swarm as runtime target and LXC as provider target.
- Use a reconciler pattern for desired versus observed ingress, certificates,
  Swarm labels, and LXC public port exposure.
- Keep public LXC exposure limited to ports 80 and 443.
- Require Traefik entrypoints `web` on `:80` and `websecure` on `:443`.
- Redirect HTTP to HTTPS.
- Use `exposedByDefault=false`.
- Forbid `--api.insecure=true`.
- Route Jenkins, SonarQube, Nexus, Portainer, Grafana when configured, and
  Infisical through HTTPS hostnames.
- Validate CN, SAN, issuer, validity, KeyUsage, ExtendedKeyUsage, and chain
  verification.
- Validate hostname resolution through DNS or hosts fallback.
- Run live install/verify/classify/repair/rerun only after governance and
  safety gates pass.
- Preserve secret redaction and Infisical-managed credential coverage.

Implicit requirements:

- Do not expand Windows-specific behavior.
- Do not introduce Java, Maven, Spring Boot, React, or Kubernetes-first
  architecture.
- Preserve hexagonal architecture and composition root wiring.
- Mock Docker, LXC, OpenSSL, HTTP, DNS, and filesystem side effects in default
  tests.
- Keep live evidence under ignored `.tiny-swarm-world/evidence/**` paths.
- Keep planned Traefik behavior separate from verified implementation.

Assumptions:

- Existing CA/certificate/key references are operator-supplied through ignored
  local configuration or secret management.
- Local DNS or hosts fallback may require explicit operator consent and
  rollback because host name resolution can mutate host state.
- Grafana is conditional until repository configuration verifies it as part of
  the selected service profile.
- `tests/live/test_post_install_browser_live.py` may be extended or paired with
  a Traefik-specific live test; existing redaction checks must not be weakened.

Non-goals:

- No public internet exposure.
- No ACME/Let's Encrypt automation unless later explicitly approved.
- No Kubernetes ingress controller.
- No replacement of Infisical as credential inventory authority.
- No committed CA private keys, secrets, live evidence, local hosts files, raw
  command output, local IP addresses, or host-specific absolute paths.
- No browser React frontend project.

Risks:

- Existing ADRs defer Traefik and TLS automation, making S01 mandatory.
- TLS and host resolution can leak secrets or host topology without strict
  evidence redaction.
- Swarm label migration can create routing drift if not reconciled.
- LXC proxy reconciliation can disrupt access if ports 80/443 are not verified
  before removing older exposure.
- The current live browser suite defaults to localhost routes and may need
  hostname-aware extension.

Open questions:

- Exact existing CA file locations are intentionally not committed.
- Grafana service inclusion must be verified from repository configuration.

Blocking questions:

- None for workflow authoring. Open questions become slice preconditions.

Confidence level: 91 percent.

Decision: `READY_FOR_WORKFLOW`.

## Three Amigos Review

Senior Requirement Engineer:

- The workflow matches the request by treating the external Markdown as input
  and converting it into repository-governed executable slices.
- Does the implementation still match the EPIC? Yes, if Traefik remains local
  Linux/WSL scoped, Docker Swarm-first, LXC-native, and fail-closed under live
  consent.

Senior System Architect:

- The current architecture records Traefik as deferred. S01 must update ADR and
  arc42 before implementation changes claim Traefik ownership.
- Routing ownership must move from service-access NGINX baseline to Traefik
  only through an explicit ingress decision, rollback model, and test-backed
  service contract.

Senior Python Automation Developer:

- Ingress desired state, certificate validation, route reconciliation, and
  evidence classification belong behind domain/application contracts.
- Docker, LXC, OpenSSL, HTTP/TLS, DNS, YAML, command execution, and evidence
  file writes stay in infrastructure adapters.

Senior React Frontend Developer:

- No React frontend work is authorized. Browser checks target deployed service
  surfaces only.

Senior Tester:

- Default gates remain static or mocked. Live browser/TLS checks are opt-in and
  must write only redacted evidence.

## Target Picture

A local Linux/WSL LXC-native Docker Swarm environment uses Traefik as central
HTTPS ingress. Public host exposure is limited to ports 80 and 443. HTTP
redirects to HTTPS. Traefik routes configured service hostnames to the matching
Swarm services. Certificates are issued by the operator-provided existing CA
and pass validation. Hostname resolution works through verified DNS or hosts
fallback. The live greenpath reaches a verified pass or stops with a precise,
classified blocker and redacted evidence.

## Verified Baseline

- Active workflow branch:
  `feature/traefik-https-ingress-existing-ca-20260609`.
- Repository identity: Python automation, Linux/WSL-only, Docker Swarm-first,
  LXC-native by default.
- `adr-service-access-dashboard-vaultwarden.adoc` currently states Traefik and
  TLS automation are deferred.
- arc42 deployment view currently states service-access NGINX owns central
  `http://localhost` routing.
- `tests/live/test_post_install_browser_live.py` exists and is opt-in via
  `TSW_RUN_POST_INSTALL_BROWSER_LIVE=1`.
- Workflow creation has not run live Docker, LXC, OpenSSL, DNS, hosts-file, or
  install commands.

## Scope

In scope:

- Workflow and context-pack regeneration.
- ADR/arc42 updates needed to permit Traefik ingress migration.
- Desired ingress state and certificate model.
- Traefik stack/configuration and Docker Swarm label migration.
- Existing CA validation and secret-safe certificate handling.
- LXC exposure reconciliation to ports 80 and 443.
- Hostname resolution validation for `*.tsw.local` hostnames.
- Opt-in live install, TLS, route, browser, and Infisical checks.
- Redacted evidence and final report.

Out of scope:

- Kubernetes ingress.
- Public internet ingress.
- ACME automation.
- Windows-native setup examples.
- Java, Maven, Spring Boot, React, TypeScript, Vite, TSX/JSX.
- Committed certificate private keys, live secrets, raw command output, or
  local host topology.

## Architecture Constraints

- Preserve hexagonal architecture.
- Domain owns provider-neutral and ingress-neutral value objects and
  invariants.
- Application services orchestrate ports and domain models.
- Infrastructure owns Docker Swarm commands, LXC commands, OpenSSL invocations,
  DNS/hosts checks, YAML parsing, HTTP/TLS probes, evidence file writes, and
  composition wiring.
- `src/tiny_swarm_world/infrastructure/composition.py` remains the wiring root.
- Entry points stay thin.
- Live infrastructure mutation requires workflow execution, active branch
  verification, live consent, and slice preconditions.

## Python Automation Assessment

Implementation should introduce a desired-state/reconciler model for ingress
routes, certificate inputs, Swarm label expectations, and LXC public exposure.
The model compares desired and observed state, classifies drift, and emits
redacted remediation hints. Certificate validation records only summaries:
subject/CN, SAN DNS names, issuer, validity window, KeyUsage,
ExtendedKeyUsage, and chain result. It must not persist private key content,
PEM payloads, absolute host paths, or raw `openssl` output.

## Frontend Assessment

No browser frontend module is created. The live browser test may verify HTTPS
route behavior and service landing pages, but the repository remains Python
automation. Static dashboard assets may be updated only if routing labels or
links change.

## Test Strategy

Default tests:

- Unit tests for ingress desired-state modeling, certificate summary parsing,
  route classification, LXC exposure reconciliation, and redaction.
- Mock all Docker, LXC, OpenSSL, DNS/hosts, HTTP/TLS, Infisical, and filesystem
  side effects unless explicitly live.
- Run targeted `unittest` commands before broader quality gates.

Live tests:

```bash
TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live
```

Repository gates:

```bash
git diff --check
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

## Resilience Requirements

- Reconciler operations must be idempotent.
- Repair loop maximum: 10 iterations.
- Stop if the same blocker repeats after a fix.
- Stop if existing CA material is missing or ambiguous.
- Stop if a repair would weaken consent, safety, secret redaction,
  certificate validation, or architecture boundaries.
- Stop before hosts/DNS mutation unless operator intent and rollback are
  explicit.
- Stop if LXD/Docker state is ambiguous.
- Stop if evidence would include secrets, raw command output, local IP
  addresses, absolute host paths, or credential-bearing URLs.

## Ordered Slices

### Slice 01: Governance Baseline And Traefik ADR

```yaml
slice_id: S01
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Requirement Engineer, Senior Documentation Engineer, Senior Security Engineer]
affected_files: [documentation/architecture/**, documentation/arc42/**, documentation/workflow/**]
affected_modules: [documentation, architecture]
affected_contracts: [traefik_ingress_decision, service_access_routing_ownership]
dependencies: []
parallel_group: sequential
file_locks: [documentation/architecture, documentation/arc42, documentation/workflow]
contract_locks: [routing_ownership, tls_policy]
architecture_locks: [deployment_view, adr]
quality_gates:
  targeted: [git diff --check]
  required: [git diff --check]
documentation:
  arc42: update-required-for-traefik-ingress-ownership
  adr: create-or-update-required-for-traefik-existing-ca-ingress
stop_conditions: [branch_mismatch, dirty_unrelated_worktree, unresolved_routing_ownership, missing_tls_policy]
```

Done criteria:

- ADR or architecture decision records Traefik ingress, existing CA handling,
  routing ownership, rollback, and forbidden insecure dashboard mode.
- arc42 deployment/concepts are updated or explicitly checked.
- Planned versus implemented behavior remains separate.

### Slice 02: Baseline Capture And Discovery Model

```yaml
slice_id: S02
profile: FULL_PATH
owner: Senior DevOps Engineer
secondary_reviewers: [Senior Python Automation Developer, Senior Tester, Evidence Auditor]
affected_files: [src/tiny_swarm_world/**, infra/config/**, tests/**, documentation/workflow/**]
affected_modules: [domain, application, infrastructure, tests, workflow]
affected_contracts: [traefik_baseline_discovery, redacted_runtime_evidence]
dependencies: [S01]
parallel_group: sequential
file_locks: [src/tiny_swarm_world, infra/config, tests, documentation/workflow]
contract_locks: [runtime_evidence, command_safety]
architecture_locks: [hexagonal, evidence_redaction]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest <relevant-tests>]
  required: [python3 tools/quality_gate.py test, git diff --check]
documentation:
  arc42: update-if-evidence-contract-changes
  adr: checked-traefik-ingress-decision
stop_conditions: [live_command_without_consent, raw_command_output_persisted, secret_or_host_data_in_evidence]
```

Done criteria:

- Discovery contracts can represent Git, Docker, Swarm, LXC, route, and
  certificate summary state.
- Evidence redaction blocks secrets, tokens, raw command output, local IP
  addresses, and host absolute paths.

### Slice 03: Desired Ingress And Certificate Validation

```yaml
slice_id: S03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Security Engineer, Senior Tester]
affected_files: [src/tiny_swarm_world/**, infra/config/**, tests/**, documentation/workflow/**]
affected_modules: [domain, application, infrastructure, tests]
affected_contracts: [desired_https_ingress, existing_ca_certificate_validation]
dependencies: [S02]
parallel_group: sequential
file_locks: [src/tiny_swarm_world, infra/config, tests, documentation/workflow]
contract_locks: [certificate_validation, service_route_catalog]
architecture_locks: [hexagonal, secret_redaction]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest <relevant-tests>]
  required: [python3 tools/quality_gate.py test, git diff --check]
documentation:
  arc42: update-if-certificate-contract-changes
  adr: checked-existing-ca-policy
stop_conditions: [ca_material_missing, ca_material_ambiguous, private_key_content_persisted, certificate_policy_unclear]
```

Done criteria:

- Hostnames include Jenkins, SonarQube, Nexus, Portainer, conditional Grafana,
  and Infisical.
- Certificate checks cover CN, SAN, issuer, validity, KeyUsage,
  ExtendedKeyUsage, and chain verification.
- Tests cover accepted and rejected certificate summaries without live OpenSSL.

### Slice 04: Traefik Stack And Swarm Routing Migration

```yaml
slice_id: S04
profile: FULL_PATH
owner: Senior DevOps Engineer
secondary_reviewers: [Senior Python Automation Developer, Senior System Architect, Senior Tester]
affected_files: [infra/config/**, infra/compose/**, src/tiny_swarm_world/**, tests/**, documentation/workflow/**]
affected_modules: [deployment, infrastructure, tests]
affected_contracts: [traefik_stack, swarm_route_labels, service_migration]
dependencies: [S03]
parallel_group: sequential
file_locks: [infra/config, infra/compose, src/tiny_swarm_world, tests, documentation/workflow]
contract_locks: [traefik_entrypoints, swarm_routing]
architecture_locks: [deployment_view, hexagonal]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest <relevant-tests>]
  required: [python3 tools/quality_gate.py test, git diff --check]
documentation:
  arc42: update-required-for-runtime-routing-change
  adr: checked-traefik-ingress-decision
stop_conditions: [api_insecure_enabled, exposed_by_default_not_false, route_label_drift, rollback_missing]
```

Done criteria:

- Traefik uses `web :80`, `websecure :443`, HTTP to HTTPS redirect, and
  `exposedByDefault=false`.
- `--api.insecure=true` is absent and tested as forbidden.
- Service migration is represented in configuration/tests without claiming
  live success.

### Slice 05: Secrets Inventory And Infisical Coverage

```yaml
slice_id: S05
profile: FULL_PATH
owner: Senior Security Engineer
secondary_reviewers: [Senior Tester, Senior Python Automation Developer, Senior Documentation Engineer]
affected_files: [src/tiny_swarm_world/**, infra/config/**, config/secrets/**, tests/**, documentation/workflow/**]
affected_modules: [security, deployment, tests]
affected_contracts: [secret_inventory, infisical_credential_inventory]
dependencies: [S04]
parallel_group: sequential
file_locks: [src/tiny_swarm_world, infra/config, config/secrets, tests, documentation/workflow]
contract_locks: [secret_redaction, infisical_inventory]
architecture_locks: [secret_management]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live]
  required: [python3 tools/quality_gate.py test, git diff --check]
documentation:
  arc42: update-if-secret-policy-changes
  adr: checked-secret-management-policy
stop_conditions: [secret_value_committed, credential_bearing_url_persisted, infisical_inventory_contradiction]
```

Done criteria:

- Secret inventory logic scans configuration surfaces for secret-like keys
  without persisting values.
- Infisical coverage remains value-free.
- Existing live-suite static tests pass or are updated without weakening
  redaction.

### Slice 06: LXC Public Port Reconciliation

```yaml
slice_id: S06
profile: FULL_PATH
owner: Senior DevOps Engineer
secondary_reviewers: [Senior System Architect, Senior Security Engineer, Senior Tester]
affected_files: [src/tiny_swarm_world/**, infra/config/**, tests/**, documentation/workflow/**]
affected_modules: [infrastructure, deployment, tests]
affected_contracts: [lxc_proxy_reconciliation, ingress_public_ports]
dependencies: [S05]
parallel_group: sequential
file_locks: [src/tiny_swarm_world, infra/config, tests, documentation/workflow]
contract_locks: [lxc_public_ports, provider_reconciliation]
architecture_locks: [deployment_view, safety_contract]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest <relevant-tests>]
  required: [python3 tools/quality_gate.py test, git diff --check]
documentation:
  arc42: update-if-port-exposure-contract-changes
  adr: checked-lxc-native-provider
stop_conditions: [unexpected_public_port, ambiguous_lxc_state, destructive_proxy_change_without_rollback]
```

Done criteria:

- Desired public port set is exactly 80 and 443.
- Drift detection reports extra/missing proxy devices without unsafe automatic
  removal.
- Mutating reconciliation is consent-gated and test-backed.

### Slice 07: Hostname Resolution And HTTPS Route Verification

```yaml
slice_id: S07
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior DevOps Engineer, Senior Python Automation Developer, Senior Security Engineer]
affected_files: [tests/live/**, src/tiny_swarm_world/**, documentation/workflow/**]
affected_modules: [tests, infrastructure]
affected_contracts: [hostname_resolution, https_endpoint_matrix, browser_live_verification]
dependencies: [S06]
parallel_group: sequential
file_locks: [tests/live, src/tiny_swarm_world, documentation/workflow]
contract_locks: [dns_hosts_fallback, browser_verification]
architecture_locks: [secret_redaction]
quality_gates:
  targeted: [TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live]
  required: [python3 tools/quality_gate.py test, git diff --check]
documentation:
  arc42: checked
  adr: checked-traefik-ingress-decision
stop_conditions: [hosts_mutation_without_consent, browser_trace_contains_secret, https_route_matrix_incomplete]
```

Done criteria:

- Hostname resolution is verified or blocked with precise remediation.
- HTTPS endpoint matrix records redacted service, hostname, status, TLS status,
  and result.
- Browser/live checks remain opt-in and do not persist secrets or screenshots.

### Slice 08: Live Greenpath Repair Loop

```yaml
slice_id: S08
profile: FULL_PATH
owner: Greenpath Recovery Lead
secondary_reviewers: [Senior DevOps Engineer, Senior Python Automation Developer, Senior Tester, Failure Classification Expert, Evidence Auditor]
affected_files: [.tiny-swarm-world/evidence/**, src/tiny_swarm_world/**, infra/config/**, infra/compose/**, tests/**, documentation/workflow/reports/**]
affected_modules: [runtime, infrastructure, deployment, tests, documentation]
affected_contracts: [install_greenpath, traefik_https_greenpath]
dependencies: [S07]
parallel_group: sequential
file_locks: [.tiny-swarm-world/evidence, src/tiny_swarm_world, infra/config, infra/compose, tests, documentation/workflow/reports]
contract_locks: [install_greenpath, live_repair_loop]
architecture_locks: [hexagonal, safety_contract, secret_redaction]
quality_gates:
  targeted: [./install.sh --confirm-reset, TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live]
  required: [python3 tools/quality_gate.py test, git diff --check]
documentation:
  arc42: update-if-runtime-contract-changes
  adr: checked
stop_conditions: [max_10_iterations, same_blocker_twice_after_fix, manual_approval_required, security_violation, external_dependency_unavailable, unknown_root_cause_after_repeated_attempts]
```

Done criteria:

- Each iteration records redacted install summary, browser-live-test result,
  failure classification, changed files, Docker/LXC/Traefik state summary, and
  HTTPS endpoint matrix.
- Each blocker fix is minimal, test-backed, and slice-scoped.
- Loop reaches greenpath or stops with precise owner, blocker, evidence path,
  and next action.

### Slice 09: Final Report And Handoff

```yaml
slice_id: S09
profile: FULL_PATH
owner: Senior Documentation Engineer
secondary_reviewers: [Senior Tester, Senior DevOps Engineer, Senior System Architect, Evidence Auditor]
affected_files: [documentation/workflow/reports/**, documentation/workflow/**]
affected_modules: [documentation, workflow]
affected_contracts: []
dependencies: [S08]
parallel_group: sequential
file_locks: [documentation/workflow/reports, documentation/workflow]
contract_locks: []
architecture_locks: []
quality_gates:
  targeted: [git diff --check]
  required: [git diff --check]
documentation:
  arc42: checked-or-updated
  adr: checked-or-updated
stop_conditions: [missing_evidence, unverified_success_claim, unredacted_secret_evidence]
```

Done criteria:

- Report documents branch, changed files, architecture decision status, CA
  validation, certificate validation, Traefik status, routing table, LXC state,
  endpoint matrix, risks, recommendations, quality commands, commit SHAs, and
  rollback references.
- Report distinguishes verified live facts from planned, skipped, or blocked
  checks.

## Slice Dependency Graph

```text
S01 -> S02 -> S03 -> S04 -> S05 -> S06 -> S07 -> S08 -> S09
```

Parallelization opportunities:

- None for write-capable execution. Routing ownership, certificate policy,
  live state, LXC exposure, and browser evidence are sequentially dependent.

## Role Ownership Map

- Senior Requirement Engineer: requirement drift, EPIC consistency, acceptance
  criteria.
- Senior System Architect: Traefik ingress ADR, routing ownership, hexagonal
  boundary review.
- Senior Python Automation Developer: domain/application/infrastructure
  implementation slices.
- Senior DevOps Engineer: Docker Swarm, Traefik, LXC, install, and live runtime
  verification.
- Senior Security Engineer: existing CA, TLS, secrets, Infisical, and evidence
  redaction.
- Senior Tester: default and live test strategy, opt-in browser suite, quality
  gates.
- Senior Documentation Engineer: workflow, arc42, ADR alignment, final report.
- Greenpath Recovery Lead: single-threaded repair loop and blocker
  prioritization.
- Failure Classification Expert: typed blocker classification.
- Evidence Auditor: evidence completeness and redaction.

## Failure Classification

- CONFIGURATION
- INFRASTRUCTURE
- LXC
- SWARM
- NETWORK
- TLS
- DNS
- TRAEFIK
- SERVICE
- SECRETS
- TEST
- ARCHITECTURE
- QUALITY
- UNKNOWN

Every failure report must include classification, owner, retry count, evidence
path, next action, and rerun command.

## Quality Gate Expectations

- Run targeted tests first.
- Run `python3 tools/quality_gate.py test` for Python/test/config behavior
  changes.
- Run `python3 tools/quality_gate.py quality` before final push when practical.
- Run `git diff --check` before every checkpoint commit.
- Live commands are not default quality gates and run only in explicitly
  authorized live slices.

## Documentation Synchronization Points

- Create or update ADR for Traefik HTTPS ingress with existing CA before
  implementation claims Traefik ownership.
- Update arc42 deployment/concepts if routing ownership, TLS policy, LXC
  exposure, or evidence semantics change.
- Update workflow reports under `documentation/workflow/reports/**`.
- Do not commit raw `.tiny-swarm-world/evidence/**` runtime evidence.

## Stop Conditions

Stop workflow execution when:

- branch does not match `feature/traefik-https-ingress-existing-ca-20260609`;
- unrelated or unclear worktree changes exist;
- workflow metadata cannot be parsed by S3D;
- required ADR/arc42 changes are missing before implementation;
- live command would run without explicit consent;
- existing CA material is missing, ambiguous, expired, mismatched, or would
  require committing secret material;
- `--api.insecure=true` appears in Traefik configuration;
- `exposedByDefault=false` is missing;
- LXC/Docker state is ambiguous;
- host DNS/hosts mutation lacks explicit operator consent and rollback;
- evidence would include secrets, tokens, raw command output, local IP
  addresses, absolute host paths, or credential-bearing URLs;
- the same blocker repeats after a fix;
- the repair loop reaches 10 iterations;
- documentation would claim unverified live success.

## Uncertainty Escalation Rules

- Requirement conflict: Senior Requirement Engineer and Root Architect.
- Routing ownership or ADR conflict: Senior System Architect.
- Existing CA, TLS, or secret exposure risk: Senior Security Engineer.
- LXC/Docker/Traefik runtime ambiguity: Senior DevOps Engineer.
- Quality failure: Senior Tester and Quality Gate owner.
- Unknown blocker: Failure Classification Expert, then Root Architect.

## Commit And Push Plan

- Do not push to `main`.
- Workflow branch: `feature/traefik-https-ingress-existing-ca-20260609`.
- Workflow creation may be committed as one workflow-scoped commit after
  `git diff --check` passes.
- During workflow execute, each implementation or repair slice gets its own
  checkpoint commit.
- Do not commit ignored local CA private material, live evidence, local
  environment files, host resolver files, or secrets.
- Push only as workflow checkpoint push, not `push auto`, and never create or
  merge a PR unless a later explicit command authorizes that flow.

## Definition Of Done

- Active workflow exists at `documentation/workflow/workflow.md` and is
  released for workflow execute.
- Context pack exists and records governing hashes.
- ADR/arc42 authorize Traefik ingress before implementation changes.
- Traefik routes configured services through HTTPS using existing CA material.
- LXC public exposure is limited to 80 and 443.
- Hostname resolution works or is blocked with precise remediation.
- `./install.sh --confirm-reset` succeeds or stops with classified blocker.
- Live browser/TLS verification passes with explicit opt-in or stops with
  redacted evidence.
- Secrets inventory and Infisical coverage are complete without exposing
  values.
- Final report distinguishes verified facts from planned or blocked work.

## Handoff To Workflow Execute

Before write-capable execution:

```bash
git status --short --branch
git branch --show-current
git show-ref --verify --quiet refs/heads/feature/traefik-https-ingress-existing-ca-20260609
```

Recommended execution sequence:

```bash
git diff --check
python3 tools/quality_gate.py test
./install.sh --confirm-reset
TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live
git diff --check
```

Operator-provided ignored inputs are expected for existing CA material,
certificate/key references, Infisical login material, and any local DNS/hosts
fallback approval. The workflow must stop rather than invent or commit those
values.

## arc42 Check Status

Checked during workflow creation. Current arc42 deployment view and
service-access ADR defer Traefik and TLS automation. This workflow therefore
requires S01 to create/update the Traefik ingress decision and update arc42
before implementation slices claim Traefik behavior as implemented.
