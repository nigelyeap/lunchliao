"""Measure ref/heroes/*.glb: bounds, height, head bone, tris. Run:
/opt/homebrew/bin/blender -b -P tools/blender/heroes/measure_ref.py"""
import bpy, os, sys
from mathutils import Vector
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
for name in ['ahma', 'gym', 'tarik', 'siao']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'ref', 'heroes', name + '.glb'))
    bpy.context.view_layer.update()
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3); tris = 0
    dg = bpy.context.evaluated_depsgraph_get()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and 'Icosphere' not in o.name]  # Icosphere is a r=1 bounds helper, skip it
    for o in meshes:
        ev = o.evaluated_get(dg); m = ev.to_mesh()
        tris += sum(len(p.vertices) - 2 for p in m.polygons)
        for v in m.vertices:
            w = ev.matrix_world @ v.co
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
        ev.to_mesh_clear()
    # glTF importer converts to Z up. Report in glTF (Y up) terms: y=blender z, z=-blender y
    print(f"== {name}: meshes {len(meshes)} tris {tris}")
    print(f"   bounds X {lo.x:.3f}..{hi.x:.3f}  Y(up) {lo.z:.3f}..{hi.z:.3f}  Z {-hi.y:.3f}..{-lo.y:.3f}  height {hi.z-lo.z:.3f}")
    for o in bpy.data.objects:
        if o.type == 'ARMATURE':
            print("   bones:", [b.name for b in o.data.bones])
            for b in o.data.bones:
                if b.name.lower() in ('head', 'neck', 'root', 'hips', 'spine'):
                    h = o.matrix_world @ b.head_local; t = o.matrix_world @ b.tail_local
                    print(f"   bone {b.name}: head (x {h.x:.3f}, y {h.z:.3f}, z {-h.y:.3f}) tail (x {t.x:.3f}, y {t.z:.3f}, z {-t.y:.3f})")
    for o in meshes:
        ev = o.evaluated_get(dg); m = ev.to_mesh(); ws = [ev.matrix_world @ v.co for v in m.vertices]
        print(f"   mesh {o.name} mats {[m_.name if m_ else None for m_ in o.data.materials]} Y {min(w.z for w in ws):.3f}..{max(w.z for w in ws):.3f} X {min(w.x for w in ws):.3f}..{max(w.x for w in ws):.3f} Z {-max(w.y for w in ws):.3f}..{-min(w.y for w in ws):.3f} vcol {bool(m.color_attributes)}")
        ev.to_mesh_clear()
    for mat in bpy.data.materials:
        if mat.use_nodes:
            for n in mat.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    print(f"   mat {mat.name} base {tuple(round(c,2) for c in n.inputs['Base Color'].default_value)} links {[l.from_node.type for l in n.inputs['Base Color'].links]}")
    for im in bpy.data.images:
        print(f"   image {im.name} {im.size[:]}")
