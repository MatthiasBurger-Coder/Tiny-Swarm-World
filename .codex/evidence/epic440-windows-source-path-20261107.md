# Epic 440 — native Windows source path transport

Status: VERIFIED_LOCAL by root; fresh committed-source preflight remains pending.
The isolated implementation worker ran no tests or host operations.
Baseline: `a09d104f7482c9eafb3b843562d65b33817cd9e7`.
Branch: `fix/epic440-windows-native-source-20261107`; isolated worktree.

Root's fresh read-only preflight established bounded Store WSL2 applicability but
reported source verification unavailable and resource_projection_unknown. Its
bounded diagnosis identified that Windows PowerShell Resolve-Path returns a
provider-qualified Path for the WSL UNC checkout, while ProviderPath is the
native UNC path required by Git -C and ResourceHost's native -File transport.
This does not authorize weakening source provenance or resource checks.

Microsoft's PathInfo.ProviderPath reference states that it returns the provider
internal path represented by PathInfo. Read on 2026-11-07:
https://learn.microsoft.com/en-us/dotnet/api/system.management.automation.pathinfo.providerpath?view=powershellsdk-7.4.0

| ID | Requirement | Implementation | Verification | State |
| --- | --- | --- | --- | --- |
| WPATH-01 | Pass native provider path to native process adapters from the actual entrypoint | prepare_windows.ps1 RepositoryRoot | Real entrypoint + actual SourceIdentity/ResourceHost adapter code, mocked process ports | VERIFIED_LOCAL |
| WPATH-02 | Preserve ordinary Windows drive path behavior | Same native canonical root initializer | Disposable Windows-drive fixture in same regression | VERIFIED_LOCAL |
| WPATH-03 | Retain source identity/resource/consent semantics | No adapter policy or validation changes | Existing suites + no host probes in fixture + root exact-source verification | VERIFIED_LOCAL |

## Concrete regression design

Resolve the provider's native path and canonicalize it with IO.Path.GetFullPath
before passing the root to native adapters. No string prefix stripping, source
bypass or special-case host path is introduced.

The regression copies the actual entrypoint, actual Adapters.ps1 and
ResourceAdapters.ps1 plus their declared public source assets into disposable
fixture roots. A fixture-only Preparation.psm1 replaces application ports; it
calls the real Get-PreparationSource and Invoke-PreparationResourceHost with the
entrypoint's received Options. Native process execution is mocked and asserts
that Git's -C and ResourceHost's -File receive the exact canonical native root
derived by the fixture's genuine Resolve-Path.ProviderPath plus GetFullPath.
Native roots cannot contain a provider prefix or dot/parent segments. No production injection hook
or test-only entrypoint parameter is added. All host mutation functions refuse.

On the approved WSL test host, one root is under local /tmp and reaches Windows
PowerShell through a genuine WSL UNC path; the other is in the selected Windows
account's disposable temporary directory and reaches it through a drive path.
With the old entrypoint, the UNC case passes a provider-qualified path to the
native mocks and fails. The drive case confirms unchanged drive semantics.
Both cases verify only fixture reads and owned temporary-file creation/removal;
no actual Git child, ResourceHost child, registry, ACL, WSL or network probe runs.

## Scope and execution plan

Serial worker implementation; root owns integration and PC-WSL verification.
Locks: bootstrap/windows/prepare_windows.ps1, tests/test_prepare_windows.py,
new tests/windows/prepare-windows-source-path.fixture.psm1 and this record.
No workflow/context edits, host access, runtime repair or publication.
Root must approve this design before source edits. Required focused entrypoint
regression and existing preparation suites run on exact transferred bytes via
approved PC WSL; full QUALITY and independent review precede acceptance.

## Implementation handoff

Root approved the concrete design before source edits. The product change is
only the native, canonical RepositoryRoot initializer. The new fixture imports
the real source/resource adapters, replaces their native process boundary,
and rejects unexpected probes/effects. Fake Git OIDs are explicitly local/mock
evidence only. The actual entrypoint runs from both genuine WSL UNC and Windows
drive roots; an additional disposable UNC control reinstates the historical
Path property and requires rejection, proving that the fixture distinguishes
the faulty transport. It introduces no production test hook.

Static `git diff --check`: PASS. No tests, PowerShell, Python execution or host
operation was run by this worker. No commit, push or publication performed.

| File | SHA-256 |
| --- | --- |
| bootstrap/windows/prepare_windows.ps1 | `7918c8135acec0a51291f090dd36f2f46b3ab4c819d360f81d8e80cb4552dbed` |
| tests/test_prepare_windows.py | `24eef9cf3da94ae59734b63c053a2f1b1a3c9b95550af79cd81ffc293c28b695` |
| tests/windows/prepare-windows-source-path.fixture.psm1 | `21656d279ea842c14c1b6751c9cd3f257647ae16851d169c6677c6c084494fb6` |

## UNC canonicalization correction

Root's initial exact-source combined focused run executed 251 tests and retained
one failing UNC transport regression; the drive case passed. Its separate
bounded Windows diagnosis found that native ProviderPath can preserve literal
parent segments for UNC paths. The entrypoint and fixture used different
relative parent depths, so lexical roots differed although GetFullPath made
them equal. The failed run is not a pass and remains retained by root.

The reviewed correction applies GetFullPath to the native ProviderPath in the
entrypoint and fixture reference. Native process/request assertions now require
the exact canonical root without provider prefixes or dot/parent segments.
The negative control replaces the complete fixture resolver with the original
historical Path expression, preserving the intended faulty-transport check.
Corrected-source tests remain NOT_RUN by this worker and require root's fresh
exact-source PC-WSL run. This does not change source/resource authority.

WPATH-01–03 passed independent exact-source architecture/security and tester/DevOps
review and root-run PC-WSL checks below. A successful mocked transport regression is not
actual source admission, resource readiness or Epic completion.


## Root exact-source verification

The corrected actual-entrypoint UNC/drive transport regression, historical
negative control, existing preparation contract and native inventory/provenance
suites passed together: 251 focused tests, exit 0 (17.507 seconds). Full seven-
stage QUALITY passed on the same exact candidate, Python 3.12.15: 43 architecture
tests and 3,247 discovery tests with 36 skipped, exit 0. This is aggregate
verification with the disjoint LTS collector correction, not invented separate
intermediate-commit gates.

Focused log SHA-256 `e4faa3b916aac6e6dfadfb301888f608590dd898d14d44920cfb062097ed164c`.
Full log SHA-256 `58c53d64aa56a24a61b6768ca6083ea75b56268d8974014b62bcca9b6af6f189`.
Exact code/test hashes above were verified on the PC WSL checkout before runs.
Read-only source admission/resource readiness on the actual host remains a
separate phase; no host mutation or Epic completion is claimed.
