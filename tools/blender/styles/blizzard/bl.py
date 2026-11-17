"""Blender-side helpers: numpy mesh in/out, colour attributes, materials, tubes, caching of SDF grids."""
import bpy, os, sys, math, hashlib, inspect, glob, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
import sdf
CACHE = '/tmp/lunchliao-scratch/cache_blizzard'
os.makedirs(CACHE, exist_ok=True)

def hexs(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

def lin(c):
    c = hexs(c) if isinstance(c, str) else np.asarray(c, np.float32)
    return np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92).astype(np.float32)

def cached(fn, dep=''):
    """fn() -> sdf.Grid. Cached on the function source, sdf.py and dep."""
    key = hashlib.md5((inspect.getsource(fn) + open(os.path.join(HERE, 'sdf.py')).read() + dep).encode()).hexdigest()[:12]
    path = f'{CACHE}/{fn.__name__}_{key}.npz'
    if os.path.exists(path):
        z = np.load(path); g = sdf.Grid.__new__(sdf.Grid)
        g.lo = z['lo']; g.h = float(z['h']); g.d = z['d']; g.n = np.array(g.d.shape)
        g.ax = [g.lo[i] + g.h * np.arange(g.n[i], dtype=np.float32) for i in range(3)]
        return g
    for old in glob.glob(f'{CACHE}/{fn.__name__}_*.npz'): os.remove(old)
    g = fn(); np.savez(path, lo=g.lo, h=g.h, d=g.d); return g

def prune(V, T, Q, kill):
    T = T[~kill[T].all(1)]; Q = Q[~kill[Q].all(1)] if len(Q) else Q
    used = np.zeros(len(V), bool); used[T] = True
    if len(Q): used[Q] = True
    idx = np.cumsum(used) - 1
    return V[used], idx[T], (idx[Q] if len(Q) else Q)

def mk(name, V, T, Q=None, parent=None):
    Q = np.zeros((0, 4), np.int32) if Q is None else Q
    me = bpy.data.meshes.new(name); nt, nq = len(T), len(Q)
    me.vertices.add(len(V)); me.vertices.foreach_set('co', np.asarray(V, np.float32).ravel())
    me.loops.add(3 * nt + 4 * nq)
    me.loops.foreach_set('vertex_index', np.concatenate([np.asarray(T).ravel(), np.asarray(Q).ravel()]).astype(np.int32))
    me.polygons.add(nt + nq)
    me.polygons.foreach_set('loop_start', np.concatenate([np.arange(nt) * 3, 3 * nt + np.arange(nq) * 4]).astype(np.int32))
    me.update(calc_edges=True); me.validate()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    if parent: ob.parent = parent
    smooth(ob); return ob

def smooth(ob):
    ob.data.polygons.foreach_set('use_smooth', np.ones(len(ob.data.polygons), bool)); ob.data.update()

def ctx(ob): return bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob])

def apply_mod(ob, m):
    with ctx(ob): bpy.ops.object.modifier_apply(modifier=m.name)

def tris(ob):
    return int(sum(len(p.vertices) - 2 for p in ob.data.polygons))

def decimate(ob, target):
    n = tris(ob)
    if n > target:
        d = ob.modifiers.new('dec', 'DECIMATE'); d.ratio = target / n; apply_mod(ob, d)
    smooth(ob); return ob

def lap_smooth(ob, it=2, f=0.5):
    m = ob.modifiers.new('sm', 'SMOOTH'); m.iterations = it; m.factor = f; apply_mod(ob, m)

def co(ob):
    a = np.zeros(len(ob.data.vertices) * 3, np.float32); ob.data.vertices.foreach_get('co', a); return a.reshape(-1, 3)

def nrm(ob):
    a = np.zeros(len(ob.data.vertices) * 3, np.float32); ob.data.vertex_normals.foreach_get('vector', a); return a.reshape(-1, 3)

def set_col(ob, rgb, name='Col', alpha=None):
    rgb = np.asarray(rgb, np.float32)
    if rgb.ndim == 1: rgb = np.repeat(rgb[None], len(ob.data.vertices), 0)
    a = ob.data.color_attributes.get(name) or ob.data.color_attributes.new(name, 'FLOAT_COLOR', 'POINT')
    a.data.foreach_set('color', np.c_[rgb, np.ones(len(rgb), np.float32) if alpha is None else alpha].astype(np.float32).ravel())

def set_uv(ob, uv_per_vert):
    """Per-vertex uv (N,2) copied to loops."""
    me = ob.data; l = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    vi = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', vi)
    l.data.foreach_set('uv', np.asarray(uv_per_vert, np.float32)[vi].ravel())

def save_png(path, rgb):
    """rgb: (H, W, 3) sRGB floats, row 0 at the top."""
    h, w = rgb.shape[:2]; img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    px = np.ones((h, w, 4), np.float32); px[..., :3] = np.clip(rgb[::-1], 0, 1); img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path; img.file_format = 'PNG'; img.save(); return img

