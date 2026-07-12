$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$bridgeScript = Join-Path $repositoryRoot "tools\windows\tws-wsl-bridge.ps1"
$runnerScript = Join-Path $repositoryRoot "tools\windows\tws-wsl-bridge-service.ps1"

. $bridgeScript

function Set-TestBridgePaths {
    param([string]$Root)

    $script:ServiceNamespaceRoot = Split-Path -Parent $Root
    $script:BridgeServicePathTestRoot = $ServiceNamespaceRoot
    $script:ServiceRoot = $Root
    $script:ServiceBundleRoot = Join-Path $Root "bundle"
    $script:ServiceLogsRoot = Join-Path $Root "logs"
    $script:StatePath = Join-Path $Root "bridge-state.json"
    $script:ServiceWrapperPath = Join-Path $Root "$ServiceName.exe"
    $script:ServiceDefinitionPath = Join-Path $Root "$ServiceName.xml"
    $script:InstallationManifestPath = Join-Path $Root "installation-manifest.json"
    $script:TransactionJournalPath = Join-Path $Root "upgrade-transaction.json"
    $script:InstalledBridgeScriptPath = Join-Path $ServiceBundleRoot "tws-wsl-bridge.ps1"
    $script:InstalledServiceRunnerPath = Join-Path $ServiceBundleRoot "tws-wsl-bridge-service.ps1"
    $script:InstalledConfigPath = Join-Path $ServiceBundleRoot "tws-wsl-bridge.config.json"
    $script:InstalledPortRegistryPath = Join-Path $ServiceBundleRoot "ports.yaml"
    $script:InstalledBundleManifestPath = Join-Path $ServiceBundleRoot "bundle-manifest.json"
}

function New-TestStagedPayload {
    param(
        [string]$Root,
        [string]$Marker = "new"
    )

    $stagingRoot = Join-Path $Root ".staging-test"
    $bundle = Join-Path $stagingRoot "bundle"
    New-Item -ItemType Directory -Path $bundle -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $bundle "payload.txt") -Value $Marker -NoNewline
    $wrapper = Join-Path $stagingRoot "$ServiceName.exe"
    $definition = Join-Path $stagingRoot "$ServiceName.xml"
    $installationManifest = Join-Path $stagingRoot "installation-manifest.json"
    Set-Content -LiteralPath $wrapper -Value "$Marker-wrapper" -NoNewline
    Set-Content -LiteralPath $definition -Value "$Marker-definition" -NoNewline
    Set-Content -LiteralPath $installationManifest -Value "$Marker-installation" -NoNewline
    return [pscustomobject]@{
        Root                 = $stagingRoot
        Bundle               = $bundle
        Wrapper              = $wrapper
        Definition           = $definition
        InstallationManifest = $installationManifest
        BundleId             = ("A" * 64)
    }
}

function Set-TestActivePayload {
    param(
        [string]$Root,
        [string]$Marker = "old"
    )

    New-Item -ItemType Directory -Path $ServiceBundleRoot -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $ServiceBundleRoot "payload.txt") -Value $Marker -NoNewline
    Set-Content -LiteralPath $ServiceWrapperPath -Value "$Marker-wrapper" -NoNewline
    Set-Content -LiteralPath $ServiceDefinitionPath -Value "$Marker-definition" -NoNewline
    Set-Content -LiteralPath $InstallationManifestPath -Value "$Marker-installation" -NoNewline
}

function Assert-TestActivePayload {
    param([string]$Marker)

    (Get-Content -LiteralPath (Join-Path $ServiceBundleRoot "payload.txt") -Raw) | Should Be $Marker
    (Get-Content -LiteralPath $ServiceWrapperPath -Raw) | Should Be "$Marker-wrapper"
    (Get-Content -LiteralPath $ServiceDefinitionPath -Raw) | Should Be "$Marker-definition"
    (Get-Content -LiteralPath $InstallationManifestPath -Raw) | Should Be "$Marker-installation"
}

