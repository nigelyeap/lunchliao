"""Siaolang (key siao), style `toy`: designer vinyl collectible, same product line as the toy Ah Ma.
Run: /opt/homebrew/bin/blender -b -P tools/blender/heroes_toy/siao.py [-- quick shots]
Builds, rigs, skins, adds shape keys and clips, saves siao.blend, exports assets/heroes/siao.glb, renders shots.
Axes: Z up, he faces +Y. The glTF exporter turns that into Y up, facing -Z."""
import bpy, sys, os, math, random
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'blender', 'heroes'))
import hero_lib as H
OUT = os.path.join(ROOT, 'shots', 'heroes_toy', 'siao')
TMP = os.path.join(HERE, '_tmp_siao')
OUT_GLB = os.path.join(ROOT, 'assets', 'heroes', 'siao.glb')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
QUICK = 'quick' in ARGS
os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
V = Vector
Z = V((0, 0, 1)); X = (1, 0, 0); Y = (0, 1, 0)
GROUPS = {'body': [], 'head': [], 'gear': []}
GRP = ['body']

def ss(e0, e1, x):
    if e1 == e0: return 1.0 if x >= e1 else 0.0
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)
smoothstep = ss

# ---------------------------------------------------------------- materials
def mat(name, hexcol, rough=.38, metal=0.0, coat=0.0, sss=0.0, spec=.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*H.srgb(hexcol), 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .08
    b.inputs['Specular IOR Level'].default_value = spec
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss
        b.inputs['Subsurface Radius'].default_value = (.08, .03, .02); b.inputs['Subsurface Scale'].default_value = .25
    return m

M = dict(
    skin=mat('skin', '#E3A476', .42, sss=.12),
    nose=mat('nose', '#DB9368', .42, sss=.12),
    lip=mat('lip', '#C9705A', .42),
    blush=mat('blush', '#EE8A88', .5),
    line=mat('line', '#C48660', .45),
    hair=mat('hair', '#26222A', .33, coat=.25),
    brow=mat('brow', '#1F1B22', .4, coat=.2),
    eye=mat('eye', '#1A1214', .08, coat=1.0),
    white=mat('white', '#FFFDF8', .25),
    mouth=mat('mouth', '#6E1D2B', .45),
    tongue=mat('tongue', '#F2818C', .35),
    teeth=mat('teeth', '#FFFAF0', .25),
    frame=mat('frame', '#17151A', .2, coat=1.0),
    gold=mat('gold', '#F0B94A', .22, metal=1.0),
    red=mat('red', '#D3202D', .3, coat=.4),
    redd=mat('red_dark', '#8E1418', .4),
    shorts=mat('shorts', '#8C2A38', .5),
    shorts_t=mat('shorts_trim', '#F1E7D2', .5),
    sweat=mat('sweat', '#BFE6FF', .08, coat=1.0),
)

def singlet_image(n=1024):
    """Cream ribbed singlet print with one clean soy-sauce stain. u runs round the body (front at 0.25), v is height."""
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / n
    img = np.empty((n, n, 3), np.float32); img[:] = (0.955, 0.925, 0.85)
    rib = (np.sin(xx * 2 * np.pi * 96) * .5 + .5)[..., None] * .028
    img -= rib
    def blob(cx, cy, rx, ry, col):
        a = np.clip((1 - np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)) * min(rx, ry) * n / 1.5 + .5, 0, 1)[..., None]
        img[:] = img * (1 - a) + np.array(col, np.float32) * a
    sc = (0.80, 0.66, 0.40); sd = (0.72, 0.56, 0.30)
    for cx, cy, rx, ry in ((.235, .40, .034, .05), (.262, .37, .03, .042), (.248, .33, .018, .03), (.28, .43, .016, .02)):
        blob(cx, cy, rx, ry, sc)
    blob(.246, .385, .016, .022, sd)
    blob(.236, .27, .007, .012, sc)      # a drip
    im = bpy.data.images.new('singlet', n, n, alpha=False)
    im.pixels.foreach_set(np.concatenate([img, np.ones((n, n, 1), np.float32)], axis=2).ravel()); im.pack(); return im

