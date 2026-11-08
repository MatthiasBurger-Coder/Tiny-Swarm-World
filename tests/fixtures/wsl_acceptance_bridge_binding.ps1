#requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$RepositoryRoot)
$ErrorActionPreference='Stop'
. (Join-Path $RepositoryRoot 'tools/windows/qualification/wsl_acceptance_bridge_binding.ps1')
$script:cases=0
function Check([bool]$condition,[string]$message){if(!$condition){throw ('Fixture: '+$message)}}
function Refuses([scriptblock]$action,[string]$code){
    $failed=$false;try{& $action | Out-Null}catch{$failed=$true;Check ($_.Exception.Message -ceq $code) ('wrong refusal '+$_.Exception.Message)}
    Check $failed ('missing refusal '+$code);$script:cases++
}
function Clone($value){return ($value | ConvertTo-Json -Depth 50 | ConvertFrom-Json)}
$s=[pscustomobject]@{schema_version=1;run_id=('a'*32);source_commit=('b'*40);source_root='C:\fixed';host='PC';original_distro='Ubuntu';
    new_distro=('TSW-Q440-'+('a'*32));original_guid='{11111111-1111-1111-1111-111111111111}';new_guid='{22222222-2222-2222-2222-222222222222}';
    original_vhd_sha256=('c'*64);new_vhd_sha256=('d'*64);firewall_query_sha256=('e'*64);pins=@{};exposure_sha256=('f'*64)}
Assert-WslBindingScenario $s;$script:cases++
$wrong=Clone $s;$wrong.new_distro='TSW-EPIC440-'+$s.run_id
Refuses {Assert-WslBindingScenario $wrong} 'BINDING_SCENARIO'
$wrong=Clone $s;$wrong.new_guid=$wrong.original_guid
Refuses {Assert-WslBindingScenario $wrong} 'BINDING_REGISTRATION_ID'
$cert=[pscustomobject]@{schema_version='tsw.windows-firewall-certificate.v1';query_sha256=$s.firewall_query_sha256;snapshot_sha256=('1'*64);
    snapshot_bytes=8903516;snapshot_schema_version=2;store='ActiveStore';association_model='PROVIDER_IDENTITY_ONE_TO_ONE';
    counts=[pscustomobject]@{rules=543;profiles=3;settings=1;address=543;application=543;interface=543;interface_type=543;port=543;security=543;service=543}}
Assert-WslBindingCertificate $cert $s.firewall_query_sha256;$script:cases++
foreach($field in @('query_sha256','snapshot_sha256','snapshot_bytes','snapshot_schema_version','store','association_model')){
    $bad=Clone $cert
    switch($field){'query_sha256'{$bad.$field='0'*64};'snapshot_sha256'{$bad.$field='invalid'};'snapshot_bytes'{$bad.$field=14680065};
        'snapshot_schema_version'{$bad.$field=$true};'store'{$bad.$field='PersistentStore'};'association_model'{$bad.$field='COUNT_ONLY'}}
    Refuses {Assert-WslBindingCertificate $bad $s.firewall_query_sha256} 'BINDING_FIREWALL_CERTIFICATE'
}
$bad=Clone $cert;$bad.counts.service=542
Refuses {Assert-WslBindingCertificate $bad $s.firewall_query_sha256} 'BINDING_FIREWALL_COUNTS'
$bad=Clone $cert;$bad | Add-Member NoteProperty raw_rules @()
Refuses {Assert-WslBindingCertificate $bad $s.firewall_query_sha256} 'BINDING_FIREWALL_CERTIFICATE'
$bad=Clone $cert;$bad.counts.rules=$true
Refuses {Assert-WslBindingCertificate $bad $s.firewall_query_sha256} 'BINDING_FIREWALL_COUNTS'
$wire=Get-WslBindingBytes $s
$decoded=Read-WslBindingWire ([Convert]::ToBase64String($wire)) (Get-WslBindingRawHash $wire)
Check ((Get-WslBindingHash $decoded) -ceq (Get-WslBindingHash $s)) 'canonical wire roundtrip';$script:cases++
$duplicate=[Text.Encoding]::UTF8.GetBytes('{"a":1,"a":2}')
Refuses {Read-WslBindingWire ([Convert]::ToBase64String($duplicate)) (Get-WslBindingRawHash $duplicate)} 'BINDING_WIRE_NONCANONICAL'

