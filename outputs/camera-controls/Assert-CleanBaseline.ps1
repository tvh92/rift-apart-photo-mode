param(
    [string]$BackupPath = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\toc.BAK'
)
$ErrorActionPreference = 'Stop'
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskAppManifest = 'C:\Program Files (x86)\Steam\steamapps\appmanifest_1895880.acf'
$taskManifestText = Get-Content -Raw -LiteralPath $taskAppManifest
if ($taskManifestText -notmatch '"StateFlags"\s+"4"' -or $taskManifestText -notmatch '"buildid"\s+"23987138"') {
    throw 'Steam is updating or the game build changed. Verify game files and establish a fresh baseline before reinstalling.'
}
if ($taskManifestText -notmatch '(?s)"1895881"\s*\{\s*"manifest"\s+"2186341403927512776"') {
    throw 'Steam depot manifest changed. The saved baseline must not be used.'
}
if ((Get-FileHash -LiteralPath (Join-Path $taskGame 'RiftApart.exe') -Algorithm SHA256).Hash -ine '51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82') {
    throw 'Unexpected executable. Refusing to reuse this baseline.'
}
if (-not (Test-Path -LiteralPath $BackupPath -PathType Leaf)) {
    throw 'toc.BAK is missing. Do not let Overstrike create a backup from a modded toc; restore a Steam-verified baseline first.'
}
if ((Get-FileHash -LiteralPath $BackupPath -Algorithm SHA1).Hash -ine '64946f571579d9ea0a17e675682e2994dc0f20fc') {
    throw 'toc.BAK is stale or modified. Refusing to install mods from it. Restore the verified baseline before reinstalling.'
}
Write-Output 'Clean baseline verified against the supported Steam build and depot manifest.'
