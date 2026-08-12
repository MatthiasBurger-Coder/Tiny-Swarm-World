# Context Pack — Issue #249

- Workflow id: `issue-249-composition-root-refactor-20260811`
- Issue: `#249`
- Branch: `architecture/workflow-composition-root-refactor-20260811`
- Baseline: `d56df8d856529a65d6a8cf2de0ad02eb026993e5`
- Process strand: issue-driven composition-root refactor
- Execution profile: `FULL_PATH`
- Affected areas: infrastructure composition, configuration, probes/readiness,
  platform/artifact/deployment/setup wiring, tests, arc42
- Forbidden areas: domain/application dependency direction, live infrastructure,
  new service boundaries, browser React, Java/Maven/Spring, unrelated cleanup
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior
  Python Automation Developer, Senior Tester
- Conditional roles: Senior Documentation Engineer for arc42/evidence; Senior
  DevOps for read-only runtime safety review
- Targeted verification: focused composition/wiring tests, architecture tests,
  `git diff --check`
- Required verification: `python3 tools/quality_gate.py quality`
- Evidence path: `.tiny-swarm/evidence/issue-249/`

This pack is navigation only. `AGENTS.md`, `QUALITY.md`, the issue, arc42, ADRs,
and skill files remain authoritative.
