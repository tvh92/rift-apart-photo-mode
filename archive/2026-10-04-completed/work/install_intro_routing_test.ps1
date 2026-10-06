param([ValidateSet('original','short','two-second')][string]$Variant = 'original')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskRepair = Join-Path $taskRoot 'outputs\startup-repair'
$taskManager = Join-Path $taskRepair ('routing-launch-' + $Variant)
$taskReferenceHash = '64946f571579d9ea0a17e675682e2994dc0f20fc'
$taskRoutingHash = '78ee66e82f32eedf237490a7239c8d7f7760ebff'
if (Get-Process -Name RiftApart,Overstrike -ErrorAction SilentlyContinue) { throw 'Game and Overstrike must be closed.' }
$taskToc = Join-Path $taskGame 'toc'
$taskBak = Join-Path $taskGame 'toc.BAK'
if ($Variant -eq 'original') {
    $taskCurrentIndexHash = (Get-FileHash -LiteralPath $taskToc -Algorithm SHA1).Hash
    if ($taskCurrentIndexHash -ine $taskReferenceHash -and $taskCurrentIndexHash -ine $taskRoutingHash) { throw 'Original routing test requires the pristine index or the validated routing-test index.' }
} else {
    if ((Get-FileHash -LiteralPath $taskToc -Algorithm SHA1).Hash -ine $taskRoutingHash) { throw 'Short routing test requires the verified original routing-test index.' }
}
if ((Test-Path -LiteralPath $taskBak) -and (Get-FileHash -LiteralPath $taskBak -Algorithm SHA1).Hash -ine $taskReferenceHash) { throw 'Unexpected backup; refusing to reuse it.' }
if ((Get-FileHash -LiteralPath (Join-Path $taskGame 'hid.dll') -Algorithm SHA256).Hash -ine '97b9a29eed154973fb587e0fae965c441b9956096211523aa1f99ef1d6d03e81') { throw 'Camera DLL changed unexpectedly.' }
switch ($Variant) {
    'original' { $taskPackageName='Intro-Original-Routing-Test.stage'; $taskExpectedPackage='e89efd8b8c9e9d75371619417d5f7fb7cf9f5084312f5662d13a4cc8ebd702fe' }
    'short' { $taskPackageName='NoIntro-Padded-CurrentBuild.stage'; $taskExpectedPackage='f2ae21130ec93f1a784ce0c701df5aa077331589b25627b136e051d253293b8f' }
    'two-second' { $taskPackageName='NoIntro-2Second-CurrentBuild.stage'; $taskExpectedPackage='580f03e7d68bb2e3464b4d77439db290902f970e3df5658e20c682c4e2b3a616' }
}
$taskPackage = Join-Path $taskRepair $taskPackageName
if ((Get-FileHash -LiteralPath $taskPackage -Algorithm SHA256).Hash -ine $taskExpectedPackage) { throw 'Diagnostic package changed.' }
New-Item -ItemType Directory -Path (Join-Path $taskManager 'Profiles'),(Join-Path $taskManager 'Mods Library') -Force | Out-Null
Copy-Item -LiteralPath $taskPackage -Destination (Join-Path $taskManager ('Mods Library\'+$taskPackageName)) -Force
$taskProfile = [ordered]@{game='RCRA';path=$taskGame;mods=@(,@($taskPackageName,$true));settings=@{suit=@{language='us';allow_cross_character_suit_models=$false};scripts=@{enabled=$false;commandline=$false}};suits=@{delete=@();order=@();modify=@{}}}
$taskProfile | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskManager 'Profiles\Audit.json') -Encoding utf8
$taskSnapshot = Join-Path $taskManager ('before-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskSnapshot | Out-Null
Copy-Item -LiteralPath $taskToc -Destination (Join-Path $taskSnapshot 'toc')
$taskMod = Join-Path $taskGame 'd\mods\mod0'
if (Test-Path -LiteralPath $taskMod) { Copy-Item -LiteralPath $taskMod -Destination (Join-Path $taskSnapshot 'mod0') }
try {
    $taskExe = Join-Path $taskRoot 'outputs\Overstrike\Overstrike.exe'
    $taskRun = Start-Process -FilePath $taskExe -ArgumentList 'install-mods Audit' -WorkingDirectory $taskManager -WindowStyle Hidden -Wait -PassThru
    if ($taskRun.ExitCode -ne 0) { throw ('Diagnostic install failed: ' + $taskRun.ExitCode) }
    if ((Get-FileHash -LiteralPath $taskToc -Algorithm SHA1).Hash -ine $taskRoutingHash) { throw 'Installed diagnostic index differs from the isolated validated result.' }
    if ((Get-FileHash -LiteralPath $taskBak -Algorithm SHA1).Hash -ine $taskReferenceHash) { throw 'Backup is not pristine.' }
    $taskExpectedArchive = Join-Path $taskRoot ('work\overstrike-audit\routing\'+$Variant+'\test-game\d\mods\mod0')
    if ((Get-FileHash -LiteralPath $taskMod -Algorithm SHA256).Hash -ine (Get-FileHash -LiteralPath $taskExpectedArchive -Algorithm SHA256).Hash) { throw 'Diagnostic movie archive differs from the validated payload.' }
} catch {
    Copy-Item -LiteralPath (Join-Path $taskSnapshot 'toc') -Destination $taskToc -Force
    if (Test-Path -LiteralPath (Join-Path $taskSnapshot 'mod0')) { Copy-Item -LiteralPath (Join-Path $taskSnapshot 'mod0') -Destination $taskMod -Force }
    throw
}
@{variant=$Variant;toc_sha1=$taskRoutingHash;toc_bak_pristine=$true;archive_matches_offline_test=$true;camera_dll_unchanged=$true;in_game_result='pending';snapshot=$taskSnapshot} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskManager 'install-result.json') -Encoding utf8
Write-Output ('Installed '+$Variant+' routing test with a pristine backup. Normal Overstrike profiles were not changed.')
