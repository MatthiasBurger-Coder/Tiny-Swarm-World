# Dependency-light verification of release assets against an independently chosen Git SHA.
# Commit membership/integrity does not authenticate the publisher or authorize mutation.
function Get-PreparationGitObjectId {
    param([string]$Type, [byte[]]$Content)
    $header = [Text.Encoding]::ASCII.GetBytes($Type + ' ' + $Content.Length + [char]0)
    $algorithm = [Security.Cryptography.SHA1]::Create()
    try {
        return ([BitConverter]::ToString($algorithm.ComputeHash($header + $Content))).Replace('-', '').ToLowerInvariant()
    } finally { $algorithm.Dispose() }
}

function Read-PreparationGitTree {
    param([byte[]]$Content)
    $entries = New-Object 'Collections.Generic.Dictionary[string,object]' ([StringComparer]::Ordinal)
    $decoder = New-Object Text.UTF8Encoding($false, $true)
    $offset = 0
    while ($offset -lt $Content.Length) {
        if ($entries.Count -ge 4096) { throw 'proof_tree_entries_exceeded' }
        $space = $offset
        while ($space -lt $Content.Length -and $Content[$space] -ne 32) { $space++ }
        $nul = $space + 1
        while ($nul -lt $Content.Length -and $Content[$nul] -ne 0) { $nul++ }
        if ($space -eq $offset -or $space -ge $Content.Length -or $nul + 21 -gt $Content.Length) { throw 'proof_malformed_tree' }
        $mode = [Text.Encoding]::ASCII.GetString($Content, $offset, $space - $offset)
        $name = $decoder.GetString($Content, $space + 1, $nul - $space - 1)
        if ($mode -notmatch '^[0-7]{5,6}$' -or !$name -or $name -in @('.', '..') -or $name -match '[/\\\x00-\x1f]' -or $entries.ContainsKey($name)) { throw 'proof_unsafe_tree_entry' }
        $id = ([BitConverter]::ToString($Content, $nul + 1, 20)).Replace('-', '').ToLowerInvariant()
        $entries.Add($name, @{mode = $mode; id = $id})
        $offset = $nul + 21
    }
    return ,$entries
}

function Test-PreparationReleaseProof {
    param([string]$RepositoryRoot, [string[]]$Assets, [string]$ExpectedRevision)
    $result = @{verified = $false; clean = $false; revision = $null; assets = @{}; cause = 'release_proof_unverified'}
    try {
        if ($ExpectedRevision -cnotmatch '^[0-9a-f]{40}$' -or $Assets.Count -eq 0 -or $Assets.Count -gt 32) { return $result }
        $root = [IO.Path]::GetFullPath($RepositoryRoot)
        $manifestPath = Join-Path $root 'tools/windows/preparation/release-manifest.json'
        $manifestFile = Get-Item -LiteralPath $manifestPath -ErrorAction Stop
        if ($manifestFile.Length -gt 8388608 -or ($manifestFile.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'proof_manifest_unsafe' }
        $text = [IO.File]::ReadAllText($manifestPath)
        $manifest = $text | ConvertFrom-Json -ErrorAction Stop
        $propertyNames = @($manifest.PSObject.Properties.Name)
        if ($propertyNames.Count -ne 4 -or @($propertyNames | Where-Object { $_ -notin @('schema_version','revision','commit','trees') }).Count) { throw 'proof_manifest_shape' }
        foreach ($property in @('schema_version','revision','commit','trees')) {
            if ([regex]::Matches($text, '"' + $property + '"\s*:').Count -ne 1) { throw 'proof_duplicate_manifest_key' }
        }
        $trees = @($manifest.trees)
        if ($manifest.schema_version -ne 1 -or $manifest.revision -cne $ExpectedRevision -or $trees.Count -gt 128 -or $trees.Count -eq 0) { throw 'proof_identity_mismatch' }
        if ($manifest.commit.Length -gt 87384) { throw 'proof_commit_oversized' }
        $commit = [Convert]::FromBase64String($manifest.commit)
        if ((Get-PreparationGitObjectId 'commit' $commit) -cne $ExpectedRevision) { throw 'proof_commit_hash' }
        $commitText = [Text.Encoding]::UTF8.GetString($commit)
        $headers = ($commitText -split "`n`n", 2)[0]
        $treeHeaders = [regex]::Matches($headers, '(?m)^tree ([0-9a-f]{40})$')
        if ($treeHeaders.Count -ne 1 -or !$headers.StartsWith('tree ')) { throw 'proof_commit_tree' }
        $rootTree = $treeHeaders[0].Groups[1].Value
        $objects = @{}
        foreach ($tree in $trees) {
            if (@($tree.PSObject.Properties).Count -ne 2 -or $tree.id -cnotmatch '^[0-9a-f]{40}$' -or $objects.ContainsKey($tree.id) -or $tree.data.Length -gt 5592408) { throw 'proof_tree_shape' }
            $bytes = [Convert]::FromBase64String($tree.data)
            if ($bytes.Length -gt 4194304 -or (Get-PreparationGitObjectId 'tree' $bytes) -cne $tree.id) { throw 'proof_tree_hash' }
            $objects[$tree.id] = Read-PreparationGitTree $bytes
        }
        if ([regex]::Matches($text, '"id"\s*:').Count -ne $trees.Count -or [regex]::Matches($text, '"data"\s*:').Count -ne $trees.Count) { throw 'proof_duplicate_tree_key' }
        foreach ($asset in $Assets) {
            if ($asset -cnotmatch '^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$') { throw 'proof_asset_path' }
            $parts = $asset.Split('/')
            if ($parts.Count -gt 12 -or $parts -contains '..' -or $parts -contains '.') { throw 'proof_asset_depth' }
            $treeId = $rootTree
            $currentPath = $root
            $rootItem = Get-Item -LiteralPath $root -ErrorAction Stop
            if ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'proof_root_reparse' }
            for ($index = 0; $index -lt $parts.Count; $index++) {
                if (!$objects.ContainsKey($treeId) -or !$objects[$treeId].ContainsKey($parts[$index])) { throw 'proof_asset_missing' }
                $entry = $objects[$treeId][$parts[$index]]
                $currentPath = Join-Path $currentPath $parts[$index]
                $item = Get-Item -LiteralPath $currentPath -ErrorAction Stop
                if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'proof_asset_reparse' }
                if ($index -lt $parts.Count - 1) {
                    if ($entry.mode -ne '40000' -or !$item.PSIsContainer) { throw 'proof_not_directory' }
                    $treeId = $entry.id
                } else {
                    if ($entry.mode -notin @('100644','100755') -or $item.PSIsContainer -or $item.Length -gt 4194304) { throw 'proof_not_regular_asset' }
                    $content = [IO.File]::ReadAllBytes($currentPath)
                    if ((Get-PreparationGitObjectId 'blob' $content) -cne $entry.id) { throw 'proof_asset_hash' }
                    $result.assets[$asset] = (Get-FileHash -LiteralPath $currentPath -Algorithm SHA256).Hash.ToLowerInvariant()
                }
            }
        }
        $result.verified = $true
        $result.clean = $true
        $result.revision = $ExpectedRevision
        $result.cause = $null
    } catch {
        $result.verified = $false
        $result.clean = $false
        $result.cause = 'release_proof_unverified'
    }
    return $result
}
