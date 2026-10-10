function Get-PreparationResourceCause($Message,$Fallback) {
    if($Message -cin @('resource_projection_schema','resource_projection_sources','resource_projection_stale','resource_projection_amounts','resource_profile_missing','resource_source_reparse','global_config_invalid','global_config_drift','global_config_displaced_drift','global_config_postwrite_divergence','resource_deadline','redirected_swap_unsupported','unsupported_config_encoding','mixed_config_newlines','duplicate_config_section','duplicate_config_key','unsupported_config_syntax','unsupported_resource_unit','unsupported_processors','physical_capacity_unknown','distro_storage_unknown','distro_storage_unsupported','resource_storage_unknown')){return $Message}
    return $Fallback
}
# Windows resource ports. Only the explicit approved action writes global configuration.
function Get-PreparationResourceProjection($Options) {
    $projection=Get-Content -Raw -LiteralPath (Join-Path $Options.RepositoryRoot 'tools/windows/preparation/resource-projection.json') | ConvertFrom-Json
    if($projection.schema_version -ne 1){throw 'resource_projection_schema'}
    $expected=@('src/tiny_swarm_world/domain/preflight/resources.py','src/tiny_swarm_world/domain/host_environment.py','infra/config/node-providers/provider_config.yaml')
    if((@($projection.sources.PSObject.Properties.Name | Sort-Object) -join '|') -cne (($expected | Sort-Object) -join '|')){throw 'resource_projection_sources'}
    foreach($source in $projection.sources.PSObject.Properties){
        $path=Join-Path $Options.RepositoryRoot $source.Name
        $component=$Options.RepositoryRoot
        foreach($part in $source.Name.Split('/')){$component=Join-Path $component $part;if((Get-Item -LiteralPath $component -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'resource_source_reparse'}}
        if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $source.Value){throw 'resource_projection_stale'}
    }
    $profile=$projection.profiles.($Options.ServiceProfile)
    if(!$profile){throw 'resource_profile_missing'}
    foreach($amounts in @($profile,$projection.node_budget)){
        foreach($key in @('memory_gib','processors','disk_gib')){
            $value=$amounts.$key
            if(($value -isnot [int] -and $value -isnot [long]) -or $value -le 0 -or $value -gt 1048576){throw 'resource_projection_amounts'}
        }
    }
    return @{profile=$profile;node_budget=$projection.node_budget}
}
function Get-PreparationConfigSnapshot($Path) {
    Assert-PreparationLocalPath $Path
    Assert-PreparationResourcePath $Path
    if(!(Test-Path -LiteralPath $Path)){return @{hash='absent';metadata='absent'}}
    $item=Get-Item -LiteralPath $Path -Force
    if($item.PSIsContainer -or $item.Length -gt 1048576){throw 'global_config_invalid'}
    $acl=Get-Acl -LiteralPath $Path
    return @{hash=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant();metadata=($acl.Sddl+'|'+$item.Attributes+'|'+$item.CreationTimeUtc.Ticks+'|'+$item.LastWriteTimeUtc.Ticks+'|'+$item.Length)}
}
function Get-PreparationResourceInventoryCore($Options,$Facts) {
    $resource=@{projection_valid=$false;storage_known=$false;config_safe=$false;effective_known=$false}
    try {
        $projection=Get-PreparationResourceProjection $Options
        $resource.projection_valid=$true;$resource.profile=$projection.profile;$resource.node_budget=$projection.node_budget
        $probe=Invoke-PreparationProcess (Get-PreparationExecutable 'powershell.exe') @('-NoProfile','-NonInteractive','-Command', '$ErrorActionPreference="Stop";$s=Get-CimInstance Win32_ComputerSystem;@{memory=[long]$s.TotalPhysicalMemory;cpu=[int]$s.NumberOfLogicalProcessors}|ConvertTo-Json -Compress') $Options.ProbeTimeoutSeconds
        if($probe.exit_code -ne 0){throw 'physical_capacity_unknown'}
        $physical=$probe.stdout | ConvertFrom-Json
        $resource.physical_memory_bytes=$physical.memory;$resource.logical_processors=$physical.cpu
        $profile=[Environment]::GetFolderPath('UserProfile')
        $local=[Environment]::GetFolderPath('LocalApplicationData')
        if(!$env:USERPROFILE -or $env:USERPROFILE.TrimEnd('\') -ine $profile.TrimEnd('\') -or !$env:LOCALAPPDATA -or $env:LOCALAPPDATA.TrimEnd('\') -ine $local.TrimEnd('\')){throw 'resource_profile_unknown'}
        $path=Join-Path $profile '.wslconfig'
        $resource.config_snapshot=Get-PreparationConfigSnapshot $path
        $bytes=[byte[]]@();if(Test-Path -LiteralPath $path){$bytes=[IO.File]::ReadAllBytes($path)}
        $parsed=ConvertFrom-PreparationWslConfig $bytes
        $resource.config_values=@{};foreach($key in @('memory','processors','swap')){if($parsed.managed.ContainsKey($key)){$resource.config_values[$key]=$parsed.managed[$key]}};$resource.config_safe=$true
        # Registry BasePath is authoritative for the selected registration. Never guess C:.
        $registrations=@(Get-ChildItem -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' | ForEach-Object{Get-ItemProperty -LiteralPath $_.PSPath} | Where-Object{$_.DistributionName -ceq $Options.Distro})
        if($registrations.Count -ne 1){throw 'distro_storage_unknown'}
        $base=[string]$registrations[0].BasePath
        if($base.StartsWith('\\?\')){$base=$base.Substring(4)}
        if($base -notmatch '^[A-Za-z]:\\' -or $base.Contains('..')){throw 'distro_storage_unsupported'}
        Assert-PreparationLocalPath $base
        Assert-PreparationResourcePath $base
        if(!(Test-Path -LiteralPath $base -PathType Container)){throw 'distro_storage_unknown'}
        $vhdName=$registrations[0].VhdFileName
        if(!$vhdName){$vhdName='ext4.vhdx'}
        if($vhdName -notmatch '^[A-Za-z0-9_.-]+\.vhdx$'){throw 'distro_storage_unsupported'}
        $vhd=Join-Path $base $vhdName
        Assert-PreparationResourcePath $vhd
        if(!(Test-Path -LiteralPath $vhd -PathType Leaf)){throw 'distro_storage_unknown'}
        $persisted=(Get-ItemProperty -LiteralPath 'HKCU:\Environment' -ErrorAction Stop).TEMP
        if(!$persisted){$persisted=Join-Path $local 'Temp'}
        $persisted=[Environment]::ExpandEnvironmentVariables([string]$persisted)
        if($persisted.Contains('%') -or !$env:TEMP -or !$env:TMP -or $persisted.TrimEnd('\') -ine $env:TEMP.TrimEnd('\') -or $persisted.TrimEnd('\') -ine $env:TMP.TrimEnd('\')){throw 'swap_storage_unknown'}
        $swap=Join-Path $env:TEMP 'swap.vhdx'
        Assert-PreparationLocalPath $swap
        Assert-PreparationResourcePath $swap
        $distroVolume=Get-Volume -FilePath $base -ErrorAction Stop
        $swapVolume=Get-Volume -FilePath (Split-Path -Parent $swap) -ErrorAction Stop
        if(!$distroVolume.UniqueId -or !$swapVolume.UniqueId -or $distroVolume.FileSystem -ne 'NTFS' -or $swapVolume.FileSystem -ne 'NTFS'){throw 'resource_storage_unknown'}
        $resource.distro_volume=$distroVolume.UniqueId;$resource.swap_volume=$swapVolume.UniqueId
        $resource.distro_free_bytes=[long]$distroVolume.SizeRemaining;$resource.swap_free_bytes=[long]$swapVolume.SizeRemaining;$resource.storage_known=$true
        if($Facts.running){
            $script=Get-Content -Raw -LiteralPath (Join-Path $Options.RepositoryRoot 'tools/windows/preparation/linux-resources.sh')
            $effective=Invoke-PreparationProcess (Get-PreparationExecutable 'wsl.exe') @('--distribution',$Options.Distro,'--exec','/bin/sh','-s') $Options.ProbeTimeoutSeconds $script
            $observed=ConvertFrom-PreparationEffectiveResources $effective
            if($observed){foreach($key in $observed.Keys){$resource[$key]=$observed[$key]};$resource.effective_known=$true}
        }
    }catch{$resource.cause=Get-PreparationResourceCause $_.Exception.Message 'resource_inventory_failed'}
    return $resource
}
function Invoke-PreparationResourceAction($Action,$Options,$Facts,$Store) {
    $path=Join-Path ([Environment]::GetFolderPath('UserProfile')) '.wslconfig'
    return Set-PreparationResourceConfig $path $Facts.resource_facts.config_snapshot $Action.after $Store $Options.ActionTimeoutSeconds $Options
}
function Set-PreparationResourceConfigCore($Path,$Approved,$Allocation,$Store,[int]$TimeoutSeconds) {
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $lock=$null;$temporary=$null;$backup=$null;$displaced=$null;$replaced=$false;$replacementAttempted=$false
    function Assert-ResourceDeadline {if($clock.Elapsed.TotalSeconds -ge $TimeoutSeconds){throw 'resource_deadline'}}
    function Assert-ResourceSnapshot {
        Assert-ResourceDeadline
        $fresh=Get-PreparationConfigSnapshot $Path
        if($fresh.hash -cne $Approved.hash -or $fresh.metadata -cne $Approved.metadata){throw 'global_config_drift'}
    }
    try {
        Assert-ResourceSnapshot
        $lockPath=Join-Path (Split-Path -Parent $Path) '.tsw-wslconfig.lock'
        Assert-PreparationResourcePath $lockPath
        $lock=New-Object IO.FileStream($lockPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
        Set-PreparationPrivateAcl $lockPath
        Assert-ResourceSnapshot
        $bytes=[byte[]]@();if($Approved.hash -ne 'absent'){$bytes=[IO.File]::ReadAllBytes($Path)}
        $parsed=ConvertFrom-PreparationWslConfig $bytes
        $merged=ConvertTo-PreparationWslConfig $parsed $Allocation
        $directory=Split-Path -Parent $Path
        $temporary=Join-Path $directory ('.tsw-wslconfig-'+[guid]::NewGuid().ToString('N')+'.tmp')
        $file=New-Object IO.FileStream($temporary,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        Set-PreparationPrivateAcl $temporary
        try{$file.Write($merged,0,$merged.Length);$file.Flush($true)}finally{$file.Dispose()}
        if($Approved.hash -ne 'absent'){
            $acl=Get-Acl -LiteralPath $Path
            $preserved=New-Object Security.AccessControl.FileSecurity
            $preserved.SetSecurityDescriptorSddlForm($acl.Sddl,([Security.AccessControl.AccessControlSections]::Access -bor [Security.AccessControl.AccessControlSections]::Owner -bor [Security.AccessControl.AccessControlSections]::Group))
            [IO.File]::SetAccessControl($temporary,$preserved)
            $item=Get-Item -LiteralPath $Path -Force
            [IO.File]::SetCreationTimeUtc($temporary,$item.CreationTimeUtc)
            [IO.File]::SetAttributes($temporary,$item.Attributes)
            $backup=Join-Path $Store ('wslconfig-'+[guid]::NewGuid().ToString('N')+'.backup')
            Assert-PreparationEvidencePath $Store
            $copy=New-Object IO.FileStream($backup,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
            Set-PreparationPrivateAcl $backup
            try{$copy.Write($bytes,0,$bytes.Length);$copy.Flush($true)}finally{$copy.Dispose()}
            Write-PreparationEvidence $Store @{event='backup_metadata';backup_path=$backup;original_acl=$acl.Sddl;original_metadata=$Approved.metadata}
            [IO.File]::SetCreationTimeUtc($backup,$item.CreationTimeUtc)
            [IO.File]::SetLastWriteTimeUtc($backup,$item.LastWriteTimeUtc)
            [IO.File]::SetAttributes($backup,$item.Attributes)
            Assert-PreparationEvidencePath $backup
        }
        # Final comparison protects cooperating TSW writers, not an OS CAS for arbitrary editors.
        Assert-ResourceSnapshot
        if($Approved.hash -ne 'absent'){$displaced=Join-Path $directory ('.tsw-displaced-'+[guid]::NewGuid().ToString('N')+'.backup')}
        $replacementAttempted=$true
        Invoke-PreparationConfigReplacement $temporary $Path $displaced
        $temporary=$null;$replaced=$true
        if($displaced){
            $displacedSnapshot=Get-PreparationConfigSnapshot $displaced
            Set-PreparationPrivateAcl $displaced
            if($displacedSnapshot.metadata -cne $Approved.metadata){throw 'global_config_displaced_drift'}
            $displacedHash=(Get-FileHash -LiteralPath $displaced -Algorithm SHA256).Hash.ToLowerInvariant()
            if($displacedHash -cne $Approved.hash){throw 'global_config_displaced_drift'}
        }
        Assert-ResourceDeadline
        $after=Get-PreparationConfigSnapshot $Path
        $expected=[Security.Cryptography.SHA256]::Create()
        try{$hash=([BitConverter]::ToString($expected.ComputeHash($merged))).Replace('-','').ToLowerInvariant()}finally{$expected.Dispose()}
        if($after.hash -cne $hash){throw 'global_config_postwrite_divergence'}
        return @{confirmed=$true;uncertain=$false;exit_code=0;observations=@{config_hash=$after.hash;backup_path=$backup;displaced_backup=$displaced;backup_hash=$Approved.hash;restart_required=$true}}
    }catch{
        $cause=Get-PreparationResourceCause $_.Exception.Message 'global_config_action_failed'
        $uncertain=$replaced -or $replacementAttempted
        if($replacementAttempted -and !$replaced){try{$current=Get-PreparationConfigSnapshot $Path;if($current.hash -ceq $Approved.hash -and $current.metadata -ceq $Approved.metadata -and (!$displaced -or !(Test-Path -LiteralPath $displaced))){$uncertain=$false}}catch{}}
        return @{confirmed=$false;uncertain=$uncertain;exit_code=$(if($_.Exception.Message -eq 'resource_deadline'){124}else{1});cause=$cause;observations=@{backup_path=$backup;displaced_backup=$displaced;backup_hash=$Approved.hash}}}
    finally{try{if($temporary -and (Test-Path -LiteralPath $temporary)){Remove-Item -LiteralPath $temporary -Force}}catch{};if($lock){try{$lock.Dispose()}catch{};try{Remove-Item -LiteralPath $lockPath -Force}catch{}}}
}
function Assert-PreparationResourcePath($Path) {
    $ancestor=$Path
    while(!(Test-Path -LiteralPath $ancestor)){$ancestor=Split-Path -Parent $ancestor;if(!$ancestor){throw 'resource_parent_unknown'}}
    Assert-PreparationEvidencePath $ancestor
}
function Assert-PreparationLocalPath($Path) {
    if($Path -notmatch '^[A-Za-z]:\\' -or $Path.Contains('..')){throw 'resource_path_unsupported'}
    $volume=Get-Volume -FilePath ([IO.Path]::GetPathRoot($Path)) -ErrorAction Stop
    if($volume.FileSystem -ne 'NTFS' -or $volume.DriveType -ne 'Fixed'){throw 'resource_path_unsupported'}
}
function Set-PreparationPrivateAcl($Path) {
    $acl=New-Object Security.AccessControl.FileSecurity
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl.SetOwner($sid);$acl.SetAccessRuleProtection($true,$false)
    foreach($principal in @($sid.Value,'S-1-5-18','S-1-5-32-544')){
        $rule=New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier($principal)),'FullControl','Allow')
        [void]$acl.AddAccessRule($rule)
    }
    [IO.File]::SetAccessControl($Path,$acl)
}
function Invoke-PreparationResourceHost($Options,$Request,[int]$TimeoutSeconds) {
    $helper=Join-Path $Options.RepositoryRoot 'tools/windows/preparation/ResourceHost.ps1'
    $process=Invoke-PreparationProcess (Get-PreparationExecutable 'powershell.exe') @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$helper) $TimeoutSeconds ($Request | ConvertTo-Json -Depth 30 -Compress)
    if($process.exit_code -in @(124,130)){if($Request.mode -eq 'apply'){return @{confirmed=$false;uncertain=$true;exit_code=$process.exit_code;cause='resource_host_deadline'}};throw 'resource_host_deadline'}
    if($process.exit_code -ne 0 -or ![string]::IsNullOrEmpty($process.stderr)){throw 'resource_host_failed'}
    return ConvertTo-PreparationHashtable ($process.stdout | ConvertFrom-Json)
}
function Get-PreparationResourceInventory($Options,$Facts) {
    try{return Invoke-PreparationResourceHost $Options @{mode='inventory';options=$Options;facts=$Facts} $Options.ProbeTimeoutSeconds}catch{return @{projection_valid=$false;storage_known=$false;config_safe=$false;effective_known=$false;cause='resource_inventory_failed'}}
}
function Set-PreparationResourceConfig($Path,$Approved,$Allocation,$Store,[int]$TimeoutSeconds,$Options) {
    return Invoke-PreparationResourceHost $Options @{mode='apply';path=$Path;approved=$Approved;allocation=$Allocation;store=$Store;timeout=$TimeoutSeconds} $TimeoutSeconds
}

function ConvertTo-PreparationHashtable($Value) {
    if($Value -is [Management.Automation.PSCustomObject]){$map=@{};foreach($p in $Value.PSObject.Properties){$map[$p.Name]=ConvertTo-PreparationHashtable $p.Value};return $map}
    if($Value -is [Array]){return ,@($Value | ForEach-Object{ConvertTo-PreparationHashtable $_})}
    return $Value
}

function Invoke-PreparationConfigReplacement($Temporary,$Path,$Displaced) {
    if($Displaced){[IO.File]::Replace($Temporary,$Path,$Displaced)}else{[IO.File]::Move($Temporary,$Path)}
}
