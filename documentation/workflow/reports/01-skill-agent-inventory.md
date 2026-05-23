# Slice 01 Skill And Agent Inventory

## Status

```text
COMPLETED
```

Slice 01 inspected the current skill, role, agent, prompt and documentation
landscape for the active workflow:

```text
Consolidate Tiny Swarm World Skills and Agents
```

The workflow is a `workflow execute` run over the skills-and-agents subject
area. It does not activate `skills update`, `push auto`, product source
implementation, Docker/Swarm deployment, Multipass operations, or live
infrastructure changes.

## S3 And S3D Result

```text
EXECUTION_PLAN
```

- Active workflow: `documentation/workflow/workflow.md`.
- Expected branch: `feature/workflow-tiny-swarm-skills-agents-20260523`.
- Active branch: `feature/workflow-tiny-swarm-skills-agents-20260523`.
- Local branch ref: present.
- Worktree before Slice 01 write: clean.
- Context pack hashes: matched `AGENTS.md`, `QUALITY.md`, `README.md`,
  `documentation/arc42/05_building_blocks.adoc`, and
  `documentation/arc42/10_quality_requirements.adoc`.
- Dependency graph: `01 -> {02, 03} -> 04 -> 05 -> 06 -> 07 -> 08`.
- Graph status: concrete, acyclic, and safe to start Slice 01.
- Current executable slice: Slice 01 only.

Slices 02 and 03 are both in parallel group `B`, but their declared locks
overlap on `.agents/skills/**`, `skill-registry`, and `process-governance`.
They must execute serially unless this workflow later narrows their locks to
disjoint file, contract and architecture sets.

## Execution Profile

```text
FULL_PATH
```

Reason: the workflow touches skill discovery, role ownership, callable agents,
routing rules, process governance, registry paths and quality authority. It
does not change runtime Python, Java example code, infrastructure assets,
compose files, stack files, build files or live platform state.

## Requirement Source

No standalone `documentation/epics/` directory exists. For this governance
workflow, the active requirement source is `documentation/workflow/workflow.md`,
especially the Requirement Clarification Record and Slice 01 definition.

Requirement check:

```text
Does the implementation still match the EPIC?
```

Result:

```text
MATCHES_ACTIVE_WORKFLOW_BASELINE
```

The inspected repository matches the workflow baseline: required target skills
are missing, registry and organigramm paths are unresolved in current files,
`.agents` and `.codex` both contain active assets, and product runtime changes
remain out of scope.

## Inventory Counts

| Area | Count | Notes |
| --- | ---: | --- |
| `.agents` files | 152 | Project-specific role, skill, prompt and orchestrator material. |
| `.agents/skills/*/SKILL.md` | 76 | Current discoverable project skill entrypoints. |
| `.agents/roles` files | 20 | Mix of flat role files and reusable role directories with `SKILL.md`. |
| `.agents/prompts` files | 6 | Includes `skills-update`, `skill-audit`, workflow prompts and slice prompts. |
| `.agents/orchestrator` files | 2 | Routing rules and swarm orchestration. |
| `.codex` files | 54 | Reusable team assets plus project-scoped callable agent TOML files. |
| `.codex/skills/*/SKILL.md` | 6 | Reusable Codex skill entrypoints. |
| `.codex/agents` files | 35 | Callable agent TOML definitions. |
| `.codex/subagents` files | 10 | Durable role descriptions. |
| `.codex/workflow` files | 1 | Reusable workflow execution rules. |

All current `.agents/skills` and `.codex/skills` discoverable skills use
`<skill-name>/SKILL.md`. Current local discovery rules require that format.

## Current Skill Entry Points

The current project-specific discoverable skill entrypoints are:

