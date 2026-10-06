$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$taskArchive = Join-Path $taskRoot 'archive\2026-10-04-completed'
if (Test-Path -LiteralPath $taskArchive) { throw 'Archive already exists; refuse to overwrite.' }
$taskPaths = [System.Collections.Generic.List[string]]::new()
$taskStartupKeep = @('README.md','NoIntro-Fixed-2Seconds.README.md','NoIntro-Fixed-2Seconds.stage','fixed-intro-package.json','permanent-install.json','installation-audit.json','steam-toc-reference.json','toc.steam-original')
Get-ChildItem -LiteralPath (Join-Path $taskRoot 'outputs\startup-repair') | Where-Object { $_.Name -notin $taskStartupKeep } | ForEach-Object { $taskPaths.Add('outputs\startup-repair\' + $_.Name) }
foreach ($taskItem in @(
 'work\intro-native','work\overstrike-audit','work\short-intro',
 'work\audit_startup_sections.py','work\diagnose_startup_toc.py','work\direct_intro_archive.py',
 'work\finalize_startup_repair.py','work\find_boot_state.py','work\finish_startup_repair.ps1',
 'work\inspect_nointro_mode.py','work\inspect_original_movies.py','work\install_compatible_intro.ps1',
 'work\install_fixed_intro_permanent.ps1','work\install_intro_routing_test.ps1','work\intro-native-boot.txt',
 'work\isolate_nointro.ps1','work\overstrike_offline_audit.py','work\prepare_intro_routing_test.py',
 'work\prepare_short_intro.py','work\prepare_two_second_intro.py','work\read_steam_toc_manifest.py',
 'work\record_intro_test_result.py','work\restore_stable_startup.ps1','work\start_startup_repair.ps1',
 'work\startup-toc-sections.json','work\trace_native_intro.py','work\unused_isolation_verify.py',
 'work\validate_short_intro_bink.py','work\verify_compatible_intro_install.py','work\verify_nointro_isolation.py','work\verify_startup_repair.py',
 'work\camera-boost-live.err','work\camera-boost-live.log','work\camera-boost-live2.err','work\camera-boost-live2.log','work\camera-boost-live3.err','work\camera-boost-live3.log',
 'work\migrate_camera_overstrike.ps1','work\__pycache__',
 'outputs\camera-controls\__pycache__','outputs\camera-controls\migration-backup',
 'outputs\camera-controls\CameraShiftBoost.py','outputs\camera-controls\Start-CameraBoost.cmd','outputs\camera-controls\Start-CameraBoost.ps1','outputs\camera-controls\Stop-CameraBoost.ps1',
 'outputs\camera-controls\boost-error.log','outputs\camera-controls\boost-status.json','outputs\camera-controls\boost.log',
 'outputs\camera-native\PhotoModeCamera.log')) {
 if (Test-Path -LiteralPath (Join-Path $taskRoot $taskItem)) { $taskPaths.Add($taskItem) }
}
# Check every resolved source and destination before any recursive directory move.
$taskPlan = foreach ($taskRelative in $taskPaths) {
 $taskSource = (Resolve-Path -LiteralPath (Join-Path $taskRoot $taskRelative)).Path
 $taskDestination = [IO.Path]::GetFullPath((Join-Path $taskArchive $taskRelative))
 if (-not $taskSource.StartsWith($taskRoot + '\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Source outside workspace.' }
 if (-not $taskDestination.StartsWith($taskArchive + '\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Destination outside archive.' }
 [pscustomobject]@{original=$taskRelative;archived=('archive\2026-10-04-completed\'+$taskRelative)}
}
New-Item -ItemType Directory -Path $taskArchive | Out-Null
$taskPlan | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $taskArchive 'manifest.json') -Encoding utf8
foreach ($taskRecord in $taskPlan) {
 $taskDestination = Join-Path $taskRoot $taskRecord.archived
 New-Item -ItemType Directory -Path (Split-Path $taskDestination -Parent) -Force | Out-Null
 Move-Item -LiteralPath (Join-Path $taskRoot $taskRecord.original) -Destination $taskDestination
 if (-not (Test-Path -LiteralPath $taskDestination)) { throw 'Archive move verification failed.' }
}
Write-Output ('Archived {0} top-level items; originals preserved, game files untouched.' -f @($taskPlan).Count)
