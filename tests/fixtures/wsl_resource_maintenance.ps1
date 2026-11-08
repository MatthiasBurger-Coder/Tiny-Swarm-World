param([Parameter(Mandatory=$true)][string]$RepositoryRoot,[string]$NativeFixtureRoot='')
$ErrorActionPreference='Stop'
. (Join-Path $RepositoryRoot 'tools/windows/qualification/wsl_resource_maintenance.ps1')
function Assert($Condition,[string]$Code){if(!$Condition){throw $Code}}
function Scenario {
    return @{schema_version=1;source_commit=('a'*40);host='TEST-HOST';registration_sha256=('b'*64);
        repository_root='C:/fixture';guest_checkout='/root/epic440-task/checkout';guest_helper_sha256=('c'*64);
        intent_sha256=('d'*64);recovery_reference='epic440:recovery';prestate_sha256=('e'*64);
        memory_gib=21;processors=8;swap_gib=6}
}
function MockPorts([string]$Fault=''){
    $ctx=@{fault=$Fault;calls=[Collections.ArrayList]::new();sets=0;restores=0;committed=$false}
    $p=@{}
    $p.Observe={param($s) [void]$ctx.calls.Add('observe');if($ctx.fault -eq 'observe'){throw 'PRIVATE_IP_ACL_SID_CANARY'}
        return @{admitted=$true;prestate_sha256=$s.prestate_sha256;bridge_running=($ctx.fault -ne 'original_stopped')}}.GetNewClosure()
    $p.Intent={param($s,$b) [void]$ctx.calls.Add('intent');if($ctx.fault -eq 'intent'){throw 'intent'}}.GetNewClosure()
    $p.Lock={param($name,$timeout) Assert ($timeout -eq 30) 'lock_timeout';[void]$ctx.calls.Add('lock:'+$name)
        if($ctx.fault -eq 'lock2' -and $name.EndsWith('Reconcile')){throw 'lock'};return $name}.GetNewClosure()
    $p.Unlock={param($m) [void]$ctx.calls.Add('unlock:'+$m)}.GetNewClosure()
    $p.StopBridge={param($b) [void]$ctx.calls.Add('stop');if($ctx.fault -eq 'stop'){throw 'stop'}}.GetNewClosure()
    $p.Plan={param($s) [void]$ctx.calls.Add('plan');$id='adapt_wsl_resources';$codes=@(@{code='prerequisite_missing'})
        if($ctx.fault -eq 'extra_action'){$id='bridge_refresh'}
        if($ctx.fault -eq 'extra_blocker'){$codes+=@{code='foreign_or_unknown_listener'}}
        return @{actions=@(@{id=$id});resources=@{blockers=@();state='CHANGE_REQUIRED';allocation=@{memory_gib=21;processors=8;swap_gib=6}};blockers=$codes;plan_fingerprint=('f'*64)}}.GetNewClosure()
    $p.Apply={param($s,$fingerprint) [void]$ctx.calls.Add('apply');Assert ($fingerprint -ceq ('f'*64)) 'fingerprint'
        $exit=3;$uncertain=@();if($ctx.fault -eq 'apply'){$exit=2};if($ctx.fault -eq 'uncertain'){$uncertain=@('adapt_wsl_resources')}
        return @{restart=@{scope='WSL-wide'};result=@{exit_code=$exit;outcome='RESTART_REQUIRED';changed=$true;
            completed_actions=@('adapt_wsl_resources');uncertain_actions=$uncertain}}}.GetNewClosure()
    $p.CheckPreservation={param($b,$phase) [void]$ctx.calls.Add('check:'+$phase)
        if($ctx.fault -eq 'preserve' -and $phase -eq 'BEFORE_SHUTDOWN'){throw 'drift'}
        if($ctx.fault -eq 'set2' -and $phase -eq 'RECOVERY'){throw 'partial_state'}
        if($ctx.fault -eq 'recovery' -and $phase -eq 'RECOVERY'){throw 'recovery'}}.GetNewClosure()
    $p.Shutdown={param($s) [void]$ctx.calls.Add('shutdown');if($ctx.fault -in @('shutdown','recovery')){throw 'shutdown'}}.GetNewClosure()
    $p.Relaunch={param($s) [void]$ctx.calls.Add('relaunch');if($ctx.fault -eq 'relaunch'){throw 'relaunch'}}.GetNewClosure()
    $p.Effective={param($s,$b) [void]$ctx.calls.Add('effective');if($ctx.fault -eq 'effective'){throw 'effective'}}.GetNewClosure()
    $p.Address={param($s,$b) return '192.0.2.8'}.GetNewClosure()
    $p.Routes={param($b,$a) return @(@{id=1},@{id=2})}.GetNewClosure()
    $p.SetRoute={param($b,$c,$a) [void]$ctx.calls.Add('set');$ctx.sets++
        if($ctx.fault -eq 'set2' -and $ctx.sets -eq 2){throw 'partial'}}.GetNewClosure()
    $p.CommitState={param($b,$a) [void]$ctx.calls.Add('commit');$ctx.committed=$true}.GetNewClosure()
    $p.RestoreBridge={param($b) [void]$ctx.calls.Add('restore');$ctx.restores++
        if($ctx.fault -eq 'restore'){throw 'restore'}}.GetNewClosure()
    $p.Final={param($s,$b) [void]$ctx.calls.Add('final');if($ctx.fault -eq 'final'){throw 'final'}}.GetNewClosure()
    $p.BeginLifetime={[void]$ctx.calls.Add('lease_begin');if($ctx.fault -eq 'lease_begin'){throw 'lease'}}.GetNewClosure()
    $p.EndLifetime={[void]$ctx.calls.Add('lease_end');if($ctx.fault -eq 'lease_end'){throw 'lease'}}.GetNewClosure()
    $p.ReadLeaseStatus={return @{owned=$true;alive=$true}}
    $p.BeginRecovery={[void]$ctx.calls.Add('begin_recovery')}.GetNewClosure()
    $p._context=$ctx
    return $p
}
$cases=0
$p=MockPorts
$result=Invoke-WslResourceMaintenance (Scenario) $p
Assert ($result.status -ceq 'MAINTENANCE_COMPLETE' -and $result.resource_verified -and !$result.services_verified) 'complete'
Assert ($result.route_changes -eq 2 -and $p._context.sets -eq 2 -and $p._context.restores -eq 1) 'exact_changes'
$calls=@($p._context.calls)
Assert ([Array]::IndexOf($calls,'lease_begin') -lt [Array]::IndexOf($calls,'observe')) 'lease_precedes_observe'
Assert ($calls[-1] -ceq 'lease_end') 'lease_closed_after_all_final_proofs'
Assert ([Array]::IndexOf($calls,'stop') -lt [Array]::IndexOf($calls,'plan')) 'fresh_after_stop'
Assert ([Array]::IndexOf($calls,'commit') -lt [Array]::IndexOf($calls,'restore')) 'commit_before_resume'
Assert ([Array]::IndexOf($calls,'unlock:Global\TinySwarmWorldWslBridgeReconcile') -lt [Array]::IndexOf($calls,'restore')) 'unlock_before_resume'
$cases++

