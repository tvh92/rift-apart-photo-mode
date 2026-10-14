$ErrorActionPreference='Stop'
$taskRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$taskCompiler=Join-Path $taskRoot 'work/toolchain/zig-x86_64-windows-0.15.2/zig.exe'
$env:ZIG_GLOBAL_CACHE_DIR=Join-Path $taskRoot 'work/zig-cache'
$taskCount='-DHID_EXPORT_COUNT='+((Get-Content -Raw (Join-Path $PSScriptRoot 'export-manifest.json') | ConvertFrom-Json).count)
& $taskCompiler cc -target x86_64-windows-gnu -O2 -Wall -Wextra -shared $taskCount (Join-Path $PSScriptRoot 'CameraBoost.c') (Join-Path $PSScriptRoot 'HidExports.c') (Join-Path $PSScriptRoot 'CameraStubs.S') (Join-Path $PSScriptRoot 'hid.def') -o (Join-Path $PSScriptRoot 'hid.dll') -lbcrypt -luser32 -lgdi32 '-Wl,--nxcompat' '-Wl,--dynamicbase'
if($LASTEXITCODE -ne 0){throw 'Cutoff candidate DLL build failed'}
$taskPython=(Join-Path $PSScriptRoot '..\..\.venv\Scripts\python.exe')
Push-Location $taskRoot
try {
    & $taskPython work/prepare_cutoff_fixture.py
    if($LASTEXITCODE -ne 0){throw 'Cutoff fixture generation failed'}
    & $taskPython work/prepare_cutoff_validation.py
    if($LASTEXITCODE -ne 0){throw 'Cutoff validation preparation failed'}
} finally {Pop-Location}
foreach($taskProbe in @('PhotoCutoffProbe','PhotoLightSpecularProbeV3','PhotoType4ProbeV3','PhotoFogSpecularProbeV3','PhotoSpecularLifecycleProbeV3','BehaviorSpecularProbeV3','SpecularStatusBitmapProbeV3','SpecularStatusThreadProbeV3')) {
    $taskArgs=@('cc','-target','x86_64-windows-gnu','-O2','-Wall','-Wextra','-Wno-unused-function',(Join-Path $taskRoot "work/native-abi/$taskProbe.c"))
    if($taskProbe -in @('PhotoSpecularLifecycleProbeV3','BehaviorSpecularProbeV3')) {
        $taskArgs+=@((Join-Path $PSScriptRoot 'HidExports.c'),(Join-Path $PSScriptRoot 'CameraStubs.S'),'-lbcrypt')
    }
    $taskArgs+=@('-luser32','-lgdi32','-o',(Join-Path $taskRoot "work/native-abi/$taskProbe.exe"))
    & $taskCompiler @taskArgs
    if($LASTEXITCODE -ne 0){throw "$taskProbe compilation failed"}
    & (Join-Path $taskRoot "work/native-abi/$taskProbe.exe")
    if($LASTEXITCODE -ne 0){throw "$taskProbe failed with exit code $LASTEXITCODE"}
}
Push-Location $taskRoot
try {
    & $taskPython work/test_cutoff_native_proxy.py
    if($LASTEXITCODE -ne 0){throw 'Cutoff proxy verification failed'}
} finally {Pop-Location}
