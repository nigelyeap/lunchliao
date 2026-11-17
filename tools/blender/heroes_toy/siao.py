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
    img = np.empty((n, n, 3), np.float32); img[:] = (0.965, 0.96, 0.94)        # cool bright white, so it does not go cream against the yellow walls
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

def catmull(P, k=6):
    P = [V(p) for p in P]; n = len(P); out = []
    for i in range(n - 1):
        p0 = P[i - 1] if i > 0 else P[0]; p1 = P[i]; p2 = P[i + 1]; p3 = P[i + 2] if i + 2 < n else P[-1]
        for s_ in range(k):
            t = s_ / k; out.append(.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1]); return out

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
KSC = 1.88 / 2.094                                  # global height scale applied before rigging
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
    S = V((_k * .335, BY + .02, .772)); E = V((_k * .56, BY + .08, .55)); Wr = V((_k * .50, .29, .60))
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
def bxy(a, z, off=0.0):
    """Point on the torso surface at angle a (0 = his left side +X, pi/2 = front +Y), height z, pushed out by off."""
    r = BR(z); return V(((r + off) * math.cos(a), BY + .03 * (1 - ss(.45, .72, z)) + (.92 * r + off) * math.sin(a), z))

ZH = .452                                    # singlet hem
def ztop(a):
    """Singlet top edge: round scoop neck (deeper in front), straps over the shoulders, round armholes at the sides."""
    c = abs(math.cos(a)); f = ss(-.3, .3, math.sin(a)); CS, CA, ZS_, ZA = .62, .90, .876, .68
    if c < CS: zb = .80 + .035 * (1 - f); return zb + (ZS_ - zb) * ss(0, CS, c)
    if c < CA: return ZS_
    return ZS_ - (ZS_ - ZA) * ss(CA, 1.0, c) ** .7
def soff(z): return .011 + .01 * (1 - ss(ZH, .54, z)) + .012 * ss(.76, .86, z)

def ring(name, pts, r, m, seg=8):
    """Closed tube along a loop (no end caps, so no seam or tab). Same as gym.py."""
    import bmesh
    P = [V(p) for p in pts]; n = len(P); cen = sum(P, V()) / n; vs = []; fs = []
    for i, p in enumerate(P):
        T = (P[(i + 1) % n] - P[i - 1]).normalized(); N = V((p.x - cen.x, p.y - cen.y, 0)).normalized(); B = N.cross(T).normalized()
        vs += [p + (N * math.cos(2 * math.pi * k / seg) + B * math.sin(2 * math.pi * k / seg)) * r for k in range(seg)]
    for i in range(n):
        j = (i + 1) % n; fs += [(i * seg + k, i * seg + (k + 1) % seg, j * seg + (k + 1) % seg, j * seg + k) for k in range(seg)]
    ob = mk(name, vs, fs, m); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free(); return ob