```text
adr-steward
agent-handoff-protocol
agent-swarm-coordination-specialist
analysis-storage-architect
analytics-persistence-review
analytics-slice-workflow
arc42-architecture-governance
architecture-archunit-hexagonal
architecture-hexagonal
architecture-modular-monorepo
build-gradle
code-property-graph-joern-specialist
contract-first-api-steward
contract-governance-expert
data-ownership-persistence-steward
devops-ci-cd
devops-docker
devops-kubernetes
distributed-systems-architect
documentation-sync
engineering-governance
execution-profile-router
flowchart-integrity-auditor
frontend-hexagonal
frontend-react
frontend-ux-guidelines
git-branch-strategy
git-clean
git-commit-message-preparation
git-commit-preparation
git-large-repository-specialist
grpc-ingestion
grpc-streaming-specialist
ingestion-handoff-review
java-25-backend
joern-semantic-analysis
microservice-migration-safety-gate
microservice-runtime-readiness-expert
microservice-senior-expert
migration-workflow
observability-diagnostics
observability-runtime-diagnostics
performance-scalability-engineer
process-performance-profiler
protobuf-contracts
python-automation
quality-architecture-validation
quality-archunit-review
quality-gate
quality-gate-governance
quality-gate-orchestrator
quality-impact-classifier
quality-mutation-testing
quality-testing-strategy
release-branch-governance
replay-graph-llm-review
replay-runtime-correlation-specialist
requirement-engineering
resilience-engineering
s3d-execution-orchestrator
security-sandbox-specialist
security-threat-modeling
service-decomposition-bounded-context
skill-registry-conflict-auditor
source-analysis-pipeline
spring-core
swarm-coordination
swarm-orchestration
testing-junit6
three-amigos-requirement-gatekeeper
workflow-authoring
workflow-conflict-resolution
workflow-executor
workflow-slice
workflow-slice-execution
workspace-lifecycle-specialist
```

Reusable `.codex/skills` entrypoints are:

```text
archunit-expert
hexagonal-architecture-expert
junit6-expert
microservice-architecture-expert
protobuf-grpc-expert
workflow-executor
```

## Current Roles And Agents

Project role files exist for:

```text
microservice-senior-expert
senior-analysis-storage-architect
senior-devops
senior-documentation-engineer
senior-execution-orchestrator
senior-git-workspace-specialist
senior-grpc-proto-specialist
senior-java-backend
senior-joern-cpg-specialist
senior-performance-engineer
senior-plugin-integration-developer
senior-python-automation-developer
senior-react-frontend
senior-requirement-engineer
senior-security-sandbox-engineer
senior-swarm-orchestrator
senior-system-architect
senior-tester
senior-ux-designer
senior-workflow-architect
```

Callable `.codex/agents` definitions exist for the workflow-required owners
and reviewers, including `senior_requirement_engineer`,
`senior_workflow_architect`, `senior_system_architect`,
`senior_python_automation_developer`, `senior_documentation_engineer`,
`senior_tester`, `senior_swarm_orchestrator`, and implementation/review
support agents.

Many role names intentionally appear in both `.agents/roles` and
`.codex/agents`. Treat these as role-to-callable-agent mappings, not automatic
duplicates to delete.

## Duplicate And Overlapping Responsibility Findings

Intentional duplicate:

- `workflow-executor` exists in both `.agents/skills` and `.codex/skills`.
  The project-specific `.agents/skills/workflow-executor/SKILL.md` is active;
  `.codex/skills/workflow-executor/SKILL.md` is reusable baseline context only.

Semantic overlaps requiring later consolidation review:

- `architecture-hexagonal` and `.codex/skills/hexagonal-architecture-expert`.
- `architecture-archunit-hexagonal` and `.codex/skills/archunit-expert`.
- `testing-junit6` and `.codex/skills/junit6-expert`.
- `protobuf-contracts` / `grpc-streaming-specialist` and
  `.codex/skills/protobuf-grpc-expert`.
- `microservice-senior-expert` and
  `.codex/skills/microservice-architecture-expert`.
- Analytics, replay, graph, persistence, source-analysis and Joern skills have
  broad forensic-analysis ancestry and need keep/remove decisions against the
  Tiny Swarm World scope before deletion or retention.

## Required Target Skills

The active workflow defines 47 required target skills.

Present in `.agents/skills`:

```text
none
```

Present only as reusable `.codex/skills`:

```text
hexagonal-architecture-expert
```

Missing from `.agents/skills`:

