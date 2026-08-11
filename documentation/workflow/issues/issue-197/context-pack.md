# Context Pack — Issue #197

- Workflow: `issue-197-20260809` / `issue-197-v1.0.0`
- Branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`
- Baseline: `b8c64eaa50839fcbf4581ca819286ad13ee88300`
- Process strand: `workflow-create-to-workflow-execute`
- Execution profile: `FULL_PATH`
- Scope: extract WSL Socat process inspection/start behavior from composition wiring into infrastructure.
- Forbidden: domain/application leakage, weakened LiveConsent, live Socat/LXC/Incus/Docker execution in tests.
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior Tester.
- Conditional roles: Senior Workflow Architect, Senior Documentation Engineer, issue-completion-auditor.
- Quality: `git diff --check`; `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition`; architecture/full gate.
- Evidence: `.tiny-swarm/evidence/issue-197/` plus slice distribution/consolidation evidence.
- Source: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/197
