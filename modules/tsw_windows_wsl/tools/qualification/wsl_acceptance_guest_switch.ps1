#requires -Version 5.1
<# Qualification-only closed guest handoff. Dot sourcing is inert. #>
[CmdletBinding()]
param([ValidateSet('Prepare','QuiesceOriginal','EnterNew','VerifyPrepared','BindNew','ReturnOriginal','SealFixtureReturn','ReturnFixture','RestoreOriginal','Reconcile','StageOriginal','InspectOriginal','PrepareOriginal','BeginProductWindow','ReconcileEffects')][string]$Mode='Prepare',
      [ValidateSet('QuiesceOriginal','EnterNew','VerifyPrepared','BindNew','ReturnOriginal','SealFixtureReturn','ReturnFixture','RestoreOriginal','StageOriginal','InspectOriginal','PrepareOriginal','BeginProductWindow','ReconcileEffects')][string]$PrepareFor='QuiesceOriginal',
      [string]$ScenarioBase64='',[string]$ExpectedScenarioSha256='',
      [string]$ApprovalBase64='',[string]$ExpectedApprovalSha256='',
      [string]$BridgeApprovalBase64='',[string]$ExpectedBridgeApprovalSha256='',
      [string]$EvidenceSha256='')
$ErrorActionPreference='Stop'