```text
tdd-expert
bdd-expert
platform-quality-gates
acceptance-checks
hexagonal-architecture-expert
mapping-dsl-expert
strangler-command-adapter-pattern
sca-migration-expert
llm-analysis-expert
kubernetes-expert
python-senior-developer
python-pip-packaging-expert
setup-bootstrap-expert
python-cli-automation
python-test-automation
tiny-swarm-world-system-architecture
platform-layout-governance
workflow-orchestration
multipass-vm-provisioning
linux-host-preparation
network-topology-design
docker-engine-installation
docker-swarm-initialization
swarm-node-management
swarm-stack-deployment
swarm-volume-network-governance
registry-infrastructure
nexus-bootstrap
docker-registry-bootstrap
maven-repository-bootstrap
image-build-publish
image-versioning-tagging
image-verification
jenkins-bootstrap
sonarqube-bootstrap
portainer-bootstrap
swagger-ui-bootstrap
reverse-proxy-routing
platform-verification
platform-reset-and-recovery
observability-and-diagnostics
secrets-and-config-management
idempotent-platform-automation
documentation-generation
frontend-developer
console-status-ui-developer
terminal-status-dashboard
```

Slice 02 must create these as project-specific skills under
`.agents/skills/<skill-name>/SKILL.md`, unless a later explicit workflow
decision changes discovery rules.

## Unrelated Or Drift Candidate Findings

Exact deletion candidate that currently exists and is referenced:

- `.agents/skills/microservice-senior-expert/SKILL.md`
- `.agents/roles/microservice-senior-expert.md`
- `.codex/agents/microservice_senior_expert.toml`
- `.codex/subagents/microservice-senior-expert.md`

Other strong drift candidates to review before deletion or retention:

- `.codex/agents/architecture_forensic_analytics_architect.toml`
- `.codex/agents/analytics_persistence_reviewer.toml`
- `.codex/agents/ingestion_handoff_reviewer.toml`
- `.codex/agents/joern_semantics_reviewer.toml`
- `.codex/agents/replay_graph_llm_reviewer.toml`
- `.codex/agents/source_analysis_reviewer.toml`
- `.codex/agents/senior_react_frontend.toml`
- `.codex/subagents/senior-react-frontend-developer.md`
- `.agents/roles/senior-plugin-integration-developer.md`
- `.agents/skills/analytics-*`
- `.agents/skills/replay-*`
- `.agents/skills/source-analysis-pipeline`
- `.agents/skills/code-property-graph-joern-specialist`
- `.agents/skills/joern-semantic-analysis`
- `.agents/skills/frontend-react`
- `.agents/skills/frontend-hexagonal`
- `.agents/skills/frontend-ux-guidelines`
- `.agents/skills/spring-core`

React/frontend assets may remain only as read-only exclusion or console-status
UI guidance until a separate frontend workflow verifies a real frontend module
and quality gate. Java and Spring assets may remain only for deployment-example
or explicit Java-example work, not as Python automation architecture drivers.

## Dead Or Stale References

- `.agents/prompts/skills-update.md` loads
  `documentation/agents/skill-registry.md` and
  `documentation/agents/organigramm.md`, but `documentation/agents/` does not
  exist.
- `documentation/skill-audit/` does not exist yet, although
  `.agents/skills/skill-registry-conflict-auditor/SKILL.md` owns that path.
- `documentation/workflow/reports/` did not exist before this Slice 01 write.
- `documentation/epics/` is absent.
- `documentation/adr/` is absent.
- `.codex/prompts/` is absent.
- Root `docs/` is absent; this repository uses `documentation/`.
- `Organigramm Maintainer` and `Process Governance Maintainer` are routing
  concepts, not current role files.
- `Root Architect` has no dedicated role file; routing currently escalates
  through `roles/senior-system-architect.md`.
- `Typed Error Router` is a workflow-executor and quality-gate protocol, not a
  standalone role file.

## Canonical Registry And Organigramm Decision

Use these canonical paths:

```text
documentation/skill-audit/skill-registry.md
documentation/skill-audit/skill-registry.json
documentation/skill-audit/organigramm.md
documentation/skill-audit/owner-map.md
```

`documentation/agents/**` is not the canonical path for this repository.
Later slices must update stale references from `documentation/agents/**` to
the selected `documentation/skill-audit/**` paths or explicitly document why a
compatibility pointer is needed.

## Owner Map Decision

