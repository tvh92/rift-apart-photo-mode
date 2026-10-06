"""Derive guarded installation with rollback to the exact tested lighting DLL."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root/'outputs/camera-native-lighting-candidate'
dest=root/'outputs/camera-native-status-candidate'
fog='228620169d5741cd57d544047d351e7bd3c7df541778bc78c17ea0655bcb6f2a'
prior='fa3ced0a22083cfe0e9ee68c96e5bdda2c4d13c46f34346c79848693873356b6'
s=(source/'Install-LightingCandidate.ps1').read_text()
s=s.replace(fog,prior).replace('$taskConfirmed','$taskPrevious')
s=s.replace('2026-10-05-before-native-lighting','2026-10-06-before-status')
s=s.replace('Confirmed rollback','Tested lighting rollback')
s=s.replace('Awaiting user ordinary-light near/far/Ctrl comparison; confirmed fog retained, isolated probes passed.',
            'Awaiting startup/Photo Ctrl status ON/OFF/fade/exit-reentry test; native lighting/fog implementation unchanged.')
s=s.replace('Lighting candidate installed and full audit passed.', 'Status candidate installed and full audit passed.')
(dest/'Install-StatusCandidate.ps1').write_text(s)
s=(source/'Restore-ConfirmedFog.ps1').read_text()
s=s.replace(fog,prior).replace('$taskConfirmed','$taskPrevious')
s=s.replace('2026-10-05-before-native-lighting','2026-10-06-before-status')
s=s.replace('Confirmed rollback','Tested lighting rollback')
s=s.replace('Restored user-confirmed fog DLL with Ctrl.', 'Restored tested lighting/fog DLL with Ctrl and no indicator.')
(dest/'Restore-TestedLighting.ps1').write_text(s)
print('Prepared status installer and exact tested-lighting rollback.')