def singlet_mat():
    m = mat('singlet', '#F6EDDA', .55)
    nt = m.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = singlet_image()
    nt.links.new(t.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color']); return m
M['singlet'] = singlet_mat()

# ---------------------------------------------------------------- mesh helpers
def mk(name, verts, faces, m, uvs=None, mat_idx=None):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    for mm in (m if isinstance(m, (list, tuple)) else [m]): me.materials.append(mm)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    if mat_idx: me.polygons.foreach_set('material_index', mat_idx)
    if uvs:
        uv = me.uv_layers.new(name='UVMap')
        flat = [c for f in uvs for co in f for c in co]; uv.data.foreach_set('uv', flat)
    ob = bpy.data.objects.new(name, me); SC.collection.objects.link(ob); GROUPS[GRP[0]].append(ob); return ob

def reg(ob):
    GROUPS[GRP[0]].append(ob); return ob

def sph_vf(seg=32, rings=16):
    vs = [V((0, 0, 1))]
    for j in range(1, rings):
        ph = math.pi * j / rings
        for i in range(seg):
            th = 2 * math.pi * i / seg
            vs.append(V((math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph))))
    vs.append(V((0, 0, -1))); fs = []
    ring = lambda j, i: 1 + (j - 1) * seg + i % seg
    for i in range(seg): fs.append((0, ring(1, i), ring(1, i + 1)))
    for j in range(1, rings - 1):
        for i in range(seg): fs.append((ring(j, i), ring(j + 1, i), ring(j + 1, i + 1), ring(j, i + 1)))
    last = len(vs) - 1
    for i in range(seg): fs.append((last, ring(rings - 1, i + 1), ring(rings - 1, i)))
    return vs, fs

