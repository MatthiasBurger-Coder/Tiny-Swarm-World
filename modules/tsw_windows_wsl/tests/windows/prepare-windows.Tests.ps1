param([Parameter(Mandatory=$true)][string]$RepositoryRoot)
$ErrorActionPreference='Stop'
$testPowerShell=(Get-Process -Id $PID).Path
if([string]::IsNullOrWhiteSpace($testPowerShell) -or !(Test-Path -LiteralPath $testPowerShell -PathType Leaf)){throw 'test_runtime_unavailable'}
Import-Module (Join-Path $RepositoryRoot 'modules/tsw_windows_wsl/bootstrap/preparation/Preparation.psm1') -Force -DisableNameChecking
$count=0
function Assert($Condition,$Name) {if(!$Condition){throw "FAIL: $Name"};$script:count++}
function Options {
    return @{Mode='Plan';Distro='Ubuntu-24.04';ServiceProfile='service-access';ProbeTimeoutSeconds=15;ActionTimeoutSeconds=900;ApproveApply=$false;QualificationRun=$false;ApprovedPlan=$null;QualificationHost='test-host';QualificationDistro='Ubuntu-24.04';QualificationRevision=('a'*40);RecoveryReference='disposable VM snapshot';Json=$true}
}
function Facts {
    return @{handoff_ready=$true;handoff_checkout='/home/operator/Tiny-Swarm-World';bridge_facts=@{schema_version=1;distro='Ubuntu-24.04';observed_address='172.20.0.2';ownership='owned';bridge_ready=$true;routing_ready=$true;agent_ready=$true;action=$null;blockers=@();fingerprint='ready'};platform='Windows';host_identity='test-host';product_type=1;build=22631;architecture='AMD64';elevated=$true;virtualization=$true;features_known=$true;features_missing=@();reboot_pending=$false;wsl_present=$true;wsl_version='3.0.1';install_capable=$true;distro_present=$true;distro_inventory_known=$true;wsl_generation=2;running=$true;linux_known=$true;linux_id='ubuntu';release='24.04';linux_architecture='x86_64';uid=1000;user='operator';config_safe=$true;config_hash='absent';config_metadata='absent';systemd_packages=$true;systemd_configured=$true;pid1='systemd';resource_facts=@{projection_valid=$true;profile=@{memory_gib=16;processors=8;disk_gib=150};node_budget=@{memory_gib=19;processors=8;disk_gib=80};physical_memory_bytes=[long]34359738368;logical_processors=16;storage_known=$true;config_safe=$true;distro_volume='volume';swap_volume='volume';distro_free_bytes=[long]536870912000;swap_free_bytes=[long]536870912000;config_values=@{memory='21GB';processors='8';swap='6GB'};config_snapshot=@{hash='test';metadata='test'};effective_known=$true;effective_physical_memory_bytes=[long]22548578304;effective_memory_bytes=[long]22333829939;effective_processors=8;effective_swap_bytes=[long]6442450944;effective_disk_bytes=[long]322122547200}}
}
$script:facts=Facts
$script:source=@{verified=$true;clean=$true;revision=('a'*40)}
$script:records=New-Object Collections.ArrayList
$script:writes=0;$script:executions=0;$script:protected=0;$script:effect=@{confirmed=$true;uncertain=$false;exit_code=0};$script:failWrite=0;$script:inventoryCount=0;$script:drift=$false
$ports=@{
    EvidencePreflight={param($o) return $true}
    Inventory={param($o) $script:inventoryCount++;$copy=@{};foreach($k in $script:facts.Keys){$copy[$k]=$script:facts[$k]};if($script:drift -and $script:inventoryCount -gt 1){$copy.config_hash='drift'};return $copy}
    SourceIdentity={param($o) return $script:source}
    ProtectEvidence={param($o) $script:protected++;return 'protected-local-store'}
    WriteEvidence={param($p,$r) [void]$script:records.Add($r);$script:writes++;if($script:failWrite -eq $script:writes){throw 'evidence-failed'}}
    Execute={param($a,$o,$f,$p) $script:executions++;return $script:effect}
    Consent={param($p) return $true}
}
$o=Options;$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.outcome -eq 'READY' -and !$r.result.preparation_ready -and !$r.result.services_verified) 'capability distinct from aggregate'
Assert ($script:writes -eq 0 -and $script:protected -eq 0 -and $script:executions -eq 0) 'read-only no writes'
$o.Mode='Help';$r=Invoke-WindowsPreparation $o @{Inventory={throw 'help probed'}};Assert ($r.result.exit_code -eq 0) 'help no probes'
foreach($case in @(@('elevated',$false),@('linux_id','debian'),@('build',19045),@('architecture','ARM64'),@('virtualization',$false),@('features_known',$false),@('wsl_version','2.3.0'),@('wsl_generation',1),@('release','22.04'),@('uid',0),@('config_safe',$false),@('systemd_packages',$false))) {
    $script:facts=Facts;$script:facts[$case[0]]=$case[1];$o=Options;$r=Invoke-WindowsPreparation $o $ports;Assert ($r.result.outcome -eq 'BLOCKED') ('blocked '+$case[0])
}
$script:facts=Facts;$script:facts.running=$false;$r=Invoke-WindowsPreparation (Options) $ports;Assert ($r.blockers[0].code -eq 'distro_stopped' -and $script:executions -eq 0) 'stopped distro not started'
foreach($case in @(@('features_missing',@('VirtualMachinePlatform'),'enable_features'),@('wsl_present',$false,'install_wsl'),@('distro_present',$false,'install_distro'),@('systemd_configured',$false,'enable_systemd'))) {
    $script:facts=Facts;$script:facts[$case[0]]=$case[1];$o=Options;$r=Invoke-WindowsPreparation $o $ports;Assert ($r.actions.Count -eq 1 -and $r.actions[0].id -eq $case[2]) ('staged '+$case[2])
}
$script:facts=Facts;$script:facts.pid1='init';$r=Invoke-WindowsPreparation (Options) $ports;Assert ($r.result.exit_code -eq 3 -and $r.restart.scope -eq 'distro') 'operator restart and PID1'
$script:facts=Facts;$script:facts.systemd_configured=$false
$o=Options;$o.Mode='Apply';$o.ApproveApply=$true;$r=Invoke-WindowsPreparation $o $ports;Assert ($r.blockers[-1].code -eq 'unqualified_target') 'ordinary apply blocked'
$o.QualificationRun=$true;$o.ApprovedPlan='stale';$r=Invoke-WindowsPreparation $o $ports;Assert ($r.blockers[-1].code -eq 'exact_plan_consent_required') 'stale plan blocked'
$o.ApprovedPlan=$null;$o.QualificationHost='other';$r=Invoke-WindowsPreparation $o $ports;Assert ($r.blockers[-1].code -eq 'qualification_authorization_mismatch') 'host binding'
$o.QualificationHost='test-host';$script:source.clean=$false;$r=Invoke-WindowsPreparation $o $ports;Assert ($r.blockers[-1].code -eq 'unverified_source') 'dirty source blocked'
$script:source.clean=$true;$script:inventoryCount=0;$script:drift=$true;$r=Invoke-WindowsPreparation $o $ports;Assert ($r.blockers[-1].code -eq 'consent_drift' -and $script:executions -eq 0) 'prestage drift invalidates'
$script:drift=$false;$script:failWrite=1;$script:writes=0;$r=Invoke-WindowsPreparation $o $ports;Assert ($r.result.exit_code -eq 2 -and $script:executions -eq 0) 'premutation evidence failure'
$script:failWrite=2;$script:writes=0;$r=Invoke-WindowsPreparation $o $ports;Assert ($r.result.exit_code -eq 4 -and $r.result.changed) 'postmutation evidence partial'
$script:failWrite=0;$script:writes=0;$r=Invoke-WindowsPreparation $o $ports;Assert ($r.result.exit_code -eq 3 -and $r.result.completed_actions[0] -eq 'enable_systemd') 'systemd confirmation restart'
foreach($code in @(124,130,1)) {$script:effect=@{confirmed=$false;uncertain=$true;exit_code=$code};$r=Invoke-WindowsPreparation $o $ports;$expected=$code;if($code -eq 1){$expected=4};Assert ($r.result.outcome -eq 'PARTIAL' -and $r.result.exit_code -eq $expected) ('bounded effect '+$code)}
$script:effect=@{confirmed=$false;uncertain=$false;exit_code=1};$r=Invoke-WindowsPreparation $o $ports;Assert ($r.result.outcome -eq 'FAILED' -and $r.result.exit_code -eq 1) 'no effects failure'
$script:facts=Facts;$o=Options;$o.Mode='Help';$o.Invalid=$true;$r=Invoke-WindowsPreparation $o @{Inventory={throw 'invalid help probed'}};Assert ($r.result.exit_code -eq 2) 'help conflicts no probes'
$o=Options;$o.ProbeTimeoutSeconds=0;$r=Invoke-WindowsPreparation $o $ports;Assert ($r.blockers[0].code -eq 'invalid_arguments') 'positive timeout'
$o=Options;$o.ApproveApply=$true;$r=Invoke-WindowsPreparation $o $ports;Assert ($r.blockers[0].code -eq 'invalid_arguments') 'read-only consent conflict'
$artifacts=Get-PreparationArtifacts;Assert ($artifacts.wsl.sha256.Length -eq 64 -and $artifacts['Ubuntu-26.04'].version -eq '26.04.1') 'immutable artifact identity'
# Pure host/help predicates cover the actual Hyper-V and WSL help observations.
$module=Get-Module Preparation
function StoreWsl2Facts {
    $f=Facts
    $f.features_missing=@('Microsoft-Windows-Subsystem-Linux')
    $f.feature_states=@{'Microsoft-Windows-Subsystem-Linux'='Disabled';VirtualMachinePlatform='Enabled'}
    $f.wsl_store_package_known=$true
    $f.wsl_store_package=@{name='MicrosoftCorporationII.WindowsSubsystemForLinux';publisher_id='8wekyb3d8bbwe';version='3.0.1.0'}
    return $f
}
# Store WSL2 needs VMP, while the legacy component is optional only with exact facts.
$script:facts=StoreWsl2Facts
$beforeFacts=Get-PreparationDigest $script:facts
$beforeEffects=@($script:writes,$script:protected,$script:executions) -join ','
$r=Invoke-WindowsPreparation (Options) $ports
Assert ($r.result.outcome -eq 'READY' -and $r.actions.Count -eq 0) 'verified Store WSL2 needs no legacy component action'
Assert ((Get-PreparationDigest $script:facts) -ceq $beforeFacts -and $script:facts.features_missing.Count -eq 1) 'Store exception preserves observed facts'
Assert ((@($script:writes,$script:protected,$script:executions) -join ',') -ceq $beforeEffects) 'Store preflight has no effects'
foreach($case in @(@('wsl_store_package_known',$false),@('wsl_store_package_known','true'),@('wsl_store_package',$null),@('wsl_present',$false),@('wsl_present','true'),@('wsl_version','2.3.0'),@('wsl_version','3.0.2'),@('wsl_version','broken'),@('distro_inventory_known',$false),@('distro_inventory_known','true'),@('distro_present',$false),@('distro_present','true'),@('wsl_generation',1),@('wsl_generation','2'),@('wsl_generation',$true),@('wsl_generation',$null),@('features_known',$false),@('features_known','true'))) {
    $script:facts=StoreWsl2Facts;$script:facts[$case[0]]=$case[1]
    $eligible=& $module {param($f) Test-PreparationStoreWsl2 $f} $script:facts
    Assert (!$eligible) ('Store exception typed predicate '+$case[0])
    $r=Invoke-WindowsPreparation (Options) $ports
    Assert ($r.result.outcome -ne 'READY') ('Store unsupported facts stay blocked '+$case[0])
}
foreach($case in @(@('name','Other'),@('name',@('MicrosoftCorporationII.WindowsSubsystemForLinux')),@('publisher_id','unknown'),@('version','2.3.0.0'),@('version','3.0.2.0'),@('version','3.0.1'),@('version','03.0.1.0'),@('version','99999999999999999.0.0.0'),@('version',$null))) {
    $script:facts=StoreWsl2Facts;$script:facts.wsl_store_package[$case[0]]=$case[1]
    $r=Invoke-WindowsPreparation (Options) $ports
    Assert ($r.actions.Count -eq 1 -and $r.actions[0].id -ceq 'enable_features') ('Store malformed identity retains feature gate '+$case[0])
}
foreach($feature in @('VirtualMachinePlatform','Microsoft-Windows-Subsystem-Linux')) {
    foreach($state in @('Enable Pending','Disable Pending','unknown',$null)) {
        $script:facts=StoreWsl2Facts;$script:facts.feature_states[$feature]=$state
        $r=Invoke-WindowsPreparation (Options) $ports
        Assert ($r.actions.Count -eq 1 -and $r.actions[0].id -ceq 'enable_features') ('Store unknown feature state '+$feature)
    }
}
$script:facts=StoreWsl2Facts;$script:facts.feature_states.VirtualMachinePlatform='Disabled';$script:facts.features_missing+=@('VirtualMachinePlatform','OtherFeature')
$r=Invoke-WindowsPreparation (Options) $ports
Assert (($r.actions[0].before -join ',') -ceq 'Microsoft-Windows-Subsystem-Linux,VirtualMachinePlatform,OtherFeature') 'Store exception cannot hide VMP or unrelated missing feature'
$script:facts=StoreWsl2Facts;$script:facts.features_missing+=@('OtherFeature')
$r=Invoke-WindowsPreparation (Options) $ports
Assert (($r.actions[0].before -join ',') -ceq 'OtherFeature') 'Store exception removes only legacy component'
foreach($case in @(@('elevated',$false,'elevation_required'),@('reboot_pending',$true,'reboot_pending'),@('virtualization',$false,'virtualization_unavailable'))) {
    $script:facts=StoreWsl2Facts;$script:facts[$case[0]]=$case[1]
    $r=Invoke-WindowsPreparation (Options) $ports
    Assert (@($r.blockers | Where-Object{$_.code -ceq $case[2]}).Count -eq 1) ('Store exception preserves independent '+$case[0])
}
$script:facts=StoreWsl2Facts;$script:facts.resource_facts.physical_memory_bytes=[long]1073741824
$r=Invoke-WindowsPreparation (Options) $ports
Assert ($r.result.outcome -eq 'BLOCKED' -and $r.resources.state -cne 'LIFECYCLE_PREREQUISITES_REQUIRED') 'Store exception still evaluates and refuses insufficient resources'
$script:facts=StoreWsl2Facts;$r=Invoke-WindowsPreparation (Options) $ports;$storeFingerprint=$r.plan_fingerprint
$script:facts.wsl_store_package.version='3.0.1.1';$r=Invoke-WindowsPreparation (Options) $ports
Assert ($r.result.outcome -eq 'READY' -and $r.plan_fingerprint -cne $storeFingerprint) 'Store package revision drift changes consent fingerprint'
$script:facts.wsl_version='3.0.1.1';$r=Invoke-WindowsPreparation (Options) $ports
Assert ($r.result.outcome -eq 'READY') 'matching four-part WSL runtime supported'
$script:facts.wsl_version='3.0.1.2';$r=Invoke-WindowsPreparation (Options) $ports
Assert ($r.result.outcome -eq 'BLOCKED') 'different explicit runtime revision cannot bypass feature'
# Exercise the real adapter observation path, with both process calls mocked.
$originalStoreProcess=& $module {${function:Invoke-PreparationProcess}}
$originalStoreExecutable=& $module {${function:Get-PreparationExecutable}}
try {
    & $module {
        $script:storeAdapterCalls=New-Object Collections.ArrayList
        $script:storeProbe=@{exit_code=0;stdout='{"msi":false,"store":1,"packages":[{"name":"MicrosoftCorporationII.WindowsSubsystemForLinux","publisher_id":"8wekyb3d8bbwe","version":"3.0.1.0"}]}';stderr=''}
        $script:storeVersion=@{exit_code=0;stdout="WSL version: 3.0.1.0`n";stderr=''}
        function script:Get-PreparationExecutable {param($Name) if($Name -cne 'powershell.exe'){throw 'unexpected_store_binary'};return 'mock-powershell'}
        function script:Invoke-PreparationProcess {
            param($File,$Arguments,$TimeoutSeconds,$InputText)
            [void]$script:storeAdapterCalls.Add(@{file=$File;arguments=$Arguments;timeout=$TimeoutSeconds})
            if($File -ceq 'mock-wsl' -and $Arguments.Count -eq 1 -and $Arguments[0] -ceq '--version'){return $script:storeVersion}
            if($File -ceq 'mock-powershell' -and $Arguments[-1] -cmatch 'Get-AppxPackage -Name MicrosoftCorporationII.WindowsSubsystemForLinux'){return $script:storeProbe}
            throw 'unexpected_store_probe'
        }
    }
    $observed=& $module {Get-PreparationWslRuntimeInventory 'mock-wsl' {7}}
    Assert ($observed.wsl_present -and $observed.wsl_version -ceq '3.0.1.0' -and $observed.wsl_store_package_known -and $observed.wsl_store_package.version -ceq '3.0.1.0') 'actual runtime adapter preserves full Store and runtime versions'
    $calls=& $module {@($script:storeAdapterCalls.ToArray())}
    Assert ($calls.Count -eq 2 -and $calls[0].timeout -eq 7 -and $calls[1].timeout -eq 7) 'Store runtime observations use two bounded probes'
    $script:facts=StoreWsl2Facts;foreach($key in $observed.Keys){$script:facts[$key]=$observed[$key]};$r=Invoke-WindowsPreparation (Options) $ports
    Assert ($r.result.outcome -eq 'READY') 'actual adapter Store facts reach optional-feature policy'
    foreach($case in @(@('3.0.1','READY'),@('3.0.1.1','BLOCKED'),@('3.0.1.0','READY'))) {
        $module.SessionState.PSVariable.Set('storeVersion',@{exit_code=0;stdout=('WSL version: '+$case[0]+"`n");stderr=''})
        $observed=& $module {Get-PreparationWslRuntimeInventory 'mock-wsl' {7}}
        $script:facts=StoreWsl2Facts;foreach($key in $observed.Keys){$script:facts[$key]=$observed[$key]};$r=Invoke-WindowsPreparation (Options) $ports
        Assert ($observed.wsl_version -ceq $case[0] -and $r.result.outcome -ceq $case[1]) 'real adapter preserves runtime revision mismatch for policy'
    }
    foreach($probe in @(@{exit_code=$false;stdout="WSL version: 3.0.1.0`n";stderr=''},@{exit_code='0';stdout="WSL version: 3.0.1.0`n";stderr=''},@{exit_code=0;stdout=$null;stderr=''},@{exit_code=0;stdout=42;stderr=''},@{exit_code=0;stdout=('x'*65537);stderr=''},@{exit_code=0;stdout="WSL version: 3.0.1.0`n";stderr='warning'},@{exit_code=0;stdout="WSL version: 3.0.1.0`n";stderr=$null},@{exit_code=0;stdout="WSL version: 3.0.1.0`n";stderr=0},@{exit_code=0;stdout="WSL version: 03.0.1.0`n";stderr=''},@{exit_code=0;stdout="unknown first line`nKernel version: 3.0.1.0`n";stderr=''})) {
        $module.SessionState.PSVariable.Set('storeVersion',$probe)
        $observed=& $module {Get-PreparationWslRuntimeInventory 'mock-wsl' {7}}
        $script:facts=StoreWsl2Facts;foreach($key in $observed.Keys){$script:facts[$key]=$observed[$key]};$r=Invoke-WindowsPreparation (Options) $ports
        Assert ($observed.wsl_present -and $null -eq $observed.wsl_version -and $r.result.outcome -ceq 'BLOCKED') 'malformed runtime result stays present unknown and cannot bypass feature'
    }
    $module.SessionState.PSVariable.Set('storeVersion',@{exit_code=0;stdout="WSL version: 3.0.1.0`n";stderr=''})
    foreach($raw in @('{"msi":false,"store":0,"packages":[]}', '{"msi":true,"store":0,"packages":[]}', '{"msi":false,"store":2,"packages":[]}', '{"msi":false,"store":"1","packages":[]}', '{"msi":false,"store":1,"packages":[{"name":"Other","publisher_id":"8wekyb3d8bbwe","version":"3.0.1.0"}]}', '{"msi":false,"store":1,"packages":[{"name":"MicrosoftCorporationII.WindowsSubsystemForLinux","publisher_id":"other","version":"3.0.1.0"}]}', '{"msi":false,"store":1,"packages":[{"name":"MicrosoftCorporationII.WindowsSubsystemForLinux","publisher_id":"8wekyb3d8bbwe","version":"bad"}]}', '{"msi":false,"store":0,"store":1,"packages":[]}', '{"msi":false,"store":0,"packages":[],"unknown":"secret"}', 'not-json')) {
        $module.SessionState.PSVariable.Set('storeProbe',@{exit_code=0;stdout=$raw;stderr=''})
        $observed=& $module {Get-PreparationWslRuntimeInventory 'mock-wsl' {7}}
        $script:facts=StoreWsl2Facts;foreach($key in $observed.Keys){$script:facts[$key]=$observed[$key]};$r=Invoke-WindowsPreparation (Options) $ports
        Assert ($r.result.outcome -eq 'BLOCKED' -and $null -eq $observed.wsl_store_package) 'unknown inbox MSI or malformed actual package probe cannot bypass feature'
    }
    foreach($probe in @(@{exit_code=124;stdout='';stderr='timeout'},@{exit_code=1;stdout='';stderr='failed'},@{exit_code=0;stdout=('x'*65537);stderr=''},@{exit_code=0;stdout='{}';stderr='error'})) {
        $module.SessionState.PSVariable.Set('storeProbe',$probe)
        $observed=& $module {Get-PreparationWslRuntimeInventory 'mock-wsl' {7}}
        Assert (!$observed.wsl_store_package_known -and $null -eq $observed.wsl_store_package) 'failed bounded package probe remains unknown'
    }
    $module.SessionState.PSVariable.Set('storeVersion',@{exit_code=1;stdout='';stderr='unsupported'})
    foreach($msi in @($false,$true)) {
        $raw=@{msi=$msi;store=0;packages=@()} | ConvertTo-Json -Compress
        $module.SessionState.PSVariable.Set('storeProbe',@{exit_code=0;stdout=$raw;stderr=''})
        $observed=& $module {Get-PreparationWslRuntimeInventory 'mock-wsl' {7}}
        Assert ($observed.wsl_present -eq $msi -and $null -eq $observed.wsl_version) 'existing absent-runtime versus MSI fallback remains'
    }
} finally {
    & $module {param($process,$executable) Set-Item Function:script:Invoke-PreparationProcess $process;Set-Item Function:script:Get-PreparationExecutable $executable} $originalStoreProcess $originalStoreExecutable
}
$script:facts=Facts
foreach($case in @(@($true,@($false),$true),@($false,@($true),$true),@($false,@($false),$false),@($null,@($true),$null),@($true,@($null),$null),@('true',@($false),$null))) {
    $v=& $module {param($h,$f) Get-PreparationVirtualization @{hypervisor_present=$h;firmware_values=$f}} $case[0] $case[1]
    Assert ($v.available -eq $case[2]) 'typed hypervisor/firmware observation'
}
$helpText="WSL-Hilfe`n --install Optionen`n --from-file Datei`n --name Name`n --no-launch`n"
foreach($case in @(@(0,$helpText,'',$true),@(-1,($helpText.ToCharArray() -join "`0"),'',$true),@(1,$helpText,'',$false),@(124,$helpText,'',$false),@(130,$helpText,'',$false),@(-1,$helpText,'error',$false),@(-1,$helpText,"`n",$false),@(-1,($helpText.Replace('--name','--name-extra')),'',$false),@(-1,($helpText.Replace('--no-launch','')),'',$false),@(-1,$null,'',$false))) {
    $detected=& $module {param($code,$output,$errorText) Test-PreparationInstallCapabilities @{exit_code=$code;stdout=$output;stderr=$errorText}} $case[0] $case[1] $case[2]
    Assert ($detected -eq $case[3]) 'bounded exact WSL help capability semantics'
}
foreach($name in @("Ubuntu`n","Ubuntu`r`n",'Ubuntu;whoami','../Ubuntu','',('a'*65))) {
    $o=Options;$o.Distro=$name;$o.UbuntuRelease='26.04'
    $r=Invoke-WindowsPreparation $o @{Inventory={throw 'unsafe selection probed'}}
    Assert ($r.blockers[0].code -eq 'invalid_arguments') 'unsafe registration refused before probes'
}
$script:facts=Facts;$script:facts.release='26.04';$script:facts.install_capable=$false
$o=Options;$o.Distro='Ubuntu';$o.UbuntuRelease='26.04';$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.outcome -eq 'READY' -and $r.selection.ubuntu_release -eq '26.04') 'existing explicit custom selection needs no install capability'
$priorFingerprint=$r.plan_fingerprint
$o.UbuntuRelease='24.04';$r=Invoke-WindowsPreparation $o $ports
Assert ($r.blockers[0].code -eq 'linux_unsupported' -and $r.plan_fingerprint -ne $priorFingerprint) 'release observation and consent binding'
$o=Options;$o.Distro='Ubuntu';$o.UbuntuRelease='26.04';$script:facts.distro_present=$false;$script:facts.features_missing=@('VirtualMachinePlatform')
$r=Invoke-WindowsPreparation $o $ports
Assert ($r.blockers[0].code -eq 'custom_registration_missing' -and $r.actions.Count -eq 0) 'absent custom selection never installs prerequisites or guesses artifacts'
$script:facts=Facts;$script:facts.distro_present=$false;$script:facts.install_capable=$false
$r=Invoke-WindowsPreparation (Options) $ports
Assert ($r.blockers[0].code -eq 'wsl_capabilities_unknown' -and $r.actions.Count -eq 0) 'canonical install still needs capabilities'
$o=Options;$o.UbuntuRelease='26.04';$r=Invoke-WindowsPreparation $o @{Inventory={throw 'contradiction probed'}}
Assert ($r.blockers[0].code -eq 'invalid_arguments') 'canonical release contradiction refused'
$script:facts=Facts
# Actual transport tests run harmless child PowerShell only, never concrete host ports.
$p=Invoke-PreparationProcess $testPowerShell @('-NoProfile','-NonInteractive','-Command','[Console]::Write("ok"); exit 7') 10
Assert ($p.exit_code -eq 7 -and $p.stdout -eq 'ok') 'native output captured'
$p=Invoke-PreparationProcess $testPowerShell @('-NoProfile','-NonInteractive','-Command','[Console]::Write([Environment]::CommandLine)') 10
Assert ($p.exit_code -eq 0 -and $p.stdout -match '\s-NoProfile -NonInteractive -Command ') 'native flags remain unquoted for WSL option parsing'
$p=Invoke-PreparationProcess $testPowerShell @('-NoProfile','-NonInteractive','-Command','Start-Sleep -Seconds 10') 1
Assert ($p.exit_code -eq 124) 'native finite timeout'
if([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT){
# Exact DISM basename alone selects actual OEM decoding; no Windows features are queried.
$dismFixture=Join-Path ([IO.Path]::GetTempPath()) ('tsw-dism-oem-'+[Guid]::NewGuid().ToString('N'))
$originalOutputEncoding=[Console]::OutputEncoding
$originalCurrentDirectory=[Environment]::CurrentDirectory
[void][IO.Directory]::CreateDirectory($dismFixture)
try{
    $oem=& (Get-Module Preparation) {Get-PreparationDismEncoding}
    $sample=$null
    foreach($value in 128..255){
        try{$decoded=$oem.GetString([byte[]]@($value));if($decoded.Length -eq 1 -and [int][char]$decoded -ge 32){$sample=$decoded;break}}catch{}
    }
    if($null -eq $sample){$sample=[string][char]252}
    $text='OEM='+$sample+"`nState : Enabled`n"
    [byte[]]$bytes=$oem.GetBytes($text)
    $dism=Join-Path $dismFixture 'Dism.exe';$other=Join-Path $dismFixture 'Other.exe'
    # Keep executable trust intact under Application Control: only the basename
    # changes; cmd's built-in type copies our exact bytes to both native pipes.
    $trustedCmd=Join-Path ([Environment]::SystemDirectory) 'cmd.exe'
    $signature=Get-AuthenticodeSignature -LiteralPath $trustedCmd
    Assert ($signature.Status -eq 'Valid' -and $signature.SignerCertificate.Subject -match 'O=Microsoft Corporation(?:,|$)') 'oem_fixture_trusted_microsoft_cmd'
    [IO.File]::Copy($trustedCmd,$dism)
    [IO.File]::Copy($trustedCmd,$other)
    Assert ((Get-FileHash -LiteralPath $dism -Algorithm SHA256).Hash -ceq (Get-FileHash -LiteralPath $trustedCmd -Algorithm SHA256).Hash -and
        (Get-FileHash -LiteralPath $other -Algorithm SHA256).Hash -ceq (Get-FileHash -LiteralPath $trustedCmd -Algorithm SHA256).Hash) 'oem_fixture_copies_preserve_signed_bytes'
    [IO.File]::WriteAllBytes((Join-Path $dismFixture 'oem.bin'),$bytes)
    [Environment]::CurrentDirectory=$dismFixture
    $emitBytes=@('/d','/a','/c','type oem.bin & type oem.bin 1>&2')
    [Console]::OutputEncoding=[Text.UTF8Encoding]::new($false,$true)
    $captured=Invoke-PreparationProcess $dism $emitBytes 10
    Assert ($captured.exit_code -eq 0 -and $captured.stdout -ceq $text -and $captured.stderr -ceq $text -and
        $captured.stdout -match 'State : Enabled') 'dism_real_process_oem_stdout_stderr_under_strict_utf8'
    $notUtf8=$false
    try{$null=([Text.UTF8Encoding]::new($false,$true)).GetString($bytes)}catch [Text.DecoderFallbackException]{$notUtf8=$true}
    if($notUtf8){
        $refused=$false
        try{$null=Invoke-PreparationProcess $other $emitBytes 10}catch{$refused=$_.Exception.ToString().Contains('DecoderFallbackException')}
        Assert $refused 'non_dism_identical_oem_bytes_still_strict_utf8_refused'
    }else{
        $unchanged=Invoke-PreparationProcess $other $emitBytes 10
        Assert ($unchanged.stdout -ceq $text) 'utf8_oem_host_keeps_other_reader_behavior'
    }
}finally{
    [Console]::OutputEncoding=$originalOutputEncoding
    [Environment]::CurrentDirectory=$originalCurrentDirectory
    Remove-Item -LiteralPath $dismFixture -Recurse -Force
}
}
$unsafePorts=@{};foreach($k in $ports.Keys){$unsafePorts[$k]=$ports[$k]};$unsafePorts.EvidencePreflight={return $false}
$script:facts=Facts;$r=Invoke-WindowsPreparation (Options) $unsafePorts
Assert ($r.blockers[0].code -eq 'unsafe_evidence_storage' -and !$r.result.changed) 'read-only evidence preflight refusal'
# More authorization bindings must refuse mutation, including EOF/noninteractive.
$script:facts=Facts;$script:facts.systemd_configured=$false;$script:effect=@{confirmed=$true;uncertain=$false;exit_code=0}
foreach($entry in @(@('QualificationDistro','Ubuntu-26.04'),@('QualificationRevision',('b'*40)),@('RecoveryReference',''))) {
    $o=Options;$o.Mode='Apply';$o.ApproveApply=$true;$o.QualificationRun=$true;$o[$entry[0]]=$entry[1]
    $r=Invoke-WindowsPreparation $o $ports
    Assert ($r.blockers[-1].code -eq 'qualification_authorization_mismatch') ('qualification '+$entry[0])
}
$o=Options;$o.Mode='Apply';$o.QualificationRun=$true;$o.Json=$true
$refuse=@{};foreach($k in $ports.Keys){$refuse[$k]=$ports[$k]};$refuse.Consent={throw 'JSON prompted'}
$r=Invoke-WindowsPreparation $o $refuse;Assert ($r.blockers[-1].code -eq 'exact_plan_consent_required') 'JSON no prompt'
$o.Json=$false;$refuse.Consent={return $false};$r=Invoke-WindowsPreparation $o $refuse
Assert ($r.blockers[-1].code -eq 'exact_plan_consent_required') 'EOF declined'
$script:facts=Facts;$o=Options;$r=Invoke-WindowsPreparation $o $ports
Assert ($r.actions.Count -eq 0 -and !$r.result.changed) 'observed rerun no-op'
$script:records.Clear();$script:facts=Facts;$script:facts.systemd_configured=$false
$script:facts.user='synthetic-user';$script:facts.host_identity='synthetic-host';$script:facts.raw_output='synthetic-secret'
$o=Options;$o.Mode='Apply';$o.ApproveApply=$true;$o.QualificationRun=$true;$o.QualificationHost='synthetic-host'
$script:effect=@{confirmed=$true;uncertain=$false;exit_code=0;observations=@{pid1='init'}}
$r=Invoke-WindowsPreparation $o $ports
$encoded=$script:records | ConvertTo-Json -Depth 20 -Compress
Assert ($encoded -notmatch 'synthetic-user|synthetic-host|synthetic-secret|raw_output') 'evidence redacts identities and raw output'
Assert ($script:records[0].before -and $script:records[1].after -and $script:records[1].restart.scope -eq 'distro') 'evidence includes before after restart'
foreach($stage in @('install_wsl','install_distro')) {
    $script:facts=Facts
    if($stage -eq 'install_wsl'){$script:facts.wsl_present=$false}else{$script:facts.distro_present=$false}
    $o=Options;$o.Mode='Apply';$o.ApproveApply=$true;$o.QualificationRun=$true
    $r=Invoke-WindowsPreparation $o $ports
    Assert ($r.result.outcome -eq 'PARTIAL' -and $r.result.exit_code -eq 4 -and $r.result.changed -and $r.result.uncertain_actions.Count -eq 0) ('confirmed fresh-stage checkpoint '+$stage)
}
# Evolving clean-host scenario: every stage requires freshly observed facts and consent.
$script:scenarioFacts=Facts
$script:scenarioFacts.features_missing=@('Microsoft-Windows-Subsystem-Linux','VirtualMachinePlatform')
$script:scenarioFacts.wsl_present=$false;$script:scenarioFacts.wsl_version=$null;$script:scenarioFacts.install_capable=$false
$script:scenarioFacts.distro_present=$false;$script:scenarioFacts.distro_inventory_known=$false
$script:scenarioFacts.running=$false;$script:scenarioFacts.linux_known=$false;$script:scenarioFacts.uid=0;$script:scenarioFacts.user='root'
$script:scenarioFacts.systemd_configured=$false;$script:scenarioFacts.pid1='init'
$script:scenarioCalls=New-Object Collections.ArrayList
$scenarioPorts=@{
    Inventory={param($o) $copy=@{};foreach($key in $script:scenarioFacts.Keys){$copy[$key]=$script:scenarioFacts[$key]};return $copy}
    EvidencePreflight={return $true}
    SourceIdentity={return @{verified=$true;clean=$true;revision=('a'*40)}}
    ProtectEvidence={return 'mock-protected-scenario-store'}
    WriteEvidence={param($p,$r)}
    Consent={throw 'scenario must use freshly renewed explicit consent'}
    Execute={
        param($action,$o,$before,$store)
        [void]$script:scenarioCalls.Add($action.id)
        switch($action.id) {
            'enable_features' {
                $script:scenarioFacts.features_missing=@();$script:scenarioFacts.reboot_pending=$true
                return @{confirmed=$true;uncertain=$false;exit_code=3010}
            }
            'install_wsl' {
                $script:scenarioFacts.wsl_present=$true;$script:scenarioFacts.wsl_version='3.0.1'
                $script:scenarioFacts.install_capable=$true;$script:scenarioFacts.distro_inventory_known=$true
                return @{confirmed=$true;uncertain=$false;exit_code=0}
            }
            'install_distro' {
                $script:scenarioFacts.distro_present=$true;$script:scenarioFacts.wsl_generation=2
                # Registration is deliberately stopped: the operator owns OOBE/account setup.
                return @{confirmed=$true;uncertain=$false;exit_code=0}
            }
            'enable_systemd' {
                $script:scenarioFacts.systemd_configured=$true
                $script:scenarioFacts.config_hash='configured-fingerprint';$script:scenarioFacts.config_metadata='0:0:644'
                return @{confirmed=$true;uncertain=$false;exit_code=0}
            }
            default {throw 'unexpected scenario mutation'}
        }
    }
}
function ScenarioPlan {
    $o=Options
    return Invoke-WindowsPreparation $o $scenarioPorts
}
function ScenarioApply($Fingerprint) {
    $o=Options;$o.Mode='Apply';$o.ApproveApply=$true;$o.QualificationRun=$true;$o.ApprovedPlan=$Fingerprint
    return Invoke-WindowsPreparation $o $scenarioPorts
}
$p=ScenarioPlan
Assert ($p.actions.Count -eq 1 -and $p.actions[0].id -eq 'enable_features') 'clean scenario first plan only features'
$oldApproval=$p.plan_fingerprint
$r=ScenarioApply $oldApproval
Assert ($r.result.exit_code -eq 3 -and $r.restart.scope -eq 'Windows' -and $script:scenarioCalls.Count -eq 1) 'clean scenario features stop at reboot'
$p=ScenarioPlan;$r=ScenarioApply $p.plan_fingerprint
Assert ($r.result.exit_code -eq 3 -and $script:scenarioCalls.Count -eq 1) 'clean scenario no dependent work before observed reboot'
# Simulated operator reboot supplies fresh facts, never an automatic host restart.
$script:scenarioFacts.reboot_pending=$false
$r=ScenarioApply $oldApproval
Assert ($r.blockers[-1].code -eq 'exact_plan_consent_required' -and $script:scenarioCalls.Count -eq 1) 'clean scenario old consent cannot authorize next stage'
$p=ScenarioPlan
Assert ($p.actions[0].id -eq 'install_wsl') 'clean scenario fresh WSL install plan'
$r=ScenarioApply $p.plan_fingerprint
Assert ($r.result.exit_code -eq 4 -and $r.result.completed_actions[0] -eq 'install_wsl' -and $script:scenarioCalls.Count -eq 2) 'clean scenario WSL checkpoint needs fresh observation'
$p=ScenarioPlan
Assert ($p.actions.Count -eq 1 -and $p.actions[0].id -eq 'install_distro') 'clean scenario explicit distro next stage'
$r=ScenarioApply $p.plan_fingerprint
Assert ($r.result.exit_code -eq 4 -and $script:scenarioCalls.Count -eq 3) 'clean scenario distro installed without launch'
$p=ScenarioPlan
Assert ($p.blockers[0].code -eq 'distro_stopped' -and $p.actions.Count -eq 0) 'clean scenario stopped distro OOBE guidance'
$r=ScenarioApply $p.plan_fingerprint
Assert ($r.result.exit_code -eq 2 -and $script:scenarioCalls.Count -eq 3) 'clean scenario stopped distro never started by adapter'
# Operator starts the selected distro. Its root account is still insufficient.
$script:scenarioFacts.running=$true;$script:scenarioFacts.linux_known=$true
$p=ScenarioPlan;$r=ScenarioApply $p.plan_fingerprint
Assert ($p.blockers[0].code -eq 'ordinary_account_required' -and $script:scenarioCalls.Count -eq 3) 'clean scenario account is operator boundary'
# Operator creates/selects the ordinary account, then logs in.
$script:scenarioFacts.uid=1000;$script:scenarioFacts.user='operator'
$p=ScenarioPlan
Assert ($p.actions.Count -eq 1 -and $p.actions[0].id -eq 'enable_systemd') 'clean scenario account facts permit systemd plan'
$r=ScenarioApply $p.plan_fingerprint
Assert ($r.result.exit_code -eq 3 -and $r.restart.scope -eq 'distro' -and $script:scenarioCalls.Count -eq 4) 'clean scenario systemd awaits selected distro restart'
$p=ScenarioPlan;$r=ScenarioApply $p.plan_fingerprint
Assert ($r.result.exit_code -eq 3 -and $script:scenarioCalls.Count -eq 4) 'clean scenario no READY from configuration alone'
# Simulated operator selected-distro restart makes PID1 observable.
$script:scenarioFacts.pid1='systemd'
$p=ScenarioPlan
Assert ($p.result.outcome -eq 'READY' -and $p.result.capability_ready -and !$p.result.preparation_ready -and !$p.result.services_verified -and $p.actions.Count -eq 0) 'clean scenario observed baseline READY only'
Assert (($script:scenarioCalls -join ',') -eq 'enable_features,install_wsl,install_distro,enable_systemd') 'clean scenario exact ordered non-destructive actions'
# Existing selected WSL2 distro: preserve host/distro ownership and reconcile only config.
$script:scenarioFacts=Facts;$script:scenarioFacts.systemd_configured=$false;$script:scenarioFacts.pid1='init'
$script:scenarioCalls.Clear()
$p=ScenarioPlan;$r=ScenarioApply $p.plan_fingerprint
Assert ($r.result.exit_code -eq 3 -and $script:scenarioCalls.Count -eq 1 -and $script:scenarioCalls[0] -eq 'enable_systemd') 'existing scenario only selected config mutation'
$p=ScenarioPlan
Assert ($p.result.exit_code -eq 3 -and !$p.result.capability_ready -and $p.actions.Count -eq 0) 'existing scenario restart required until observed PID1'
$script:scenarioFacts.pid1='systemd'
$p=ScenarioPlan
Assert ($p.result.outcome -eq 'READY' -and $p.actions.Count -eq 0 -and $script:scenarioCalls.Count -eq 1) 'existing scenario observed READY and no replay'
# Actual Git fixture proves configured filters cannot spawn subprocesses during source inspection.
$programFiles=[Environment]::GetFolderPath('ProgramFiles')
$gitPath=if($programFiles){Join-Path $programFiles 'Git/cmd/git.exe'}else{$null}
if($gitPath -and (Test-Path -LiteralPath $gitPath)) {
    $gitFixture=Join-Path ([IO.Path]::GetTempPath()) ('tsw-git-'+[guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory($gitFixture)
    try {
        [void][IO.Directory]::CreateDirectory((Join-Path $gitFixture 'modules/tsw_windows_wsl/bootstrap/preparation'))
        Copy-Item -LiteralPath (Join-Path $RepositoryRoot 'modules/tsw_windows_wsl/bootstrap/prepare_windows.ps1') -Destination (Join-Path $gitFixture 'modules/tsw_windows_wsl/bootstrap')
        foreach($asset in @('Preparation.psm1','Policy.ps1','Application.ps1','Adapters.ps1','SourceProof.ps1','Download.ps1','linux-config.sh')){Copy-Item -LiteralPath (Join-Path $RepositoryRoot ('modules/tsw_windows_wsl/bootstrap/preparation/'+$asset)) -Destination (Join-Path $gitFixture 'modules/tsw_windows_wsl/bootstrap/preparation')}
        [IO.File]::WriteAllText((Join-Path $gitFixture '.gitattributes'),'*.ps1 filter=evil')
        foreach($arguments in @(@('init'),@('config','user.name','LifecycleTest'),@('config','user.email','test@example.invalid'),@('config','core.autocrlf','false'),@('add','.'),@('commit','-m','mock fixture'))) {
            $child=Invoke-PreparationProcess $gitPath (@('-C',$gitFixture)+$arguments) 10
            if($child.exit_code -ne 0){throw 'git_fixture_setup_failed'}
        }
        $child=Invoke-PreparationProcess $gitPath @('-C',$gitFixture,'config','filter.evil.clean','cmd.exe /c echo marker > filter-ran.txt') 10
        [IO.File]::AppendAllText((Join-Path $gitFixture 'modules/tsw_windows_wsl/bootstrap/prepare_windows.ps1'),"`n# drift")
        $o=Options;$o.RepositoryRoot=$gitFixture
        $module=Get-Module Preparation
        $sourceResult=& $module {param($o) Get-PreparationSource $o} $o
        Assert (!$sourceResult.clean -and !(Test-Path -LiteralPath (Join-Path $gitFixture 'filter-ran.txt'))) 'configured clean filter never spawned'
    } finally {Remove-Item -LiteralPath $gitFixture -Recurse -Force}
}
# Actual bounded verification helper hashes local fixture without network.
$verificationFixture=Join-Path ([IO.Path]::GetTempPath()) ('tsw-artifact-'+[guid]::NewGuid().ToString('N'))
[IO.File]::WriteAllText($verificationFixture,'untrusted-artifact')
try {
    $p=Invoke-PreparationProcess $testPowerShell @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',(Join-Path $RepositoryRoot 'modules/tsw_windows_wsl/bootstrap/preparation/Download.ps1'),'-VerifyOnly','-Url','https://github.com/microsoft/WSL/releases/download/3.0.1/wsl.3.0.1.0.x64.msi','-Destination',$verificationFixture) 10
    $verification=$p.stdout | ConvertFrom-Json
    Assert ($p.exit_code -eq 1 -and $verification.cause -eq 'artifact_hash_mismatch') 'bounded artifact helper real hash refusal'
    $p=Invoke-PreparationProcess $testPowerShell @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',(Join-Path $RepositoryRoot 'modules/tsw_windows_wsl/bootstrap/preparation/Download.ps1'),'-VerifyOnly','-Url','https://github.com/microsoft/WSL/releases/download/3.0.1/wsl.3.0.1.0.x64.msi','-Destination',$verificationFixture,'-ExpectedSha256',('0'*64)) 10
    $verification=$p.stdout | ConvertFrom-Json
    Assert ($p.exit_code -eq 1 -and $verification.cause -eq 'artifact_catalogue_mismatch') 'stale artifact declaration refused'

    $signatureHarness=$verificationFixture+'.ps1'
    $body=@'
param([string]$Helper,[string]$Destination)
function Get-FileHash {param($LiteralPath,$Algorithm) return @{Hash='28b1a0d013640a2ac95898ea705fa186e5b4ff767a1c1b49257161bc106599c6'}}
function Get-AuthenticodeSignature {param($LiteralPath) return @{Status='Invalid';SignerCertificate=@{Subject='O=Foreign publisher'}}}
& $Helper -VerifyOnly -Url 'https://github.com/microsoft/WSL/releases/download/3.0.1/wsl.3.0.1.0.x64.msi' -Destination $Destination
exit $LASTEXITCODE
'@
    [IO.File]::WriteAllText($signatureHarness,$body)
    try {
        $p=Invoke-PreparationProcess $testPowerShell @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$signatureHarness,'-Helper',(Join-Path $RepositoryRoot 'modules/tsw_windows_wsl/bootstrap/preparation/Download.ps1'),'-Destination',$verificationFixture) 10
        $verification=$p.stdout | ConvertFrom-Json
        Assert ($p.exit_code -eq 1 -and $verification.cause -eq 'artifact_signature_invalid') 'bounded artifact helper signature refusal'
    } finally {Remove-Item -LiteralPath $signatureHarness -Force}

} finally {Remove-Item -LiteralPath $verificationFixture -Force}
# Exercise concrete installation adapter using mocked native transport, hash/signature ports.
$module=Get-Module Preparation
$script:adapterCalls=New-Object Collections.ArrayList
$module.SessionState.PSVariable.Set('adapterCalls',$script:adapterCalls)
$module.SessionState.PSVariable.Set('verificationCause','artifact_hash_mismatch')
$originalExecutableResolver=& $module {(Get-Command Get-PreparationExecutable).ScriptBlock}
$module.SessionState.PSVariable.Set('testPowerShell',$testPowerShell)
& $module {
    function script:Get-PreparationExecutable {param($Name) return $script:testPowerShell}
    function script:Invoke-PreparationProcess {
        param($File,$Arguments,$TimeoutSeconds,$InputText)
        [void]$script:adapterCalls.Add(@{file=$File;arguments=$Arguments})
        if($Arguments -contains '-Destination'){$i=[Array]::IndexOf($Arguments,'-Destination');[IO.File]::WriteAllText($Arguments[$i+1],'untrusted-content')}
        return @{exit_code=1;stdout=(@{verified=$false;cause=$script:verificationCause} | ConvertTo-Json -Compress);stderr=''}
    }
}
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('tsw-mock-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($fixture)
try {
    $o=Options;$o.RepositoryRoot=$RepositoryRoot
    $r=& $module {param($o,$f,$s) Invoke-PreparationAction @{id='install_wsl'} $o $f $s} $o (Facts) $fixture
    Assert ($r.exit_code -eq 1 -and !$r.uncertain -and $script:adapterCalls.Count -eq 1) 'artifact mismatch no installer'
    $module.SessionState.PSVariable.Set('verificationCause','artifact_signature_invalid')
    $script:adapterCalls.Clear()
    $r=& $module {param($o,$f,$s) Invoke-PreparationAction @{id='install_wsl'} $o $f $s} $o (Facts) $fixture
    Assert ($r.exit_code -eq 1 -and $script:adapterCalls.Count -eq 1) 'invalid signature no installer'
    $before=Facts;$before.distro_present=$false;$before.registrations=@(@{name='Other';generation=2;is_default=$true})
    $after=Facts;$after.registrations=@(@{name='Other';generation=2;is_default=$false},@{name='Ubuntu-24.04';generation=2;is_default=$true})
    $module.SessionState.PSVariable.Set('afterFixture',$after)
    & $module {function script:Get-PreparationInventory {param($o) return $script:afterFixture}}
    $r=& $module {param($o,$f) Get-PreparationObservedEffect @{id='install_distro'} $o $f 0} $o $before
    Assert ($r.uncertain -and !$r.confirmed) 'unrelated default drift refused'
    $after.registrations[0].is_default=$true;$after.registrations[1].is_default=$false
    $r=& $module {param($o,$f) Get-PreparationObservedEffect @{id='install_distro'} $o $f 0} $o $before
    Assert ($r.confirmed -and !$r.uncertain) 'unrelated registrations preserved'
    $after.systemd_configured=$true
    $r=& $module {param($o,$f) Get-PreparationObservedEffect @{id='enable_systemd'} $o $f 124} $o $before
    Assert ($r.confirmed -and $r.exit_code -eq 124) 'timeout followed by observed effects'
    $after.feature_states=@{VirtualMachinePlatform='Enable Pending'};$after.features_known=$true
    $r=& $module {param($o,$f) Get-PreparationObservedEffect @{id='enable_features';before=@('VirtualMachinePlatform')} $o $f 3010} $o $before
    Assert ($r.confirmed -and $r.exit_code -eq 3010) 'feature pending confirmed 3010'
    $r=& $module {param($o,$f) Get-PreparationObservedEffect @{id='install_wsl'} $o $f 0} $o $before
    Assert ($r.confirmed -and $r.exit_code -eq 0) 'WSL version postverified'
    $o.ActionTimeoutSeconds=0;$o.ActionDeadline=[Diagnostics.Stopwatch]::StartNew()
    $r=& $module {param($o,$f) Get-PreparationObservedEffect @{id='enable_systemd'} $o $f 0} $o $before
    Assert ($r.uncertain -and $r.exit_code -eq 124) 'postverification honors exhausted budget'
} finally {
    & $module {param($resolver) Set-Item Function:script:Get-PreparationExecutable $resolver} $originalExecutableResolver
    Remove-Item -LiteralPath $fixture -Recurse -Force
}
if($env:OS -eq 'Windows_NT') {
    $path=& $module {Get-PreparationExecutable 'wsl.exe'}
    Assert ($path -like '*Windows*System32*wsl.exe') 'protected binary resolver'
}
$threw=$false;try{& $module {Get-PreparationExecutable 'evil.exe'}}catch{$threw=$true}
Assert $threw 'unknown binary refused'
# Direct evidence safety guard fixtures: no filesystem or ACL changes.
if($env:OS -eq 'Windows_NT') {
& $module {
    $script:ownerId=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $script:reparse=$false;$script:unsafeAcl=$false;$script:readAcl=$false;$script:ancestorRights=0;$script:ancestorOwner=$null
    function script:Test-Path {param($LiteralPath) return $true}
    function script:Get-Item {param($LiteralPath,[switch]$Force) return @{Attributes=$(if($script:reparse){[IO.FileAttributes]::ReparsePoint}else{[IO.FileAttributes]::Directory})}}
    function script:Get-Acl {
        param($LiteralPath)
        $ancestor=($LiteralPath.TrimEnd('/','\') -eq 'C:')
        $owner=$script:ownerId
        if($ancestor -and $script:ancestorOwner){$owner=$script:ancestorOwner}
        $acl=New-Object PSObject -Property @{OwnerId=$owner;UnsafeAcl=$script:unsafeAcl;ReadAcl=$script:readAcl;AncestorRights=$(if($ancestor){$script:ancestorRights}else{0})}
        $acl | Add-Member ScriptMethod GetOwner {param($type) return (New-Object Security.Principal.SecurityIdentifier($this.OwnerId))}
        $acl | Add-Member ScriptMethod GetAccessRules {param($a,$b,$c) if($this.UnsafeAcl){return @(@{AccessControlType='Allow';FileSystemRights=[Security.AccessControl.FileSystemRights]::Write;IdentityReference=@{Value='S-1-1-0'}})};if($this.AncestorRights){return @(@{AccessControlType='Allow';PropagationFlags=0;FileSystemRights=$this.AncestorRights;IdentityReference=@{Value='S-1-5-11'}})};if($this.ReadAcl){return @(@{AccessControlType='Allow';PropagationFlags=0;FileSystemRights=[Security.AccessControl.FileSystemRights]::ReadAndExecute;IdentityReference=@{Value='S-1-5-32-545'}})};return @()}
        return $acl
    }
}
$ok=& $module {try{Assert-PreparationEvidencePath 'C:/mock';$true}catch{$false}}
Assert $ok 'restrictive evidence ACL accepted'
& $module {$script:readAcl=$true}
$ok=& $module {try{Assert-PreparationEvidencePath 'C:/mock';$true}catch{$false}}
Assert $ok 'standard Users read execute ACL accepted'
& $module {$script:readAcl=$false;$script:ancestorRights=[Security.AccessControl.FileSystemRights]::AppendData}
$ok=& $module {try{Assert-PreparationEvidencePath 'C:/mock';$true}catch{$false}}
Assert $ok 'ancestor Authenticated Users sibling creation accepted'
& $module {$script:ancestorRights=[Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles}
$ok=& $module {try{Assert-PreparationEvidencePath 'C:/mock';$true}catch{$false}}
Assert (!$ok) 'ancestor untrusted child deletion refused'
& $module {$script:ancestorRights=0;$script:ancestorOwner='S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464'}
$ok=& $module {try{Assert-PreparationEvidencePath 'C:/mock';$true}catch{$false}}
Assert $ok 'OS ancestor TrustedInstaller owner accepted'
& $module {$script:ancestorOwner=$null;$script:ownerId='S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464'}
$ok=& $module {try{Assert-PreparationEvidencePath 'C:/mock';$true}catch{$false}}
Assert (!$ok) 'TrustedInstaller cannot own strict managed leaf'
& $module {$script:ownerId=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value}

& $module {$script:ancestorOwner=$null}

& $module {$script:readAcl=$false}
& $module {$script:reparse=$true}
$ok=& $module {try{Assert-PreparationEvidencePath 'C:/mock';$true}catch{$false}}
Assert (!$ok) 'evidence reparse refused'
& $module {$script:reparse=$false;$script:ownerId='S-1-1-0'}
$ok=& $module {try{Assert-PreparationEvidencePath 'C:/mock';$true}catch{$false}}
Assert (!$ok) 'foreign owner refused'
& $module {$script:ownerId=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value;$script:unsafeAcl=$true}
$ok=& $module {try{Assert-PreparationEvidencePath 'C:/mock';$true}catch{$false}}
Assert (!$ok) 'untrusted write ACL refused'
}
# W06 follows lifecycle and resources, shares qualification and consent authority.
$script:facts=Facts;$script:source=@{verified=$true;clean=$true;revision=('a'*40)};$script:failWrite=0;$script:drift=$false
$script:facts.bridge_facts=@{schema_version=1;distro='Ubuntu-24.04';observed_address='172.20.0.2';ownership='absent';bridge_ready=$false;routing_ready=$false;agent_ready=$false;action='install';blockers=@();fingerprint='bridge-before'}
$o=Options;$previousExecutions=$script:executions;$r=Invoke-WindowsPreparation $o $ports
Assert ($r.actions.Count -eq 1 -and $r.actions[0].id -eq 'bridge_install' -and $script:executions -eq $previousExecutions) 'W06 install read-only plan delegates existing owner'
Assert ($r.actions[0].credential_guidance -match 'current Windows account') 'credential owner guidance'
$beforeFingerprint=$r.plan_fingerprint;$script:facts.bridge_facts.observed_address='172.20.0.3';$script:facts.bridge_facts.fingerprint='bridge-changed';$r=Invoke-WindowsPreparation $o $ports
Assert ($r.plan_fingerprint -ne $beforeFingerprint) 'address drift invalidates exact plan'
$o.Mode='Apply';$o.ApproveApply=$true;$r=Invoke-WindowsPreparation $o $ports
Assert ($r.blockers[-1].code -eq 'unqualified_target' -and $script:executions -eq $previousExecutions) 'W06 retains qualification guard'
$script:facts.bridge_facts.blockers=@('foreign_portproxy_collision');$o=Options;$r=Invoke-WindowsPreparation $o $ports
Assert ($r.actions.Count -eq 0 -and $r.blockers.code -contains 'foreign_portproxy_collision') 'W06 collision before mutation'
$script:facts=Facts;$script:facts.Remove('bridge_facts');$r=Invoke-WindowsPreparation $o $ports
Assert ($r.blockers.code -contains 'bridge_inventory_required') 'unobserved bridge cannot imply capability ready'
$script:facts=Facts;$script:facts.systemd_configured=$false;$script:facts.bridge_facts=@{blockers=@('bridge_inventory_unavailable')};$r=Invoke-WindowsPreparation $o $ports
Assert ($r.actions[0].id -eq 'enable_systemd' -and $r.actions.Count -eq 1) 'lifecycle stage precedes bridge'
$script:facts=Facts;$script:facts.bridge_facts=@{schema_version=1;distro='Ubuntu-24.04';observed_address='172.20.0.2';ownership='owned';bridge_ready=$false;routing_ready=$false;agent_ready=$false;action='refresh';blockers=@();fingerprint='owned-refresh'}
$o=Options;$o.Mode='Apply';$o.QualificationRun=$true;$o.ApproveApply=$true
$script:source.verified=$false;$prior=$script:executions;$r=Invoke-WindowsPreparation $o $ports
Assert ($r.blockers[-1].code -eq 'unverified_source' -and $script:executions -eq $prior) 'W06 unverified executed source never reaches Execute'
$script:source.verified=$true;$script:effect=@{confirmed=$true;uncertain=$false;exit_code=0};$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.completed_actions -contains 'bridge_refresh' -and $r.result.changed -and !$r.result.services_verified) 'qualified actual Application executes owned bridge stage'
$script:facts=Facts;$o=Options;$prior=$script:executions;$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.capability_ready -and !$r.actions.Count -and $script:executions -eq $prior) 'rerun observes ready owned bridge without mutation'
Write-Output "PASS $count Windows lifecycle assertions (mocked host ports; no live preparation)"
# W07 handoff is selected-account advice only; no install action is delegated.
$script:facts=Facts
$script:facts.handoff_ready=$true;$script:facts.handoff_checkout='/home/operator/TSW checkout'
$o=Options;$o.LinuxCheckout='/home/operator/TSW checkout'
$r=Invoke-WindowsPreparation $o $ports
Assert ($r.handoff.account -ceq 'operator' -and $r.handoff.distro -ceq 'Ubuntu-24.04') 'W07 selected account and distro'
Assert ($r.handoff.operator_command -match "--distribution 'Ubuntu-24.04' --user 'operator'" -and $r.handoff.operator_command -match "cd -- ''/home/operator/TSW checkout'' && ./modules/tsw_native_linux/boostrap/prepare_linux.sh --service-profile service-access && exec ./modules/tsw_native_linux/boostrap/install.sh") 'W07 exact quoted command and preparation dependency'
Assert (!$r.result.preparation_ready -and !$r.result.services_verified -and $r.handoff.status -eq 'LINUX_PREPARATION_REQUIRED') 'W07 no false aggregate readiness'
$before=$script:executions
$r=Invoke-WindowsPreparation $o $ports
Assert ($before -eq $script:executions) 'W07 rerun prints only'
$script:facts.handoff_ready=$false
$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.exit_code -eq 2 -and $r.handoff.status -eq 'BLOCKED' -and !$r.handoff.operator_command) 'W07 missing checkout refuses command'
$o.LinuxCheckout='/mnt/c/checkout';$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.exit_code -eq 2 -and $r.blockers[0].code -eq 'invalid_arguments') 'W07 mounted checkout refused'
$o.LinuxCheckout='/home/operator/evil;touch';$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.exit_code -eq 2) 'W07 metacharacters refused'
Write-Output 'PASS W07 mocked handoff contracts'

# W08 checkpoints are evidence, never reusable approval or readiness.
$script:stateRecords=New-Object Collections.ArrayList
$script:stateInvalid=$false
$ports.ReadState={param($o,$identity) if($script:stateInvalid){throw 'stale_corrupt_foreign_bootstrap_state'};return $null}
$ports.WriteState={param($store,$state) [void]$script:stateRecords.Add($state)}
$script:facts=Facts;$script:facts.systemd_configured=$false
$o=Options;$o.Mode='Apply';$o.ApproveApply=$true;$o.QualificationRun=$true
$script:failWrite=0;$script:effect=@{confirmed=$true;uncertain=$false;exit_code=0}
$r=Invoke-WindowsPreparation $o $ports
Assert ($script:stateRecords.Count -eq 2) 'W08 durable intent then effect'
Assert ($script:stateRecords[0].stage -eq 'enable_systemd' -and $script:stateRecords[0].uncertain -and $script:stateRecords[1].restart -eq 'distro') 'W08 stage and restart boundary'
$module=Get-Module Preparation
$wire=$script:stateRecords[1] | ConvertTo-Json -Depth 12 -Compress
$valid=& $module {param($text) ConvertFrom-PreparationStateJson $text} $wire
Assert ($valid.timestamp_utc -is [string] -and $valid.timestamp_utc -ceq $script:stateRecords[1].timestamp_utc) 'W08 timestamp wire type and value preserved across PowerShell runtimes'
$identity=$script:stateRecords[1].identity
& $module {param($state,$identity) Assert-PreparationState $state $identity} $valid $identity
Assert ($valid.versions.windows_build -eq 22631 -and $valid.versions.wsl -eq '3.0.1' -and $valid.exit_code -eq 0) 'W08 tested version and exit context'
foreach($field in @('schema','exit_code','confirmed','uncertain','observation','next_command')) {
    $bad=& $module {param($text) ConvertFrom-PreparationStateJson $text} $wire
    $bad.$field='password-do-not-publish'
    $blocked=$false
    try{& $module {param($state,$identity) Assert-PreparationState $state $identity} $bad $identity}catch{$blocked=$true}
    Assert $blocked ('W08 rejects corrupt '+$field)
}
foreach($invalid in @(@{field='schema';value=$true},@{field='schema';value=1.0},@{field='exit_code';value=0.0},@{field='exit_code';value=3011},@{field='windows_build';value=22631.5})) {
    $bad=& $module {param($text) ConvertFrom-PreparationStateJson $text} $wire
    if($invalid.field -eq 'windows_build'){$bad.versions.windows_build=$invalid.value}else{$bad.($invalid.field)=$invalid.value}
    $blocked=$false
    try{& $module {param($state,$identity) Assert-PreparationState $state $identity} $bad $identity}catch{$blocked=$true}
    Assert $blocked ('W08 rejects noninteger or out-of-range '+$invalid.field)
}
$before=$script:executions;$script:stateInvalid=$true
$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.exit_code -eq 2 -and $script:executions -eq $before) 'W08 invalid checkpoint prevents privileged execution'
$o.Mode='Plan';$o.ApproveApply=$false;$o.QualificationRun=$false
$r=Invoke-WindowsPreparation $o $ports
Assert ($r.actions.Count -eq 1 -and $r.blockers[-1].stage -eq 'state_validation' -and $r.read_only) 'W08 stale state retains read-only inventory plan'
$script:stateInvalid=$false
$o.Mode='Apply';$o.ApproveApply=$true;$o.QualificationRun=$true
$ports.LockState={param($store) $script:facts.systemd_configured=$true;return $null}
$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.exit_code -eq 2 -and $script:executions -eq $before -and $r.blockers[-1].code -eq 'consent_drift') 'W08 reinventory under lock rejects concurrent completion'
$ports.Remove('LockState')
$script:facts=Facts # Restart completed and actual systemd observed.
$o.Mode='Plan';$o.ApproveApply=$false;$o.QualificationRun=$false
$r=Invoke-WindowsPreparation $o $ports
Assert ($script:executions -eq $before -and $script:stateRecords.Count -eq 2) 'W08 observed satisfied resume skips mutation and writes'
Write-Output 'PASS W08 mocked recovery contracts'

