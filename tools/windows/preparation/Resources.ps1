# Pure resource assessment and supported INI merge; no host commands.
function Test-PreparationResourceArguments($Options) {
    foreach($key in @('WslMemoryGiB','WslProcessors','WslSwapGiB')) {
        if($null -ne $Options[$key]) {
            $value=$Options[$key]
            if($value -isnot [int] -and $value -isnot [long]){return $false}
            if($value -gt 1048576 -or $value -lt 0 -or ($key -ne 'WslSwapGiB' -and $value -eq 0)){return $false}
        }
    }
    return $true
}
function ConvertFrom-PreparationWslConfig([byte[]]$Bytes) {
    $encoding=New-Object Text.UTF8Encoding($false,$true)
    $offset=0
    $bom=[byte[]]@()
    if($Bytes.Length -ge 3 -and $Bytes[0] -eq 239 -and $Bytes[1] -eq 187 -and $Bytes[2] -eq 191){$offset=3;$bom=[byte[]]@(239,187,191)}
    elseif($Bytes.Length -ge 2 -and $Bytes[0] -eq 255 -and $Bytes[1] -eq 254){$encoding=New-Object Text.UnicodeEncoding($false,$false,$true);$offset=2;$bom=[byte[]]@(255,254)}
    elseif($Bytes.Length -ge 2 -and $Bytes[0] -eq 254 -and $Bytes[1] -eq 255){throw 'unsupported_config_encoding'}
    $text=$encoding.GetString($Bytes,$offset,$Bytes.Length-$offset)
    if($text.Contains([string][char]0) -or $text -match "`r(?!`n)"){throw 'unsupported_config_encoding'}
    $newline="`n"
    if($text.Contains("`r`n")){$newline="`r`n";if(($text -replace "`r`n",'').Contains("`n")){throw 'mixed_config_newlines'}}
    $lines=@($text -split '\r?\n')
    $sections=@{};$keys=@{};$managed=@{};$section='';$indices=@{};$sectionIndex=-1
    for($i=0;$i -lt $lines.Count;$i++) {
        $line=$lines[$i]
        if($line -match '^\s*(?:[#;].*)?$'){continue}
        if($line -match '^\s*\[([A-Za-z0-9_.-]+)\]\s*(?:[#;].*)?$') {
            $section=$Matches[1].ToLowerInvariant()
            if($sections.ContainsKey($section)){throw 'duplicate_config_section'}
            $sections[$section]=$true
            if($section -eq 'wsl2'){$sectionIndex=$i}
        } elseif($section -and $line -match '^\s*([A-Za-z0-9_.-]+)\s*=\s*(.*?)\s*$') {
            $key=$Matches[1].ToLowerInvariant();$value=$Matches[2];$identity=$section+':'+$key
            if($keys.ContainsKey($identity)){throw 'duplicate_config_key'}
            $keys[$identity]=$true
            if($section -eq 'wsl2'){$managed[$key]=$value;$indices[$key]=$i}
        } else {throw 'unsupported_config_syntax'}
    }
    foreach($key in @('memory','swap')){if($managed.ContainsKey($key) -and $managed[$key] -notmatch '^\d+(?:GB|MB)$'){throw 'unsupported_resource_unit'}}
    if($managed.ContainsKey('processors') -and $managed.processors -notmatch '^[1-9][0-9]*$'){throw 'unsupported_processors'}
    if($managed.ContainsKey('swapfile')){throw 'redirected_swap_unsupported'}
    return @{lines=$lines;newline=$newline;encoding=$encoding;bom=$bom;managed=$managed;indices=$indices;section_index=$sectionIndex;text=$text}
}
function ConvertTo-PreparationWslConfig($Parsed,$Allocation) {
    $lines=New-Object Collections.Generic.List[string]
    foreach($line in $Parsed.lines){$lines.Add($line)}
    $values=[ordered]@{memory=([string]$Allocation.memory_gib+'GB');processors=[string]$Allocation.processors;swap=([string]$Allocation.swap_gib+'GB')}
    foreach($key in $values.Keys){if($Parsed.indices.ContainsKey($key)){
        $index=$Parsed.indices[$key]
        # Preserve key spelling and surrounding whitespace; only the value changes.
        $lines[$index]=[regex]::Replace($lines[$index], '^(\s*[A-Za-z0-9_.-]+\s*=\s*).*?(\s*)$', ('${1}'+$values[$key]+'${2}'))
    }}
    $insert=$Parsed.section_index+1
    if($Parsed.section_index -lt 0){if($lines.Count -gt 0 -and $lines[$lines.Count-1] -eq ''){$lines.RemoveAt($lines.Count-1)};$lines.Add('[wsl2]');$insert=$lines.Count}
    foreach($key in $values.Keys){if(!$Parsed.indices.ContainsKey($key)){$lines.Insert($insert,($key+'='+$values[$key]));$insert++}}
    $text=$lines -join $Parsed.newline
    if($Parsed.text.Length -eq 0 -and !$text.EndsWith($Parsed.newline)){$text+=$Parsed.newline}
    return [byte[]]($Parsed.bom+$Parsed.encoding.GetBytes($text))
}
function Get-PreparationResourceAssessment($Options,$Facts) {
    $r=$Facts.resource_facts
    $blockers=New-Object Collections.ArrayList
    function ResourceBlock($code){[void]$blockers.Add(@{code=$code;stage='wsl_resources';remedy='Inspect capacity and global configuration; rerun preflight before fresh consent.'})}
    if(!$r -or !$r.projection_valid){ResourceBlock 'resource_projection_unknown';return @{blockers=@($blockers.ToArray());state='BLOCKED'}}
    foreach($key in @('physical_memory_bytes','logical_processors','distro_free_bytes','swap_free_bytes')){
        if(($r[$key] -isnot [int] -and $r[$key] -isnot [long]) -or $r[$key] -le 0){ResourceBlock 'resource_inventory_unknown';return @{blockers=@($blockers.ToArray());state='BLOCKED'}}
    }
    $profile=$r.profile;$nodes=$r.node_budget
    $required=@{memory_gib=[Math]::Max($profile.memory_gib,$nodes.memory_gib+2);processors=[Math]::Max($profile.processors,$nodes.processors);disk_gib=[Math]::Max($profile.disk_gib,$nodes.disk_gib)}
    $allocation=@{memory_gib=$required.memory_gib;processors=$required.processors;swap_gib=[Math]::Ceiling($required.memory_gib/4)}
    foreach($entry in @(@('WslMemoryGiB','memory_gib'),@('WslProcessors','processors'),@('WslSwapGiB','swap_gib'))){if($null -ne $Options[$entry[0]]){$allocation[$entry[1]]=$Options[$entry[0]]}}
    if($null -eq $Options.WslSwapGiB){$allocation.swap_gib=[Math]::Ceiling($allocation.memory_gib/4)}
    $reserve=@{memory_gib=[Math]::Max(4,[Math]::Ceiling($r.physical_memory_bytes/1073741824/4));processors=[Math]::Max(1,[Math]::Ceiling($r.logical_processors/4));disk_gib=20}
    if($r.physical_memory_bytes -le 0 -or $r.logical_processors -le 0 -or !$r.storage_known){ResourceBlock 'resource_inventory_unknown'}
    if(!$r.config_safe){ResourceBlock 'unsafe_global_wsl_config'}
    if($allocation.memory_gib -lt $required.memory_gib -or $allocation.processors -lt $required.processors){ResourceBlock 'allocation_below_requirements'}
    if(($allocation.memory_gib+$reserve.memory_gib)*1073741824 -gt $r.physical_memory_bytes -or $allocation.processors+$reserve.processors -gt $r.logical_processors){ResourceBlock 'insufficient_host_capacity'}
    # Reserve the full proposed swap: sparse allocation is not established by FileInfo.Length.
    if($r.storage_known){
        if($r.distro_volume -eq $r.swap_volume){if($r.distro_free_bytes -lt ($required.disk_gib+$allocation.swap_gib+20)*1073741824){ResourceBlock 'insufficient_host_disk'}}
        elseif($r.distro_free_bytes -lt ($required.disk_gib+20)*1073741824 -or $r.swap_free_bytes -lt ($allocation.swap_gib+20)*1073741824){ResourceBlock 'insufficient_host_disk'}
    }
    $matches=$r.config_values.memory -eq ([string]$allocation.memory_gib+'GB') -and $r.config_values.processors -eq [string]$allocation.processors -and $r.config_values.swap -eq ([string]$allocation.swap_gib+'GB')
    $effective=$false
    if($matches -and $blockers.Count -eq 0){
        $minimum=[Math]::Max($profile.memory_gib,$nodes.memory_gib)*1073741824
        $ceiling=$allocation.memory_gib*1073741824
        $tolerance=[Math]::Max(268435456,$ceiling*0.02)
        $effective=$r.effective_known -and $r.effective_memory_bytes -ge $minimum -and [Math]::Abs($r.effective_memory_bytes-$ceiling) -le $tolerance -and $r.effective_processors -eq $allocation.processors -and [Math]::Abs($r.effective_swap_bytes-$allocation.swap_gib*1073741824) -le 16777216 -and $r.effective_disk_bytes -ge $required.disk_gib*1073741824
        if(!$r.effective_known){ResourceBlock 'effective_resources_unknown'}
        elseif($r.effective_memory_bytes -lt $minimum){ResourceBlock 'insufficient_effective_memory'}
        elseif($r.effective_disk_bytes -lt $required.disk_gib*1073741824){ResourceBlock 'insufficient_effective_disk'}
        elseif(!$effective){ResourceBlock 'effective_resources_mismatch'}
    }
    return @{state=$(if($effective){'VERIFIED'}elseif($blockers.Count){'BLOCKED'}else{'CHANGE_REQUIRED'});windows_reserve=$reserve;allocation=$allocation;managed_nodes=$nodes;profile_minimum=$profile;required=$required;blockers=@($blockers.ToArray());change_required=(!$matches -and $blockers.Count -eq 0);effective_verified=$effective;global_impact='All WSL2 distributions; operator must shut down all WSL after configuration changes.';affected_running=@($Facts.running_registrations);config_snapshot=$r.config_snapshot;current_settings=$r.config_values}
}

function ConvertFrom-PreparationEffectiveResources($Probe) {
    if($Probe.exit_code -ne 0 -or ![string]::IsNullOrEmpty($Probe.stderr) -or $Probe.stdout -isnot [string]){return $null}
    $observed=@{}
    foreach($line in ($Probe.stdout.TrimEnd("`n") -split '\n')){
        if($line -cnotmatch '^(effective_memory_bytes|effective_processors|effective_swap_bytes|effective_disk_bytes)=([0-9]+)$'){return $null}
        $key=$Matches[1];$text=$Matches[2]
        if($observed.ContainsKey($key)){return $null}
        $value=0L
        if(![long]::TryParse($text,[ref]$value)){return $null}
        $observed[$key]=$value
    }
    if($observed.Count -ne 4 -or $observed.effective_memory_bytes -le 0 -or $observed.effective_processors -le 0 -or $observed.effective_disk_bytes -le 0){return $null}
    return $observed
}
