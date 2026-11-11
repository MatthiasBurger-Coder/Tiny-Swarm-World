param([Parameter(Mandatory=$true)][string]$RepositoryRoot)
$ErrorActionPreference='Stop'
. (Join-Path $RepositoryRoot 'modules/tsw_windows_wsl/tools/qualification/wsl_acceptance_guest_switch.ps1')
function Assert($yes,[string]$reason){if(!$yes){throw $reason}}
function Copy-SwitchFixtureValue($v){
 if($null -eq $v -or $v -is [string] -or $v -is [ValueType]){return $v}
 if($v -is [Collections.IDictionary]){$r=@{};foreach($k in $v.Keys){$r[$k]=Copy-SwitchFixtureValue $v[$k]};return $r}
 if($v -is [Collections.IEnumerable]){return ,@($v|ForEach-Object{Copy-SwitchFixtureValue $_})}
 $r=@{};foreach($p in $v.PSObject.Properties){$r[$p.Name]=Copy-SwitchFixtureValue $p.Value};return $r
}
function Scenario {
 $pins=@{};foreach($p in Get-WslSwitchAssets){$pins[$p]='c'*64}
 return @{schema_version=2;handoff_policy='ALL_STOPPED_COLD_KERNEL_V1';run_id=('a'*32);host='PC';source_commit=('b'*40);pins=$pins;
 original_machine_sha256=('d'*64);original_proposal_sha256=('e'*64);registration_state_sha256=('f'*64);
 registration_scenario=@{run_id=('a'*32);host='PC';source_commit=('b'*40);image_sha256='48d56724b5c8e60f24893e83e73bbb58c60b3ca22fba3da977075420acd54104'};
 bridge_scenario=@{run_id=('a'*32);host='PC';source_commit=('b'*40);original_distro='Ubuntu';new_distro=('TSW-Q440-'+('a'*32));
 original_guid='{00000000-0000-0000-0000-000000000001}';new_guid='{00000000-0000-0000-0000-000000000002}';original_vhd_sha256=('1'*64);new_vhd_sha256=('2'*64)};
 linux_pins=@{'native_runtime_inventory.py'= ('3'*64);'native_lxd_snap_provenance.py'= ('4'*64)}}
}
function Ports([string]$fault=''){
 $c=@{state=$null;running=@('Ubuntu');events=[Collections.ArrayList]::new();fault=$fault;changed=0;observations=0;proofs=0;saveCount=0;boot=('a'*64);resets=0;bridgeStopped=$false}
 $p=@{}
 $p.Begin={param($phase) [void]$c.events.Add('begin:'+ $phase)}.GetNewClosure()
 $p.Clock={return [DateTimeOffset]::UtcNow}
 $p.Source={param($s) [void]$c.events.Add('source');if($c.fault -ceq 'source'){throw 'SOURCE_PRIVATE_CANARY'}}.GetNewClosure()
 $p.Observe={param($s) $c.observations++;if($c.fault -ceq 'registry'){throw 'REGISTRY'}
  $running=Copy-SwitchFixtureValue $c.running
  if($c.fault -ceq 'both'){$running=@('Ubuntu','TSW-Q440-'+$s.run_id)}
  if($c.fault -ceq 'third'){$running=@('foreign')}
  $id=if($c.fault -ceq 'race' -and $c.observations -gt 1){'7'*64}else{'6'*64}
  return @{running=$running;registration_count=$(if($c.fault -ceq 'third-registration'){3}else{2});receipt_matches=$true;registrations_sha256=$id;default='original-guid'}
 }.GetNewClosure()
 $p.Load={param($s) Copy-SwitchFixtureValue $c.state}.GetNewClosure()
 $p.Save={param($s,$v) $c.saveCount++;[void]$c.events.Add('save:'+ $v.stage+':'+$v.pending)
  if($c.fault -ceq 'intent-write' -and $v.pending){throw 'DURABILITY'}
  $c.state=Copy-SwitchFixtureValue $v;return Copy-SwitchFixtureValue $v
 }.GetNewClosure()
 $p.Lock={if($c.fault -ceq 'lock'){throw 'LOCKED'};[void]$c.events.Add('lock');return 'owned'}.GetNewClosure()
 $p.Unlock={param($lock) [void]$c.events.Add('unlock')}.GetNewClosure()
 $p.Registration={param($s) [void]$c.events.Add('registration');if($c.fault -ceq 'receipt'){throw 'BAD_RECEIPT'}}.GetNewClosure()
 $p.Original={param($kind,$s) [void]$c.events.Add('original:'+ $kind)
  if($kind -cin @('quiescent','restored')){$c.proofs++;if($c.fault -ceq 'original-proof'){throw 'SOURCE_PRIVATE_CANARY'};return @{status='FULL_ACTUAL_PROOF';proposal_sha256=$s.original_proposal_sha256;boot_id_sha256=$c.boot;machine_id_sha256=$s.original_machine_sha256}}
  Assert ($c.state.pending -ceq $(if($kind -ceq 'quiesce'){'quiesce-original'}else{'restore-original'})) 'original_without_intent'
  $c.changed++;if($c.fault -ceq 'original-timeout'){throw 'UNCERTAIN'}
  return @{scope='WSL_EXACT_GUEST_RUNTIME_WINDOW_ONLY';decision=$(if($kind -ceq 'quiesce'){'QUIESCED'}else{'RESTORED'});proposal_sha256=$s.original_proposal_sha256}
 }.GetNewClosure()
 $p.Bridge={param($phase,$s,$go) [void]$c.events.Add('bridge:'+ $phase)
  $action=@{StopOriginal='stop-original-bridge';Bind='bind-new';StageRestore='stage-original';ResumeOriginal='resume-original-bridge'}
  Assert ($c.state.pending -ceq $action[$phase]) 'bridge_without_intent';$c.changed++
  if($phase -cin @('StopOriginal','StageRestore')){$c.bridgeStopped=$true}else{$c.bridgeStopped=$false}
  if($c.fault -ceq 'bridge-timeout'){throw 'UNCERTAIN'}
  return @{status=@{StopOriginal='ORIGINAL_BRIDGE_STOPPED';Bind='NEW_BINDING_READY';StageRestore='ORIGINAL_PAYLOAD_STAGED_STOPPED';ResumeOriginal='ORIGINAL_BINDING_RESTORED'}[$phase]}
 }.GetNewClosure()
 $p.Terminate={param($who,$s) [void]$c.events.Add('terminate:'+ $who);Assert ($c.state.pending -ceq ('terminate-'+$who)) 'terminate_without_intent'
  Assert ($c.running.Count -eq 1 -and $c.running[0] -ceq $(if($who -ceq 'original'){'Ubuntu'}else{'TSW-Q440-'+$s.run_id})) 'terminate_wrong_guest'
  $c.changed++;$c.running=@();if($c.fault -ceq 'terminate-timeout'){throw 'UNCERTAIN'}
 }.GetNewClosure()
 $p.Start={param($who,$s) [void]$c.events.Add('start:'+ $who);Assert ($c.state.pending -ceq ('start-'+$who) -and $c.running.Count -eq 0) 'overlapping_start'
  $c.changed++;$c.running=@($(if($who -ceq 'original'){'Ubuntu'}else{'TSW-Q440-'+$s.run_id}));if($c.fault -ceq 'start-timeout'){throw 'UNCERTAIN'}
 }.GetNewClosure()
 $p.Network={param($s) [void]$c.events.Add('network');return @{status=$(if($c.fault -ceq 'network'){ 'KERNEL_NETWORK_RESIDUE'}elseif($c.fault -ceq 'module'){ 'KERNEL_NETWORK_UNKNOWN_PREREQUISITE_REQUIRED'}else{'KERNEL_NETWORK_ABSENT'})}}.GetNewClosure()
 $p.FixtureBoundary={param($s,[bool]$active=$false)
  [void]$c.events.Add('fixture-boundary')
  Assert ($active -eq !$c.bridgeStopped) 'fixture_bridge_state'
  if($c.fault -ceq 'fixture-boundary'){throw 'SWITCH_FIXTURE_BOUNDARY'}
  return @{fingerprint=('5'*64)}
 }.GetNewClosure()
 $p.FixtureProof={param($s)
  [void]$c.events.Add('fixture-proof')
  if($c.fault -cin @('fixture-residue','fixture-worker','fixture-product')){throw 'SWITCH_FIXTURE_PROOF'}
  return @{status='FIXTURE_RETURN_EMPTY';run_id=$s.run_id;source_commit=$s.source_commit;boot_id_sha256=$c.boot;
   machine_id_sha256=('8'*64);resources_sha256=$(if($c.fault -ceq 'fixture-drift'){'7'*64}else{'4'*64});daemon='EXACT_INCUS_EMPTY';workers=0;product_started=$false}
 }.GetNewClosure()
 $p.Prepared={param($s,$hash) [void]$c.events.Add('prepared');if($c.fault -ceq 'prepared'){throw 'BAD_PREPARATION'};return @{status='NEW_GUEST_PREPARED'}}.GetNewClosure()
 $p.Stopped={param($s,$hash) [void]$c.events.Add('stopped');if($c.fault -ceq 'stopped'){throw 'FOREIGN_OR_RUNNING_NODE'};if($c.fault -ceq 'unknown-upgrade-ledger'){throw 'UNKNOWN_CASE_LEDGER'};return @{status=$(if($c.fault -ceq 'old-stopped-variant'){'NEW_OWNED_NODES_STOPPED'}else{'OWNED_CASES_DISPOSED'});boot_id_sha256=$c.boot;machine_id_sha256=('8'*64)}}.GetNewClosure()
 $p.Boot={param($who,$s)
  $boot=if($c.fault -ceq 'boot-unchanged'){$c.state.resets[$who].previous_boot_sha256}else{$c.boot}
  return @{boot_id_sha256=$boot;machine_id_sha256=$(if($who -ceq 'original'){$s.original_machine_sha256}else{'8'*64})}
 }.GetNewClosure()
 $p.Reset={param($direction,$s,$state)
  [void]$c.events.Add('reset:'+ $direction)
  Assert ($c.running.Count -eq 0 -and $c.bridgeStopped -and $state.pending -ceq ('reset-to-'+$direction) -and
   $c.state.pending -ceq $state.pending -and
   ($state.resets[$direction].previous_boot_sha256 -ceq $c.boot -or
    ($direction -ceq 'original' -and $state.receipts.fixture_seal -ceq (Get-WslSwitchHash @($s.source_commit,$state.receipts.fixture_boundary,'NEW_NOT_STARTED')) -and
     $state.resets.original.previous_boot_sha256 -ceq $state.resets.new.previous_boot_sha256))) 'reset_without_proof_or_intent'
  $c.resets++;$c.changed++;$c.boot=$(if($direction -ceq 'new'){'b'*64}else{'c'*64})
  $state.resets[$direction].outcome='command-returned';$c.state=Copy-SwitchFixtureValue $state
  if($c.fault -ceq 'reset-timeout'){throw 'UNCERTAIN'}
  $state.resets[$direction].outcome='all-stopped';$c.state=Copy-SwitchFixtureValue $state
  return @{status='VM_RESET_ALL_STOPPED'}
 }.GetNewClosure()
 $p._ctx=$c;return $p
}
function Run($p,$s,[string]$phase,[string]$evidence=''){
 $p._ctx.observations=0
 $prepared=Invoke-WslAcceptanceGuestSwitch $s Prepare $null $null $evidence $p $phase
 Assert ($prepared.status -ceq 'PREPARED_READ_ONLY') 'prepare_missing'
 if($phase -cin @('SealFixtureReturn','ReturnFixture') -and $prepared.Contains('evidence_sha256')){$evidence=$prepared.evidence_sha256}
 $p._ctx.observations=0
 $g=@{schema_version=1;decision='GO';phase=$phase;scenario_sha256=(Get-WslSwitchHash $s);source_commit=$s.source_commit;
 proposal_sha256=$prepared.proposal_sha256;expires_at_utc=([DateTimeOffset]::UtcNow.AddSeconds((Get-WslSwitchSeconds $phase)+120).ToString('yyyy-MM-ddTHH:mm:ssZ'));evidence_sha256=$evidence}
 $b=@{guest_quiesce_sha256=$(if($phase -ceq 'ReturnOriginal'){$evidence}else{if($p._ctx.state){$p._ctx.state.receipts.quiesce}else{''}})}
 return Invoke-WslAcceptanceGuestSwitch $s $phase $g $b $evidence $p
}
$cases=0;$s=Scenario;$p=Ports
$r=Invoke-WslAcceptanceGuestSwitch $s Prepare $null $null '' $p
Assert ($r.status -ceq 'PREPARED_READ_ONLY' -and $null -eq $p._ctx.state -and $p._ctx.changed -eq 0 -and $p._ctx.saveCount -eq 0) 'prepare_effect';$cases++
foreach($phase in @('QuiesceOriginal','EnterNew','VerifyPrepared','BindNew','ReturnOriginal','RestoreOriginal')){
 $evidence=if($phase -cin @('VerifyPrepared','ReturnOriginal')){'9'*64}else{''}
 $r=Run $p $s $phase $evidence
 $expected=@{QuiesceOriginal='ORIGINAL_QUIESCED';EnterNew='NEW_GUEST_SAFE_FOR_PREPARATION';VerifyPrepared='NEW_GUEST_PREPARED';BindNew='NEW_BINDING_READY';ReturnOriginal='ORIGINAL_READY_FOR_BRIDGE_RESUME';RestoreOriginal='ORIGINAL_RESTORED_NEW_RETAINED_STOPPED'}
 Assert ($r.status -ceq $expected[$phase] -and !$r.application_ready) ('complete_'+$phase+'_'+$r.error);$cases++
}
Assert ($p._ctx.resets -eq 2 -and $p._ctx.state.resets.new.outcome -ceq 'changed-boot' -and $p._ctx.state.resets.original.outcome -ceq 'changed-boot') 'reset_not_once_each';$cases++
Assert ($p._ctx.state.stage -ceq 'restored' -and $p._ctx.running.Count -eq 1 -and $p._ctx.running[0] -ceq 'Ubuntu') 'final_running'
$events=@($p._ctx.events)
Assert ([Array]::IndexOf($events,'original:quiescent') -lt [Array]::IndexOf($events,'bridge:StopOriginal')) 'stale_quiesce'
Assert ([Array]::IndexOf($events,'bridge:StopOriginal') -lt [Array]::IndexOf($events,'terminate:original')) 'terminate_before_bridge_stop'
Assert ([Array]::IndexOf($events,'terminate:original') -lt [Array]::IndexOf($events,'start:new')) 'overlap'
Assert ([Array]::IndexOf($events,'bridge:StageRestore') -lt [Array]::IndexOf($events,'terminate:new')) 'return_bridge_order'
Assert ([Array]::IndexOf($events,'bridge:ResumeOriginal') -lt [Array]::IndexOf($events,'original:restore')) 'restore_before_heartbeat';$cases++
foreach($fault in @('source','registry','third-registration')){
 $p=Ports $fault;$r=Invoke-WslAcceptanceGuestSwitch $s Prepare $null $null '' $p
 Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.changed -eq 0 -and $p._ctx.saveCount -eq 0) ('denial_'+$fault)
 Assert (($r|ConvertTo-Json -Compress) -notmatch 'PRIVATE_CANARY') 'raw_error';$cases++
}
foreach($fault in @('both','third','receipt','lock','intent-write','race')){
 $p=Ports $fault;$r=Run $p $s QuiesceOriginal
 Assert ($r.status -cin @('BLOCKED','RECOVERY_REQUIRED') -and $p._ctx.changed -eq 0) ('pre_effect_'+$fault);$cases++
}
$p=Ports;$null=Run $p $s QuiesceOriginal;$p._ctx.fault='original-proof'
$r=Run $p $s EnterNew;Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.changed -eq 1 -and $p._ctx.running[0] -ceq 'Ubuntu') 'stale_original_proof';$cases++
foreach($fault in @('original-timeout','bridge-timeout','terminate-timeout','start-timeout','reset-timeout','boot-unchanged')){
 $p=Ports
 if($fault -ceq 'original-timeout'){$p._ctx.fault=$fault;$r=Run $p $s QuiesceOriginal;$phase='QuiesceOriginal'}else{
  $null=Run $p $s QuiesceOriginal;$p._ctx.fault=$fault;$r=Run $p $s EnterNew;$phase='EnterNew'}
 Assert ($r.status -ceq 'RECOVERY_REQUIRED' -and $p._ctx.state.pending) ('uncertain_'+$fault)
 $before=$p._ctx.changed;$p._ctx.fault='';$r=Run $p $s $phase
 Assert ($r.status -ceq 'RECOVERY_REQUIRED' -and $p._ctx.changed -eq $before) ('replayed_'+$fault)
 $r=Invoke-WslAcceptanceGuestSwitch $s Reconcile $null $null '' $p
 Assert ($r.status -ceq 'RECOVERY_REQUIRED' -and $p._ctx.changed -eq $before) 'reconcile_effect';$cases++
}
foreach($fault in @('network','module')){
 $p=Ports;$null=Run $p $s QuiesceOriginal;$p._ctx.fault=$fault;$r=Run $p $s EnterNew
 Assert ($p._ctx.state.stage -ceq 'new_running' -and $p._ctx.running[0] -ceq ('TSW-Q440-'+$s.run_id) -and !$r.application_ready) 'network_unknown_authority'
 if($fault -ceq 'module'){Assert ($r.status -ceq 'NEW_GUEST_NETWORK_PREREQUISITE_REQUIRED') 'module_not_explicit'}
 $changed=$p._ctx.changed;$p._ctx.fault='';$r=Run $p $s EnterNew
 Assert ($r.status -ceq 'NEW_GUEST_SAFE_FOR_PREPARATION' -and $p._ctx.changed -eq $changed) 'network_resume_replays_start';$cases++
}
$p=Ports;$null=Run $p $s QuiesceOriginal;$null=Run $p $s EnterNew;$p._ctx.fault='prepared'
$r=Run $p $s VerifyPrepared ('9'*64);Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.state.stage -ceq 'safe') 'missing_preparation';$cases++
$p._ctx.fault='';$null=Run $p $s VerifyPrepared ('9'*64);$null=Run $p $s BindNew;$p._ctx.fault='stopped';$changed=$p._ctx.changed
$r=Run $p $s ReturnOriginal ('9'*64);Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.changed -eq $changed -and $p._ctx.state.stage -ceq 'bound') 'foreign_stop_adopt';$cases++
foreach($key in @('run_id','source_commit','original_machine_sha256','original_proposal_sha256','registration_state_sha256')){
 $bad=Copy-SwitchFixtureValue $s;$bad[$key]='foreign';$p=Ports;$r=Invoke-WslAcceptanceGuestSwitch $bad Prepare $null $null '' $p
 Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.events.Count -eq 0) ('schema_'+$key);$cases++
}
$p=Ports;$null=Run $p $s QuiesceOriginal;$p._ctx.state.scenario_sha256='0'*64
$r=Invoke-WslAcceptanceGuestSwitch $s Reconcile $null $null '' $p;Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.changed -eq 1) 'foreign_bookmark';$cases++
foreach($fault in @('expired','too-long','phase','source','scenario','proposal','evidence')){
 $p=Ports;$r=Invoke-WslAcceptanceGuestSwitch $s Prepare $null $null '' $p
 $g=@{schema_version=1;decision='GO';phase='QuiesceOriginal';scenario_sha256=(Get-WslSwitchHash $s);source_commit=$s.source_commit;
 proposal_sha256=$r.proposal_sha256;expires_at_utc=([DateTimeOffset]::UtcNow.AddSeconds(1620).ToString('yyyy-MM-ddTHH:mm:ssZ'));evidence_sha256=''}
 switch($fault){
  'expired'{$g.expires_at_utc=[DateTimeOffset]::UtcNow.AddSeconds(-1).ToString('yyyy-MM-ddTHH:mm:ssZ')}
  'too-long'{$g.expires_at_utc=[DateTimeOffset]::UtcNow.AddSeconds(10000).ToString('yyyy-MM-ddTHH:mm:ssZ')}
  'phase'{$g.phase='EnterNew'}
  'source'{$g.source_commit='0'*40}
  'scenario'{$g.scenario_sha256='0'*64}
  'proposal'{$g.proposal_sha256='0'*64}
  'evidence'{$g.evidence_sha256='0'*64}
 }
 $p._ctx.observations=0;$r=Invoke-WslAcceptanceGuestSwitch $s QuiesceOriginal $g $null '' $p
 Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.changed -eq 0 -and $p._ctx.saveCount -eq 0) ('go_'+$fault);$cases++
}
$v=@{a=1;b='canonical'};$bytes=Get-WslSwitchBytes $v;$wire=[Convert]::ToBase64String($bytes)
$null=Read-WslSwitchWire $wire (Get-WslSwitchRawHash $bytes);$cases++
foreach($raw in @('{"b":"canonical","a":1}','{"a":1,"a":1,"b":"canonical"}')){
 $bytes=[Text.Encoding]::UTF8.GetBytes($raw);$denied=$false
 try{$null=Read-WslSwitchWire ([Convert]::ToBase64String($bytes)) (Get-WslSwitchRawHash $bytes)}catch{$denied=$true}
 Assert $denied 'wire_alias_or_duplicate';$cases++
}
foreach($ledgerFault in @('old-stopped-variant','unknown-upgrade-ledger')){
$p=Ports;$null=Run $p $s QuiesceOriginal;$null=Run $p $s EnterNew;$null=Run $p $s VerifyPrepared ('9'*64);$null=Run $p $s BindNew
$p._ctx.fault=$ledgerFault;$changed=$p._ctx.changed;$resets=$p._ctx.resets
$r=Run $p $s ReturnOriginal ('9'*64)
Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.state.stage -ceq 'bound' -and !$p._ctx.state.pending -and
 $p._ctx.changed -eq $changed -and $p._ctx.resets -eq $resets -and $p._ctx.running[0] -ceq ('TSW-Q440-'+$s.run_id)) ('invalid_case_ledger_admitted_'+$ledgerFault);$cases++
}
# The same pure boundary consumed by production Reset is exercised without an OS.
$p=Ports;$null=Run $p $s QuiesceOriginal;$base=Copy-SwitchFixtureValue $p._ctx.state
$base.pending='reset-to-new';$base.stage='original_stopped'
$base.resets.new=@{action='reset-to-new';previous_boot_sha256=('a'*64);next_boot_sha256='';machine_sha256=$s.original_machine_sha256;outcome='intent'}
$obs=@{running=@();registration_count=2;registrations_sha256=('6'*64);receipt_matches=$true;default='original-guid'}
$null=Assert-WslSwitchResetBoundary $s $base $obs new Stopped @{clients=0;workers=0};$cases++
foreach($fault in @('running','third-registration','registry','bridge','client','worker','pending','boot','action')){
 $v=Copy-SwitchFixtureValue $base;$o=Copy-SwitchFixtureValue $obs;$bridge='Stopped';$children=@{clients=0;workers=0}
 switch($fault){
  'running'{$o.running=@('Ubuntu')}
  'third-registration'{$o.registration_count=3}
  'registry'{$o.registrations_sha256='drift'}
  'bridge'{$bridge='Running'}
  'client'{$children.clients=1}
  'worker'{$children.workers=1}
  'pending'{$v.pending=''}
  'boot'{$v.resets.new.previous_boot_sha256='invalid'}
  'action'{$v.resets.new.action='foreign'}
 }
 $denied=$false;try{$null=Assert-WslSwitchResetBoundary $s $v $o new $bridge $children}catch{$denied=$true}
 Assert $denied ('reset_boundary_'+$fault);$cases++
}
# Fixture return is independent from preparation, product cases and admission.
foreach($stage in @('new_running','safe','prepared')){
 $p=Ports;$null=Run $p $s QuiesceOriginal;$null=Run $p $s EnterNew
 $p._ctx.state.stage=$stage
 $before=$p._ctx.changed;$r=Run $p $s SealFixtureReturn
 Assert ($r.status -ceq 'FIXTURE_RETURN_SEALED' -and $p._ctx.changed -eq $before) ('seal_'+$stage)
 $r=Run $p $s ReturnFixture
 Assert ($r.status -ceq 'ORIGINAL_READY_FOR_BRIDGE_RESUME' -and $p._ctx.state.stage -ceq 'original_running') ('fixture_return_'+$stage+'_'+$r.error)
 Assert (@($p._ctx.events | Where-Object{$_ -cin @('stopped','prepared','bridge:Bind','bridge:StageRestore')}).Count -eq 0) 'fixture_product_dependency'
 $r=Run $p $s RestoreOriginal
 Assert ($r.status -ceq 'ORIGINAL_RESTORED_NEW_RETAINED_STOPPED' -and !$r.application_ready) 'fixture_restore';$cases++
}
foreach($fault in @('fixture-residue','fixture-worker','fixture-product','fixture-drift','fixture-boundary')){
 $p=Ports;$null=Run $p $s QuiesceOriginal;$null=Run $p $s EnterNew;$null=Run $p $s SealFixtureReturn
 $before=$p._ctx.changed;$bookmark=Get-WslSwitchHash $p._ctx.state;$p._ctx.fault=$fault
 if($fault -cin @('fixture-residue','fixture-worker','fixture-product','fixture-boundary')){
  $r=Invoke-WslAcceptanceGuestSwitch $s Prepare $null $null '' $p ReturnFixture
 }else{$r=Run $p $s ReturnFixture}
 Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.changed -eq $before -and (Get-WslSwitchHash $p._ctx.state) -ceq $bookmark) ('fixture_refusal_'+$fault);$cases++
}
$p=Ports;$null=Run $p $s QuiesceOriginal;$r=Run $p $s ReturnFixture
Assert ($r.status -ceq 'ORIGINAL_RESTORED_NEW_RETAINED_STOPPED' -and $p._ctx.resets -eq 0) 'fixture_early_original';$cases++
# Early stopped states return via their own cold original-direction reset.
foreach($stage in @('original_bridge_stopped','original_stopped','reset_for_new')){
 $p=Ports;$null=Run $p $s QuiesceOriginal;$null=Run $p $s EnterNew
 $p._ctx.state.stage=$stage;$p._ctx.state.receipts.Remove('network')
 $p._ctx.state.resets.new=@{action='reset-to-new';previous_boot_sha256=('a'*64);next_boot_sha256='';machine_sha256=$s.original_machine_sha256;outcome='captured'}
 if($stage -ceq 'original_bridge_stopped'){$p._ctx.running=@('Ubuntu');$p._ctx.boot='a'*64}else{
  $p._ctx.running=@();$p._ctx.boot='a'*64
  if($stage -ceq 'reset_for_new'){$p._ctx.state.resets.new.outcome='all-stopped';$p._ctx.boot='b'*64}
 }
 $r=Run $p $s ReturnFixture
 Assert ($r.status -ceq 'ORIGINAL_READY_FOR_BRIDGE_RESUME') ('fixture_early_'+$stage+'_'+$r.error)
 $r=Run $p $s RestoreOriginal;Assert ($r.status -ceq 'ORIGINAL_RESTORED_NEW_RETAINED_STOPPED') ('fixture_early_restored_'+$stage);$cases++
}
foreach($fault in @('original-timeout','bridge-timeout','terminate-timeout','reset-timeout','start-timeout')){
 $p=Ports
 if($fault -ceq 'original-timeout'){$p._ctx.fault=$fault;$null=Run $p $s QuiesceOriginal}else{
  $null=Run $p $s QuiesceOriginal;$p._ctx.fault=$fault;$null=Run $p $s EnterNew}
 $p._ctx.fault=''
 if($fault -ceq 'start-timeout'){$r=Run $p $s SealFixtureReturn;Assert ($r.status -ceq 'FIXTURE_RETURN_SEALED') 'fixture_pending_start_seal'}
 $r=Run $p $s ReturnFixture
 Assert ($r.status -cin @('ORIGINAL_READY_FOR_BRIDGE_RESUME','ORIGINAL_RESTORED_NEW_RETAINED_STOPPED')) ('fixture_pending_'+$fault+'_'+$r.error);$cases++
}
foreach($pending in @('bind-new','stage-original','resume-original-bridge','restore-original')){
 $p=Ports;$null=Run $p $s QuiesceOriginal;$null=Run $p $s EnterNew;$null=Run $p $s SealFixtureReturn
 $p._ctx.state.pending=$pending;$before=$p._ctx.changed;$bookmark=Get-WslSwitchHash $p._ctx.state
 $r=Run $p $s ReturnFixture
 Assert ($r.status -ceq 'RECOVERY_REQUIRED' -and $p._ctx.changed -eq $before -and (Get-WslSwitchHash $p._ctx.state) -ceq $bookmark) ('fixture_unresolved_'+$pending);$cases++
}
foreach($fault in @('terminate-timeout','start-timeout','reset-timeout')){
 $p=Ports;$null=Run $p $s QuiesceOriginal;$null=Run $p $s EnterNew;$null=Run $p $s SealFixtureReturn
 $p._ctx.fault=$fault;$r=Run $p $s ReturnFixture
 Assert ($r.status -ceq 'RECOVERY_REQUIRED' -and $p._ctx.state.receipts.Contains('fixture_seal')) ('fixture_return_uncertain_'+$fault)
 $p._ctx.fault=''
 if($fault -ceq 'reset-timeout'){
  $before=$p._ctx.changed;$bookmark=Get-WslSwitchHash $p._ctx.state;$r=Run $p $s ReturnFixture
  Assert ($r.status -ceq 'RECOVERY_REQUIRED' -and $p._ctx.changed -eq $before -and (Get-WslSwitchHash $p._ctx.state) -ceq $bookmark) 'fixture_reset_unknown_retained'
 }else{
  $r=Run $p $s ReturnFixture;Assert ($r.status -ceq 'ORIGINAL_READY_FOR_BRIDGE_RESUME') ('fixture_return_reconciled_'+$fault+'_'+$r.error)
 };$cases++
}
$p=Ports;$null=Run $p $s QuiesceOriginal;$null=Run $p $s EnterNew;$null=Run $p $s SealFixtureReturn
$p._ctx.state.stage='fixture_new_stopped';$p._ctx.running=@();$before=$p._ctx.changed
$r=Run $p $s ReturnOriginal ('9'*64)
Assert ($r.status -ceq 'BLOCKED' -and $p._ctx.changed -eq $before) 'fixture_stage_not_product_return';$cases++
# Execute the actual Save body on new private fixture files. The second save
# reaches File.Replace, including Windows PowerShell's explicit null binding.
$tokens=$null;$parseErrors=$null
$tree=[Management.Automation.Language.Parser]::ParseFile((Join-Path $RepositoryRoot 'modules/tsw_windows_wsl/tools/qualification/wsl_acceptance_guest_switch.ps1'),[ref]$tokens,[ref]$parseErrors)
Assert ($parseErrors.Count -eq 0) 'source parses for actual Save'
$saveDefinitions=@($tree.FindAll({param($a) $a -is [Management.Automation.Language.FunctionDefinitionAst] -and $a.Name -ceq 'Save'},$true))
Assert ($saveDefinitions.Count -eq 1) 'unique actual Save'
$saveRoot=Join-Path ([IO.Path]::GetTempPath()) ('tsw-switch-save-'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($saveRoot)
try{
 $saveModule=New-Module -ArgumentList $saveRoot,$saveDefinitions[0].Extent.Text -ScriptBlock {
  param($root,$body)
  $script:parent=$root;$script:directory=$root;$script:bookmark=Join-Path $root 'guest-switch.json';$script:loaded=$null
  function Assert-WslSwitchBookmark($state,$spec) {}
  function CheckPath($p) {if(!(Test-Path -LiteralPath $p)){throw 'SAVE_PATH_MISSING'}}
  function Assert-WslSwitch($value,$code) {if(!$value){throw $code}}
  function Get-WslSwitchBytes($value) {return ,([Text.Encoding]::UTF8.GetBytes(($value|ConvertTo-Json -Compress)))}
  function Get-WslSwitchRawHash($raw) {$h=[Security.Cryptography.SHA256]::Create();try{return [Convert]::ToBase64String($h.ComputeHash($raw))}finally{$h.Dispose()}}
  function ReadJson($path,$limit) {return @{raw=[IO.File]::ReadAllBytes($path)}}
  $script:prep=New-Module -ScriptBlock {function Set-PreparationPrivateAcl($path) {if(!(Test-Path -LiteralPath $path)){throw 'SAVE_TEMP_ABSENT'}}}
  . ([scriptblock]::Create($body))
  $null=Save @{} @{stage='intent'}
  $null=Save @{} @{stage='pending'}
  $actual=[IO.File]::ReadAllText($bookmark)|ConvertFrom-Json
  if($actual.stage -cne 'pending' -or @(Get-ChildItem $root -Filter '*.tmp').Count -ne 0){throw 'ACTUAL_SAVE_REPLACE_FAILED'}
  [IO.File]::WriteAllText($bookmark,'{"stage":"foreign"}')
  $blocked=$false;try{$null=Save @{} @{stage='forbidden'}}catch{$blocked=$_.Exception.Message -ceq 'SWITCH_BOOKMARK_CAS'}
  if(!$blocked -or ([IO.File]::ReadAllText($bookmark)|ConvertFrom-Json).stage -cne 'foreign'){throw 'ACTUAL_SAVE_CAS_BYPASSED'}
  Export-ModuleMember -Function @() -Alias @()
 }
 Remove-Module $saveModule -Force;$cases++
}finally{Remove-Item -LiteralPath $saveRoot -Recurse -Force}
@{status='PASS';cases=$cases;actual_guest_effects=0;actual_preparation=$false;originals_touched=$false;application_ready=$false}|ConvertTo-Json -Compress
