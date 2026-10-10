# Implementation summary

Issue status: BLOCKED. Frozen runtime candidate:
`3da77f8908d598688ed46dd6eab74c5f32a7ac50`, based on integrated #459/#460.
The narrow urllib3 lock correction passes strict audit and full Python 3.12
quality. A live checkpoint persistence defect is now being remediated in the existing Windows adapter; product Python is unchanged. The existing completed #355
workflow was not executed or replaced. Branch:
fix/boot-w09-live-qualification-20261010.

Authorized native existing-host tests prepared an owned Python venv and isolated
checkpoint state, preserving eight/nine measured existing file scopes and three
running nodes. Network preparation blocked on existing IPv6-enabled bridges.
Native fresh-host and recoverable fault-test prerequisites remain missing.

The authorized isolated Hyper-V Windows environment now boots Windows 11
Enterprise Evaluation 26H2 build 26300.9457. Windows OS-only provisioning used
24 GiB; answer credentials were removed and verified absent. A scoped owned-VM
storage ACL repair preserved the private parent ACL. Its clean pre-WSL checkpoint
was subsequently restored and booted with matching version, absent candidate
marker, no WSL and VirtualMachinePlatform Disabled. This verifies environment
recovery only. The guest stopped normally and 32-GiB RAM was set and observed.

Source-bound guest dry-run verified the frozen SHA and exited 2 with only
Windows feature prerequisites pending; measured configuration/registration
invariants were unchanged (partial S13). The prepared full 32-GiB feature-only
phase retains the 34-GiB free-host guard. The first UAC launch was canceled
(host exit 1). The authorized retry passed that guard at 34.676 GiB, booted
the full guest, and confirmed enable_features. Apply returned exit 4 PARTIAL
because effect checkpoint persistence failed. Independent inventory and saved
effect evidence confirmed both features Enabled and a pending Windows reboot.
A separate owned-guest recovery restart verified the boot transition and exact
source; post-restart dry-run exits 2 with only install_wsl pending.

A protected disposable-directory reproduction preserves the canonical pending
checkpoint and identifies PowerShell null argument conversion at File.Replace.
The narrow NullString correction preserves atomic replacement and all ACL/state
guards. A new real-filesystem regression passes under Windows PowerShell 5.1.
The revised candidate passes the full Python 3.12 quality retry and the Windows
PowerShell 5.1 filesystem regression. Source freeze and revised live application
are still pending. The original failed gate remains recorded.

The operator then manually installed WSL/Ubuntu in the owned VM. Read-only
inspection confirms WSL 3.0.1.0 and running Ubuntu 26.04.1 LTS/x86_64/systemd.
Its approximately 16-GiB WSL memory and 12 processors still need the selected
21-GiB/8-processor allocation. Preserve this operator-created registration;
manual prerequisites do not count as candidate-executed install qualification.

All releases remain UNQUALIFIED. AC1/AC2 and the required product install,
rerun, recovery, preservation/reset and authentication scenarios remain open.
Separate destructive WSL reset authorization is still absent. No issue close,
push, PR or merge is implied by the local verification/environment progress.
