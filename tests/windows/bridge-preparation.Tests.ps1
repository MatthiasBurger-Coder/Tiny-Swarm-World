param([Parameter(Mandatory=$true)][string]$RepositoryRoot)
$ErrorActionPreference='Stop'
Import-Module Microsoft.PowerShell.Utility
Import-Module Microsoft.PowerShell.Management
. (Join-Path $RepositoryRoot 'tools/windows/tws-wsl-bridge.ps1')
$count=0
$originalHostsReader=${function:Get-PreparationHostsText}
$originalWslDescriptor=${function:Test-PreparationWslPathDescriptor}
$originalWslPathObservation=${function:Get-PreparationWslPathObservation}
$originalIpHelperIdentity=${function:Get-PreparationIpHelperIdentity}
$originalIpFunction=${function:Get-WslIp}
$originalCredentialFunction=${function:Request-BridgeServiceCredential}
$originalFirewallFilters=${function:Get-PreparationFirewallFilters}
function Assert($Value,$Name){if(!$Value){throw "FAIL: $Name"};$script:count++}
# Only disposable test files are written; no host/service/routing resources.
$tempRoot=Join-Path ([IO.Path]::GetTempPath()) ('tsw-w06-test-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempRoot | Out-Null
try {
    $source=Join-Path $tempRoot 'source.json';$staged=Join-Path $tempRoot 'staged.json'
    [IO.File]::WriteAllText($source,'{"distro":"auto","listenAddress":"0.0.0.0"}')
    Copy-Item -LiteralPath $source -Destination $staged
    $savedHostsPath=$HostsPath
    $HostsPath=Join-Path $tempRoot 'hosts.txt'
    [IO.File]::WriteAllText($HostsPath, "127.0.0.1 localhost`r`n", [Text.Encoding]::UTF8)
    $plainHosts=& $originalHostsReader
    Assert ($plainHosts -ceq "127.0.0.1 localhost`r`n") 'host fingerprint preserves exact text'
    Assert ($plainHosts.PSObject.Properties.Name -notcontains 'PSProvider' -and $plainHosts.PSObject.Properties.Name -notcontains 'PSDrive') 'host fingerprint excludes filesystem provider metadata'
    Assert ((Get-BridgePreparationDigest @($plainHosts)) -ceq (Get-BridgePreparationDigest @("127.0.0.1 localhost`r`n"))) 'plain hosts digest equals literal digest'
    $HostsPath=$savedHostsPath
    $Action='inventory'
    function Initialize-BridgeAclGuardType{throw 'read-only inventory invoked C# compiler'}
    Assert (Test-BridgeHandleObjectSafe -Path $source -ExpectedDirectory $false) 'in-memory no-compiler guard reads regular object'
    Assert (!(Test-BridgeHandleObjectSafe -Path $source -ExpectedDirectory $true)) 'in-memory guard rejects changed object type'
    Assert (!(Test-BridgeHandleAclExact -Path $source -CurrentSid ([Security.Principal.WindowsIdentity]::GetCurrent().User.Value) -ExpectedDirectory $false)) 'in-memory guard rejects unprotected authority ACL'
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    foreach($directory in @($false,$true)) {
        $inheritance='';if($directory){$inheritance='OICI'}
        $sddl='O:BAG:BAD:P(A;'+$inheritance+';FA;;;SY)(A;'+$inheritance+';FA;;;BA)(A;'+$inheritance+';FRFX;;;'+$sid+')'
        $descriptor=[Security.AccessControl.RawSecurityDescriptor]::new($sddl)
        Assert (Test-BridgeReadOnlyDescriptor $descriptor $sid $directory) 'read-only exact descriptor accepts existing protected three-ACE contract'
        $descriptor=[Security.AccessControl.RawSecurityDescriptor]::new($sddl.Replace('FRFX','FA'))
        Assert (!(Test-BridgeReadOnlyDescriptor $descriptor $sid $directory)) 'read-only descriptor refuses excess owner-account mutation rights'
        $descriptor=[Security.AccessControl.RawSecurityDescriptor]::new($sddl.Replace('D:P','D:'))
        Assert (!(Test-BridgeReadOnlyDescriptor $descriptor $sid $directory)) 'read-only descriptor refuses inherited policy'
    }
    $hardlink=Join-Path $tempRoot 'hardlink.json'
    New-Item -ItemType HardLink -Path $hardlink -Value $source | Out-Null
    Assert (!(Test-BridgeHandleObjectSafe -Path $source -ExpectedDirectory $false)) 'in-memory guard rejects hard-linked payload'
    Remove-Item -LiteralPath $hardlink
    # Exercise the real read-only handle/signature adapter on disposable files.
    $script:signer=[pscustomobject]@{Subject='CN=Microsoft Corporation, O=Microsoft Corporation, C=US';Thumbprint='fixture';SimpleName='Microsoft Corporation'}
    $script:signer | Add-Member ScriptMethod GetNameInfo {param($Type,$Issuer) return $this.SimpleName}
    $script:signature=[pscustomobject]@{Status='Valid';SignerCertificate=$script:signer}
    function Get-AuthenticodeSignature{param($LiteralPath,$ErrorAction) return $script:signature}
    function Test-PreparationWslPathDescriptor{param($Security,$VolumeRoot) return $true}
    $pathProof=Get-PreparationWslPathObservation $source $false $false
    Assert ($pathProof.hash -and $pathProof.identity.Count -eq 3) 'actual WSL path reader binds file identity and hash'
    foreach($field in @('Status','Subject','SimpleName')) {
        $target=$script:signer;if($field -eq 'Status'){$target=$script:signature}
        $saved=$target.$field;$target.$field='foreign';$threw=$false
        try{Get-PreparationWslPathObservation $source $false $false | Out-Null}catch{$threw=$true}
        Assert $threw ('WSL signature rejects '+$field);$target.$field=$saved
    }
    New-Item -ItemType HardLink -Path $hardlink -Value $source | Out-Null
    $threw=$false;try{Get-PreparationWslPathObservation $source $false $false | Out-Null}catch{$threw=$true}
    Assert $threw 'WSL path guard rejects actual hardlink';Remove-Item -LiteralPath $hardlink
    $junction=Join-Path $tempRoot 'junction';$junctionTarget=Join-Path $tempRoot 'target'
    New-Item -ItemType Directory -Path $junctionTarget | Out-Null
    New-Item -ItemType Junction -Path $junction -Target $junctionTarget | Out-Null
    try{$threw=$false;try{Get-PreparationWslPathObservation $junction $true $false | Out-Null}catch{$threw=$true};Assert $threw 'WSL path guard rejects actual reparse point'}finally{[IO.Directory]::Delete($junction)}
    ${function:Test-PreparationWslPathDescriptor}=$originalWslDescriptor
    Remove-Item function:Get-AuthenticodeSignature
    $safe='O:SYG:SYD:(A;;FA;;;SY)(A;;FA;;;BA)(A;;FRFX;;;BU)(A;OICIIO;GA;;;CO)'
    Assert (Test-PreparationWslPathDescriptor ([Security.AccessControl.RawSecurityDescriptor]::new($safe)) $false) 'safe inherited Windows ACL and inherit-only creator owner accepted'
    foreach($unsafe in @($safe.Replace('O:SY','O:BU'),$safe.Replace('FRFX','FW'),$safe.Replace('FRFX','DC'),$safe.Replace('FRFX','WD'),$safe.Replace('FRFX','WO'),$safe.Replace('OICIIO','OICI'))) {
        Assert (!(Test-PreparationWslPathDescriptor ([Security.AccessControl.RawSecurityDescriptor]::new($unsafe)) $false)) 'foreign path mutation ACL rejected'
    }
    $create=[Security.AccessControl.RawSecurityDescriptor]::new('O:SYG:SYD:(A;;FA;;;SY)(A;;0x6;;;AU)')
    Assert (Test-PreparationWslPathDescriptor $create $true) 'volume root permits harmless sibling creation'
    Assert (!(Test-PreparationWslPathDescriptor $create $false)) 'creation permission rejected below volume root'
    Assert (!(Test-PreparationWslPathDescriptor ([Security.AccessControl.RawSecurityDescriptor]::new('O:SYG:SYD:(A;;FA;;;SY)(A;;0x40;;;AU)')) $true)) 'volume root foreign delete-child rejected'
    $Action='refresh'
    Set-BridgeStagedDistro -Path $staged -Name 'Ubuntu-24.04'
    Assert ((Read-BridgeConfig $staged).distro -eq 'Ubuntu-24.04') 'protected staged copy binds explicit distro'
    Assert ((Read-BridgeConfig $source).distro -eq 'auto') 'shared source auto distro preserved'
} finally { Remove-Item -LiteralPath $tempRoot -Recurse -Force }
$Distro='Ubuntu-24.04';$ObservedAddress='172.20.0.2'
$config=[pscustomobject]@{distro=$Distro;listenAddress='0.0.0.0';hostsAddress='127.0.0.1';firewallRulePrefix='Tiny Swarm World';discoveryIntervalMinutes=1;hostNames=@()}
$mappings=@([pscustomobject]@{Name='web';ListenPort=80;ConnectPort=80})
$hostNames=@('jenkins.tsw.local')
$script:policyFilters=$null;$script:filterPort='80';$script:filterProtocol='TCP';$script:owned=$false;$script:running=$true;$script:records=@();$script:rules=@();$script:listeners=@();$script:hosts='127.0.0.1 localhost';$script:state=$null;$script:installedConfig=$config;$script:routing=$true;$script:serviceReady=$true
function Test-PreparationDistroRunning{param($Name) return $script:running}
$script:bridgeAccountSid='S-1-5-21-101-202-303-1001'
function Get-BridgeServiceOwnership{return [pscustomobject]@{Status=$(if($script:owned){'owned'}else{'absent'});RequiresAdoption=$false;Service=[pscustomobject]@{Status='Running'};AccountSid=$script:bridgeAccountSid}}
function Assert-BridgeRuntimeStateAuthority{}
function Get-ProtectedBridgeState{return $script:state}
function Read-BridgeConfig{param($Path) return $script:installedConfig}
function Get-InstalledBridgeBundleIdOrEmpty{return 'bundle'}
function Get-PortProxyRecords{return $script:records}
function Get-NetFirewallRule{param($ErrorAction) return @()}
function Get-FirewallRuleSnapshot{param($Config) return [pscustomobject]@{Rules=$script:rules;FiltersByRuleId=@{rule=@{LocalPort=$script:filterPort;Protocol=$script:filterProtocol}}}}
function Get-PreparationFirewallFilters{param($Rules) if($null -ne $script:policyFilters){return $script:policyFilters};return @{ports=@{LocalPort=$script:filterPort;Protocol=$script:filterProtocol}}}
function Get-NetTCPConnection{param($State,$ErrorAction) return $script:listeners}
$script:hostsReadFailure=$false
$script:hostsFixturePath=$null
function Get-PreparationHostsText{if($script:hostsReadFailure){throw 'fixture_hosts_read_unavailable'};if($script:hostsFixturePath){return & $originalHostsReader};return $script:hosts}
function Remove-ManagedHostsBlock{return ($script:hosts -replace '(?ms)# >>> Tiny Swarm World WSL Bridge >>>.*?# <<< Tiny Swarm World WSL Bridge <<<','')}
function Get-FileHash{param($LiteralPath,$Algorithm) return [pscustomobject]@{Hash='same'}}
function Test-Path{param($LiteralPath,$PathType) return $false}
function Test-BridgeServiceReady{return $script:serviceReady}
function Test-PortProxyMappingsReady{param($Config,$WslIp,$Mappings) return $script:routing}
function Test-FirewallRulesReady{param($Config,$Mappings) return $true}
function Test-HostsFileReady{param($Config,$HostNames) return $true}
# Any forbidden read-only path becomes an immediate failure.
function Get-WslIp{throw 'inventory started WSL'}
function Enter-BridgeMutex{throw 'inventory created mutex'}
function Write-StateFile{throw 'inventory wrote state'}
function Request-BridgeServiceCredential{throw 'inventory requested credentials'}
function Test-TcpPort{throw 'inventory conflated deployed endpoint'}
function New-Item{throw 'inventory wrote filesystem'}
function Start-Service{throw 'inventory started service'}
function Probe{return Get-BridgePreparationInventory $config $mappings $hostNames 'registry'}
$r=Probe;Assert ($r.action -eq 'install' -and !$r.bridge_ready -and $r.blockers.Count -eq 0) 'absent registration plans existing install'
Assert ($r.endpoint_state -eq 'UNVERIFIED' -and $r.login_state -eq 'UNVERIFIED') 'routing distinct from endpoint and login'
$before=$r.fingerprint;$r=Probe;Assert ($r.fingerprint -eq $before) 'stable exact plan'
# Real Get-Content values retain filesystem provider metadata on Windows 5.1.
$contentFixture=Join-Path ([IO.Path]::GetTempPath()) ('tsw-w09-hosts-'+[guid]::NewGuid().ToString('N'))
$plainHosts=$script:hosts
$savedHostsPath=$HostsPath;$HostsPath=$contentFixture;$script:hostsFixturePath=$contentFixture
try {
    [IO.File]::WriteAllText($contentFixture,$plainHosts)
    $observed=Microsoft.PowerShell.Management\Get-Content -LiteralPath $contentFixture -Raw -Encoding UTF8
    Assert ($observed.PSObject.Properties.Name -contains 'PSPath') 'real hosts observation carries filesystem metadata'
    # Keep small real path metadata for a bounded red assertion before the fix.
    $observed.PSObject.Properties.Remove('PSDrive')
    $observed.PSObject.Properties.Remove('PSProvider')
    $script:hosts=$observed
    Assert ((Probe).fingerprint -eq $before) 'equivalent decoded hosts exclude incidental filesystem metadata'
    $script:hosts=Microsoft.PowerShell.Management\Get-Content -LiteralPath $contentFixture -Raw -Encoding UTF8
    Assert ((Probe).fingerprint -eq $before) 'complete real provider metadata does not enter inventory digest'
    Assert ([IO.File]::ReadAllText($contentFixture) -ceq $plainHosts) 'read-only inventory preserves actual hosts fixture'
    [IO.File]::WriteAllText($contentFixture,($plainHosts+"`n"))
    $script:hosts=Microsoft.PowerShell.Management\Get-Content -LiteralPath $contentFixture -Raw -Encoding UTF8
    Assert ((Probe).fingerprint -ne $before) 'hosts newline remains consent fingerprint evidence'
    [IO.File]::WriteAllText($contentFixture,($plainHosts+"`n# changed content"))
    $script:hosts=Microsoft.PowerShell.Management\Get-Content -LiteralPath $contentFixture -Raw -Encoding UTF8
    Assert ((Probe).fingerprint -ne $before) 'hosts content change remains consent fingerprint evidence'
} finally {
    $script:hosts=$plainHosts
    $HostsPath=$savedHostsPath;$script:hostsFixturePath=$null
    [IO.File]::Delete($contentFixture)
}

$script:hostsReadFailure=$true
$readFailed=$false
try { Probe | Out-Null } catch { $readFailed=$_.Exception.Message -eq 'fixture_hosts_read_unavailable' }
finally { $script:hostsReadFailure=$false }
Assert $readFailed 'hosts read failure cannot become an empty-content inventory'
$script:running=$false;$r=Probe;Assert ($r.blockers -contains 'selected_distro_stopped' -and !$r.action) 'stopped distro never started';$script:running=$true
$script:records=@([pscustomobject]@{ListenAddress='0.0.0.0';ListenPort=80;ConnectAddress='172.20.0.8';ConnectPort=80});$r=Probe;Assert ($r.blockers -contains 'foreign_portproxy_collision') 'foreign proxy blocked';$script:records=@()
$script:rules=@([pscustomobject]@{Name='foreign';DisplayName='Tiny Swarm World TCP 80';Enabled=$true;Direction='Inbound';Action='Allow'});$r=Probe;Assert ($r.blockers -contains 'foreign_firewall_collision') 'foreign firewall preserved';$script:rules=@()
$script:listeners=@([pscustomobject]@{LocalAddress='127.0.0.1';LocalPort=80;OwningProcess=100});$r=Probe;Assert ($r.blockers -contains 'foreign_or_unknown_listener') 'unknown listener never killed';$script:listeners=@()
$script:hosts='127.0.0.2 jenkins.tsw.local';$r=Probe;Assert ($r.blockers -contains 'foreign_hosts_collision') 'foreign name preserved';$script:hosts='127.0.0.1 localhost'
$script:owned=$true
$script:state=[pscustomobject]@{generatedAt=[DateTimeOffset]::Now.ToString('o');agentMode='windows-service';agentStatus='ready';wslIp=$ObservedAddress;bundleId='bundle';configPath=$InstalledConfigPath;registryPath=$InstalledPortRegistryPath;listenAddress='0.0.0.0';firewallRulePrefix='Tiny Swarm World';mappings=@([pscustomobject]@{listenPort=80;connectPort=80})}
$r=Probe;Assert ($r.bridge_ready -and !$r.action) 'owned ready agent no-op'
# Exercise the genuine identity helper with deterministic CIM observations.
$script:identityFailure='';$script:processReads=0;$script:serviceReads=0
$script:creation=[DateTime]::UtcNow.AddMinutes(-5)
function Get-CimInstance {
    param($ClassName,$Filter,$OperationTimeoutSec,$ErrorAction)
    if($script:identityFailure -eq 'technical'){throw 'fixture_cim_unavailable'}
    if($ClassName -eq 'Win32_Service'){
        $script:serviceReads++
        $value=[pscustomobject]@{Name='iphlpsvc';State='Running';ProcessId=4280;StartName='LocalSystem'}
        switch($script:identityFailure){
            'service_name'{$value.Name='other'} 'stopped'{$value.State='Stopped'}
            'service_pid'{$value.ProcessId=0} 'service_owner'{$value.StartName='unknown-fixture-account'}
            'service_recycled'{if($script:serviceReads -gt 1){$value.ProcessId=4281}}
        }
        if($script:identityFailure -eq 'service_duplicate'){return @($value,$value)}
        return $value
    }
    $script:processReads++
    $value=[pscustomobject]@{ProcessId=4280;Name='svchost.exe';ExecutablePath=(Join-Path ([Environment]::GetFolderPath('System')) 'svchost.exe');CreationDate=$script:creation}
    switch($script:identityFailure){
        'process_pid'{$value.ProcessId=4281} 'process_name'{$value.Name='foreign.exe'}
        'image'{$value.ExecutablePath='C:\untrusted\svchost.exe'} 'creation_missing'{$value.CreationDate=$null}
        'creation_string'{$value.CreationDate=$value.CreationDate.ToString('o')}
        'recheck_creation_string'{if($script:processReads -gt 1){$value.CreationDate=$value.CreationDate.ToString('o')}}
        'process_recycled'{if($script:processReads -gt 1){$value.CreationDate=$value.CreationDate.AddSeconds(1)}}
    }
    if($script:identityFailure -eq 'process_duplicate'){return @($value,$value)}
    return $value
}
function Invoke-CimMethod {
    param($InputObject,$MethodName,$OperationTimeoutSec,$ErrorAction)
    if($script:identityFailure -eq 'owner_probe'){throw 'fixture_owner_unavailable'}
    return [pscustomobject]@{ReturnValue=$(if($script:identityFailure -eq 'owner_error'){1}else{0});Sid=$(if($script:identityFailure -eq 'process_owner'){'S-1-5-19'}else{'S-1-5-18'})}
}
function IdentityProbe {$script:processReads=0;$script:serviceReads=0;return Get-PreparationIpHelperIdentity}
$identity=IdentityProbe
Assert ($identity.pid -eq 4280 -and $identity.owner -eq 'S-1-5-18') 'live SYSTEM IP Helper identity accepted'
foreach($failure in @('service_name','stopped','service_pid','service_owner','service_recycled','service_duplicate','process_pid','process_name','image','creation_missing','creation_string','recheck_creation_string','process_recycled','process_duplicate','process_owner','owner_error','owner_probe','technical')){
    $script:identityFailure=$failure
    Assert ($null -eq (IdentityProbe)) ('IP Helper identity fails closed '+$failure)
}
$script:identityFailure='';$script:processReads=0;$script:serviceReads=0
$script:records=@([pscustomobject]@{ListenAddress='0.0.0.0';ListenPort=80;ConnectAddress=$ObservedAddress;ConnectPort=80})
$script:listeners=@([pscustomobject]@{LocalAddress='0.0.0.0';LocalPort=80;OwningProcess=4})
Assert ((Probe).bridge_ready) 'legacy System portproxy listener remains ready'
$script:listeners[0].OwningProcess=4280
$script:processReads=0;$script:serviceReads=0;$first=Probe
Assert $first.bridge_ready 'exact mapping and live IP Helper listener ready'
Assert ($script:serviceReads -eq 2 -and $script:processReads -eq 2) 'one live identity observation per inventory'
$script:creation=$script:creation.AddSeconds(1);$script:processReads=0;$script:serviceReads=0
Assert ((Probe).fingerprint -ne $first.fingerprint) 'IP Helper creation identity binds fresh consent'
foreach($failure in @('wrong_pid','wrong_address','wrong_connect_port','wrong_connect_address','duplicate_record','duplicate_mapping','no_mapping','technical')){
    $savedRecords=$script:records;$savedMappings=$script:state.mappings
    $script:listeners[0].OwningProcess=4280;$script:listeners[0].LocalAddress='0.0.0.0'
    $script:processReads=0;$script:serviceReads=0
    switch($failure){
        'wrong_pid'{$script:listeners[0].OwningProcess=4281}
        'wrong_address'{$script:listeners[0].LocalAddress='127.0.0.1'}
        'wrong_connect_port'{$script:records=@([pscustomobject]@{ListenAddress='0.0.0.0';ListenPort=80;ConnectAddress=$ObservedAddress;ConnectPort=81})}
        'wrong_connect_address'{$script:records=@([pscustomobject]@{ListenAddress='0.0.0.0';ListenPort=80;ConnectAddress='172.20.0.8';ConnectPort=80})}
        'duplicate_record'{$script:records=@($savedRecords[0],$savedRecords[0])}
        'duplicate_mapping'{$script:state.mappings=@($savedMappings[0],$savedMappings[0])}
        'no_mapping'{$script:state.mappings=@()}
        'technical'{$script:identityFailure='technical'}
    }
    $r=Probe
    Assert (!$r.bridge_ready -and !$r.action -and $r.blockers -contains 'foreign_or_unknown_listener') ('listener ownership conjunct rejected '+$failure)
    $script:records=$savedRecords;$script:state.mappings=$savedMappings;$script:identityFailure=''
}
$script:listeners=@();$script:records=@()
Remove-Item Function:\Get-CimInstance,Function:\Invoke-CimMethod
$script:ipHelperUnavailable=$false
function Get-PreparationIpHelperIdentity{if($script:ipHelperUnavailable){return $null};return [ordered]@{pid=42;owner='S-1-5-18';created_utc='fixture'}}
$script:records=@([pscustomobject]@{ListenAddress='0.0.0.0';ListenPort=80;ConnectAddress=$ObservedAddress;ConnectPort=80})
$script:listeners=@([pscustomobject]@{LocalAddress='0.0.0.0';LocalPort=80;OwningProcess=42})
$r=Probe;Assert ($r.blockers.Count -eq 0) 'IP Helper listener with exact protected mapping accepted'
$script:listeners[0].OwningProcess=43;$r=Probe
Assert ($r.blockers -contains 'foreign_or_unknown_listener') 'unrelated listener PID remains blocked'
# Full inventory recognition with actual process/service/snapshot logic and mocked OS observations.
$script:listeners[0].OwningProcess=42
$wslRoot=Join-Path ([Environment]::GetFolderPath('ProgramFiles')) 'WSL'
$relayPath=Join-Path $wslRoot 'wslrelay.exe';$wslServicePath=Join-Path $wslRoot 'wslservice.exe'
$script:relay=[pscustomobject]@{ProcessId=1992;ParentProcessId=4380;ExecutablePath=$relayPath;CreationDate=[datetime]'2026-01-01T01:00:00Z';CommandLine=' --mode 1 --vm-id {2cbb8b46-a84e-469d-9f54-1bbc26b7a7ce} --handle 2856'}
$script:wslParent=[pscustomobject]@{ProcessId=4380;ParentProcessId=600;ExecutablePath=$wslServicePath;CreationDate=[datetime]'2026-01-01T00:00:00Z';CommandLine='"'+$wslServicePath+'"'}
$script:wslService=[pscustomobject]@{Name='WSLService';State='Running';StartName='LocalSystem';PathName='"'+$wslServicePath+'"';ProcessId=4380}
$script:relaySid=$script:bridgeAccountSid;$script:parentSid='S-1-5-18';$script:ownerCode=0
$script:wslPathBad=$false;$script:wslPathVersion='one';$script:wslSnapshotDrift=$false;$script:wslServiceReads=0
function Get-CimInstance {
    param($ClassName,$Filter,$ErrorAction)
    if($ClassName -eq 'Win32_Service' -and $Filter -eq "Name='WSLService'") {
        $script:wslServiceReads++
        if($script:wslSnapshotDrift -and $script:wslServiceReads % 2 -eq 0){$script:relay.CreationDate=$script:relay.CreationDate.AddSeconds(1)}
        return $script:wslService
    }
    if($ClassName -eq 'Win32_Process' -and $Filter -eq ('ProcessId='+$script:relay.ProcessId)){return $script:relay}
    if($ClassName -eq 'Win32_Process' -and $Filter -eq ('ProcessId='+$script:wslParent.ProcessId)){return $script:wslParent}
    throw 'Unexpected WSL observation'
}
function Invoke-CimMethod{param($InputObject,$MethodName,$ErrorAction) if($MethodName -ne 'GetOwnerSid'){throw 'Unexpected mutation'};return [pscustomobject]@{ReturnValue=$script:ownerCode;Sid=$(if($InputObject.ProcessId -eq $script:relay.ProcessId){$script:relaySid}else{$script:parentSid})}}
function Get-PreparationWslPathObservation{param($Path,$Directory,$VolumeRoot) if($script:wslPathBad){throw 'Unsafe path'};return [ordered]@{path=$Path;directory=$Directory;volume=$VolumeRoot;identity=$script:wslPathVersion;hash='signed-fixture';acl='safe-fixture'}}
function Stop-Process{throw 'Companion must never be terminated'}
function Remove-NetTCPConnection{throw 'Companion must never be removed'}
$ipv4=$script:listeners[0];$relayListener=[pscustomobject]@{LocalAddress='::1';LocalPort=80;OwningProcess=1992}
$script:listeners=@($ipv4,$relayListener)
$r=Probe
Assert ($r.blockers.Count -eq 0 -and $r.bridge_ready -and !$r.action -and $r.preserved_companions.Count -eq 1 -and $r.preserved_companions[0].classification -eq 'windows_wsl_companion_preserve') 'exact signed protected WSL companion preserved beside owned IPv4'
$script:ipHelperUnavailable=$true
$candidate=Probe
Assert ($candidate.blockers -contains 'foreign_or_unknown_listener' -and $candidate.preserved_companions.Count -eq 0) 'relay rejects IP Helper PID without verified identity'
$ipv4.OwningProcess=4
$candidate=Probe
Assert ($candidate.blockers.Count -eq 0 -and $candidate.preserved_companions.Count -eq 1) 'System IPv4 owner remains independent of unavailable IP Helper'
$ipv4.OwningProcess=42;$script:ipHelperUnavailable=$false
foreach($duplicate in @('record','mapping')) {
    $savedProxyRecords=$script:records;$savedProxyMappings=$script:state.mappings
    if($duplicate -eq 'record'){$script:records=@($script:records[0],$script:records[0])}
    else{$script:state.mappings=@($script:state.mappings[0],$script:state.mappings[0])}
    $candidate=Probe
    Assert ($candidate.blockers -contains 'foreign_or_unknown_listener' -and $candidate.preserved_companions.Count -eq 0) ('relay refuses duplicate protected '+$duplicate)
    $script:records=$savedProxyRecords;$script:state.mappings=$savedProxyMappings
}
foreach($port in @(443,8086,16081)) {
    $mappings[0].ListenPort=$port;$mappings[0].ConnectPort=$port
    $script:state.mappings[0].listenPort=$port;$script:state.mappings[0].connectPort=$port
    $script:records[0].ListenPort=$port;$script:records[0].ConnectPort=$port
    $ipv4.LocalPort=$port;$relayListener.LocalPort=$port
    $candidate=Probe
    Assert ($candidate.blockers.Count -eq 0 -and $candidate.preserved_companions.Count -eq 1 -and !$candidate.action) ('mapped relay companion accepted: '+$port)
}
$mappings[0].ListenPort=80;$mappings[0].ConnectPort=80
$script:state.mappings[0].listenPort=80;$script:state.mappings[0].connectPort=80
$script:records[0].ListenPort=80;$script:records[0].ConnectPort=80
$ipv4.LocalPort=80;$relayListener.LocalPort=80
$relayFingerprint=$r.fingerprint
Assert ((Probe).fingerprint -eq $relayFingerprint) 'stable full relay proof deterministic'
# The production mapping resolver includes validated config additions alongside registry entries.
$savedMappings=$mappings;$savedStateMappings=$script:state.mappings
$savedRecords=$script:records;$savedListeners=$script:listeners
$config | Add-Member -NotePropertyName additionalPortMappings -NotePropertyValue @([pscustomobject]@{listenPort=16081;connectPort=16081})
$mappings=@(Get-PortMappings $config $savedMappings)
$script:state.mappings=@($savedStateMappings)+@([pscustomobject]@{listenPort=16081;connectPort=16081})
$script:records=@($savedRecords)+@([pscustomobject]@{ListenAddress='0.0.0.0';ListenPort=16081;ConnectAddress=$ObservedAddress;ConnectPort=16081})
$script:listeners=@($savedListeners)+@([pscustomobject]@{LocalAddress='0.0.0.0';LocalPort=16081;OwningProcess=42},[pscustomobject]@{LocalAddress='::1';LocalPort=16081;OwningProcess=1992})
$candidate=Probe
Assert ($mappings.Count -eq 2 -and $candidate.blockers.Count -eq 0 -and $candidate.preserved_companions.Count -eq 2 -and !$candidate.action) 'actual resolver validated config addition companion accepted'
$mappings=$savedMappings;$script:state.mappings=$savedStateMappings;$script:records=$savedRecords;$script:listeners=$savedListeners
$config.PSObject.Properties.Remove('additionalPortMappings')
$script:listeners=@($savedListeners)+@([pscustomobject]@{LocalAddress='::1';LocalPort=7750;OwningProcess=1992})
$candidate=Probe
Assert ($candidate.preserved_companions.Count -eq 1 -and $candidate.fingerprint -eq $relayFingerprint -and !$candidate.action) 'same PID outside resolved mappings is neither companion nor mutation target'
$script:listeners=$savedListeners
$ownership=Get-BridgeServiceOwnership
foreach($badMapping in @([pscustomobject]@{ListenPort=7750;ConnectPort=7750},[pscustomobject]@{ListenPort=80;ConnectPort=81},[pscustomobject]@{ListenPort=0;ConnectPort=80},[pscustomobject]@{ListenPort=65536;ConnectPort=80})) {
    $reads=$script:wslServiceReads
    $proof=Get-PreparationWslRelayProof $relayListener $script:listeners $script:records $script:state $ownership $badMapping $config @(4,42) $mappings
    Assert ($null -eq $proof -and $script:wslServiceReads -eq $reads) 'noncanonical helper mapping rejected before provenance observation'
}
$proof=Get-PreparationWslRelayProof $relayListener $script:listeners $script:records $script:state $ownership $mappings[0] $config @(4,42)
Assert ($null -eq $proof) 'helper without resolved mapping authority fails closed'
$proof=Get-PreparationWslRelayProof $relayListener $script:listeners $script:records $null $ownership $mappings[0] $config @(4,42) $mappings
Assert ($null -eq $proof) 'missing protected state rejects companion'
$script:state.mappings=@()
$candidate=Probe
Assert ($candidate.blockers -contains 'foreign_or_unknown_listener' -and !$candidate.action) 'missing protected state mapping rejects companion'
$script:state.mappings=$savedStateMappings
$script:state.mappings[0].connectPort=81
$candidate=Probe
Assert ($candidate.blockers -contains 'foreign_or_unknown_listener' -and !$candidate.action) 'mismatched protected state mapping rejects companion'
$script:state.mappings[0].connectPort=80
$savedCommand=$script:relay.CommandLine
$script:relay.CommandLine='"'+$relayPath+'"'+$savedCommand
Assert ((Probe).blockers.Count -eq 0) 'canonical exe-prefixed argument variant accepted'
$script:relay.CommandLine=$savedCommand
foreach($entry in @(@('relay','ParentProcessId',999),@('relay','ExecutablePath','C:\foreign\wslrelay.exe'),@('wslParent','ExecutablePath','C:\foreign\wslservice.exe'),@('wslService','Name','foreign'),@('wslService','State','Stopped'),@('wslService','StartName','foreign'),@('wslService','PathName','C:\foreign\wslservice.exe'),@('wslService','ProcessId',999),@('wslParent','CreationDate',[datetime]'2026-01-01T02:00:00Z'))) {
    $target=Get-Variable -Name $entry[0] -Scope Script -ValueOnly;$old=$target.($entry[1]);$target.($entry[1])=$entry[2]
    $r=Probe;Assert ($r.blockers -contains 'foreign_or_unknown_listener' -and !$r.action -and $r.preserved_companions.Count -eq 0) ('relay guard '+$entry[0]+'.'+$entry[1])
    $target.($entry[1])=$old
}
foreach($bad in @(($savedCommand.Replace('--mode 1','--mode 2')),($savedCommand.Replace('--vm-id {','--vm-id invalid{')),($savedCommand+' --extra'),('foreign '+$savedCommand),($savedCommand.Replace('--handle 2856','--handle -1')))) {
    $script:relay.CommandLine=$bad;Assert ((Probe).blockers -contains 'foreign_or_unknown_listener') ('strict observed relay arguments reject unknown variants: '+[string]$bad)
}
$script:relay.CommandLine=$savedCommand
foreach($field in @('relaySid','parentSid','bridgeAccountSid')) {
    $old=Get-Variable -Name $field -Scope Script -ValueOnly;Set-Variable -Name $field -Scope Script -Value 'S-1-5-21-9-9-9-9'
    Assert ((Probe).blockers -contains 'foreign_or_unknown_listener') ('selected protected account guard '+$field)
    Set-Variable -Name $field -Scope Script -Value $old
}
$script:ownerCode=5;Assert ((Probe).blockers -contains 'foreign_or_unknown_listener') 'owner query failure rejected';$script:ownerCode=0
$script:wslPathBad=$true;Assert ((Probe).blockers -contains 'foreign_or_unknown_listener') 'unsafe executable or ancestor blocks relay';$script:wslPathBad=$false
foreach($address in @('::','::ffff:127.0.0.1','127.0.0.1')) {
    $relayListener.LocalAddress=$address;Assert ((Probe).blockers -contains 'foreign_or_unknown_listener') 'only literal IPv6 loopback companion accepted'
}
$relayListener.LocalAddress='::1'
$script:listeners=@($relayListener);Assert ((Probe).blockers -contains 'foreign_or_unknown_listener') 'relay without IPv4 listener rejected';$script:listeners=@($ipv4,$relayListener)
$ipv4.OwningProcess=43;Assert ((Probe).blockers -contains 'foreign_or_unknown_listener') 'relay never excuses foreign IPv4 listener';$ipv4.OwningProcess=42
$record=$script:records[0];$script:records=@();Assert ((Probe).blockers -contains 'foreign_or_unknown_listener') 'relay without protected proxy record rejected';$script:records=@($record)
$record.ConnectPort=81;Assert ((Probe).blockers -contains 'foreign_or_unknown_listener') 'relay requires exact destination port';$record.ConnectPort=80
$script:listeners+= [pscustomobject]@{LocalAddress='::';LocalPort=80;OwningProcess=999};Assert ((Probe).blockers -contains 'foreign_or_unknown_listener') 'recognized companion never excuses another foreign listener';$script:listeners=@($ipv4,$relayListener)
foreach($mutation in @('creation','parent_creation','command','path_identity','service_parent','service_pid','relay_pid','bridge_sid')) {
    $beforeRelay=(Probe).fingerprint
    switch($mutation){
        'creation'{$script:relay.CreationDate=$script:relay.CreationDate.AddSeconds(1)}
        'parent_creation'{$script:wslParent.CreationDate=$script:wslParent.CreationDate.AddSeconds(1)}
        'command'{$script:relay.CommandLine=$script:relay.CommandLine.Replace('2856','2857')}
        'path_identity'{$script:wslPathVersion='two'}
        'service_parent'{$script:wslParent.ParentProcessId++}
        'service_pid'{$script:wslParent.ProcessId++;$script:wslService.ProcessId=$script:wslParent.ProcessId;$script:relay.ParentProcessId=$script:wslParent.ProcessId}
        'relay_pid'{$script:relay.ProcessId++;$relayListener.OwningProcess=$script:relay.ProcessId}
        'bridge_sid'{$script:bridgeAccountSid='S-1-5-21-404-505-606-1002';$script:relaySid=$script:bridgeAccountSid}
    }
    $r=Probe;Assert ($r.blockers.Count -eq 0 -and $r.fingerprint -ne $beforeRelay) ('full inventory binds relay provenance '+$mutation)
}
# Every second query is the actual fresh socket observation inside the proof.
$script:socketRead=0;$script:socketChange=''
function Get-NetTCPConnection {
    param($State,$ErrorAction)
    $script:socketRead++
    if($script:socketRead % 2 -eq 0) {
        $copy=@($script:listeners | ForEach-Object{[pscustomobject]@{LocalAddress=$_.LocalAddress;LocalPort=$_.LocalPort;OwningProcess=$_.OwningProcess}})
        switch($script:socketChange) {
            'missing_relay'{return @($copy | Where-Object{$_.LocalAddress -ne '::1'})}
            'missing_ipv4'{return @($copy | Where-Object{$_.LocalAddress -eq '::1'})}
            'relay_pid'{$copy[1].OwningProcess++;return $copy}
            'ipv4_pid'{$copy[0].OwningProcess++;return $copy}
            'extra'{return @($copy)+@([pscustomobject]@{LocalAddress='::';LocalPort=80;OwningProcess=999})}
            'duplicate'{return @($copy)+@($copy[1])}
            'query_failure'{throw 'Socket inventory unavailable'}
            'reorder'{[array]::Reverse($copy);return $copy}
        }
    }
    return $script:listeners
}
foreach($change in @('missing_relay','missing_ipv4','relay_pid','ipv4_pid','extra','duplicate','query_failure')) {
    $script:socketRead=0;$script:socketChange=$change;$r=Probe
    Assert ($r.blockers -contains 'foreign_or_unknown_listener' -and $r.preserved_companions.Count -eq 0 -and !$r.action) ('fresh socket drift blocks '+$change)
}
$script:socketRead=0;$script:socketChange='reorder';$r=Probe
Assert ($r.blockers.Count -eq 0 -and $r.preserved_companions.Count -eq 1) 'socket order alone is not drift'
$script:socketChange='';$script:socketRead=0
function Get-NetTCPConnection{param($State,$ErrorAction) return $script:listeners}
$script:wslSnapshotDrift=$true;$script:wslServiceReads=0
Assert ((Probe).blockers -contains 'foreign_or_unknown_listener') 'before-after relay process drift blocks recognition'
$script:wslSnapshotDrift=$false
Remove-Item function:Get-CimInstance,function:Invoke-CimMethod,function:Stop-Process,function:Remove-NetTCPConnection
Set-Item function:Get-PreparationWslPathObservation $originalWslPathObservation
$script:records=@();$script:listeners=@()

${function:Get-PreparationIpHelperIdentity}=$originalIpHelperIdentity
# Model the adapted CIM representation from shipped NetSecurity types/CDXML.
$formatterAssembly=Join-Path $env:windir 'System32/WindowsPowerShell/v1.0/Modules/NetSecurity/Microsoft.Windows.Firewall.Commands.dll'
[void][Reflection.Assembly]::Load([IO.File]::ReadAllBytes($formatterAssembly))
$any=[Microsoft.Windows.Firewall.Commands.Formatting.Formatter]::FormatNullableString($null)
Assert ($any -eq 'Any') 'actual shipped CIM null-string formatter emits Any'
$anyArray=[Microsoft.Windows.Firewall.Commands.Formatting.Formatter]::FormatNullableStringArray($null)
Assert (@($anyArray).Count -eq 1 -and $anyArray[0] -eq 'Any') 'actual shipped CIM null-array formatter emits Any'
function CanonicalFilters {
    return @{
        ports=@([pscustomobject]@{InstanceID='rule';Protocol='TCP';LocalPort='80';RemotePort=@('Any');DynamicTarget=[uint32]0})
        addresses=@([pscustomobject]@{InstanceID='rule';LocalAddress=@('Any');RemoteAddress=@('Any')})
        applications=@([pscustomobject]@{InstanceID='rule';Program='Any';Package=$null;PackageObserved=$true})
        interfaces=@([pscustomobject]@{InstanceID='rule';InterfaceAlias=@('Any')})
        interface_types=@([pscustomobject]@{InstanceID='rule';InterfaceType=[uint32]0})
        security=@([pscustomobject]@{InstanceID='rule';Authentication=[uint16]0;Encryption=[uint16]0;OverrideBlockRules=$false;LocalUser='Any';RemoteUser='Any';RemoteMachine='Any'})
        services=@([pscustomobject]@{InstanceID='rule';Service='Any'})
    }
}
# Exercise the original family reader, not the later policy fixture override.
function ResetBatchFixture {
    $script:batchRows=CanonicalFilters;$script:batchCalls=@{};$script:batchFailure='';$script:partialFailure=$false
    $script:batchRows.applications[0].PSObject.Properties.Remove('PackageObserved')
    foreach($kind in @($script:batchRows.Keys)){
        $foreign=$script:batchRows[$kind][0].PSObject.Copy();$foreign.InstanceID='rule-extra'
        $script:batchRows[$kind]=@($script:batchRows[$kind][0],$foreign)
    }
}
function ReadBatchFixture($Kind,$All,$Rule) {
    $script:batchCalls[$Kind]++
    if($script:batchFailure -ceq $Kind){
        if($script:partialFailure){Write-Output $script:batchRows[$Kind][0];Write-Error 'fixture_partial_family_error'}
        throw 'fixture_family_unavailable'
    }
    if(!$All){return @($script:batchRows[$Kind]|Where-Object{$_.InstanceID -eq $Rule.Name})}
    return $script:batchRows[$Kind]
}
function Get-NetFirewallPortFilter{[CmdletBinding()]param([switch]$All,[Parameter(ValueFromPipeline=$true)]$Rule) process{ReadBatchFixture 'ports' $All $Rule}}
function Get-NetFirewallAddressFilter{[CmdletBinding()]param([switch]$All,[Parameter(ValueFromPipeline=$true)]$Rule) process{ReadBatchFixture 'addresses' $All $Rule}}
function Get-NetFirewallApplicationFilter{[CmdletBinding()]param([switch]$All,[Parameter(ValueFromPipeline=$true)]$Rule) process{ReadBatchFixture 'applications' $All $Rule}}
function Get-NetFirewallInterfaceFilter{[CmdletBinding()]param([switch]$All,[Parameter(ValueFromPipeline=$true)]$Rule) process{ReadBatchFixture 'interfaces' $All $Rule}}
function Get-NetFirewallInterfaceTypeFilter{[CmdletBinding()]param([switch]$All,[Parameter(ValueFromPipeline=$true)]$Rule) process{ReadBatchFixture 'interface_types' $All $Rule}}
function Get-NetFirewallSecurityFilter{[CmdletBinding()]param([switch]$All,[Parameter(ValueFromPipeline=$true)]$Rule) process{ReadBatchFixture 'security' $All $Rule}}
function Get-NetFirewallServiceFilter{[CmdletBinding()]param([switch]$All,[Parameter(ValueFromPipeline=$true)]$Rule) process{ReadBatchFixture 'services' $All $Rule}}
$batchRules=@([pscustomobject]@{Name='rule';Profile=[uint16]0})
ResetBatchFixture
$batch=& $originalFirewallFilters -Rules $batchRules
Assert (Test-PreparationFirewallPolicyCanonical $batchRules $batch) 'batched native projections preserve canonical policy'
foreach($kind in @('ports','addresses','applications','interfaces','interface_types','security','services')){
    Assert ($script:batchCalls[$kind] -eq 1 -and @($batch[$kind]).Count -eq 1) ('one family read excludes near foreign identity '+$kind)
}
ResetBatchFixture
$manyRules=@(0..23|ForEach-Object{[pscustomobject]@{Name=('owned-'+$_);Profile=[uint16]0}})
foreach($kind in @($script:batchRows.Keys)){
    $template=$script:batchRows[$kind][0];$foreign=$script:batchRows[$kind][1]
    $script:batchRows[$kind]=@($manyRules|ForEach-Object{$copy=$template.PSObject.Copy();$copy.InstanceID=$_.Name;$copy})+@($foreign)
}
$batch=& $originalFirewallFilters -Rules $manyRules
Assert (Test-PreparationFirewallPolicyCanonical $manyRules $batch) 'complete 24-rule projections preserve policy'
foreach($kind in @('ports','addresses','applications','interfaces','interface_types','security','services')){
    Assert ($script:batchCalls[$kind] -eq 1) ('one query covers all owned rules '+$kind)
}
ResetBatchFixture;$empty=& $originalFirewallFilters -Rules @()
Assert ($empty.Count -eq 0 -and $script:batchCalls.Count -eq 0) 'zero rules make no filter family queries'
ResetBatchFixture
foreach($kind in @($script:batchRows.Keys)){$script:batchRows[$kind][0].InstanceID='RuLe'}
$batch=& $originalFirewallFilters -Rules $batchRules
Assert (Test-PreparationFirewallPolicyCanonical $batchRules $batch) 'exact rule identity matches native case-insensitive contract'
foreach($kind in @('ports','addresses','applications','interfaces','interface_types','security','services')){
    foreach($shape in @('missing','duplicate','thrown','partial')){
        ResetBatchFixture
        switch($shape){
            'missing'{$script:batchRows[$kind]=@($script:batchRows[$kind][1])}
            'duplicate'{$script:batchRows[$kind]=@($script:batchRows[$kind][0],$script:batchRows[$kind][0])}
            'thrown'{$script:batchFailure=$kind}
            'partial'{$script:batchFailure=$kind;$script:partialFailure=$true}
        }
        $blocked=$false
        try{$batch=& $originalFirewallFilters -Rules $batchRules;$blocked=!(Test-PreparationFirewallPolicyCanonical $batchRules $batch)}catch{$blocked=$true}
        Assert $blocked ('family observation never permits incomplete or ambiguous policy '+$kind+' '+$shape)
    }
}
foreach($shape in @('missing_package','restricted_application','missing_remote_port','missing_rule_id','empty_rule_id','duplicate_rule_id')){
    ResetBatchFixture;$selectedRules=$batchRules
    switch($shape){
        'missing_package'{$script:batchRows.applications[0].PSObject.Properties.Remove('Package')}
        'restricted_application'{$script:batchRows.applications[0].Program='restricted-app'}
        'missing_remote_port'{$script:batchRows.ports[0].PSObject.Properties.Remove('RemotePort')}
        'missing_rule_id'{$selectedRules=@([pscustomobject]@{Profile=[uint16]0})}
        'empty_rule_id'{$selectedRules=@([pscustomobject]@{Name=' ';Profile=[uint16]0})}
        'duplicate_rule_id'{$selectedRules=@($batchRules[0],$batchRules[0])}
    }
    $blocked=$false
    try{$batch=& $originalFirewallFilters -Rules $selectedRules;$blocked=!(Test-PreparationFirewallPolicyCanonical $selectedRules $batch)}catch{$blocked=$true}
    Assert $blocked ('batch retrieval preserves malformed/restricted observation refusal '+$shape)
}
foreach($name in @('Get-NetFirewallPortFilter','Get-NetFirewallAddressFilter','Get-NetFirewallApplicationFilter','Get-NetFirewallInterfaceFilter','Get-NetFirewallInterfaceTypeFilter','Get-NetFirewallSecurityFilter','Get-NetFirewallServiceFilter')){Remove-Item ('Function:\'+$name)}
$script:rules=@([pscustomobject]@{Name='rule';DisplayName='Tiny Swarm World TCP 80';Enabled=$true;Direction='Inbound';Action='Allow';Profile=[uint16]0})
$script:policyFilters=CanonicalFilters;$r=Probe
Assert ($r.bridge_ready -and !$r.action) 'unrestricted observed CIM defaults retain ready no-op'
foreach($entry in @(@('ports','RemotePort',@('443')),@('ports','DynamicTarget','WifiDirectPrinting'),@('addresses','LocalAddress',@('127.0.0.1')),@('addresses','RemoteAddress',@('LocalSubnet')),@('applications','Program','restricted-app'),@('applications','Package','S-1-15-2-1'),@('interfaces','InterfaceAlias',@('Ethernet')),@('interface_types','InterfaceType','Wired'),@('security','Authentication','Required'),@('security','Encryption','Required'),@('security','OverrideBlockRules',$true),@('security','LocalUser','restricted-owner'),@('security','RemoteUser','restricted-user'),@('security','RemoteMachine','restricted-machine'),@('services','Service','restricted-service'))) {
    $script:policyFilters=CanonicalFilters;$script:policyFilters[$entry[0]][0].($entry[1])=$entry[2]
    $r=Probe
    Assert ($r.blockers -contains 'owned_firewall_policy_conflict' -and !$r.bridge_ready -and !$r.action) ('administrator restriction preserved '+$entry[0]+'.'+$entry[1])
}
$script:policyFilters=CanonicalFilters;$script:rules[0].Profile='Private';$r=Probe
Assert ($r.blockers -contains 'owned_firewall_policy_conflict' -and !$r.action) 'administrator profile restriction preserved'
$script:rules[0].Profile=[uint16]0
foreach($shape in @('missing_group','duplicate_filter','missing_package','missing_override','missing_property','unobserved_package')) {
    $script:policyFilters=CanonicalFilters
    switch($shape){
        'missing_group'{$script:policyFilters.Remove('addresses')}
        'duplicate_filter'{$script:policyFilters.addresses+= $script:policyFilters.addresses[0]}
        'missing_package'{$script:policyFilters.applications[0].PSObject.Properties.Remove('Package')}
        'unobserved_package'{$script:policyFilters.applications[0].PackageObserved=$false}
        'missing_override'{$script:policyFilters.security[0].PSObject.Properties.Remove('OverrideBlockRules')}
        'missing_property'{$script:policyFilters.addresses[0].PSObject.Properties.Remove('RemoteAddress')}
    }
    $r=Probe;Assert ($r.blockers -contains 'owned_firewall_policy_conflict' -and !$r.action) ('unknown filter observation blocks '+$shape)
}
$script:rules=@();$script:policyFilters=$null
$script:state.generatedAt=[DateTimeOffset]::Now.AddMinutes(-10).ToString('o');$r=Probe;Assert (!$r.agent_ready -and $r.action -eq 'refresh') 'stale heartbeat not ready'
$script:state.generatedAt=[DateTimeOffset]::Now.ToString('o')
$ObservedAddress='172.20.0.3';$script:routing=$false;$r=Probe;Assert ($r.action -eq 'refresh' -and !$r.bridge_ready -and $r.fingerprint -ne $before) 'changed address invalidates plan and delegates refresh'
$beforeFilters=(Probe).fingerprint;$script:filterPort='81';$r=Probe;Assert ($r.fingerprint -ne $beforeFilters -and !$r.bridge_ready) 'same nonready state binds port-filter drift'
$beforeFilters=$r.fingerprint;$script:filterProtocol='UDP';$r=Probe;Assert ($r.fingerprint -ne $beforeFilters) 'same nonready state binds protocol-filter drift'
$beforeHeartbeat=$r.fingerprint;$script:state.agentStatus='degraded';$r=Probe;Assert ($r.fingerprint -ne $beforeHeartbeat) 'same nonready state binds protected heartbeat status'
$script:state.agentStatus='ready'
$script:installedConfig=[pscustomobject]@{distro='auto'};$r=Probe;Assert ($r.action -eq 'install') 'selected distro config upgrade through existing lifecycle'
$script:installedConfig=$config
foreach($address in @('127.0.0.1','0.0.0.0','invalid')){$ObservedAddress=$address;$threw=$false;try{Probe | Out-Null}catch{$threw=$true};Assert $threw 'unsafe observed address rejected'}
$ObservedAddress='172.20.0.2';$Distro='auto';$threw=$false;try{Probe | Out-Null}catch{$threw=$true};Assert $threw 'auto selection refused'
# Existing reconciliation owner consumes changing observed addresses; no new updater.
$Distro='';$script:agentAddress='172.20.0.2';$script:converged=@()
function Get-WslIp{param($Config) return $script:agentAddress}
function Enter-BridgeMutex{param($Name) return $null}
function Exit-BridgeMutex{param($Mutex)}
function Write-StateFile{param($Config,$WslIp,$Mappings,$HostNames,$RegistryPath,$Discovery)}
function Reconcile-PortProxy{param($Config,$WslIp,$Mappings) $script:converged+= $WslIp}
function Reconcile-FirewallRules{param($Config,$Mappings)}
function Reconcile-HostsFile{param($Config,$HostNames)}
function Get-BridgeDiscovery{param($Config,$WslIp,$Mappings,$HostNames) return [pscustomobject]@{Ready=$true;WslIp=$WslIp;DiscoveryIntervalMinutes=1;DriftReasons=@()}}
function Write-BridgeDiscovery{param($Discovery)}
Invoke-BridgeReconcile $config $mappings $hostNames 'registry'
$script:agentAddress='172.20.0.3';Invoke-BridgeReconcile $config $mappings $hostNames 'registry'
Assert (($script:converged -join ',') -eq '172.20.0.2,172.20.0.3') 'existing agent converges changed addresses'
# Explicit preparation keeps its consented address; the unbound agent above converges.
${function:Get-WslIp}=$originalIpFunction
$Distro='Ubuntu-24.04';$ObservedAddress='172.20.0.2';$Action='refresh'
function wsl.exe{$global:LASTEXITCODE=0;return '172.20.0.3'}
$previousConverged=$script:converged.Count;$threw=$false
try{Invoke-BridgeReconcile $config $mappings $hostNames 'registry'}catch{$threw=$true}
Assert ($threw -and $script:converged.Count -eq $previousConverged) 'fresh apply address drift blocks before route writes'
$Action='install';$script:installCalls=0
function Get-BridgePrerequisiteResults{param($Config) try{Get-WslIp $Config | Out-Null;return @(New-BridgePrerequisiteResult 'wsl-ipv4' $true 'ready')}catch{return @(New-BridgePrerequisiteResult 'wsl-ipv4' $false 'address drift')}}
function Read-TswPortRegistry{param($RegistryPath) return [pscustomobject]@{Mappings=$mappings;HostNames=$hostNames}}
function Get-PortMappings{param($Config,$RegistryMappings) return $RegistryMappings}
function Get-BridgeHostNames{param($Config,$RegistryHostNames) return $RegistryHostNames}
$script:installedConfig=$config
function Get-BridgePreparationInventory{param($Config,$Mappings,$HostNames,$RegistryPath) return @{blockers=@();action='install'}}
function Install-BridgeService{param($ResolvedConfigPath,$ResolvedPortRegistryPath,$Config) $script:installCalls++}
$threw=$false;try{Invoke-BridgeAction}catch{$threw=$true}
Assert ($threw -and $script:installCalls -eq 0) 'fresh install address drift blocks service and credential mutations'
$Action='refresh'
# Run the actual credential dialog owner with harmless mocked credentials.
${function:Request-BridgeServiceCredential}=$originalCredentialFunction
$script:credential=[pscustomobject]@{UserName='owner'}
function Get-Credential{param($UserName,$Message) return $script:credential}
function Test-BridgeServiceAccountMatchesCurrentIdentity{param($AccountName) return $AccountName -eq 'owner'}
$c=Request-BridgeServiceCredential 'owner';Assert ($c.UserName -eq 'owner') 'existing credential owner accepts matching identity'
$script:credential=[pscustomobject]@{UserName='foreign'};$threw=$false;try{Request-BridgeServiceCredential 'owner' | Out-Null}catch{$threw=$true};Assert $threw 'foreign credential owner blocked'
$script:credential=$null;$threw=$false;try{Request-BridgeServiceCredential 'owner' | Out-Null}catch{$threw=$true};Assert $threw 'credential cancellation stops'
. (Join-Path $RepositoryRoot 'tools/windows/preparation/Bridge.ps1')
$script:bridgeProbeCalls=@()
function Get-PreparationExecutable{param($Name) return $Name}
function Invoke-PreparationProcess{param($Executable,$Arguments,$TimeoutSeconds) $script:bridgeProbeCalls+=,@($Arguments);return @{exit_code=0;stdout='Ubuntu-26.04';stderr=''}}
$o=@{Distro='Ubuntu-24.04';ProbeTimeoutSeconds=15;RepositoryRoot=$RepositoryRoot}
$r=Get-PreparationBridgeInventory $o @{running=$true;pid1='systemd'}
Assert ($r.blockers -contains 'selected_distro_stopped' -and $script:bridgeProbeCalls.Count -eq 1 -and ($script:bridgeProbeCalls[0] -join ',') -eq '--list,--running,--quiet') 'stale running facts never start stopped selected distro'
$script:bridgeProbeCalls=@();$r=Get-PreparationBridgeInventory $o @{running=$false;pid1='systemd'}
Assert ($script:bridgeProbeCalls.Count -eq 0) 'known stopped lifecycle emits no native probe'
$script:bridgeProbeCalls=@()
function Invoke-PreparationProcess{param($Executable,$Arguments,$TimeoutSeconds) $script:bridgeProbeCalls+=,@($Arguments);return @{exit_code=0;stdout='Ubuntu-24.04';stderr=''}}
$r=Get-PreparationBridgeInventory $o @{running=$true;pid1='systemd'}
Assert ($r.blockers -contains 'observed_wsl_address_required' -and $script:bridgeProbeCalls.Count -eq 1 -and ($script:bridgeProbeCalls[0] -join ',') -eq '--list,--running,--quiet') 'W06 no distro exec even when observed address missing'
# Exercise the actual W06 Execute adapter with transport/inventory ports mocked.
$script:bridgeEffectCode=0;$script:freshFingerprint='approved';$script:postReady=$true;$script:bridgeNativeCalls=0;$script:bridgeReads=0
function Get-PreparationBridgeInventory{param($Options,$Facts) $script:bridgeReads++;return @{fingerprint=$script:freshFingerprint;observed_address='172.20.0.2';bridge_ready=$(if($script:bridgeReads -gt 1){$script:postReady}else{$false});blockers=@()}}
function Invoke-PreparationBridgeProcess{param($Options,$Action,$Address,$TimeoutSeconds) $script:bridgeNativeCalls++;return @{exit_code=$script:bridgeEffectCode;stdout='';stderr=''}}
$o.ActionTimeoutSeconds=15
$a=@{id='bridge_refresh';operation='refresh';before=@{fingerprint='approved'}}
$r=Invoke-PreparationBridgeAction $a $o @{running=$true;pid1='systemd'} 'test-store'
Assert ($r.exit_code -eq 0 -and $r.confirmed -and !$r.uncertain -and $script:bridgeNativeCalls -eq 1) 'actual bridge execute delegates and verifies registration/agent'
$script:bridgeReads=0;$script:freshFingerprint='stale';$previousCalls=$script:bridgeNativeCalls;$r=Invoke-PreparationBridgeAction $a $o @{} 'test-store'
Assert (!$r.confirmed -and !$r.uncertain -and $r.cause -eq 'bridge_consent_drift' -and $script:bridgeNativeCalls -eq $previousCalls) 'actual bridge execute blocks fresh drift before transport'
foreach($code in @(124,130,1)){$script:bridgeReads=0;$script:freshFingerprint='approved';$script:bridgeEffectCode=$code;$r=Invoke-PreparationBridgeAction $a $o @{} 'test-store';Assert ($r.exit_code -eq $code -and $r.confirmed) 'nonzero transport preserves separately observed ready effect'}
$script:bridgeReads=0;$script:bridgeEffectCode=0;$script:postReady=$false;$r=Invoke-PreparationBridgeAction $a $o @{} 'test-store'
Assert (!$r.confirmed -and $r.uncertain -and $r.cause -eq 'bridge_postcheck_failed') 'zero transport never implies ready postcheck'
Write-Output "PASS $count mocked W06 bridge checks; no live infrastructure"
