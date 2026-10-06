"""Reuse the saved reflection parser, retaining separate light evidence."""
from pathlib import Path
source=Path(__file__).with_name('shader_fog_reflection_main.py').read_text()
source=source.replace("if b'Fog' not in blob:","if b'Light' not in blob:")
source=source.replace('shader-fog-reflection-main.json','shader-light-reflection-main.json')
source=source.replace('Fog shaders','Light shaders')
source=source.replace("if 'fog' in field['name'].lower() or 'volumetric' in buffer['name'].lower():",
                      "if 'light' in field['name'].lower() or 'light' in buffer['name'].lower():")
source=source.replace("if 'fog' in member['name'].lower():","if 'light' in member['name'].lower():")
exec(compile(source,'shader_fog_reflection_main.py','exec'))