Describe "Tiny Swarm World Windows bridge protected state" {
    BeforeEach {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
    }

    It "ignores checkout evidence as cleanup authority" {
        $checkoutEvidence = Join-Path $TestDrive ".tws-wsl-bridge.state.json"
        Set-Content -LiteralPath $checkoutEvidence -Value '{"firewallRulePrefix":"Foreign"}'

        $state = Get-ProtectedBridgeState

        $state | Should Be $null
    }

    It "validates the complete cleanup plan before any mutation" {
        $state = [pscustomobject]@{
            contractVersion = 2
            serviceName = $ServiceName
            agentMode = "windows-service"
            listenAddress = "0.0.0.0"
            wslIp = "172.20.0.2"
            firewallRulePrefix = "Tiny Swarm World"
            mappings = @(
                [pscustomobject]@{ listenPort = 80; connectPort = 80 },
                [pscustomobject]@{ listenPort = 443; connectPort = 70000 }
            )
        }
        Mock Remove-PortProxy {}
        Mock Remove-NetFirewallRule {}

        { New-BridgeCleanupPlan -State $state } | Should Throw

        Assert-MockCalled Remove-PortProxy -Times 0
        Assert-MockCalled Remove-NetFirewallRule -Times 0
    }

    It "creates sorted unique exact cleanup resources" {
        $state = [pscustomobject]@{
            contractVersion = 2
            serviceName = $ServiceName
            agentMode = "windows-service"
            listenAddress = "0.0.0.0"
            wslIp = "172.20.0.2"
            firewallRulePrefix = "Tiny Swarm World"
            mappings = @(
                [pscustomobject]@{ listenPort = 443; connectPort = 443 },
                [pscustomobject]@{ listenPort = 80; connectPort = 80 },
                [pscustomobject]@{ listenPort = 443; connectPort = 443 }
            )
        }

        $plan = New-BridgeCleanupPlan -State $state

        ($plan.Ports -join ",") | Should Be "80,443"
        ($plan.FirewallRuleNames -join ",") | Should Be "Tiny Swarm World TCP 80,Tiny Swarm World TCP 443"
        $plan.Mappings[0].ConnectAddress | Should Be "172.20.0.2"
    }

    It "rejects conflicting duplicate cleanup mappings" {
        $state = [pscustomobject]@{
            contractVersion = 2
            serviceName = $ServiceName
            agentMode = "windows-service"
            listenAddress = "0.0.0.0"
            wslIp = "172.20.0.2"
            firewallRulePrefix = "Tiny Swarm World"
            mappings = @(
                [pscustomobject]@{ listenPort = 443; connectPort = 443 },
                [pscustomobject]@{ listenPort = 443; connectPort = 8443 }
            )
        }

        { New-BridgeCleanupPlan -State $state } | Should Throw
    }

    It "does not remove a stale listener now owned by another tuple" {
        $previous = [pscustomobject]@{
            contractVersion = 2
            serviceName = $ServiceName
            agentMode = "windows-service"
            listenAddress = "0.0.0.0"
            wslIp = "172.20.0.2"
            mappings = @([pscustomobject]@{ listenPort = 80; connectPort = 80 })
        }
        $config = [pscustomobject]@{ listenAddress = "127.0.0.1" }
        Mock Get-ProtectedBridgeState { $previous }
        Mock Get-PortProxyRecords {
            [pscustomobject]@{
                ListenAddress = "0.0.0.0"
                ListenPort = 80
                ConnectAddress = "172.30.0.9"
                ConnectPort = 8080
            }
        }
        Mock Remove-PortProxy {}

        { Remove-StalePortProxyMappings -Config $config -Mappings @() } | Should Throw

        Assert-MockCalled Remove-PortProxy -Times 0 -Scope It
    }
}