def build_body():
    cz = [.44, .46, .52, .60, .70, .78, .84, .88, .905]; cr = [.395, .40, .43, .435, .405, .345, .275, .20, .15]
    zs = np.linspace(cz[0], cz[-1], 26); rs = np.interp(zs, cz, cr)
    for _ in range(3): rs[1:-1] = (rs[:-2] + 2 * rs[1:-1] + rs[2:]) / 4
    global BR
    BR = lambda z: float(np.interp(z, zs, rs))
    # skin torso under the singlet (shows in the scoop neck and armholes)
    tz = np.linspace(cz[0], cz[-1], 18); seg = 40; vs = []; fs = []
    for z in tz:
        for i in range(seg): vs.append(bxy(2 * math.pi * i / seg, float(z)))
    for j in range(len(tz) - 1):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
    fs.append(tuple(range((len(tz) - 1) * seg, len(tz) * seg)))
    setw(mk('torso', vs, fs, M['skin']), w_torso)
    # singlet: one closed shell with thickness. inner ring at the hem, J rows up to the cut edge, inner ring at the neck/armholes
    seg = 96; J = 10; rows = []
    A = [2 * math.pi * i / seg for i in range(seg)]
    rows.append([bxy(a, ZH, -.004) for a in A])
    for j in range(J):
        rows.append([bxy(a, ZH + (ztop(a) - ZH) * j / (J - 1), soff(ZH + (ztop(a) - ZH) * j / (J - 1))) for a in A])
    rows.append([bxy(a, ztop(a), -.006) for a in A])
    vs = [p for r in rows for p in r]; fs = []; uvs = []
    uvv = lambda p: (p.z - .44) / .46
    for j in range(len(rows) - 1):
        for i in range(seg):
            i2 = (i + 1) % seg
            fs.append((j * seg + i, (j + 1) * seg + i, (j + 1) * seg + i2, j * seg + i2))
            uvs.append([(i / seg, uvv(rows[j][i])), (i / seg, uvv(rows[j + 1][i])), ((i + 1) / seg, uvv(rows[j + 1][i2])), ((i + 1) / seg, uvv(rows[j][i2]))])
    setw(mk('singlet', vs, fs, M['singlet'], uvs), w_torso)
    # bold red piping on the neck/armhole edge and the hem
    setw(ring('pipe_top', [bxy(2 * math.pi * i / 96, ztop(2 * math.pi * i / 96), soff(ztop(2 * math.pi * i / 96)) + .004) for i in range(96)], .0135, M['red'], seg=6), w_torso)
    setw(ring('pipe_hem', [bxy(2 * math.pi * i / 64, ZH + .006, soff(ZH) + .002) for i in range(64)], .014, M['red'], seg=6), w_torso)
    setw(sweep('neck', [(0, BY + .01, .84), (0, BY + .02, .95), (0, BY + .02, 1.08)], [.13, .126, .13], M['skin'], seg=24), w_neck)
    # shorts
    setw(ell('hips', (0, BY, .465), (.37, .31, .10), M['shorts'], seg=20), w_hips)
    for s in (-1, 1):
        sl = sweep('short_leg', [(s * .19, BY, .50), (s * .195, BY, .40), (s * .198, BY, .355), (s * .20, BY, .33)], [.20, .20, .197, .195], [M['shorts'], M['shorts_t']], seg=24, lip=(.012, .14))
        for p in sl.data.polygons:
            if 5 * 24 <= p.index < 8 * 24: p.material_index = 1
        setw(sl, w_legtop_s(s))
        setw(sweep('leg', [(s * .20, BY, .36), (s * .20, BY, .22), (s * .195, BY, .105)], [.105, .10, .094], M['skin'], seg=20), w_legskin)
        setw(ell('foot', (s * .195, BY + .075, .078), (.098, .165, .058), M['skin'], seg=20), w_foot)
        setw(ell('sole', (s * .195, BY + .075, .032), (.125, .215, .032), M['red'], seg=20), w_sole)
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
    hand, _ = so.remesh(voxel=.0065, smooth=6, smooth_factor=.6, target_tris=950)
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
    rnd = random.Random(5); so = H.Soup('hair'); n = 420
    for i in range(n):
        z = 1 - 2 * (i + .5) / n; a = i * 2.39996; r = math.sqrt(1 - z * z); d = V((r * math.cos(a), r * math.sin(a), z))
        az = math.degrees(math.atan2(abs(d.x), d.y)); el = math.degrees(math.asin(d.z))
        top = 26 + 30 * ss(100, 180, az) - 22 * ss(70, 100, az) * (1 - ss(100, 180, az)) * 0
        if az < 78 or el > top or el < -30 or (az < 115 and el < -14): continue
        so.sphere(HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z)) * .93, .125, seg=12)
    hair, _ = so.remesh(voxel=.012, smooth=30, smooth_factor=.8, target_tris=2600)
    H.set_material(hair, M['hair']); reg(hair); setw(hair, w_head)
    rs = random.Random(11)
    def spike(b, d, L, r0, bend):
        d = V(d).normalized(); side = d.cross(Z).normalized() * bend
        pts = [b - d * .04, b + d * L * .5 + side, b + d * L + side * 2.2 + Z * .02 * bend]
        setw(sweep('spike', pts, [r0 * 1.3, r0 * .95, r0 * .3], M['hair'], seg=8), w_head)
    for s in (-1, 1):
        for el, az, L, r0 in ((30, 88, .24, .052), (18, 100, .34, .058), (4, 112, .30, .05), (-8, 124, .24, .045), (38, 105, .2, .045)):
            a = math.radians(az); e_ = math.radians(el + rs.uniform(-4, 4))
            d = V((s * math.sin(a) * math.cos(e_), math.cos(a) * math.cos(e_), math.sin(e_)))
            b = HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z)) * .96
            spike(b, d + V((0, 0, .3 + rs.uniform(-.1, .2))), L * rs.uniform(.9, 1.2), r0, rs.uniform(-.05, .05))
    for fx, fy, lean, L in ((-.14, .04, -1, .14), (.01, -.04, .3, .17), (.15, .05, 1, .13)):
        zz = math.sqrt(max(0, 1 - (fx / HR.x) ** 2 - (fy / HR.y) ** 2)) * HR.z
        b = HC + V((fx, fy, zz - .03)); d = V((lean * .35, .05, 1)).normalized()
        spike(b, d, L, .05, lean * .025)
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
base = dict(bz=.2, tilt=-.006, arch=.022, bw=.036, eye='bead', es=(1.0, 1.0), cut=None, hl=.0, wr=0, w=.33, curve=.07, up=.012, dn=.075, tt=.58, tg=.12, cz=-.255, arc=1.0,
            bo=(.05, -.018), bt=(-.03, .075), ps=(1.0, .68), pd=(.0, .0))
