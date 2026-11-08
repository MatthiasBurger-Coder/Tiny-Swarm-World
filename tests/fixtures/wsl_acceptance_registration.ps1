param([Parameter(Mandatory=$true)][string]$RepositoryRoot,[switch]$CertificateTransportContract,[switch]$NativeExecutableContract,[switch]$BridgeLogContract)
$ErrorActionPreference='Stop'
. (Join-Path $RepositoryRoot 'tools/windows/qualification/wsl_acceptance_registration.ps1')
function Assert($yes,[string]$code){if(!$yes){throw $code}}
function Copy-RegistrationFixtureValue($x){return ConvertTo-PreparationHashtable ($x|ConvertTo-Json -Depth 30 -Compress|ConvertFrom-Json)}
# Pure local conversion only; no production transport is installed in this fixture.
function ConvertTo-PreparationHashtable($x){
 if($null -eq $x -or $x -is [string] -or $x -is [ValueType]){return $x}
 if($x -is [Collections.IDictionary]){$o=@{};foreach($k in $x.Keys){$o[$k]=ConvertTo-PreparationHashtable $x[$k]};return $o}
 if($x -is [Collections.IEnumerable]){return ,@($x|ForEach-Object{ConvertTo-PreparationHashtable $_})}
 $o=@{};foreach($p in $x.PSObject.Properties){$o[$p.Name]=ConvertTo-PreparationHashtable $p.Value};return $o
}
function Baseline {
 return @{default='{00000000-0000-0000-0000-000000000001}';global_sha256=('g'*64);running_sha256=('r'*64);
 registrations=@(@{id='{00000000-0000-0000-0000-000000000001}';name='Ubuntu';version=2;running=$true;
  values_sha256='original-registry';base_sha256='original-base';vhd_identity='original-fileid';rootfs_sha256=$null;path_matches=$false})}
}
function Scenario($b){return @{schema_version=1;operation='WSL_ACCEPTANCE_REGISTRATION';decision='GO';run_id=('a'*32);
 host='PC';source_commit=('b'*40);source_pins_sha256=('c'*64);preserve_sha256=(Get-AcceptanceRegistrationDigest $b);
 image_sha256='48d56724b5c8e60f24893e83e73bbb58c60b3ca22fba3da977075420acd54104';
 image_signer='843938DF228D22F7B3742BC0D94AA3F0EFE21092';expires_utc=([DateTimeOffset]::UtcNow.AddSeconds(3000).ToString('yyyy-MM-ddTHH:mm:ssZ'))}}
