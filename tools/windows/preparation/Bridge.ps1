# W06 delegates routing ownership and credentials to the existing protected bridge.
function Invoke-PreparationBridgeProcess($Options, [string]$Action, [string]$Address, [int]$TimeoutSeconds) {
    $arguments=@('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $Options.RepositoryRoot 'tools/windows/tws-wsl-bridge.ps1'),'-Action',$Action,'-ConfigPath',(Join-Path $Options.RepositoryRoot 'tools/windows/tws-wsl-bridge.config.json'),'-PortRegistryPath',(Join-Path $Options.RepositoryRoot 'infra/config/ports.yaml'),'-Distro',$Options.Distro,'-ObservedAddress',$Address)
    if($Action -ne 'install'){$arguments=@('-NonInteractive')+$arguments}
    return Invoke-PreparationProcess (Get-PreparationExecutable 'powershell.exe') $arguments $TimeoutSeconds
}
function Get-PreparationBridgeInventory($Options,$Facts) {
    if($Facts.running -ne $true -or $Facts.pid1 -ne 'systemd'){return @{state='LIFECYCLE_PREREQUISITES_REQUIRED'}}
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $budget=$Options.ProbeTimeoutSeconds
    if($Options.ContainsKey('BridgeBudgetSeconds') -and $Options.BridgeBudgetSeconds){$budget=[Math]::Min($budget,$Options.BridgeBudgetSeconds)}
    $runningProbe=Invoke-PreparationProcess (Get-PreparationExecutable 'wsl.exe') @('--list','--running','--quiet') $budget
    if($runningProbe.exit_code -ne 0){return @{state='BLOCKED';blockers=@('running_registration_inventory_unavailable')}}
    $names=@(($runningProbe.stdout -replace "`0",'') -split '\r?\n' | ForEach-Object{$_.Trim()} | Where-Object{$_})
    if($names -cnotcontains $Options.Distro){return @{state='BLOCKED';blockers=@('selected_distro_stopped')}}
    $remaining=$budget-[int][Math]::Ceiling($clock.Elapsed.TotalSeconds)
    if($remaining -le 0){return @{state='BLOCKED';blockers=@('bridge_inventory_deadline')}}
    # W06 never starts a Linux process: consume the W04/W05 running-only observation.
    $address=$Facts['observed_wsl_address']
    if($address -isnot [string] -or $address -notmatch '\A(?:[0-9]{1,3}\.){3}[0-9]{1,3}\z'){return @{state='BLOCKED';blockers=@('observed_wsl_address_required')}}
    $probe=Invoke-PreparationBridgeProcess $Options 'inventory' $address $remaining
    if($probe.exit_code -ne 0){return @{state='BLOCKED';blockers=@('bridge_inventory_unavailable')}}
    try {
        $inventory=ConvertTo-PreparationHashtable ($probe.stdout | ConvertFrom-Json)
        if($inventory.schema_version -ne 1 -or $inventory.distro -cne $Options.Distro -or $inventory.observed_address -cne $address -or $inventory.bridge_ready -isnot [bool] -or !$inventory.fingerprint){throw 'invalid_bridge_inventory'}
        return $inventory
    }catch{return @{state='BLOCKED';blockers=@('bridge_inventory_invalid')}}
}
function Add-PreparationBridgePlan($Options,$Facts,$Blockers,$Actions) {
    $bridge=$Facts.bridge_facts
    if(!$bridge -or $bridge.state -eq 'LIFECYCLE_PREREQUISITES_REQUIRED'){
        [void]$Blockers.Add(@{code='bridge_inventory_required';stage='windows_bridge';remedy='Rerun preparation after lifecycle/resource prerequisites and read-only bridge inventory are available.'})
        return
    }
    foreach($code in $bridge.blockers){[void]$Blockers.Add(@{code=$code;stage='windows_bridge';remedy='Resolve observed ownership/configuration collision without deleting foreign state, then rerun preflight.'})}
    if($bridge.blockers.Count -gt 0){return}
    if($bridge.bridge_ready -eq $true){return}
    if($bridge.action -notin @('install','refresh')){
        [void]$Blockers.Add(@{code='bridge_action_unknown';stage='windows_bridge';remedy='Inspect the existing bridge owner and rerun inventory.'});return
    }
    [void]$Actions.Add(@{id=('bridge_'+$bridge.action);owner='W06 existing Windows bridge';target=$Options.Distro;operation=$bridge.action
        before=$bridge;after=@{distro=$Options.Distro;observed_address=$bridge.observed_address;bridge_ready=$true}
        prerequisites=@('candidate_eligibility','fresh_consent','protected_evidence');privilege='administrator';timeout_seconds=$Options.ActionTimeoutSeconds
        restart_scope='none';preservation_rule='Existing bridge ownership, ACL, credential, WinSW and payload transaction guards; shared auto config remains unchanged.'
        verification_probe='read_only_bridge_inventory';retry_budget=0
        credential_guidance=$(if($bridge.action -eq 'install' -and $bridge.ownership -eq 'absent'){'Existing bridge dialog requires the current Windows account that owns the selected WSL registration; password is never preparation evidence.'}else{'Reuse owned registration credentials.'})})
}
function Invoke-PreparationBridgeAction($Action,$Options,$Facts,$Store) {
    $started=[Diagnostics.Stopwatch]::StartNew()
    $freshOptions=@{};foreach($key in $Options.Keys){$freshOptions[$key]=$Options[$key]}
    $freshOptions.BridgeBudgetSeconds=$Options.ActionTimeoutSeconds
    $fresh=Get-PreparationBridgeInventory $freshOptions $Facts
    if(!$fresh.ContainsKey('fingerprint')){return @{exit_code=$(if($fresh.blockers -contains 'bridge_inventory_deadline'){124}else{1});confirmed=$false;uncertain=$false;cause='bridge_fresh_inventory_failed'}}
    if($fresh.fingerprint -cne $Action.before.fingerprint){return @{exit_code=1;confirmed=$false;uncertain=$false;cause='bridge_consent_drift'}}
    $name=$Action.operation
    if($name -notin @('install','refresh')){throw 'invalid_bridge_action'}
    $remaining=$Options.ActionTimeoutSeconds-[int][Math]::Ceiling($started.Elapsed.TotalSeconds)
    if($remaining -le 0){return @{exit_code=124;confirmed=$false;uncertain=$false;cause='bridge_action_deadline'}}
    $result=Invoke-PreparationBridgeProcess $Options $name $fresh.observed_address $remaining
    $remaining=$Options.ActionTimeoutSeconds-[int][Math]::Ceiling($started.Elapsed.TotalSeconds)
    if($remaining -le 0){return @{exit_code=124;confirmed=$false;uncertain=$true;cause='bridge_action_deadline'}}
    $postOptions=@{};foreach($key in $Options.Keys){$postOptions[$key]=$Options[$key]}
    $postOptions.BridgeBudgetSeconds=$remaining
    $postOptions.ProbeTimeoutSeconds=[Math]::Min($Options.ProbeTimeoutSeconds,[Math]::Max(1,[int]($remaining/2)))
    $after=Get-PreparationBridgeInventory $postOptions $Facts
    $confirmed=$after['bridge_ready'] -eq $true -and $after.blockers.Count -eq 0
    return @{exit_code=$result.exit_code;confirmed=$confirmed;uncertain=(!$confirmed);observations=$after;cause=$(if(!$confirmed){'bridge_postcheck_failed'}else{$null})}
}
