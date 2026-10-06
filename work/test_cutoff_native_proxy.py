import ctypes as C,time,json,struct
from pathlib import Path
root=Path('outputs/camera-native-lighting-v3').resolve()
real=C.WinDLL(r'C:\Windows\System32\hid.dll',use_last_error=True)
proxy=C.WinDLL(str(root/'hid.dll'),use_last_error=True)
for library in (real,proxy):
 library.HidD_GetHidGuid.argtypes=[C.c_void_p];library.HidD_GetHidGuid.restype=None
expected=C.create_string_buffer(16);actual=C.create_string_buffer(16)
real.HidD_GetHidGuid(expected);proxy.HidD_GetHidGuid(actual)
assert actual.raw==expected.raw,'HID forwarding changed the result'
manifest=json.loads((root/'export-manifest.json').read_text())
for ordinal,name in manifest['system_hid_exports']:
 if name:getattr(proxy,name)
 else:proxy[ordinal]
for _ in range(50):
 log=root/'PhotoModeCamera.log'
 if log.exists() and 'Unsupported executable' in log.read_text():break
 time.sleep(.1)
else:raise AssertionError('Expected non-game build guard did not run')
report={'hid_guid_matches_system':True,'all_exports_resolved':manifest['count'],'non_game_hook_guard':'refused correctly'}
(root/'proxy-test.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
