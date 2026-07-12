# FR-1 Characterization Baseline

Date: `2026-07-12`

Scope: read-only host detection, preflight, legacy OS/runtime consumers,
composition, installer, and package-entrypoint behavior before FR-1 product
changes.

Command:

```bash
PYTHONPATH=src "$TSW_QUALITY_PYTHON" -m unittest \
  tests.domain.preflight.test_host_environment \
  tests.infrastructure.adapters.preflight.test_host_preflight_probe \
  tests.infrastructure.adapters.network.test_host_network_probe \
  tests.infrastructure.test_os_types \
  tests.infrastructure.test_composition \
  tests.test_installer \
  tests.test_package_entrypoint
```

`TSW_QUALITY_PYTHON` resolved to the pre-existing shared WSL virtual
environment interpreter. Its host-specific absolute location is deliberately
not persisted in general workflow evidence.

Result: `PASS` — 222 tests ran in 6.622 seconds.

This characterization executed no live Incus, Docker, Docker Swarm, Windows,
network, or service mutation. Real WSL live validation remains `NOT_RUN`.
