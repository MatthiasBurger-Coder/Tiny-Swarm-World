# Pester 4-compatible syntax; all certificate-store access is mocked.
$repositoryRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
. (Join-Path $repositoryRoot 'tools/windows/tsw-tls-trust.ps1')

function New-TswTestCa {
    param([string]$Path, [bool]$Ca = $true, [bool]$Expired = $false, [string]$KeyUsage = '')
    $key = [Security.Cryptography.RSA]::Create(2048)
    try {
        $request = New-Object Security.Cryptography.X509Certificates.CertificateRequest 'CN=Disposable TSW test', $key, ([Security.Cryptography.HashAlgorithmName]::SHA256), ([Security.Cryptography.RSASignaturePadding]::Pkcs1)
        $request.CertificateExtensions.Add((New-Object Security.Cryptography.X509Certificates.X509BasicConstraintsExtension $Ca, $false, 0, $true))
        if ($KeyUsage) {
            $request.CertificateExtensions.Add((New-Object Security.Cryptography.X509Certificates.X509KeyUsageExtension ([Security.Cryptography.X509Certificates.X509KeyUsageFlags]$KeyUsage), $true))
        }
        $end = [DateTimeOffset]::UtcNow.AddDays(2)
        if ($Expired) { $end = [DateTimeOffset]::UtcNow.AddDays(-1) }
        $cert = $request.CreateSelfSigned([DateTimeOffset]::UtcNow.AddDays(-2), $end)
        try { [IO.File]::WriteAllBytes($Path, $cert.Export('Cert')) } finally { $cert.Dispose() }
    } finally { $key.Dispose() }
}

$script:realWriteReceipt = ${function:Write-TswReceipt}
$script:realTestReceipt = ${function:Test-TswReceipt}

