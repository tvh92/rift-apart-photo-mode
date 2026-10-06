"""Convert the native UI probe's own BGRA output into preview artifacts."""
from pathlib import Path
from PIL import Image
for mode in ('on','off'):
    base=Path('work/native-abi')/('status-'+mode)
    Image.frombytes('RGBA',(280,52),base.with_suffix('.bgra').read_bytes(),'raw','BGRA').save(base.with_suffix('.png'))
print('Native status ON/OFF previews written.')
