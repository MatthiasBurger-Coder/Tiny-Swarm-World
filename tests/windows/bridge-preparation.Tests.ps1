param([Parameter(Mandatory=$true)][string]$RepositoryRoot)
$ErrorActionPreference='Stop'
Import-Module Microsoft.PowerShell.Utility
Import-Module Microsoft.PowerShell.Management
. (Join-Path $RepositoryRoot 'tools/windows/tws-wsl-bridge.ps1')
$count=0
$originalIpFunction=${function:Get-WslIp}
$originalCredentialFunction=${function:Request-BridgeServiceCredential}
function Assert($Value,$Name){if(!$Value){throw "FAIL: $Name"};$script:count++}
# Only disposable test files are written; no host/service/routing resources.
$tempRoot=Join-Path ([IO.Path]::GetTempPath()) ('tsw-w06-test-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempRoot | Out-Null
try {
    $source=Join-Path $tempRoot 'source.json';$staged=Join-Path $tempRoot 'staged.json'
    [IO.File]::WriteAllText($source,'{"distro":"auto","listenAddress":"0.0.0.0"}')
    Copy-Item -LiteralPath $source -Destination $staged
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
function Get-BridgeServiceOwnership{return [pscustomobject]@{Status=$(if($script:owned){'owned'}else{'absent'});RequiresAdoption=$false;Service=[pscustomobject]@{Status='Running'}}}
function Assert-BridgeRuntimeStateAuthority{}
function Get-ProtectedBridgeState{return $script:state}
function Read-BridgeConfig{param($Path) return $script:installedConfig}
function Get-InstalledBridgeBundleIdOrEmpty{return 'bundle'}
function Get-PortProxyRecords{return $script:records}
function Get-NetFirewallRule{param($ErrorAction) return @()}
function Get-FirewallRuleSnapshot{param($Config) return [pscustomobject]@{Rules=$script:rules;FiltersByRuleId=@{rule=@{LocalPort=$script:filterPort;Protocol=$script:filterProtocol}}}}
function Get-PreparationFirewallFilters{param($Rules) if($null -ne $script:policyFilters){return $script:policyFilters};return @{ports=@{LocalPort=$script:filterPort;Protocol=$script:filterProtocol}}}
function Get-NetTCPConnection{param($State,$ErrorAction) return $script:listeners}
function Get-Content{param($LiteralPath,[switch]$Raw,$Encoding) return $script:hosts}
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
$script:running=$false;$r=Probe;Assert ($r.blockers -contains 'selected_distro_stopped' -and !$r.action) 'stopped distro never started';$script:running=$true
$script:records=@([pscustomobject]@{ListenAddress='0.0.0.0';ListenPort=80;ConnectAddress='172.20.0.8';ConnectPort=80});$r=Probe;Assert ($r.blockers -contains 'foreign_portproxy_collision') 'foreign proxy blocked';$script:records=@()
$script:rules=@([pscustomobject]@{Name='foreign';DisplayName='Tiny Swarm World TCP 80';Enabled=$true;Direction='Inbound';Action='Allow'});$r=Probe;Assert ($r.blockers -contains 'foreign_firewall_collision') 'foreign firewall preserved';$script:rules=@()
$script:listeners=@([pscustomobject]@{LocalAddress='127.0.0.1';LocalPort=80;OwningProcess=100});$r=Probe;Assert ($r.blockers -contains 'foreign_or_unknown_listener') 'unknown listener never killed';$script:listeners=@()
$script:hosts='127.0.0.2 jenkins.tsw.local';$r=Probe;Assert ($r.blockers -contains 'foreign_hosts_collision') 'foreign name preserved';$script:hosts='127.0.0.1 localhost'
$script:owned=$true
$script:state=[pscustomobject]@{generatedAt=[DateTimeOffset]::Now.ToString('o');agentMode='windows-service';agentStatus='ready';wslIp=$ObservedAddress;bundleId='bundle';configPath=$InstalledConfigPath;registryPath=$InstalledPortRegistryPath;listenAddress='0.0.0.0';firewallRulePrefix='Tiny Swarm World';mappings=@([pscustomobject]@{listenPort=80;connectPort=80})}
$r=Probe;Assert ($r.bridge_ready -and !$r.action) 'owned ready agent no-op'
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