Describe 'Standalone CurrentUser public CA trust' {
    BeforeEach {
        $script:caPath = Join-Path $TestDrive 'ca.der'
        New-TswTestCa $script:caPath
        $script:sha = Get-TswCertificateSha256 ([IO.File]::ReadAllBytes($script:caPath))
        $script:storeBytes = $null
        $script:receiptPath = Join-Path $TestDrive 'owned.receipt'
        Remove-Item -LiteralPath $script:receiptPath -Force -ErrorAction SilentlyContinue
        Mock Get-TswRootCertificates {
            if ($script:storeBytes) {
                New-Object Security.Cryptography.X509Certificates.X509Certificate2 -ArgumentList (,$script:storeBytes)
            }
        }
        Mock Add-TswRootCertificate { param($Certificate) $script:storeBytes = $Certificate.RawData }
        Mock Remove-TswRootCertificate { $script:storeBytes = $null }
        Mock Get-TswReceiptPath { $script:receiptPath }
        Mock Write-TswReceipt { [IO.File]::WriteAllText($script:receiptPath, 'owned') }
        Mock Test-TswReceipt { Test-Path -LiteralPath $script:receiptPath }
    }

    It 'defaults to read-only inspection without state creation' {
        $result = Invoke-TswTlsTrust -CertificatePath $script:caPath
        $result.Status | Should Be 'absent'
        $result.Fingerprint | Should Be $script:sha
        $result.Store | Should Be 'CurrentUser/Root'
        Assert-MockCalled Add-TswRootCertificate -Times 0 -Exactly -Scope It
        Assert-MockCalled Get-TswReceiptPath -Times 0 -Exactly -Scope It
    }
    It 'requires approval and independent fingerprint for mutations' {
        { Invoke-TswTlsTrust install $script:caPath -Approve } | Should Throw
        { Invoke-TswTlsTrust install $script:caPath $script:sha } | Should Throw
        { Invoke-TswTlsTrust remove $script:caPath -Approve } | Should Throw
        Assert-MockCalled Add-TswRootCertificate -Times 0 -Exactly -Scope It
        Assert-MockCalled Remove-TswRootCertificate -Times 0 -Exactly -Scope It
    }
    It 'rejects wrong fingerprint before accessing the store' {
        { Invoke-TswTlsTrust install $script:caPath ('0' * 64) -Approve } | Should Throw
        Assert-MockCalled Get-TswRootCertificates -Times 0 -Exactly -Scope It
    }
    It 'rejects private key material' {
        [IO.File]::WriteAllText($script:caPath, '-----BEGIN PRIVATE KEY-----')
        { Invoke-TswTlsTrust install $script:caPath $script:sha -Approve } | Should Throw
        Assert-MockCalled Add-TswRootCertificate -Times 0 -Exactly -Scope It
    }
    It 'rejects non CA certificates' {
        New-TswTestCa $script:caPath -Ca $false
        { Invoke-TswTlsTrust -CertificatePath $script:caPath } | Should Throw
    }
    It 'rejects expired certificates' {
        New-TswTestCa $script:caPath -Expired $true
        { Invoke-TswTlsTrust -CertificatePath $script:caPath } | Should Throw
    }
    It 'rejects an explicit key usage without certificate signing' {
        New-TswTestCa $script:caPath -KeyUsage 'DigitalSignature'
        $fingerprint = Get-TswCertificateSha256 ([IO.File]::ReadAllBytes($script:caPath))
        { Invoke-TswTlsTrust install $script:caPath $fingerprint -Approve } | Should Throw
        Assert-MockCalled Add-TswRootCertificate -Times 0 -Exactly -Scope It
    }
    It 'accepts explicit certificate signing key usage' {
        New-TswTestCa $script:caPath -KeyUsage 'KeyCertSign, CrlSign'
        $fingerprint = Get-TswCertificateSha256 ([IO.File]::ReadAllBytes($script:caPath))
        (Invoke-TswTlsTrust install $script:caPath $fingerprint -Approve).Status | Should Be 'installed'
    }
    It 'allows expired removal only with an exact protected receipt and fingerprint' {
        New-TswTestCa $script:caPath -Expired $true
        $script:storeBytes = [IO.File]::ReadAllBytes($script:caPath)
        $fingerprint = Get-TswCertificateSha256 $script:storeBytes
        { Invoke-TswTlsTrust install $script:caPath $fingerprint -Approve } | Should Throw
        { Invoke-TswTlsTrust remove $script:caPath $fingerprint -Approve } | Should Throw
        Assert-MockCalled Remove-TswRootCertificate -Times 0 -Exactly -Scope It
        # Exercise real DPAPI receipt validation inside the mocked-store workflow.
        $cert = Read-TswPublicCa $script:caPath -AllowExpired
        try {
            & $script:realWriteReceipt $script:receiptPath $cert
            Mock Test-TswReceipt { param($Path, $Certificate) & $script:realTestReceipt $Path $Certificate }
            { Invoke-TswTlsTrust remove $script:caPath ('0' * 64) -Approve } | Should Throw
            $otherPath = Join-Path $TestDrive 'other-expired.der'
            New-TswTestCa $otherPath -Expired $true
            $otherFingerprint = Get-TswCertificateSha256 ([IO.File]::ReadAllBytes($otherPath))
            { Invoke-TswTlsTrust remove $otherPath $otherFingerprint -Approve } | Should Throw
            Assert-MockCalled Remove-TswRootCertificate -Times 0 -Exactly -Scope It
            (Invoke-TswTlsTrust remove $script:caPath $fingerprint -Approve).Status | Should Be 'removed'
            Assert-MockCalled Remove-TswRootCertificate -Times 1 -Exactly -Scope It
        } finally { $cert.Dispose() }
    }
    It 'accepts a single PEM and rejects multiple PEM certificates' {
        $pem = "-----BEGIN CERTIFICATE-----`n" + [Convert]::ToBase64String([IO.File]::ReadAllBytes($script:caPath)) + "`n-----END CERTIFICATE-----`n"
        [IO.File]::WriteAllText($script:caPath, $pem)
        (Invoke-TswTlsTrust -CertificatePath $script:caPath -ExpectedSha256 $script:sha).Status | Should Be 'absent'
        [IO.File]::WriteAllText($script:caPath, $pem + $pem)
        { Invoke-TswTlsTrust -CertificatePath $script:caPath } | Should Throw
    }
    It 'rejects trailing DER data and network paths' {
        $bytes = [IO.File]::ReadAllBytes($script:caPath)
        [IO.File]::WriteAllBytes($script:caPath, ($bytes + $bytes))
        { Invoke-TswTlsTrust -CertificatePath $script:caPath } | Should Throw
        { Assert-TswLocalPath '\\server\share\ca.der' } | Should Throw
        { Assert-TswLocalPath 'https://example.invalid/ca.pem' } | Should Throw
    }
    It 'adds once and leaves repeat installation unchanged' {
        (Invoke-TswTlsTrust install $script:caPath $script:sha -Approve).Status | Should Be 'installed'
        (Invoke-TswTlsTrust install $script:caPath $script:sha -Approve).Status | Should Be 'already-trusted'
        Assert-MockCalled Add-TswRootCertificate -Times 1 -Exactly -Scope It
        Assert-MockCalled Write-TswReceipt -Times 1 -Exactly -Scope It
    }
    It 'rejects a thumbprint match with different actual bytes' {
        $cert = Read-TswPublicCa $script:caPath
        try { $script:thumbprint = $cert.Thumbprint } finally { $cert.Dispose() }
        Mock Get-TswRootCertificates {
            [pscustomobject]@{ RawData = [byte[]]@(1, 2, 3); Thumbprint = $script:thumbprint }
        }
        { Invoke-TswTlsTrust install $script:caPath $script:sha -Approve } | Should Throw
        Assert-MockCalled Add-TswRootCertificate -Times 0 -Exactly -Scope It
    }
    It 'never records or removes pre-existing trust' {
        $script:storeBytes = [IO.File]::ReadAllBytes($script:caPath)
        (Invoke-TswTlsTrust install $script:caPath $script:sha -Approve).Status | Should Be 'already-trusted'
        { Invoke-TswTlsTrust remove $script:caPath $script:sha -Approve } | Should Throw
        Assert-MockCalled Write-TswReceipt -Times 0 -Exactly -Scope It
        Assert-MockCalled Remove-TswRootCertificate -Times 0 -Exactly -Scope It
    }
    It 'does not record provenance when import throws' {
        Mock Add-TswRootCertificate { throw 'failed import' }
        { Invoke-TswTlsTrust install $script:caPath $script:sha -Approve } | Should Throw
        Assert-MockCalled Write-TswReceipt -Times 0 -Exactly -Scope It
    }
    It 'does not record provenance when import returns without adding' {
        Mock Add-TswRootCertificate { }
        { Invoke-TswTlsTrust install $script:caPath $script:sha -Approve } | Should Throw
        Assert-MockCalled Write-TswReceipt -Times 0 -Exactly -Scope It
    }
    It 'preserves trust when recording provenance fails' {
        Mock Write-TswReceipt { throw 'failed receipt' }
        { Invoke-TswTlsTrust install $script:caPath $script:sha -Approve } | Should Throw
        { Invoke-TswTlsTrust remove $script:caPath $script:sha -Approve } | Should Throw
        Assert-MockCalled Remove-TswRootCertificate -Times 0 -Exactly -Scope It
    }
    It 'removes only an owned exact addition and consumes its receipt' {
        Invoke-TswTlsTrust install $script:caPath $script:sha -Approve | Out-Null
        (Invoke-TswTlsTrust remove $script:caPath $script:sha -Approve).Status | Should Be 'removed'
        Test-Path -LiteralPath $script:receiptPath | Should Be $false
        Assert-MockCalled Remove-TswRootCertificate -Times 1 -Exactly -Scope It
    }
    It 'preserves unrelated store certificates during removal' {
        $otherPath = Join-Path $TestDrive 'unrelated.der'
        New-TswTestCa $otherPath
        $otherBytes = [IO.File]::ReadAllBytes($otherPath)
        $script:certificates = @{}
        $otherHash = Get-TswCertificateSha256 $otherBytes
        $script:certificates[$otherHash] = $otherBytes
        Mock Get-TswRootCertificates {
            foreach ($bytes in $script:certificates.Values) {
                New-Object Security.Cryptography.X509Certificates.X509Certificate2 -ArgumentList (,$bytes)
            }
        }
        Mock Add-TswRootCertificate {
            param($Certificate)
            $script:certificates[(Get-TswCertificateSha256 $Certificate.RawData)] = $Certificate.RawData
        }
        Mock Remove-TswRootCertificate {
            param($Certificate)
            $script:certificates.Remove((Get-TswCertificateSha256 $Certificate.RawData))
        }
        Invoke-TswTlsTrust install $script:caPath $script:sha -Approve | Out-Null
        (Invoke-TswTlsTrust remove $script:caPath $script:sha -Approve).Status | Should Be 'removed'
        $script:certificates.Count | Should Be 1
        [Convert]::ToBase64String($script:certificates[$otherHash]) | Should Be ([Convert]::ToBase64String($otherBytes))
        Assert-MockCalled Remove-TswRootCertificate -Times 1 -Exactly -Scope It
    }
    It 'consumes authority before removal and preserves trust on failed removal' {
        Invoke-TswTlsTrust install $script:caPath $script:sha -Approve | Out-Null
        Mock Remove-TswRootCertificate {
            Test-Path -LiteralPath $script:receiptPath | Should Be $false
        }
        { Invoke-TswTlsTrust remove $script:caPath $script:sha -Approve } | Should Throw
        Test-Path -LiteralPath $script:receiptPath | Should Be $false
        { Invoke-TswTlsTrust remove $script:caPath $script:sha -Approve } | Should Throw
        Assert-MockCalled Remove-TswRootCertificate -Times 1 -Exactly -Scope It
    }
    It 'refuses to reuse stale receipts for a new installation' {
        [IO.File]::WriteAllText($script:receiptPath, 'stale')
        { Invoke-TswTlsTrust install $script:caPath $script:sha -Approve } | Should Throw
        Assert-MockCalled Add-TswRootCertificate -Times 0 -Exactly -Scope It
    }
}

