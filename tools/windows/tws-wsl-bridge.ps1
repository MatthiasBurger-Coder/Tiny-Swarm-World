#requires -Version 5.1
<#
.SYNOPSIS
  Tiny Swarm World Windows <-> WSL bridge.

.DESCRIPTION
  Prepares the Windows side before a Tiny Swarm World installation in WSL.
  It reconciles:
    - Windows portproxy rules -> current WSL IP
    - Windows Firewall inbound rules
    - Windows hosts-file entries for known tsw.local names
    - Automatic Windows discovery/reconcile service at a fixed interval

  Check Windows and WSL prerequisites without changing state:
    .\tools\windows\tws-wsl-bridge.ps1 -Action prerequisites

  Run from an elevated PowerShell once:
    .\tools\windows\tws-wsl-bridge.ps1 -Action install

  Trigger discovery/reconcile manually:
    Restart-Service -Name TinySwarmWorldWslBridge
#>

[CmdletBinding()]
param(
    [ValidateSet("prerequisites", "discover", "install", "reconcile", "refresh", "verify", "status", "uninstall")]
    [string]$Action = "refresh",

    [string]$ConfigPath = "",

    [string]$TaskName = "TinySwarmWorld-WslBridge",

    [string]$PortRegistryPath = "",

    [int]$ConnectTimeoutMs = 1500
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
    $ConfigPath = Join-Path $PSScriptRoot "tws-wsl-bridge.config.json"
}