# Actual application checkpoint validation retains four-part runtime observations.
$versionModule=Get-Module Preparation
$versionPorts=@{};foreach($key in $ports.Keys){$versionPorts[$key]=$ports[$key]}
$script:versionRecords=New-Object Collections.ArrayList
$script:versionExecutions=0
$versionPorts.ReadState={param($o,$identity) return $null}
$versionPorts.WriteState={
    param($store,$state)
    $wire=$state | ConvertTo-Json -Depth 12 -Compress
    & $versionModule {param($text,$identity) Assert-PreparationState (ConvertFrom-PreparationStateJson $text) $identity} $wire $state.identity
    [void]$script:versionRecords.Add($state)
}
$versionPorts.Execute={
    param($action,$o,$facts,$plan)
    if($action.id -cne 'adapt_wsl_resources' -or $script:versionRecords.Count -ne 1 -or $script:versionRecords[0].status -cne 'pending' -or $script:versionRecords[0].versions.wsl -cne '3.0.3.0'){throw 'version_checkpoint_missing_before_execution'}
    $script:versionExecutions++
    return @{confirmed=$true;uncertain=$false;exit_code=0}
}
$script:facts=StoreWsl2Facts;$script:facts.wsl_version='3.0.3.0';$script:facts.wsl_store_package.version='3.0.3.0'
$script:facts.resource_facts.config_values.memory='25GB';$script:facts.resource_facts.config_values.swap='4GB'
$o=Options;$o.Mode='Apply';$o.ApproveApply=$true;$o.QualificationRun=$true
$r=Invoke-WindowsPreparation $o $versionPorts
Assert ($r.result.exit_code -eq 3 -and $r.result.completed_actions[0] -ceq 'adapt_wsl_resources' -and $script:versionExecutions -eq 1) 'four-part pending checkpoint permits only the mocked resource action'
Assert ($script:versionRecords.Count -eq 2 -and $script:versionRecords[1].status -ceq 'effect' -and $script:versionRecords[1].versions.wsl -ceq '3.0.3.0') 'four-part runtime survives actual pending and effect validation unchanged'
$invalidWslVersions=@(
    @{value='3.0'},@{value='3.0.3.0.1'},@{value='3..3'},@{value='3.0.3.'},@{value=' 3.0.3'},@{value='3.0.3 '},
    @{value="3.0.3`n"},@{value="3.0.3.0`r`n"},@{value='3.a.3'},@{value=(([string][char]0x0663)+'.0.3')},
    @{value=$false},@{value=0},@{value=3.0},@{value=@('3.0.3')},@{value=@{major=3}}
)
$versionPorts.ReadState={
    param($o,$identity)
    $wire=$script:versionRecords[0] | ConvertTo-Json -Depth 12 -Compress
    $state=& $versionModule {param($text) ConvertFrom-PreparationStateJson $text} $wire
    $state.versions.wsl=$script:invalidWslVersion
    & $versionModule {param($state,$identity) Assert-PreparationState $state $identity} $state $identity
    return $state
}
foreach($case in $invalidWslVersions){
    $script:invalidWslVersion=$case.value
    $beforeExecutions=$script:versionExecutions;$beforeRecords=$script:versionRecords.Count
    $r=Invoke-WindowsPreparation $o $versionPorts
    Assert ($r.result.exit_code -eq 2 -and @($r.blockers | Where-Object{$_.code -ceq 'bootstrap_state_invalid'}).Count -eq 1 -and $script:versionExecutions -eq $beforeExecutions -and $script:versionRecords.Count -eq $beforeRecords) 'invalid stored WSL version blocks before execution or another checkpoint'
}
Write-Output 'PASS W08 full WSL version application boundaries (mocked effects)'