foreach($fault in @('lease_begin','lease_end','observe','intent','lock2','stop','extra_action','extra_blocker','apply','uncertain',
    'preserve','shutdown','relaunch','effective','set2','restore','final','recovery')){
    $p=MockPorts $fault;$result=Invoke-WslResourceMaintenance (Scenario) $p
    Assert ($result.status -cne 'MAINTENANCE_COMPLETE') ('fault_pass_'+$fault)
    Assert (($result | ConvertTo-Json -Compress) -notmatch 'PRIVATE_IP_ACL_SID_CANARY') 'redaction'
    if($fault -in @('lease_begin','observe','intent','lock2','stop','extra_action','extra_blocker')){
        Assert (@($p._context.calls | Where-Object{$_ -eq 'apply'}).Count -eq 0) ('unexpected_apply_'+$fault)
    }
    if($fault -in @('apply','uncertain','preserve')){
        Assert (@($p._context.calls | Where-Object{$_ -eq 'shutdown'}).Count -eq 0) ('unexpected_shutdown_'+$fault)
    }
    if($fault -eq 'set2'){
        Assert ($result.route_changes -eq 1 -and $result.recovery_required -and $p._context.restores -eq 0) 'partial_not_resumed'
    }
    if($fault -eq 'lock2'){
        Assert (@($p._context.calls | Where-Object{$_ -eq 'unlock:Global\TinySwarmWorldWslBridgeServiceUpdate'}).Count -eq 1) 'lock_release'
    }
    if($fault -eq 'stop'){Assert ($p._context.restores -eq 1) 'uncertain_stop_recovered'}
    $cases++
}
$p=MockPorts 'original_stopped';$result=Invoke-WslResourceMaintenance (Scenario) $p
Assert ($result.status -ceq 'MAINTENANCE_COMPLETE' -and @($p._context.calls | Where-Object{$_ -eq 'stop'}).Count -eq 0) 'stopped_preserved'
$cases++
foreach($change in @(@{swap_gib=7},@{memory_gib=$true},@{source_commit='invalid'},@{intent_sha256='bad'},@{foreign='value'})){
    $s=Scenario;foreach($key in $change.Keys){$s[$key]=$change[$key]};$p=MockPorts
    $result=Invoke-WslResourceMaintenance $s $p
    Assert ($result.status -ceq 'BLOCKED' -and $p._context.calls.Count -eq 0) 'invalid_scenario_zero_effect'
    $cases++
}
$registry=@(
    [ordered]@{key='/v4tov4/tcp';name='127.0.0.1/1111';kind='String';value='192.0.2.5/2222'},
    [ordered]@{key='/v4tov6/tcp';name='127.0.0.1/3333';kind='String';value='::1/4444'},
    [ordered]@{key='/v6tov4/tcp';name='::1/5555';kind='String';value='192.0.2.6/6666'},
    [ordered]@{key='/v6tov6/tcp';name='::1/7777';kind='String';value='::1/8888'},
    [ordered]@{key='/foreign-metadata';name='opaque';kind='Binary';value=@(0,255)})