$HostsPath = Join-Path $env:windir "System32\drivers\etc\hosts"
$HostsStart = "# >>> Tiny Swarm World WSL Bridge >>>"
$HostsEnd = "# <<< Tiny Swarm World WSL Bridge <<<"
$ServiceName = "TinySwarmWorldWslBridge"
$ServiceDisplayName = "Tiny Swarm World WSL Bridge"
$CanonicalProgramDataRoot = [Environment]::GetFolderPath(
    [Environment+SpecialFolder]::CommonApplicationData
)
if ([string]::IsNullOrWhiteSpace($CanonicalProgramDataRoot)) {
    throw "Windows CommonApplicationData could not be resolved."
}
$CanonicalProgramDataRoot = [IO.Path]::GetFullPath($CanonicalProgramDataRoot).TrimEnd('\')
$BridgeServicePathTestRoot = ""
$ServiceNamespaceRoot = Join-Path $CanonicalProgramDataRoot "TinySwarmWorld"
$ServiceRoot = Join-Path $ServiceNamespaceRoot "WslBridge"
$ServiceBundleRoot = Join-Path $ServiceRoot "bundle"
$ServiceLogsRoot = Join-Path $ServiceRoot "logs"
$StatePath = Join-Path $ServiceRoot "bridge-state.json"
$ServiceWrapperPath = Join-Path $ServiceRoot "$ServiceName.exe"
$ServiceDefinitionPath = Join-Path $ServiceRoot "$ServiceName.xml"
$ServiceRunnerPath = Join-Path $PSScriptRoot "tws-wsl-bridge-service.ps1"
$InstalledBridgeScriptPath = Join-Path $ServiceBundleRoot "tws-wsl-bridge.ps1"
$InstalledServiceRunnerPath = Join-Path $ServiceBundleRoot "tws-wsl-bridge-service.ps1"
$InstalledConfigPath = Join-Path $ServiceBundleRoot "tws-wsl-bridge.config.json"
$InstalledPortRegistryPath = Join-Path $ServiceBundleRoot "ports.yaml"
$InstalledBundleManifestPath = Join-Path $ServiceBundleRoot "bundle-manifest.json"
$InstallationManifestPath = Join-Path $ServiceRoot "installation-manifest.json"
$TransactionJournalPath = Join-Path $ServiceRoot "upgrade-transaction.json"
$BridgeScriptSourcePath = $PSCommandPath
$WinSwDownloadUri = "https://github.com/winsw/winsw/releases/download/v2.12.0/WinSW.NET461.exe"
$WinSwSha256 = "B5066B7BBDFBA1293E5D15CDA3CAAEA88FBEAB35BD5B38C41C913D492AADFC4F"

function Get-TswRepositoryRoot {
    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
}

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Assert-Administrator {
    if (-not (Test-IsAdministrator)) {
        throw "This action needs an elevated PowerShell. Start PowerShell as Administrator and run the command again."
    }
}

function Get-CurrentBridgeServiceAccount {
    return [Security.Principal.WindowsIdentity]::GetCurrent().Name
}

function Get-BridgeAccountSidValue {
    param([string]$AccountName)

    $normalizedAccount = $AccountName
    if ($normalizedAccount.StartsWith(".\")) {
        $normalizedAccount = "$env:COMPUTERNAME\$($normalizedAccount.Substring(2))"
    }
    $account = New-Object Security.Principal.NTAccount($normalizedAccount)
    return $account.Translate([Security.Principal.SecurityIdentifier]).Value
}

function Test-BridgeServiceAccountMatchesCurrentIdentity {
    param([string]$AccountName)

    if ([string]::IsNullOrWhiteSpace($AccountName)) {
        return $false
    }

    try {
        $accountSid = Get-BridgeAccountSidValue -AccountName $AccountName
        $currentSid = [Security.Principal.WindowsIdentity]::GetCurrent().User
        return $null -ne $currentSid -and $accountSid -eq $currentSid.Value
    } catch {
        return $false
    }
}

function Test-BridgeServicePathMatches {
    param([string]$PathName)

    if ([string]::IsNullOrWhiteSpace($PathName)) {
        return $false
    }
    $normalizedPath = $PathName.Trim().Trim([char]34)
    return [StringComparer]::OrdinalIgnoreCase.Equals($normalizedPath, $ServiceWrapperPath)
}

function Test-PathInsideBridgeServiceRoot {
    param([string]$Path)

    $root = [IO.Path]::GetFullPath($ServiceRoot).TrimEnd('\') + '\'
    $candidate = [IO.Path]::GetFullPath($Path)
    return $candidate.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)
}

function Assert-BridgeServicePathSafety {
    $programDataRoot = [IO.Path]::GetFullPath(
        [Environment]::GetFolderPath([Environment+SpecialFolder]::CommonApplicationData)
    ).TrimEnd('\')
    if (-not [StringComparer]::OrdinalIgnoreCase.Equals($programDataRoot, $CanonicalProgramDataRoot)) {
        throw "The canonical Windows ProgramData path changed during bridge execution."
    }
    $serviceRootPath = [IO.Path]::GetFullPath($ServiceRoot)
    $boundaryRoot = $programDataRoot
    $insideCanonicalRoot = $serviceRootPath.StartsWith(
        $programDataRoot + '\',
        [StringComparison]::OrdinalIgnoreCase
    )
    if (-not $insideCanonicalRoot) {
        $pesterLoaded = $null -ne (Get-Module -Name Pester -ErrorAction SilentlyContinue)
        if (-not $pesterLoaded -or [string]::IsNullOrWhiteSpace($BridgeServicePathTestRoot)) {
            throw "The Windows bridge service root must remain below canonical ProgramData."
        }
        $testRoot = [IO.Path]::GetFullPath($BridgeServicePathTestRoot).TrimEnd('\')
        $insideTestRoot = (
            [StringComparer]::OrdinalIgnoreCase.Equals($serviceRootPath, $testRoot) -or
            $serviceRootPath.StartsWith($testRoot + '\', [StringComparison]::OrdinalIgnoreCase)
        )
        if (-not $insideTestRoot) {
            throw "The Windows bridge service root escaped the active Pester test root."
        }
        $boundaryRoot = $testRoot
    }

    $paths = [System.Collections.ArrayList]::new()
    [void]$paths.Add($boundaryRoot)
    $candidate = $serviceRootPath
    while (
        [StringComparer]::OrdinalIgnoreCase.Equals($candidate, $boundaryRoot) -or
        $candidate.StartsWith($boundaryRoot + '\', [StringComparison]::OrdinalIgnoreCase)
    ) {
        [void]$paths.Add($candidate)
        if ([StringComparer]::OrdinalIgnoreCase.Equals($candidate, $boundaryRoot)) {
            break
        }
        $candidate = Split-Path -Parent $candidate
    }
    [void]$paths.Add([IO.Path]::GetFullPath($ServiceBundleRoot))
    foreach ($path in $paths) {
        if (-not (Test-Path -LiteralPath $path)) {
            continue
        }
        $item = Get-Item -LiteralPath $path -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse points are not allowed in the Windows bridge service path: $path"
        }
    }
}

function Get-BridgeMutationRights {
    return (
        [Security.AccessControl.FileSystemRights]::WriteData -bor
        [Security.AccessControl.FileSystemRights]::AppendData -bor
        [Security.AccessControl.FileSystemRights]::WriteExtendedAttributes -bor
        [Security.AccessControl.FileSystemRights]::WriteAttributes -bor
        [Security.AccessControl.FileSystemRights]::Delete -bor
        [Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles -bor
        [Security.AccessControl.FileSystemRights]::ChangePermissions -bor
        [Security.AccessControl.FileSystemRights]::TakeOwnership
    )
}

function Assert-BridgePayloadPathSafety {
    param([string]$Path)

    if (-not (Test-PathInsideBridgeServiceRoot -Path $Path)) {
        throw "Bridge payload path escaped the protected service root: $Path"
    }
    $root = [IO.Path]::GetFullPath($ServiceRoot).TrimEnd('\')
    $candidate = [IO.Path]::GetFullPath($Path)
    while ($candidate.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
        if (Test-Path -LiteralPath $candidate) {
            $item = Get-Item -LiteralPath $candidate -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Reparse points are not allowed in bridge payload paths: $candidate"
            }
        }
        if ([StringComparer]::OrdinalIgnoreCase.Equals($candidate, $root)) {
            break
        }
        $candidate = Split-Path -Parent $candidate
    }
}

function Test-BridgePathAclHardened {
    param(
        [string]$Path,
        [bool]$RequireProtected = $false
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }
    try {
        $item = Get-Item -LiteralPath $Path -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            return $false
        }
        $currentSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
        return Test-BridgeHandleAclExact `
            -Path $Path `
            -CurrentSid $currentSid `
            -ExpectedDirectory ([bool]$item.PSIsContainer)
    } catch {
        return $false
    }
}

function Test-BridgeServiceAclHardened {
    if (
        -not (Test-Path -LiteralPath $ServiceNamespaceRoot -PathType Container) -or
        -not (Test-Path -LiteralPath $ServiceRoot -PathType Container)
    ) {
        return $false
    }
    if (
        -not (Test-BridgePathAclHardened -Path $ServiceNamespaceRoot -RequireProtected $true) -or
        -not (Test-BridgePathAclHardened -Path $ServiceRoot -RequireProtected $true)
    ) {
        return $false
    }
    try {
        $authorityFileNames = [System.Collections.Generic.HashSet[string]]::new(
            [StringComparer]::OrdinalIgnoreCase
        )
        foreach ($name in @(
            "$ServiceName.exe",
            "$ServiceName.xml",
            "bridge-state.json",
            "installation-manifest.json",
            "upgrade-transaction.json"
        )) {
            [void]$authorityFileNames.Add($name)
        }
        foreach ($item in @(
            Get-ChildItem -LiteralPath $ServiceRoot -Force -ErrorAction Stop |
                Sort-Object Name
        )) {
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                return $false
            }
            $isTransactionalDirectory = (
                $item.PSIsContainer -and
                ($item.Name -like ".staging-*" -or $item.Name -like ".rollback-*")
            )
            if ($item.Name -eq "bundle" -or $isTransactionalDirectory) {
                if (-not $item.PSIsContainer) {
                    return $false
                }
                foreach ($authorityItem in @(Get-BridgeTreeItemsNoFollow -Root $item.FullName)) {
                    if (-not (Test-BridgePathAclHardened -Path $authorityItem.FullName -RequireProtected $true)) {
                        return $false
                    }
                }
                continue
            }
            if ($item.Name -eq "logs") {
                if (
                    -not $item.PSIsContainer -or
                    -not (Test-BridgePathAclHardened -Path $item.FullName -RequireProtected $true)
                ) {
                    return $false
                }
                foreach ($logItem in @(Get-ChildItem -LiteralPath $item.FullName -Force -ErrorAction Stop)) {
                    if (
                        $logItem.PSIsContainer -or
                        -not (Test-BridgeHandleObjectSafe -Path $logItem.FullName -ExpectedDirectory $false)
                    ) {
                        return $false
                    }
                }
                continue
            }
            if (
                $item.PSIsContainer -or
                -not $authorityFileNames.Contains($item.Name) -or
                -not (Test-BridgePathAclHardened -Path $item.FullName -RequireProtected $true)
            ) {
                return $false
            }
        }
    } catch {
        return $false
    }
    return $true
}

function Get-BridgeTreeItemsNoFollow {
    param([string]$Root)

    $pending = [Collections.Generic.Queue[string]]::new()
    $pending.Enqueue([IO.Path]::GetFullPath($Root))
    while ($pending.Count -gt 0) {
        $path = $pending.Dequeue()
        $item = Get-Item -LiteralPath $path -Force -ErrorAction Stop
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse points are not allowed in the Windows bridge service tree: $path"
        }
        Write-Output $item
        if (-not $item.PSIsContainer) {
            continue
        }
        foreach ($child in @(
            Get-ChildItem -LiteralPath $path -Force -ErrorAction Stop |
                Sort-Object FullName
        )) {
            if (($child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Reparse points are not allowed in the Windows bridge service tree: $($child.FullName)"
            }
            $pending.Enqueue($child.FullName)
        }
    }
}

function Write-BytesAtomically {
    param(
        [string]$Path,
        [byte[]]$Bytes
    )

    $parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $temporaryPath = Join-Path $parent ".$([IO.Path]::GetFileName($Path)).$([guid]::NewGuid().ToString('N')).new"
    $backupPath = Join-Path $parent ".$([IO.Path]::GetFileName($Path)).$([guid]::NewGuid().ToString('N')).bak"
    $failedCandidatePath = Join-Path $parent ".$([IO.Path]::GetFileName($Path)).$([guid]::NewGuid().ToString('N')).failed"
    $replacedExisting = $false
    try {
        [IO.File]::WriteAllBytes($temporaryPath, $Bytes)
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            [IO.File]::Replace($temporaryPath, $Path, $backupPath, $true)
            $replacedExisting = $true
        } else {
            [IO.File]::Move($temporaryPath, $Path)
        }
        try {
            if (Test-PathInsideBridgeServiceRoot -Path $Path) {
                Set-BridgeExactAcl -Path $Path
            }
        } catch {
            if ($replacedExisting -and (Test-Path -LiteralPath $backupPath -PathType Leaf)) {
                [IO.File]::Replace($backupPath, $Path, $failedCandidatePath, $true)
            } else {
                Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
            }
            throw
        }
        Remove-Item -LiteralPath $backupPath -Force -ErrorAction SilentlyContinue
    } finally {
        Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $backupPath -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $failedCandidatePath -Force -ErrorAction SilentlyContinue
    }
}

function Write-TextAtomically {
    param(
        [string]$Path,
        [string]$Text
    )

    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($Text)
    Write-BytesAtomically -Path $Path -Bytes $bytes
}

function Install-BridgeBundleFile {
    param(
        [string]$Source,
        [string]$Destination
    )

    $resolvedSource = (Resolve-Path -LiteralPath $Source).Path
    Write-BytesAtomically -Path $Destination -Bytes ([IO.File]::ReadAllBytes($resolvedSource))
}

function Initialize-BridgeAclGuardType {
    if ($null -ne ("TinySwarmWorld.BridgeAclGuard" -as [type])) {
        return
    }
    Add-Type -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using Microsoft.Win32.SafeHandles;

namespace TinySwarmWorld
{
    public static class BridgeAclGuard
    {
        private const uint ReadControl = 0x00020000;
        private const uint WriteDac = 0x00040000;
        private const uint WriteOwner = 0x00080000;
        private const uint FileShareReadWrite = 0x00000003;
        private const uint OpenExisting = 3;
        private const uint FileFlagOpenReparsePoint = 0x00200000;
        private const uint FileFlagBackupSemantics = 0x02000000;
        private const uint FileAttributeDirectory = 0x00000010;
        private const uint FileAttributeReparsePoint = 0x00000400;
        private const uint OwnerSecurityInformation = 0x00000001;
        private const uint DaclSecurityInformation = 0x00000004;
        private const uint ProtectedDaclSecurityInformation = 0x80000000;
        private const uint SddlRevision1 = 1;
        private const int SeFileObject = 1;

        [StructLayout(LayoutKind.Sequential)]
        private struct ByHandleFileInformation
        {
            internal uint FileAttributes;
            internal System.Runtime.InteropServices.ComTypes.FILETIME CreationTime;
            internal System.Runtime.InteropServices.ComTypes.FILETIME LastAccessTime;
            internal System.Runtime.InteropServices.ComTypes.FILETIME LastWriteTime;
            internal uint VolumeSerialNumber;
            internal uint FileSizeHigh;
            internal uint FileSizeLow;
            internal uint NumberOfLinks;
            internal uint FileIndexHigh;
            internal uint FileIndexLow;
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern SafeFileHandle CreateFileW(
            string fileName,
            uint desiredAccess,
            uint shareMode,
            IntPtr securityAttributes,
            uint creationDisposition,
            uint flagsAndAttributes,
            IntPtr templateFile);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetFileInformationByHandle(
            SafeFileHandle file,
            out ByHandleFileInformation information);

        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool ConvertStringSecurityDescriptorToSecurityDescriptorW(
            string stringSecurityDescriptor,
            uint stringSdRevision,
            out IntPtr securityDescriptor,
            out uint securityDescriptorSize);

        [DllImport("advapi32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetSecurityDescriptorOwner(
            IntPtr securityDescriptor,
            out IntPtr owner,
            out bool ownerDefaulted);

        [DllImport("advapi32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetSecurityDescriptorDacl(
            IntPtr securityDescriptor,
            out bool daclPresent,
            out IntPtr dacl,
            out bool daclDefaulted);

        [DllImport("advapi32.dll")]
        private static extern uint SetSecurityInfo(
            SafeFileHandle handle,
            int objectType,
            uint securityInformation,
            IntPtr owner,
            IntPtr group,
            IntPtr dacl,
            IntPtr sacl);

        [DllImport("advapi32.dll")]
        private static extern uint GetSecurityInfo(
            SafeFileHandle handle,
            int objectType,
            uint securityInformation,
            out IntPtr owner,
            out IntPtr group,
            out IntPtr dacl,
            out IntPtr sacl,
            out IntPtr securityDescriptor);

        [DllImport("advapi32.dll")]
        private static extern uint GetSecurityDescriptorLength(IntPtr securityDescriptor);

        [DllImport("kernel32.dll")]
        private static extern IntPtr LocalFree(IntPtr memory);

        public static void Harden(string path, string currentSid, bool expectedDirectory)
        {
            new SecurityIdentifier(currentSid);
            ByHandleFileInformation originalInformation;
            using (SafeFileHandle handle = OpenNoFollow(
                path,
                ReadControl | WriteDac | WriteOwner))
            {
                originalInformation = ReadAndValidateInformation(
                    handle,
                    path,
                    expectedDirectory);
                ApplyExactSecurity(handle, currentSid, expectedDirectory, path);
            }

            using (SafeFileHandle verificationHandle = OpenNoFollow(path, ReadControl))
            {
                ByHandleFileInformation verificationInformation = ReadAndValidateInformation(
                    verificationHandle,
                    path,
                    expectedDirectory);
                if (
                    originalInformation.VolumeSerialNumber != verificationInformation.VolumeSerialNumber ||
                    originalInformation.FileIndexHigh != verificationInformation.FileIndexHigh ||
                    originalInformation.FileIndexLow != verificationInformation.FileIndexLow)
                {
                    throw new InvalidOperationException(
                        "The Windows bridge path changed during handle-bound ACL hardening: " + path);
                }
            }
        }

        public static bool VerifyExact(string path, string currentSid, bool expectedDirectory)
        {
            new SecurityIdentifier(currentSid);
            using (SafeFileHandle handle = OpenNoFollow(path, ReadControl))
            {
                ReadAndValidateInformation(handle, path, expectedDirectory);
                return ReadExactSecurity(handle, currentSid, expectedDirectory);
            }
        }

        public static bool VerifySafeObject(string path, bool expectedDirectory)
        {
            using (SafeFileHandle handle = OpenNoFollow(path, ReadControl))
            {
                ReadAndValidateInformation(handle, path, expectedDirectory);
                return true;
            }
        }

        public static bool IsSddlExact(string sddl, string currentSid, bool directory)
        {
            try
            {
                return IsDescriptorExact(
                    new RawSecurityDescriptor(sddl),
                    currentSid,
                    directory);
            }
            catch
            {
                return false;
            }
        }

        private static SafeFileHandle OpenNoFollow(string path, uint access)
        {
            SafeFileHandle handle = CreateFileW(
                path,
                access,
                FileShareReadWrite,
                IntPtr.Zero,
                OpenExisting,
                FileFlagOpenReparsePoint | FileFlagBackupSemantics,
                IntPtr.Zero);
            if (handle.IsInvalid)
            {
                int error = Marshal.GetLastWin32Error();
                handle.Dispose();
                throw new Win32Exception(error, "Could not open the Windows bridge path without following reparse points: " + path);
            }
            return handle;
        }

        private static ByHandleFileInformation ReadAndValidateInformation(
            SafeFileHandle handle,
            string path,
            bool expectedDirectory)
        {
            ByHandleFileInformation information;
            if (!GetFileInformationByHandle(handle, out information))
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }
            if ((information.FileAttributes & FileAttributeReparsePoint) != 0)
            {
                throw new InvalidOperationException(
                    "Reparse points are not allowed in the Windows bridge service tree: " + path);
            }
            bool isDirectory = (information.FileAttributes & FileAttributeDirectory) != 0;
            if (isDirectory != expectedDirectory)
            {
                throw new InvalidOperationException(
                    "The Windows bridge path type changed during ACL hardening: " + path);
            }
            if (!isDirectory && information.NumberOfLinks != 1)
            {
                throw new InvalidOperationException(
                    "Hard-linked files are not allowed in the Windows bridge service tree: " + path);
            }
            return information;
        }

        private static bool ReadExactSecurity(
            SafeFileHandle handle,
            string currentSid,
            bool directory)
        {
            IntPtr owner;
            IntPtr group;
            IntPtr dacl;
            IntPtr sacl;
            IntPtr descriptor;
            uint result = GetSecurityInfo(
                handle,
                SeFileObject,
                OwnerSecurityInformation | DaclSecurityInformation,
                out owner,
                out group,
                out dacl,
                out sacl,
                out descriptor);
            if (result != 0)
            {
                throw new Win32Exception((int)result);
            }
            try
            {
                uint length = GetSecurityDescriptorLength(descriptor);
                byte[] bytes = new byte[checked((int)length)];
                Marshal.Copy(descriptor, bytes, 0, checked((int)length));
                return IsDescriptorExact(
                    new RawSecurityDescriptor(bytes, 0),
                    currentSid,
                    directory);
            }
            finally
            {
                if (descriptor != IntPtr.Zero)
                {
                    LocalFree(descriptor);
                }
            }
        }

        private static bool IsDescriptorExact(
            RawSecurityDescriptor descriptor,
            string currentSid,
            bool directory)
        {
            SecurityIdentifier administrators = new SecurityIdentifier("S-1-5-32-544");
            if (
                descriptor.Owner == null ||
                !descriptor.Owner.Equals(administrators) ||
                (descriptor.ControlFlags & ControlFlags.DiscretionaryAclProtected) == 0 ||
                (descriptor.ControlFlags & ControlFlags.DiscretionaryAclPresent) == 0 ||
                descriptor.DiscretionaryAcl == null ||
                descriptor.DiscretionaryAcl.Count != 3)
            {
                return false;
            }

            InheritanceFlags inheritance = directory
                ? InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit
                : InheritanceFlags.None;
            AceFlags expectedAceFlags = directory
                ? AceFlags.ContainerInherit | AceFlags.ObjectInherit
                : AceFlags.None;
            Dictionary<string, int> expectedMasks = new Dictionary<string, int>(
                StringComparer.OrdinalIgnoreCase);
            expectedMasks.Add(
                "S-1-5-18",
                ExpectedMask("S-1-5-18", FileSystemRights.FullControl, inheritance));
            expectedMasks.Add(
                "S-1-5-32-544",
                ExpectedMask("S-1-5-32-544", FileSystemRights.FullControl, inheritance));
            expectedMasks.Add(
                currentSid,
                ExpectedMask(currentSid, FileSystemRights.ReadAndExecute, inheritance));
            HashSet<string> seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (GenericAce genericAce in descriptor.DiscretionaryAcl)
            {
                CommonAce ace = genericAce as CommonAce;
                if (
                    ace == null ||
                    ace.AceQualifier != AceQualifier.AccessAllowed ||
                    ace.AceFlags != expectedAceFlags ||
                    ace.SecurityIdentifier == null ||
                    !expectedMasks.ContainsKey(ace.SecurityIdentifier.Value) ||
                    seen.Contains(ace.SecurityIdentifier.Value) ||
                    ace.AccessMask != expectedMasks[ace.SecurityIdentifier.Value])
                {
                    return false;
                }
                seen.Add(ace.SecurityIdentifier.Value);
            }
            return seen.Count == expectedMasks.Count;
        }

        private static int ExpectedMask(
            string sid,
            FileSystemRights rights,
            InheritanceFlags inheritance)
        {
            FileSystemAccessRule rule = new FileSystemAccessRule(
                new SecurityIdentifier(sid),
                rights,
                inheritance,
                PropagationFlags.None,
                AccessControlType.Allow);
            return (int)rule.FileSystemRights;
        }

        private static void ApplyExactSecurity(
            SafeFileHandle handle,
            string currentSid,
            bool directory,
            string path)
        {
            string inheritance = directory ? "OICI" : "";
            string sddl =
                "O:BAG:BAD:P" +
                "(A;" + inheritance + ";FA;;;SY)" +
                "(A;" + inheritance + ";FA;;;BA)" +
                "(A;" + inheritance + ";FRFX;;;" + currentSid + ")";
            IntPtr descriptor = IntPtr.Zero;
            try
            {
                uint descriptorSize;
                if (!ConvertStringSecurityDescriptorToSecurityDescriptorW(
                    sddl,
                    SddlRevision1,
                    out descriptor,
                    out descriptorSize))
                {
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                }
                IntPtr owner;
                bool ownerDefaulted;
                if (!GetSecurityDescriptorOwner(descriptor, out owner, out ownerDefaulted))
                {
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                }
                bool daclPresent;
                IntPtr dacl;
                bool daclDefaulted;
                if (!GetSecurityDescriptorDacl(
                    descriptor,
                    out daclPresent,
                    out dacl,
                    out daclDefaulted) || !daclPresent)
                {
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                }
                uint result = SetSecurityInfo(
                    handle,
                    SeFileObject,
                    OwnerSecurityInformation |
                        DaclSecurityInformation |
                        ProtectedDaclSecurityInformation,
                    owner,
                    IntPtr.Zero,
                    dacl,
                    IntPtr.Zero);
                if (result != 0)
                {
                    throw new Win32Exception((int)result, "Could not atomically harden the Windows bridge ACL: " + path);
                }
            }
            finally
            {
                if (descriptor != IntPtr.Zero)
                {
                    LocalFree(descriptor);
                }
            }
        }
    }
}
"@
}

function Invoke-BridgeHandleAclHardening {
    param(
        [string]$Path,
        [string]$CurrentSid,
        [bool]$ExpectedDirectory
    )

    Initialize-BridgeAclGuardType
    [TinySwarmWorld.BridgeAclGuard]::Harden($Path, $CurrentSid, $ExpectedDirectory)
}

function Test-BridgeHandleAclExact {
    param(
        [string]$Path,
        [string]$CurrentSid,
        [bool]$ExpectedDirectory
    )

    Initialize-BridgeAclGuardType
    return [TinySwarmWorld.BridgeAclGuard]::VerifyExact(
        $Path,
        $CurrentSid,
        $ExpectedDirectory
    )
}

function Test-BridgeHandleObjectSafe {
    param(
        [string]$Path,
        [bool]$ExpectedDirectory
    )

    try {
        Initialize-BridgeAclGuardType
        return [TinySwarmWorld.BridgeAclGuard]::VerifySafeObject(
            $Path,
            $ExpectedDirectory
        )
    } catch {
        return $false
    }
}

function Set-BridgeExactAcl {
    param([string]$Path)

    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Reparse points are not allowed in the Windows bridge service tree: $Path"
    }
    $isDirectory = [bool]$item.PSIsContainer
    $currentSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    Invoke-BridgeHandleAclHardening `
        -Path $Path `
        -CurrentSid $currentSid `
        -ExpectedDirectory $isDirectory

    $protectedItem = Get-Item -LiteralPath $Path -Force
    if (
        ($protectedItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
        [bool]$protectedItem.PSIsContainer -ne $isDirectory -or
        -not (Test-BridgePathAclHardened -Path $Path -RequireProtected $true)
    ) {
        throw "The no-follow ACL operation did not leave the expected protected path: $Path"
    }
}

function Protect-BridgeServiceRoot {
    Assert-BridgeServicePathSafety
    if (-not [IO.Directory]::Exists($ServiceNamespaceRoot)) {
        [void][IO.Directory]::CreateDirectory($ServiceNamespaceRoot)
    }
    Assert-BridgeServicePathSafety
    Set-BridgeExactAcl -Path $ServiceNamespaceRoot
    Assert-BridgeServicePathSafety
    if (-not (Test-BridgePathAclHardened -Path $ServiceNamespaceRoot -RequireProtected $true)) {
        throw "The Windows bridge namespace ACL did not reach the required exact state."
    }

    if (-not [IO.Directory]::Exists($ServiceRoot)) {
        [void][IO.Directory]::CreateDirectory($ServiceRoot)
    }
    Assert-BridgeServicePathSafety
    Set-BridgeExactAcl -Path $ServiceRoot
    if (-not [IO.Directory]::Exists($ServiceBundleRoot)) {
        [void][IO.Directory]::CreateDirectory($ServiceBundleRoot)
    }
    if (-not [IO.Directory]::Exists($ServiceLogsRoot)) {
        [void][IO.Directory]::CreateDirectory($ServiceLogsRoot)
    }
    Assert-BridgeServicePathSafety

    $pendingDirectories = [Collections.Generic.Queue[string]]::new()
    $pendingDirectories.Enqueue($ServiceRoot)
    while ($pendingDirectories.Count -gt 0) {
        $directoryPath = $pendingDirectories.Dequeue()
        Set-BridgeExactAcl -Path $directoryPath
        $children = @(
            Get-ChildItem -LiteralPath $directoryPath -Force -ErrorAction Stop |
                Sort-Object FullName
        )
        foreach ($child in $children) {
            if (($child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Reparse points are not allowed in the Windows bridge service tree: $($child.FullName)"
            }
            Set-BridgeExactAcl -Path $child.FullName
            if ($child.PSIsContainer) {
                $pendingDirectories.Enqueue($child.FullName)
            }
        }
    }
    Assert-BridgeServicePathSafety
    if (-not (Test-BridgeServiceAclHardened)) {
        throw "The Windows bridge service ACL did not reach the required exact state."
    }
}

function Assert-ValidIPv4Address {
    param(
        [string]$Value,
        [string]$Name
    )

    $parts = @($Value.Split('.'))
    if ($parts.Count -ne 4) {
        throw "$Name must be an IPv4 address."
    }
    foreach ($part in $parts) {
        $octet = 0
        if ($part -notmatch '^\d{1,3}$' -or -not [int]::TryParse($part, [ref]$octet) -or $octet -gt 255) {
            throw "$Name must be an IPv4 address."
        }
    }
}

function Assert-ValidTcpPort {
    param(
        [int]$Port,
        [string]$Name
    )
    if ($Port -lt 1 -or $Port -gt 65535) {
        throw "$Name must be between 1 and 65535."
    }
}

function Assert-ValidRouteHostName {
    param([string]$HostName)

    if (
        [string]::IsNullOrWhiteSpace($HostName) -or
        $HostName.Length -gt 253 -or
        $HostName -notmatch '(?i)^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$'
    ) {
        throw "Invalid route hostname: '$HostName'."
    }
}

function Assert-ValidFirewallRulePrefix {
    param([string]$Prefix)

    if ($Prefix -notmatch '^[A-Za-z0-9][A-Za-z0-9 ._-]{0,63}$') {
        throw "firewallRulePrefix contains unsupported characters."
    }
}

function Initialize-BridgeServiceLogOnRightType {
    if ($null -eq ("TinySwarmWorld.LsaAccountRights" -as [type])) {
        Add-Type -TypeDefinition @"
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.Principal;

namespace TinySwarmWorld
{
    public static class LsaAccountRights
    {
        [StructLayout(LayoutKind.Sequential)]
        private struct LsaObjectAttributes
        {
            public int Length;
            public IntPtr RootDirectory;
            public IntPtr ObjectName;
            public uint Attributes;
            public IntPtr SecurityDescriptor;
            public IntPtr SecurityQualityOfService;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct LsaUnicodeString
        {
            public ushort Length;
            public ushort MaximumLength;
            public IntPtr Buffer;
        }

        [DllImport("advapi32.dll")]
        private static extern uint LsaOpenPolicy(
            IntPtr systemName,
            ref LsaObjectAttributes objectAttributes,
            uint desiredAccess,
            out IntPtr policyHandle);

        [DllImport("advapi32.dll")]
        private static extern uint LsaAddAccountRights(
            IntPtr policyHandle,
            IntPtr accountSid,
            LsaUnicodeString[] userRights,
            uint countOfRights);

        [DllImport("advapi32.dll")]
        private static extern uint LsaEnumerateAccountRights(
            IntPtr policyHandle,
            IntPtr accountSid,
            out IntPtr userRights,
            out uint countOfRights);

        [DllImport("advapi32.dll")]
        private static extern uint LsaRemoveAccountRights(
            IntPtr policyHandle,
            IntPtr accountSid,
            bool allRights,
            LsaUnicodeString[] userRights,
            uint countOfRights);

        [DllImport("advapi32.dll")]
        private static extern uint LsaFreeMemory(IntPtr buffer);

        [DllImport("advapi32.dll")]
        private static extern uint LsaClose(IntPtr policyHandle);

        [DllImport("advapi32.dll")]
        private static extern uint LsaNtStatusToWinError(uint status);

        public static void GrantLogOnAsService(string accountName)
        {
            const uint policyLookupNames = 0x00000800;
            const uint policyCreateAccount = 0x00000010;
            var sid = (SecurityIdentifier)new NTAccount(accountName).Translate(typeof(SecurityIdentifier));
            var sidBytes = new byte[sid.BinaryLength];
            sid.GetBinaryForm(sidBytes, 0);
            var sidPointer = Marshal.AllocHGlobal(sidBytes.Length);
            var rightPointer = Marshal.StringToHGlobalUni("SeServiceLogonRight");
            IntPtr policyHandle = IntPtr.Zero;

            try
            {
                Marshal.Copy(sidBytes, 0, sidPointer, sidBytes.Length);
                var attributes = new LsaObjectAttributes();
                attributes.Length = Marshal.SizeOf(typeof(LsaObjectAttributes));
                var status = LsaOpenPolicy(
                    IntPtr.Zero,
                    ref attributes,
                    policyLookupNames | policyCreateAccount,
                    out policyHandle);
                ThrowIfFailed(status);

                var right = new LsaUnicodeString
                {
                    Buffer = rightPointer,
                    Length = (ushort)("SeServiceLogonRight".Length * 2),
                    MaximumLength = (ushort)(("SeServiceLogonRight".Length + 1) * 2)
                };
                ThrowIfFailed(LsaAddAccountRights(policyHandle, sidPointer, new[] { right }, 1));
            }
            finally
            {
                if (policyHandle != IntPtr.Zero)
                {
                    LsaClose(policyHandle);
                }
                Marshal.FreeHGlobal(rightPointer);
                Marshal.FreeHGlobal(sidPointer);
            }
        }

        public static bool HasLogOnAsService(string accountName)
        {
            const uint policyLookupNames = 0x00000800;
            var sid = (SecurityIdentifier)new NTAccount(accountName).Translate(typeof(SecurityIdentifier));
            var sidBytes = new byte[sid.BinaryLength];
            sid.GetBinaryForm(sidBytes, 0);
            var sidPointer = Marshal.AllocHGlobal(sidBytes.Length);
            IntPtr policyHandle = IntPtr.Zero;
            IntPtr rightsPointer = IntPtr.Zero;

            try
            {
                Marshal.Copy(sidBytes, 0, sidPointer, sidBytes.Length);
                var attributes = new LsaObjectAttributes();
                attributes.Length = Marshal.SizeOf(typeof(LsaObjectAttributes));
                var status = LsaOpenPolicy(
                    IntPtr.Zero,
                    ref attributes,
                    policyLookupNames,
                    out policyHandle);
                ThrowIfFailed(status);

                uint count;
                status = LsaEnumerateAccountRights(policyHandle, sidPointer, out rightsPointer, out count);
                if (status != 0)
                {
                    var error = (int)LsaNtStatusToWinError(status);
                    if (error == 2)
                    {
                        return false;
                    }
                    throw new Win32Exception(error);
                }

                var structureSize = Marshal.SizeOf(typeof(LsaUnicodeString));
                for (var index = 0; index < count; index++)
                {
                    var itemPointer = IntPtr.Add(rightsPointer, index * structureSize);
                    var item = (LsaUnicodeString)Marshal.PtrToStructure(
                        itemPointer,
                        typeof(LsaUnicodeString));
                    var value = Marshal.PtrToStringUni(item.Buffer, item.Length / 2);
                    if (string.Equals(value, "SeServiceLogonRight", StringComparison.Ordinal))
                    {
                        return true;
                    }
                }
                return false;
            }
            finally
            {
                if (rightsPointer != IntPtr.Zero)
                {
                    LsaFreeMemory(rightsPointer);
                }
                if (policyHandle != IntPtr.Zero)
                {
                    LsaClose(policyHandle);
                }
                Marshal.FreeHGlobal(sidPointer);
            }
        }

        public static void RevokeLogOnAsService(string accountName)
        {
            const uint policyLookupNames = 0x00000800;
            var sid = (SecurityIdentifier)new NTAccount(accountName).Translate(typeof(SecurityIdentifier));
            var sidBytes = new byte[sid.BinaryLength];
            sid.GetBinaryForm(sidBytes, 0);
            var sidPointer = Marshal.AllocHGlobal(sidBytes.Length);
            var rightPointer = Marshal.StringToHGlobalUni("SeServiceLogonRight");
            IntPtr policyHandle = IntPtr.Zero;

            try
            {
                Marshal.Copy(sidBytes, 0, sidPointer, sidBytes.Length);
                var attributes = new LsaObjectAttributes();
                attributes.Length = Marshal.SizeOf(typeof(LsaObjectAttributes));
                var status = LsaOpenPolicy(
                    IntPtr.Zero,
                    ref attributes,
                    policyLookupNames,
                    out policyHandle);
                ThrowIfFailed(status);
                var right = new LsaUnicodeString
                {
                    Buffer = rightPointer,
                    Length = (ushort)("SeServiceLogonRight".Length * 2),
                    MaximumLength = (ushort)(("SeServiceLogonRight".Length + 1) * 2)
                };
                ThrowIfFailed(LsaRemoveAccountRights(
                    policyHandle,
                    sidPointer,
                    false,
                    new[] { right },
                    1));
            }
            finally
            {
                if (policyHandle != IntPtr.Zero)
                {
                    LsaClose(policyHandle);
                }
                Marshal.FreeHGlobal(rightPointer);
                Marshal.FreeHGlobal(sidPointer);
            }
        }

        private static void ThrowIfFailed(uint status)
        {
            if (status != 0)
            {
                throw new Win32Exception((int)LsaNtStatusToWinError(status));
            }
        }
    }
}
"@
    }

}

function Grant-BridgeServiceLogOnRight {
    param([string]$AccountName)

    Initialize-BridgeServiceLogOnRightType
    [TinySwarmWorld.LsaAccountRights]::GrantLogOnAsService($AccountName)
}

function Test-BridgeServiceLogOnRight {
    param([string]$AccountName)

    Initialize-BridgeServiceLogOnRightType
    return [TinySwarmWorld.LsaAccountRights]::HasLogOnAsService($AccountName)
}

function Revoke-BridgeServiceLogOnRight {
    param([string]$AccountName)

    Initialize-BridgeServiceLogOnRightType
    [TinySwarmWorld.LsaAccountRights]::RevokeLogOnAsService($AccountName)
}

function Test-OtherServiceUsesBridgeAccount {
    param([string]$AccountSid)

    foreach ($service in @(Get-CimInstance -ClassName Win32_Service -ErrorAction Stop)) {
        if ([string]$service.Name -eq $ServiceName -or [string]::IsNullOrWhiteSpace([string]$service.StartName)) {
            continue
        }
        try {
            $sid = Get-BridgeAccountSidValue -AccountName ([string]$service.StartName)
            if ($sid -eq $AccountSid) {
                return $true
            }
        } catch {
            continue
        }
    }
    return $false
}

function Undo-BridgeOwnedLogOnRight {
    param(
        $Manifest,
        [string]$AccountName
    )

    if (
        $null -eq $Manifest -or
        -not [bool]$Manifest.logOnRightGrantedByTsw -or
        [bool]$Manifest.logOnRightPreexisting
    ) {
        return
    }
    $accountSid = Get-BridgeAccountSidValue -AccountName $AccountName
    if ([string]$Manifest.accountSid -ne $accountSid) {
        Write-Warning "The service-logon right was left unchanged because its ownership SID is inconsistent."
        return
    }
    if (Test-OtherServiceUsesBridgeAccount -AccountSid $accountSid) {
        Write-Warning "The service-logon right was left unchanged because another Windows service uses the account."
        return
    }
    if (-not (Test-BridgeServiceLogOnRight -AccountName $AccountName)) {
        return
    }
    Revoke-BridgeServiceLogOnRight -AccountName $AccountName
    Write-Host "SERVICE right removed: SeServiceLogonRight"
}

function Undo-BridgeTransactionOwnedLogOnRight {
    param($Transaction)

    if ($Transaction.ServiceExisted -or -not $Transaction.ServiceCreateIntent) {
        return
    }
    $manifest = Get-BridgeInstallationManifest
    if ($null -eq $manifest) {
        return
    }
    Undo-BridgeOwnedLogOnRight `
        -Manifest $manifest `
        -AccountName (Get-CurrentBridgeServiceAccount)
}

function Get-ConfiguredDistro {
    param($Config)

    if ($Config.PSObject.Properties.Name -contains "distro") {
        return [string]$Config.distro
    }
    return "auto"
}

function Invoke-WslShellText {
    param(
        $Config,
        [string]$Command
    )

    $distro = Get-ConfiguredDistro $Config
    if ([string]::IsNullOrWhiteSpace($distro) -or $distro -eq "auto") {
        $raw = & wsl.exe sh -lc $Command 2>$null
    } else {
        $raw = & wsl.exe -d $distro -e sh -lc $Command 2>$null
    }

    if ($LASTEXITCODE -ne 0) {
        throw "WSL command failed for configured distro '$distro': $Command"
    }

    return ($raw -join "`n").Trim()
}

function New-BridgePrerequisiteResult {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Message
    )

    return [pscustomobject]@{
        Name    = $Name
        Passed  = $Passed
        Message = $Message
    }
}

function Get-BridgePrerequisiteResults {
    param($Config)

    $results = [System.Collections.ArrayList]::new()
    $windowsDetected = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "windows" `
        -Passed $windowsDetected `
        -Message $(if ($windowsDetected) { "Windows host detected." } else { "Run this script from Windows PowerShell." })))

    $isAdministrator = Test-IsAdministrator
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "administrator" `
        -Passed $isAdministrator `
        -Message $(if ($isAdministrator) { "PowerShell is elevated." } else { "Open PowerShell as Administrator." })))

    $wslAvailable = $null -ne (Get-Command wsl.exe -ErrorAction SilentlyContinue)
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "wsl-command" `
        -Passed $wslAvailable `
        -Message $(if ($wslAvailable) { "wsl.exe is available." } else { "Install WSL 2 before preparing the bridge." })))

    $netshAvailable = $null -ne (Get-Command netsh.exe -ErrorAction SilentlyContinue)
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "netsh-command" `
        -Passed $netshAvailable `
        -Message $(if ($netshAvailable) { "netsh.exe is available." } else { "netsh.exe is required for Windows portproxy rules." })))

    $firewallAvailable = $null -ne (Get-Command New-NetFirewallRule -ErrorAction SilentlyContinue)
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "firewall-cmdlet" `
        -Passed $firewallAvailable `
        -Message $(if ($firewallAvailable) { "Windows Firewall cmdlets are available." } else { "New-NetFirewallRule is unavailable." })))

    $serviceManagementAvailable = (
        $null -ne (Get-Command Get-Service -ErrorAction SilentlyContinue) -and
        $null -ne (Get-Command New-Service -ErrorAction SilentlyContinue) -and
        $null -ne (Get-Command sc.exe -ErrorAction SilentlyContinue)
    )
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "service-management" `
        -Passed $serviceManagementAvailable `
        -Message $(if ($serviceManagementAvailable) { "Windows service management commands are available." } else { "Get-Service, New-Service, and sc.exe are required." })))

    $ipHelper = Get-Service -Name iphlpsvc -ErrorAction SilentlyContinue
    $ipHelperRunning = $null -ne $ipHelper -and $ipHelper.Status -eq "Running"
    [void]$results.Add((New-BridgePrerequisiteResult `
        -Name "ip-helper" `
        -Passed $ipHelperRunning `
        -Message $(if ($ipHelperRunning) { "IP Helper is running." } else { "Start the Windows IP Helper service (iphlpsvc)." })))

    if ($wslAvailable) {
        try {
            $kernelRelease = Invoke-WslShellText -Config $Config -Command "uname -r"
            $isWsl2 = $kernelRelease -match "(?i)(microsoft-standard-wsl2|wsl2)"
            [void]$results.Add((New-BridgePrerequisiteResult `
                -Name "wsl2-runtime" `
                -Passed $isWsl2 `
                -Message $(if ($isWsl2) { "Configured distro is running under WSL 2." } else { "Configured distro is not running under WSL 2." })))
        } catch {
            [void]$results.Add((New-BridgePrerequisiteResult `
                -Name "wsl2-runtime" `
                -Passed $false `
                -Message $_.Exception.Message))
        }

        try {
            $pidOne = Invoke-WslShellText -Config $Config -Command "ps -p 1 -o comm="
            $systemdRunning = $pidOne.Trim() -eq "systemd"
            [void]$results.Add((New-BridgePrerequisiteResult `
                -Name "wsl-systemd" `
                -Passed $systemdRunning `
                -Message $(if ($systemdRunning) { "systemd is PID 1 in the configured distro." } else { "Enable systemd in the configured WSL distro." })))
        } catch {
            [void]$results.Add((New-BridgePrerequisiteResult `
                -Name "wsl-systemd" `
                -Passed $false `
                -Message $_.Exception.Message))
        }

        try {
            $wslIp = Get-WslIp $Config
            [void]$results.Add((New-BridgePrerequisiteResult `
                -Name "wsl-ipv4" `
                -Passed $true `
                -Message "Current WSL IPv4 address resolved: $wslIp"))
        } catch {
            [void]$results.Add((New-BridgePrerequisiteResult `
                -Name "wsl-ipv4" `
                -Passed $false `
                -Message $_.Exception.Message))
        }
    }

    return @($results)
}

function Write-BridgePrerequisiteResults {
    param($Results)

    foreach ($result in $Results) {
        $status = if ($result.Passed) { "OK" } else { "FAIL" }
        $color = if ($result.Passed) { "Green" } else { "Yellow" }
        Write-Host ("PREREQUISITE {0,-4} {1}: {2}" -f $status, $result.Name, $result.Message) -ForegroundColor $color
    }
}

function Assert-BridgePrerequisites {
    param($Config)

    $results = @(Get-BridgePrerequisiteResults -Config $Config)
    Write-BridgePrerequisiteResults -Results $results
    $failed = @($results | Where-Object { -not $_.Passed })
    if ($failed.Count -gt 0) {
        $failedNames = $failed.Name -join ", "
        throw "Windows/WSL bridge prerequisites failed: $failedNames"
    }
}

function Read-BridgeConfig {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Config file not found: $Path"
    }

    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Convert-ToArray {
    param($Value)
    if ($null -eq $Value) { return @() }
    if ($Value -is [System.Array]) { return @($Value) }
    return @($Value)
}

function Get-WslIp {
    param($Config)

    $distro = ""
    if ($Config.PSObject.Properties.Name -contains "distro") {
        $distro = [string]$Config.distro
    }

    if ([string]::IsNullOrWhiteSpace($distro) -or $distro -eq "auto") {
        $raw = & wsl.exe hostname -I 2>$null
    } else {
        $raw = & wsl.exe -d $distro -e hostname -I 2>$null
    }

    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($raw -join " "))) {
        throw "Could not determine WSL IP. Check that WSL is installed and the configured distro is running. Configured distro: '$distro'"
    }

    $ip = (($raw -join " ").Trim().Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries))[0]

    Assert-ValidIPv4Address -Value $ip -Name "WSL address"

    return $ip
}

function Get-ListenAddress {
    param($Config)
    if ($Config.PSObject.Properties.Name -contains "listenAddress" -and -not [string]::IsNullOrWhiteSpace([string]$Config.listenAddress)) {
        $address = [string]$Config.listenAddress
        Assert-ValidIPv4Address -Value $address -Name "listenAddress"
        return $address
    }
    return "0.0.0.0"
}

function Get-HostsAddress {
    param($Config)
    if ($Config.PSObject.Properties.Name -contains "hostsAddress" -and -not [string]::IsNullOrWhiteSpace([string]$Config.hostsAddress)) {
        $address = [string]$Config.hostsAddress
        Assert-ValidIPv4Address -Value $address -Name "hostsAddress"
        return $address
    }
    return "127.0.0.1"
}

function Get-FirewallRulePrefix {
    param($Config)
    if ($Config.PSObject.Properties.Name -contains "firewallRulePrefix" -and -not [string]::IsNullOrWhiteSpace([string]$Config.firewallRulePrefix)) {
        $prefix = [string]$Config.firewallRulePrefix
        Assert-ValidFirewallRulePrefix -Prefix $prefix
        return $prefix
    }
    return "Tiny Swarm World"
}

function Get-DiscoveryIntervalMinutes {
    param($Config)

    $interval = 1
    if ($Config.PSObject.Properties.Name -contains "discoveryIntervalMinutes") {
        $interval = [int]$Config.discoveryIntervalMinutes
    }
    if ($interval -lt 1 -or $interval -gt 60) {
        throw "discoveryIntervalMinutes must be between 1 and 60."
    }
    return $interval
}

function Add-TswRegistryPortMapping {
    param(
        [System.Collections.ArrayList] $Mappings,
        [hashtable] $Entry
    )

    if (-not $Entry.ContainsKey("external_port")) {
        return
    }

    $protocol = "tcp"
    if ($Entry.ContainsKey("protocol")) {
        $protocol = [string] $Entry["protocol"]
    }

    if ($protocol.ToLowerInvariant() -ne "tcp") {
        return
    }

    $port = [int] $Entry["external_port"]
    Assert-ValidTcpPort -Port $port -Name "external_port"
    $name = "port-$port"
    if ($Entry.ContainsKey("id") -and -not [string]::IsNullOrWhiteSpace([string] $Entry["id"])) {
        $name = [string] $Entry["id"]
    }

    [void] $Mappings.Add([pscustomobject]@{
        Name        = $name
        ListenPort  = $port
        ConnectPort = $port
    })
}

function Add-TswRegistryHostName {
    param(
        [System.Collections.ArrayList] $HostNames,
        [hashtable] $Entry
    )

    if (-not $Entry.ContainsKey("route_host")) {
        return
    }

    $hostName = [string] $Entry["route_host"]
    if (-not [string]::IsNullOrWhiteSpace($hostName)) {
        Assert-ValidRouteHostName -HostName $hostName
        [void] $HostNames.Add($hostName)
    }
}

function Read-TswPortRegistry {
    param([string] $RegistryPath)

    $mappings = [System.Collections.ArrayList]::new()
    $hostNames = [System.Collections.ArrayList]::new()
    if (-not (Test-Path -LiteralPath $RegistryPath)) {
        return [pscustomobject]@{ Mappings = @(); HostNames = @() }
    }

    $inPorts = $false
    $current = $null

    foreach ($line in Get-Content -LiteralPath $RegistryPath) {
        if ($line -match "^ports:\s*$") {
            $inPorts = $true
            continue
        }
        if (-not $inPorts) {
            continue
        }
        if ($line -match "^\S" -and $line -notmatch "^ports:\s*$") {
            break
        }
        if ($line -match "^\s*-\s+id:\s*(.+?)\s*$") {
            if ($null -ne $current) {
                Add-TswRegistryPortMapping -Mappings $mappings -Entry $current
                Add-TswRegistryHostName -HostNames $hostNames -Entry $current
            }
            $current = @{ id = $Matches[1].Trim().Trim('"').Trim("'") }
            continue
        }
        if ($null -eq $current) {
            continue
        }
        if ($line -match "^\s+external_port:\s*(\d+)\s*$") {
            $current["external_port"] = [int] $Matches[1]
            continue
        }
        if ($line -match "^\s+protocol:\s*(\S+)\s*$") {
            $current["protocol"] = $Matches[1].Trim().Trim('"').Trim("'")
            continue
        }
        if ($line -match "^\s+route_host:\s*(\S+)\s*$") {
            $current["route_host"] = $Matches[1].Trim().Trim('"').Trim("'")
            continue
        }
    }

    if ($null -ne $current) {
        Add-TswRegistryPortMapping -Mappings $mappings -Entry $current
        Add-TswRegistryHostName -HostNames $hostNames -Entry $current
    }

    return [pscustomobject]@{
        Mappings = @($mappings | Sort-Object ListenPort -Unique)
        HostNames = @($hostNames | Sort-Object -Unique)
    }
}

function Get-ConfigPortMappings {
    param($Config)

    $result = @()
    $propertyNames = $Config.PSObject.Properties.Name
    $mappingProperties = @("additionalPortMappings", "portMappings")

    foreach ($propertyName in $mappingProperties) {
        if (-not ($propertyNames -contains $propertyName)) {
            continue
        }
        foreach ($m in (Convert-ToArray $Config.$propertyName)) {
            $name = "port-$($m.listenPort)"
            if ($m.PSObject.Properties.Name -contains "name" -and -not [string]::IsNullOrWhiteSpace([string]$m.name)) {
                $name = [string]$m.name
            }

            $result += [pscustomobject]@{
                Name        = $name
                ListenPort  = [int]$m.listenPort
                ConnectPort = [int]$m.connectPort
            }
            Assert-ValidTcpPort -Port ([int]$m.listenPort) -Name "$propertyName.listenPort"
            Assert-ValidTcpPort -Port ([int]$m.connectPort) -Name "$propertyName.connectPort"
        }
    }

    if ($propertyNames -contains "ports") {
        foreach ($p in (Convert-ToArray $Config.ports)) {
            $port = [int]$p
            Assert-ValidTcpPort -Port $port -Name "ports"
            $result += [pscustomobject]@{
                Name        = "port-$port"
                ListenPort  = $port
                ConnectPort = $port
            }
        }
    }

    return $result
}

function Get-PortMappings {
    param(
        $Config,
        $RegistryMappings
    )

    $result = @()
    $seenPorts = [System.Collections.Generic.HashSet[int]]::new()

    foreach ($m in (Convert-ToArray $RegistryMappings)) {
        if ($seenPorts.Add([int] $m.ListenPort)) {
            $result += $m
        }
    }

    foreach ($m in (Get-ConfigPortMappings $Config)) {
        if ($seenPorts.Add([int] $m.ListenPort)) {
            $result += $m
        }
    }

    if ($result.Count -eq 0) {
        throw "No ports configured. Add external TCP ports to infra\config\ports.yaml or provide additionalPortMappings in $ConfigPath."
    }

    return $result | Sort-Object ListenPort -Unique
}

function Remove-PortProxy {
    param(
        [string]$ListenAddress,
        [int]$ListenPort
    )

    $null = & netsh interface portproxy delete v4tov4 "listenaddress=$ListenAddress" "listenport=$ListenPort" protocol=tcp 2>$null
}

function Add-PortProxy {
    param(
        [string]$ListenAddress,
        [int]$ListenPort,
        [string]$ConnectAddress,
        [int]$ConnectPort
    )

    $output = & netsh interface portproxy add v4tov4 "listenaddress=$ListenAddress" "listenport=$ListenPort" "connectaddress=$ConnectAddress" "connectport=$ConnectPort" protocol=tcp 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to add portproxy $ListenAddress`:$ListenPort -> $ConnectAddress`:$ConnectPort. Output: $($output -join ' ')"
    }
}

function Get-PortProxyRecords {
    $records = [System.Collections.ArrayList]::new()
    $output = & netsh interface portproxy show v4tov4 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to inspect Windows portproxy state."
    }

    foreach ($line in $output) {
        if ($line -match '^\s*(\d{1,3}(?:\.\d{1,3}){3})\s+(\d+)\s+(\d{1,3}(?:\.\d{1,3}){3})\s+(\d+)\s*$') {
            [void]$records.Add([pscustomobject]@{
                ListenAddress  = $Matches[1]
                ListenPort     = [int]$Matches[2]
                ConnectAddress = $Matches[3]
                ConnectPort    = [int]$Matches[4]
            })
        }
    }
    return @($records)
}

function Get-ProtectedBridgeState {
    if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) {
        return $null
    }
    try {
        return Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        throw "The protected Windows bridge state is invalid; destructive cleanup was refused."
    }
}

function Remove-StalePortProxyMappings {
    param(
        $Config,
        $Mappings
    )

    $previous = Get-ProtectedBridgeState
    if ($null -eq $previous -or -not ($previous.PSObject.Properties.Name -contains "mappings")) {
        return
    }
    if (
        $previous.contractVersion -ne 2 -or
        [string]$previous.serviceName -ne $ServiceName -or
        [string]$previous.agentMode -ne "windows-service"
    ) {
        throw "Protected previous bridge state is not valid stale-mapping authority."
    }

    $listenAddress = Get-ListenAddress $Config
    $previousListenAddress = $listenAddress
    if ($previous.PSObject.Properties.Name -contains "listenAddress" -and -not [string]::IsNullOrWhiteSpace([string]$previous.listenAddress)) {
        $previousListenAddress = [string]$previous.listenAddress
    }
    Assert-ValidIPv4Address -Value $previousListenAddress -Name "previous listenAddress"
    $previousConnectAddress = [string]$previous.wslIp
    Assert-ValidIPv4Address -Value $previousConnectAddress -Name "previous wslIp"
    $desiredPorts = [System.Collections.Generic.HashSet[int]]::new()
    foreach ($mapping in $Mappings) {
        [void]$desiredPorts.Add([int]$mapping.ListenPort)
    }

    $records = @(Get-PortProxyRecords)
    foreach ($mapping in (Convert-ToArray $previous.mappings)) {
        $port = [int]$mapping.listenPort
        Assert-ValidTcpPort -Port $port -Name "previous listenPort"
        $connectPort = [int]$mapping.connectPort
        Assert-ValidTcpPort -Port $connectPort -Name "previous connectPort"
        if ($previousListenAddress -ne $listenAddress -or -not $desiredPorts.Contains($port)) {
            $sameListener = @($records | Where-Object {
                $_.ListenAddress -eq $previousListenAddress -and $_.ListenPort -eq $port
            })
            $exactPrevious = @($sameListener | Where-Object {
                $_.ConnectAddress -eq $previousConnectAddress -and $_.ConnectPort -eq $connectPort
            })
            if ($exactPrevious.Count -eq 1) {
                Remove-PortProxy -ListenAddress $previousListenAddress -ListenPort $port
                Write-Host ("PORTPROXY stale mapping removed {0}:{1}" -f $previousListenAddress, $port)
            } elseif ($sameListener.Count -ne 0) {
                throw "Stale portproxy cleanup refused a listener now owned by a different tuple: $previousListenAddress`:$port"
            }
        }
    }
}

