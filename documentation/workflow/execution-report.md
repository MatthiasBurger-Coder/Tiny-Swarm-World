# Workflow Execution Report

Workflow: `fresh-install-reset-full-deploy-v1.1.0`

Status: Slice 05 completed; ready to execute Slice 06.

## Creation Evidence

* Workflow branch: `feature/workflow-install-reset-reinstall-20260602`
* Branch ref verified before artifact creation.
* Active branch verified before artifact creation.
* Existing `documentation/workflow` was regenerated.
* Workflow was updated to require mandatory reset before setup and full
  deployment acceptance including service-access dashboard/index assets.
* Follow-up S3D preflight reported an orchestration blocker before
  write-capable execution: execution profile was too weak, prose
  parallelization contradicted YAML dependencies, and file locks did not cover
  all affected paths.
* Workflow metadata was repaired to `FULL_PATH`, serial slice order, and
  explicit file locks for all declared affected write paths.

## Commands Run During Creation

```bash
git status --short --branch
git branch --show-current
git show-ref --verify --quiet refs/heads/feature/workflow-install-reset-reinstall-20260602
rg ...
sed ...
sha256sum ...
rm -rf documentation/workflow && mkdir -p documentation/workflow/reports
```

No live infrastructure commands were run.

## Slice 05 Checkpoint

Slice ID: `05`

Title: Complete Full Deployment Durchstich

Responsible agent roles:

* Senior Python Automation Developer
* Senior Tester
* Senior DevOps Engineer
* Senior System Architect

Outcome:

* Existing setup wiring was verified: the default setup profile includes
  `service-access`, and setup phases include preflight, platform bootstrap,
  deployment bootstrap, artifact prepare/verify, deployment apply/verify, and
  platform verify.
* Artifact contracts and composition include the service-access dashboard and
  NGINX images.
* A deterministic publisher regression test now proves that the
  service-access dashboard build context packages `Dockerfile` plus
  `index.html`, and that the NGINX build context packages `Dockerfile` plus
  `default.conf`, without live LXC or Docker execution.
* Deployment apply includes `deployment:service-access-stack`.
* Deployment verify includes `deployment:service-access-service-readiness`.
* Setup workflow result handling already stops on blocked or failed selected
  phases, so install success cannot bypass selected artifact, stack, or
  readiness failures.
* arc42 runtime documentation and the existing service-access ADR were
  synchronized with the verified reset and deployment sequence.
* No live end-to-end installation success is claimed without an explicit live
  run.

Quality gates:

```bash
PATH=.venv/bin:$PATH PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
PATH=.venv/bin:$PATH PYTHONPATH=src python3 -m unittest tests.domain.deployment.test_service_stack_contract tests.domain.artifacts.test_container_image_contract
PATH=.venv/bin:$PATH PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_service_stack_plan tests.application.services.deployment.test_verify_swarm_service_readiness tests.application.services.deployment.test_deployment_workflows
PATH=.venv/bin:$PATH PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml
PATH=.venv/bin:$PATH python3 tools/quality_gate.py lint
PATH=.venv/bin:$PATH python3 tools/quality_gate.py typecheck
git diff --check
PATH=.venv/bin:$PATH python3 tools/quality_gate.py quality
```

Result: passed.

Full quality result: lint, arch-lint, arch-tests, typecheck, and 637 unit
tests passed.

Checkpoint commit: `acc7b0d`

Rollback reference: `de20f2d`

arc42Updated: true.

adrUpdated: existing ADR synchronized; no new ADR required.

Push result: pushed to `origin/feature/workflow-install-reset-reinstall-20260602`.

No live infrastructure commands were run.

## Quality Evidence

Passed during workflow artifact creation:

```bash
git diff --check
```

Full quality gate during initial creation was reserved for implementation or
commit readiness and was not executed for the original governance-only workflow
artifact update:

```bash
python3 tools/quality_gate.py quality
```

## Governance Unblock: Slice 01 Infra Marker Locks

During Slice 01 execution, the required full quality gate initially blocked on
pre-existing architecture documentation drift:

* `infra/prepare/README.md` was missing.
* `infra/platform/README.md`, `infra/artifacts/README.md`,
  `infra/deployment/README.md`, and `infra/shared/README.md` were missing.
