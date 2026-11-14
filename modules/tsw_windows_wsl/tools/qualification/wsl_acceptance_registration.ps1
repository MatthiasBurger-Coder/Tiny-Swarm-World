#requires -Version 5.1
<# Qualification-only import. Dot sourcing defines functions and performs no host action. #>
[CmdletBinding()]
param([ValidateSet('Plan','Import','Verify')][string]$Mode='Plan',
      [string]$ScenarioBase64='',[string]$ExpectedScenarioSha256='')
$ErrorActionPreference='Stop'

function Get-AcceptanceRegistrationDigest($Value){
 function Canonical($x){
  if($null -eq $x -or $x -is [string] -or $x -is [ValueType]){return $x}
  if($x -is [Collections.IDictionary]){$o=[ordered]@{};foreach($k in @($x.Keys|Sort-Object)){$o[$k]=Canonical $x[$k]};return $o}
  if($x -is [Collections.IEnumerable]){return ,@($x|ForEach-Object{Canonical $_})}
  $o=[ordered]@{};foreach($p in @($x.PSObject.Properties|Sort-Object Name)){$o[$p.Name]=Canonical $p.Value};return $o
 }
 $h=[Security.Cryptography.SHA256]::Create()
 try{return ([BitConverter]::ToString($h.ComputeHash([Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject (Canonical $Value) -Depth 40 -Compress))))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}
}
function Assert-AcceptanceRegistrationScenario($s){
 $fields=@('schema_version','operation','decision','run_id','host','source_commit','source_pins_sha256','preserve_sha256','image_sha256','image_signer','expires_utc')
 if($s -isnot [Collections.IDictionary] -or $s.Count -ne $fields.Count){throw 'SCENARIO_INVALID'}
 foreach($k in $fields){if(!$s.Contains($k)){throw 'SCENARIO_INVALID'}}
 foreach($k in $s.Keys){if($k -cnotin $fields){throw 'SCENARIO_INVALID'}}
 if($s.schema_version -isnot [int] -or $s.schema_version -ne 1 -or $s.operation -cne 'WSL_ACCEPTANCE_REGISTRATION' -or
    $s.decision -cnotin @('PLAN','GO') -or $s.run_id -isnot [string] -or $s.run_id -cnotmatch '\A[0-9a-f]{32}\z' -or
    $s.host -isnot [string] -or $s.host -cnotmatch '\A[A-Za-z0-9][A-Za-z0-9.-]{0,62}\z' -or
    $s.source_commit -isnot [string] -or $s.source_commit -cnotmatch '\A[0-9a-f]{40}\z'){throw 'SCENARIO_INVALID'}
 foreach($k in @('source_pins_sha256','preserve_sha256','image_sha256')){if($s[$k] -isnot [string] -or $s[$k] -cnotmatch '\A[0-9a-f]{64}\z'){throw 'SCENARIO_INVALID'}}
 if($s.image_sha256 -cne '48d56724b5c8e60f24893e83e73bbb58c60b3ca22fba3da977075420acd54104' -or
    $s.image_signer -cne '843938DF228D22F7B3742BC0D94AA3F0EFE21092' -or $s.expires_utc -isnot [string] -or
    $s.expires_utc -cnotmatch '\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\z'){throw 'SCENARIO_INVALID'}
 $when=[DateTimeOffset]::MinValue
 if(![DateTimeOffset]::TryParseExact($s.expires_utc,'yyyy-MM-ddTHH:mm:ssZ',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::AssumeUniversal,[ref]$when)){throw 'SCENARIO_INVALID'}
}
function Assert-AcceptanceRegistrationInventory($Before,$After,[string]$Name,[bool]$NewExpected){
 if($null -eq $Before -or $null -eq $After -or $Before.default -cne $After.default -or
    $Before.global_sha256 -cne $After.global_sha256 -or $Before.running_sha256 -cne $After.running_sha256){throw 'ORIGINAL_PRESERVATION_DRIFT'}
 $original=@($Before.registrations);$now=@($After.registrations)
 if($original.Count -lt 1 -or $original.Count -gt 32 -or $now.Count -gt 33){throw 'REGISTRATION_BOUND'}
 $ids=@{};$names=@{}
 foreach($row in $now){
  if($row.id -isnot [string] -or $row.id -cnotmatch '\A\{[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}\z' -or
     $row.name -isnot [string] -or !$row.name -or $ids.ContainsKey($row.id) -or $names.ContainsKey($row.name)){throw 'REGISTRATION_AMBIGUOUS'}
  $ids[$row.id]=$true;$names[$row.name]=$true
 }
 foreach($row in $original){
  $actual=@($now|Where-Object{$_.id -ceq $row.id})
  if($actual.Count -ne 1 -or (Get-AcceptanceRegistrationDigest $actual[0]) -cne (Get-AcceptanceRegistrationDigest $row)){throw 'ORIGINAL_PRESERVATION_DRIFT'}
 }
 $new=@($now|Where-Object{$_.id -cnotin @($original|ForEach-Object{$_.id})})
 if(!$NewExpected){if($new.Count -ne 0){throw 'REGISTRATION_COLLISION'};return $null}
 if($new.Count -ne 1 -or $new[0].name -cne $Name -or $new[0].version -isnot [int] -or $new[0].version -ne 2 -or $new[0].running -isnot [bool] -or $new[0].running -ne $false -or
    !$new[0].path_matches -or $new[0].vhd_identity -isnot [string] -or !$new[0].vhd_identity -or
    $new[0].rootfs_sha256 -isnot [string] -or $new[0].rootfs_sha256 -cnotmatch '\A[0-9a-f]{64}\z'){throw 'NEW_REGISTRATION_UNPROVEN'}
 return $new[0]
}
function Assert-AcceptanceRegistrationSourceView($View,$Scenario,$State,[byte[]]$Raw){
 if($Raw.Length -gt 131072){throw 'REGISTRATION_VIEW_BOUND'}
 $decoded=([Text.UTF8Encoding]::new($false,$true)).GetString($Raw)|ConvertFrom-Json -ErrorAction Stop
 if((Get-AcceptanceRegistrationDigest $decoded) -cne (Get-AcceptanceRegistrationDigest $State)){throw 'REGISTRATION_VIEW_PARSED_BINDING'}
 $fields=@('schema_version','run_id','source_commit','registered_source_commit','registration_scenario_sha256',
 'registration_state_sha256','original_guid','new_guid','original_vhd_sha256','new_vhd_sha256')
 $keys=if($View -is [Collections.IDictionary]){@($View.Keys)}else{@($View.PSObject.Properties.Name)}
 if($null -eq $View -or $keys.Count -ne $fields.Count -or @($keys|Where-Object{$_ -cnotin $fields}).Count){throw 'REGISTRATION_VIEW_FIELDS'}
 if($View.schema_version -isnot [int] -or $View.schema_version -ne 1 -or $View.run_id -cne $Scenario.run_id -or
 $View.source_commit -cnotmatch '\A[0-9a-f]{40}\z' -or $View.registered_source_commit -cne $Scenario.source_commit -or
 $View.registration_scenario_sha256 -cne (Get-AcceptanceRegistrationDigest $Scenario) -or $State.stage -cne 'registered' -or
 $State.scenario_sha256 -cne $View.registration_scenario_sha256){throw 'REGISTRATION_VIEW_BINDING'}
 $hash=[Security.Cryptography.SHA256]::Create()
 try{$digest=([BitConverter]::ToString($hash.ComputeHash($Raw))).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose()}
 if($digest -cne $View.registration_state_sha256){throw 'REGISTRATION_VIEW_RECEIPT'}
 $original=@($State.baseline.registrations)
 if($original.Count -ne 1 -or $original[0].name -cne 'Ubuntu' -or $original[0].id.ToLowerInvariant() -cne $View.original_guid -or
 $State.receipt.name -cne ('TSW-Q440-'+$View.run_id) -or $State.receipt.id.ToLowerInvariant() -cne $View.new_guid -or
 (Get-AcceptanceRegistrationDigest $original[0].vhd_identity) -cne $View.original_vhd_sha256 -or
 (Get-AcceptanceRegistrationDigest $State.receipt.vhd_identity) -cne $View.new_vhd_sha256){throw 'REGISTRATION_VIEW_IDENTITY'}
 # This is a read-only source view over the original immutable import receipt.
 # It neither republishes that receipt nor admits another distribution.
 return $View
}
function Invoke-WslAcceptanceRegistration($s,[string]$Mode,[Collections.IDictionary]$Ports){
 $result=[ordered]@{schema_version=1;scope='WSL_ACCEPTANCE_REGISTRATION';status='BLOCKED';
  import_attempted=$false;registration_verified=$false;recovery_required=$false;services_verified=$false;error='NONE'}
 $lock=$null;$pending=$false
 try{
  Assert-AcceptanceRegistrationScenario $s
  if($Mode -cnotin @('Plan','Import','Verify')){throw 'MODE_INVALID'}
  foreach($key in @('Source','Observe','Load','Lock','Unlock','Intent','Save','Import','Receipt','Clock','Preconditions')){
   if(!$Ports.Contains($key) -or $Ports[$key] -isnot [scriptblock]){throw 'PORTS_INVALID'}
  }
  & $Ports.Source $s | Out-Null
  $now=& $Ports.Clock
  $expiry=[DateTimeOffset]::ParseExact($s.expires_utc,'yyyy-MM-ddTHH:mm:ssZ',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::AssumeUniversal)
  if($Mode -ceq 'Import' -and ($s.decision -cne 'GO' -or ($expiry-$now).TotalSeconds -lt 2400 -or ($expiry-$now).TotalSeconds -gt 3600)){throw 'GO_EXPIRED_OR_INSUFFICIENT'}
  $name='TSW-Q440-'+$s.run_id
  $state=& $Ports.Load $s
  if($Mode -ceq 'Verify'){
   if($null -eq $state -or $state.schema_version -isnot [int] -or $state.schema_version -ne 1 -or $state.stage -cne 'registered' -or $state.scenario_sha256 -cne (Get-AcceptanceRegistrationDigest $s) -or $null -eq $state.baseline -or $null -eq $state.receipt -or (Get-AcceptanceRegistrationDigest $state.baseline) -cne $s.preserve_sha256){throw 'ORIGINAL_RECEIPT_REQUIRED'}
   $actual=& $Ports.Observe $s
   $new=Assert-AcceptanceRegistrationInventory $state.baseline $actual $name $true
   if((Get-AcceptanceRegistrationDigest $new) -cne (Get-AcceptanceRegistrationDigest $state.receipt)){throw 'NEW_REGISTRATION_DRIFT'}
   & $Ports.Source $s | Out-Null
   $result.status='VERIFIED_STOPPED';$result.registration_verified=$true;return $result
  }
  if($null -ne $state){$result.recovery_required=$true;throw 'ORIGINAL_IMPORT_NOT_REPLAYABLE'}
  $before=& $Ports.Observe $s
  if((Get-AcceptanceRegistrationDigest $before) -cne $s.preserve_sha256){throw 'PRESTATE_MISMATCH'}
  Assert-AcceptanceRegistrationInventory $before $before $name $false | Out-Null
  if(@($before.registrations|Where-Object{$_.name -ieq $name}).Count){throw 'REGISTRATION_COLLISION'}
  & $Ports.Preconditions $s | Out-Null
  if($Mode -ceq 'Plan'){$result.status='PLAN_ONLY';return $result}
  $lock=& $Ports.Lock $s
  & $Ports.Source $s | Out-Null
  if($null -ne (& $Ports.Load $s)){throw 'ORIGINAL_IMPORT_NOT_REPLAYABLE'}
  $fresh=& $Ports.Observe $s
  if((Get-AcceptanceRegistrationDigest $fresh) -cne $s.preserve_sha256){throw 'PRESTATE_MISMATCH'}
  & $Ports.Preconditions $s | Out-Null
  $state=& $Ports.Intent $s $before
  # This durable pending state precedes the only external registration write.
  $state.stage='import_pending';$state=& $Ports.Save $s $state
  $pending=$true
  if(($expiry-(& $Ports.Clock)).TotalSeconds -lt 1200){throw 'GO_EXPIRED_OR_INSUFFICIENT'}
  $result.import_attempted=$true
  & $Ports.Import $s $name | Out-Null
  $after=& $Ports.Observe $s
  $new=Assert-AcceptanceRegistrationInventory $before $after $name $true
  & $Ports.Source $s | Out-Null
  $state.receipt=$new;$state.stage='registered';$state=& $Ports.Receipt $s $state
  $result.status='IMPORTED_STOPPED';$result.registration_verified=$true
 }catch{
  $result.error='REGISTRATION_REFUSED_OR_UNCERTAIN'
  if($pending){$result.status='RECOVERY_REQUIRED';$result.recovery_required=$true}
 }finally{if($null -ne $lock){try{& $Ports.Unlock $lock | Out-Null}catch{$result.status='RECOVERY_REQUIRED';$result.recovery_required=$true}}}
 return $result
}

