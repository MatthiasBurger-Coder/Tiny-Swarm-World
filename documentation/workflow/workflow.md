# Workflow: Agents, Skills, Python Quality And Bash Specialist Alignment

## Executive Summary

This workflow plans a governance-only update for Tiny Swarm World agent and
skill material. The target is to make `.agents/**` and `.codex/**` consistently
reflect that the repository is a Python 3.12, Linux/WSL-only automation project
with a hexagonal architecture and Python quality gates from
`tools/quality_gate.py`.

The workflow also introduces expert-level Bash specialist coverage for shell
scripts and shell snippets without adding new required external quality tools
or running live infrastructure commands.

## Requirement Clarification Record

Original request:

```text
workflow create with subagents:
Ueberarbeite das agents und skills so, damit dieses mit
- Python uebereinstimmt
- Python qualitiy check mit mit quality-gate.py und linter nach hexagonaler Architektur funktion
- Bash spezialisten expert level entsteht
```

Interpreted intent:

- Create an executable workflow for later `workflow execute` work.
- Align agent, role, skill, routing and prompt governance with the Python
  automation architecture.
- Use `tools/quality_gate.py` as quality authority, including `arch-lint` and
  `arch-tests` for hexagonal architecture checks.
- Add Bash specialist ownership and review guidance for shell scripts, shell
  snippets and shell command examples.

Change type:

- Governance, workflow and agent/skill metadata change.

Affected process strand:

- Workflow create.
- Skills and agents governance.
- Quality-gate governance.

Affected architecture area:

- Python hexagonal architecture governance.
- Agent routing and role ownership.
- Bash/POSIX shell review ownership.
- Documentation and arc42 governance alignment.

Explicit requirements:

- Revise agents and skills to match Python as the primary architecture.
- Use Python quality checks with `tools/quality_gate.py`.
- Include hexagonal architecture linter and architecture-test coverage.
- Create expert-level Bash specialist coverage.
- Use subagents for review and planning.

Implicit requirements:

- Keep root `AGENTS.md` and `QUALITY.md` authoritative.
- Keep Java material scoped to the deployment example under `src/main/java`.
- Do not make Gradle, Maven, JUnit or ArchUnit the default project quality
  path.
- Do not run live infrastructure commands.
- Do not add required `shellcheck` or `shfmt` gates unless `QUALITY.md` is
  explicitly changed by a future requirement.
- Preserve `.codex` reusable template boundaries while adding project-specific
  guards where needed.

Assumptions accepted for workflow creation:

- No `documentation/epics` source exists in this repository at workflow-create
  time, so EPIC traceability is recorded as a gap, not a blocker.
- "Bash specialist" means role, skill, routing, callable agent and durable
  subagent documentation coverage.
- `shellcheck` and `shfmt` may be documented as optional diagnostics only.
- Stale Java/Gradle/JUnit/ArchUnit wording should be constrained to explicit
  Java deployment-example work, not deleted blindly.
- The active implementation scope is `.agents/**`, `.codex/**`,
  `documentation/process/**`, `documentation/arc42/**` and
  `documentation/workflow/**`.

Non-goals:

- No Python product behavior change.
- No Java deployment-example implementation change.
- No live Multipass, Docker Swarm, compose, netplan, Portainer, Nexus, Jenkins,
  RabbitMQ, SonarQube or bootstrap execution.
- No new external static-analysis CI configuration.
- No required shell quality gate added to the default Python quality gate.

Open questions:

- Which future EPIC should own long-term agent and skill governance?
- Should optional shell diagnostics become required in a later `QUALITY.md`
  update?

Blocking questions:

- None for workflow creation. The open questions above are non-blocking because
  this workflow keeps scope to governance and does not change product runtime
  behavior or the authoritative quality gate.

Confidence level:

- 86 percent.

Decision:

```text
PROCEED_WITH_ACCEPTED_ASSUMPTIONS
```

## Verified Baseline

- Active branch:
  `architecture/workflow-agents-skills-python-quality-bash-20260523`
- Repository root: `D:/Projects/Tiny-Swarm-World`
- `AGENTS.md` says Tiny Swarm World is primarily Python automation with
  hexagonal architecture.
- `QUALITY.md` says the default gate is
  `python3 tools/quality_gate.py quality`.
- `tools/quality_gate.py` defines the full gate order:
  `lint`, `arch-lint`, `arch-tests`, `typecheck`, `test`.