Describe "Tiny Swarm World Windows bridge payload transaction" {
    BeforeEach {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        New-Item -ItemType Directory -Path $ServiceRoot -Force | Out-Null
        Mock Set-BridgeExactAcl {}
    }

    It "restores the complete previous payload after a partial candidate move" {
        Set-TestActivePayload -Root $ServiceRoot
        $staged = New-TestStagedPayload -Root $ServiceRoot
        Mock Set-BridgeExactAcl {}
        $transaction = New-BridgePayloadTransaction `
            -StagedPayload $staged `
            -ServiceRootExisted $true `
            -ServiceExisted $true `
            -ServiceWasRunning $true
        Remove-Item -LiteralPath $staged.Wrapper -Force

        { Switch-BridgePayload -Transaction $transaction } | Should Throw
        Restore-BridgePayload -Transaction $transaction

        Assert-TestActivePayload -Marker "old"
    }

    It "never removes an untouched active item when an earlier backup move fails" {
        Set-TestActivePayload -Root $ServiceRoot
        $staged = New-TestStagedPayload -Root $ServiceRoot
        $transaction = New-BridgePayloadTransaction `
            -StagedPayload $staged `
            -ServiceRootExisted $true `
            -ServiceExisted $true `
            -ServiceWasRunning $true
        New-Item -ItemType Directory -Path $transaction.RollbackRoot -Force | Out-Null
        Set-Content -LiteralPath $transaction.Items[1].Backup -Value "collision" -NoNewline

        { Switch-BridgePayload -Transaction $transaction } | Should Throw
        Restore-BridgePayload -Transaction $transaction

        Assert-TestActivePayload -Marker "old"
    }

    It "commits the candidate only after removing rollback artifacts and journal" {
        Set-TestActivePayload -Root $ServiceRoot
        $staged = New-TestStagedPayload -Root $ServiceRoot
        $transaction = New-BridgePayloadTransaction `
            -StagedPayload $staged `
            -ServiceRootExisted $true `
            -ServiceExisted $true `
            -ServiceWasRunning $true

        Switch-BridgePayload -Transaction $transaction
        Complete-BridgePayloadTransaction -Transaction $transaction

        Assert-TestActivePayload -Marker "new"
        (Test-Path -LiteralPath $transaction.RollbackRoot) | Should Be $false
        (Test-Path -LiteralPath $TransactionJournalPath) | Should Be $false
    }

    It "keeps the journal when a required previous backup is missing" {
        Set-TestActivePayload -Root $ServiceRoot
        $staged = New-TestStagedPayload -Root $ServiceRoot
        $transaction = New-BridgePayloadTransaction `
            -StagedPayload $staged `
            -ServiceRootExisted $true `
            -ServiceExisted $true `
            -ServiceWasRunning $true
        Switch-BridgePayload -Transaction $transaction
        Remove-Item -LiteralPath $transaction.Items[1].Backup -Force

        { Restore-BridgePayload -Transaction $transaction } | Should Throw

        (Test-Path -LiteralPath $TransactionJournalPath) | Should Be $true
    }

    It "preserves an already restored original when staged and original fingerprints are identical" {
        $activePath = Join-Path $ServiceRoot "identical.exe"
        $backupPath = Join-Path $ServiceRoot "missing-backup.exe"
        Set-Content -LiteralPath $activePath -Value "same-wrapper" -NoNewline
        $fingerprint = (Get-FileHash -LiteralPath $activePath -Algorithm SHA256).Hash
        $item = [pscustomobject]@{
            Active              = $activePath
            Backup              = $backupPath
            Staged              = (Join-Path $ServiceRoot "missing-staged.exe")
            OriginalExisted     = $true
            OriginalFingerprint = $fingerprint
            StagedFingerprint   = $fingerprint
            OriginalMoveIntent  = $false
            OriginalMoved       = $false
            StagedMoveIntent    = $false
            StagedMoved         = $false
        }
        $transaction = [pscustomobject]@{
            Phase = "activated"
            Items = @($item)
        }
        Mock Write-BridgeTransactionJournal {}

        Restore-BridgePayload -Transaction $transaction

        (Get-Content -LiteralPath $activePath -Raw) | Should Be "same-wrapper"
        (Test-Path -LiteralPath $backupPath) | Should Be $false
    }

    It "reconstructs only a missing pinned WinSW wrapper during rollback recovery" {
        $item = [pscustomobject]@{
            Active              = $ServiceWrapperPath
            Backup              = (Join-Path $ServiceRoot ".rollback-test\$ServiceName.exe")
            Staged              = (Join-Path $ServiceRoot ".staging-test\$ServiceName.exe")
            OriginalExisted     = $true
            OriginalFingerprint = $WinSwSha256
            StagedFingerprint   = $WinSwSha256
        }
        Mock Invoke-WebRequest {
            param($UseBasicParsing, $Uri, $OutFile)
            Set-Content -LiteralPath $OutFile -Value "downloaded-pinned-wrapper" -NoNewline
        }
        Mock Get-FileHash { [pscustomobject]@{ Hash = $WinSwSha256 } }

        $restored = Restore-BridgePinnedWrapperForRecovery -Item $item

        $restored | Should Be $true
        (Test-Path -LiteralPath $ServiceWrapperPath) | Should Be $true
        Assert-MockCalled Invoke-WebRequest -Times 1 -Scope It
        Assert-MockCalled Set-BridgeExactAcl -Times 1 -Scope It
    }
}

Describe "Tiny Swarm World Windows bridge pinned-wrapper recovery validation" {
    BeforeEach {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        New-Item -ItemType Directory -Path $ServiceRoot -Force | Out-Null
        Mock Set-BridgeExactAcl {}
    }

    It "does not activate a reconstructed WinSW wrapper with a mismatched checksum" {
        $item = [pscustomobject]@{
            Active              = $ServiceWrapperPath
            Backup              = (Join-Path $ServiceRoot ".rollback-test\$ServiceName.exe")
            Staged              = (Join-Path $ServiceRoot ".staging-test\$ServiceName.exe")
            OriginalExisted     = $true
            OriginalFingerprint = $WinSwSha256
            StagedFingerprint   = $WinSwSha256
        }
        Mock Invoke-WebRequest {
            param($UseBasicParsing, $Uri, $OutFile)
            Set-Content -LiteralPath $OutFile -Value "unexpected-wrapper" -NoNewline
        }

        { Restore-BridgePinnedWrapperForRecovery -Item $item } | Should Throw

        (Test-Path -LiteralPath $ServiceWrapperPath) | Should Be $false
        Assert-MockCalled Set-BridgeExactAcl -Times 0 -Scope It
    }
}