* `infra/prepare/portainer/README.md` and `infra/prepare/nexus/README.md`
  were also required by the retired-helper documentation tests.

Typed routing classified the failure as documentation governance drift surfaced
through the `test` stage, with a Slice 01 file-lock conflict. The workflow was
amended so Slice 01 explicitly owns the marker documentation required by the
existing architecture tests.

Files added or updated:

* `documentation/workflow/workflow.md`
* `documentation/workflow/context-pack.md`
* `documentation/workflow/context-pack.json`
* `infra/prepare/README.md`
* `infra/prepare/portainer/README.md`
* `infra/prepare/nexus/README.md`
* `infra/platform/README.md`
* `infra/artifacts/README.md`
* `infra/deployment/README.md`
* `infra/shared/README.md`

Verification:

```bash
python3 -m json.tool documentation/workflow/context-pack.json >/dev/null
PATH=.venv/bin:$PATH PYTHONPATH=src python3 -m unittest tests.architecture.test_legacy_surface_documentation tests.architecture.test_infra_responsibility_boundaries
git diff --check
PATH=.venv/bin:$PATH python3 tools/quality_gate.py quality
```

Result:

* Context-pack JSON parsed successfully.
* Targeted architecture documentation tests passed: 15 tests.
* Full quality gate passed: lint, arch-lint, arch-tests, typecheck, and 616
  unit tests.
* No live infrastructure commands were run.

## Slice 01 Checkpoint

Slice ID: `01`

Title: Define Fresh-Install Destructive Scope

Responsible agent roles:

* Senior System Architect
* Senior Requirement Engineer
* Senior DevOps Engineer

Outcome:

* Fresh install ownership boundary documented.
* Update/reconcile preservation documented.
* Mandatory reset-first install behavior selected for the active workflow.
* Full deployment Durchstich includes service-access dashboard/index
  acceptance.
* Destructive reset confirmation remains mandatory.
* Infra boundary marker documentation restored and owned by Slice 01.

Quality gates:

```bash
PYTHONPATH=src python3 -m unittest tests.architecture.test_legacy_surface_documentation tests.architecture.test_infra_responsibility_boundaries
git diff --check
PATH=.venv/bin:$PATH python3 tools/quality_gate.py quality
```

Result: passed.

Checkpoint commit: `9d3b6e6`

Rollback reference: `32c1103`

arc42Updated: checked and already synchronized in the Slice 01 scope.

adrUpdated: not required; existing platform separation and destructive
reset/destroy policy decisions cover the Slice 01 scope.

Push result: pushed to `origin/feature/workflow-install-reset-reinstall-20260602`.

## Slice 02 Checkpoint

Slice ID: `02`

Title: Implement Reset/Destroy Step Contracts

Responsible agent roles:

* Senior Python Automation Developer
* Senior System Architect
* Senior Tester

Outcome:

* Added `PortManagedNodeTeardown` as an application port for managed node reset
  and destroy operations.
* Added reset/destroy managed-node steps behind `NodeProviderSelectionService`.
* Provider selection, missing-node, missing-port, provider mismatch, and backend
  mismatch blockers stop before adapter calls.
* `PlatformWorkflowResult.blocked` can preserve `executed=True` only for
  post-apply blocked paths; pre-apply/direct fail-closed blockers remain
  `executed=False`.
* Reset/destroy workflow regression tests use fakes only and prove exact
  confirmation, step verification, pre-apply blocking, missing evidence, failed
  verification, and direct post-apply blocked evidence.

Quality gates:

```bash
PATH=.venv/bin:$PATH PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows tests.application.services.platform.test_node_provider_selection
PATH=.venv/bin:$PATH PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition.TestComposition.test_composed_default_lxc_init_without_live_consent_fails_closed_before_runtime_probe tests.infrastructure.test_composition.TestComposition.test_composed_default_lxc_init_workflow_blocks_before_live_step_execution
PATH=.venv/bin:$PATH python3 tools/quality_gate.py lint
PATH=.venv/bin:$PATH python3 tools/quality_gate.py typecheck
git diff --check
PATH=.venv/bin:$PATH python3 tools/quality_gate.py quality
```

Result: passed.

Full quality result: lint, arch-lint, arch-tests, typecheck, and 629 unit tests
passed.

