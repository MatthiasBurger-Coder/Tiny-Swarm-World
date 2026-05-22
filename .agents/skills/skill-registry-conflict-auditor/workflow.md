# Workflow

## Phase 1 - Load Governance Baseline

Read the authoritative sources before classifying conflicts:

1. `AGENTS.md`
2. `QUALITY.md`
3. active `documentation/workflow/**`
4. `.agents/orchestrator/**`
5. `.agents/skills/**`
6. `.agents/roles/**`
7. `.codex/AGENTS.md`
8. `.codex/skills/**`
9. `.codex/agents/**`
10. `documentation/adr/**`

## Phase 2 - Build Registry

For each skill or role, record:

- name
- path
- mission or responsibility
- forbidden scope
- inputs
- outputs
- STOP rules
- related skills or roles
- architecture zone
- workflow slices where it applies

## Phase 3 - Detect Conflicts

Compare registry entries for:

- same output with incompatible rules
- missing owner for required output
- owner assigned before its skill exists
- reusable `.codex` file receiving project-specific rules
- quality gate rules that weaken `QUALITY.md`
- architecture rules that weaken `AGENTS.md` or ADRs
- service-boundary rules that allow shared implementation modules
- data ownership rules that allow cross-service database access

## Phase 4 - Classify

Classify every finding:

- `BLOCKING`: execution must stop until the conflict is resolved.
- `NON_BLOCKING`: execution may continue when the risk and owner are documented.

Use `BLOCKING` whenever continuing would require guessing or would weaken a mandatory repository rule.

## Phase 5 - Route Resolution

Route conflicts to the smallest owner set:

- architecture conflicts to Senior System Architect;
- quality conflicts to Senior Tester or quality-gate skills;
- security conflicts to security roles or skills;
- API conflicts to contract or gRPC/protobuf roles;
- data ownership conflicts to storage roles or data ownership skills;
- workflow conflicts to Senior Workflow Architect or Senior Swarm Orchestrator;
- release conflicts to release or git governance skills.

## Phase 6 - Report

Report:

- registry summary
- conflicts and classification
- affected files
- required owners
- resolution steps
- remaining blockers
- whether workflow execution may continue