function Get-WslSwitchCanonical($Value){
 if($null -eq $Value -or $Value -is [string] -or $Value -is [ValueType]){return $Value}
 if($Value -is [Collections.IDictionary]){$r=[ordered]@{};foreach($k in @($Value.Keys|Sort-Object)){$r[$k]=Get-WslSwitchCanonical $Value[$k]};return $r}
 if($Value -is [Collections.IEnumerable]){return ,@($Value|ForEach-Object{Get-WslSwitchCanonical $_})}
 $r=[ordered]@{};foreach($p in @($Value.PSObject.Properties|Sort-Object Name)){$r[$p.Name]=Get-WslSwitchCanonical $p.Value};return $r
}
function Get-WslSwitchBytes($Value){return ,([Text.UTF8Encoding]::new($false,$true)).GetBytes((ConvertTo-Json -InputObject (Get-WslSwitchCanonical $Value) -Depth 70 -Compress))}
function Get-WslSwitchRawHash([byte[]]$Bytes){$h=[Security.Cryptography.SHA256]::Create();try{return ([BitConverter]::ToString($h.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}}
function Get-WslSwitchHash($Value){return Get-WslSwitchRawHash (Get-WslSwitchBytes $Value)}
function Assert-WslSwitch($Condition,[string]$Code){if(!$Condition){throw $Code}}
function Assert-WslSwitchFields($Value,[string[]]$Names){
 $keys=if($Value -is [Collections.IDictionary]){@($Value.Keys)}else{@($Value.PSObject.Properties.Name)}
 Assert-WslSwitch ($null -ne $Value -and $keys.Count -eq $Names.Count) 'SWITCH_FIELDS'
 foreach($k in $keys){Assert-WslSwitch ($k -is [string] -and $k -cin $Names) 'SWITCH_FIELDS'}
}
function Read-WslSwitchWire([string]$Wire,[string]$Hash){
 Assert-WslSwitch ($Wire.Length -le 180000 -and $Hash -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_WIRE'
 $raw=[Convert]::FromBase64String($Wire)
 Assert-WslSwitch ($raw.Length -le 131072 -and (Get-WslSwitchRawHash $raw) -ceq $Hash) 'SWITCH_WIRE'
 $value=([Text.UTF8Encoding]::new($false,$true)).GetString($raw)|ConvertFrom-Json -ErrorAction Stop
 Assert-WslSwitch ([Convert]::ToBase64String((Get-WslSwitchBytes $value)) -ceq $Wire) 'SWITCH_NONCANONICAL'
 return $value
}
function Get-WslSwitchAssets {
 return @('modules/tsw_windows_wsl/tools/qualification/wsl_acceptance_guest_switch.ps1','modules/tsw_core/tests/fixtures/wsl_acceptance_guest_switch.ps1',
 'modules/tsw_windows_wsl/tests/tools/test_wsl_acceptance_guest_switch.py','modules/tsw_windows_wsl/tools/qualification/wsl_acceptance_registration.ps1',
 'modules/tsw_windows_wsl/tools/qualification/wsl_acceptance_bridge_binding.ps1','modules/tsw_windows_wsl/tools/qualification/wsl_resource_maintenance.ps1',
 'modules/tsw_windows_wsl/tools/qualification/windows_firewall_snapshot.ps1','modules/tsw_windows_wsl/tools/qualification/windows_firewall_certificate.ps1',
 'modules/tsw_windows_wsl/bootstrap/tws-wsl-bridge.ps1','modules/tsw_windows_wsl/bootstrap/tws-wsl-bridge-service.ps1','modules/tsw_windows_wsl/bootstrap/preparation/Preparation.psm1',
 'modules/tsw_windows_wsl/bootstrap/preparation/Resources.ps1','modules/tsw_windows_wsl/bootstrap/preparation/ResourceAdapters.ps1','modules/tsw_windows_wsl/bootstrap/preparation/SourceProof.ps1',
 'modules/tsw_windows_wsl/bootstrap/preparation/Bridge.ps1','modules/tsw_windows_wsl/bootstrap/preparation/Handoff.ps1','modules/tsw_windows_wsl/bootstrap/preparation/Policy.ps1',
 'modules/tsw_windows_wsl/bootstrap/preparation/Application.ps1','modules/tsw_windows_wsl/bootstrap/preparation/Adapters.ps1',
 'modules/tsw_core/tools/linux/qualification/wsl_original_runtime_window.py')
}
function Assert-WslSwitchScenario($s){
 $fields=@('schema_version','run_id','host','source_commit','pins','original_machine_sha256',
 'original_proposal_sha256','registration_scenario','registration_state_sha256','bridge_scenario','linux_pins','handoff_policy')
 if($s.schema_version -ceq 3){$fields+='window'}
 Assert-WslSwitchFields $s $fields
 Assert-WslSwitch ($s.schema_version -is [int] -and $s.schema_version -in @(2,3) -and $s.handoff_policy -ceq 'ALL_STOPPED_COLD_KERNEL_V1' -and $s.run_id -cmatch '\A[0-9a-f]{32}\z' -and
 $s.host -cmatch '\A[A-Za-z0-9][A-Za-z0-9.-]{0,62}\z' -and $s.source_commit -cmatch '\A[0-9a-f]{40}\z') 'SWITCH_SCENARIO'
 foreach($k in @('original_machine_sha256','original_proposal_sha256','registration_state_sha256')){Assert-WslSwitch ($s.$k -is [string] -and $s.$k -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_SCENARIO'}
 Assert-WslSwitchFields $s.pins (Get-WslSwitchAssets)
 foreach($k in Get-WslSwitchAssets){Assert-WslSwitch ($s.pins.$k -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_SOURCE_PINS'}
 Assert-WslSwitchFields $s.linux_pins @('native_runtime_inventory.py','native_lxd_snap_provenance.py')
 foreach($k in @('native_runtime_inventory.py','native_lxd_snap_provenance.py')){Assert-WslSwitch ($s.linux_pins.$k -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_LINUX_PINS'}
 $b=$s.bridge_scenario;$r=$s.registration_scenario
 Assert-WslSwitch ($b.run_id -ceq $s.run_id -and $r.run_id -ceq $s.run_id -and $b.host -ceq $s.host -and $r.host -ceq $s.host -and
 $b.source_commit -ceq $s.source_commit -and ($s.schema_version -ceq 3 -or $r.source_commit -ceq $s.source_commit) -and $b.original_distro -ceq 'Ubuntu' -and
 $b.new_distro -ceq ('TSW-Q440-'+$s.run_id) -and $r.image_sha256 -ceq '48d56724b5c8e60f24893e83e73bbb58c60b3ca22fba3da977075420acd54104') 'SWITCH_INPUT_BINDING'
 foreach($k in @('original_guid','new_guid')){Assert-WslSwitch ($b.$k -cmatch '\A\{[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\}\z') 'SWITCH_REGISTRATION'}
 Assert-WslSwitch ($b.original_guid -cne $b.new_guid) 'SWITCH_REGISTRATION'
 foreach($k in @('original_vhd_sha256','new_vhd_sha256')){Assert-WslSwitch ($b.$k -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_REGISTRATION'}
 if($s.schema_version -ceq 3){Assert-WslSwitchWindow $s}
}
function Get-WslSwitchOriginalContext($s){
 Assert-WslSwitch ($s.schema_version -ceq 3) 'SWITCH_WINDOW_REQUIRED'
 return [ordered]@{schema_version=1;run_id=$s.run_id;window=$s.window.kind;source_commit=$s.source_commit;
 scenario_sha256=(Get-WslSwitchHash $s);adapter_sha256=$s.window.adapter_sha256;machine_sha256=$s.original_machine_sha256;
 proposal_sha256=$s.original_proposal_sha256;backup_sha256=$s.window.backup_sha256;parent_switch_sha256=$s.window.parent_switch_sha256;
 parent_bridge_sha256=$s.window.parent_bridge_sha256;registration_sha256=$s.registration_state_sha256;
 legacy_lock_inode=$s.window.legacy_lock_inode;parent_switch=$s.window.parent_switch;parent_bridge=$s.window.parent_bridge}
}
function Assert-WslSwitchWindow($s){
 $w=$s.window
 Assert-WslSwitchFields $w @('kind','adapter_sha256','backup_sha256','legacy_lock_inode','parent_switch_sha256','parent_bridge_sha256','parent_switch','parent_bridge','source_view')
 Assert-WslSwitch ($w.kind -cin @('fixture','product') -and ($w.legacy_lock_inode -is [int] -or $w.legacy_lock_inode -is [long] -or $w.legacy_lock_inode -is [uint64]) -and $w.legacy_lock_inode -gt 0) 'SWITCH_WINDOW'
 foreach($key in @('adapter_sha256','backup_sha256','parent_switch_sha256','parent_bridge_sha256')){Assert-WslSwitch ($w.$key -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_WINDOW'}
 $zero='0'*64
 Assert-WslSwitch ($w.adapter_sha256 -ceq $s.pins.'modules/tsw_core/tools/linux/qualification/wsl_original_runtime_window.py' -and $w.backup_sha256 -cne $zero) 'SWITCH_WINDOW_SOURCE'
 if($w.kind -ceq 'fixture'){Assert-WslSwitch ($null -eq $w.parent_switch -and $null -eq $w.parent_bridge -and $w.parent_switch_sha256 -ceq $zero -and $w.parent_bridge_sha256 -ceq $zero) 'SWITCH_WINDOW_PARENT'}else{
  Assert-WslSwitch ($null -ne $w.parent_switch -and $null -ne $w.parent_bridge -and
   (Get-WslSwitchHash $w.parent_switch) -ceq $w.parent_switch_sha256 -and (Get-WslSwitchHash $w.parent_bridge) -ceq $w.parent_bridge_sha256) 'SWITCH_WINDOW_PARENT'
 }
 Assert-WslSwitch ($s.bridge_scenario.schema_version -ceq 2 -and $s.bridge_scenario.window -ceq $w.kind -and
  $s.bridge_scenario.parent_switch_sha256 -ceq $w.parent_switch_sha256 -and $s.bridge_scenario.parent_bridge_sha256 -ceq $w.parent_bridge_sha256 -and
  $s.bridge_scenario.registration_state_sha256 -ceq $s.registration_state_sha256 -and $w.source_view.source_commit -ceq $s.source_commit -and
  $w.source_view.registered_source_commit -ceq $s.registration_scenario.source_commit) 'SWITCH_WINDOW_BINDING'
}
function Get-WslSwitchSeconds([string]$Phase){switch -CaseSensitive ($Phase){
 'Prepare'{180};'QuiesceOriginal'{1500};'EnterNew'{2400};'VerifyPrepared'{600};'BindNew'{960};'ReturnOriginal'{2400};'SealFixtureReturn'{600};'ReturnFixture'{2400};'RestoreOriginal'{2200};'Reconcile'{300};'StageOriginal'{900};'InspectOriginal'{600};'PrepareOriginal'{900};'BeginProductWindow'{600};'ReconcileEffects'{2400};default{throw 'SWITCH_PHASE'}}}
function Assert-WslSwitchRunning($Observation,$s,[string]$Wanted){
 $names=@($Observation.running)
 $expected=@(switch -CaseSensitive ($Wanted){'original'{@('Ubuntu')};'new'{@('TSW-Q440-'+$s.run_id)};'none'{@()};default{throw 'SWITCH_RUNNING_PREDICATE'}})
 Assert-WslSwitch ($names.Count -eq @($expected).Count) 'SWITCH_RUNNING_SCOPE'
 if($names.Count){Assert-WslSwitch ($names[0] -ceq $expected[0]) 'SWITCH_RUNNING_SCOPE'}
}
function Assert-WslSwitchApproval($go,$s,[string]$Phase,[string]$Proposal,[DateTimeOffset]$Now,[string]$Evidence){
 $fields=@('schema_version','decision','phase','scenario_sha256','source_commit','proposal_sha256','expires_at_utc','evidence_sha256')
 if($s.schema_version -ceq 3){$fields+=@('original_context_sha256','original_proposal_sha256','original_lock_witness','legacy_go','legacy_go_sha256')}
 Assert-WslSwitchFields $go $fields
 if($s.schema_version -ceq 3){
  Assert-WslSwitch ($go.original_context_sha256 -ceq (Get-WslSwitchHash (Get-WslSwitchOriginalContext $s)) -and $go.original_proposal_sha256 -ceq $s.original_proposal_sha256) 'SWITCH_ORIGINAL_GO_BINDING'
  if($Phase -ceq 'QuiesceOriginal'){Assert-WslSwitch ($null -ne $go.legacy_go -and $go.legacy_go_sha256 -ceq (Get-WslSwitchHash $go.legacy_go)) 'SWITCH_ORIGINAL_INNER_GO'}else{Assert-WslSwitch ($null -eq $go.legacy_go -and $go.legacy_go_sha256 -ceq ('0'*64)) 'SWITCH_ORIGINAL_INNER_GO'}
 }
 Assert-WslSwitch ($go.schema_version -is [int] -and $go.schema_version -eq 1 -and $go.decision -ceq 'GO' -and $go.phase -ceq $Phase -and
 $go.scenario_sha256 -ceq (Get-WslSwitchHash $s) -and $go.source_commit -ceq $s.source_commit -and $go.proposal_sha256 -ceq $Proposal -and
 $go.evidence_sha256 -ceq $Evidence) 'SWITCH_GO_BINDING'
 $expiry=[DateTimeOffset]::ParseExact($go.expires_at_utc,'yyyy-MM-ddTHH:mm:ssZ',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::AssumeUniversal)
 $remaining=($expiry-$Now).TotalSeconds;$reserve=Get-WslSwitchSeconds $Phase
 Assert-WslSwitch ($remaining -ge $reserve -and $remaining -le $reserve+300) 'SWITCH_GO_EXPIRED'
}
function New-WslSwitchBookmark($s){$v=@{schema_version=$(if($s.schema_version -ceq 3){3}else{2});scenario_sha256=(Get-WslSwitchHash $s);run_id=$s.run_id;source_commit=$s.source_commit;
 original_guid=$s.bridge_scenario.original_guid;new_guid=$s.bridge_scenario.new_guid;original_vhd_sha256=$s.bridge_scenario.original_vhd_sha256;
 new_vhd_sha256=$s.bridge_scenario.new_vhd_sha256;stage='registered';pending='';receipts=@{};resets=@{}}
 if($s.schema_version -ceq 3){$v.window=$s.window.kind;$v.original_context_sha256=Get-WslSwitchHash (Get-WslSwitchOriginalContext $s);$v.bridge_scenario_sha256=Get-WslSwitchHash $s.bridge_scenario}
 return $v
}
function Assert-WslSwitchBookmark($v,$s){
 $fields=@('schema_version','scenario_sha256','run_id','source_commit','original_guid','new_guid','original_vhd_sha256','new_vhd_sha256','stage','pending','receipts','resets')
 if($s.schema_version -ceq 3){$fields+=@('window','original_context_sha256','bridge_scenario_sha256')}
 Assert-WslSwitchFields $v $fields
 if($s.schema_version -ceq 3){Assert-WslSwitch ($v.window -ceq $s.window.kind -and $v.original_context_sha256 -ceq (Get-WslSwitchHash (Get-WslSwitchOriginalContext $s)) -and $v.bridge_scenario_sha256 -ceq (Get-WslSwitchHash $s.bridge_scenario)) 'SWITCH_BOOKMARK_WINDOW'}
 $expected=New-WslSwitchBookmark $s
 foreach($k in @('schema_version','scenario_sha256','run_id','source_commit','original_guid','new_guid','original_vhd_sha256','new_vhd_sha256')){Assert-WslSwitch ($v.$k -ceq $expected.$k) 'SWITCH_BOOKMARK_BINDING'}
 Assert-WslSwitch ($v.stage -cin @('registered','original_prepared','quiesced','original_bridge_stopped','original_stopped','reset_for_new','new_running','safe','prepared','bound',
 'fixture_new_stopped','fixture_reset_for_original','original_payload_staged','new_stopped','reset_for_original','original_running','original_bridge_ready','restored') -and $v.pending -cin @('','quiesce-original','stop-original-bridge',
 'terminate-original','reset-to-new','start-new','bind-new','stage-original','terminate-new','reset-to-original','start-original','resume-original-bridge','restore-original','prepare-original')) 'SWITCH_BOOKMARK_STATE'
 Assert-WslSwitch ($v.receipts -is [Collections.IDictionary] -and $v.receipts.Count -le 16) 'SWITCH_BOOKMARK_RECEIPTS'
 foreach($k in $v.receipts.Keys){Assert-WslSwitch ($k -cin @('registration','quiesce','network','prepared','stopped','bridge','restore','fixture_boundary','fixture_seal','fixture_original_boot','reconciliation_parent','parent_switch','parent_bridge','recovered_fixture') -and $v.receipts[$k] -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_BOOKMARK_RECEIPTS'}
 Assert-WslSwitch ($v.resets -is [Collections.IDictionary] -and $v.resets.Count -le 2) 'SWITCH_RESET_FIELDS'
 foreach($direction in $v.resets.Keys){
  Assert-WslSwitch ($direction -cin @('new','original')) 'SWITCH_RESET_FIELDS'
  $row=$v.resets[$direction];Assert-WslSwitchFields $row @('action','previous_boot_sha256','next_boot_sha256','machine_sha256','outcome')
  Assert-WslSwitch ($row.action -ceq ('reset-to-'+$direction) -and $row.previous_boot_sha256 -cmatch '\A[0-9a-f]{64}\z' -and
   $row.machine_sha256 -cmatch '\A[0-9a-f]{64}\z' -and $row.outcome -cin @('captured','intent','command-returned','all-stopped','changed-boot') -and
   ($row.next_boot_sha256 -ceq '' -or $row.next_boot_sha256 -cmatch '\A[0-9a-f]{64}\z')) 'SWITCH_RESET_FIELDS'
  if($row.outcome -ceq 'changed-boot'){Assert-WslSwitch ($row.next_boot_sha256 -and $row.next_boot_sha256 -cne $row.previous_boot_sha256) 'SWITCH_BOOT_UNCHANGED'}
 }
}
function Assert-WslSwitchResetBoundary($s,$state,$observation,[string]$Direction,[string]$BridgeStatus,$Children){
 Assert-WslSwitch ($Direction -cin @('new','original') -and $state.pending -ceq ('reset-to-'+$Direction) -and
  $state.resets[$Direction].outcome -ceq 'intent' -and $BridgeStatus -ceq 'Stopped') 'SWITCH_RESET_NOT_ADMITTED'
 Assert-WslSwitchBookmark $state $s
 Assert-WslSwitch ($observation.registration_count -eq 2 -and $observation.registrations_sha256 -ceq $state.receipts.registration) 'SWITCH_RESET_REGISTRATION'
 Assert-WslSwitchRunning $observation $s none
 Assert-WslSwitchFields $Children @('clients','workers')
 Assert-WslSwitch ($Children.clients -is [int] -and $Children.clients -eq 0 -and $Children.workers -is [int] -and $Children.workers -eq 0) 'SWITCH_UNSETTLED_CHILD'
}
function Invoke-WslAcceptanceGuestSwitch($s,[string]$Phase,$go,$bridgeGo,[string]$Evidence,[Collections.IDictionary]$Ports,[string]$Target='QuiesceOriginal'){
 $result=[ordered]@{schema_version=1;scope='WSL_CLOSED_GUEST_SWITCH';phase=$Phase;status='BLOCKED';recovery_required=$false;application_ready=$false;error='NONE'}
 $lock=$null;$state=$null;$control=@{intent=$false}
 try{
  Assert-WslSwitchScenario $s
  foreach($name in @('Begin','Clock','Source','Observe','Load','Save','Lock','Unlock','Original','Bridge','Terminate','Start','Network','Prepared','Stopped','Registration','Reset','Boot','FixtureBoundary','FixtureProof')){
   Assert-WslSwitch ($Ports.Contains($name) -and $Ports[$name] -is [scriptblock]) 'SWITCH_PORTS'}
  if($s.schema_version -ceq 3){foreach($name in @('StageOriginal','OriginalWitness','Parent','BridgeStopped','OriginalBridge','BridgeOutcome')){Assert-WslSwitch ($Ports.Contains($name) -and $Ports[$name] -is [scriptblock]) 'SWITCH_PORTS'}}
  & $Ports.Begin $Phase | Out-Null;& $Ports.Source $s | Out-Null
  $state=& $Ports.Load $s;$before=& $Ports.Observe $s
  if($null -eq $state){Assert-WslSwitch ($before.receipt_matches -eq $true) 'SWITCH_REGISTRATION_DRIFT';$state=New-WslSwitchBookmark $s;$state.receipts.registration=$before.registrations_sha256}else{Assert-WslSwitchBookmark $state $s}
  Assert-WslSwitch ($before.registration_count -eq 2 -and $before.registrations_sha256 -ceq $state.receipts.registration) 'SWITCH_REGISTRATION_DRIFT'
  $proposal=Get-WslSwitchHash @($before,$state)
  function FixtureEvidence([bool]$Recovery=$false) {
   $boundary=if($Recovery){@{fingerprint=$state.receipts.fixture_boundary}}else{& $Ports.FixtureBoundary $s}
   Assert-WslSwitch ($boundary.fingerprint -cmatch '\A[0-9a-f]{64}\z' -and $boundary.fingerprint -ceq $state.receipts.fixture_boundary) 'SWITCH_FIXTURE_BOUNDARY'
   $proof=& $Ports.FixtureProof $s
   Assert-WslSwitchFields $proof @('status','run_id','source_commit','boot_id_sha256','machine_id_sha256','resources_sha256','daemon','workers','product_started')
   Assert-WslSwitch ($proof.status -ceq 'FIXTURE_RETURN_EMPTY' -and $proof.run_id -ceq $s.run_id -and $proof.source_commit -ceq $s.source_commit -and
    $proof.workers -is [int] -and $proof.workers -eq 0 -and $proof.product_started -is [bool] -and !$proof.product_started -and
    $proof.daemon -cin @('EXACT_INCUS_EMPTY','POSITIVELY_ABSENT')) 'SWITCH_FIXTURE_PROOF'
   foreach($key in @('boot_id_sha256','machine_id_sha256','resources_sha256')){Assert-WslSwitch ($proof.$key -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_FIXTURE_PROOF'}
   return @{proof=$proof;digest=(Get-WslSwitchHash @($proof,$boundary.fingerprint,(Get-WslSwitchHash $s)))}
  }
  if($Phase -ceq 'Prepare'){
   $result.target_phase=$Target;$result.proposal_sha256=$proposal
   if($Target -cin @('SealFixtureReturn','ReturnFixture') -and @($before.running).Count -eq 1 -and $before.running[0] -ceq ('TSW-Q440-'+$s.run_id)){$result.evidence_sha256=(FixtureEvidence).digest}
   if($Target -ceq 'ReturnFixture' -and !$result.Contains('evidence_sha256') -and $state.receipts.Contains('fixture_seal')){$result.evidence_sha256=$state.receipts.fixture_seal}
   if($Target -ceq 'ReconcileEffects' -and $state.pending -ceq 'bind-new'){$outcome=& $Ports.BridgeOutcome $s;if($outcome.status -cne 'BOUND'){$result.evidence_sha256=(FixtureEvidence $true).digest}}
   if($s.schema_version -ceq 3 -and @($before.running).Count -eq 1 -and $before.running[0] -ceq 'Ubuntu'){$result.original_lock_witness=& $Ports.OriginalWitness $s;$result.original_context_sha256=Get-WslSwitchHash (Get-WslSwitchOriginalContext $s)}
   $result.status='PREPARED_READ_ONLY';return $result
  }
  if($Phase -ceq 'InspectOriginal'){
   Assert-WslSwitch ($s.schema_version -ceq 3 -and !$state.pending) 'SWITCH_WINDOW_REQUIRED'
   Assert-WslSwitchRunning $before $s original
   $result.original=& $Ports.Original 'inspect' $s;$result.original_lock_witness=& $Ports.OriginalWitness $s
   $result.status='ORIGINAL_INSPECTED_READ_ONLY';return $result
  }
  if($Phase -ceq 'Reconcile'){
   $result.recovery_required=[bool]$state.pending
   $result.stage=$state.stage;$result.pending=$state.pending
   if($s.schema_version -ceq 3 -and $s.window.kind -ceq 'fixture' -and $state.stage -ceq 'restored' -and !$state.pending){$result.parent=& $Ports.Parent $s;$result.original=& $Ports.Original 'restored' $s}
   $result.status=if($state.pending){'RECOVERY_REQUIRED'}else{'OBSERVED_READ_ONLY'}
   return $result
  }
  Assert-WslSwitchApproval $go $s $Phase $proposal (& $Ports.Clock) $Evidence
  $lock=& $Ports.Lock
  & $Ports.Source $s | Out-Null
  $fresh=& $Ports.Observe $s;$loaded=& $Ports.Load $s
  if($null -eq $loaded){Assert-WslSwitch ($fresh.receipt_matches -eq $true) 'SWITCH_REGISTRATION_DRIFT';$loaded=New-WslSwitchBookmark $s;$loaded.receipts.registration=$fresh.registrations_sha256}
  Assert-WslSwitch ((Get-WslSwitchHash @($fresh,$loaded)) -ceq $proposal) 'SWITCH_PRESTATE_DRIFT'
  Assert-WslSwitch (!$state.pending -or $Phase -cin @('SealFixtureReturn','ReturnFixture','ReconcileEffects')) 'SWITCH_UNCERTAIN_NOT_REPLAYABLE'
  function Check([string]$Wanted){& $Ports.Source $s | Out-Null;$actual=& $Ports.Observe $s;Assert-WslSwitch ($actual.registration_count -eq 2 -and $actual.registrations_sha256 -ceq $state.receipts.registration) 'SWITCH_REGISTRATION_DRIFT';Assert-WslSwitchRunning $actual $s $Wanted;return $actual}
  function CurrentBoot([string]$Who){
   $boot=& $Ports.Boot $Who $s
   if($Who -ceq 'original' -and $state.receipts.Contains('fixture_original_boot')){
    Assert-WslSwitch ($boot.machine_id_sha256 -ceq $s.original_machine_sha256 -and $boot.boot_id_sha256 -ceq $state.receipts.fixture_original_boot) 'SWITCH_BOOT_BINDING_DRIFT';return
   }
   $row=$state.resets[$Who]
   Assert-WslSwitch ($null -ne $row -and $row.outcome -ceq 'changed-boot' -and $boot.boot_id_sha256 -ceq $row.next_boot_sha256 -and
    $boot.machine_id_sha256 -ceq $(if($Who -ceq 'original'){$s.original_machine_sha256}else{$row.machine_sha256})) 'SWITCH_BOOT_BINDING_DRIFT'
  }
  function SaveStage([string]$Stage){$state.stage=$Stage;$state.pending='';$state=& $Ports.Save $s $state;Assert-WslSwitchBookmark $state $s}
  function Intent([string]$Action){$state.pending=$Action;$control.intent=$true;$state=& $Ports.Save $s $state;Assert-WslSwitchBookmark $state $s}
  if($Phase -ceq 'StageOriginal'){
   Assert-WslSwitch ($s.schema_version -ceq 3 -and $state.stage -ceq 'registered' -and !$state.pending) 'SWITCH_STAGE'
   Check original | Out-Null
   $result.source=& $Ports.StageOriginal $s $go;$result.status='ORIGINAL_SOURCE_STAGED'
  }elseif($Phase -ceq 'BeginProductWindow'){
   Assert-WslSwitch ($s.schema_version -ceq 3 -and $s.window.kind -ceq 'product' -and $state.stage -ceq 'registered' -and !$state.pending -and $null -eq (& $Ports.Load $s)) 'SWITCH_STAGE'
   Check original | Out-Null;$parents=& $Ports.Parent $s
   Assert-WslSwitch ((Get-WslSwitchHash $parents.switch) -ceq $s.window.parent_switch_sha256 -and (Get-WslSwitchHash $parents.bridge) -ceq $s.window.parent_bridge_sha256) 'SWITCH_WINDOW_PARENT'
   & $Ports.Original 'inspect' $s | Out-Null
   $state.receipts.parent_switch=$s.window.parent_switch_sha256;$state.receipts.parent_bridge=$s.window.parent_bridge_sha256
   $control.intent=$true;SaveStage 'registered';$result.status='PRODUCT_WINDOW_OPENED'
  }elseif($Phase -ceq 'PrepareOriginal'){
   Assert-WslSwitch ($s.schema_version -ceq 3 -and $state.stage -ceq 'registered' -and !$state.pending) 'SWITCH_STAGE'
   Check original | Out-Null;& $Ports.Registration $s | Out-Null
   if($s.window.kind -ceq 'product'){
    $parents=& $Ports.Parent $s
    Assert-WslSwitch ($state.receipts.parent_switch -ceq $s.window.parent_switch_sha256 -and $state.receipts.parent_bridge -ceq $s.window.parent_bridge_sha256 -and
     (Get-WslSwitchHash $parents.switch) -ceq $s.window.parent_switch_sha256 -and (Get-WslSwitchHash $parents.bridge) -ceq $s.window.parent_bridge_sha256) 'SWITCH_WINDOW_PARENT'
   }
   Intent 'prepare-original';$q=& $Ports.Original 'prepare' $s $go
   Assert-WslSwitch ($q.status -ceq 'ORIGINAL_PREPARED' -and $q.proposal_sha256 -ceq $s.original_proposal_sha256) 'SWITCH_ORIGINAL_PREPARE'
   SaveStage 'original_prepared';$result.status='ORIGINAL_PREPARED'
  }elseif($Phase -ceq 'ReconcileEffects'){
   Assert-WslSwitch ($s.schema_version -ceq 3 -and [bool]$state.pending) 'SWITCH_RECOVERY_NOT_ADMITTED'
   $old=Get-WslSwitchHash $state;$action=$state.pending
   # Preserve the old intent in create-only history before recording its exact,
   # freshly approved resolution. No unknown action is replayed implicitly.
   $state.receipts.reconciliation_parent=$old
   if($action -ceq 'prepare-original'){
    Check original | Out-Null;$control.intent=$true;& $Ports.Original 'recover-prepare' $s $go | Out-Null;$q=& $Ports.Original 'prepared' $s
    Assert-WslSwitch ($q.status -ceq 'ORIGINAL_PREPARED') 'SWITCH_RECOVERY_INCOMPLETE';SaveStage 'original_prepared'
   }elseif($action -cin @('quiesce-original','restore-original')){
    Check original | Out-Null
    # A bridge still running must be positively original-bound; a bridge that
    # was stopped/bound requires its independently approved Recover/Resume.
    if($state.stage -cin @('registered','original_prepared','quiesced')){& $Ports.FixtureBoundary $s $true | Out-Null}else{Assert-WslSwitch ($state.stage -ceq 'original_bridge_ready') 'SWITCH_RECOVERY_BRIDGE_REQUIRED';& $Ports.OriginalBridge $s | Out-Null}
    $control.intent=$true;$q=& $Ports.Original 'restore' $s $go
    Assert-WslSwitch ($q.decision -ceq 'RESTORED' -and $q.proposal_sha256 -ceq $s.original_proposal_sha256) 'SWITCH_RESTORE_RESULT'
    & $Ports.Original 'restored' $s | Out-Null;$state.receipts.restore=Get-WslSwitchHash $q;SaveStage 'restored'
   }elseif($action -cin @('stop-original-bridge','bind-new','stage-original','resume-original-bridge')){
    if($action -ceq 'bind-new'){
     Check new | Out-Null;$outcome=& $Ports.BridgeOutcome $s
     if($outcome.status -ceq 'BOUND'){$state.receipts.bridge=Get-WslSwitchHash $outcome;SaveStage 'bound';$result.status='PENDING_EFFECT_RECONCILED';$result.stage=$state.stage;return $result}
     Assert-WslSwitch ($outcome.status -ceq 'RECOVERY_REQUIRED') 'SWITCH_BRIDGE_RESULT'
     $proof=FixtureEvidence $true
     Assert-WslSwitch ($Evidence -ceq $proof.digest -and !$state.receipts.Contains('stopped')) 'SWITCH_RECOVERY_DISPOSAL_REQUIRED'
    }elseif($action -ceq 'stage-original'){
     Check new | Out-Null;& $Ports.Stopped $s $state.receipts.stopped | Out-Null
    }else{Check original | Out-Null;& $Ports.Original 'quiescent' $s | Out-Null}
    Assert-WslSwitch ($bridgeGo.phase -ceq 'Recover') 'SWITCH_RECOVERY_BRIDGE_GO'
    $control.intent=$true;$b=& $Ports.Bridge 'Recover' $s $bridgeGo
    Assert-WslSwitch ($b.status -ceq 'RECOVERED_STOPPED') 'SWITCH_BRIDGE_RESULT'
    & $Ports.BridgeStopped $s | Out-Null
    if($action -ceq 'stop-original-bridge'){$boundary=& $Ports.FixtureBoundary $s;$state.receipts.fixture_boundary=$boundary.fingerprint;SaveStage 'original_bridge_stopped'}
    elseif($action -ceq 'bind-new'){
     # Recover may leave the original payload staged in a live transaction and
     # owned routes from an attempted new binding. Preserve that provenance;
     # the fresh empty-case proof authorizes only returning the new guest.
     Check new | Out-Null;$last=& $Ports.Boot 'new' $s
     Assert-WslSwitch ($last.boot_id_sha256 -ceq $proof.proof.boot_id_sha256 -and $last.machine_id_sha256 -ceq $proof.proof.machine_id_sha256) 'SWITCH_BOOT_BINDING_DRIFT'
     $state.receipts.recovered_fixture=$proof.digest
     $state.resets.original=@{action='reset-to-original';previous_boot_sha256=$last.boot_id_sha256;next_boot_sha256='';machine_sha256=$last.machine_id_sha256;outcome='captured'}
     Intent 'terminate-new';& $Ports.Terminate 'new' $s | Out-Null;Check none | Out-Null;SaveStage 'new_stopped'
    }
    elseif($action -ceq 'stage-original'){SaveStage 'original_payload_staged'}else{SaveStage 'original_running'}
   }elseif($action -cin @('terminate-original','terminate-new')){
    & $Ports.BridgeStopped $s | Out-Null
    $who=if($action -ceq 'terminate-original'){'original'}else{'new'}
    $names=@($before.running)
    if($action -ceq 'terminate-original'){
     $boundary=& $Ports.FixtureBoundary $s
     Assert-WslSwitch ($boundary.fingerprint -ceq $state.receipts.fixture_boundary -and $null -ne $state.resets.new -and $state.resets.new.outcome -ceq 'captured') 'SWITCH_RECOVERY_TERMINATE_PROOF'
    }else{
     Assert-WslSwitch ((($state.receipts.Contains('stopped') -and $state.stage -ceq 'original_payload_staged') -or ($state.receipts.Contains('recovered_fixture') -and $state.stage -ceq 'prepared')) -and $null -ne $state.resets.original -and $state.resets.original.outcome -ceq 'captured') 'SWITCH_RECOVERY_TERMINATE_PROOF'
    }
    if($names.Count){
     Check $who | Out-Null
     if($who -ceq 'original'){& $Ports.Original 'quiescent' $s | Out-Null}else{if($state.receipts.Contains('recovered_fixture')){$freshProof=FixtureEvidence $true;Assert-WslSwitch ($freshProof.digest -ceq $state.receipts.recovered_fixture) 'SWITCH_FIXTURE_PROOF'}else{CurrentBoot new;& $Ports.Stopped $s $state.receipts.stopped | Out-Null}}
     # Explicit current-phase GO admits this bounded retry only after proving
     # the guest still running and the unchanged disposal/bridge boundary.
     $control.intent=$true;& $Ports.Terminate $who $s | Out-Null
    }
    Check none | Out-Null
    SaveStage $(if($who -ceq 'original'){'original_stopped'}else{'new_stopped'})
   }elseif($action -ceq 'start-new'){
    # Never launch the new guest to resolve uncertainty. A positively observed
    # empty fixture can be sealed separately; an all-stopped outcome returns
    # through the original-direction reset path.
    & $Ports.BridgeStopped $s | Out-Null
    if(@($before.running).Count -eq 0){
     Check none | Out-Null
     Assert-WslSwitch ($state.resets.new.outcome -ceq 'all-stopped') 'SWITCH_RECOVERY_START_PROOF'
     SaveStage 'original_stopped'
    }else{
     Check new | Out-Null;$proof=FixtureEvidence
     Assert-WslSwitch ($state.resets.new.outcome -ceq 'all-stopped' -and $proof.proof.boot_id_sha256 -cne $state.resets.new.previous_boot_sha256 -and $proof.proof.machine_id_sha256 -cne $s.original_machine_sha256) 'SWITCH_RECOVERY_START_PROOF'
     $state.resets.new.next_boot_sha256=$proof.proof.boot_id_sha256;$state.resets.new.machine_sha256=$proof.proof.machine_id_sha256;$state.resets.new.outcome='changed-boot';SaveStage 'new_running'
    }
   }elseif($action -cin @('reset-to-new','reset-to-original','start-original')){
    & $Ports.BridgeStopped $s | Out-Null
    $running=@((Check $(if(@($before.running).Count -eq 0){'none'}else{'original'})).running)
    if(!$running.Count){
     $row=if($action -ceq 'reset-to-new'){$state.resets.new}else{$state.resets.original}
     Assert-WslSwitch ($null -ne $row -and $row.outcome -cin @('captured','intent','command-returned','all-stopped')) 'SWITCH_RECOVERY_RESET_PROOF'
     $state.resets.original=@{action='reset-to-original';previous_boot_sha256=$row.previous_boot_sha256;next_boot_sha256='';machine_sha256=$s.original_machine_sha256;outcome='intent'}
     Intent 'reset-to-original';$reset=& $Ports.Reset 'original' $s $state
     Assert-WslSwitch ($reset.status -ceq 'VM_RESET_ALL_STOPPED' -and $state.resets.original.outcome -ceq 'all-stopped') 'SWITCH_RESET_OUTCOME'
     SaveStage 'reset_for_original';Intent 'start-original';& $Ports.Start 'original' $s | Out-Null
    }else{Assert-WslSwitch ($action -ceq 'start-original' -and $state.resets.original.outcome -ceq 'all-stopped') 'SWITCH_RECOVERY_RESET_PROOF'}
    Check original | Out-Null;$boot=& $Ports.Boot 'original' $s
    Assert-WslSwitch ($boot.machine_id_sha256 -ceq $s.original_machine_sha256 -and $boot.boot_id_sha256 -cne $state.resets.original.previous_boot_sha256) 'SWITCH_BOOT_UNCHANGED'
    & $Ports.Original 'quiescent' $s | Out-Null
    $state.resets.original.next_boot_sha256=$boot.boot_id_sha256;$state.resets.original.machine_sha256=$s.original_machine_sha256;$state.resets.original.outcome='changed-boot';SaveStage 'original_running'
   }else{throw 'SWITCH_RECOVERY_UNRESOLVED'}
   $result.status='PENDING_EFFECT_RECONCILED';$result.stage=$state.stage
  }elseif($Phase -ceq 'QuiesceOriginal'){
   Assert-WslSwitch ($state.stage -ceq $(if($s.schema_version -ceq 3){'original_prepared'}else{'registered'})) 'SWITCH_STAGE';Check original | Out-Null
   & $Ports.Registration $s | Out-Null
   Intent 'quiesce-original';$q=& $Ports.Original 'quiesce' $s $go
   Assert-WslSwitch ($q.scope -ceq 'WSL_EXACT_GUEST_RUNTIME_WINDOW_ONLY' -and $q.decision -ceq 'QUIESCED' -and $q.proposal_sha256 -ceq $s.original_proposal_sha256) 'SWITCH_QUIESCE_RESULT'
   $actual=& $Ports.Original 'quiescent' $s
   $state.receipts.quiesce=Get-WslSwitchHash $q;SaveStage 'quiesced';$result.status='ORIGINAL_QUIESCED'
  }elseif($Phase -ceq 'EnterNew'){
   Assert-WslSwitch ($state.stage -cin @('quiesced','original_bridge_stopped','original_stopped','reset_for_new','new_running')) 'SWITCH_STAGE'
   if($state.stage -ceq 'quiesced'){
    $activeBoundary=& $Ports.FixtureBoundary $s $true
    Check original | Out-Null;& $Ports.Original 'quiescent' $s | Out-Null
    Assert-WslSwitch ($bridgeGo.guest_quiesce_sha256 -ceq $state.receipts.quiesce) 'SWITCH_BRIDGE_QUIESCE_BINDING'
    Intent 'stop-original-bridge';$b=& $Ports.Bridge 'StopOriginal' $s $bridgeGo
    Assert-WslSwitch ($b.status -ceq 'ORIGINAL_BRIDGE_STOPPED') 'SWITCH_BRIDGE_RESULT'
    $boundary=& $Ports.FixtureBoundary $s
    $state.receipts.fixture_boundary=$boundary.fingerprint;SaveStage 'original_bridge_stopped'
   }
   if($state.stage -ceq 'original_bridge_stopped'){
    Check original | Out-Null;$last=& $Ports.Original 'quiescent' $s
    Assert-WslSwitch ($last.boot_id_sha256 -cmatch '\A[0-9a-f]{64}\z' -and $last.machine_id_sha256 -ceq $s.original_machine_sha256) 'SWITCH_BOOT_PROOF'
    $state.resets.new=@{action='reset-to-new';previous_boot_sha256=$last.boot_id_sha256;next_boot_sha256='';machine_sha256=$last.machine_id_sha256;outcome='captured'}
    Intent 'terminate-original';& $Ports.Terminate 'original' $s | Out-Null;Check none | Out-Null;SaveStage 'original_stopped'
   }
   if($state.stage -ceq 'original_stopped'){
    Check none | Out-Null;$state.resets.new.outcome='intent';Intent 'reset-to-new'
    $reset=& $Ports.Reset 'new' $s $state;Assert-WslSwitch ($reset.status -ceq 'VM_RESET_ALL_STOPPED' -and $state.resets.new.outcome -ceq 'all-stopped') 'SWITCH_RESET_OUTCOME';SaveStage 'reset_for_new'
   }
   if($state.stage -ceq 'reset_for_new'){
    Check none | Out-Null;Intent 'start-new';& $Ports.Start 'new' $s | Out-Null;Check new | Out-Null;$boot=& $Ports.Boot 'new' $s
    Assert-WslSwitch ($boot.boot_id_sha256 -cmatch '\A[0-9a-f]{64}\z' -and $boot.boot_id_sha256 -cne $state.resets.new.previous_boot_sha256 -and $boot.machine_id_sha256 -cmatch '\A[0-9a-f]{64}\z' -and $boot.machine_id_sha256 -cne $s.original_machine_sha256) 'SWITCH_BOOT_UNCHANGED'
    $state.resets.new.next_boot_sha256=$boot.boot_id_sha256;$state.resets.new.machine_sha256=$boot.machine_id_sha256;$state.resets.new.outcome='changed-boot';SaveStage 'new_running'
   }
   Check new | Out-Null;CurrentBoot new;$network=& $Ports.Network $s
   if($network.status -ceq 'KERNEL_NETWORK_UNKNOWN_PREREQUISITE_REQUIRED'){$result.status='NEW_GUEST_NETWORK_PREREQUISITE_REQUIRED';return $result}
   Assert-WslSwitch ($network.status -ceq 'KERNEL_NETWORK_ABSENT') 'SWITCH_NETWORK_NOT_PROVEN'
   $state.receipts.network=Get-WslSwitchHash $network;SaveStage 'safe';$result.status='NEW_GUEST_SAFE_FOR_PREPARATION'
  }elseif($Phase -ceq 'VerifyPrepared'){
   Assert-WslSwitch ($state.stage -ceq 'safe' -and $Evidence -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_STAGE';Check new | Out-Null;CurrentBoot new
   $p=& $Ports.Prepared $s $Evidence;Assert-WslSwitch ($p.status -ceq 'NEW_GUEST_PREPARED') 'SWITCH_PREPARATION_NOT_PROVEN'
   $state.receipts.prepared=$Evidence;SaveStage 'prepared';$result.status='NEW_GUEST_PREPARED'
  }elseif($Phase -ceq 'BindNew'){
   Assert-WslSwitch ($state.stage -ceq 'prepared') 'SWITCH_STAGE';Check new | Out-Null;CurrentBoot new
   & $Ports.Prepared $s $state.receipts.prepared | Out-Null
   Intent 'bind-new';$b=& $Ports.Bridge 'Bind' $s $bridgeGo;Assert-WslSwitch ($b.status -ceq 'NEW_BINDING_READY') 'SWITCH_BRIDGE_RESULT'
   $state.receipts.bridge=Get-WslSwitchHash $b;SaveStage 'bound';$result.status='NEW_BINDING_READY'
  }elseif($Phase -ceq 'ReturnOriginal'){
   Assert-WslSwitch ($state.stage -cin @('bound','original_payload_staged','new_stopped','reset_for_original') -and $Evidence -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_STAGE'
   if($state.stage -ceq 'bound'){
    Check new | Out-Null;CurrentBoot new;$stopped=& $Ports.Stopped $s $Evidence
    Assert-WslSwitch ($stopped.status -ceq 'OWNED_CASES_DISPOSED') 'SWITCH_NEW_QUIESCE_NOT_PROVEN'
    Assert-WslSwitch ($bridgeGo.guest_quiesce_sha256 -ceq $Evidence) 'SWITCH_BRIDGE_QUIESCE_BINDING'
    $state.receipts.stopped=$Evidence;Intent 'stage-original';$b=& $Ports.Bridge 'StageRestore' $s $bridgeGo
    Assert-WslSwitch ($b.status -ceq 'ORIGINAL_PAYLOAD_STAGED_STOPPED') 'SWITCH_BRIDGE_RESULT';SaveStage 'original_payload_staged'
   }
   if($state.stage -ceq 'original_payload_staged'){
    Check new | Out-Null;CurrentBoot new;$last=& $Ports.Stopped $s $state.receipts.stopped
    Assert-WslSwitch ($last.boot_id_sha256 -cmatch '\A[0-9a-f]{64}\z' -and $last.machine_id_sha256 -ceq $state.resets.new.machine_sha256) 'SWITCH_BOOT_PROOF'
    $state.resets.original=@{action='reset-to-original';previous_boot_sha256=$last.boot_id_sha256;next_boot_sha256='';machine_sha256=$last.machine_id_sha256;outcome='captured'}
    Intent 'terminate-new';& $Ports.Terminate 'new' $s | Out-Null;Check none | Out-Null;SaveStage 'new_stopped'
   }
   if($state.stage -ceq 'new_stopped'){Check none | Out-Null;$state.resets.original.outcome='intent';Intent 'reset-to-original'
    $reset=& $Ports.Reset 'original' $s $state;Assert-WslSwitch ($reset.status -ceq 'VM_RESET_ALL_STOPPED' -and $state.resets.original.outcome -ceq 'all-stopped') 'SWITCH_RESET_OUTCOME';SaveStage 'reset_for_original'}
   Check none | Out-Null;Intent 'start-original';& $Ports.Start 'original' $s | Out-Null;Check original | Out-Null
   $boot=& $Ports.Boot 'original' $s
   Assert-WslSwitch ($boot.boot_id_sha256 -cmatch '\A[0-9a-f]{64}\z' -and $boot.boot_id_sha256 -cne $state.resets.original.previous_boot_sha256 -and $boot.machine_id_sha256 -ceq $s.original_machine_sha256) 'SWITCH_BOOT_UNCHANGED'
   $state.resets.original.next_boot_sha256=$boot.boot_id_sha256;$state.resets.original.machine_sha256=$boot.machine_id_sha256;$state.resets.original.outcome='changed-boot'
   & $Ports.Original 'quiescent' $s | Out-Null;SaveStage 'original_running';$result.status='ORIGINAL_READY_FOR_BRIDGE_RESUME'
  }elseif($Phase -cin @('SealFixtureReturn','ReturnFixture')){
   # This route never binds a bridge to the fixture or accepts a product ledger.
   Assert-WslSwitch ($state.stage -cin @('registered','original_prepared','quiesced','original_bridge_stopped','original_stopped','reset_for_new','new_running','safe','prepared','fixture_new_stopped','fixture_reset_for_original','original_running')) 'SWITCH_FIXTURE_STAGE'
   Assert-WslSwitch ($state.stage -cne 'registered' -or $state.pending -ceq 'quiesce-original') 'SWITCH_FIXTURE_STAGE'
   Assert-WslSwitch (!$state.receipts.Contains('bridge') -and !$state.receipts.Contains('stopped')) 'SWITCH_FIXTURE_PRODUCT_STARTED'
   $running=@((Check $(if(@($before.running).Count){if($before.running[0] -ceq 'Ubuntu'){'original'}else{'new'}}else{'none'})).running)
   $originalRunning=$running.Count -eq 1 -and $running[0] -ceq 'Ubuntu'
   $newRunning=$running.Count -eq 1 -and $running[0] -ceq ('TSW-Q440-'+$s.run_id)
   $proof=$null
   if($newRunning){
    $observation=FixtureEvidence
    $proof=$observation.proof
    Assert-WslSwitch ($state.receipts.Contains('fixture_boundary') -and $Evidence -ceq $observation.digest) 'SWITCH_FIXTURE_EVIDENCE'
   }
   if(!$newRunning -and $state.receipts.Contains('fixture_boundary')){
    $boundary=& $Ports.FixtureBoundary $s
    Assert-WslSwitch ($boundary.fingerprint -ceq $state.receipts.fixture_boundary) 'SWITCH_FIXTURE_BOUNDARY'
   }
   if($state.pending){
    # A fresh phase GO binds the exact uncertain bookmark. Only positively
    # observed outcomes below may be reconciled; unknown outcomes stay retained.
    switch -CaseSensitive ($state.pending){
     'quiesce-original'{
      Assert-WslSwitch ($originalRunning -and $Phase -ceq 'ReturnFixture') 'SWITCH_FIXTURE_PENDING'
      & $Ports.Original 'quiescent' $s | Out-Null;& $Ports.FixtureBoundary $s $true | Out-Null;SaveStage 'quiesced'
     }
     'stop-original-bridge'{
      Assert-WslSwitch ($originalRunning -and $Phase -ceq 'ReturnFixture') 'SWITCH_FIXTURE_PENDING'
      & $Ports.Original 'quiescent' $s | Out-Null;$boundary=& $Ports.FixtureBoundary $s
      $state.receipts.fixture_boundary=$boundary.fingerprint;SaveStage 'original_bridge_stopped'
     }
     'terminate-original'{
      Assert-WslSwitch (!$newRunning -and $Phase -ceq 'ReturnFixture') 'SWITCH_FIXTURE_PENDING'
      $boundary=& $Ports.FixtureBoundary $s
      Assert-WslSwitch ($boundary.fingerprint -ceq $state.receipts.fixture_boundary) 'SWITCH_FIXTURE_BOUNDARY'
      if($originalRunning){& $Ports.Original 'quiescent' $s | Out-Null;SaveStage 'original_bridge_stopped'}else{
       Assert-WslSwitch ($null -ne $state.resets.new -and $state.resets.new.outcome -ceq 'captured') 'SWITCH_FIXTURE_PENDING';SaveStage 'original_stopped'
      }
     }
     'reset-to-new'{
      Assert-WslSwitch (!$running.Count -and $Phase -ceq 'ReturnFixture' -and $state.resets.new.outcome -cin @('intent','command-returned','all-stopped')) 'SWITCH_FIXTURE_PENDING'
      # Return performs a separate, freshly approved original-direction reset.
      SaveStage 'original_stopped'
     }
     'start-new'{
      Assert-WslSwitch ($newRunning -and $Phase -ceq 'SealFixtureReturn' -and $state.resets.new.outcome -ceq 'all-stopped' -and
       $proof.boot_id_sha256 -cne $state.resets.new.previous_boot_sha256 -and $proof.machine_id_sha256 -cne $s.original_machine_sha256) 'SWITCH_FIXTURE_PENDING'
      $state.resets.new.next_boot_sha256=$proof.boot_id_sha256;$state.resets.new.machine_sha256=$proof.machine_id_sha256;$state.resets.new.outcome='changed-boot';SaveStage 'new_running'
     }
     'terminate-new'{
      Assert-WslSwitch ($Phase -ceq 'ReturnFixture' -and $state.receipts.Contains('fixture_seal') -and $state.stage -cin @('new_running','safe','prepared')) 'SWITCH_FIXTURE_PENDING'
      if($newRunning){Assert-WslSwitch ($observation.digest -ceq $state.receipts.fixture_seal) 'SWITCH_FIXTURE_SEAL';SaveStage $state.stage}else{
       Assert-WslSwitch (!$running.Count -and $Evidence -ceq $state.receipts.fixture_seal -and $null -ne $state.resets.original) 'SWITCH_FIXTURE_PENDING';SaveStage 'fixture_new_stopped'
      }
     }
     'reset-to-original'{
      Assert-WslSwitch ($Phase -ceq 'ReturnFixture' -and !$running.Count -and $state.receipts.Contains('fixture_seal') -and
       $state.stage -ceq 'fixture_new_stopped' -and $state.resets.original.outcome -ceq 'all-stopped') 'SWITCH_FIXTURE_PENDING';SaveStage 'fixture_reset_for_original'
     }
     'start-original'{
      Assert-WslSwitch ($Phase -ceq 'ReturnFixture' -and $state.stage -ceq 'fixture_reset_for_original' -and $state.receipts.Contains('fixture_seal')) 'SWITCH_FIXTURE_PENDING'
      if($originalRunning){
       $boot=& $Ports.Boot 'original' $s
       Assert-WslSwitch ($boot.machine_id_sha256 -ceq $s.original_machine_sha256 -and $boot.boot_id_sha256 -cne $state.resets.original.previous_boot_sha256) 'SWITCH_BOOT_UNCHANGED'
       & $Ports.Original 'quiescent' $s | Out-Null
       $state.resets.original.next_boot_sha256=$boot.boot_id_sha256;$state.resets.original.machine_sha256=$s.original_machine_sha256;$state.resets.original.outcome='changed-boot';SaveStage 'original_running'
      }else{Assert-WslSwitch (!$running.Count -and $state.resets.original.outcome -ceq 'all-stopped') 'SWITCH_FIXTURE_PENDING';SaveStage 'fixture_reset_for_original'}
     }
     default{throw 'SWITCH_FIXTURE_PENDING_UNRESOLVED'}
    }
   }
   if($Phase -ceq 'SealFixtureReturn'){
    Assert-WslSwitch ($newRunning -and $state.stage -cin @('new_running','safe','prepared')) 'SWITCH_FIXTURE_STAGE'
    CurrentBoot new
    $state.receipts.fixture_seal=$observation.digest;SaveStage $state.stage
    $result.status='FIXTURE_RETURN_SEALED';$result.evidence_sha256=$observation.digest;return $result
   }
   if($state.stage -cin @('quiesced','original_prepared')){
    $activeBoundary=& $Ports.FixtureBoundary $s $true
    Check original | Out-Null
    if($state.stage -ceq 'original_prepared'){& $Ports.Original 'prepared' $s | Out-Null}else{& $Ports.Original 'quiescent' $s | Out-Null}
    Intent 'restore-original';$q=& $Ports.Original 'restore' $s $go
    Assert-WslSwitch ($q.decision -ceq 'RESTORED' -and $q.proposal_sha256 -ceq $s.original_proposal_sha256) 'SWITCH_RESTORE_RESULT'
    & $Ports.Original 'restored' $s | Out-Null
    $finalBoundary=& $Ports.FixtureBoundary $s $true
    Assert-WslSwitch ($finalBoundary.fingerprint -ceq $activeBoundary.fingerprint) 'SWITCH_FIXTURE_BOUNDARY'
    $state.receipts.restore=Get-WslSwitchHash $q;SaveStage 'restored'
    $result.status='ORIGINAL_RESTORED_NEW_RETAINED_STOPPED';return $result
   }
   $boundary=& $Ports.FixtureBoundary $s
   Assert-WslSwitch ($boundary.fingerprint -ceq $state.receipts.fixture_boundary) 'SWITCH_FIXTURE_BOUNDARY'
   if($state.stage -ceq 'original_bridge_stopped'){
    Check original | Out-Null;$boot=& $Ports.Boot 'original' $s
    Assert-WslSwitch ($boot.machine_id_sha256 -ceq $s.original_machine_sha256) 'SWITCH_BOOT_BINDING_DRIFT'
    & $Ports.Original 'quiescent' $s | Out-Null
    $state.receipts.fixture_original_boot=$boot.boot_id_sha256;SaveStage 'original_running'
   }
   if($state.stage -cin @('new_running','safe','prepared')){
    Check new | Out-Null;CurrentBoot new
    Assert-WslSwitch ($state.receipts.fixture_seal -ceq $observation.digest) 'SWITCH_FIXTURE_SEAL'
    $state.resets.original=@{action='reset-to-original';previous_boot_sha256=$proof.boot_id_sha256;next_boot_sha256='';machine_sha256=$proof.machine_id_sha256;outcome='captured'}
    Intent 'terminate-new';& $Ports.Terminate 'new' $s | Out-Null;Check none | Out-Null;SaveStage 'fixture_new_stopped'
   }
   if($state.stage -cin @('original_stopped','reset_for_new')){
    Check none | Out-Null
    Assert-WslSwitch ($null -ne $state.resets.new -and $state.resets.new.previous_boot_sha256 -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_FIXTURE_ORIGINAL_BOOT'
    $state.resets.original=@{action='reset-to-original';previous_boot_sha256=$state.resets.new.previous_boot_sha256;next_boot_sha256='';machine_sha256=$s.original_machine_sha256;outcome='captured'}
    # Separate marker prevents a later fixture intent from being mistaken for a
    # product return. No fixture guest was ever started on this branch.
    $state.receipts.fixture_seal=Get-WslSwitchHash @($s.source_commit,$state.receipts.fixture_boundary,'NEW_NOT_STARTED');SaveStage 'fixture_new_stopped'
   }
   if($state.stage -ceq 'fixture_new_stopped'){
    Check none | Out-Null;$state.resets.original.outcome='intent';Intent 'reset-to-original'
    $reset=& $Ports.Reset 'original' $s $state
    Assert-WslSwitch ($reset.status -ceq 'VM_RESET_ALL_STOPPED' -and $state.resets.original.outcome -ceq 'all-stopped') 'SWITCH_RESET_OUTCOME';SaveStage 'fixture_reset_for_original'
   }
   if($state.stage -ceq 'fixture_reset_for_original'){
    Check none | Out-Null;Intent 'start-original';& $Ports.Start 'original' $s | Out-Null;Check original | Out-Null
    $boot=& $Ports.Boot 'original' $s
    Assert-WslSwitch ($boot.machine_id_sha256 -ceq $s.original_machine_sha256 -and $boot.boot_id_sha256 -cne $state.resets.original.previous_boot_sha256) 'SWITCH_BOOT_UNCHANGED'
    $state.resets.original.next_boot_sha256=$boot.boot_id_sha256;$state.resets.original.machine_sha256=$s.original_machine_sha256;$state.resets.original.outcome='changed-boot'
    & $Ports.Original 'quiescent' $s | Out-Null;SaveStage 'original_running'
   }
   Assert-WslSwitch ($state.stage -ceq 'original_running') 'SWITCH_FIXTURE_STAGE';Check original | Out-Null;CurrentBoot original
   $result.status='ORIGINAL_READY_FOR_BRIDGE_RESUME'
  }elseif($Phase -ceq 'RestoreOriginal'){
   Assert-WslSwitch ($state.stage -cin @('original_running','original_bridge_ready')) 'SWITCH_STAGE';Check original | Out-Null;CurrentBoot original
   & $Ports.Original 'quiescent' $s | Out-Null
   if($state.stage -ceq 'original_running'){
    Intent 'resume-original-bridge';$b=& $Ports.Bridge 'ResumeOriginal' $s $bridgeGo
    Assert-WslSwitch ($b.status -ceq 'ORIGINAL_BINDING_RESTORED') 'SWITCH_BRIDGE_RESULT';SaveStage 'original_bridge_ready'
   }
   Check original | Out-Null;if($s.schema_version -ceq 3){& $Ports.OriginalBridge $s | Out-Null};Intent 'restore-original';$q=& $Ports.Original 'restore' $s $go
   Assert-WslSwitch ($q.decision -ceq 'RESTORED' -and $q.proposal_sha256 -ceq $s.original_proposal_sha256) 'SWITCH_RESTORE_RESULT'
   & $Ports.Original 'restored' $s | Out-Null;Check original | Out-Null
   $state.receipts.restore=Get-WslSwitchHash $q;SaveStage 'restored';$result.status='ORIGINAL_RESTORED_NEW_RETAINED_STOPPED'
  }else{throw 'SWITCH_PHASE'}
 }catch{
  $result.error='SWITCH_REFUSED_OR_UNCERTAIN';if($_.Exception.Message -cmatch '\ASWITCH_[A-Z0-9_]{1,80}\z'){$result.error=$_.Exception.Message}
  if($control.intent -or ($null -ne $state -and $state.pending)){$result.recovery_required=$true;$result.status='RECOVERY_REQUIRED'}
 }finally{if($null -ne $lock){try{& $Ports.Unlock $lock | Out-Null}catch{$result.status='RECOVERY_REQUIRED';$result.recovery_required=$true}}}
 return $result
}

function Get-WslSwitchOriginalStageProbe {
 return @'
import sys,os,stat,json,hashlib,base64,re,time,fcntl,subprocess
from pathlib import Path
from uuid import UUID
run,window,source,expected,scenario,context,proposal,machine,ctx64,go64,go_sha,part,total,data=sys.argv[1:]
def need(x):
    if not x:raise ValueError('staging_refused')
def sha(x):return hashlib.sha256(x).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def validate_staging(ctxraw,goraw,run,window,source,expected,scenario,context,proposal,machine):
    ctx=json.loads(ctxraw);go=json.loads(goraw)
    need(canon(ctx)==ctxraw and sha(ctxraw)==context and canon(go)==goraw)
    need(ctx['run_id']==run and ctx['window']==window and ctx['source_commit']==source and ctx['adapter_sha256']==expected and ctx['machine_sha256']==machine and ctx['scenario_sha256']==scenario and ctx['proposal_sha256']==proposal)
    need(set(go)=={'schema_version','decision','phase','scenario_sha256','source_commit','proposal_sha256','expires_at_utc','evidence_sha256','original_context_sha256','original_proposal_sha256','original_lock_witness','legacy_go','legacy_go_sha256'})
    need(type(go['schema_version']) is int and go['schema_version']==1 and go['decision']=='GO' and go['phase']=='StageOriginal' and go['scenario_sha256']==scenario and go['source_commit']==source and go['original_context_sha256']==context and go['original_proposal_sha256']==proposal and go['legacy_go'] is None and go['legacy_go_sha256']=='0'*64)
    import datetime
    expiry=datetime.datetime.strptime(go['expires_at_utc'],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp()
    need(0<expiry-time.time()<=1200)
    return ctx,go
def trusted(p):
    for q in (p,*p.parents):
        s=q.lstat();need(s.st_uid==0 and not stat.S_ISLNK(s.st_mode) and not s.st_mode&0o022)
def private(p):
    trusted(p);s=p.lstat();need(stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and s.st_size<=131072)
    raw=p.read_bytes();need(len(raw)==s.st_size);return raw
def put(p,raw):
    if os.path.lexists(p):need(private(p)==raw);return
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,'wb',closefd=False) as f:f.write(raw);f.flush();os.fsync(fd)
    finally:os.close(fd)
    fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)
need(os.geteuid()==0 and re.fullmatch('[0-9a-f]{32}',run) and window in ('fixture','product') and re.fullmatch('[0-9a-f]{40}',source))
need(all(re.fullmatch('[0-9a-f]{64}',v) for v in (expected,scenario,context,proposal,machine,go_sha)))
ctxraw=base64.b64decode(ctx64,validate=True);body=base64.b64decode(go64,validate=True)
need(len(ctxraw)<=131072 and len(body)<=131072 and sha(body)==go_sha)
ctx,go=validate_staging(ctxraw,body,run,window,source,expected,scenario,context,proposal,machine)
index=int(part);count=int(total);need(0<=index<=count and 1<=count<=64)
lock=Path('/root/tsw440-wsl-r7-20261108/runtime-window/lock');trusted(lock)
info=lock.lstat();need(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and stat.S_IMODE(info.st_mode)==0o600 and info.st_ino==ctx['legacy_lock_inode'])
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(str(UUID(boot))==boot)
need(sha(Path('/etc/machine-id').read_bytes().strip())==machine)
witness={'device':info.st_dev,'inode':info.st_ino,'machine_sha256':machine,'boot_sha256':sha(boot.encode())}
need(go['original_lock_witness']==witness)
base=Path('/root/tsw440-acceptance');existing=base if base.exists() else Path('/root');trusted(existing)
for p in (existing,lock):
    result=subprocess.run(['/usr/bin/findmnt','-T',str(p),'-n','-o','FSTYPE'],stdin=subprocess.DEVNULL,capture_output=True,timeout=10,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
    need(result.returncode==0 and result.stdout==b'ext4\n' and not result.stderr)
fd=os.open(lock,os.O_RDONLY|os.O_NOFOLLOW)
try:
    need(os.fstat(fd)==info);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);need(lock.lstat()==info)
    for p in (base,base/run,base/run/'original-windows',base/run/'original-windows'/window):
        if not os.path.lexists(p):trusted(p.parent);p.mkdir(mode=0o700)
        trusted(p);need(p.is_dir() and stat.S_IMODE(p.stat().st_mode)==0o700)
    home=base/run/'original-windows'/window
    for p in (home.parent/('machine-'+machine+'.lock'),home/'window.lock'):put(p,b'')
    locks=[]
    try:
        for p in (home.parent/('machine-'+machine+'.lock'),home/'window.lock'):
            current=p.lstat();handle=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);locks.append(handle)
            need(os.fstat(handle)==current);fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);need(p.lstat()==current)
        identity={'schema_version':1,'run_id':run,'window':window,'source_commit':source,'adapter_sha256':expected,'parts':count,'machine_sha256':machine}
        put(home/'delivery.json',canon(identity))
        authorities=list(home.glob('authority-*.json'));need(len(authorities)<64 or (home/('authority-'+go_sha+'.json')).exists())
        put(home/('authority-'+go_sha+'.json'),body)
        if index<count:
            raw=base64.b64decode(data,validate=True);need(0<len(raw)<=6144)
            put(home/('part-'+str(index).zfill(4)),raw)
            print('{"status":"ORIGINAL_SOURCE_PART_STAGED"}')
        else:
            need(data=='')
            chunks=[private(home/('part-'+str(i).zfill(4))) for i in range(count)]
            raw=b''.join(chunks);need(len(raw)<=131072 and sha(raw)==expected)
            put(home/'adapter.py',raw)
            print('{"status":"ORIGINAL_SOURCE_STAGED"}')
    finally:
        for handle in reversed(locks):os.close(handle)
finally:os.close(fd)
'@
}
function Get-WslSwitchOriginalWitnessProbe {
 return @'
import os,sys,stat,json,hashlib,re,fcntl
from pathlib import Path
from uuid import UUID
machine,expected=sys.argv[1:];expected=int(expected)
p=Path('/root/tsw440-wsl-r7-20261108/runtime-window/lock')
for q in (p,*p.parents):
 s=q.lstat();assert s.st_uid==0 and not stat.S_ISLNK(s.st_mode) and not s.st_mode&0o022
s=p.lstat();assert stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and s.st_ino==expected
fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
try:
 assert os.fstat(fd)==s;fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);assert p.lstat()==s
 raw=Path('/etc/machine-id').read_bytes().strip();assert re.fullmatch(b'[0-9a-f]{32}',raw) and hashlib.sha256(raw).hexdigest()==machine
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert str(UUID(boot))==boot
 print(json.dumps({'device':s.st_dev,'inode':s.st_ino,'machine_sha256':machine,'boot_sha256':hashlib.sha256(boot.encode()).hexdigest()},sort_keys=True,separators=(',',':')))
finally:os.close(fd)
'@
}

function Get-WslSwitchOriginalAdapterProbe {
 return @'
import sys,os,stat,hashlib,re
from pathlib import Path
run,window,expected,*arguments=sys.argv[1:]
assert re.fullmatch('[0-9a-f]{32}',run) and window in ('fixture','product') and re.fullmatch('[0-9a-f]{64}',expected)
p=Path('/root/tsw440-acceptance')/run/'original-windows'/window/'adapter.py'
for q in (p,*p.parents):
    s=q.lstat();assert s.st_uid==0 and not stat.S_ISLNK(s.st_mode) and not s.st_mode&0o022
s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and s.st_size<=131072
fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
try:
    z=os.fstat(fd);assert (z.st_dev,z.st_ino)==(s.st_dev,s.st_ino)
    with os.fdopen(fd,'rb',closefd=False) as stream:raw=stream.read(131073)
    assert len(raw)==s.st_size and hashlib.sha256(raw).hexdigest()==expected and p.lstat().st_ino==z.st_ino
finally:os.close(fd)
sys.argv=[str(p),*arguments]
exec(compile(raw,str(p),'exec',dont_inherit=True),{'__name__':'__main__','__file__':str(p)})
'@
}

function Get-WslSwitchOriginalProbe {
 return @'
import sys,os,stat,hashlib,json,importlib.util
from pathlib import Path
kind,machine,proposal=sys.argv[1:]
p=Path('/root/tsw440-wsl-r7-20261108/epic440-wsl-runtime-window.py')
assert p.is_file() and not p.is_symlink() and p.stat().st_uid==0 and p.stat().st_size<=1048576 and p.stat().st_nlink==1 and stat.S_IMODE(p.stat().st_mode)==0o600
assert hashlib.sha256(p.read_bytes()).hexdigest()=='fcf16059dced9a3ed07ea54e1d346e7b67726cfe873de2849b58a202519962bd'
spec=importlib.util.spec_from_file_location('epic440_original_window',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.trusted_tree(p);port=m.RealPort(machine);journal=m.Journal(m.PRIVATE)
raw=m.read_proposal(journal);assert m.sha(raw)==proposal
baseline=m.strict(raw);m.validate_baseline(baseline);port.settle()
current=port.snapshot();m.verify_observation(baseline,current,journal,restored=(kind=='restored'))
from uuid import UUID
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert str(UUID(boot))==boot
print(json.dumps({'boot_id_sha256':m.sha(boot.encode()),'machine_id_sha256':machine,'status':'ORIGINAL_RESTORED' if kind=='restored' else 'ORIGINAL_QUIESCENT','proposal_sha256':proposal,'observation_sha256':m.digest(current)},sort_keys=True,separators=(',',':')))
'@
}
function Get-WslSwitchBootProbe {
 return @'
import os,json,hashlib
from pathlib import Path
from uuid import UUID
assert os.geteuid()==0 and 'microsoft' in Path('/proc/sys/kernel/osrelease').read_text().lower()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert str(UUID(boot))==boot
machine=Path('/etc/machine-id').read_text().strip();assert len(machine)==32 and all(c in '0123456789abcdef' for c in machine)
print(json.dumps({'boot_id_sha256':hashlib.sha256(boot.encode()).hexdigest(),'machine_id_sha256':hashlib.sha256(machine.encode()).hexdigest()},sort_keys=True,separators=(',',':')))
'@
}
function Get-WslSwitchNetworkProbe {
 # Linux UAPI nf_tables/nfnetlink/netlink.h: closed GETTABLE dump only. Missing
 # already-loaded modules is UNKNOWN, never a socket request that can autoload.
 return @'
import os,sys,json,socket,struct,time,stat,hashlib
from pathlib import Path
class Unknown(Exception):pass
class Residue(Exception):pass
_reads={}
def need(value):
    if not value:raise Unknown()
def read(path,limit=65536):
    with open(path,'rb') as stream:data=stream.read(limit+1)
    need(len(data)<=limit);_reads[str(path)]=hashlib.sha256(data).hexdigest();return data
def nft_messages(data,seq,port):
    offset=0;done=False
    while offset<len(data):
        need(len(data)-offset>=16)
        length,kind,flags,seen,pid=struct.unpack_from('=IHHII',data,offset)
        need(16<=length<=len(data)-offset and seen==seq and pid==port and flags&~2==0)
        body=data[offset+16:offset+length];offset+=(length+3)&~3
        need(offset<=len(data))
        if kind==3:
            need(flags==2 and not done and len(body) in (0,4) and (not body or struct.unpack('=i',body)[0]==0))
            done=True
        elif kind==2:
            raise Unknown()
        elif kind==0xA00:
            need(not done and len(body)>=4 and body[1]==0);raise Residue()
        else:raise Unknown()
    return done
def nft_empty():
    need(Path('/sys/module/nf_tables').is_dir() and Path('/sys/module/nfnetlink').is_dir())
    with socket.socket(socket.AF_NETLINK,socket.SOCK_RAW,12) as sock:
        sock.settimeout(2);sock.bind((0,0));port=sock.getsockname()[0];seq=1
        need(sock.sendto(struct.pack('=IHHII',20,0xA01,0x301,seq,port)+b'\x00\x00\x00\x00',(0,0))==20)
        total=0;deadline=time.monotonic()+3
        for _ in range(8):
            need(time.monotonic()<deadline)
            data,ancillary,flags,address=sock.recvmsg(65536)
            need(address==(0,0) and not ancillary and not flags and data)
            total+=len(data);need(total<=262144)
            if nft_messages(data,seq,port):
                _reads['netfilter_dump']=hashlib.sha256(data).hexdigest();return
        raise Unknown()
def inspect():
    need(os.geteuid()==0 and 'microsoft' in read('/proc/sys/kernel/osrelease').decode().lower())
    machine=read('/etc/machine-id',64).strip();need(len(machine)==32 and all(c in b'0123456789abcdef' for c in machine))
    names=set(os.listdir('/sys/class/net'));need(names=={'lo','eth0'})
    route=read('/proc/net/route').decode().splitlines();need(route and len(route)<=128)
    for row in route[1:]:
        fields=row.split();need(len(fields)==11 and fields[0] in names)
    ipv6=Path('/proc/net/ipv6_route')
    if ipv6.exists():
        rows=read(ipv6).decode().splitlines();need(len(rows)<=128)
        for row in rows:need(len(row.split())==10 and row.split()[-1] in names)
    for name in ('ip_tables_names','ip6_tables_names','arp_tables_names'):
        path=Path('/proc/net')/name
        if path.exists() and read(path).strip():raise Residue()
    for name in ('tcp','tcp6','udp','udp6','unix'):
        rows=read('/proc/net/'+name,131072).decode().splitlines();need(rows and len(rows)<=1024)
        for row in rows[1:]:
            fields=row.split()
            if name=='unix':
                if any(x in row.lower() for x in ('incus','lxd','docker')):raise Residue()
            else:
                need(len(fields)>=4)
                address,port=fields[1].rsplit(':',1);port=int(port,16)
                listening=fields[3]=='0A' if name.startswith('tcp') else port!=0
                loopback=address in {'0100007F','3500007F','00000000000000000000000001000000'}
                if listening and (not loopback or port!=53):raise Residue()
    for path in ('/var/lib/incus/unix.socket','/run/incus/unix.socket','/var/run/docker.sock','/var/snap/lxd/common/lxd/unix.socket'):
        if os.path.lexists(path):raise Residue()
    nft_empty()
    return hashlib.sha256(json.dumps({'reads':_reads,'interfaces':sorted(names)},sort_keys=True,separators=(',',':')).encode()).hexdigest()
if __name__=='__main__':
    try:
        need(sys.argv[1:]==[]);proof=inspect();print(json.dumps({'status':'KERNEL_NETWORK_ABSENT','observation_sha256':proof},sort_keys=True,separators=(',',':')))
    except Residue:print('{"status":"KERNEL_NETWORK_RESIDUE"}');sys.exit(2)
    except Exception:print('{"status":"KERNEL_NETWORK_UNKNOWN_PREREQUISITE_REQUIRED"}');sys.exit(2)
'@
}
function Get-WslSwitchFixtureProof {
 # Fixed stdlib-only read probe: no package, preparation or capability admission.
 return @'
import sys,os,stat,json,hashlib,re,socket,http.client,time,struct
from pathlib import Path
from uuid import UUID
run,source=sys.argv[1:]
def need(value):
    if not value:raise ValueError('fixture_return_unproven')
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def trusted(path):
    for item in (path,*path.parents):
        info=item.lstat();need(info.st_uid==0 and not stat.S_ISLNK(info.st_mode) and not info.st_mode&0o022)
def read(path,limit=65536):
    with path.open('rb') as stream:raw=stream.read(limit+1)
    need(len(raw)<=limit);return raw
need(os.geteuid()==0 and re.fullmatch('[0-9a-f]{32}',run) and re.fullmatch('[0-9a-f]{40}',source))
need('microsoft' in read(Path('/proc/sys/kernel/osrelease')).decode().lower())
boot=read(Path('/proc/sys/kernel/random/boot_id')).decode().strip();need(str(UUID(boot))==boot)
machine=read(Path('/etc/machine-id')).strip();need(re.fullmatch(b'[0-9a-f]{32}',machine))
root=Path('/root/tsw440-acceptance')/run
if os.path.lexists(root):
    trusted(root);need(root.is_dir())
    for name in ('cases','product-case-ledger.json','new-case-stop.json'):
        need(not os.path.lexists(root/name))
    # Known preparation/fixture child intents cannot be ignored after a crash.
    rows=list(root.iterdir());need(len(rows)<=128)
    for row in rows:
        need(not row.is_symlink())
        if row.is_file() and ('intent' in row.name or 'journal' in row.name or 'pid' in row.name):need(False)
for path in ('/var/lib/lxd','/var/snap/lxd','/var/snap/incus','/run/lxd','/run/incus/unix.socket','/run/docker.sock','/var/lib/docker'):
    need(not os.path.lexists(path))
workers=('wsl_product_acceptance.py','product_upgrade_cases.py','incus_profile_listener_fixture.py','native_lxd_maintenance.py','native_runtime_inventory.py','pytest','unittest','tiny_swarm_world')
programs={'apt','apt-get','dpkg','snap','git','pip','pip3','incus','lxc','lxd','dockerd','containerd','lxc-start','lxc-monitord','forkproxy'}
def process_snapshot():
    pids=list(Path('/proc').iterdir());need(len(pids)<=8192);daemons=[]
    for pid in pids:
        if not pid.name.isdigit() or int(pid.name)==os.getpid():continue
        try:
            raw=read(pid/'cmdline');args=[part.decode('utf-8','strict') for part in raw.split(b'\0') if part]
            if not args:continue
            binary=Path(args[0]).name
            need(not re.fullmatch(r'(?:python|pypy)[0-9.]*|bash|dash|sh|zsh|fish|busybox|make|cmake|gcc|g[+][+]|cc|ninja|node|npm|curl|wget|sudo|timeout|setsid',binary))
            need(binary not in programs and not any(any(word in arg for word in workers) for arg in args))
            need(not any(str(root) in arg for arg in args))
            if binary=='incusd':
                executable=(pid/'exe').resolve(strict=True);trusted(executable)
                need(str(executable) in {'/usr/libexec/incus/incusd','/usr/lib/incus/incusd','/opt/incus/bin/incusd'} and pid.stat().st_uid==0)
                daemons.append(int(pid.name))
        except FileNotFoundError:
            need(not pid.exists())
    need(len(daemons)<=1);return daemons
daemons=process_snapshot()
def check_resources(query):
    projects=query('/1.0/projects?recursion=1');need(isinstance(projects,list) and len(projects)==1 and projects[0].get('name')=='default')
    need(query('/1.0/instances?recursion=1&project=default')==[])
    profiles=query('/1.0/profiles?recursion=1&project=default')
    need(isinstance(profiles,list) and len(profiles)==1 and profiles[0].get('name')=='default' and profiles[0].get('used_by')==[])
    devices=profiles[0].get('devices');need(isinstance(devices,dict) and all(isinstance(v,dict) and v.get('type') in {'disk','nic'} for v in devices.values()))
    pools=query('/1.0/storage-pools?recursion=1');need(isinstance(pools,list) and len(pools)<=16)
    names=[];storage=[]
    for pool in pools:
        name=pool.get('name');need(isinstance(name,str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.+-]{0,62}',name) and name not in names);names.append(name)
        volumes=query('/1.0/storage-pools/'+name+'/volumes?recursion=1&project=default')
        need(isinstance(volumes,list) and len(volumes)<=2048 and all(isinstance(v,dict) and v.get('type')=='image' and re.fullmatch('[0-9a-f]{64}',v.get('name','')) for v in volumes))
        storage.append({'pool':pool,'volumes':sorted(volumes,key=lambda item:item['name'])})
    operations=query('/1.0/operations?recursion=1&all-projects=true');need(isinstance(operations,dict) and all(isinstance(v,list) and not v for v in operations.values()))
    return digest({'projects':projects,'instances':[],'profiles':profiles,'storage':sorted(storage,key=lambda item:item['pool']['name']),'operations':operations})
sock=Path('/var/lib/incus/unix.socket')
if os.path.lexists(sock):
    trusted(sock.parent);info=sock.lstat()
    need(stat.S_ISSOCK(info.st_mode) and info.st_uid==0 and not info.st_mode&0o007 and len(daemons)==1)
    started=time.monotonic();calls=0
    def unique(pairs):
        value={}
        for key,item in pairs:need(key not in value);value[key]=item
        return value
    def query(uri):
        global calls
        calls+=1;need(calls<=64 and time.monotonic()-started<120)
        connection=http.client.HTTPConnection('localhost',timeout=3)
        channel=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);channel.settimeout(3)
        try:
            channel.connect(str(sock));peer,uid,_=struct.unpack('3i',channel.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,struct.calcsize('3i')))
            need(uid==0 and peer in daemons)
            connection.sock=channel;connection.request('GET',uri,headers={'Host':'localhost','Connection':'close'})
            reply=connection.getresponse();need(reply.status==200)
            raw=reply.read(1048577);need(len(raw)<=1048576)
            row=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:need(False))
            need(isinstance(row,dict) and row.get('type')=='sync' and row.get('status_code')==200 and row.get('error_code')==0 and row.get('error')=='' and row.get('operation')=='')
            return row['metadata']
        finally:connection.close();channel.close()
    server=query('/1.0');need(server.get('environment',{}).get('server_version')=='6.0.5')
    resources=check_resources(query);daemon='EXACT_INCUS_EMPTY'
else:
    need(not daemons)
    for path in ('/var/lib/incus','/run/incus','/usr/bin/incus','/usr/sbin/incusd','/usr/libexec/incus/incusd','/usr/lib/incus/incusd','/opt/incus'):
        need(not os.path.lexists(path))
    resources=digest({'daemon':'POSITIVELY_ABSENT','resources':[]});daemon='POSITIVELY_ABSENT'
need(process_snapshot()==daemons)
print(json.dumps({'status':'FIXTURE_RETURN_EMPTY','run_id':run,'source_commit':source,'boot_id_sha256':hashlib.sha256(boot.encode()).hexdigest(),'machine_id_sha256':hashlib.sha256(machine).hexdigest(),'resources_sha256':resources,'daemon':daemon,'workers':0,'product_started':False},sort_keys=True,separators=(',',':')))
'@
}

function Get-WslSwitchNewProof {
 return @'
import sys,os,stat,json,hashlib,subprocess,importlib.util,re,socket,struct
from uuid import UUID
from pathlib import Path
kind,run,source,expected,encoded=sys.argv[1:]
need=lambda value: value or (_ for _ in ()).throw(ValueError('proof'))
need(re.fullmatch('[0-9a-f]{32}',run) and re.fullmatch('[0-9a-f]{40}',source) and re.fullmatch('[0-9a-f]{64}',expected))
need(os.geteuid()==0)
root=Path('/root/tsw440-acceptance')/run
checkout=root/'checkout'
def trusted(path,directory=False):
    for p in (path,*path.parents):
        s=p.lstat();need(s.st_uid==0 and not stat.S_ISLNK(s.st_mode) and not s.st_mode&0o022)
    need(path.is_dir() if directory else path.is_file())
def private(path,limit=65536):
    trusted(path);s=path.stat();need(stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and s.st_size<=limit)
    return path.read_bytes()
def unique(pairs):
    result={}
    for key,value in pairs:need(key not in result);result[key]=value
    return result
def strict(raw):return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:need(False))
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
trusted(root,True);trusted(checkout,True);trusted(checkout/'.git',True)
env={'LC_ALL':'C','PATH':'/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/root','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_OPTIONAL_LOCKS':'0'}
def git(args,exits=(0,),directory=checkout):
    p=subprocess.run(['/usr/bin/git','--no-optional-locks','-C',str(directory),'-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','-c','core.untrackedCache=false',*args],env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=10)
    need(p.returncode in exits and not p.stderr and len(p.stdout)<=1048576);return p.stdout
need(git(['config','--local','--includes','--null','--get-regexp',r'^filter\.'],(0,1))==b'')
def verify_qualification_helpers():
    # Verify every executable helper before its transitive imports execute.
    directory=checkout/'modules/tsw_core/tools/linux/qualification';trusted(directory,True)
    helpers=list(directory.glob('*.py'));need(0<len(helpers)<=128)
    for helper in helpers:
        trusted(helper);content=helper.read_bytes();need(len(content)<=1048576 and content==git(['show',source+':modules/tsw_core/tools/linux/qualification/'+helper.name]))
    sys.path.insert(0,str(directory))
def admitted_product_revision(qualification,product,parents,changes):
    need(re.fullmatch('[0-9a-f]{40}',qualification) and re.fullmatch('[0-9a-f]{40}',product))
    if product!=qualification:need(parents==[product,qualification] and changes==['modules/tsw_core/infra/config/incus-profile-capabilities.json'])
    return product
def validate_promoted_capability():
    capraw=git(['show',product_source+':modules/tsw_core/infra/config/incus-profile-capabilities.json']);need(len(capraw)<=65536)
    matrix=strict(capraw);need(isinstance(matrix,dict) and set(matrix)=={'schema_version','capability','admitted_versions'} and type(matrix['schema_version']) is int and matrix['schema_version']==1 and matrix['capability']=='installation-scoped-incus-manager-profile' and isinstance(matrix['admitted_versions'],list) and len(matrix['admitted_versions'])==1)
    entry=matrix['admitted_versions'][0];need(isinstance(entry,dict) and set(entry)=={'client_version','server_version','fixture_source_revision','fixture_sha256'} and entry['client_version']==entry['server_version']=='6.0.5' and re.fullmatch('[0-9a-f]{40}',entry['fixture_source_revision']) and re.fullmatch('[0-9a-f]{64}',entry['fixture_sha256']))
    verify_qualification_helpers()
    from preserving_product_acceptance import validate_host_artifacts
    proof=strict(private(root/'both-host-profile-capability.json'))
    artifacts={host:private(root/('profile-capability-'+host+'.json'),8388608) for host in ('native_linux','wsl2')}
    sources=validate_host_artifacts(proof,hashlib.sha256(capraw).hexdigest(),entry['fixture_sha256'],artifacts)
    for revision in (product_source,entry['fixture_source_revision'],*sources.values()):need(hashlib.sha256(git(['show',revision+':modules/tsw_core/tools/linux/qualification/incus_profile_listener_fixture.py'])).hexdigest()==entry['fixture_sha256'])
    return capraw
path=root/('preparation.json' if kind=='prepared' else 'new-case-stop.json');raw=private(path);need(hashlib.sha256(raw).hexdigest()==expected);receipt=strict(raw)
need(type(receipt['schema_version']) is int and receipt['schema_version']==1 and receipt['run_id']==run and isinstance(receipt['source_commit'],str))
product_source=source if kind=='prepared' else receipt['source_commit']
need(re.fullmatch('[0-9a-f]{40}',product_source))
need(git(['rev-parse','HEAD']).decode().strip()==source and git(['status','--porcelain=v1','--untracked-files=all'])==b'')
parents=git(['rev-list','--parents','-n','1',product_source]).decode().split() if product_source!=source else []
changes=git(['diff','--name-only','--no-renames',source,product_source,'--']).decode().splitlines() if product_source!=source else []
admitted_product_revision(source,product_source,parents,changes)
import base64
pins=strict(base64.b64decode(encoded));need(set(pins)=={'native_runtime_inventory.py','native_lxd_snap_provenance.py'})
for name,sha in pins.items():
    p=checkout/'modules/tsw_core/tools/linux/qualification'/name;trusted(p);raw=p.read_bytes();need(len(raw)<=1048576 and hashlib.sha256(raw).hexdigest()==sha and raw==git(['show',source+':modules/tsw_core/tools/linux/qualification/'+name]))
sys.path.insert(0,str(checkout/'modules/tsw_core/tools/linux/qualification'));import native_runtime_inventory as n
r=n.Runner()
def binding():
    row=n._systemctl_show(n.Runner(),'incus.service');need(row['load_state']=='loaded' and row['active_state']=='active' and row['sub_state']=='running')
    need(n._resolve_executable(n.Runner(),row)==('incus_system','system:incus'))
    sock='/var/lib/incus/unix.socket';need(n._endpoint(n.Runner(),sock,unit='incus.service')[1]);n._require_full_local_access(sock,incus=True)
    return sock
def query(uri):
    sock=binding();env={'LC_ALL':'C','PATH':n.ENV_BASE['PATH'],'INCUS_SOCKET':sock}
    raw=r.run(['/usr/bin/incus','--force-local','query','--request','GET','--raw',uri],env=env,command_id='guest_switch_read',safe_args=[])[1]
    value=strict(raw);need(set(value)=={'type','status','status_code','operation','error_code','error','metadata'} and value['type']=='sync' and value['status']=='Success' and value['status_code']==200 and value['error_code']==0 and value['operation']=='' and value['error']=='')
    return value['metadata']
need(receipt['source_commit']==product_source)
sock=binding();version=r.run(['/usr/bin/incus','--version'],env={'LC_ALL':'C','PATH':n.ENV_BASE['PATH'],'INCUS_SOCKET':sock},command_id='guest_switch_version')[1].decode().strip();need(version=='6.0.5')
metadata=n._read_server_root(n.Runner(),['/usr/bin/incus','--force-local'],{'LC_ALL':'C','PATH':n.ENV_BASE['PATH'],'INCUS_SOCKET':sock},binding,incus=True,cli_version='6.0.5',phase='initial')
need(metadata['server_version']=='6.0.5')
def case_ledger_names(ledger,run,source):
    need(isinstance(ledger,dict) and set(ledger)=={'schema_version','run_id','source_commit','cases'} and type(ledger['schema_version']) is int and ledger['schema_version'] in (1,2) and ledger['run_id']==run and ledger['source_commit']==source and isinstance(ledger['cases'],list))
    recipes=('minimal', 'swagger-internal', 'swagger-published', 'swagger-traefik-swarm', 'swagger-traefik-portainer', 'swagger-add-traefik', 'full-swarm', 'full-portainer', 'upgrade-swagger-swarm', 'upgrade-traefik-swarm', 'upgrade-batch-default-swarm-published', 'upgrade-batch-default-swarm-internal', 'upgrade-batch-default-portainer-published', 'upgrade-batch-default-portainer-internal', 'upgrade-batch-service-access-swarm-published', 'upgrade-batch-service-access-swarm-internal', 'upgrade-batch-service-access-portainer-published', 'upgrade-batch-service-access-portainer-internal', 'recover-batch-swarm', 'recover-batch-portainer', 'upgrade-portainer', 'recover-portainer', 'upgrade-product-v1', 'recover-product-v1')
    recipes=recipes[:8] if ledger['schema_version']==1 else recipes
    need(0<len(ledger['cases'])<=len(recipes))
    seen=[]
    for row in ledger['cases']:
        need(isinstance(row,dict) and set(row)=={'case','outcome_sha256'} and row['case'] in recipes and isinstance(row['outcome_sha256'],str) and re.fullmatch('[0-9a-f]{64}',row['outcome_sha256']))
        seen.append(recipes.index(row['case']))
    need(seen==sorted(set(seen)))
    return recipes
def case_ledger_directory_names(ledger,names,recipes):
    need(isinstance(names,list) and len(names)<=len(recipes) and all(type(name) is str and name in recipes for name in names) and len(set(names))==len(names))
    need(set(names)=={row['case'] for row in ledger['cases']})
def verify_case_checkout(case_name,capraw):
    casecheckout=root/'cases'/case_name/'checkout';trusted(casecheckout,True);trusted(casecheckout/'.git',True)
    need(git(['config','--local','--includes','--null','--get-regexp',r'^filter\.'],(0,1),casecheckout)==b'')
    need(git(['rev-parse','HEAD'],directory=casecheckout).decode().strip()==product_source and git(['status','--porcelain=v1','--untracked-files=all'],directory=casecheckout)==b'')
    cap=casecheckout/'modules/tsw_core/infra/config/incus-profile-capabilities.json';trusted(cap);need(cap.read_bytes()==capraw)
def case_requires_checkout(outcome,effect_markers,child_intents):
    if outcome['status'] not in ('CASE_NOT_EXECUTED','CASE_NOT_IMPLEMENTED'):return True
    need(set(outcome)=={'status','run_id','source_commit','case','epic_complete'} and outcome['epic_complete'] is False and not effect_markers)
    for row in child_intents:
        need(isinstance(row,dict) and set(row)=={'argv_sha256','timeout','public'} and type(row['public']) is bool and isinstance(row['argv_sha256'],str) and re.fullmatch('[0-9a-f]{64}',row['argv_sha256']) and type(row['timeout']) is int and row['timeout']>0)
    # A successful prepare can already run the real public --preview. That is
    # a source claim requiring the normal clean checkout, not the absent-source exception.
    return any(row['public'] for row in child_intents)
if kind=='prepared':
    need(set(receipt)=={'schema_version','run_id','source_commit','kind','package_versions','python_version'} and receipt['kind']=='NEW_GUEST_PREPARATION')
    versions=subprocess.run(['/usr/bin/dpkg-query','--show','--showformat=${Package}=${Version}\n','incus','incus-base','incus-client'],env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=10)
    need(versions.returncode==0 and not versions.stderr and set(versions.stdout.decode().splitlines())=={'incus=6.0.5-8','incus-base=6.0.5-8','incus-client=6.0.5-8'} and set(receipt['package_versions'])=={'incus','incus-base','incus-client'} and all(v=='6.0.5-8' for v in receipt['package_versions'].values()))
    py=checkout/'.venv/bin/python';trusted(checkout/'.venv',True);trusted(checkout/'.venv/bin',True);need(py.exists());trusted(py.resolve())
    versions={}
    for name in ('requirements.lock','requirements.build.lock'):
        path=checkout/name;trusted(path);content=path.read_bytes();need(len(content)<=1048576 and content==git(['show',source+':'+name]))
        for line in content.decode().splitlines():
            match=re.fullmatch(r'([A-Za-z0-9_.-]+)==([^ \\]+) *\\?',line)
            if match:
                package,version=match.groups();need(package not in versions);versions[package]=version
    need(len(versions)>=10)
    program='import sys,json,importlib.metadata as m; p=json.loads(sys.argv[1]); assert all(m.version(k)==v for k,v in p.items()); import pydantic,yaml,requests,ruamel.yaml; print(".".join(map(str,sys.version_info[:3])))'
    probe=subprocess.run([str(py),'-I','-c',program,json.dumps(versions)],env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=10)
    need(probe.returncode==0 and not probe.stderr and probe.stdout.decode().strip()==receipt['python_version'] and tuple(map(int,receipt['python_version'].split('.'))) >= (3,12))
    status='NEW_GUEST_PREPARED'
else:
    need(kind=='stopped' and set(receipt)=={'schema_version','run_id','source_commit','kind','case_journal_sha256','machine_id_sha256','boot_id_sha256'} and receipt['kind']=='OWNED_CASES_DISPOSED')
    ledgerraw=private(root/'product-case-ledger.json');need(hashlib.sha256(ledgerraw).hexdigest()==receipt['case_journal_sha256']);ledger=strict(ledgerraw)
    if product_source!=source:
        # The one changed tracked asset must carry the actual paired admission;
        # unchanged code does not turn a matrix edit into qualification evidence.
        capraw=validate_promoted_capability()
    recipes=case_ledger_names(ledger,run,product_source)
    declared=list((root/'cases').iterdir());need(len(declared)<=len(recipes))
    need(all(p.is_dir() and not p.is_symlink() for p in declared));case_ledger_directory_names(ledger,[p.name for p in declared],recipes)
    seen=[]
    for case in ledger['cases']:
        need(set(case)=={'case','outcome_sha256'} and case['case'] in recipes and re.fullmatch('[0-9a-f]{64}',case['outcome_sha256']))
        seen.append(recipes.index(case['case']));journal=root/'cases'/case['case']/'journal';trusted(journal,True)
        files=list(journal.glob('outcome-*.json'));need(0<len(files)<=64);matches=0;matched=None
        for file in files:
            need(re.fullmatch(r'outcome-[0-9a-f]{32}\.json',file.name));content=private(file)
            if hashlib.sha256(content).hexdigest()==case['outcome_sha256']:
                actual=strict(content)
                need(actual.get('run_id')==run and actual.get('source_commit')==product_source and actual.get('case')==case['case'] and actual.get('status') in ('CASE_PASS_DISPOSED','CASE_FAILED_DISPOSED','CASE_RECOVERED','CASE_NOT_EXECUTED','CASE_NOT_EXERCISED','CASE_NOT_IMPLEMENTED'))
                matches+=1;matched=actual
        need(matches==1 and matched is not None)
        intents=list(journal.glob('child-*-intent.json'));need(len(intents)<=1024)
        for intent in intents:
            stem=intent.name.removesuffix('-intent.json');pidfile=journal/(stem+'-pid.json')
            if not pidfile.exists():
                refused=journal/(stem+'-launch-refused.json');need(refused.exists() and strict(private(refused))=={'released':False});continue
            child=strict(private(pidfile));need(set(child)=={'pid','start_time'} and type(child['pid']) is int and child['pid']>1 and type(child['start_time']) is int)
            try:os.killpg(child['pid'],0)
            except ProcessLookupError:pass
            else:need(False)
        if product_source!=source:
            effects=list(journal.glob('execution-intent-*.json'))+list(journal.glob('engine-recovery-started.json'))+list(journal.glob('disposal-intent.json'))
            unexecuted=matched['status'] in ('CASE_NOT_EXECUTED','CASE_NOT_IMPLEMENTED')
            child_rows=[strict(private(p)) for p in intents] if unexecuted else []
            if case_requires_checkout(matched,effects,child_rows):
                verify_case_checkout(case['case'],capraw)
    need(seen==sorted(set(seen)))
    projects=query('/1.0/projects?recursion=1');need(isinstance(projects,list) and len(projects)==1 and projects[0]['name']=='default')
    need(query('/1.0/instances?recursion=1&project=default')==[])
    profiles=query('/1.0/profiles?recursion=1&project=default');need(isinstance(profiles,list) and len(profiles)<=128 and all(isinstance(x,dict) and not x['name'].startswith('tsw-manager-') for x in profiles))
    pools=query('/1.0/storage-pools?recursion=1');need(isinstance(pools,list) and len(pools)<=16)
    for pool in pools:
        need(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.+-]{0,62}',pool['name']))
        volumes=query('/1.0/storage-pools/'+pool['name']+'/volumes?recursion=1&project=default')
        need(isinstance(volumes,list) and len(volumes)<=2048 and all(isinstance(x,dict) and x['type'] not in {'container','virtual-machine'} and '/' not in x['name'] for x in volumes))
    operations=query('/1.0/operations?recursion=1&all-projects=true');need(isinstance(operations,dict) and all(isinstance(v,list) and not v for v in operations.values()))
    pids=[x for x in Path('/proc').iterdir() if x.name.isdigit()];need(len(pids)<=4096)
    for pid in pids:
        if int(pid.name)==os.getpid():continue
        try:
            with (pid/'cmdline').open('rb') as stream:cmd=stream.read(65537)
        except FileNotFoundError:continue
        need(len(cmd)<=65536);args=[x.decode('utf-8','strict') for x in cmd.split(b'\0') if x]
        need(not any(x.endswith(('/wsl_product_acceptance.py','/product_upgrade_cases.py')) or x in {'pytest','unittest','tiny_swarm_world'} for x in args))
    status='OWNED_CASES_DISPOSED'
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(str(UUID(boot))==boot)
machine=Path('/etc/machine-id').read_bytes().strip();need(re.fullmatch(b'[0-9a-f]{32}',machine))
bootsha=hashlib.sha256(boot.encode()).hexdigest();machinesha=hashlib.sha256(machine).hexdigest()
if receipt.get('kind')=='OWNED_CASES_DISPOSED':need(receipt['boot_id_sha256']==bootsha and receipt['machine_id_sha256']==machinesha)
binding();print(json.dumps({'status':status,'receipt_sha256':expected,'observation_sha256':digest(metadata),'qualification_source_commit':source,'product_source_commit':product_source,'boot_id_sha256':bootsha,'machine_id_sha256':machinesha},sort_keys=True,separators=(',',':')))
'@
}

function New-WslAcceptanceGuestSwitchProductionPorts($Scenario){
 Assert-WslSwitchScenario $Scenario
 Assert-WslSwitch ([Environment]::Is64BitProcess -and [Environment]::Is64BitOperatingSystem -and [Environment]::MachineName -ceq $Scenario.host) 'SWITCH_NATIVE_HOST'
 $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
 Assert-WslSwitch ([IO.Path]::GetFullPath($Scenario.bridge_scenario.source_root) -ceq $root) 'SWITCH_SOURCE_ROOT'
 # Verify every transitive preparation import before any of its code executes.
 $actor=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
 foreach($relative in Get-WslSwitchAssets){
  $path=Join-Path $root $relative;$item=Get-Item -LiteralPath $path -Force
  Assert-WslSwitch (!$item.PSIsContainer -and !($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -and $item.Length -le 2097152 -and
   (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $Scenario.pins.$relative) 'SWITCH_SOURCE_PIN'
  $parent=$item.Directory
  while($null -ne $parent -and $parent.FullName.Length -ge $root.Length){
   Assert-WslSwitch (!($parent.Attributes -band [IO.FileAttributes]::ReparsePoint) -and
    (Get-Acl -LiteralPath $parent.FullName).GetOwner([Security.Principal.SecurityIdentifier]).Value -ceq $actor) 'SWITCH_SOURCE_OWNER'
   $parent=$parent.Parent
  }
 }
 Import-Module (Join-Path $root 'modules/tsw_windows_wsl/bootstrap/preparation/Preparation.psm1') -Force -DisableNameChecking
 $prep=Get-Module Preparation
 . (Join-Path $root 'modules/tsw_windows_wsl/tools/qualification/wsl_acceptance_registration.ps1')
 . (Join-Path $root 'modules/tsw_windows_wsl/tools/qualification/wsl_acceptance_bridge_binding.ps1')
 Assert-AcceptanceRegistrationScenario (& $prep {param($v) ConvertTo-PreparationHashtable $v} $Scenario.registration_scenario)
 Assert-WslBindingScenario $Scenario.bridge_scenario
 foreach($relative in @($Scenario.bridge_scenario.pins.PSObject.Properties.Name)){
  Assert-WslSwitch ($Scenario.bridge_scenario.pins.$relative -ceq $Scenario.pins.$relative) 'SWITCH_BRIDGE_PINS'}
 $defs=@{}
 foreach($name in @('Get-WslSwitchCanonical','Get-WslSwitchBytes','Get-WslSwitchRawHash','Get-WslSwitchHash','Assert-WslSwitch','Assert-WslSwitchFields',
 'Assert-WslSwitchRunning','Assert-WslSwitchResetBoundary','Get-WslSwitchAssets','Get-WslSwitchSeconds','Assert-WslSwitchBookmark','New-WslSwitchBookmark',
 'Assert-WslSwitchScenario','Get-WslSwitchOriginalContext','Assert-WslSwitchWindow','Get-WslSwitchOriginalStageProbe','Get-WslSwitchOriginalWitnessProbe','Get-WslSwitchOriginalAdapterProbe','Assert-AcceptanceRegistrationSourceView','Get-WslSwitchOriginalProbe','Get-WslSwitchBootProbe','Get-WslSwitchNetworkProbe','Get-WslSwitchNewProof','Get-WslSwitchFixtureProof','Get-WslBindingCanonical','Get-WslBindingBytes','Get-WslBindingRawHash',
 'Get-WslBindingHash','Assert-WslBindingFields','Assert-WslBindingScenario','Assert-WslBindingCertificate','Get-WslBindingPhaseSeconds','Assert-WslBindingApproval',
 'Invoke-WslAcceptanceBridgeBinding','New-WslAcceptanceBridgeProductionPorts')){$defs[$name]=(Get-Item ('Function:'+ $name)).ScriptBlock}
 $module=New-Module -Name ('Epic440GuestSwitch'+$Scenario.run_id) -ArgumentList $root,$Scenario,$prep,$defs -ScriptBlock {
  param($root,$scenario,$prep,$definitions)
  foreach($name in $definitions.Keys){Set-Item ('Function:script:'+ $name) $definitions[$name]}
  $script:s=$scenario;$script:sourceRoot=$root;$script:prep=$prep;$script:watch=$null;$script:seconds=0;$script:calls=0;$script:bytes=0
  $script:loaded=$null;$script:bridgePorts=$null
  $script:parent=Join-Path ([Environment]::GetFolderPath('CommonApplicationData')) 'TinySwarmWorld/maintenance'
  $windowSuffix=if($scenario.schema_version -ceq 3){'-'+$scenario.window.kind}else{''}
  $script:directory=Join-Path $script:parent ('acceptance-'+$scenario.run_id+$windowSuffix)
  $script:bookmark=Join-Path $script:directory 'guest-switch.json'
  $script:registration=Join-Path ([Environment]::GetFolderPath('CommonApplicationData')) ('TinySwarmWorld/Qualification/AcceptanceRegistrations/'+$scenario.run_id+'/registration.json')
  function CheckPath([string]$p){& $prep {param($p) Assert-PreparationLocalPath $p;Assert-PreparationEvidencePath $p} $p}
  function Remaining([int]$reserve=1){
   Assert-WslSwitch ($null -ne $watch -and $seconds-$watch.Elapsed.TotalSeconds -ge $reserve -and $script:calls -lt 256 -and $script:bytes -le 8388608) 'SWITCH_DEADLINE'
   return [int][Math]::Floor($seconds-$watch.Elapsed.TotalSeconds)
  }
  function Run([string]$file,[string[]]$arguments,[int]$timeout,[int]$limit=131072,[int[]]$exits=@(0)){
   [void](Remaining $timeout);$script:calls++
   $r=& $prep {param($f,$a,$t) Invoke-PreparationProcess $f $a $t} $file $arguments $timeout
   $out=[Text.Encoding]::UTF8.GetByteCount([string]$r.stdout);$err=[Text.Encoding]::UTF8.GetByteCount([string]$r.stderr);$script:bytes+=$out+$err
   Assert-WslSwitch ($r.exit_code -in $exits -and !$r.stderr -and $out -le $limit -and $script:bytes -le 8388608) 'SWITCH_CHILD_UNCERTAIN'
   return [string]$r.stdout
  }
  function NativeExecutable([string]$name){
   Assert-WslSwitch ($name -cin @('wsl.exe','powershell.exe')) 'SWITCH_NATIVE_EXECUTABLE'
   $path=& $prep {param($name) Get-PreparationExecutable $name} $name
   & $prep {param($p) Assert-PreparationLocalPath $p} $path
   $trusted=@('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
   $current=$path;$leaf=$true
   while($current){
    $item=Get-Item -LiteralPath $current -Force
    Assert-WslSwitch (!($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) 'SWITCH_NATIVE_REPARSE'
    $acl=Get-Acl -LiteralPath $current
    Assert-WslSwitch ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -cin $trusted) 'SWITCH_NATIVE_OWNER'
    $mask=[Security.AccessControl.FileSystemRights]::Delete -bor [Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles -bor [Security.AccessControl.FileSystemRights]::ChangePermissions -bor [Security.AccessControl.FileSystemRights]::TakeOwnership
    if($leaf){$mask=$mask -bor [Security.AccessControl.FileSystemRights]::WriteData -bor [Security.AccessControl.FileSystemRights]::AppendData -bor [Security.AccessControl.FileSystemRights]::WriteAttributes -bor [Security.AccessControl.FileSystemRights]::WriteExtendedAttributes}
    foreach($rule in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])){
     if(!($rule.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -and $rule.AccessControlType -eq 'Allow' -and
      ($rule.FileSystemRights -band $mask) -and $rule.IdentityReference.Value -cnotin ($trusted+@('S-1-3-0'))){throw 'SWITCH_NATIVE_ACL'}
    }
    $leaf=$false;$current=Split-Path -Parent $current
   }
   $sig=Get-AuthenticodeSignature -LiteralPath $path -ErrorAction Stop
   Assert-WslSwitch ($sig.Status -eq 'Valid' -and $sig.SignerCertificate.Subject -match '(?:^|,\s*)O=Microsoft Corporation(?:,|$)') 'SWITCH_NATIVE_SIGNATURE'
   return $path
  }
  function Wsl {return NativeExecutable 'wsl.exe'}
  function Source($s){
   [void](Remaining);Assert-WslSwitch ([Environment]::MachineName -ceq $s.host) 'SWITCH_HOST'
   $encoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($sourceRoot))
   $query=@'
$ErrorActionPreference='Stop';$WarningPreference='SilentlyContinue'
$r=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('@ROOT@'))
Import-Module (Join-Path $r 'modules/tsw_windows_wsl/bootstrap/preparation/Preparation.psm1') -Force -DisableNameChecking
$m=Get-Module Preparation;$o=@{RepositoryRoot=$r;QualificationRevision='@SOURCE@';ProbeTimeoutSeconds=15}
& $m {param($o) Get-PreparationSource $o} $o | ConvertTo-Json -Depth 20 -Compress
'@
   $query=$query.Replace('@ROOT@',$encoded).Replace('@SOURCE@',$s.source_commit)
   $ps=NativeExecutable 'powershell.exe'
   $wire=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($query))
   $text=Run $ps @('-NoProfile','-NonInteractive','-EncodedCommand',$wire) 60 2097152
   $proof=$text|ConvertFrom-Json -ErrorAction Stop
   Assert-WslSwitch ($proof.verified -eq $true -and $proof.clean -eq $true -and $proof.revision -ceq $s.source_commit) 'SWITCH_SOURCE'
   foreach($relative in Get-WslSwitchAssets){$p=Join-Path $sourceRoot $relative;CheckPath $p
    Assert-WslSwitch ((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $s.pins.$relative) 'SWITCH_SOURCE_PIN'}
   [void](Wsl);[void](Remaining)
  }
  function InitializeIdentity {
   if('Epic440SwitchFile' -as [type]){return}
   Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;using Microsoft.Win32.SafeHandles;
public static class Epic440SwitchFile {
 [StructLayout(LayoutKind.Sequential)] struct Info {public uint attr;public System.Runtime.InteropServices.ComTypes.FILETIME create,access,write;public uint volume,sizeHi,sizeLo,links,indexHi,indexLo;}
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern SafeFileHandle CreateFile(string p,uint access,uint share,IntPtr security,uint creation,uint flags,IntPtr template);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandle(SafeFileHandle h,out Info i);
 public static string Read(string p){using(var h=CreateFile(p,128,7,IntPtr.Zero,3,0x02200000,IntPtr.Zero)){Info i;if(h.IsInvalid||!GetFileInformationByHandle(h,out i)||(i.attr&1024)!=0||i.links!=1)throw new InvalidOperationException("SWITCH_VHD_HANDLE");return i.volume.ToString("x8")+":"+i.indexHi.ToString("x8")+i.indexLo.ToString("x8")+":"+i.attr.ToString("x8")+":"+i.links.ToString("x8");}}
}
'@
  }
  function ReadJson([string]$p,[int]$limit=131072){
   CheckPath $p;$item=Get-Item -LiteralPath $p -Force
   Assert-WslSwitch (!$item.PSIsContainer -and $item.Length -le $limit) 'SWITCH_FILE_BOUND'
   $raw=[IO.File]::ReadAllBytes($p);Assert-WslSwitch ($raw.Length -le $limit) 'SWITCH_FILE_BOUND'
   $v=([Text.UTF8Encoding]::new($false,$true)).GetString($raw)|ConvertFrom-Json -ErrorAction Stop
   return @{raw=$raw;value=(& $prep {param($v) ConvertTo-PreparationHashtable $v} $v)}
  }
  function RegistrationState {
   $r=ReadJson $registration
   if($s.schema_version -ceq 3){
    [void](Assert-AcceptanceRegistrationSourceView $s.window.source_view $s.registration_scenario $r.value $r.raw)
    Assert-WslSwitch ($s.window.source_view.source_commit -ceq $s.source_commit) 'SWITCH_REGISTRATION_SOURCE_VIEW'
   }
   Assert-WslSwitch ((Get-WslSwitchRawHash $r.raw) -ceq $s.registration_state_sha256 -and $r.value.stage -ceq 'registered' -and
    $r.value.scenario_sha256 -ceq (Get-WslSwitchHash $s.registration_scenario) -and $null -ne $r.value.receipt -and
    $r.value.receipt.name -ceq ('TSW-Q440-'+$s.run_id) -and $r.value.receipt.id.ToLowerInvariant() -ceq $s.bridge_scenario.new_guid -and
    (Get-WslSwitchHash $r.value.receipt.vhd_identity) -ceq $s.bridge_scenario.new_vhd_sha256) 'SWITCH_REGISTRATION_RECEIPT'
   return $r.value
  }
  function Observe($s){
   [void](Remaining);InitializeIdentity;$registrationState=RegistrationState
   $text=Run (Wsl) @('--list','--running','--quiet') 15 65536
   $running=@($text.Replace("`0",'') -split '\r?\n'|Where-Object{$_}|Sort-Object)
   Assert-WslSwitch ($running.Count -le 32 -and @($running|Select-Object -Unique).Count -eq $running.Count) 'SWITCH_RUNNING_LIST'
   $key=[Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Software\Microsoft\Windows\CurrentVersion\Lxss',$false)
   Assert-WslSwitch ($null -ne $key) 'SWITCH_REGISTRY'
   try{
    $rootValues=[ordered]@{};foreach($name in @($key.GetValueNames()|Sort-Object)){$rootValues[$name]=@([string]$key.GetValueKind($name),$key.GetValue($name))}
    $fullMatches=$true
    $rows=@(foreach($id in @($key.GetSubKeyNames()|Sort-Object)){
     Assert-WslSwitch ($id -cmatch '\A\{[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\}\z') 'SWITCH_REGISTRY_GUID'
     $entry=$key.OpenSubKey($id,$false);Assert-WslSwitch ($null -ne $entry) 'SWITCH_REGISTRY'
     try{
      $name=$entry.GetValue('DistributionName');$version=$entry.GetValue('Version')
      Assert-WslSwitch ($name -is [string] -and $name -and $version -is [int] -and $version -eq 2) 'SWITCH_REGISTRY'
      $values=[ordered]@{};$stable=[ordered]@{};foreach($v in @($entry.GetValueNames()|Sort-Object)){$value=@([string]$entry.GetValueKind($v),$entry.GetValue($v));$values[$v]=$value;if($v -cne 'State'){$stable[$v]=$value}}
      $base=[string]$entry.GetValue('BasePath');if($base.StartsWith('\\?\')){$base=$base.Substring(4)}
      $base=[IO.Path]::GetFullPath($base).TrimEnd('\');$disk=[string]$entry.GetValue('VhdFileName','ext4.vhdx')
      Assert-WslSwitch ($disk -cmatch '\A[A-Za-z0-9_.-]+\.vhdx\z') 'SWITCH_VHD_PATH'
      $path=Join-Path $base $disk;& $prep {param($p) Assert-PreparationLocalPath $p;Assert-PreparationSelectedVhdMetadata $p} $path
      [ordered]@{id=$id.ToLowerInvariant();name=$name;version=$version;values_sha256=(Get-WslSwitchHash $values);stable_values_sha256=(Get-WslSwitchHash $stable);
       base_sha256=(Get-WslSwitchHash $base);vhd_identity=([Epic440SwitchFile]::Read($path))}
     }finally{$entry.Dispose()}
    })
    Assert-WslSwitch ($rows.Count -eq 2 -and @($rows.name|Select-Object -Unique).Count -eq $rows.Count -and
     @($running|Where-Object{$_ -cnotin $rows.name}).Count -eq 0) 'SWITCH_REGISTRY_SET'
    $expected=@($registrationState.baseline.registrations)+@($registrationState.receipt)
    Assert-WslSwitch ($rows.Count -eq $expected.Count -and [string]$key.GetValue('DefaultDistribution') -ceq $registrationState.baseline.default) 'SWITCH_REGISTRATION_DRIFT'
    foreach($e in $expected){$matches=@($rows|Where-Object{$_.id -ceq $e.id.ToLowerInvariant()});Assert-WslSwitch ($matches.Count -eq 1) 'SWITCH_REGISTRATION_DRIFT'
     if($matches[0].values_sha256 -cne $e.values_sha256){$fullMatches=$false}
     foreach($field in @('name','version','base_sha256','vhd_identity')){Assert-WslSwitch ($matches[0].$field -ceq $e.$field) 'SWITCH_REGISTRATION_DRIFT'}}
    $original=@($rows|Where-Object{$_.id -ceq $s.bridge_scenario.original_guid})
    Assert-WslSwitch ($original.Count -eq 1 -and $original[0].name -ceq 'Ubuntu' -and (Get-WslSwitchHash $original[0].vhd_identity) -ceq $s.bridge_scenario.original_vhd_sha256) 'SWITCH_ORIGINAL_REGISTRATION'
    $stableRows=@($rows|ForEach-Object{[ordered]@{id=$_.id;name=$_.name;version=$_.version;values_sha256=$_.stable_values_sha256;base_sha256=$_.base_sha256;vhd_identity=$_.vhd_identity}})
    return @{running=$running;registration_count=$rows.Count;receipt_matches=$fullMatches;registrations_sha256=(Get-WslSwitchHash @($rootValues,$stableRows));default=$registrationState.baseline.default}
   }finally{$key.Dispose()}
  }
  function Linux([string]$who,[string]$code,[string[]]$arguments,[int]$timeout){
   $name=if($who -ceq 'original'){'Ubuntu'}elseif($who -ceq 'new'){'TSW-Q440-'+$s.run_id}else{throw 'SWITCH_TARGET'}
   # This method is never a CLI port. All callers select a fixed source literal.
   $json=Run (Wsl) (@('--distribution',$name,'--user','root','--exec','/usr/bin/python3','-I','-c',$code)+$arguments) $timeout
   $v=$json|ConvertFrom-Json -ErrorAction Stop
   return $v
  }
  function OriginalWindow([string]$kind,$s,$go){
   Assert-WslSwitchRunning (Observe $s) $s original
   $ctx=Get-WslSwitchOriginalContext $s
   $body=Get-WslSwitchBytes $ctx;$encoded=[Convert]::ToBase64String($body)
   $arguments=@($kind,'--context-base64',$encoded,'--expected-context-sha256',(Get-WslSwitchRawHash $body))
   if($kind -cin @('prepare','recover-prepare','quiesce','restore')){
    Assert-WslSwitch ($null -ne $go) 'SWITCH_ORIGINAL_APPROVAL_REQUIRED'
    $raw=Get-WslSwitchBytes $go
    $arguments+=@('--approval-base64',([Convert]::ToBase64String($raw)),'--expected-approval-sha256',(Get-WslSwitchRawHash $raw))
   }
   $proof=Linux original (Get-WslSwitchOriginalAdapterProbe) (@($s.run_id,$s.window.kind,$s.window.adapter_sha256)+$arguments) $(if($kind -cin @('quiesce','restore')){1300}else{350})
   Assert-WslSwitch ($proof.window_schema_version -eq 1 -and $proof.run_id -ceq $s.run_id -and
    $proof.window -ceq $s.window.kind -and $proof.context_sha256 -ceq (Get-WslSwitchRawHash $body) -and $proof.source_commit -ceq $s.source_commit) 'SWITCH_ORIGINAL_WINDOW_RECEIPT'
   return $proof
  }
  function StageOriginalSource($s,$go){
   Assert-WslSwitchRunning (Observe $s) $s original
   Source $s
   $relative='modules/tsw_core/tools/linux/qualification/wsl_original_runtime_window.py'
   $path=Join-Path $sourceRoot $relative;CheckPath $path
   $bytes=[IO.File]::ReadAllBytes($path)
   Assert-WslSwitch ($bytes.Length -le 131072 -and (Get-WslSwitchRawHash $bytes) -ceq $s.window.adapter_sha256) 'SWITCH_ORIGINAL_SOURCE_BYTES'
   # Membership is independently checked against the committed, fixed Git blob.
   $git=$null
   foreach($candidate in @((Join-Path ([Environment]::GetFolderPath('ProgramFiles')) 'Git/cmd/git.exe'),(Join-Path ([Environment]::GetFolderPath('ProgramFiles')) 'Git/bin/git.exe'))){if(Test-Path $candidate -PathType Leaf){$git=$candidate;break}}
   Assert-WslSwitch ($null -ne $git) 'SWITCH_GIT_REQUIRED'
   $trustedGit=@('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
   $current=$git;$leaf=$true
   while($current){
    $item=Get-Item $current -Force;Assert-WslSwitch (!($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) 'SWITCH_GIT_REPARSE'
    $acl=Get-Acl $current;Assert-WslSwitch ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -cin $trustedGit) 'SWITCH_GIT_OWNER'
    $mask=[Security.AccessControl.FileSystemRights]::Delete -bor [Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles -bor [Security.AccessControl.FileSystemRights]::ChangePermissions -bor [Security.AccessControl.FileSystemRights]::TakeOwnership
    if($leaf){$mask=$mask -bor [Security.AccessControl.FileSystemRights]::WriteData -bor [Security.AccessControl.FileSystemRights]::AppendData -bor [Security.AccessControl.FileSystemRights]::WriteAttributes -bor [Security.AccessControl.FileSystemRights]::WriteExtendedAttributes}
    foreach($rule in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])){if(!($rule.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -and $rule.AccessControlType -eq 'Allow' -and ($rule.FileSystemRights -band $mask) -and $rule.IdentityReference.Value -cnotin ($trustedGit+@('S-1-3-0'))){throw 'SWITCH_GIT_ACL'}}
    $leaf=$false;$current=Split-Path -Parent $current
   }
   $expected=Run $git @('--no-replace-objects','--no-optional-locks','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','-C',$sourceRoot,'rev-parse',($s.source_commit+':'+$relative)) 15 256
   $object=& $prep {param($raw) Get-PreparationGitObjectId 'blob' $raw} $bytes
   Assert-WslSwitch ($expected.Trim() -ceq $object) 'SWITCH_ORIGINAL_GIT_BLOB'
   $raw=Get-WslSwitchBytes $go;$go64=[Convert]::ToBase64String($raw)
   $count=[int][Math]::Ceiling($bytes.Length/6144.0)
   for($index=0;$index -le $count;$index++){
    Source $s
    $data=''
    if($index -lt $count){$length=[Math]::Min(6144,$bytes.Length-$index*6144);$piece=New-Object byte[] $length;[Array]::Copy($bytes,$index*6144,$piece,0,$length);$data=[Convert]::ToBase64String($piece)}
    $proof=Linux original (Get-WslSwitchOriginalStageProbe) @($s.run_id,$s.window.kind,$s.source_commit,$s.window.adapter_sha256,
     (Get-WslSwitchHash $s),(Get-WslSwitchHash (Get-WslSwitchOriginalContext $s)),$s.original_proposal_sha256,
     $s.original_machine_sha256,([Convert]::ToBase64String((Get-WslSwitchBytes (Get-WslSwitchOriginalContext $s)))),$go64,(Get-WslSwitchRawHash $raw),[string]$index,[string]$count,$data) 30
    Assert-WslSwitch ($proof.status -ceq $(if($index -eq $count){'ORIGINAL_SOURCE_STAGED'}else{'ORIGINAL_SOURCE_PART_STAGED'})) 'SWITCH_ORIGINAL_STAGE_RESULT'
   }
   return @{status='ORIGINAL_SOURCE_STAGED';adapter_sha256=$s.window.adapter_sha256}
  }

  function Original([string]$kind,$s,$go=$null){
   if($s.schema_version -ceq 3){return OriginalWindow $kind $s $go}
   Assert-WslSwitchRunning (Observe $s) $s original
   if($kind -cin @('quiescent','restored')){
    $r=Linux original (Get-WslSwitchOriginalProbe) @($kind,$s.original_machine_sha256,$s.original_proposal_sha256) 300
    Assert-WslSwitch ($r.status -ceq $(if($kind -ceq 'restored'){'ORIGINAL_RESTORED'}else{'ORIGINAL_QUIESCENT'}) -and $r.proposal_sha256 -ceq $s.original_proposal_sha256) 'SWITCH_ORIGINAL_PROOF';return $r
   }
   Assert-WslSwitch ($kind -cin @('quiesce','restore')) 'SWITCH_ORIGINAL_MODE'
   # Verify immutable driver before invoking its unchanged canonical CLI.
   [void](Linux original @'
import hashlib,stat
from pathlib import Path
p=Path('/root/tsw440-wsl-r7-20261108/epic440-wsl-runtime-window.py')
s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and s.st_size<=1048576 and hashlib.sha256(p.read_bytes()).hexdigest()=='fcf16059dced9a3ed07ea54e1d346e7b67726cfe873de2849b58a202519962bd'
print('{"status":"IMMUTABLE_DRIVER_VERIFIED"}')
'@ @() 10)
   $text=Run (Wsl) @('--distribution','Ubuntu','--user','root','--exec','/usr/bin/python3','-I',
    '/root/tsw440-wsl-r7-20261108/epic440-wsl-runtime-window.py',$kind,'--machine-id-sha256',$s.original_machine_sha256) 650
   return $text|ConvertFrom-Json -ErrorAction Stop
  }
  function NewProof([string]$kind,[string]$hash){
   Assert-WslSwitchRunning (Observe $s) $s new
   Assert-WslSwitch ($hash -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_PROOF_HASH'
   $pins=[Convert]::ToBase64String((Get-WslSwitchBytes $s.linux_pins))
   $proof=Linux new (Get-WslSwitchNewProof) @($kind,$s.run_id,$s.source_commit,$hash,$pins) 240
   Assert-WslSwitch (($kind -ceq 'prepared' -and $proof.status -ceq 'NEW_GUEST_PREPARED' -or $kind -ceq 'stopped' -and $proof.status -ceq 'OWNED_CASES_DISPOSED') -and $proof.receipt_sha256 -ceq $hash) 'SWITCH_NEW_PROOF'
   return $proof
  }
  function Load($s){
   Assert-WslSwitch (Test-Path -LiteralPath $parent -PathType Container) 'SWITCH_PRIVATE_PARENT_REQUIRED';CheckPath $parent
   if(!(Test-Path -LiteralPath $bookmark)){Assert-WslSwitch (!(Test-Path -LiteralPath $directory)) 'SWITCH_BOOKMARK_MISSING';$script:loaded=$null;return $null}
   $r=ReadJson $bookmark 16384;Assert-WslSwitch ([Convert]::ToBase64String((Get-WslSwitchBytes $r.value)) -ceq [Convert]::ToBase64String($r.raw)) 'SWITCH_BOOKMARK_NONCANONICAL';$script:loaded=Get-WslSwitchRawHash $r.raw;Assert-WslSwitchBookmark $r.value $s;return $r.value
  }
  function Save($s,$state){
   Assert-WslSwitchBookmark $state $s;CheckPath $parent
   if(!(Test-Path -LiteralPath $directory)){
    Assert-WslSwitch ($null -eq $script:loaded) 'SWITCH_BOOKMARK_CAS';[void](New-Item -ItemType Directory -Path $directory -ErrorAction Stop)
    $acl=[Security.AccessControl.DirectorySecurity]::new();$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl.SetOwner($sid);$acl.SetAccessRuleProtection($true,$false)
    foreach($principal in @($sid.Value,'S-1-5-18','S-1-5-32-544')){[void]$acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($principal),'FullControl','ContainerInherit,ObjectInherit','None','Allow'))}
    [IO.Directory]::SetAccessControl($directory,$acl)
   }
   CheckPath $directory
   if($s.schema_version -ceq 3){
    $scenarioFile=Join-Path $directory 'scenario.json';$scenarioBytes=Get-WslSwitchBytes $s
    if(Test-Path $scenarioFile){Assert-WslSwitch ([Convert]::ToBase64String([IO.File]::ReadAllBytes($scenarioFile)) -ceq [Convert]::ToBase64String($scenarioBytes)) 'SWITCH_SCENARIO_CAS'}else{
     $f=[IO.FileStream]::new($scenarioFile,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
     try{& $prep {param($p) Set-PreparationPrivateAcl $p} $scenarioFile;$f.Write($scenarioBytes,0,$scenarioBytes.Length);$f.Flush($true)}finally{$f.Dispose()}
    }
   }
   if(Test-Path -LiteralPath $bookmark){$r=ReadJson $bookmark 16384;Assert-WslSwitch ((Get-WslSwitchRawHash $r.raw) -ceq $script:loaded) 'SWITCH_BOOKMARK_CAS'}else{Assert-WslSwitch ($null -eq $script:loaded) 'SWITCH_BOOKMARK_CAS'}
   $raw=Get-WslSwitchBytes $state;Assert-WslSwitch ($raw.Length -le 16384) 'SWITCH_BOOKMARK_BOUND'
   $tmp=Join-Path $directory ('guest-switch-'+[Guid]::NewGuid().ToString('N')+'.tmp')
   try{
    $stream=[IO.FileStream]::new($tmp,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try{& $prep {param($p) Set-PreparationPrivateAcl $p} $tmp;$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}
    if(Test-Path -LiteralPath $bookmark){
     if($s.schema_version -ceq 3){
      $previous=[IO.File]::ReadAllBytes($bookmark);$oldHash=Get-WslSwitchRawHash $previous
      $history=Join-Path $directory ('previous-'+$oldHash+'.json')
      if(Test-Path $history){Assert-WslSwitch ([Convert]::ToBase64String([IO.File]::ReadAllBytes($history)) -ceq [Convert]::ToBase64String($previous)) 'SWITCH_HISTORY_CAS'}else{
       Assert-WslSwitch (@(Get-ChildItem $directory -Filter 'previous-*.json').Count -lt 256) 'SWITCH_HISTORY_BOUND'
       $h=[IO.FileStream]::new($history,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
       try{& $prep {param($p) Set-PreparationPrivateAcl $p} $history;$h.Write($previous,0,$previous.Length);$h.Flush($true)}finally{$h.Dispose()}
      }
     }
     [IO.File]::Replace($tmp,$bookmark,[System.Management.Automation.Language.NullString]::Value)
    }else{[IO.File]::Move($tmp,$bookmark)}
    $script:loaded=Get-WslSwitchRawHash $raw;return $state
   }finally{if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Force -ErrorAction Stop}}
  }
  $ports=@{}
  $ports.Begin={param($phase) $script:watch=[Diagnostics.Stopwatch]::StartNew();$script:seconds=Get-WslSwitchSeconds $phase;$script:calls=0;$script:bytes=0}
  $ports.Clock={return [DateTimeOffset]::UtcNow}
  $ports.Source={param($s) Source $s}
  $ports.Observe={param($s) Observe $s}
  $ports.Load={param($s) Load $s}
  $ports.Save={param($s,$v) Save $s $v}
  $ports.Registration={param($s) $r=RegistrationState;Assert-WslSwitchRunning (Observe $s) $s original
   Assert-WslSwitch ($r.receipt.running -eq $false) 'SWITCH_INITIAL_REGISTRATION_NOT_STOPPED';return $r.scenario_sha256}
  $ports.Lock={$m=[Threading.Mutex]::new($false,'Global\TinySwarmWorldEpic440GuestSwitch');if(!$m.WaitOne(0)){$m.Dispose();throw 'SWITCH_LOCKED'};return $m}
  $ports.Unlock={param($m) try{$m.ReleaseMutex()}finally{$m.Dispose()}}
  $ports.Original={param($kind,$s,$go=$null) Original $kind $s $go}
  $ports.StageOriginal={param($s,$go) StageOriginalSource $s $go}
  $ports.OriginalWitness={param($s) Assert-WslSwitchRunning (Observe $s) $s original;Linux original (Get-WslSwitchOriginalWitnessProbe) @($s.original_machine_sha256,[string]$s.window.legacy_lock_inode) 30}
  $ports.Parent={param($s)
   $folder=Join-Path $parent ('acceptance-'+$s.run_id+'-fixture')
   $saved=ReadJson (Join-Path $folder 'scenario.json') 131072
   Assert-WslSwitch ([Convert]::ToBase64String((Get-WslSwitchBytes $saved.value)) -ceq [Convert]::ToBase64String($saved.raw)) 'SWITCH_PARENT_NONCANONICAL'
   $spec=$saved.value;Assert-WslSwitchScenario $spec
   Assert-WslSwitch ($spec.schema_version -ceq 3 -and $spec.window.kind -ceq 'fixture' -and $spec.run_id -ceq $s.run_id -and $spec.source_commit -ceq $s.source_commit -and $spec.registration_state_sha256 -ceq $s.registration_state_sha256 -and $spec.original_machine_sha256 -ceq $s.original_machine_sha256) 'SWITCH_PARENT_IDENTITY'
   foreach($key in @('original_guid','new_guid','original_vhd_sha256','new_vhd_sha256')){Assert-WslSwitch ($spec.bridge_scenario.$key -ceq $s.bridge_scenario.$key) 'SWITCH_PARENT_IDENTITY'}
   $old=ReadJson (Join-Path $folder 'guest-switch.json') 16384
   Assert-WslSwitch ([Convert]::ToBase64String((Get-WslSwitchBytes $old.value)) -ceq [Convert]::ToBase64String($old.raw)) 'SWITCH_PARENT_NONCANONICAL'
   Assert-WslSwitchBookmark $old.value $spec
   Assert-WslSwitch ($old.value.stage -ceq 'restored' -and !$old.value.pending) 'SWITCH_PARENT_UNRESTORED'
   $owner=New-WslAcceptanceBridgeProductionPorts $s.bridge_scenario;$update=$null;$reconcile=$null
   try{
    & $owner.Begin 'Recover' | Out-Null;$update=& $owner.Lock 'Global\TinySwarmWorldWslBridgeServiceUpdate';$reconcile=& $owner.Lock 'Global\TinySwarmWorldWslBridgeReconcile'
    $capsule=& $owner.Parent
    if($s.window.kind -ceq 'product'){Assert-WslSwitch ((Get-WslSwitchHash $old.value) -ceq $s.window.parent_switch_sha256 -and (Get-WslSwitchHash $capsule) -ceq $s.window.parent_bridge_sha256) 'SWITCH_PARENT_HASH'}
    return @{switch=$old.value;bridge=$capsule}
   }finally{if($null -ne $reconcile){& $owner.Unlock $reconcile | Out-Null};if($null -ne $update){& $owner.Unlock $update | Out-Null}}
  }
  $ports.BridgeOutcome={param($s)
   Assert-WslSwitchRunning (Observe $s) $s new
   $owner=New-WslAcceptanceBridgeProductionPorts $s.bridge_scenario;$update=$null;$reconcile=$null
   try{
    & $owner.Begin 'Recover' | Out-Null;$update=& $owner.Lock 'Global\TinySwarmWorldWslBridgeServiceUpdate';$reconcile=& $owner.Lock 'Global\TinySwarmWorldWslBridgeReconcile'
    return & $owner.Outcome
   }finally{if($null -ne $reconcile){& $owner.Unlock $reconcile | Out-Null};if($null -ne $update){& $owner.Unlock $update | Out-Null}}
  }
  $ports.OriginalBridge={param($s)
   Assert-WslSwitchRunning (Observe $s) $s original
   $owner=New-WslAcceptanceBridgeProductionPorts $s.bridge_scenario;$update=$null;$reconcile=$null
   try{
    & $owner.Begin 'OriginalRestoredBoundary' | Out-Null;$update=& $owner.Lock 'Global\TinySwarmWorldWslBridgeServiceUpdate';$reconcile=& $owner.Lock 'Global\TinySwarmWorldWslBridgeReconcile'
    return & $owner.Observe 'OriginalRestoredBoundary'
   }finally{if($null -ne $reconcile){& $owner.Unlock $reconcile | Out-Null};if($null -ne $update){& $owner.Unlock $update | Out-Null}}
  }
  $ports.BridgeStopped={param($s)
   $owner=New-WslAcceptanceBridgeProductionPorts $s.bridge_scenario;$update=$null;$reconcile=$null
   try{
    & $owner.Begin 'Recover' | Out-Null;$update=& $owner.Lock 'Global\TinySwarmWorldWslBridgeServiceUpdate';$reconcile=& $owner.Lock 'Global\TinySwarmWorldWslBridgeReconcile'
    $owned=& $owner.Observe 'Recover';& $owner.Stopped 'ResetBoundary' | Out-Null
    Assert-WslSwitch ($owned.payload.status -ceq 'Stopped') 'SWITCH_RECOVERY_BRIDGE_REQUIRED';return $owned
   }finally{if($null -ne $reconcile){& $owner.Unlock $reconcile | Out-Null};if($null -ne $update){& $owner.Unlock $update | Out-Null}}
  }
  $ports.Bridge={param($phase,$s,$go)
   Assert-WslSwitch ($phase -cin @('StopOriginal','Bind','StageRestore','ResumeOriginal','Recover')) 'SWITCH_BRIDGE_PHASE'
   $p=New-WslAcceptanceBridgeProductionPorts $s.bridge_scenario
   [void](Remaining (Get-WslBindingPhaseSeconds $phase))
   $r=Invoke-WslAcceptanceBridgeBinding $s.bridge_scenario $phase $go $p
   [void](Remaining);return $r
  }
  $ports.Terminate={param($who,$s)
   Assert-WslSwitch ($who -cin @('original','new')) 'SWITCH_TARGET';Assert-WslSwitchRunning (Observe $s) $s $who
   $name=if($who -ceq 'original'){'Ubuntu'}else{'TSW-Q440-'+$s.run_id}
   [void](Run (Wsl) @('--terminate',$name) 30 65536)
  }
  $ports.Start={param($who,$s)
   Assert-WslSwitch ($who -cin @('original','new')) 'SWITCH_TARGET';Assert-WslSwitchRunning (Observe $s) $s none
   $name=if($who -ceq 'original'){'Ubuntu'}else{'TSW-Q440-'+$s.run_id}
   [void](Run (Wsl) @('--distribution',$name,'--user','root','--exec','/bin/true') 30 65536)
  }
  $ports.Network={param($s)
   Assert-WslSwitchRunning (Observe $s) $s new
   # One fixed observation. Missing prerequisites/residue require separate
   # preparation and an explicit phase resume; never autoload or delete here.
   $text=Run (Wsl) @('--distribution',('TSW-Q440-'+$s.run_id),'--user','root','--exec','/usr/bin/python3','-I','-c',(Get-WslSwitchNetworkProbe)) 15 131072 @(0,2)
   return $text|ConvertFrom-Json -ErrorAction Stop
  }
  $ports.FixtureBoundary={param($s,[bool]$active=$false)
   $owner=New-WslAcceptanceBridgeProductionPorts $s.bridge_scenario;$update=$null;$reconcile=$null
   try{
    $phase=if($active){'FixtureOriginalBoundary'}else{'FixtureBoundary'}
    & $owner.Begin $phase | Out-Null
    $update=& $owner.Lock 'Global\TinySwarmWorldWslBridgeServiceUpdate'
    $reconcile=& $owner.Lock 'Global\TinySwarmWorldWslBridgeReconcile'
    return & $owner.Observe $phase
   }finally{if($null -ne $reconcile){& $owner.Unlock $reconcile | Out-Null};if($null -ne $update){& $owner.Unlock $update | Out-Null}}
  }
  $ports.FixtureProof={param($s)
   Assert-WslSwitchRunning (Observe $s) $s new
   return Linux new (Get-WslSwitchFixtureProof) @($s.run_id,$s.source_commit) 180
  }
  $ports.Prepared={param($s,$hash) NewProof prepared $hash}
  $ports.Stopped={param($s,$hash) NewProof stopped $hash}
  $ports.Boot={param($who,$s)
   Assert-WslSwitch ($who -cin @('original','new')) 'SWITCH_TARGET';Assert-WslSwitchRunning (Observe $s) $s $who
   $r=Linux $who (Get-WslSwitchBootProbe) @() 10
   Assert-WslSwitch ($r.boot_id_sha256 -cmatch '\A[0-9a-f]{64}\z' -and $r.machine_id_sha256 -cmatch '\A[0-9a-f]{64}\z') 'SWITCH_BOOT_PROOF'
   return $r
  }
  function NoChildren {
   # Counts only actual current-actor launchers/test workers; never signals a
   # saved PID, and makes no visibility/exclusivity claim about other users.
   $query=@'
$ErrorActionPreference='Stop';$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$rows=@(Get-CimInstance -ClassName Win32_Process -Filter "Name='wsl.exe' OR Name='powershell.exe' OR Name='pwsh.exe' OR Name='python.exe' OR Name='python3.exe' OR Name='bash.exe' OR Name='sh.exe'" -OperationTimeoutSec 5)
if($rows.Count -gt 256){throw 'process_bound'}
$clients=0;$workers=0
foreach($p in $rows){
 $owner=Invoke-CimMethod -InputObject $p -MethodName GetOwnerSid -OperationTimeoutSec 5
 if($owner.ReturnValue -ne 0 -or !$owner.Sid){throw 'owner_unknown'}
 if($owner.Sid -ceq $sid -and $p.ProcessId -ne $PID -and $p.ProcessId -ne @COORDINATOR@){
  if($p.Name -ieq 'wsl.exe'){$clients++}
  if($p.Name -imatch '\A(?:powershell|pwsh|python3?|bash|sh)\.exe\z' -or $p.CommandLine -match '(?i)([\/]tests[\/]|-m[ ]+(unittest|pytest)|check_(complexity|architecture)|incus_profile_listener_fixture|wsl_resource_maintenance|prepare-windows)'){$workers++}
 }
}
@{clients=$clients;workers=$workers}|ConvertTo-Json -Compress
'@
   $query=$query.Replace('@COORDINATOR@',[string]$PID)
   $ps=NativeExecutable 'powershell.exe'
   $text=Run $ps @('-NoProfile','-NonInteractive','-EncodedCommand',([Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($query)))) 10 65536
   $r=$text|ConvertFrom-Json -ErrorAction Stop
   Assert-WslSwitch ($r.clients -is [int] -and $r.clients -eq 0 -and $r.workers -is [int] -and $r.workers -eq 0) 'SWITCH_UNSETTLED_CHILD'
   return $r
  }
  $ports.Reset={param($direction,$s,$state)
   Assert-WslSwitch ($direction -cin @('new','original') -and $state.pending -ceq ('reset-to-'+$direction) -and
    $state.resets[$direction].outcome -ceq 'intent') 'SWITCH_RESET_NOT_ADMITTED'
   Assert-WslSwitchBookmark $state $s;[void](Remaining 540)
   Source $s
   $owner=New-WslAcceptanceBridgeProductionPorts $s.bridge_scenario;$update=$null;$reconcile=$null;$ownerWatch=[Diagnostics.Stopwatch]::StartNew()
   try{
    & $owner.Begin 'Recover' | Out-Null
    $update=& $owner.Lock 'Global\TinySwarmWorldWslBridgeServiceUpdate'
    $reconcile=& $owner.Lock 'Global\TinySwarmWorldWslBridgeReconcile'
    # Read-only Recover observation checks complete foreign preservation and
    # descriptor/source/GUID/VHD identity. No Recover/Stop/Start effect is called.
    $owned=& $owner.Observe 'Recover';& $owner.Stopped 'ResetBoundary' | Out-Null
    $fresh=Observe $s;Assert-WslSwitchRunning $fresh $s none
    Assert-WslSwitch ($fresh.registration_count -eq 2 -and $fresh.registrations_sha256 -ceq $state.receipts.registration) 'SWITCH_RESET_REGISTRATION'
    $children=NoChildren
    Assert-WslSwitchResetBoundary $s $state $fresh $direction $owned.payload.status $children
    # Last JIT registry/running check immediately precedes the only global
    # command. An outside launch can still race this check; locks are not global
    # Windows user/session exclusion. Unknown outcomes are never replayed.
    $jit=Observe $s;Assert-WslSwitchRunning $jit $s none
    Assert-WslSwitch ($jit.registration_count -eq 2 -and $jit.registrations_sha256 -ceq $state.receipts.registration) 'SWITCH_RESET_REGISTRATION'
    Assert-WslSwitchResetBoundary $s $state $jit $direction $owned.payload.status $children
    [void](Save $s $state) # Flush the same intent under both owner locks after JIT proofs.
    Assert-WslSwitch ($ownerWatch.Elapsed.TotalSeconds -lt 210) 'SWITCH_RESET_OWNER_RESERVE'
    $resetWatch=[Diagnostics.Stopwatch]::StartNew()
    [void](Run (Wsl) @('--shutdown') 60 65536)
    $state.resets[$direction].outcome='command-returned';[void](Save $s $state)
    $verify=[Diagnostics.Stopwatch]::StartNew()
    $after=Observe $s;Assert-WslSwitchRunning $after $s none
    Assert-WslSwitch ($after.registration_count -eq 2 -and $after.registrations_sha256 -ceq $state.receipts.registration) 'SWITCH_RESET_REGISTRATION'
    [void](NoChildren);Assert-WslSwitch ($verify.Elapsed.TotalSeconds -lt 30 -and $resetWatch.Elapsed.TotalSeconds -lt 90 -and $ownerWatch.Elapsed.TotalSeconds -lt 300) 'SWITCH_RESET_VERIFY_TIMEOUT'
    $state.resets[$direction].outcome='all-stopped';[void](Save $s $state)
    return @{status='VM_RESET_ALL_STOPPED'}
   }finally{
    if($null -ne $reconcile){& $owner.Unlock $reconcile | Out-Null}
    if($null -ne $update){& $owner.Unlock $update | Out-Null}
   }
  }

  $script:ports=$ports
 }
 $result=@{}
 foreach($name in @('Begin','Clock','Source','Observe','Load','Save','Lock','Unlock','Original','Bridge','Terminate','Start','Network','Prepared','Stopped','Registration','Reset','Boot','FixtureBoundary','FixtureProof','StageOriginal','OriginalWitness','Parent','BridgeStopped','OriginalBridge','BridgeOutcome')){
  $result[$name]={& $module {param($op,$a) & ($script:ports[$op]) @a} $name $args}.GetNewClosure()
 }
 return $result
}
if($MyInvocation.InvocationName -ne '.'){
 try{
  $s=Read-WslSwitchWire $ScenarioBase64 $ExpectedScenarioSha256
  $go=if($Mode -cin @('Prepare','Reconcile','InspectOriginal')){$null}else{Read-WslSwitchWire $ApprovalBase64 $ExpectedApprovalSha256}
  $bridgeGo=if($BridgeApprovalBase64 -and $Mode -cin @('EnterNew','BindNew','ReturnOriginal','SealFixtureReturn','ReturnFixture','RestoreOriginal','ReconcileEffects')){Read-WslSwitchWire $BridgeApprovalBase64 $ExpectedBridgeApprovalSha256}else{$null}
  $ports=New-WslAcceptanceGuestSwitchProductionPorts $s
  $r=Invoke-WslAcceptanceGuestSwitch $s $Mode $go $bridgeGo $EvidenceSha256 $ports $PrepareFor
  $r|ConvertTo-Json -Depth 8 -Compress
  if($r.status -cin @('ORIGINAL_SOURCE_STAGED','ORIGINAL_INSPECTED_READ_ONLY','ORIGINAL_PREPARED','PRODUCT_WINDOW_OPENED','PENDING_EFFECT_RECONCILED','PREPARED_READ_ONLY','OBSERVED_READ_ONLY','ORIGINAL_QUIESCED','NEW_GUEST_SAFE_FOR_PREPARATION',
   'FIXTURE_RETURN_SEALED','NEW_GUEST_NETWORK_PREREQUISITE_REQUIRED','NEW_GUEST_PREPARED','NEW_BINDING_READY','ORIGINAL_READY_FOR_BRIDGE_RESUME','ORIGINAL_RESTORED_NEW_RETAINED_STOPPED')){exit 0};exit 2
 }catch{[Console]::Error.WriteLine('{"status":"SWITCH_ADMISSION_FAILED"}');exit 2}
}
