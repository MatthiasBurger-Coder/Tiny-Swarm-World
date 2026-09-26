# WSL / PowerShell interop recovery

The prior restricted execution environment did not expose /run/WSL sockets.
PowerShell attempts failed with UtilAcceptVsock. After the user changed this
session to unrestricted execution, the existing sockets were visible and the
same PowerShell invocation returned `interop-ok` with exit 0 in 0.358 seconds.
No WSL restart, service restart, socket deletion or host configuration change
was performed. This supports an execution-environment access issue; it does
not establish a persistent defect in the host WSL installation.

The previously blocked Pester test was rerun in the existing mounted checkout:
`python3 -m unittest tests.test_windows_wsl_bridge_assets.TestWindowsWslBridgeAssets.test_windows_service_behavior_contract_with_pester`
Result: PASS, one test in 9.734 seconds. The wrapper, test script and bridge
script were compared byte-for-byte against the issue worktree before retry.

The remaining independent path limitation is in the existing test wrapper:
it only translates /mnt/<drive> paths. Full final verification therefore uses
a source-identical mounted copy, checked by SHA-256 before and after the run.

For recurrence caused by a stale WSL_INTEROP value, a documented workaround is
to point it at the relay socket of an active WSL session. Merely finding a
socket is insufficient; test an actual Windows executable launch. Source:
https://github.com/microsoft/WSL/issues/41283

No permanently hard-coded relay PID is installed in project code or profiles.