function Test-PortProxyMappingsReady {
    param(
        $Config,
        [string]$WslIp,
        $Mappings
    )

    $listenAddress = Get-ListenAddress $Config
    $records = @(Get-PortProxyRecords)
    foreach ($mapping in $Mappings) {
        $matches = @($records | Where-Object {
            $_.ListenAddress -eq $listenAddress -and
            $_.ListenPort -eq [int]$mapping.ListenPort -and
            $_.ConnectAddress -eq $WslIp -and
            $_.ConnectPort -eq [int]$mapping.ConnectPort
        })
        if ($matches.Count -ne 1) {
            return $false
        }
    }
    return $true
}

function Reconcile-PortProxy {
    param(
        $Config,
        [string]$WslIp,
        $Mappings
    )

    Remove-StalePortProxyMappings -Config $Config -Mappings $Mappings
    $listenAddress = Get-ListenAddress $Config
    $records = @(Get-PortProxyRecords)

    foreach ($m in $Mappings) {
        $matches = @($records | Where-Object {
            $_.ListenAddress -eq $listenAddress -and
            $_.ListenPort -eq [int]$m.ListenPort -and
            $_.ConnectAddress -eq $WslIp -and
            $_.ConnectPort -eq [int]$m.ConnectPort
        })
        if ($matches.Count -eq 1) {
            Write-Host ("PORTPROXY unchanged {0}:{1} -> {2}:{3} ({4})" -f $listenAddress, $m.ListenPort, $WslIp, $m.ConnectPort, $m.Name)
            continue
        }
        $sameListener = @($records | Where-Object {
            $_.ListenAddress -eq $listenAddress -and $_.ListenPort -eq [int]$m.ListenPort
        })
        if ($sameListener.Count -ne 0) {
            throw "Portproxy reconcile refused a listener owned by a different tuple: $listenAddress`:$($m.ListenPort)"
        }
        Add-PortProxy -ListenAddress $listenAddress -ListenPort $m.ListenPort -ConnectAddress $WslIp -ConnectPort $m.ConnectPort
        Write-Host ("PORTPROXY {0}:{1} -> {2}:{3} ({4})" -f $listenAddress, $m.ListenPort, $WslIp, $m.ConnectPort, $m.Name)
    }
}

