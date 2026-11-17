"""First-person viewmodels cut from the toy heroes.
Run: blender -b -P vm_build.py -- <key ...|all> [quick] [norender]
For each hero: imports assets/heroes/<key>.glb, cuts the hands (with any cuff detail near the wrist) and the held prop,
moves them into the camera space of play/chope.html make() (same P, rest.R, rest.L as the procedural builder),
adds a forearm running back out of view (arm() direction) with the team wristband, and writes
assets/viewmodels/<key>.glb with meshes R, L, A (vertices local to their own pivot, objects at identity)
plus a check render from the game camera (fov 78 vertical, 16:9) at shots/viewmodels_toy/<key>.png.
Material names kept from the hero. 'team' is the team colour slot, 'skin*' the hero skin.
Coordinates: configs are in three.js camera space (x right, y up, -z forward). tb() maps them to Blender (x, -z, y);
the glTF Y-up export maps them back."""
import bpy, bmesh, sys, os, math
from mathutils import Vector as V, Matrix, Euler

HD = os.path.dirname(os.path.abspath(__file__))
RT = os.path.abspath(os.path.join(HD, '..', '..', '..'))
HEROES = os.path.join(RT, 'assets', 'heroes'); OUTG = os.path.join(RT, 'assets', 'viewmodels'); SHOTS = os.path.join(RT, 'shots', 'viewmodels_toy')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['all']
QUICK = 'quick' in ARGS; NORENDER = 'norender' in ARGS
ALL = 'ahma uncle nsboy engineer gym rascal debater tarik rider dj lens siao ice'.split()
KEYS = [k for k in ARGS if k in ALL] or ALL
os.makedirs(OUTG, exist_ok=True); os.makedirs(SHOTS, exist_ok=True)

def tb(p): return V((p[0], -p[2], p[1]))
def srgb(h):
    c = [int(h.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c)
def newmat(name, hexcol, rough=.4, metal=0.0, coat=0.0, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(hexcol), 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat
    if emit:
        b.inputs['Emission Color'].default_value = (*srgb(hexcol), 1); b.inputs['Emission Strength'].default_value = emit
    return m

# tris allowed: the count before the weapon redesign plus 20%, never more than 12k
BUDGET = dict(ahma=12000, debater=9578, dj=12000, engineer=8844, gym=11558, ice=9151, lens=9636, nsboy=8630, rascal=5972, rider=7570, siao=10681, tarik=9440, uncle=9834)

# ---------------------------------------------------------------- per-hero config (three.js camera space)
# P: rig position. hr: right hand point in R space. rl: rest.L. s: hero -> viewmodel scale.
# R/L: (side, groups, extra) cut lists. side picks which transform. mode 'shared' = one transform for both hands
# (they hold one prop), else each hand gets its own transform anchored on its hand centroid.
# rot_r/rot_l: Euler degrees (Blender axes, about the hand anchor) applied after the scale.
C = {
    'ahma': dict(cuff=1, P=(0, -.30, -.60), mode='shared', hr=(.28, .01, .06), s=.653, both_in_R=True, objs_r=['walker'], rc=.075),
    'uncle': dict(P=(.24, -.25, -.46), rl=(-.52, -.07, -.02), lo=(.10, .17, -.24), s=.72, rot_l=(0, 0, -10)),
    'nsboy': dict(P=(.25, -.32, -.50), rl=(-.07, .03, -.34), s=.78),
    'engineer': dict(P=(.24, -.28, -.48), rl=(-.50, -.10, -.04), s=.72),
    'gym': dict(P=(0, -.37, -.58), rl=(-.125, -.02, .04), mode='gym', s=.60),
    'rascal': dict(P=(.20, -.24, -.42), rl=(-.44, -.06, -.04), s=.95, rc=0, wcut=.02, fa_in=.03, a_groups_r=['handslot.r'], rot_l=(-25, 0, 25), rot_r=(-20, 0, 0)),
    'debater': dict(cuff=1, P=(.24, -.27, -.48), rl=(-.46, -.04, -.04), s=.66),
    'tarik': dict(cuff=1, P=(.22, -.28, -.50), rl=(-.44, -.06, -.04), s=.62, objs_r=['jug'], objs_l=['mug']),
    'rider': dict(P=(.24, -.27, -.48), rl=(-.44, -.06, -.04), s=.72),
    'dj': dict(P=(.24, -.27, -.48), rl=(-.44, -.06, -.04), s=.62, no_slot=True),
    'lens': dict(P=(.25, -.30, -.50), rl=(-.07, .03, -.34), mode='shared', s=.66, slot_r=['prop']),
    'siao': dict(P=(0, -.37, -.58), mode='two', hr=(.19, .13, -.05), rl=(-.125, -.02, .04), lo=(-.065, .15, -.09), s=.98, rc=0, wcut=.035, fa_in=.035),
    'ice': dict(P=(.24, -.27, -.48), rl=(-.44, -.06, -.04), s=.64),
}

# ---------------------------------------------------------------- import and cut
def load(key):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HEROES, key + '.glb'))
    new = [o for o in bpy.data.objects if o not in before]
    rig = next(o for o in new if o.type == 'ARMATURE')
    meshes = [o for o in new if o.type == 'MESH' and o.vertex_groups]
    keep = [o for o in new if not (o.type == 'MESH' and not o.vertex_groups)]
    for o in new:
        if o not in keep: bpy.data.objects.remove(o)
    H = dict(key=key, rig=rig, meshes=meshes, new=keep)
    bpy.context.view_layer.update()
    for o in meshes:   # dominant group per vertex, cached
        names = {g.index: g.name for g in o.vertex_groups}
        o['dom'] = [names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in o.data.vertices]
    return H