Describe "Tiny Swarm World Windows bridge fail-closed service transitions" {
    BeforeEach {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        $script:ServiceRunnerPath = Join-Path $TestDrive "runner.ps1"
        Set-Content -LiteralPath $ServiceRunnerPath -Value "# runner"
        $script:BridgeScriptSourcePath = Join-Path $TestDrive "bridge.ps1"
        Set-Content -LiteralPath $BridgeScriptSourcePath -Value "# bridge"
        Mock Assert-Administrator {}
        Mock Get-DiscoveryIntervalMinutes { 1 }
        Mock Get-CurrentBridgeServiceAccount { "TEST\operator" }
    }

    It "fails closed when ACL hardening reports an error" {
        Mock Invoke-BridgeHandleAclHardening { throw "ACL failure" }

        { Protect-BridgeServiceRoot } | Should Throw
    }

    It "rejects a reparse swap after handle-bound ACL hardening" {
        $script:aclGetItemCalls = 0
        Mock Get-Item {
            $script:aclGetItemCalls += 1
            if ($script:aclGetItemCalls -eq 1) {
                return [pscustomobject]@{
                    Attributes = [IO.FileAttributes]::Directory
                    PSIsContainer = $true
                }
            }
            return [pscustomobject]@{
                Attributes = (
                    [IO.FileAttributes]::Directory -bor
                    [IO.FileAttributes]::ReparsePoint
                )
                PSIsContainer = $true
            }
        }
        Mock Invoke-BridgeHandleAclHardening {}

        { Set-BridgeExactAcl -Path (Join-Path $TestDrive "candidate") } | Should Throw

        Assert-MockCalled Invoke-BridgeHandleAclHardening -Times 1 -Scope It
    }

    It "treats FILE_DELETE_CHILD as a mutating ACL right" {
        $mutationRights = Get-BridgeMutationRights

        (($mutationRights -band [Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles) -ne 0) |
            Should Be $true
    }

    It "accepts only the exact three-entry protected directory ACL" {
        Initialize-BridgeAclGuardType
        $currentSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
        $exact = "O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FRFX;;;$currentSid)"
        $extraAllow = $exact + "(A;OICI;FRFX;;;BU)"
        $extraDeny = $exact + "(D;OICI;FR;;;BU)"

        [TinySwarmWorld.BridgeAclGuard]::IsSddlExact($exact, $currentSid, $true) |
            Should Be $true
        [TinySwarmWorld.BridgeAclGuard]::IsSddlExact($extraAllow, $currentSid, $true) |
            Should Be $false
        [TinySwarmWorld.BridgeAclGuard]::IsSddlExact($extraDeny, $currentSid, $true) |
            Should Be $false
    }

    It "rejects a noncanonical root without the explicit Pester test boundary" {
        $script:BridgeServicePathTestRoot = ""

        { Assert-BridgeServicePathSafety } | Should Throw
    }

    It "does not mutate or ask for credentials when ownership is a collision" {
        Mock Get-BridgeServiceOwnership {
            [pscustomobject]@{ Status = "collision"; Service = $null }
        }
        Mock Request-BridgeServiceCredential { throw "must not run" }
        Mock Protect-BridgeServiceRoot {}

        { Install-BridgeService -ResolvedConfigPath $BridgeScriptSourcePath -ResolvedPortRegistryPath $BridgeScriptSourcePath -Config ([pscustomobject]@{}) } | Should Throw

        Assert-MockCalled Protect-BridgeServiceRoot -Times 0 -Scope It
        Assert-MockCalled Request-BridgeServiceCredential -Times 0 -Scope It
    }

    It "does not mutate when the credential dialog is cancelled" {
        Mock Get-BridgeServiceOwnership {
            [pscustomobject]@{ Status = "absent"; Service = $null }
        }
        Mock Request-BridgeServiceCredential { throw "cancelled" }
        Mock Protect-BridgeServiceRoot {}

        { Install-BridgeService -ResolvedConfigPath $BridgeScriptSourcePath -ResolvedPortRegistryPath $BridgeScriptSourcePath -Config ([pscustomobject]@{}) } | Should Throw

        Assert-MockCalled Protect-BridgeServiceRoot -Times 0 -Scope It
    }

    It "revalidates full ownership after a bounded ACL migration" {
        $runningService = [pscustomobject]@{ Status = "Running" }
        $script:ownershipCalls = 0
        Mock Get-BridgeServiceOwnership {
            $script:ownershipCalls += 1
            if ($script:ownershipCalls -eq 1) {
                return [pscustomobject]@{
                    Status = "owned"
                    Service = $runningService
                    RequiresAdoption = $false
                    RequiresAclMigration = $true
                }
            }
            return [pscustomobject]@{
                Status = "collision"
                Service = $runningService
                RequiresAdoption = $false
            }
        }
        Mock Enter-BridgeMutex { $null }
        Mock Exit-BridgeMutex {}
        Mock Protect-BridgeServiceRoot {}
        Mock Request-BridgeServiceCredential { throw "must not prompt" }

        { Install-BridgeService -ResolvedConfigPath $BridgeScriptSourcePath -ResolvedPortRegistryPath $BridgeScriptSourcePath -Config ([pscustomobject]@{}) } | Should Throw

        Assert-MockCalled Protect-BridgeServiceRoot -Times 1 -Scope It
        Assert-MockCalled Request-BridgeServiceCredential -Times 0 -Scope It
    }

    It "fails closed on a bounded mutex timeout" {
        $mutex = New-Object psobject
        $mutex | Add-Member -MemberType ScriptMethod -Name WaitOne -Value { param($timeout) return $false }

        { Wait-BridgeMutex -Mutex $mutex -Name "test" -Timeout ([TimeSpan]::Zero) } | Should Throw
    }

    It "rejects runtime state when the ProgramData ACL is unsafe" {
        Mock Assert-BridgeServicePathSafety {}
        Mock Test-BridgeServiceAclHardened { $false }

        { Assert-BridgeRuntimeStateAuthority } | Should Throw
    }

    It "revokes only a right that the installation demonstrably granted" {
        Mock Test-OtherServiceUsesBridgeAccount { $false }
        Mock Test-BridgeServiceLogOnRight { $true }
        Mock Get-BridgeAccountSidValue { "S-1-5-21-test" }
        Mock Revoke-BridgeServiceLogOnRight {}
        $manifest = [pscustomobject]@{
            accountSid = "S-1-5-21-test"
            logOnRightPreexisting = $false
            logOnRightGrantedByTsw = $true
        }

        Undo-BridgeOwnedLogOnRight -Manifest $manifest -AccountName "TEST\operator"

        Assert-MockCalled Revoke-BridgeServiceLogOnRight -Times 1 -Scope It
    }

    It "preserves a preexisting service logon right" {
        Mock Revoke-BridgeServiceLogOnRight {}
        $manifest = [pscustomobject]@{
            accountSid = "S-1-5-21-test"
            logOnRightPreexisting = $true
            logOnRightGrantedByTsw = $false
        }

        Undo-BridgeOwnedLogOnRight -Manifest $manifest -AccountName "TEST\operator"

        Assert-MockCalled Revoke-BridgeServiceLogOnRight -Times 0 -Scope It
    }
}

Describe "Tiny Swarm World Windows bridge exact ownership metadata" {
    It "allows only explicit install-time ACL migration for an exact SCM registration" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        $service = [pscustomobject]@{ Status = "Running" }
        Mock Get-BridgeService { $service }
        Mock Assert-BridgeServicePathSafety {}
        Mock Get-BridgeServiceDetails {
            [pscustomobject]@{
                PathName = $ServiceWrapperPath
                StartName = "TEST\operator"
                StartMode = "Auto"
            }
        }
        Mock Test-BridgeServicePathMatches { $true }
        Mock Test-BridgeServiceAccountMatchesCurrentIdentity { $true }
        Mock Get-BridgeAccountSidValue { "S-1-5-21-test" }
        Mock Test-BridgeServiceAclHardened { $false }
        Mock Get-FileHash { throw "unsafe payload must not be read" }

        $migrationOwnership = Get-BridgeServiceOwnership -AllowAclMigration
        $defaultOwnership = Get-BridgeServiceOwnership

        $migrationOwnership.Status | Should Be "owned"
        $migrationOwnership.RequiresAclMigration | Should Be $true
        $defaultOwnership.Status | Should Be "collision"
        $defaultOwnership.Reason | Should Be "service_acl_not_owned"
        Assert-MockCalled Get-FileHash -Times 0 -Scope It
    }

    It "accepts the exact generated WinSW definition" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        New-Item -ItemType Directory -Path $ServiceRoot -Force | Out-Null
        Set-Content -LiteralPath $ServiceDefinitionPath -Value (New-BridgeServiceDefinition -IntervalMinutes 1)

        (Test-BridgeServiceDefinitionOwned) | Should Be $true
    }

    It "rejects unknown WinSW top-level nodes" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        New-Item -ItemType Directory -Path $ServiceRoot -Force | Out-Null
        $xml = (New-BridgeServiceDefinition -IntervalMinutes 1).Replace(
            "</service>",
            "  <env name=`"FOREIGN`" value=`"1`"/>`r`n</service>"
        )
        Set-Content -LiteralPath $ServiceDefinitionPath -Value $xml

        (Test-BridgeServiceDefinitionOwned) | Should Be $false
    }

    It "rejects a WinSW log path outside the protected service root" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        New-Item -ItemType Directory -Path $ServiceRoot -Force | Out-Null
        $xml = (New-BridgeServiceDefinition -IntervalMinutes 1).Replace(
            "%BASE%\logs",
            "C:\foreign-logs"
        )
        Set-Content -LiteralPath $ServiceDefinitionPath -Value $xml

        (Test-BridgeServiceDefinitionOwned) | Should Be $false
    }

    It "does not accept expected paths that appear only in XML comments" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        New-Item -ItemType Directory -Path $ServiceRoot -Force | Out-Null
        $xml = @"
