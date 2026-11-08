#requires -Version 5.1
<# Source-bound prerequisite maintenance. Dot sourcing performs no host action. #>
[CmdletBinding()]
param([string]$ScenarioBase64='', [string]$ExpectedScenarioSha256='',
      [ValidateSet('Prepare','Execute','Recover')][string]$Mode='Prepare')
$ErrorActionPreference='Stop'

function Get-WslMaintenanceDigest($Value) {
    function Canonical($Item){
        if($null -eq $Item -or $Item -is [string] -or $Item -is [ValueType]){return $Item}
        if($Item -is [Collections.IDictionary]){
            $o=[ordered]@{};foreach($k in @($Item.Keys | Sort-Object)){$o[$k]=Canonical $Item[$k]};return $o
        }
        if($Item -is [Collections.IEnumerable]){return ,@($Item | ForEach-Object{Canonical $_})}
        $o=[ordered]@{};foreach($p in @($Item.PSObject.Properties | Sort-Object Name)){$o[$p.Name]=Canonical $p.Value};return $o
    }
    $bytes=[Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject (Canonical $Value) -Depth 100 -Compress))
    $hash=[Security.Cryptography.SHA256]::Create()
    try{return ([BitConverter]::ToString($hash.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}
    finally{$hash.Dispose()}
}

function Get-WslMaintenanceFirewallCommand {
    # Fixed source-only asset; no dynamic path, arguments, imports or sourcing.
    $path=Join-Path $PSScriptRoot 'windows_firewall_snapshot.ps1'
    $item=Get-Item -LiteralPath $path -Force
    if($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'FIREWALL_SOURCE_INVALID'}
    $stream=[IO.FileStream]::new($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try{
        $bytes=[byte[]]::new(65537);$length=0
        while($length -lt $bytes.Length){$read=$stream.Read($bytes,$length,($bytes.Length-$length));if($read -eq 0){break};$length+=$read}
        if($length -eq 0 -or $length -gt 65536){throw 'FIREWALL_SOURCE_BOUND'}
        if($length -ge 3 -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191){throw 'FIREWALL_SOURCE_INVALID'}
        $hash=[Security.Cryptography.SHA256]::Create()
        try{$actual=([BitConverter]::ToString($hash.ComputeHash($bytes,0,$length))).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose()}
        if($actual -cne 'a6a5aee14f32ada47cd14b58f59372fc0ba21ceaef64401d93b94822932c19e5'){throw 'FIREWALL_SOURCE_MISMATCH'}
        $text=([Text.UTF8Encoding]::new($false,$true)).GetString($bytes,0,$length)
        if($text.Contains("`0")){throw 'FIREWALL_SOURCE_INVALID'}
        return $text
    }finally{$stream.Dispose()}
}

function Assert-WslMaintenanceScenario($Scenario) {
    $fields=@('schema_version','source_commit','host','registration_sha256','repository_root',
        'guest_checkout','guest_helper_sha256','intent_sha256','recovery_reference','prestate_sha256',
        'memory_gib','processors','swap_gib')
    if($Scenario -isnot [Collections.IDictionary] -or $Scenario.Count -ne $fields.Count){throw 'SCENARIO_INVALID'}
    foreach($field in $fields){if(!$Scenario.Contains($field)){throw 'SCENARIO_INVALID'}}
    foreach($field in $Scenario.Keys){if($field -cnotin $fields){throw 'SCENARIO_INVALID'}}
    if($Scenario.schema_version -isnot [int] -or $Scenario.schema_version -ne 1 -or
        $Scenario.source_commit -isnot [string] -or $Scenario.source_commit -cnotmatch '\A[0-9a-f]{40}\z' -or
        $Scenario.host -isnot [string] -or $Scenario.host -cnotmatch '\A[A-Za-z0-9][A-Za-z0-9.-]{0,62}\z'){
        throw 'SCENARIO_INVALID'
    }
    foreach($field in @('registration_sha256','guest_helper_sha256','intent_sha256','prestate_sha256')){
        if($Scenario[$field] -isnot [string] -or $Scenario[$field] -cnotmatch '\A[0-9a-f]{64}\z'){throw 'SCENARIO_INVALID'}
    }
    foreach($field in @('memory_gib','processors','swap_gib')){
        if($Scenario[$field] -isnot [int]){throw 'SCENARIO_INVALID'}
    }
    if($Scenario.memory_gib -ne 21 -or $Scenario.processors -ne 8 -or $Scenario.swap_gib -ne 6){throw 'SCENARIO_INVALID'}
    if($Scenario.repository_root -isnot [string] -or $Scenario.repository_root -cnotmatch '\A[A-Za-z]:[\\/][^\x00-\x1f]{1,220}\z' -or
        $Scenario.guest_checkout -isnot [string] -or $Scenario.guest_checkout -cnotmatch '\A/root/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/checkout\z' -or
        $Scenario.recovery_reference -isnot [string] -or $Scenario.recovery_reference -cnotmatch '\A[A-Za-z0-9_.:-]{1,128}\z'){
        throw 'SCENARIO_INVALID'
    }
}

function Assert-WslMaintenanceResourcePlan($plan){
        $codes=@($plan.blockers | ForEach-Object{$_.code})
        if(@($plan.actions).Count -ne 1 -or $plan.actions[0].id -cne 'adapt_wsl_resources' -or
            @($plan.resources.blockers).Count -ne 0 -or
            $plan.resources.state -cne 'CHANGE_REQUIRED' -or $plan.resources.allocation.memory_gib -ne 21 -or
            $plan.resources.allocation.processors -ne 8 -or $plan.resources.allocation.swap_gib -ne 6 -or
            @($codes | Where-Object{$_ -cne 'prerequisite_missing'}).Count -ne 0 -or
            $plan.plan_fingerprint -cnotmatch '\A[0-9a-f]{64}\z'){throw 'RESOURCE_PLAN_INVALID'}
}

function Invoke-WslResourceMaintenance {
    param([Collections.IDictionary]$Scenario,[Collections.IDictionary]$Ports)
    # Mock ports are only a dot-sourced test seam. The executable entrypoint
    # always constructs production ports from the exact source-bound scenario.
    $summary=[ordered]@{schema_version=1;scope='WSL_RESOURCE_MAINTENANCE';status='BLOCKED';
        phase='ADMISSION';changed=$false;recovery_required=$false;resource_verified=$false;
        runtime_effect_attempted=$false;shutdown_attempted=$false;relaunch_attempted=$false;
        bridge_restored=$false;route_changes=0;services_verified=$false;error='NONE'}
    $update=$null;$reconcile=$null;$before=$null;$stopped=$false;$effectAttempted=$false
    try {
        Assert-WslMaintenanceScenario $Scenario
        foreach($name in @('Observe','Lock','Unlock','StopBridge','Plan','Apply','CheckPreservation',
            'Shutdown','Relaunch','Effective','Address','Routes','SetRoute','CommitState',
            'RestoreBridge','Final','Intent','BeginRecovery')){
            if(!$Ports.Contains($name) -or $Ports[$name] -isnot [scriptblock]){throw 'PORTS_INVALID'}
        }
        $before=& $Ports.Observe $Scenario
        if($before.admitted -isnot [bool] -or !$before.admitted -or
            $before.prestate_sha256 -cne $Scenario.prestate_sha256){throw 'PRESTATE_MISMATCH'}
        & $Ports.Intent $Scenario $before | Out-Null
        $summary.phase='QUIESCE'
        $update=& $Ports.Lock 'Global\TinySwarmWorldWslBridgeServiceUpdate' 30
        $reconcile=& $Ports.Lock 'Global\TinySwarmWorldWslBridgeReconcile' 30
        & $Ports.CheckPreservation $before 'ORIGINAL' | Out-Null
        if($before.bridge_running){$stopped=$true;$summary.runtime_effect_attempted=$true;& $Ports.StopBridge $before | Out-Null}
        & $Ports.CheckPreservation $before 'QUIESCED' | Out-Null
        $summary.phase='RESOURCE_PLAN'
        $plan=& $Ports.Plan $Scenario
        Assert-WslMaintenanceResourcePlan $plan
        & $Ports.CheckPreservation $before 'BEFORE_APPLY' | Out-Null
        $summary.phase='RESOURCE_APPLY';$effectAttempted=$true;$summary.runtime_effect_attempted=$true
        $effect=& $Ports.Apply $Scenario $plan.plan_fingerprint
        if($effect.result.exit_code -isnot [int] -or $effect.result.exit_code -ne 3 -or
            $effect.result.outcome -cne 'RESTART_REQUIRED' -or $effect.restart.scope -cne 'WSL-wide' -or
            $effect.result.changed -isnot [bool] -or !$effect.result.changed -or
            (@($effect.result.completed_actions) -join ',') -cne 'adapt_wsl_resources' -or
            @($effect.result.uncertain_actions).Count -ne 0){throw 'RESOURCE_APPLY_UNCERTAIN'}
        $summary.changed=$true
        & $Ports.CheckPreservation $before 'BEFORE_SHUTDOWN' | Out-Null
        $summary.phase='SHUTDOWN';$summary.shutdown_attempted=$true; & $Ports.Shutdown $Scenario | Out-Null
        $summary.phase='RELAUNCH';$summary.relaunch_attempted=$true; & $Ports.Relaunch $Scenario | Out-Null
        $summary.phase='EFFECTIVE'; & $Ports.Effective $Scenario $before | Out-Null
        $summary.resource_verified=$true
        $address=& $Ports.Address $Scenario $before
        $summary.phase='ROUTES'
        $changes=@(& $Ports.Routes $before $address)
        foreach($change in $changes){
            & $Ports.CheckPreservation $before 'BEFORE_ROUTE' | Out-Null
            & $Ports.SetRoute $before $change $address | Out-Null
            $summary.route_changes++
        }
        & $Ports.CommitState $before $address | Out-Null
        & $Ports.CheckPreservation $before 'FINAL' | Out-Null
        $summary.phase='RESTORE_BRIDGE'
        # Release Reconcile before starting the original service so its own
        # guarded loop can acquire that mutex. ServiceUpdate stays held.
        & $Ports.Unlock $reconcile | Out-Null;$reconcile=$null
        & $Ports.RestoreBridge $before | Out-Null;$stopped=$false
        $summary.bridge_restored=$true
        & $Ports.Final $Scenario $before | Out-Null
        $summary.status='MAINTENANCE_COMPLETE';$summary.phase='COMPLETE'
    } catch {
        $summary.error='MAINTENANCE_REFUSED_OR_FAILED'
        $summary.recovery_required=$effectAttempted
        if($effectAttempted){$summary.status='RECOVERY_REQUIRED'}
    } finally {
        if($null -ne $reconcile){try{& $Ports.Unlock $reconcile | Out-Null}catch{$summary.recovery_required=$true};$reconcile=$null}
        if($stopped -and $null -ne $before){
            try{& $Ports.BeginRecovery | Out-Null
                & $Ports.CheckPreservation $before 'RECOVERY' | Out-Null
                & $Ports.RestoreBridge $before | Out-Null
                & $Ports.Final $Scenario $before | Out-Null;$summary.bridge_restored=$true}
            catch{$summary.recovery_required=$true;$summary.status='RECOVERY_REQUIRED'}
        }
        if($null -ne $update){try{& $Ports.Unlock $update | Out-Null}catch{$summary.recovery_required=$true;$summary.status='RECOVERY_REQUIRED'}}
        if($summary.recovery_required){$summary.status='RECOVERY_REQUIRED'}
    }
    return $summary
}

function Get-WslMaintenanceRegistrySnapshot {
    param([switch]$ServiceConfiguration)
    $key='SYSTEM\CurrentControlSet\Services\PortProxy'
    if($ServiceConfiguration){$key='SYSTEM\CurrentControlSet\Services\TinySwarmWorldWslBridge'}
    $root=[Microsoft.Win32.Registry]::LocalMachine.OpenSubKey($key,$false)
    if($null -eq $root){throw 'PORTPROXY_REGISTRY_UNAVAILABLE'}
    $rows=[Collections.ArrayList]::new();$budget=@{bytes=0}
    function Read-WslMaintenanceRegistryNode($Key,[string]$Relative,[int]$Depth){
        if($Depth -gt 4 -or $rows.Count -ge 4096){throw 'PORTPROXY_REGISTRY_LIMIT'}
        $budget.bytes+=[Text.Encoding]::UTF8.GetByteCount($Relative)+16
        if($budget.bytes -gt 2097152){throw 'PORTPROXY_REGISTRY_LIMIT'}
        [void]$rows.Add([ordered]@{key=$Relative;name='';kind='KEY';value=''})
        foreach($name in @($Key.GetValueNames() | Sort-Object)){
            if($rows.Count -ge 4096 -or $name.Length -gt 512){throw 'PORTPROXY_REGISTRY_LIMIT'}
            $kind=$Key.GetValueKind($name).ToString()
            $value=$Key.GetValue($name,$null,[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
            if($null -eq $value -or (($value | ConvertTo-Json -Depth 8 -Compress).Length -gt 2097152)){throw 'PORTPROXY_REGISTRY_INVALID'}
            $budget.bytes+=[Text.Encoding]::UTF8.GetByteCount(($value | ConvertTo-Json -Depth 8 -Compress))+$name.Length+16
            if($budget.bytes -gt 2097152){throw 'PORTPROXY_REGISTRY_LIMIT'}
            # Preserve every value kind and foreign family; no registry writes.
            [void]$rows.Add([ordered]@{key=$Relative;name=$name;kind=$kind;value=$value})
        }
        foreach($name in @($Key.GetSubKeyNames() | Sort-Object)){
            if($name.Length -gt 512){throw 'PORTPROXY_REGISTRY_LIMIT'}
            $child=$Key.OpenSubKey($name,$false)
            if($null -eq $child){throw 'PORTPROXY_REGISTRY_UNAVAILABLE'}
            try{Read-WslMaintenanceRegistryNode $child ($Relative+'/'+$name) ($Depth+1)}finally{$child.Dispose()}
        }
    }
    try{Read-WslMaintenanceRegistryNode $root '' 0}finally{$root.Dispose()}
    return @($rows.ToArray())
}

function ConvertFrom-WslMaintenanceNetshAll {
    param([byte[]]$Bytes,$Registry)
    function Address([string]$Value,[string]$Version){
        if($Value.Length -gt 255){throw 'NETSH_UNCLASSIFIABLE'}
        $ip=$null
        if([Net.IPAddress]::TryParse($Value,[ref]$ip)){
            if(($Version -eq '4' -and $ip.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork) -or
                ($Version -eq '6' -and $ip.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetworkV6)){throw 'NETSH_UNCLASSIFIABLE'}
            return $ip.ToString().ToLowerInvariant()
        }
        if($Value -cnotmatch '\A[A-Za-z0-9][A-Za-z0-9_.-]{0,252}\z'){throw 'NETSH_UNCLASSIFIABLE'}
        return $Value.ToLowerInvariant()
    }
    function Row([string]$Family,[string]$Listen,[string]$ListenPort,[string]$Connect,[string]$ConnectPort){
        foreach($port in @($ListenPort,$ConnectPort)){
            $number=0
            if($port -cnotmatch '\A[0-9]{1,5}\z' -or ![int]::TryParse($port,[ref]$number) -or $number -gt 65535){throw 'NETSH_UNCLASSIFIABLE'}
        }
        return @($Family,(Address $Listen ($Family.Substring(1,1))),[string][int]$ListenPort,
            (Address $Connect ($Family.Substring(5,1))),[string][int]$ConnectPort) -join '|'
    }
    $expected=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($record in $Registry){
        $key=[string]$record.key
        if($record.kind -ceq 'KEY' -or $key.ToLowerInvariant() -notin @('/v4tov4/tcp','/v4tov6/tcp','/v6tov4/tcp','/v6tov6/tcp')){continue}
        if($record.kind -cne 'String' -or $record.name -isnot [string] -or $record.value -isnot [string]){throw 'NETSH_UNCLASSIFIABLE'}
        $listen=$record.name -split '/';$connect=$record.value -split '/'
        if($listen.Count -ne 2 -or $connect.Count -ne 2){throw 'NETSH_UNCLASSIFIABLE'}
        $family=($key -split '/')[1].ToLowerInvariant()
        if(!$expected.Add((Row $family $listen[0] $listen[1] $connect[0] $connect[1]))){throw 'NETSH_AMBIGUOUS'}
    }
    $format='oem:'+([Globalization.CultureInfo]::CurrentCulture.TextInfo.OEMCodePage)
    if($Bytes.Length -ge 2 -and $Bytes[0] -eq 255 -and $Bytes[1] -eq 254){
        $format='utf16-le-bom'
        $text=([Text.UnicodeEncoding]::new($false,$false,$true)).GetString($Bytes,2,$Bytes.Length-2)
    }elseif($Bytes.Length -ge 3 -and $Bytes[0] -eq 239 -and $Bytes[1] -eq 187 -and $Bytes[2] -eq 191){
        $format='utf8-bom'
        $text=([Text.UTF8Encoding]::new($false,$true)).GetString($Bytes,3,$Bytes.Length-3)
    }else{
        $encoding=[Text.Encoding]::GetEncoding([Globalization.CultureInfo]::CurrentCulture.TextInfo.OEMCodePage,
            [Text.EncoderFallback]::ExceptionFallback,[Text.DecoderFallback]::ExceptionFallback)
        $text=$encoding.GetString($Bytes)
    }
    $observed=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $sections=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $layout=[Text.StringBuilder]::new();$family='';$stage='header'
    foreach($lineMatch in [regex]::Matches($text,'(?m)^.*(?:\r?\n|$)')){
        $line=$lineMatch.Value.TrimEnd("`r","`n")
        $ending=$lineMatch.Value.Substring($line.Length)
        $trim=$line.Trim()
        if(!$trim){[void]$layout.Append($lineMatch.Value);continue}
        $versions=[regex]::Matches($trim,'\bipv([46])\b',[Text.RegularExpressions.RegexOptions]::IgnoreCase)
        if($versions.Count -eq 2){
            $label=[regex]::Replace($trim,'\bipv[46]\b','',[Text.RegularExpressions.RegexOptions]::IgnoreCase)
            if($stage -in @('labels','separator') -or $label -notmatch '\A[\p{L}\p{M}\s:]+\z'){throw 'NETSH_UNCLASSIFIABLE'}
            $family='v'+$versions[0].Groups[1].Value+'tov'+$versions[1].Groups[1].Value
            if(!$sections.Add($family)){throw 'NETSH_AMBIGUOUS'}
            $stage='labels';[void]$layout.Append($lineMatch.Value);continue
        }
        if($stage -eq 'labels'){
            if($trim -notmatch '\A[\p{L}\p{M}]+\s+[\p{L}\p{M}]+\s+[\p{L}\p{M}]+\s+[\p{L}\p{M}]+\z'){throw 'NETSH_UNCLASSIFIABLE'}
            $stage='separator';[void]$layout.Append($lineMatch.Value);continue
        }
        if($stage -eq 'separator'){
            if($trim -cnotmatch '\A-{1,80}\s+-{1,80}\s+-{1,80}\s+-{1,80}\z'){throw 'NETSH_UNCLASSIFIABLE'}
            $stage='rows';[void]$layout.Append($lineMatch.Value);continue
        }
        if($stage -ne 'rows'){throw 'NETSH_UNCLASSIFIABLE'}
        $parts=$trim -split '\s+'
        if($parts.Count -ne 4){throw 'NETSH_UNCLASSIFIABLE'}
        if(!$observed.Add((Row $family $parts[0] $parts[1] $parts[2] $parts[3]))){throw 'NETSH_AMBIGUOUS'}
        [void]$layout.Append('ROW:'+$family+$ending)
    }
    if($stage -in @('labels','separator') -or !$expected.SetEquals($observed)){throw 'NETSH_REGISTRY_MISMATCH'}
    $hash=[Security.Cryptography.SHA256]::Create()
    try{$rawHash=([BitConverter]::ToString($hash.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose()}
    return @{projection=(Get-WslMaintenanceDigest @($observed | Sort-Object));raw_sha256=$rawHash;
        layout=(Get-WslMaintenanceDigest @($format,$layout.ToString()));count=$observed.Count}
}

function New-WslMaintenanceProductionPorts {
    param([Collections.IDictionary]$Scenario)
    Assert-WslMaintenanceScenario $Scenario
    $actor=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    foreach($path in @($Scenario.repository_root,(Join-Path $Scenario.repository_root '.git'))){
        $item=Get-Item -LiteralPath $path -Force
        if(!$item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
            (Get-Acl -LiteralPath $path).GetOwner([Security.Principal.SecurityIdentifier]).Value -cne $actor){throw 'SOURCE_OWNER_MISMATCH'}
    }
    $digestFunction=${function:Get-WslMaintenanceDigest}
    $registryFunction=${function:Get-WslMaintenanceRegistrySnapshot}
    $netshFunction=${function:ConvertFrom-WslMaintenanceNetshAll}
    $planValidator=${function:Assert-WslMaintenanceResourcePlan}
    $firewallCommand=Get-WslMaintenanceFirewallCommand
    $module=New-Module -Name Epic440WslMaintenance -ArgumentList $Scenario,$digestFunction,$registryFunction,$netshFunction,$planValidator,$firewallCommand -ScriptBlock {
        param($Scenario,$digestFunction,$registryFunction,$netshFunction,$planValidator,$firewallCommand)
        Set-Item Function:script:Get-WslMaintenanceDigest $digestFunction
        Set-Item Function:script:Get-WslMaintenanceRegistrySnapshot $registryFunction
        Set-Item Function:script:ConvertFrom-WslMaintenanceNetshAll $netshFunction
        Set-Item Function:script:Assert-WslMaintenanceResourcePlan $planValidator
        $script:clock=[Diagnostics.Stopwatch]::StartNew();$script:commandCount=0;$script:outputBytes=0
        $script:limits=@{seconds=1800;commands=256;bytes=67108864};$script:recoveryBegun=$false
        $script:firewallCommand=$firewallCommand
        $script:s=$Scenario
        $script:root=$s.repository_root
        Import-Module (Join-Path $root 'bootstrap/windows/preparation/Preparation.psm1') -Force -DisableNameChecking
        $script:preparation=Get-Module Preparation
        $script:preparationPorts=& $preparation {New-PreparationPorts}
        $script:options=@{Mode='Check';Json=$true;Distro='Ubuntu';UbuntuRelease='26.04';ExpectedRelease='26.04';
            ServiceProfile='service-access';RepositoryRoot=$root;LinuxCheckout=$s.guest_checkout;
            ProbeTimeoutSeconds=15;OverallTimeoutSeconds=180;ActionTimeoutSeconds=120;
            WslMemoryGiB=21;WslProcessors=8;WslSwapGiB=6;ApproveApply=$false;QualificationRun=$false;ApprovedPlan=$null}
        . (Join-Path $root 'bootstrap/windows/tws-wsl-bridge.ps1') -Action inventory -Distro Ubuntu `
            -ConfigPath (Join-Path $root 'bootstrap/windows/tws-wsl-bridge.config.json') `
            -PortRegistryPath (Join-Path $root 'infra/config/ports.yaml')
        $script:resumedAt=$null;$script:expectedRegistry=$null;$script:stateOriginal=$null;$script:routeSets=0
        function ClaimCommand {
            $remaining=$script:limits.seconds-[int][Math]::Ceiling($script:clock.Elapsed.TotalSeconds)
            if($remaining -le 0 -or $script:commandCount -ge $script:limits.commands){throw 'MAINTENANCE_DEADLINE'}
            $script:commandCount++
            return $remaining
        }
        function BeginRecovery {
            if($script:recoveryBegun){throw 'RECOVERY_ALREADY_STARTED'}
            $script:recoveryBegun=$true
            $script:clock=[Diagnostics.Stopwatch]::StartNew();$script:commandCount=0;$script:outputBytes=0
            $script:limits=@{seconds=600;commands=128;bytes=67108864}
        }
        function Run([string]$File,[string[]]$Arguments,[int]$Timeout=30,[int]$OutputLimit=8388608,[int[]]$ExpectedExits=@(0)){
            $remaining=ClaimCommand
            $r=& $preparation {param($f,$a,$t) Invoke-PreparationProcess $f $a $t} $File $Arguments ([Math]::Min($Timeout,$remaining))
            $stdoutBytes=[Text.Encoding]::UTF8.GetByteCount($r.stdout)
            $script:outputBytes+=$stdoutBytes+[Text.Encoding]::UTF8.GetByteCount($r.stderr)
            if($r.exit_code -notin $ExpectedExits -or ($r.exit_code -ne 0 -and $stdoutBytes -ne 0) -or
                $r.stderr.Length -ne 0 -or $stdoutBytes -gt $OutputLimit -or $script:outputBytes -gt $script:limits.bytes){throw 'HOST_COMMAND_FAILED'}
            return $r.stdout
        }
        function Wsl([string[]]$Arguments,[int]$Timeout=30,[int[]]$ExpectedExits=@(0)){
            $exe=& $preparation {Get-PreparationExecutable 'wsl.exe'}
            return Run $exe $Arguments $Timeout 8388608 $ExpectedExits
        }
        function NetshAll {
            $left=ClaimCommand
            $info=[Diagnostics.ProcessStartInfo]::new()
            $info.FileName=Join-Path ([Environment]::GetFolderPath('System')) 'netsh.exe'
            $info.WorkingDirectory=[Environment]::GetFolderPath('System')
            $info.Arguments='interface portproxy show all';$info.UseShellExecute=$false;$info.CreateNoWindow=$true
            $info.RedirectStandardInput=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
            $process=[Diagnostics.Process]::new();$process.StartInfo=$info
            $stdout=[IO.MemoryStream]::new();$stderr=[IO.MemoryStream]::new();$started=$false
            try{
                [void]$process.Start();$started=$true;$process.StandardInput.Close()
                $out=$process.StandardOutput.BaseStream.CopyToAsync($stdout)
                $err=$process.StandardError.BaseStream.CopyToAsync($stderr)
                if(!$process.WaitForExit([Math]::Min($left,30)*1000)){$process.Kill();[void]$process.WaitForExit(5000);throw 'NETSH_DEADLINE'}
                if(![Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($out,$err),2000) -or
                    $process.ExitCode -ne 0 -or $stderr.Length -ne 0 -or $stdout.Length -gt 2097152){throw 'NETSH_CAPTURE_FAILED'}
                $script:outputBytes+=$stdout.Length
                if($script:outputBytes -gt $script:limits.bytes){throw 'MAINTENANCE_OUTPUT_LIMIT'}
                return ,$stdout.ToArray()
            }finally{
                if($started){try{if(!$process.HasExited){$process.Kill();[void]$process.WaitForExit(5000)}}catch{}}
                $process.Dispose();$stdout.Dispose();$stderr.Dispose()
            }
        }
        function Running {
            return @( (Wsl @('--list','--running','--quiet')) -replace "`0",'' -split '\r?\n' |
                ForEach-Object{$_.Trim()} | Where-Object{$_})
        }
        function Registration {
            $base=[Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Software\Microsoft\Windows\CurrentVersion\Lxss',$false)
            if($null -eq $base){throw 'REGISTRATION_UNAVAILABLE'}
            try{
                $entries=@(foreach($key in @($base.GetSubKeyNames() | Sort-Object)){
                    $child=$base.OpenSubKey($key,$false)
                    if($null -eq $child){throw 'REGISTRATION_UNAVAILABLE'}
                    try{[ordered]@{id=$key;name=$child.GetValue('DistributionName');base=$child.GetValue('BasePath');
                        version=$child.GetValue('Version');uid=$child.GetValue('DefaultUid');vhd=$child.GetValue('VhdFileName');
                        flags=$child.GetValue('Flags');package=$child.GetValue('PackageFamilyName')}}finally{$child.Dispose()}
                })
                if($entries.Count -ne 1 -or $entries[0].name -cne 'Ubuntu' -or $entries[0].version -ne 2 -or
                    $entries[0].uid -lt 1000 -or $entries[0].uid -ge 65534){throw 'REGISTRATION_MISMATCH'}
                $value=Get-WslMaintenanceDigest $entries
                if($value -cne $s.registration_sha256){throw 'REGISTRATION_MISMATCH'}
                return $value
            }finally{$base.Dispose()}
        }
        function Source {
            if([Environment]::MachineName -cne $s.host){throw 'HOST_MISMATCH'}
            $value=& $preparationPorts.SourceIdentity $options
            if(!$value.verified -or !$value.clean -or $value.revision -cne $s.source_commit){throw 'SOURCE_MISMATCH'}
            $nativeHelper=Join-Path $root 'tools/linux/qualification/wsl_guest_inventory.py'
            if((Get-FileHash -LiteralPath $nativeHelper -Algorithm SHA256).Hash.ToLowerInvariant() -cne $s.guest_helper_sha256){throw 'SOURCE_MISMATCH'}
            $null=Registration
        }
        function LinuxBinding($Facts){
            return [ordered]@{uid=$Facts.uid;user=$Facts.user;release=$Facts.release;architecture=$Facts.linux_architecture;
                linux_id=$Facts.linux_id;generation=$Facts.wsl_generation;config=$Facts.config_hash;
                metadata=$Facts.config_metadata;systemd=$Facts.systemd_configured;pid1=$Facts.pid1;
                wsl_version=$Facts.wsl_version;store_package=$Facts.wsl_store_package}
        }
        function Guest {
            Source
            $checkout=$s.guest_checkout
            $helper=$checkout+'/tools/linux/qualification/wsl_guest_inventory.py'
            $hash=Wsl @('--distribution','Ubuntu','--user','root','--exec','/usr/bin/sha256sum',$helper)
            if(($hash -split '\s+')[0] -cne $s.guest_helper_sha256){throw 'GUEST_SOURCE_MISMATCH'}
            $git=@('--distribution','Ubuntu','--user','root','--exec','/usr/bin/env','-i','LC_ALL=C',
                'PATH=/usr/bin:/bin','GIT_CONFIG_NOSYSTEM=1','GIT_CONFIG_GLOBAL=/dev/null','/usr/bin/git','--no-optional-locks',
                '-c','core.fsmonitor=false','-c','core.untrackedCache=false','-C',$checkout)
            $head=Wsl ($git+@('rev-parse','HEAD'))
            if($head.Trim() -cne $s.source_commit){throw 'GUEST_SOURCE_MISMATCH'}
            $filterText=Wsl ($git+@('config','--name-only','--get-regexp','^filter\..*\.(clean|smudge|process|required)$')) 30 @(0,1)
            $filters=@($filterText -split '\r?\n' | Where-Object{$_})
            if($filterText.Length -gt 65536 -or $filters.Count -gt 64){throw 'GUEST_FILTERS_UNKNOWN'}
            foreach($key in $filters){
                if($key.Length -gt 128 -or $key -cnotmatch '\Afilter\.[A-Za-z0-9_.-]+\.(clean|smudge|process|required)\z'){throw 'GUEST_FILTERS_UNKNOWN'}
                $value='';if($key.EndsWith('.required')){$value='false'}
                $git+=@('-c',($key+'='+$value))
            }
            $clean=Wsl ($git+@('status','--porcelain','--untracked-files=all','--ignore-submodules=all'))
            if(![string]::IsNullOrWhiteSpace($clean)){throw 'GUEST_SOURCE_MISMATCH'}
            $raw=Wsl @('--distribution','Ubuntu','--user','root','--exec','/usr/bin/python3','-E','-s','-B',
                $helper,'--source-commit',$s.source_commit) 310
            $proof=ValidateGuestProof $raw
            return [ordered]@{graph=$proof.graph_sha256;details=$proof.detail_sha256;instances=$proof.instance_count;projects=$proof.project_count}
        }
        function ValidateGuestProof([string]$Raw){
            if(!$Raw.Trim().StartsWith('{') -or !$Raw.Trim().EndsWith('}')){throw 'GUEST_PRESERVATION_UNPROVEN'}
            $proof=$Raw | ConvertFrom-Json -ErrorAction Stop
            $expected=@('schema_version','scope','decision','source_commit','graph_sha256','detail_sha256',
                'instance_count','project_count','detail_count','command_count')
            if($proof -isnot [PSCustomObject] -or
                ((@($proof.PSObject.Properties.Name | Sort-Object)) -join '|') -cne (($expected | Sort-Object) -join '|')){
                throw 'GUEST_PRESERVATION_UNPROVEN'
            }
            foreach($name in $expected){
                if([regex]::Matches($Raw,('"'+[regex]::Escape($name)+'"\s*:')).Count -ne 1){throw 'GUEST_PRESERVATION_UNPROVEN'}
            }
            if($proof.schema_version -isnot [int] -or $proof.schema_version -ne 1 -or
                $proof.scope -isnot [string] -or $proof.scope -cne 'WSL_GUEST_PRESERVATION_ONLY' -or
                $proof.decision -isnot [string] -or $proof.source_commit -isnot [string] -or
                $proof.decision -cne 'ALL_INSTANCES_STOPPED_GRAPH_COMPLETE' -or $proof.source_commit -cne $s.source_commit -or
                $proof.graph_sha256 -isnot [string] -or $proof.detail_sha256 -isnot [string] -or
                $proof.graph_sha256 -cnotmatch '\A[0-9a-f]{64}\z' -or $proof.detail_sha256 -cnotmatch '\A[0-9a-f]{64}\z'){
                throw 'GUEST_PRESERVATION_UNPROVEN'
            }
            foreach($field in @('instance_count','project_count','detail_count','command_count')){
                if($proof.$field -isnot [int] -or $proof.$field -lt 0 -or $proof.$field -gt 10000){throw 'GUEST_PRESERVATION_UNPROVEN'}
            }
            if($proof.project_count -eq 0 -or $proof.detail_count -eq 0 -or
                $proof.command_count -eq 0 -or $proof.command_count -gt 2048 -or $proof.detail_count -gt $proof.command_count -or
                $proof.project_count -gt $proof.detail_count -or $proof.instance_count*2 -gt $proof.detail_count){throw 'GUEST_PRESERVATION_UNPROVEN'}
            return $proof
        }
        function Firewall {
            $exe=& $preparation {Get-PreparationExecutable 'powershell.exe'}
            return Run $exe @('-NoProfile','-NonInteractive','-Command',$script:firewallCommand) 120 14680064
        }
        function StableState($State){
            $stable=[ordered]@{}
            foreach($property in @($State.PSObject.Properties | Sort-Object Name)){
                if($property.Name -notin @('agentStatus','generatedAt','action','driftReasons')){
                    $stable[$property.Name]=$property.Value
                }
            }
            return $stable
        }
        function RegistryStructure($Rows,$State){
            $owned=@{}
            foreach($mapping in @($State.mappings)){$owned[[string]$State.listenAddress+'/'+$mapping.listenPort]=[string]$mapping.connectPort}
            return @($Rows | ForEach-Object{
                if($_.key -ceq '/v4tov4/tcp' -and $owned.ContainsKey($_.name)){
                    $parts=[string]$_.value -split '/'
                    if($_.kind -cne 'String' -or $parts.Count -ne 2 -or $parts[1] -cne $owned[$_.name]){throw 'ROUTE_AUTHORITY_UNVERIFIED'}
                    [ordered]@{key=$_.key;name=$_.name;kind=$_.kind;value=('OWNED_IP/'+$parts[1])}
                }else{$_}
            })
        }
        function Snapshot {
            Assert-BridgeRuntimeStateAuthority
            $powershell=& $preparation {Get-PreparationExecutable 'powershell.exe'}
            $taskQuery='$ErrorActionPreference="Stop";$ProgressPreference="SilentlyContinue";$t=@(Get-ScheduledTask -ErrorAction Stop);if($t.Count -gt 8192){throw "task_limit"};$m=@($t | Where-Object{$_.TaskName -ceq "TinySwarmWorld-WslBridge"});@{conflicts=@($m | Where-Object{[string]$_.State -cne "Disabled" -or $_.Settings.Enabled -ne $false}).Count} | ConvertTo-Json -Compress'
            $tasks=(Run $powershell @('-NoProfile','-NonInteractive','-Command',$taskQuery) 15 4096) | ConvertFrom-Json
            if($tasks.conflicts -isnot [int] -or $tasks.conflicts -ne 0){throw 'LEGACY_WRITER_UNQUIESCED'}
            $owner=Get-BridgeServiceOwnership
            if($owner.Status -cne 'owned' -or $owner.RequiresAdoption -or $null -eq $owner.Service -or
                (Test-Path -LiteralPath $TransactionJournalPath) -or $owner.AccountSid -cne
                [Security.Principal.WindowsIdentity]::GetCurrent().User.Value){throw 'BRIDGE_OWNERSHIP_MISMATCH'}
            $details=Get-BridgeServiceDetails
            $identity=Get-WslMaintenanceDigest @((Get-BridgeServiceDefinitionFields),$details,(Get-BridgeBundleIdentity),
                (Get-WslMaintenanceRegistrySnapshot -ServiceConfiguration),
                (Get-FileHash -LiteralPath $InstalledConfigPath -Algorithm SHA256).Hash)
            $firewall=Firewall
            $hosts=[IO.File]::ReadAllBytes($HostsPath)
            $records=@(Get-WslMaintenanceRegistrySnapshot)
            $all=NetshAll
            $netshProof=ConvertFrom-WslMaintenanceNetshAll $all $records
            return @{identity=$identity;owner=$owner;firewall=(Get-WslMaintenanceDigest $firewall);
                hosts=(Get-WslMaintenanceDigest $hosts);registry=$records;netsh=$netshProof;
                all=$all;state=(Get-ProtectedBridgeState);service_state=[string]$owner.Service.Status;
                running=($owner.Service.Status -eq 'Running')}
        }
        function Observe {
            Source
            if((@(Running) -join ',') -cne 'Ubuntu'){throw 'RUNNING_REGISTRATION_MISMATCH'}
            $guest=Guest;$net=Snapshot
            if($net.service_state -notin @('Running','Stopped')){throw 'BRIDGE_RUNTIME_DRIFT'}
            if($net.running -and !(Test-BridgeServiceReady)){throw 'BRIDGE_RUNTIME_CONTRACT_NOT_READY'}
            $facts=& $preparationPorts.Inventory $options
            if(!$facts.elevated -or !$facts.running -or !$facts.linux_known -or
                $facts.uid -lt 1000 -or $facts.uid -ge 65534 -or $facts.release -cne '26.04' -or
                $facts.pid1 -cne 'systemd' -or @($facts.bridge_facts.blockers).Count -ne 0){throw 'PRESTATE_BLOCKED'}
            # Resuming the existing reconciler must not create a missing
            # firewall rule/hosts entry as a side effect of this IP-only stage.
            $config=Read-BridgeConfig $InstalledConfigPath
            $registry=Read-TswPortRegistry $InstalledPortRegistryPath
            $mappings=@(Get-PortMappings $config $registry.Mappings)
            $names=@(Get-BridgeHostNames $config $registry.HostNames)
            if(!(Test-FirewallRulesReady $config $mappings) -or !(Test-HostsFileReady $config $names)){
                throw 'BASELINE_FIREWALL_OR_HOSTS_REPAIR_REQUIRED'
            }
            $eligibility=Plan
            Assert-WslMaintenanceResourcePlan $eligibility
            $script:stateOriginal=Get-WslMaintenanceDigest $net.state
            $script:stateExpected=$script:stateOriginal
            $script:stableExpected=Get-WslMaintenanceDigest (StableState $net.state)
            $script:expectedRegistry=@($net.registry)
            $resourceConfig=Get-WslMaintenanceDigest $facts.resource_facts.config_snapshot
            $resourceBefore=[ordered]@{config=$resourceConfig;settings=$facts.resource_facts.config_values;
                physical=$facts.resource_facts.physical_memory_bytes;cpus=$facts.resource_facts.logical_processors;
                effective_memory=$facts.resource_facts.effective_physical_memory_bytes;
                effective_cpus=$facts.resource_facts.effective_processors;effective_swap=$facts.resource_facts.effective_swap_bytes}
            $os=Get-WslMaintenanceDigest (LinuxBinding $facts)
            $stable=[ordered]@{guest=$guest;os=$os;resources=$resourceBefore;bridge=$net.identity;firewall=$net.firewall;hosts=$net.hosts;
                netsh=$net.netsh.raw_sha256;
                registry=$net.registry;state=(StableState $net.state);running=$net.running;registration=$s.registration_sha256}
            $before=@{admitted=$true;prestate_sha256=(Get-WslMaintenanceDigest $stable);guest=$guest;net=$net;
                stable_state=$script:stableExpected;os=$os;resource_config=$resourceConfig;bridge_running=$net.running;
                old_address=[string]$net.state.wslIp;new_address=[string]$net.state.wslIp}
            $null=Routes $before $before.old_address
            $static=StableState $net.state
            $static.Remove('wslIp')
            $before.recovery=[ordered]@{guest_graph=$guest.graph;guest_details=$guest.details;os=$os;firewall=$net.firewall;
                hosts=$net.hosts;bridge=$net.identity;registry_structure=(Get-WslMaintenanceDigest (RegistryStructure $net.registry $net.state));
                state_static=(Get-WslMaintenanceDigest $static);old_address=(Get-WslMaintenanceDigest $before.old_address);
                netsh_layout=$net.netsh.layout;resource_config=$resourceConfig;
                resource_file=$facts.resource_facts.config_snapshot.hash;
                resource_metadata=(Get-WslMaintenanceDigest $facts.resource_facts.config_snapshot.metadata);
                resource_metrics=[ordered]@{physical_bytes=$resourceBefore.physical;
                    cpu_count=$resourceBefore.cpus;effective_memory_bytes=$resourceBefore.effective_memory;
                    effective_cpus=$resourceBefore.effective_cpus;effective_swap_bytes=$resourceBefore.effective_swap}}
            return $before
        }
        function CheckPreservation($Before,[string]$Phase){
            $null=Registration
            if((@(Running) -join ',') -cne 'Ubuntu'){throw 'RUNNING_REGISTRATION_MISMATCH'}
            if($Phase -ceq 'RECOVERY' -and (@(Running) -join ',') -cne 'Ubuntu'){throw 'RECOVERY_REENTRY_REQUIRED'}
            $net=Snapshot
            if($net.identity -cne $Before.net.identity -or $net.firewall -cne $Before.net.firewall -or
                $net.hosts -cne $Before.net.hosts -or (Get-WslMaintenanceDigest $net.registry) -cne
                (Get-WslMaintenanceDigest $script:expectedRegistry)){throw 'PRESERVATION_DRIFT'}
            if($net.netsh.layout -cne $Before.net.netsh.layout -or
                ($script:routeSets -eq 0 -and $net.netsh.raw_sha256 -cne $Before.net.netsh.raw_sha256)){
                throw 'NETSH_PRESERVATION_DRIFT'
            }
            $stable=Get-WslMaintenanceDigest (StableState $net.state)
            if($Phase -in @('ORIGINAL','RECOVERY_ORIGINAL','QUIESCED')){
                if($stable -cne $Before.stable_state){throw 'PROTECTED_STATE_DRIFT'}
            }elseif($Phase -in @('RECOVERY','RESTORED')){
                if($stable -cne $script:stableExpected){throw 'PROTECTED_STATE_DRIFT'}
            }elseif((Get-WslMaintenanceDigest $net.state) -cne $script:stateExpected){throw 'PROTECTED_STATE_DRIFT'}
            if($Phase -ceq 'RECOVERY_ORIGINAL'){
                if($net.running -isnot [bool] -or $net.running -ne $Before.recovery_running){throw 'BRIDGE_RUNTIME_DRIFT'}
            }elseif($Phase -in @('ORIGINAL','RESTORED')){
                if($net.running -isnot [bool] -or $net.running -ne $Before.bridge_running){throw 'BRIDGE_RUNTIME_DRIFT'}
            }elseif($Phase -cne 'RECOVERY'){
                if($net.running -isnot [bool] -or $net.running){throw 'BRIDGE_RUNTIME_DRIFT'}
            }
            if($Phase -ceq 'RECOVERY'){
                $facts=& $preparationPorts.Inventory $options
                if(@($facts.bridge_facts.blockers).Count -ne 0 -or
                    $net.state.wslIp -cne [string]$facts.observed_wsl_address){throw 'RECOVERY_ROUTE_STATE_UNCERTAIN'}
                foreach($mapping in @($net.state.mappings)){
                    $name=[string]$net.state.listenAddress+'/'+$mapping.listenPort
                    $rows=@($net.registry | Where-Object{$_.key -ceq '/v4tov4/tcp' -and $_.name -ceq $name})
                    if($rows.Count -ne 1 -or $rows[0].kind -cne 'String' -or
                        $rows[0].value -cne ($net.state.wslIp+'/'+$mapping.connectPort)){throw 'RECOVERY_ROUTE_STATE_UNCERTAIN'}
                }
            }
            if($Phase -ceq 'QUIESCED'){
                $script:stateOriginal=Get-WslMaintenanceDigest $net.state
                $script:stateExpected=$script:stateOriginal
                $script:stableExpected=$stable
                $Before.net.state=$net.state
            }
            if($Phase -ceq 'BEFORE_APPLY'){
                $facts=& $preparationPorts.Inventory $options
                if((Get-WslMaintenanceDigest $facts.resource_facts.config_snapshot) -cne $Before.resource_config -or
                    (Get-WslMaintenanceDigest (LinuxBinding $facts)) -cne $Before.os){throw 'RESOURCE_CONFIG_DRIFT'}
            }
            if($Phase -in @('BEFORE_SHUTDOWN','FINAL','RESTORED')){
                if((Get-WslMaintenanceDigest (Guest)) -cne (Get-WslMaintenanceDigest $Before.guest)){throw 'GUEST_PRESERVATION_DRIFT'}
            }
            if($Phase -in @('FINAL','RESTORED')){AssertAddress $Before $Before.new_address}
        }
        function Lock([string]$Name,[int]$Seconds){return Enter-BridgeMutex -Name $Name -Timeout ([TimeSpan]::FromSeconds($Seconds))}
        function Unlock($Mutex){Exit-BridgeMutex $Mutex}
        function StopBridge($Before){
            $owner=Get-BridgeServiceOwnership
            if($owner.Status -cne 'owned' -or $owner.RequiresAdoption){throw 'BRIDGE_OWNERSHIP_MISMATCH'}
            if(@($owner.Service.DependentServices | Where-Object{$_.Status -ne 'Stopped'}).Count -ne 0){throw 'BRIDGE_DEPENDENT_SERVICE_RUNNING'}
            Stop-Service -Name $ServiceName -ErrorAction Stop
            $owner.Service.WaitForStatus('Stopped',[TimeSpan]::FromSeconds(30))
        }
        function Plan {
            $options.Mode='Check';$options.ApproveApply=$false;$options.QualificationRun=$false;$options.ApprovedPlan=$null
            return & $preparation {param($o,$p) Invoke-WindowsPreparation $o $p} $options $preparationPorts
        }
        function Apply($Ignored,[string]$Fingerprint){
            $options.Mode='Apply';$options.ApproveApply=$true;$options.QualificationRun=$true;$options.ApprovedPlan=$Fingerprint
            $options.QualificationHost=$s.host;$options.QualificationDistro='Ubuntu';$options.QualificationRevision=$s.source_commit
            $options.RecoveryReference=$s.recovery_reference
            return & $preparation {param($o,$p) Invoke-WindowsPreparation $o $p} $options $preparationPorts
        }
        function Shutdown {
            if((@(Running) -join ',') -cne 'Ubuntu'){throw 'RUNNING_REGISTRATION_MISMATCH'}
            $null=Wsl @('--shutdown') 60
            if(@(Running).Count -ne 0){throw 'SHUTDOWN_UNVERIFIED'}
        }
        function Relaunch {
            $null=Registration
            if(@(Running).Count -ne 0){throw 'RUNNING_REGISTRATION_MISMATCH'}
            $null=Wsl @('--distribution','Ubuntu','--exec','/usr/bin/true') 120
            if((@(Running) -join ',') -cne 'Ubuntu'){throw 'RELAUNCH_UNVERIFIED'}
        }
        function Effective($Ignored,$Before){
            $p=Plan
            if(@($p.resources.blockers).Count -ne 0 -or $p.resources.state -cne 'VERIFIED' -or
                @($p.actions | Where-Object{$_.id -eq 'adapt_wsl_resources'}).Count -ne 0){throw 'RESOURCE_EFFECT_UNVERIFIED'}
            if((Get-WslMaintenanceDigest (Guest)) -cne (Get-WslMaintenanceDigest $Before.guest)){throw 'GUEST_PRESERVATION_DRIFT'}
        }
        function Address($Ignored,$Before){
            $facts=& $preparationPorts.Inventory $options
            $address=[string]$facts.observed_wsl_address
            Assert-ValidIPv4Address $address 'selected Ubuntu address'
            $ip=[Net.IPAddress]::Parse($address)
            if([Net.IPAddress]::IsLoopback($ip) -or $ip.GetAddressBytes()[0] -eq 0 -or $ip.GetAddressBytes()[0] -ge 224){throw 'ADDRESS_UNVERIFIED'}
            $Before.new_address=$address
            return $address
        }
        function Routes($Before,[string]$Address){
            $state=$Before.net.state
            if($state.contractVersion -ne 2 -or $state.agentMode -cne 'windows-service' -or $state.serviceName -cne $ServiceName -or
                $state.listenAddress -notin @('0.0.0.0','127.0.0.1')){throw 'ROUTE_AUTHORITY_UNVERIFIED'}
            $config=Read-BridgeConfig $InstalledConfigPath
            $registry=Read-TswPortRegistry $InstalledPortRegistryPath
            $mappings=@(Get-PortMappings $config $registry.Mappings)
            if((Get-WslMaintenanceDigest @($state.mappings | Sort-Object listenPort)) -cne
                (Get-WslMaintenanceDigest @($mappings | ForEach-Object{[pscustomobject]@{name=$_.Name;listenPort=$_.ListenPort;connectPort=$_.ConnectPort}} | Sort-Object listenPort))){throw 'ROUTE_AUTHORITY_UNVERIFIED'}
            foreach($mapping in $mappings){
                $name=[string]$state.listenAddress+'/'+$mapping.ListenPort
                $rows=@($script:expectedRegistry | Where-Object{$_.key -ceq '/v4tov4/tcp' -and $_.name -ceq $name})
                if($rows.Count -ne 1 -or $rows[0].kind -cne 'String' -or $rows[0].value -cne ($Before.old_address+'/'+$mapping.ConnectPort)){throw 'ROUTE_AUTHORITY_UNVERIFIED'}
                if($Address -cne $Before.old_address){[ordered]@{name=$name;listen=[string]$state.listenAddress;listen_port=[int]$mapping.ListenPort;connect_port=[int]$mapping.ConnectPort}}
            }
        }
        function SetRoute($Before,$Change,[string]$Address){
            CheckPreservation $Before 'BEFORE_ROUTE'
            $state=$Before.net.state
            $matches=@($state.mappings | Where-Object{
                $_.listenPort -eq $Change.listen_port -and $_.connectPort -eq $Change.connect_port})
            $name=[string]$state.listenAddress+'/'+$Change.listen_port
            $rows=@($script:expectedRegistry | Where-Object{$_.key -ceq '/v4tov4/tcp' -and $_.name -ceq $name})
            if($matches.Count -ne 1 -or $Change.name -cne $name -or $Change.listen -cne $state.listenAddress -or
                $Address -cne $Before.new_address -or $Address -ceq $Before.old_address -or
                $rows.Count -ne 1 -or $rows[0].kind -cne 'String' -or
                $rows[0].value -cne ($Before.old_address+'/'+$Change.connect_port)){throw 'ROUTE_AUTHORITY_UNVERIFIED'}
            AssertAddress $Before $Address
            $netsh=Join-Path ([Environment]::GetFolderPath('System')) 'netsh.exe'
            $null=Run $netsh @('interface','portproxy','set','v4tov4',('listenaddress='+$Change.listen),
                ('listenport='+$Change.listen_port),('connectaddress='+$Address),('connectport='+$Change.connect_port),'protocol=tcp') 30
            $script:routeSets++
            $script:expectedRegistry=@($script:expectedRegistry | ForEach-Object{
                if($_.key -ceq '/v4tov4/tcp' -and $_.name -ceq $Change.name){
                    [ordered]@{key=$_.key;name=$_.name;kind=$_.kind;value=($Address+'/'+$Change.connect_port)}
                }else{$_}
            })
            CheckPreservation $Before 'AFTER_ROUTE'
        }
        function CommitState($Before,[string]$Address){
            CheckPreservation $Before 'BEFORE_STATE'
            Assert-BridgeRuntimeStateAuthority
            AssertAddress $Before $Address
            $state=Get-ProtectedBridgeState
            if((Get-WslMaintenanceDigest $state) -cne $script:stateOriginal){throw 'STATE_CAS_DRIFT'}
            if($Address -cne $Before.old_address){
                $state.wslIp=$Address
                Write-TextAtomically $StatePath (($state | ConvertTo-Json -Depth 100)+[Environment]::NewLine)
                if((Get-WslMaintenanceDigest (Get-ProtectedBridgeState)) -cne (Get-WslMaintenanceDigest $state)){throw 'STATE_COMMIT_UNVERIFIED'}
                $script:stateExpected=Get-WslMaintenanceDigest $state
                $script:stableExpected=Get-WslMaintenanceDigest (StableState $state)
            }
        }
        function AssertAddress($Before,[string]$Address){
            $null=Registration
            $facts=& $preparationPorts.Inventory $options
            if(!$facts.running -or !$facts.linux_known -or $facts.release -cne '26.04' -or
                $facts.pid1 -cne 'systemd' -or $facts.uid -lt 1000 -or $facts.uid -ge 65534 -or
                (Get-WslMaintenanceDigest (LinuxBinding $facts)) -cne $Before.os -or
                $facts.observed_wsl_address -cne $Address -or $Before.new_address -cne $Address){throw 'ADDRESS_DRIFT'}
            # The protected state intentionally retains its old IP until every
            # admitted set completes. Only that classifier's transient label is
            # covered by the complete cumulative registry CAS, never a listener
            # or other blocker. No product predicate is modified.
            if(@($facts.bridge_facts.blockers | Where-Object{$_ -cne 'foreign_portproxy_rule'}).Count -ne 0){throw 'LISTENER_OR_BRIDGE_DRIFT'}
        }
        function RestoreBridge($Before){
            $owner=Get-BridgeServiceOwnership
            if($owner.Status -cne 'owned' -or $owner.RequiresAdoption){throw 'BRIDGE_OWNERSHIP_MISMATCH'}
            if($Before.bridge_running){
                if($null -eq $script:resumedAt){$script:resumedAt=[DateTimeOffset]::UtcNow}
                if($owner.Service.Status -eq 'Stopped'){
                    if(@($owner.Service.ServicesDependedOn | Where-Object{$_.Status -ne 'Running'}).Count -ne 0){throw 'FOREIGN_DEPENDENCY_START_FORBIDDEN'}
                    Start-BridgeServiceChecked
                }
                elseif($owner.Service.Status -ne 'Running'){throw 'BRIDGE_RUNTIME_DRIFT'}
            }
            elseif($owner.Service.Status -ne 'Stopped'){throw 'BRIDGE_RUNTIME_DRIFT'}
        }
        function WaitHeartbeat([int]$Seconds=60){
            $wait=[Diagnostics.Stopwatch]::StartNew()
            while($wait.Elapsed.TotalSeconds -lt $Seconds){
                $state=Get-ProtectedBridgeState
                $stamp=[DateTimeOffset]::MinValue
                if([DateTimeOffset]::TryParse([string]$state.generatedAt,[ref]$stamp) -and
                    $stamp -ge $script:resumedAt -and $stamp -le [DateTimeOffset]::UtcNow -and
                    [string]$state.agentMode -ceq 'windows-service' -and
                    [string]$state.agentStatus -in @('ready','degraded') -and
                    @($state.driftReasons) -notcontains 'reconcile_in_progress'){
                    return
                }
                Start-Sleep -Milliseconds 250
            }
            throw 'BRIDGE_FIRST_LOOP_UNVERIFIED'
        }
        function Final($Ignored,$Before){
            if($null -ne $script:resumedAt){WaitHeartbeat}
            Source;CheckPreservation $Before 'RESTORED'
            $current=Get-BridgeServiceOwnership
            if(($current.Service.Status -eq 'Running') -ne $Before.bridge_running){throw 'BRIDGE_RECOVERY_UNVERIFIED'}
        }
        function ReadIntent {
            $path=$s.guest_checkout+'/.tiny-swarm/evidence/issue-449/wsl-maintenance-intent.json'
            $canonical=Wsl @('--distribution','Ubuntu','--user','root','--exec','/usr/bin/readlink','-e',$path)
            if($canonical.Trim() -cne $path){throw 'INTENT_UNTRUSTED'}
            $row=Wsl @('--distribution','Ubuntu','--user','root','--exec','/usr/bin/stat','-c','%u:%a:%f:%h:%s',$path)
            $fields=$row.Trim() -split ':'
            if($fields.Count -ne 5 -or ($fields[0..3] -join ':') -cne '0:600:8180:1' -or
                $fields[4] -cnotmatch '\A[0-9]{1,5}\z' -or [int]$fields[4] -gt 32768){throw 'INTENT_UNTRUSTED'}
            $parent=$s.guest_checkout+'/.tiny-swarm/evidence/issue-449'
            $directory=Wsl @('--distribution','Ubuntu','--user','root','--exec','/usr/bin/stat','-c','%u:%a:%f',$parent)
            if($directory.Trim() -cne '0:700:41c0'){throw 'INTENT_UNTRUSTED'}
            $filesystem=Wsl @('--distribution','Ubuntu','--user','root','--exec','/usr/bin/findmnt','--noheadings','--output','FSTYPE','--target',$path)
            if($filesystem.Trim() -cne 'ext4'){throw 'INTENT_UNTRUSTED'}
            $value=Wsl @('--distribution','Ubuntu','--user','root','--exec','/usr/bin/sha256sum',$path)
            if(($value -split '\s+')[0] -cne $s.intent_sha256){throw 'INTENT_MISMATCH'}
            $text=Wsl @('--distribution','Ubuntu','--user','root','--exec','/usr/bin/cat',$path)
            if(!$text.Trim().StartsWith('{') -or !$text.Trim().EndsWith('}')){throw 'INTENT_MISMATCH'}
            $intent=$text | ConvertFrom-Json -ErrorAction Stop
            $names=@($intent.PSObject.Properties.Name)
            $expected=@($s.Keys | Where-Object{$_ -cne 'intent_sha256'})+@('bridge_running','recovery')
            if((($names | Sort-Object) -join '|') -cne (($expected | Sort-Object) -join '|')){throw 'INTENT_MISMATCH'}
            foreach($name in $expected){
                if([regex]::Matches($text,('"'+[regex]::Escape($name)+'"\s*:')).Count -ne 1){throw 'INTENT_MISMATCH'}
                if($name -ceq 'bridge_running'){
                    if($intent.$name -isnot [bool]){throw 'INTENT_MISMATCH'}
                }elseif($name -ceq 'recovery'){
                    ValidateRecoveryBinding $intent.recovery $text
                }elseif($intent.$name.GetType() -ne $s[$name].GetType() -or $intent.$name -cne $s[$name]){throw 'INTENT_MISMATCH'}
            }
            $after=Wsl @('--distribution','Ubuntu','--user','root','--exec','/usr/bin/sha256sum',$path)
            if(($after -split '\s+')[0] -cne $s.intent_sha256){throw 'INTENT_MISMATCH'}
            return $intent
        }
        function Intent($Ignored,$Before){
            $intent=ReadIntent
            if($intent.bridge_running -ne $Before.bridge_running -or
                (Get-WslMaintenanceDigest $intent.recovery) -cne (Get-WslMaintenanceDigest $Before.recovery)){throw 'INTENT_MISMATCH'}
        }
        function ValidateRecoveryBinding($Binding,[string]$Text){
            $names=@('guest_graph','guest_details','os','firewall','hosts','bridge','registry_structure',
                'state_static','old_address','netsh_layout','resource_config','resource_file','resource_metadata','resource_metrics')
            if($Binding -isnot [PSCustomObject] -or ((@($Binding.PSObject.Properties.Name | Sort-Object)) -join '|') -cne (($names | Sort-Object) -join '|')){throw 'INTENT_MISMATCH'}
            foreach($name in $names){
                if([regex]::Matches($Text,('"'+$name+'"\s*:')).Count -ne 1){throw 'INTENT_MISMATCH'}
                if($name -eq 'resource_metrics'){continue}
                if($Binding.$name -isnot [string] -or
                    ($Binding.$name -cnotmatch '\A[0-9a-f]{64}\z' -and !($name -eq 'resource_file' -and $Binding.$name -ceq 'absent'))){throw 'INTENT_MISMATCH'}
            }
            $metrics=@('physical_bytes','cpu_count','effective_memory_bytes','effective_cpus','effective_swap_bytes')
            if($Binding.resource_metrics -isnot [PSCustomObject] -or
                ((@($Binding.resource_metrics.PSObject.Properties.Name | Sort-Object)) -join '|') -cne (($metrics | Sort-Object) -join '|')){throw 'INTENT_MISMATCH'}
            foreach($name in $metrics){
                $value=$Binding.resource_metrics.$name
                if([regex]::Matches($Text,('"'+$name+'"\s*:')).Count -ne 1 -or
                    ($null -ne $value -and (($value -isnot [int] -and $value -isnot [long]) -or $value -lt 0))){throw 'INTENT_MISMATCH'}
            }
        }
        function ReadResourceBackup($Recovery){
            $store=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'TinySwarmWorld/preparation'
            $old=[byte[]]@();$metadata=$null
            if($Recovery.resource_file -cne 'absent'){
                & $preparation {param($p) Assert-PreparationEvidencePath $p} $store
                $backups=@(Get-ChildItem -LiteralPath $store -Filter 'wslconfig-*.backup' -File -ErrorAction Stop)
                $records=@(Get-ChildItem -LiteralPath $store -Filter '*.json' -File -ErrorAction Stop)
                if($backups.Count -gt 256 -or $records.Count -gt 512){throw 'RECOVERY_EVIDENCE_LIMIT'}
                $matched=$null
                foreach($file in $backups){
                    if($file.Name -cnotmatch '\Awslconfig-[0-9a-f]{32}\.backup\z' -or $file.Length -gt 1048576){throw 'RECOVERY_EVIDENCE_LIMIT'}
                    & $preparation {param($p) Assert-PreparationEvidencePath $p} $file.FullName
                    if((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $Recovery.resource_file){$matched=$file;break}
                }
                if($null -eq $matched){throw 'RECOVERY_BACKUP_UNPROVEN'}
                $total=0
                foreach($record in $records){
                    $total+=$record.Length
                    if($record.Length -gt 262144 -or $total -gt 8388608){throw 'RECOVERY_EVIDENCE_LIMIT'}
                    & $preparation {param($p) Assert-PreparationEvidencePath $p} $record.FullName
                    $entry=Get-Content -LiteralPath $record.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
                    if($entry.PSObject.Properties.Name -notcontains 'event' -or $entry.event -cne 'backup_metadata'){continue}
                    if([StringComparer]::OrdinalIgnoreCase.Equals([string]$entry.backup_path,$matched.FullName) -and
                        (Get-WslMaintenanceDigest $entry.original_metadata) -ceq $Recovery.resource_metadata){$metadata=[string]$entry.original_metadata;break}
                }
                if($null -eq $metadata){throw 'RECOVERY_BACKUP_UNPROVEN'}
                $old=[IO.File]::ReadAllBytes($matched.FullName)
            }
            return @{bytes=$old;metadata=$metadata}
        }
        function VerifyRecoveryResources($Intent,$Facts){
            $current=$Facts.resource_facts.config_snapshot
            if((Get-WslMaintenanceDigest $current) -ceq $Intent.recovery.resource_config){return}
            # Recompute the exact W05 intended bytes from its existing protected
            # backup. Never replay Apply or write/restore global configuration.
            $backup=ReadResourceBackup $Intent.recovery
            $old=[byte[]]$backup.bytes;$metadata=$backup.metadata
            if($Intent.recovery.resource_file -cne 'absent'){
                $sha=[Security.Cryptography.SHA256]::Create()
                try{$oldHash=([BitConverter]::ToString($sha.ComputeHash($old))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
                if($oldHash -cne $Intent.recovery.resource_file -or
                    (Get-WslMaintenanceDigest $metadata) -cne $Intent.recovery.resource_metadata){throw 'RECOVERY_BACKUP_UNPROVEN'}
            }elseif($old.Length -ne 0 -or $null -ne $metadata){throw 'RECOVERY_BACKUP_UNPROVEN'}
            $merged=& $preparation {param($b) ConvertTo-PreparationWslConfig (ConvertFrom-PreparationWslConfig $b) @{memory_gib=21;processors=8;swap_gib=6}} $old
            $sha=[Security.Cryptography.SHA256]::Create()
            try{$expected=([BitConverter]::ToString($sha.ComputeHash([byte[]]$merged))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
            if($current.hash -cne $expected){throw 'RECOVERY_CONFIG_UNPROVEN'}
            if($null -ne $metadata){
                $oldMeta=[regex]::Match($metadata,'\A(.*)\|([^|]*)\|([0-9]+)\|([0-9]+)\|([0-9]+)\z')
                $newMeta=[regex]::Match([string]$current.metadata,'\A(.*)\|([^|]*)\|([0-9]+)\|([0-9]+)\|([0-9]+)\z')
                if(!$oldMeta.Success -or !$newMeta.Success){throw 'RECOVERY_CONFIG_UNPROVEN'}
                foreach($index in @(1,2,3)){if($oldMeta.Groups[$index].Value -cne $newMeta.Groups[$index].Value){throw 'RECOVERY_CONFIG_UNPROVEN'}}
            }
        }
        function Recover {
            $result=[ordered]@{schema_version=1;scope='WSL_RESOURCE_MAINTENANCE_RECOVERY';status='RECOVERY_REQUIRED';
                phase='ADMISSION';reentry_attempted=$false;bridge_restored=$false;resource_verified=$false;
                route_changes=0;w05_replayed=$false;services_verified=$false}
            $update=$null;$reconcile=$null;$before=$null;$quiesced=$false
            try{
                Source
                $running=@(Running)
                if($running.Count -eq 0){$result.reentry_attempted=$true;Relaunch}
                elseif(($running -join ',') -cne 'Ubuntu'){throw 'RUNNING_REGISTRATION_MISMATCH'}
                $intent=ReadIntent
                $guest=Guest;$facts=& $preparationPorts.Inventory $options;$net=Snapshot
                if(@($facts.bridge_facts.blockers | Where-Object{$_ -cne 'foreign_portproxy_rule'}).Count -ne 0){throw 'RECOVERY_LISTENER_UNPROVEN'}
                $static=StableState $net.state;$static.Remove('wslIp')
                if($net.service_state -notin @('Running','Stopped') -or
                    (!$intent.bridge_running -and $net.running) -or
                    $guest.graph -cne $intent.recovery.guest_graph -or $guest.details -cne $intent.recovery.guest_details -or
                    (Get-WslMaintenanceDigest (LinuxBinding $facts)) -cne $intent.recovery.os -or
                    $net.identity -cne $intent.recovery.bridge -or $net.firewall -cne $intent.recovery.firewall -or
                    $net.hosts -cne $intent.recovery.hosts -or $net.netsh.layout -cne $intent.recovery.netsh_layout -or
                    (Get-WslMaintenanceDigest $static) -cne $intent.recovery.state_static -or
                    (Get-WslMaintenanceDigest (RegistryStructure $net.registry $net.state)) -cne $intent.recovery.registry_structure){throw 'RECOVERY_PRESERVATION_UNPROVEN'}
                VerifyRecoveryResources $intent $facts
                $address=[string]$facts.observed_wsl_address
                Assert-ValidIPv4Address $address 'selected Ubuntu address'
                $ip=[Net.IPAddress]::Parse($address)
                if([Net.IPAddress]::IsLoopback($ip) -or $ip.GetAddressBytes()[0] -eq 0 -or $ip.GetAddressBytes()[0] -ge 224){throw 'ADDRESS_UNVERIFIED'}
                if((Get-WslMaintenanceDigest ([string]$net.state.wslIp)) -cne $intent.recovery.old_address -and $net.state.wslIp -cne $address){throw 'RECOVERY_STATE_UNPROVEN'}
                $config=Read-BridgeConfig $InstalledConfigPath;$registry=Read-TswPortRegistry $InstalledPortRegistryPath
                $mappings=@(Get-PortMappings $config $registry.Mappings)
                if((Get-WslMaintenanceDigest @($net.state.mappings | Sort-Object listenPort)) -cne
                    (Get-WslMaintenanceDigest @($mappings | ForEach-Object{[pscustomobject]@{name=$_.Name;listenPort=$_.ListenPort;connectPort=$_.ConnectPort}} | Sort-Object listenPort))){throw 'RECOVERY_STATE_UNPROVEN'}
                $changes=@(foreach($mapping in $mappings){
                    $name=[string]$net.state.listenAddress+'/'+$mapping.ListenPort
                    $rows=@($net.registry | Where-Object{$_.key -ceq '/v4tov4/tcp' -and $_.name -ceq $name})
                    if($rows.Count -ne 1 -or $rows[0].kind -cne 'String'){throw 'RECOVERY_ROUTE_UNPROVEN'}
                    $parts=[string]$rows[0].value -split '/'
                    if($parts.Count -ne 2 -or $parts[1] -cne [string]$mapping.ConnectPort -or
                        ($parts[0] -cne $address -and (Get-WslMaintenanceDigest $parts[0]) -cne $intent.recovery.old_address)){throw 'RECOVERY_ROUTE_UNPROVEN'}
                    if($parts[0] -cne $address){[ordered]@{name=$name;listen=[string]$net.state.listenAddress;
                        listen_port=[int]$mapping.ListenPort;connect_port=[int]$mapping.ConnectPort;original_address=$parts[0]}}
                })
                $script:expectedRegistry=@($net.registry);$script:stateOriginal=Get-WslMaintenanceDigest $net.state
                $script:stateExpected=$script:stateOriginal;$script:stableExpected=Get-WslMaintenanceDigest (StableState $net.state)
                $before=@{net=$net;guest=$guest;os=$intent.recovery.os;stable_state=$script:stableExpected;
                    bridge_running=$intent.bridge_running;recovery_running=$net.running;old_address=[string]$net.state.wslIp;new_address=$address}
                $update=Lock 'Global\TinySwarmWorldWslBridgeServiceUpdate' 30
                $reconcile=Lock 'Global\TinySwarmWorldWslBridgeReconcile' 30
                CheckPreservation $before 'RECOVERY_ORIGINAL'
                $quiesced=$true
                if($net.running){StopBridge $before}
                CheckPreservation $before 'QUIESCED'
                $result.phase='FORWARD_ROUTES'
                $stateAddress=$before.old_address
                foreach($change in $changes){$before.old_address=$change.original_address;SetRoute $before $change $address;$result.route_changes++}
                $before.old_address=$stateAddress
                CommitState $before $address
                CheckPreservation $before 'FINAL'
                Unlock $reconcile;$reconcile=$null
                RestoreBridge $before;$quiesced=$false
                Final $s $before;$result.bridge_restored=$true
                $plan=Plan;$result.resource_verified=($plan.resources.state -ceq 'VERIFIED' -and @($plan.resources.blockers).Count -eq 0)
                $result.status=$(if($result.resource_verified){'FORWARD_RECOVERY_COMPLETE'}else{'RECOVERY_RESOURCE_STAGE_REQUIRED'})
                $result.phase='COMPLETE'
            }catch{$result.status='RECOVERY_REQUIRED'}finally{
                if($null -ne $reconcile){try{Unlock $reconcile}catch{};$reconcile=$null}
                if($quiesced -and $null -ne $before){
                    try{BeginRecovery;CheckPreservation $before 'RECOVERY';RestoreBridge $before;Final $s $before;$result.bridge_restored=$true}catch{}
                }
                if($null -ne $update){try{Unlock $update}catch{$result.status='RECOVERY_REQUIRED'}}
            }
            return $result
        }
        Export-ModuleMember -Function Observe,Lock,Unlock,StopBridge,Plan,Apply,CheckPreservation,Shutdown,Relaunch,Effective,Address,Routes,SetRoute,CommitState,RestoreBridge,Final,Intent,BeginRecovery,Recover
    }
    $ports=@{}
    foreach($name in @('Observe','Lock','Unlock','StopBridge','Plan','Apply','CheckPreservation','Shutdown','Relaunch',
        'Effective','Address','Routes','SetRoute','CommitState','RestoreBridge','Final','Intent','BeginRecovery','Recover')){
        $ports[$name]={& $module {param($command,$arguments) & $command @arguments} $name $args}.GetNewClosure()
    }
    return $ports
}

if($MyInvocation.InvocationName -ne '.'){
    try{
        if($ExpectedScenarioSha256 -cnotmatch '\A[0-9a-f]{64}\z' -or $ScenarioBase64.Length -gt 32768){throw 'SCENARIO_INVALID'}
        $bytes=[Convert]::FromBase64String($ScenarioBase64)
        $hash=[Security.Cryptography.SHA256]::Create()
        try{$actual=([BitConverter]::ToString($hash.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose()}
        if($actual -cne $ExpectedScenarioSha256){throw 'SCENARIO_MISMATCH'}
        $text=([Text.UTF8Encoding]::new($false,$true)).GetString($bytes)
        if(!$text.Trim().StartsWith('{') -or !$text.Trim().EndsWith('}')){throw 'SCENARIO_INVALID'}
        $object=$text | ConvertFrom-Json -ErrorAction Stop
        foreach($property in $object.PSObject.Properties){
            if([regex]::Matches($text,('"'+[regex]::Escape($property.Name)+'"\s*:')).Count -ne 1){throw 'SCENARIO_DUPLICATE_KEY'}
        }
        $scenario=@{};foreach($property in $object.PSObject.Properties){$scenario[$property.Name]=$property.Value}
        Assert-WslMaintenanceScenario $scenario
        $ports=New-WslMaintenanceProductionPorts $scenario
        if($Mode -ceq 'Prepare'){
            $before=& $ports.Observe $scenario
            $result=@{schema_version=1;scope='WSL_RESOURCE_MAINTENANCE_PROPOSAL';status='PROPOSAL_ONLY';
                source_commit=$scenario.source_commit;prestate_sha256=$before.prestate_sha256;
                bridge_running=$before.bridge_running;recovery=$before.recovery;
                runtime_effect_attempted=$false;services_verified=$false}
        }elseif($Mode -ceq 'Recover'){$result=& $ports.Recover}
        else{$result=Invoke-WslResourceMaintenance $scenario $ports}
    }catch{$result=@{schema_version=1;scope='WSL_RESOURCE_MAINTENANCE';status='BLOCKED';error='SCENARIO_OR_ADAPTER_INVALID';services_verified=$false}}
    $result | ConvertTo-Json -Depth 8 -Compress
    if($result.status -in @('PROPOSAL_ONLY','MAINTENANCE_COMPLETE','FORWARD_RECOVERY_COMPLETE')){exit 0}else{exit 2}
}
