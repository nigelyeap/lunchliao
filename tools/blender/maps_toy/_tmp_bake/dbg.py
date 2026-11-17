import sys, numpy as np, bpy
src = open('/Users/nigelyeap/Documents/lunchliao-hd/tools/blender/maps_toy/bake_ao.py').read().split('# ---------------------------------------------------------------- bake')[0]
__file__ = '/Users/nigelyeap/Documents/lunchliao-hd/tools/blender/maps_toy/bake_ao.py'
exec(src)
tot = 0; lo = np.array([9., 9.]); hi = -lo; nl = nu = 0
for o in BAKE:
    me = o.data; n = len(me.loops); uv = np.empty(n * 2, np.float32); me.uv_layers['lightmap'].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    vi = np.empty(n, np.int32); me.loops.foreach_get('vertex_index', vi)
    lo = np.minimum(lo, uv.min(0)); hi = np.maximum(hi, uv.max(0)); nl += n
    nu += len(np.unique(np.c_[vi, uv.view(np.int32)], axis=0))
    pa = 0
    for p in me.polygons:
        ids = list(p.loop_indices); a = uv[ids]; x, y = a[:, 0], a[:, 1]; pa += abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))) / 2
    tot += pa
print('DBG uv bounds', lo, hi, 'uv area', tot, 'loops', nl, 'unique vert+uv', nu, 'verts', sum(len(o.data.vertices) for o in BAKE))
A3 = sum(p.area for o in BAKE for p in o.data.polygons)
print('DBG 3d area m2', round(A3), 'px per m at RES', round((tot * RES * RES / A3) ** .5, 1))
rows = []
for o in BAKE:
    me = o.data; n = len(me.loops); uv = np.empty(n * 2, np.float32); me.uv_layers['lightmap'].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    ua = 0
    for p in me.polygons:
        a = uv[list(p.loop_indices)]; ua += abs(np.dot(a[:, 0], np.roll(a[:, 1], 1)) - np.dot(a[:, 1], np.roll(a[:, 0], 1))) / 2
    s = o.matrix_world.to_scale()
    rows.append((sum(p.area for p in me.polygons), ua, o.name, tuple(round(x, 2) for x in s), len(me.polygons)))
for r in sorted(rows, reverse=True)[:20]: print('DBG %9.0f m2 uv %.4f %s scale %s faces %d' % r)