# Construct the real shared producer command without executing its firewall
# query. This requires the separately integrated, hash-pinned loader assets.
$loader=New-Module -ArgumentList $RepositoryRoot -ScriptBlock {
    param($root)
    . (Join-Path $root 'tools/windows/qualification/wsl_resource_maintenance.ps1')
}
$command=& $loader {Get-WslMaintenanceFirewallCertificateCommand}
$exe=Join-Path ([Environment]::GetFolderPath('System')) 'WindowsPowerShell\v1.0\powershell.exe'
$arguments=Get-WslBindingCertificateArguments $command
$native=Get-WslBindingProcessArguments $exe $arguments
Check ($arguments.Count -eq 4 -and $arguments[2] -ceq '-Command' -and $arguments[3] -ceq $command) 'exact actual plain source command'
Check ($command.Length -gt 20000 -and $exe.Length+4+$native.Length -le 32767) 'actual full producer fits native boundary'
Check (([Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))).Length -gt 32767) 'old real encoded transport regression';$script:cases++
# Use the Windows argv parser to check all quotes/backslashes in the actual
# command survive the same argument string used by production ProcessStartInfo.
Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;
public static class TswBindingFixtureArgv {
 [DllImport("shell32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CommandLineToArgvW(string s,out int n);
 [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr p);
 public static string[] Parse(string s){int n;IntPtr p=CommandLineToArgvW(s,out n);if(p==IntPtr.Zero)throw new InvalidOperationException("argv");try{var a=new string[n];for(int i=0;i<n;i++)a[i]=Marshal.PtrToStringUni(Marshal.ReadIntPtr(p,i*IntPtr.Size));return a;}finally{LocalFree(p);}}
}
'@
$parsed=[TswBindingFixtureArgv]::Parse(('"'+$exe+'" '+$native))
Check ($parsed.Length -eq 5 -and $parsed[4] -ceq $command) 'real producer quote roundtrip';$script:cases++
[void](Get-WslBindingProcessArguments 'c' @(('x'*32762)));$script:cases++
Refuses {Get-WslBindingProcessArguments 'c' @(('x'*32763))} 'BINDING_COMMAND_LINE_BOUND'
Refuses {Get-WslBindingProcessArguments $exe (Get-WslBindingCertificateArguments ('"'*30000))} 'BINDING_COMMAND_LINE_BOUND'
Refuses {Get-WslBindingCertificateArguments ("bad`0command")} 'BINDING_FIREWALL_COMMAND'

function Approval([string]$phase){
    $g=[ordered]@{schema_version=1;decision='GO';phase=$phase;scenario_sha256=(Get-WslBindingHash $s);source_commit=$s.source_commit;
        proposal_sha256=('9'*64);expires_at_utc=[DateTimeOffset]::UtcNow.AddSeconds((Get-WslBindingPhaseSeconds $phase)+120).ToString('o');
        reviews=@{requirements='APPROVED';architecture='APPROVED';security='APPROVED';devops='APPROVED';test_evidence='APPROVED'}}
    if($phase -cin @('StopOriginal','StageRestore')){$g.guest_quiesce_sha256='8'*64}
    return [pscustomobject]$g
}
function Protocol([string]$phase,[string]$fail='',[string]$fingerprint=('9'*64),[string]$prepareFor='Archive'){
    $context=@{events=[Collections.Generic.List[string]]::new();failureAt=$fail;fingerprint=$fingerprint}
    $script:events=$context.events
    $p=@{}
    foreach($name in @('Begin','Observe','Intent','Lock','Unlock','Archive','Stage','Switch','Protect','Stop','Stopped','Start','Heartbeat','Final','Complete','Pending','Recover','Failure')){
        $p[$name]={
            $context.events.Add($name)
            if($name -ceq 'Unlock'){$context.events.Add('unlock:'+([string]$args[0]))}
            if($name -ceq 'Lock'){$context.events.Add('lock:'+([string]$args[0]))}
            if($name -ceq $context.failureAt){throw 'BINDING_INJECTED'}
            switch($name){'Observe'{return @{fingerprint=$context.fingerprint;original_bundle_id=('7'*64)}};
                'Lock'{return [string]$args[0]};'Stage'{return @{BundleId=('6'*64)}};'Start'{return [DateTimeOffset]::UtcNow}}
        }.GetNewClosure()
    }
    $g=if($phase -ceq 'Prepare'){$null}else{Approval $phase}
    return Invoke-WslAcceptanceBridgeBinding $s $phase $g $p $prepareFor
}
$expected=@{Archive='ORIGINAL_ARCHIVED';StopOriginal='ORIGINAL_BRIDGE_STOPPED';Bind='NEW_BINDING_READY';
    StageRestore='ORIGINAL_PAYLOAD_STAGED_STOPPED';ResumeOriginal='ORIGINAL_BINDING_RESTORED';Recover='RECOVERED_STOPPED'}
foreach($phase in $expected.Keys){
    $r=Protocol $phase
    Check ($r.status -ceq $expected[$phase] -and !$r.application_ready) ('phase '+$phase)
    Check ($events.Contains('lock:Global\TinySwarmWorldWslBridgeServiceUpdate') -and $events.Contains('lock:Global\TinySwarmWorldWslBridgeReconcile')) 'owned locks'
    Check ($events.IndexOf('Observe') -gt $events.IndexOf('Lock')) 'fresh observation under lock'
    Check ($events.IndexOf('Intent') -lt $(if($phase -ceq 'Archive'){$events.IndexOf('Archive')}elseif($phase -ceq 'ResumeOriginal'){$events.IndexOf('Pending')}elseif($phase -ceq 'Recover'){$events.IndexOf('Stop')}elseif($phase -ceq 'StopOriginal'){$events.IndexOf('Stop')}else{$events.IndexOf('Stage')})) 'intent before effects'
    if($phase -cin @('Bind','ResumeOriginal')){
        Check ($events.IndexOf('unlock:Global\TinySwarmWorldWslBridgeReconcile') -lt $events.IndexOf('Start')) 'release reconcile before real heartbeat'
        Check ($events.IndexOf('Heartbeat') -lt $events.IndexOf('Complete')) 'heartbeat before commit'
    }else{Check (!$events.Contains('Start') -and !$events.Contains('Heartbeat')) 'stopped-only phase'}
    $script:cases++
}
$r=Protocol 'Prepare' '' ('9'*64) 'StopOriginal'
Check ($r.status -ceq 'PREPARED_READ_ONLY' -and $r.target_phase -ceq 'StopOriginal' -and !$events.Contains('Lock') -and !$events.Contains('Intent')) 'prepare no effects';$script:cases++
$r=Protocol 'Bind' '' ('0'*64)
Check ($r.error -ceq 'BINDING_PRESTATE_DRIFT' -and !$events.Contains('Intent') -and !$events.Contains('Stop')) 'CAS before effects';$script:cases++
foreach($step in @('Stage','Stop','Switch','Protect','Stopped','Start','Heartbeat','Final','Complete')){
    $r=Protocol 'Bind' $step
    Check ($r.error -ceq 'BINDING_INJECTED' -and $r.status -ceq 'BLOCKED') ('failure '+$step)
    Check ($events.Contains('unlock:Global\TinySwarmWorldWslBridgeServiceUpdate')) 'failure releases update lock'
    Check (!$events.Contains('Recover')) 'no automatic cross-guest restore/start';$script:cases++
}
$go=Approval 'StopOriginal';$go.PSObject.Properties.Remove('guest_quiesce_sha256')
Refuses {Assert-WslBindingApproval $go $s 'StopOriginal' ('9'*64)} 'BINDING_GO'
$go=Approval 'Bind';$go.expires_at_utc=[DateTimeOffset]::UtcNow.AddSeconds(60).ToString('o')
Refuses {Assert-WslBindingApproval $go $s 'Bind' ('9'*64)} 'BINDING_GO_EXPIRED'

# Execute the actual nested production StartOwned body in an isolated module,
# replacing only observations and the SCM transport. Payload drift must refuse
# before Start-BridgeServiceChecked, including after a previously admitted GO.
$tokens=$null;$parseErrors=$null
$tree=[Management.Automation.Language.Parser]::ParseFile((Join-Path $RepositoryRoot 'tools/windows/qualification/wsl_acceptance_bridge_binding.ps1'),[ref]$tokens,[ref]$parseErrors)
Check ($parseErrors.Count -eq 0) 'binding source parses'
# Execute the actual nested module constructor, without the factory's provider
# preflight or any port effect. Internal helpers must not replace the caller's
# Source/Run, while explicit module invocation and captured ports remain usable.
$constructors=@($tree.FindAll({param($a) $a -is [Management.Automation.Language.CommandAst] -and $a.GetCommandName() -ceq 'New-Module'},$true))
Check ($constructors.Count -eq 1) 'one actual binding module constructor'
$moduleSeam=New-Module -ArgumentList $RepositoryRoot,$constructors[0].Extent.Text -ScriptBlock {
    param($root,$constructor)
    function Source {return 'CALLER_SOURCE'}
    function Run {return 'CALLER_RUN'}
    $Scenario=@{source_root=$root;run_id=('7'*32)}
    $nested=& ([scriptblock]::Create($constructor))
    if($nested -isnot [Management.Automation.PSModuleInfo] -or $nested.ExportedFunctions.Count -ne 0){throw 'BINDING_HELPERS_EXPORTED'}
    if((Source) -cne 'CALLER_SOURCE' -or (Run) -cne 'CALLER_RUN'){throw 'BINDING_CALLER_HELPERS_REPLACED'}
    if((& $nested {Get-WslBindingPhaseSeconds 'Archive'}) -ne 180){throw 'BINDING_EXPLICIT_MODULE_CALL_BROKEN'}
    if((& $nested {@($script:bindingPorts.Keys).Count}) -ne 18){throw 'BINDING_CAPTURED_PORTS_MISSING'}
    $probe={& $nested {param($value) Get-WslBindingHash $value} @{proof='private-module'}}.GetNewClosure()
    if((& $probe) -cnotmatch '\A[0-9a-f]{64}\z'){throw 'BINDING_MODULE_CLOSURE_BROKEN'}
    Remove-Module $nested -Force
    Export-ModuleMember -Function @() -Alias @()
}
Remove-Module $moduleSeam -Force;$script:cases++
$definitions=@($tree.FindAll({param($a) $a -is [Management.Automation.Language.FunctionDefinitionAst] -and $a.Name -ceq 'StartOwned'},$true))
Check ($definitions.Count -eq 1) 'one actual StartOwned body'
$startModule=New-Module -ArgumentList $RepositoryRoot,$definitions[0].Extent.Text -ScriptBlock {
    param($root,$body)
    . (Join-Path $root 'tools/windows/qualification/wsl_acceptance_bridge_binding.ps1')
    function Claim {param($Reserve) return 360}
    function Registrations {return $script:testRegs}
    function Running {return $script:testRunning}
    function Payload {return $script:testPayload}
    function ReadDescriptor {return $script:testDescriptor}
    function Start-BridgeServiceChecked {$script:startCalls++}
    . ([scriptblock]::Create($body))
}
$startPayload=[pscustomobject]@{status='Stopped';hashes=@{bundle=('1'*64);wrapper=('2'*64)};policy_sha256=('3'*64);
    config=[pscustomobject]@{distro=$s.new_distro}}
$startDescriptor=[pscustomobject]@{bound_hashes=$startPayload.hashes;archive_hashes=$startPayload.hashes;
    original=[pscustomobject]@{policy_sha256=$startPayload.policy_sha256;registration_sha256=('4'*64);config=[pscustomobject]@{distro='auto'}}}
$startRegs=[pscustomobject]@{hash=('4'*64);default_guid=$s.original_guid}
function StartSeam($phase,$payload,$descriptor,$regs,$names){
    return & $startModule {param($spec,$phase,$payload,$descriptor,$regs,$names)
        $script:bindingSpec=$spec;$script:bindingPhase=$phase;$script:testPayload=$payload;$script:testDescriptor=$descriptor;
        $script:testRegs=$regs;$script:testRunning=$names;$script:startCalls=0
        try{StartOwned | Out-Null;return @{calls=$startCalls;error='NONE'}}catch{return @{calls=$startCalls;error=$_.Exception.Message}}
    } $s $phase $payload $descriptor $regs $names
}
$r=StartSeam 'Bind' $startPayload $startDescriptor $startRegs @($s.new_distro)
Check ($r.calls -eq 1 -and $r.error -ceq 'NONE') 'actual prestart positive';$script:cases++
foreach($kind in @('hash','running','config','policy','registration','guest')){
    $p=Clone $startPayload;$d=Clone $startDescriptor;$reg=Clone $startRegs;$names=@($s.new_distro)
    switch($kind){'hash'{$p.hashes.bundle='0'*64};'running'{$p.status='Running'};'config'{$p.config.distro='auto'};
        'policy'{$p.policy_sha256='0'*64};'registration'{$reg.hash='0'*64};'guest'{$names=@($s.original_distro)}}
    $r=StartSeam 'Bind' $p $d $reg $names
    Check ($r.calls -eq 0 -and $r.error -cin @('BINDING_START_CAS','BINDING_START_CONFIG')) ('actual prestart drift '+$kind);$script:cases++
}
$p=Clone $startPayload;$p.config=[pscustomobject]@{distro='auto'}
$r=StartSeam 'ResumeOriginal' $p $startDescriptor $startRegs @($s.original_distro)
Check ($r.calls -eq 1 -and $r.error -ceq 'NONE') 'actual original auto positive';$script:cases++
$reg=Clone $startRegs;$reg.default_guid=$s.new_guid
$r=StartSeam 'ResumeOriginal' $p $startDescriptor $reg @($s.original_distro)
Check ($r.calls -eq 0 -and $r.error -ceq 'BINDING_ORIGINAL_DEFAULT_GUID') 'actual original auto default drift';$script:cases++
$p.config=[pscustomobject]@{distro=$s.new_distro}
$r=StartSeam 'ResumeOriginal' $p $startDescriptor $startRegs @($s.original_distro)
Check ($r.calls -eq 0 -and $r.error -ceq 'BINDING_START_CONFIG') 'actual original config drift';$script:cases++

# Exercise existing production payload transaction primitives on newly created
# disposable files. No SCM, ACL, guest, registry, firewall or network access.
. (Join-Path $RepositoryRoot 'bootstrap/windows/tws-wsl-bridge.ps1') -Action inventory
function Set-BridgeExactAcl {param([string]$Path) if(!(Test-Path -LiteralPath $Path)){throw 'fixture ACL target absent'}}
$script:ServiceRoot=Join-Path ([IO.Path]::GetTempPath()) ('tsw-binding-payload-'+[guid]::NewGuid().ToString('N'))
$script:ServiceBundleRoot=Join-Path $ServiceRoot 'bundle'
$script:ServiceWrapperPath=Join-Path $ServiceRoot ($ServiceName+'.exe')
$script:ServiceDefinitionPath=Join-Path $ServiceRoot ($ServiceName+'.xml')
$script:InstallationManifestPath=Join-Path $ServiceRoot 'installation-manifest.json'
$script:TransactionJournalPath=Join-Path $ServiceRoot 'upgrade-transaction.json'
function Test-PathInsideBridgeServiceRoot {param([string]$Path) return ([IO.Path]::GetFullPath($Path).StartsWith($ServiceRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase))}
function NewFixturePayload([string]$root,[string]$label){
    [IO.Directory]::CreateDirectory((Join-Path $root 'bundle')) | Out-Null
    [IO.File]::WriteAllText((Join-Path $root 'bundle/payload.txt'),$label)
    foreach($name in @(($ServiceName+'.exe'),($ServiceName+'.xml'),'installation-manifest.json')){[IO.File]::WriteAllText((Join-Path $root $name),$label+':'+$name)}
    return [pscustomobject]@{Root=$root;Bundle=(Join-Path $root 'bundle');Wrapper=(Join-Path $root ($ServiceName+'.exe'));
        Definition=(Join-Path $root ($ServiceName+'.xml'));InstallationManifest=(Join-Path $root 'installation-manifest.json');BundleId=('3'*64)}
}
try{
    [void](NewFixturePayload $ServiceRoot 'original')
    $archive=Join-Path $ServiceRoot '.staging-acceptance-original'
    [void](NewFixturePayload $archive 'original')
    $archiveHash=Get-BridgePayloadFingerprint $archive
    $stage=NewFixturePayload (Join-Path $ServiceRoot '.staging-fixture') 'new'
    $tx=New-BridgePayloadTransaction $stage $true $true $false ('4'*64)
    $original=@($tx.Items | ForEach-Object{$_.OriginalFingerprint})
    Write-BridgeTransactionJournal $tx;Switch-BridgePayload $tx
    foreach($item in $tx.Items){Check ((Get-BridgePayloadFingerprint $item.Active) -ceq $item.StagedFingerprint) 'real switch'}
    Restore-BridgePayload $tx
    foreach($i in 0..3){Check ((Get-BridgePayloadFingerprint $tx.Items[$i].Active) -ceq $original[$i]) 'exact original restore'}
    Complete-BridgePayloadRollback $tx
    Check ((Get-BridgePayloadFingerprint $archive) -ceq $archiveHash -and !(Test-Path $TransactionJournalPath)) 'archive survives rollback cleanup';$script:cases++
    $stage=NewFixturePayload (Join-Path $ServiceRoot '.staging-fixture') 'new'
    $tx=New-BridgePayloadTransaction $stage $true $true $false ('4'*64)
    Switch-BridgePayload $tx;Complete-BridgePayloadTransaction $tx
    Check ((Get-BridgePayloadFingerprint $archive) -ceq $archiveHash -and !(Test-Path $tx.RollbackRoot) -and !(Test-Path $TransactionJournalPath)) 'archive survives commit cleanup';$script:cases++
    $stage=NewFixturePayload (Join-Path $ServiceRoot '.staging-fixture') 'third'
    $tx=New-BridgePayloadTransaction $stage $true $true $false ('3'*64)
    Switch-BridgePayload $tx
    [IO.File]::WriteAllText($ServiceWrapperPath,'unknown external modification')
    $denied=$false;try{Restore-BridgePayload $tx}catch{$denied=$true}
    Check ($denied -and [IO.File]::ReadAllText($ServiceWrapperPath) -ceq 'unknown external modification') 'real rollback refuses foreign bytes';$script:cases++
    # Feed synthetic files only to the actual timestamp/path/bundle validator.
    # This proves parser refusals, never a genuine service heartbeat or host GO.
    $script:StatePath=Join-Path $ServiceRoot 'heartbeat-fixture.json'
    $script:InstalledConfigPath=Join-Path $ServiceBundleRoot 'config.json'
    $script:InstalledPortRegistryPath=Join-Path $ServiceBundleRoot 'ports.yaml'
    $transition=[DateTimeOffset]::UtcNow.AddSeconds(-1)
    $heartbeat=[pscustomobject]@{generatedAt=[DateTimeOffset]::UtcNow.ToString('o');agentMode='windows-service';agentStatus='ready';
        bundleId=('2'*64);configPath=$InstalledConfigPath;registryPath=$InstalledPortRegistryPath}
    [IO.File]::WriteAllText($StatePath,($heartbeat | ConvertTo-Json))
    Wait-BridgeServiceHeartbeat $transition ('2'*64) 1;$script:cases++
    foreach($field in @('generatedAt','bundleId','agentStatus','configPath')){
        $bad=Clone $heartbeat
        switch($field){'generatedAt'{$bad.$field=$transition.AddSeconds(-1).ToString('o')};'bundleId'{$bad.$field='0'*64};
            'agentStatus'{$bad.$field='starting'};'configPath'{$bad.$field=Join-Path $ServiceRoot 'foreign.json'}}
        [IO.File]::WriteAllText($StatePath,($bad | ConvertTo-Json))
        $denied=$false;try{Wait-BridgeServiceHeartbeat $transition ('2'*64) 1}catch{$denied=$true}
        Check $denied ('actual heartbeat validator '+$field);$script:cases++
    }
}finally{Remove-Item -LiteralPath $ServiceRoot -Recurse -Force -ErrorAction SilentlyContinue}
[pscustomobject]@{status='PASS';cases=$script:cases;runtime_mutations=0;live_capability_claim=$false;real_payload_primitives=$true} | ConvertTo-Json -Compress