- `.importlinter` defines forbidden dependencies from domain to application or
  infrastructure and from application to infrastructure.
- No frontend module or frontend package tooling is present.
- Shell scripts exist under `infra/**/*.sh`; no dedicated Bash specialist role
  or skill exists yet.
- No active `documentation/workflow/workflow.md` existed before this workflow
  was created.
- No `documentation/epics` directory was found.

## Target Picture

After `workflow execute`, the repository has:

- Python agent and skill wording that names Python 3.12, Linux/WSL-only
  operation, POSIX paths and `tools/quality_gate.py`.
- Quality-gate wording that consistently names `lint`, `arch-lint`,
  `arch-tests`, `typecheck`, `test` and full `quality`.
- Architecture wording that names `.importlinter`,
  `tests.architecture.test_hexagonal_imports`,
  `python3 tools/quality_gate.py arch-lint` and
  `python3 tools/quality_gate.py arch-tests`.
- Java/Gradle/JUnit/ArchUnit skills guarded for explicit `src/main/java`
  deployment-example work only.
- A Bash specialist skill, project role, callable agent and durable subagent
  document.
- Routing that sends Bash/POSIX shell scripts, shell snippets, shellcheck/shfmt
  policy and `infra/**/*.sh` review to the Bash specialist while keeping broad
  deployment/build ownership with Senior DevOps.
- Documentation and arc42 material synchronized with the governance model.

## Scope

In scope:

- `.agents/roles/**`
- `.agents/skills/**`
- `.agents/orchestrator/routing-rules.md`
- `.agents/prompts/**`
- `.codex/agents/**`
- `.codex/subagents/**`
- selected `.codex/skills/**` guards for portable Java skills
- `documentation/process/**`
- `documentation/arc42/**`
- `documentation/workflow/**`

Out of scope:

- `src/tiny_swarm_world/**`
- `src/main/java/**`
- `infra/**/*.sh` implementation changes
- `tools/quality_gate.py` behavior changes
- `QUALITY.md` default gate changes unless a later slice discovers an
  unavoidable documented conflict and stops for approval.

## Architecture Constraints

- Preserve Python hexagonal architecture.
- Domain code must not import application or infrastructure.
- Application code must not import infrastructure.
- Concrete adapter construction belongs in
  `src/tiny_swarm_world/infrastructure/composition.py`.
- Java under `src/main/java` remains a deployment example only.
- Bash guidance must preserve Linux/WSL-only operation, POSIX paths, script
  locality via `${BASH_SOURCE[0]}`, secret safety and live-infrastructure
  restrictions.

## Python Automation Assessment

Python product code is not changed by this workflow. The workflow changes the
agent and skill governance that controls future Python automation work. The
Python Automation Developer owns wording that affects domain, application,
ports, adapters, YAML handling, command orchestration, path handling and
infrastructure automation slices.

Required Python alignment points:

- Python 3.12 compatibility.
- Linux/WSL-only baseline.
- POSIX paths and bash-style examples.
- `asyncio` consistency for asynchronous command orchestration.
- Application services depend on ports, not infrastructure adapters.
- Quality commands come from `QUALITY.md` and `tools/quality_gate.py`.

## Frontend Assessment

Status: not applicable for implementation in this workflow.

No frontend module, `package.json`, JavaScript or TypeScript tooling, Vite,
Next, Webpack, Rollup or frontend client module was verified. The Senior React
Frontend Developer is included for mandatory workflow-create coverage only and
records a no-impact assessment.

Frontend scope is not authorized for this workflow. Do not add React,
TypeScript, package tooling, frontend build tooling, UI components, API client
layers or frontend tests unless a future requirement explicitly introduces a
verified frontend module and its tooling conventions.

Python UI adapters remain Python automation scope, not React frontend scope.

## Test Strategy

For workflow execution:

- Run `git diff --check` after each governance slice.
- Run exact Python quality commands from `QUALITY.md`.
- For architecture-sensitive wording, run:

```bash
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
```

- For final readiness when practical, run:

```bash
python3 tools/quality_gate.py quality
```

Do not claim a gate passed unless it actually ran. If the full gate is skipped
for a governance-only slice, record the reason and do not claim full readiness.

## Resilience Requirements

- Agent and skill instructions must stop instead of guessing quality authority,
  architecture authority or role ownership.
- Bash guidance must prefer static review and dry-run reasoning before live
  infrastructure commands.
