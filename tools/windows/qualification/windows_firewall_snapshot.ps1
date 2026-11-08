$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false,$true)
# Open-instance CLR accessors propagate getter failures; PowerShell's dynamic
# property adapter can otherwise silently turn a failed getter into null.
$script:firewallPsValue=[Delegate]::CreateDelegate([Func[Management.Automation.PSMemberInfo,object]],[Management.Automation.PSMemberInfo].GetProperty('Value').GetGetMethod())
function Canonical($Item,[int]$Depth=0){
 if($Depth -gt 90){throw 'FIREWALL_DEPTH_BOUND'}
 if($null -eq $Item -or $Item -is [string] -or $Item -is [ValueType]){return $Item}
 if($Item -is [Microsoft.Management.Infrastructure.CimInstance]){
  if($null -eq $script:firewallNativeValue){
   $script:firewallNativeValue=[Delegate]::CreateDelegate([Func[Microsoft.Management.Infrastructure.CimProperty,object]],[Microsoft.Management.Infrastructure.CimProperty].GetProperty('Value').GetGetMethod())
   $script:firewallNativeType=[Delegate]::CreateDelegate([Func[Microsoft.Management.Infrastructure.CimProperty,Microsoft.Management.Infrastructure.CimType]],[Microsoft.Management.Infrastructure.CimProperty].GetProperty('CimType').GetGetMethod())
   $flagProperty=[Microsoft.Management.Infrastructure.CimProperty].GetProperty('Flags')
   $script:firewallNativeFlags=if($null -ne $flagProperty){[Delegate]::CreateDelegate([Func[Microsoft.Management.Infrastructure.CimProperty,Microsoft.Management.Infrastructure.CimFlags]],$flagProperty.GetGetMethod())}else{$null}
  }
  $system=$Item.CimSystemProperties
  $provider=[object[]]::new(4)
  $provider[0]=$system.ClassName;$provider[1]=$system.Namespace;$provider[2]=$system.ServerName;$provider[3]=$system.Path
  $native=[ordered]@{};$raw=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
  $nativeNames=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
  foreach($p in @($Item.CimInstanceProperties | Sort-Object Name)){
   if($p.Name -isnot [string] -or !$p.Name -or !$nativeNames.Add($p.Name)){throw 'FIREWALL_PROPERTY_AMBIGUOUS'}
   try{$value=$script:firewallNativeValue.Invoke($p);$cimType=$script:firewallNativeType.Invoke($p);$cimFlags=if($null -ne $script:firewallNativeFlags){[long]$script:firewallNativeFlags.Invoke($p)}else{$null}}catch{throw 'FIREWALL_DATA_UNREADABLE'}
   $raw.Add($p.Name,$value)
   if($null -ne $value -and $value -isnot [string] -and $value -isnot [ValueType]){
    $simple=$false
    if($value -is [array]){$type=$value.GetType().GetElementType();$simple=($type -eq [string] -or $type.IsValueType)}
    if(!$simple){$value=Canonical $value ($Depth+1)}
   }
   $entry=[object[]]::new(3);$entry[0]=[string]$cimType;$entry[1]=$cimFlags
   $entry[2]=$value;$native[$p.Name]=$entry
  }
  $equivalent=[Collections.Generic.List[string]]::new();$aliases=[ordered]@{};$enums=[ordered]@{};$overrides=[ordered]@{}
  $adaptedNames=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
  foreach($p in @($Item.PSObject.Properties | Sort-Object Name)){
   if($p.Name -isnot [string] -or !$p.Name -or !$adaptedNames.Add($p.Name)){throw 'FIREWALL_PROPERTY_AMBIGUOUS'}
   # These are SDK introspection wrappers, not firewall configuration. Native
   # data with a colliding name is still fully present in native_properties.
   if($p.MemberType -eq [Management.Automation.PSMemberTypes]::Property -and $p.Name -in @('CimClass','CimInstanceProperties','CimSystemProperties')){continue}
   try{$value=$script:firewallPsValue.Invoke($p)}catch{throw 'FIREWALL_DATA_UNREADABLE'}
   $target=$null;$isAlias=$false
   if($p.MemberType -eq [Management.Automation.PSMemberTypes]::AliasProperty -and $raw.ContainsKey($p.ReferencedMemberName)){$target=$p.ReferencedMemberName;$isAlias=$true}
   elseif($p.MemberType -eq [Management.Automation.PSMemberTypes]::Property -and $raw.ContainsKey($p.Name)){$target=$p.Name}
   if($null -ne $target){
    $original=$raw[$target];$equal=($null -eq $original -and $null -eq $value)
    if($null -ne $original -and $null -ne $value -and $original.GetType() -eq $value.GetType()){
     if($value -is [string] -or $value -is [ValueType]){$equal=$value.Equals($original)}
     elseif($value -is [array]){$element=$value.GetType().GetElementType();if($element -eq [string] -or $element.IsValueType){$equal=[Collections.StructuralComparisons]::StructuralEqualityComparer.Equals($value,$original)}}
    }
    if($equal){if($isAlias){$aliases[$p.Name]=$target}else{$equivalent.Add($p.Name)};continue}
   }
   if($p.MemberType -eq [Management.Automation.PSMemberTypes]::Property -and $raw.ContainsKey($p.Name) -and $null -ne $value -and $value.GetType().IsEnum -and $null -ne $raw[$p.Name]){
    $same=$false
    try{$same=$raw[$p.Name].Equals([Convert]::ChangeType($value,$raw[$p.Name].GetType(),[Globalization.CultureInfo]::InvariantCulture))}catch{}
    if($same){$enums[$p.Name]=@($value.GetType().FullName,$value.ToString());continue}
   }
   $entry=[object[]]::new(4);$entry[0]=[string]$p.MemberType;$entry[1]=if($null -eq $value){$null}else{$value.GetType().FullName}
   $entry[2]=if($p.MemberType -eq [Management.Automation.PSMemberTypes]::AliasProperty){$p.ReferencedMemberName}else{$null}
   $simple=($null -eq $value -or $value -is [string] -or $value -is [ValueType])
   if(!$simple -and $value -is [array]){$type=$value.GetType().GetElementType();$simple=($type -eq [string] -or $type.IsValueType)}
   if($simple){$entry[3]=$value}else{$entry[3]=Canonical $value ($Depth+1)}
   $overrides[$p.Name]=$entry
  }
  return [ordered]@{provider_identity=$provider;native_properties=$native;adapted_equivalent=@($equivalent);alias_links=$aliases;enum_views=$enums;adapted_overrides=$overrides}
 }
 if($Item -is [Microsoft.Management.Infrastructure.CimClass] -or $Item -is [Microsoft.Management.Infrastructure.CimProperty] -or $Item -is [Microsoft.Management.Infrastructure.CimSystemProperties]){throw 'FIREWALL_FRAMEWORK_DATA_UNSUPPORTED'}
 if($Item -is [Collections.IDictionary]){
  $o=[ordered]@{};$names=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
  foreach($key in @($Item.Keys | Sort-Object)){
   if($key -isnot [string] -or !$key -or !$names.Add($key)){throw 'FIREWALL_PROPERTY_AMBIGUOUS'}
   $o[$key]=Canonical $Item[$key] ($Depth+1)
  };return $o
 }
 if($Item -is [Collections.IEnumerable]){return ,@($Item | ForEach-Object{Canonical $_ ($Depth+1)})}
 $o=[ordered]@{};$names=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
 foreach($p in @($Item.PSObject.Properties | Sort-Object Name)){
  if($p.Name -isnot [string] -or !$p.Name -or !$names.Add($p.Name)){throw 'FIREWALL_PROPERTY_AMBIGUOUS'}
  try{$value=$script:firewallPsValue.Invoke($p)}catch{throw 'FIREWALL_DATA_UNREADABLE'}
  $o[$p.Name]=Canonical $value ($Depth+1)
 };return $o
}
function Identity($Item,[string]$Name){
 if($Item -is [Microsoft.Management.Infrastructure.CimInstance]){
  $p=$Item.CimInstanceProperties[$Name];if($null -eq $p){throw 'FIREWALL_IDENTITY_AMBIGUOUS'};return $p.Value
 }
 return $Item.$Name
}
function Rows($Items,[string]$Identity,[int]$Limit){
 $itemsArray=@($Items)
 if($itemsArray.Count -gt $Limit){throw 'FIREWALL_ENTITY_BOUND'}
 $indexed=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
 foreach($item in $itemsArray){
  if($null -eq $item){throw 'FIREWALL_ROW_INVALID'}
  $value=Canonical $item
  $key=if($Identity){Identity $item $Identity}else{ConvertTo-Json -InputObject $value -Depth 100 -Compress}
  if(!$Identity -and [Text.Encoding]::UTF8.GetByteCount($key) -gt 14680064){throw 'FIREWALL_OUTPUT_BOUND'}
  if($key -isnot [string] -or $key.Length -eq 0 -or ($Identity -and $key.Length -gt 4096) -or $key.Contains("`0") -or $indexed.ContainsKey($key)){throw 'FIREWALL_IDENTITY_AMBIGUOUS'}
  $indexed.Add($key,[ordered]@{identity=$key;value=$value})
 }
 $keys=[string[]]@($indexed.Keys);[Array]::Sort($keys,[StringComparer]::Ordinal)
 return ,@($keys | ForEach-Object{$indexed[$_]})
}
$rawRules=@(Get-NetFirewallRule -PolicyStore ActiveStore -ErrorAction Stop)
$rules=Rows $rawRules 'InstanceID' 8192
$profiles=Rows @(Get-NetFirewallProfile -PolicyStore ActiveStore -ErrorAction Stop) 'Name' 16
$settings=Rows @(Get-NetFirewallSetting -PolicyStore ActiveStore -ErrorAction Stop) '' 128
$ruleIDs=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach($rule in $rules){[void]$ruleIDs.Add([string]$rule.identity)}
$families=[ordered]@{}
$commands=[ordered]@{address='Get-NetFirewallAddressFilter';application='Get-NetFirewallApplicationFilter';
 interface='Get-NetFirewallInterfaceFilter';interface_type='Get-NetFirewallInterfaceTypeFilter';
 port='Get-NetFirewallPortFilter';security='Get-NetFirewallSecurityFilter';service='Get-NetFirewallServiceFilter'}
