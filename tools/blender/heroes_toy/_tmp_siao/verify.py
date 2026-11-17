import bpy
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/Users/nigelyeap/Documents/lunchliao-hd/assets/heroes/siao.glb')
ms=[o for o in bpy.data.objects if o.type=='MESH' and o.name!='Icosphere']; rig=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
lo=Vector((1e9,)*3); hi=Vector((-1e9,)*3)
for o in ms:
    for v in o.data.vertices:
        w=o.matrix_world@v.co; lo=Vector(map(min,lo,w)); hi=Vector(map(max,hi,w))
print('V_HEIGHT', round(hi.z-lo.z,3), 'X', round(lo.x,2), round(hi.x,2), 'Y', round(lo.y,2), round(hi.y,2))
print('V_TRIS', sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in ms))
print('V_BONES', sorted(b.name for b in rig.data.bones))
for o in ms:
    if o.data.shape_keys: print('V_SK', o.name, [k.name for k in o.data.shape_keys.key_blocks])
print('V_ACTS', [(a.name, a.frame_range[0], a.frame_range[1]) for a in bpy.data.actions], bpy.context.scene.render.fps)
for a in bpy.data.actions: print('V_KEYS', a.name, sorted({int(round(k.co[0])) for fc in a.fcurves for k in fc.keyframe_points})[:3], max(int(round(k.co[0])) for fc in a.fcurves for k in fc.keyframe_points))
