$ErrorActionPreference = 'Stop'
$taskManifestPath = Join-Path $PSScriptRoot 'change.json'
$taskManifest = Get-Content -Raw -LiteralPath $taskManifestPath | ConvertFrom-Json
$taskExpectedTarget = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\d\config'
if ($taskManifest.game_config -cne $taskExpectedTarget) { throw 'Unexpected installation target.' }
if (Get-Process -Name RiftApart -ErrorAction SilentlyContinue) { throw 'Close Rift Apart before installing the patch.' }
function Confirm-TaskHash($taskPath, $taskExpectedHash) {
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $taskPath).Hash -ine $taskExpectedHash) {
        throw "File differs from the validated version: $taskPath"
    }
}
Confirm-TaskHash $taskManifest.backup $taskManifest.original_sha256
Confirm-TaskHash $taskManifest.prepared_config $taskManifest.patched_sha256
Confirm-TaskHash $taskExpectedTarget $taskManifest.original_sha256
$taskTocPath = Join-Path (Split-Path (Split-Path $taskExpectedTarget -Parent) -Parent) 'toc'
Confirm-TaskHash $taskTocPath $taskManifest.toc_sha256
$taskTemporary = $taskExpectedTarget + '.tether1000.tmp'
if (-not (Test-Path -LiteralPath $taskTemporary)) {
    [IO.File]::Copy($taskManifest.prepared_config, $taskTemporary, $false)
}
Confirm-TaskHash $taskTemporary $taskManifest.patched_sha256
[IO.File]::Replace($taskTemporary, $taskExpectedTarget, [System.Management.Automation.Language.NullString]::Value)
Confirm-TaskHash $taskExpectedTarget $taskManifest.patched_sha256
Confirm-TaskHash $taskTocPath $taskManifest.toc_sha256
$taskManifest.installed = $true
$taskManifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskManifestPath -Encoding utf8
Write-Output 'Installed: native Photo Mode Free camera TetherDistance = 1000.'
