# Fixture module used only inside disposable entrypoint transport tests.
# Application/OS effects are replaced; native source/resource argument building is real.
$ErrorActionPreference='Stop'
. $PSScriptRoot/ResourceAdapters.ps1
. $PSScriptRoot/Adapters.ps1
$script:expectedNativeRoot=[IO.Path]::GetFullPath((Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).ProviderPath)
$script:nativeGitCalls=0
$script:resourceHostCalls=0
$script:mockGitPath=$null

function Assert-NativeFixtureRoot($Root) {
    if($Root -isnot [string] -or $Root -cne $script:expectedNativeRoot -or $Root.Contains('::') -or $Root -cmatch '(?:\A|[\\/])\.{1,2}(?:[\\/]|\z)'){throw 'fixture_root_is_not_canonical_native_path'}
}
function Test-Path {
    param($LiteralPath,$Path,$PathType)
    $candidate=$LiteralPath
    if(!$candidate){$candidate=$Path}
    if($candidate -cmatch '[\\/]Git[\\/](?:cmd|bin)[\\/]git\.exe\z'){
        $script:mockGitPath=$candidate
        return $true
    }
    if($PathType){return Microsoft.PowerShell.Management\Test-Path -LiteralPath $candidate -PathType $PathType}
    return Microsoft.PowerShell.Management\Test-Path -LiteralPath $candidate
}
function Invoke-PreparationProcess {
    param($File,[string[]]$Arguments,$TimeoutSeconds,$InputText)
    if($TimeoutSeconds -ne 7){throw 'fixture_timeout_not_preserved'}
    if($script:mockGitPath -and $File -ceq $script:mockGitPath){
        $rootIndex=[Array]::IndexOf($Arguments,'-C')
        if($rootIndex -lt 0){throw 'fixture_native_git_root_is_missing'}
        Assert-NativeFixtureRoot $Arguments[$rootIndex+1]
        $script:nativeGitCalls++
        if($Arguments -contains 'config'){return @{exit_code=1;stdout='';stderr=''}}
        if($Arguments -contains 'status'){return @{exit_code=0;stdout='';stderr=''}}
        if($Arguments -contains 'rev-parse' -or $Arguments -contains 'hash-object'){return @{exit_code=0;stdout=(('a'*40)+"`n");stderr=''}}
        if($Arguments -contains 'ls-tree'){return @{exit_code=0;stdout=('100644 blob '+('a'*40)+"`tfixture`n");stderr=''}}
        throw 'fixture_unexpected_git_probe'
    }
    $fileIndex=[Array]::IndexOf($Arguments,'-File')
    if($fileIndex -lt 0 -or $Arguments[$fileIndex+1] -cne (Join-Path $script:expectedNativeRoot 'modules/tsw_windows_wsl/bootstrap/preparation/ResourceHost.ps1')){throw 'fixture_native_resource_file_is_not_provider_path'}
    $request=$InputText | ConvertFrom-Json -ErrorAction Stop
    if($request.mode -cne 'inventory' -or $request.options.RepositoryRoot -cne $script:expectedNativeRoot){throw 'fixture_native_resource_request_is_not_provider_path'}
    Assert-NativeFixtureRoot $request.options.RepositoryRoot
    $script:resourceHostCalls++
    return @{exit_code=0;stdout='{"fixture_verified":true}';stderr=''}
}
function New-PreparationPorts {return @{fixture_only=$true}}
function Invoke-WindowsPreparation {
    param($Options,$Ports)
    if($Options.Mode -cne 'Check' -or !$Options.Json -or $Options.ApproveApply -or $Options.QualificationRun -or !$Ports.fixture_only){throw 'fixture_requires_read_only_entrypoint'}
    # Fake Git identities exercise the native adapter boundary, not actual provenance.
    $source=Get-PreparationSource $Options
    if(!$source.verified -or !$source.clean -or $source.revision -cne ('a'*40) -or $script:nativeGitCalls -le 3){throw 'fixture_native_source_transport_failed'}
    $resource=Invoke-PreparationResourceHost $Options @{mode='inventory';options=$Options;facts=@{}} $Options.ProbeTimeoutSeconds
    if(!$resource.fixture_verified -or $script:resourceHostCalls -ne 1){throw 'fixture_native_resource_transport_failed'}
    Assert-NativeFixtureRoot $Options.RepositoryRoot
    return @{schema_version=1;read_only=$true;source_verified=$true;resource_transport_verified=$true
        unc_root=$script:expectedNativeRoot.StartsWith('\\');drive_root=($script:expectedNativeRoot -cmatch '\A[A-Za-z]:\\')
        native_git_calls=$script:nativeGitCalls;native_resource_calls=$script:resourceHostCalls
        result=@{outcome='READY';exit_code=0;changed=$false;preparation_ready=$false;services_verified=$false}}
}
# No host inventory, evidence or mutation port is exported or invoked by this fixture.
Export-ModuleMember -Function Invoke-WindowsPreparation,New-PreparationPorts