def ex(**kw): d = dict(base); d.update(kw); return d
EXPR['base'] = ex()
EXPR['smile'] = ex(w=.32, curve=.085, up=.004, dn=.03, tt=.5, tg=0, bo=(.02, 0), bt=(0, .02), ps=(.9, .8), es=(.95, .95))
EXPR['mouth_open'] = ex(w=.24, curve=.01, up=.03, dn=.125, tt=.26, tg=.34, bo=(.07, .03), bt=(-.02, .0), es=(1.1, 1.1), ps=(.8, .6))
EXPR['blink'] = ex(eye='arc', arc=.2)
EXPR['angry'] = ex(bz=.235, tilt=.11, arch=-.004, bw=.062, es=(1.08, 1.0), cut=(.022, .6), wr=-.02, w=.31, curve=-.07, up=.03, dn=.07, tt=1.0, tg=0, cz=-.25, bo=(.045, .0), bt=(.03, .06), ps=(.95, .62))
EXPR['grin'] = ex(bz=.225, tilt=-.01, arch=.034, wr=.022, w=.345, curve=.075, up=.01, dn=.13, tt=.55, tg=.14, cz=-.26, bo=(.07, -.01), bt=(-.05, .07), es=(1.1, 1.1), ps=(.85, .58))
EXPR['ult'] = ex(bz=.215, tilt=.075, arch=.004, bw=.05, es=(1.2, 1.25), wr=.012, w=.34, curve=.0, up=.05, dn=.15, tt=.3, tg=.36, cz=-.255, bo=(.06, -.02), bt=(.0, .1), ps=(.7, .5))
FM = ['skin', 'lip', 'brow', 'eye', 'white', 'line', 'mouth', 'teeth', 'tongue', 'blush']
HSEG, HRING = 56, 28

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
        blob(s * EXe, EZe, (.036 * pr, .02, .04 * pr), .02, 'eye', show=bead, seg=16, d=(-s * .006 + e['pd'][0], e['pd'][1]), cut=ct)
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

