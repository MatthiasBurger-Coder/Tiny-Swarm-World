# All host-dependent operations are isolated here; application consumes ports.
function Invoke-PreparationProcess {
    param([string]$File, [string[]]$Arguments, [int]$TimeoutSeconds, [string]$InputText='')
    if ($TimeoutSeconds -le 0) {throw 'invalid_timeout'}
    $info=New-Object Diagnostics.ProcessStartInfo
    $info.FileName=$File
    $info.UseShellExecute=$false
    $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true
    $info.RedirectStandardError=$true
    $info.RedirectStandardInput=$true
    # WSL parses raw option tokens; quoting every flag turns --version into a Linux command.
    # Quote other arguments using CommandLineToArgvW, preserving quotes/trailing slashes.
    $encoded=foreach ($arg in $Arguments) {
        if($arg -cmatch '\A[A-Za-z0-9_./:=+-]+\z') {$arg}
        else {'"'+([regex]::Replace(([regex]::Replace($arg,'(\\*)"','$1$1\"')),'(\\+)$','$1$1'))+'"'}
    }
    $info.Arguments=$encoded -join ' '
    $process=New-Object Diagnostics.Process
    $process.StartInfo=$info
    $processDeadline=[Diagnostics.Stopwatch]::StartNew()
    function Get-ProcessRemainingMilliseconds {return [Math]::Max(0,($TimeoutSeconds*1000)-[int]$processDeadline.ElapsedMilliseconds)}
    try {
        [void]$process.Start()
        $stdout=$process.StandardOutput.ReadToEndAsync()
        $stderr=$process.StandardError.ReadToEndAsync()
        if ($InputText) {
            $inputTask=$process.StandardInput.WriteAsync($InputText)
            if(!$inputTask.Wait((Get-ProcessRemainingMilliseconds))){try{$process.Kill()}catch{}
            return @{exit_code=124
            stdout=''
            stderr='stdin_timeout'}}
        }
        $process.StandardInput.Close()
        if (!$process.WaitForExit((Get-ProcessRemainingMilliseconds))) {try{$process.Kill()}catch{}
        return @{exit_code=124
        stdout=''
        stderr='timeout'}}
        if(![Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($stdout,$stderr),(Get-ProcessRemainingMilliseconds))){return @{exit_code=124
        stdout=''
        stderr='output_timeout'}}
        return @{exit_code=$process.ExitCode
        stdout=$stdout.Result
        stderr=$stderr.Result}
    } catch [Management.Automation.PipelineStoppedException] {
        try{$process.Kill()}catch{}
        return @{exit_code=130
        stdout=''
        stderr='interrupted'}
    } finally {$process.Dispose()}
}
function Get-PreparationSource($Options) {
    $assets=@('install.sh','prepare_linux.sh','tools/windows/preparation/Handoff.ps1','tools/windows/preparation/linux-handoff.sh','prepare_windows.ps1','tools/windows/preparation/Preparation.psm1','tools/windows/preparation/Policy.ps1','tools/windows/preparation/Application.ps1','tools/windows/preparation/Adapters.ps1','tools/windows/preparation/linux-config.sh','tools/windows/preparation/Download.ps1','tools/windows/preparation/SourceProof.ps1','tools/windows/preparation/Resources.ps1','tools/windows/preparation/ResourceAdapters.ps1','tools/windows/preparation/ResourceHost.ps1','tools/windows/preparation/linux-resources.sh','tools/windows/preparation/resource-projection.json','src/tiny_swarm_world/domain/preflight/resources.py','src/tiny_swarm_world/domain/host_environment.py','infra/config/node-providers/provider_config.yaml','tools/build_wsl_resource_projection.py','tools/windows/preparation/Bridge.ps1','tools/windows/tws-wsl-bridge.ps1','tools/windows/tws-wsl-bridge-service.ps1','tools/windows/tws-wsl-bridge.config.json','infra/config/ports.yaml')
    $hashes=[ordered]@{}
    foreach($asset in $assets){$path=Join-Path $Options.RepositoryRoot $asset
    if(!(Test-Path -LiteralPath $path -PathType Leaf)){return @{verified=$false
    clean=$false
    revision=$null
    asset=$asset}}
    $componentPath=$Options.RepositoryRoot
    $rootItem=Get-Item -LiteralPath $componentPath -Force
    if($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint){return @{verified=$false;clean=$false;revision=$null;cause='source_reparse'}}
    foreach($component in $asset.Split('/')){
        $componentPath=Join-Path $componentPath $component
        $item=Get-Item -LiteralPath $componentPath -Force
        if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){return @{verified=$false;clean=$false;revision=$null;cause='source_reparse'}}
    }
    if($item.PSIsContainer -or $item.Length -gt 4194304){return @{verified=$false;clean=$false;revision=$null;cause='source_asset_invalid'}}
    $hashes[$asset]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
    $git=$null
    foreach($candidate in @((Join-Path ([Environment]::GetFolderPath('ProgramFiles')) 'Git/cmd/git.exe'),(Join-Path ([Environment]::GetFolderPath('ProgramFiles')) 'Git/bin/git.exe'))){
        if(Test-Path -LiteralPath $candidate -PathType Leaf){
            $git=@{Source=$candidate}
            break
        }
    }
    if($git){
        $revision=Invoke-PreparationProcess $git.Source @('--no-optional-locks','-c','core.fsmonitor=false','-c','core.untrackedCache=false','-C',$Options.RepositoryRoot,'rev-parse','HEAD') $Options.ProbeTimeoutSeconds
        $safeGit=@('--no-optional-locks','-c','core.fsmonitor=false','-c','core.untrackedCache=false')
        $filterKeys=Invoke-PreparationProcess $git.Source ($safeGit+@('-C',$Options.RepositoryRoot,'config','--name-only','--get-regexp','^filter\..*\.(clean|process|required)$')) $Options.ProbeTimeoutSeconds
        if($filterKeys.exit_code -notin @(0,1)){return @{verified=$false;clean=$false;revision=$null;cause='filter_inventory_unknown'}}
        foreach($key in ($filterKeys.stdout -split '\r?\n' | Where-Object{$_})) {
            if($key -notmatch '^filter\.[A-Za-z0-9_.-]+\.(clean|process|required)$'){return @{verified=$false;clean=$false;revision=$null;cause='unsafe_filter_name'}}
            $value='';if($key -match '\.required$'){$value='false'}
            $safeGit+=@('-c',($key+'='+$value))
        }
        $dirty=Invoke-PreparationProcess $git.Source ($safeGit+@('-C',$Options.RepositoryRoot,'status','--porcelain','--untracked-files=all','--ignore-submodules=all')) $Options.ProbeTimeoutSeconds
        if($revision.exit_code -eq 0 -and $dirty.exit_code -eq 0){
            $assetsMatch=$true
            foreach($asset in $assets){
                $current=Get-Item -LiteralPath $Options.RepositoryRoot -Force
                if($current.Attributes -band [IO.FileAttributes]::ReparsePoint){$assetsMatch=$false}
                $componentPath=$Options.RepositoryRoot
                foreach($component in $asset.Split('/')) {
                    $componentPath=Join-Path $componentPath $component
                    $current=Get-Item -LiteralPath $componentPath -Force
                    if($current.Attributes -band [IO.FileAttributes]::ReparsePoint){$assetsMatch=$false}
                }
                if($current.PSIsContainer){$assetsMatch=$false}
                $mode=Invoke-PreparationProcess $git.Source ($safeGit+@('-C',$Options.RepositoryRoot,'ls-tree','HEAD','--',$asset)) $Options.ProbeTimeoutSeconds
                if($mode.exit_code -ne 0 -or $mode.stdout -cnotmatch '^(100644|100755) blob [0-9a-f]{40}\t'){$assetsMatch=$false}
                $expected=Invoke-PreparationProcess $git.Source @('--no-optional-locks','-c','core.fsmonitor=false','-C',$Options.RepositoryRoot,'rev-parse',('HEAD:'+$asset)) $Options.ProbeTimeoutSeconds
                $actual=Invoke-PreparationProcess $git.Source @('--no-optional-locks','-C',$Options.RepositoryRoot,'hash-object','--no-filters','--',(Join-Path $Options.RepositoryRoot $asset)) $Options.ProbeTimeoutSeconds
                if($expected.exit_code -ne 0 -or $actual.exit_code -ne 0 -or $expected.stdout.Trim() -cne $actual.stdout.Trim()){$assetsMatch=$false}
            }
            return @{verified=($assetsMatch -and $revision.stdout.Trim() -match '^[0-9a-f]{40}$')
            clean=($assetsMatch -and [string]::IsNullOrWhiteSpace($dirty.stdout))
            revision=$revision.stdout.Trim()
            assets=$hashes}
        }
    }
    if(Test-Path -LiteralPath (Join-Path $Options.RepositoryRoot '.git')){return @{verified=$false
    clean=$false
    revision=$null
    assets=$hashes}}
    return Test-PreparationReleaseProof -RepositoryRoot $Options.RepositoryRoot -Assets $assets -ExpectedRevision $Options.QualificationRevision
}