- Shell guidance must call out traps, cleanup, idempotency, environment
  validation and secret-safe diagnostics as review concerns.
- Optional diagnostics such as `shellcheck` and `shfmt` must be reported as
  optional unless `QUALITY.md` makes them required.

## Execution Profile

```text
executionProfile=FULL_PATH
reason=The request changes skill, role, agent, routing, process and quality-governance authority.
requiredFullReviews=Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior React Frontend Developer, Senior Tester, Senior DevOps, Senior Documentation Engineer
allowedImpactChecks=Senior React Frontend Developer may record N/A implementation impact because no frontend module exists
requiredQualityChecks=git diff --check; python3 tools/quality_gate.py arch-lint; python3 tools/quality_gate.py arch-tests; python3 tools/quality_gate.py quality when practical for final readiness
stopConditions=unknown role ownership, stale Java default gates, invented shell required gates, active branch mismatch, dirty unrelated worktree
```

## Ordered Slices

### Slice 01: Align Python Automation Agents And Skills

Purpose:

Make Python automation roles, callable agents and skills explicitly name the
Python 3.12, Linux/WSL-only and `tools/quality_gate.py` baseline.

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - ".agents/roles/senior-python-automation-developer.md"
  - ".codex/agents/senior_python_automation_developer.toml"
  - ".agents/skills/python-automation/SKILL.md"
  - ".codex/subagents/senior-python-automation-developer.md"
affected_modules:
  - ".agents"
  - ".codex"
affected_contracts: []
dependencies: []
parallel_group: "A"
file_locks:
  - ".agents/roles/senior-python-automation-developer.md"
  - ".codex/agents/senior_python_automation_developer.toml"
  - ".agents/skills/python-automation/SKILL.md"
  - ".codex/subagents/senior-python-automation-developer.md"
contract_locks: []
architecture_locks:
  - "python-hexagonal-governance"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "git diff --check"
documentation:
  arc42: "checked; no direct product architecture change expected"
  adr: "not required unless execution changes quality authority"
stop_conditions:
  - "Python 3.12 baseline cannot be preserved"
  - "Linux/WSL-only baseline is weakened"
  - "Gradle, Maven, JUnit or ArchUnit becomes the Python default gate"
```

Prerequisites:

- Root `AGENTS.md` and `QUALITY.md` read.
- Active branch verified.

Allowed write scope:

- Only files listed in `affected_files`.

Done criteria:

- Python role and skill wording names Python 3.12 and Linux/WSL-only operation.
- Verification wording names `tools/quality_gate.py` gates and full `quality`.
- No product code changes.

### Slice 02: Replace Java Default Drift In Architecture And Quality Skills

Purpose:

Constrain Java/Gradle/JUnit/ArchUnit language to explicit Java deployment
example scope and make architecture validation Python import-linter based.

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior System Architect"
secondary_reviewers:
  - "Senior Tester"
  - "Senior Python Automation Developer"
affected_files:
  - ".agents/skills/analytics-slice-workflow/SKILL.md"
  - ".agents/skills/architecture-archunit-hexagonal/SKILL.md"
  - ".agents/skills/architecture-modular-monorepo/SKILL.md"
  - ".agents/roles/senior-system-architect.md"
  - ".codex/agents/senior_system_architect.toml"
  - ".agents/skills/microservice-senior-expert/SKILL.md"
  - ".codex/agents/microservice_senior_expert.toml"
  - ".codex/skills/archunit-expert/SKILL.md"
  - ".codex/skills/junit6-expert/SKILL.md"
affected_modules:
  - ".agents"
  - ".codex"
affected_contracts: []
dependencies: []
parallel_group: "A"
file_locks:
  - ".agents/skills/analytics-slice-workflow/SKILL.md"
  - ".agents/skills/architecture-archunit-hexagonal/SKILL.md"
  - ".agents/skills/architecture-modular-monorepo/SKILL.md"
  - ".agents/roles/senior-system-architect.md"
  - ".codex/agents/senior_system_architect.toml"
  - ".agents/skills/microservice-senior-expert/SKILL.md"
  - ".codex/agents/microservice_senior_expert.toml"
  - ".codex/skills/archunit-expert/SKILL.md"
  - ".codex/skills/junit6-expert/SKILL.md"
contract_locks: []
architecture_locks:
  - "python-architecture-validation"
  - "java-deployment-example-boundary"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
documentation:
  arc42: "check constraints and quality requirements for Python quality authority"
  adr: "not required unless service runtime policy changes"
stop_conditions:
  - "A portable Java skill is changed into a project-specific rule without a Tiny Swarm World guard"
  - "Microservice wording implies Spring Boot is mandatory for all future services"
  - "Architecture checks omit import-linter or tests.architecture.test_hexagonal_imports"
```

