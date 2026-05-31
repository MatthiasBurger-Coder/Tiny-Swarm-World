# Workflow Context Pack

Workflow: `install-observability-console-status-v1.0.0`

Branch: `feature/workflow-install-observability-20260529`

Process strand: `S3D`

Execution profile: `NORMAL_PATH`

Affected areas:

- setup orchestration
- platform workflows
- command executor status behavior
- terminal console status UI
- centralized logging
- composition wiring

Forbidden areas:

- browser or React frontend
- Kubernetes-first behavior
- Java, Maven, or Spring Boot structure
- live LXD/Incus/LXC/Docker/Swarm/compose/service bootstrap during default gates
- Windows-specific expansion

Required roles:

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer
- Senior Tester

Conditional roles:

- Console/status UI skills
- Senior Documentation Engineer
- Senior DevOps Engineer if live-command semantics are touched

Quality commands:

```bash
git diff --check
PYTHONPATH=src python3 -m unittest tests.application.services.commands.test_command_executer
PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_linux_ui
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_command_runner_ui_failure_semantics
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.test_package_entrypoint
python3 tools/quality_gate.py quality
```

Governing input hashes:

- `AGENTS.md`: `05de31b1c980f393d9dd83e744a2debfdc1b6e0a`
- `QUALITY.md`: `17002150bab9f168eb60be85d55b7a0c1cb441e5`
- `documentation/epics/system-unification.md`: `ca0710c2a98c762c997f4f8e98d93d081bc6375c`
- `documentation/epics/autonomous-runnable-setup.md`: `be3fbac77027c2d5af95e6f00794000949584d56`
- `documentation/arc42/06_runtime_view.adoc`: `6546c837d3cfff9a3b0fb87263cac5aeb76606f9`
- `documentation/arc42/10_quality_requirements.adoc`: `f7331a4d5a9c78b27b610fb266985652d7196045`
- `src/tiny_swarm_world/application/services/commands/command_executer/command_executer.py`: `96e0db019bd3efa70498f871e2cfc7a196a1e1c9`
- `src/tiny_swarm_world/application/services/setup/workflow.py`: `e68f5b987628f14950063d98dd552a9619826b09`
- `src/tiny_swarm_world/application/services/platform/workflows.py`: `160184a8429ad2730a28518f262989c7769d280b`

Freshness rule:

- This context pack is stale when any hash above changes, when active branch
  differs from the recorded branch, or when a slice attempts to write outside
  its allowed scope.
