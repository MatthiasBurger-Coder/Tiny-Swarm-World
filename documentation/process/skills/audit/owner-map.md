# Owner Map

## Status

```text
CURRENT_WITH_ISSUE_COMPLETION_GATES
```

| Concept | Owner | Review And Escalation |
| --- | --- | --- |
| Organigramm Maintainer | Senior Documentation Engineer | Skill Registry Conflict Auditor, Senior Workflow Architect, Senior System Architect when hierarchy changes affect architecture governance. |
| Process Governance Maintainer | Senior Workflow Architect | Senior Requirement Engineer for drift, Senior Tester for quality authority, Engineering Governance skill for consistency. |
| Issue Completion Discipline | Senior Requirement Engineer | Use `issue-completion-auditor` for final PASS/INCOMPLETE/BLOCKED/REJECTED decisions; Senior System Architect reviews architecture fit, Senior Tester reviews test and evidence coverage. |
| Root Architect | Senior System Architect | Escalate to requirement, security, DevOps, data, contract, release or quality owners when those concerns are primary. |
| Typed Error Router | Workflow Executor / Senior Workflow Architect | Senior Execution Orchestrator owns lock-conflict routing; Senior Tester and Quality Gate Orchestrator own quality failure classification. |
| Service Boundary Governance | Senior System Architect | Use `service-decomposition-bounded-context`, `microservice-runtime-readiness-expert`, `microservice-migration-safety-gate`, and `contract-governance-expert` by concern. |
| Audit Evidence Governance | Senior Documentation Engineer | Use `audit-evidence-manager`; escalate quality evidence to `qms-light-governance-expert` and traceability to `traceability-engineer`. |
| QMS-Light Governance | Senior Tester | Use `qms-light-governance-expert`; escalate release readiness to `release-baseline-governance-expert`. |
| ISMS-Light Governance | Security Owner | Use `isms-light-security-governance-expert`; escalate ASVS and supply-chain concerns to the matching security skills. |
| Live Evidence Governance | Senior DevOps Engineer | Use `live-evidence-validation-expert`; escalate release claims to `release-baseline-governance-expert`. |
| Branch And CI Governance | Senior DevOps Engineer | Use `branch-ci-governance-expert`; escalate quality failures to Quality Gate Orchestrator. |
| Release Baseline Governance | Root Architect | Use `release-baseline-governance-expert`; require quality, security, documentation, traceability and live-evidence owners when applicable. |
| Documentation Audience Governance | Senior Documentation Engineer | Use `documentation-audience-architect`; escalate architecture documentation to arc42 governance. |

Root `AGENTS.md` and `QUALITY.md` remain authoritative when this map conflicts
with project-wide engineering or quality rules.