Describe 'Protected receipt primitives with disposable files only' {
    It 'round trips user protected provenance and rejects different certificate bytes' {
        $directory = Join-Path $TestDrive 'protected'
        [void][IO.Directory]::CreateDirectory($directory)
        $first = Join-Path $directory 'first.der'
        $second = Join-Path $directory 'second.der'
        New-TswTestCa $first
        New-TswTestCa $second
        $a = Read-TswPublicCa $first
        $b = Read-TswPublicCa $second
        try {
            $receipt = Join-Path $directory 'test.receipt'
            Write-TswReceipt $receipt $a
            (Test-TswReceipt $receipt $a) | Should Be $true
            (Test-TswReceipt $receipt $b) | Should Be $false
            { Write-TswReceipt $receipt $a } | Should Throw
            [IO.File]::WriteAllText($receipt, '{"fingerprint":"forged"}')
            { Test-TswReceipt $receipt $a } | Should Throw
        } finally { $a.Dispose(); $b.Dispose() }
    }
    It 'rejects foreign write ACLs instead of repairing them' {
        $path = Join-Path $TestDrive 'unsafe'
        [void][IO.Directory]::CreateDirectory($path)
        $acl = Get-Acl -LiteralPath $path
        $everyone = New-Object Security.Principal.SecurityIdentifier 'S-1-1-0'
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule $everyone, 'Modify', 'Allow'))
        Set-Acl -LiteralPath $path -AclObject $acl
        { Assert-TswStateAcl $path } | Should Throw
    }
}

