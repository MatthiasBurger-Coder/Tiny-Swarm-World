# Registration preservation: bounded full WinSW log hashing

Root released four isolated files from clean8ba4e86f. Actual read-only Plan
passed native WSL admission, then failed GlobalProof BRIDGE_FILE_BOUND for
TinySwarmWorldWslBridge.out.log.old, 5,641,197 bytes. Raw exception/stack remains
private under registration-plan-readonly-r3 (SHA55e7ee6452c268825cd8cbf78f55e356b134e69245f58faa4562efbfc66e5122).
No Import, service operation, guest mutation or file cleanup occurred.

Source New-BridgeServiceDefinition emits logpath %BASE%/logs, log mode=roll,
with no sizeThreshold. Its exact XML parser rejects nested threshold settings.
Pinned primary https://raw.githubusercontent.com/winsw/winsw/v2.12.0/doc/xmlConfigFile.md
(logging section) defines startup roll as moving logs to *.old. Thus 16MiB is
an explicit admitted observation bound, NOT a claimed configured rotation size.
The separate roll-by-size default10MB documented in loggingAndErrorReporting.md
is not our configured mode and is not used as authority.

| Contract | Change / verification |
| --- | --- |
| Preserve all bytes | Full SHA256 via bounded 64KiB streaming, no truncation/omission/sampling |
| Narrow larger input | Only four exact direct logs/WinSW stdout/stderr current/old names admit16MiB; other paths/files retain4MiB |
| Existing checks | Recursive128-entry count, owner/ACL/no-reparse checks before and after hashes, routes/firewall/service/config/source proofs unchanged |
| Aggregate bound | All bridge file lengths, including excluded mutable state, sum<=64MiB; collected length must equal opened stream length; growth/mtime/length drift refuses |
| Time/transport | Existing2400s deadline checked each stream chunk; no stdout/RAM transport/command cap increase |
| Regression | Actual5,641,197-byte temporary log fullhash equals Get-FileHash; changed bytes change actual GlobalProof; unknown/nested oversized files, >16MiB, collected-length drift, >64MiB aggregate all refuse |

Tests use actual production module GlobalProof/file classification/hash functions,
actual temporary filesystem bytes and synthetic external certificate/route/service
transport plus evidence-path port. They do not query providers or change services,
registrations, source payload or host logs. No broad bridge directory adoption,
ACL repair, log deletion or current service control is introduced.

Nearest PC test: python -m unittest tests.tools.test_wsl_acceptance_registration
(includes new real bridge log preservation case). Root stages exact assets and
runs tests through authorized WSL. Author ran AST/diff-whitespace checks only;
PowerShell parsing/tests are ACTUAL NOT_RUN. No actual Plan retry until integrated
clean successor source and Root execution; resource-parent source8ba remains
immutable. Four locks: registration PS, its PS fixture/Python launcher, this file.

Root review correction: the new GlobalProof log fixture explicitly selects
native Windows PowerShell on Windows/WSL and skips elsewhere, matching the
existing actual native executable test; generic pure fixtures remain unchanged.

Root integration verification: all 4 nearest tests actually PASS on the approved
PC/WSL host (6.656s), including the full 5,641,197-byte preservation hash and
changed-byte, unknown/nested log, per-file/aggregate bound denials. Exact affected
source/fixtures hash-checked before execution. Log SHA256:
`a46b63941b1bb4d7d490590f908e94f9b920d15a77011c83a8d28c810c46e23d`.
No registration import or host qualification PASS is inferred.
