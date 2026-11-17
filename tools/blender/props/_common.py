# Shared helpers for prop scripts. Run via: blender -b -P <prop>.py
# Blender coords: Z up, front faces -Y (exports as glTF +Z). 1 unit = 1 m.
import bpy, bmesh, math, os, json, sys
from mathutils import Vector, Matrix, Quaternion

ROOT = '/Users/nigelyeap/Documents/lunchliao-hd'
TEXDIR = ROOT + '/assets/tex/'
OUTDIR = ROOT + '/assets/props/'
# metres of world space covered by one tile of each texture (box-projected UVs)
TEXSCALE = {'floor_tile': 1.2, 'wall_tile': 1.6, 'steel_brushed': 0.6, 'formica': 0.8,
            'concrete_painted': 1.5, 'plywood': 1.0, 'plastic_blue': 0.5, 'plastic_red': 0.5}
SHARP = math.radians(38)
_mats = {}
TEXSLOTS = set()

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear(); TEXSLOTS.clear()

def lin(h):
    f = lambda v: (v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f((h >> 16 & 255) / 255), f((h >> 8 & 255) / 255), f((h & 255) / 255), 1.0)

def _occ_group():
    g = bpy.data.node_groups.get('glTF Material Output')
    if not g:
        g = bpy.data.node_groups.new('glTF Material Output', 'ShaderNodeTree')
        g.interface.new_socket('Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
    return g

def flat(name, hexc, rough=0.6, metal=0.0, emit=None, alpha=None):
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(hexc); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emit: b.inputs['Emission Color'].default_value = lin(emit[0]); b.inputs['Emission Strength'].default_value = emit[1]
    if alpha is not None:
        b.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    _mats[name] = m; return m

def tex(name):
    if name in _mats: return _mats[name]
    TEXSLOTS.add(name)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    def img(suffix, nc):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(f'{TEXDIR}{name}_{suffix}.png', check_existing=True)
        if nc: n.image.colorspace_settings.name = 'Non-Color'
        return n
    nt.links.new(img('basecolor', False).outputs['Color'], b.inputs['Base Color'])
    o = img('orm', True); sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(o.outputs['Color'], sp.inputs['Color'])
    nt.links.new(sp.outputs['Green'], b.inputs['Roughness']); nt.links.new(sp.outputs['Blue'], b.inputs['Metallic'])
    gn = nt.nodes.new('ShaderNodeGroup'); gn.node_tree = _occ_group(); nt.links.new(sp.outputs['Red'], gn.inputs['Occlusion'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(img('normal', True).outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    _mats[name] = m; return m

# ---- geometry ----
def _bevel(bm, bv, seg):
    if bv <= 0: return
    es = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > SHARP]
    bmesh.ops.bevel(bm, geom=es, offset=bv, segments=seg, profile=0.5, affect='EDGES', clamp_overlap=True)

def mk(name, bm, mat, loc=(0, 0, 0), rot=(0, 0, 0), group=None):
    bm.normal_update(); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces: f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > SHARP: e.smooth = False
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    if len(rot) == 4: ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = rot
    else: ob.rotation_euler = tuple(math.radians(a) for a in rot)
    ob.location = loc
    if group: ob['grp'] = group
    return ob

def box(name, sx, sy, sz, mat, loc=(0, 0, 0), rot=(0, 0, 0), bv=0.012, seg=1, group=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co.x *= sx; v.co.y *= sy; v.co.z *= sz
    _bevel(bm, min(bv, min(sx, sy, sz) * 0.35), seg)
    return mk(name, bm, mat, loc, rot, group)

def cyl(name, r, h, mat, loc=(0, 0, 0), rot=(0, 0, 0), r2=None, n=16, bv=0.006, seg=1, group=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n, radius1=r, radius2=r if r2 is None else r2, depth=h)
    _bevel(bm, min(bv, r * 0.4, h * 0.4), seg)
    return mk(name, bm, mat, loc, rot, group)

def sphere(name, rx, ry, rz, mat, loc=(0, 0, 0), rot=(0, 0, 0), n=10, group=None):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=n, v_segments=max(4, n // 2), radius=1.0)
    for v in bm.verts: v.co.x *= rx; v.co.y *= ry; v.co.z *= rz
    return mk(name, bm, mat, loc, rot, group)

def lathe(name, prof, mat, loc=(0, 0, 0), rot=(0, 0, 0), n=20, group=None):
    """prof: list of (radius, z) along the outline of a solid of revolution."""
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=n, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    return mk(name, bm, mat, loc, rot, group)

def arc(cx, cz, r, a0, a1, n):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

def limb(name, p0, p1, r0, r1, mat, n=8, group=None):
    a, b = Vector(p0), Vector(p1); d = b - a
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return cyl(name, r0, d.length, mat, tuple((a + b) / 2), tuple(q), r2=r1, n=n, bv=0, group=group)

def quad(name, w, h, loc, mat, rot=(0, 0, 0)):
    """Front-facing (-Y) quad, UV 0..1 bottom-left origin. Used for SIGN_* placeholders."""
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
    f = bm.faces.new(vs); uv = bm.loops.layers.uv.new('UVMap')
    for l, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uv].uv = t
    ob = mk(name, bm, mat, loc, rot); ob['keep'] = 1; return ob

# ---- finalize: merge by material, box-project UVs, export ----
def finalize(prop, pivots=None, keep_prefix=('SIGN_',)):
    pivots = pivots or {}
    obs = [o for o in bpy.data.objects if o.type == 'MESH']
    groups = {}
    for o in obs:
        if o.get('keep'): continue
        key = o.get('grp') or 'm:' + o.data.materials[0].name
        groups.setdefault(key, []).append(o)
    for key, lst in groups.items():
        bm = bmesh.new(); mats = []
        for o in lst:
            m = o.data.copy(); m.transform(o.matrix_basis)
            mt = o.data.materials[0]
            if mt not in mats: mats.append(mt)
            idx = mats.index(mt)
            for p in m.polygons: p.material_index = idx
            bm.from_mesh(m); bpy.data.meshes.remove(m)
        bm.normal_update(); uv = bm.loops.layers.uv.verify()
        for f in bm.faces:
            sc = TEXSCALE.get(mats[f.material_index].name, 1.0); n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
            for l in f.loops:
                c = l.vert.co; a, b = {0: (c.y, c.z), 1: (c.x, c.z), 2: (c.x, c.y)}[ax]
                l[uv].uv = (a / sc, b / sc)
        name = key if not key.startswith('m:') else f'{prop}__{key[2:]}'
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        for mt in mats: me.materials.append(mt)
        if key in pivots:
            p = Vector(pivots[key]); me.transform(Matrix.Translation(-p))
        ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
        if key in pivots: ob.location = p
        ob['done'] = 1
    for o in obs:
        if not o.get('keep'): bpy.data.objects.remove(o, do_unlink=True)
    tris = 0; nodes = []
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        nodes.append(o.name); tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    os.makedirs(OUTDIR, exist_ok=True)
    path = OUTDIR + prop + '.glb'
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_yup=True, export_cameras=False, export_lights=False, export_image_format='AUTO')
    mf = OUTDIR + 'manifest.json'
    d = json.load(open(mf)) if os.path.exists(mf) else {}
    d[prop] = {'tris': tris, 'nodes': sorted(nodes), 'tex_slots': sorted(TEXSLOTS), 'flat_mats': sorted(k for k in _mats if k not in TEXSLOTS), 'bytes': os.path.getsize(path)}
    json.dump(d, open(mf, 'w'), indent=1)
    print('EXPORTED', prop, 'tris', tris, 'bytes', os.path.getsize(path))