function New-WslAcceptanceRegistrationProductionPorts($s){
 $root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
 Import-Module (Join-Path $root 'modules/tsw_windows_wsl/bootstrap/preparation/Preparation.psm1') -Force -DisableNameChecking
 $preparation=Get-Module Preparation
 # Reuse read-only registry and the reviewed complete firewall getter. The old
 # timeout-prone per-rule snapshot is never used as a compatibility fallback.
 . (Join-Path $root 'modules/tsw_windows_wsl/tools/qualification/wsl_resource_maintenance.ps1')
 if(!(Get-Command Get-WslMaintenanceFirewallCertificateCommand -ErrorAction SilentlyContinue)){throw 'FIREWALL_SNAPSHOT_DEPENDENCY_UNAVAILABLE'}
 $firewall=Get-WslMaintenanceFirewallCertificateCommand
 $certificateValidator=${function:ConvertFrom-WslMaintenanceFirewallCertificate}
 $parent=Join-Path ([Environment]::GetFolderPath('CommonApplicationData')) 'TinySwarmWorld/Qualification/AcceptanceRegistrations'
 $image=Join-Path ([Environment]::GetFolderPath('CommonApplicationData')) 'TinySwarmWorld/Qualification/Images/ubuntu-26.04.1-wsl-amd64.wsl'
 $digestFunction=${function:Get-AcceptanceRegistrationDigest}
 $module=New-Module -ArgumentList $root,$parent,$image,$preparation,$firewall,$s,$digestFunction,$certificateValidator -ScriptBlock {
  param($root,$parent,$image,$preparation,$firewall,$scenario,$digestFunction,$certificateValidator)
  Set-Item Function:script:Get-AcceptanceRegistrationDigest $digestFunction
  Set-Item Function:script:ConvertFrom-WslMaintenanceFirewallCertificate $certificateValidator
  $script:root=$root;$script:parent=$parent;$script:image=$image;$script:prep=$preparation;$script:firewall=$firewall;$script:s=$scenario
  $script:watch=[Diagnostics.Stopwatch]::StartNew();$script:calls=0;$script:bytes=0
  $script:task=Join-Path $parent $scenario.run_id;$script:install=Join-Path $script:task 'guest'
  $script:state=Join-Path $script:task 'registration.json';$script:loadedHash=$null
  function Require($yes,[string]$code){if(!$yes){throw $code}}
  function Run([string]$exe,[string[]]$arguments,[int]$seconds=15,[int]$limit=1048576,[int[]]$exits=@(0)){
   $left=2400-[int][Math]::Ceiling($script:watch.Elapsed.TotalSeconds)
   Require ($left -ge $seconds -and $script:calls -lt 128) 'REGISTRATION_DEADLINE'
   $script:calls++
   $r=& $script:prep {param($e,$a,$t) Invoke-PreparationProcess $e $a $t} $exe $arguments $seconds
   $n=[Text.Encoding]::UTF8.GetByteCount([string]$r.stdout);$script:bytes+=$n+[Text.Encoding]::UTF8.GetByteCount([string]$r.stderr)
   Require ($r.exit_code -in $exits -and !$r.stderr -and $n -le $limit -and $script:bytes -le 67108864) 'REGISTRATION_COMMAND_FAILED'
   return $r
  }
  function TrustedWsl {
   $path=& $script:prep {Get-PreparationExecutable 'wsl.exe'}
   Require ([Environment]::Is64BitProcess -and [Environment]::Is64BitOperatingSystem) 'NATIVE_WINDOWS_REQUIRED'
   & $script:prep {param($p) Assert-PreparationLocalPath $p} $path
   $expected=Join-Path ([Environment]::GetFolderPath('System')) 'wsl.exe'
   Require ([IO.Path]::GetFullPath($path) -ieq [IO.Path]::GetFullPath($expected)) 'WSL_EXECUTABLE_PATH'
   # OS binaries have a different ownership contract from private evidence.
   $trusted=@('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
   $current=$path;$leaf=$true
   while($current){
    $item=Get-Item -LiteralPath $current -Force -ErrorAction Stop
    Require (!($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) 'WSL_EXECUTABLE_REPARSE'
    if($leaf){Require (!$item.PSIsContainer) 'WSL_EXECUTABLE_PATH'}
    $acl=Get-Acl -LiteralPath $current -ErrorAction Stop
    Require ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -cin $trusted) 'WSL_EXECUTABLE_OWNER'
    $mask=[Security.AccessControl.FileSystemRights]::Delete -bor [Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles -bor [Security.AccessControl.FileSystemRights]::ChangePermissions -bor [Security.AccessControl.FileSystemRights]::TakeOwnership
    if($leaf){$mask=$mask -bor [Security.AccessControl.FileSystemRights]::WriteData -bor [Security.AccessControl.FileSystemRights]::AppendData -bor [Security.AccessControl.FileSystemRights]::WriteAttributes -bor [Security.AccessControl.FileSystemRights]::WriteExtendedAttributes}
    foreach($rule in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])){
     Require (($rule.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -or $rule.AccessControlType -ne 'Allow' -or
      !($rule.FileSystemRights -band $mask) -or $rule.IdentityReference.Value -cin ($trusted+@('S-1-3-0'))) 'WSL_EXECUTABLE_ACL'
    }
    $leaf=$false;$current=Split-Path -Parent $current
   }
   $sig=Get-AuthenticodeSignature -LiteralPath $path -ErrorAction Stop
   Require ($sig.Status -eq 'Valid' -and $sig.SignerCertificate.Subject -match '(?:^|,\s*)O=Microsoft Corporation(?:,|$)') 'WSL_EXECUTABLE_UNTRUSTED'
   return $path
  }
  function FileIdentity([string]$path){
   & $script:prep {param($p) Assert-PreparationLocalPath $p;Assert-PreparationSelectedVhdMetadata $p} $path
   if(-not ('Epic440RegistrationFile' -as [type])){
    Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices; using Microsoft.Win32.SafeHandles;
public static class Epic440RegistrationFile {
 [StructLayout(LayoutKind.Sequential)] public struct Info { public uint Attributes; public System.Runtime.InteropServices.ComTypes.FILETIME Creation, Access, Write; public uint Volume, HighSize, LowSize, Links, HighIndex, LowIndex; }
 [DllImport("kernel32.dll", SetLastError=true)] public static extern bool GetFileInformationByHandle(SafeFileHandle h, out Info i);
}
'@
   }
   $f=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
   try{$i=New-Object Epic440RegistrationFile+Info;Require ([Epic440RegistrationFile]::GetFileInformationByHandle($f.SafeFileHandle,[ref]$i) -and $i.Links -eq 1 -and $f.Length -gt 0) 'VHD_IDENTITY_UNAVAILABLE'
    return ('{0:x8}:{1:x8}{2:x8}:{3:x8}:{4:x8}' -f $i.Volume,$i.HighIndex,$i.LowIndex,$i.Attributes,$i.Links)
   }finally{$f.Dispose()}
  }
  function Source($s){
   Require ([Environment]::MachineName -ceq $s.host) 'HOST_MISMATCH'
   Require (Test-Path -LiteralPath (Join-Path $script:root '.git')) 'COMMITTED_GIT_SOURCE_REQUIRED'
   $encoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($script:root))
   $query='$ErrorActionPreference="Stop";$ProgressPreference="SilentlyContinue";$root=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("'+$encoded+'"));Import-Module (Join-Path $root "modules/tsw_windows_wsl/bootstrap/preparation/Preparation.psm1") -Force -DisableNameChecking;$m=Get-Module Preparation;$o=@{RepositoryRoot=$root;ProbeTimeoutSeconds=15;QualificationRevision="'+$s.source_commit+'"};& $m {param($options) Get-PreparationSource $options} $o | ConvertTo-Json -Depth 12 -Compress'
   $exe=& $script:prep {Get-PreparationExecutable 'powershell.exe'}
   $query64=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($query))
   $probe=Run $exe @('-NoProfile','-NonInteractive','-EncodedCommand',$query64) 180 2097152
   $source=$probe.stdout|ConvertFrom-Json -ErrorAction Stop
   Require ($source.verified -eq $true -and $source.clean -eq $true -and $source.revision -ceq $s.source_commit) 'SOURCE_MISMATCH'
   $pins=[ordered]@{}
   foreach($relative in @('modules/tsw_windows_wsl/tools/qualification/wsl_acceptance_registration.ps1','modules/tsw_windows_wsl/tools/qualification/wsl_resource_maintenance.ps1',
      'modules/tsw_core/tests/fixtures/wsl_acceptance_registration.ps1','modules/tsw_windows_wsl/tests/tools/test_wsl_acceptance_registration.py')){
    $path=Join-Path $script:root $relative
    & $script:prep {param($p) Assert-PreparationEvidencePath $p} $path
    $pins[$relative]=(Get-FileHash -LiteralPath $path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
   }
   Require ((Get-AcceptanceRegistrationDigest @($source.assets,$pins)) -ceq $s.source_pins_sha256) 'SOURCE_PINS_MISMATCH'
   Require ($script:watch.Elapsed.TotalSeconds -lt 2400) 'REGISTRATION_DEADLINE'
  }
  function FirewallCertificate {
   $exe=& $script:prep {Get-PreparationExecutable 'powershell.exe'}
   $f=Run $exe @('-NoProfile','-NonInteractive','-Command',$script:firewall) 120 4096
   return ConvertFrom-WslMaintenanceFirewallCertificate ([string]$f.stdout)
  }
  function BridgeFileLimit([string]$Bridge,[string]$Path){
   $logs=[IO.Path]::GetFullPath((Join-Path $Bridge 'logs')).TrimEnd('\','/')
   $file=[IO.Path]::GetFullPath($Path)
   $names=@('TinySwarmWorldWslBridge.out.log','TinySwarmWorldWslBridge.out.log.old','TinySwarmWorldWslBridge.err.log','TinySwarmWorldWslBridge.err.log.old')
   if(([IO.Path]::GetDirectoryName($file)).TrimEnd('\','/') -ieq $logs -and [IO.Path]::GetFileName($file) -cin $names){return 16777216}
   return 4194304
  }
  function BridgeFileHash([string]$Path,[long]$Maximum,[long]$ExpectedLength){
   & $script:prep {param($p) Assert-PreparationEvidencePath $p} $Path
   $before=(Get-Item -LiteralPath $Path -Force -ErrorAction Stop).LastWriteTimeUtc.Ticks
   $stream=[IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
   $hash=[Security.Cryptography.SHA256]::Create()
   try{
    $length=$stream.Length;Require ($length -le $Maximum) 'BRIDGE_FILE_BOUND';Require ($length -eq $ExpectedLength) 'BRIDGE_FILE_DRIFT'
    $buffer=New-Object byte[] 65536;$total=0L
    while($true){
     Require ($script:watch.Elapsed.TotalSeconds -lt 2400) 'REGISTRATION_DEADLINE'
     $n=$stream.Read($buffer,0,[int][Math]::Min($buffer.Length,$Maximum-$total+1))
     if(!$n){break};$total+=$n;Require ($total -le $Maximum) 'BRIDGE_FILE_BOUND'
     [void]$hash.TransformBlock($buffer,0,$n,$buffer,0)
    }
    Require ($total -eq $length -and $stream.Length -eq $length -and (Get-Item -LiteralPath $Path -Force -ErrorAction Stop).LastWriteTimeUtc.Ticks -eq $before) 'BRIDGE_FILE_DRIFT'
    [void]$hash.TransformFinalBlock([byte[]]@(),0,0)
    & $script:prep {param($p) Assert-PreparationEvidencePath $p} $Path
    return ([BitConverter]::ToString($hash.Hash)).Replace('-','')
   }finally{$hash.Dispose();$stream.Dispose()}
  }
  function GlobalProof {
   $certificate=FirewallCertificate
   $exe=& $script:prep {Get-PreparationExecutable 'powershell.exe'}
   $netsh=Join-Path ([Environment]::GetFolderPath('System')) 'netsh.exe'
   $routes=Run $netsh @('interface','portproxy','show','all') 30 2097152
   $serviceQuery='$ErrorActionPreference="Stop";@(Get-CimInstance -ClassName Win32_Service -Filter "Name=''TinySwarmWorldWslBridge''" -ErrorAction Stop | Select-Object Name,PathName,StartMode,StartName,State)|ConvertTo-Json -Depth 5 -Compress'
   $service=Run $exe @('-NoProfile','-NonInteractive','-Command',$serviceQuery) 15 1048576
   $properties=$service.stdout
   $files=[ordered]@{}
   foreach($p in @((Join-Path ([Environment]::GetFolderPath('UserProfile')) '.wslconfig'),
      (Join-Path ([Environment]::GetFolderPath('System')) 'drivers/etc/hosts'))){
    $files[$p]=if(Test-Path -LiteralPath $p -PathType Leaf){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}else{'ABSENT'}
   }
   $bridge=Join-Path ([Environment]::GetFolderPath('CommonApplicationData')) 'TinySwarmWorld/WslBridge'
   if(Test-Path -LiteralPath $bridge){
    & $script:prep {param($p) Assert-PreparationEvidencePath $p} $bridge
    $queue=[Collections.Generic.Queue[string]]::new();$queue.Enqueue($bridge)
    $all=[Collections.Generic.List[object]]::new();$count=0;$totalFileBytes=0L
    while($queue.Count -gt 0){
     foreach($child in @(Get-ChildItem -LiteralPath $queue.Dequeue() -Force -ErrorAction Stop)){
      $count++;Require ($count -le 128) 'BRIDGE_BOUND'
      & $script:prep {param($p) Assert-PreparationEvidencePath $p} $child.FullName
      if($child.PSIsContainer){$queue.Enqueue($child.FullName)}else{
       $limit=BridgeFileLimit $bridge $child.FullName
       Require ($child.Length -le $limit) 'BRIDGE_FILE_BOUND'
       $totalFileBytes+=$child.Length;Require ($totalFileBytes -le 67108864) 'BRIDGE_TOTAL_BOUND'
       $all.Add($child)
      }
     }
    }
    foreach($p in @($all|Sort-Object FullName)){
     & $script:prep {param($p) Assert-PreparationEvidencePath $p} $p.FullName
     if($p.Name -cne 'bridge-state.json'){$files[$p.FullName]=BridgeFileHash $p.FullName (BridgeFileLimit $bridge $p.FullName) $p.Length}
    }
   }
   return Get-AcceptanceRegistrationDigest @($certificate,$routes.stdout,$properties,$files)
  }
  function Observe($s){
   $wsl=TrustedWsl
   $run=Run $wsl @('--list','--running','--quiet') 15 65536
   $running=@(([string]$run.stdout).Replace("`0",'') -split '\r?\n'|Where-Object{$_}|Sort-Object)
   Require ($running.Count -le 32) 'REGISTRATION_BOUND'
   $base=[Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Software\Microsoft\Windows\CurrentVersion\Lxss',$false)
   Require ($null -ne $base) 'ORIGINAL_REGISTRY_REQUIRED'
   try{
    $rootValues=[ordered]@{};foreach($key in @($base.GetValueNames()|Sort-Object)){$rootValues[$key]=@([string]$base.GetValueKind($key),$base.GetValue($key))}
    $rows=@(foreach($id in @($base.GetSubKeyNames()|Sort-Object)){
     Require ($id -cmatch '\A\{[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}\z') 'REGISTRATION_AMBIGUOUS'
     $entry=$base.OpenSubKey($id,$false);Require ($null -ne $entry) 'REGISTRATION_UNREADABLE'
     try{
      $values=[ordered]@{};foreach($k in @($entry.GetValueNames()|Sort-Object)){$values[$k]=@([string]$entry.GetValueKind($k),$entry.GetValue($k))}
      $name=$entry.GetValue('DistributionName');$version=$entry.GetValue('Version')
      Require ($name -is [string] -and $name -and $version -is [int] -and $version -eq 2) 'REGISTRATION_UNSUPPORTED'
      $path=[string]$entry.GetValue('BasePath');if($path.StartsWith('\\?\')){$path=$path.Substring(4)}
      $path=[IO.Path]::GetFullPath($path).TrimEnd('\')
      $vhd=$entry.GetValue('VhdFileName');if(!$vhd){$vhd='ext4.vhdx'}
      Require ($vhd -is [string] -and $vhd -cmatch '\A[A-Za-z0-9_.-]+\.vhdx\z') 'VHD_PATH_INVALID'
      $vhdPath=Join-Path $path $vhd
      $identity=FileIdentity $vhdPath
      $matches=$path -ieq [IO.Path]::GetFullPath($script:install)
      $rootfs=$null
      if($matches -and $name -cnotin $running){
       $encoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($vhdPath))
       $hashQuery='$ErrorActionPreference="Stop";$p=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("'+$encoded+'"));$f=[IO.File]::Open($p,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read);$h=[Security.Cryptography.SHA256]::Create();try{([BitConverter]::ToString($h.ComputeHash($f))).Replace("-","").ToLowerInvariant()}finally{$h.Dispose();$f.Dispose()}'
       $exe=& $script:prep {Get-PreparationExecutable 'powershell.exe'}
       $proof=Run $exe @('-NoProfile','-NonInteractive','-EncodedCommand',([Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($hashQuery)))) 180 128
       $rootfs=$proof.stdout.Trim();Require ($rootfs -cmatch '\A[0-9a-f]{64}\z') 'ROOTFS_IDENTITY_UNPROVEN'
      }
      [ordered]@{id=$id;name=$name;version=$version;values_sha256=(Get-AcceptanceRegistrationDigest $values);
       base_sha256=(Get-AcceptanceRegistrationDigest $path);vhd_identity=$identity;rootfs_sha256=$rootfs;running=($name -cin $running);
       path_matches=$matches}
     }finally{$entry.Dispose()}
    })
    Require ($rows.Count -gt 0 -and $rows.Count -le 32 -and @($running|Where-Object{$_ -cnotin @($rows|ForEach-Object{$_.name})}).Count -eq 0) 'REGISTRATION_INVENTORY_INCOMPLETE'
    $default=[string]$base.GetValue('DefaultDistribution');Require ($default -cin @($rows|ForEach-Object{$_.id})) 'DEFAULT_REGISTRATION_UNPROVEN'
    return [ordered]@{default=$default;registrations=$rows;running_sha256=(Get-AcceptanceRegistrationDigest $running);
     global_sha256=(Get-AcceptanceRegistrationDigest @($rootValues,(GlobalProof)))}
   }finally{$base.Dispose()}
  }
  function Preconditions($s){
   Require (!(Test-Path -LiteralPath $script:task)) 'TASK_PATH_COLLISION'
   & $script:prep {param($p) Assert-PreparationLocalPath $p;Assert-PreparationEvidencePath $p} $script:parent
   Require (Test-Path -LiteralPath $script:parent -PathType Container) 'PRIVATE_PARENT_REQUIRED'
   & $script:prep {param($p) Assert-PreparationLocalPath $p;Assert-PreparationEvidencePath $p} $script:image
   $item=Get-Item -LiteralPath $script:image -Force -ErrorAction Stop
   Require (!$item.PSIsContainer -and $item.Length -eq 418495746 -and
    (Get-FileHash -LiteralPath $script:image -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $s.image_sha256) 'IMAGE_MISMATCH'
   $volume=Get-Volume -FilePath $script:parent -ErrorAction Stop
   Require ($volume.SizeRemaining -ge 8589934592) 'IMPORT_STORAGE_INSUFFICIENT'
   [void](TrustedWsl)
  }
  function Load($s){
   if(!(Test-Path -LiteralPath $script:state)){return $null}
   & $script:prep {param($p) Assert-PreparationEvidencePath $p} $script:state
   $item=Get-Item -LiteralPath $script:state -Force;Require (!$item.PSIsContainer -and $item.Length -le 131072) 'STATE_INVALID'
   $raw=[IO.File]::ReadAllText($script:state,[Text.Encoding]::UTF8);$script:loadedHash=Get-AcceptanceRegistrationDigest $raw
   return & $script:prep {param($text) ConvertTo-PreparationHashtable ($text|ConvertFrom-Json -ErrorAction Stop)} $raw
  }
  function Save($s,$state){
   & $script:prep {param($p) Assert-PreparationEvidencePath $p} $script:task
   if(Test-Path -LiteralPath $script:state){
    $raw=[IO.File]::ReadAllText($script:state,[Text.Encoding]::UTF8)
    Require ((Get-AcceptanceRegistrationDigest $raw) -ceq $script:loadedHash) 'STATE_CAS_DRIFT'
   }else{Require ($null -eq $script:loadedHash) 'STATE_CAS_DRIFT'}
   $raw=ConvertTo-Json -InputObject $state -Depth 30 -Compress
   Require ([Text.Encoding]::UTF8.GetByteCount($raw) -le 131072) 'STATE_BOUND'
   $temporary=Join-Path $script:task ('state-'+[Guid]::NewGuid().ToString('N')+'.tmp')
   $stream=[IO.FileStream]::new($temporary,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
   try{& $script:prep {param($p) Set-PreparationPrivateAcl $p} $temporary
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes($raw);$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)
   }finally{$stream.Dispose()}
   if(Test-Path -LiteralPath $script:state){[IO.File]::Replace($temporary,$script:state,[System.Management.Automation.Language.NullString]::Value)}else{[IO.File]::Move($temporary,$script:state)}
   $script:loadedHash=Get-AcceptanceRegistrationDigest $raw
   return $state
  }
  function Intent($s,$before){
   Preconditions $s
   # Existing parent is private with inheritable ACL; never repair a foreign path.
   [void](New-Item -ItemType Directory -Path $script:task -ErrorAction Stop)
   $acl=New-Object Security.AccessControl.DirectorySecurity
   $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
   $acl.SetOwner($sid);$acl.SetAccessRuleProtection($true,$false)
   foreach($principal in @($sid.Value,'S-1-5-18','S-1-5-32-544')){
    $rule=New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier($principal)),'FullControl','ContainerInherit,ObjectInherit','None','Allow')
    [void]$acl.AddAccessRule($rule)
   }
   [IO.Directory]::SetAccessControl($script:task,$acl)
   & $script:prep {param($p) Assert-PreparationEvidencePath $p} $script:task
   $state=@{schema_version=1;scenario_sha256=(Get-AcceptanceRegistrationDigest $s);stage='intent';baseline=$before;receipt=$null}
   return Save $s $state
  }
  function Lock($s){
   $mutex=[Threading.Mutex]::new($false,'Global\TinySwarmWorldEpic440AcceptanceRegistration')
   if(!$mutex.WaitOne(0)){$mutex.Dispose();throw 'IMPORT_LOCKED'};return $mutex
  }
  function Unlock($mutex){try{$mutex.ReleaseMutex()}finally{$mutex.Dispose()}}
  function ImportGuest($s,[string]$name){
   Require ($name -ceq ('TSW-Q440-'+$s.run_id) -and !(Test-Path -LiteralPath $script:install)) 'IMPORT_TARGET_COLLISION'
   & $script:prep {param($p) Assert-PreparationEvidencePath $p} $script:image
   $stream=[IO.File]::Open($script:image,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
   $hash=[Security.Cryptography.SHA256]::Create()
   try{
    Require ($stream.Length -eq 418495746 -and ([BitConverter]::ToString($hash.ComputeHash($stream))).Replace('-','').ToLowerInvariant() -ceq $s.image_sha256) 'IMAGE_MISMATCH'
    [void](Run (TrustedWsl) @('--import',$name,$script:install,$script:image,'--version','2') 600 1048576)
   }finally{$hash.Dispose();$stream.Dispose()}
  }
  function Receipt($s,$state){return Save $s $state}
  function Clock{return [DateTimeOffset]::UtcNow}
  Export-ModuleMember -Function Source,Observe,Load,Lock,Unlock,Intent,Save,ImportGuest,Receipt,Clock,Preconditions
 }
 $ports=@{}
 foreach($name in @('Source','Observe','Load','Lock','Unlock','Intent','Save','Receipt','Clock','Preconditions')){
  $ports[$name]={& $module {param($f,$items) & $f @items} $name $args}.GetNewClosure()
 }
 $ports.Import={& $module {param($items) ImportGuest @items} $args}.GetNewClosure()
 return $ports
}
if($MyInvocation.InvocationName -ne '.'){
 try{
  if($ExpectedScenarioSha256 -cnotmatch '\A[0-9a-f]{64}\z' -or $ScenarioBase64.Length -gt 8192){throw 'SCENARIO_INVALID'}
  $bytes=[Convert]::FromBase64String($ScenarioBase64);$h=[Security.Cryptography.SHA256]::Create()
  try{$digest=([BitConverter]::ToString($h.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}
  if($digest -cne $ExpectedScenarioSha256){throw 'SCENARIO_HASH_MISMATCH'}
  $raw=[Text.UTF8Encoding]::new($false,$true).GetString($bytes);$doc=$raw|ConvertFrom-Json -ErrorAction Stop
  foreach($p in $doc.PSObject.Properties){if([regex]::Matches($raw,('"'+[regex]::Escape($p.Name)+'"\s*:')).Count -ne 1){throw 'SCENARIO_DUPLICATE_KEY'}}
  $scenario=@{};foreach($p in $doc.PSObject.Properties){$scenario[$p.Name]=$p.Value}
  Assert-AcceptanceRegistrationScenario $scenario
  $ports=New-WslAcceptanceRegistrationProductionPorts $scenario
  $result=Invoke-WslAcceptanceRegistration $scenario $Mode $ports
 }catch{$result=@{schema_version=1;scope='WSL_ACCEPTANCE_REGISTRATION';status='BLOCKED';error='SCENARIO_OR_PRODUCTION_ADAPTER_INVALID';services_verified=$false}}
 $result|ConvertTo-Json -Depth 8 -Compress
 if($result.status -cin @('PLAN_ONLY','IMPORTED_STOPPED','VERIFIED_STOPPED')){exit 0}else{exit 2}
}
