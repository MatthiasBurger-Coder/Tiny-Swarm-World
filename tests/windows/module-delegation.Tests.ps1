param([Parameter(Mandatory=$true)][string]$RepositoryRoot)
$ErrorActionPreference='Stop'
function Assert($Condition,$Message) {if(!$Condition){throw $Message}}
# Parse every WSL-owned PowerShell asset, without executing it.
Get-ChildItem (Join-Path $RepositoryRoot 'bootstrap/windows') -Recurse -File | Where-Object {$_.Extension -in @('.ps1','.psm1')} | ForEach-Object {
    $tokens=$null;$errors=$null
    [void][Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$tokens,[ref]$errors)
    Assert ($errors.Count -eq 0) ('PowerShell parse: '+$_.FullName)
}
# Public entry point with a stub module: no probes, WSL or host changes.
$temp=Join-Path ([IO.Path]::GetTempPath()) ('tsw-module-'+[guid]::NewGuid().ToString('N'))
try {
    $target=Join-Path $temp 'bootstrap/windows'
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Copy-Item (Join-Path $RepositoryRoot 'bootstrap/windows/*') $target -Recurse
    @'
function New-PreparationPorts {return @{}}
function Invoke-WindowsPreparation($Options,$Ports) {
    if($Options.Distro -cne 'Ubuntu-24.04' -or $Options.LinuxCheckout -cne '/home/operator/checkout with spaces' -or $Options.ServiceProfile -cne 'default' -or $Options.Mode -cne 'Plan'){throw 'Forwarded options changed'}
    return @{result=@{outcome='FIXTURE';exit_code=[int]$env:TSW_MODULE_EXIT}}
}
Export-ModuleMember -Function New-PreparationPorts,Invoke-WindowsPreparation
'@ | Set-Content (Join-Path $target 'preparation/Preparation.psm1')
    $engine=(Get-Process -Id $PID).Path
    foreach($status in @(0,17)) {
        $env:TSW_MODULE_EXIT=[string]$status
        $output=& $engine -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $target 'prepare_windows.ps1') -DryRun -Json -Distro Ubuntu-24.04 -LinuxCheckout '/home/operator/checkout with spaces' -ServiceProfile default
        Assert ($LASTEXITCODE -eq $status) 'Public Windows exit propagation'
        Assert (($output | ConvertFrom-Json).result.exit_code -eq $status) 'Public Windows envelope'
    }
} finally {Remove-Item $temp -Recurse -Force;Remove-Item Env:TSW_MODULE_EXIT -ErrorAction SilentlyContinue}
. (Join-Path $RepositoryRoot 'bootstrap/windows/preparation/Handoff.ps1')
. (Join-Path $RepositoryRoot 'bootstrap/windows/preparation/Adapters.ps1')
$options=@{Distro='Ubuntu-24.04';LinuxCheckout='/home/operator/checkout with spaces';ServiceProfile='default';RepositoryRoot=$RepositoryRoot;ProbeTimeoutSeconds=15}
$facts=@{handoff_ready=$true;handoff_checkout=$options.LinuxCheckout;user='operator';running=$true;pid1='systemd';uid=1000}
$handoff=Get-PreparationHandoff $options $facts
Assert ($handoff.operator_command -match "--distribution 'Ubuntu-24.04' --user 'operator'") 'Selected distro/account'
Assert ($handoff.install_command -ceq "cd -- '/home/operator/checkout with spaces' && exec ./bootstrap/linux/install.sh --service-profile default") 'Core install target and quoting'
Assert ($handoff.operator_command -match 'prepare_linux.sh --service-profile default && exec ./bootstrap/linux/install.sh') 'Preparation before install'
function Get-PreparationExecutable($Name) {Assert ($Name -ceq 'wsl.exe') 'WSL only';return 'stub-wsl'}
$script:status=0
function Invoke-PreparationProcess($File,$Arguments,$TimeoutSeconds,$InputText='') {
    Assert ($File -ceq 'stub-wsl') 'Stub WSL target'
    if($Arguments[0] -eq '--list'){return @{exit_code=0;stdout="Ubuntu-24.04`n"}}
    Assert (($Arguments -join '|') -ceq ('--distribution|Ubuntu-24.04|--user|operator|--exec|/bin/sh|-s|--|/home/operator/checkout with spaces|'+('a'*40))) 'WSL argv preservation'
    Assert ($InputText -match 'bootstrap/linux/install.sh') 'Core source-proof target'
    return @{exit_code=$script:status;stdout="handoff_ready=true`nhandoff_checkout=/home/operator/checkout with spaces`n"}
}
foreach($status in @(0,17,124)) {
    $script:status=$status
    $result=Get-PreparationHandoffInventory $options $facts @{verified=$true;clean=$true;revision=('a'*40)}
    Assert ($result.handoff_ready -eq ($status -eq 0)) 'WSL failure cannot report ready'
}
# Source admission ignores absent native edition files; core edits still block.
function Test-Path {
    param([string]$LiteralPath,[string]$PathType)
    if($LiteralPath -match '[\\/]Git[\\/]cmd[\\/]git\.exe$'){return $true}
    if($PathType){return Microsoft.PowerShell.Management\Test-Path -LiteralPath $LiteralPath -PathType $PathType}
    return Microsoft.PowerShell.Management\Test-Path -LiteralPath $LiteralPath
}
$script:dirty=''
function Invoke-PreparationProcess($File,$Arguments,$TimeoutSeconds,$InputText='') {
    if($Arguments -contains 'status') {
        foreach($excluded in @(':(exclude)install.sh',':(exclude)tsw',':(exclude)src/tsw_native_linux')){
            Assert ($Arguments -contains $excluded) 'Native assets excluded from WSL admission'
        }
        return @{exit_code=0;stdout=$script:dirty}
    }
    if($Arguments -contains 'config'){return @{exit_code=1;stdout=''}}
    if($Arguments -contains 'ls-tree'){return @{exit_code=0;stdout=("100644 blob "+('b'*40)+"`tfixture")}}
    if($Arguments -contains 'hash-object' -or $Arguments[-1] -like 'HEAD:*'){return @{exit_code=0;stdout=('b'*40)}}
    return @{exit_code=0;stdout=('a'*40)}
}
foreach($dirty in @('', ' M bootstrap/linux/install.sh')) {
    $script:dirty=$dirty
    $result=Get-PreparationSource $options
    Assert $result.verified 'Asset hashes remain verified'
    Assert ($result.clean -eq ($dirty -eq '')) 'Core edits still block admission'
}
Remove-Item Function:Test-Path
Write-Output 'PASS module boundaries and stubbed public/WSL handoff'
