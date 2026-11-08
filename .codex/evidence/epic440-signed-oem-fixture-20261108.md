# Signed executable OEM transport fixture

Scope: `tests/windows/prepare-windows.Tests.ps1` and this record, isolated from frozen qualification source 86e5ef64f53885b135b14a069756b9cf8dfe39d9. Production files and Windows policies remain unchanged.

Actual full quality on source 86e5ef64: 3712 tests, one failure, 36 skips. Log SHA256 `30a2678cf6a3fe9b190a9fdbb8d58a62eb12d4770087003561be194d22d253b6`. Application Control refused Process.Start for the fixture's generated unsigned executable. This result remains failed.

The fixture now copies the fixed system-directory Microsoft-signed cmd.exe bytes into its own temporary Dism.exe and Other.exe. Signature and copy hashes are asserted. Its built-in type emits a fixture-owned OEM byte file to both actual redirected pipes; no DISM feature query runs. The existing exact stdout/stderr OEM assertions and non-DISM strict UTF-8 denial remain. Current directory and output encoding are restored before temporary cleanup. No policy exclusions, generated unsigned executable, skips, adapter mocks or relaxed assertions are introduced.

Root authorized one targeted execution on designated PC/WSL with process umask 022 and private 0600 log. Integration is deferred until the qualification/matrix promotion boundary is complete. Live product qualification is not claimed.

Actual nearest result: designated PC 192.168.178.58, existing Ubuntu/pc, fresh source 86e5ef64 plus only this fixture overlay; `python -m unittest -v tests.test_prepare_windows` PASS, 11 tests in 27.345 seconds, exit 0. Fixture SHA256 `193af23339e2f07a51962038f879b4075e17be63ecea523bd76e5c6f80421ca1`; log SHA256 `ae4380b5d43626be1487ba37c2dd27a873e84194e37ebd72ce57d1f3ad7be68b`. Full quality was not repeated. The original full failure remains preserved and is not relabeled as a pass.