$text="Listen on ipv4: Connect to ipv4:`r`nAddress Port Address Port`r`n------- ---- ------- ----`r`n127.0.0.1 1111 192.0.2.5 2222`r`n`r`n"
$text+="Listen on ipv4: Connect to ipv6:`r`nAddress Port Address Port`r`n------- ---- ------- ----`r`n127.0.0.1 3333 ::1 4444`r`n`r`n"
$text+="Listen on ipv6: Connect to ipv4:`r`nAddress Port Address Port`r`n------- ---- ------- ----`r`n::1 5555 192.0.2.6 6666`r`n`r`n"
$text+="Listen on ipv6: Connect to ipv6:`r`nAddress Port Address Port`r`n------- ---- ------- ----`r`n::1 7777 ::1 8888`r`n"
$parsed=ConvertFrom-WslMaintenanceNetshAll ([Text.Encoding]::ASCII.GetBytes($text)) $registry
Assert ($parsed.count -eq 4) 'all_four_families'
$german=$text.Replace('Listen on','Abfragen auf').Replace('Connect to','Verbinden mit').Replace('Address Port Address Port','Adresse Anschluss Adresse Anschluss')
$localized=ConvertFrom-WslMaintenanceNetshAll ([Text.Encoding]::ASCII.GetBytes($german)) $registry
Assert ($localized.projection -ceq $parsed.projection) 'localized_same_complete_projection'
$unicode=[byte[]](@(255,254)+[Text.Encoding]::Unicode.GetBytes($text))
$wide=ConvertFrom-WslMaintenanceNetshAll $unicode $registry
Assert ($wide.projection -ceq $parsed.projection) 'unicode_bom_no_dropped_rows'
$cases+=3
foreach($bad in @(
    $text.Replace('192.0.2.5 2222','192.0.2.9 2222'),
    ($text+"::1 9999 ::1 9998`r`n"),
    $text.Replace('127.0.0.1 1111 192.0.2.5 2222',"127.0.0.1 1111 192.0.2.5 2222`r`n127.0.0.1 1111 192.0.2.5 2222"),
    ($text+"UNKNOWN OUTPUT`r`n"),
    $text.Replace('Connect to ipv6:','Connect to ipv5:'),
    $text.Replace('1111','999999'),
    $text.Replace('127.0.0.1 3333 ::1 4444','127.0.0.1 3333 192.0.2.7 4444'),
    $text.Replace('Address Port Address Port','Address Port Extra Address Port'))){
    $denied=$false;try{ConvertFrom-WslMaintenanceNetshAll ([Text.Encoding]::ASCII.GetBytes($bad)) $registry | Out-Null}catch{$denied=$true}
    Assert $denied 'netsh_mutated_missing_extra_or_unknown_refused'
    $cases++
}
if([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT){
    $child=[Diagnostics.Process]::new()
    $child.StartInfo.FileName=Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
    $program="[Console]::WriteLine('READY');[Console]::Out.Flush();[Console]::ReadLine() | Out-Null"
    $child.StartInfo.Arguments='-NoProfile -NonInteractive -EncodedCommand '+[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($program))
    $child.StartInfo.UseShellExecute=$false;$child.StartInfo.CreateNoWindow=$true
    $child.StartInfo.RedirectStandardInput=$true;$child.StartInfo.RedirectStandardOutput=$true
    try{
        Assert ($child.Start()) 'owned_image_child_start'
        $ownedPid=$child.Id;$ownedStart=$child.StartTime.ToUniversalTime().Ticks
        $before=Get-WslMaintenanceOwnedProcessImage $child $child.StartInfo.FileName
        $ready=$child.StandardOutput.ReadLineAsync()
        Assert ($ready.Wait(10000) -and $ready.Result -ceq 'READY') 'owned_image_child_ready'
        $after=Get-WslMaintenanceOwnedProcessImage $child $child.StartInfo.FileName
        Assert ($before -ceq $after -and $child.Id -eq $ownedPid -and $child.StartTime.ToUniversalTime().Ticks -eq $ownedStart) 'owned_image_handle_stable_before_after_ready'
        $denied=$false;try{$null=Get-WslMaintenanceOwnedProcessImage $child ($child.StartInfo.FileName+'.foreign')}catch{$denied=$_.Exception.Message -ceq 'OWNED_PROCESS_IMAGE_MISMATCH'}
        Assert $denied 'owned_image_wrong_expected_refused'
        $child.StandardInput.Close();Assert ($child.WaitForExit(10000) -and $child.ExitCode -eq 0) 'owned_image_eof_settled'
    }finally{
        if(!$child.HasExited -and $child.Id -eq $ownedPid -and $child.StartTime.ToUniversalTime().Ticks -eq $ownedStart -and
           (Get-WslMaintenanceOwnedProcessImage $child $child.StartInfo.FileName)){$child.Kill();$child.WaitForExit()}
        $child.Dispose()
    }
    $cases++
}
if($NativeFixtureRoot){
    $s=Scenario;$s.repository_root=$NativeFixtureRoot
    $ports=New-WslMaintenanceProductionPorts $s
    $adapter=$ports.Routes.Module.SessionState.PSVariable.GetValue('module')
    Assert ($null -ne $adapter) 'production_module_binding'
    # Host process effects remain mocked in this fixture; Python protocol tests
    # separately execute the exact literal child and prove EOF/expiry semantics.
    & $adapter {$script:realBeginLifetime=${function:BeginLifetime};$script:realEndLifetime=${function:EndLifetime};function script:BeginLifetime {};function script:EndLifetime {}}
    & $adapter {
        function script:Get-WslMaintenanceOwnedProcessImage($Process,$Expected) {return $Process.MainModule.FileName}
        function script:FakeLease([string]$Fault='') {
            $ctx=@{closed=$false;kills=0;disposed=$false}
            $task=[pscustomobject]@{IsCompleted=$false;Result=$null}
            $task | Add-Member ScriptMethod Wait {param($Milliseconds) return $true}
            $done=[pscustomobject]@{}
            $done | Add-Member ScriptMethod Wait {param($Milliseconds) return $true}
            $stream=[IO.MemoryStream]::new()
            $input=[pscustomobject]@{ctx=$ctx;task=$task;fault=$Fault}
            $input | Add-Member ScriptMethod Close {
                $this.ctx.closed=$true
                if($this.fault -ne 'timeout'){$this.ctx.process.HasExited=$true}
                $this.task.IsCompleted=$true;$this.task.Result=$(if($this.fault -eq 'bad_ack'){'OTHER'}else{'CLOSED'})
            }
            $output=[pscustomobject]@{}
            $output | Add-Member ScriptMethod ReadToEnd {return ''}
            $process=[pscustomobject]@{Id=77;StartTime=([datetime]'2026-01-01T00:00:00Z');
                MainModule=[pscustomobject]@{FileName='C:/Windows/System32/wsl.exe'};
                HasExited=$false;ExitCode=0;StandardInput=$input;StandardOutput=$output;ctx=$ctx}
            $process | Add-Member ScriptMethod WaitForExit {param($Milliseconds) return $this.HasExited}
            $process | Add-Member ScriptMethod Kill {$this.ctx.kills++;$this.HasExited=$true}
            $process | Add-Member ScriptMethod Dispose {$this.ctx.disposed=$true}
            $ctx.process=$process
            $lease=@{process=$process;pid=77;start=$process.StartTime.ToUniversalTime().Ticks;
                exe='C:/Windows/System32/wsl.exe';stderr=$stream;closed=$task;errorTask=$done;
                clock=[pscustomobject]@{Elapsed=[TimeSpan]::Zero};seconds=10;context=$ctx}
            if($Fault -eq 'identity'){$process.MainModule.FileName='C:/unknown.exe'}
            if($Fault -eq 'expired'){$process.HasExited=$true;$process.ExitCode=3;$task.IsCompleted=$true;
                $lease.clock=[pscustomobject]@{Elapsed=[TimeSpan]::FromSeconds(10)}}
            return $lease
        }
        $good=FakeLease;CloseLease $good
        if(!$good.context.closed -or !$good.context.disposed -or $good.context.kills -ne 0){throw 'lease_not_cleanly_closed'}
        foreach($fault in @('identity','bad_ack','timeout')){
            $lease=FakeLease $fault;$blocked=$false
            try{CloseLease $lease}catch{$blocked=$true}
            if(!$blocked -or !$lease.context.disposed){throw 'lease_failure_claimed_success'}
            if($fault -eq 'identity' -and $lease.context.kills -ne 0){throw 'unknown_process_killed'}
        }
        $expired=FakeLease 'expired';CloseLease $expired -AllowExpired
        if(!$expired.context.disposed -or $expired.context.kills -ne 0){throw 'finite_expired_child_not_settled'}
        $early=FakeLease 'expired';$early.clock.Elapsed=[TimeSpan]::Zero;$blocked=$false
        try{CloseLease $early -AllowExpired}catch{$blocked=$true}
        if(!$blocked){throw 'early_nonzero_not_expiry'}
        $originalSource=${function:Source};$originalRunning=${function:Running}
        $originalNew=${function:NewReadLease};$originalWait=${function:WaitIncusReady}
        try{
            function script:Source {}
            function script:Running {return 'Ubuntu'}
            $script:lease=FakeLease;$same=$script:lease
            & $script:realBeginLifetime;& $script:realBeginLifetime
            if(![object]::ReferenceEquals($same,$script:lease) -or $script:lease.seconds -ne 10){throw 'idempotent_lease_was_replaced'}
            foreach($names in @(@(),@('Ubuntu','FOREIGN'))){
                $script:testRunning=$names
                function script:Running {return $script:testRunning}
                $blocked=$false;try{& $script:realBeginLifetime}catch{$blocked=$true}
                if(!$blocked){throw 'stopped_or_foreign_lifetime_admitted'}
            }
            CloseLease $same;$script:lease=$null
        }finally{
            Set-Item Function:script:Source $originalSource;Set-Item Function:script:Running $originalRunning
            Set-Item Function:script:NewReadLease $originalNew;Set-Item Function:script:WaitIncusReady $originalWait
            $script:lease=$null
        }
        AssertMappingCount @{mappings=@(1..24)}
        $blocked=$false;try{AssertMappingCount @{mappings=@(1..25)}}catch{$blocked=$true}
        if(!$blocked){throw 'mapping25_admitted'}
        $script:clock=[Diagnostics.Stopwatch]::StartNew();$script:limits=@{seconds=4800;commands=512;bytes=67108864}
        $script:commandCount=511;$null=ClaimCommand;$blocked=$false
        try{$null=ClaimCommand}catch{$blocked=$true};if(!$blocked){throw 'command513_admitted'}
        $script:commandCount=0;$script:clock=[pscustomobject]@{Elapsed=[TimeSpan]::FromSeconds(4785)}
        $blocked=$false;try{$null=ClaimCommand}catch{$blocked=$true};if(!$blocked){throw 'cleanup_reserve_consumed'}
        $script:clock=[Diagnostics.Stopwatch]::StartNew();$script:commandCount=0
    }
    $cases+=13
    # Real production Run/Firewall reader with fake child transport only. The
    # separate shared-producer contract executes the full8.9MB payload in RAM.
    $certificateRaw=([ordered]@{schema_version='tsw.windows-firewall-certificate.v1';
      query_sha256='a6a5aee14f32ada47cd14b58f59372fc0ba21ceaef64401d93b94822932c19e5';
      snapshot_sha256=('c'*64);snapshot_bytes=8903516;snapshot_schema_version=2;store='ActiveStore';
      association_model='PROVIDER_IDENTITY_ONE_TO_ONE';counts=[ordered]@{rules=543;profiles=3;settings=1;
       address=543;application=543;interface=543;interface_type=543;port=543;security=543;service=543}} | ConvertTo-Json -Depth 4 -Compress)
    $fakePreparation=New-Module -ArgumentList $certificateRaw -ScriptBlock {
      param($raw)
      $script:raw=$raw;$script:observations=0
      function Get-PreparationExecutable([string]$Name){return 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'}
      function Invoke-PreparationProcess($File,$Arguments,$Timeout){
       if($Arguments[-1] -notlike '*tsw.windows-firewall-certificate.v1*' -or $Timeout -gt 120){throw 'fake_transport_wrong_fixed_command'}
       $script:observations++;return @{exit_code=0;stdout=$script:raw;stderr=''}
      }
    }
    & $adapter {
      param($transport)
      $original=$script:preparation;$initialBytes=$script:outputBytes;$initialCommands=$script:commandCount
      try{
       $script:preparation=$transport
       $first=$null
       for($i=0;$i -lt 8;$i++){
        $current=Get-WslMaintenanceDigest (Firewall)
        if($null -ne $first -and $first -cne $current){throw 'fake_cert_unexpected_drift'}
        $first=$current
       }
       if($script:commandCount-$initialCommands -ne 8 -or $script:outputBytes-$initialBytes -gt 32768){throw 'full_snapshot_transported'}
       if((& $transport {$script:observations}) -ne 8){throw 'certificate_observation_cached'}
       & $transport {$script:raw=$script:raw.Replace(('c'*64),('d'*64))}
       if((Get-WslMaintenanceDigest (Firewall)) -ceq $first){throw 'changed_foreign_digest_lost'}
       & $transport {$script:raw=$script:raw.Replace('"snapshot_bytes":8903516','"snapshot_bytes":true')}
       $denied=$false;try{$null=Firewall}catch{if($_.Exception.Message -ceq 'FIREWALL_CERTIFICATE_INVALID'){$denied=$true}}
       if(!$denied){throw 'malformed_certificate_admitted'}
       & $transport {$script:raw='x'*5000}
       $denied=$false;try{$null=Firewall}catch{if($_.Exception.Message -ceq 'HOST_COMMAND_FAILED'){$denied=$true}}
       if(!$denied){throw 'parent_transport_bound_ignored'}
      }finally{$script:preparation=$original}
    } $fakePreparation
    $cases+=5
    $goodProof=[ordered]@{schema_version=1;scope='WSL_GUEST_PRESERVATION_ONLY';decision='ALL_INSTANCES_STOPPED_GRAPH_COMPLETE';
        source_commit=('a'*40);graph_sha256=('b'*64);detail_sha256=('c'*64);
        instance_count=1;project_count=1;detail_count=3;command_count=10}
    $rawProof=$goodProof | ConvertTo-Json -Compress
    $accepted=& $adapter {param($raw) ValidateGuestProof $raw} $rawProof
    Assert ($accepted.scope -ceq 'WSL_GUEST_PRESERVATION_ONLY') 'closed_guest_scope'
    $cases++
    foreach($change in @(@{schema_version=$true},@{scope='native-linux-test-host'},@{decision=$true},
        @{source_commit=$true},@{target_host='native-linux-test-host'},@{project_count=0},@{command_count=2049},
        @{detail_count=0},@{instance_count=10000},@{command_count=$false},@{detail_count=11})){
        $copy=@{};foreach($key in $goodProof.Keys){$copy[$key]=$goodProof[$key]};foreach($key in $change.Keys){$copy[$key]=$change[$key]}
        $denied=$false;try{& $adapter {param($raw) ValidateGuestProof $raw} ($copy | ConvertTo-Json -Compress) | Out-Null}catch{$denied=$true}
        Assert $denied 'guest_reader_forgery_refused';$cases++
    }
    foreach($raw in @(('['+$rawProof+']'),$rawProof.Replace('"schema_version":1','"schema_version":1,"schema_version":1'))){
        $denied=$false;try{& $adapter {param($value) ValidateGuestProof $value} $raw | Out-Null}catch{$denied=$true}
        Assert $denied 'guest_reader_array_or_duplicate_refused';$cases++
    }
    & $adapter {
        $script:fixture=@{fullSnapshots=0;routingSnapshots=0;firewallDrift=$false;writes=0;runs=[Collections.ArrayList]::new();foreign=$false;netsh_corrupt=$false;enforce_budget=$false;address='192.0.2.8'}
        $script:fixtureService=$null
        $script:fixtureMappings=@([pscustomobject]@{Name='one';ListenPort=1111;ConnectPort=2222},
            [pscustomobject]@{Name='two';ListenPort=3333;ConnectPort=4444})
        $script:fixtureState=[pscustomobject]@{contractVersion=2;agentMode='windows-service';serviceName=$ServiceName;
            wslIp='192.0.2.5';listenAddress='127.0.0.1';agentStatus='degraded';generatedAt='PRESERVE_TIMESTAMP';
            bundleId='PRESERVE_BUNDLE';private_note='DO_NOT_EXPORT';mappings=@(
                [pscustomobject]@{name='one';listenPort=1111;connectPort=2222},
                [pscustomobject]@{name='two';listenPort=3333;connectPort=4444})}
        $script:fixtureRegistry=@(
            [ordered]@{key='/v4tov4/tcp';name='127.0.0.1/1111';kind='String';value='192.0.2.5/2222'},
            [ordered]@{key='/v4tov4/tcp';name='127.0.0.1/3333';kind='String';value='192.0.2.5/4444'},
            [ordered]@{key='/v6tov6/tcp';name='::1/5555';kind='String';value='::1/6666'},
            [ordered]@{key='/foreign-metadata';name='FOREIGN_CANARY';kind='Binary';value=@(0,255)},
            [ordered]@{key='/unknown-empty';name='';kind='KEY';value=''})
        function script:Registration {return 'same-registration'}
        function script:Running {return @('Ubuntu')}
        function script:Guest {return @{graph='same';details='same'}}
        function script:AssertAddress($Before,$Address){if($script:fixture.address -cne $Address){throw 'ADDRESS_DRIFT'}}
        function script:Assert-BridgeRuntimeStateAuthority {}
        function script:Read-BridgeConfig {param($Path) return @{}}
        function script:Read-TswPortRegistry {param($Path) return @{Mappings=@()}}
        function script:Get-PortMappings {return $script:fixtureMappings}
        function script:Get-ProtectedBridgeState {return $script:fixtureState}
        function script:Snapshot([switch]$RoutingOnly) {
            if($RoutingOnly){$script:fixture.routingSnapshots++}else{$script:fixture.fullSnapshots++}
            if($script:fixture.enforce_budget){$null=ClaimCommand}
            $rows=$script:fixtureRegistry | ConvertTo-Json -Depth 10 -Compress | ConvertFrom-Json
            if($script:fixture.foreign){$rows[3].value=@(7,8)}
            $text="Listen on ipv4: Connect to ipv4:`r`nAddress Port Address Port`r`n------- ---- ------- ----`r`n"
            foreach($row in $script:fixtureRegistry | Where-Object{$_.key -ceq '/v4tov4/tcp'}){
                $listen=$row.name -split '/';$connect=$row.value -split '/'
                $text+=($listen[0]+' '+$listen[1]+' '+$connect[0]+' '+$connect[1]+"`r`n")
            }
            $text+="`r`nListen on ipv6: Connect to ipv6:`r`nAddress Port Address Port`r`n------- ---- ------- ----`r`n::1 5555 ::1 6666`r`n"
            if($script:fixture.netsh_corrupt){$text+="::1 9999 ::1 9998`r`n"}
            $bytes=[Text.Encoding]::ASCII.GetBytes($text)
            $proof=ConvertFrom-WslMaintenanceNetshAll $bytes $rows
            $result=@{proof_kind=$(if($RoutingOnly){'ROUTING_CAS'}else{'FULL_PRESERVATION'});identity='same-bridge';hosts='same-hosts';registry=@($rows);
                all=$bytes;netsh=$proof;state=$script:fixtureState;service_state=$(if($null -ne $script:fixtureService){[string]$script:fixtureService.Status}else{'Stopped'});running=($null -ne $script:fixtureService -and $script:fixtureService.Status -eq 'Running')}
            if(!$RoutingOnly){$result.firewall=$(if($script:fixture.firewallDrift){'foreign-firewall-drift'}else{'same-firewall'})}
            return $result
        }
        function script:Run($File,$Arguments,$Timeout,$OutputLimit){
            [void]$script:fixture.runs.Add(@($Arguments))
            if(($Arguments[0..3] -join ' ') -cne 'interface portproxy set v4tov4' -or $Timeout -ne 30){throw 'UNEXPECTED_MUTATOR'}
            $listen=($Arguments | Where-Object{$_ -like 'listenaddress=*'}) -replace '^listenaddress=',''
            $port=($Arguments | Where-Object{$_ -like 'listenport=*'}) -replace '^listenport=',''
            $address=($Arguments | Where-Object{$_ -like 'connectaddress=*'}) -replace '^connectaddress=',''
            $connect=($Arguments | Where-Object{$_ -like 'connectport=*'}) -replace '^connectport=',''
            foreach($row in $script:fixtureRegistry){if($row.key -ceq '/v4tov4/tcp' -and $row.name -ceq ($listen+'/'+$port)){$row.value=$address+'/'+$connect}}
            return ''
        }
        function script:Write-TextAtomically($Path,$Text){$script:fixture.writes++;$script:fixtureState=$Text | ConvertFrom-Json}
        $script:expectedRegistry=@((Snapshot).registry)
        $script:stateOriginal=Get-WslMaintenanceDigest $script:fixtureState
        $script:stateExpected=$script:stateOriginal
        $script:stableExpected=Get-WslMaintenanceDigest (StableState $script:fixtureState)
        $script:fixtureBefore=@{net=(Snapshot);guest=(Guest);stable_state=$script:stableExpected;
            bridge_running=$false;old_address='192.0.2.5';new_address='192.0.2.8'}
    }
    $before=& $adapter {$script:fixtureBefore}
    & $adapter {$script:fixture.fullSnapshots=0;$script:fixture.routingSnapshots=0}
    & $ports.CheckPreservation $before 'BEFORE_ROUTE'
    & $ports.CheckPreservation $before 'AFTER_ROUTE'
    Assert ((& $adapter {$script:fixture.fullSnapshots -eq 0 -and $script:fixture.routingSnapshots -eq 2})) 'route_checks_use_only_fresh_routing_proof'
    & $adapter {$script:fixture.firewallDrift=$true}
    & $ports.CheckPreservation $before 'BEFORE_ROUTE'
    $denied=$false;try{& $ports.CheckPreservation $before 'BEFORE_STATE'}catch{$denied=$true}
    Assert $denied 'full_afterbatch_detects_foreign_firewall_drift'
    & $adapter {$script:fixture.firewallDrift=$false}
    & $ports.CheckPreservation $before 'BEFORE_STATE'
    Assert ((& $adapter {$script:fixture.fullSnapshots -eq 2 -and $script:fixture.routingSnapshots -eq 3})) 'full_afterbatch_is_fresh_not_cached'
    $cases+=3
    $changes=@(& $ports.Routes $before '192.0.2.8')
    Assert ($changes.Count -eq 2) 'owned_changes_only'
    # Foreign change and invented tuple refuse before the production Run seam.
    & $adapter {$script:fixture.foreign=$true}
    $denied=$false;try{& $ports.SetRoute $before $changes[0] '192.0.2.8'}catch{$denied=$true}
    Assert $denied 'foreign_refusal'
    Assert ((& $adapter {$script:fixture.runs.Count}) -eq 0) 'foreign_zero_effect'
    & $adapter {$script:fixture.foreign=$false;$script:fixture.netsh_corrupt=$true}
    $denied=$false;try{& $ports.SetRoute $before $changes[0] '192.0.2.8'}catch{$denied=$true}
    Assert $denied 'same_registry_extra_netsh_row_refusal'
    Assert ((& $adapter {$script:fixture.runs.Count}) -eq 0) 'netsh_mismatch_zero_effect'
    & $adapter {$script:fixture.netsh_corrupt=$false}
    $denied=$false;try{& $ports.SetRoute $before @{name='invented';listen='127.0.0.1';listen_port=9999;connect_port=9999} '192.0.2.8'}catch{$denied=$true}
    Assert $denied 'invented_tuple_refusal'
    Assert ((& $adapter {$script:fixture.runs.Count}) -eq 0) 'invented_zero_effect'
    & $ports.SetRoute $before $changes[0] '192.0.2.8'
    & $ports.SetRoute $before $changes[1] '192.0.2.8'
    Assert ((& $adapter {$script:fixture.runs.Count}) -eq 2) 'two_fixed_sets'
    $denied=$false;try{& $ports.SetRoute $before $changes[0] '192.0.2.8'}catch{$denied=$true}
    Assert $denied 'replay_refused'
    & $adapter {$script:fixtureState.bundleId='DRIFT'}
    $denied=$false;try{& $ports.CommitState $before '192.0.2.8'}catch{$denied=$true}
    Assert $denied 'state_cas_refusal'
    Assert ((& $adapter {$script:fixture.writes}) -eq 0) 'state_cas_zero_effect'
    & $adapter {$script:fixtureState.bundleId='PRESERVE_BUNDLE'}
    & $ports.CommitState $before '192.0.2.8'
    $final=& $adapter {$script:fixtureState}
    Assert ($final.wslIp -ceq '192.0.2.8' -and $final.agentStatus -ceq 'degraded' -and
        $final.generatedAt -ceq 'PRESERVE_TIMESTAMP' -and $final.bundleId -ceq 'PRESERVE_BUNDLE' -and
        $final.private_note -ceq 'DO_NOT_EXPORT') 'state_only_ip_changed'
    Assert ((& $adapter {$script:fixture.writes}) -eq 1) 'one_state_write'
    $foreign=& $adapter {$script:fixtureRegistry[3]}
    Assert ($foreign.kind -ceq 'Binary' -and (@($foreign.value) -join ',') -ceq '0,255') 'foreign_binary_preserved'
    Assert ((& $adapter {$script:fixtureRegistry[4].kind}) -ceq 'KEY') 'foreign_empty_key_preserved'
    & $adapter {
        $script:fixtureService=[pscustomobject]@{Status='Running';DependentServices=@();ServicesDependedOn=@()}
        $script:fixtureService | Add-Member ScriptMethod WaitForStatus {param($Status,$Timeout) $this.Status=$Status}
        $script:serviceCalls=[Collections.ArrayList]::new()
        function script:Get-BridgeServiceOwnership {return @{Status='owned';RequiresAdoption=$false;Service=$script:fixtureService}}
        function script:Stop-Service {
            [CmdletBinding()]param([string]$Name,[switch]$Force)
            if($Force){throw 'FORCE_FORBIDDEN'}
            [void]$script:serviceCalls.Add('stop:'+$Name);$script:fixtureService.Status='Stopped'
        }
        function script:Start-BridgeServiceChecked {
            [void]$script:serviceCalls.Add('start');$script:fixtureService.Status='Running'
        }
    }
    & $ports.StopBridge @{bridge_running=$true}
    Assert ((& $adapter {$script:serviceCalls[0]}) -ceq 'stop:TinySwarmWorldWslBridge') 'exact_no_force_service'
    & $ports.RestoreBridge @{bridge_running=$false}
    Assert ((& $adapter {$script:serviceCalls.Count}) -eq 1) 'original_stopped_no_start'
    & $ports.RestoreBridge @{bridge_running=$true}
    Assert ((& $adapter {$script:serviceCalls.Count}) -eq 2) 'original_running_restored'
    & $ports.RestoreBridge @{bridge_running=$true}
    Assert ((& $adapter {$script:serviceCalls.Count}) -eq 2) 'running_not_restarted'
    & $adapter {$script:fixtureService.DependentServices=@([pscustomobject]@{Status='Running'})}
    $denied=$false;try{& $ports.StopBridge @{bridge_running=$true}}catch{$denied=$true}
    Assert ($denied -and (& $adapter {$script:serviceCalls.Count}) -eq 2) 'dependent_not_touched'
    $cases+=14
    & $adapter {
        $script:fixtureService.Status='Running';$script:fixtureService.DependentServices=@()
        $script:serviceCalls.Clear();$script:fixture.address='192.0.2.5';$script:fixture.enforce_budget=$true
        $script:fixtureState.wslIp='192.0.2.5'
        $script:fixtureRegistry[0].value='192.0.2.5/2222';$script:fixtureRegistry[1].value='192.0.2.5/4444'
        $script:clock=[Diagnostics.Stopwatch]::StartNew();$script:limits=@{seconds=4800;commands=512;bytes=67108864}
        $script:recoveryBegun=$false;$script:routeSets=0;$script:resumedAt=$null
        $script:expectedRegistry=@((Snapshot).registry)
        $script:stateOriginal=Get-WslMaintenanceDigest $script:fixtureState
        $script:stateExpected=$script:stateOriginal;$script:stableExpected=Get-WslMaintenanceDigest (StableState $script:fixtureState)
        $script:fixtureBefore=@{admitted=$true;prestate_sha256=$s.prestate_sha256;net=(Snapshot);guest=(Guest);
            stable_state=$script:stableExpected;bridge_running=$true;old_address='192.0.2.5';new_address='192.0.2.5'}
        $script:preparationPorts=@{Inventory={return @{bridge_facts=@{blockers=@()};observed_wsl_address='192.0.2.5'}}}
        function script:Observe {return $script:fixtureBefore}
        function script:Intent {}
        function script:Lock {param($Name,$Seconds) return $Name}
        function script:Unlock {param($Mutex)}
        function script:Source {}
        function script:WaitHeartbeat {}
        function script:Plan {
            $script:clock=[pscustomobject]@{Elapsed=([TimeSpan]::FromSeconds(4801))}
            $null=ClaimCommand
            throw 'UNREACHABLE'
        }
    }
    $recovered=Invoke-WslResourceMaintenance $s $ports
    Assert ($recovered.status -ceq 'BLOCKED' -and $recovered.bridge_restored -and !$recovered.recovery_required) 'deadline_reserve_restores_healthy_original_runtime'
    Assert ((& $adapter {$script:fixtureService.Status}) -ceq 'Running') 'deadline_bridge_not_left_stopped'
    Assert ((& $adapter {$script:recoveryBegun -and $script:limits.seconds -eq 3600 -and $script:commandCount -gt 0})) 'real_production_recovery_clock_used'
    $resetDenied=$false;try{& $ports.BeginRecovery}catch{$resetDenied=$true}
    Assert $resetDenied 'recovery_budget_not_resettable'
    $cases++
    & $adapter {
        $script:backupBytes=[Text.Encoding]::UTF8.GetBytes("# PRIVATE_CONFIG_CANARY`n[wsl2]`nmemory=25GB`nprocessors=8`nswap=4GB`n[other]`nkeep=yes`n")
        $script:backupMetadata='PRIVATE_SDDL|Archive|10|20|'+$script:backupBytes.Length
        function script:ReadResourceBackup {param($Recovery) return @{bytes=$script:backupBytes;metadata=$script:backupMetadata}}
        $sha=[Security.Cryptography.SHA256]::Create()
        try{$oldHash=([BitConverter]::ToString($sha.ComputeHash($script:backupBytes))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
        $merged=& $preparation {param($b) ConvertTo-PreparationWslConfig (ConvertFrom-PreparationWslConfig $b) @{memory_gib=21;processors=8;swap_gib=6}} $script:backupBytes
        $sha=[Security.Cryptography.SHA256]::Create()
        try{$newHash=([BitConverter]::ToString($sha.ComputeHash([byte[]]$merged))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
        $script:resourceIntent=@{recovery=@{resource_config=('0'*64);resource_file=$oldHash;
            resource_metadata=(Get-WslMaintenanceDigest $script:backupMetadata)}}
        $script:resourceFacts=@{resource_facts=@{config_snapshot=@{hash=$newHash;metadata=('PRIVATE_SDDL|Archive|10|30|'+$merged.Length)}}}
    }
    & $adapter {VerifyRecoveryResources $script:resourceIntent $script:resourceFacts}
    & $adapter {$script:resourceFacts.resource_facts.config_snapshot.metadata='ALTERED_SDDL|Archive|10|30|1'}
    $denied=$false;try{& $adapter {VerifyRecoveryResources $script:resourceIntent $script:resourceFacts}}catch{$denied=$true}
    Assert $denied 'recovery_resource_acl_drift_refused'
    & $adapter {$script:resourceFacts.resource_facts.config_snapshot.hash=('0'*64)}
    $denied=$false;try{& $adapter {VerifyRecoveryResources $script:resourceIntent $script:resourceFacts}}catch{$denied=$true}
    Assert $denied 'recovery_unrelated_global_config_change_refused'
    $cases+=3
    & $adapter {
        function script:ResetRecoveryFixture([string]$Case){
            $script:fixture.case=$Case;$script:fixture.unsafe=0;$script:fixture.reentries=0
            $script:fixture.running=@('Ubuntu');$script:fixture.foreign=$false;$script:fixture.netsh_corrupt=$false
            $script:fixture.enforce_budget=$false;$script:fixture.address='192.0.2.8';$script:fixture.writes=0
            $script:fixture.runs.Clear();$script:serviceCalls.Clear()
            $script:fixtureService.Status='Stopped';$script:fixtureService.DependentServices=@();$script:fixtureService.ServicesDependedOn=@()
            $script:fixtureState.wslIp='192.0.2.5';$script:fixtureState.bundleId='PRESERVE_BUNDLE'
            $script:fixtureRegistry[0].value='192.0.2.5/2222';$script:fixtureRegistry[1].value='192.0.2.5/4444'
            $script:clock=[Diagnostics.Stopwatch]::StartNew();$script:limits=@{seconds=4800;commands=512;bytes=67108864}
            $script:recoveryBegun=$false;$script:resumedAt=$null;$script:routeSets=0
            $script:recoveryFacts=@{linux_known=$true;running=$true;uid=1000;user='fixture';linux_id='ubuntu';release='26.04';
                linux_architecture='x86_64';wsl_generation=2;config_hash='same';config_metadata='same';systemd_configured=$true;
                pid1='systemd';wsl_version='3.0.3.0';wsl_store_package=@{};observed_wsl_address='192.0.2.8';bridge_facts=@{blockers=@()}}
            $script:preparationPorts=@{Inventory={return $script:recoveryFacts}}
            $net=Snapshot;$static=StableState $net.state;$static.Remove('wslIp');$guest=Guest
            $script:recoveryIntent=@{bridge_running=($Case -ne 'original_stopped');recovery=@{
                guest_graph=$guest.graph;guest_details=$guest.details;os=(Get-WslMaintenanceDigest (LinuxBinding $script:recoveryFacts));
                bridge=$net.identity;firewall=$net.firewall;hosts=$net.hosts;netsh_layout=$net.netsh.layout;
                state_static=(Get-WslMaintenanceDigest $static);old_address=(Get-WslMaintenanceDigest '192.0.2.5');
                registry_structure=(Get-WslMaintenanceDigest (RegistryStructure $net.registry $net.state))}}
            if($Case -eq 'partial'){$script:fixtureRegistry[0].value='192.0.2.8/2222'}
            if($Case -eq 'complete'){
                $script:fixtureRegistry[0].value='192.0.2.8/2222';$script:fixtureRegistry[1].value='192.0.2.8/4444';$script:fixtureState.wslIp='192.0.2.8'
            }
            if($Case -eq 'third_ip'){$script:fixtureRegistry[0].value='192.0.2.99/2222'}
            if($Case -eq 'foreign'){$script:fixture.foreign=$true}
            if($Case -eq 'guest_drift'){$script:recoveryIntent.recovery.guest_graph='unexpected'}
            if($Case -eq 'reentry'){$script:fixture.running=@()}
            if($Case -eq 'other_running'){$script:fixture.running=@('Ubuntu','Other')}
        }
        function script:Source {if($script:fixture.case -eq 'registration'){throw 'REGISTRATION_MISMATCH'}}
        function script:ReadIntent {return $script:recoveryIntent}
        function script:Running {return @($script:fixture.running)}
        function script:Relaunch {
            if($script:fixture.running.Count -ne 0){throw 'UNEXPECTED_REENTRY'}
            $script:fixture.reentries++;$script:fixture.running=@('Ubuntu')
        }
        function script:VerifyRecoveryResources {param($Intent,$Facts)}
        function script:Plan {return @{resources=@{state=$(if($script:fixture.case -eq 'resources_pending'){'CHANGE_REQUIRED'}else{'VERIFIED'});blockers=@()}}}
        function script:Apply {$script:fixture.unsafe++;throw 'RECOVERY_APPLY_FORBIDDEN'}
        function script:Shutdown {$script:fixture.unsafe++;throw 'RECOVERY_SHUTDOWN_FORBIDDEN'}
    }
    foreach($case in @('partial','complete','reentry','original_stopped','resources_pending','third_ip','foreign','guest_drift','other_running','registration')){
        & $adapter {param($c) ResetRecoveryFixture $c} $case
        $r=& $ports.Recover
        if($case -in @('partial','complete','reentry','original_stopped')){
            Assert ($r.status -ceq 'FORWARD_RECOVERY_COMPLETE' -and $r.bridge_restored -and !$r.w05_replayed) ('forward_complete_'+$case)
        }elseif($case -eq 'resources_pending'){
            Assert ($r.status -ceq 'RECOVERY_RESOURCE_STAGE_REQUIRED' -and $r.bridge_restored -and !$r.resource_verified) 'pending_resources_no_apply_replay'
        }else{
            Assert ($r.status -ceq 'RECOVERY_REQUIRED' -and (& $adapter {$script:fixture.runs.Count}) -eq 0 -and
                (& $adapter {$script:serviceCalls.Count}) -eq 0) ('forward_refusal_'+$case)
        }
        Assert ((& $adapter {$script:fixture.unsafe}) -eq 0) 'forward_never_apply_or_shutdown'
        if($case -eq 'reentry'){Assert ((& $adapter {$script:fixture.reentries}) -eq 1) 'selected_reentry_once'}
        if($case -eq 'complete'){Assert ((& $adapter {$script:fixture.runs.Count}) -eq 0) 'completed_routes_not_replayed'}
        if($case -eq 'original_stopped'){Assert ((& $adapter {$script:fixtureService.Status}) -ceq 'Stopped') 'recovery_keeps_original_stopped'}
        $cases++
    }
}
[ordered]@{status='PASS';cases=$cases;runtime_mutations=0;live_capability_claim=$false} | ConvertTo-Json -Compress
