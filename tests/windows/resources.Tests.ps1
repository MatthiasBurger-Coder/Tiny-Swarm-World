param([Parameter(Mandatory=$true)][string]$RepositoryRoot)
$ErrorActionPreference='Stop'
Import-Module (Join-Path $RepositoryRoot 'tools/windows/preparation/Preparation.psm1') -Force -DisableNameChecking
$m=Get-Module Preparation
$count=0
function Assert($value,$name){if(!$value){throw "FAIL: $name"};$script:count++}
function ResourceFacts {
    return @{resource_facts=@{projection_valid=$true;profile=@{memory_gib=16;processors=8;disk_gib=150};node_budget=@{memory_gib=19;processors=8;disk_gib=80};physical_memory_bytes=[long]34359738368;logical_processors=16;storage_known=$true;config_safe=$true;distro_volume='same';swap_volume='same';distro_free_bytes=[long]536870912000;swap_free_bytes=[long]536870912000;config_values=@{memory='21GB';processors='8';swap='6GB'};config_snapshot=@{hash='approved';metadata='acl'};effective_known=$true;effective_memory_bytes=[long]22333829939;effective_processors=8;effective_swap_bytes=[long]6442450944;effective_disk_bytes=[long]322122547200}}
}
function Assess($f,$o=@{}){return & $m {param($o,$f) Get-PreparationResourceAssessment $o $f} $o $f}
foreach($gib in @(16,32,64)){
    $f=ResourceFacts;$f.resource_facts.physical_memory_bytes=[long]$gib*1073741824
    $r=Assess $f
    Assert ($r.allocation.memory_gib -eq 21 -and $r.managed_nodes.memory_gib -eq 19 -and $r.windows_reserve.memory_gib -eq [Math]::Max(4,$gib/4)) "separate budgets $gib"
    Assert ($r.effective_verified -eq ($gib -ge 32)) "capacity $gib"
}
$f=ResourceFacts;$r=Assess $f @{WslMemoryGiB=24};Assert ($r.allocation.swap_gib -eq 6 -and $r.change_required) 'override derives swap'
$r=Assess $f @{WslMemoryGiB=20};Assert ($r.blockers.code -contains 'allocation_below_requirements') 'cannot shrink nodes'
$r=Assess $f @{WslMemoryGiB=25};Assert ($r.blockers.code -contains 'insufficient_host_capacity') 'cannot consume Windows reserve'
$r=Assess $f @{WslSwapGiB=0};Assert ($r.allocation.swap_gib -eq 0 -and $r.change_required) 'swap can disable'
$f=ResourceFacts;$f.resource_facts.logical_processors=8;Assert ((Assess $f).blockers.code -contains 'insufficient_host_capacity') 'CPU reserve'
$f=ResourceFacts;$f.resource_facts.storage_known=$false;Assert ((Assess $f).blockers.code -contains 'resource_inventory_unknown') 'unknown disk'
$f=ResourceFacts;$f.resource_facts.distro_free_bytes=[long]176*1073741824;Assert ((Assess $f).effective_verified) 'colocated exact disk boundary'
$f.resource_facts.distro_free_bytes--;Assert ((Assess $f).blockers.code -contains 'insufficient_host_disk') 'colocated disk shortage'
$f=ResourceFacts;$f.resource_facts.swap_volume='different';$f.resource_facts.distro_free_bytes=[long]170*1073741824;$f.resource_facts.swap_free_bytes=[long]26*1073741824;Assert ((Assess $f).effective_verified) 'different volume exact boundary'
$f.resource_facts.swap_free_bytes--;Assert ((Assess $f).blockers.code -contains 'insufficient_host_disk') 'different swap volume shortage'
foreach($key in @('effective_memory_bytes','effective_processors','effective_swap_bytes','effective_disk_bytes')){$f=ResourceFacts;$f.resource_facts[$key]=0;Assert (!(Assess $f).effective_verified) "effective observation $key"}
$f=ResourceFacts;$f.resource_facts.effective_memory_bytes=[long]20.7GB;Assert ((Assess $f).effective_verified) 'kernel ceiling tolerance'
$f.resource_facts.effective_memory_bytes=[long]18.9GB;Assert (!(Assess $f).effective_verified) 'minimum never excused'
$f=ResourceFacts;$f.resource_facts.profile.memory_gib=24;$f.resource_facts.config_values.memory='24GB';$f.resource_facts.effective_memory_bytes=[long]23.8GB
Assert ((Assess $f).blockers.code -contains 'insufficient_effective_memory') 'profile usable RAM floor independent from ceiling tolerance'
foreach($o in @(@{WslMemoryGiB=0},@{WslProcessors=-1},@{WslSwapGiB=-1},@{WslMemoryGiB='21'})){
    $r=Invoke-WindowsPreparation (@{Mode='Plan';Distro='Ubuntu-24.04';ProbeTimeoutSeconds=15;ActionTimeoutSeconds=900}+ $o) @{Inventory={throw 'must not probe'}}
    Assert ($r.blockers[0].code -eq 'invalid_arguments') 'override rejected before probes'
}
foreach($encodingName in @('utf8','utf8bom','utf16')){
    $text="# retain`r`n[wsl2]`r`n  memory = 8GB  `r`nnetworkingMode=mirrored`r`n[experimental]`r`nautoMemoryReclaim=gradual`r`n"
    $enc=New-Object Text.UTF8Encoding($false)
    if($encodingName -eq 'utf8bom'){$enc=New-Object Text.UTF8Encoding($true)}
    if($encodingName -eq 'utf16'){$enc=New-Object Text.UnicodeEncoding($false,$true)}
    $bytes=[byte[]]($enc.GetPreamble()+$enc.GetBytes($text))
    $after=& $m {param($bytes) $p=ConvertFrom-PreparationWslConfig $bytes;ConvertTo-PreparationWslConfig $p @{memory_gib=21;processors=8;swap_gib=6}} $bytes
    $decoded=$enc.GetString($after)
    Assert ($decoded.Contains('  memory = 21GB  ') -and $decoded.Contains('networkingMode=mirrored') -and $decoded.Contains('[experimental]') -and $decoded.Contains("`r`n")) "preserve $encodingName"
    $again=& $m {param($bytes) $p=ConvertFrom-PreparationWslConfig $bytes;ConvertTo-PreparationWslConfig $p @{memory_gib=21;processors=8;swap_gib=6}} $after
    Assert ([Convert]::ToBase64String($after) -ceq [Convert]::ToBase64String($again)) "idempotent $encodingName"
}
foreach($text in @("[wsl2]`nmemory=8GB`nMEMORY=9GB","[wsl2]`n[wsl2]","[wsl2]`nmemory=8GiB","[wsl2]`nswapfile=D:\swap.vhdx","garbage","[wsl2]`nprocessors=2.5")){
    $failed=$false;try{& $m {param($text) ConvertFrom-PreparationWslConfig ([Text.Encoding]::UTF8.GetBytes($text))} $text | Out-Null}catch{$failed=$true}
    Assert $failed 'ambiguous config preserved by refusal'
}
# Concrete projection provenance; altered input blocks, without touching canonical files.
$o=@{RepositoryRoot=$RepositoryRoot;ServiceProfile='service-access'}
$p=& $m {param($o) Get-PreparationResourceProjection $o} $o
Assert ($p.node_budget.memory_gib -eq 19 -and $p.profile.disk_gib -eq 150) 'canonical projection'
$sandbox=Join-Path ([IO.Path]::GetTempPath()) ('tsw-projection-'+[guid]::NewGuid().ToString('N'))
try{
    $projectionText=Get-Content -Raw -LiteralPath (Join-Path $RepositoryRoot 'tools/windows/preparation/resource-projection.json')
    $assetNames=@('tools/windows/preparation/resource-projection.json','src/tiny_swarm_world/domain/preflight/resources.py','src/tiny_swarm_world/domain/host_environment.py','infra/config/node-providers/provider_config.yaml')
    foreach($asset in $assetNames){$target=Join-Path $sandbox $asset;[void][IO.Directory]::CreateDirectory((Split-Path -Parent $target));[IO.File]::WriteAllBytes($target,[IO.File]::ReadAllBytes((Join-Path $RepositoryRoot $asset)))}
    $sandboxOptions=@{RepositoryRoot=$sandbox;ServiceProfile='service-access'}
    $source=Join-Path $sandbox 'infra/config/node-providers/provider_config.yaml';[IO.File]::AppendAllText($source,"`n# drift")
    $refused=$false;try{& $m {param($o) Get-PreparationResourceProjection $o} $sandboxOptions | Out-Null}catch{$refused=$true};Assert $refused 'canonical source drift blocks Windows projection'
    [IO.File]::WriteAllBytes($source,[IO.File]::ReadAllBytes((Join-Path $RepositoryRoot 'infra/config/node-providers/provider_config.yaml')))
    $invalid=$projectionText | ConvertFrom-Json;$invalid.sources.PSObject.Properties.Remove('src/tiny_swarm_world/domain/host_environment.py')
    [IO.File]::WriteAllText((Join-Path $sandbox 'tools/windows/preparation/resource-projection.json'),($invalid | ConvertTo-Json -Depth 10))
    $refused=$false;try{& $m {param($o) Get-PreparationResourceProjection $o} $sandboxOptions | Out-Null}catch{$refused=$true};Assert $refused 'incomplete source hash inventory blocked'
    $invalid=$projectionText | ConvertFrom-Json;$invalid.node_budget.memory_gib=0
    [IO.File]::WriteAllText((Join-Path $sandbox 'tools/windows/preparation/resource-projection.json'),($invalid | ConvertTo-Json -Depth 10))
    $refused=$false;try{& $m {param($o) Get-PreparationResourceProjection $o} $sandboxOptions | Out-Null}catch{$refused=$true};Assert $refused 'malformed projection amounts blocked'
}finally{if(Test-Path -LiteralPath $sandbox){Remove-Item -LiteralPath $sandbox -Recurse -Force}}
$output="effective_memory_bytes=22000000000`neffective_processors=8`neffective_swap_bytes=0`neffective_disk_bytes=200000000000`n"
foreach($bad in @($output.Replace('effective_processors=8','effective_processors=oops'),($output+'effective_processors=9'),($output+'projection_valid=1'),($output.Replace('effective_processors=8','effective_processors=999999999999999999999999999')))){
    $parsed=& $m {param($s) ConvertFrom-PreparationEffectiveResources @{exit_code=0;stdout=$s;stderr=''}} $bad
    Assert (!$parsed) 'malformed duplicate or unknown effective keys refused'
}
$parsed=& $m {param($s) ConvertFrom-PreparationEffectiveResources @{exit_code=0;stdout=$s;stderr='unexpected'}} $output
Assert (!$parsed) 'stderr invalidates effective observation'
$full=@{handoff_ready=$true;handoff_checkout='/home/operator/Tiny-Swarm-World';bridge_facts=@{bridge_ready=$true;blockers=@();fingerprint='owned-ready'};platform='Windows';host_identity='test-host';product_type=1;build=22631;architecture='AMD64';elevated=$true;virtualization=$true;features_known=$true;features_missing=@();reboot_pending=$false;wsl_present=$true;wsl_version='3.0.1';distro_present=$true;distro_inventory_known=$true;wsl_generation=2;running=$true;linux_known=$true;linux_id='ubuntu';release='24.04';linux_architecture='x86_64';uid=1000;user='operator';config_safe=$true;systemd_packages=$true;systemd_configured=$true;pid1='systemd';resource_facts=(ResourceFacts).resource_facts}
$o=@{Mode='Plan';Distro='Ubuntu-24.04';ServiceProfile='default';ProbeTimeoutSeconds=15;ActionTimeoutSeconds=900;WslMemoryGiB=22;WslProcessors=9;WslSwapGiB=0;Json=$true;ApproveApply=$false;QualificationRun=$false;QualificationHost='test-host';QualificationDistro='Ubuntu-24.04';QualificationRevision=('a'*40);RecoveryReference='disposable snapshot'}
$script:resourceExecutions=0;$script:resourceWrites=0;$script:resourceDrift=$false;$script:resourceInventory=0
$ports=@{Inventory={param($options) $script:resourceInventory++;if($script:resourceDrift -and $script:resourceInventory -gt 1){$full.resource_facts.config_snapshot.hash='changed'};return $full};SourceIdentity={return @{verified=$true;clean=$true;revision=('a'*40)}};EvidencePreflight={return $true};ProtectEvidence={return 'disposable'};WriteEvidence={$script:resourceWrites++};Execute={param($a,$o,$f,$s) $script:resourceExecutions++;return @{confirmed=$true;uncertain=$false;exit_code=0}}}
$r=Invoke-WindowsPreparation $o $ports
Assert ($r.actions.Count -eq 1 -and $r.actions[0].id -eq 'adapt_wsl_resources' -and $script:resourceExecutions -eq 0 -and $script:resourceWrites -eq 0) 'read-only resource plan no effects'
$baselineFingerprint=$r.plan_fingerprint
$full.resource_facts.distro_free_bytes-=1000000;$full.resource_facts.swap_free_bytes-=1000000;$full.resource_facts.effective_disk_bytes-=1000000
$fluctuation=Invoke-WindowsPreparation $o $ports
Assert ($fluctuation.plan_fingerprint -ceq $baselineFingerprint) 'feasible disk fluctuation retains exact plan identity'
Assert ($fluctuation.target.resource_facts.distro_free_bytes -eq $full.resource_facts.distro_free_bytes) 'fingerprint normalization preserves real observed facts'
$free=$full.resource_facts.distro_free_bytes;$full.resource_facts.distro_free_bytes=1
$shortage=Invoke-WindowsPreparation $o $ports
Assert ($shortage.plan_fingerprint -cne $baselineFingerprint -and $shortage.blockers.code -contains 'insufficient_host_disk') 'capacity drop invalidates consent'
$full.resource_facts.distro_free_bytes=$free;$full.resource_facts.swap_volume='other'
$volumeChange=Invoke-WindowsPreparation $o $ports
Assert ($volumeChange.plan_fingerprint -cne $baselineFingerprint) 'volume change binds consent'
$full.resource_facts.swap_volume='same'
Assert ($r.result.next_command.Contains('-ServiceProfile default') -and $r.result.next_command.Contains('-WslMemoryGiB 22') -and $r.result.next_command.Contains('-WslProcessors 9') -and $r.result.next_command.Contains('-WslSwapGiB 0')) 'rerun preserves selection and overrides'
$o.Mode='Apply';$o.ApproveApply=$true
$r=Invoke-WindowsPreparation $o $ports
Assert ($r.blockers.code -contains 'unqualified_target' -and $script:resourceExecutions -eq 0) 'ordinary resource apply guarded'
$o.QualificationRun=$true;$script:resourceDrift=$true;$script:resourceInventory=0
$r=Invoke-WindowsPreparation $o $ports
Assert ($r.blockers.code -contains 'consent_drift' -and $script:resourceExecutions -eq 0) 'resource consent drift blocks'
$script:resourceDrift=$false;$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.exit_code -eq 3 -and $r.restart.scope -eq 'WSL-wide' -and $script:resourceExecutions -eq 1 -and !$r.result.capability_ready) 'confirmed resource mutation requires operator restart'
$ports.Execute={return @{confirmed=$false;uncertain=$true;exit_code=124;cause='resource_host_deadline'}}
$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.exit_code -eq 124 -and $r.result.outcome -eq 'PARTIAL') 'bounded resource deadline preserved'
$o.Mode='Plan';$o.ApproveApply=$false;$o.QualificationRun=$false;$o.Remove('WslMemoryGiB');$o.Remove('WslProcessors');$o.Remove('WslSwapGiB');$full.resource_facts=(ResourceFacts).resource_facts
$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.outcome -eq 'READY' -and $r.actions.Count -eq 0 -and $r.resources.effective_verified) 'zero change observed capacity verification'
$full.resource_facts.effective_processors=4;$r=Invoke-WindowsPreparation $o $ports
Assert ($r.result.exit_code -eq 3 -and !$r.result.capability_ready) 'matching config insufficient to establish effective capacity'
foreach($bad in @('32',$null,0)){$f=ResourceFacts;$f.resource_facts.physical_memory_bytes=$bad;Assert ((Assess $f).blockers.code -contains 'resource_inventory_unknown') 'typed physical facts required'}
Write-Output "PASS: $count resource assertions"