Checkpoint commit: `d85939f`

Rollback reference: `14d1e22`

arc42Updated: false.

adrUpdated: false.

Push result: pushed to `origin/feature/workflow-install-reset-reinstall-20260602`.

No live infrastructure commands were run.

## Slice 03 Checkpoint

Slice ID: `03`

Title: Add LXC-Native Destructive Infrastructure Adapter

Responsible agent roles:

* Senior DevOps Engineer
* Senior Python Automation Developer
* Senior Tester

Outcome:

* `LxcNodeProvider` now implements the managed-node teardown port in addition
  to the existing node lifecycle port.
* Reset and destroy use only exact-name LXD/Incus lookups for configured Tiny
  Swarm World nodes; no broad provider enumeration or delete-all operation was
  added.
* Teardown is two-phase: every requested node is selected, configured,
  looked up, marker/profile/image verified, and live-consent checked before any
  delete command is issued.
* Already absent managed nodes are verified as successful reset/destroy
  evidence.
* Existing nodes with missing or mismatched Tiny Swarm World markers block
  before mutation.
* Delete commands are scoped to exact configured names with `--force`, and
  absence is verified by a second exact-name lookup.
* A delete command failure is rechecked with the same scoped lookup; if the
  node is already absent, the operation is treated as idempotent success.
* Composition wires the same `LxcNodeProvider` instance as both
  `node_lifecycle` and `managed_node_teardown`, and reset/destroy workflows now
  contain the managed-node teardown steps.
* Subagent findings were incorporated: no partial multi-node delete before full
  preflight success, idempotent delete-race handling, and teardown-specific
  fake-runner command guards.

Quality gates:

```bash
PATH=.venv/bin:$PATH PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider tests.infrastructure.test_composition
git diff --check
PATH=.venv/bin:$PATH python3 tools/quality_gate.py quality
```

Result: passed.

Full quality result: lint, arch-lint, arch-tests, typecheck, and 631 unit tests
passed.

Checkpoint commit: `d28becf`

Rollback reference: `1026437`

arc42Updated: false; pending Slice 05 documentation synchronization.

adrUpdated: false.

Push result: pushed to `origin/feature/workflow-install-reset-reinstall-20260602`.

No live infrastructure commands were run.

## Slice 04 Checkpoint

Slice ID: `04`

Title: Make install.sh Fresh-Install By Default

Responsible agent roles:

* Senior Python Automation Developer
* Senior DevOps Engineer
* Senior Tester

Outcome:

* `install.sh` now prompts the operator for the exact
  `RESET_TINY_SWARM_PLATFORM` destructive confirmation before starting the
  fresh-install reset prelude.
* The wrapper runs `platform reset --live --confirm RESET_TINY_SWARM_PLATFORM`
  before `setup run --live`.
* Setup starts only after reset exits successfully.
* Reset failures stop installation, write `reset-run.exit`, append
  `reset_exit` and `setup_skipped_due_to_reset_failure=yes` to context, and
  exit with the reset code.
* Setup failures still write `setup-run.exit`, append `setup_exit`, and exit
  with the setup code.
* Evidence now distinguishes `reset-run.log`, `reset-run.exit`,
  `setup-run.log`, `setup-run.exit`, and context markers.
* Deterministic shell-level tests use a temporary fake repository plus fake
  `script` and `python3` commands; no live infrastructure commands are run.
* Installation documentation now describes reset-before-setup, failure-stop
  behavior and the concrete evidence files.

Quality gates:

```bash
bash -n install.sh
PATH=.venv/bin:$PATH PYTHONPATH=src python3 -m unittest tests.test_install_script tests.test_package_entrypoint
git diff --check -- install.sh documentation/user_guide/installation.adoc tests/test_install_script.py
PATH=.venv/bin:$PATH python3 tools/quality_gate.py quality
```

Result: passed.

Full quality result: lint, arch-lint, arch-tests, typecheck, and 636 unit tests
passed.

Checkpoint commit: `1c59023`

Rollback reference: `444dcba`

arc42Updated: false; pending Slice 05 documentation synchronization.

adrUpdated: false.

Push result: pushed to `origin/feature/workflow-install-reset-reinstall-20260602`.

No live infrastructure commands were run.