function Get-FirewallRuleSnapshot {
    param($Config)

    $prefix = Get-FirewallRulePrefix $Config
    $rules = @(Get-NetFirewallRule -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -like "$prefix TCP *" })
    $filtersByRuleId = @{}
    if ($rules.Count -gt 0) {
        foreach ($filter in @($rules | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue)) {
            $filtersByRuleId[[string]$filter.InstanceID] = $filter
        }
    }
    return [pscustomobject]@{
        Rules           = $rules
        FiltersByRuleId = $filtersByRuleId
    }
}

function Test-FirewallRuleReady {
    param(
        $Config,
        [int]$Port,
        $Snapshot = $null
    )

    $prefix = Get-FirewallRulePrefix $Config
    $ruleName = "$prefix TCP $Port"
    if ($null -eq $Snapshot) {
        $Snapshot = Get-FirewallRuleSnapshot -Config $Config
    }
    $rules = @($Snapshot.Rules | Where-Object { $_.DisplayName -eq $ruleName })
    if ($rules.Count -ne 1) {
        return $false
    }
    $rule = $rules[0]
    if ($rule.Enabled.ToString() -ne "True" -or $rule.Direction.ToString() -ne "Inbound" -or $rule.Action.ToString() -ne "Allow") {
        return $false
    }
    $filter = $Snapshot.FiltersByRuleId[[string]$rule.Name]
    return (
        $null -ne $filter -and
        $filter.LocalPort.ToString() -eq $Port.ToString() -and
        $filter.Protocol.ToString() -in @("TCP", "6")
    )
}

function Test-FirewallRulesReady {
    param(
        $Config,
        $Mappings
    )

    $prefix = Get-FirewallRulePrefix $Config
    $desiredPorts = @(($Mappings | Select-Object -ExpandProperty ListenPort) | Sort-Object -Unique)
    $snapshot = Get-FirewallRuleSnapshot -Config $Config
    $managedRules = @($snapshot.Rules)
    if ($managedRules.Count -ne $desiredPorts.Count) {
        return $false
    }
    foreach ($port in $desiredPorts) {
        if (-not (Test-FirewallRuleReady -Config $Config -Port $port -Snapshot $snapshot)) {
            return $false
        }
    }
    return $true
}

function Reconcile-FirewallRules {
    param(
        $Config,
        $Mappings
    )

    $prefix = Get-FirewallRulePrefix $Config
    $snapshot = Get-FirewallRuleSnapshot -Config $Config

    $desiredPorts = @(($Mappings | Select-Object -ExpandProperty ListenPort) | Sort-Object -Unique)
    $desiredNames = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($port in $desiredPorts) {
        [void]$desiredNames.Add("$prefix TCP $port")
    }

    $snapshot.Rules |
        Where-Object { -not $desiredNames.Contains($_.DisplayName) } |
        Remove-NetFirewallRule -ErrorAction SilentlyContinue

    foreach ($port in $desiredPorts) {
        $ruleName = "$prefix TCP $port"
        if (Test-FirewallRuleReady -Config $Config -Port $port -Snapshot $snapshot) {
            Write-Host ("FIREWALL unchanged TCP {0}" -f $port)
            continue
        }
        Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -eq $ruleName } |
            Remove-NetFirewallRule -ErrorAction SilentlyContinue
        New-NetFirewallRule `
            -DisplayName $ruleName `
            -Direction Inbound `
            -Action Allow `
            -Protocol TCP `
            -LocalPort $port `
            -Profile Any | Out-Null

        Write-Host ("FIREWALL allow TCP {0}" -f $port)
    }
}

function Remove-ManagedHostsBlock {
    if (-not (Test-Path -LiteralPath $HostsPath)) {
        return ""
    }

    $content = Get-Content -LiteralPath $HostsPath -Raw -ErrorAction Stop
    $startEsc = [regex]::Escape($HostsStart)
    $endEsc = [regex]::Escape($HostsEnd)
    $pattern = "(?ms)^[ \t]*$startEsc.*?^[ \t]*$endEsc[ \t]*(\r?\n)?"
    return [regex]::Replace($content, $pattern, "")
}

function Get-BridgeHostNames {
    param(
        $Config,
        $RegistryHostNames
    )

    $hostNames = @()
    if (-not ($Config.PSObject.Properties.Name -contains "hostNames")) {
        $hostNames = @()
    } else {
        $hostNames = @(Convert-ToArray $Config.hostNames | ForEach-Object { [string]$_ })
    }

    $hostNames += @(Convert-ToArray $RegistryHostNames | ForEach-Object { [string]$_ })
    $result = @($hostNames | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object -Unique)
    foreach ($hostName in $result) {
        Assert-ValidRouteHostName -HostName $hostName
    }
    return $result
}

function Get-ReconciledHostsContent {
    param(
        $Config,
        $HostNames
    )

    $hostNames = @(Convert-ToArray $HostNames)
    $content = Remove-ManagedHostsBlock
    if ($hostNames.Count -eq 0) {
        return $content.TrimEnd() + [Environment]::NewLine
    }

    $hostsAddress = Get-HostsAddress $Config
    $hostLines = @(
        $hostNames | ForEach-Object { "$hostsAddress`t$_" }
    )
    $block = @($HostsStart) + $hostLines + @($HostsEnd)
    $block = $block -join [Environment]::NewLine
    $base = $content.TrimEnd()
    if ([string]::IsNullOrWhiteSpace($base)) {
        return $block + [Environment]::NewLine
    }
    return $base + [Environment]::NewLine + $block + [Environment]::NewLine
}

function Test-HostsFileReady {
    param(
        $Config,
        $HostNames
    )

    if (-not (Test-Path -LiteralPath $HostsPath)) {
        return $false
    }
    $current = Get-Content -LiteralPath $HostsPath -Raw -ErrorAction Stop
    $desired = Get-ReconciledHostsContent -Config $Config -HostNames $HostNames
    return $current -eq $desired
}

function Reconcile-HostsFile {
    param(
        $Config,
        $HostNames
    )

    $hostNames = @(Convert-ToArray $HostNames)
    if ($hostNames.Count -eq 0) {
        return
    }

    $hostsAddress = Get-HostsAddress $Config
    $newContent = Get-ReconciledHostsContent -Config $Config -HostNames $hostNames
    if ((Test-Path -LiteralPath $HostsPath) -and (Test-HostsFileReady -Config $Config -HostNames $hostNames)) {
        Write-Host ("HOSTS unchanged {0} -> {1}" -f ($hostNames -join ", "), $hostsAddress)
        return
    }

    [System.IO.File]::WriteAllText($HostsPath, $newContent, [System.Text.Encoding]::ASCII)
    Write-Host ("HOSTS {0} -> {1}" -f ($hostNames -join ", "), $hostsAddress)
}

function Remove-HostsFileBlock {
    $content = Remove-ManagedHostsBlock
    Set-Content -LiteralPath $HostsPath -Value ($content.TrimEnd() + [Environment]::NewLine) -Encoding ASCII -Force
    Write-Host "HOSTS managed Tiny Swarm block removed"
}

function Unregister-BridgeTask {
    if ($null -eq (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue)) {
        return
    }
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "TASK removed: $TaskName"
    }
}

function Get-BridgeService {
    return Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
}

function Get-BridgeServiceDetails {
    $serviceRegistryPath = "HKLM:\SYSTEM\CurrentControlSet\Services\$ServiceName"
    $properties = Get-ItemProperty -LiteralPath $serviceRegistryPath -ErrorAction SilentlyContinue
    if ($null -eq $properties) {
        return $null
    }
    return [pscustomobject]@{
        PathName  = [string]$properties.ImagePath
        StartName = [string]$properties.ObjectName
        StartMode = $(if ([int]$properties.Start -eq 2) { "Auto" } else { "Other" })
    }
}

function Get-BridgeServiceDefinitionFields {
    param([string]$Path = $ServiceDefinitionPath)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }
    try {
        $definition = [xml](Get-Content -LiteralPath $Path -Raw -Encoding UTF8)
        $serviceNode = $definition.DocumentElement
        if ($null -eq $serviceNode -or $serviceNode.LocalName -ne "service") {
            return $null
        }
        if ($serviceNode.Attributes.Count -ne 0) {
            return $null
        }
        $expectedNodeNames = @(
            "id",
            "name",
            "description",
            "executable",
            "arguments",
            "workingdirectory",
            "startmode",
            "delayedAutoStart",
            "hidewindow",
            "stoptimeout",
            "onfailure",
            "resetfailure",
            "logpath",
            "log"
        )
        $elementNodes = @($serviceNode.ChildNodes | Where-Object {
            $_.NodeType -eq [Xml.XmlNodeType]::Element
        })
        if ($elementNodes.Count -ne $expectedNodeNames.Count) {
            return $null
        }
        foreach ($node in $elementNodes) {
            if ($expectedNodeNames -cnotcontains [string]$node.Name) {
                return $null
            }
            if (-not [string]::IsNullOrEmpty([string]$node.NamespaceURI)) {
                return $null
            }
            if (@($node.SelectNodes("./*")).Count -ne 0) {
                return $null
            }
        }
        $fields = [ordered]@{}
        foreach ($name in $expectedNodeNames) {
            $nodes = @($serviceNode.SelectNodes("./$name"))
            if ($nodes.Count -ne 1) {
                return $null
            }
            $fields[$name] = [string]$nodes[0].InnerText
        }

        foreach ($name in @(
            "id",
            "name",
            "description",
            "executable",
            "arguments",
            "workingdirectory",
            "startmode",
            "delayedAutoStart",
            "hidewindow",
            "stoptimeout",
            "resetfailure",
            "logpath"
        )) {
            if ($serviceNode.SelectSingleNode("./$name").Attributes.Count -ne 0) {
                return $null
            }
        }
        $onFailureNode = $serviceNode.SelectSingleNode("./onfailure")
        if (
            $onFailureNode.Attributes.Count -ne 2 -or
            $null -eq $onFailureNode.Attributes["action"] -or
            $null -eq $onFailureNode.Attributes["delay"] -or
            [string]$onFailureNode.Attributes["action"].Value -cne "restart" -or
            [string]$onFailureNode.Attributes["delay"].Value -cne "10 sec" -or
            -not [string]::IsNullOrWhiteSpace([string]$onFailureNode.InnerText)
        ) {
            return $null
        }
        $logNode = $serviceNode.SelectSingleNode("./log")
        if (
            $logNode.Attributes.Count -ne 1 -or
            $null -eq $logNode.Attributes["mode"] -or
            [string]$logNode.Attributes["mode"].Value -cne "roll" -or
            -not [string]::IsNullOrWhiteSpace([string]$logNode.InnerText)
        ) {
            return $null
        }
        $expectedStaticValues = [ordered]@{
            description      = "Keeps the Tiny Swarm World Windows to WSL network bridge aligned with the current WSL address."
            startmode        = "Automatic"
            delayedAutoStart = "true"
            hidewindow       = "true"
            stoptimeout      = "30 sec"
            resetfailure     = "1 hour"
            logpath          = "%BASE%\logs"
        }
        foreach ($entry in $expectedStaticValues.GetEnumerator()) {
            if ([string]$fields[$entry.Key] -cne [string]$entry.Value) {
                return $null
            }
        }
        return [pscustomobject]$fields
    } catch {
        return $null
    }
}

