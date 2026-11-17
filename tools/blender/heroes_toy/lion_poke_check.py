# counts body verts that sit above the mouth sheet (visible inside the open jaw) per clip frame and face key
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
head = next(o for o in meshes if any('mouth_sheet' in (s.material.name if s.material else '') for s in o.material_slots))
body = max((o for o in meshes if o is not head), key=lambda o: len(o.data.vertices))
gi = head.vertex_groups['prop'].index
jawv = {v.index for v in head.data.vertices if any(g.group == gi and g.weight > .5 for g in v.groups)}
si = next(i for i, s in enumerate(head.material_slots) if 'mouth_sheet' in s.material.name)
rest = [body.matrix_world @ v.co for v in body.data.vertices]
def check(tag):
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    he = head.evaluated_get(dg); hm = he.to_mesh(); M = he.matrix_world
    vs = [M @ v.co for v in hm.vertices]; ps = [p for p in hm.polygons if p.material_index == si]
    n = sum(((M.to_3x3() @ p.normal) * p.area for p in ps), Vector()).normalized()
    if n.z < 0: n = -n
    jp = [tuple(p.vertices) for p in hm.polygons if all(i in jawv for i in p.vertices)]
    bvh = BVHTree.FromPolygons(vs, jp); he.to_mesh_clear()
    be = body.evaluated_get(dg); bm = be.to_mesh(); B = be.matrix_world; bad = []
    for v in bm.vertices:
        p = B @ v.co; h = bvh.ray_cast(p, -n, .4)
        if h[0] is not None and h[3] > .004 and h[1].dot(n) > .2 and rest[v.index].z < 1.5: bad.append((h[3], rest[v.index]))
    be.to_mesh_clear()
    if '-v' in sys.argv: print('DBG', tag, 'n.z %.3f' % n.z, 'sheet polys', len(ps))
    if bad:
        zs = [r.z for d, r in bad]; ys = [r.y for d, r in bad]
        if '-l' in sys.argv: print('LIST', tag, sorted({(round(r.z, 2), round(r.y, 2), round(abs(r.x), 2)) for d, r in bad})[::3])
        print('POKE %-14s n=%3d maxh=%.3f restZ %.2f..%.2f restY %.2f..%.2f' % (tag, len(bad), max(d for d, r in bad), min(zs), max(zs), min(ys), max(ys)))
    return len(bad)
tot = check('rest')
kbs = head.data.shape_keys.key_blocks
for kb in kbs[1:]:
    bk = body.data.shape_keys.key_blocks.get(kb.name) if body.data.shape_keys else None      # the game drives same-named keys on every mesh
    for k in (kb, bk):
        if k: k.value = 1
    tot += check('key ' + kb.name)
    for k in (kb, bk):
        if k: k.value = 0
arm.animation_data_create()
for a in bpy.data.actions:
    if 'Key' in a.name: continue
    arm.animation_data.action = a; worst = 0
    if hasattr(arm.animation_data, 'action_slot') and a.slots: arm.animation_data.action_slot = a.slots[0]
    print('ACT', a.name, tuple(a.frame_range), bpy.app.version_string)
    for f in range(int(a.frame_range[0]), int(a.frame_range[1]) + 1):
        bpy.context.scene.frame_set(f); worst += check('%s f%d' % (a.name, f))
    tot += worst
print('POKE_TOTAL', tot)