Prerequisites:

- Verify whether each Java-oriented reference is portable, project-specific or
  deployment-example scoped.

Allowed write scope:

- Only files listed in `affected_files`.

Done criteria:

- Analytics and architecture skills reference Python `unittest`,
  `.importlinter`, `arch-lint` and `arch-tests`.
- Java deployment-example skills remain available only for explicit Java tasks.
- Senior System Architect references `quality-architecture-validation` instead
  of Java ArchUnit as the Python architecture authority.

### Slice 03: Add Expert Bash Specialist Coverage

Purpose:

Create dedicated Bash/POSIX shell governance without changing shell script
behavior or adding required shell tools to the default quality gate.

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior DevOps Engineer"
secondary_reviewers:
  - "Senior System Architect"
  - "Senior Tester"
  - "Senior Security Sandbox Engineer"
affected_files:
  - ".agents/skills/devops-bash/SKILL.md"
  - ".agents/roles/senior-bash-specialist.md"
  - ".codex/agents/senior_bash_specialist.toml"
  - ".codex/subagents/senior-bash-specialist.md"
  - ".agents/orchestrator/routing-rules.md"
  - ".agents/roles/senior-devops.md"
  - ".codex/agents/senior_devops.toml"
  - ".codex/subagents/senior-devops-engineer.md"
  - ".codex/AGENTS.md"
affected_modules:
  - ".agents"
  - ".codex"
affected_contracts: []
dependencies: []
parallel_group: "A"
file_locks:
  - ".agents/skills/devops-bash/SKILL.md"
  - ".agents/roles/senior-bash-specialist.md"
  - ".codex/agents/senior_bash_specialist.toml"
  - ".codex/subagents/senior-bash-specialist.md"
  - ".agents/orchestrator/routing-rules.md"
  - ".agents/roles/senior-devops.md"
  - ".codex/agents/senior_devops.toml"
  - ".codex/subagents/senior-devops-engineer.md"
  - ".codex/AGENTS.md"
contract_locks: []
architecture_locks:
  - "linux-wsl-operating-model"
  - "live-infrastructure-safety"
quality_gates:
  targeted:
    - "git diff --check"
  required:
    - "git diff --check"
documentation:
  arc42: "check concepts and risks for shell specialist governance"
  adr: "not required unless shell checks become mandatory quality policy"
stop_conditions:
  - "shellcheck or shfmt is made required without QUALITY.md authority"
  - "Bash specialist guidance authorizes live infrastructure execution by default"
  - "Senior DevOps deployment ownership becomes ambiguous"
```

Prerequisites:

- Existing shell files under `infra/**/*.sh` inventoried for ownership only.

Allowed write scope:

- Only files listed in `affected_files`.

Done criteria:

- New `devops-bash` skill defines mission, responsibilities, forbidden scope,
  inputs, outputs, collaboration rules and STOP rules.
- New Senior Bash Specialist role owns shell scripts, Bash/POSIX snippets,
  shellcheck/shfmt policy and shell commands embedded in YAML or docs.
- Callable `.codex/agents/senior_bash_specialist.toml` and durable subagent
  documentation exist.
- Routing sends shell-specific work to Bash specialist before broad DevOps.
- `shellcheck` and `shfmt` are optional diagnostics only.

### Slice 04: Normalize Workflow, Executor And Quality-Gate Wording

Purpose:

Make workflow prompts and quality-gate skills use exact Python quality-gate
names and report architecture-sensitive checks consistently.

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers:
  - "Senior Workflow Architect"
  - "Senior System Architect"
  - "Senior Python Automation Developer"
affected_files:
  - ".agents/prompts/slice-execute.md"
  - ".agents/prompts/workflow-execute.md"
  - ".agents/skills/workflow-authoring/SKILL.md"
  - ".agents/skills/workflow-executor/SKILL.md"
  - ".agents/skills/quality-gate-governance/SKILL.md"
  - ".agents/skills/quality-gate-orchestrator/quality-gates.md"
  - ".agents/roles/senior-tester.md"
  - ".codex/agents/senior_tester.toml"
affected_modules:
  - ".agents"
  - ".codex"
affected_contracts: []
dependencies:
  - "01"
  - "02"
  - "03"
parallel_group: "B"
file_locks:
  - ".agents/prompts/slice-execute.md"
  - ".agents/prompts/workflow-execute.md"
  - ".agents/skills/workflow-authoring/SKILL.md"
  - ".agents/skills/workflow-executor/SKILL.md"
  - ".agents/skills/quality-gate-governance/SKILL.md"
  - ".agents/skills/quality-gate-orchestrator/quality-gates.md"
  - ".agents/roles/senior-tester.md"
  - ".codex/agents/senior_tester.toml"
contract_locks: []
architecture_locks:
  - "quality-gate-authority"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
documentation:
  arc42: "quality requirements checked"
  adr: "not required unless quality policy changes"
stop_conditions:
  - "A quality command cannot be verified from QUALITY.md or tools/quality_gate.py"
  - "Documentation treats git diff --check as a replacement for required Python gates"
  - "A failed required gate is described as optional"
```