def ell(name, c, r, m, rot=None, seg=24):
    vs, fs = sph_vf(seg, seg // 2); c = V(c); R = rot if rot is not None else Matrix.Identity(3)
    return mk(name, [c + R @ V((v.x * r[0], v.y * r[1], v.z * r[2])) for v in vs], fs, m)

def frame_from(axis):
    n = V(axis).normalized(); a = V((1, 0, 0)) if abs(n.x) < .9 else V((0, 1, 0))
    t = n.cross(a).normalized(); u = n.cross(t).normalized(); return t, u, n

def tor(name, c, axis, R, r, m, seg=40, rseg=10, squash=None):
    t, u, n = frame_from(axis); c = V(c); vs = []; fs = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; d = t * math.cos(a) + u * math.sin(a)
        for j in range(rseg):
            b = 2 * math.pi * j / rseg; p = d * (R + r * math.cos(b)) + n * (r * math.sin(b))
            if squash: p = V((p.x * squash[0], p.y * squash[1], p.z * squash[2]))
            vs.append(c + p)
    for i in range(seg):
        for j in range(rseg):
            a = i * rseg + j; b = ((i + 1) % seg) * rseg + j; c2 = ((i + 1) % seg) * rseg + (j + 1) % rseg; d2 = i * rseg + (j + 1) % rseg
            fs.append((a, b, c2, d2))
    return mk(name, vs, fs, m)

def fillet(pts, R, k=6):
    pts = [V(p) for p in pts]; out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p = pts[i]; d1 = (pts[i - 1] - p).normalized(); d2 = (pts[i + 1] - p).normalized()
        th = d1.angle(d2)
        if th > 3.1: out.append(p); continue
        tl = R / math.tan(th / 2); c = p + (d1 + d2).normalized() * (R / math.sin(th / 2))
        v0 = p + d1 * tl - c; v1 = p + d2 * tl - c
        for s in range(k + 1): out.append(c + v0.slerp(v1, s / k).normalized() * R)
    out.append(pts[-1]); return out

def bez(a, b, c, n=10):
    a, b, c = V(a), V(b), V(c)
    return [a * (1 - t) ** 2 + b * 2 * t * (1 - t) + c * t * t for t in [i / (n - 1) for i in range(n)]]

def sweep(name, pts, radii, m, seg=14, uvrep=None, round_caps=True, lip=None):
    pts = [V(p) for p in pts]; n = len(pts)
    if isinstance(radii, (int, float)): radii = [radii] * n
    T = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    N = frame_from(T[0])[0]; rings = []
    def ring(c, Nn, Bn, r): return [c + (Nn * math.cos(2 * math.pi * i / seg) + Bn * math.sin(2 * math.pi * i / seg)) * r for i in range(seg)]
    def dome(c, t, Nn, Bn, r, sign):
        return [ring(c + t * (sign * r * math.sin(a)), Nn, Bn, r * math.cos(a)) for a in (math.radians(35), math.radians(65), math.radians(89))]
    for i in range(n):
        N = (N - T[i] * N.dot(T[i])).normalized(); B = T[i].cross(N)
        if i == 0 and round_caps: rings += reversed(dome(pts[0], T[0], N, B, radii[0], -1))
        rings.append(ring(pts[i], N, B, radii[i]))
    if lip:
        rings.append(ring(pts[-1] - T[-1] * lip[0], N, B, lip[1])); rings.append(ring(pts[-1] - T[-1] * lip[0] * 3, N, B, lip[1] * .2))
    elif round_caps: rings += dome(pts[-1], T[-1], N, B, radii[-1], 1)
    vs = [p for r in rings for p in r]; fs = []; uvs = []
    L = [0.0]
    for j in range(1, len(rings)): L.append(L[-1] + ((rings[j][0] + rings[j][seg // 2]) * .5 - (rings[j - 1][0] + rings[j - 1][seg // 2]) * .5).length)
    ur, vr = uvrep or (1, 1)
    for j in range(len(rings) - 1):
        for i in range(seg):
            fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
            uvs.append([(i / seg * ur, L[j] * vr), ((i + 1) / seg * ur, L[j] * vr), ((i + 1) / seg * ur, L[j + 1] * vr), (i / seg * ur, L[j + 1] * vr)])
    fs.append(tuple(reversed(range(seg)))); uvs.append([(0, 0)] * seg)
    fs.append(tuple(range((len(rings) - 1) * seg, len(rings) * seg))); uvs.append([(0, 0)] * seg)
    return mk(name, vs, fs, m, uvs)

# ---------------------------------------------------------------- proportions and landmarks
KSC = 1.88 / 1.96 * .985                          # global height scale applied before rigging
BY = -0.02                                  # body centre in Y
HC = V((0, 0.0, 1.47)); HR = V((0.56, 0.52, 0.49))   # head centre and radii. Top = 1.96
HOLE = (0.0, -0.28, 0.175, 0.115)           # mouth hole on the head: centre fx, centre fz, half width, half height

def surf(fx, fz, off=0.0):
    """Face coordinates (x right of centre, z above centre) -> point on the front of the head, normal, tangent, up."""
    k = max(1e-4, 1 - (fx / HR.x) ** 2 - (fz / HR.z) ** 2); y = HR.y * math.sqrt(k)
    n = V((fx / HR.x ** 2, y / HR.y ** 2, fz / HR.z ** 2)).normalized()
    t = n.cross(Z).normalized(); u = t.cross(n).normalized()
    return HC + V((fx, y, fz)) + n * off, n, t, u

KNEE_Z, ANK_Z = 0.27, 0.09
ARM = {}
for _k in (-1, 1):
    S = V((_k * .30, BY + .02, .79)); E = V((_k * .56, BY + .08, .55)); Wr = V((_k * .50, .29, .60))
    ARM[_k] = (S, E, Wr)
EXe, EZe = .215, -.01

# ---------------------------------------------------------------- weights
def setw(ob, fn):
    for g in list(ob.vertex_groups): ob.vertex_groups.remove(g)
    vgs = {}
    for v in ob.data.vertices:
        w = {b: x for b, x in fn(v.co).items() if x > 1e-4}
        tot = sum(w.values())
        if tot <= 0: w = {'chest': 1.0}; tot = 1.0
        for b, x in w.items():
            if b not in vgs: vgs[b] = ob.vertex_groups.new(name=b)
            vgs[b].add([v.index], x / tot, 'REPLACE')
    return ob

def w_head(co): return {'head': 1.0}
def w_hips(co): return {'hips': 1.0}
def w_foot(co): return {'foot.l' if co.x < 0 else 'foot.r': 1.0}
def w_torso(co):
    z = co.z; h = 1 - ss(.46, .60, z); c = ss(.60, .80, z); nk = ss(.84, .92, z) * .5
    return {'hips': h, 'spine': max(0, 1 - h - c), 'chest': c * (1 - nk), 'neck': c * nk}
def w_neck(co):
    z = co.z; c = 1 - ss(.84, .94, z); hd = ss(.98, 1.07, z)
    return {'chest': c, 'neck': max(0, 1 - c - hd), 'head': hd}
def w_arm(k):
    S, E, Wr = ARM[k]; s = 'l' if k < 0 else 'r'
    u = (E - S).normalized(); f = (Wr - E).normalized(); bis = (u + f).normalized()
    def fn(co):
        lo = ss(-.04, .05, (co - E).dot(bis)); hd = ss(-.02, .04, (co - Wr).dot(f)); ch = 1 - ss(-.05, .09, (co - S).dot(u))
        return {'hand.' + s: hd, 'lowerarm.' + s: lo * (1 - hd), 'upperarm.' + s: (1 - lo) * (1 - ch), 'chest': (1 - lo) * ch}
    return fn
def w_legtop(co):
    s = 'l' if co.x < 0 else 'r'; h = ss(.46, .58, co.z)
    return {'hips': h, 'upperleg.' + s: 1 - h}
def w_legtop_s(s):
    return lambda co: {k: v for k, v in (w_legtop(V((-1 if s < 0 else 1, 0, co.z))).items())}
def w_legskin(co):
    s = 'l' if co.x < 0 else 'r'; z = co.z; wl = 1 - ss(.23, .31, z); wf = 1 - ss(.07, .13, z)
    return {'upperleg.' + s: 1 - wl, 'lowerleg.' + s: max(0, wl - wf), 'foot.' + s: wf}
def w_sole(co):
    s = 'l' if co.x < 0 else 'r'; t = ss(.12, .22, co.y)
    return {'foot.' + s: 1 - t, 'toes.' + s: t}

# ---------------------------------------------------------------- body
def build_body():
    cz = [.44, .46, .52, .60, .70, .78, .84, .88, .905]; cr = [.395, .40, .43, .435, .405, .345, .275, .20, .15]
    zs = np.linspace(cz[0], cz[-1], 26); rs = np.interp(zs, cz, cr)
    for _ in range(3): rs[1:-1] = (rs[:-2] + 2 * rs[1:-1] + rs[2:]) / 4
    global BR
    BR = lambda z: float(np.interp(z, zs, rs))
    rows = list(zip(rs, zs)); seg = 48; vs = []; fs = []; uvs = []
    for r, z in rows:
        for i in range(seg):
            a = 2 * math.pi * i / seg; vs.append(V((r * math.cos(a), BY + .92 * r * math.sin(a) + .03 * (1 - ss(.45, .72, z)), z)))
    for j in range(len(rows) - 1):
        for i in range(seg):
            fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
            v0 = (rows[j][1] - .44) / .46; v1 = (rows[j + 1][1] - .44) / .46
            uvs.append([(i / seg, v0), ((i + 1) / seg, v0), ((i + 1) / seg, v1), (i / seg, v1)])
    fs.append(tuple(range((len(rows) - 1) * seg, len(rows) * seg))); uvs.append([(.5, .99)] * seg)
    setw(mk('singlet', vs, fs, M['singlet'], uvs), w_torso)
    setw(tor('hem_trim', (0, BY + .03, .452), Z, BR(.452) + .004, .016, M['red'], seg=40, rseg=6, squash=(1, .92, 1)), w_torso)
    setw(tor('collar', (0, BY, .902), Z, .157, .024, M['red'], seg=32, rseg=6, squash=(1, .92, 1)), w_torso)
    setw(sweep('neck', [(0, BY + .01, .84), (0, BY + .02, .95), (0, BY + .02, 1.08)], [.152, .146, .146], M['skin'], seg=24), w_neck)
    # shorts
    setw(ell('hips', (0, BY, .465), (.37, .31, .10), M['shorts']), w_hips)
    for s in (-1, 1):
        sl = sweep('short_leg', [(s * .19, BY, .50), (s * .195, BY, .40), (s * .198, BY, .355), (s * .20, BY, .33)], [.20, .20, .197, .195], [M['shorts'], M['shorts_t']], seg=24, lip=(.012, .14))
        for p in sl.data.polygons:
            if 5 * 24 <= p.index < 8 * 24: p.material_index = 1
        setw(sl, w_legtop_s(s))
        setw(sweep('leg', [(s * .20, BY, .36), (s * .20, BY, .22), (s * .195, BY, .105)], [.105, .10, .094], M['skin'], seg=20), w_legskin)
        setw(ell('foot', (s * .195, BY + .075, .078), (.098, .165, .058), M['skin']), w_foot)
        setw(ell('sole', (s * .195, BY + .075, .032), (.125, .215, .032), M['red']), w_sole)
        post = V((s * .195, BY + .20, .098))
        for o in (-1, 1):
            setw(sweep('strap', bez(post, (s * .195 + o * .085, BY + .14, .18), (s * .195 + o * .112, BY + .01, .05)), .017, M['red'], seg=8), w_foot)
        setw(ell('strap_post', post, (.02, .02, .025), M['red'], seg=12), w_foot)

def hand_soup(k, Wr, f):
    n = V((-k, 0, 0)); n = (n - f * n.dot(f)).normalized(); u = f.cross(n).normalized()
    if u.z < 0: u = -u
    P = Wr + f * .045; so = H.Soup('hand')
    R = Matrix((f, n, u)).transposed().to_4x4()
    so.ellipsoid(P, (.065, .052, .078), R)
    so.capsule(Wr - f * .02, P, .055, .06)
    for ku in (.057, .019, -.019, -.057):
        p0 = P + f * .05 + u * ku; p1 = p0 + f * .035 + n * .012; p2 = p1 + n * .042; p3 = p2 - f * .032 + n * .006
        for a, b in ((p0, p1), (p1, p2), (p2, p3)): so.capsule(a, b, .0215, .0215, seg=12)
    t0 = P + u * .06 + f * .012 + n * .008; t1 = P + f * .062 + u * .043 + n * .036; t2 = P + f * .05 + u * .012 + n * .06
    so.capsule(t0, t1, .028, .026, seg=12); so.capsule(t1, t2, .026, .024, seg=12)
    hand, _ = so.remesh(voxel=.0065, smooth=6, smooth_factor=.6, target_tris=1150)
    H.set_material(hand, M['skin']); return reg(hand)

def build_arms():
    for k in (-1, 1):
        S, E, Wr = ARM[k]; Cp = E * 2 - (S + Wr) * .5
        path = bez(S, Cp, Wr, 13)
        prof = np.interp(np.linspace(0, 1, 13), [0, .25, .5, .8, 1], [.106, .124, .108, .09, .077]).tolist()
        fn = w_arm(k)
        setw(sweep('arm', path, prof, M['skin'], seg=20), fn)
        f = (Wr - path[-2]).normalized()
        setw(hand_soup(k, Wr, f), fn)

# ---------------------------------------------------------------- head
def build_head_gear():
    GRP[0] = 'gear'
    for s in (-1, 1):
        setw(ell('ear', HC + V((s * .565, -.02, -.03)), (.052, .09, .105), M['skin'], seg=20), w_head)
    p, n, t, u = surf(0, -.088); setw(ell('nose', p + n * .008, (.066, .058, .056), M['nose'], seg=24), w_head)
    # hair: a horseshoe of curls round the sides and back, bald dome on top
    rnd = random.Random(5); so = H.Soup('hair'); n = 120
    for i in range(n):
        z = 1 - 2 * (i + .5) / n; a = i * 2.39996; r = math.sqrt(1 - z * z); d = V((r * math.cos(a), r * math.sin(a), z))
        az = math.degrees(math.atan2(abs(d.x), d.y)); el = math.degrees(math.asin(d.z))
        top = 26 + 30 * ss(100, 180, az) - 22 * ss(70, 100, az) * (1 - ss(100, 180, az)) * 0
        if az < 78 or el > top or el < -30 or (az < 115 and el < -14): continue
        so.sphere(HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z)) * .92, rnd.uniform(.125, .15), seg=18)
    hair, _ = so.remesh(voxel=.013, smooth=10, smooth_factor=.6, target_tris=1900)
    H.set_material(hair, M['hair']); reg(hair); setw(hair, w_head)
    rs = random.Random(11)
    def spike(b, d, L, r0, bend):
        d = V(d).normalized(); side = d.cross(Z).normalized() * bend
        pts = [b - d * .04, b + d * L * .5 + side, b + d * L + side * 2.2 + Z * .02 * bend]
        setw(sweep('spike', pts, [r0, r0 * .75, r0 * .3], M['hair'], seg=6), w_head)
    for s in (-1, 1):
        for el, az, L, r0 in ((30, 88, .24, .052), (18, 100, .34, .058), (4, 112, .30, .05), (-8, 124, .24, .045), (38, 105, .2, .045)):
            a = math.radians(az); e_ = math.radians(el + rs.uniform(-4, 4))
            d = V((s * math.sin(a) * math.cos(e_), math.cos(a) * math.cos(e_), math.sin(e_)))
            b = HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z)) * .96
            spike(b, d + V((0, 0, .3 + rs.uniform(-.1, .2))), L * rs.uniform(.9, 1.2), r0, rs.uniform(-.05, .05))
    for k, (fx, fy, L) in enumerate(((-.12, .06, .04), (.04, -.04, .05), (.15, .08, .035), (-.03, .0, .03))):
        zz = math.sqrt(max(0, 1 - (fx / HR.x) ** 2 - (fy / HR.y) ** 2)) * HR.z
        b = HC + V((fx, fy, zz - .01)); sd = rs.choice((-1, 1)) * .3
        setw(sweep('strand', [b - Z * .01, b + V((sd * .25, .02, L * .55)), b + V((sd * .9, .03, L * .95)), b + V((sd * 1.7, .04, L * 1.05))], [.017, .014, .01, .005], M['hair'], seg=5), w_head)
    setw(ell('sweat', surf(.30, .36, .03)[0], (.032, .024, .052), M['sweat'], seg=14), w_head)
    # glasses (frames only, so the eyes and brows stay readable)
    RR = .152; cs = {}
    for s in (-1, 1):
        p, n, t, u = surf(s * EXe, EZe + s * .03); ng = V((s * .13, 1, -.04)).normalized(); c = p + n * .075
        tg = ng.cross(Z).normalized(); cs[s] = (c, tg, ng)
        setw(tor('rim', c, ng, RR, .02, M['frame'], seg=32, rseg=6), w_head)
        outer = c + tg * (s * (RR + .005))
        setw(ell('hinge', outer, (.024, .022, .024), M['frame'], seg=12), w_head)
        setw(sweep('temple', fillet([outer, HC + V((s * .58, .30, .06)), HC + V((s * .595, .0, .045))], .12), .013, M['frame'], seg=8), w_head)
    a = cs[-1][0] + cs[-1][1] * RR; b = cs[1][0] - cs[1][1] * RR
    setw(sweep('bridge', bez(a + Z * .03, (a + b) * .5 + V((0, .03, .085)), b + Z * .03, 8), .015, M['frame'], seg=8), w_head)
    GRP[0] = 'body'

# ---------------------------------------------------------------- face: one mesh, head shell with a mouth hole + overlay, six shape keys
EXPR = {}
base = dict(bz=.2, tilt=-.006, arch=.022, bw=.036, eye='bead', es=(1.0, 1.0), cut=None, hl=.0, wr=0, w=.33, curve=.07, up=.012, dn=.075, tt=.85, tg=.05, cz=-.255, arc=1.0,
            bo=(.05, -.018), bt=(-.03, .075), ps=(1.0, .68), pd=(.0, .0))
def ex(**kw): d = dict(base); d.update(kw); return d
EXPR['base'] = ex()
EXPR['smile'] = ex(w=.27, curve=.075, dn=.02, tt=.4, tg=0, bo=(.02, 0), bt=(0, .02), ps=(.9, .8), es=(.95, .95))
EXPR['mouth_open'] = ex(w=.24, curve=.01, up=.03, dn=.125, tt=.26, tg=.34, bo=(.07, .03), bt=(-.02, .0), es=(1.1, 1.1), ps=(.8, .6))
EXPR['blink'] = ex(eye='arc', arc=.2)
EXPR['angry'] = ex(bz=.235, tilt=.11, arch=-.004, bw=.062, es=(1.08, 1.0), cut=(.022, .6), wr=-.02, w=.31, curve=-.07, up=.03, dn=.07, tt=1.0, tg=0, cz=-.25, bo=(.045, .0), bt=(.03, .06), ps=(.95, .62))
EXPR['grin'] = ex(bz=.225, tilt=-.01, arch=.034, wr=.022, w=.345, curve=.075, up=.01, dn=.13, tt=.55, tg=.14, cz=-.26, bo=(.07, -.01), bt=(-.05, .07), es=(1.1, 1.1), ps=(.85, .58))
EXPR['ult'] = ex(bz=.215, tilt=.075, arch=.004, bw=.05, es=(1.2, 1.25), wr=.012, w=.34, curve=.0, up=.05, dn=.15, tt=.3, tg=.36, cz=-.255, bo=(.06, -.02), bt=(.0, .1), ps=(.7, .5))
FM = ['skin', 'lip', 'brow', 'eye', 'white', 'line', 'mouth', 'teeth', 'tongue', 'blush']
HSEG, HRING = 64, 32

def head_base():
    """Head ellipsoid (skin) with the mouth-hole faces removed. Returns verts, faces."""
    vs, fs = sph_vf(HSEG, HRING); P = [HC + V((v.x * HR.x, v.y * HR.y, v.z * HR.z)) for v in vs]; keep = []
    for f in fs:
        c = sum((P[i] for i in f), V()) / len(f); fx = c.x - HC.x; fz = c.z - HC.z
        inside = c.y - HC.y > .05 and ((fx - HOLE[0]) / HOLE[2]) ** 2 + ((fz - HOLE[1]) / HOLE[3]) ** 2 < 1
        if not inside: keep.append(f)
    return P, keep

def face_geo(e):
    vs = []; fs = []; mi = []
    def add(v, f, m):
        o = len(vs); vs.extend(v); fs.extend([tuple(i + o for i in ff) for ff in f]); mi.extend([FM.index(m)] * len(f))
    def hide(v): return [HC.copy() for _ in v]
    def stroke(pts, rw, rn, off, m, show=True, seg=8):
        P = [surf(x, z, off) for x, z in pts]; n = len(P); v = []
        for i in range(n):
            p, nn, _, _ = P[i]; tan = (P[min(i + 1, n - 1)][0] - P[max(i - 1, 0)][0]).normalized(); side = nn.cross(tan).normalized()
            f = max(0.0, math.sin(math.pi * i / (n - 1))) ** .45 if 0 < i < n - 1 else 0.0
            v += [p + (side * math.cos(a) * rw + nn * math.sin(a) * rn) * f for a in [2 * math.pi * kk / seg for kk in range(seg)]]
        f = [(i * seg + kk, i * seg + (kk + 1) % seg, (i + 1) * seg + (kk + 1) % seg, (i + 1) * seg + kk) for i in range(n - 1) for kk in range(seg)]
        add(v if show else hide(v), f, m)
    def blob(fx, fz, rad, off, m, tilt=0.0, show=True, seg=20, d=(0, 0), cut=None):
        p, n, t, u = surf(fx, fz); sv, sf = sph_vf(seg, seg // 2); ct, st = math.cos(tilt), math.sin(tilt)
        v = []
        for q in sv:
            lx, lz = q.x * rad[0], q.z * rad[2]
            if cut: lz = min(lz, cut[0] + cut[1] * lx)
            v.append(p + t * (lx * ct - lz * st + d[0]) + u * (lx * st + lz * ct + d[1]) + n * (q.y * rad[1] + off))
        add(v if show else hide(v), sf, m)
    for s in (-1, 1):
        si = 0 if s < 0 else 1; bo = e['bo'][si]; btl = e['tilt'] + e['bt'][si]
        stroke([(s * (EXe + q * .105), e['bz'] + bo + q * btl + e['arch'] * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], e['bw'], .02, .004, 'brow')
        bead = e['eye'] == 'bead'; a, c = .07 * e['es'][0], .082 * e['es'][1]; pr = e['ps'][si]
        ct = (e['cut'][0], e['cut'][1] * s) if e['cut'] else None
        blob(s * EXe, EZe, (a, .034, c), 0, 'white', show=bead, seg=24, cut=ct)
        blob(s * EXe, EZe, (.03 * pr, .02, .034 * pr), .02, 'eye', show=bead, seg=16, d=(-s * .006 + e['pd'][0], e['pd'][1]), cut=ct)
        blob(s * EXe, EZe, (.008, .006, .008), .036, 'white', show=bead, seg=8, d=(-s * .006 - .008, .01))
        stroke([(s * EXe + .066 * math.cos(ph), EZe - .028 + .062 * e['arc'] * math.sin(ph)) for ph in [math.radians(168 - 156 * i / 11) for i in range(12)]], .0145, .011, .005, 'eye', show=not bead)
        v = [surf(s * .375, -.2, .0025)[0]]; f = []
        for j in range(1, 4):
            for i in range(20):
                ang = 2 * math.pi * i / 20; v.append(surf(s * .375 + .08 * j / 3 * math.cos(ang), -.2 + .058 * j / 3 * math.sin(ang), .0025 if j < 3 else .0)[0])
        ri = lambda j, i: 1 + (j - 1) * 20 + i % 20
        f += [(0, ri(1, i), ri(1, i + 1)) for i in range(20)]
        f += [(ri(j, i), ri(j + 1, i), ri(j + 1, i + 1), ri(j, i + 1)) for j in (1, 2) for i in range(20)]
        add(v, f, 'blush')
    for z0, hw0 in ((.262, .12), (.305, .09)):
        stroke([(q * hw0, z0 + e['wr'] + .012 * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .0075, .004, .001, 'line')
    # moustache: a thick clean bar under the nose
    stroke([(q * .125, -.168 - .03 * q * q - .004) for q in [i / 6 - 1 for i in range(13)]], .026, .017, .006, 'brow')
    # mouth: a skin grid with lips, a real cavity, upper tooth row and tongue
    X0, ZT, NC = .235, -.13, 16
    hw = e['w'] / 2
    def env(x): return max(0.0, 1 - (x / hw) ** 2) ** .5
    def zc(x): return e['cz'] + e['curve'] * min(1.0, (x / hw) ** 2)
    def half(x): return .0075 * min(1.0, env(x) * 2.5)
    tg0 = 1 - e['tg']; tt = min(e['tt'], tg0)
    tk = [0, tt / 2, tt, tt + (tg0 - tt) / 2, tg0, tg0 + (1 - tg0) / 2, 1]
    NA, NCc = 6, 5
    def gprof(t):
        b = max(0.0, math.sin(math.pi * t)) ** .6
        tooth = (.3 + .7 * ss(max(tt, 1e-3), min(tt + .25, 1.0), t)) if tt > 0 else 1.0
        tong = 1 - .5 * ss(tg0 - .1, tg0 + .1, t) if e['tg'] > 0 else 1.0
        return b * tooth * tong
    cols = []
    xs = [-X0 + 2 * X0 * i / NC for i in range(NC + 1)]
    for x in xs:
        zU = zc(x) + e['up'] * env(x) + half(x); zL = zc(x) - e['dn'] * env(x) - half(x)
        ZB = -.435 + .05 * ss(.1, .235, abs(x)); lm = env(x) ** .3
        lip = .003 + .006 * lm; opn = min(1.0, max(0.0, zU - zL - .015) / .05); D = .075 * opn
        col = []
        for j in range(NA + 1):
            s_ = j / NA; col.append((ZT + (zU - ZT) * s_, .0025 + (lip - .0025) * ss(.35, 1, s_)))
        for t in tk[1:]: col.append((zU + (zL - zU) * t, lip - D * gprof(t)))
        for j in range(1, NCc + 1):
            s_ = j / NCc; col.append((zL + (ZB - zL) * s_, lip - (lip - .0025) * ss(0, .65, s_)))
        cols.append(col)
    R = len(cols[0]); v = []
    for i, col in enumerate(cols):
        for z, off in col:
            q = ((xs[i] - HOLE[0]) / HOLE[2]) ** 2 + ((z - HOLE[1]) / HOLE[3]) ** 2
            v.append(surf(xs[i], z, off - .0055 * ss(1.0, 1.7, q))[0])
    f = []; fm = []
    nb = len(tk) - 1
    def rowmat(r, i=0):
        if env((xs[i] + xs[i + 1]) / 2) <= 0.02 or max(env(xs[i]), env(xs[i + 1])) <= 0.0: return 'skin'
        if r < NA - 1: return 'skin'
        if r == NA - 1: return 'lip'
        r2 = r - NA
        if r2 < nb: return ['teeth', 'teeth', 'mouth', 'mouth', 'tongue', 'tongue'][r2]
        return 'lip' if r2 == nb else 'skin'
    for i in range(NC):
        for r in range(R - 1):
            f.append((i * R + r, (i + 1) * R + r, (i + 1) * R + r + 1, i * R + r + 1)); fm.append(rowmat(r, i))
    o = len(vs); vs.extend(v); fs.extend([tuple(a + o for a in ff) for ff in f]); mi.extend([FM.index(m) for m in fm])
    return vs, fs, mi

def build_face():
    GRP[0] = 'head'
    P, keep = head_base(); nh = len(P)
    ev, ef, emi = face_geo(EXPR['base'])
    verts = P + ev; faces = list(keep) + [tuple(i + nh for i in f) for f in ef]; mis = [0] * len(keep) + emi
    ob = mk('siao_head', verts, faces, [M[k] for k in FM], mat_idx=mis)
    ob.shape_key_add(name='Basis')
    for name in ('blink', 'mouth_open', 'smile', 'angry', 'grin', 'ult'):
        k = ob.shape_key_add(name=name); v2 = face_geo(EXPR[name])[0]
        k.data.foreach_set('co', [c for vv in (P + v2) for c in vv])
    me = ob.data; nrm = [Vector(v.normal) for v in me.vertices]
    def an(p): d = p - HC; return V((d.x / HR.x ** 2, d.y / HR.y ** 2, d.z / HR.z ** 2)).normalized()
    for i in range(nh): nrm[i] = an(P[i])
    NCm, Rm, hwm = 16, 18, .11; st = nh + len(ev) - (NCm + 1) * Rm
    xs_ = [-.235 + 2 * .235 * i / NCm for i in range(NCm + 1)]
    for i in range(NCm + 1):
        for j in range(Rm):
            if j <= 5 or j >= 13 or abs(xs_[i]) >= hwm: nrm[st + i * Rm + j] = an(ev[len(ev) - (NCm + 1) * Rm + i * Rm + j])
    me.normals_split_custom_set_from_vertices(nrm)
    setw(ob, w_head); GRP[0] = 'body'; return ob

def set_expr(face, name=None):
    for k in face.data.shape_keys.key_blocks:
        if k.name != 'Basis': k.value = 1.0 if k.name == name else 0.0
