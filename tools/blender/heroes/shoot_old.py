"""Render the old ref ahma glb for a look reference. Blender Z up here, glTF Y up maps to Z."""
import bpy, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
from render_lib import *
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'ref', 'heroes', 'ahma.glb'))
for o in bpy.data.objects:
    if o.name.startswith('Icosphere'): o.hide_render = True
setup_render(1024, 1024, 24); studio_light((0, 0, 1.1)); floor()
out = os.path.join(ROOT, 'shots', 'heroes', 'ahma')
shoot(os.path.join(out, 'ref_old_front.png'), (0, -6.5, 1.6), (0, 0, 1.05), 60)
shoot(os.path.join(out, 'ref_old_three_quarter.png'), (4.2, -4.8, 2.0), (0, 0, 1.05), 60)
shoot(os.path.join(out, 'ref_old_face.png'), (1.2, -2.0, 1.9), (0, 0, 1.65), 85)
