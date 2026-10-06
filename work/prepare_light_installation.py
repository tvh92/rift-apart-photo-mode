"""Prepare rollback to the confirmed fog release, leaving its artifacts intact."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root/'outputs/camera-native-fog-candidate'
dest=root/'outputs/camera-native-lighting-candidate'
prior='5c36943c6dfb45713382bf471e6f9939f857ee94f7789b8fefb2fc3abc292842'
confirmed='228620169d5741cd57d544047d351e7bd3c7df541778bc78c17ea0655bcb6f2a'
s=(source/'Install-FogCandidate.ps1').read_text()
s=s.replace(prior,confirmed).replace('before-native-fog','before-native-lighting')
s=s.replace('Awaiting user startup/Photo-entry/far-camera/Ctrl/exit/reentry test; isolated probes passed.',
            'Awaiting user ordinary-light near/far/Ctrl comparison; confirmed fog retained, isolated probes passed.')
s=s.replace('Fog candidate installed and full audit passed.', 'Lighting candidate installed and full audit passed.')
needle="if($taskManifest.install_blocked_reason){throw $taskManifest.install_blocked_reason}"
s=s.replace(needle,needle+"\nforeach($taskProperty in $taskManifest.source_hashes.PSObject.Properties) {\n    if((Get-FileHash (Join-Path $PSScriptRoot $taskProperty.Name)).Hash -ine $taskProperty.Value){throw 'Validated source changed; rebuild and review first.'}\n}")
needle="if($LASTEXITCODE -ne 0){throw 'Current installation audit failed.'}"
s=s.replace(needle,needle+"\n    $taskPre=Get-Content -Raw (Join-Path $PSScriptRoot 'pre-installation-audit.json') | ConvertFrom-Json\n    if($taskPre.fixed_intro_enabled){throw 'Original full movie profile required.'}")
needle="if($LASTEXITCODE -ne 0){throw 'Post-installation audit failed.'}"
s=s.replace(needle,needle+"\n        $taskPost=Get-Content -Raw (Join-Path $PSScriptRoot 'installation-audit.json') | ConvertFrom-Json\n        foreach($taskProperty in $taskPre.PSObject.Properties) {\n            if($taskProperty.Name -notin @('camera_dll_sha256','camera_dll_variant','in_game_status')) {\n                $taskBefore=$taskProperty.Value | ConvertTo-Json -Compress -Depth 10\n                $taskAfter=$taskPost.($taskProperty.Name) | ConvertTo-Json -Compress -Depth 10\n                if($taskBefore -cne $taskAfter){throw ('Installation changed audit field: '+$taskProperty.Name)}\n            }\n        }")
(dest/'Install-LightingCandidate.ps1').write_text(s)
s=(source/'Restore-ConfirmedCtrl.ps1').read_text()
s=s.replace(prior,confirmed).replace('before-native-fog','before-native-lighting')
s=s.replace('Restored user-confirmed Ctrl DLL.', 'Restored user-confirmed fog DLL with Ctrl.')
(dest/'Restore-ConfirmedFog.ps1').write_text(s)
print('Prepared lighting installation/rollback scripts; confirmed fog artifacts untouched.')
