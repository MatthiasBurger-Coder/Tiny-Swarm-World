# Context Pack — Issue #156

- Workflow: `issue-156-20260809` / `issue-156-v1.0.0`
- Branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`
- Baseline: `b8c64eaa50839fcbf4581ca819286ad13ee88300`
- Process strand: `workflow-create-to-workflow-execute`
- Execution profile: `FULL_PATH`
- Scope: central registry-backed direct Docker published ports, effective URLs/health and evidence.
- Forbidden: Incus/LXC setup, Docker installation, Swarm bootstrap, Traefik redesign, local DNS/hosts changes, RabbitMQ reintroduction.
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior Tester.
- Conditional roles: Senior DevOps Engineer, Senior Documentation Engineer, arc42 governance, issue-completion-auditor.
- Quality: `git diff --check`; targeted Compose/config tests; `python3 tools/quality_gate.py quality`.
- Evidence: `.tiny-swarm/evidence/issue-156/` plus slice distribution/consolidation evidence.
- Source: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/156