# Exercise durable create-then-replace IO; only Windows ACL boundaries are mocked.
$stateModule=Import-Module (Join-Path $RepositoryRoot 'modules/tsw_windows_wsl/bootstrap/preparation/Preparation.psm1') -Force -DisableNameChecking -PassThru
$stateStore=Join-Path ([IO.Path]::GetTempPath()) ('tsw-state-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($stateStore)
try {
    $versionIo=& $stateModule {
        param($store,$pending,$effect,$invalidVersions)
        function Assert-PreparationEvidencePath($Path) {
            if(!$Path.StartsWith($store,[StringComparison]::Ordinal) -or !(Test-Path -LiteralPath $Path)){throw 'unexpected_test_evidence_path'}
        }
        function Set-PreparationPrivateAcl($Path) {}
        Write-PreparationState $store $pending
        Write-PreparationState $store $effect
        $roundtrips=0
        foreach($case in @(@{value='3.0.1'},@{value='3.0.3.0'},@{value='03.0.1'},@{value=$null},@{value=''})){
            foreach($record in @($pending,$effect)){
                $copy=ConvertTo-PreparationHashtable (ConvertFrom-PreparationStateJson ($record | ConvertTo-Json -Depth 12 -Compress))
                $copy.versions.wsl=$case.value
                Write-PreparationState $store $copy
                $persisted=ConvertFrom-PreparationStateJson (Get-Content -Raw -LiteralPath (Join-Path $store 'bootstrap.state.json'))
                Assert-PreparationState $persisted $copy.identity
                if($persisted.status -cne $copy.status){throw 'state_roundtrip_status_changed'}
                if($null -eq $case.value){if($null -ne $persisted.versions.wsl){throw 'state_roundtrip_unknown_changed'}}
                elseif($persisted.versions.wsl -isnot [string] -or $persisted.versions.wsl -cne $case.value){throw 'state_roundtrip_version_changed'}
                $roundtrips++
            }
        }
        $statePath=Join-Path $store 'bootstrap.state.json'
        $beforeHash=(Get-FileHash -LiteralPath $statePath -Algorithm SHA256).Hash
        foreach($case in $invalidVersions){
            $copy=ConvertTo-PreparationHashtable (ConvertFrom-PreparationStateJson ($effect | ConvertTo-Json -Depth 12 -Compress))
            $copy.versions.wsl=$case.value
            $blocked=$false
            try{Write-PreparationState $store $copy}catch{$blocked=$true}
            if(!$blocked -or (Get-FileHash -LiteralPath $statePath -Algorithm SHA256).Hash -cne $beforeHash -or @(Get-ChildItem -LiteralPath $store -Force).Count -ne 1){throw 'invalid_version_changed_durable_checkpoint'}
        }
        return @{roundtrips=$roundtrips;invalid_versions=$invalidVersions.Count}
    } $stateStore $script:stateRecords[0] $script:stateRecords[1] $invalidWslVersions
    Assert ($versionIo.roundtrips -eq 10 -and $versionIo.invalid_versions -eq $invalidWslVersions.Count) 'actual pending/effect IO preserves full legacy/new/null/empty versions and refuses malformed replacement'
    $persisted=& $stateModule {param($text) ConvertFrom-PreparationStateJson $text} (Get-Content -Raw -LiteralPath (Join-Path $stateStore 'bootstrap.state.json'))
    Assert ($persisted.status -ceq 'effect' -and $persisted.confirmed -and !$persisted.uncertain -and $persisted.restart -ceq 'distro') 'durable effect replaces pending state'
    Assert (@(Get-ChildItem -LiteralPath $stateStore -Force).Count -eq 1) 'atomic replacement leaves only the checkpoint'
} finally {Remove-Item -LiteralPath $stateStore -Recurse -Force}

# Actual W05 observation variants: unavailable W06 query versus owned bridge
# with foreign-listener refusal. Neither is admitted as a healthy bridge.
$resourceFingerprintModule=Get-Module Preparation
$script:resourceBridgeVariants=@(
    @{state='BLOCKED';blockers=@('bridge_inventory_unavailable')},
    @{schema_version=1;ownership='owned';bridge_ready=$false;routing_ready=$false;agent_ready=$false;
      login_state='UNVERIFIED';endpoint_state='UNVERIFIED';action=$null;blockers=@('foreign_or_unknown_listener');fingerprint='observed-w06'}
)
function ResourceFingerprintFacts($Bridge){
    $value=Facts
    $value.resource_facts.config_values.memory='25GB';$value.resource_facts.config_values.swap='4GB'
    $value.bridge_facts=$Bridge
    return $value
}
$script:source=@{verified=$true;clean=$true;revision=('a'*40)}
$resourceFingerprintPorts=@{};foreach($key in $ports.Keys){$resourceFingerprintPorts[$key]=$ports[$key]}
$resourceFingerprintPorts.ProtectEvidence={param($o) return 'protected-mocked-resource-store'}
$resourceFingerprintPorts.WriteEvidence={param($store,$event)}
$resourceFingerprintPorts.LockState={param($store) return [IO.MemoryStream]::new()}
$resourceFingerprintPorts.ReadState={param($o,$identity) return $null}
$resourceFingerprintPorts.WriteState={param($store,$state)}
$script:resourceReinventories=0;$script:resourceEffects=0;$script:resourceDrift=$false
$resourceFingerprintPorts.Inventory={
    param($o)
    $script:resourceReinventories++
    $value=ResourceFingerprintFacts $script:resourceBridgeVariants[($script:resourceReinventories-1)%2]
    if($script:resourceDrift -and $script:resourceReinventories -gt 1){$value.resource_facts.config_snapshot.hash='unexpected-config-change'}
    return $value
}
$resourceFingerprintPorts.SourceIdentity={param($o) return $script:source}
$resourceFingerprintPorts.Execute={param($action,$o,$facts,$store)
    if($action.id -cne 'adapt_wsl_resources'){throw 'unexpected_resource_test_action'}
    $script:resourceEffects++
    return @{confirmed=$true;uncertain=$false;exit_code=0}
}
$o=Options
$resourceFirst=Invoke-WindowsPreparation $o $resourceFingerprintPorts
$resourceSecond=Invoke-WindowsPreparation $o $resourceFingerprintPorts
Assert ($resourceFirst.actions.Count -eq 1 -and $resourceFirst.actions[0].id -ceq 'adapt_wsl_resources' -and
    $resourceFirst.plan_fingerprint -ceq $resourceSecond.plan_fingerprint) 'resource_only_consent_excludes_unrelated_bridge_observation'
Assert ($resourceFirst.target.bridge_facts.blockers[0] -ceq 'bridge_inventory_unavailable' -and
    $resourceSecond.target.bridge_facts.blockers[0] -ceq 'foreign_or_unknown_listener' -and
    $script:resourceBridgeVariants[0].ContainsKey('state') -and $script:resourceBridgeVariants[1].ContainsKey('fingerprint')) 'resource_projection_preserves_raw_target_and_input_bridge_evidence'
$script:resourceReinventories=0
$o.Mode='Apply';$o.ApproveApply=$true;$o.QualificationRun=$true;$o.ApprovedPlan=$resourceFirst.plan_fingerprint
$resourceApplied=Invoke-WindowsPreparation $o $resourceFingerprintPorts
Assert ($script:resourceReinventories -eq 3 -and $script:resourceEffects -eq 1 -and
    $resourceApplied.result.exit_code -eq 3 -and $resourceApplied.result.completed_actions[0] -ceq 'adapt_wsl_resources') 'resource_apply_three_real_reinventories_allow_w06_observation_alternation_without_bridge_effect'
$script:resourceReinventories=0;$script:resourceEffects=0;$script:resourceDrift=$true
$resourceRefused=Invoke-WindowsPreparation $o $resourceFingerprintPorts
Assert ($script:resourceEffects -eq 0 -and $resourceRefused.result.exit_code -eq 2 -and
    $resourceRefused.blockers[-1].code -ceq 'consent_drift') 'resource_config_snapshot_drift_still_refuses_before_effect'
$bridgeFingerprintPorts=@{};foreach($key in $resourceFingerprintPorts.Keys){$bridgeFingerprintPorts[$key]=$resourceFingerprintPorts[$key]}
$script:bridgeFingerprint='first-observation'
$bridgeFingerprintPorts.Inventory={param($o)
    $value=Facts
    $value.bridge_facts=@{schema_version=1;distro='Ubuntu-24.04';observed_address='172.20.0.2';ownership='owned';
        bridge_ready=$false;routing_ready=$false;agent_ready=$false;action='refresh';blockers=@();fingerprint=$script:bridgeFingerprint}
    return $value
}
$o=Options
$bridgeFirst=Invoke-WindowsPreparation $o $bridgeFingerprintPorts
$script:bridgeFingerprint='changed-observation'
$bridgeSecond=Invoke-WindowsPreparation $o $bridgeFingerprintPorts
Assert ($bridgeFirst.actions.Count -eq 1 -and $bridgeFirst.actions[0].id -ceq 'bridge_refresh' -and
    $bridgeFirst.plan_fingerprint -cne $bridgeSecond.plan_fingerprint) 'bridge_mutation_retains_exact_bridge_fingerprint_binding'

Write-Output 'PASS durable checkpoint filesystem contracts (mocked ACL boundaries)'
