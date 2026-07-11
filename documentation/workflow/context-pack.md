# Workflow Context Pack

Workflow ID: `workflow-issue-157-final-gaps-20260711`
Version: `workflow-issue-157-final-gaps-v1.0.0`
Issue: `#157 Gateway: Route HTTP services through Traefik using central access configuration`
Branch: `fix/issue-157-final-gaps-20260711`
Baseline: `main@3e0d28db0e59fc3f38929c4b91cac0566ed39fb6`
Process Strand: `workflow create -> workflow execute -> completion audit -> PR readiness`
Execution Profile: `FULL_PATH`
Status: `SLICE_05_AUDIT_PASS_CHECKPOINT_PENDING`

## Orientation

This pack is a navigation aid for closing only the final repository-verifiable
gaps in Issue #157. Root `AGENTS.md`, `QUALITY.md`, ADRs, arc42, source files
and `documentation/workflow/workflow.md` remain authoritative.

The previous dashboard asset workflow was already locally executed and is
replaced by this issue-specific workflow.

## Execution Checkpoint

- Slice 01: `578f5e57d28cc5c6536781d88e88bd6cc7b69cea`.
- Slice 02: `b08e1e266dc5abffdfff6ba0725c8948ec5bd549`.
- Slice 03: `54725a0ff3cc9005459c2277d487e9722e093b3d`.
- Slice 04: `183ccac6143f5f58a904e891fd92abe7d8959ce6`.
- Integrated G2 quality: `PASS`; Ruff, Import Linter, 18 architecture tests,
  Mypy across 471 source files, and 1,361 unittests (1,333 passed, 28 skipped)
  are green.
- All six individual Slice 05 quality commands and the Requirement,
  Architecture, and Test/Evidence completion perspectives pass.
- Independent Slice 05 pre-publication audit: `PASS`; checkpoint pending.
- All Slice 06 publication/check results remain pending.
- Live Selenium is `NOT_RUN`; no current consent or approved prerequisite set
  was supplied, and the referenced ignored environment file was not read.

## Verified Baseline

- Public `main` commit:
  `3e0d28db0e59fc3f38929c4b91cac0566ed39fb6`.
- A dedicated isolated worktree is active; its host-specific absolute path is
  intentionally not persisted.
- Active branch: `fix/issue-157-final-gaps-20260711`.
- Existing central model:
  `tiny_swarm_world.domain.ingress.DesiredHttpsIngress`.
- Existing compose/dashboard consumer:
  `ComposeFileRepositoryYaml`.
- Existing browser contract:
  `tests/live/browser_e2e_contract.py`.
- Existing committed fallback dashboard:
  `infra/config/compose/service-access/dashboard/index.html`.
- No repository EPIC directory; Issue #157 plus the user's final-gap request
  are the requirement source.

## Gate Decision

`READY_FOR_WORKFLOW` at 97 percent confidence.

Non-blocking accepted assumptions:

- routing evidence `result: generated` is not live-readiness evidence;
- UTC timestamp is injectable while list/key ordering is deterministic;
- active conditional routes are not also skipped;
- the referenced local env file does not grant live consent;
- no new ADR is required.

## Affected Areas

- effective access model port exposure;
- conditional route activation and shared-upstream label rendering;
- productive redacted routing evidence;
- atomic ignored local JSON persistence;
- deployment pre-apply composition;
- optional-route integration fixtures;
- dynamic browser expectation and summary semantics;
- renderer-centric dashboard tests and committed fallback drift;
- directly related arc42, user documentation and evidence.

## Forbidden Areas

- Incus/LXC installation and node lifecycle;
- Docker installation or Swarm bootstrap;
- setup phase order;
- Issue #156 direct-port publication;
- DNS/hosts/resolver mutation;
- TLS/certificate lifecycle;
- messaging/RabbitMQ/legacy broker behavior;
- Infisical bootstrap or raw credential values;
- Kubernetes implementation;
- React/browser frontend implementation;
- global test mutation of committed YAML;
- raw `.env` content, secrets, private keys or local topology in evidence;
- opportunistic refactoring.