function Test-BridgeServiceDefinitionOwned {
    param([string]$Path = $ServiceDefinitionPath)

    $fields = Get-BridgeServiceDefinitionFields -Path $Path
    if ($null -eq $fields) {
        return $false
    }
    try {
        $expectedExecutable = "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
        $argumentPrefix = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$InstalledServiceRunnerPath`" -BridgeScriptPath `"$InstalledBridgeScriptPath`" -ConfigPath `"$InstalledConfigPath`" -PortRegistryPath `"$InstalledPortRegistryPath`" -IntervalMinutes "
        $argumentsMatch = [string]$fields.arguments -match (
            "^" + [regex]::Escape($argumentPrefix) + "(?:[1-9]|[1-5][0-9]|60)$"
        )
        return (
            [string]$fields.id -eq $ServiceName -and
            [string]$fields.name -eq $ServiceDisplayName -and
            [StringComparer]::OrdinalIgnoreCase.Equals([string]$fields.executable, $expectedExecutable) -and
            $argumentsMatch -and
            [StringComparer]::OrdinalIgnoreCase.Equals([string]$fields.workingdirectory, $ServiceBundleRoot)
        )
    } catch {
        return $false
    }
}

function Test-BridgeLegacyServiceDefinitionOwned {
    param([string]$Path = $ServiceDefinitionPath)

    $fields = Get-BridgeServiceDefinitionFields -Path $Path
    if ($null -eq $fields) {
        return $false
    }
    try {
        $expectedExecutable = "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
        $argumentPrefix = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$InstalledServiceRunnerPath`" -BridgeScriptPath `"$InstalledBridgeScriptPath`" -ConfigPath `"$InstalledConfigPath`" -PortRegistryPath `"$InstalledPortRegistryPath`" -StateEvidencePath `""
        $argumentsMatch = [string]$fields.arguments -match (
            "^" + [regex]::Escape($argumentPrefix) + "[^`"]+`" -IntervalMinutes (?:[1-9]|[1-5][0-9]|60)$"
        )
        return (
            [string]$fields.id -eq $ServiceName -and
            [string]$fields.name -eq $ServiceDisplayName -and
            [StringComparer]::OrdinalIgnoreCase.Equals([string]$fields.executable, $expectedExecutable) -and
            $argumentsMatch -and
            [StringComparer]::OrdinalIgnoreCase.Equals([string]$fields.workingdirectory, $ServiceBundleRoot)
        )
    } catch {
        return $false
    }
}

function Get-BridgeInstallationManifest {
    if (-not (Test-Path -LiteralPath $InstallationManifestPath -PathType Leaf)) {
        return $null
    }
    try {
        return Get-Content -LiteralPath $InstallationManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        throw "The protected Windows bridge installation manifest is invalid."
    }
}

function Get-BridgeServiceOwnership {
    param([switch]$AllowAclMigration)

    $service = Get-BridgeService
    if ($null -eq $service) {
        if (Test-Path -LiteralPath $ServiceRoot) {
            try {
                Assert-BridgeServicePathSafety
            } catch {
                return [pscustomobject]@{ Status = "collision"; Service = $null; Details = $null; RequiresAdoption = $false; Reason = "unsafe_service_root_without_registration" }
            }
            if (-not (Test-BridgeServiceAclHardened)) {
                return [pscustomobject]@{ Status = "collision"; Service = $null; Details = $null; RequiresAdoption = $false; Reason = "unprotected_service_root_without_registration" }
            }
        }
        if (Test-Path -LiteralPath $TransactionJournalPath -PathType Leaf) {
            try {
                Assert-BridgeServicePathSafety
            } catch {
                return [pscustomobject]@{ Status = "collision"; Service = $null; Details = $null; RequiresAdoption = $false; Reason = "unsafe_recovery_path" }
            }
            if (-not (Test-BridgeServiceAclHardened)) {
                return [pscustomobject]@{ Status = "collision"; Service = $null; Details = $null; RequiresAdoption = $false; Reason = "unprotected_recovery_journal" }
            }
            return [pscustomobject]@{ Status = "owned"; Service = $null; Details = $null; RequiresAdoption = $false; Reason = "interrupted_transaction" }
        }
        try {
            $orphanedManifest = Get-BridgeInstallationManifest
        } catch {
            return [pscustomobject]@{ Status = "collision"; Service = $null; Details = $null; RequiresAdoption = $false; Reason = "installation_manifest_invalid" }
        }
        if ($null -ne $orphanedManifest) {
            try {
                Assert-BridgeServicePathSafety
                $manifestAccountSid = Get-BridgeAccountSidValue `
                    -AccountName ([string]$orphanedManifest.serviceAccount)
                $orphanedOwned = (
                    $orphanedManifest.contractVersion -eq 1 -and
                    [string]$orphanedManifest.serviceName -eq $ServiceName -and
                    [string]$orphanedManifest.accountSid -eq $manifestAccountSid -and
                    (Test-BridgeServiceAccountMatchesCurrentIdentity `
                        -AccountName ([string]$orphanedManifest.serviceAccount)) -and
                    [string]$orphanedManifest.wrapperSha256 -eq $WinSwSha256 -and
                    $orphanedManifest.PSObject.Properties.Name -contains "logOnRightPreexisting" -and
                    $orphanedManifest.PSObject.Properties.Name -contains "logOnRightGrantedByTsw" -and
                    (
                        [bool]$orphanedManifest.logOnRightPreexisting -xor
                        [bool]$orphanedManifest.logOnRightGrantedByTsw
                    ) -and
                    (Test-BridgeServiceAclHardened) -and
                    (Test-BridgeServiceDefinitionOwned) -and
                    (Test-Path -LiteralPath $ServiceWrapperPath -PathType Leaf) -and
                    (Get-FileHash -LiteralPath $ServiceWrapperPath -Algorithm SHA256).Hash -eq $WinSwSha256
                )
                if ($orphanedOwned) {
                    return [pscustomobject]@{
                        Status = "owned"
                        Service = $null
                        Details = [pscustomobject]@{ StartName = [string]$orphanedManifest.serviceAccount }
                        RequiresAdoption = $false
                        Reason = "owned_orphaned_installation"
                        AccountSid = $manifestAccountSid
                    }
                }
            } catch {
                # Fall through to collision classification.
            }
        }
        $rootHasContent = (
            (Test-Path -LiteralPath $ServiceRoot -PathType Container) -and
            $null -ne (Get-ChildItem -LiteralPath $ServiceRoot -Force -ErrorAction SilentlyContinue | Select-Object -First 1)
        )
        return [pscustomobject]@{
            Status           = $(if ($rootHasContent) { "collision" } else { "absent" })
            Service          = $null
            Details          = $null
            RequiresAdoption = $false
            Reason           = $(if ($rootHasContent) { "service_root_without_registration" } else { "service_absent" })
        }
    }

    try {
        Assert-BridgeServicePathSafety
    } catch {
        return [pscustomobject]@{ Status = "collision"; Service = $service; Details = $null; RequiresAdoption = $false; Reason = "unsafe_service_path" }
    }
    $details = Get-BridgeServiceDetails
    $registrationIdentityOwned = (
        $null -ne $details -and
        (Test-BridgeServicePathMatches -PathName ([string]$details.PathName)) -and
        (Test-BridgeServiceAccountMatchesCurrentIdentity -AccountName ([string]$details.StartName))
    )
    if (-not $registrationIdentityOwned) {
        return [pscustomobject]@{ Status = "collision"; Service = $service; Details = $details; RequiresAdoption = $false; Reason = "registration_not_owned" }
    }

    $accountSid = Get-BridgeAccountSidValue -AccountName ([string]$details.StartName)
    if (-not (Test-BridgeServiceAclHardened)) {
        if ($AllowAclMigration) {
            return [pscustomobject]@{
                Status               = "owned"
                Service              = $service
                Details              = $details
                RequiresAdoption     = $false
                RequiresAclMigration = $true
                Reason               = "registration_owned_acl_migration_required"
                AccountSid           = $accountSid
            }
        }
        return [pscustomobject]@{
            Status               = "collision"
            Service              = $service
            Details              = $details
            RequiresAdoption     = $false
            RequiresAclMigration = $false
            Reason               = "service_acl_not_owned"
            AccountSid           = $accountSid
        }
    }
    $wrapperOwned = (
        (Test-Path -LiteralPath $ServiceWrapperPath -PathType Leaf) -and
        (Get-FileHash -LiteralPath $ServiceWrapperPath -Algorithm SHA256).Hash -eq $WinSwSha256
    )
    if (-not $wrapperOwned) {
        return [pscustomobject]@{ Status = "collision"; Service = $service; Details = $details; RequiresAdoption = $false; Reason = "service_wrapper_invalid" }
    }
    try {
        $manifest = Get-BridgeInstallationManifest
    } catch {
        return [pscustomobject]@{ Status = "collision"; Service = $service; Details = $details; RequiresAdoption = $false; Reason = "installation_manifest_invalid" }
    }
    if ($null -eq $manifest) {
        if (-not ((Test-BridgeServiceDefinitionOwned) -or (Test-BridgeLegacyServiceDefinitionOwned))) {
            return [pscustomobject]@{ Status = "collision"; Service = $service; Details = $details; RequiresAdoption = $false; Reason = "legacy_service_definition_invalid" }
        }
        return [pscustomobject]@{ Status = "owned"; Service = $service; Details = $details; RequiresAdoption = $true; Reason = "verified_legacy_registration"; AccountSid = $accountSid }
    }
    if (-not (Test-BridgeServiceDefinitionOwned)) {
        return [pscustomobject]@{ Status = "collision"; Service = $service; Details = $details; RequiresAdoption = $false; Reason = "service_definition_invalid" }
    }
    $manifestAccountSid = ""
    try {
        $manifestAccountSid = Get-BridgeAccountSidValue -AccountName ([string]$manifest.serviceAccount)
    } catch {
        $manifestAccountSid = ""
    }
    $manifestOwned = (
        $manifest.contractVersion -eq 1 -and
        [string]$manifest.serviceName -eq $ServiceName -and
        [string]$manifest.accountSid -eq $accountSid -and
        $manifestAccountSid -eq $accountSid -and
        [string]$manifest.wrapperSha256 -eq $WinSwSha256 -and
        $manifest.PSObject.Properties.Name -contains "logOnRightPreexisting" -and
        $manifest.PSObject.Properties.Name -contains "logOnRightGrantedByTsw" -and
        ([bool]$manifest.logOnRightPreexisting -xor [bool]$manifest.logOnRightGrantedByTsw)
    )
    return [pscustomobject]@{
        Status           = $(if ($manifestOwned) { "owned" } else { "collision" })
        Service          = $service
        Details          = $details
        RequiresAdoption = $false
        Reason           = $(if ($manifestOwned) { "installation_manifest_valid" } else { "installation_manifest_invalid" })
        AccountSid       = $accountSid
    }
}

function Get-BridgeRecoveryServiceOwnership {
    param($Transaction)

    try {
        Assert-BridgeServicePathSafety
    } catch {
        return [pscustomobject]@{ Status = "collision"; Service = $null; Details = $null; Reason = "unsafe_recovery_path" }
    }
    if (-not (Test-BridgeServiceAclHardened)) {
        return [pscustomobject]@{ Status = "collision"; Service = $null; Details = $null; Reason = "unprotected_recovery_root" }
    }

    $service = Get-BridgeService
    if ($null -eq $service) {
        return [pscustomobject]@{
            Status  = $(if ($Transaction.ServiceExisted) { "collision" } else { "owned" })
            Service = $null
            Details = $null
            Reason  = $(if ($Transaction.ServiceExisted) { "expected_service_missing" } else { "service_was_absent" })
        }
    }
    if (-not $Transaction.ServiceExisted -and -not $Transaction.ServiceCreateIntent) {
        return [pscustomobject]@{ Status = "collision"; Service = $service; Details = $null; Reason = "unexpected_service_during_recovery" }
    }
    $details = Get-BridgeServiceDetails
    $registrationOwned = (
        $null -ne $details -and
        (Test-BridgeServicePathMatches -PathName ([string]$details.PathName)) -and
        (Test-BridgeServiceAccountMatchesCurrentIdentity -AccountName ([string]$details.StartName))
    )
    return [pscustomobject]@{
        Status  = $(if ($registrationOwned) { "owned" } else { "collision" })
        Service = $service
        Details = $details
        Reason  = $(if ($registrationOwned) { "scm_registration_owned" } else { "scm_registration_collision" })
    }
}

function New-BridgeInstallationManifestText {
    param(
        [string]$AccountSid,
        [string]$AccountName,
        [bool]$LogOnRightPreexisting,
        [bool]$LogOnRightGrantedByTsw
    )

    $manifest = [ordered]@{
        contractVersion = 1
        serviceName     = $ServiceName
        accountSid      = $AccountSid
        serviceAccount  = $AccountName
        wrapperSha256   = $WinSwSha256
        logOnRightPreexisting = $LogOnRightPreexisting
        logOnRightGrantedByTsw = $LogOnRightGrantedByTsw
        installedAt     = [DateTimeOffset]::Now.ToString("o")
    }
    return (($manifest | ConvertTo-Json -Depth 3) + [Environment]::NewLine)
}

function Test-BridgeServiceReady {
    $service = Get-BridgeService
    if ($null -eq $service) {
        return $false
    }

    try {
        Assert-BridgeServicePathSafety
    } catch {
        return $false
    }
    if (-not (Test-BridgeServiceAclHardened)) {
        return $false
    }

    $serviceDetails = Get-BridgeServiceDetails
    $wrapperReady = (
        (Test-Path -LiteralPath $ServiceWrapperPath -PathType Leaf) -and
        (Get-FileHash -LiteralPath $ServiceWrapperPath -Algorithm SHA256).Hash -eq $WinSwSha256
    )
    $definitionReady = Test-BridgeServiceDefinitionOwned
    return (
        $service.Status -eq "Running" -and
        $null -ne $serviceDetails -and
        $serviceDetails.StartMode -eq "Auto" -and
        (Test-BridgeServicePathMatches -PathName ([string]$serviceDetails.PathName)) -and
        (Test-BridgeServiceAccountMatchesCurrentIdentity -AccountName ([string]$serviceDetails.StartName)) -and
        $wrapperReady -and
        $definitionReady -and
        (Test-Path -LiteralPath $InstalledBridgeScriptPath -PathType Leaf) -and
        (Test-Path -LiteralPath $InstalledServiceRunnerPath -PathType Leaf) -and
        (Test-Path -LiteralPath $InstalledConfigPath -PathType Leaf) -and
        (Test-Path -LiteralPath $InstalledPortRegistryPath -PathType Leaf) -and
        (Test-Path -LiteralPath $InstalledBundleManifestPath -PathType Leaf)
    )
}

function Assert-BridgeRuntimeStateAuthority {
    Assert-BridgeServicePathSafety
    if (-not (Test-BridgeServiceAclHardened)) {
        throw "Windows bridge runtime state refused an unsafe ProgramData ACL."
    }
    $ownership = Get-BridgeServiceOwnership
    if ($ownership.Status -ne "owned") {
        throw "Windows bridge runtime state requires an owned service registration."
    }
}

function Get-BridgeAgentMode {
    if (Test-BridgeServiceReady) {
        return "windows-service"
    }
    return "unavailable"
}

function Remove-BridgeServiceRegistration {
    $ownership = Get-BridgeServiceOwnership
    if ($ownership.Status -eq "collision") {
        throw "Windows service removal was refused because the registration is not owned by Tiny Swarm World."
    }
    $service = $ownership.Service
    if ($null -eq $service) {
        return
    }

    if ($service.Status -ne "Stopped") {
        Stop-Service -Name $ServiceName -Force
        $service.WaitForStatus("Stopped", [TimeSpan]::FromSeconds(30))
    }

    & sc.exe delete $ServiceName | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not remove Windows service $ServiceName (exit code $LASTEXITCODE)."
    }
    for ($attempt = 0; $attempt -lt 30 -and $null -ne (Get-BridgeService); $attempt++) {
        Start-Sleep -Milliseconds 500
    }
    if ($null -ne (Get-BridgeService)) {
        throw "Windows service $ServiceName is still pending deletion. Close service-management consoles and retry."
    }
}

function Request-BridgeServiceCredential {
    param([string]$ExpectedAccount)

    Write-Host "A Windows credential dialog will open once. Use $ExpectedAccount, which owns the WSL distribution."
    $credential = Get-Credential -UserName $ExpectedAccount -Message "Tiny Swarm World WSL Bridge service account"
    if ($null -eq $credential) {
        throw "Windows service installation was cancelled before credentials were supplied."
    }
    if (-not (Test-BridgeServiceAccountMatchesCurrentIdentity -AccountName $credential.UserName)) {
        throw "The Windows service account must be the current WSL owner account $ExpectedAccount."
    }
    return $credential
}

function New-BridgeServiceRegistration {
    param(
        [string]$ExpectedAccount,
        [Management.Automation.PSCredential]$Credential = $null
    )

    if ($null -eq $Credential) {
        $Credential = Request-BridgeServiceCredential -ExpectedAccount $ExpectedAccount
    }

    Grant-BridgeServiceLogOnRight -AccountName $ExpectedAccount
    New-Service `
        -Name $ServiceName `
        -BinaryPathName "`"$ServiceWrapperPath`"" `
        -Credential $Credential `
        -DisplayName $ServiceDisplayName `
        -Description "Keeps the Tiny Swarm World Windows to WSL network bridge aligned with the current WSL address." `
        -StartupType Automatic | Out-Null
}

function Set-BridgeServiceRuntimePolicy {
    & sc.exe config $ServiceName start= delayed-auto | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not configure delayed automatic service start (exit code $LASTEXITCODE)."
    }
    & sc.exe failure $ServiceName reset= 3600 actions= restart/10000 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not configure service recovery (exit code $LASTEXITCODE)."
    }
}

function Start-BridgeServiceChecked {
    Start-Service -Name $ServiceName
    $service = Get-Service -Name $ServiceName
    $service.WaitForStatus("Running", [TimeSpan]::FromSeconds(30))
    if (-not (Test-BridgeServiceReady)) {
        throw "Windows service $ServiceName did not reach the expected running state."
    }
}

function Start-BridgeServiceRollbackChecked {
    param([string]$ExpectedBundleId = "")

    Start-Service -Name $ServiceName
    $service = Get-Service -Name $ServiceName
    $service.WaitForStatus("Running", [TimeSpan]::FromSeconds(30))
    if ([string]::IsNullOrWhiteSpace($ExpectedBundleId)) {
        $ownership = Get-BridgeServiceOwnership
        if ($ownership.Status -ne "owned" -or $service.Status -ne "Running") {
            throw "The legacy Windows bridge service could not be restored as an owned running registration."
        }
        return
    }
    if (-not (Test-BridgeServiceReady)) {
        throw "The previous Windows bridge service payload did not return to its expected running state."
    }
}

function Stop-BridgeServiceChecked {
    param($Service)

    if ($null -eq $Service -or $Service.Status -eq "Stopped") {
        return
    }
    Stop-Service -Name $ServiceName -Force
    $Service.WaitForStatus("Stopped", [TimeSpan]::FromSeconds(30))
}

function New-BridgeServiceDefinition {
    param([int]$IntervalMinutes)

    $escapedRunner = [Security.SecurityElement]::Escape($InstalledServiceRunnerPath)
    $escapedBridge = [Security.SecurityElement]::Escape($InstalledBridgeScriptPath)
    $escapedConfig = [Security.SecurityElement]::Escape($InstalledConfigPath)
    $escapedPortRegistry = [Security.SecurityElement]::Escape($InstalledPortRegistryPath)
    $escapedWorkingDirectory = [Security.SecurityElement]::Escape($ServiceBundleRoot)
    return @"
<service>
  <id>$ServiceName</id>
  <name>$ServiceDisplayName</name>
  <description>Keeps the Tiny Swarm World Windows to WSL network bridge aligned with the current WSL address.</description>
  <executable>%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe</executable>
  <arguments>-NoProfile -NonInteractive -ExecutionPolicy Bypass -File &quot;$escapedRunner&quot; -BridgeScriptPath &quot;$escapedBridge&quot; -ConfigPath &quot;$escapedConfig&quot; -PortRegistryPath &quot;$escapedPortRegistry&quot; -IntervalMinutes $IntervalMinutes</arguments>
  <workingdirectory>$escapedWorkingDirectory</workingdirectory>
  <startmode>Automatic</startmode>
  <delayedAutoStart>true</delayedAutoStart>
  <hidewindow>true</hidewindow>
  <stoptimeout>30 sec</stoptimeout>
  <onfailure action="restart" delay="10 sec"/>
  <resetfailure>1 hour</resetfailure>
  <logpath>%BASE%\logs</logpath>
  <log mode="roll"></log>
</service>
"@
}

function Get-BridgeBundleId {
    param($Hashes)

    $lines = @($Hashes.Keys | Sort-Object | ForEach-Object { "$_=$($Hashes[$_])" })
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes(($lines -join "`n"))
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha256.ComputeHash($bytes))).Replace("-", "")
    } finally {
        $sha256.Dispose()
    }
}

