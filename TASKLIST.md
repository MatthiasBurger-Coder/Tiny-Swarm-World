# TASKLIST
Ordered remediation plan derived from AUDIT_REPORT findings.

## Phase 1: Repository discovery and audit baseline
### Task T-001: Python package/import model is not runnable from repository root
- Task ID: T-001
- Phase: Phase 1: Repository discovery and audit baseline
- Status: TODO
- Rationale: Resolve F-001 (Critical, Python/Entrypoint).
- Inputs: AUDIT_REPORT.md (F-001), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: None.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Core modules import `application`, `domain`, and `infrastructure` as top-level packages, but repository layout places them under `docker/`, so default execution/test discovery from repo root fails without PYTHONPATH hacks. is resolved and acceptance criteria for F-001 are met.
### Task T-002: Repository mixes active and dead orchestration implementations
- Task ID: T-002
- Phase: Phase 1: Repository discovery and audit baseline
- Status: TODO
- Rationale: Resolve F-003 (High, Maintainability).
- Inputs: AUDIT_REPORT.md (F-003), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: F-001.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: `docker/swarm/prepere.py` imports non-existent modules and contains commented execution paths, while `docker/tiny_swarm_world.py` contains different active flow. is resolved and acceptance criteria for F-003 are met.
### Task T-003: Documentation is largely placeholder/outdated versus implementation
- Task ID: T-003
- Phase: Phase 1: Repository discovery and audit baseline
- Status: TODO
- Rationale: Resolve F-011 (High, Documentation).
- Inputs: AUDIT_REPORT.md (F-011), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: F-001, F-008.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Critical docs contain placeholders, typos, or unrelated architecture text not tied to repository automation. is resolved and acceptance criteria for F-011 are met.

## Phase 2: Environment and dependency normalization
### Task T-004: Python package/import model is not runnable from repository root
- Task ID: T-004
- Phase: Phase 2: Environment and dependency normalization
- Status: TODO
- Rationale: Resolve F-001 (Critical, Python/Entrypoint).
- Inputs: AUDIT_REPORT.md (F-001), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: None.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Core modules import `application`, `domain`, and `infrastructure` as top-level packages, but repository layout places them under `docker/`, so default execution/test discovery from repo root fails without PYTHONPATH hacks. is resolved and acceptance criteria for F-001 are met.
### Task T-005: Test suite is not runnable on clean checkout and has low signal
- Task ID: T-005
- Phase: Phase 2: Environment and dependency normalization
- Status: TODO
- Rationale: Resolve F-012 (High, Tests).
- Inputs: AUDIT_REPORT.md (F-012), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: F-001.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Tests fail at collection without PYTHONPATH and dependencies; several tests are duplicated/skipped or not asserting runtime behavior. is resolved and acceptance criteria for F-012 are met.
### Task T-006: Configuration contracts are implicit and unvalidated
- Task ID: T-006
- Phase: Phase 2: Environment and dependency normalization
- Status: TODO
- Rationale: Resolve F-013 (Medium, Configuration).
- Inputs: AUDIT_REPORT.md (F-013), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: F-011.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Many required parameters (VM specs, ports, credentials, repo URLs) are hardcoded in YAML/scripts without schema validation or documented overrides. is resolved and acceptance criteria for F-013 are met.

## Phase 3: Entrypoint and orchestration repair
### Task T-007: Python package/import model is not runnable from repository root
- Task ID: T-007
- Phase: Phase 3: Entrypoint and orchestration repair
- Status: TODO
- Rationale: Resolve F-001 (Critical, Python/Entrypoint).
- Inputs: AUDIT_REPORT.md (F-001), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: None.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Core modules import `application`, `domain`, and `infrastructure` as top-level packages, but repository layout places them under `docker/`, so default execution/test discovery from repo root fails without PYTHONPATH hacks. is resolved and acceptance criteria for F-001 are met.
### Task T-008: No implemented stack deployment in main orchestration
- Task ID: T-008
- Phase: Phase 3: Entrypoint and orchestration repair
- Status: TODO
- Rationale: Resolve F-008 (Critical, Deployment).
- Inputs: AUDIT_REPORT.md (F-008), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `python -m <canonical_entrypoint> --dry-run && <smoke-check-command>` plus targeted checks for changed scripts/configs.
- Dependencies: F-007.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Main python flow stops after swarm join and does not deploy Portainer/Nexus/Jenkins/RabbitMQ/SonarQube/Swagger/NGINX. is resolved and acceptance criteria for F-008 are met.
### Task T-009: Error propagation in command execution hides failures
- Task ID: T-009
- Phase: Phase 3: Entrypoint and orchestration repair
- Status: TODO
- Rationale: Resolve F-014 (Medium, Python).
- Inputs: AUDIT_REPORT.md (F-014), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: F-007.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Command execution catches exceptions per command and continues; higher-level services do not fail fast when critical steps fail. is resolved and acceptance criteria for F-014 are met.