# ---------------------------------------------------------------- rig
LEG = {}
for _k in (-1, 1): LEG[_k] = (V((_k * .20, BY, .52)), V((_k * .20, BY, KNEE_Z)), V((_k * .20, BY, ANK_Z)))
BONES = [
    ('root', (0, 0, 0), (0, 0, 0.25), None),
    ('hips', (0, BY, .50), (0, BY, .64), 'root'),
    ('spine', (0, BY, .64), (0, BY, .76), 'hips'),
    ('chest', (0, BY, .76), (0, BY, .86), 'spine'),
    ('neck', (0, BY, .86), (0, BY, 1.03), 'chest'),
    ('head', (0, BY, 1.03), (0, BY, 1.95), 'neck'),
    ('eye.l', tuple(surf(-EXe, EZe)[0]), tuple(surf(-EXe, EZe)[0] + V((0, .06, 0))), 'head'),
    ('eye.r', tuple(surf(EXe, EZe)[0]), tuple(surf(EXe, EZe)[0] + V((0, .06, 0))), 'head'),
]
for k, side in ((-1, 'l'), (1, 'r')):
    sh, el, wr = ARM[k]; hp, kn, an = LEG[k]
    BONES += [
        ('upperarm.' + side, tuple(sh), tuple(el), 'chest'),
        ('lowerarm.' + side, tuple(el), tuple(wr), 'upperarm.' + side),
        ('hand.' + side, tuple(wr), tuple(wr + V((0, .10, -.02))), 'lowerarm.' + side),
        ('handslot.' + side, tuple(wr + V((0, .06, 0))), tuple(wr + V((0, .14, 0))), 'hand.' + side),
        ('upperleg.' + side, tuple(hp), tuple(kn), 'hips'),
        ('lowerleg.' + side, tuple(kn), tuple(an), 'upperleg.' + side),
        ('foot.' + side, tuple(an), (k * .20, BY + .20, .05), 'lowerleg.' + side),
        ('toes.' + side, (k * .20, BY + .20, .05), (k * .20, BY + .31, .04), 'foot.' + side),
    ]
BONES.append(('prop', (0, 0, 0), (0, 0, 0.3), 'root'))
RIGID = {'eye.l', 'eye.r', 'prop', 'handslot.l', 'handslot.r'}

def make_armature():
    arm = bpy.data.armatures.new('siao_rig'); ob = bpy.data.objects.new('siao_rig', arm)
    SC.collection.objects.link(ob); H.select_only([ob], ob)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, h, t, parent in BONES:
        b = arm.edit_bones.new(name); b.head = Vector(h) * KSC; b.tail = Vector(t) * KSC
        if parent: b.parent = arm.edit_bones[parent]; b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in arm.bones: b.use_deform = b.name not in RIGID
    return ob

def rest_mat(rig, name): return rig.data.bones[name].matrix_local
def world_quat_to_local(rig, pb, q):
    M = rest_mat(rig, pb.name).to_3x3(); return (M.inverted() @ q.to_matrix() @ M).to_quaternion()
def set_world_rot(rig, pb, q):
    pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = world_quat_to_local(rig, pb, q)
def axis_rot(axis, deg): return Quaternion(Vector(axis), math.radians(deg))
def reset_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)


# =====================================================================================
# animation: hunched, low, animal body language
# =====================================================================================
FPS = 30
ANIM_BONES = ['hips', 'spine', 'chest', 'neck', 'head', 'upperarm.l', 'lowerarm.l', 'hand.l', 'upperarm.r', 'lowerarm.r', 'hand.r',
              'upperleg.l', 'lowerleg.l', 'foot.l', 'upperleg.r', 'lowerleg.r', 'foot.r']

def hips_move(rig, dy, dz):
    pb = rig.pose.bones['hips']; pb.location = rest_mat(rig, 'hips').to_3x3().inverted() @ Vector((0, dy, dz))

