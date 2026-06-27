# Workflow: Remove Unused PortVmRepositoryYaml

Workflow ID: `remove-port-vm-repository-yaml-v1.0.0`
Branch: `fix/workflow-remove-port-vm-repository-yaml-20260627`
Created: 2026-06-27
Status: Ready for `workflow execute`

## Executive Summary

`PortVmRepositoryYaml` appears to be a dormant infrastructure adapter. Repository-wide static search found the concrete class only in
`src/tiny_swarm_world/infrastructure/adapters/repositories/vm_repository_yaml.py` and in
`documentation/architecture/responsibility-separation-analysis.md`. The abstract `PortVmRepository` port remains used by command-builder code and by the command workflow's `_EmptyVmRepository`, so this workflow removes only the unused YAML adapter and any stale architecture documentation reference after verification.

## Requirement Clarification

- Original Request: Search usage of `PortVmRepositoryYaml` inside the system. If it is no longer needed, run `workflow create` to remove it safely.
- Interpreted Intent: Create an executable cleanup workflow for removing the unused concrete YAML VM repository adapter while preserving the active VM repository port and command-builder behavior.
- Change Type: Product source cleanup with architecture documentation synchronization.
- Affected Process Strand: Workflow creation, then workflow execution.
- Affected Architecture Area: Infrastructure repositories, Platform Provisioning documentation, hexagonal boundary checks.
- Explicit Requirements: Verify usage first; do not remove if still required; create a workflow when unused.
- Implicit Requirements: Preserve Linux/WSL-only baseline; avoid live infrastructure commands; keep domain and application independent from infrastructure.
- Assumptions: The concrete YAML adapter is not runtime-wired because no import or composition registration references it.
- Non-Goals: Remove `PortVmRepository`; remove `_EmptyVmRepository`; change command-builder semantics; run live LXD, Incus, Docker, Swarm, Portainer, Nexus, Jenkins, Pulsar, SonarQube, or socat commands.
- Risks: Stale documentation could continue to claim ownership of a removed file; tests may rely on import discovery rather than direct references; a hidden dynamic import would not be found by text search.
- Open Questions: None blocking.
- Blocking Questions: None.
- Confidence Level: 94 percent.
- Decision: `READY_FOR_WORKFLOW`.

## Five-Role Review

- Senior Requirement Engineer: Requirement is narrow and acceptance criteria are testable through search, source deletion, documentation sync, and quality gates.
- Senior System Architect: Removing an unused infrastructure adapter is compatible with hexagonal architecture when the application port stays intact and composition remains unchanged.
- Senior Python Automation Developer: No runtime behavior should change if the adapter is not imported, registered, or instantiated. Verify with targeted tests and typecheck.
- Senior React Frontend Developer: No browser React or frontend module impact. Console/status UI is not affected.
- Senior Tester: Use static search before and after removal, targeted architecture tests, and the repository quality gate where practical.

## Execution Profile

`executionProfile=FULL_PATH`

Reason: The workflow plans product source deletion in `src/tiny_swarm_world/infrastructure` and architecture documentation synchronization. This can affect package imports, type checking, and architecture documentation even though the implementation scope is small.

## Target Picture

After execution:

- `src/tiny_swarm_world/infrastructure/adapters/repositories/vm_repository_yaml.py` is removed if no runtime usage is found.
- `PortVmRepository` remains available for command-builder strategies and `_EmptyVmRepository`.
- Architecture documentation no longer lists the removed adapter as a current Platform Provisioning source file.
- Static search for `PortVmRepositoryYaml` returns no product or documentation references except workflow evidence, if any.
- Quality checks pass or any failure is classified through the repository quality rules.

## Verified Baseline

Static search performed during workflow creation:

```text
rg -n "PortVmRepositoryYaml|port_vm_repository_yaml|PortVm" .
```

Relevant findings:

- Concrete class definition: `src/tiny_swarm_world/infrastructure/adapters/repositories/vm_repository_yaml.py`
- Documentation reference: `documentation/architecture/responsibility-separation-analysis.md`
- Active port usage: `src/tiny_swarm_world/application/ports/repositories/port_vm_repository.py`
- Active port consumers: command-builder VM parameter strategies and `CommandWorkflow`.
- Runtime fallback implementation: `_EmptyVmRepository` in `src/tiny_swarm_world/infrastructure/adapters/command_runner/command_workflow.py`
- No import or composition reference to `PortVmRepositoryYaml` was found.

arc42 check status:

- Checked `documentation/arc42/02_constraints.adoc`: no direct `PortVmRepositoryYaml` reference.
- Checked `documentation/arc42/05_building_blocks.adoc`: retained VM-named command-template infrastructure is described as dormant legacy command-template infrastructure; no direct adapter reference.
- Checked `documentation/arc42/11_risks_and_debt.adoc`: retained VM-named helpers are documented as legacy command-template infrastructure; no direct adapter reference.
- No arc42 file update is required by workflow creation. Execution must update arc42 only if implementation findings change architecture claims.

## Scope

In scope:

- Verify concrete adapter usage one more time during execution.
- Remove `src/tiny_swarm_world/infrastructure/adapters/repositories/vm_repository_yaml.py` when unused.
- Update `documentation/architecture/responsibility-separation-analysis.md` to remove or revise the stale file ownership reference.
- Run targeted checks and required quality gates.

Out of scope:

- Replacing `PortVmRepository` with a different persistence abstraction.
- Changing command-builder strategy behavior.
- Reintroducing Multipass support.
- Live infrastructure execution.
- Browser frontend or React work.
- Java, Maven, Spring Boot, Gradle, JUnit, or ArchUnit changes.

## Architecture Constraints

- Preserve hexagonal architecture.
- Domain must not import application or infrastructure modules.
- Application services and ports must not depend on concrete infrastructure adapters.
- Infrastructure adapters may implement application ports.
- Standard concrete wiring remains in `src/tiny_swarm_world/infrastructure/composition.py`.
- Do not move adapter construction into application services.
- Use POSIX command examples in documentation and workflow evidence.

## Python Automation Assessment

The implementation is expected to be a deletion of a concrete infrastructure adapter plus documentation sync. The port remains because command-builder code still depends on `PortVmRepository`. No migration is needed unless execution discovers hidden imports, tests, or composition wiring.

## Frontend Assessment

No frontend, console/status UI, browser React, state, or API client work is planned. The Senior React Frontend Developer role is an N/A impact review for this workflow.

## Test Strategy

Targeted development checks:

```bash
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
```

Required completion gate when practical:

```bash
python3 tools/quality_gate.py quality
```

Documentation-only fallback is not sufficient because the workflow removes Python source. If the full gate cannot run, execution must report the exact command failure or environment blocker.

## Resilience Requirements

- Do not run live infrastructure commands.
- Do not delete the active `PortVmRepository` port or runtime fallback implementation.
- Stop if dynamic usage, composition usage, tests, or documentation prove the adapter is still required.
- Preserve user changes and stop on unrelated or unclear local modifications.

## Ordered Slices

### Slice 01: Verify Usage And Remove Adapter

Purpose: Confirm the concrete YAML adapter is unused and remove only that adapter.

Prerequisites:

- Active branch is `fix/workflow-remove-port-vm-repository-yaml-20260627`.
- Working tree has no unrelated or unclear changes.
- Static usage search confirms no concrete adapter consumers.

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/vm_repository_yaml.py"
affected_modules:
  - "tiny_swarm_world.infrastructure.adapters.repositories"
affected_contracts:
  - "PortVmRepository implementation set"
dependencies: []
parallel_group: "A"
file_locks:
  - "src/tiny_swarm_world/infrastructure/adapters/repositories/vm_repository_yaml.py"