Prerequisites:

- Slices 01, 02 and 03 complete or explicitly skipped with documented reason.

Allowed write scope:

- Only files listed in `affected_files`.

Done criteria:

- Workflow prompts and quality skills name exact gate commands.
- Architecture-sensitive slices require `arch-lint` and `arch-tests`.
- Senior Tester reports whether `lint`, `arch-lint`, `arch-tests`,
  `typecheck`, `test` or `quality` ran.
- Java gates are not default Python gates.

### Slice 05: Documentation Sync, arc42 Check And Final Verification

Purpose:

Synchronize process and architecture documentation with the new governance
model, then run final verification.

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "documentation/process/skill-agent-creation.md"
  - "documentation/process/skills-update.md"
  - "documentation/process/workflow-create.md"
  - "documentation/arc42/02_constraints.adoc"
  - "documentation/arc42/08_concepts.adoc"
  - "documentation/arc42/10_quality_requirements.adoc"
  - "documentation/arc42/11_risks_and_debt.adoc"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - "documentation/workflow/workflow.md"
affected_modules:
  - "documentation"
affected_contracts: []
dependencies:
  - "04"
parallel_group: "C"
file_locks:
  - "documentation/process/skill-agent-creation.md"
  - "documentation/process/skills-update.md"
  - "documentation/process/workflow-create.md"
  - "documentation/arc42/02_constraints.adoc"
  - "documentation/arc42/08_concepts.adoc"
  - "documentation/arc42/10_quality_requirements.adoc"
  - "documentation/arc42/11_risks_and_debt.adoc"
  - "documentation/workflow/context-pack.md"
  - "documentation/workflow/context-pack.json"
  - "documentation/workflow/workflow.md"
contract_locks: []
architecture_locks:
  - "documentation-governance"
  - "arc42-governance"
quality_gates:
  targeted:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
  required:
    - "git diff --check"
    - "python3 tools/quality_gate.py arch-lint"
    - "python3 tools/quality_gate.py arch-tests"
    - "python3 tools/quality_gate.py quality"
documentation:
  arc42: "update or explicitly record no-change rationale"
  adr: "not required unless a new quality or architecture policy is introduced"
stop_conditions:
  - "arc42 impact cannot be classified"
  - "context-pack hashes are stale after final edits"
  - "full quality gate is skipped without explicit documented reason"