def mat(name, col=None, tex=None, flat=None, rough=.6, metal=0., sss=0., coat=0., alpha=1., spec=.5, emit=0., sheen=0.):
    """col=None reads the 'Col' vertex colour. tex multiplies it."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    if col is None:
        a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'Col'; src = a.outputs['Color']
    else:
        r = nt.nodes.new('ShaderNodeRGB'); r.outputs[0].default_value = (*lin(col), 1); src = r.outputs[0]
    if tex is not None:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = tex; tsrc = t.outputs['Color']
        if flat is not None:   # vertex alpha masks the texture (0 = flat colour)
            fm = nt.nodes.new('ShaderNodeMix'); fm.data_type = 'RGBA'; fm.inputs[6].default_value = (*lin(flat), 1)
            nt.links.new(a.outputs['Alpha'], fm.inputs[0]); nt.links.new(tsrc, fm.inputs[7]); tsrc = fm.outputs[2]
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
        nt.links.new(tsrc, mx.inputs[6]); nt.links.new(src, mx.inputs[7]); src = mx.outputs[2]
    nt.links.new(src, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss; b.inputs['Subsurface Radius'].default_value = (1.0, .35, .2)
        b.inputs['Subsurface Scale'].default_value = .03
    if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .05
    if sheen: b.inputs['Sheen Weight'].default_value = sheen
    if emit: nt.links.new(src, b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emit
    if alpha < 1: b.inputs['Alpha'].default_value = alpha; m.surface_render_method = 'BLENDED'
    return m

def use(ob, m): ob.data.materials.clear(); ob.data.materials.append(m); return ob

def tube_mesh(name, pts, r, closed=False, res=3, parent=None, radii=None):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = res; cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1); sp.use_cyclic_u = closed
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1); sp.points[i].radius = 1 if radii is None else radii[i]
    tmp = bpy.data.objects.new(name + '_c', cu); bpy.context.scene.collection.objects.link(tmp)
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    if parent: ob.parent = parent
    smooth(ob); return ob

def prim(name, op, parent=None, **kw):
    getattr(bpy.ops.mesh, op)(**kw); ob = bpy.context.object; ob.name = name
    if parent: ob.parent = parent
    smooth(ob); return ob

def join(obs, name):
    with bpy.context.temp_override(active_object=obs[0], selected_editable_objects=obs, selected_objects=obs, object=obs[0]):
        bpy.ops.object.join()
    obs[0].name = name; return obs[0]

def smooth_path(pts, n=40):
    """Catmull-Rom resample of a polyline."""
    P = np.asarray(pts, np.float32); P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]]); out = []
    seg = len(P) - 3
    for t in np.linspace(0, seg, n, endpoint=True):
        i = min(int(t), seg - 1); u = t - i; p0, p1, p2, p3 = P[i:i + 4]
        out.append(.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return np.array(out, np.float32)

def mirror(V, T, Q):
    V = V.copy(); V[:, 0] *= -1; return V, T[:, ::-1].copy(), (Q[:, ::-1].copy() if Q is not None and len(Q) else Q)

def rotz(V, deg, pivot):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a); p = np.asarray(pivot, np.float32); W = V - p
    return np.stack([c * W[:, 0] - s * W[:, 1], s * W[:, 0] + c * W[:, 1], W[:, 2]], 1) + p

def bake(hi, lo, stem, size=2048, kinds=('NORMAL',), ext=0.02):
    """Cycles selected-to-active bake of hi onto lo (new 'bake' UV layer). Wires the maps into lo's material, removes hi."""
    sc = bpy.context.scene; eng = sc.render.engine; sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.device = 'CPU'
    bpy.context.view_layer.update(); me = lo.data
    uv = me.uv_layers.new(name='bake'); keep = me.uv_layers[0].name; me.uv_layers.active = uv
    for o in bpy.context.view_layer.objects: o.select_set(False)
    lo.select_set(True); bpy.context.view_layer.objects.active = lo
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003); bpy.ops.object.mode_set(mode='OBJECT')
    me.uv_layers[keep].active_render = True
    nt = lo.active_material.node_tree; b = nt.nodes['Principled BSDF']
    un = nt.nodes.new('ShaderNodeUVMap'); un.uv_map = 'bake'; done = []
    for kind in kinds:
        img = bpy.data.images.new(os.path.basename(stem) + '_' + kind.lower(), size, size, alpha=False)
        if kind == 'NORMAL': img.colorspace_settings.name = 'Non-Color'
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; nt.links.new(un.outputs[0], n.inputs[0]); nt.nodes.active = n
        hi.select_set(True); lo.select_set(True); bpy.context.view_layer.objects.active = lo
        kw = dict(pass_filter={'COLOR'}) if kind == 'DIFFUSE' else {}
        bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=ext, max_ray_distance=ext * 2.5, margin=8, **kw)
        img.filepath_raw = stem + '_' + kind.lower() + '.png'; img.file_format = 'PNG'; img.save(); done.append((kind, n))
    for kind, n in done:
        if kind == 'NORMAL':
            nm = nt.nodes.new('ShaderNodeNormalMap'); nm.uv_map = 'bake'; nt.links.new(n.outputs[0], nm.inputs['Color']); nt.links.new(nm.outputs[0], b.inputs['Normal'])
        else: nt.links.new(n.outputs[0], b.inputs['Base Color'])
    bpy.data.objects.remove(hi); sc.render.engine = eng
