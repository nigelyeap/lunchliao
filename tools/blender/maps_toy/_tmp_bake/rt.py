import bpy, json, struct
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/Users/nigelyeap/Documents/lunchliao-hd/assets/maps/hawker.glb')
out='/Users/nigelyeap/Documents/lunchliao-hd/tools/blender/maps_toy/_tmp_bake/rt.glb'
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True, export_yup=True, export_image_format='AUTO', export_animations=False)
b=open(out,'rb').read(); n=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+n])
print('RT verts', sum(j['accessors'][p['attributes']['POSITION']]['count'] for m in j['meshes'] for p in m['primitives']), len(b)//1024, 'KB')
