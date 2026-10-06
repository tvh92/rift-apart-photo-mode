"""Prepare exact prior-status rollback and audited specular installation."""
from pathlib import Path
root=Path(__file__).resolve().parents[1];source=root/'outputs/camera-native-status-candidate';dest=root/'outputs/camera-native-lighting-v2'
old='fa3ced0a22083cfe0e9ee68c96e5bdda2c4d13c46f34346c79848693873356b6'
previous='77051506a589b1051556505b309c32eb7a4a69e93df93d0a29d85b74b045a2d0'
s=(source/'Install-StatusCandidate.ps1').read_text().replace(old,previous)
s=s.replace('2026-10-06-before-status','2026-10-06-before-specular')
s=s.replace('Tested lighting rollback','Previous status rollback')
s=s.replace('Awaiting startup/Photo Ctrl status ON/OFF/fade/exit-reentry test; native lighting/fog implementation unchanged.',
            'Awaiting far-camera surface-light comparison; diffuse/specular and type4 far fades overridden; separate UI test waived.')
s=s.replace('Status candidate installed and full audit passed.','Specular lighting candidate installed and full audit passed.')
(dest/'Install-SpecularCandidate.ps1').write_text(s)
s=(source/'Restore-TestedLighting.ps1').read_text().replace(old,previous)
s=s.replace('2026-10-06-before-status','2026-10-06-before-specular')
s=s.replace('Tested lighting rollback','Previous status rollback')
s=s.replace('Restored tested lighting/fog DLL with Ctrl and no indicator.', 'Restored previous status/fog/RGB-light DLL770.')
(dest/'Restore-PreviousStatus.ps1').write_text(s)
print('Prepared audited specular install and exact previous status rollback.')