foreach($name in $commands.Keys){
 $command=$commands[$name]
 $raw=@(& $command -PolicyStore ActiveStore -ErrorAction Stop)
 $rows=Rows $raw 'InstanceID' 8192
 $filterIDs=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
 foreach($row in $rows){[void]$filterIDs.Add([string]$row.identity)}
 if(!$ruleIDs.SetEquals($filterIDs)){throw 'FIREWALL_ASSOCIATION_INCOMPLETE'}
 # Native automatically-managed 1:1 association uses actual provider identity
 # fields. Retain the complete independent arrays, never fabricate a joined
 # edge. Fixed first/middle/last native association probes admit this model;
 # rule count cannot increase the number of provider calls.
 if($rules.Count -gt 0){
  $indices=@(0,[int][Math]::Floor($rules.Count/2),($rules.Count-1)) | Select-Object -Unique
  foreach($index in $indices){
   $rule=$rules[$index]
   # Canonical copies retain every property but the supported native cmdlet
   # requires the genuine CimInstance, selected by its exact observed key.
   $original=@($rawRules | Where-Object{(Identity $_ 'InstanceID') -ceq [string]$rule.identity})
   if($original.Count -ne 1){throw 'FIREWALL_ASSOCIATION_INCOMPLETE'}
   $related=@(& $command -PolicyStore ActiveStore -AssociatedNetFirewallRule $original[0] -ErrorAction Stop)
   if($related.Count -ne 1 -or (Identity $related[0] 'InstanceID') -cne [string]$rule.identity){throw 'FIREWALL_ASSOCIATION_UNSUPPORTED'}
   $candidate=Rows $related 'InstanceID' 1
   $bulk=@($rows | Where-Object{[string]$_.identity -ceq [string]$rule.identity})
   if((ConvertTo-Json -InputObject $candidate -Depth 100 -Compress) -cne (ConvertTo-Json -InputObject $bulk -Depth 100 -Compress)){throw 'FIREWALL_ASSOCIATION_DRIFT'}
  }
 }
 $families[$name]=$rows
}
$result=[ordered]@{schema_version=2;store='ActiveStore';association_model='PROVIDER_IDENTITY_ONE_TO_ONE';
 rules=$rules;profiles=$profiles;settings=$settings;filters=$families;
 cim_layout=[ordered]@{provider_identity=@('class_name','namespace','server','path');native_property=@('cim_type','flags','value');adapted_override=@('member_type','clr_type','alias_target','value');enum_view=@('clr_type','name');equivalent_rule='same-name exact CLR type/value';alias_rule='native referenced-member exact CLR type/value'}}
$json=ConvertTo-Json -InputObject $result -Depth 100 -Compress
if([Text.Encoding]::UTF8.GetByteCount($json) -gt 14680064){throw 'FIREWALL_OUTPUT_BOUND'}
$json
