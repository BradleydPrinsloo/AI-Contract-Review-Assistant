param(
    [string]$ManifestPath = (Join-Path $PSScriptRoot 'BUNDLE-CONTENTS-SHA256.txt')
)

$ErrorActionPreference = 'Stop'

if (!(Test-Path -LiteralPath $ManifestPath)) {
    throw "Checksum manifest not found: $ManifestPath"
}

$bundleRoot = Split-Path -Parent $ManifestPath
$failures = @()

Get-Content -LiteralPath $ManifestPath | Where-Object { $_.Trim() } | ForEach-Object {
    if ($_ -notmatch '^([a-fA-F0-9]{64}) \*(.+)$') {
        $failures += "Malformed manifest line: $_"
        return
    }

    $expected = $Matches[1].ToLowerInvariant()
    $relative = $Matches[2]
    $path = Join-Path $bundleRoot $relative

    if (!(Test-Path -LiteralPath $path)) {
        $failures += "Missing file: $relative"
        return
    }

    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    if ($actual -ne $expected) {
        $failures += "Hash mismatch: $relative"
    }
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host 'All ContractIQ bundle checksums verified.'