def rot(rig, name, rx=0.0, ry=0.0, rz=0.0):
    """World-axis euler in degrees. rx < 0 leans the top forward (+Y). For a leg or arm rx > 0 swings it forward."""
    set_world_rot(rig, rig.pose.bones[name], axis_rot(Z, rz) @ axis_rot(Y, ry) @ axis_rot(X, rx))

def crouch(rig, bend, lift=None):
    """Knees bent `bend` degrees, feet kept flat, hips dropped to match."""
    for side in ('l', 'r'):
        rot(rig, 'upperleg.' + side, rx=bend * 0.5); rot(rig, 'lowerleg.' + side, rx=-bend); rot(rig, 'foot.' + side, rx=bend * 0.5)
    drop = (0.25 + 0.20) * (1 - math.cos(math.radians(bend * 0.5)))
    return -drop if lift is None else lift

def lerp_pose(a, b, u):
    return {k: tuple(a[k][i] + (b[k][i] - a[k][i]) * u for i in range(len(a[k]))) for k in a}

def apply_pose(rig, P):
    for k, v in P.items():
        if k == 'hips_t': hips_move(rig, v[0], v[1])
        else: rot(rig, k, *v)

def keyed(keys, t):
    """keys: [(t, pose dict)], pose dicts share the same keys. Smoothstep between neighbours, hold the ends."""
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = smoothstep(0, 1, (t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return lerp_pose(a, b, u)
    return keys[-1][1]

def pose_frame(rig, t, kind):
    reset_pose(rig)
    s = math.sin(2 * math.pi * t); c = math.cos(2 * math.pi * t)
    if kind == 'idle':
        # low and hunched, weight shifting, a slow head tilt and a quick sniff twitch around a third of the way through
        snf = max(0.0, math.sin(2 * math.pi * (t - 0.30) * 1.0)) ** 10
        twitch = 5.0 * snf * math.sin(2 * math.pi * t * 9)
        gate = max(0.0, math.sin(2 * math.pi * (t - 0.1) * 2)) ** 4; jit = gate * math.sin(2 * math.pi * t * 14) + .25 * math.sin(2 * math.pi * t * 11)
        rot(rig, 'spine', rx=-10); rot(rig, 'chest', rx=-16 + 1.5 * s + 1.5 * jit, rz=2.0 * c + 2 * jit)
        rot(rig, 'neck', rx=10); rot(rig, 'head', rx=17 + twitch - 2 * s + 3 * jit, ry=9 * math.sin(2 * math.pi * t + 0.8) + 5 * jit, rz=-6 * c + 3 * jit)
        dz = crouch(rig, 22 + 2 * s)
        hips_move(rig, 0.02, dz + 0.008 * s)
        for k, side in ((-1, 'l'), (1, 'r')):
            rot(rig, 'upperarm.' + side, rx=48 + 4 * s * k + 5 * jit * k, ry=k * -8, rz=k * -20); rot(rig, 'lowerarm.' + side, rx=62 + 5 * c * k + 8 * jit); rot(rig, 'hand.' + side, rx=-20 + 10 * s + 14 * jit * k)
    elif kind == 'run':
        # bounding, low, 18 degree lean, arms swept back and wide like a chasing animal
        rot(rig, 'spine', rx=-9); rot(rig, 'chest', rx=-15, rz=5 * s); rot(rig, 'neck', rx=6); rot(rig, 'head', rx=14, rz=-4 * s, ry=2 * c)
        for k, sg in ((-1, 1), (1, -1)):
            side = 'l' if k < 0 else 'r'; ph = s * sg
            rot(rig, 'upperleg.' + side, rx=12 + 40 * ph)
            rot(rig, 'lowerleg.' + side, rx=-25 - 65 * max(0.0, -ph))
            rot(rig, 'foot.' + side, rx=10 + 20 * max(0.0, -ph))
            rot(rig, 'upperarm.' + side, rx=-72 - 12 * ph, ry=k * -10, rz=k * -24)
            rot(rig, 'lowerarm.' + side, rx=22 - 8 * ph)
            rot(rig, 'hand.' + side, rx=-15)
        hips_move(rig, 0.04, -0.09 + 0.05 * abs(s))
    elif kind == 'attack':
        # haymaker with the right arm: coil, swing across, follow through, recover (ACT.siao in chope.html)
        rest = {'chest': (-9, 0, 0), 'spine': (-5, 0, 0), 'head': (9, 0, 0), 'upperarm.r': (-6, 6, 4), 'lowerarm.r': (10, 0, 0), 'hand.r': (-10, 0, 0),
                'upperarm.l': (-6, -6, -4), 'lowerarm.l': (10, 0, 0), 'hand.l': (-10, 0, 0), 'hips_t': (0.02, -0.01)}
        coil = {'chest': (-14, 0, -28), 'spine': (-6, 0, -10), 'head': (12, 0, 24), 'upperarm.r': (-70, 20, 25), 'lowerarm.r': (70, 0, 0), 'hand.r': (-20, 0, 0),
                'upperarm.l': (25, -10, -10), 'lowerarm.l': (30, 0, 0), 'hand.l': (-10, 0, 0), 'hips_t': (-0.03, -0.015)}
        swing = {'chest': (-20, 0, 30), 'spine': (-10, 0, 14), 'head': (10, 0, -20), 'upperarm.r': (80, -30, -50), 'lowerarm.r': (15, 0, 0), 'hand.r': (-30, 0, 0),
                 'upperarm.l': (-40, -10, -10), 'lowerarm.l': (40, 0, 0), 'hand.l': (-10, 0, 0), 'hips_t': (0.12, -0.02)}
        thru = {'chest': (-18, 0, 38), 'spine': (-10, 0, 16), 'head': (10, 0, -26), 'upperarm.r': (60, -45, -75), 'lowerarm.r': (30, 0, 0), 'hand.r': (-30, 0, 0),
                'upperarm.l': (-45, -10, -10), 'lowerarm.l': (40, 0, 0), 'hand.l': (-10, 0, 0), 'hips_t': (0.10, -0.02)}
        P = keyed([(0.0, rest), (0.28, coil), (0.40, swing), (0.50, thru), (1.0, rest)], t)
        crouch(rig, 20); apply_pose(rig, P)
    elif kind == 'ult':
        # Wild Leap: the pounce. 20 degree lean, arms reaching forward, legs tucked under
        rot(rig, 'spine', rx=-10); rot(rig, 'chest', rx=-12); rot(rig, 'neck', rx=6); rot(rig, 'head', rx=14)
        for k, side in ((-1, 'l'), (1, 'r')):
            rot(rig, 'upperarm.' + side, rx=95, ry=k * -10, rz=k * -22); rot(rig, 'lowerarm.' + side, rx=15); rot(rig, 'hand.' + side, rx=-25)
            rot(rig, 'upperleg.' + side, rx=50 + (10 if k > 0 else 0)); rot(rig, 'lowerleg.' + side, rx=-95); rot(rig, 'foot.' + side, rx=25)
        hips_move(rig, 0.05, 0.22)

def key_all(rig, frame, names):
    for n in names:
        pb = rig.pose.bones[n]; pb.keyframe_insert('rotation_quaternion', frame=frame)
        if n == 'hips': pb.keyframe_insert('location', frame=frame)

def make_action(rig, name, kind, frames, loop=True):
    act = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act
    for f in range(frames + 1):
        t = (f % frames) / frames if loop else min(f, frames) / frames
        bpy.context.scene.frame_set(f); pose_frame(rig, t, kind); key_all(rig, f, ANIM_BONES)
    act.frame_range = (0, frames); act.use_frame_range = True; act.use_fake_user = True; return act

# ---------------------------------------------------------------- build, stage, shots, export
def join_groups():
    out = {}
    for key, name in (('body', 'siao_body'), ('head', 'siao_head'), ('gear', 'siao_headgear')):
        obs = [o for o in GROUPS[key] if o.name in bpy.data.objects]
        if key == 'head': out[key] = obs[0]; out[key].name = name; continue
        for o in obs:
            if o.data.users == 1 and not o.modifiers: pass
        H.select_only(obs, obs[0]); bpy.ops.object.join(); o = bpy.context.view_layer.objects.active; o.name = name; out[key] = o
    return out

def look_at(o, target):
    o.rotation_euler = (V(target) - o.location).to_track_quat('-Z', 'Y').to_euler()

def stage():
    w = bpy.data.worlds.new('World'); SC.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (.5, .62, .85, 1); bg.inputs[1].default_value = .45
    def lamp(name, kind, loc, energy, col, size=2.0, tgt=(0, .2, 1.1)):
        d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = col
        if kind == 'AREA': d.size = size
        else: d.spot_size = 1.0; d.spot_blend = .7; d.shadow_soft_size = .3
        o = bpy.data.objects.new(name, d); SC.collection.objects.link(o); o.location = loc; look_at(o, tgt); return o
    lamp('key', 'AREA', (1.9, 4.9, 6.0), 1800, (1.0, .79, .54), 2.2)
    lamp('fill', 'AREA', (-5.0, 3.5, 2.2), 420, (.62, .76, 1.0), 5.0)
    lamp('rim', 'SPOT', (-3.2, -4.6, 3.8), 5200, (1.0, .78, .52))
    prof = [(14, 0)] + [(-5 - 4 * math.sin(a), 4 - 4 * math.cos(a)) for a in [math.pi / 2 * i / 16 for i in range(17)]] + [(-9, 16)]
    vs = [(x, y, z) for (y, z) in prof for x in (-30, 30)]
    fs = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(prof) - 1)]
    me = bpy.data.meshes.new('cyc'); me.from_pydata(vs, [], fs); me.polygons.foreach_set('use_smooth', [True] * len(fs))
    m = bpy.data.materials.new('cyc'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (.46, .44, .42, 1); b.inputs['Roughness'].default_value = .85
    me.materials.append(m); SC.collection.objects.link(bpy.data.objects.new('cyc', me))
    SC.render.engine = 'BLENDER_EEVEE'; SC.eevee.taa_render_samples = 16 if QUICK else 96
    SC.view_settings.view_transform = 'AgX'; SC.view_settings.look = 'AgX - Punchy'
    SC.render.image_settings.file_format = 'PNG'; SC.render.film_transparent = False
    try: SC.eevee.use_raytracing = True
    except Exception: pass
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'HORIZONTAL'; cam = bpy.data.objects.new('cam', cd)
    SC.collection.objects.link(cam); SC.camera = cam; return cam

def shoot(cam, path, w, h, az, dist, target, width_m, cam_z=None):
    SC.render.resolution_x = w; SC.render.resolution_y = h; t = V(target); a = math.radians(az)
    cam.location = (t.x - dist * math.sin(a), t.y + dist * math.cos(a), cam_z if cam_z is not None else t.z)
    cam.data.lens = dist * 36 / width_m; look_at(cam, t)
    SC.render.filepath = path; bpy.ops.render.render(write_still=True)

def row(paths, out, cols=None):
    ims = []
    for p in paths:
        im = bpy.data.images.load(p); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); ims.append(a.reshape(h, w, 4))
    cols = cols or len(ims)
    rows = [np.concatenate(ims[i:i + cols], axis=1) for i in range(0, len(ims), cols)][::-1]
    a = np.concatenate(rows, axis=0); h, w = a.shape[:2]
    o = bpy.data.images.new('row', w, h, alpha=False); o.pixels.foreach_set(a.ravel()); o.filepath_raw = out; o.file_format = 'PNG'; o.save()

