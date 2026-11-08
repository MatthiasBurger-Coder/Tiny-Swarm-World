# Registration native WSL binary admission

Root explicitly released this narrow source fix after actual read-only Plan
failed in Observe with foreign_evidence_owner. Windows source00c was verified
clean. A separate actual read-only probe confirmed the resolved executable is
System32/wsl.exe, owned by TrustedInstaller, with Valid Authenticode signature.
Raw error/ScriptStackTrace retained privately; SHA256
056246b0d14afb1106c440f07b6ecfadb2df870d6a60727aa3df6ae3e6cae8f5.
No registration Import, guest start/stop or original mutation was attempted.

| Requirement | Implementation / evidence |
| --- | --- |
| Distinguish OS executable trust from private evidence ownership | Only registration TrustedWsl changes; generic evidence validator unchanged |
| Exact native executable | Require 64-bit process/OS and absolute System32/wsl.exe; no PATH/actor-owned replacement |
| Full trusted native chain | System/Administrators/TrustedInstaller owners only, every ancestor; no reparse, untrusted delete/replace/ACL rights; leaf also denies untrusted writes |
| Signed Microsoft binary | Valid signature and exact Microsoft Corporation organization, matching existing GuestSwitch NativeExecutable policy |
| Regression at actual consumer boundary | Real production-module TrustedWsl validates actual Windows binary, then fake foreign owner/reparse/write/invalid signature/impostor signer/wrong path all refuse |
| Preserve read-only Plan semantics | No change to source pins, image, registry, preservation, import intent/receipt or budgets |

Four file locks: registration source, its PowerShell fixture, Python launcher,
this record. No shared native parser/helper or other worker files changed.
Python AST and git diff whitespace checks only; tests and PowerShell parse have
NOT_RUN by author. Root owns exact staged PC checks and source integration.
Actual successful Plan must be retried only after Root integrates/pins a clean
committed successor Windows source; no accepted scenario is fabricated from the
failed observation and no fake preserve hash is supplied for Import.

Root static review correction: the new actual native trust regression explicitly
selects Windows PowerShell on Windows/WSL and skips elsewhere. Generic fake
fixture tests retain their existing runtime selector; Linux pwsh is not used
for Windows ACL/AuthentiCode interop. No tests executed for this correction.

Root integration verification: all 3 nearest tests actually PASS on the approved
PC/WSL host (6.444s), including the real native binary policy and all fake denial
cases. Exact affected files hash-checked before execution; log SHA256
`10fd274de85b178ef6fbcbea6944aaa55c90646798e04adae7bf06d2308e1ca5`.
No registration import or host qualification success is inferred.
