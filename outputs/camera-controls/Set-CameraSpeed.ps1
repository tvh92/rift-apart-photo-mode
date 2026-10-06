param([ValidateSet('1','10','100','1000','Vanilla')][string]$Multiplier = '10')
$ErrorActionPreference = 'Stop'
$taskManifestPath = Join-Path $PSScriptRoot 'change.json'
$taskManifest = Get-Content -Raw -LiteralPath $taskManifestPath | ConvertFrom-Json
$taskTarget = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\d\config'
if ($taskManifest.target -cne $taskTarget) { throw 'Unexpected game path.' }
if (Get-Process -Name RiftApart -ErrorAction SilentlyContinue) { throw 'Close Rift Apart before changing camera speed.' }
$taskCurrentHash = (Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash
$taskKnownHashes = @($taskManifest.source_sha256, $taskManifest.vanilla_sha256)
foreach ($taskPreset in $taskManifest.presets.PSObject.Properties) { $taskKnownHashes += $taskPreset.Value.sha256 }
if ($taskCurrentHash -notin $taskKnownHashes) { throw 'Game config changed since preparation. Refusing to overwrite it.' }
if ($Multiplier -eq 'Vanilla') {
    $taskSource = $taskManifest.vanilla_backup
    $taskHash = $taskManifest.vanilla_sha256
} else {
    $taskPreset = $taskManifest.presets.PSObject.Properties[$Multiplier].Value
    $taskSource = $taskPreset.file
    $taskHash = $taskPreset.sha256
}
if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash -ine $taskHash) { throw 'Preset hash mismatch.' }
if ($taskCurrentHash -ine $taskHash) {
    $taskTemporary = $taskTarget + '.camera-speed.tmp'
    if (Test-Path -LiteralPath $taskTemporary) { throw 'An existing temporary file needs inspection before continuing.' }
    [IO.File]::Copy($taskSource, $taskTemporary, $false)
    [IO.File]::Replace($taskTemporary, $taskTarget, [System.Management.Automation.Language.NullString]::Value)
    if ((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash -ine $taskHash) { throw 'Installed config hash mismatch.' }
}
$taskManifest.installed_multiplier = $Multiplier
$taskManifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $taskManifestPath -Encoding utf8
Write-Output "Camera setting installed: $Multiplier. Restart the game to load it."