Describe 'Canonical state path guards' {
    BeforeEach {
        $script:stateBase = Join-Path ([Environment]::GetFolderPath('UserProfile')) ('tsw-trust-fixture-' + [Guid]::NewGuid().ToString('N'))
        $acl = New-Object Security.AccessControl.DirectorySecurity
        $sid = Get-TswUserSid
        $acl.SetOwner($sid)
        $acl.SetAccessRuleProtection($true, $false)
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule $sid, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow'))
        [void][IO.Directory]::CreateDirectory($script:stateBase, $acl)
        Mock Get-TswLocalApplicationData { $script:stateBase }
    }
    AfterEach { Remove-Item -LiteralPath $script:stateBase -Recurse -Force }
    It 'does not create state when queried read-only' {
        Get-TswReceiptPath ('A' * 64) | Should Be $null
        Test-Path -LiteralPath (Join-Path $script:stateBase 'TinySwarmWorld') | Should Be $false
    }
    It 'creates canonical protected directories and fingerprint-only receipt names' {
        $path = Get-TswReceiptPath ('a' * 64) -Create
        $path | Should Be (Join-Path $script:stateBase ('TinySwarmWorld/TlsTrust/' + ('A' * 64) + '.receipt'))
        Assert-TswStateAcl (Split-Path -Parent $path) -Protected
        { Get-TswReceiptPath '../other' -Create } | Should Throw
    }
    It 'rejects an existing unprotected TlsTrust directory' {
        [void][IO.Directory]::CreateDirectory((Join-Path $script:stateBase 'TinySwarmWorld/TlsTrust'))
        { Get-TswReceiptPath ('A' * 64) -Create } | Should Throw
    }
    It 'coexists with preparation inherited ACLs without rewriting shared state' {
        $parent = Join-Path $script:stateBase 'TinySwarmWorld'
        [void][IO.Directory]::CreateDirectory($parent)
        $preparation = Join-Path $parent 'preparation.marker'
        [IO.File]::WriteAllText($preparation, 'preserve preparation')
        $before = (Get-Acl -LiteralPath $parent).Sddl
        (Get-Acl -LiteralPath $parent).AreAccessRulesProtected | Should Be $false
        $receipt = Get-TswReceiptPath ('A' * 64) -Create
        (Get-Acl -LiteralPath $parent).Sddl | Should Be $before
        [IO.File]::ReadAllText($preparation) | Should Be 'preserve preparation'
        Assert-TswStateAcl (Split-Path -Parent $receipt) -Protected
    }
    It 'rejects a foreign-writable shared parent without rewriting it' {
        $parent = Join-Path $script:stateBase 'TinySwarmWorld'
        [void][IO.Directory]::CreateDirectory($parent)
        $acl = Get-Acl -LiteralPath $parent
        $everyone = New-Object Security.Principal.SecurityIdentifier 'S-1-1-0'
        $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule $everyone, 'Modify', 'Allow'))
        Set-Acl -LiteralPath $parent -AclObject $acl
        $before = (Get-Acl -LiteralPath $parent).Sddl
        { Get-TswReceiptPath ('A' * 64) -Create } | Should Throw
        (Get-Acl -LiteralPath $parent).Sddl | Should Be $before
        Test-Path -LiteralPath (Join-Path $parent 'TlsTrust') | Should Be $false
    }
    It 'rejects reparse ancestors without changing their target' {
        $target = Join-Path $script:stateBase 'target'
        [void][IO.Directory]::CreateDirectory($target)
        $link = Join-Path $script:stateBase 'TinySwarmWorld'
        New-Item -ItemType Junction -Path $link -Target $target | Out-Null
        try {
            { Get-TswReceiptPath ('A' * 64) -Create } | Should Throw
            @(Get-ChildItem -LiteralPath $target).Count | Should Be 0
        } finally { [IO.Directory]::Delete($link) }
    }
}