contract_locks:
  - "tiny_swarm_world.application.ports.repositories.port_vm_repository.PortVmRepository"
architecture_locks:
  - "hexagonal infrastructure adapter boundary"
quality_gates:
  targeted:
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "checked; update only if execution changes architecture claims"
  adr: "not required unless adapter removal exposes a broader persistence decision"
stop_conditions:
  - "PortVmRepositoryYaml has a runtime import, composition registration, test dependency, or dynamic loading path."
  - "Removing the adapter requires changing application or domain imports."
  - "The port itself appears unused and scope would expand beyond the concrete adapter."
```

Done criteria:

- `PortVmRepositoryYaml` source file is removed.
- `PortVmRepository` remains in place.
- Search confirms no stale concrete adapter imports remain.

### Slice 02: Synchronize Architecture Documentation

Purpose: Remove stale architecture ownership references to the deleted adapter and keep Platform Provisioning documentation accurate.

Prerequisites:

- Slice 01 completed or explicitly determined that no source removal is allowed.

```yaml
slice_id: "02"
profile: "NORMAL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "documentation/architecture/responsibility-separation-analysis.md"
  - "documentation/arc42/02_constraints.adoc"
  - "documentation/arc42/05_building_blocks.adoc"
  - "documentation/arc42/11_risks_and_debt.adoc"
affected_modules: []
affected_contracts: []
dependencies:
  - "01"
parallel_group: "B"
file_locks:
  - "documentation/architecture/responsibility-separation-analysis.md"
  - "documentation/arc42/**"
contract_locks: []
architecture_locks:
  - "Platform Provisioning responsibility map"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "checked during workflow creation; update if source removal invalidates existing text"
  adr: "not required unless a new architectural decision is discovered"
stop_conditions:
  - "Documentation would need to claim unverified runtime behavior."
  - "Removing the file reference conflicts with an EPIC or ADR source of truth."
```

Done criteria:

- Stale references to the deleted adapter are removed or rewritten.
- arc42 files are checked and updated only when needed.
- Documentation does not present planned behavior as implemented.

### Slice 03: Verification And Evidence

Purpose: Run the targeted and required checks, classify failures, and prepare execution evidence.

Prerequisites:

- Slice 01 and Slice 02 completed.

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Quality Gate Orchestrator"
  - "Senior System Architect"
affected_files:
  - ".codex/evidence/slice-01-distribution.md"
  - ".codex/evidence/slice-01-consolidation.md"
  - ".codex/evidence/slice-02-distribution.md"
  - ".codex/evidence/slice-02-consolidation.md"
affected_modules: []
affected_contracts: []
dependencies:
  - "01"
  - "02"
parallel_group: "C"
file_locks:
  - ".codex/evidence/**"
contract_locks: []
architecture_locks:
  - "quality gate evidence"
quality_gates:
  targeted:
    - "rg -n \"PortVmRepositoryYaml|vm_repository_yaml\" src tests documentation"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py typecheck"
  required:
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "record checked/updated status in execution evidence"
  adr: "record not required or blocker reason"
stop_conditions:
  - "Required quality gate fails and cannot be classified."
  - "Search reveals unexpected adapter usage after deletion."
  - "Evidence files would include secrets or raw live command output."
```

Done criteria:

- Required checks pass or blockers are reported exactly.
- Evidence records distribution, consolidation, arc42 status, and no-live-infrastructure confirmation.
- Final handoff is ready for commit preparation if requested later.

## Slice Dependency Graph

```text
Slice 01 -> Slice 02 -> Slice 03
```

## Parallel Execution