```

Prerequisites:

- Slices 01 through 04 completed.

Allowed write scope:

- Only files listed in `affected_files`.

Done criteria:

- Process docs and arc42 docs align with agent/skill governance.
- Context pack hashes are refreshed.
- Final verification result is recorded.
- Remaining risks are documented.

## Slice Dependency Graph

```text
01 --\
02 ----> 04 --> 05
03 --/
```

Parallelization:

- Slices 01, 02 and 03 may run in parallel after S3/S3D verification because
  their write scopes are disjoint.
- Slice 04 depends on 01, 02 and 03.
- Slice 05 depends on 04.

## Role And Subagent Ownership Map

| Area | Owner | Notes |
|---|---|---|
| Workflow creation and dependency ordering | Senior Workflow Architect | Current workflow authoring |
| Requirement and EPIC drift | Senior Requirement Engineer | EPIC source missing, traceability gap recorded |
| Architecture boundaries and arc42 | Senior System Architect | Python import-linter architecture authority |
| Python automation wording | Senior Python Automation Developer | Slice 01 |
| Frontend assessment | Senior React Frontend Developer | N/A implementation impact |
| Quality-gate validation | Senior Tester | Slice 04 and final verification |
| Bash specialist creation | Senior DevOps Engineer | Slice 03 creates future Senior Bash Specialist ownership |
| Documentation consistency | Senior Documentation Engineer | Slice 05 |
| Security-sensitive shell guidance | Senior Security Sandbox Engineer | Reviewer for Slice 03 |

## Quality-Gate Expectations

Authoritative commands:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

Full gate order:

```text
lint -> arch-lint -> arch-tests -> typecheck -> test
```

Governance-only targeted check:

```bash
git diff --check
```

Optional Bash diagnostics:

```bash
shellcheck infra/**/*.sh
shfmt -d infra/**/*.sh
```

The optional Bash diagnostics are not required by `QUALITY.md` and must not be
reported as passed unless they actually run.

## Documentation Synchronization Points

- Update `documentation/process/**` only when process wording changes.
- Update `documentation/arc42/02_constraints.adoc` if constraints change.
- Update `documentation/arc42/08_concepts.adoc` if governance concepts change.
- Update `documentation/arc42/10_quality_requirements.adoc` when quality-gate
  expectations are clarified.
- Update `documentation/arc42/11_risks_and_debt.adoc` when Bash script risks or
  stale Java-default risk remains documented.

## Stop Conditions

Stop workflow execution if:

- The active branch is not
  `architecture/workflow-agents-skills-python-quality-bash-20260523`.
- The local branch ref cannot be verified.
- The working tree contains unrelated or unclear changes.
- Any slice tries to modify product source, shell script behavior, Java example
  code or `tools/quality_gate.py` without a workflow refinement.
- A quality command cannot be verified from `QUALITY.md` or
  `tools/quality_gate.py`.
- `shellcheck` or `shfmt` is made mandatory without an explicit `QUALITY.md`
  change and approval.
- Java/Gradle/JUnit/ArchUnit becomes the default quality path for Python work.
- Frontend implementation is introduced without verified frontend tooling and a
  new explicit requirement.
- A required subagent or role cannot be verified.
- File locks overlap without a documented handoff.

## Uncertainty Escalation Rules

- EPIC ownership uncertainty routes to Senior Requirement Engineer.
- Architecture or quality authority conflict routes to Senior System Architect
  and Senior Tester.
- Bash live-infrastructure safety uncertainty routes to Senior DevOps and
  Senior Security Sandbox Engineer.
- New required shell quality tools require explicit `QUALITY.md` governance and
  user approval.
- Any unresolved governance conflict escalates to Root Architect via Senior
  System Architect.

## Commit And Push Plan

This workflow creation does not authorize push, PR creation, merge or cleanup.
During `workflow execute`, create commits or push only if the user explicitly
requests that behavior or a later approved workflow amendment authorizes it.

Each executed slice must remain independently reviewable. Do not combine
unrelated slice changes in one commit.

## Definition Of Done

- All slices are complete or explicitly skipped with a documented reason.
- Agent and skill governance consistently reflects Python 3.12, Linux/WSL-only
  operation and `tools/quality_gate.py`.
- Hexagonal architecture checks are documented as `arch-lint` and
  `arch-tests`.
- Bash specialist role, skill, callable agent, durable subagent and routing
  coverage exist.
- Java/Gradle/JUnit/ArchUnit wording is constrained to explicit Java
  deployment-example work.
- Process and arc42 documentation are synchronized or checked with a no-change
  rationale.
- Required quality gates have exact command evidence.
- No live infrastructure commands were run.

## Handoff To Workflow Execute

`workflow execute` may start when:

- this file and `documentation/workflow/context-pack.*` are present;
- the active branch is
  `architecture/workflow-agents-skills-python-quality-bash-20260523`;
- the working tree status is understood;
- S3/S3D validates slice metadata and file locks;
- the executor accepts the non-blocking EPIC traceability gap recorded above.

Use the project-specific `.agents/skills/workflow-executor/SKILL.md` as the
active executor.

## arc42 Check Status

arc42 was checked during workflow creation. Existing arc42 files are placeholder
level and do not yet describe agent/skill governance in detail. Slice 05 is
responsible for updating or explicitly recording no-change rationale for:

- `documentation/arc42/02_constraints.adoc`
- `documentation/arc42/08_concepts.adoc`
- `documentation/arc42/10_quality_requirements.adoc`
- `documentation/arc42/11_risks_and_debt.adoc`
