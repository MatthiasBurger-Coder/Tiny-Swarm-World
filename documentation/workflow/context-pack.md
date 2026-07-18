# Workflow context pack

Workflow: workflow-sonarcloud-remediation-v3.0.0
Branch: fix/workflow-sonarcloud-remediation-20260718
Requirement authority: documentation/epics/sonarcloud-remediation.md
Profile: FULL_PATH
Scope: all 329 baseline findings in 33 ordered slices.
Forbidden: suppressions, exclusions, profile/config changes, live infrastructure.
Quality: changed-module tests; git diff --check; python3 tools/quality_gate.py quality; remote SonarCloud analysis.
