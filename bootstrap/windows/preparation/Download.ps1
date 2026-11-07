param(
    [Parameter(Mandatory=$true)][string]$Url,
    [Parameter(Mandatory=$true)][string]$Destination,
    [string]$ExpectedSha256,
    [switch]$VerifyOnly
)
# Runs only as a bounded child. No downloaded content is executed here.
$ErrorActionPreference='Stop'
$catalogue=@{
    'https://github.com/microsoft/WSL/releases/download/3.0.1/wsl.3.0.1.0.x64.msi'='28b1a0d013640a2ac95898ea705fa186e5b4ff767a1c1b49257161bc106599c6'
    'https://releases.ubuntu.com/noble/ubuntu-24.04.5-wsl-amd64.wsl'='bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e'
    'https://releases.ubuntu.com/resolute/ubuntu-26.04.1-wsl-amd64.wsl'='48d56724b5c8e60f24893e83e73bbb58c60b3ca22fba3da977075420acd54104'
}
$result=@{verified=$false;cause='artifact_download_failed'}
try {
    if(!$catalogue.ContainsKey($Url)){throw 'unreviewed_artifact'}
    if($ExpectedSha256 -and $ExpectedSha256 -cne $catalogue[$Url]){$result.cause='artifact_catalogue_mismatch';throw 'artifact_catalogue_mismatch'}
    if(!$VerifyOnly) {
        [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -MaximumRedirection 5 -Uri $Url -OutFile $Destination
    }
    $result.cause='artifact_hash_mismatch'
    if((Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant() -cne $catalogue[$Url]){throw 'artifact_hash_mismatch'}
    if($Url -like '*microsoft/WSL/*') {
        $result.cause='artifact_signature_invalid'
        $signature=Get-AuthenticodeSignature -LiteralPath $Destination
        if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '(?:^|,\s*)O=Microsoft Corporation(?:,|$)'){throw 'artifact_signature_invalid'}
    }
    $result.verified=$true
    $result.cause=$null
} catch {
    if($_.Exception.Message -eq 'unreviewed_artifact'){$result.cause='unreviewed_artifact'}
}
$result | ConvertTo-Json -Compress
if(!$result.verified){exit 1}
exit 0
