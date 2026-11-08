param([Parameter(Mandatory=$true)][string]$RepositoryRoot,[switch]$EmitUnicodeSnapshot,[switch]$NativeCimContract,[switch]$SourceGuardContract,[switch]$DynamicTargetContract,[switch]$CertificateContract)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
# Load the installed CIM SDK through its shipped module; no provider command.
Import-Module (Join-Path ([Environment]::GetFolderPath('System')) 'WindowsPowerShell/v1.0/Modules/CimCmdlets/CimCmdlets.psd1') -ErrorAction Stop
if($DynamicTargetContract){Import-Module NetSecurity -ErrorAction Stop -DisableNameChecking}
. (Join-Path $RepositoryRoot 'tools/windows/qualification/wsl_resource_maintenance.ps1')
function Assert($Condition,[string]$Code){if(!$Condition){throw $Code}}
$command=Get-WslMaintenanceFirewallCommand
function Fixture([int]$Count=3){
 $rules=@(for($i=0;$i -lt $Count;$i++){
  [pscustomobject][ordered]@{InstanceID=('rule-'+$i);Name=('rule-'+$i);Profile='Any';
   Description='foreign rule preserved';Opaque=[ordered]@{b=2;a=@('ordered','values')}}
 })
 $filters=@{}
 foreach($family in @('address','application','interface','interface_type','port','security','service')){
  $filters[$family]=@($rules | ForEach-Object{[pscustomobject][ordered]@{InstanceID=$_.InstanceID;
   ForeignProperty=('PRIVATE_CANARY_'+$family);Nested=[ordered]@{z=2;a=1}}})
 }
 return @{rules=$rules;filters=$filters;profiles=@([pscustomobject]@{Name='Domain';Opaque='profile'},
  [pscustomobject]@{Name='Private';Opaque='profile'},[pscustomobject]@{Name='Public';Opaque='profile'});
  settings=@([pscustomobject]@{Opaque='global';UnknownProperty=@('retained')});calls=@{};reverse=$false;fault=''}
}
function Called([string]$Name,[string]$PolicyStore){
 Assert ($PolicyStore -ceq 'ActiveStore') 'wrong_policy_store'
 if(!$script:ctx.calls.ContainsKey($Name)){$script:ctx.calls[$Name]=0};$script:ctx.calls[$Name]++
 if($script:ctx.fault -ceq ('failure_'+$Name)){throw 'PROVIDER_UNREADABLE'}
}
function Ordered($Rows){
 $a=@($Rows);if($script:ctx.reverse){[array]::Reverse($a)};return $a
}
function Get-NetFirewallRule {param($PolicyStore) Called 'rules' $PolicyStore;Ordered $script:ctx.rules}
function Get-NetFirewallProfile {param($PolicyStore) Called 'profiles' $PolicyStore;Ordered $script:ctx.profiles}
function Get-NetFirewallSetting {param($PolicyStore) Called 'settings' $PolicyStore;Ordered $script:ctx.settings}
function Family([string]$Name,$PolicyStore,$AssociatedNetFirewallRule){
 Called $Name $PolicyStore
 if($null -ne $AssociatedNetFirewallRule){
  if($script:ctx.fault -ceq 'wrong_association'){return [pscustomobject]@{InstanceID='foreign';ForeignProperty='opaque'}}
  $row=@($script:ctx.filters[$Name] | Where-Object{$_.InstanceID -ceq $AssociatedNetFirewallRule.InstanceID})
  if($script:ctx.fault -ceq 'association_drift'){
   return [pscustomobject]@{InstanceID=$AssociatedNetFirewallRule.InstanceID;ForeignProperty='changed';Nested=@{z=2;a=1}}
  }
  return $row
 }
 Ordered $script:ctx.filters[$Name]
}
function Get-NetFirewallAddressFilter {param($PolicyStore,$AssociatedNetFirewallRule) Family 'address' $PolicyStore $AssociatedNetFirewallRule}
function Get-NetFirewallApplicationFilter {param($PolicyStore,$AssociatedNetFirewallRule) Family 'application' $PolicyStore $AssociatedNetFirewallRule}
function Get-NetFirewallInterfaceFilter {param($PolicyStore,$AssociatedNetFirewallRule) Family 'interface' $PolicyStore $AssociatedNetFirewallRule}
function Get-NetFirewallInterfaceTypeFilter {param($PolicyStore,$AssociatedNetFirewallRule) Family 'interface_type' $PolicyStore $AssociatedNetFirewallRule}
function Get-NetFirewallPortFilter {param($PolicyStore,$AssociatedNetFirewallRule) Family 'port' $PolicyStore $AssociatedNetFirewallRule}
function Get-NetFirewallSecurityFilter {param($PolicyStore,$AssociatedNetFirewallRule) Family 'security' $PolicyStore $AssociatedNetFirewallRule}
function Get-NetFirewallServiceFilter {param($PolicyStore,$AssociatedNetFirewallRule) Family 'service' $PolicyStore $AssociatedNetFirewallRule}
function Capture {return & ([scriptblock]::Create($command))}
function Fingerprint {return Get-WslMaintenanceDigest (Capture)}
function MustFail([string]$Expected){
 $failed=$false
 try{$null=Capture}catch{Assert ($_.Exception.Message -ceq $Expected) 'wrong_refusal';$failed=$true}
 Assert $failed 'unexpected_capture_success'
}
if($CertificateContract){
 $fullCommand=$command
 $certificateCommand=Get-WslMaintenanceFirewallCertificateCommand
 function CertificateCapture {
  $writer=[IO.StringWriter]::new([Globalization.CultureInfo]::InvariantCulture);$previous=[Console]::Out
  try{[Console]::SetOut($writer);& ([scriptblock]::Create($certificateCommand));return $writer.ToString()}
  finally{[Console]::SetOut($previous);$writer.Dispose()}
 }
 $sha=[Security.Cryptography.SHA256]::Create()
 try{$commandHash=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($certificateCommand)))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
 $script:ctx=Fixture;$full=Capture;$raw=CertificateCapture;$certificate=ConvertFrom-WslMaintenanceFirewallCertificate $raw
 $sha=[Security.Cryptography.SHA256]::Create()
 try{$fullHash=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($full)))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
 Assert ($certificate.snapshot_sha256 -ceq $fullHash -and $certificate.snapshot_bytes -eq [Text.Encoding]::UTF8.GetByteCount($full)) 'hash_entire_exact_current_snapshot'
 Assert ($certificate.counts.rules -eq 3 -and @($certificate.counts.PSObject.Properties).Count -eq 10) 'closed_complete_counts'
 Assert (!$raw.Contains('PRIVATE_CANARY') -and [Text.Encoding]::UTF8.GetByteCount($raw) -lt 4096) 'no_private_data_transport'
 $before=$certificate.snapshot_sha256;$cases=3
 foreach($family in @('address','application','interface','interface_type','port','security','service')){
  $script:ctx=Fixture;$script:ctx.filters[$family][1].ForeignProperty='changed same-count foreign data'
  $after=ConvertFrom-WslMaintenanceFirewallCertificate (CertificateCapture)
  Assert ($after.snapshot_sha256 -cne $before -and $after.counts.rules -eq $certificate.counts.rules) 'count_preserving_change_not_lost';$cases++
 }
 foreach($fault in @('extra','wrong_query','bool_bytes','wrong_count','unknown_family','duplicate','array')){
  $copy=ConvertFrom-Json -InputObject $raw
  switch($fault){
   'extra'{Add-Member -InputObject $copy -NotePropertyName unexpected -NotePropertyValue 'PRIVATE_CANARY'}
   'wrong_query'{$copy.query_sha256=('0'*64)}
   'bool_bytes'{$copy.snapshot_bytes=$true}
   'wrong_count'{$copy.counts.port++}
   'unknown_family'{Add-Member -InputObject $copy.counts -NotePropertyName unknown -NotePropertyValue 3}
  }
  $bad=ConvertTo-Json -InputObject $copy -Depth 8 -Compress
  if($fault -ceq 'duplicate'){$bad=$bad.Replace('"store":"ActiveStore"','"store":"ActiveStore","store":"ActiveStore"')}
  if($fault -ceq 'array'){$bad='['+$bad+']'}
  $failed=$false;try{$null=ConvertFrom-WslMaintenanceFirewallCertificate $bad}catch{$failed=$true}
  Assert $failed 'malformed_certificate_admitted';$cases++
 }
 # Eight full current Windows-RAM snapshots exceed the parent's old64MiB
 # representation; certificates retain every byte's digest within its budget.
 $script:ctx=Fixture
 Add-Member -InputObject $script:ctx.profiles[0] -NotePropertyName LargeForeignData -NotePropertyValue ('x'*8903516)
 $totalFull=0L;$totalTransport=0L;$largeDigest=$null
 for($i=0;$i -lt 8;$i++){
  $observation=CertificateCapture;$row=ConvertFrom-WslMaintenanceFirewallCertificate $observation
  $totalFull+=$row.snapshot_bytes;$totalTransport+=[Text.Encoding]::UTF8.GetByteCount($observation)
  if($null -ne $largeDigest){Assert ($row.snapshot_sha256 -ceq $largeDigest) 'fresh_large_snapshot_drift'}
  $largeDigest=$row.snapshot_sha256
 }
 Assert ($totalFull -gt 67108864 -and $totalTransport -lt 32768 -and $script:ctx.calls.rules -eq 8) 'fresh_full_hash_not_cached_or_subset';$cases++
 [ordered]@{status='PASS';cases=$cases;runtime_mutations=0;live_capability_claim=$false;
  command_sha256=$commandHash;fresh_large_observations=8;full_windows_ram_bytes=$totalFull;transport_bytes=$totalTransport} | ConvertTo-Json -Compress
 exit 0
}
if($SourceGuardContract){
 $scratch=Join-Path ([IO.Path]::GetTempPath()) ('epic440-firewall-source-'+[Guid]::NewGuid().ToString('N'))
 if(Test-Path -LiteralPath $scratch){throw 'scratch_exists'}
 [void][IO.Directory]::CreateDirectory($scratch)
 try{
  $original=Join-Path $RepositoryRoot 'tools/windows/qualification/windows_firewall_snapshot.ps1'
  $asset=Join-Path $scratch 'windows_firewall_snapshot.ps1'
  Copy-Item -LiteralPath $original -Destination $asset
  $controller=Join-Path $scratch 'wsl_resource_maintenance.ps1'
  Copy-Item -LiteralPath (Join-Path $RepositoryRoot 'tools/windows/qualification/wsl_resource_maintenance.ps1') -Destination $controller
  . $controller
  Assert ((Get-WslMaintenanceFirewallCommand) -ceq [IO.File]::ReadAllText($original)) 'fixed_source_exact_bytes'
  $cases=1
  foreach($change in @('tampered','bom','overbound','empty')){
   if($change -ceq 'tampered'){[IO.File]::AppendAllText($asset,"`n")}
   elseif($change -ceq 'bom'){[IO.File]::WriteAllBytes($asset,[byte[]](@(239,187,191)+[IO.File]::ReadAllBytes($original)))}
   elseif($change -ceq 'overbound'){[IO.File]::WriteAllBytes($asset,[byte[]]::new(65537))}
   else{[IO.File]::WriteAllBytes($asset,[byte[]]::new(0))}
   $failed=$false
   try{$null=Get-WslMaintenanceFirewallCommand}catch{
    Assert ($_.Exception.Message -ceq $(if($change -ceq 'tampered'){'FIREWALL_SOURCE_MISMATCH'}elseif($change -ceq 'bom'){'FIREWALL_SOURCE_INVALID'}else{'FIREWALL_SOURCE_BOUND'})) 'source_wrong_refusal'
    $failed=$true
   }
   Assert $failed 'tampered_source_admitted';$cases++
  }
  [ordered]@{status='PASS';cases=$cases;runtime_mutations=0;live_capability_claim=$false;fixed_source_hash_bound=$true} | ConvertTo-Json -Compress
 }finally{Remove-Item -LiteralPath $scratch -Recurse -Force}
 exit 0
}
function NativeRow([string]$Class,[string]$Id,[string]$Name='',[string]$AliasTarget='InstanceID',[long]$Flags=0){
 $row=[Microsoft.Management.Infrastructure.CimInstance]::new($Class,'root/standardcimv2')
 foreach($key in @('InstanceID','TwinID')){$row.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create($key,$Id,[Microsoft.Management.Infrastructure.CimType]::String,[Microsoft.Management.Infrastructure.CimFlags]::None))}
 $row.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create('NativeUnknown','native-data',[Microsoft.Management.Infrastructure.CimType]::String,([Microsoft.Management.Infrastructure.CimFlags]$Flags)))
 $row.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create('Nullable',$null,[Microsoft.Management.Infrastructure.CimType]::String,[Microsoft.Management.Infrastructure.CimFlags]::None))
 $row.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create('EmptyStrings',[string[]]@(),[Microsoft.Management.Infrastructure.CimType]::StringArray,[Microsoft.Management.Infrastructure.CimFlags]::None))
 $row.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create('Numbers',[int[]]@(1,2),[Microsoft.Management.Infrastructure.CimType]::SInt32Array,[Microsoft.Management.Infrastructure.CimFlags]::None))
 $row.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create('provider_identity','foreign-collision-retained',[Microsoft.Management.Infrastructure.CimType]::String,[Microsoft.Management.Infrastructure.CimFlags]::None))
 if($Name){$row.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create('Name',$Name,[Microsoft.Management.Infrastructure.CimType]::String,[Microsoft.Management.Infrastructure.CimFlags]::None))}
 Add-Member -InputObject $row -MemberType AliasProperty -Name AliasIdentity -Value $AliasTarget
 Add-Member -InputObject $row -NotePropertyName ForeignProperty -NotePropertyValue 'foreign-adapted'
 return $row
}
function NativeFixture([string]$Alias='InstanceID',[long]$Flags=0){
 $context=Fixture
 $context.rules=@($context.rules | ForEach-Object{NativeRow 'MSFT_NetFirewallRule' $_.InstanceID '' $Alias $Flags})
 foreach($name in @($context.filters.Keys)){
  $context.filters[$name]=@($context.filters[$name] | ForEach-Object{NativeRow ('MSFT_Filter_'+$name) $_.InstanceID '' $Alias $Flags})
 }
 $context.profiles=@($context.profiles | ForEach-Object{NativeRow 'MSFT_NetFirewallProfile' $_.Name $_.Name $Alias $Flags})
 $context.settings=@(NativeRow 'MSFT_NetFirewallSetting' 'global' '' $Alias $Flags)
 return $context
}
if($DynamicTargetContract){
 $fixtureTypeNames=[Collections.Generic.List[string]]::new()
 try{
 $expectedGetter='4c13885350db45b07859f387cee1006382074f4271efead21fab12426b2c5bf6'
 $getter=$null
 foreach($data in @(Get-TypeData -TypeName '*MSFT_NetProtocolPortFilter')){
  $member=$data.Members['DynamicTarget']
  if($member -is [Management.Automation.Runspaces.ScriptPropertyData]){
   $sha=[Security.Cryptography.SHA256]::Create()
   try{$hash=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($member.GetScriptBlock.ToString())))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
   if($hash -ceq $expectedGetter){$getter=$member.GetScriptBlock}
  }
 }
 Assert ($null -ne $getter) 'installed_getter_definition_not_bound'
 function Set-FixtureDynamicGetter($Row,$ScriptBlock){
  # A new process-local type name overrides only this synthetic object's view;
  # the installed NetSecurity type definition is never removed or modified.
  $name='TSW.Epic440.DynamicTarget.'+[Guid]::NewGuid().ToString('N')
  Update-TypeData -TypeName $name -MemberType ScriptProperty -MemberName DynamicTarget -Value $ScriptBlock -Force
  $fixtureTypeNames.Add($name);$Row.PSObject.TypeNames.Insert(0,$name)
 }
 function DynamicRow([uint32]$Value,[string]$Class='MSFT_NetProtocolPortFilter',[string]$Property='DynamicTarget',
                     [string]$NativeType='UInt32',[bool]$Backing=$true,[bool]$KnownGetter=$true,[long]$Flags=33554436){
  $row=NativeRow $Class 'rule-0'
  # Complete the public native port fields used by installed typed views.
  $row.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create('Protocol','6',[Microsoft.Management.Infrastructure.CimType]::String,[Microsoft.Management.Infrastructure.CimFlags]::None))
  foreach($field in @('LocalPort','RemotePort','IcmpType')){
   $row.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create($field,[string[]]@('Any'),[Microsoft.Management.Infrastructure.CimType]::StringArray,[Microsoft.Management.Infrastructure.CimFlags]::None))
  }
  if($Backing){
   $nativeValue=if($NativeType -ceq 'UInt64'){[uint64]$Value}else{$Value}
   $row.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create('DynamicTransport',$nativeValue,([Microsoft.Management.Infrastructure.CimType]::$NativeType),([Microsoft.Management.Infrastructure.CimFlags]$Flags)))
   # Create marks a new synthetic property modified; model a provider read
   # through the real SDK's public state API rather than forging its Flags.
   $row.CimInstanceProperties['DynamicTransport'].IsValueModified=(($Flags -band 33554432) -eq 0)
  }
  $scriptBlock=if($KnownGetter){$getter}else{[scriptblock]::Create($getter.ToString()+"`n# changed getter source")}
  if($Property -ceq 'DynamicTarget' -and !$KnownGetter){Set-FixtureDynamicGetter $row $scriptBlock}
  elseif($null -eq $row.PSObject.Properties[$Property]){Add-Member -InputObject $row -MemberType ScriptProperty -Name $Property -Value $scriptBlock}
  else{Assert ($Property -ceq 'DynamicTarget' -and $KnownGetter -and
    $row.PSObject.Properties[$Property] -is [Management.Automation.PSScriptProperty]) 'unexpected_existing_fixture_member'}
  return $row
 }
 function DynamicFixture($Row){$context=Fixture;$context.filters.port[0]=$Row;return $context}
 $script:ctx=DynamicFixture (DynamicRow ([uint32]::MaxValue))
 $initial=Capture;$fingerprint=Get-WslMaintenanceDigest $initial;$data=$initial | ConvertFrom-Json
 $value=$data.filters.port[0].value;$entry=$value.adapted_overrides.DynamicTarget;$descriptor=$entry[3]
 Assert ($value.native_properties.DynamicTransport[0] -ceq 'UInt32' -and
  $value.native_properties.DynamicTransport[1] -eq 33554436 -and
  $value.native_properties.DynamicTransport[2] -eq [uint32]::MaxValue) 'complete_native_backing_retained'
 Assert ($entry.Count -eq 4 -and $entry[0] -ceq 'ScriptProperty' -and $null -eq $entry[1] -and $null -eq $entry[2]) 'no_converted_value_fabricated'
 Assert ($descriptor.representation -ceq 'tsw.netsecurity.dynamic-target-conversion-error.v1' -and
  $descriptor.native_property -ceq 'DynamicTransport' -and $descriptor.getter_sha256 -ceq $expectedGetter -and
  $descriptor.member_clr -ceq 'System.Management.Automation.PSScriptProperty' -and
  $descriptor.exception_types.Count -eq 4 -and
  $descriptor.exception_types[3] -ceq 'System.Management.Automation.PSInvalidCastException') 'explicit_pinned_conversion_descriptor'
 $alias=$value.adapted_overrides.DynamicTransport
 Assert ($alias.Count -eq 4 -and $alias[0] -ceq 'AliasProperty' -and $null -eq $alias[1] -and
  $alias[2] -ceq 'DynamicTarget') 'original_alias_target_retained'
 Assert ($alias[3].representation -ceq 'tsw.netsecurity.dynamic-target-conversion-error.v1' -and
  $alias[3].native_property -ceq 'DynamicTransport' -and $alias[3].getter_sha256 -ceq $expectedGetter -and
  $alias[3].member_clr -ceq 'System.Management.Automation.PSAliasProperty' -and
  $alias[3].exception_types.Count -eq 4) 'exact_alias_conversion_descriptor'
 Assert ((Fingerprint) -ceq $fingerprint) 'descriptor_snapshot_stable'
 $script:ctx=DynamicFixture (DynamicRow ([uint32]::MaxValue-1))
 Assert ((Fingerprint) -cne $fingerprint) 'unknown_native_value_change_not_discarded'
 $cases=7
 foreach($fault in @('class','property','native_type','getter','flags','exception')){
  $row=switch($fault){
   'class'{DynamicRow ([uint32]::MaxValue) 'MSFT_Other_Class'}
   'property'{DynamicRow ([uint32]::MaxValue) 'MSFT_NetProtocolPortFilter' 'OtherDerivedView'}
   'native_type'{DynamicRow ([uint32]::MaxValue) 'MSFT_NetProtocolPortFilter' 'DynamicTarget' 'UInt64'}
   'getter'{DynamicRow ([uint32]::MaxValue) 'MSFT_NetProtocolPortFilter' 'DynamicTarget' 'UInt32' $true $false}
   'flags'{DynamicRow ([uint32]::MaxValue) 'MSFT_NetProtocolPortFilter' 'DynamicTarget' 'UInt32' $true $true 0}
   'exception'{$r=DynamicRow ([uint32]::MaxValue);Set-FixtureDynamicGetter $r {throw 'OTHER_FAILURE'};$r}
  }
  $script:ctx=DynamicFixture $row;MustFail 'FIREWALL_DATA_UNREADABLE';$cases++
 }
 # Exercise identity/backing guards directly with the actual getter's ErrorRecord;
 # a missing backing field may itself produce a readable null in PowerShell and
 # must not be faked into a nonexistent real getter exception.
 $tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($command,[ref]$tokens,[ref]$errors)
 $definition=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq 'DynamicTargetConversion'},$true))
 Assert ($errors.Count -eq 0 -and $definition.Count -eq 1) 'exact_conversion_helper_definition'
 . ([scriptblock]::Create($definition[0].Extent.Text))
 $row=DynamicRow ([uint32]::MaxValue);$member=$row.PSObject.Properties['DynamicTarget'];$failure=$null
 $valueGetter=[Delegate]::CreateDelegate([Func[Management.Automation.PSMemberInfo,object]],[Management.Automation.PSMemberInfo].GetProperty('Value').GetGetMethod())
 try{$null=$valueGetter.Invoke($member)}catch{$failure=$_}
 Assert ($null -ne $failure) 'actual_getter_conversion_did_not_fail'
 $native=@{DynamicTransport=@('UInt32',33554436,[uint32]::MaxValue)}
 $raw=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
 Assert ($null -eq (DynamicTargetConversion $failure $member $row $native $raw)) 'missing_backing_admitted';$cases++
 $raw.Add('DynamicTransport',[uint32]::MaxValue)
 $other=[Management.Automation.PSNoteProperty]::new('DynamicTarget','synthetic')
 Assert ($null -eq (DynamicTargetConversion $failure $other $row $native $raw)) 'wrong_member_kind_admitted';$cases++
 $raw.Add('DynamicTarget',[uint32]1)
 Assert ($null -eq (DynamicTargetConversion $failure $member $row $native $raw)) 'native_name_collision_admitted';$cases++
 $raw.Remove('DynamicTarget') | Out-Null
 $alias=$row.PSObject.Properties['DynamicTransport'];$aliasFailure=$null
 try{$null=$valueGetter.Invoke($alias)}catch{$aliasFailure=$_}
 Assert ($null -ne $aliasFailure -and $null -ne (DynamicTargetConversion $aliasFailure $alias $row $native $raw)) 'actual_alias_conversion_not_recognized';$cases++
 $wrongAlias=[Management.Automation.PSAliasProperty]::new('DynamicTransport','OtherDerivedView')
 Assert ($null -eq (DynamicTargetConversion $aliasFailure $wrongAlias $row $native $raw)) 'wrong_alias_reference_admitted';$cases++
 $changed=DynamicRow ([uint32]::MaxValue) 'MSFT_NetProtocolPortFilter' 'DynamicTarget' 'UInt32' $true $false
 Assert ($null -eq (DynamicTargetConversion $aliasFailure $changed.PSObject.Properties['DynamicTransport'] $changed $native $raw)) 'alias_changed_target_getter_admitted';$cases++
 $otherFailure=$null;try{throw 'OTHER_FAILURE'}catch{$otherFailure=$_}
 Assert ($null -eq (DynamicTargetConversion $otherFailure $alias $row $native $raw)) 'alias_unknown_error_chain_admitted';$cases++
 $script:ctx=Fixture
 Add-Member -InputObject $script:ctx.filters.address[0] -MemberType ScriptProperty -Name UnreadableData -Value {throw 'UNREADABLE_DATA'}
 MustFail 'FIREWALL_DATA_UNREADABLE';$cases++
 [ordered]@{status='PASS';cases=$cases;runtime_mutations=0;live_capability_claim=$false;
  genuine_cim_in_memory=$true;installed_getter_source_bound=$true} | ConvertTo-Json -Compress
 exit 0
 }finally{foreach($name in $fixtureTypeNames){Remove-TypeData -TypeName $name -ErrorAction Stop}}
}
if($NativeCimContract){
 $script:ctx=NativeFixture;$initial=Capture;$fingerprint=Get-WslMaintenanceDigest $initial
 $data=$initial | ConvertFrom-Json;$v=$data.filters.address[0].value;$cases=0
 Assert ($data.schema_version -eq 2 -and $data.rules[0].identity -ceq 'rule-0') 'native_schema_identity'
 Assert ($v.provider_identity[0] -ceq 'MSFT_Filter_address' -and $v.provider_identity[1] -ceq 'root/standardcimv2') 'finite_provider_identity'
 Assert ($v.native_properties.NativeUnknown[0] -ceq 'String' -and $v.native_properties.NativeUnknown[2] -ceq 'native-data') 'native_type_value'
 $flags=[long]$script:ctx.filters.address[0].CimInstanceProperties['NativeUnknown'].Flags
 Assert ($v.native_properties.NativeUnknown[1] -eq $flags) 'native_flags'
 Assert ($v.native_properties.Nullable.Count -eq 3 -and $null -eq $v.native_properties.Nullable[2]) 'native_null'
 Assert ($v.native_properties.EmptyStrings[2].Count -eq 0 -and $null -ne $v.native_properties.EmptyStrings[2]) 'native_empty_array'
 Assert (($v.native_properties.Numbers[2] -join ',') -ceq '1,2') 'native_array_order'
 Assert ($v.adapted_equivalent -contains 'NativeUnknown') 'proven_equivalent_value_reference'
 Assert ($v.alias_links.AliasIdentity -ceq 'InstanceID') 'proven_alias_identity'
 Assert ($v.adapted_overrides.ForeignProperty[3] -ceq 'foreign-adapted') 'foreign_alias_data'
 Assert ($v.native_properties.provider_identity[2] -ceq 'foreign-collision-retained') 'no_reserved_key_overwrite'
 $cases+=11
 $script:ctx=NativeFixture;$script:ctx.reverse=$true;Assert ((Fingerprint) -ceq $fingerprint) 'native_stable_order';$cases++
 foreach($family in @('address','application','interface','interface_type','port','security','service')){
  $script:ctx=NativeFixture;$script:ctx.filters[$family][1].CimInstanceProperties['NativeUnknown'].Value='changed'
  Assert ((Fingerprint) -cne $fingerprint) ('native_lost_family_'+$family);$cases++
 }
 $script:ctx=NativeFixture 'TwinID';Assert ((Fingerprint) -cne $fingerprint) 'alias_target_change_even_equal_value';$cases++
 $script:ctx=NativeFixture 'InstanceID' ([long][Microsoft.Management.Infrastructure.CimFlags]::ReadOnly)
 Assert ((Fingerprint) -cne $fingerprint) 'flags_change_retained';$cases++
 $script:ctx=NativeFixture
 Add-Member -InputObject $script:ctx.filters.address[0] -NotePropertyName ForeignProperty -NotePropertyValue 'changed' -Force
 Assert ((Fingerprint) -cne $fingerprint) 'adapted_only_change_retained';$cases++
 $script:ctx=NativeFixture;$script:ctx.filters.address[0]=NativeRow 'MSFT_Other_Class' 'rule-0'
 Assert ((Fingerprint) -cne $fingerprint) 'provider_class_change_retained';$cases++
 $script:ctx=NativeFixture
 Add-Member -InputObject $script:ctx.filters.address[0] -MemberType ScriptProperty -Name UnreadableData -Value {throw 'UNREADABLE_DATA'}
 $failed=$false;try{$null=Capture}catch{$failed=$true};Assert $failed 'unreadable_data_not_ignored';$cases++
 [ordered]@{status='PASS';cases=$cases;runtime_mutations=0;live_capability_claim=$false;genuine_cim_in_memory=$true} | ConvertTo-Json -Compress
 exit 0
}
if($EmitUnicodeSnapshot){
 $script:ctx=Fixture
 $unicode=(-join @([char]0x00fc,[char]0x2603,[char]0x4e2d))
 $script:ctx.filters.address[0].ForeignProperty=$unicode
 $payload=Capture
 # The actual getter sets the process Console encoding. This direct marker
 # proves non-ASCII byte transport independently of JSON escaping choices.
 [Console]::WriteLine($unicode)
 [Console]::WriteLine($payload)
 exit 0
}
$cases=0
$script:ctx=Fixture;$original=Capture;$before=Get-WslMaintenanceDigest $original
$data=$original | ConvertFrom-Json
Assert ($data.store -ceq 'ActiveStore' -and $data.rules.Count -eq 3) 'complete_store'
foreach($family in @('address','application','interface','interface_type','port','security','service')){
 Assert ($data.filters.$family.Count -eq 3 -and $data.filters.$family[0].value.ForeignProperty -ceq ('PRIVATE_CANARY_'+$family)) 'all_foreign_properties'
}
$cases++
$script:ctx=Fixture;$script:ctx.reverse=$true
Assert ((Fingerprint) -ceq $before) 'enumeration_order_drift';$cases++
foreach($family in @('address','application','interface','interface_type','port','security','service')){
 $script:ctx=Fixture;$script:ctx.filters[$family][1].ForeignProperty='changed'
 Assert ((Fingerprint) -cne $before) ('lost_family_'+$family);$cases++
}
foreach($family in @('rules','profiles','settings')){
 $script:ctx=Fixture;$script:ctx[$family][0] | Add-Member -NotePropertyName AddedForeignProperty -NotePropertyValue 'changed'
 Assert ((Fingerprint) -cne $before) ('lost_global_'+$family);$cases++
}
foreach($count in @(3,30)){
 $script:ctx=Fixture $count;$null=Capture
 $calls=($script:ctx.calls.Values | Measure-Object -Sum).Sum
 Assert ($calls -eq 31) 'nonconstant_provider_call_count'
 Assert ($script:ctx.calls.rules -eq 1 -and $script:ctx.calls.profiles -eq 1 -and $script:ctx.calls.settings -eq 1) 'repeated_global_query'
 $cases++
}
foreach($family in @('address','application','interface','interface_type','port','security','service','rules','profiles','settings')){
 $script:ctx=Fixture;$script:ctx.fault='failure_'+$family;MustFail 'PROVIDER_UNREADABLE';$cases++
}
$script:ctx=Fixture;$script:ctx.filters.address+=@($script:ctx.filters.address[0]);MustFail 'FIREWALL_IDENTITY_AMBIGUOUS';$cases++
$script:ctx=Fixture;$script:ctx.rules+=@($script:ctx.rules[0]);MustFail 'FIREWALL_IDENTITY_AMBIGUOUS';$cases++
$script:ctx=Fixture;$script:ctx.filters.port=$script:ctx.filters.port[0..1];MustFail 'FIREWALL_ASSOCIATION_INCOMPLETE';$cases++
$script:ctx=Fixture;$script:ctx.filters.port[0].InstanceID='foreign';MustFail 'FIREWALL_ASSOCIATION_INCOMPLETE';$cases++
foreach($fault in @('wrong_association','association_drift')){
 $script:ctx=Fixture;$script:ctx.fault=$fault
 MustFail $(if($fault -ceq 'wrong_association'){'FIREWALL_ASSOCIATION_UNSUPPORTED'}else{'FIREWALL_ASSOCIATION_DRIFT'});$cases++
}
$script:ctx=Fixture;$script:ctx.filters.address[0].InstanceID=$null;MustFail 'FIREWALL_IDENTITY_AMBIGUOUS';$cases++
$script:ctx=Fixture
$ambiguous=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
$ambiguous.Add('Case','first');$ambiguous.Add('case','second');$script:ctx.filters.address[0].Nested=$ambiguous
MustFail 'FIREWALL_PROPERTY_AMBIGUOUS';$cases++
$script:ctx=Fixture 8193;MustFail 'FIREWALL_ENTITY_BOUND';$cases++
$script:ctx=Fixture;$script:ctx.settings[0].Opaque='x'*14680065;MustFail 'FIREWALL_OUTPUT_BOUND';$cases++
$script:ctx=Fixture 0;$empty=Capture | ConvertFrom-Json
Assert ($empty.rules.Count -eq 0 -and $empty.filters.address.Count -eq 0) 'empty_complete_store';$cases++
[ordered]@{status='PASS';cases=$cases;runtime_mutations=0;live_capability_claim=$false;provider_calls_independent_of_rule_count=$true} | ConvertTo-Json -Compress