<service>
  <id>$ServiceName</id>
  <name>$ServiceDisplayName</name>
  <!-- $InstalledBridgeScriptPath $InstalledServiceRunnerPath $InstalledConfigPath $InstalledPortRegistryPath -->
  <executable>foreign.exe</executable>
  <arguments>--foreign</arguments>
  <workingdirectory>C:\foreign</workingdirectory>
</service>
"@
        Set-Content -LiteralPath $ServiceDefinitionPath -Value $xml

        (Test-BridgeServiceDefinitionOwned) | Should Be $false
    }

    It "rejects an unsafe empty service root before fresh installation" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        New-Item -ItemType Directory -Path $ServiceRoot -Force | Out-Null
        Mock Get-BridgeService { $null }
        Mock Assert-BridgeServicePathSafety { throw "reparse point" }

        $ownership = Get-BridgeServiceOwnership

        $ownership.Status | Should Be "collision"
        $ownership.Reason | Should Be "unsafe_service_root_without_registration"
    }

    It "classifies an invalid existing installation manifest as collision" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        New-Item -ItemType Directory -Path $ServiceRoot -Force | Out-Null
        Set-Content -LiteralPath $InstallationManifestPath -Value "{invalid"
        Set-Content -LiteralPath $ServiceWrapperPath -Value "wrapper"
        $service = [pscustomobject]@{ Status = "Running" }
        Mock Get-BridgeService { $service }
        Mock Assert-BridgeServicePathSafety {}
        Mock Get-BridgeServiceDetails {
            [pscustomobject]@{ PathName = $ServiceWrapperPath; StartName = "TEST\operator"; StartMode = "Auto" }
        }
        Mock Test-BridgeServicePathMatches { $true }
        Mock Test-BridgeServiceAccountMatchesCurrentIdentity { $true }
        Mock Get-BridgeAccountSidValue { "S-1-5-21-test" }
        Mock Test-BridgeServiceAclHardened { $true }
        Mock Get-FileHash { [pscustomobject]@{ Hash = $WinSwSha256 } }

        $ownership = Get-BridgeServiceOwnership

        $ownership.Status | Should Be "collision"
        $ownership.Reason | Should Be "installation_manifest_invalid"
    }
}

