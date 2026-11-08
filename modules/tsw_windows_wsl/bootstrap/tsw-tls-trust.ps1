#requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateSet('inspect', 'install', 'remove')][string]$Action = 'inspect',
    [string]$CertificatePath,
    [string]$ExpectedSha256,
    [switch]$Approve
)

function Get-TswCertificateSha256 {
    param([byte[]]$Bytes)
    $hash = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hash.ComputeHash($Bytes))).Replace('-', '') }
    finally { $hash.Dispose() }
}

function Assert-TswLocalPath {
    param([string]$Path)
    if ($Path -notmatch '^[A-Za-z]:[\\/]' -or $Path.Substring(2).Contains(':')) {
        throw 'Local drive path required.'
    }
    $drive = New-Object IO.DriveInfo ([IO.Path]::GetPathRoot($Path))
    if ($drive.DriveType -ne [IO.DriveType]::Fixed) { throw 'Local fixed drive required.' }
    $cursor = [IO.Path]::GetFullPath($Path)
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            if ((Get-Item -LiteralPath $cursor -Force -ErrorAction Stop).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw 'Reparse paths are not allowed.'
            }
        }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
}

function Read-TswPublicCa {
    param([string]$Path, [string]$Fingerprint, [switch]$AllowExpired)
    Assert-TswLocalPath $Path
    $file = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if ($file.PSIsContainer -or $file.Length -gt 1048576) { throw 'Single public CA file required.' }
    $bytes = [IO.File]::ReadAllBytes($file.FullName)
    $text = [Text.Encoding]::ASCII.GetString($bytes)
    if ($text -match 'PRIVATE KEY') { throw 'Private-key material rejected.' }
    if ($text -match '-----') {
        if ($text -cnotmatch '\A\s*-----BEGIN CERTIFICATE-----\s*([A-Za-z0-9+/=\s]+)\s*-----END CERTIFICATE-----\s*\z') {
            throw 'Exactly one public PEM certificate required.'
        }
        $bytes = [Convert]::FromBase64String($Matches[1])
    }
    if ([Security.Cryptography.X509Certificates.X509Certificate2]::GetCertContentType($bytes) -ne
        [Security.Cryptography.X509Certificates.X509ContentType]::Cert) { throw 'Public DER certificate required.' }
    $cert = New-Object Security.Cryptography.X509Certificates.X509Certificate2 -ArgumentList (,$bytes)
    try {
        if ($cert.HasPrivateKey -or [Convert]::ToBase64String($bytes) -cne [Convert]::ToBase64String($cert.RawData)) {
            throw 'Ambiguous or non-public certificate rejected.'
        }
        $constraints = @($cert.Extensions | Where-Object { $_.Oid.Value -eq '2.5.29.19' })
        if ($constraints.Count -ne 1) { throw 'CA basic constraints required.' }
        $basic = New-Object Security.Cryptography.X509Certificates.X509BasicConstraintsExtension
        $basic.CopyFrom($constraints[0])
        if (-not $basic.CertificateAuthority) { throw 'Non-CA certificate rejected.' }
        $usages = @($cert.Extensions | Where-Object { $_.Oid.Value -eq '2.5.29.15' })
        if ($usages.Count -gt 1) { throw 'Ambiguous key usage rejected.' }
        if ($usages.Count -eq 1) {
            $usage = New-Object Security.Cryptography.X509Certificates.X509KeyUsageExtension
            $usage.CopyFrom($usages[0])
            if (-not ($usage.KeyUsages -band [Security.Cryptography.X509Certificates.X509KeyUsageFlags]::KeyCertSign)) {
                throw 'CA key usage must permit certificate signing.'
            }
        }
        $now = [DateTime]::UtcNow
        if ((-not $AllowExpired -and $cert.NotAfter.ToUniversalTime() -le $now) -or $cert.NotBefore.ToUniversalTime() -gt $now) {
            throw 'Certificate is outside its validity period.'
        }
        $actual = Get-TswCertificateSha256 $cert.RawData
        if ($Fingerprint -and ($Fingerprint -notmatch '^[A-Fa-f0-9]{64}$' -or $actual -ine $Fingerprint)) {
            throw 'SHA256 fingerprint mismatch.'
        }
        return $cert
    } catch { $cert.Dispose(); throw }
}

# All store operations are isolated here so unit tests never mutate trust.
function Get-TswRootCertificates {
    $store = New-Object Security.Cryptography.X509Certificates.X509Store 'Root', 'CurrentUser'
    try {
        $store.Open([Security.Cryptography.X509Certificates.OpenFlags]::ReadOnly)
        return @($store.Certificates)
    } finally { $store.Close() }
}

