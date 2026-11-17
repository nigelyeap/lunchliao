import bpy, os, sys, math
sys.path.insert(0, '/Users/nigelyeap/Documents/lunchliao-hd/tools/blender/heroes')
from render_lib import *
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.expanduser('~/Documents/chope-src/heroes/nsboy.glb'))
for o in bpy.data.objects:
    if o.name.startswith('Icosphere'): o.hide_render = True
lo=[1e9]*3;hi=[-1e9]*3
for o in bpy.data.objects:
    if o.type=='MESH':
        for v in o.data.vertices:
            w=o.matrix_world@v.co; lo=[min(a,b) for a,b in zip(lo,w)]; hi=[max(a,b) for a,b in zip(hi,w)]
print('OLDBOUNDS',lo,hi)
setup_render(900, 900, 24); studio_light((0, 0, 1.1)); floor()
out = os.path.dirname(os.path.abspath(__file__))
shoot(os.path.join(out, 'old_front.png'), (0, 6.5, 1.6), (0, 0, 1.0), 60)
shoot(os.path.join(out, 'old_34.png'), (4.2, 4.8, 2.0), (0, 0, 1.0), 60)
shoot(os.path.join(out, 'old_back.png'), (-3, -5.5, 2.0), (0, 0, 1.0), 60)