## Phase 4: Multipass VM lifecycle repair
### Task T-010: Canonical orchestration hard-resets all VMs on every run
- Task ID: T-010
- Phase: Phase 4: Multipass VM lifecycle repair
- Status: TODO
- Rationale: Resolve F-002 (Critical, Multipass).
- Inputs: AUDIT_REPORT.md (F-002), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `python -m <canonical_entrypoint> --dry-run && <smoke-check-command>` plus targeted checks for changed scripts/configs.
- Dependencies: F-001.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Startup sequence always executes cleanup (`multipass delete --all` + `multipass purge`) before provisioning. is resolved and acceptance criteria for F-002 are met.
### Task T-011: Repository mixes active and dead orchestration implementations
- Task ID: T-011
- Phase: Phase 4: Multipass VM lifecycle repair
- Status: TODO
- Rationale: Resolve F-003 (High, Maintainability).
- Inputs: AUDIT_REPORT.md (F-003), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: F-001.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: `docker/swarm/prepere.py` imports non-existent modules and contains commented execution paths, while `docker/tiny_swarm_world.py` contains different active flow. is resolved and acceptance criteria for F-003 are met.

## Phase 5: Networking and WSL2/Linux compatibility repair
### Task T-012: Netplan generation and transfer path assumptions are fragile
- Task ID: T-012
- Phase: Phase 5: Networking and WSL2/Linux compatibility repair
- Status: TODO
- Rationale: Resolve F-004 (High, Networking).
- Inputs: AUDIT_REPORT.md (F-004), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `python -m <canonical_entrypoint> --dry-run && <smoke-check-command>` plus targeted checks for changed scripts/configs.
- Dependencies: F-001.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Netplan YAML is generated as `cloud-init-manager.yaml` in CWD-dependent path, but transfer command assumes `config/cloud-init-manager.yaml` relative to execution directory. is resolved and acceptance criteria for F-004 are met.
### Task T-013: WSL2/Linux networking procedure is incomplete and non-idempotent
- Task ID: T-013
- Phase: Phase 5: Networking and WSL2/Linux compatibility repair
- Status: TODO
- Rationale: Resolve F-005 (High, Networking).
- Inputs: AUDIT_REPORT.md (F-005), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `python -m <canonical_entrypoint> --dry-run && <smoke-check-command>` plus targeted checks for changed scripts/configs.
- Dependencies: F-004.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Networking relies on ad-hoc socat/iptables commands without lifecycle management or cleanup guarantees. is resolved and acceptance criteria for F-005 are met.

## Phase 6: Docker installation readiness repair
### Task T-014: Docker install sequence lacks daemon readiness and robust retry controls
- Task ID: T-014
- Phase: Phase 6: Docker installation readiness repair
- Status: TODO
- Rationale: Resolve F-006 (High, Docker).
- Inputs: AUDIT_REPORT.md (F-006), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `python -m <canonical_entrypoint> --dry-run && <smoke-check-command>` plus targeted checks for changed scripts/configs.
- Dependencies: F-002.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Docker installation runs package commands but does not verify daemon active state before swarm operations. is resolved and acceptance criteria for F-006 are met.

## Phase 7: Swarm bootstrap and cluster verification repair
### Task T-015: Swarm bootstrap flow is not idempotent and has weak result parsing
- Task ID: T-015
- Phase: Phase 7: Swarm bootstrap and cluster verification repair
- Status: TODO
- Rationale: Resolve F-007 (Critical, Swarm).
- Inputs: AUDIT_REPORT.md (F-007), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `python -m <canonical_entrypoint> --dry-run && <smoke-check-command>` plus targeted checks for changed scripts/configs.
- Dependencies: F-006.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Manager init always calls `docker swarm init`; token/IP extraction parses positional output structures instead of validated schema. is resolved and acceptance criteria for F-007 are met.

