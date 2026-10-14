$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskPython = (Join-Path $PSScriptRoot '..\..\.venv\Scripts\python.exe')
$taskManager = Join-Path $taskRoot 'outputs\Overstrike'
if (Get-Process -Name RiftApart,Overstrike -ErrorAction SilentlyContinue) { throw 'Close Rift Apart and Overstrike before reinstalling.' }
& (Join-Path $PSScriptRoot 'Assert-CleanBaseline.ps1')
# This wrapper is limited to the audited camera or camera+fixed-intro profile, rather than
# silently reinstalling other mods or overwriting an unrecognized installation.
& $taskPython (Join-Path $PSScriptRoot 'Check-Installation.py')
if ($LASTEXITCODE -ne 0) { throw 'Current installation is unrecognized. No game files were changed.' }
$taskBackupDir = Join-Path $taskRoot ('outputs\startup-repair\guarded-reinstall-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskBackupDir | Out-Null
foreach ($taskName in @('toc','toc.sha1')) {
    $taskSource = Join-Path $taskGame $taskName
    if (Test-Path -LiteralPath $taskSource) { Copy-Item -LiteralPath $taskSource -Destination (Join-Path $taskBackupDir $taskName) }
}
foreach ($taskName in @('mod0','mod1')) {
    $taskModFile = Join-Path $taskGame ('d\mods\'+$taskName)
    if (Test-Path -LiteralPath $taskModFile) { Copy-Item -LiteralPath $taskModFile -Destination (Join-Path $taskBackupDir $taskName) }
}
try {
    $taskInstall = Start-Process -FilePath (Join-Path $taskManager 'Overstrike.exe') -ArgumentList 'install-mods "RCRA (Steam)"' -WorkingDirectory $taskManager -WindowStyle Hidden -Wait -PassThru
    if ($taskInstall.ExitCode -ne 0) { throw ('Overstrike failed with exit code ' + $taskInstall.ExitCode) }
    & (Join-Path $PSScriptRoot 'Assert-CleanBaseline.ps1')
    & $taskPython (Join-Path $PSScriptRoot 'Check-Installation.py')
    if ($LASTEXITCODE -ne 0) { throw 'Post-install audit failed.' }
} catch {
    # Recover only from this run's audited snapshots, never historical modded
    # indices mislabeled as vanilla baselines.
    foreach ($taskName in @('toc','toc.sha1')) {
        $taskSaved = Join-Path $taskBackupDir $taskName
        if (Test-Path -LiteralPath $taskSaved) { Copy-Item -LiteralPath $taskSaved -Destination (Join-Path $taskGame $taskName) -Force }
    }
    foreach ($taskName in @('mod0','mod1')) {
        $taskSaved = Join-Path $taskBackupDir $taskName
        if (Test-Path -LiteralPath $taskSaved) { Copy-Item -LiteralPath $taskSaved -Destination (Join-Path $taskGame ('d\mods\'+$taskName)) -Force }
    }
    throw
}
Write-Output 'Configured verified mods reinstalled and audited. Clean toc.BAK and native camera DLL preserved.'