- Can this workflow run in parallel? No, execute slices sequentially.
- Conflicting workflows: Any workflow touching infrastructure repository adapters, VM command-builder behavior, architecture responsibility documents, or arc42 building blocks.
- Shared files: `documentation/architecture/responsibility-separation-analysis.md`, `documentation/arc42/**`, `src/tiny_swarm_world/infrastructure/adapters/repositories/**`.
- Shared infrastructure: None. No live infrastructure validation is allowed.
- Requires isolated worktree: Yes for parallel stream execution; not needed for the sequential main workflow branch.
- Requires serialized live validation: Yes by policy, but this workflow has no live validation.
- Merge-order constraints: Source removal before documentation synchronization before quality evidence.

## Automatic Work Distribution Policy

During `workflow execute`, each slice must be inspected for safe specialist stream decomposition.

Stream map:

- backend: Senior Python Automation Developer for Slice 01.
- frontend: N/A impact review; no React or console/status UI files are planned.
- tests: Senior Tester for Slice 03 and quality gate interpretation.
- runtime: N/A impact review; no live runtime mutation.
- documentation: Senior Documentation Engineer for Slice 02.
- quality: Quality Gate Orchestrator plus Senior Tester for Slice 03.
- architecture: Senior System Architect for all slices.
- security: N/A impact review unless unexpected live command or secret-handling surface is discovered.

Use real Codex subagents where supported. If subagents are unavailable, perform explicit role-based fallback review in the main execution thread. Before implementation, create `.codex/evidence/slice-<number>-distribution.md`. For implemented slices, create `.codex/evidence/slice-<number>-consolidation.md`. Codex remains final integration owner.

Do not parallelize when files overlap, architecture boundaries are unclear, requirements contradict, mandatory order exists, shared migrations or generated-file conflicts appear, a Three Amigos decision marks the slice unsafe for parallelism, secrets handling is unclear, or safety guards would be weakened.

## Git Worktree Execution Rule

The active workflow branch is `fix/workflow-remove-port-vm-repository-yaml-20260627`. Parallel execution streams, if later authorized, must use isolated worktrees and branches named:

```text
fix/workflow-remove-port-vm-repository-yaml-20260627-slice-<number>-<stream>
```

Stream workers must not merge directly to the workflow branch. Codex consolidates accepted results after evidence and tests pass.

## Quality-Gate Expectations

Use `QUALITY.md` as authority.

- Targeted checks first: `python3 tools/quality_gate.py arch-tests`, `python3 tools/quality_gate.py typecheck`, and focused static search.
- Required full gate: `python3 tools/quality_gate.py quality`.
- Documentation check: `git diff --check`.
- Do not run live infrastructure commands.
- Do not weaken `.importlinter`, architecture tests, type checks, or unit tests.

## Documentation Synchronization Points

- Update `documentation/architecture/responsibility-separation-analysis.md` if the adapter is removed.
- Check arc42 constraints, building blocks, and risks/debt after removal.
- Do not add an ADR unless execution discovers a broader architectural decision beyond deleting an unused adapter.

## Stop Conditions

Stop and report if:

- `PortVmRepositoryYaml` is discovered in runtime wiring, tests, dynamic loading, or composition.
- The removal would require deleting or changing `PortVmRepository`.
- Application or domain code would need to import infrastructure to compensate.
- Live infrastructure commands are required.
- Documentation sources conflict about whether the adapter is current behavior.
- Quality command authority cannot be verified from `QUALITY.md`.
- Required quality gates fail and cannot be classified.
- Unrelated or unclear local changes appear.

## Definition Of Done

- Concrete unused adapter removed or a documented blocker explains why it remains.
- Stale documentation references synchronized.
- `PortVmRepository` consumers remain intact.
- Static search confirms no concrete adapter references remain outside execution evidence.
- Targeted and required quality gates are run and reported.
- No live infrastructure command is executed.

## Handoff To Workflow Execute

`workflow execute` may proceed on branch `fix/workflow-remove-port-vm-repository-yaml-20260627` after verifying:

```bash
git branch --show-current
git status --short
```

Expected active branch:

```text
fix/workflow-remove-port-vm-repository-yaml-20260627
```
