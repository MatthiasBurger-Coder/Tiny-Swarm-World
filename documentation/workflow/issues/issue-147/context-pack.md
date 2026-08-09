# Context Pack — Issue #147

- Workflow: `issue-147-20260809` / `issue-147-v1.0.0`
- Branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`
- Baseline: `b8c64eaa50839fcbf4581ca819286ad13ee88300`
- Process strand: `workflow-create-to-workflow-execute`
- Execution profile: `FULL_PATH`
- Scope: eliminate duplicate stack verification and repeated step-local remote/API lookups.
- Forbidden: long-lived cross-invocation caches, stale-state suppression of required refresh, changed deployment semantics and live API dependence.
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior Tester.
- Conditional roles: resilience engineering, Senior Documentation Engineer, issue-completion-auditor.
- Quality: `git diff --check`; `tests.application.services.deployment.test_ensure_service_stack`; full gate.
- Evidence: `.tiny-swarm/evidence/issue-147/` using #152 call-count measurements.
- Source: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/147

