#requires -Version 5.1
<# Qualification-only binding of an existing protected bridge; no guest lifecycle. #>
[CmdletBinding()]
param([ValidateSet('Prepare','Archive','StopOriginal','Bind','StageRestore','ResumeOriginal','Recover')][string]$Mode='Prepare',
      [ValidateSet('Archive','StopOriginal','Bind','StageRestore','ResumeOriginal','Recover')][string]$PrepareFor='Archive',
      [string]$ScenarioBase64='',[string]$ExpectedScenarioSha256='',
      [string]$ApprovalBase64='',[string]$ExpectedApprovalSha256='')
$ErrorActionPreference='Stop'

function Get-WslBindingCanonical($Value) {
    if($null -eq $Value -or $Value -is [string] -or $Value -is [ValueType]){return $Value}
    if($Value -is [Collections.IDictionary]){
        $r=[ordered]@{};foreach($k in @($Value.Keys | Sort-Object)){$r[$k]=Get-WslBindingCanonical $Value[$k]};return $r
    }
    if($Value -is [Collections.IEnumerable]){return ,@($Value | ForEach-Object{Get-WslBindingCanonical $_})}
    $r=[ordered]@{};foreach($p in @($Value.PSObject.Properties | Sort-Object Name)){$r[$p.Name]=Get-WslBindingCanonical $p.Value};return $r
}
function Get-WslBindingBytes($Value) {
    return ,([Text.UTF8Encoding]::new($false,$true)).GetBytes((ConvertTo-Json -InputObject (Get-WslBindingCanonical $Value) -Depth 90 -Compress))
}
function Get-WslBindingRawHash([byte[]]$Bytes) {
    $sha=[Security.Cryptography.SHA256]::Create()
    try{return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
}
function Get-WslBindingHash($Value){return Get-WslBindingRawHash (Get-WslBindingBytes $Value)}
function Assert-WslBindingFields($Value,[string[]]$Names,[string]$Code) {
    $keys=if($Value -is [Collections.IDictionary]){@($Value.Keys)}else{@($Value.PSObject.Properties.Name)}
    if($null -eq $Value -or $keys.Count -ne $Names.Count){throw $Code}
    foreach($key in $keys){if($key -isnot [string] -or $key -cnotin $Names){throw $Code}}
}
function Read-WslBindingWire([string]$Base64,[string]$Expected) {
    if($Expected -cnotmatch '\A[0-9a-f]{64}\z' -or $Base64.Length -gt 90000){throw 'BINDING_WIRE_INVALID'}
    $bytes=[Convert]::FromBase64String($Base64)
    if($bytes.Length -gt 65536 -or (Get-WslBindingRawHash $bytes) -cne $Expected){throw 'BINDING_WIRE_HASH'}
    $text=([Text.UTF8Encoding]::new($false,$true)).GetString($bytes)
    $value=$text | ConvertFrom-Json -ErrorAction Stop
    # Duplicate/aliased JSON properties cannot survive this exact canonical wire
    # comparison. Source coordinators use this same pure canonical encoder.
    if([Convert]::ToBase64String((Get-WslBindingBytes $value)) -cne [Convert]::ToBase64String($bytes)){throw 'BINDING_WIRE_NONCANONICAL'}
    return $value
}
function Assert-WslBindingScenario($s) {
    Assert-WslBindingFields $s @('schema_version','run_id','source_commit','source_root','host','original_distro','new_distro',
        'original_guid','new_guid','original_vhd_sha256','new_vhd_sha256','firewall_query_sha256','pins','exposure_sha256') 'BINDING_SCENARIO'
    if($s.schema_version -isnot [int] -or $s.schema_version -ne 1 -or $s.run_id -isnot [string] -or $s.run_id -cnotmatch '\A[0-9a-f]{32}\z' -or
        $s.source_commit -isnot [string] -or $s.source_commit -cnotmatch '\A[0-9a-f]{40}\z' -or
        $s.source_root -isnot [string] -or $s.source_root -cnotmatch '\A[A-Za-z]:[\\/][^\x00-\x1f]{1,220}\z' -or
        $s.host -isnot [string] -or $s.host -cnotmatch '\A[A-Za-z0-9][A-Za-z0-9.-]{0,62}\z' -or
        $s.original_distro -cne 'Ubuntu' -or $s.new_distro -cne ('TSW-Q440-'+$s.run_id)){throw 'BINDING_SCENARIO'}
    foreach($key in @('original_guid','new_guid')){
        if($s.$key -isnot [string] -or $s.$key -cnotmatch '\A\{[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\}\z'){throw 'BINDING_REGISTRATION_ID'}
    }
    if($s.original_guid -ceq $s.new_guid){throw 'BINDING_REGISTRATION_ID'}
    foreach($key in @('original_vhd_sha256','new_vhd_sha256','firewall_query_sha256','exposure_sha256')){
        if($s.$key -isnot [string] -or $s.$key -cnotmatch '\A[0-9a-f]{64}\z'){throw 'BINDING_SCENARIO'}
    }
}
function Assert-WslBindingCertificate($c,[string]$Query) {
    Assert-WslBindingFields $c @('schema_version','query_sha256','snapshot_sha256','snapshot_bytes',
        'snapshot_schema_version','store','association_model','counts') 'BINDING_FIREWALL_CERTIFICATE'
    if($c.schema_version -cne 'tsw.windows-firewall-certificate.v1' -or $c.query_sha256 -cne $Query -or
        $c.snapshot_sha256 -isnot [string] -or $c.snapshot_sha256 -cnotmatch '\A[0-9a-f]{64}\z' -or
        ($c.snapshot_bytes -isnot [int] -and $c.snapshot_bytes -isnot [long]) -or
        $c.snapshot_bytes -lt 0 -or $c.snapshot_bytes -gt 14680064 -or
        $c.snapshot_schema_version -isnot [int] -or $c.snapshot_schema_version -ne 2 -or
        $c.store -cne 'ActiveStore' -or $c.association_model -cne 'PROVIDER_IDENTITY_ONE_TO_ONE'){throw 'BINDING_FIREWALL_CERTIFICATE'}
    Assert-WslBindingFields $c.counts @('rules','profiles','settings','address','application','interface','interface_type','port','security','service') 'BINDING_FIREWALL_COUNTS'
    foreach($k in @('rules','profiles','settings','address','application','interface','interface_type','port','security','service')){
        $n=$c.counts.$k
        if(($n -isnot [int] -and $n -isnot [long]) -or $n -lt 0 -or $n -gt 20000){throw 'BINDING_FIREWALL_COUNTS'}
        if($k -notin @('rules','profiles','settings') -and $n -ne $c.counts.rules){throw 'BINDING_FIREWALL_COUNTS'}
    }
}
function Get-WslBindingPhaseSeconds([string]$Phase) {
    switch -CaseSensitive ($Phase){'Prepare'{180};'Archive'{180};'StopOriginal'{180};'Bind'{360};'StageRestore'{180};'ResumeOriginal'{360};'Recover'{300};default{throw 'BINDING_PHASE'}}
}
function Assert-WslBindingApproval($g,$s,[string]$Phase,[string]$Before) {
    $fields=@('schema_version','decision','phase','scenario_sha256','source_commit','proposal_sha256','expires_at_utc','reviews')
    if($Phase -cin @('StopOriginal','StageRestore')){$fields+='guest_quiesce_sha256'}
    Assert-WslBindingFields $g $fields 'BINDING_GO'
    if($g.schema_version -isnot [int] -or $g.schema_version -ne 1 -or $g.decision -cne 'GO' -or $g.phase -cne $Phase -or
        $g.scenario_sha256 -cne (Get-WslBindingHash $s) -or $g.source_commit -cne $s.source_commit -or
        $g.proposal_sha256 -cne $Before){throw 'BINDING_GO'}
    if($g.proposal_sha256 -isnot [string] -or $g.proposal_sha256 -cnotmatch '\A[0-9a-f]{64}\z'){throw 'BINDING_GO'}
    if($Phase -cin @('StopOriginal','StageRestore') -and ($g.guest_quiesce_sha256 -isnot [string] -or $g.guest_quiesce_sha256 -cnotmatch '\A[0-9a-f]{64}\z')){throw 'BINDING_GUEST_QUIESCE_RECEIPT'}
    Assert-WslBindingFields $g.reviews @('requirements','architecture','security','devops','test_evidence') 'BINDING_REVIEWS'
    foreach($key in @('requirements','architecture','security','devops','test_evidence')){if($g.reviews.$key -cne 'APPROVED'){throw 'BINDING_REVIEWS'}}
    $expiry=[DateTimeOffset]::Parse([string]$g.expires_at_utc)
    $left=($expiry-[DateTimeOffset]::UtcNow).TotalSeconds;$budget=Get-WslBindingPhaseSeconds $Phase
    if($left -lt $budget -or $left -gt ($budget+300)){throw 'BINDING_GO_EXPIRED'}
}

function Invoke-WslAcceptanceBridgeBinding {
    param($Scenario,[string]$Phase,$Approval,[Collections.IDictionary]$Ports,[string]$PrepareFor='Archive')
    $summary=[ordered]@{schema_version=1;scope='PRESERVING_ACCEPTANCE_BRIDGE';phase=$Phase;status='BLOCKED';
        changed=$false;recovery_required=$false;application_ready=$false;error='NONE'}
    $update=$null;$reconcile=$null;$activeIntent=$false
    try{
        Assert-WslBindingScenario $Scenario
        foreach($name in @('Begin','Observe','Intent','Lock','Unlock','Archive','Stage','Switch','Protect','Stop','Stopped','Start','Heartbeat','Final','Complete','Pending','Recover','Failure')){
            if(!$Ports.Contains($name) -or $Ports[$name] -isnot [scriptblock]){throw 'BINDING_PORTS'}
        }
        & $Ports.Begin $Phase | Out-Null
        if($Phase -ceq 'Prepare'){
            if($PrepareFor -cnotin @('Archive','StopOriginal','Bind','StageRestore','ResumeOriginal','Recover')){throw 'BINDING_PHASE'}
            $before=& $Ports.Observe $PrepareFor
            $summary.status='PREPARED_READ_ONLY';$summary.proposal_sha256=$before.fingerprint
            $summary.target_phase=$PrepareFor
            return $summary
        }
        Assert-WslBindingApproval $Approval $Scenario $Phase $Approval.proposal_sha256
        $update=& $Ports.Lock 'Global\TinySwarmWorldWslBridgeServiceUpdate'
        $reconcile=& $Ports.Lock 'Global\TinySwarmWorldWslBridgeReconcile'
        $before=& $Ports.Observe $Phase
        if($before.fingerprint -cne $Approval.proposal_sha256){throw 'BINDING_PRESTATE_DRIFT'}
        $fresh=$before
        & $Ports.Intent $Phase $fresh $Approval | Out-Null
        if($Phase -ceq 'Archive'){
            & $Ports.Archive $fresh | Out-Null
            $summary.changed=$true;$summary.status='ORIGINAL_ARCHIVED'
            return $summary
        }
        if($Phase -ceq 'Recover'){
            $activeIntent=$true
            & $Ports.Stop $fresh | Out-Null
            & $Ports.Recover $fresh | Out-Null
            $summary.changed=$true;$summary.status='RECOVERED_STOPPED'
            return $summary
        }
        if($Phase -ceq 'StopOriginal'){
            $activeIntent=$true
            & $Ports.Stop $fresh | Out-Null
            & $Ports.Stopped $Phase | Out-Null
            $summary.changed=$true;$summary.status='ORIGINAL_BRIDGE_STOPPED'
            return $summary
        }
        if($Phase -ceq 'ResumeOriginal'){
            & $Ports.Pending $fresh | Out-Null
            $bundle=$fresh.original_bundle_id
        }else{
            $stage=& $Ports.Stage $Phase $fresh
            $activeIntent=$true
            & $Ports.Stop $fresh | Out-Null
            & $Ports.Switch $stage $fresh | Out-Null
            & $Ports.Protect | Out-Null
            & $Ports.Stopped $Phase | Out-Null
            $bundle=$stage.BundleId
        }
        $summary.changed=$true
        if($Phase -ceq 'StageRestore'){
            $summary.status='ORIGINAL_PAYLOAD_STAGED_STOPPED'
            return $summary
        }
        & $Ports.Unlock $reconcile | Out-Null;$reconcile=$null
        $activeIntent=$true
        $started=& $Ports.Start $fresh
        & $Ports.Heartbeat $started $bundle | Out-Null
        & $Ports.Final $Phase $fresh $bundle | Out-Null
        & $Ports.Complete $Phase | Out-Null
        $summary.status=if($Phase -ceq 'Bind'){'NEW_BINDING_READY'}else{'ORIGINAL_BINDING_RESTORED'}
        return $summary
    }catch{
        $code='BINDING_FAILURE_REDACTED'
        if($_.Exception.Message -cmatch '\ABINDING_[A-Z0-9_]{1,80}\z'){$code=$_.Exception.Message}
        $summary.error=$code;$summary.recovery_required=$activeIntent
        try{& $Ports.Failure $code $activeIntent | Out-Null}catch{}
        # Never start an original-bound service as automatic rollback while the
        # new guest runs. Explicit Recover/Resume have their own fresh phase GO.
        return $summary
    }finally{
        if($null -ne $reconcile){& $Ports.Unlock $reconcile | Out-Null}
        if($null -ne $update){& $Ports.Unlock $update | Out-Null}
    }
}

function Get-WslBindingProcessArguments([string]$File,[string[]]$Arguments) {
    # ProcessStartInfo.Arguments uses the Windows native quoting contract. Bound
    # the actual quoted command line, including executable quotes and NUL.
    if(!$File -or $File.Contains("`0")){throw 'BINDING_COMMAND_ARGUMENT'}
    $quoted=foreach($arg in $Arguments){
        if($null -eq $arg -or $arg.Contains("`0")){throw 'BINDING_COMMAND_ARGUMENT'}
        if($arg -cmatch '\A[A-Za-z0-9_./:=+-]+\z'){$arg}
        else{'"'+([regex]::Replace(([regex]::Replace($arg,'(\\*)"','$1$1\"')),'(\\+)$','$1$1'))+'"'}
    }
    $text=$quoted -join ' '
    if($File.Length+2+1+$text.Length+1 -gt 32767){throw 'BINDING_COMMAND_LINE_BOUND'}
    return $text
}
function Get-WslBindingCertificateArguments([string]$Command) {
    if(!$Command -or $Command.Length -gt 30000 -or $Command.Contains("`0")){throw 'BINDING_FIREWALL_COMMAND'}
    # The loader supplies exact hash-verified source. Keep it a single final
    # -Command argument; UTF16 Base64 would exceed CreateProcess's native cap.
    return ,@('-NoProfile','-NonInteractive','-Command',$Command)
}

function Assert-WslBindingStartPayload($Scenario,[string]$Phase,$Payload,$Descriptor,$Registrations,[string[]]$Running) {
    if($Phase -cnotin @('Bind','ResumeOriginal')){throw 'BINDING_START_PHASE'}
    $expected=if($Phase -ceq 'Bind'){$Scenario.new_distro}else{$Scenario.original_distro}
    $hashes=if($Phase -ceq 'Bind'){$Descriptor.bound_hashes}else{$Descriptor.archive_hashes}
    if($Payload.status -cne 'Stopped' -or $null -eq $hashes -or
        (Get-WslBindingHash $Payload.hashes) -cne (Get-WslBindingHash $hashes) -or
        $Payload.policy_sha256 -cne $Descriptor.original.policy_sha256 -or
        $Registrations.hash -cne $Descriptor.original.registration_sha256 -or
        $Running.Count -ne 1 -or $Running[0] -cne $expected){throw 'BINDING_START_CAS'}
    $distro=''
    if($Payload.config.PSObject.Properties.Name -ccontains 'distro'){
        if($Payload.config.distro -isnot [string]){throw 'BINDING_START_CONFIG'}
        $distro=$Payload.config.distro
    }
    if($Phase -ceq 'Bind'){
        if($distro -cne $Scenario.new_distro){throw 'BINDING_START_CONFIG'}
    }else{
        if((Get-WslBindingHash $Payload.config) -cne (Get-WslBindingHash $Descriptor.original.config) -or
            $distro -cnotin @('','auto',$Scenario.original_distro)){throw 'BINDING_START_CONFIG'}
        if($distro -cin @('','auto') -and $Registrations.default_guid -cne $Scenario.original_guid){throw 'BINDING_ORIGINAL_DEFAULT_GUID'}
    }
}

function New-WslAcceptanceBridgeProductionPorts($Scenario) {
    Assert-WslBindingScenario $Scenario
    $root=[IO.Path]::GetFullPath($Scenario.source_root)
    $actor=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    foreach($path in @($root,(Join-Path $root '.git'))){
        $item=Get-Item -LiteralPath $path -Force
        if(!$item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
            (Get-Acl -LiteralPath $path).GetOwner([Security.Principal.SecurityIdentifier]).Value -cne $actor){throw 'BINDING_SOURCE_OWNER'}
    }
    $assets=@('tools/windows/qualification/wsl_acceptance_bridge_binding.ps1','tools/windows/qualification/wsl_resource_maintenance.ps1',
        'tools/windows/qualification/windows_firewall_snapshot.ps1','tools/windows/qualification/windows_firewall_certificate.ps1',
        'bootstrap/windows/tws-wsl-bridge.ps1','bootstrap/windows/tws-wsl-bridge-service.ps1')
    Assert-WslBindingFields $Scenario.pins $assets 'BINDING_SOURCE_PINS'
    # Verify bytes before dot sourcing any helper. Hash-matched source is read
    # locked for construction; no helper code executes on a hash mismatch.
    $handles=[Collections.Generic.List[IDisposable]]::new()
    try{
        foreach($relative in $assets){
            $path=Join-Path $root $relative;$item=Get-Item -LiteralPath $path -Force
            $ancestor=Split-Path -Parent $path
            while($ancestor -ine $root){
                $directory=Get-Item -LiteralPath $ancestor -Force
                if(!$directory.PSIsContainer -or ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'BINDING_SOURCE_REPARSE'}
                $ancestor=Split-Path -Parent $ancestor
                if(!$ancestor){throw 'BINDING_SOURCE_PATH'}
            }
            if($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.Length -gt 2097152){throw 'BINDING_SOURCE_FILE'}
            $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
            $handles.Add($stream)
            if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Scenario.pins.$relative){throw 'BINDING_SOURCE_DRIFT'}
        }
    $module=New-Module -Name ('Epic440BridgeBinding'+$Scenario.run_id) -ArgumentList $Scenario -ScriptBlock {
        param($spec)
        . (Join-Path $spec.source_root 'tools/windows/qualification/wsl_acceptance_bridge_binding.ps1')
        . (Join-Path $spec.source_root 'tools/windows/qualification/wsl_resource_maintenance.ps1')
        . (Join-Path $spec.source_root 'bootstrap/windows/tws-wsl-bridge.ps1') -Action inventory
        $script:bindingSpec=$spec;$script:bindingClock=$null;$script:bindingDeadline=0;$script:bindingCommands=0;$script:bindingBytes=0
        $script:bindingPhase='';$script:bindingTransaction=$null;$script:bindingDescriptor=$null
        $script:bindingArchive=Join-Path $ServiceRoot ('.staging-acceptance-'+$spec.run_id+'-original')
        $script:bindingDescriptorPath=Join-Path $bindingArchive 'descriptor.json'
        $script:bindingPayload=Join-Path $bindingArchive 'payload'
        $script:bindingOld=$null;$script:bindingLast=$null;$script:bindingCertificateCommand=$null

        function Claim([int]$Reserve=1){
            if($null -eq $bindingClock){throw 'BINDING_CLOCK'}
            $remaining=$bindingDeadline-$bindingClock.Elapsed.TotalSeconds
            if($remaining -lt $Reserve -or $bindingCommands -ge 256 -or $bindingBytes -gt 67108864){throw 'BINDING_DEADLINE'}
            $script:bindingCommands++
            return [int][Math]::Floor($remaining)
        }
        function ReadProcess([string]$File,[string[]]$Arguments,[int]$Timeout=15,[switch]$Raw,[int[]]$Expected=@(0)){
            $left=Claim
            $limit=[Math]::Min($Timeout,$left)
            $info=[Diagnostics.ProcessStartInfo]::new();$info.FileName=$File;$info.UseShellExecute=$false
            $info.CreateNoWindow=$true;$info.RedirectStandardInput=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
            $info.WorkingDirectory=[Environment]::GetFolderPath('System')
            $info.EnvironmentVariables['GIT_CONFIG_NOSYSTEM']='1';$info.EnvironmentVariables['GIT_CONFIG_GLOBAL']='NUL'
            $info.EnvironmentVariables['GIT_OPTIONAL_LOCKS']='0'
            $info.Arguments=Get-WslBindingProcessArguments $File $Arguments
            $p=[Diagnostics.Process]::new();$p.StartInfo=$info
            $o=[IO.MemoryStream]::new();$e=[IO.MemoryStream]::new();$launched=$false
            try{
                [void]$p.Start();$launched=$true;$p.StandardInput.Close()
                $out=$p.StandardOutput.BaseStream.CopyToAsync($o);$err=$p.StandardError.BaseStream.CopyToAsync($e)
                $watch=[Diagnostics.Stopwatch]::StartNew()
                while(!$p.WaitForExit(100)){
                    if($watch.Elapsed.TotalSeconds -ge $limit -or $o.Length -gt 2097152 -or $e.Length -gt 2097152){throw 'BINDING_CHILD_BOUND'}
                }
                if(![Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($out,$err),2000) -or
                    $p.ExitCode -notin $Expected -or $o.Length -gt 2097152 -or $e.Length -ne 0){throw 'BINDING_CHILD_FAILED'}
                $script:bindingBytes+=$o.Length+$e.Length;[void](Claim)
                if($Raw){return ,$o.ToArray()}
                return ([Text.UTF8Encoding]::new($false,$true)).GetString($o.ToArray())
            }finally{
                if($launched -and !$p.HasExited){$p.Kill();if(!$p.WaitForExit(5000)){throw 'BINDING_CHILD_NOT_SETTLED'}}
                $p.Dispose();$o.Dispose();$e.Dispose()
            }
        }
        function Source {
            $assets=@('tools/windows/qualification/wsl_acceptance_bridge_binding.ps1','tools/windows/qualification/wsl_resource_maintenance.ps1',
                'tools/windows/qualification/windows_firewall_snapshot.ps1','tools/windows/qualification/windows_firewall_certificate.ps1',
                'bootstrap/windows/tws-wsl-bridge.ps1','bootstrap/windows/tws-wsl-bridge-service.ps1')
            Assert-WslBindingFields $bindingSpec.pins $assets 'BINDING_SOURCE_PINS'
            foreach($relative in $assets){
                $path=Join-Path $bindingSpec.source_root $relative;$item=Get-Item -LiteralPath $path -Force
                if($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
                    $bindingSpec.pins.$relative -cnotmatch '\A[0-9a-f]{64}\z' -or
                    (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $bindingSpec.pins.$relative){throw 'BINDING_SOURCE_DRIFT'}
            }
            $git=Join-Path ${env:ProgramFiles} 'Git\cmd\git.exe'
            $prefix=@('--no-optional-locks','-C',$bindingSpec.source_root,'-c','core.fsmonitor=false','-c','core.hooksPath=NUL','-c','core.untrackedCache=false')
            $head=(ReadProcess $git ($prefix+@('rev-parse','HEAD'))).Trim()
            if($head -cne $bindingSpec.source_commit){throw 'BINDING_SOURCE_DRIFT'}
            if((ReadProcess $git ($prefix+@('config','--local','--includes','--null','--get-regexp','^filter\.')) 15 -Expected @(0,1)).Length){throw 'BINDING_SOURCE_FILTER'}
            if((ReadProcess $git ($prefix+@('status','--porcelain=v1','--untracked-files=all'))).Length){throw 'BINDING_SOURCE_DIRTY'}
            foreach($relative in $assets){
                $blob=ReadProcess $git ($prefix+@('show',($head+':'+$relative))) 15 -Raw
                if((Get-WslBindingRawHash $blob) -cne $bindingSpec.pins.$relative){throw 'BINDING_SOURCE_BLOB'}
            }
            if($null -eq (Get-Command Get-WslMaintenanceFirewallCertificateCommand -ErrorAction SilentlyContinue)){throw 'BINDING_FIREWALL_LOADER_REQUIRED'}
            $script:bindingCertificateCommand=Get-WslMaintenanceFirewallCertificateCommand
        }
        function Certificate {
            if($bindingCertificateCommand -isnot [string] -or !$bindingCertificateCommand){throw 'BINDING_FIREWALL_LOADER_REQUIRED'}
            [void](Claim 120)
            $ps=Join-Path ([Environment]::GetFolderPath('System')) 'WindowsPowerShell\v1.0\powershell.exe'
            $arguments=Get-WslBindingCertificateArguments $bindingCertificateCommand
            $text=ReadProcess $ps $arguments 120
            if($null -eq (Get-Command ConvertFrom-WslMaintenanceFirewallCertificate -ErrorAction SilentlyContinue)){throw 'BINDING_FIREWALL_LOADER_REQUIRED'}
            $c=ConvertFrom-WslMaintenanceFirewallCertificate $text
            Assert-WslBindingCertificate $c $bindingSpec.firewall_query_sha256
            return $c
        }
        function Running {
            $wsl=Join-Path ([Environment]::GetFolderPath('System')) 'wsl.exe'
            $text=ReadProcess $wsl @('--list','--running','--quiet')
            $names=@(($text -replace "`0",'') -split '\r?\n' | ForEach-Object{$_.Trim()} | Where-Object{$_})
            if(@($names | Select-Object -Unique).Count -ne $names.Count){throw 'BINDING_RUNNING_AMBIGUOUS'}
            return $names
        }
        function Address([string]$name){
            $names=@(Running)
            if($names.Count -ne 1 -or $names[0] -cne $name){throw 'BINDING_RUNNING_SCOPE'}
            $exe=Join-Path ([Environment]::GetFolderPath('System')) 'wsl.exe'
            $text=ReadProcess $exe @('--distribution',$name,'--exec','hostname','-I')
            $tokens=@($text.Trim() -split '\s+' | Where-Object{$_})
            $ip=$null
            if($tokens.Count -lt 1 -or $tokens.Count -gt 16 -or ![Net.IPAddress]::TryParse($tokens[0],[ref]$ip) -or
                $ip.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork -or [Net.IPAddress]::IsLoopback($ip) -or
                $ip.GetAddressBytes()[0] -eq 0 -or $ip.GetAddressBytes()[0] -ge 224){throw 'BINDING_ADDRESS'}
            $after=@(Running)
            if($after.Count -ne 1 -or $after[0] -cne $name){throw 'BINDING_RUNNING_DRIFT'}
            return $ip.ToString()
        }
        function Registrations {
            $key=Get-Item -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'
            $default=[string]$key.GetValue('DefaultDistribution','')
            $rows=@();$bound=@{};$namesSeen=@{}
            foreach($entry in @(Get-ChildItem -LiteralPath $key.PSPath)){
                if($rows.Count -ge 128){throw 'BINDING_REGISTRATION_BOUND'}
                $values=[ordered]@{}
                foreach($name in @($entry.GetValueNames() | Sort-Object)){
                    if($values.Count -ge 64){throw 'BINDING_REGISTRATION_BOUND'}
                    if($name -cne 'State'){$values[$name]=@($entry.GetValueKind($name).ToString(),$entry.GetValue($name,$null,[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames))}
                }
                $distro=$entry.GetValue('DistributionName','');$guid=$entry.PSChildName.ToLowerInvariant()
                if($distro -isnot [string] -or !$distro -or $namesSeen.ContainsKey($distro)){throw 'BINDING_REGISTRATION_AMBIGUOUS'}
                $namesSeen[$distro]=$true
                $rows+=@{guid=$guid;values=$values}
                if($distro -cin @($bindingSpec.original_distro,$bindingSpec.new_distro)){
                    $version=$entry.GetValue('Version',0)
                    if($bound.ContainsKey($distro) -or $entry.GetValueKind('Version') -ne [Microsoft.Win32.RegistryValueKind]::DWord -or
                        $version -isnot [int] -or $version -ne 2){throw 'BINDING_REGISTRATION_AMBIGUOUS'}
                    $base=[string]$entry.GetValue('BasePath','');$disk=[string]$entry.GetValue('VhdFileName','ext4.vhdx')
                    if($base.StartsWith('\\?\')){$base=$base.Substring(4)}
                    if($base -cnotmatch '\A[A-Za-z]:\\' -or $disk -cnotmatch '\A[A-Za-z0-9_.-]+\.vhdx\z'){throw 'BINDING_VHD_PATH'}
                    $base=[IO.Path]::GetFullPath($base)
                    $path=Join-Path $base $disk
                    $parent=$base
                    while($parent){
                        $dir=Get-Item -LiteralPath $parent -Force
                        if(!$dir.PSIsContainer -or ($dir.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'BINDING_VHD_PATH'}
                        $next=Split-Path -Parent $parent
                        if($next -eq $parent){break};$parent=$next
                    }
                    $file=Get-Item -LiteralPath $path -Force
                    if($file.PSIsContainer -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'BINDING_VHD_PATH'}
                    $identity=[TswAcceptanceFileIdentity]::Read($path)
                    $bound[$distro]=@{guid=$guid;vhd_sha256=(Get-WslBindingHash $identity)}
                }
            }
            if($bound.Count -ne 2 -or $bound[$bindingSpec.original_distro].guid -cne $bindingSpec.original_guid -or
                $bound[$bindingSpec.new_distro].guid -cne $bindingSpec.new_guid -or
                $bound[$bindingSpec.original_distro].vhd_sha256 -cne $bindingSpec.original_vhd_sha256 -or
                $bound[$bindingSpec.new_distro].vhd_sha256 -cne $bindingSpec.new_vhd_sha256){throw 'BINDING_REGISTRATION_DRIFT'}
            return @{hash=(Get-WslBindingHash @($default,@($rows | Sort-Object guid)));default_guid=$default.ToLowerInvariant()}
        }
        function InitializeFileIdentity {
            if('TswAcceptanceFileIdentity' -as [type]){return}
            Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;using Microsoft.Win32.SafeHandles;
public static class TswAcceptanceFileIdentity {
 [StructLayout(LayoutKind.Sequential,Pack=4)] struct Info { public uint attr;public long created,accessed,written;public uint volume,hi,lo,links,indexHi,indexLo; }
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern SafeFileHandle CreateFile(string p,uint a,uint s,IntPtr x,uint d,uint f,IntPtr t);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandle(SafeFileHandle h,out Info i);
 public static string Read(string p){using(var h=CreateFile(p,128,7,IntPtr.Zero,3,0x02200000,IntPtr.Zero)){Info i;if(h.IsInvalid||!GetFileInformationByHandle(h,out i)||(i.attr&1024)!=0||i.links!=1)throw new InvalidOperationException("BINDING_VHD_HANDLE");return i.volume.ToString("x8")+":"+i.indexHi.ToString("x8")+i.indexLo.ToString("x8")+":"+i.attr.ToString("x8")+":"+i.links.ToString("x8");}}
}
'@
        }
        function Payload {
            Assert-BridgeServicePathSafety
            if(!(Test-BridgeServiceAclHardened)){throw 'BINDING_ACL'}
            $owner=Get-BridgeServiceOwnership
            if($owner.Status -cne 'owned' -or $owner.RequiresAdoption -or $null -eq $owner.Service -or
                !(Test-BridgeServiceDefinitionOwned) -or @($owner.Service.DependentServices).Count -ne 0){throw 'BINDING_OWNER'}
            if(!(Test-BridgeServiceLogOnRight -AccountName (Get-CurrentBridgeServiceAccount))){throw 'BINDING_LOGON_RIGHT'}
            if($null -ne (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)){throw 'BINDING_LEGACY_TASK'}
            $hashes=[ordered]@{}
            foreach($path in @($ServiceBundleRoot,$ServiceWrapperPath,$ServiceDefinitionPath,$InstallationManifestPath)){
                $hashes[[IO.Path]::GetFileName($path)]=Get-BridgePayloadFingerprint $path
            }
            $manifest=Get-BridgeInstallationManifest
            Assert-WslBindingFields $manifest @('contractVersion','serviceName','accountSid','serviceAccount','wrapperSha256','logOnRightPreexisting','logOnRightGrantedByTsw','installedAt') 'BINDING_INSTALL_MANIFEST'
            $config=Read-BridgeConfig $InstalledConfigPath
            $state=Get-ProtectedBridgeState
            if($null -ne $state){
                $projection=[ordered]@{}
                foreach($property in $state.PSObject.Properties){if($property.Name -cne 'generatedAt'){$projection[$property.Name]=$property.Value}}
                $state=[pscustomobject]$projection
            }
            return @{hashes=$hashes;bundle_id=(Get-BridgeBundleIdentity).BundleId;config=$config;
                policy_sha256=(Get-WslBindingHash @($owner.Details,$manifest,(Get-Acl $ServiceRoot).Sddl));
                registration_policy_sha256=(Get-WslBindingHash @($owner.Details,(Get-Acl $ServiceRoot).Sddl));
                status=[string]$owner.Service.Status;state=$state}
        }
        function EffectiveDistro($config){
            if($config.PSObject.Properties.Name -cnotcontains 'distro'){return ''}
            if($config.distro -isnot [string]){throw 'BINDING_ORIGINAL_CONFIG'}
            return [string]$config.distro
        }
        function Routes($payload) {
            if($null -eq $payload.state -or $payload.state.contractVersion -ne 2){throw 'BINDING_STATE_AUTHORITY'}
            $all=@(Get-WslMaintenanceRegistrySnapshot)
            $netsh=Join-Path ([Environment]::GetFolderPath('System')) 'netsh.exe'
            $raw=ReadProcess $netsh @('interface','portproxy','show','all') 15 -Raw
            [void](ConvertFrom-WslMaintenanceNetshAll $raw $all)
            $owned=@();$foreign=@();$wanted=@{}
            foreach($m in @($payload.state.mappings)){
                if($m.listenPort -isnot [int] -or $m.connectPort -isnot [int] -or $m.listenPort -lt 1 -or $m.listenPort -gt 65535 -or
                    $m.connectPort -lt 1 -or $m.connectPort -gt 65535 -or $wanted.ContainsKey([string]$m.listenPort)){throw 'BINDING_MAPPING_SCHEMA'}
                $wanted[[string]$m.listenPort]=[string]$m.connectPort
            }
            if($wanted.Count -lt 1 -or $wanted.Count -gt 64){throw 'BINDING_MAPPING_SCHEMA'}
            foreach($r in $all){
                $parts=if($r.name -is [string]){@($r.name -split '/')}else{@()}
                if($r.key -ceq '/v4tov4/tcp' -and $r.kind -ceq 'String' -and $parts.Count -eq 2 -and
                    $parts[0] -ceq [string]$payload.state.listenAddress -and $wanted.ContainsKey($parts[1])){
                    if($r.value -cne ([string]$payload.state.wslIp+'/'+$wanted[$parts[1]])){throw 'BINDING_ROUTE_DRIFT'}
                    $owned+=@{key=$r.key;name=$r.name;kind=$r.kind;value=$r.value}
                }else{$foreign+=$r}
            }
            if($owned.Count -ne $wanted.Count){throw 'BINDING_ROUTE_AUTHORITY'}
            $exposure=@($owned | ForEach-Object{ @($_.key,$_.name,(($_.value -split '/')[1])) })
            if((Get-WslBindingHash $exposure) -cne $bindingSpec.exposure_sha256){throw 'BINDING_EXPOSURE_UNAPPROVED'}
            return @{foreign_sha256=(Get-WslBindingHash $foreign);owned=$owned;exposure_sha256=(Get-WslBindingHash $exposure)}
        }
        function Hosts {
            $item=Get-Item -LiteralPath $HostsPath -Force
            if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'BINDING_HOSTS_REPARSE'}
            return Get-WslBindingHash @((Get-FileHash $HostsPath -Algorithm SHA256).Hash,(Get-Acl $HostsPath).Sddl)
        }
        function ReadDescriptor {
            Assert-BridgePayloadPathSafety $bindingDescriptorPath
            $d=Get-Content -LiteralPath $bindingDescriptorPath -Raw -Encoding UTF8 | ConvertFrom-Json
            Assert-WslBindingFields $d @('schema_version','scenario_sha256','original','archive_hashes','phase','phase_intent',
                'transaction_id','bound_hashes','approval_sha256','guest_quiesce_sha256','staging_root','bound_address',
                'rollback_root','transaction_before_hashes','transaction_staged_hashes') 'BINDING_DESCRIPTOR'
            if($d.schema_version -isnot [int] -or $d.schema_version -ne 1 -or $d.scenario_sha256 -cne (Get-WslBindingHash $bindingSpec) -or
                $d.phase -cnotin @('archived','original-stopped','switch-intent','bound-pending','bound','restore-pending','restored','recovered-stopped','recovery-required') -or
                $d.phase_intent -cnotin @('','Archive','StopOriginal','Bind','StageRestore','ResumeOriginal','Recover') -or
                $d.transaction_id -isnot [string] -or ($d.transaction_id -and $d.transaction_id -cnotmatch '\A[0-9a-f]{32}\z')){throw 'BINDING_DESCRIPTOR'}
            Assert-WslBindingFields $d.archive_hashes @('bundle',($ServiceName+'.exe'),($ServiceName+'.xml'),'installation-manifest.json') 'BINDING_DESCRIPTOR'
            foreach($name in @('bundle',($ServiceName+'.exe'),($ServiceName+'.xml'),'installation-manifest.json')){
                if((Get-BridgePayloadFingerprint (Join-Path $bindingPayload $name)) -cne [string]$d.archive_hashes.$name){throw 'BINDING_ARCHIVE_DRIFT'}
            }
            $script:bindingDescriptor=$d;return $d
        }
        function KnownTransaction {
            $d=ReadDescriptor;$tx=Read-BridgeTransactionJournal
            if($null -eq $tx){return $null}
            if($tx.TransactionId -cne $d.transaction_id -or !$tx.ServiceExisted -or !$tx.ServiceRootExisted -or
                $tx.ServiceCreateIntent -or $tx.ServiceCreated -or $tx.StagedPayload.Root -ine $d.staging_root -or
                $tx.RollbackRoot -ine $d.rollback_root){throw 'BINDING_RECOVERY_JOURNAL'}
            foreach($item in $tx.Items){
                $name=[IO.Path]::GetFileName($item.Active)
                if(!$item.OriginalExisted -or $item.OriginalFingerprint -cne $d.transaction_before_hashes.$name -or
                    $item.StagedFingerprint -cne $d.transaction_staged_hashes.$name -or
                    $item.Backup -ine (Join-Path $d.rollback_root $name) -or $item.Staged -ine (Join-Path $d.staging_root $name)){
                    throw 'BINDING_RECOVERY_JOURNAL'
                }
                foreach($candidate in @($item.Active,$item.Backup,$item.Staged)){
                    $fp=Get-BridgePayloadFingerprint $candidate
                    if($fp -and $fp -cnotin @($item.OriginalFingerprint,$item.StagedFingerprint)){throw 'BINDING_RECOVERY_MEMBER_DRIFT'}
                }
            }
            return $tx
        }
        function RecoveryPayload {
            $d=ReadDescriptor;$tx=KnownTransaction
            if($null -eq $tx){
                $p=Payload
                $fp=Get-WslBindingHash $p.hashes
                if($fp -cne (Get-WslBindingHash $d.archive_hashes) -and $fp -cne (Get-WslBindingHash $d.bound_hashes)){throw 'BINDING_RECOVERY_MEMBER_DRIFT'}
                return $p
            }
            $owner=Get-BridgeRecoveryServiceOwnership $tx
            if($owner.Status -cne 'owned' -or $null -eq $owner.Service -or @($owner.Service.DependentServices).Count -ne 0 -or
                (Get-WslBindingHash @($owner.Details,(Get-Acl $ServiceRoot).Sddl)) -cne $d.original.payload.registration_policy_sha256){throw 'BINDING_RECOVERY_OWNER'}
            $hashes=[ordered]@{};foreach($item in $tx.Items){$hashes[[IO.Path]::GetFileName($item.Active)]=Get-BridgePayloadFingerprint $item.Active}
            return @{hashes=$hashes;bundle_id='';config=$null;policy_sha256=$null;incomplete=$true;
                status=[string]$owner.Service.Status;state=(Get-ProtectedBridgeState)}
        }
        function SyncFile([string]$path){$f=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$f.Flush($true)}finally{$f.Dispose()}}
        function SaveDescriptor($d){Write-TextAtomically -Path $bindingDescriptorPath -Text (($d | ConvertTo-Json -Depth 30)+[Environment]::NewLine);Set-BridgeExactAcl $bindingDescriptorPath;SyncFile $bindingDescriptorPath}
        function Snapshot([string]$phase){
            [void](Claim);Source
            $regs=Registrations;$running=@(Running);$p=if($phase -ceq 'Recover'){RecoveryPayload}else{Payload}
            if($phase -ceq 'Archive'){
                if($running.Count -ne 1 -or $running[0] -cne $bindingSpec.original_distro -or $p.status -cne 'Running' -or
                    (Test-Path $TransactionJournalPath)){throw 'BINDING_ORIGINAL_PRESTATE'}
                if((EffectiveDistro $p.config) -cin @('','auto') -and $regs.default_guid -cne $bindingSpec.original_guid){throw 'BINDING_ORIGINAL_DEFAULT_GUID'}
                if((EffectiveDistro $p.config) -cnotin @('','auto',$bindingSpec.original_distro)){throw 'BINDING_ORIGINAL_CONFIG'}
            }else{
                $d=ReadDescriptor
                if($regs.hash -cne $d.original.registration_sha256){throw 'BINDING_REGISTRATION_DRIFT'}
                $only=if($phase -cin @('StopOriginal','ResumeOriginal')){$bindingSpec.original_distro}else{$bindingSpec.new_distro}
                if($phase -cne 'Recover' -and ($running.Count -ne 1 -or $running[0] -cne $only)){throw 'BINDING_RUNNING_SCOPE'}
                if($phase -ceq 'Recover' -and ($running.Count -gt 1 -or @($running | Where-Object{$_ -cnotin @($bindingSpec.original_distro,$bindingSpec.new_distro)}).Count)){throw 'BINDING_RUNNING_SCOPE'}
                if($phase -cin @('Bind','ResumeOriginal') -and $p.status -cne 'Stopped'){throw 'BINDING_SERVICE_NOT_STOPPED'}
                if($phase -ceq 'StopOriginal' -and $p.status -cne 'Running'){throw 'BINDING_ORIGINAL_PRESTATE'}
                if($phase -cne 'Recover' -and $p.policy_sha256 -cne $d.original.policy_sha256){throw 'BINDING_SERVICE_POLICY_DRIFT'}
                if($phase -cin @('Bind','StopOriginal') -and (Get-WslBindingHash $p.hashes) -cne (Get-WslBindingHash $d.archive_hashes)){throw 'BINDING_ACTIVE_CAS'}
                if($phase -ceq 'Bind' -and $d.phase -cne 'original-stopped'){throw 'BINDING_STOP_RECEIPT_REQUIRED'}
                if($phase -ceq 'StageRestore' -and ($d.phase -cne 'bound' -or (Get-WslBindingHash $p.hashes) -cne (Get-WslBindingHash $d.bound_hashes))){throw 'BINDING_BOUND_PAYLOAD_DRIFT'}
                if((EffectiveDistro $d.original.config) -cin @('','auto') -and $regs.default_guid -cne $bindingSpec.original_guid){throw 'BINDING_ORIGINAL_DEFAULT_GUID'}
            }
            $routes=Routes $p;$hosts=Hosts
            $certificate=Certificate
            Assert-WslBindingCertificate $certificate $bindingSpec.firewall_query_sha256
            if($phase -cnotin @('Prepare','Archive')){
                $old=$bindingDescriptor.original
                if($certificate.snapshot_sha256 -cne $old.certificate.snapshot_sha256 -or $routes.foreign_sha256 -cne $old.routes.foreign_sha256 -or $hosts -cne $old.hosts_sha256){throw 'BINDING_FOREIGN_DRIFT'}
            }
            $result=[ordered]@{registration_sha256=$regs.hash;payload=$p;routes=$routes;hosts_sha256=$hosts;certificate=$certificate;
                policy_sha256=$p.policy_sha256;config=$p.config;original_bundle_id=$p.bundle_id}
            $result.observed_address=if($running.Count -eq 1){Address $running[0]}else{''}
            if($phase -cnotin @('Prepare','Archive')){$result.original_bundle_id=$bindingDescriptor.original.payload.bundle_id}
            $result.fingerprint=Get-WslBindingHash $result
            $script:bindingLast=$result;return $result
        }
        function OriginalArchive($before){
            if(Test-Path $bindingArchive){throw 'BINDING_ARCHIVE_EXISTS'}
            [void](Claim 30);New-Item -ItemType Directory -Path $bindingPayload -Force | Out-Null
            Set-BridgeExactAcl $bindingArchive;Set-BridgeExactAcl $bindingPayload
            $d=[ordered]@{schema_version=1;scenario_sha256=(Get-WslBindingHash $bindingSpec);original=$before;
                archive_hashes=$null;phase='archive-intent';phase_intent='Archive';transaction_id='';bound_hashes=$null;
                approval_sha256=$script:bindingApprovalSha;guest_quiesce_sha256='';staging_root='';bound_address='';
                rollback_root='';transaction_before_hashes=$null;transaction_staged_hashes=$null}
            SaveDescriptor $d
            $items=@($ServiceBundleRoot,$ServiceWrapperPath,$ServiceDefinitionPath,$InstallationManifestPath)
            $total=0;$count=0
            foreach($path in $items){
                $rootItem=Get-Item -LiteralPath $path -Force
                $files=if($rootItem.PSIsContainer){@(Get-BridgeTreeItemsNoFollow $path)}else{@($rootItem)}
                foreach($f in $files){$count++;if(!$f.PSIsContainer){$total+=$f.Length};if($count -gt 4096 -or $total -gt 33554432){throw 'BINDING_ARCHIVE_BOUND'}}
            }
            foreach($path in $items){Copy-Item -LiteralPath $path -Destination (Join-Path $bindingPayload ([IO.Path]::GetFileName($path))) -Recurse -ErrorAction Stop}
            foreach($f in @(Get-BridgeTreeItemsNoFollow $bindingArchive)){Set-BridgeExactAcl $f.FullName;if(!$f.PSIsContainer){SyncFile $f.FullName}}
            $hashes=[ordered]@{}
            foreach($path in $items){$name=[IO.Path]::GetFileName($path);$hashes[$name]=Get-BridgePayloadFingerprint (Join-Path $bindingPayload $name)
                if($hashes[$name] -cne $before.payload.hashes.$name -or (Get-BridgePayloadFingerprint $path) -cne $hashes[$name]){throw 'BINDING_ARCHIVE_DRIFT'}}
            $d.archive_hashes=$hashes;$d.phase='archived';$d.phase_intent=''
            SaveDescriptor $d;$script:bindingDescriptor=$d
        }
        function Stage([string]$phase,$before){
            [void](Claim 30);$d=ReadDescriptor
            $stageRoot=Join-Path $ServiceRoot ('.staging-acceptance-'+[guid]::NewGuid().ToString('N'))
            $d.staging_root=$stageRoot;SaveDescriptor $d
            New-Item -ItemType Directory -Path $stageRoot | Out-Null;Set-BridgeExactAcl $stageRoot
            foreach($item in @(Get-ChildItem -LiteralPath $bindingPayload -Force)){Copy-Item -LiteralPath $item.FullName -Destination (Join-Path $stageRoot $item.Name) -Recurse}
            foreach($f in @(Get-BridgeTreeItemsNoFollow $stageRoot)){Set-BridgeExactAcl $f.FullName;if(!$f.PSIsContainer){SyncFile $f.FullName}}
            $bundle=Join-Path $stageRoot 'bundle';$manifestPath=Join-Path $bundle 'bundle-manifest.json'
            if($phase -ceq 'Bind'){
                $configPath=Join-Path $bundle 'tws-wsl-bridge.config.json'
                $old=Read-BridgeConfig $configPath
                Set-BridgeStagedDistro $configPath $bindingSpec.new_distro
                $new=Read-BridgeConfig $configPath
                $a=Get-WslBindingCanonical $old;$b=Get-WslBindingCanonical $new
                $a['distro']=$bindingSpec.new_distro
                if((Get-WslBindingHash $a) -cne (Get-WslBindingHash $b)){throw 'BINDING_CONFIG_DELTA'}
                $bm=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
                $hashes=[ordered]@{};foreach($property in $bm.hashes.PSObject.Properties){$hashes[$property.Name]=(Get-FileHash (Join-Path $bundle $property.Name) -Algorithm SHA256).Hash}
                $bm.hashes=$hashes;$bm.bundleId=Get-BridgeBundleId $hashes
                Write-TextAtomically $manifestPath (($bm | ConvertTo-Json -Depth 8)+[Environment]::NewLine);SyncFile $configPath;SyncFile $manifestPath
            }
            $bm=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
            $stage=[pscustomobject]@{Root=$stageRoot;Bundle=$bundle;Wrapper=(Join-Path $stageRoot ($ServiceName+'.exe'));
                Definition=(Join-Path $stageRoot ($ServiceName+'.xml'));InstallationManifest=(Join-Path $stageRoot 'installation-manifest.json');BundleId=[string]$bm.bundleId}
            Test-BridgeStagedPayload $stage
            foreach($name in @(($ServiceName+'.exe'),($ServiceName+'.xml'),'installation-manifest.json')){
                if((Get-BridgePayloadFingerprint (Join-Path $stageRoot $name)) -cne [string]$d.archive_hashes.$name){throw 'BINDING_STAGED_POLICY_DRIFT'}
            }
            return $stage
        }
        function Activate($stage,$before){
            if($bindingPhase -ceq 'Bind'){[void](Claim 205)}else{[void](Claim 40)}
            if((Get-WslBindingHash (Payload).hashes) -cne (Get-WslBindingHash $before.payload.hashes)){throw 'BINDING_ACTIVE_CAS'}
            if(Test-Path $TransactionJournalPath){throw 'BINDING_PENDING_TRANSACTION'}
            $tx=New-BridgePayloadTransaction $stage $true $true $false $before.payload.bundle_id
            $script:bindingTransaction=$tx
            $d=ReadDescriptor;$d.transaction_id=$tx.TransactionId;$d.rollback_root=$tx.RollbackRoot
            $d.transaction_before_hashes=$before.payload.hashes;$stagedHashes=[ordered]@{}
            foreach($item in $tx.Items){$stagedHashes[[IO.Path]::GetFileName($item.Active)]=$item.StagedFingerprint}
            $d.transaction_staged_hashes=$stagedHashes;$d.phase='switch-intent';SaveDescriptor $d
            Write-BridgeTransactionJournal $tx;SyncFile $TransactionJournalPath
            Switch-BridgePayload $tx
            Protect-BridgeServiceRoot
            $d.bound_hashes=(Payload).hashes;$d.phase=if($bindingPhase -ceq 'Bind'){'bound-pending'}else{'restore-pending'}
            if($bindingPhase -ceq 'Bind'){$d.bound_address=$before.observed_address};SaveDescriptor $d
        }
        function StopOwned {
            [void](Claim 30);$tx=$null
            if($bindingPhase -ceq 'Recover'){$tx=KnownTransaction}
            $owner=if($null -ne $tx){Get-BridgeRecoveryServiceOwnership $tx}else{Get-BridgeServiceOwnership}
            if($owner.Status -cne 'owned' -or ($null -eq $tx -and $owner.RequiresAdoption) -or $null -eq $owner.Service -or @($owner.Service.DependentServices).Count){throw 'BINDING_OWNER'}
            Stop-BridgeServiceChecked $owner.Service
        }
        function StartOwned {
            [void](Claim 195)
            $regs=Registrations;$p=Payload;$d=ReadDescriptor;$names=@(Running)
            Assert-WslBindingStartPayload $bindingSpec $bindingPhase $p $d $regs $names
            $when=[DateTimeOffset]::UtcNow;Start-BridgeServiceChecked;return $when
        }
        function CheckFinal([string]$phase,$before,[string]$bundle){
            $p=Payload;$regs=Registrations;$names=@(Running)
            $expected=if($phase -ceq 'ResumeOriginal'){$bindingSpec.original_distro}else{$bindingSpec.new_distro}
            if($p.bundle_id -cne $bundle -or $p.status -cne 'Running' -or $p.policy_sha256 -cne $before.policy_sha256 -or
                $regs.hash -cne $before.registration_sha256 -or $names.Count -ne 1 -or $names[0] -cne $expected){throw 'BINDING_FINAL_OWNER'}
            $certificate=Certificate;$routes=Routes $p
            if($certificate.snapshot_sha256 -cne $before.certificate.snapshot_sha256 -or $routes.foreign_sha256 -cne $before.routes.foreign_sha256 -or
                (Hosts) -cne $before.hosts_sha256){throw 'BINDING_FINAL_PRESERVATION'}
            $address=Address $expected
            if([string]$p.state.wslIp -cne $address -or $address -cne $before.observed_address){throw 'BINDING_FINAL_ADDRESS'}
            if($phase -ceq 'ResumeOriginal'){
                $d=ReadDescriptor
                if((Get-WslBindingHash $p.hashes) -cne (Get-WslBindingHash $d.archive_hashes)){throw 'BINDING_ORIGINAL_BYTES'}
            }
        }
        function Pending($before){
            [void](Claim 205);$d=ReadDescriptor
            if((Get-WslBindingHash $before.payload.hashes) -cne (Get-WslBindingHash $d.archive_hashes)){throw 'BINDING_ORIGINAL_BYTES'}
            $tx=KnownTransaction
            if($null -eq $tx){
                if($d.phase -cnotin @('original-stopped','recovered-stopped')){throw 'BINDING_RESTORE_JOURNAL'}
            }elseif($tx.TransactionId -cne $d.transaction_id -or $d.phase -cne 'restore-pending'){throw 'BINDING_RESTORE_JOURNAL'}
            $script:bindingTransaction=$tx
        }
        function RecoverStopped($before){
            $d=ReadDescriptor;$tx=KnownTransaction
            if($null -ne $tx){
                if($tx.TransactionId -cne $d.transaction_id -or !$tx.ServiceExisted -or $tx.ServiceCreateIntent -or $tx.ServiceCreated){throw 'BINDING_RECOVERY_JOURNAL'}
                foreach($item in $tx.Items){
                    if($item.OriginalExisted -and !(Test-Path $item.Active) -and !(Test-Path $item.Backup)){throw 'BINDING_RECOVERY_MEMBER_MISSING'}
                    if((Get-BridgePayloadFingerprint $item.Backup) -ceq $item.OriginalFingerprint){$item.OriginalMoveIntent=$true}
                }
                Restore-BridgePayload $tx;Protect-BridgeServiceRoot
                foreach($item in $tx.Items){if((Get-BridgePayloadFingerprint $item.Active) -cne $item.OriginalFingerprint){throw 'BINDING_RECOVERY_INCOMPLETE'}}
                Complete-BridgePayloadRollback $tx
            }
            $current=Payload
            if((Get-WslBindingHash $current.hashes) -cne (Get-WslBindingHash $d.archive_hashes)){
                $stage=Stage 'StageRestore' $before
                Activate $stage (@{payload=$current})
            }
            if((Payload).status -cne 'Stopped'){throw 'BINDING_RECOVERY_NOT_STOPPED'}
            $d=ReadDescriptor;$d.phase=if($null -ne (Read-BridgeTransactionJournal)){'restore-pending'}else{'recovered-stopped'}
            $d.phase_intent='';SaveDescriptor $d
        }
        $ports=@{}
        $ports.Begin={param($phase) $script:bindingClock=[Diagnostics.Stopwatch]::StartNew();$script:bindingDeadline=Get-WslBindingPhaseSeconds $phase
            $script:bindingPhase=$phase;InitializeFileIdentity;Assert-Administrator
            if($env:COMPUTERNAME -ine $bindingSpec.host){throw 'BINDING_HOST'};Source}
        $ports.Observe={param($phase) Snapshot $phase}
        $ports.Intent={param($phase,$before,$go) [void](Claim 1);$script:bindingApprovalSha=Get-WslBindingHash $go
            if($phase -cne 'Archive'){$d=ReadDescriptor;$d.phase_intent=$phase;$d.approval_sha256=$bindingApprovalSha
                if($phase -cin @('StopOriginal','StageRestore')){$d.guest_quiesce_sha256=$go.guest_quiesce_sha256};SaveDescriptor $d}}
        $ports.Lock={param($name) [void](Claim 30);Enter-BridgeMutex -Name $name -Timeout ([TimeSpan]::FromSeconds(30))}
        $ports.Unlock={param($m) Exit-BridgeMutex $m}
        $ports.Archive={param($before) OriginalArchive $before}
        $ports.Stage={param($phase,$before) Stage $phase $before}
        $ports.Stop={param($before) StopOwned}
        $ports.Stopped={param($phase) if((Payload).status -cne 'Stopped'){throw 'BINDING_STOP_NOT_CONFIRMED'}
            if($phase -ceq 'StopOriginal'){$d=ReadDescriptor;$d.phase='original-stopped';$d.phase_intent='';SaveDescriptor $d}}
        $ports.Switch={param($stage,$before) Activate $stage $before}
        $ports.Protect={Protect-BridgeServiceRoot}
        $ports.Start={param($before) StartOwned}
        $ports.Heartbeat={param($when,$bundle) [void](Claim 165);Wait-BridgeServiceHeartbeat -TransitionStartedAt $when -ExpectedBundleId $bundle -TimeoutSeconds 45}
        $ports.Final={param($phase,$before,$bundle) CheckFinal $phase $before $bundle}
        $ports.Complete={param($phase) if($null -ne $bindingTransaction){Complete-BridgePayloadTransaction $bindingTransaction}
            $d=ReadDescriptor;$d.phase=if($phase -ceq 'Bind'){'bound'}else{'restored'};$d.transaction_id='';SaveDescriptor $d}
        $ports.Pending={param($before) Pending $before}
        $ports.Recover={param($before) RecoverStopped $before}
        $ports.Failure={param($code,$active) if(Test-Path $bindingDescriptorPath){$d=ReadDescriptor;$d.phase='recovery-required';SaveDescriptor $d}}
        $script:bindingPorts=$ports
    }
    }finally{foreach($handle in $handles){$handle.Dispose()}}
    $result=@{}
    foreach($name in @('Begin','Observe','Intent','Lock','Unlock','Archive','Stage','Switch','Protect','Stop','Stopped','Start','Heartbeat','Final','Complete','Pending','Recover','Failure')){
        $result[$name]={& $module {param($operation,$arguments) & ($script:bindingPorts[$operation]) @arguments} $name $args}.GetNewClosure()
    }
    return $result
}

if($MyInvocation.InvocationName -ne '.'){
    try{
        $s=Read-WslBindingWire $ScenarioBase64 $ExpectedScenarioSha256
        $g=if($Mode -ceq 'Prepare'){$null}else{Read-WslBindingWire $ApprovalBase64 $ExpectedApprovalSha256}
        $ports=New-WslAcceptanceBridgeProductionPorts $s
        $result=Invoke-WslAcceptanceBridgeBinding $s $Mode $g $ports $PrepareFor
        $result | ConvertTo-Json -Depth 8 -Compress
        if($result.status -cin @('PREPARED_READ_ONLY','ORIGINAL_ARCHIVED','ORIGINAL_BRIDGE_STOPPED','NEW_BINDING_READY','ORIGINAL_PAYLOAD_STAGED_STOPPED','ORIGINAL_BINDING_RESTORED','RECOVERED_STOPPED')){exit 0}
        exit 2
    }catch{[Console]::Error.WriteLine('{"status":"BINDING_ADMISSION_FAILED"}');exit 2}
}