function Add-TswRootCertificate {
    param([Security.Cryptography.X509Certificates.X509Certificate2]$Certificate)
    $store = New-Object Security.Cryptography.X509Certificates.X509Store 'Root', 'CurrentUser'
    try { $store.Open('ReadWrite'); $store.Add($Certificate) } finally { $store.Close() }
}

function Remove-TswRootCertificate {
    param([Security.Cryptography.X509Certificates.X509Certificate2]$Certificate)
    $store = New-Object Security.Cryptography.X509Certificates.X509Store 'Root', 'CurrentUser'
    try { $store.Open('ReadWrite'); $store.Remove($Certificate) } finally { $store.Close() }
}

function Test-TswRootCertificate {
    param([Security.Cryptography.X509Certificates.X509Certificate2]$Certificate)
    $exact = [Convert]::ToBase64String($Certificate.RawData)
    foreach ($existing in @(Get-TswRootCertificates)) {
        if ([Convert]::ToBase64String($existing.RawData) -ceq $exact) { return $true }
        if ($existing.Thumbprint -eq $Certificate.Thumbprint) { throw 'Store certificate collision.' }
    }
    return $false
}

function Get-TswUserSid {
    return [Security.Principal.WindowsIdentity]::GetCurrent().User
}

function Assert-TswStateAcl {
    param([string]$Path, [switch]$Protected)
    Assert-TswLocalPath $Path
    $sid = Get-TswUserSid
    $acl = Get-Acl -LiteralPath $Path -ErrorAction Stop
    $owner = $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
    if ($owner -notin @($sid.Value, 'S-1-5-18', 'S-1-5-32-544')) { throw 'Untrusted state owner.' }
    if ($Protected -and ($owner -ne $sid.Value -or -not $acl.AreAccessRulesProtected)) {
        throw 'Protected user-owned state required.'
    }
    # Reject any foreign allow ACE capable of modifying data, ACLs or ownership.
    $write = [Security.AccessControl.FileSystemRights]'Write, Delete, DeleteSubdirectoriesAndFiles, ChangePermissions, TakeOwnership'
    foreach ($rule in $acl.GetAccessRules($true, $true, [Security.Principal.SecurityIdentifier])) {
        if ($rule.AccessControlType -eq 'Allow' -and ($rule.FileSystemRights -band $write) -and
            $rule.IdentityReference.Value -notin @($sid.Value, 'S-1-5-18', 'S-1-5-32-544')) {
            throw 'State path permits foreign writes.'
        }
    }
}

function Get-TswLocalApplicationData {
    return [Environment]::GetFolderPath('LocalApplicationData')
}

function Get-TswReceiptPath {
    param([string]$Fingerprint, [switch]$Create)
    if ($Fingerprint -notmatch '^[A-Fa-f0-9]{64}$') { throw 'Invalid receipt fingerprint.' }
    $base = Get-TswLocalApplicationData
    $profile = [Environment]::GetFolderPath('UserProfile').TrimEnd('\')
    if (-not $base.StartsWith($profile + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Local user profile state required.'
    }
    $cursor = $base
    while ($cursor.Length -ge $profile.Length) {
        Assert-TswStateAcl $cursor
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
    $sid = Get-TswUserSid
    foreach ($segment in @('TinySwarmWorld', 'TlsTrust')) {
        $base = Join-Path $base $segment
        Assert-TswLocalPath $base
        if (-not (Test-Path -LiteralPath $base)) {
            if (-not $Create) { return $null }
            $acl = New-Object Security.AccessControl.DirectorySecurity
            $acl.SetOwner($sid)
            $acl.SetAccessRuleProtection($true, $false)
            $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule $sid, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow'))
            [void][IO.Directory]::CreateDirectory($base, $acl)
        }
        # Preparation shares this parent and may legitimately inherit safe ACLs.
        # Only our own state directory requires a protected, user-owned ACL.
        Assert-TswStateAcl $base -Protected:($segment -eq 'TlsTrust')
    }
    $path = Join-Path $base ($Fingerprint.ToUpperInvariant() + '.receipt')
    Assert-TswLocalPath $path
    if (Test-Path -LiteralPath $path) { Assert-TswStateAcl $path -Protected }
    return $path
}

function Write-TswReceipt {
    param([string]$Path, [Security.Cryptography.X509Certificates.X509Certificate2]$Certificate)
    # DPAPI binds the receipt to the current user; no caller-supplied state path API.
    Add-Type -AssemblyName System.Security
    $payload = [Text.Encoding]::UTF8.GetBytes('TSW-TLS-1:CurrentUser/Root:' + [Convert]::ToBase64String($Certificate.RawData))
    $bytes = [Security.Cryptography.ProtectedData]::Protect($payload, $null, 'CurrentUser')
    $acl = New-Object Security.AccessControl.FileSecurity
    $sid = Get-TswUserSid
    $acl.SetOwner($sid)
    $acl.SetAccessRuleProtection($true, $false)
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule $sid, 'FullControl', 'Allow'))
    $stream = New-Object IO.FileStream $Path, ([IO.FileMode]::CreateNew), ([Security.AccessControl.FileSystemRights]::Write), ([IO.FileShare]::None), 4096, ([IO.FileOptions]::WriteThrough), $acl
    try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush() } finally { $stream.Dispose() }
    Assert-TswStateAcl $Path -Protected
}