Describe "Tiny Swarm World Windows bridge verified firewall cleanup" {
    It "retains cleanup authority when an exact firewall rule remains" {
        $ruleName = "Tiny Swarm World TCP 443"
        $plan = [pscustomobject]@{
            Mappings = @()
            FirewallRuleNames = @($ruleName)
        }
        Mock Get-PortProxyRecords { @() }
        Mock Get-NetFirewallRule {
            [pscustomobject]@{ DisplayName = $ruleName }
        }
        Mock Remove-NetFirewallRule {}

        { Invoke-BridgeCleanupPlan -Plan $plan } | Should Throw
    }

    It "propagates technical firewall query failures" {
        Mock Get-NetFirewallRule { throw [InvalidOperationException]::new("CIM unavailable") }

        { Get-ExactBridgeFirewallRules -RuleName "Tiny Swarm World TCP 443" } | Should Throw
    }
}

Describe "Tiny Swarm World Windows bridge journal reload recovery" {
    It "recovers a partially switched payload from the protected journal" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        New-Item -ItemType Directory -Path $ServiceRoot -Force | Out-Null
        Set-TestActivePayload -Root $ServiceRoot
        $staged = New-TestStagedPayload -Root $ServiceRoot
        Mock Set-BridgeExactAcl {}
        $transaction = New-BridgePayloadTransaction `
            -StagedPayload $staged `
            -ServiceRootExisted $true `
            -ServiceExisted $true `
            -ServiceWasRunning $false
        Remove-Item -LiteralPath $staged.Wrapper -Force
        { Switch-BridgePayload -Transaction $transaction } | Should Throw
        $stoppedService = [pscustomobject]@{ Status = "Stopped" }
        Mock Assert-BridgeServicePathSafety {}
        Mock Assert-BridgePayloadPathSafety {}
        Mock Test-BridgeServiceAclHardened { $true }
        Mock Get-BridgeService { $stoppedService }
        Mock Get-BridgeServiceDetails {
            [pscustomobject]@{
                PathName = $ServiceWrapperPath
                StartName = "TEST\operator"
                StartMode = "Auto"
            }
        }
        Mock Test-BridgeServiceAccountMatchesCurrentIdentity { $true }
        Mock Enter-BridgeMutex { $null }
        Mock Exit-BridgeMutex {}
        Mock Protect-BridgeServiceRoot {}

        Recover-BridgeInterruptedTransaction

        Assert-TestActivePayload -Marker "old"
        (Test-Path -LiteralPath $TransactionJournalPath) | Should Be $false
    }
}

Describe "Tiny Swarm World Windows bridge checksum preactivation" {
    It "never stops or switches the service after a staged WinSW checksum mismatch" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        $script:ServiceRunnerPath = Join-Path $TestDrive "runner.ps1"
        $sourcePath = Join-Path $TestDrive "source.txt"
        Set-Content -LiteralPath $ServiceRunnerPath -Value "# runner"
        Set-Content -LiteralPath $sourcePath -Value "source"
        $script:BridgeScriptSourcePath = $sourcePath
        $runningService = [pscustomobject]@{ Status = "Running" }
        Mock Assert-Administrator {}
        Mock Get-DiscoveryIntervalMinutes { 1 }
        Mock Get-CurrentBridgeServiceAccount { "TEST\operator" }
        Mock Get-BridgeServiceOwnership {
            [pscustomobject]@{ Status = "owned"; Service = $runningService }
        }
        Mock Get-BridgeAccountSidValue { "S-1-5-21-test" }
        Mock Test-BridgeServiceLogOnRight { $true }
        Mock Protect-BridgeServiceRoot {}
        Mock Set-BridgeExactAcl {}
        Mock Invoke-WebRequest {
            param($UseBasicParsing, $Uri, $OutFile)
            [IO.File]::WriteAllBytes($OutFile, [byte[]](1, 2, 3, 4))
        }
        Mock Stop-BridgeServiceChecked {}
        Mock Switch-BridgePayload {}

        { Install-BridgeService -ResolvedConfigPath $sourcePath -ResolvedPortRegistryPath $sourcePath -Config ([pscustomobject]@{}) } | Should Throw

        Assert-MockCalled Stop-BridgeServiceChecked -Times 0 -Scope It
        Assert-MockCalled Switch-BridgePayload -Times 0 -Scope It
        @(Get-ChildItem -LiteralPath $ServiceRoot -Directory -Filter ".staging-*" -ErrorAction SilentlyContinue).Count | Should Be 0
    }
}

