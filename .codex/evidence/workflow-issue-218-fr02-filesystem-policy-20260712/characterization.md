# FR-2 Baseline Characterization

Date: `2026-07-12`
Baseline: `main@81ca7efab062347a87c32e5305427236b048d741`
Mode: read-only and simulated; live infrastructure `NOT_RUN`

## Green regression baseline

The existing installer, install-script, package entrypoint, preflight service,
host-preflight adapter, composition, project-path, and simulated host-platform
modules passed 281 tests in 14.990 seconds.

Command:

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_installer \
  tests.test_install_script \
  tests.test_package_entrypoint \
  tests.application.services.platform.test_preflight_service \
  tests.infrastructure.adapters.preflight.test_host_preflight_probe \
  tests.infrastructure.test_composition \
  tests.integration.test_host_platform_paths \
  tests.infrastructure.test_project_paths
```

The full gate on merged `main` also passed before workflow creation: Ruff,
3 import contracts over 300 files/687 dependencies, 18 architecture tests,
Mypy over 488 files, and 1,456 tests in 98.336 seconds with 28 expected skips.

Command:

```bash
python3 tools/quality_gate.py quality
```

## Expected FR-2 RED

- `--allow-wsl-windows-filesystem` is not accepted by the CLI/installer parser.
- A dedicated project-filesystem domain assessment and inspector port do not
  exist.
- `ProjectPaths` resolves repository paths but does not classify the backing
  filesystem.
- A simulated WSL2 live installer path can reach
  `ensure_python_environment` before any filesystem decision.
- The existing global `--preflight` has no `HOST-FILESYSTEM` check.
- No protected override-decision repository exists.

Read-only mount metadata shows the relevant WSL drive mount family as
`9p`/`v9fs` with a DrvFS characteristic. Exact host paths, usernames, mount
sources, and other host details are intentionally not persisted here.

## Baseline ordering

```text
repository check
-> host detection
-> Python dependency bootstrap
-> secrets/general evidence
-> reset
-> setup
```

FR-2 must insert filesystem evaluation/authorization immediately after host
detection and prove that `BLOCKED` prevents every later action.
