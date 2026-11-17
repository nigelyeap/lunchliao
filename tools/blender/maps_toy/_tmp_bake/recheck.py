# render the base x AO check from an existing <id>_lit.glb + <id>_ao.png
import bpy, sys, os, json
from mathutils import Vector
MID = sys.argv[sys.argv.index('--') + 1]
H = '/Users/nigelyeap/Documents/lunchliao-hd/tools/blender/maps_toy'
src = open(H + '/bake_ao.py').read()
CAMS = eval(src.split('CAMS = ')[1].split('\n\n')[0].split('# ground_a')[0] + src.split('CAMS = ')[1].split('\n\n')[0].split('game coords (x, y up, z)')[1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=f'{H}/../../../assets/maps/{MID}_lit.glb')
SC = bpy.context.scene; meta = json.load(open(f'{H}/../../../assets/maps/{MID}_ao.json'))
BAKE = [bpy.data.objects[n] for n in meta['meshes']]
for o in BAKE: o.data.uv_layers[1].name = 'lightmap'
png = f'{H}/../../../assets/maps/{MID}_ao.png'; TMP = H + '/_tmp_bake'
exec('if True:\n' + src.split("if 'check' in ARGS:\n")[1].split("print('AO done'")[0])
