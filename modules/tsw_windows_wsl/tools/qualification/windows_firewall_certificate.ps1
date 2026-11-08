$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
try {
  $utf8=New-Object System.Text.UTF8Encoding($false,$true)
  $sha=[System.Security.Cryptography.SHA256]::Create()
  function Hash-Bytes([byte[]]$bytes) {
    return [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-','').ToLowerInvariant()
  }
  function Assert-Keys($value,[string[]]$keys) {
    if ($value -isnot [pscustomobject]) { throw 'certificate' }
    $names=@($value.PSObject.Properties | ForEach-Object { $_.Name })
    if ($names.Count -ne $keys.Count) { throw 'certificate' }
    foreach($key in $keys) { if (@($names | Where-Object { $_ -ceq $key }).Count -ne 1) { throw 'certificate' } }
  }
  function Assert-Strings($value,[string[]]$expected) {
    if ($value -isnot [array] -or $value.Count -ne $expected.Count) { throw 'certificate' }
    for($i=0;$i -lt $expected.Count;$i++) {
      if ($value[$i] -isnot [string] -or $value[$i] -cne $expected[$i]) { throw 'certificate' }
    }
  }
  function Get-Identities($rows,[int]$maximum) {
    if ($rows -isnot [array] -or $rows.Count -gt $maximum) { throw 'certificate' }
    $ids=[System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($row in $rows) {
      Assert-Keys $row @('identity','value')
      if ($row.identity -isnot [string] -or [string]::IsNullOrEmpty($row.identity) -or
          $row.value -isnot [pscustomobject] -or -not $ids.Add($row.identity)) { throw 'certificate' }
    }
    return ,$ids
  }
  $queryBytes=[Convert]::FromBase64String('QUERY_BASE64')
  $querySha=Hash-Bytes $queryBytes
  if ($queryBytes.Length -gt 65536 -or $querySha -cne 'QUERY_SHA256') { throw 'certificate' }
  $query=$utf8.GetString($queryBytes)
  $outputs=@(& ([ScriptBlock]::Create($query)))
  if ($outputs.Count -ne 1 -or $outputs[0] -isnot [string]) { throw 'certificate' }
  $bytes=$utf8.GetBytes($outputs[0])
  if ($bytes.Length -gt 14680064) { throw 'certificate' }
  $full=ConvertFrom-Json -InputObject $outputs[0] -ErrorAction Stop
  Assert-Keys $full @('schema_version','store','association_model','rules','profiles','settings','filters','cim_layout')
  if (($full.schema_version -isnot [int] -and $full.schema_version -isnot [long]) -or
      $full.schema_version -ne 2 -or $full.store -isnot [string] -or $full.store -cne 'ActiveStore' -or
      $full.association_model -isnot [string] -or $full.association_model -cne 'PROVIDER_IDENTITY_ONE_TO_ONE') { throw 'certificate' }
  $layout=$full.cim_layout
  Assert-Keys $layout @('provider_identity','native_property','adapted_override','enum_view','equivalent_rule','alias_rule')
  Assert-Strings $layout.provider_identity @('class_name','namespace','server','path')
  Assert-Strings $layout.native_property @('cim_type','flags','value')
  Assert-Strings $layout.adapted_override @('member_type','clr_type','alias_target','value')
  Assert-Strings $layout.enum_view @('clr_type','name')
  if ($layout.equivalent_rule -isnot [string] -or $layout.equivalent_rule -cne 'same-name exact CLR type/value' -or
      $layout.alias_rule -isnot [string] -or $layout.alias_rule -cne 'native referenced-member exact CLR type/value') { throw 'certificate' }
  $rules=Get-Identities $full.rules 8192
  $profiles=Get-Identities $full.profiles 16
  $settings=Get-Identities $full.settings 128
  $filterKinds=@('address','application','interface','interface_type','port','security','service')
  Assert-Keys $full.filters $filterKinds
  $counts=[ordered]@{rules=$rules.Count;profiles=$profiles.Count;settings=$settings.Count}
  foreach($kind in $filterKinds) {
    $ids=Get-Identities $full.filters.$kind 8192
    if (-not $rules.SetEquals($ids)) { throw 'certificate' }
    $counts[$kind]=$ids.Count
  }
  $certificate=[ordered]@{
    schema_version='tsw.windows-firewall-certificate.v1';query_sha256=$querySha
    snapshot_sha256=(Hash-Bytes $bytes);snapshot_bytes=$bytes.Length;snapshot_schema_version=2
    store='ActiveStore';association_model='PROVIDER_IDENTITY_ONE_TO_ONE';counts=$counts
  }
  [Console]::Out.WriteLine(($certificate | ConvertTo-Json -Depth 4 -Compress))
} catch {
  [Console]::Error.WriteLine('WINDOWS_FIREWALL_CERTIFICATE_FAILED')
  exit 2
}