## Phase 8: Compose stack and service deployment repair
### Task T-016: No implemented stack deployment in main orchestration
- Task ID: T-016
- Phase: Phase 8: Compose stack and service deployment repair
- Status: TODO
- Rationale: Resolve F-008 (Critical, Deployment).
- Inputs: AUDIT_REPORT.md (F-008), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `python -m <canonical_entrypoint> --dry-run && <smoke-check-command>` plus targeted checks for changed scripts/configs.
- Dependencies: F-007.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Main python flow stops after swarm join and does not deploy Portainer/Nexus/Jenkins/RabbitMQ/SonarQube/Swagger/NGINX. is resolved and acceptance criteria for F-008 are met.
### Task T-017: Compose assets are inconsistent with swarm/VM execution context
- Task ID: T-017
- Phase: Phase 8: Compose stack and service deployment repair
- Status: TODO
- Rationale: Resolve F-010 (High, Deployment).
- Inputs: AUDIT_REPORT.md (F-010), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `python -m <canonical_entrypoint> --dry-run && <smoke-check-command>` plus targeted checks for changed scripts/configs.
- Dependencies: F-008.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Several compose files bind services to 127.0.0.1 and use host paths unsuitable for remote VM swarm deployment. is resolved and acceptance criteria for F-010 are met.

## Phase 9: Configuration and secret handling normalization
### Task T-018: Portainer/Nexus automation uses hardcoded insecure default credentials
- Task ID: T-018
- Phase: Phase 9: Configuration and secret handling normalization
- Status: TODO
- Rationale: Resolve F-009 (High, Security).
- Inputs: AUDIT_REPORT.md (F-009), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: F-008.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Admin credentials and registry password are embedded in scripts. is resolved and acceptance criteria for F-009 are met.
### Task T-019: Configuration contracts are implicit and unvalidated
- Task ID: T-019
- Phase: Phase 9: Configuration and secret handling normalization
- Status: TODO
- Rationale: Resolve F-013 (Medium, Configuration).
- Inputs: AUDIT_REPORT.md (F-013), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: F-011.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Many required parameters (VM specs, ports, credentials, repo URLs) are hardcoded in YAML/scripts without schema validation or documented overrides. is resolved and acceptance criteria for F-013 are met.

## Phase 10: Test, smoke test, and verification automation
### Task T-020: Test suite is not runnable on clean checkout and has low signal
- Task ID: T-020
- Phase: Phase 10: Test, smoke test, and verification automation
- Status: TODO
- Rationale: Resolve F-012 (High, Tests).
- Inputs: AUDIT_REPORT.md (F-012), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: F-001.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Tests fail at collection without PYTHONPATH and dependencies; several tests are duplicated/skipped or not asserting runtime behavior. is resolved and acceptance criteria for F-012 are met.
### Task T-021: Error propagation in command execution hides failures
- Task ID: T-021
- Phase: Phase 10: Test, smoke test, and verification automation
- Status: TODO
- Rationale: Resolve F-014 (Medium, Python).
- Inputs: AUDIT_REPORT.md (F-014), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: F-007.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Command execution catches exceptions per command and continues; higher-level services do not fail fast when critical steps fail. is resolved and acceptance criteria for F-014 are met.

## Phase 11: Documentation correction and operational handover
### Task T-022: Documentation is largely placeholder/outdated versus implementation
- Task ID: T-022
- Phase: Phase 11: Documentation correction and operational handover
- Status: TODO
- Rationale: Resolve F-011 (High, Documentation).
- Inputs: AUDIT_REPORT.md (F-011), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: F-001, F-008.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Critical docs contain placeholders, typos, or unrelated architecture text not tied to repository automation. is resolved and acceptance criteria for F-011 are met.
### Task T-023: Repository contains non-production leftovers and mixed-language comments
- Task ID: T-023
- Phase: Phase 11: Documentation correction and operational handover
- Status: TODO
- Rationale: Resolve F-015 (Low, Maintainability).
- Inputs: AUDIT_REPORT.md (F-015), current implementation under docker/.
- Files/directories to inspect: `docker/`, `tests/`, `documentation/`, `README.md`.
- Files to modify: Scoped to components tied to this finding; update docs/tests in same task.
- Commands to run: `pytest -q` plus targeted checks for changed scripts/configs.
- Dependencies: None.
- Implementation steps:
  1. Reproduce current failure/limitation.
  2. Apply minimal code/config changes for this finding.
  3. Add/adjust automated validation.
  4. Update related documentation claims.
- Validation steps:
  - Run task-specific command(s).
  - Confirm expected logs/outputs/artifacts.
  - Re-run baseline tests to detect regressions.
- Expected evidence:
  - Updated files in git diff.
  - Command output proving behavior change.
  - Documentation synchronized with implemented flow.
- Rollback considerations:
  - Keep changes isolated by concern.
  - Revert task commit if validation fails or introduces regressions.
- Expected result: Legacy files, typos, and non-English comments reduce clarity and violate stated style expectations. is resolved and acceptance criteria for F-015 are met.
