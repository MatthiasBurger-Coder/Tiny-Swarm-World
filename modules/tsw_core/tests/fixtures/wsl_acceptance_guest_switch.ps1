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
   ($state.resets[$direction].previous_boot_sha256 -ceq $c.boot -or ($c.ContainsKey('phase') -and $c.phase -ceq 'ReconcileEffects' -and $state.receipts.Contains('reconciliation_parent')) -or
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
 if($phase -cin @('SealFixtureReturn','ReturnFixture','ReconcileEffects') -and $prepared.Contains('evidence_sha256')){$evidence=$prepared.evidence_sha256}
 $p._ctx.observations=0
 $g=@{schema_version=1;decision='GO';phase=$phase;scenario_sha256=(Get-WslSwitchHash $s);source_commit=$s.source_commit;
 proposal_sha256=$prepared.proposal_sha256;expires_at_utc=([DateTimeOffset]::UtcNow.AddSeconds((Get-WslSwitchSeconds $phase)+120).ToString('yyyy-MM-ddTHH:mm:ssZ'));evidence_sha256=$evidence}
 if($s.schema_version -ceq 3){$g.original_context_sha256=Get-WslSwitchHash (Get-WslSwitchOriginalContext $s);$g.original_proposal_sha256=$s.original_proposal_sha256;$g.original_lock_witness=$prepared.original_lock_witness;$g.legacy_go=$null;$g.legacy_go_sha256='0'*64;if($phase -ceq 'QuiesceOriginal'){$g.legacy_go=@{fresh=$true};$g.legacy_go_sha256=Get-WslSwitchHash $g.legacy_go}}
 $b=@{phase='Recover';guest_quiesce_sha256=$(if($phase -ceq 'ReturnOriginal'){$evidence}else{if($p._ctx.state){$p._ctx.state.receipts.quiesce}else{''}})}
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
# Schema3 exercises the actual coordinator with injected host effects only.
function WindowScenario {
 $v=Scenario;$v.schema_version=3;$v.bridge_scenario.schema_version=2;$v.bridge_scenario.window='fixture'
 $v.bridge_scenario.parent_switch_sha256='0'*64;$v.bridge_scenario.parent_bridge_sha256='0'*64
 $v.bridge_scenario.registration_state_sha256=$v.registration_state_sha256
 $v.window=@{kind='fixture';adapter_sha256=$v.pins.'modules/tsw_core/tools/linux/qualification/wsl_original_runtime_window.py';backup_sha256=('6'*64);legacy_lock_inode=42;
  parent_switch_sha256=('0'*64);parent_bridge_sha256=('0'*64);parent_switch=$null;parent_bridge=$null;
  source_view=@{source_commit=$v.source_commit;registered_source_commit=$v.registration_scenario.source_commit}}
 return $v
}
function WindowPorts {
 $v=Ports;$c=$v._ctx;$c.phase='';$c.metadata=$false;$c.parents=$null
 $baseOriginal=$v.Original;$baseBridge=$v.Bridge
 $v.Begin={param($phase) $c.phase=$phase;[void]$c.events.Add('begin:'+ $phase)}.GetNewClosure()
 $v.StageOriginal={param($s,$g) Assert ($g.phase -ceq 'StageOriginal') 'stage_approval';[void]$c.events.Add('staged');return @{status='ORIGINAL_SOURCE_STAGED'}}.GetNewClosure()
 $v.OriginalWitness={param($s) return @{device=4;inode=42;machine_sha256=$s.original_machine_sha256;boot_sha256=$c.boot}}.GetNewClosure()
 $v.Parent={param($s) Assert ($null -ne $c.parents) 'missing_fixture_parent';return Copy-SwitchFixtureValue $c.parents}.GetNewClosure()
 $v.BridgeStopped={param($s) Assert $c.bridgeStopped 'bridge_not_stopped';return @{status='Stopped'}}.GetNewClosure()
 $v.BridgeOutcome={param($s) if($c.fault -ceq 'bound-applied'){return @{status='BOUND';proof=@{actual='bound'}}};return @{status='RECOVERY_REQUIRED'}}.GetNewClosure()
 $v.OriginalBridge={param($s) Assert (!$c.bridgeStopped -and $c.running.Count -eq 1 -and $c.running[0] -ceq 'Ubuntu') 'bridge_not_original';[void]$c.events.Add('actual-original-bridge')}.GetNewClosure()
 $v.Original={param($kind,$s,$g=$null)
  if($kind -ceq 'inspect'){return @{status='ORIGINAL_INSPECTED';proposal_sha256=$s.original_proposal_sha256}}
  if($kind -cin @('prepare','recover-prepare')){
   Assert ($c.state.pending -ceq 'prepare-original' -and $g.original_context_sha256 -ceq (Get-WslSwitchHash (Get-WslSwitchOriginalContext $s))) 'prepare_without_context_go'
   $c.metadata=$true;if($c.fault -ceq 'prepare-timeout'){throw 'UNCERTAIN'};return @{status='ORIGINAL_PREPARED';proposal_sha256=$s.original_proposal_sha256}
  }
  if($kind -ceq 'prepared'){Assert $c.metadata 'metadata_missing';return @{status='ORIGINAL_PREPARED';proposal_sha256=$s.original_proposal_sha256}}
  if($kind -ceq 'restore' -and $c.phase -ceq 'ReconcileEffects'){
   Assert ($g.phase -ceq 'ReconcileEffects') 'recovery_without_own_go';$c.changed++;return @{decision='RESTORED';proposal_sha256=$s.original_proposal_sha256}
  }
  return & $baseOriginal $kind $s
 }.GetNewClosure()
 $v.Bridge={param($phase,$s,$g)
  if($phase -ceq 'Recover'){
   Assert ($g.phase -ceq 'Recover' -and $c.state.pending) 'bridge_recovery_without_own_go'
   $c.changed++;$c.bridgeStopped=$true;return @{status='RECOVERED_STOPPED'}
  }
  return & $baseBridge $phase $s $g
 }.GetNewClosure()
 return $v
}
$ws=WindowScenario;$wp=WindowPorts
$preview=Invoke-WslAcceptanceGuestSwitch $ws Prepare $null $null '' $wp PrepareOriginal
Assert ($preview.status -ceq 'PREPARED_READ_ONLY' -and $null -eq $wp._ctx.state -and $wp._ctx.saveCount -eq 0 -and $wp._ctx.changed -eq 0) 'window_preview_write';$cases++
$r=Run $wp $ws StageOriginal;Assert ($r.status -ceq 'ORIGINAL_SOURCE_STAGED' -and $null -eq $wp._ctx.state) ('window_stage_'+$r.error);$cases++
$r=Invoke-WslAcceptanceGuestSwitch $ws InspectOriginal $null $null '' $wp
Assert ($r.status -ceq 'ORIGINAL_INSPECTED_READ_ONLY' -and $null -eq $wp._ctx.state) 'inspect_effect';$cases++
$r=Run $wp $ws PrepareOriginal;Assert ($r.status -ceq 'ORIGINAL_PREPARED' -and $wp._ctx.state.stage -ceq 'original_prepared') ('window_prepare_'+$r.error);$cases++
foreach($phase in @('QuiesceOriginal','EnterNew','SealFixtureReturn','ReturnFixture','RestoreOriginal')){
 $r=Run $wp $ws $phase;Assert ($r.status -cnotin @('BLOCKED','RECOVERY_REQUIRED')) ('fixture_window_'+$phase+'_'+$r.error)
}
$fixture=Copy-SwitchFixtureValue $wp._ctx.state
Assert ($fixture.window -ceq 'fixture' -and $fixture.stage -ceq 'restored' -and !$fixture.pending) 'fixture_not_restored'
$parents=@{switch=$fixture;bridge=@{fixture='restored';source_commit=$ws.source_commit}}
$product=WindowScenario;$product.window.kind='product';$product.window.parent_switch=$parents.switch;$product.window.parent_bridge=$parents.bridge
$product.window.parent_switch_sha256=Get-WslSwitchHash $parents.switch;$product.window.parent_bridge_sha256=Get-WslSwitchHash $parents.bridge
$product.bridge_scenario.window='product';$product.bridge_scenario.parent_switch_sha256=$product.window.parent_switch_sha256;$product.bridge_scenario.parent_bridge_sha256=$product.window.parent_bridge_sha256
$next=WindowPorts;$next._ctx.parents=$parents
$r=Run $next $product BeginProductWindow
Assert ($r.status -ceq 'PRODUCT_WINDOW_OPENED' -and $next._ctx.state.window -ceq 'product' -and $next._ctx.changed -eq 0) ('product_begin_'+$r.error)
$r=Run $next $product PrepareOriginal
Assert ($r.status -ceq 'ORIGINAL_PREPARED' -and (Get-WslSwitchHash $fixture) -ceq (Get-WslSwitchHash $parents.switch) -and
 $product.bridge_scenario.original_guid -ceq $ws.bridge_scenario.original_guid -and $product.bridge_scenario.new_guid -ceq $ws.bridge_scenario.new_guid) 'product_reimport_or_parent_changed';$cases++
$bad=WindowPorts;$r=Run $bad $product BeginProductWindow
Assert ($r.status -ceq 'BLOCKED' -and $bad._ctx.saveCount -eq 0 -and $bad._ctx.changed -eq 0) 'missing_parent_created_window';$cases++
# Every irreversible uncertainty gets a fresh explicit current-state approval.
foreach($action in @('prepare-original','quiesce-original','stop-original-bridge','reset-to-new','start-new','terminate-original','bind-new','stage-original','terminate-new','reset-to-original','start-original','resume-original-bridge','restore-original')){
 $rp=WindowPorts;$v=New-WslSwitchBookmark $ws;$v.receipts.registration='6'*64;$v.pending=$action;$v.stage='original_prepared'
 $rp._ctx.metadata=$true
 switch($action){
  'prepare-original'{$v.stage='registered'}
  'quiesce-original'{}
  'stop-original-bridge'{$v.stage='quiesced'}
  'terminate-original'{$v.stage='original_bridge_stopped';$rp._ctx.running=@();$rp._ctx.bridgeStopped=$true;$v.receipts.fixture_boundary='5'*64;$v.resets.new=@{action='reset-to-new';previous_boot_sha256=('a'*64);next_boot_sha256='';machine_sha256=$ws.original_machine_sha256;outcome='captured'}}
  'reset-to-new'{$v.stage='original_stopped';$rp._ctx.running=@();$rp._ctx.bridgeStopped=$true;$v.receipts.fixture_boundary='5'*64;$v.resets.new=@{action='reset-to-new';previous_boot_sha256=('a'*64);next_boot_sha256='';machine_sha256=$ws.original_machine_sha256;outcome='command-returned'}}
  'start-new'{$v.stage='reset_for_new';$rp._ctx.running=@();$rp._ctx.bridgeStopped=$true;$v.resets.new=@{action='reset-to-new';previous_boot_sha256=('a'*64);next_boot_sha256='';machine_sha256=$ws.original_machine_sha256;outcome='all-stopped'}}
  'bind-new'{$rp._ctx.boot='b'*64;$v.stage='prepared';$rp._ctx.running=@('TSW-Q440-'+$ws.run_id);$rp._ctx.bridgeStopped=$false;$v.receipts.fixture_boundary='5'*64}
  'stage-original'{$v.stage='bound';$rp._ctx.running=@('TSW-Q440-'+$ws.run_id);$v.receipts.stopped='9'*64}
  'terminate-new'{$v.stage='original_payload_staged';$rp._ctx.running=@();$rp._ctx.bridgeStopped=$true;$v.receipts.stopped='9'*64;$v.resets.original=@{action='reset-to-original';previous_boot_sha256=('a'*64);next_boot_sha256='';machine_sha256=('8'*64);outcome='captured'}}
  'reset-to-original'{$v.stage='new_stopped';$rp._ctx.running=@();$rp._ctx.bridgeStopped=$true;$v.resets.original=@{action='reset-to-original';previous_boot_sha256=('a'*64);next_boot_sha256='';machine_sha256=('8'*64);outcome='command-returned'}}
  'start-original'{$v.stage='reset_for_original';$rp._ctx.bridgeStopped=$true;$rp._ctx.boot='c'*64;$v.resets.original=@{action='reset-to-original';previous_boot_sha256=('a'*64);next_boot_sha256='';machine_sha256=$ws.original_machine_sha256;outcome='all-stopped'}}
  'resume-original-bridge'{$v.stage='original_running';$v.receipts.fixture_original_boot=$rp._ctx.boot}
  'restore-original'{$v.stage='original_bridge_ready'}
 }
 $rp._ctx.state=Copy-SwitchFixtureValue $v;$old=Get-WslSwitchHash $v
 $r=Run $rp $ws ReconcileEffects
 Assert ($r.status -ceq 'PENDING_EFFECT_RECONCILED' -and !$rp._ctx.state.pending -and $rp._ctx.state.receipts.reconciliation_parent -ceq $old) ('pending_'+$action+'_'+$r.error)
 $cases++
}

# Failed parent/runtime proofs must never retain a read-only success status.
foreach($fault in @('missing-parent','original-proof')){
 $rp=WindowPorts;$rp._ctx.state=Copy-SwitchFixtureValue $fixture
 if($fault -ceq 'original-proof'){$rp._ctx.parents=$parents;$rp._ctx.fault='original-proof'}
 $count=$rp._ctx.changed;$saves=$rp._ctx.saveCount
 $r=Invoke-WslAcceptanceGuestSwitch $ws Reconcile $null $null '' $rp
 Assert ($r.status -ceq 'BLOCKED' -and $rp._ctx.changed -eq $count -and $rp._ctx.saveCount -eq $saves) ('false_reconcile_success_'+$fault);$cases++
}
# A failed runtime postcondition after approved restore retains the durable
# original uncertainty and its prior proofs; it cannot become reconciled.
$rp=WindowPorts;$v=New-WslSwitchBookmark $ws;$v.receipts.registration='6'*64
$v.receipts.quiesce='9'*64;$v.stage='original_prepared';$v.pending='quiesce-original'
$rp._ctx.state=Copy-SwitchFixtureValue $v;$rp._ctx.fault='original-proof'
$before=Get-WslSwitchHash $rp._ctx.state;$saves=$rp._ctx.saveCount
$r=Run $rp $ws ReconcileEffects
Assert ($r.status -ceq 'RECOVERY_REQUIRED' -and $r.recovery_required -and
 $rp._ctx.state.pending -ceq 'quiesce-original' -and $rp._ctx.state.receipts.quiesce -ceq ('9'*64) -and
 (Get-WslSwitchHash $rp._ctx.state) -ceq $before -and $rp._ctx.saveCount -eq $saves -and $rp._ctx.changed -eq 1) 'failed_recovery_postcondition_cleared_intent';$cases++
# Applied Bind with lost acknowledgement reconciles solely through fresh actual
# owner proof, without stopping/recovering the bridge or inventing fixture proof.
$rp=WindowPorts;$v=New-WslSwitchBookmark $ws;$v.receipts.registration='6'*64;$v.stage='prepared';$v.pending='bind-new'
$rp._ctx.state=$v;$rp._ctx.running=@('TSW-Q440-'+$ws.run_id);$rp._ctx.fault='bound-applied'
$r=Run $rp $ws ReconcileEffects
Assert ($r.status -ceq 'PENDING_EFFECT_RECONCILED' -and $rp._ctx.state.stage -ceq 'bound' -and $rp._ctx.changed -eq 0 -and $rp._ctx.state.receipts.Contains('bridge')) 'applied_bind_replayed';$cases++

@{status='PASS';cases=$cases;actual_guest_effects=0;actual_preparation=$false;originals_touched=$false;application_ready=$false;versioned_windows=$true;pending_reconciliation_cases=13;pending_reconciliation_denials=1}|ConvertTo-Json -Compress