Describe "Tiny Swarm World Windows bridge LSA provenance upgrade" {
    It "preserves the previous Tiny Swarm grant provenance" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        $script:ServiceRunnerPath = Join-Path $TestDrive "runner.ps1"
        $sourcePath = Join-Path $TestDrive "source.txt"
        Set-Content -LiteralPath $ServiceRunnerPath -Value "# runner"
        Set-Content -LiteralPath $sourcePath -Value "source"
        $runningService = [pscustomobject]@{ Status = "Running" }
        $script:observedPreexisting = $null
        $script:observedGranted = $null
        Mock Assert-Administrator {}
        Mock Get-DiscoveryIntervalMinutes { 1 }
        Mock Get-CurrentBridgeServiceAccount { "TEST\operator" }
        Mock Get-BridgeServiceOwnership {
            [pscustomobject]@{
                Status = "owned"
                Service = $runningService
                RequiresAdoption = $false
            }
        }
        Mock Get-BridgeAccountSidValue { "S-1-5-21-test" }
        Mock Test-BridgeServiceLogOnRight { $true }
        Mock Get-BridgeInstallationManifest {
            [pscustomobject]@{
                accountSid = "S-1-5-21-test"
                serviceAccount = "TEST\operator"
                logOnRightPreexisting = $false
                logOnRightGrantedByTsw = $true
            }
        }
        Mock Protect-BridgeServiceRoot {}
        Mock New-BridgeStagedPayload {
            param(
                $ResolvedConfigPath,
                $ResolvedPortRegistryPath,
                $ServiceDefinition,
                $AccountSid,
                $AccountName,
                $LogOnRightPreexisting,
                $LogOnRightGrantedByTsw
            )
            $script:observedPreexisting = $LogOnRightPreexisting
            $script:observedGranted = $LogOnRightGrantedByTsw
            throw "stop after provenance capture"
        }

        { Install-BridgeService -ResolvedConfigPath $sourcePath -ResolvedPortRegistryPath $sourcePath -Config ([pscustomobject]@{}) } | Should Throw

        $script:observedPreexisting | Should Be $false
        $script:observedGranted | Should Be $true
    }


    It "records a newly restored orphan logon right as Tiny Swarm owned" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        $script:ServiceRunnerPath = Join-Path $TestDrive "runner.ps1"
        $sourcePath = Join-Path $TestDrive "source.txt"
        Set-Content -LiteralPath $ServiceRunnerPath -Value "# runner"
        Set-Content -LiteralPath $sourcePath -Value "source"
        $script:observedPreexisting = $null
        $script:observedGranted = $null
        Mock Assert-Administrator {}
        Mock Get-DiscoveryIntervalMinutes { 1 }
        Mock Get-CurrentBridgeServiceAccount { "TEST\operator" }
        Mock Get-BridgeServiceOwnership {
            [pscustomobject]@{
                Status = "owned"
                Service = $null
                RequiresAdoption = $false
                AccountSid = "S-1-5-21-test"
            }
        }
        Mock Request-BridgeServiceCredential { $null }
        Mock Get-BridgeAccountSidValue { "S-1-5-21-test" }
        Mock Test-BridgeServiceLogOnRight { $false }
        Mock Get-BridgeInstallationManifest {
            [pscustomobject]@{
                accountSid = "S-1-5-21-test"
                serviceAccount = "TEST\operator"
                logOnRightPreexisting = $true
                logOnRightGrantedByTsw = $false
            }
        }
        Mock Protect-BridgeServiceRoot {}
        Mock New-BridgeStagedPayload {
            param(
                $ResolvedConfigPath,
                $ResolvedPortRegistryPath,
                $ServiceDefinition,
                $AccountSid,
                $AccountName,
                $LogOnRightPreexisting,
                $LogOnRightGrantedByTsw
            )
            $script:observedPreexisting = $LogOnRightPreexisting
            $script:observedGranted = $LogOnRightGrantedByTsw
            throw "stop after provenance capture"
        }

        { Install-BridgeService -ResolvedConfigPath $sourcePath -ResolvedPortRegistryPath $sourcePath -Config ([pscustomobject]@{}) } | Should Throw

        $script:observedPreexisting | Should Be $false
        $script:observedGranted | Should Be $true
    }

    It "refuses orphan ownership from a different account SID before prompting" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        $script:ServiceRunnerPath = Join-Path $TestDrive "runner.ps1"
        $sourcePath = Join-Path $TestDrive "source.txt"
        Set-Content -LiteralPath $ServiceRunnerPath -Value "# runner"
        Set-Content -LiteralPath $sourcePath -Value "source"
        Mock Assert-Administrator {}
        Mock Get-DiscoveryIntervalMinutes { 1 }
        Mock Get-CurrentBridgeServiceAccount { "TEST\operator" }
        Mock Get-BridgeServiceOwnership {
            [pscustomobject]@{
                Status = "owned"
                Service = $null
                RequiresAdoption = $false
                AccountSid = "S-1-5-21-foreign"
            }
        }
        Mock Get-BridgeAccountSidValue { "S-1-5-21-test" }
        Mock Request-BridgeServiceCredential { throw "must not prompt" }

        { Install-BridgeService -ResolvedConfigPath $sourcePath -ResolvedPortRegistryPath $sourcePath -Config ([pscustomobject]@{}) } | Should Throw

        Assert-MockCalled Request-BridgeServiceCredential -Times 0 -Scope It
    }
}

