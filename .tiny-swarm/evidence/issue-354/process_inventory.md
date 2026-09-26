# Process inventory before migration

| Location | API | Ownership |
|---|---|---|
| `src/tiny_swarm_world/infrastructure/adapters/clients/infisical_cli_client.py:339` | `result = subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/node_command.py:40` | `process = await asyncio.create_subprocess_exec(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/common.py:39` | `runner = run or subprocess.run` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_portainer_http_client.py:136` | `result = subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py:239` | `run=subprocess.run if self.process_runner is None else None,` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py:260` | `run=subprocess.run if self.process_runner is None else None,` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py:274` | `run=subprocess.run,` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/command_runner/async_command_runner.py:38` | `process = await asyncio.create_subprocess_shell(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/host/hang_diagnostics.py:61` | `completed = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/host/windows_command_runner.py:25` | `popen: Callable[..., subprocess.Popen[str]] / None = None,` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/host/windows_command_runner.py:30` | `self.popen = popen or subprocess.Popen` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/host/windows_command_runner.py:90` | `def _terminate(self, process: subprocess.Popen[str]) -> tuple[str, str]:` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/host/windows_command_runner.py:105` | `result = subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/host/wsl_resource_inspector.py:153` | `result = subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/host/wsl_resource_inspector.py:173` | `result = subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/network/host_network_probe.py:178` | `completed = subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/network/host_network_repair.py:266` | `completed = subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/network/wsl_socat_exposure.py:44` | `process = await asyncio.create_subprocess_exec(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/network/wsl_socat_exposure.py:55` | `process = await asyncio.create_subprocess_exec(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/preflight/artifact_readiness.py:289` | `completed = subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/preflight/artifact_readiness.py:311` | `completed = subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/preflight/lxc_provider_preflight.py:84` | `process = await asyncio.create_subprocess_exec(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/preflight/windows_wsl_bridge_state.py:264` | `completed = subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/adapters/ui/windows_ui.py:27` | `os.system("cls")  # Clear screen in Windows` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/composition_probes.py:235` | `result = subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/process/runner.py:74` | `"""Concrete runner backed by ``subprocess.run`` with safe defaults."""` | Runtime boundary migration |
| `src/tiny_swarm_world/infrastructure/process/runner.py:150` | `result = subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/installer.py:1038` | `return subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/installer.py:1280` | `process = subprocess.Popen(` | Runtime boundary migration |
| `src/tiny_swarm_world/installer.py:1301` | `def _terminate_process(process: subprocess.Popen[bytes]) -> None:` | Runtime boundary migration |
| `src/tiny_swarm_world/installer.py:1727` | `return subprocess.run(` | Runtime boundary migration |
| `src/tiny_swarm_world/installer.py:1748` | `result = subprocess.run(` | Runtime boundary migration |
| `tools/coverage_diff.py:54` | `result = subprocess.run(` | Standalone development/bootstrap tool; separate lifecycle |
| `tools/install_debugger.py:725` | `result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)` | Standalone development/bootstrap tool; separate lifecycle |
| `tools/live/run_classic_acceptance.py:377` | `completed = subprocess.run(` | Standalone development/bootstrap tool; separate lifecycle |
| `tools/live/run_classic_acceptance.py:718` | `result = subprocess.run(` | Standalone development/bootstrap tool; separate lifecycle |
| `tools/quality_gate.py:129` | `completed = subprocess.run(` | Standalone development/bootstrap tool; separate lifecycle |
| `tools/security_gate.py:104` | `completed = subprocess.run(command, check=False, cwd=REPOSITORY_ROOT)` | Standalone development/bootstrap tool; separate lifecycle |
| `tools/windows/optional/tws_dns_resolver.py:65` | `result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=True)` | Standalone development/bootstrap tool; separate lifecycle |

Terminal clearing is presentation only; use terminal escape output without a process. Pure filesystem/string operations remain unchanged.