function Test-BridgeStagedPayload {
    param($StagedPayload)

    Assert-BridgePayloadPathSafety -Path $StagedPayload.Root
    $bridgePath = Join-Path $StagedPayload.Bundle "tws-wsl-bridge.ps1"
    $runnerPath = Join-Path $StagedPayload.Bundle "tws-wsl-bridge-service.ps1"
    $configPath = Join-Path $StagedPayload.Bundle "tws-wsl-bridge.config.json"
    $registryPath = Join-Path $StagedPayload.Bundle "ports.yaml"
    $manifestPath = Join-Path $StagedPayload.Bundle "bundle-manifest.json"
    foreach ($path in @($bridgePath, $runnerPath, $configPath, $registryPath, $manifestPath, $StagedPayload.Wrapper, $StagedPayload.Definition, $StagedPayload.InstallationManifest)) {
        Assert-BridgePayloadPathSafety -Path $path
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Staged bridge payload is incomplete: $path"
        }
    }

    foreach ($scriptPath in @($bridgePath, $runnerPath)) {
        $parseTokens = $null
        $parseErrors = $null
        [void][Management.Automation.Language.Parser]::ParseFile(
            $scriptPath,
            [ref]$parseTokens,
            [ref]$parseErrors
        )
        if ($parseErrors.Count -ne 0) {
            throw "Staged PowerShell payload failed syntax validation: $scriptPath"
        }
    }
    [void](Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json)
    [void](Read-TswPortRegistry -RegistryPath $registryPath)
    $definitionText = Get-Content -LiteralPath $StagedPayload.Definition -Raw -Encoding UTF8
    [void][xml]$definitionText
    if ($definitionText.IndexOf("<password", [StringComparison]::OrdinalIgnoreCase) -ge 0) {
        throw "The staged Windows service definition must not contain a password element."
    }
    foreach ($expectedPath in @($InstalledBridgeScriptPath, $InstalledServiceRunnerPath, $InstalledConfigPath, $InstalledPortRegistryPath)) {
        if ($definitionText.IndexOf($expectedPath, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
            throw "The staged Windows service definition does not reference the protected bundle."
        }
    }
    if (-not (Test-BridgeServiceDefinitionOwned -Path $StagedPayload.Definition)) {
        throw "The staged Windows service definition does not match the exact owned service contract."
    }
    if ((Get-FileHash -LiteralPath $StagedPayload.Wrapper -Algorithm SHA256).Hash -ne $WinSwSha256) {
        throw "The staged WinSW wrapper hash does not match the pinned release."
    }

    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.contractVersion -ne 1 -or [string]$manifest.bundleId -ne [string]$StagedPayload.BundleId) {
        throw "The staged bundle manifest is invalid."
    }
}

function New-BridgeStagedPayload {
    param(
        [string]$ResolvedConfigPath,
        [string]$ResolvedPortRegistryPath,
        [string]$ServiceDefinition,
        [string]$AccountSid,
        [string]$AccountName,
        [bool]$LogOnRightPreexisting,
        [bool]$LogOnRightGrantedByTsw
    )

    $stagingRoot = Join-Path $ServiceRoot ".staging-$([guid]::NewGuid().ToString('N'))"
    $stagedBundleRoot = Join-Path $stagingRoot "bundle"
    $stagedWrapperPath = Join-Path $stagingRoot "$ServiceName.exe"
    $stagedDefinitionPath = Join-Path $stagingRoot "$ServiceName.xml"
    $stagedInstallationManifestPath = Join-Path $stagingRoot "installation-manifest.json"
    try {
        New-Item -ItemType Directory -Path $stagedBundleRoot -Force | Out-Null
        Set-BridgeExactAcl -Path $stagingRoot
        Set-BridgeExactAcl -Path $stagedBundleRoot
        $bundleFiles = @(
            [pscustomobject]@{ Source = $BridgeScriptSourcePath; Destination = (Join-Path $stagedBundleRoot "tws-wsl-bridge.ps1") },
            [pscustomobject]@{ Source = $ServiceRunnerPath; Destination = (Join-Path $stagedBundleRoot "tws-wsl-bridge-service.ps1") },
            [pscustomobject]@{ Source = $ResolvedConfigPath; Destination = (Join-Path $stagedBundleRoot "tws-wsl-bridge.config.json") },
            [pscustomobject]@{ Source = $ResolvedPortRegistryPath; Destination = (Join-Path $stagedBundleRoot "ports.yaml") }
        )
        $bundleHashes = [ordered]@{}
        foreach ($file in $bundleFiles) {
            Install-BridgeBundleFile -Source $file.Source -Destination $file.Destination
            $sourceHash = (Get-FileHash -LiteralPath $file.Source -Algorithm SHA256).Hash
            $stagedHash = (Get-FileHash -LiteralPath $file.Destination -Algorithm SHA256).Hash
            if ($sourceHash -ne $stagedHash) {
                throw "Staged bridge payload hash mismatch for $([IO.Path]::GetFileName($file.Destination))."
            }
            $bundleHashes[[IO.Path]::GetFileName($file.Destination)] = $stagedHash
        }

        $bundleId = Get-BridgeBundleId -Hashes $bundleHashes
        $bundleManifest = [ordered]@{
            contractVersion = 1
            bundleId        = $bundleId
            hashes          = $bundleHashes
        }
        Write-TextAtomically `
            -Path (Join-Path $stagedBundleRoot "bundle-manifest.json") `
            -Text (($bundleManifest | ConvertTo-Json -Depth 5) + [Environment]::NewLine)

        if (
            (Test-Path -LiteralPath $ServiceWrapperPath -PathType Leaf) -and
            (Get-FileHash -LiteralPath $ServiceWrapperPath -Algorithm SHA256).Hash -eq $WinSwSha256
        ) {
            Install-BridgeBundleFile -Source $ServiceWrapperPath -Destination $stagedWrapperPath
        } else {
            Invoke-WebRequest -UseBasicParsing -Uri $WinSwDownloadUri -OutFile $stagedWrapperPath
        }
        $wrapperHash = (Get-FileHash -LiteralPath $stagedWrapperPath -Algorithm SHA256).Hash
        if ($wrapperHash -ne $WinSwSha256) {
            throw "WinSW checksum mismatch. Expected $WinSwSha256, got $wrapperHash."
        }

        Write-TextAtomically -Path $stagedDefinitionPath -Text $ServiceDefinition
        Write-TextAtomically `
            -Path $stagedInstallationManifestPath `
            -Text (New-BridgeInstallationManifestText `
                -AccountSid $AccountSid `
                -AccountName $AccountName `
                -LogOnRightPreexisting $LogOnRightPreexisting `
                -LogOnRightGrantedByTsw $LogOnRightGrantedByTsw)
        $stagedPayload = [pscustomobject]@{
            Root                 = $stagingRoot
            Bundle               = $stagedBundleRoot
            Wrapper              = $stagedWrapperPath
            Definition           = $stagedDefinitionPath
            InstallationManifest = $stagedInstallationManifestPath
            BundleId             = $bundleId
        }
        Test-BridgeStagedPayload -StagedPayload $stagedPayload
        return $stagedPayload
    } catch {
        Remove-Item -LiteralPath $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue
        throw
    }
}

function Get-BridgePayloadFingerprint {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Reparse points are not valid bridge payload fingerprint inputs: $Path"
    }
    if (-not $item.PSIsContainer) {
        return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    }
    $hashes = [ordered]@{}
    $files = @(
        Get-BridgeTreeItemsNoFollow -Root $Path |
            Where-Object { -not $_.PSIsContainer } |
            Sort-Object FullName
    )
    foreach ($file in $files) {
        $relative = $file.FullName.Substring([IO.Path]::GetFullPath($Path).TrimEnd('\').Length + 1).Replace('\', '/')
        $hashes[$relative] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    }
    return Get-BridgeBundleId -Hashes $hashes
}

function New-BridgeTransactionItem {
    param(
        [string]$Active,
        [string]$Backup,
        [string]$Staged
    )

    return [pscustomobject]@{
        Active             = $Active
        Backup             = $Backup
        Staged             = $Staged
        OriginalExisted    = (Test-Path -LiteralPath $Active)
        OriginalFingerprint = Get-BridgePayloadFingerprint -Path $Active
        StagedFingerprint  = Get-BridgePayloadFingerprint -Path $Staged
        OriginalMoveIntent = $false
        OriginalMoved      = $false
        StagedMoveIntent   = $false
        StagedMoved        = $false
    }
}

function New-BridgePayloadTransaction {
    param(
        $StagedPayload,
        [bool]$ServiceRootExisted,
        [bool]$ServiceExisted,
        [bool]$ServiceWasRunning,
        [string]$PreviousBundleId = ""
    )

    $rollbackRoot = Join-Path $ServiceRoot ".rollback-$([guid]::NewGuid().ToString('N'))"
    return [pscustomobject]@{
        ContractVersion  = 1
        TransactionId    = [guid]::NewGuid().ToString("N")
        Phase            = "prepared"
        StagedPayload = $StagedPayload
        RollbackRoot  = $rollbackRoot
        ServiceRootExisted = $ServiceRootExisted
        ServiceExisted    = $ServiceExisted
        ServiceWasRunning = $ServiceWasRunning
        ServiceCreateIntent = $false
        ServiceCreated      = $false
        PreviousBundleId  = $PreviousBundleId
        Items         = @(
            (New-BridgeTransactionItem -Active $ServiceBundleRoot -Backup (Join-Path $rollbackRoot "bundle") -Staged $StagedPayload.Bundle),
            (New-BridgeTransactionItem -Active $ServiceWrapperPath -Backup (Join-Path $rollbackRoot "$ServiceName.exe") -Staged $StagedPayload.Wrapper),
            (New-BridgeTransactionItem -Active $ServiceDefinitionPath -Backup (Join-Path $rollbackRoot "$ServiceName.xml") -Staged $StagedPayload.Definition),
            (New-BridgeTransactionItem -Active $InstallationManifestPath -Backup (Join-Path $rollbackRoot "installation-manifest.json") -Staged $StagedPayload.InstallationManifest)
        )
    }
}

function Write-BridgeTransactionJournal {
    param($Transaction)

    $journal = [ordered]@{
        contractVersion   = $Transaction.ContractVersion
        transactionId     = $Transaction.TransactionId
        phase             = $Transaction.Phase
        stagingRoot       = $Transaction.StagedPayload.Root
        rollbackRoot      = $Transaction.RollbackRoot
        expectedBundleId  = $Transaction.StagedPayload.BundleId
        previousBundleId  = $Transaction.PreviousBundleId
        serviceRootExisted = $Transaction.ServiceRootExisted
        serviceExisted    = $Transaction.ServiceExisted
        serviceWasRunning = $Transaction.ServiceWasRunning
        serviceCreateIntent = $Transaction.ServiceCreateIntent
        serviceCreated      = $Transaction.ServiceCreated
        items              = @($Transaction.Items | ForEach-Object {
            [ordered]@{
                active             = $_.Active
                backup             = $_.Backup
                staged             = $_.Staged
                originalExisted    = $_.OriginalExisted
                originalFingerprint = $_.OriginalFingerprint
                stagedFingerprint  = $_.StagedFingerprint
                originalMoveIntent = $_.OriginalMoveIntent
                originalMoved      = $_.OriginalMoved
                stagedMoveIntent   = $_.StagedMoveIntent
                stagedMoved        = $_.StagedMoved
            }
        })
    }
    Write-TextAtomically `
        -Path $TransactionJournalPath `
        -Text (($journal | ConvertTo-Json -Depth 6) + [Environment]::NewLine)
}

function Switch-BridgePayload {
    param($Transaction)

    $Transaction.Phase = "switching"
    Write-BridgeTransactionJournal -Transaction $Transaction
    New-Item -ItemType Directory -Path $Transaction.RollbackRoot -Force | Out-Null
    Set-BridgeExactAcl -Path $Transaction.RollbackRoot
    foreach ($item in $Transaction.Items) {
        if (Test-Path -LiteralPath $item.Active) {
            $item.OriginalMoveIntent = $true
            Write-BridgeTransactionJournal -Transaction $Transaction
            Move-Item -LiteralPath $item.Active -Destination $item.Backup
            $item.OriginalMoved = $true
            Write-BridgeTransactionJournal -Transaction $Transaction
        }
    }
    foreach ($item in $Transaction.Items) {
        $item.StagedMoveIntent = $true
        Write-BridgeTransactionJournal -Transaction $Transaction
        Move-Item -LiteralPath $item.Staged -Destination $item.Active
        $item.StagedMoved = $true
        Write-BridgeTransactionJournal -Transaction $Transaction
    }
    $Transaction.Phase = "activated"
    Write-BridgeTransactionJournal -Transaction $Transaction
}

function Restore-BridgePayload {
    param($Transaction)

    $Transaction.Phase = "rolling_back"
    Write-BridgeTransactionJournal -Transaction $Transaction
    foreach ($item in @($Transaction.Items)[($Transaction.Items.Count - 1)..0]) {
        $activeIsOriginal = $false
        if (Test-Path -LiteralPath $item.Active) {
            $activeFingerprint = Get-BridgePayloadFingerprint -Path $item.Active
            if (
                $item.OriginalExisted -and
                $activeFingerprint -eq $item.OriginalFingerprint
            ) {
                $activeIsOriginal = $true
            } elseif ($activeFingerprint -eq $item.StagedFingerprint) {
                Remove-Item -LiteralPath $item.Active -Recurse -Force
            } else {
                throw "Rollback refused an unrecognized active bridge payload: $($item.Active)"
            }
        }
        if (
            $item.OriginalExisted -and
            -not $activeIsOriginal -and
            -not (Test-Path -LiteralPath $item.Backup)
        ) {
            $activeIsOriginal = Restore-BridgePinnedWrapperForRecovery -Item $item
            if (-not $activeIsOriginal) {
                throw "Rollback requires a missing previous bridge payload backup: $($item.Backup)"
            }
        }
        if (
            -not $activeIsOriginal -and
            ($item.OriginalMoved -or $item.OriginalMoveIntent) -and
            (Test-Path -LiteralPath $item.Backup)
        ) {
            $backupFingerprint = Get-BridgePayloadFingerprint -Path $item.Backup
            if ($backupFingerprint -ne $item.OriginalFingerprint) {
                throw "Rollback backup fingerprint mismatch: $($item.Backup)"
            }
            if (Test-Path -LiteralPath $item.Active) {
                throw "Rollback refused to overwrite an already restored bridge payload: $($item.Active)"
            }
            Move-Item -LiteralPath $item.Backup -Destination $item.Active
        }
        $item.StagedMoved = $false
        $item.StagedMoveIntent = $false
        $item.OriginalMoved = $false
        $item.OriginalMoveIntent = $false
        Write-BridgeTransactionJournal -Transaction $Transaction
    }
}

function Restore-BridgePinnedWrapperForRecovery {
    param($Item)

    $isPinnedEquivalentWrapper = (
        [StringComparer]::OrdinalIgnoreCase.Equals(
            [IO.Path]::GetFullPath([string]$Item.Active),
            [IO.Path]::GetFullPath($ServiceWrapperPath)
        ) -and
        [bool]$Item.OriginalExisted -and
        [string]$Item.OriginalFingerprint -eq $WinSwSha256 -and
        [string]$Item.StagedFingerprint -eq $WinSwSha256 -and
        -not (Test-Path -LiteralPath $Item.Active) -and
        -not (Test-Path -LiteralPath $Item.Backup)
    )
    if (-not $isPinnedEquivalentWrapper) {
        return $false
    }

    $temporaryPath = Join-Path $ServiceRoot ".wrapper-recovery-$([guid]::NewGuid().ToString('N')).exe"
    Assert-BridgePayloadPathSafety -Path $temporaryPath
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $WinSwDownloadUri -OutFile $temporaryPath
        $downloadedHash = (Get-FileHash -LiteralPath $temporaryPath -Algorithm SHA256).Hash
        if ($downloadedHash -ne $WinSwSha256) {
            throw "WinSW recovery checksum mismatch. Expected $WinSwSha256, got $downloadedHash."
        }
        Move-Item -LiteralPath $temporaryPath -Destination $Item.Active
        Set-BridgeExactAcl -Path $Item.Active
        if ((Get-BridgePayloadFingerprint -Path $Item.Active) -ne $Item.OriginalFingerprint) {
            throw "The reconstructed pinned WinSW wrapper did not match the previous fingerprint."
        }
        return $true
    } finally {
        Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
    }
}