| Concept | Interim Owner | Review / Escalation |
| --- | --- | --- |
| Organigramm Maintainer | Senior Documentation Engineer | Skill Registry Conflict Auditor, Senior Workflow Architect, Senior System Architect when hierarchy affects governance architecture. |
| Process Governance Maintainer | Senior Workflow Architect | Senior Requirement Engineer for drift, Senior Tester for quality authority, Engineering Governance skill for process consistency. |
| Root Architect | Senior System Architect | Escalates to requirement, security, DevOps, data, contract, release or quality owners when those concerns are primary. |
| Typed Error Router | Workflow Executor / Senior Workflow Architect | Senior Execution Orchestrator owns lock-conflict routing; Senior Tester and Quality Gate Orchestrator own quality failure classification. |

No new role file is required in Slice 01. Later documentation slices must make
this owner map visible from root `AGENTS.md` and process documentation.

## Skill File Format Decision

Authoritative project skill format remains:

```text
.agents/skills/<skill-name>/SKILL.md
```

Reasons:

- `.agents/AGENTS.md` states that discoverable skills require this structure.
- `documentation/process/skill-agent-creation.md` states that skills live under
  `.agents/skills/<name>/SKILL.md`.
- The current session's available skill list discovers directory-based
  `SKILL.md` entrypoints.
- Grouped `.md`-only files such as `.agents/skills/python/python-senior-developer.md`
  would be invisible to current local skill discovery.

The target grouping from `documentation/workflow/workflow.md` should be
represented through registry metadata, organigramm sections, or optional
non-authoritative grouped index files. Slice 02 must not create `.md`-only
skill files as the only source for a required skill.

## Documentation And arc42 Decision

Slice 01 is a governance metadata report and does not change product runtime
architecture. arc42 can remain check-only for Slice 01.

Slice 06 should update documentation, and likely a short arc42 process
governance note, if the registry, organigramm, root-agent authority or owner
map becomes part of the durable project architecture view. That update must be
clearly marked as process governance, not runtime architecture.

## Next Slice Handoff

Slice 02 may begin only after this report is reviewed as the Slice 01 handoff.

Recommended execution:

- Run Slice 02 and Slice 03 serially unless their locks are narrowed.
- Create required skills as `.agents/skills/<skill-name>/SKILL.md`.
- Preserve `.codex` assets as reusable or callable-agent material unless a
  later slice proves a safe replacement.
- Do not delete, rename or replace candidate skills before reference checks in
  Slice 04.
- Do not touch `src/tiny_swarm_world/**`, `src/main/java/**`, `infra/**`,
  `tools/**`, build files, compose files, stack files, Dockerfiles or live
  infrastructure commands in this workflow.

## Commands Executed Or Used For Evidence

```bash
git status --short --branch
git branch --show-current
git show-ref --verify --quiet refs/heads/feature/workflow-tiny-swarm-skills-agents-20260523
git diff --check
find .agents -type f | sort
find .codex -type f | sort
find .agents/skills -mindepth 2 -maxdepth 2 -name SKILL.md -type f | sort
find .codex/skills -mindepth 2 -maxdepth 2 -name SKILL.md -type f | sort
find .agents/roles -type f | sort
rg -n "spring-boot-expert|forensic-analytics-expert|react-developer" AGENTS.md README.md documentation .agents .codex
rg -n "documentation/agents|documentation/skill-audit|Organigramm Maintainer|Process Governance Maintainer|Typed Error Router|Root Architect" .agents documentation .codex AGENTS.md README.md
rg -n "python-senior-developer|python-pip-packaging-expert|setup-bootstrap-expert|tdd-expert|bdd-expert|platform-quality-gates|acceptance-checks|frontend-developer|console-status-ui-developer|terminal-status-dashboard" .agents AGENTS.md documentation .codex README.md
```

Subagent reviews were completed by:

- Senior Swarm Orchestrator / S3 readiness sidecar.
- Senior Workflow Architect / S3D reviewer.
- Senior System Architect reviewer.
- Senior Requirement Engineer owner review.

## Slice 01 Blockers

```text
none
```

## Blockers Before Slice 02

The following are resolved by this report and no longer block Slice 02:

- canonical registry and organigramm path decision;
- skill-file format decision;
- interim owner map for Organigramm Maintainer, Process Governance Maintainer,
  Root Architect and Typed Error Router;
- current missing required skill inventory.

Remaining constraints for Slice 02:

- required skills must be created in discoverable `<skill-name>/SKILL.md`
  format;
- responsibilities must stay Tiny Swarm World-specific;
- no runtime source, Java deployment-example, infrastructure, tooling, build,
  compose, stack or live infrastructure changes are allowed.
