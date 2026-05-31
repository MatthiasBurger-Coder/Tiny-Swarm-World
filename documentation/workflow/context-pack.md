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
- cross-cutting method trace logging
- installation runtime trace coverage
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
- Senior Tester
- Senior Documentation Engineer

Conditional roles:

- Console/status UI skills
- Senior Documentation Engineer
- Senior DevOps Engineer if live-command semantics are touched

Quality commands:

```bash
git diff --check
PYTHONPATH=src python3 -m unittest tests.application.ports.test_method_trace
PYTHONPATH=src python3 -m unittest tests.application.services.shared.test_method_trace_wrapper
PYTHONPATH=src python3 -m unittest tests.architecture.test_installation_method_trace_coverage
PYTHONPATH=src python3 -m unittest tests.application.services.commands.test_command_executer
PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_platform_workflows
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_linux_ui
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_command_runner_ui_failure_semantics
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.test_package_entrypoint
python3 tools/quality_gate.py quality
```

Governing input hashes:

- `AGENTS.md`: `e038d8a8b5baddbc2886e47a5a2596a4a5bf222a`
- `QUALITY.md`: `08c7475fe511ac39c215284c5c1f23117848b567`
- `documentation/epics/system-unification.md`: `489f0123f604cc40700721a45bacdf22ba0260a2`
- `documentation/epics/autonomous-runnable-setup.md`: `db17388e1e92be425e253be89e8628a378d4532d`
- `documentation/arc42/06_runtime_view.adoc`: `c92d384c02f61b6deb866c3cb50e808962332b23`
- `documentation/arc42/09_architecture_decisions.adoc`: `218cd138207a6beb091677c875e13ff1968b4148`
- `documentation/arc42/10_quality_requirements.adoc`: `a0ac540f5e2e8acd1a62937b2322fbfa19a343c0`
- `documentation/architecture/adr-cross-cutting-method-trace-logging.adoc`: `65b57d3e9bcf5ee739735303400bf25fc7b61b16`
- `src/tiny_swarm_world/application/services/commands/command_executer/command_executer.py`: `38904d22f0522ee1b3de70c1866f2d66fd06b243`
- `src/tiny_swarm_world/application/ports/method_trace/port_method_trace.py`: `14a21e76ac7acf406cc403dd900424620e9061c1`
- `src/tiny_swarm_world/application/services/shared/method_trace_wrapper.py`: `c1d670f25d7cb795cbf6930b5dc3d1c610006943`
- `src/tiny_swarm_world/application/services/setup/workflow.py`: `c615e01e0b1bacc6a8572d59475f5ce1164058f5`
- `src/tiny_swarm_world/application/services/platform/workflows.py`: `cda2514fb66707ed5c6fa6ed876d90c12a7eb187`

Freshness rule:

- This context pack is stale when any hash above changes, when active branch
  differs from the recorded branch, or when a slice attempts to write outside
  its allowed scope.
