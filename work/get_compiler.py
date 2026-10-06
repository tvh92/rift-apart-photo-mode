import urllib.request,json,hashlib,zipfile
from pathlib import Path
root=Path('work/toolchain').resolve();root.mkdir(parents=True,exist_ok=True)
index=json.load(urllib.request.urlopen('https://ziglang.org/download/index.json'))
version='0.15.2';record=index[version]['x86_64-windows']
(root/'zig-download.json').write_text(json.dumps({'version':version,**record},indent=2))
archive=root/Path(record['tarball']).name
if not archive.exists():
 with urllib.request.urlopen(record['tarball']) as response, archive.open('wb') as dest:
  while chunk:=response.read(1024*1024):dest.write(chunk)
assert hashlib.sha256(archive.read_bytes()).hexdigest()==record['shasum'],'Official compiler checksum mismatch'
with zipfile.ZipFile(archive) as z:
 for entry in z.namelist():
  resolved=(root/entry).resolve()
  assert resolved.is_relative_to(root),'Unsafe archive path'
 z.extractall(root)
print('Official Zig compiler verified and extracted:',root)
