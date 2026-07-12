# Issue #218 Phase-3 Baseline Inventory

Date: `2026-07-12`
Mode: read-only static inventory; no live command or product mutation
Purpose: preserve the issue-required baseline for later FR workflows. Findings
are routed to their owning FR and are not presented as FR-1 implementation.

## 1. WSL treated as native or classified outside the typed detector

Search scope: `src`, `tools`, and `infra/config`; Python, shell, and YAML files.
Signals searched: `WSL_INTEROP`, `WSL_DISTRO_NAME`, Microsoft/WSL kernel text,
`platform.system`, `OsTypes`, and `is_linux_or_wsl`.

Findings:

- Active preflight, installer, `OsTypes.detect_current`, network runtime, and
  CLI classification now delegate to the FR-1 typed detector.
- `tools/install_debugger.py:309-311` still owns a separate WSL/native heuristic.
- `infrastructure/adapters/file_management/path_strategies/path_factory.py`
  and `infrastructure/adapters/ui/factory_ui.py` still select only from
  `platform.system()`/legacy `OsTypes` parsing.
- `PortHostPreflightProbe.is_linux_or_wsl` remains a legacy compatibility
  boolean, but its default typed report now fails closed as sandbox-unverified.

Owners: FR-8 for generic path/command cleanup and FR-14 for complete native
isolation. Status: `OPEN` outside the FR-1 active-consumer consolidation.

## 2. Hard-coded WSL, Windows, and repository assumptions

Fixed-string search covered the issue's Windows mount examples, `wsl.exe`,
PowerShell/pwsh, netsh/portproxy, Windows system paths, and drive-letter paths.

Findings:

- `installer.py`, the preflight port default, and
  `windows_wsl_bridge_state.py` contain the fixed ProgramData bridge path under
  the Windows system mount.
- `installer.py` and `application/services/network/host_integration.py` contain
  direct PowerShell command guidance; the application service also embeds
  Windows command strings.
- `tools/windows/optional/tws_dns_resolver.py` invokes `wsl.exe`; this is an
  explicitly Windows-only optional tool but still requires ownership review.
- `host_network_repair.py` contains PowerShell execution in an infrastructure
  adapter, which is the correct technology layer but must be governed by the
  dedicated FR-7 Windows Service Agent boundary.
- No committed product/config match for a fixed project-checkout root was found
  in the scanned scope.

Owners: FR-2, FR-7, FR-8, and FR-14. Status: `OPEN`.

## 3. Long-running workflows and calls without an outer timeout

Search covered synchronous/async subprocess creation, `asyncio.wait_for`, and
timeout parameters.

Findings:

- `installer.ensure_python_environment` creates the venv and runs pip commands
  with no subprocess timeout.
- `installer._python_imports_available`, `_run_phase`, `_run_text`,
  `_inside_git_worktree`, and `_git_check_ignore` use subprocess calls without
  a centrally governed outer workflow timeout.
- `composition._wsl_socat_process_exists` and `_start_wsl_socat_command` wait
  for child exit without an explicit bound.
- Many LXC/Docker/HTTP/network adapters already have individual timeout values,
  but they are not yet proven complete or governed by the FR-11 central outer
  status taxonomy. The scan also identifies unbounded calls that FR-12 must
  close individually.

Owners: FR-9, FR-11, FR-12, and FR-13. Status: `OPEN`.

## 4. Chained or semantically bundled apply/verify steps

The literal shell-chain search for `&&`/`;` around deployment/platform verify
found no active source/config shell chain in the scanned scope.

Semantic bundling remains:

- `infrastructure/composition.py:1380-1387` places `deployment apply`,
  `deployment verify`, and `platform verify` inside one setup workflow phase
  bundle.
- `domain/preflight/installation_plan.py:223-225` groups all three workflow
  names under one installation phase.
- These in-process steps are ordered, but FR-10 still requires distinct
  installer steps, individual evidence/exit status, and an explicit rule that
  platform verify is never started after deployment verify fails or times out.

Owner: FR-10, with FR-11/12/15 verification. Status: `OPEN`.

## Inventory conclusion

The four inventories are now explicit and persisted. FR-1 resolves only the
active host-classification divergence declared by its workflow. Every other
finding remains routed to its later owning FR; this document authorizes no
scope reduction and no premature `VERIFIED` status.