Describe "Tiny Swarm World Windows bridge heartbeat rollback" {
    It "restores and restarts the previous service after a candidate heartbeat timeout" {
        Set-TestBridgePaths -Root (Join-Path $TestDrive "service-root")
        $script:ServiceRunnerPath = Join-Path $TestDrive "runner.ps1"
        $sourcePath = Join-Path $TestDrive "source.txt"
        Set-Content -LiteralPath $ServiceRunnerPath -Value "# runner"
        Set-Content -LiteralPath $sourcePath -Value "source"
        $runningService = [pscustomobject]@{ Status = "Running" }
        $staged = [pscustomobject]@{
            Root = (Join-Path $ServiceRoot ".staging-test")
            BundleId = ("A" * 64)
        }
        $transaction = [pscustomobject]@{
            ContractVersion = 1
            TransactionId = ("a" * 32)
            Phase = "prepared"
            StagedPayload = $staged
            RollbackRoot = (Join-Path $ServiceRoot ".rollback-test")
            ServiceRootExisted = $true
            ServiceExisted = $true
            ServiceWasRunning = $true
            ServiceCreateIntent = $false
            ServiceCreated = $false
            PreviousBundleId = ("B" * 64)
            Items = @()
        }
        $script:heartbeatCalls = 0
        Mock Assert-Administrator {}
        Mock Get-DiscoveryIntervalMinutes { 1 }
        Mock Get-CurrentBridgeServiceAccount { "TEST\operator" }
        Mock Get-BridgeServiceOwnership {
            [pscustomobject]@{ Status = "owned"; Service = $runningService }
        }
        Mock Get-BridgeService { $runningService }
        Mock Get-BridgeAccountSidValue { "S-1-5-21-test" }
        Mock Test-BridgeServiceLogOnRight { $true }
        Mock Protect-BridgeServiceRoot {}
        Mock New-BridgeStagedPayload { $staged }
        Mock Get-InstalledBridgeBundleIdOrEmpty { "B" * 64 }
        Mock New-BridgePayloadTransaction { $transaction }
        Mock Write-BridgeTransactionJournal {}
        Mock Enter-BridgeMutex { $null }
        Mock Exit-BridgeMutex {}
        Mock Stop-BridgeServiceChecked {}
        Mock Switch-BridgePayload {}
        Mock Start-BridgeServiceChecked {}
        Mock Wait-BridgeServiceHeartbeat {
            $script:heartbeatCalls++
            if ($script:heartbeatCalls -eq 1) {
                throw "heartbeat timeout"
            }
        }
        Mock Undo-BridgeTransactionOwnedLogOnRight {}
        Mock Restore-BridgePayload {}
        Mock Start-BridgeServiceRollbackChecked {}
        Mock Complete-BridgePayloadRollback {}
        Mock Complete-BridgePayloadTransaction {}

        { Install-BridgeService -ResolvedConfigPath $sourcePath -ResolvedPortRegistryPath $sourcePath -Config ([pscustomobject]@{}) } | Should Throw

        Assert-MockCalled Restore-BridgePayload -Times 1 -Scope It
        Assert-MockCalled Start-BridgeServiceRollbackChecked -Times 1 -Scope It
        Assert-MockCalled Wait-BridgeServiceHeartbeat -Times 2 -Scope It
        Assert-MockCalled Complete-BridgePayloadRollback -Times 1 -Scope It
    }
}

Describe "Tiny Swarm World Windows bridge service runner" {
    It "returns a failure after three consecutive reconcile errors" {
        . $runnerScript `
            -BridgeScriptPath "bridge.ps1" `
            -ConfigPath "config.json" `
            -PortRegistryPath "ports.yaml"
        Mock Invoke-BridgeReconcileProcess { 1 }
        Mock Start-Sleep {}

        $result = Invoke-BridgeServiceLoop

        $result | Should Be 1
        Assert-MockCalled Invoke-BridgeReconcileProcess -Times 3
        Assert-MockCalled Start-Sleep -Times 2
    }
}
