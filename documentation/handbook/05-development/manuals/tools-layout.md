# Bootstrap and developer-tool layout

[Product Handbook](../../../README.adoc) / [Part 5: Development](../README.adoc)

Choose the directory by purpose, then by target system. Installation preparation
belongs under `bootstrap/windows` for Windows/WSL and `bootstrap/linux` for native
Linux and shared Linux/WSL prerequisites. Quality, audit, packaging, qualification
and developer tools remain under `tools`. Product Python still executes on Linux
or inside WSL; WSL-specific preparation belongs to the Windows installation path.

```text
bootstrap/
  windows/
    optional/         Optional Windows-side DNS resolver
    preparation/      Windows preparation, WSL shell helpers and validation
    ...               Windows bridge, TLS trust and host diagnostics
  linux/
    ...               Interpreter prerequisites, preflight and install diagnostics
tools/
  windows/
    live/             Hyper-V test VM and Windows portproxy cleanup
    ...               Release-proof and WSL resource-projection generators
  linux/
    live/             Shared secure runtime paths for credentials and evidence
    qualification/    Bounded native runtime inventory and Incus qualification
    ...               Python quality, audit and developer tools
tests/
  e2e/classic/        Classic live acceptance runner and end-to-end tests
```

## Entry points and handoff

- Native Linux: `./bootstrap/linux/prepare_linux.sh` invokes
  `bootstrap/linux/ubuntu_python_prerequisites.sh`, then the Python preparation service.
- Windows/WSL: `./bootstrap/windows/prepare_windows.ps1` loads PowerShell modules from
  `bootstrap/windows/preparation`. These invoke `bootstrap/windows/preparation/linux-*.sh`
  inside the selected running WSL distribution. The installation handoff retains
  its selected Linux user, source identity, consent and readiness checks.
- Quality: `python3 tools/linux/quality_gate.py quality` from the repository root.
- Diagnostics: `python3 bootstrap/linux/install_debugger.py` on Linux/WSL.
- Live acceptance: `tests/e2e/classic/run_classic_acceptance.py` orchestrates the
  authorized Classic acceptance chain. It requires explicit live approval and
  can change the test system; ordinary test discovery does not execute it.
- Packaging: `tools/windows/build_windows_preparation_manifest.py` and
  `tools/windows/build_wsl_resource_projection.py` support Windows/WSL preparation.
  Run them with Python on Linux/WSL; their directory does not authorize execution
  through Windows Python.
- The optional DNS resolver under `bootstrap/windows/optional` belongs to the
  Windows bridge; it does not execute product Python.

## Path migration

| Previous location | Current location |
| --- | --- |
| Quality, audit and developer `tools/*.py` | `tools/linux/*.py` |
| `tools/preflight.py`, `tools/install_debugger.py` | `bootstrap/linux/` |
| Windows preparation and bridge under `tools/windows` | `bootstrap/windows/` |
| `tools/build_windows_preparation_manifest.py` | `tools/windows/build_windows_preparation_manifest.py` |
| `tools/build_wsl_resource_projection.py` | `tools/windows/build_wsl_resource_projection.py` |
| `tools/ubuntu_python_prerequisites.sh` | `bootstrap/linux/ubuntu_python_prerequisites.sh` |
| `tools/live/run_classic_acceptance.py` | `tests/e2e/classic/run_classic_acceptance.py` |
| `tools/live/secure_runtime_paths.py` | `tools/linux/live/secure_runtime_paths.py` |
| `tools/live/*.ps1` | `tools/windows/live/*.ps1` |
| `tools/qualification/*.py` | `tools/linux/qualification/*.py` |
| WSL preparation helpers | `bootstrap/windows/preparation/linux-*.sh` |

Use the current paths for commands and Python imports (`tools.linux.*` for shared
tools and `tools.windows.*` for Windows/WSL-specific packaging). Old
entry points are removed. Historical evidence, accepted ADRs and workflow
snapshots retain their original paths and source hashes; they describe their
recorded revision. Future qualification needs fresh source-bound authorization
and must not reuse historical GO records for the relocated tools.

## Migration scope and verification

The migration separates bootstrap from developer tools, updates callers/imports, CI, source-proof
catalogues and isolated test fixtures, then updates operational documentation.
Shared path and source-proof dependencies require serial implementation.
Domain rules, infrastructure mutation guards and quality thresholds are preserved.

An independent architecture review identified caller and fixture dependencies.
Agent-run verification requires SSH to `pc@192.168.178.58`, execution inside WSL,
and confirmation that the remote files match this checkout. After SSH access was
restored, an earlier tools-only layout had 1,905 snapshot files verified by SHA-256
and 337 focused tests passed on Python 3.12.15. Those results predate the bootstrap
split and acceptance-runner move and do not verify the current layout. The full quality gate was stopped at
the user's request and has no completed result. No live qualification was executed.

Further tests and quality gates run only when creating a pull request or on an
explicit verification request. Test-host credentials alone do not authorize a
run. When verification is authorized, run the focused tests first:

```bash
PYTHONPATH=src python3 -m unittest tests.tools.test_platform_layout tests.test_ci_workflow_contract tests.test_install_debugger tests.test_security_gate tests.test_ubuntu_prerequisites tests.test_prepare_windows tests.test_windows_source_proof tests.test_wsl_resource_projection tests.test_install_handoff tests.test_install_script tests.tools.test_secure_runtime_paths tests.tools.test_classic_live_runner tests.tools.test_native_runtime_inventory tests.tools.test_native_lxd_snap_provenance tests.infrastructure.adapters.clients.test_lxc_profile_listener_fixture
python3 tools/linux/quality_gate.py quality
```
