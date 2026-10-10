param([string]$RepositoryRoot, [string]$FixtureCatalog)
$ErrorActionPreference = 'Stop'
. (Join-Path $RepositoryRoot 'tools/windows/preparation/SourceProof.ps1')
$cases = Get-Content -LiteralPath $FixtureCatalog -Raw | ConvertFrom-Json
$count = 0
foreach ($case in $cases) {
    $source = Test-PreparationReleaseProof -RepositoryRoot $case.root -Assets $case.assets -ExpectedRevision $case.revision
    if ($source.verified -ne $case.expected -or $source.clean -ne $case.expected) {
        throw ('FAIL release proof case: ' + $case.name)
    }
    $count++
}
Write-Output "PASS $count offline commit/tree/blob source identity cases"
