# Context Pack — Issue #217

- Workflow: `issue-217-20260809` (`issue-217-v1.0.0`).
- Authoring branch: `feature/workflow-review-obsolete-issues-20260809`.
- Implementation branch: `requirements/review-obsolete-issues-156-163-197-20260809`.
- Execution profile: `FULL_PATH`.
- Process strand: `workflow-create-to-workflow-execute`.
- Scope: evidence-backed current-main review of Issues #156, #163 and #197,
  decision consolidation, duplicate-work prevention and guarded issue actions.
- Forbidden areas: product implementation during authoring, unrelated backlog
  cleanup, live Docker/LXC/Incus/Swarm/network/Selenium actions, unverified
  Sonar success and browser React.
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior
  Python Automation Developer, Senior Tester.
- Conditional roles: Senior Workflow Architect, Senior Documentation Engineer,
  Senior Security Sandbox Engineer, Senior Execution Orchestrator and Senior
  DevOps when a verified slice needs their responsibility.
- Quality commands: `git diff --check`, targeted issue tests from workflow
  slices, `python3 tools/quality_gate.py quality`.
- Evidence root: `.tiny-swarm/evidence/issue-217-obsolescence-review/`.
- Parallelism: only S217-02/03/04, each with disjoint evidence files and an
  isolated worktree; consolidation and GitHub issue actions are serialized.

This pack is navigation context only. The authoritative governance sources,
workflow, issue bodies and repository behavior remain authoritative.