function Complete-BridgePayloadTransaction {
    param($Transaction)

    $Transaction.Phase = "committed"
    Write-BridgeTransactionJournal -Transaction $Transaction
    Remove-Item -LiteralPath $Transaction.StagedPayload.Root -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $Transaction.RollbackRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $TransactionJournalPath -Force -ErrorAction SilentlyContinue
}

function Complete-BridgePayloadRollback {
    param($Transaction)

    $Transaction.Phase = "rolled_back"
    Write-BridgeTransactionJournal -Transaction $Transaction
    Remove-Item -LiteralPath $Transaction.StagedPayload.Root -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $Transaction.RollbackRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $TransactionJournalPath -Force -ErrorAction SilentlyContinue
    if (-not $Transaction.ServiceRootExisted -and -not $Transaction.ServiceExisted) {
        Remove-Item -LiteralPath $ServiceRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Read-BridgeTransactionJournal {
    if (-not (Test-Path -LiteralPath $TransactionJournalPath -PathType Leaf)) {
        return $null
    }
    Assert-BridgeServicePathSafety
    if (-not (Test-BridgeServiceAclHardened)) {
        throw "The protected bridge upgrade journal root ACL is not trusted."
    }
    Assert-BridgePayloadPathSafety -Path $TransactionJournalPath
    try {
        $journal = Get-Content -LiteralPath $TransactionJournalPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        throw "The protected bridge upgrade journal is invalid; automatic recovery was refused."
    }
    if (
        $journal.contractVersion -ne 1 -or
        [string]$journal.transactionId -notmatch '^[a-f0-9]{32}$' -or
        [string]$journal.phase -notin @("prepared", "switching", "activated", "committed", "rolling_back", "rolled_back")
    ) {
        throw "The protected bridge upgrade journal contract is invalid."
    }
    $stagingRoot = [string]$journal.stagingRoot
    $rollbackRoot = [string]$journal.rollbackRoot
    foreach ($path in @($stagingRoot, $rollbackRoot)) {
        if (-not (Test-PathInsideBridgeServiceRoot -Path $path)) {
            throw "The protected bridge upgrade journal contains an unsafe path."
        }
        if (Test-Path -LiteralPath $path) {
            Assert-BridgePayloadPathSafety -Path $path
        }
    }

    $expectedActivePaths = [System.Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    foreach ($path in @($ServiceBundleRoot, $ServiceWrapperPath, $ServiceDefinitionPath, $InstallationManifestPath)) {
        [void]$expectedActivePaths.Add([IO.Path]::GetFullPath($path))
    }
    $items = @()
    foreach ($item in (Convert-ToArray $journal.items)) {
        $active = [IO.Path]::GetFullPath([string]$item.active)
        $backup = [IO.Path]::GetFullPath([string]$item.backup)
        $staged = [IO.Path]::GetFullPath([string]$item.staged)
        if (
            -not $expectedActivePaths.Remove($active) -or
            -not (Test-PathInsideBridgeServiceRoot -Path $backup) -or
            -not (Test-PathInsideBridgeServiceRoot -Path $staged)
        ) {
            throw "The protected bridge upgrade journal contains an unexpected payload path."
        }
        $items += [pscustomobject]@{
            Active              = $active
            Backup              = $backup
            Staged              = $staged
            OriginalExisted     = [bool]$item.originalExisted
            OriginalFingerprint = [string]$item.originalFingerprint
            StagedFingerprint   = [string]$item.stagedFingerprint
            OriginalMoveIntent  = [bool]$item.originalMoveIntent
            OriginalMoved       = [bool]$item.originalMoved
            StagedMoveIntent    = [bool]$item.stagedMoveIntent
            StagedMoved         = [bool]$item.stagedMoved
        }
    }
    if ($expectedActivePaths.Count -ne 0 -or $items.Count -ne 4) {
        throw "The protected bridge upgrade journal payload set is incomplete."
    }
    return [pscustomobject]@{
        ContractVersion = 1
        TransactionId   = [string]$journal.transactionId
        Phase           = [string]$journal.phase
        StagedPayload   = [pscustomobject]@{
            Root     = $stagingRoot
            BundleId = [string]$journal.expectedBundleId
        }
        RollbackRoot     = $rollbackRoot
        ServiceRootExisted = [bool]$journal.serviceRootExisted
        ServiceExisted    = [bool]$journal.serviceExisted
        ServiceWasRunning = [bool]$journal.serviceWasRunning
        ServiceCreateIntent = [bool]$journal.serviceCreateIntent
        ServiceCreated      = [bool]$journal.serviceCreated
        PreviousBundleId  = [string]$journal.previousBundleId
        Items              = $items
    }
}

function Recover-BridgeInterruptedTransaction {
    $transaction = Read-BridgeTransactionJournal
    if ($null -eq $transaction) {
        return
    }
    if ($transaction.Phase -in @("committed", "rolled_back")) {
        Remove-Item -LiteralPath $transaction.StagedPayload.Root -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $transaction.RollbackRoot -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $TransactionJournalPath -Force
        return
    }

    $ownership = Get-BridgeRecoveryServiceOwnership -Transaction $transaction
    if ($ownership.Status -eq "collision") {
        throw "Interrupted bridge upgrade recovery was refused because the service registration is not owned."
    }
    $reconcileMutex = Enter-BridgeMutex -Name "Global\TinySwarmWorldWslBridgeReconcile"
    try {
        if (
            -not $transaction.ServiceExisted -and
            ($transaction.ServiceCreateIntent -or $transaction.ServiceCreated) -and
            $null -ne $ownership.Service
        ) {
            Remove-BridgeServiceRegistrationWithOwnedRight
            $ownership = Get-BridgeRecoveryServiceOwnership -Transaction $transaction
        } else {
            Stop-BridgeServiceChecked -Service $ownership.Service
        }
        Undo-BridgeTransactionOwnedLogOnRight -Transaction $transaction
        Restore-BridgePayload -Transaction $transaction
        Protect-BridgeServiceRoot
    } finally {
        Exit-BridgeMutex -Mutex $reconcileMutex
    }
    if ($transaction.ServiceWasRunning -and $null -ne $ownership.Service) {
        $restoredOwnership = Get-BridgeServiceOwnership
        if ($restoredOwnership.Status -ne "owned") {
            throw "Recovered bridge payload did not restore full service ownership."
        }
        $rollbackStartedAt = [DateTimeOffset]::Now
        Start-BridgeServiceRollbackChecked `
            -ExpectedBundleId $transaction.PreviousBundleId
        Wait-BridgeServiceHeartbeat `
            -TransitionStartedAt $rollbackStartedAt `
            -ExpectedBundleId $transaction.PreviousBundleId
    }
    Complete-BridgePayloadRollback -Transaction $transaction
    Write-Host "SERVICE recovered an interrupted bridge payload transaction."
}

function Wait-BridgeServiceHeartbeat {
    param(
        [DateTimeOffset]$TransitionStartedAt,
        [string]$ExpectedBundleId = "",
        [int]$TimeoutSeconds = 45
    )

    $deadline = [DateTimeOffset]::Now.AddSeconds($TimeoutSeconds)
    while ([DateTimeOffset]::Now -lt $deadline) {
        if (Test-Path -LiteralPath $StatePath -PathType Leaf) {
            try {
                $state = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
                $generatedAt = [DateTimeOffset]::Parse([string]$state.generatedAt)
                $configMatches = [StringComparer]::OrdinalIgnoreCase.Equals(
                    [IO.Path]::GetFullPath([string]$state.configPath),
                    [IO.Path]::GetFullPath($InstalledConfigPath)
                )
                $registryMatches = [StringComparer]::OrdinalIgnoreCase.Equals(
                    [IO.Path]::GetFullPath([string]$state.registryPath),
                    [IO.Path]::GetFullPath($InstalledPortRegistryPath)
                )
                if (
                    $generatedAt -gt $TransitionStartedAt -and
                    [string]$state.agentMode -eq "windows-service" -and
                    [string]$state.agentStatus -eq "ready" -and
                    (
                        [string]::IsNullOrWhiteSpace($ExpectedBundleId) -or
                        [string]$state.bundleId -eq $ExpectedBundleId
                    ) -and
                    $configMatches -and
                    $registryMatches
                ) {
                    return
                }
            } catch {
                # The service writes atomically, but tolerate a transient read during startup.
            }
        }
        Start-Sleep -Milliseconds 500
    }
    throw "Windows service $ServiceName did not publish a fresh ready heartbeat within $TimeoutSeconds seconds."
}

function Install-BridgeService {
    param(
        [string]$ResolvedConfigPath,
        [string]$ResolvedPortRegistryPath,
        $Config
    )

    Assert-Administrator
    if (-not (Test-Path -LiteralPath $ServiceRunnerPath -PathType Leaf)) {
        throw "Missing Windows service runner: $ServiceRunnerPath"
    }
    if (-not (Test-Path -LiteralPath $ResolvedPortRegistryPath -PathType Leaf)) {
        throw "Missing port registry: $ResolvedPortRegistryPath"
    }

    $intervalMinutes = Get-DiscoveryIntervalMinutes $Config
    $serviceXml = New-BridgeServiceDefinition -IntervalMinutes $intervalMinutes
    $expectedAccount = Get-CurrentBridgeServiceAccount
    if (Test-Path -LiteralPath $TransactionJournalPath -PathType Leaf) {
        Recover-BridgeInterruptedTransaction
    }
    $serviceRootExisted = Test-Path -LiteralPath $ServiceRoot -PathType Container
    $ownership = Get-BridgeServiceOwnership -AllowAclMigration
    if ($ownership.Status -eq "collision") {
        throw "Existing Windows service registration is not owned by this installation. Automatic replacement was refused; inspect it and run an explicit uninstall before reinstalling."
    }
    if (
        $ownership.PSObject.Properties.Name -contains "RequiresAclMigration" -and
        [bool]$ownership.RequiresAclMigration
    ) {
        $aclMigrationMutex = Enter-BridgeMutex -Name "Global\TinySwarmWorldWslBridgeReconcile"
        try {
            Protect-BridgeServiceRoot
        } finally {
            Exit-BridgeMutex -Mutex $aclMigrationMutex
        }
        $ownership = Get-BridgeServiceOwnership
        if ($ownership.Status -eq "collision") {
            throw "The Windows bridge ACL migration completed, but full service ownership validation failed."
        }
    }
    $service = $ownership.Service

    $accountSid = Get-BridgeAccountSidValue -AccountName $expectedAccount
    if (
        $ownership.PSObject.Properties.Name -contains "AccountSid" -and
        -not [string]::IsNullOrWhiteSpace([string]$ownership.AccountSid) -and
        [string]$ownership.AccountSid -ne $accountSid
    ) {
        throw "The orphaned Windows bridge installation belongs to a different service account SID. Automatic account migration was refused."
    }
    $credential = $null
    if ($null -eq $service) {
        $credential = Request-BridgeServiceCredential -ExpectedAccount $expectedAccount
    }
    $logOnRightCurrentlyPresent = Test-BridgeServiceLogOnRight -AccountName $expectedAccount
    $existingManifest = Get-BridgeInstallationManifest
    $existingManifestMatchesAccount = $false
    if ($null -ne $existingManifest) {
        $hasManifestAccount = (
            $existingManifest.PSObject.Properties.Name -contains "accountSid" -and
            $existingManifest.PSObject.Properties.Name -contains "serviceAccount"
        )
        if ($hasManifestAccount) {
            try {
                $existingManifestMatchesAccount = (
                    [string]$existingManifest.accountSid -eq $accountSid -and
                    (Get-BridgeAccountSidValue `
                        -AccountName ([string]$existingManifest.serviceAccount)) -eq $accountSid
                )
            } catch {
                $existingManifestMatchesAccount = $false
            }
        }
        if (-not $ownership.RequiresAdoption -and -not $existingManifestMatchesAccount) {
            throw "The protected Windows bridge manifest does not belong to the target service account SID."
        }
    }
    $preserveExistingProvenance = (
        $null -ne $existingManifest -and
        -not $ownership.RequiresAdoption -and
        $existingManifestMatchesAccount -and
        ($null -ne $service -or $logOnRightCurrentlyPresent)
    )
    if ($preserveExistingProvenance) {
        $logOnRightPreexisting = [bool]$existingManifest.logOnRightPreexisting
        $logOnRightGrantedByTsw = [bool]$existingManifest.logOnRightGrantedByTsw
    } else {
        $logOnRightPreexisting = $logOnRightCurrentlyPresent
        $logOnRightGrantedByTsw = -not $logOnRightCurrentlyPresent
    }
    if ($null -ne $service -and -not $logOnRightCurrentlyPresent) {
        throw "The owned Windows service account no longer has SeServiceLogonRight; automatic credential or policy repair was refused."
    }
    Protect-BridgeServiceRoot
    $stagedPayload = New-BridgeStagedPayload `
        -ResolvedConfigPath $ResolvedConfigPath `
        -ResolvedPortRegistryPath $ResolvedPortRegistryPath `
        -ServiceDefinition $serviceXml `
        -AccountSid $accountSid `
        -AccountName $expectedAccount `
        -LogOnRightPreexisting $logOnRightPreexisting `
        -LogOnRightGrantedByTsw $logOnRightGrantedByTsw
    $serviceWasRunning = $null -ne $service -and $service.Status -ne "Stopped"
    $previousBundleId = Get-InstalledBridgeBundleIdOrEmpty
    $transaction = New-BridgePayloadTransaction `
        -StagedPayload $stagedPayload `
        -ServiceRootExisted $serviceRootExisted `
        -ServiceExisted ($null -ne $service) `
        -ServiceWasRunning $serviceWasRunning `
        -PreviousBundleId $previousBundleId
    Write-BridgeTransactionJournal -Transaction $transaction
    $transactionFinalized = $false
    try {
        $reconcileMutex = Enter-BridgeMutex -Name "Global\TinySwarmWorldWslBridgeReconcile"
        try {
            Stop-BridgeServiceChecked -Service $service
            $transitionStartedAt = [DateTimeOffset]::Now
            Switch-BridgePayload -Transaction $transaction
            Protect-BridgeServiceRoot

            if ($null -eq $service) {
                $transaction.ServiceCreateIntent = $true
                Write-BridgeTransactionJournal -Transaction $transaction
                New-BridgeServiceRegistration `
                    -ExpectedAccount $expectedAccount `
                    -Credential $credential
                $transaction.ServiceCreated = $true
                Write-BridgeTransactionJournal -Transaction $transaction
                Set-BridgeServiceRuntimePolicy
            }
        } finally {
            Exit-BridgeMutex -Mutex $reconcileMutex
        }

        Start-BridgeServiceChecked
        Wait-BridgeServiceHeartbeat `
            -TransitionStartedAt $transitionStartedAt `
            -ExpectedBundleId $stagedPayload.BundleId
        Complete-BridgePayloadTransaction -Transaction $transaction
        $transactionFinalized = $true
    } catch {
        $upgradeError = $_
        $rollbackError = $null
        try {
            $rollbackMutex = Enter-BridgeMutex -Name "Global\TinySwarmWorldWslBridgeReconcile"
            try {
                if (
                    -not $transaction.ServiceExisted -and
                    ($transaction.ServiceCreateIntent -or $transaction.ServiceCreated) -and
                    $null -ne (Get-BridgeService)
                ) {
                    Remove-BridgeServiceRegistrationWithOwnedRight
                } else {
                    Stop-BridgeServiceChecked -Service (Get-BridgeService)
                }
                Undo-BridgeTransactionOwnedLogOnRight -Transaction $transaction
                Restore-BridgePayload -Transaction $transaction
                Protect-BridgeServiceRoot
            } finally {
                Exit-BridgeMutex -Mutex $rollbackMutex
            }
            if ($null -ne $service -and $serviceWasRunning) {
                $rollbackStartedAt = [DateTimeOffset]::Now
                Start-BridgeServiceRollbackChecked `
                    -ExpectedBundleId $previousBundleId
                Wait-BridgeServiceHeartbeat `
                    -TransitionStartedAt $rollbackStartedAt `
                    -ExpectedBundleId $previousBundleId
            }
            Complete-BridgePayloadRollback -Transaction $transaction
            $transactionFinalized = $true
        } catch {
            $rollbackError = $_.Exception.Message
        }
        if ($null -ne $rollbackError) {
            throw "Windows service upgrade failed: $($upgradeError.Exception.Message) Rollback also failed: $rollbackError"
        }
        throw $upgradeError
    } finally {
        if (-not $transactionFinalized) {
            # A failed rollback keeps its artifacts for administrator diagnosis.
        }
    }
    Unregister-BridgeTask
    Write-Host "SERVICE installed: $ServiceName (automatic, interval $intervalMinutes minute(s))"
}

function Remove-BridgeServiceRegistrationWithOwnedRight {
    $ownership = Get-BridgeServiceOwnership
    if ($ownership.Status -eq "collision") {
        throw "Windows service removal was refused because ownership is unresolved."
    }
    $manifest = Get-BridgeInstallationManifest
    $accountName = $(
        if ($null -ne $ownership.Details) { [string]$ownership.Details.StartName } else { "" }
    )
    Remove-BridgeServiceRegistration
    if (-not [string]::IsNullOrWhiteSpace($accountName)) {
        Undo-BridgeOwnedLogOnRight -Manifest $manifest -AccountName $accountName
    }
}

function Uninstall-BridgeService {
    Remove-BridgeServiceRegistrationWithOwnedRight
    if (Test-Path -LiteralPath $ServiceRoot -PathType Container) {
        Remove-Item -LiteralPath $ServiceRoot -Recurse -Force
    }
    Write-Host "SERVICE removed: $ServiceName"
}

function New-BridgeCleanupPlan {
    param($State)

    if ($null -eq $State) {
        return $null
    }

    if (
        $State.contractVersion -ne 2 -or
        [string]$State.serviceName -ne $ServiceName -or
        [string]$State.agentMode -ne "windows-service"
    ) {
        throw "The protected bridge state is not valid cleanup authority for this Windows service."
    }

    $listenAddress = [string]$State.listenAddress
    Assert-ValidIPv4Address -Value $listenAddress -Name "previous listenAddress"
    $connectAddress = [string]$State.wslIp
    Assert-ValidIPv4Address -Value $connectAddress -Name "previous wslIp"
    $ports = [System.Collections.Generic.HashSet[int]]::new()
    $connectPortsByListenPort = @{}
    $mappings = @()
    foreach ($mapping in (Convert-ToArray $State.mappings)) {
        $port = [int]$mapping.listenPort
        Assert-ValidTcpPort -Port $port -Name "previous listenPort"
        $connectPort = [int]$mapping.connectPort
        Assert-ValidTcpPort -Port $connectPort -Name "previous connectPort"
        if ($connectPortsByListenPort.ContainsKey($port)) {
            if ([int]$connectPortsByListenPort[$port] -ne $connectPort) {
                throw "The protected bridge state contains conflicting mappings for listen port $port."
            }
        } else {
            $connectPortsByListenPort[$port] = $connectPort
            [void]$ports.Add($port)
            $mappings += [pscustomobject]@{
                ListenAddress  = $listenAddress
                ListenPort     = $port
                ConnectAddress = $connectAddress
                ConnectPort    = $connectPort
            }
        }
    }

    $prefix = "Tiny Swarm World"
    if ($State.PSObject.Properties.Name -contains "firewallRulePrefix") {
        $prefix = [string]$State.firewallRulePrefix
    }
    Assert-ValidFirewallRulePrefix -Prefix $prefix
    $sortedPorts = @($ports | Sort-Object)
    return [pscustomobject]@{
        ListenAddress     = $listenAddress
        Mappings          = @($mappings | Sort-Object ListenPort)
        Ports             = $sortedPorts
        FirewallRuleNames = @($sortedPorts | ForEach-Object { "$prefix TCP $_" })
    }
}

function Get-ExactBridgeFirewallRules {
    param([string]$RuleName)

    try {
        return @(
            Get-NetFirewallRule -DisplayName $RuleName -ErrorAction Stop |
                Where-Object { [string]$_.DisplayName -ceq $RuleName }
        )
    } catch {
        if ([string]$_.FullyQualifiedErrorId -like "CmdletizationQuery_NotFound*") {
            return @()
        }
        throw
    }
}

function Invoke-BridgeCleanupPlan {
    param($Plan)

    if ($null -eq $Plan) {
        return
    }
    $records = @(Get-PortProxyRecords)
    foreach ($mapping in $Plan.Mappings) {
        $ownedRecord = @($records | Where-Object {
            $_.ListenAddress -eq $mapping.ListenAddress -and
            $_.ListenPort -eq $mapping.ListenPort -and
            $_.ConnectAddress -eq $mapping.ConnectAddress -and
            $_.ConnectPort -eq $mapping.ConnectPort
        })
        if ($ownedRecord.Count -eq 1) {
            Remove-PortProxy -ListenAddress $mapping.ListenAddress -ListenPort $mapping.ListenPort
            $remainingRecord = @(Get-PortProxyRecords | Where-Object {
                $_.ListenAddress -eq $mapping.ListenAddress -and
                $_.ListenPort -eq $mapping.ListenPort -and
                $_.ConnectAddress -eq $mapping.ConnectAddress -and
                $_.ConnectPort -eq $mapping.ConnectPort
            })
            if ($remainingRecord.Count -ne 0) {
                throw "Managed portproxy cleanup could not remove the exact previous tuple."
            }
            Write-Host ("PORTPROXY removed {0}:{1}" -f $mapping.ListenAddress, $mapping.ListenPort)
        }
    }
    foreach ($ruleName in $Plan.FirewallRuleNames) {
        $ownedRules = @(Get-ExactBridgeFirewallRules -RuleName $ruleName)
        if ($ownedRules.Count -gt 0) {
            $ownedRules | Remove-NetFirewallRule -ErrorAction Stop
        }
        $remainingRules = @(Get-ExactBridgeFirewallRules -RuleName $ruleName)
        if ($remainingRules.Count -ne 0) {
            throw "Managed Firewall cleanup could not remove exact rule: $ruleName"
        }
    }
    Write-Host "FIREWALL managed Tiny Swarm rules removed"
}

function Test-TcpPort {
    param(
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutMs
    )

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect($HostName, $Port, $null, $null)
        $ok = $async.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
        if ($ok) {
            $client.EndConnect($async)
            return $true
        }
        return $false
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Verify-Bridge {
    param(
        $Config,
        $Mappings
    )

    $failed = @()

    foreach ($m in $Mappings) {
        $ok = Test-TcpPort -HostName "127.0.0.1" -Port $m.ListenPort -TimeoutMs $ConnectTimeoutMs
        if ($ok) {
            Write-Host ("VERIFY OK   127.0.0.1:{0} ({1})" -f $m.ListenPort, $m.Name)
        } else {
            Write-Host ("VERIFY FAIL 127.0.0.1:{0} ({1})" -f $m.ListenPort, $m.Name) -ForegroundColor Yellow
            $failed += $m
        }
    }

    if ($failed.Count -gt 0) {
        throw "Windows bridge verification failed for $($failed.Count) port(s). This can also mean the Tiny Swarm services are not running yet."
    }
}

function Get-BridgeDiscovery {
    param(
        $Config,
        [string]$WslIp,
        $Mappings,
        $HostNames
    )

    $driftReasons = [System.Collections.ArrayList]::new()
    if (-not (Test-PortProxyMappingsReady -Config $Config -WslIp $WslIp -Mappings $Mappings)) {
        [void]$driftReasons.Add("portproxy_drift")
    }
    if (-not (Test-FirewallRulesReady -Config $Config -Mappings $Mappings)) {
        [void]$driftReasons.Add("firewall_drift")
    }
    if (-not (Test-HostsFileReady -Config $Config -HostNames $HostNames)) {
        [void]$driftReasons.Add("hosts_drift")
    }
    if (-not (Test-BridgeServiceReady)) {
        [void]$driftReasons.Add("bridge_agent_drift")
    }

    return [pscustomobject]@{
        Ready                    = $driftReasons.Count -eq 0
        WslIp                    = $WslIp
        DiscoveryIntervalMinutes = Get-DiscoveryIntervalMinutes $Config
        DriftReasons             = @($driftReasons)
    }
}

function Write-BridgeDiscovery {
    param($Discovery)

    $status = if ($Discovery.Ready) { "READY" } else { "DEGRADED" }
    $reasons = if ($Discovery.DriftReasons.Count -eq 0) { "none" } else { $Discovery.DriftReasons -join "," }
    Write-Host ("DISCOVERY {0} wslIp={1} intervalMinutes={2} drift={3}" -f $status, $Discovery.WslIp, $Discovery.DiscoveryIntervalMinutes, $reasons)
}

function Enter-BridgeMutex {
    param(
        [string]$Name,
        [TimeSpan]$Timeout = ([TimeSpan]::FromMinutes(2))
    )

    $mutex = New-Object Threading.Mutex($false, $Name)
    try {
        Wait-BridgeMutex -Mutex $mutex -Name $Name -Timeout $Timeout
        return $mutex
    } catch {
        $mutex.Dispose()
        throw
    }
}

function Wait-BridgeMutex {
    param(
        $Mutex,
        [string]$Name,
        [TimeSpan]$Timeout
    )

    $lockTaken = $false
    try {
        $lockTaken = $Mutex.WaitOne($Timeout)
    } catch [Threading.AbandonedMutexException] {
        $lockTaken = $true
    }
    if (-not $lockTaken) {
        throw "Timed out waiting for the Windows/WSL bridge lock: $Name"
    }
}

function Exit-BridgeMutex {
    param($Mutex)

    if ($null -eq $Mutex) {
        return
    }
    try {
        $Mutex.ReleaseMutex()
    } finally {
        $Mutex.Dispose()
    }
}

function Invoke-BridgeReconcile {
    param(
        $Config,
        $Mappings,
        $HostNames,
        [string]$RegistryPath
    )

    $mutex = Enter-BridgeMutex -Name "Global\TinySwarmWorldWslBridgeReconcile"
    try {
        Assert-BridgeRuntimeStateAuthority

        $wslIp = Get-WslIp $Config
        $pendingDiscovery = [pscustomobject]@{
            Ready                    = $false
            WslIp                    = $wslIp
            DiscoveryIntervalMinutes = Get-DiscoveryIntervalMinutes $Config
            DriftReasons             = @("reconcile_in_progress")
        }
        Write-StateFile `
            -Config $Config `
            -WslIp $wslIp `
            -Mappings $Mappings `
            -HostNames $HostNames `
            -RegistryPath $RegistryPath `
            -Discovery $pendingDiscovery
        Reconcile-PortProxy -Config $Config -WslIp $wslIp -Mappings $Mappings
        Reconcile-FirewallRules -Config $Config -Mappings $Mappings
        Reconcile-HostsFile -Config $Config -HostNames $HostNames
        $discovery = Get-BridgeDiscovery -Config $Config -WslIp $wslIp -Mappings $Mappings -HostNames $HostNames
        Write-StateFile `
            -Config $Config `
            -WslIp $wslIp `
            -Mappings $Mappings `
            -HostNames $HostNames `
            -RegistryPath $RegistryPath `
            -Discovery $discovery
        Write-BridgeDiscovery -Discovery $discovery
        if (-not $discovery.Ready) {
            throw "Windows/WSL bridge reconcile finished with drift: $($discovery.DriftReasons -join ', ')"
        }
    } finally {
        Exit-BridgeMutex -Mutex $mutex
    }
}

function Get-BridgeBundleIdentity {
    if (-not (Test-Path -LiteralPath $InstalledBundleManifestPath -PathType Leaf)) {
        throw "The installed Windows bridge bundle manifest is missing."
    }
    $manifest = Get-Content -LiteralPath $InstalledBundleManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.contractVersion -ne 1 -or $null -eq $manifest.hashes) {
        throw "The installed Windows bridge bundle manifest is invalid."
    }
    $verifiedHashes = [ordered]@{}
    foreach ($property in @($manifest.hashes.PSObject.Properties | Sort-Object Name)) {
        $fileName = [string]$property.Name
        if ($fileName -notmatch '^[A-Za-z0-9._-]+$') {
            throw "The installed bundle manifest contains an invalid file name."
        }
        $path = Join-Path $ServiceBundleRoot $fileName
        Assert-BridgePayloadPathSafety -Path $path
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Installed bridge bundle file is missing: $fileName"
        }
        $actualHash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
        if ($actualHash -ne [string]$property.Value) {
            throw "Installed bridge bundle hash mismatch: $fileName"
        }
        $verifiedHashes[$fileName] = $actualHash
    }
    $bundleId = Get-BridgeBundleId -Hashes $verifiedHashes
    if ($bundleId -ne [string]$manifest.bundleId) {
        throw "Installed bridge bundle identity does not match its manifest."
    }
    return [pscustomobject]@{
        BundleId = $bundleId
        Hashes   = $verifiedHashes
    }
}

function Get-InstalledBridgeBundleIdOrEmpty {
    try {
        return [string](Get-BridgeBundleIdentity).BundleId
    } catch {
        return ""
    }
}

function Write-StateFile {
    param(
        $Config,
        [string]$WslIp,
        $Mappings,
        $HostNames,
        [string]$RegistryPath,
        $Discovery
    )

    Assert-BridgeRuntimeStateAuthority
    $bundleIdentity = Get-BridgeBundleIdentity
    $state = [ordered]@{
        contractVersion    = 2
        agentMode          = Get-BridgeAgentMode
        agentStatus        = $(if ($Discovery.Ready) { "ready" } else { "degraded" })
        generatedAt        = (Get-Date).ToString("o")
        action             = $Action
        wslIp              = $WslIp
        serviceName        = $ServiceName
        discoveryIntervalMinutes = $Discovery.DiscoveryIntervalMinutes
        driftReasons       = @($Discovery.DriftReasons)
        listenAddress      = (Get-ListenAddress $Config)
        hostsAddress       = (Get-HostsAddress $Config)
        firewallRulePrefix = (Get-FirewallRulePrefix $Config)
        configPath         = (Resolve-Path -LiteralPath $ConfigPath).Path
        registryPath       = $RegistryPath
        bundleId           = $bundleIdentity.BundleId
        bundleHashes       = $bundleIdentity.Hashes
        hostNames          = @($HostNames)
        mappings           = @($Mappings | ForEach-Object {
            [ordered]@{
                name        = $_.Name
                listenPort  = $_.ListenPort
                connectPort = $_.ConnectPort
            }
        })
    }

    $stateJson = $state | ConvertTo-Json -Depth 6
    Write-TextAtomically -Path $StatePath -Text ($stateJson + [Environment]::NewLine)
    Write-Host "STATE written: $StatePath"
}

function Show-Status {
    param(
        $Config,
        $Mappings,
        $HostNames
    )

    Write-Host "Tiny Swarm World Windows <-> WSL bridge status"
    Write-Host ("Config: {0}" -f (Resolve-Path -LiteralPath $ConfigPath).Path)
    Write-Host ("Ports: {0}" -f (($Mappings | Select-Object -ExpandProperty ListenPort) -join ", "))
    Write-Host ("Hosts: {0}" -f ($HostNames -join ", "))

    $wslIp = ""
    try {
        $wslIp = Get-WslIp $Config
        Write-Host ("WSL IP: {0}" -f $wslIp)
    } catch {
        Write-Host ("WSL IP: unavailable - {0}" -f $_.Exception.Message) -ForegroundColor Yellow
    }

    if (-not [string]::IsNullOrWhiteSpace($wslIp)) {
        try {
            $discovery = Get-BridgeDiscovery -Config $Config -WslIp $wslIp -Mappings $Mappings -HostNames $HostNames
            Write-BridgeDiscovery -Discovery $discovery
        } catch {
            Write-Host ("DISCOVERY unavailable - {0}" -f $_.Exception.Message) -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "Portproxy:"
    & netsh interface portproxy show v4tov4

    Write-Host ""
    Write-Host "Windows service:"
    Get-Service -Name $ServiceName -ErrorAction SilentlyContinue | Format-List Name, DisplayName, Status, StartType

    Write-Host ""
    Write-Host "Legacy scheduled task:"
    if ($null -ne (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue)) {
        Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Format-List TaskName, State, TaskPath
    } else {
        Write-Host "Scheduled Task cmdlets unavailable; no new task is registered by this version."
    }

    Write-Host ""
    Write-Host "Managed hosts block present:"
    if ((Test-Path -LiteralPath $HostsPath) -and ((Get-Content -LiteralPath $HostsPath -Raw) -like "*$HostsStart*")) {
        Write-Host "yes"
    } else {
        Write-Host "no"
    }
}

function Invoke-BridgeAction {
    if ($Action -eq "uninstall") {
        Assert-Administrator
        $updateMutex = Enter-BridgeMutex -Name "Global\TinySwarmWorldWslBridgeServiceUpdate"
        try {
            if (Test-Path -LiteralPath $TransactionJournalPath -PathType Leaf) {
                Recover-BridgeInterruptedTransaction
            }
            $ownership = Get-BridgeServiceOwnership
            if ($ownership.Status -eq "collision") {
                throw "Uninstall was refused because the Windows service registration or protected root is not owned by Tiny Swarm World."
            }
            $installationPresent = $ownership.Status -eq "owned"
            $protectedState = Get-ProtectedBridgeState
            if ($installationPresent -and $null -eq $protectedState) {
                throw "Protected cleanup authority is missing; uninstall was refused before changing service, portproxy, Firewall, or hosts state."
            }
            $cleanupPlan = New-BridgeCleanupPlan -State $protectedState
            $reconcileMutex = Enter-BridgeMutex -Name "Global\TinySwarmWorldWslBridgeReconcile"
            try {
                Stop-BridgeServiceChecked -Service $ownership.Service
                Unregister-BridgeTask
                Invoke-BridgeCleanupPlan -Plan $cleanupPlan
                Remove-HostsFileBlock
                Uninstall-BridgeService
            } finally {
                Exit-BridgeMutex -Mutex $reconcileMutex
            }
            Write-Host "Uninstalled."
        } finally {
            Exit-BridgeMutex -Mutex $updateMutex
        }
        return
    }

    $config = Read-BridgeConfig -Path $ConfigPath
    $registryPath = $(
        if ([string]::IsNullOrWhiteSpace($PortRegistryPath)) {
            Join-Path (Get-TswRepositoryRoot) "infra\config\ports.yaml"
        } else {
            (Resolve-Path -LiteralPath $PortRegistryPath).Path
        }
    )
    $registry = Read-TswPortRegistry -RegistryPath $registryPath
    $mappings = @(Get-PortMappings $config $registry.Mappings)
    $hostNames = @(Get-BridgeHostNames $config $registry.HostNames)

    switch ($Action) {
        "prerequisites" {
            Assert-BridgePrerequisites -Config $config
            Write-Host "Windows/WSL bridge prerequisites are ready. No bridge state was changed."
        }

        "discover" {
            Assert-BridgePrerequisites -Config $config
            $wslIp = Get-WslIp $config
            $discovery = Get-BridgeDiscovery -Config $config -WslIp $wslIp -Mappings $mappings -HostNames $hostNames
            Write-BridgeDiscovery -Discovery $discovery
            $discovery | ConvertTo-Json -Depth 4
            if (-not $discovery.Ready) {
                throw "Windows/WSL bridge discovery found drift: $($discovery.DriftReasons -join ', ')"
            }
        }

        "install" {
            Assert-BridgePrerequisites -Config $config
            $resolvedConfig = (Resolve-Path -LiteralPath $ConfigPath).Path
            $updateMutex = Enter-BridgeMutex -Name "Global\TinySwarmWorldWslBridgeServiceUpdate"
            try {
                Install-BridgeService `
                    -ResolvedConfigPath $resolvedConfig `
                    -ResolvedPortRegistryPath $registryPath `
                    -Config $config
            } finally {
                Exit-BridgeMutex -Mutex $updateMutex
            }
            Write-Host ""
            Write-Host "Installed. Discovery/reconcile now runs as Windows service. Trigger a restart with:"
            Write-Host "  Restart-Service -Name $ServiceName"
        }

        "reconcile" {
            Assert-BridgePrerequisites -Config $config
            Invoke-BridgeReconcile -Config $config -Mappings $mappings -HostNames $hostNames -RegistryPath $registryPath
            Write-Host "Reconcile completed."
        }

        "refresh" {
            Assert-BridgePrerequisites -Config $config
            Invoke-BridgeReconcile -Config $config -Mappings $mappings -HostNames $hostNames -RegistryPath $registryPath
            Write-Host "Reconcile completed."
        }

        "verify" {
            Verify-Bridge -Config $config -Mappings $mappings
        }

        "status" {
            Show-Status -Config $config -Mappings $mappings -HostNames $hostNames
        }
    }
}

if ($MyInvocation.InvocationName -ne ".") {
    Invoke-BridgeAction
}