def bone(H, name, tail=False):
    b = H['rig'].data.bones[name]; return H['rig'].matrix_world @ (b.tail_local if tail else b.head_local)

def hmat(H, name):
    for o in H['meshes']:
        for m in o.data.materials:
            if m and (m.name == name or m.name.split('.')[0] == name): return m
    raise KeyError(name)

def cut(H, name, sel):
    """sel(obj_short_name, group, world_centroid, mat_name) -> bool. Returns one object in world coords, or None."""
    parts = []
    for o in H['meshes']:
        dom = o['dom']; M = o.matrix_world.copy(); short = o.name.split('_', 1)[-1]
        me = o.data.copy(); bm = bmesh.new(); bm.from_mesh(me); kill = []
        mats = [m.name if m else '' for m in o.data.materials]
        for f in bm.faces:
            gs = [dom[v.index] for v in f.verts]; g = max(set(gs), key=gs.count)
            if not sel(short, g, M @ f.calc_center_median(), mats[f.material_index] if mats else ''): kill.append(f)
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        n = len(bm.faces); bm.to_mesh(me); bm.free()
        if not n: bpy.data.meshes.remove(me); continue
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
        if me.shape_keys: ob.shape_key_clear()
        ob.vertex_groups.clear(); me.transform(M); parts.append(ob)
    return join(parts, name)

def join(parts, name):
    parts = [p for p in parts if p]
    if not parts: return None
    if len(parts) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for p in parts: p.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    ob = parts[0]; ob.name = name; ob.data.name = name; return ob

def centroid(H, group):
    s = V(); n = 0
    for o in H['meshes']:
        for v, g in zip(o.data.vertices, o['dom']):
            if g == group: s += o.matrix_world @ v.co; n += 1
    return s / n