function Get-PreparationExecutable($Name) {
    if($Name -notin @('powershell.exe','dism.exe','msiexec.exe','wsl.exe')){throw 'invalid_executable'}
    $base=[Environment]::GetFolderPath('System')
    if($Name -eq 'powershell.exe'){return Join-Path $base 'WindowsPowerShell/v1.0/powershell.exe'}
    return Join-Path $base $Name
}
function Get-PreparationInventory($Options) {
    $inventoryDeadline=[Diagnostics.Stopwatch]::StartNew()
    function Get-InventoryRemaining {
        if($Options.OverallTimeoutSeconds){
            $remaining=$Options.OverallTimeoutSeconds-[int][Math]::Ceiling($inventoryDeadline.Elapsed.TotalSeconds)
            if($remaining -le 0){throw 'inventory_deadline_exceeded'}
            return [Math]::Min($remaining,$Options.ProbeTimeoutSeconds)
        }
        return $Options.ProbeTimeoutSeconds
    }
    $facts=[ordered]@{platform=$(if([Environment]::OSVersion.Platform -eq 'Win32NT'){'Windows'}else{'unsupported'})
    host_identity=[Environment]::MachineName
    product_type=0
    build=0
    architecture=$env:PROCESSOR_ARCHITECTURE
    elevated=$false
    virtualization=$null
    features_known=$false
    features_missing=@()
    reboot_pending=$false
    wsl_present=$null
    wsl_version=$null
    install_capable=$false
    distro_present=$null
    running=$false
    linux_known=$false}
    $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
    $facts.elevated=(New-Object Security.Principal.WindowsPrincipal($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    # Bounded native PowerShell CIM/DISM probes, not unbounded in-process calls.
    $probe=Invoke-PreparationProcess (Get-PreparationExecutable 'powershell.exe') @('-NoProfile','-NonInteractive','-Command', '$ErrorActionPreference="Stop"; $o=Get-CimInstance Win32_OperatingSystem; $c=Get-CimInstance Win32_Processor; $s=Get-CimInstance Win32_ComputerSystem; @{build=[int]$o.BuildNumber;product_type=[int]$o.ProductType;firmware_values=@($c | ForEach-Object {$_.VirtualizationFirmwareEnabled});hypervisor_present=$s.HypervisorPresent;architecture=$(if(@($c).Count -gt 0 -and @($c | Where-Object {$_.Architecture -ne 9}).Count -eq 0){"AMD64"}else{"unsupported"});features=@()} | ConvertTo-Json -Depth 5 -Compress') (Get-InventoryRemaining)
    if($probe.exit_code -ne 0){throw 'host_inventory_unavailable'}
    $hostFacts=$probe.stdout | ConvertFrom-Json
    $facts.architecture=$hostFacts.architecture
    $facts.build=$hostFacts.build
    $facts.product_type=$hostFacts.product_type
    $virtualization=Get-PreparationVirtualization $hostFacts
    $facts.virtualization=$virtualization.available
    $facts.virtualization_known=$virtualization.known
    $facts.firmware_virtualization=$virtualization.firmware_enabled
    $facts.hypervisor_present=$virtualization.hypervisor_present
    $facts.features_known=$true
    $hostFacts.features=@()
    $facts.feature_states=@{}
    foreach($featureName in @('Microsoft-Windows-Subsystem-Linux','VirtualMachinePlatform')) {
        $featureProbe=Invoke-PreparationProcess (Get-PreparationExecutable 'dism.exe') @('/Online','/English','/Get-FeatureInfo',('/FeatureName:'+$featureName),'/LogPath:NUL') (Get-InventoryRemaining)
        if($featureProbe.exit_code -ne 0 -or $featureProbe.stdout -notmatch '(?m)^State\s*:\s*(Enabled|Disabled|Enable Pending|Disable Pending)\s*$') {$facts.features_known=$false
        continue}
        $hostFacts.features+=@{FeatureName=$featureName
        State=$Matches[1]}
        $facts.feature_states[$featureName]=$Matches[1]
    }
    foreach($feature in $hostFacts.features){if($feature.State -eq 5 -or $feature.State -eq 'Enable Pending'){$facts.reboot_pending=$true}
    if($feature.State -ne 2 -and $feature.State -ne 'Enabled'){$facts.features_missing+= $feature.FeatureName}}
    $facts.reboot_pending=$facts.reboot_pending -or (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')
    $wslPath=Get-PreparationExecutable 'wsl.exe'
    $wsl=$null
    if(Test-Path -LiteralPath $wslPath){$wsl=@{Source=$wslPath}}
    if(!$wsl){$facts.wsl_present=$false
    return $facts}
    $version=Invoke-PreparationProcess $wsl.Source @('--version') (Get-InventoryRemaining)
    if($version.exit_code -ne 0){
        # Inbox WSL without readable modern version is unsupported, not absent.
        $packageProbe=Invoke-PreparationProcess (Get-PreparationExecutable 'powershell.exe') @('-NoProfile','-NonInteractive','-Command', '@{msi=(Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Lxss\MSI");store=@(Get-AppxPackage -Name MicrosoftCorporationII.WindowsSubsystemForLinux -ErrorAction Stop).Count} | ConvertTo-Json -Compress') (Get-InventoryRemaining)
        if($packageProbe.exit_code -eq 0){$package=$packageProbe.stdout | ConvertFrom-Json
        if($package.msi -is [bool] -and $package.store -is [int] -and !$package.msi -and $package.store -eq 0){$facts.wsl_present=$false
        return $facts}}
        $facts.wsl_present=$true
        return $facts
    }
    $facts.wsl_present=$true
    if(($version.stdout -replace "`0",'') -match '(?m)^.*?:\s*(\d+\.\d+\.\d+)(?:\.\d+)?\s*$'){$facts.wsl_version=$Matches[1]}
    $help=Invoke-PreparationProcess $wsl.Source @('--help') (Get-InventoryRemaining)
    $facts.install_capable=Test-PreparationInstallCapabilities $help
    $list=Invoke-PreparationProcess $wsl.Source @('--list','--verbose') (Get-InventoryRemaining)
    $namesProbe=Invoke-PreparationProcess $wsl.Source @('--list','--quiet') (Get-InventoryRemaining)
    $running=Invoke-PreparationProcess $wsl.Source @('--list','--running','--quiet') (Get-InventoryRemaining)
    if($list.exit_code -ne 0 -or $running.exit_code -ne 0 -or $namesProbe.exit_code -ne 0){return $facts}
    $text=$list.stdout -replace "`0",''
    $name=[regex]::Escape($Options.Distro)
    $match=[regex]::Match($text,('(?m)^\s*\*?\s*'+$name+'\s+\S+\s+([12])\s*$'))
    $facts.registrations=@()
    foreach($line in ($text -split '\n')){if($line -match '^\s*(\*?)\s*(.+?)\s{2,}\S+\s+([12])\s*$'){$facts.registrations+=@{name=$Matches[2]
    generation=[int]$Matches[3]
    is_default=($Matches[1] -eq '*')}}}
    $registeredNames=@(($namesProbe.stdout -replace "`0",'') -split '\r?\n' | ForEach-Object{$_.Trim()} | Where-Object{$_})
    $facts.distro_inventory_known=((($registeredNames | Sort-Object) -join '|') -ceq ((@($facts.registrations | ForEach-Object{$_.name}) | Sort-Object) -join '|'))
    if(!$facts.distro_inventory_known){return $facts}
    $facts.distro_present=$registeredNames -ccontains $Options.Distro
    if($facts.distro_present -and !$match.Success){$facts.distro_inventory_known=$false
    return $facts}
    if(!$match.Success){return $facts}
    $facts.wsl_generation=[int]$match.Groups[1].Value
    $facts.running_registrations=@(($running.stdout -replace "`0",'') -split '\r?\n' | ForEach-Object{$_.Trim()} | Where-Object{$_})
    $facts.running=@(($running.stdout -replace "`0",'') -split '\r?\n' | ForEach-Object{$_.Trim()}) -contains $Options.Distro
    if(!$facts.running){return $facts}
    $uid=Invoke-PreparationProcess $wsl.Source @('--distribution',$Options.Distro,'--exec','id','-u') (Get-InventoryRemaining)
    $user=Invoke-PreparationProcess $wsl.Source @('--distribution',$Options.Distro,'--exec','id','-un') (Get-InventoryRemaining)
    $script=Get-Content -Raw -LiteralPath (Join-Path $Options.RepositoryRoot 'tools/windows/preparation/linux-config.sh')
    $linux=Invoke-PreparationProcess $wsl.Source @('--distribution',$Options.Distro,'--user','root','--exec','/bin/sh','-s','--','inspect') (Get-InventoryRemaining) $script
    if($uid.exit_code -ne 0 -or $user.exit_code -ne 0 -or $linux.exit_code -ne 0){return $facts}
    $facts.uid=[int]$uid.stdout.Trim()
    $facts.user=$user.stdout.Trim()
    foreach($line in ($linux.stdout -split '\n')){if($line -match '^([a-z0-9_]+)=(.*)$'){$value=$Matches[2].Trim()
    if($value -eq 'true'){$value=$true}elseif($value -eq 'false'){$value=$false}
    $facts[$Matches[1]]=$value}}
    $facts.linux_known=$true
    $facts.resource_facts=Get-PreparationResourceInventory $Options $facts
    $facts.bridge_facts=Get-PreparationBridgeInventory $Options $facts
    return $facts
}
function Get-PreparationHandoffInventory($Options,$Facts,$Source) {
    if($Facts.running -ne $true -or $Facts.pid1 -ne 'systemd' -or $Facts.uid -lt 1000 -or $Facts.user -cnotmatch '\A[a-z_][a-z0-9_-]{0,31}\z' -or !$Source.verified -or !$Source.clean){return @{handoff_ready=$false}}
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $running=Invoke-PreparationProcess (Get-PreparationExecutable 'wsl.exe') @('--list','--running','--quiet') $Options.ProbeTimeoutSeconds
    $names=@(($running.stdout -replace "`0",'') -split '\r?\n' | ForEach-Object{$_.Trim()} | Where-Object{$_})
    if($running.exit_code -ne 0 -or $names -cnotcontains $Options.Distro){return @{handoff_ready=$false}}
    $remaining=$Options.ProbeTimeoutSeconds-[int][Math]::Ceiling($clock.Elapsed.TotalSeconds)
    if($remaining -le 0){return @{handoff_ready=$false}}
    $script=Get-Content -Raw -LiteralPath (Join-Path $Options.RepositoryRoot 'tools/windows/preparation/linux-handoff.sh')
    $probe=Invoke-PreparationProcess (Get-PreparationExecutable 'wsl.exe') @('--distribution',$Options.Distro,'--user',$Facts.user,'--exec','/bin/sh','-s','--',[string]$Options.LinuxCheckout,$Source.revision) $remaining $script
    $result=@{handoff_ready=$false}
    if($probe.exit_code -eq 0){foreach($line in ($probe.stdout -split '\n')){if($line -match '^(handoff_ready|handoff_checkout)=(.*)$'){$result[$Matches[1]]=$(if($Matches[1] -eq 'handoff_ready'){$Matches[2].Trim() -ceq 'true'}else{$Matches[2].Trim()})}}}
    return $result
}
function Assert-PreparationEvidencePath($Path) {
    $current=$Path
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $managedRoot=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'TinySwarmWorld'
    $platformRoot=[IO.Path]::GetPathRoot($managedRoot)
    $first=$true
    $trustedInstaller='S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464'
    while($current -and (Test-Path -LiteralPath $current)) {
        $item=Get-Item -LiteralPath $current -Force
        if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'reparse_evidence_path'}
        $acl=Get-Acl -LiteralPath $current
        $owner=$acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
        $strict=$first -or $current.TrimEnd('\','/') -ieq $managedRoot.TrimEnd('\','/')
        $trustedOwners=@($sid,'S-1-5-18','S-1-5-32-544')
        if(!$strict -and $current.TrimEnd('\','/') -ieq $platformRoot.TrimEnd('\','/')){$trustedOwners+= $trustedInstaller}
        if($owner -notin $trustedOwners){throw 'foreign_evidence_owner'}
        # Existing ancestors may permit creation of harmless sibling directories.
        # They must not permit replacement/removal of an existing protected child.
        $writeMask=[Security.AccessControl.FileSystemRights]::Delete -bor [Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles -bor [Security.AccessControl.FileSystemRights]::ChangePermissions -bor [Security.AccessControl.FileSystemRights]::TakeOwnership
        if($strict) {
            $writeMask=$writeMask -bor [Security.AccessControl.FileSystemRights]::WriteData -bor [Security.AccessControl.FileSystemRights]::AppendData -bor [Security.AccessControl.FileSystemRights]::WriteAttributes -bor [Security.AccessControl.FileSystemRights]::WriteExtendedAttributes
        }
        foreach($rule in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
            $applies=!($rule.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly)
            if($applies -and $rule.AccessControlType -eq 'Allow' -and ($rule.FileSystemRights -band $writeMask) -and $rule.IdentityReference.Value -notin @($sid,'S-1-5-18','S-1-5-32-544','S-1-3-0')) {throw 'untrusted_evidence_acl'}
        }
        $first=$false
        $current=Split-Path -Parent $current
    }
}
function Test-PreparationEvidence($Options) {
    try {
        $path=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'TinySwarmWorld/preparation'
        while(!(Test-Path -LiteralPath $path)) {
            $path=Split-Path -Parent $path
            if(!$path){return $false}
        }
        Assert-PreparationEvidencePath $path
        return $true
    } catch {return $false}
}
function Protect-PreparationEvidence($Options) {
    $path=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'TinySwarmWorld/preparation'
    # Validate existing ancestors even when leaf does not yet exist.
    $ancestor=$path
    while(!(Test-Path -LiteralPath $ancestor)){$ancestor=Split-Path -Parent $ancestor
    if(!$ancestor){throw 'evidence_parent_missing'}}
    Assert-PreparationEvidencePath $ancestor
    [void][IO.Directory]::CreateDirectory($path)
    Assert-PreparationEvidencePath $path
    $acl=New-Object Security.AccessControl.DirectorySecurity
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl.SetOwner($sid)
    $acl.SetAccessRuleProtection($true,$false)
    foreach($principal in @($sid.Value,'S-1-5-18','S-1-5-32-544')){ $rule=New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier($principal)),'FullControl','ContainerInherit,ObjectInherit','None','Allow')
    [void]$acl.AddAccessRule($rule) }
    Set-Acl -LiteralPath $path -AclObject $acl
    return $path
}
function Write-PreparationEvidence($Path,$Record) {
    Assert-PreparationEvidencePath $Path
    $name=[guid]::NewGuid().ToString('N')
    $temporary=Join-Path $Path ($name+'.tmp')
    $final=Join-Path $Path ($name+'.json')
    try{[IO.File]::WriteAllText($temporary,($Record | ConvertTo-Json -Depth 12 -Compress), (New-Object Text.UTF8Encoding($false)))
    [IO.File]::Move($temporary,$final)}finally{if(Test-Path -LiteralPath $temporary){Remove-Item -LiteralPath $temporary -Force}}
}
function Invoke-PreparationAction($Action,$Options,$Facts,$Store) {
    $deadline=[Diagnostics.Stopwatch]::StartNew()
    $Options.ActionDeadline=$deadline
    function Get-PreparationRemaining {
        $remaining=$Options.ActionTimeoutSeconds-[int][Math]::Ceiling($deadline.Elapsed.TotalSeconds)
        if($remaining -le 0){throw 'action_deadline_exceeded'}
        return $remaining
    }
    $result=$null
    if($Action.id -in @('bridge_install','bridge_refresh')){return Invoke-PreparationBridgeAction $Action $Options $Facts $Store}
    if($Action.id -eq 'adapt_wsl_resources'){return Invoke-PreparationResourceAction $Action $Options $Facts $Store}
    if($Action.id -eq 'enable_features') {
        $allowed=@('Microsoft-Windows-Subsystem-Linux','VirtualMachinePlatform')
        foreach($feature in $Action.before){if($feature -notin $allowed){throw 'invalid_feature'}
        $result=Invoke-PreparationProcess (Get-PreparationExecutable 'dism.exe') @('/Online','/Enable-Feature',('/FeatureName:'+$feature),'/All','/NoRestart') (Get-PreparationRemaining)
        if($result.exit_code -notin @(0,3010)){return Get-PreparationObservedEffect $Action $Options $Facts $result.exit_code}}
    } elseif($Action.id -in @('install_wsl','install_distro')) {
        $artifacts=Get-PreparationArtifacts
        $artifact=$artifacts.wsl
        $extension='.msi'
        if($Action.id -eq 'install_distro'){$artifact=$artifacts[$Options.Distro]
        $extension='.wsl'}
        $download=Join-Path $Store ([guid]::NewGuid().ToString('N')+$extension)
        try {
            # Bounded download runs out of process; no implicit redirect/channel selection.
            $downloadScript=Join-Path $Options.RepositoryRoot 'tools/windows/preparation/Download.ps1'
            $result=Invoke-PreparationProcess (Get-PreparationExecutable 'powershell.exe') @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$downloadScript,'-Url',$artifact.url,'-Destination',$download,'-ExpectedSha256',$artifact.sha256) (Get-PreparationRemaining)
            if($result.exit_code -ne 0){
                $cause='artifact_transport_failed'
                try{$failure=$result.stdout | ConvertFrom-Json;if($failure.cause){$cause=$failure.cause}}catch{}
                return @{exit_code=$result.exit_code;confirmed=$false;uncertain=$false;cause=$cause}
            }
            try {$verification=$result.stdout | ConvertFrom-Json} catch {return @{exit_code=1;confirmed=$false;uncertain=$false;cause='artifact_verification_unknown'}}
            if($verification.verified -ne $true){return @{exit_code=1;confirmed=$false;uncertain=$false;cause=$verification.cause}}
            if($Action.id -eq 'install_wsl'){
                $result=Invoke-PreparationProcess (Get-PreparationExecutable 'msiexec.exe') @('/i',$download,'/qn','/norestart') (Get-PreparationRemaining)
            } else {$result=Invoke-PreparationProcess (Get-PreparationExecutable 'wsl.exe') @('--install','--from-file',$download,'--name',$Options.Distro,'--no-launch') (Get-PreparationRemaining)}
        }finally{if(Test-Path -LiteralPath $download){Remove-Item -LiteralPath $download -Force}}
    } elseif($Action.id -eq 'enable_systemd') {
        $script=Get-Content -Raw -LiteralPath (Join-Path $Options.RepositoryRoot 'tools/windows/preparation/linux-config.sh')
        $result=Invoke-PreparationProcess (Get-PreparationExecutable 'wsl.exe') @('--distribution',$Options.Distro,'--user','root','--exec','/bin/sh','-s','--','apply',$Facts.config_hash,$Facts.config_metadata) (Get-PreparationRemaining) $script
    } else {throw 'invalid_action'}
    if($result.exit_code -notin @(0,3010)){return Get-PreparationObservedEffect $Action $Options $Facts $result.exit_code}
    return Get-PreparationObservedEffect $Action $Options $Facts $result.exit_code
}
function Get-PreparationObservedEffect($Action,$Options,$Facts,$ExitCode) {
    # Return code alone never confirms a mutation.
    try{$observeOptions=@{}
    foreach($key in $Options.Keys){$observeOptions[$key]=$Options[$key]}
        if($Options.ActionDeadline){$remaining=$Options.ActionTimeoutSeconds-[int][Math]::Ceiling($Options.ActionDeadline.Elapsed.TotalSeconds)
        if($remaining -le 0){return @{exit_code=124
        confirmed=$false
        uncertain=$true}}
        $observeOptions.OverallTimeoutSeconds=$remaining}
        $after=Get-PreparationInventory $observeOptions
        $confirmed=$false
        if($Action.id -eq 'install_distro') {
            $beforeNames=@($Facts.registrations | ForEach-Object{ $_.name+':'+$_.generation+':'+$_.is_default })
            $afterNames=@($after.registrations | Where-Object{$_.name -ne $Options.Distro} | ForEach-Object{ $_.name+':'+$_.generation+':'+$_.is_default })
            if((($beforeNames | Sort-Object) -join '|') -cne (($afterNames | Sort-Object) -join '|')){return @{exit_code=1
            confirmed=$false
            uncertain=$true}}
        }
        switch($Action.id){'enable_features'{$confirmed=$after.features_known
        foreach($name in $Action.before){if($after.feature_states[$name] -notin @('Enabled','Enable Pending')){$confirmed=$false}}}
        'install_wsl'{$confirmed=$after.wsl_version -eq '3.0.1'}
        'install_distro'{$confirmed=$after.distro_present -and $after.wsl_generation -eq 2}
        'enable_systemd'{$confirmed=$after.systemd_configured -eq $true}}
        return @{exit_code=$ExitCode
        confirmed=[bool]$confirmed
        uncertain=(!$confirmed)
        observations=(Get-PreparationEvidenceFacts $after)}
    }catch{return @{exit_code=$ExitCode
    confirmed=$false
    uncertain=$true}}
}
function Get-PreparationStateIdentity($Options,$Facts,$Source) {
    return @{contract='bootstrap-v1';revision=$Source.revision;host=(Get-PreparationDigest $Facts.host_identity)
    distro=$Options.Distro;release=$Options.ExpectedRelease
    selection=(Get-PreparationDigest @($Options.ServiceProfile,$Options.WslMemoryGiB,$Options.WslProcessors,$Options.WslSwapGiB))}
}
function Read-PreparationState($Options,$Identity) {
    $path=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'TinySwarmWorld/preparation/bootstrap.state.json'
    if(!(Test-Path -LiteralPath $path)){return $null}
    Assert-PreparationEvidencePath $path
    $item=Get-Item -LiteralPath $path -Force
    if($item.PSIsContainer -or $item.Length -gt 262144){throw 'invalid_bootstrap_state'}
    $text=Get-Content -Raw -LiteralPath $path
    $names=@([regex]::Matches($text,'"([A-Za-z_]+)"\s*:') | ForEach-Object{$_.Groups[1].Value})
    if(@($names | Group-Object | Where-Object{$_.Count -gt 1}).Count -gt 0){throw 'duplicate_bootstrap_state_field'}
    $state=$text | ConvertFrom-Json
    Assert-PreparationState $state $Identity
    return $state
}
function Assert-PreparationState($State,$Identity) {
    $keys=@($State.PSObject.Properties.Name | Sort-Object)
    $expected=@('schema','identity','operation','stage','status','exit_code','confirmed','uncertain','timestamp_utc','versions','observation','restart','next_command' | Sort-Object)
    if(($keys -join '|') -cne ($expected -join '|')){throw 'invalid_bootstrap_state_fields'}
    if($State.schema -isnot [int] -or $State.schema -ne 1 -or $State.operation -isnot [string] -or $State.operation -cnotmatch '^[a-f0-9]{32}$' -or $State.stage -notin @('enable_features','install_wsl','install_distro','enable_systemd','adapt_wsl_resources','bridge_install','bridge_refresh') -or $State.status -notin @('pending','effect') -or $State.exit_code -isnot [int] -or $State.exit_code -lt 0 -or $State.exit_code -gt 3010 -or $State.confirmed -isnot [bool] -or $State.uncertain -isnot [bool] -or ($State.confirmed -and $State.uncertain) -or $State.observation -isnot [string] -or $State.observation -cnotmatch '^[a-f0-9]{64}$' -or $State.restart -notin @('none','login','distro','Windows','WSL-wide') -or $State.timestamp_utc -isnot [string] -or $State.timestamp_utc -cnotmatch '^\d{4}-\d{2}-\d{2}T[0-9:.]+Z$'){throw 'invalid_bootstrap_state'}
    if((@($State.identity.PSObject.Properties.Name | Sort-Object) -join '|') -cne 'contract|distro|host|release|revision|selection'){throw 'invalid_bootstrap_identity'}
    foreach($key in @('contract','revision','host','distro','release','selection')){if($State.identity.$key -isnot [string] -or $State.identity.$key -cne $Identity[$key]){throw 'stale_foreign_bootstrap_state'}}
    if((@($State.versions.PSObject.Properties.Name | Sort-Object) -join '|') -cne 'ubuntu|windows_build|wsl' -or $State.versions.windows_build -isnot [int] -or ($State.versions.wsl -and $State.versions.wsl -cnotmatch '^\d+\.\d+\.\d+$') -or ($State.versions.ubuntu -and $State.versions.ubuntu -cnotin @('24.04','26.04'))){throw 'invalid_bootstrap_versions'}
    if($State.next_command -isnot [string] -or $State.next_command -cnotmatch '^\./prepare_windows\.ps1 -Distro [A-Za-z0-9._-]+ -UbuntuRelease (?:24\.04|26\.04) -ServiceProfile (?:default|service-access) -Preflight(?: -Wsl(?:MemoryGiB|Processors|SwapGiB) [0-9]+)*$'){throw 'invalid_bootstrap_recovery_command'}
}
function Lock-PreparationState($Store) {
    Assert-PreparationEvidencePath $Store
    $path=Join-Path $Store 'bootstrap.lock'
    if(Test-Path -LiteralPath $path){Assert-PreparationEvidencePath $path}
    $stream=New-Object IO.FileStream($path,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try {Set-PreparationPrivateAcl $path;return $stream} catch {$stream.Dispose();throw}
}
function Write-PreparationState($Store,$Record) {
    Assert-PreparationEvidencePath $Store
    $path=Join-Path $Store 'bootstrap.state.json'
    $temporary=Join-Path $Store ('.bootstrap-'+[guid]::NewGuid().ToString('N')+'.tmp')
    try {
        Assert-PreparationState (($Record | ConvertTo-Json -Depth 12 -Compress) | ConvertFrom-Json) $Record.identity
        $stream=New-Object IO.FileStream($temporary,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try {
            Set-PreparationPrivateAcl $temporary
            $bytes=(New-Object Text.UTF8Encoding($false)).GetBytes(($Record | ConvertTo-Json -Depth 12 -Compress))
            $stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)
        } finally {$stream.Dispose()}
        if(Test-Path -LiteralPath $path){Assert-PreparationEvidencePath $path;[IO.File]::Replace($temporary,$path,$null)}
        else{[IO.File]::Move($temporary,$path)}
    } finally {if(Test-Path -LiteralPath $temporary){Remove-Item -LiteralPath $temporary -Force}}
}
function New-PreparationPorts {
    return @{EvidencePreflight=${function:Test-PreparationEvidence}
    Consent={param($Plan) $Plan | ConvertTo-Json -Depth 30 | Out-Host
    if([Environment]::UserInteractive){ return ((Read-Host 'Approve this exact preparation plan? Type yes') -ceq 'yes') }
    return $false}
    Inventory=${function:Get-PreparationInventory}
    HandoffInventory=${function:Get-PreparationHandoffInventory}
    SourceIdentity=${function:Get-PreparationSource}
    ProtectEvidence=${function:Protect-PreparationEvidence}
    WriteEvidence=${function:Write-PreparationEvidence}
    LockState=${function:Lock-PreparationState}
    ReadState=${function:Read-PreparationState}
    WriteState=${function:Write-PreparationState}
    Execute=${function:Invoke-PreparationAction}}
}