function Test-TswReceipt {
    param([string]$Path, [Security.Cryptography.X509Certificates.X509Certificate2]$Certificate)
    if (-not $Path -or -not (Test-Path -LiteralPath $Path)) { return $false }
    Assert-TswStateAcl $Path -Protected
    if ((Get-Item -LiteralPath $Path).Length -gt 2097152) { throw 'Invalid receipt.' }
    Add-Type -AssemblyName System.Security
    try {
        $bytes = [Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($Path), $null, 'CurrentUser')
        return [Text.Encoding]::UTF8.GetString($bytes) -ceq ('TSW-TLS-1:CurrentUser/Root:' + [Convert]::ToBase64String($Certificate.RawData))
    } catch { throw 'Invalid protected receipt.' }
}

function Invoke-TswTlsTrust {
    [CmdletBinding()]
    param(
        [ValidateSet('inspect', 'install', 'remove')][string]$Action = 'inspect',
        [Parameter(Mandatory = $true)][string]$CertificatePath,
        [string]$ExpectedSha256,
        [switch]$Approve
    )
    $ErrorActionPreference = 'Stop'
    if ($Action -ne 'inspect' -and ($ExpectedSha256 -notmatch '^[A-Fa-f0-9]{64}$' -or -not $Approve)) {
        throw 'Mutation requires independent -ExpectedSha256 and explicit -Approve.'
    }
    $cert = Read-TswPublicCa $CertificatePath $ExpectedSha256 -AllowExpired:($Action -eq 'remove')
    $mutex = $null
    $locked = $false
    try {
        $fingerprint = Get-TswCertificateSha256 $cert.RawData
        if ($Action -ne 'inspect') {
            $mutex = New-Object Threading.Mutex $false, ('Local\TswTlsTrust-' + (Get-TswUserSid).Value)
            try { $locked = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $locked = $true }
            if (-not $locked) { throw 'Another trust operation is active.' }
        }
        $present = Test-TswRootCertificate $cert
        $status = 'absent'
        if ($present) { $status = 'trusted' }
        if ($Action -eq 'install' -and -not $present) {
            $receipt = Get-TswReceiptPath $fingerprint -Create
            if (Test-Path -LiteralPath $receipt) { throw 'Stale receipt requires manual review; trust unchanged.' }
            Add-TswRootCertificate $cert
            if (-not (Test-TswRootCertificate $cert)) { throw 'Import not verified; no removal authority recorded.' }
            # A failed receipt leaves trust intact, requiring manual operator review.
            Write-TswReceipt $receipt $cert
            $status = 'installed'
        } elseif ($Action -eq 'install') { $status = 'already-trusted' }
        if ($Action -eq 'remove') {
            $receipt = Get-TswReceiptPath $fingerprint
            if (-not (Test-TswReceipt $receipt $cert)) { throw 'No matching owned addition; trust preserved.' }
            # Consume authority first: an interruption must not leave a reusable
            # receipt that could later authorize removing independently restored trust.
            # Failure after consumption preserves trust for manual operator review.
            $receipt = Get-TswReceiptPath $fingerprint
            Remove-Item -LiteralPath $receipt -ErrorAction Stop
            if ($present) {
                Remove-TswRootCertificate $cert
                if (Test-TswRootCertificate $cert) { throw 'Removal not verified; manual review required.' }
            }
            $status = 'removed'
        }
        return [pscustomobject]@{ Fingerprint = $fingerprint; Store = 'CurrentUser/Root'; Status = $status }
    } finally {
        if ($locked) { $mutex.ReleaseMutex() }
        if ($mutex) { $mutex.Dispose() }
        $cert.Dispose()
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    try {
        if (-not $CertificatePath) { throw 'CertificatePath required.' }
        Invoke-TswTlsTrust -Action $Action -CertificatePath $CertificatePath -ExpectedSha256 $ExpectedSha256 -Approve:$Approve
    } catch {
        # Native exceptions may contain paths or certificate details; keep CLI output minimal.
        Write-Output 'Store=CurrentUser/Root Status=failed'
        exit 1
    }
}