def forearm_info(H, sd):
    """radius of the lower arm near the wrist and its sleeve material (most common on the elbow half)."""
    W = bone(H, 'hand.' + sd); E = bone(H, 'lowerarm.' + sd); ax = (W - E).normalized(); L = (W - E).length
    rs = []; cnt = {}
    for o in H['meshes']:
        M = o.matrix_world; dom = o['dom']
        for v, g in zip(o.data.vertices, dom):
            if g != 'lowerarm.' + sd: continue
            p = M @ v.co; t = (p - E).dot(ax)
            if .3 * L < t < .9 * L: rs.append((p - E - ax * t).length)
        for f in o.data.polygons:
            if dom[f.vertices[0]] == 'lowerarm.' + sd and (M @ f.center - E).dot(ax) < .5 * L and o.data.materials:
                m = o.data.materials[f.material_index]; cnt[m] = cnt.get(m, 0) + 1
    rs.sort()
    return (rs[len(rs) // 2] if rs else .05), max(cnt, key=cnt.get)

# ---------------------------------------------------------------- primitives (Blender coords)
def frame(d):
    d = d.normalized(); u = d.cross(V((0, 0, 1)) if abs(d.z) < .9 else V((1, 0, 0))).normalized(); return d, u, d.cross(u)

def mesh_from(name, verts, faces, mat, uvs=None, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.materials.append(mat)
    if uvs:
        uv = me.uv_layers.new(name='UVMap')
        for p in me.polygons:
            for li, vi in zip(p.loop_indices, p.vertices): uv.data[li].uv = uvs[vi]
    me.polygons.foreach_set('use_smooth', [smooth] * len(me.polygons)); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return ob

def tube(name, W, d, r0, length, mat, seg=20, rings=2, grow=.12):
    """round-nosed tube from W (nose inside the hand) along d, UVs so prints keep their aspect."""
    d, u, w = frame(d); verts = []; uvs = []; prof = []
    for i in range(5):                                   # hemisphere nose
        a = math.pi / 2 * (1 - i / 4); prof.append((-math.sin(a) * r0 * .9, math.cos(a) * r0 if i else .002))
    for j in range(1, rings + 1):
        t = j / rings; prof.append((t * length, r0 * (1 + grow * t)))
    for k, (x, r) in enumerate(prof):
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append(W + d * x + (u * math.cos(a) + w * math.sin(a)) * r); uvs.append((i / seg * 1.0, x / (2 * math.pi * r0)))
    faces = [(k * seg + i, k * seg + (i + 1) % seg, (k + 1) * seg + (i + 1) % seg, (k + 1) * seg + i) for k in range(len(prof) - 1) for i in range(seg)]
    faces.append(tuple(range((len(prof) - 1) * seg, len(prof) * seg))[::-1])
    return mesh_from(name, verts, faces, mat, uvs)

def torus(name, C, axis, R, r, mat, seg=24, rseg=8):
    d, u, w = frame(axis); verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; e = u * math.cos(a) + w * math.sin(a)
        for j in range(rseg):
            b = 2 * math.pi * j / rseg; verts.append(C + e * (R + r * math.cos(b)) + d * r * math.sin(b))
    faces = [(i * rseg + j, i * rseg + (j + 1) % rseg, ((i + 1) % seg) * rseg + (j + 1) % rseg, ((i + 1) % seg) * rseg + j) for i in range(seg) for j in range(rseg)]
    return mesh_from(name, verts, faces, mat)

def rbox(name, C, size, mat, bev=.012, rot=(0, 0, 0), basis=None, bseg=3):
    """rounded box, size in Blender axes, rot Euler radians, or basis = three axis vectors for the box x, y, z."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = V((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=bev, segments=bseg, profile=.5, affect='EDGES')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.transform(Matrix.Translation(C) @ (Matrix(basis).transposed() if basis else Euler(rot).to_matrix()).to_4x4())
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob

def lathe(name, C, axis, prof, mat, seg=32, smooth=True, a0=0.0):
    """prof: [(along, radius)] revolved round axis from C."""
    d, u, w = frame(axis); verts = []
    for x, r in prof:
        for i in range(seg):
            a = a0 + 2 * math.pi * i / seg; verts.append(C + d * x + (u * math.cos(a) + w * math.sin(a)) * max(r, 1e-4))
    faces = [(k * seg + i, k * seg + (i + 1) % seg, (k + 1) * seg + (i + 1) % seg, (k + 1) * seg + i) for k in range(len(prof) - 1) for i in range(seg)]
    return mesh_from(name, verts, faces, mat, smooth=smooth)

def rod(name, a, b, r, mat, seg=12, r2=None, smooth=True):
    """capped stick from a to b. seg=4 with smooth=False gives a square stick."""
    L = (b - a).length; r2 = r if r2 is None else r2; e = min(r, r2) * (.25 if smooth else 0)
    prof = [(0, 0), (0, r - e), (e, r), (L - e, r2), (L, r2 - e), (L, 0)] if smooth else [(0, 0), (0, r), (L, r2), (L, 0)]
    return lathe(name, a, b - a, prof, mat, seg, smooth, math.pi / 4 if seg == 4 else 0)

def P3(x, y, z): return tb((x, y, z))

def ball(name, C, r, mat, seg=24, rings=14, scl=(1, 1, 1)):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    for v in bm.verts: v.co = V((v.co.x * scl[0], v.co.y * scl[1], v.co.z * scl[2])) + C
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob

def xform(ob, M):
    if ob: ob.data.transform(M); ob.data.update()
    return ob

def mirror_x(ob):
    ob.data.transform(Matrix.Scale(-1, 4, V((1, 0, 0)))); ob.data.flip_normals(); ob.data.update(); return ob

# ---------------------------------------------------------------- build one hero
TEAM = None
def arm_dir(sd): return tb(((1 if sd == 'r' else -1) * .45, -.55, .70)).normalized()

def T_of(anchor, target, s, rot=(0, 0, 0)):
    return Matrix.Translation(target) @ Matrix.Scale(s, 4) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4() @ Matrix.Translation(-anchor)

def hand_cut(H, sd, cfg, extra_groups=(), objs=(), lower_mats=()):
    """hand.<sd> faces, cuff faces of lowerarm within rc of the wrist, slot groups and whole prop objects."""
    W = bone(H, 'hand.' + sd); rc = cfg.get('rc', .06)
    groups = {'hand.' + sd} | set(extra_groups)
    ax = (W - bone(H, 'lowerarm.' + sd)).normalized()
    def sel(short, g, c, m):
        if short in objs: return True
        if g == 'hand.' + sd and rc == 0 and cfg.get('wcut', .005) > 0 and (c - W).dot(ax) < cfg.get('wcut', .005): return False   # clean wrist cut on bare arms
        if g in groups: return True
        if g == 'lowerarm.' + sd and ((c - W).length < rc or m in lower_mats): return True
        return False
    return cut(H, 'hand_' + sd, sel)

def add_forearm(H, sd, M, s, parts, out_space):
    """forearm tube and team band from the transformed wrist along the arm() direction."""
    r, m = forearm_info(H, sd); W = M @ bone(H, 'hand.' + sd); d = arm_dir(sd); r = min(r * s, .043)
    W = W - d * C[H['key']].get('fa_in', 0)
    parts.append(tube('fa_' + sd, W - out_space, d, r, .55, m))
    parts.append(torus('band_' + sd, W - out_space + d * (r * 1.25 + .015), d, r * 1.06, .013, TEAM))
    if C[H['key']].get('cuff'): parts.append(torus('cuff_' + sd, W - out_space + d * .006, d, r * 1.06, .012, m))

def build(key):
    global TEAM
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cfg = C[key]; H = load(key); s = cfg['s']
    TEAM = newmat('team', '#1AA3E8', .4, coat=.3)
    mode = cfg.get('mode', 'indep'); R, L, A = [], [], []
    a_mats = set(cfg.get('a_mats', [])); a_groups = set(cfg.get('a_groups_r', []))
    slot_r = cfg.get('slot_r', [] if cfg.get('no_slot') else ['handslot.r'])
    slot_l = [] if cfg.get('no_slot') else ['handslot.l']
    objs_r = cfg.get('objs_r', []); objs_l = cfg.get('objs_l', [])
    rl = tb(cfg.get('rl', (0, 0, 0)))

    def split_A(ob):
        """move faces matching a_mats / a_groups into a new object."""
        if not ob or not (a_mats or a_groups): return ob, None
        return ob, None

    if mode in ('shared',):
        anchor = centroid(H, 'hand.r'); hr = tb(cfg.get('hr', (0, 0, 0)))
        rot = cfg.get('rot', (0, 0, 0))
        M = T_of(anchor, hr, s, rot)
        if cfg.get('both_in_R'):
            hr_ob = hand_cut(H, 'r', cfg, slot_r, objs_r); hl_ob = hand_cut(H, 'l', cfg, slot_l, objs_r)
            R += [xform(hr_ob, M), xform(hl_ob, M)]
            add_forearm(H, 'r', M, s, R, V()); add_forearm(H, 'l', M, s, R, V())
        else:
            gs = cfg.get('gs', 1.0)   # prop-only scale about the right hand, the left hand slides along with it
            Mp = Matrix.Translation(hr) @ Matrix.Scale(gs, 4) @ Matrix.Translation(-hr) @ M
            Ml_ = Matrix.Translation((gs - 1) * (M @ centroid(H, 'hand.l') - hr)) @ M
            if a_mats or a_groups:
                A.append(xform(cut(H, 'ammo', lambda sh, g, c, m: m.split('.')[0] in a_mats or g in a_groups), Mp))
            R.append(xform(cut(H, 'prop', lambda sh, g, c, m: g in slot_r or sh in objs_r), Mp))
            R.append(xform(hand_cut(H, 'r', cfg, (), ()), M)); add_forearm(H, 'r', M, s, R, V())
            hl_ob = hand_cut(H, 'l', cfg, slot_l, objs_l)
            L.append(xform(hl_ob, Matrix.Translation(-rl) @ Ml_)); add_forearm(H, 'l', Ml_, s, L, rl)
    elif mode == 'gym':
        gym_build(H, cfg, R, L)
    else:   # indep and two: each hand anchored on its own centroid
        hr = tb(cfg.get('hr', (0, 0, 0)))
        Mr = T_of(centroid(H, 'hand.r'), hr, s, cfg.get('rot_r', (0, 0, 0)))
        Ml = T_of(centroid(H, 'hand.l'), tb(cfg.get('lo', (0, 0, 0))), s, cfg.get('rot_l', (0, 0, 0)))
        if a_mats or a_groups:
            A.append(xform(cut(H, 'ammo', lambda sh, g, c, m: g in ('handslot.r',) and (m.split('.')[0] in a_mats or g in a_groups)), Mr))
        R.append(xform(hand_cut(H, 'r', cfg, slot_r, objs_r), Mr)); add_forearm(H, 'r', Mr, s, R, V())
        L.append(xform(hand_cut(H, 'l', cfg, slot_l, objs_l, cfg.get('l_lower_mats', ())), Ml)); add_forearm(H, 'l', Ml, s, L, V())
        HOOKS.get(key, lambda *a: None)(H, cfg, R, L, A, Mr, Ml)

    # over budget: thin the cut hands only, props stay clean (ahma's walker)
    R, L, A = ([o for o in l if o] for l in (R, L, A))
    tot = sum(tris(o) for o in R + L + A); hands = [o for o in R + L if o.name.startswith('hand_')]; ht = sum(tris(o) for o in hands)
    if tot > BUDGET[key] and hands:
        for o in hands:
            o.modifiers.new('d', 'DECIMATE').ratio = max(.25, 1 - (tot - BUDGET[key] * .97) / ht)
            bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier='d')
    # remove A faces from R (they were cut twice when the ammo is part of the slot group)
    Rob = join(R, 'R'); Lob = join(L, 'L'); Aob = join(A, 'A')
    if Aob and (a_mats or a_groups):
        strip(Rob, lambda m, c: m.split('.')[0] in a_mats or c in a_groups, a_groups)
    for o in list(bpy.data.objects):
        if o not in (Rob, Lob, Aob): bpy.data.objects.remove(o)
    for ob in (Rob, Lob, Aob):
        if ob: finish(ob)
    tot = sum(tris(o) for o in (Rob, Lob, Aob))
    if tot > BUDGET[key]: print('VM OVER BUDGET', key, tot, BUDGET[key])
    return Rob, Lob, Aob

def strip(ob, test, a_groups):
    """drop ammo faces from R by material (group info is gone after the cut, so A-by-group heroes tag via material set)."""
    mats = [m.name if m else '' for m in ob.data.materials]
    bm = bmesh.new(); bm.from_mesh(ob.data)
    kill = [f for f in bm.faces if test(mats[f.material_index], None)]
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(ob.data); bm.free()

def finish(ob):
    me = ob.data
    for i, m in enumerate(me.materials):     # merge duplicate slots of the same material
        pass
    me.update()

def gym_build(H, cfg, R, L):
    """ball (from the toy) centred in R, the toy right hand pressed on its right side, mirrored for the left."""
    s = cfg['s']; bc = centroid(H, 'handslot.r')
    br = .13; bm_ = hmat(H, 'ball'); bl = hmat(H, 'bline')
    R.append(ball('ball', V(), br, bm_, seg=48, rings=24))
    for ax in (V((1, 0, 0)), V((0, 1, 0)), V((.7, 0, .7))): R.append(torus('bl', V(), ax, br * .995, .005, bl, seg=64, rseg=6))
    ballo = None
    rot = Euler([math.radians(a) for a in cfg.get('rot', (0, 0, 0))]).to_matrix().to_4x4()
    Mb = Matrix.Translation(V()) @ Matrix.Scale(s, 4) @ Matrix.Translation(-bc)
    R.append(xform(ballo, Mb))
    br = .21 * s
    # hand: anchor on the palm centre, turn so the palm (which faces up under the ball in the toy) faces -x (the ball)
    hc = centroid(H, 'hand.r')
    Mh = Matrix.Translation(tb((.125, -.02, .04)) + V((.0, 0, 0))) @ Matrix.Scale(s * 1.0, 4) @ Euler([math.radians(a) for a in cfg.get('hrot', (0, -90, 0))]).to_matrix().to_4x4() @ Matrix.Translation(-hc)
    h = hand_cut(H, 'r', dict(rc=.0))
    R.append(xform(h, Mh)); add_forearm(H, 'r', Mh, s, R, V())
    hl = hand_cut(H, 'r', dict(rc=.0)); xform(hl, Mh); mirror_x(hl)
    rl = tb((-.125, -.02, .04)); xform(hl, Matrix.Translation(-rl)); L.append(hl)
    r, m = forearm_info(H, 'r'); W = Mh @ bone(H, 'hand.r'); W = V((-W.x, W.y, W.z))
    L.append(tube('fa_l', W - rl, arm_dir('l'), r * s, .55, m)); d = arm_dir('l')
    L.append(torus('band_l', W - rl + d * (r * s * 1.25 + .015), d, r * s * 1.06, .013, TEAM))

# ---------------------------------------------------------------- per-hero extras
def clear(*lists):
    for l in lists:
        for o in l: bpy.data.objects.remove(o)
        l.clear()

def fist(H, sd, out, pos, s, skin, sleeve, rot=(0, 0, 0), r=None, d=None, band=True):
    """siao's closed fist (thumb up, knuckles forward, recoloured) centred on pos, with forearm and team band.
    Returns wrist point, forearm direction and forearm radius."""
    S = H.get('_S') or load('siao'); H['_S'] = S
    f = hand_cut(S, sd, dict(rc=0, wcut=.02))
    W0 = bone(S, 'hand.' + sd); ax = (W0 - bone(S, 'lowerarm.' + sd)).normalized()   # straight wrist rim, the face cut is jagged
    bm = bmesh.new(); bm.from_mesh(f.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=W0 + ax * .045, plane_no=ax, clear_inner=True)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bm.to_mesh(f.data); bm.free()
    for i in range(len(f.data.materials)): f.data.materials[i] = skin
    M = T_of(centroid(S, 'hand.' + sd), pos, s, rot); out.append(xform(f, M))
    d = (d or arm_dir(sd)).normalized(); r = r or min(forearm_info(S, sd)[0] * s, .043) * 1.08
    W = M @ bone(S, 'hand.' + sd) - d * .04 * s
    out.append(tube('fa_' + sd, W, d, r, .55, sleeve))
    if band: out.append(torus('band_' + sd, W + d * (r * 1.25 + .015), d, r * 1.06, .013, TEAM))
    return W, d, r

def hook_uncle(H, cfg, R, L, A, Mr, Ml):
    """Booger Flick: right fist with the index finger out and a booger on the tip (A). The left hand keeps the toy's kopi bag."""
    clear(R); skin = hmat(H, 'skin'); g = hmat(H, 'green')
    fist(H, 'r', R, V(), .72, skin, skin)
    a, b = P3(-.03, .035, -.02), P3(-.055, .085, -.125)
    R.append(rod('finger', a, b, .017, skin, r2=.0145)); R.append(ball('ftip', b, .0145, skin, seg=12, rings=8))
    R.append(ball('nail', b + P3(.0, .009, .004), .0095, newmat('nail', '#F2D2BC', .3), seg=10, rings=6, scl=(1, 1.2, .5)))
    A.append(ball('booger', b + P3(-.004, .012, -.016), .024, g, seg=14, rings=10, scl=(1, 1.1, .9)))
    A.append(ball('drip', b + P3(-.002, -.012, -.018), .012, g, seg=10, rings=6, scl=(1, 1, 1.5)))
    A.append(ball('blob', b + P3(.012, .022, -.03), .011, g, seg=10, rings=6))

def hook_nsboy(H, cfg, R, L, A, Mr, Ml):
    """Rubber Band Rifle: level toy rifle, barrel forward. A red band runs along the top from the muzzle post back to a
    clothes peg (A), spare bands sit round the fore-end. Right fist on the grip, left fist on the foregrip."""
    clear(R, L); skin = hmat(H, 'skin'); g = hmat(H, 'gun'); g2 = hmat(H, 'gun2'); sg = hmat(H, 'sight'); bd = hmat(H, 'band')
    peg = newmat('peg', '#D9B26F', .55); x = -.012; fy = V((0, 1, 0))
    R.append(rbox('grip', P3(x, -.02, .005), (.04, .052, .14), g, rot=(math.radians(-12), 0, 0)))
    R.append(rbox('recv', P3(x, .095, -.06), (.062, .50, .085), g, bev=.016))
    R.append(rbox('fore', P3(x, .085, -.40), (.076, .22, .076), g2, bev=.016))
    R.append(rod('barrel', P3(x, .10, -.50), P3(x, .10, -.68), .021, sg))
    R.append(torus('muzzle', P3(x, .10, -.675), fy, .021, .007, g2, seg=16, rseg=6))
    R.append(rod('foregrip', P3(x, .06, -.34), P3(x, -.075, -.34), .021, g))
    R.append(rbox('rail', P3(x, .148, -.08), (.03, .30, .022), sg, bev=.006))
    for z in (-.20, .03): R.append(rbox('railpost', P3(x, .135, z), (.02, .03, .03), sg, bev=.005))
    R.append(rbox('post', P3(x, .145, -.655), (.014, .018, .075), sg, bev=.004))
    R.append(rbox('peg', P3(x, .168, .13), (.03, .09, .026), peg, bev=.006, rot=(math.radians(8), 0, 0)))
    R.append(rod('pegspring', P3(x - .02, .168, .12), P3(x + .02, .168, .12), .008, hmat(H, 'buckle'), seg=8))
    for z in (-.305, -.33, -.47): R.append(torus('spare', P3(x, .085, z), fy, .057, .006, bd, seg=20, rseg=6))
    for sx in (-1, 1):   # the loaded band: two strands, post to peg
        A.append(rod('band', P3(x + sx * .009, .178, -.66), P3(x + sx * .013, .176, .10), .0065, bd, seg=6))
    A.append(rod('bandf', P3(x - .011, .178, -.662), P3(x + .011, .178, -.662), .0065, bd, seg=6))
    sl = forearm_info(H, 'r')[1]
    fist(H, 'r', R, V(), .78, skin, sl); fist(H, 'l', L, P3(x + .07, -.04, 0), .78, skin, sl)

def hook_engineer(H, cfg, R, L, A, Mr, Ml):
    """Foam Dart Ricochet: chunky navy and lime dart blaster in the right fist, a dart in the muzzle (A), spare darts
    clipped on the side. The left fist carries the toy's red toolbox by the handle, long face to the camera."""
    clear(R, L); skin = hmat(H, 'skin'); navy = hmat(H, 'navy'); nd = hmat(H, 'navy_dark'); lime = hmat(H, 'lime')
    wh = hmat(H, 'white'); st = hmat(H, 'steel'); dt = hmat(H, 'dart'); x = -.01; fy = V((0, 1, 0))
    def dart(out, x_, y_, z0, z1, k=1.0):
        out.append(rod('dart', P3(x_, y_, z0), P3(x_, y_, z1), .019 * k, wh, seg=10))
        out.append(ball('dtip', P3(x_, y_, z1 - .008 * k), .026 * k, dt, seg=12, rings=8, scl=(1, .7, 1)))
    R.append(rbox('grip', P3(x, -.02, .005), (.042, .055, .14), navy, rot=(math.radians(-12), 0, 0)))
    R.append(rbox('body', P3(x, .09, -.07), (.072, .30, .095), navy, bev=.018))
    R.append(rbox('slide', P3(x, .148, -.07), (.056, .27, .034), lime, bev=.012))
    R.append(lathe('barrel', P3(x, .095, -.19), fy, [(0, .03), (.01, .05), (.13, .05), (.15, .058), (.18, .058), (.185, .05), (.17, .03)], lime, seg=20))
    R.append(rod('bore', P3(x, .095, -.33), P3(x, .095, -.362), .031, nd, seg=14))
    R.append(torus('ring', P3(x, .095, -.335), fy, .058, .007, wh, seg=20, rseg=6))
    R.append(rod('primer', P3(x, .10, .07), P3(x, .10, .125), .013, st, seg=8))
    R.append(ball('knob', P3(x, .10, .135), .03, wh, seg=14, rings=8))
    R.append(torus('guard', P3(x, .025, -.075), V((1, 0, 0)), .03, .007, nd, seg=14, rseg=6))
    R.append(rbox('clip', P3(x - .04, .09, -.10), (.014, .05, .085), lime, bev=.005))
    for y_ in (.068, .112): dart(R, x - .052, y_, -.03, -.15, .72)
    dart(A, x, .095, -.33, -.44)
    fist(H, 'r', R, V(), .72, skin, skin)
    # toolbox under a level fist
    tbx = hmat(H, 'toolbox'); tbd = hmat(H, 'toolbox_dark'); gr = hmat(H, 'grip'); tape = hmat(H, 'tape')
    hp = P3(.05, .17, -.16); c = hp + P3(0, -.125, 0)
    fist(H, 'l', L, hp, .72, skin, skin, rot=cfg.get('rot_fist', (0, 90, 0)))
    L.append(rod('handle', hp + P3(-.085, 0, 0), hp + P3(.085, 0, 0), .014, gr, seg=10))
    for sx in (-1, 1): L.append(rod('hpost', hp + P3(sx * .08, 0, 0), hp + P3(sx * .08, -.06, 0), .011, gr, seg=8))
    L.append(rbox('box', c, (.27, .12, .105), tbx, bev=.014))
    L.append(rbox('lid', c + P3(0, .058, 0), (.28, .13, .034), tbd, bev=.012))
    L.append(rbox('tape', c + P3(0, -.012, 0), (.273, .123, .022), tape, bev=.004))
    for sx in (-1, 1): L.append(rbox('latch', c + P3(sx * .075, .035, .062), (.032, .012, .042), st, bev=.004))

def hook_rider(H, cfg, R, L, A, Mr, Ml):
    """Chopstick Fan: three pairs of disposable chopsticks fanned out of the right fist, each still half in its paper
    sleeve. The left fist holds the spare bundle in a rubber band, with the order phone strapped on the forearm."""
    clear(R, L); skin = hmat(H, 'skin'); wood = hmat(H, 'wood'); wrap = hmat(H, 'wrap'); green = hmat(H, 'green'); dg = hmat(H, 'dgreen')
    sl = hmat(H, 'sleeve'); el = math.radians(52)
    def pair(out, B, d, n=.40, s0=.09, s1=.23):
        d = d.normalized(); u = d.cross(V((0, 0, 1))).normalized()
        for k in (-1, 1): out.append(rod('stick', B + u * k * .0068, B + d * n + u * k * .0068, .0078, wood, seg=4, smooth=False))
        out.append(rod('sleeve', B + d * s0, B + d * s1, .019, wrap, seg=4, smooth=False))
        out.append(rod('print', B + d * (s1 - .05), B + d * (s1 - .022), .0195, green, seg=4, smooth=False))
    for a in (-24, 0, 24):
        a = math.radians(a); pair(R, P3(-.005, -.05, .01), P3(math.sin(a) * math.cos(el), math.sin(el), -math.cos(a) * math.cos(el)))
    for sd, out, pos in (('r', R, V()), ('l', L, P3(.03, .14, -.16))):
        W, d, r = fist(H, sd, out, pos, .72, skin, sl)
        out.append(tube('cuff_' + sd, W + d * .15, d, r * 1.22, .42, green)); out.append(torus('hem_' + sd, W + d * .155, d, r * 1.2, .009, dg, seg=20, rseg=6))
    # spare bundle: seven sleeved pairs
    B = P3(.03, .04, -.16); d = P3(.05, 1, -.12).normalized(); u, w = frame(d)[1:]
    for i in range(7):
        o = V() if i == 0 else (u * math.cos(i * math.pi / 3) + w * math.sin(i * math.pi / 3)) * .024
        h = .0 if i == 0 else .012 * math.sin(i * 2.3)
        L.append(rod('sleeve', B + o, B + o + d * (.215 + h), .0135, wrap, seg=4, smooth=False))
        L.append(rod('stick', B + o + d * (.2 + h), B + o + d * (.262 + h), .008, wood, seg=4, smooth=False))
    L.append(rod('print', B + d * .15, B + d * .185, .041, green, seg=6, smooth=False))
    L.append(torus('rubber', B + d * .135, d, .041, .006, newmat('rubber', '#D3202D', .35), seg=16, rseg=6))
    # phone on the forearm, screen up
    n = (V((0, 0, 1)) - d.dot(V((0, 0, 1))) * d); d = arm_dir('l'); n = (V((.25, -.2, 1)) - d * d.dot(V((.25, -.2, 1)))).normalized(); sdv = d.cross(n)
    c = W + d * .19 + n * (r * 1.22 + .012)
    L.append(rbox('case', c, (.078, .135, .016), hmat(H, 'case'), bev=.006, basis=(sdv, d, n)))
    L.append(rbox('screen', c + n * .008, (.064, .118, .004), hmat(H, 'screen'), bev=.0015, basis=(sdv, d, n)))
    L.append(rbox('pin', c + n * .011 - d * .02, (.02, .02, .003), newmat('pin', '#F2761E', .3), bev=.001, basis=(sdv, d, n)))
    for k in (-.035, .035): L.append(torus('strap', W + d * (.19 + k), d, r * 1.24, .007, hmat(H, 'case'), seg=20, rseg=6))

def hook_dj(H, cfg, R, L, A, Mr, Ml):
    """launchpad under the flat right palm, a mic in a fist (siao's fist pose, dj skin) on the left."""
    hr = R[0]; zs = [ (hr.matrix_world @ v.co).z for v in hr.data.vertices]
    zmin = sorted(zs)[len(zs) // 20]
    padc = tb((-.03, 0, -.05)); padc.z = zmin - .016
    R.append(rbox('pad', padc, (.24, .19, .03), hmat(H, 'padg'), bev=.012))
    cols = ['bpink', 'bcyan', 'bpurp', 'bcyan', 'bcyan', 'bpink', 'bcyan', 'bpurp', 'bpurp', 'bcyan', 'bpink', 'bcyan']
    for i in range(4):
        for j in range(3):
            c = padc + V((-.084 + i * .056, -.055 + j * .055, .017))
            R.append(rbox('p%d%d' % (i, j), c, (.044, .044, .008), hmat(H, cols[(i * 3 + j) % 12]), bev=.004))
    # left: replace the flat hand with a fist round a mic
    for o in L: bpy.data.objects.remove(o)
    L.clear()
    W, d, r = fist(H, 'l', L, V(), cfg['s'] * .95, hmat(H, 'skin'), hmat(H, 'jacket'), band=False)
    L.append(torus('trim_l', W + d * .03, d, r * 1.06, .011, hmat(H, 'trim')))
    L.append(torus('band_l', W + d * (r * 1.25 + .03), d, r * 1.08, .013, TEAM))
    hb = hmat(H, 'can'); g = hmat(H, 'grille')
    L.append(lathe('mic', V((0, 0, -.06)), V((0, 0, 1)), [(0, 0), (.0, .016), (.01, .018), (.13, .022), (.15, .03), (.155, .03)], hb))
    L.append(ball('grille', V((0, 0, .125)), .038, g))
    L.append(torus('micring', V((0, 0, .1)), V((0, 0, 1)), .03, .006, hmat(H, 'trim')))

def hook_ice(H, cfg, R, L, A, Mr, Ml):
    w = H['cart_mats'] if 'cart_mats' in H else None
    cart = next(o for o in bpy.data.objects if o.name.startswith('CART'))
    mm = {m.name.split('.')[0]: m for m in cart.data.materials}
    c = tb((.045, .01, -.06))
    L.append(rbox('waf1', c + V((0, 0, -.021)), (.075, .12, .012), mm['wafer'], bev=.005))
    L.append(rbox('yam', c, (.07, .114, .032), mm['yam'], bev=.009))
    L.append(rbox('waf2', c + V((0, 0, .021)), (.075, .12, .012), mm['wafer'], bev=.005))

def hook_rascal(H, cfg, R, L, A, Mr, Ml):
    """the toy's pinch hands cut badly. Use fists, keep the toy ruler, the star stays as A."""
    for o in R + L: bpy.data.objects.remove(o)
    R.clear(); L.clear()
    L.append(xform(cut(H, 'ruler', lambda sh, g, c, m: g == 'handslot.l'), Ml))
    skin = hmat(H, 'skin'); fist(H, 'r', R, V(), .8, skin, skin); fist(H, 'l', L, V(), .8, skin, skin)

def hook_siao(H, cfg, R, L, A, Mr, Ml):
    """Bare Arms: big bare fists on thick forearms. Grubby cloth hand wraps cover the wrist, knuckles are scraped raw,
    a crossed plaster sits on each forearm."""
    skin = hmat(H, 'skin'); cloth = newmat('wrap', '#E6DAC0', .85); cl2 = newmat('wrap_dark', '#BFB08E', .85)
    scuff = newmat('scuff', '#C2523F', .6); pl = newmat('plaster', '#F4E7CC', .6); pad = newmat('plaster_pad', '#D9B98C', .6)
    for sd, out, M in (('r', R, Mr), ('l', L, Ml)):
        fistob = out[0]; W = M @ bone(H, 'hand.' + sd); d = arm_dir(sd); sg = 1 if sd == 'r' else -1
        for o in [o for o in out if o.name.startswith(('band_', 'fa_'))]: out.remove(o); bpy.data.objects.remove(o)
        pts = [v.co.copy() for v in fistob.data.vertices]; c = sum(pts, V()) / len(pts)
        ax = (W - c).normalized(); L0 = (W - c).length
        def rad(t):   # fist radius round the wrap axis at t
            ds = sorted(((p - c) - ax * (p - c).dot(ax)).length for p in pts if abs((p - c).dot(ax) - t) < .012)
            return ds[int(len(ds) * .85)] if ds else 0
        rf = .056; prof = [(-.012, rad(-.006) * .9)]
        for t in (-.006, .012, .03): prof.append((t, rad(t) * 1.05 + .003))
        prof += [(L0 - .01, rf * 1.04), (L0 + .03, rf * 1.1), (L0 + .034, rf * .8)]
        out.append(lathe('wrap_' + sd, c, ax, prof, cloth, seg=24))
        for i, t in enumerate((.0, .026, L0 - .005, L0 + .028)):   # wound edges, each a little off true
            tilt = (ax + frame(ax)[1 + i % 2] * (.16 if i % 2 else -.12)).normalized()
            rr = (rad(t) * 1.05 + .004) if t < .04 else rf * (1.06 + 1.6 * (t - L0))
            out.append(torus('turn_' + sd, c + ax * t, tilt, rr, .0045, cl2, seg=20, rseg=5))
        out.append(rbox('tail_' + sd, c + ax * (L0 + .04) + V((0, 0, -rf * 1.12)), (.022, .006, .05), cloth, bev=.002, rot=(0, .3 * sg, 0)))
        out.append(torus('hem_' + sd, W + d * .034, d, rf * 1.07, .015, cloth, seg=24, rseg=8))
        out.append(tube('fa_' + sd, W - d * .01, d, rf, .55, skin, grow=.3))
        out.append(torus('band_' + sd, W + d * .15, d, rf * 1.12, .013, TEAM))
        # scraped knuckles: the front-most point of the fist in four height slabs
        zs = sorted(p.z for p in pts); z0, z1 = zs[len(zs) // 10], zs[-len(zs) // 6]
        for i in range(4):
            za = z0 + (z1 - z0) * i / 4; zb = z0 + (z1 - z0) * (i + 1) / 4
            sl = [p for p in pts if za <= p.z <= zb and (p - c).dot(ax) < -.02]
            if not sl: continue
            k = min(sl, key=lambda p: (p - c).dot(ax))
            out.append(ball('scuff_' + sd, k + ax * .004, .013, scuff, seg=10, rings=6, scl=(1, .55, .8)))
        n = (V((-.3 * sg, -.25, 1)) - d * d.dot(V((-.3 * sg, -.25, 1)))).normalized(); sdv = d.cross(n); pc = W + d * .27 + n * (rf * 1.19)
        for a in (.75, -.75):
            u = (sdv * math.cos(a) + d * math.sin(a)); v = n.cross(u)
            out.append(rbox('plaster_' + sd, pc, (.066, .02, .006), pl, bev=.002, basis=(u, v, n)))
        out.append(rbox('pad_' + sd, pc + n * .002, (.02, .02, .006), pad, bev=.002, basis=(sdv, d, n)))

HOOKS = dict(siao=hook_siao, uncle=hook_uncle, dj=hook_dj, ice=hook_ice, rascal=hook_rascal, nsboy=hook_nsboy, engineer=hook_engineer, rider=hook_rider)

# ---------------------------------------------------------------- export, render
def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons) if ob else 0

def export(key, obs):
    for img in bpy.data.images:
        if img.size[0] > 512: img.scale(512, 512 * img.size[1] // img.size[0])
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        if o: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTG, key + '.glb'), export_format='GLB', use_selection=True,
                              export_yup=True, export_apply=True, export_animations=False, export_skins=False,
                              export_morph=False, export_image_format='AUTO')

def stage():
    sc = bpy.context.scene
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (.55, .66, .86, 1); w.node_tree.nodes['Background'].inputs[1].default_value = .6
    def lamp(name, kind, loc, energy, col, size=1.0):
        d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = col
        if kind == 'AREA': d.size = size
        o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.location = loc
        o.rotation_euler = (V((0, .6, -.2)) - V(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
    lamp('key', 'AREA', (-1.2, -.6, 1.6), 260, (1, .86, .7), 1.5)
    lamp('fill', 'AREA', (1.6, .4, .2), 60, (.7, .8, 1), 2.5)
    lamp('rim', 'AREA', (.4, 2.5, 1.2), 160, (1, .85, .65), 1.5)
    fl = bpy.data.meshes.new('floor'); fl.from_pydata([(-20, -2, -1.55), (20, -2, -1.55), (20, 40, -1.55), (-20, 40, -1.55)], [], [(0, 1, 2, 3)])
    m = newmat('floor', '#9C958C', .8); fl.materials.append(m); sc.collection.objects.link(bpy.data.objects.new('floor', fl))
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(78); cd.clip_start = .05
    cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); cam.rotation_euler = (math.pi / 2, 0, 0); sc.camera = cam
    sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 16 if QUICK else 64
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
    sc.render.resolution_x = 1600; sc.render.resolution_y = 900
    try: sc.eevee.use_raytracing = True
    except Exception: pass

def render(key, R, L, A):
    P = cfg_P = V(C[key]['P']); rl = V(C[key].get('rl', (0, 0, 0)))
    R.location = tb(P)
    if L: L.location = tb(P + rl)
    if A: A.location = tb(P)
    stage()
    bpy.context.scene.render.filepath = os.path.join(SHOTS, key + '.png')
    bpy.ops.render.render(write_still=True)

log = []
for key in KEYS:
    Rob, Lob, Aob = build(key)
    export(key, [Rob, Lob, Aob])
    t = (tris(Rob), tris(Lob), tris(Aob)); log.append('%s R=%d L=%d A=%d total=%d' % (key, *t, sum(t)))
    print('VM', log[-1])
    if not NORENDER: render(key, Rob, Lob, Aob)
open(os.path.join(HD, '_tris.txt'), 'a').write('\n'.join(log) + '\n')