def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

def main():
    build_body(); build_arms(); build_head_gear(); build_face()
    print('BREAK', sorted([(o.name, tris(o)) for g in GROUPS.values() for o in g if o.name in bpy.data.objects], key=lambda t: -t[1])[:14])
    objs = join_groups(); body, head, gear = objs['body'], objs['head'], objs['gear']
    for o in (body, head, gear):
        H.select_only([o], o); o.scale = (KSC, KSC, KSC); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); o.data.update()
    print('SIAO_TRIS', {o.name: tris(o) for o in (body, head, gear)}, 'total', sum(tris(o) for o in (body, head, gear)))
    # shape keys carry no tangents. weights of joined body were set before joining.
    rig = make_armature()
    for o in (body, head, gear):
        o.parent = rig; md = o.modifiers.new('arm', 'ARMATURE'); md.object = rig
    # gear and body groups: ensure every vertex weighted
    for o in (body, head, gear):
        loose = sum(1 for v in o.data.vertices if not v.groups); print('unweighted', o.name, loose)
    face = head
    cam = stage()
    reset_pose(rig); set_expr(face, None)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(TMP, 'siao_rig.blend'))
    # actions
    SC.render.fps = FPS
    rig.animation_data_create()
    acts = [make_action(rig, 'idle', 'idle', 60), make_action(rig, 'run', 'run', 24), make_action(rig, 'attack', 'attack', 18, loop=False), make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    reset_pose(rig)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'siao.blend'))
    # export
    for k in face.data.shape_keys.key_blocks: k.value = 0.0
    for o in list(bpy.data.objects):
        if o.name in ('cyc',) or o.type in ('LIGHT', 'CAMERA'): o.select_set(False)
    H.select_only([body, head, gear, rig], rig)
    os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
        export_animations=True, export_animation_mode='ACTIONS', export_nla_strips=True, export_skins=True, export_def_bones=False,
        export_morph=True, export_morph_normal=False, export_image_format='AUTO', export_materials='EXPORT', export_texcoords=True,
        export_normals=True, export_all_influences=False, export_optimize_animation_size=True)
    print('EXPORT', OUT_GLB, os.path.getsize(OUT_GLB) // 1024, 'KB')
    # shots
    tmp = os.path.join(TMP, 'shots'); os.makedirs(tmp, exist_ok=True)
    def play(name, f):
        rig.animation_data.action = bpy.data.actions[name]; SC.frame_set(f + 5); SC.frame_set(f); bpy.context.view_layer.update()
    rig.animation_data.action = None; reset_pose(rig)
    play('idle', 0)
    shoot(cam, os.path.join(OUT, 'beauty.png'), 1600, 1600, 28, 8, (0, .05, .96), 2.8, cam_z=1.1)
    ps = []
    for i, az in enumerate((0, 90, 180)):
        rig.rotation_euler = (0, 0, math.radians(-az)); bpy.context.view_layer.update()
        p = os.path.join(tmp, f't{i}.png'); ps.append(p); shoot(cam, p, 534, 800, 0, 9, (0, 0, .96), 2.15, cam_z=.96)
    rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(OUT, 'turnaround.png'))
    rig.animation_data.action = None; reset_pose(rig); ps = []
    for name in ('smile', 'angry', 'grin', 'ult'):
        set_expr(face, name); p = os.path.join(tmp, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, 0, 1.44), 1.35)
    row(ps, os.path.join(OUT, 'expressions.png')); set_expr(face, None)
    ps = []
    for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
        for i in range(4):
            play(name, int(i * n / 4)); p = os.path.join(tmp, f'{name}_{i}.png'); ps.append(p)
            shoot(cam, p, 400, 500, 35, 7, (0, .1, 0.92), 2.25, cam_z=1.1)
    row(ps, os.path.join(OUT, 'anim_sheet.png'), 4)

main()
