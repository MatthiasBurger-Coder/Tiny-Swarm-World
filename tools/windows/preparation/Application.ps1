function Invoke-WindowsPreparation {
    param([hashtable]$Options, [hashtable]$Ports)
    if ($Options.Mode -eq 'Help' -and !$Options.Invalid -and !$Options.ApproveApply -and !$Options.QualificationRun -and !$Options.ApprovedPlan) { return @{schema_version=1
    help='./prepare_windows.ps1 -Distro Ubuntu-24.04 -Preflight. Existing custom registrations require -Distro exact_name -UbuntuRelease 24.04 or 26.04; absent custom names are never installed. Use -DryRun to inspect, -Json for one nonprompting envelope. Apply shows the fresh plan and asks exact yes; JSON needs -ApproveApply. Optional -ApprovedPlan fingerprint rejects stale plans. Ordinary Apply is unqualified and blocked. Qualification additionally requires -QualificationRun -QualificationHost observed_host -QualificationDistro selected_distro -QualificationRevision clean_revision -RecoveryReference recoverable_target. Operator creates/selects accounts and restarts Windows/selected distro. Capability READY is not aggregate readiness.'
    result=@{outcome='HELP'
    exit_code=0
    preparation_ready=$false
    services_verified=$false}} }
    $selection=Get-PreparationSelection $Options
    if ($Options.Invalid -or !$selection.valid -or $Options.Mode -notin @('Help','Check','Plan','Apply') -or $Options.ProbeTimeoutSeconds -le 0 -or $Options.ActionTimeoutSeconds -le 0 -or ($Options.Mode -eq 'Help') -or ($Options.Mode -ne 'Apply' -and ($Options.ApproveApply -or $Options.QualificationRun -or $Options.ApprovedPlan))) { return @{schema_version=1
    blockers=@(@{code='invalid_arguments'
    remedy='Use -Help.'})
    result=@{outcome='BLOCKED'
    exit_code=2
    changed=$false
    preparation_ready=$false
    services_verified=$false}} }
    $Options.ExpectedRelease=$selection.release
    $Options.InstallArtifact=$selection.install_artifact
    try {
        $facts=& $Ports.Inventory $Options
        if($Ports.EvidencePreflight){$facts.evidence_storage_safe=[bool](& $Ports.EvidencePreflight $Options)}else{$facts.evidence_storage_safe=$false}
        $source=& $Ports.SourceIdentity $Options
        $plan=New-PreparationPlan $Options $facts $source
    } catch { return @{schema_version=1
    blockers=@(@{code='inventory_failed'
    remedy='Inspect host prerequisites and rerun preflight.'})
    result=@{outcome='BLOCKED'
    exit_code=2
    changed=$false
    preparation_ready=$false
    services_verified=$false}} }
    if ($Options.Mode -ne 'Apply') { return $plan }
    $guard=$null
    if (!$Options.QualificationRun) { $guard='unqualified_target' }
    elseif ((!$Options.ApproveApply -and ($Options.Json -or !$Ports.Consent -or !(& $Ports.Consent $plan))) -or ($Options.ApprovedPlan -and $Options.ApprovedPlan -cne $plan.plan_fingerprint)) { $guard='exact_plan_consent_required' }
    elseif (!$source.verified -or !$source.clean -or !$source.revision) { $guard='unverified_source' }
    elseif ($Options.QualificationHost -cne $facts.host_identity -or $Options.QualificationDistro -cne $Options.Distro -or $Options.QualificationRevision -cne $source.revision -or [string]::IsNullOrWhiteSpace($Options.RecoveryReference) -or $Options.RecoveryReference.Length -gt 256) { $guard='qualification_authorization_mismatch' }
    if ($guard) { $plan.blockers+=@{code=$guard
    stage='consent'
    remedy='Reinventory and supply fresh exact-plan authorization for a recoverable candidate target.'}
    $plan.result.outcome='BLOCKED'
    $plan.result.exit_code=2
    return $plan }
    if ($plan.blockers.Count -gt 0 -or $plan.actions.Count -eq 0) { return $plan }
    $attempted=$false
    try {
        $freshFacts=& $Ports.Inventory $Options
        $freshFacts.evidence_storage_safe=[bool](& $Ports.EvidencePreflight $Options)
        $fresh=New-PreparationPlan $Options $freshFacts (& $Ports.SourceIdentity $Options)
        if ($fresh.plan_fingerprint -cne $plan.plan_fingerprint) { throw 'consent_drift' }
        $store=& $Ports.ProtectEvidence $Options
        & $Ports.WriteEvidence $store @{event='intent'
        plan_fingerprint=$plan.plan_fingerprint
        revision=$source.revision
        actions=$plan.actions
        before=(Get-PreparationEvidenceFacts $facts)
        qualification=$true
        recovery_declared=$true} | Out-Null
        $plan.result.evidence_path=$store
        foreach ($action in $plan.actions) {
            $attempted=$true
            $effect=& $Ports.Execute $action $Options $facts $store
            if ($effect.confirmed) { $plan.result.completed_actions+= $action.id
            $plan.result.changed=$true }
            if ($effect.uncertain) { $plan.result.uncertain_actions+= $action.id }
            if ($effect.exit_code -ne 0 -and $effect.exit_code -ne 3010) {
                $plan.result.outcome='FAILED'
                $plan.result.exit_code=1
                if ($plan.result.changed -or $effect.uncertain) {$plan.result.outcome='PARTIAL'
                $plan.result.exit_code=4}
                if ($effect.exit_code -in @(124,130)) {$plan.result.exit_code=$effect.exit_code}
            } elseif (!$effect.confirmed) { $plan.result.outcome='PARTIAL'
            $plan.result.exit_code=4
            $plan.result.uncertain_actions+= $action.id }
            else {
                $plan.result.outcome='PARTIAL'
                $plan.result.exit_code=4
                $plan.blockers+=@{code='next_stage_consent_required'
                stage='next_stage'
                remedy=$plan.result.next_command}
                if($action.id -eq 'enable_systemd') {$plan.result.outcome='RESTART_REQUIRED'
                $plan.result.exit_code=3
                $plan.restart=@{scope='distro'
                operator_command=('wsl.exe --terminate '+$Options.Distro+'; wsl.exe --distribution '+$Options.Distro)}}
                elseif($effect.exit_code -eq 3010 -or $action.id -eq 'enable_features') {$plan.result.outcome='RESTART_REQUIRED'
                $plan.result.exit_code=3
                $plan.restart=@{scope='Windows'
                operator_command='Restart-Computer'}}
            }
            if($effect.cause){$plan.blockers+=@{code=$effect.cause;stage=$action.id;remedy='Inspect the safe failure code and rerun preflight before new consent.'}}
            & $Ports.WriteEvidence $store @{event='effect'
            plan_fingerprint=$plan.plan_fingerprint
            action=$action.id
            confirmed=$effect.confirmed
            uncertain=$effect.uncertain
            exit_code=$effect.exit_code
            outcome=$plan.result.outcome
            after=$effect.observations
            cause=$effect.cause
            restart=$plan.restart} | Out-Null
            break # Freshly discovered stages always need another invocation/consent.
        }
    } catch {
        $plan.blockers+=@{code= $(if (!$attempted -and $_.Exception.Message -eq 'consent_drift') {'consent_drift'} else {'evidence_or_action_failed'})
        stage='apply'
        remedy='Inspect protected evidence and rerun read-only preflight before fresh consent.'}
        if ($attempted) {
            $plan.result.outcome='PARTIAL'
            $plan.result.exit_code=4
            if($_.Exception.Message -match 'deadline|timeout'){$plan.result.exit_code=124}
            if($_.Exception -is [Management.Automation.PipelineStoppedException]){$plan.result.exit_code=130}
            if (!$plan.result.changed) {$plan.result.uncertain_actions+= $plan.actions[0].id}
        }
        else {$plan.result.outcome='BLOCKED'
        $plan.result.exit_code=2}
    }
    $plan.result.capability_ready=$false
    return $plan
}
