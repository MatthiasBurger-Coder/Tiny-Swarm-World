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
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_progress_trace_ui
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ui.test_command_runner_ui_failure_semantics
PYTHONPATH=src python3 -m unittest tests.infrastructure.logging.test_progress_trace_logging
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition tests.test_package_entrypoint
python3 tools/quality_gate.py quality
```

Governing input hashes:

- `AGENTS.md`: `e038d8a8b5baddbc2886e47a5a2596a4a5bf222a`
- `QUALITY.md`: `08c7475fe511ac39c215284c5c1f23117848b567`
- `documentation/epics/system-unification.md`: `489f0123f604cc40700721a45bacdf22ba0260a2`
- `documentation/epics/autonomous-runnable-setup.md`: `db17388e1e92be425e253be89e8628a378d4532d`
- `documentation/arc42/06_runtime_view.adoc`: `6be2a5208f050324fd06727e148d7bae95def7e8`
- `documentation/arc42/09_architecture_decisions.adoc`: `45bf3590092cdc03b8d46b560f518c890361f87e`
- `documentation/arc42/10_quality_requirements.adoc`: `bbb8de787bb5a0b28f70e267d929662216ee57e0`
- `documentation/architecture/adr-cross-cutting-method-trace-logging.adoc`: `b250dab725233e0c304afe3e3d4aab285a94fa6d`
- `documentation/workflow/workflow.md`: `d33caab516a97674605f6529f765519e185da8aa`
- `src/tiny_swarm_world/application/services/commands/command_executer/command_executer.py`: `f57e1c8806949b456344a6877984178344f27d1c`
- `src/tiny_swarm_world/application/ports/method_trace/port_method_trace.py`: `b6569265188abc0d86869a13ba7083739f948777`
- `src/tiny_swarm_world/application/services/shared/method_trace_wrapper.py`: `b4f11e3a6d66d6394f97259222565f0c3a5ddfa7`
- `tests/architecture/test_installation_method_trace_coverage.py`: `a31d093c54740c269f554030b790fdc150b98916`
- `src/tiny_swarm_world/application/services/setup/workflow.py`: `668ce756f7854bea8fcb3e0531418540340f6634`
- `src/tiny_swarm_world/application/services/platform/workflows.py`: `59029e9b114f792f1616572aeb64d1cb111d236b`
- `src/tiny_swarm_world/infrastructure/composition.py`: `74f368e97a2bee834cad853b8a8c8b92964664bc`
- `src/tiny_swarm_world/__main__.py`: `4d65cc09e5bbc68cd205f179141cba4025b56b93`
- `src/tiny_swarm_world/infrastructure/adapters/ui/progress_trace_ui.py`: `6d8ec50d3844277b2cb66a9cc0b5b11625f0eec8`
- `src/tiny_swarm_world/infrastructure/logging/progress_trace_logging.py`: `da6b8ce7d0152e2cc84a5d14f69dc9721bcd807e`
- `src/tiny_swarm_world/infrastructure/adapters/ui/command_async_runner_ui.py`: `8ed34bb8eb4a2a5a3bcf6fe27b52a5adb5fee69d`
- `src/tiny_swarm_world/infrastructure/adapters/ui/command_sync_runner_ui.py`: `660c845ac03e1b81b3e38f70a7263a8d74fc6f24`
- `tests/infrastructure/adapters/ui/test_progress_trace_ui.py`: `28336e3e9ec68fe9f1c2a2d5fb11727bb3765588`
- `tests/infrastructure/logging/test_progress_trace_logging.py`: `190de2300d989806ecd943e490c850c3cb0b230d`
- `tests/test_package_entrypoint.py`: `b1d79ef188fe18b28ab7927efbb33ea73e6a2456`
- `tests/infrastructure/test_composition.py`: `4cdfb7f875ac6c8397a45f61e106139880873a1c`

Freshness rule:

- This context pack is stale when any hash above changes, when active branch
  differs from the recorded branch, or when a slice attempts to write outside
  its allowed scope.