function Ports([string]$fault=''){
 $ctx=@{before=(Baseline);state=$null;events=[Collections.ArrayList]::new();imports=0;observations=0;fault=$fault;imported=$false}
 $p=@{}
 $p.Source={param($s) [void]$ctx.events.Add('source');if($ctx.fault -ceq 'source' -or $s.host -cne 'PC' -or $s.source_commit -cne ('b'*40) -or $s.source_pins_sha256 -cne ('c'*64)){throw 'PRIVATE_CANARY'}}.GetNewClosure()
 $p.Clock={return [DateTimeOffset]::UtcNow}
 $p.Preconditions={param($s) [void]$ctx.events.Add('preconditions');if($ctx.fault -cin @('image','path','acl','storage','executable')){throw 'PREFLIGHT'}}.GetNewClosure()
 $p.Load={param($s) return Copy-RegistrationFixtureValue $ctx.state}.GetNewClosure()
 $p.Lock={param($s) [void]$ctx.events.Add('lock');if($ctx.fault -ceq 'lock'){throw 'LOCK'};return 'owned-lock'}.GetNewClosure()
 $p.Unlock={param($lock) [void]$ctx.events.Add('unlock')}.GetNewClosure()
 $p.Intent={param($s,$before) [void]$ctx.events.Add('intent');$ctx.state=@{schema_version=1;scenario_sha256=(Get-AcceptanceRegistrationDigest $s);stage='intent';baseline=(Copy-RegistrationFixtureValue $before);receipt=$null};return Copy-RegistrationFixtureValue $ctx.state}.GetNewClosure()
 $p.Save={param($s,$state) [void]$ctx.events.Add('save:'+ $state.stage);if($ctx.fault -ceq 'pending_write'){throw 'CAS'};$ctx.state=Copy-RegistrationFixtureValue $state;return Copy-RegistrationFixtureValue $state}.GetNewClosure()
 $p.Import={param($s,$name) Assert ($ctx.state.stage -ceq 'import_pending') 'effect_before_intent';Assert ($name -ceq ('TSW-Q440-'+$s.run_id)) 'import_name';[void]$ctx.events.Add('import');$ctx.imports++;$ctx.imported=$true;if($ctx.fault -ceq 'timeout'){throw 'UNCERTAIN'}}.GetNewClosure()
 $p.Receipt={param($s,$state) [void]$ctx.events.Add('receipt');if($ctx.fault -ceq 'receipt_write'){throw 'CAS'};$ctx.state=Copy-RegistrationFixtureValue $state;return Copy-RegistrationFixtureValue $state}.GetNewClosure()
 $p.Observe={param($s)
  $ctx.observations++;[void]$ctx.events.Add('observe');$b=Copy-RegistrationFixtureValue $ctx.before
  if($ctx.imported){
   $new=@{id='{00000000-0000-0000-0000-000000000002}';name=('TSW-Q440-'+$s.run_id);version=2;running=$false;
     values_sha256='new-registry';base_sha256='new-base';vhd_identity='new-fileid';rootfs_sha256=('f'*64);path_matches=$true}
   $b.registrations+=@($new)
   switch($ctx.fault){
    'original_registry'{$b.registrations[0].values_sha256='changed'}
    'original_vhd'{$b.registrations[0].vhd_identity='changed'}
    'original_state'{$b.registrations[0].running=$false}
    'default'{$b.default=$new.id}
    'global'{$b.global_sha256='changed'}
    'running_set'{$b.running_sha256='changed'}
    'new_running'{$new.running=$true}
    'new_version'{$new.version=1}
    'new_path'{$new.path_matches=$false}
    'new_vhd'{$new.vhd_identity=''}
    'extra'{$b.registrations+=@(@{id='{00000000-0000-0000-0000-000000000003}';name='foreign'})}
    'duplicate'{$new.id=$b.registrations[0].id}
    'wrong_name'{$new.name='FOREIGN'}
   }
  }
  if($ctx.fault -ceq 'race' -and $ctx.observations -gt 1){$b.global_sha256='changed'}
  return $b
 }.GetNewClosure()
 $p._ctx=$ctx;return $p
}
if($BridgeLogContract){
 $s=Scenario (Baseline);$ports=New-WslAcceptanceRegistrationProductionPorts $s
 $adapter=$ports.Source.Module.SessionState.PSVariable.GetValue('module')
 $temp=Join-Path ([IO.Path]::GetTempPath()) ('tsw-registration-log-'+[Guid]::NewGuid().ToString('N'))
 [void][IO.Directory]::CreateDirectory((Join-Path $temp 'logs'))
 $file=Join-Path $temp 'logs/TinySwarmWorldWslBridge.out.log.old'
 $stream=[IO.File]::Open($file,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$stream.SetLength(5641197)}finally{$stream.Dispose()}
 $transport=New-Module -ScriptBlock {
  function Get-PreparationExecutable($Name){return 'fake-read-only-transport'}
  function Assert-PreparationEvidencePath($Path){}
 }
 try{
  & $adapter {
   param($transport,$temp,$file)
   $original=$script:prep;$script:prep=$transport;$script:fixtureBridge=$temp
   try{
    function Join-Path {param($Path,$ChildPath)
     if($ChildPath -ceq 'TinySwarmWorld/WslBridge'){return $script:fixtureBridge}
     return Microsoft.PowerShell.Management\Join-Path $Path $ChildPath
    }
    function Test-Path {param($LiteralPath,$PathType)
     if($LiteralPath.StartsWith($script:fixtureBridge,[StringComparison]::OrdinalIgnoreCase)){return Microsoft.PowerShell.Management\Test-Path -LiteralPath $LiteralPath}
     return $false
    }
    function FirewallCertificate {return @{fixed='full-certificate-contract-elsewhere'}}
    function Run {param($Exe,$Arguments,$Seconds,$Limit) return @{stdout='unchanged-full-fixture-output';stderr='';exit_code=0}}
    $limit=BridgeFileLimit $temp $file
    if($limit -ne 16777216){throw 'known_log_limit'}
    $actual=BridgeFileHash $file $limit 5641197
    if($actual -cne (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash){throw 'full_log_hash_mismatch'}
    $code='';try{[void](BridgeFileHash $file $limit 5641196)}catch{$code=$_.Exception.Message}
    if($code -cne 'BRIDGE_FILE_DRIFT'){throw 'collected_size_drift_admitted'}
    $before=GlobalProof
    $stream=[IO.File]::Open($file,[IO.FileMode]::Open,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try{$stream.WriteByte(123)}finally{$stream.Dispose()}
    if((GlobalProof) -ceq $before){throw 'changed_log_bytes_lost'}
    $unknown=Join-Path $temp 'logs/foreign.out.log.old';[IO.File]::Move($file,$unknown)
    $code='';try{[void](GlobalProof)}catch{$code=$_.Exception.Message}
    if($code -cne 'BRIDGE_FILE_BOUND'){throw 'unknown_oversized_admitted'}
    [IO.File]::Move($unknown,$file)
    $nested=Join-Path $temp 'logs/nested';[void][IO.Directory]::CreateDirectory($nested)
    $nestedFile=Join-Path $nested 'TinySwarmWorldWslBridge.out.log.old';[IO.File]::Move($file,$nestedFile)
    $code='';try{[void](GlobalProof)}catch{$code=$_.Exception.Message}
    if($code -cne 'BRIDGE_FILE_BOUND'){throw 'nested_log_exemption'}
    [IO.File]::Move($nestedFile,$file);[IO.Directory]::Delete($nested)
    $stream=[IO.File]::Open($file,[IO.FileMode]::Open,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try{$stream.SetLength(16777217)}finally{$stream.Dispose()}
    $code='';try{[void](GlobalProof)}catch{$code=$_.Exception.Message}
    if($code -cne 'BRIDGE_FILE_BOUND'){throw 'log_cap_ignored'}
    $code='';try{[void](BridgeFileHash $file 16777216 16777217)}catch{$code=$_.Exception.Message}
    if($code -cne 'BRIDGE_FILE_BOUND'){throw 'hash_read_cap_ignored'}
    [IO.File]::Delete($file)
    foreach($name in @('TinySwarmWorldWslBridge.out.log','TinySwarmWorldWslBridge.out.log.old','TinySwarmWorldWslBridge.err.log','TinySwarmWorldWslBridge.err.log.old')){
     $stream=[IO.File]::Open((Join-Path $temp ('logs/'+$name)),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
     try{$stream.SetLength(16777216)}finally{$stream.Dispose()}
    }
    [IO.File]::WriteAllBytes((Join-Path $temp 'payload.json'),[byte[]]@(1))
    $code='';try{[void](GlobalProof)}catch{$code=$_.Exception.Message}
    if($code -cne 'BRIDGE_TOTAL_BOUND'){throw 'aggregate_cap_ignored'}
   }finally{$script:prep=$original}
  } $transport $temp $file
 }finally{if([IO.Directory]::Exists($temp)){[IO.Directory]::Delete($temp,$true)}}
 [ordered]@{status='PASS';cases=9;full_log_bytes=5641197;runtime_mutations=0;imports=0}|ConvertTo-Json -Compress
 exit 0
}
if($NativeExecutableContract){
 $s=Scenario (Baseline);$ports=New-WslAcceptanceRegistrationProductionPorts $s
 $adapter=$ports.Source.Module.SessionState.PSVariable.GetValue('module')
 Assert ($null -ne $adapter) 'registration_native_module'
 # Exercise the actual OS-native chain/signature validator before fake faults.
 $actual=& $adapter {TrustedWsl}
 Assert ([IO.Path]::GetFullPath($actual) -ieq (Join-Path ([Environment]::GetFolderPath('System')) 'wsl.exe')) 'actual_native_wsl'
 $transport=New-Module -ScriptBlock {
  function Get-PreparationExecutable($Name){return Join-Path ([Environment]::GetFolderPath('System')) 'wsl.exe'}
  function Assert-PreparationLocalPath($Path){}
 }
 & $adapter {
  param($transport)
  $original=$script:prep;$script:prep=$transport
  try{
   function Get-Item {param($LiteralPath,[switch]$Force,$ErrorAction)
    return [pscustomobject]@{Attributes=$(if($script:fault -ceq 'reparse'){[IO.FileAttributes]::ReparsePoint}else{[IO.FileAttributes]::Normal});PSIsContainer=$false}
   }
   function Get-Acl {param($LiteralPath,$ErrorAction)
    $acl=[pscustomobject]@{Fault=$script:fault}
    $acl|Add-Member ScriptMethod GetOwner {param($type)
     $sid=if($this.Fault -ceq 'foreign-owner'){'S-1-5-21-111-222-333-444'}else{'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464'}
     return [Security.Principal.SecurityIdentifier]::new($sid)
    }
    $acl|Add-Member ScriptMethod GetAccessRules {param($explicit,$inherited,$type)
     if($this.Fault -ceq 'untrusted-write'){
      return @([pscustomobject]@{PropagationFlags=[Security.AccessControl.PropagationFlags]::None;AccessControlType='Allow';FileSystemRights=[Security.AccessControl.FileSystemRights]::WriteData;IdentityReference=[Security.Principal.SecurityIdentifier]::new('S-1-1-0')})
     };return @()
    }
    return $acl
   }
   function Get-AuthenticodeSignature {param($LiteralPath,$ErrorAction)
    return @{Status=$(if($script:fault -ceq 'signature'){'Invalid'}else{'Valid'});SignerCertificate=@{Subject=$(if($script:fault -ceq 'signer'){'CN=Microsoft impostor, O=Foreign'}else{'CN=Microsoft Windows, O=Microsoft Corporation, C=US'})}}
   }
   $script:fault='';[void](TrustedWsl)
   foreach($case in @(@('foreign-owner','WSL_EXECUTABLE_OWNER'),@('reparse','WSL_EXECUTABLE_REPARSE'),@('untrusted-write','WSL_EXECUTABLE_ACL'),@('signature','WSL_EXECUTABLE_UNTRUSTED'),@('signer','WSL_EXECUTABLE_UNTRUSTED'))){
    $script:fault=$case[0];$code='';try{[void](TrustedWsl)}catch{$code=$_.Exception.Message}
    if($code -cne $case[1]){throw 'native_fault_not_rejected'}
   }
   & $transport {function script:Get-PreparationExecutable($Name){return Join-Path ([Environment]::GetFolderPath('UserProfile')) 'wsl.exe'}}
   $script:fault='';$code='';try{[void](TrustedWsl)}catch{$code=$_.Exception.Message}
   if($code -cne 'WSL_EXECUTABLE_PATH'){throw 'native_wrong_path_admitted'}
  }finally{$script:prep=$original}
 } $transport
 [ordered]@{status='PASS';cases=8;runtime_mutations=0;actual_native_binary_verified=$true;imports=0}|ConvertTo-Json -Compress
 exit 0
}
if($CertificateTransportContract){
 $s=Scenario (Baseline);$ports=New-WslAcceptanceRegistrationProductionPorts $s
 $adapter=$ports.Source.Module.SessionState.PSVariable.GetValue('module')
 Assert ($null -ne $adapter) 'registration_production_module_binding'
 $raw=([ordered]@{schema_version='tsw.windows-firewall-certificate.v1';
  query_sha256='a6a5aee14f32ada47cd14b58f59372fc0ba21ceaef64401d93b94822932c19e5';snapshot_sha256=('c'*64);
  snapshot_bytes=8903516;snapshot_schema_version=2;store='ActiveStore';association_model='PROVIDER_IDENTITY_ONE_TO_ONE';
  counts=[ordered]@{rules=543;profiles=3;settings=1;address=543;application=543;interface=543;
   interface_type=543;port=543;security=543;service=543}} | ConvertTo-Json -Depth 4 -Compress)
 $transport=New-Module -ArgumentList $raw -ScriptBlock {
  param($raw)
  $script:raw=$raw;$script:calls=0
  function Get-PreparationExecutable($Name){return 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'}
  function Invoke-PreparationProcess($File,$Arguments,$Seconds){
   if($Arguments[-1] -notlike '*tsw.windows-firewall-certificate.v1*' -or $Seconds -ne 120){throw 'wrong_certificate_transport'}
   $script:calls++;return @{stdout=$script:raw;stderr='';exit_code=0}
  }
 }
 & $adapter {
  param($transport)
  $original=$script:prep
  try{
   $script:prep=$transport
   $first=Get-AcceptanceRegistrationDigest (FirewallCertificate)
   for($i=0;$i -lt 7;$i++){if((Get-AcceptanceRegistrationDigest (FirewallCertificate)) -cne $first){throw 'unexpected_cert_drift'}}
   if($script:calls -ne 8 -or $script:bytes -gt 32768 -or (& $transport {$script:calls}) -ne 8){throw 'certificate_cached_or_full_transported'}
   & $transport {$script:raw=$script:raw.Replace(('c'*64),('d'*64))}
   if((Get-AcceptanceRegistrationDigest (FirewallCertificate)) -ceq $first){throw 'changed_foreign_digest_lost'}
   & $transport {$script:raw=$script:raw.Replace('"snapshot_bytes":8903516','"snapshot_bytes":true')}
   $failed=$false;try{$null=FirewallCertificate}catch{if($_.Exception.Message -ceq 'FIREWALL_CERTIFICATE_INVALID'){$failed=$true}}
   if(!$failed){throw 'malformed_certificate_admitted'}
   & $transport {$script:raw='x'*5000}
   $failed=$false;try{$null=FirewallCertificate}catch{if($_.Exception.Message -ceq 'REGISTRATION_COMMAND_FAILED'){$failed=$true}}
   if(!$failed){throw 'transport_bound_ignored'}
  }finally{$script:prep=$original}
 } $transport
 [ordered]@{status='PASS';cases=5;runtime_mutations=0;live_capability_claim=$false;provider_queries=0} | ConvertTo-Json -Compress
 exit 0
}
$cases=0
$p=Ports;$s=Scenario $p._ctx.before
$r=Invoke-WslAcceptanceRegistration $s 'Plan' $p
Assert ($r.status -ceq 'PLAN_ONLY' -and $null -eq $p._ctx.state -and $p._ctx.imports -eq 0) 'plan_effect';$cases++
$p=Ports;$s=Scenario $p._ctx.before
$r=Invoke-WslAcceptanceRegistration $s 'Import' $p
Assert ($r.status -ceq 'IMPORTED_STOPPED' -and $r.registration_verified -and !$r.services_verified) 'import_result'
Assert ($p._ctx.state.stage -ceq 'registered' -and $p._ctx.state.receipt.vhd_identity -ceq 'new-fileid') 'missing_actual_receipt'
Assert ([Array]::IndexOf(@($p._ctx.events),'save:import_pending') -lt [Array]::IndexOf(@($p._ctx.events),'import')) 'write_ahead'
Assert ($p._ctx.events[-1] -ceq 'unlock') 'lock_release';$cases++
$events=$p._ctx.events.Count
$r=Invoke-WslAcceptanceRegistration $s 'Verify' $p
Assert ($r.status -ceq 'VERIFIED_STOPPED' -and $p._ctx.imports -eq 1 -and @($p._ctx.events|Select-Object -Skip $events|Where-Object{$_ -match '^(intent|save|receipt|import|lock)'}).Count -eq 0) 'verify_effect';$cases++
$r=Invoke-WslAcceptanceRegistration $s 'Import' $p
Assert ($r.status -ceq 'BLOCKED' -and $r.recovery_required -and $p._ctx.imports -eq 1) 'replay';$cases++
foreach($fault in @('source','image','path','acl','storage','executable','lock','race','pending_write')){
 $p=Ports $fault;$s=Scenario $p._ctx.before;$r=Invoke-WslAcceptanceRegistration $s 'Import' $p
 Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.imports -eq 0) ('pre_effect_'+$fault)
 Assert (($r|ConvertTo-Json -Compress) -notmatch 'PRIVATE_CANARY') 'raw_error';$cases++
}
foreach($fault in @('timeout','receipt_write','original_registry','original_vhd','original_state','default','global','running_set',
 'new_running','new_version','new_path','new_vhd','extra','duplicate','wrong_name')){
 $p=Ports $fault;$s=Scenario $p._ctx.before;$r=Invoke-WslAcceptanceRegistration $s 'Import' $p
 Assert ($r.status -ceq 'RECOVERY_REQUIRED' -and $r.import_attempted -and !$r.registration_verified -and $p._ctx.imports -eq 1) ('partial_'+$fault)
 $again=Invoke-WslAcceptanceRegistration $s 'Import' $p
 Assert ($again.status -cne 'IMPORTED_STOPPED' -and $p._ctx.imports -eq 1) ('partial_replay_'+$fault);$cases++
}
foreach($change in @(@{decision='PLAN'},@{expires_utc=([DateTimeOffset]::UtcNow.AddSeconds(300).ToString('yyyy-MM-ddTHH:mm:ssZ'))},
 @{host='FOREIGN'},@{source_commit=('f'*40)},@{source_pins_sha256=('e'*64)},@{image_sha256=('d'*64)},@{image_signer='foreign'},@{run_id='../foreign'},@{schema_version=$true},@{operation='OTHER'},@{extra='value'})){
 $p=Ports;$s=Scenario $p._ctx.before;foreach($k in $change.Keys){$s[$k]=$change[$k]}
 $r=Invoke-WslAcceptanceRegistration $s 'Import' $p
 Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.imports -eq 0) 'bad_scenario';$cases++
}
$p=Ports;$s=Scenario $p._ctx.before;$r=Invoke-WslAcceptanceRegistration $s 'Verify' $p
Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.imports -eq 0) 'verify_unknown_receipt';$cases++
# Inspect the actual production import function AST: no arbitrary argv or effects.
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $RepositoryRoot 'tools/windows/qualification/wsl_acceptance_registration.ps1'),[ref]$tokens,[ref]$errors)
Assert ($errors.Count -eq 0) 'production_syntax'
$import=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'ImportGuest'},$true).Extent.Text
Assert ($import.Contains("@('--import',"+'$name,'+'$script:install,'+'$script:image,'+"'--version','2') 600 1048576")) 'production_argv'
foreach($forbidden in @('--unregister','--terminate','--shutdown','--set-default','--exec','--install')){Assert (!$import.Contains($forbidden)) 'forbidden_import_effect'}
Assert ($import.Contains('[IO.FileShare]::Read') -and $import.Contains('ComputeHash')) 'pinned_open_image';$cases++
[ordered]@{status='PASS';cases=$cases;runtime_mutations=0;actual_import=$false;originals_touched=$false;services_verified=$false}|ConvertTo-Json -Compress
