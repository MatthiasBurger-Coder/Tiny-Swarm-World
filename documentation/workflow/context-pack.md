# Context Pack: Issue #218 FR-1

- Workflow: `workflow-issue-218-fr01-host-detection-20260712`
- Version: `workflow-issue-218-fr01-v1.0.0`
- Branch: `feature/workflow-issue-218-fr01-host-detection-20260712`
- Baseline: `main@d778fce69bd8f87195ad9b975a1036e3cd1a8819`
- Process strand: `workflow create -> workflow execute -> PR/CI/Sonar -> merge`
- Execution profile: `FULL_PATH`
- Authoring publication: commit
  `d161915f630241ba9bdcc6a8f339b84f4bddd137` verified at
  `origin/feature/workflow-issue-218-fr01-host-detection-20260712`
- Gate: `READY_FOR_WORKFLOW` at 97 percent confidence
- Affected areas: host detection, preflight, composition, CLI, tests, arc42/ADR
- Forbidden areas: live infrastructure, network mutation, resources, filesystem
  policy, timeout/heartbeat implementation, browser/React, Java/Spring, Kubernetes-first
- Required roles: Senior Workflow Architect, Senior Requirement Engineer,
  Senior System Architect, Senior Python Automation Developer, Senior Tester,
  Senior DevOps, Senior Documentation Engineer, Console/status UI Developer,
  Issue Completion Auditor
- Conditional roles: Console/status UI required for `host detect`; browser
  React forbidden/N/A; terminal dashboard not applicable
- Targeted quality: focused host/preflight/installer/entrypoint tests,
  `arch-lint`, `arch-tests`, and `git diff --check`
- Required quality: `python3 tools/quality_gate.py quality`
- Evidence: `.codex/evidence/slice-01-distribution.md`,
  `.codex/evidence/slice-01-consolidation.md`, supporting evidence under
  `.codex/evidence/workflow-issue-218-fr01-host-detection-20260712/`, and
  ignored `.tiny-swarm/evidence/issue-218-fr01/`
- Live validation: forbidden/not run for this workflow

This navigation aid does not replace root `AGENTS.md`, `QUALITY.md`, ADRs,
arc42, the workflow, routing rules, or skill files. Reopen authoritative files
when any recorded hash changes.
