# Context Pack — Issue #144

- Workflow: `issue-144-20260809` / `issue-144-v1.0.0`
- Branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`
- Baseline: `b8c64eaa50839fcbf4581ca819286ad13ee88300`
- Process strand: `workflow-create-to-workflow-execute`
- Execution profile: `FULL_PATH`
- Scope: remove blocking install-path polling sleeps while preserving retry semantics and progress.
- Forbidden: nested event loops, busy waiting, ad hoc threads, live service dependencies and unrelated UI rewrites.
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior Tester.
- Conditional roles: Console/status UI reviewer, Senior Documentation Engineer, resilience engineering, issue-completion-auditor.
- Quality: `git diff --check`; focused Nexus/SonarQube/Infisical tests; `python3 tools/quality_gate.py quality`.
- Evidence: `.tiny-swarm/evidence/issue-144/` using the #152 performance contract.
- Source: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/144