## Required Roles

- Senior Workflow Architect
- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior Tester
- Senior DevOps Engineer
- Senior Documentation Engineer
- Security / Evidence Reviewer
- Live Evidence Validation Reviewer
- Git Commit Reviewer / Operator
- Issue Completion Auditor

Conditional Console/status UI reviewer: N/A.

Browser React reviewer: forbidden/N/A because no frontend module is involved.

## Slice Graph

```text
01 model seam + optional routes
  +--> 02 routing evidence --------+
  +--> 03 dashboard tests ---------+--> 05 docs/evidence/local quality --> 06 PR/CI/review
  +--> 04 browser matrix ----------+
```

Slices 02, 03 and 04 are the only parallel-eligible group. They require
isolated worktrees and disjoint locks after Slice 01 consolidation.

## Evidence Roots

Committed workflow evidence:

```text
.codex/evidence/workflow-issue-157-final-gaps-20260711/
```

Ignored issue-completion evidence:

```text
.tiny-swarm/evidence/issue-157-final-gaps-20260711/
```

Ignored product routing evidence:

```text
.tiny-swarm-world/evidence/solid-typed-evidence/routing/
  effective-access-model.json
```

Ignored opt-in browser evidence:

```text
.tiny-swarm-world/evidence/solid-typed-evidence/e2e/
```

## Targeted Verification

- `PYTHONPATH=src python3 -m unittest tests.domain.ingress.test_desired_state`
- `PYTHONPATH=src python3 -m unittest tests.integration.test_optional_service_routing`
- `PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_write_effective_access_model_evidence`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_routing_evidence_local_repository`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml`
- `PYTHONPATH=src python3 -m unittest tests.integration.test_service_access_routing`
- `PYTHONPATH=src python3 -m unittest tests.live.browser_e2e_contract`
- `PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live.StaticPostInstallLiveSuiteTest`
- `git diff --check`

## Required Final Quality

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

On a Windows host, run through WSL with the verified workflow worktree as the
working directory. Keep its host-specific absolute path out of committed
evidence.

No command above may require live infrastructure.

## Live Validation

Live Selenium is optional and serialized. It requires explicit current
operator consent, Selenium/browser dependencies, reachable approved
infrastructure and approved credential sources. Missing prerequisites produce
redacted `skipped` evidence and no live pass claim. The selected local env file
must not be read during static execution.

## Governing Inputs

- `AGENTS.md`
- `QUALITY.md`
- `documentation/process/issue-completion-discipline.md`
- `documentation/process/branch-governance.md`
- `.agents/orchestrator/routing-rules.md`
- `.agents/skills/execution-profile-router/SKILL.md`
- `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md`
- `.agents/skills/workflow-authoring/SKILL.md`
- `.agents/skills/workflow-slice/SKILL.md`
- `.agents/skills/engineering-governance/SKILL.md`
- `.agents/skills/arc42-architecture-governance/SKILL.md`
- `.agents/skills/architecture-hexagonal/SKILL.md`
- `.agents/skills/quality-testing-strategy/SKILL.md`
- `.agents/skills/quality-gate-governance/SKILL.md`
- `.agents/skills/s3d-execution-orchestrator/SKILL.md`
- `.agents/skills/issue-completion-auditor/SKILL.md`
- mandatory role definitions named in the workflow;
- Issue #157;
- directly affected source, test, config, CI and arc42 files recorded in
  `context-pack.json`.

## Hash Provenance

SHA-256 values are recorded in `context-pack.json`. The context pack is stale
when a governing hash changes, a listed file moves, branch/baseline differs,
or another workflow acquires an overlapping lock.

## Publication Boundary

Workflow creation publication may commit and push only the regenerated
`documentation/workflow/**` files and this workflow's `.codex/evidence/**`
files. It must not create or merge a PR.

Workflow execution may create the implementation PR in Slice 06 because the
user explicitly requested that lifecycle. Automatic merge is not part of this
workflow.

Authoring publication completed through WSL Git to
`origin/fix/issue-157-final-gaps-20260711`. No PR, merge, deletion or cleanup
was performed.
