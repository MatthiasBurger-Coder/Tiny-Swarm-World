# Workflow context pack

Workflow: `workflow-sonarcloud-remediation-v2.0.0`

Branch: `fix/workflow-sonarcloud-remediation-20260718`

Process strand: Python test-quality remediation and workflow governance.

Execution profile: `FULL_PATH`, sequential two-slice pilot.

Affected areas: test assertions, SonarCloud issue evidence, workflow evidence.

Forbidden areas: production code, infrastructure, SonarCloud configuration, quality-profile suppression/exclusions, and live infrastructure.

Required roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior Tester, Issue Completion Auditor.

Conditional roles: Senior DevOps Engineer only for remote-analysis evidence; no frontend role is authorized.

Authoritative quality commands:

- `git diff --check`
- `PYTHONPATH=src python3 -m unittest <changed module>`
- `python3 tools/quality_gate.py quality`

The full quality command applies to Slice 02. Slice 01 is evidence-only and records its documented `git diff --check` verification.

This pack is navigation aid only. It is stale when any hash in `context-pack.json` changes, governance conflicts, or an execution slice touches governance material. The authoritative files must then be reread.
