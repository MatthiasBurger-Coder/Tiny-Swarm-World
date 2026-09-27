# Issue #358 changed files

- `src/tiny_swarm_world/__main__.py`: thin command edge and compatibility exports.
- `src/tiny_swarm_world/cli_presentation.py`: CLI output formatting.
- `src/tiny_swarm_world/application/services/cli_dispatch.py`: typed action dispatch.
- `src/tiny_swarm_world/application/services/platform/host/prepare_with_preflight.py`: guarded host preparation use case.
- `src/tiny_swarm_world/application/services/setup/installation_plan.py`: setup preview data.
- `src/tiny_swarm_world/infrastructure/composition_cli.py`: workflow composition and execution binding.
- `src/tiny_swarm_world/infrastructure/composition.py`: CLI composition facade.
- `tests/test_package_entrypoint.py`: complete declared command registry coverage.
- `tests/architecture/test_hexagonal_imports.py`: command boundary assertion follows composition and application dispatch.
- `tests/application/services/platform/host/test_prepare_with_preflight.py`: preflight ordering and action coverage.
- `tests/infrastructure/adapters/network/test_host_network_repair.py`: drain the stub pipe in a flaky shell fixture exposed by the full gate.
- `tools/quality_gate.py`: lint and typecheck the CLI entrypoint and presentation module.
- `documentation/arc42/05_analysis/responsibility-separation-analysis.md`: current CLI boundary.
- `.tiny-swarm/evidence/358/*.md`: issue evidence.
