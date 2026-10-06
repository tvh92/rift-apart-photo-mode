$ErrorActionPreference = 'Stop'
$taskManifestPath = Join-Path $PSScriptRoot 'change.json'
$taskManifest = Get-Content -Raw -LiteralPath $taskManifestPath | ConvertFrom-Json
$taskExpectedTarget = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\d\config'
if ($taskManifest.game_config -cne $taskExpectedTarget) { throw 'Unexpected restoration target.' }
if (Get-Process -Name RiftApart -ErrorAction SilentlyContinue) { throw 'Close Rift Apart before restoring.' }
function Confirm-TaskHash($taskPath, $taskExpectedHash) {
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $taskPath).Hash -ine $taskExpectedHash) {
        throw "File differs from the expected version: $taskPath. Restoration stopped to avoid overwriting another update or mod."
    }
}
Confirm-TaskHash $taskManifest.backup $taskManifest.original_sha256
Confirm-TaskHash $taskExpectedTarget $taskManifest.patched_sha256
$taskTemporary = $taskExpectedTarget + '.tether1000.restore.tmp'
if (Test-Path -LiteralPath $taskTemporary) { throw 'Temporary restoration file already exists.' }
[IO.File]::Copy($taskManifest.backup, $taskTemporary, $false)
Confirm-TaskHash $taskTemporary $taskManifest.original_sha256
[IO.File]::Replace($taskTemporary, $taskExpectedTarget, [System.Management.Automation.Language.NullString]::Value)
Confirm-TaskHash $taskExpectedTarget $taskManifest.original_sha256
$taskManifest.installed = $false
$taskManifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskManifestPath -Encoding utf8
Write-Output 'Restored the original config archive.'
