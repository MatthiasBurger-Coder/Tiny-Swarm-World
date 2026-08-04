# Issue #218 — Native Linux regression

## Actual native-host execution — PASS for host-platform regression

The regression was executed in the disposable Incus VM
`tsw-issue-218-native-linux`:

```text
OS: Ubuntu 24.04.4 LTS
Kernel: 6.8.0-136-generic x86_64
WSLInterop: absent (/proc/sys/fs/binfmt_misc/WSLInterop does not exist)
Python: 3.12.3
```

The real CLI host detector returned:

```text
environment=native_linux
setup_path=native_linux
platform_family=linux
windows_interop_available=false
supported=true
static_validation_only=false
```

The composed native host-preparation service was executed directly for all
three operations:

```text
prepare: SUCCESS, verified=true, changed=false
verify:  SUCCESS, verified=true, changed=false
cleanup: SUCCESS, verified=true, changed=false
evidence: windows_command_runner=not_selected, mutation=none
```

The targeted native/host/architecture suite was then run inside the same VM.
Result: `202` tests, `0` errors, `0` failures, `OK`.

The VM intentionally did not run a complete Docker/Incus service deployment:
its network was unavailable, it had no Docker or Incus CLI, and its measured
2 CPUs/4 GiB/limited disk would correctly fail the full-profile resource gate.
That limitation does not affect the native host-routing regression: no
Windows command runner, PowerShell, `wsl.exe`, `netsh`, firewall, portproxy or
Windows-hosts mutation was selected or invoked.

The disposable VM was removed after evidence capture; it was not a product
environment or a substitute for the real WSL2 acceptance run.
