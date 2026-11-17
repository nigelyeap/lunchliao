"""Ah Ma, toon style frame. Run: /opt/homebrew/bin/blender -b -P build.py  (SHOTS=hero,face,expr,turn to pick shots)
Look = 3-band ramp on N.L (Shader to RGB) + fresnel rim band + inverted-hull ink. All portable to three.js."""
import bpy, bmesh, math, os, random
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = '/Users/nigelyeap/Documents/lunchliao-hd'
HERE = ROOT + '/tools/blender/styles/toon'
OUT = ROOT + '/shots/styles/toon'
SHOTS = os.environ.get('SHOTS', 'hero,face,expr,turn').split(',')
bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
random.seed(3)

# ---------- colour + materials ----------
SAT = 1.3
def C(h):
    h = h.lstrip('#'); v = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    lin = [((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in v]
    l = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return tuple(min(max(l + (x - l) * SAT, 0), 1) for x in lin) + (1,)   # extra saturation so colours survive AgX

KEY_DIR = Vector((0.5, 0.5, 0.707)).normalized()      # front-left of a +Y camera, 45 deg up
RIM_DIR = Vector((-0.55, -0.7, 0.45)).normalized()    # back-right
FILL_DIR = Vector((-0.75, 0.45, 0.3)).normalized()
KEY_E = 3.0
T_LIT, T_HI = 0.16, 0.86

def toon(name, base, shadow=None, hi=0.3, tex=None, tint=(0.52, 0.5, 0.85, 1), rim=0.55, t_hi=T_HI):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    def mix(f, a, b, mode='MIX'):
        n = N.new('ShaderNodeMix'); n.data_type = 'RGBA'; n.blend_type = mode
        for i, v in ((0, f), (6, a), (7, b)):
            if isinstance(v, bpy.types.NodeSocket): L.new(v, n.inputs[i])
            else: n.inputs[i].default_value = v
        return n.outputs[2]
    def math_(op, a, b):
        n = N.new('ShaderNodeMath'); n.operation = op
        for i, v in ((0, a), (1, b)):
            if isinstance(v, bpy.types.NodeSocket): L.new(v, n.inputs[i])
            else: n.inputs[i].default_value = v
        return n.outputs[0]
    if tex:
        t = N.new('ShaderNodeTexImage'); t.image = tex
        hs = N.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = SAT; L.new(t.outputs['Color'], hs.inputs['Color'])
        base_s = hs.outputs['Color']
        shadow_s = mix(1.0, base_s, tint, 'MULTIPLY')
    else:
        base_s, shadow_s = base, (shadow or base)
    d = N.new('ShaderNodeBsdfDiffuse'); d.inputs['Color'].default_value = (1, 1, 1, 1)
    s = N.new('ShaderNodeShaderToRGB'); L.new(d.outputs[0], s.inputs[0])
    bw = N.new('ShaderNodeRGBToBW'); L.new(s.outputs[0], bw.inputs[0])
    lum = math_('MULTIPLY', bw.outputs[0], 1 / KEY_E)
    col = mix(math_('GREATER_THAN', lum, T_LIT), shadow_s, base_s)
    if hi:
        col = mix(math_('MULTIPLY', math_('GREATER_THAN', lum, t_hi), hi), col, (1, 0.96, 0.86, 1))
    if rim:
        g = N.new('ShaderNodeNewGeometry'); lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
        dp = N.new('ShaderNodeVectorMath'); dp.operation = 'DOT_PRODUCT'
        L.new(g.outputs['Normal'], dp.inputs[0]); dp.inputs[1].default_value = RIM_DIR
        rm = math_('MULTIPLY', math_('GREATER_THAN', lw.outputs['Facing'], 0.72), math_('GREATER_THAN', dp.outputs['Value'], 0.15))
        col = mix(math_('MULTIPLY', rm, rim), col, (1, 0.86, 0.6, 1))
    e = N.new('ShaderNodeEmission'); L.new(col, e.inputs['Color'])
    o = N.new('ShaderNodeOutputMaterial'); L.new(e.outputs[0], o.inputs['Surface'])
    return m

def flat(name, col, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    e = N.new('ShaderNodeEmission'); e.inputs['Color'].default_value = col; e.inputs['Strength'].default_value = strength
    o = N.new('ShaderNodeOutputMaterial'); L.new(e.outputs[0], o.inputs['Surface'])
    return m

_INK = {}
def ink(hexcol):
    if hexcol not in _INK:
        m = flat('ink_' + hexcol, C(hexcol)); m.use_backface_culling = True
        if hasattr(m, 'use_backface_culling_shadow'): m.use_backface_culling_shadow = True
        _INK[hexcol] = m
    return _INK[hexcol]

# ---------- mesh helpers ----------
TRIS = 0
COL = bpy.data.collections.new('ahma'); SC.collection.children.link(COL)

def mesh_obj(name, part, mat, ol=0.008, olc='#3a1e2a', weld=True, shadow=True, mi=None, recalc=True):
    global TRIS
    verts, faces = part[0], part[1]; uvs = part[2] if len(part) > 2 else None
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    if uvs:
        me.uv_layers.new(name='UVMap').data.foreach_set('uv', [c for f in uvs for uv in f for c in uv])
    if mi: me.polygons.foreach_set('material_index', mi)
    if weld or recalc:
        bm = bmesh.new(); bm.from_mesh(me)
        if weld: bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        if recalc: bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
    me.shade_smooth()
    TRIS += sum(len(p.vertices) - 2 for p in me.polygons)
    ob = bpy.data.objects.new(name, me); COL.objects.link(ob)
    mats = mat if isinstance(mat, list) else [mat]
    for m in mats: me.materials.append(m)
    ob.visible_shadow = shadow
    if ol:
        me.materials.append(ink(olc))
        md = ob.modifiers.new('outline', 'SOLIDIFY'); md.thickness = ol; md.offset = 1
        md.use_flip_normals = True; md.use_rim = False; md.material_offset = len(mats)
    return ob

def join(parts):
    V, F = [], []
    for p in parts:
        b = len(V); V += list(p[0]); F += [tuple(i + b for i in f) for f in p[1]]
    return V, F

def ellipsoid(c, r, nu=14, nv=8):
    c = Vector(c); V, F = [], []
    for j in range(nv + 1):
        ph = -math.pi / 2 + math.pi * j / nv
        for i in range(nu):
            th = 2 * math.pi * i / nu
            V.append(c + Vector((r[0] * math.cos(ph) * math.cos(th), r[1] * math.cos(ph) * math.sin(th), r[2] * math.sin(ph))))
    for j in range(nv):
        for i in range(nu):
            a = j * nu + i; b = j * nu + (i + 1) % nu; F.append((a, b, b + nu, a + nu))
    return V, F

def catmull(P, n=5):
    P = [np.array(p, float) for p in P]; out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for k in range(n):
            t = k / n
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1]); return out

def rounded(pts, rho, n=5):
    pts = [Vector(p) for p in pts]; out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a = (pts[i - 1] - pts[i]).normalized(); b = (pts[i + 1] - pts[i]).normalized()
        p0, p2 = pts[i] + a * rho, pts[i] + b * rho
        for k in range(n + 1):
            t = k / n; out.append((1 - t) ** 2 * p0 + 2 * t * (1 - t) * pts[i] + t * t * p2)
    out.append(pts[-1]); return out

def tube(pts, rad, seg=10, cap0='round', cap1='round', closed=False):
    """Swept tube. Returns verts, faces, uvs (uv in metres: around, along)."""
    P = [Vector(tuple(p)) for p in pts]; n = len(P)
    R = list(rad) if hasattr(rad, '__len__') else [rad] * n
    T = [((P[(i + 1) % n] - P[i - 1]) if closed else (P[min(i + 1, n - 1)] - P[max(i - 1, 0)])).normalized() for i in range(n)]
    ref = Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0))
    nr = (ref - T[0] * ref.dot(T[0])).normalized(); fr = []
    for i in range(n):
        nr = (nr - T[i] * nr.dot(T[i])).normalized(); fr.append((nr.copy(), T[i].cross(nr)))
    def cap(i, sg, style):
        c, r, t, f = P[i], R[i], T[i] * sg, fr[i]
        if style == 'round':
            return [(c + t * r * math.sin(a), r * math.cos(a), f) for a in (0.6, 1.15)] + [(c + t * r, 0, f)]
        if style == 'flat':   # open cuff look: lip, then a recessed disc
            return [(c, r * 0.8, f), (c - t * r * 0.4, r * 0.78, f), (c - t * r * 0.4, 0, f)]
        return []
    seq = []
    if not closed and cap0: seq += list(reversed(cap(0, -1, cap0)))
    seq += [(P[i], R[i], fr[i]) for i in range(n)]
    if not closed and cap1: seq += cap(n - 1, 1, cap1)
    V, F, U = [], [], []; vl = [0.0]
    for j in range(1, len(seq)): vl.append(vl[-1] + (seq[j][0] - seq[j - 1][0]).length + abs(seq[j][1] - seq[j - 1][1]))
    for c, r, (nn, b) in seq:
        for k in range(seg):
            a = 2 * math.pi * k / seg; V.append(c + (nn * math.cos(a) + b * math.sin(a)) * r)
    m = len(seq); circ = 2 * math.pi * max(R)
    for j in range(m if closed else m - 1):
        j2 = (j + 1) % m
        for k in range(seg):
            k2 = (k + 1) % seg
            F.append((j * seg + k, j * seg + k2, j2 * seg + k2, j2 * seg + k))
            u0, u1 = k / seg * circ, (k + 1) / seg * circ
            U.append(((u0, vl[j]), (u1, vl[j]), (u1, vl[j2]), (u0, vl[j2])))
    return V, F, U

def lathe(rows, seg=32, expo=2.0, xc=0.0, vlen=1.4):
    """rows: (z, rx, ry, yc). Elliptical (or superellipse) cross-sections. UV u wraps once, v = arc length / vlen."""
    V, F, U = [], [], []; vl = [0.0]
    for j in range(1, len(rows)):
        a, b = rows[j - 1], rows[j]; vl.append(vl[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    for z, rx, ry, yc in rows:
        for i in range(seg):
            a = 2 * math.pi * i / seg; cx, cy = math.cos(a), math.sin(a)
            if expo != 2.0:
                cx = math.copysign(abs(cx) ** (2 / expo), cx); cy = math.copysign(abs(cy) ** (2 / expo), cy)
            V.append(Vector((xc + rx * cx, yc + ry * cy, z)))
    for j in range(len(rows) - 1):
        for i in range(seg):
            i2 = (i + 1) % seg
            F.append((j * seg + i, j * seg + i2, (j + 1) * seg + i2, (j + 1) * seg + i))
            u0, u1 = i / seg, (i + 1) / seg
            U.append(((u0, vl[j] / vlen), (u1, vl[j] / vlen), (u1, vl[j + 1] / vlen), (u0, vl[j + 1] / vlen)))
    return V, F, U

def circle(c, n_dir, R, n=24, squash=(1, 1)):
    c = Vector(c); n_dir = Vector(n_dir).normalized()
    e1 = Vector((n_dir.y, -n_dir.x, 0)); e1 = e1.normalized() if e1.length > 1e-4 else Vector((1, 0, 0))
    e2 = n_dir.cross(e1)
    return [c + e1 * (R * squash[0] * math.cos(2 * math.pi * k / n)) + e2 * (R * squash[1] * math.sin(2 * math.pi * k / n)) for k in range(n)]

# ---------- samfu floral texture ----------
def make_tex(path, W=2048, H=1024):
    rng = np.random.default_rng(11)
    s8 = lambda h: np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)
    img = np.zeros((H, W, 3), np.float32); img[:] = s8('#16a3a0')
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    def blob(cx, cy, rx, ry, ang, col):
        for ox in (-W, 0, W):
            for oy in (-H, 0, H):
                x0, y0 = cx + ox, cy + oy; R = max(rx, ry) + 2
                if x0 + R < 0 or x0 - R > W or y0 + R < 0 or y0 - R > H: continue
                a, b = int(max(0, y0 - R)), int(min(H, y0 + R + 1)); c, d = int(max(0, x0 - R)), int(min(W, x0 + R + 1))
                dx, dy = xx[a:b, c:d] - x0, yy[a:b, c:d] - y0
                u = dx * math.cos(ang) + dy * math.sin(ang); v = -dx * math.sin(ang) + dy * math.cos(ang)
                al = np.clip((1 - np.sqrt((u / rx) ** 2 + (v / ry) ** 2)) * min(rx, ry) + 0.5, 0, 1)[..., None]
                img[a:b, c:d] = img[a:b, c:d] * (1 - al) + col * al
    pts = []
    for _ in range(6000):
        p = (rng.random() * W, rng.random() * H)
        if all(math.hypot(min(abs(p[0] - q[0]), W - abs(p[0] - q[0])), min(abs(p[1] - q[1]), H - abs(p[1] - q[1]))) > 175 for q in pts): pts.append(p)
    pal = [('#ff9fb8', '#ffd447'), ('#fff1d8', '#ff8a5c'), ('#ff7f8e', '#ffe08a')]
    for i, (cx, cy) in enumerate(pts):
        R = rng.uniform(50, 66); rot = rng.random() * 6.28; pc, cc = pal[i % 3]
        for k in range(2):
            a = rot + 0.6 + k * 2.6
            blob(cx + math.cos(a) * R * 1.05, cy + math.sin(a) * R * 1.05, R * 0.5, R * 0.22, a, s8('#8fe0b0'))
        for k in range(5):
            a = rot + k * 2 * math.pi / 5
            blob(cx + math.cos(a) * R * 0.55, cy + math.sin(a) * R * 0.55, R * 0.42, R * 0.42, 0, s8(pc))
        blob(cx, cy, R * 0.27, R * 0.27, 0, s8(cc))
    for _ in range(140):
        p = (rng.random() * W, rng.random() * H)
        if all(math.hypot(p[0] - q[0], p[1] - q[1]) > 110 for q in pts): blob(p[0], p[1], 9, 9, 0, s8('#fff1d8'))
    im = bpy.data.images.new('samfu_gen', W, H, alpha=False)
    rgba = np.concatenate([img[::-1], np.ones((H, W, 1), np.float32)], axis=2)
    im.pixels.foreach_set(rgba.ravel()); im.filepath_raw = path; im.file_format = 'PNG'; im.save()
    bpy.data.images.remove(im)
    return bpy.data.images.load(path)

# ---------- palette ----------
TEX = make_tex(HERE + '/samfu.png')
M = dict(
    skin=toon('skin', C('#f7c193'), C('#db826c'), hi=0.0), blush=toon('blush', C('#f59a8c'), C('#d8756f'), hi=0, rim=0),
    skinline=toon('skinline', C('#b9604e'), C('#9c4a48'), hi=0, rim=0),
    hair=toon('hair', C('#d6d7e6'), C('#8e86bd'), hi=0.9, t_hi=0.8), samfu=toon('samfu', None, tex=TEX, hi=0.12),
    teal=toon('teal', C('#16a3a0'), C('#0c527f'), hi=0.12), pipe=toon('pipe', C('#ec3f8e'), C('#9c1f74'), hi=0.3),
    slacks=toon('slacks', C('#34366e'), C('#1c1a45'), hi=0.0), red=toon('red', C('#ee3a30'), C('#a51c3c'), hi=0.35),
    metal=toon('metal', C('#cdd7e8'), C('#7c8cb2'), hi=1.0, t_hi=0.72), rubber=toon('rubber', C('#55556a'), C('#2e2c45'), hi=0.2),
    gold=toon('gold', C('#f7c744'), C('#c47a20'), hi=0.9, t_hi=0.7), jade=toon('jade', C('#45cc90'), C('#1f8a72'), hi=0.8, t_hi=0.75),
    sclera=toon('sclera', C('#fffaf2'), C('#d8cde8'), hi=0, rim=0), iris=toon('iris', C('#5c2e1a'), C('#45221c'), hi=0, rim=0),
    iris2=toon('iris2', C('#c0702e'), C('#96522e'), hi=0, rim=0), pupil=flat('pupil', C('#1c0d0a')),
    white=flat('white', (1, 1, 1, 1), 1.6), lash=flat('lash', C('#3a1e2a')), brow=toon('brow', C('#4e4866'), C('#3a3352'), hi=0, rim=0),
    mouth=flat('mouth', C('#6a1c2c')), teeth=toon('teeth', C('#fffaf0'), C('#e0d4e4'), hi=0, rim=0),
    tongue=toon('tongue', C('#f47f80'), C('#d0606c'), hi=0, rim=0),
    leekw=toon('leekw', C('#f1f5dd'), C('#b9c9b4'), hi=0), leekg=toon('leekg', C('#62b84a'), C('#2f7d50'), hi=0.2),
    orange=toon('orange', C('#ff9a2e'), C('#d2562a'), hi=0.5, t_hi=0.8),
)
INK = dict(skin='#7c3a30', hair='#4a3f78', samfu='#0b3a55', slacks='#100e2a', red='#5c0f22', metal='#2c3654', gold='#70400c', jade='#0e4a3c', pipe='#5c0f44', veg='#1f4a2a')

# ---------- head ----------
HC = Vector((0, 0.04, 1.70))
def sstep(a, b, x):
    t = min(max((x - a) / (b - a), 0), 1); return t * t * (3 - 2 * t)

def head_pt(th, ph, jaw=0.0, scale=1.0):
    h = math.cos(ph) ** (0.55 if ph < 0 else 1.0)          # lower half stays wide, then turns in: a soft U jaw
    dx, dy, dz = h * math.cos(th), h * math.sin(th), math.sin(ph)
    rx = 0.375 * (1 + 0.10 * math.exp(-((dz + 0.3) / 0.3) ** 2))
    p = Vector((rx * dx, 0.345 * dy, (0.32 if dz > 0 else 0.34) * dz)) * scale
    if dz < 0: p.z -= jaw * sstep(0.0, 0.7, -dz) * (0.4 + 0.6 * max(dy, 0))
    return HC + p

NU, NV = 56, 32
def head_mesh(jaw=0.0, scale=1.0):
    V = [head_pt(0, -math.pi / 2, jaw, scale)]
    for j in range(1, NV):
        for i in range(NU): V.append(head_pt(2 * math.pi * i / NU, -math.pi / 2 + math.pi * j / NV, jaw, scale))
    V.append(head_pt(0, math.pi / 2, jaw, scale)); top = len(V) - 1; F = []
    r = lambda j, i: 1 + (j - 1) * NU + i % NU
    for i in range(NU):
        F.append((0, r(1, i + 1), r(1, i))); F.append((top, r(NV - 1, i), r(NV - 1, i + 1)))
        for j in range(1, NV - 1): F.append((r(j, i), r(j, i + 1), r(j + 1, i + 1), r(j + 1, i)))
    return V, F

def hairline(d):   # minimum dz for hair at this direction
    az = math.atan2(abs(d.x), d.y); return 0.66 - 1.25 * (1 - math.cos(az)) / 2

# ---------- face decals (2D face space -> projected onto the head) ----------
EXPR = dict(
    smile=dict(hu=.046, hl=.032, cut=0, slant=.004, closed=False, ir=.037, pr=.017, lz=.002, b0=(.058, .112), b1=(.205, .106), bb=.022,
               mz=-.158, mw=.080, cl=.030, uh=0, lh=0, pu=.5, pl=.5, tu=0, tl=0, jaw=0),
    angry=dict(hu=.042, hl=.028, cut=.050, slant=.012, closed=False, ir=.034, pr=.015, lz=-.004, b0=(.042, .060), b1=(.200, .138), bb=.004,
               mz=-.165, mw=.090, cl=-.018, uh=.016, lh=.042, pu=.3, pl=.35, tu=.06, tl=.06, jaw=0),
    grin=dict(hu=.036, hl=0, cut=0, slant=0, closed=True, ir=.037, pr=.017, lz=0, b0=(.065, .130), b1=(.205, .112), bb=.026,
              mz=-.150, mw=.120, cl=.036, uh=.006, lh=.090, pu=.5, pl=.6, tu=.027, tl=0, jaw=.015),
    ult=dict(hu=.058, hl=.040, cut=.032, slant=.014, closed=False, ir=.026, pr=.010, lz=0, b0=(.045, .074), b1=(.205, .160), bb=.006,
             mz=-.160, mw=.100, cl=-.006, uh=.040, lh=.108, pu=.45, pl=.5, tu=.024, tl=.016, jaw=.04),
)
FM = ['blush', 'sclera', 'iris', 'iris2', 'pupil', 'white', 'lash', 'skinline', 'brow', 'mouth', 'teeth', 'tongue']

class Decal:
    def __init__(s): s.v, s.f, s.m = [], [], []
    def grid(s, fn, nx, ny, mat, off):
        b = len(s.v)
        for j in range(ny + 1):
            for i in range(nx + 1): x, z = fn(i / nx, j / ny); s.v.append((x, z, off))
        for j in range(ny):
            for i in range(nx):
                a = b + j * (nx + 1) + i; s.f.append((a, a + 1, a + nx + 2, a + nx + 1)); s.m.append(FM.index(mat))
    def disc(s, cx, cz, rx, rz, mat, off, clamp=lambda x, z: (x, z), n=16, rings=3):
        s.grid(lambda u, v: clamp(cx + rx * v * math.cos(2 * math.pi * u), cz + rz * v * math.sin(2 * math.pi * u)), n, rings, mat, off)

def face2d(e):
    d = Decal(); EX, EZ, W = 0.135, -0.005, 0.060
    S = math.sin; PI = math.pi; c01 = lambda t: min(max(t, 0), 1)
    for sg in (1, -1):
        d.disc(sg * 0.222, -0.092, 0.058, 0.034, 'blush', 0.0012, n=14, rings=2)
        tt = lambda x: c01((sg * x - (EX - W)) / (2 * W))
        if e['closed']:
            lo = up = lambda x: EZ + e['hu'] * S(PI * tt(x)) ** 0.8 - 0.012
        else:
            lo = lambda x: EZ - e['hl'] * S(PI * tt(x)) ** 0.8 + e['slant'] * (tt(x) - .5)
            up = lambda x: max(EZ + e['hu'] * S(PI * tt(x)) ** 0.6 + e['slant'] * (tt(x) - .5) - e['cut'] * (1 - tt(x)) ** 1.5, lo(x))
        xs = lambda u: sg * (EX - W + 2 * W * u)
        def clamp(x, z):
            x = sg * min(max(sg * x, EX - W), EX + W); return x, min(max(z, lo(x)), up(x))
        d.grid(lambda u, v: (xs(u), lo(xs(u)) + (up(xs(u)) - lo(xs(u))) * v), 14, 3, 'sclera', 0.002)
        ix, iz, ir = sg * (EX - 0.004), EZ + e['lz'], e['ir']
        d.disc(ix, iz, ir, ir, 'iris', 0.003, clamp, 18, 3)
        d.disc(ix, iz - ir * 0.38, ir * 0.72, ir * 0.55, 'iris2', 0.0037, clamp, 14, 2)
        d.disc(ix, iz, e['pr'], e['pr'], 'pupil', 0.0044, clamp, 12, 2)
        d.disc(ix + ir * 0.42, iz + ir * 0.42, ir * 0.30, ir * 0.30, 'white', 0.0052, clamp, 10, 2)
        d.disc(ix - ir * 0.40, iz - ir * 0.45, ir * 0.14, ir * 0.14, 'white', 0.0052, clamp, 8, 1)
        def lash(u, v):                      # thick upper lash line with an outer flick
            uu = -0.05 + 1.17 * u; x = xs(uu); zc = up(xs(c01(uu))) + max(uu - 1, 0) * 0.30
            th = 0.004 + 0.012 * S(PI * c01(uu * 0.85 + 0.1)) * (1.25 if e['closed'] else 1)
            return x, zc - 0.002 + (th + 0.002) * v
        d.grid(lash, 16, 1, 'lash', 0.006)
        d.grid(lambda u, v: (xs(0.2 + 0.75 * u), lo(xs(0.2 + 0.75 * u)) - 0.011 - 0.0035 * v * S(PI * u)), 8, 1, 'skinline', 0.0015)
        b0, b1 = e['b0'], e['b1']
        def brow(u, v):
            x = sg * (b0[0] + (b1[0] - b0[0]) * u); z = b0[1] + (b1[1] - b0[1]) * u + e['bb'] * S(PI * u)
            th = 0.036 * (1 - 0.62 * u) * (0.55 + 0.45 * S(PI * c01(u * 0.9 + 0.12)))
            return x, z + th * (v - 0.5)
        d.grid(brow, 10, 1, 'brow', 0.003)
    mz, mw = e['mz'], e['mw']
    base = lambda s: mz + e['cl'] * s * s
    k = lambda s: max(1 - s * s, 0)
    up = lambda s: base(s) + e['uh'] * k(s) ** e['pu']
    lo = lambda s: base(s) - e['lh'] * k(s) ** e['pl']
    mid = lambda s: (up(s) + lo(s)) / 2
    d.grid(lambda u, v: (mw * (2 * u - 1), lo(2 * u - 1) + (up(2 * u - 1) - lo(2 * u - 1)) * v), 16, 3, 'mouth', 0.002)
    def tclamp(x, z):
        s = min(max(x / mw, -0.85), 0.85); a = lo(s) + 0.004
        return s * mw, min(max(z, a), max(a, up(s) - e['tu'] - 0.006))
    d.disc(0, lo(0) + 0.38 * e['lh'], 0.6 * mw, 0.45 * e['lh'] + 1e-4, 'tongue', 0.003, tclamp, 14, 2)
    def tup(u, v):
        s = 0.92 * (2 * u - 1); z1 = max(up(s) - e['tu'], (mid(s) + 0.003) if e['tl'] else lo(s))
        return s * mw, up(s) + (min(z1, up(s)) - up(s)) * v
    def tlo(u, v):
        s = 0.92 * (2 * u - 1); z1 = min(lo(s) + e['tl'], mid(s) - 0.003)
        return s * mw, lo(s) + (max(z1, lo(s)) - lo(s)) * v
    d.grid(tup, 14, 1, 'teeth', 0.004); d.grid(tlo, 14, 1, 'teeth', 0.004)
    lipth = lambda s: 0.0035 + 0.0035 * k(min(abs(s), 1))
    d.grid(lambda u, v: (mw * 1.05 * (2 * u - 1), (up(2 * u - 1) if abs(2 * u - 1) <= 1 else base(1.05 * (2 * u - 1))) - 0.001 + (lipth(2 * u - 1) + 0.001) * v), 18, 1, 'lash', 0.0055)
    d.grid(lambda u, v: (mw * (2 * u - 1), lo(2 * u - 1) + 0.001 - (lipth(2 * u - 1) + 0.001) * v), 18, 1, 'lash', 0.0055)
    for sg in (1, -1):                       # smile lines, nose side to mouth corner
        p0 = (sg * 0.060, -0.082); p2 = (sg * (mw + 0.030), base(1) - 0.012); p1 = (sg * (mw + 0.058), -0.105)
        def sl(u, v):
            x = (1 - u) ** 2 * p0[0] + 2 * u * (1 - u) * p1[0] + u * u * p2[0]; z = (1 - u) ** 2 * p0[1] + 2 * u * (1 - u) * p1[1] + u * u * p2[1]
            return x + (0.0008 + 0.005 * S(PI * u)) * (v - 0.5), z
        d.grid(sl, 10, 1, 'skinline', 0.0015)
    return d

def face_n(p, n):
    d = (Vector(p) - HC).normalized()
    w = 0.85 * sstep(0.15, 0.7, d.y) * sstep(-0.97, -0.72, d.z)
    return (Vector(n) * (1 - w) + Vector((d.x * 0.7, 1, 0.2)).normalized() * w).normalized()

def set_normals(ob, ns):
    ob.data.normals_split_custom_set_from_vertices([tuple(n) for n in ns])

def project(d, bvh, nout=None):
    out = []
    for x, z, off in d.v:
        loc, nrm, _, _ = bvh.ray_cast(Vector((x, 3.0, HC.z + z)), Vector((0, -1, 0)))
        if loc is None: loc, nrm = Vector((x, HC.y, HC.z + z)), Vector((0, 1, 0))
        out.append(loc + nrm * off)
        if nout is not None: nout.append(face_n(loc, nrm))
    return out

def build_head():
    hv, hf = head_mesh()
    head = mesh_obj('head', (hv, hf), M['skin'], olc=INK['skin'], weld=False)
    set_normals(head, [face_n(v.co, head.data.vertex_normals[i].vector) for i, v in enumerate(head.data.vertices)])
    head.shape_key_add(name='smile')
    decs = {k: face2d(e) for k, e in EXPR.items()}
    d0 = decs['smile']
    faces = []
    for fi, f in enumerate(d0.f):            # wind every decal face toward +Y, judged where it is largest
        best = 0.0
        for dd in decs.values():
            p = [dd.v[i] for i in f]; a = sum(p[i][0] * p[(i + 1) % 4][1] - p[(i + 1) % 4][0] * p[i][1] for i in range(4))
            if abs(a) > abs(best): best = a
        faces.append(tuple(reversed(f)) if best > 0 else f)
    face = None
    for k, e in EXPR.items():
        ns = []; v, _ = head_mesh(e['jaw']); pv = project(decs[k], BVHTree.FromPolygons(v, hf), ns)
        if face is None:
            face = mesh_obj('face', (pv, faces), [M[n] for n in FM], ol=0, weld=False, shadow=False, mi=d0.m, recalc=False)
            set_normals(face, ns)
            face.shape_key_add(name='smile')
        else:
            for ob, co in ((head, v), (face, pv)):
                ob.shape_key_add(name=k).data.foreach_set('co', [c for p in co for c in p])
    # static bits: nose, ears, studs
    mesh_obj('nose', ellipsoid((0, HC.y + 0.335, HC.z - 0.068), (0.044, 0.040, 0.035), 14, 8), M['skin'], ol=0.004, olc=INK['skin'], shadow=False)
    for sg in (1, -1):
        mesh_obj('ear', ellipsoid((sg * 0.375, HC.y - 0.015, HC.z - 0.035), (0.04, 0.062, 0.088), 12, 8), M['skin'], olc=INK['skin'])
        mesh_obj('stud', ellipsoid((sg * 0.405, HC.y - 0.005, HC.z - 0.105), (0.024,) * 3, 10, 6), M['gold'], ol=0.004, olc=INK['gold'])
    return head, face

def build_hair():
    hv, hf = head_mesh(scale=1.03)
    ok = [((v - HC).normalized().z > hairline((v - HC).normalized()) + 0.04) for v in hv]
    parts = [(hv, [f for f in hf if all(ok[i] for i in f)])]
    N = 100; ga = math.pi * (3 - math.sqrt(5))
    for k in range(N):
        z = 1 - 2 * (k + 0.5) / N; r = math.sqrt(1 - z * z); d = Vector((r * math.cos(k * ga), r * math.sin(k * ga), z))
        if d.z < hairline(d) - 0.02: continue
        p = head_pt(math.atan2(d.y, d.x), math.asin(d.z)) + d * (0.0 + 0.012 * max(d.z, 0))
        p += Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0)) * 0.008
        rad = random.uniform(0.092, 0.112)
        parts.append(ellipsoid(p, (rad, rad, rad * 0.95), 16, 9))
    mesh_obj('hair', join(parts), M['hair'], olc=INK['hair'], ol=0.007)

def build_glasses():
    for sg in (1, -1):
        n = Vector((sg * 0.2, 0.98, 0)); c = Vector((sg * 0.135, HC.y + 0.375, HC.z - 0.005))
        ring = circle(c, n, 0.094, 28)
        mesh_obj('ring', tube(ring, 0.0085, 8, closed=True), M['gold'], ol=0.0035, olc=INK['gold'], shadow=False)
        e1 = Vector((n.y, -n.x, 0)).normalized()
        tp = catmull([c + e1 * (sg * 0.094), (sg * 0.352, HC.y + 0.215, HC.z + 0.004), (sg * 0.392, HC.y + 0.03, HC.z + 0.02)], 5)
        mesh_obj('temple', tube(tp, 0.007, 6), M['gold'], ol=0.003, olc=INK['gold'], shadow=False)
        # anime glint: two slanted bars on the lens
        V, F = [], []
        for a, w in ((0.0, 0.011), (0.02, 0.005)):
            b = len(V); o = c + n.normalized() * 0.002 + Vector((0.058 + a, 0, 0.052 - a * 0.9))
            for dx, dz in ((0, 0), (w, 0), (w + 0.022, 0.026), (0.022, 0.026)): V.append(o + Vector((dx - 0.03, 0, dz - 0.012)))
            F.append((b, b + 1, b + 2, b + 3))
        mesh_obj('glint', (V, F), M['white'], ol=0, shadow=False, recalc=False, weld=False)
    br = catmull([(-0.043, HC.y + 0.385, HC.z + 0.012), (0, HC.y + 0.398, HC.z + 0.03), (0.043, HC.y + 0.385, HC.z + 0.012)], 5)
    mesh_obj('bridge', tube(br, 0.0075, 6), M['gold'], ol=0.003, olc=INK['gold'], shadow=False)

# ---------- body ----------
WX, RZ, WY0, WY1 = 0.40, 0.92, 0.34, 0.78     # walker half width, rail height, rail back/front y

def build_body():
    rows = [(1.42, .16, .13, .03), (1.38, .25, .20, .03), (1.31, .385, .28, .03), (1.22, .435, .345, .035), (1.05, .465, .405, .05),
            (0.88, .485, .43, .055), (0.72, .49, .43, .05), (0.63, .505, .445, .045)]
    rows = [tuple(r) for r in catmull(rows, 3)] + [(0.63, .475, .415, .045), (0.68, .40, .35, .045), (0.70, 0, 0, .045)]
    blouse = mesh_obj('blouse', lathe(rows, 44), M['samfu'], olc=INK['samfu'])
    bv = BVHTree.FromObject(blouse, bpy.context.evaluated_depsgraph_get())
    def on_blouse(x, z, off=0.006):
        loc, nrm, _, _ = bv.ray_cast(Vector((x, 3, z)), Vector((0, -1, 0)))
        return (loc + nrm * off) if loc else Vector((x, 0.3, z))   # blouse object sits at origin so local = world
    mesh_obj('hem', tube(circle((0, .045, .632), (0, 0, 1), 1, 44, squash=(.505, .445)), 0.015, 6, closed=True), M['pipe'], ol=0.004, olc=INK['pipe'])
    coll = [(1.335, .255, .225, .035), (1.37, .24, .21, .035), (1.418, .228, .198, .035), (1.418, .205, .178, .035), (1.36, .2, .17, .035)]
    mesh_obj('collar', lathe(coll, 32), M['teal'], ol=0.005, olc=INK['samfu'])
    mesh_obj('collar_pipe', tube(circle((0, .035, 1.42), (0, 0, 1), 1, 32, squash=(.228, .198)), 0.011, 6, closed=True), M['pipe'], ol=0.003, olc=INK['pipe'])
    # placket piping + frog buttons, running to her right side (viewer side of the 3/4 shot)
    pl = catmull([(0.0, 1.33), (0.10, 1.305), (0.23, 1.20), (0.30, 1.05)], 6)
    mesh_obj('placket', tube([on_blouse(x, z) for x, z in pl], 0.008, 6), M['pipe'], ol=0.003, olc=INK['pipe'], shadow=False)
    for i in (2, 8, 14):
        p = on_blouse(pl[i][0], pl[i][1], 0.012)
        mesh_obj('frog', ellipsoid(p, (0.024,) * 3, 10, 6), M['pipe'], ol=0.004, olc=INK['pipe'], shadow=False)
        mesh_obj('frogbar', tube([on_blouse(pl[i][0] + dx, pl[i][1] - 0.012 * (dx / 0.05), 0.008) for dx in (-0.055, -0.02, 0.02, 0.055)], 0.007, 6), M['pipe'], ol=0.003, olc=INK['pipe'], shadow=False)
    for sg in (1, -1):
        S_, E_, W_ = Vector((sg * 0.40, 0.02, 1.27)), Vector((sg * 0.535, 0.10, 1.04)), Vector((sg * 0.415, 0.41, 0.99))
        palm = Vector((sg * WX, 0.485, RZ + 0.052))
        ap = catmull([S_, E_, W_, palm], 6); ar = [x[0] for x in catmull([(0.09,), (0.08,), (0.06,), (0.052,)], 6)]
        mesh_obj('arm', tube(ap, ar, 12), M['skin'], olc=INK['skin'])
        sp = catmull([Vector((sg * 0.33, 0.01, 1.30)), S_.lerp(E_, 0.3), S_.lerp(E_, 0.78)], 4)
        sr = [x[0] for x in catmull([(0.125,), (0.14,), (0.145,)], 4)]
        sv, sf, su = tube(sp, sr, 16, cap1='flat')
        su = [tuple((u / 2.8 + 0.37, v / 1.4 + 0.25) for u, v in f) for f in su]
        mesh_obj('sleeve', (sv, sf, su), M['samfu'], olc=INK['samfu'])
        mesh_obj('cuff', tube(circle(sp[-1], sp[-1] - sp[-2], 0.146, 20), 0.013, 6, closed=True), M['pipe'], ol=0.004, olc=INK['pipe'])
        # hand: palm on the rail, four fingers curled over the outside, thumb round the inside
        parts = [ellipsoid(palm + Vector((0, 0, -0.004)), (0.072, 0.088, 0.044), 14, 8)]
        for kf in range(4):
            y = 0.428 + 0.039 * kf; fr = 0.0235 - 0.002 * (kf == 3)
            pts = [(sg * WX + sg * 0.053 * math.cos(a), y, RZ + 0.053 * math.sin(a)) for a in np.linspace(math.radians(105), math.radians(-115), 9)]
            parts.append(tube(pts, fr, 8)[:2])
        pts = [(sg * WX + sg * 0.055 * math.cos(a), 0.392, RZ + 0.055 * math.sin(a)) for a in np.linspace(math.radians(70), math.radians(245), 8)]
        parts.append(tube(pts, 0.026, 8)[:2])
        mesh_obj('hand', join(parts), M['skin'], ol=0.006, olc=INK['skin'])
        if sg == -1:   # jade bangle on her left wrist
            c = E_.lerp(W_, 0.84)
            mesh_obj('bangle', tube(circle(c, W_ - E_, 0.078, 24), 0.019, 8, closed=True), M['jade'], ol=0.004, olc=INK['jade'])
        # legs, feet, slippers
        lp = catmull([(sg * 0.18, 0.03, 0.72), (sg * 0.205, 0.03, 0.42), (sg * 0.215, 0.04, 0.165)], 4)
        lr = [x[0] for x in catmull([(0.18,), (0.15,), (0.118,)], 4)]
        mesh_obj('leg', tube(lp, lr, 16, cap1='flat'), M['slacks'], olc=INK['slacks'])
        fc, frad = Vector((sg * 0.215, 0.135, 0.082)), (0.085, 0.165, 0.05)
        mesh_obj('foot', join([ellipsoid(fc, frad, 14, 8), tube([(sg * 0.215, 0.045, 0.25), (sg * 0.215, 0.05, 0.07)], 0.062, 10)[:2]]), M['skin'], ol=0.006, olc=INK['skin'])
        sole = [(0, 0, 0), (0, .07, .14), (0.005, .094, .176), (0.014, .098, .182), (0.03, .098, .182), (0.039, .094, .176), (0.044, .07, .14), (0.044, 0, 0)]
        mesh_obj('sole', lathe([(z, rx * 1.04, ry * 1.06, 0.145) for z, rx, ry in sole], 24, xc=sg * 0.215), M['red'], ol=0.006, olc=INK['red'])
        def on_foot(x, y):
            q = 1 - ((x - fc.x) / frad[0]) ** 2 - ((y - fc.y) / frad[1]) ** 2
            return Vector((x, y, (fc.z + frad[2] * math.sqrt(q) + 0.012) if q > 0.02 else 0.05))
        post = (fc.x - sg * 0.012, 0.255)
        for side in (1, -1):
            end = (fc.x + side * 0.092, 0.10)
            pts = [on_foot(post[0] + (end[0] - post[0]) * t, post[1] + (end[1] - post[1]) * t) for t in np.linspace(0, 1, 9)]
            mesh_obj('strap', tube(pts, 0.010, 8), M['red'], ol=0.004, olc=INK['red'])

def build_walker():
    for sg in (1, -1):
        x = sg * WX
        path = rounded([(x, WY0 - 0.10, 0.03), (x, WY0, RZ), (x, WY1, RZ), (x, WY1 + 0.08, 0.03)], 0.075, 6)
        mesh_obj('frame', tube(path, 0.02, 10), M['metal'], ol=0.006, olc=INK['metal'])
        mesh_obj('grip', tube([(x, WY0 + 0.035, RZ), (x, WY0 + 0.285, RZ)], 0.029, 10), M['rubber'], ol=0.005, olc='#16142a')
        back = lambda z: (x, WY0 - 0.10 * (RZ - z) / (RZ - 0.03), z); front = lambda z: (x, WY1 + 0.08 * (RZ - z) / (RZ - 0.03), z)
        mesh_obj('brace', tube([back(0.36), front(0.36)], 0.016, 8), M['metal'], ol=0.005, olc=INK['metal'])
        for leg in (back, front):
            mesh_obj('tip', tube([leg(0.0), leg(0.085)], [0.032, 0.027], 10), M['rubber'], ol=0.005, olc='#16142a')
    fy = lambda z: WY1 + 0.08 * (RZ - z) / (RZ - 0.03)
    for z in (0.80, 0.42):
        mesh_obj('bar', tube([(-WX, fy(z), z), (WX, fy(z), z)], 0.017, 8), M['metal'], ol=0.005, olc=INK['metal'])
    by = fy(0.80) + 0.135
    rows = [(0.50, 0, 0), (0.50, .215, .078), (0.506, .238, .098), (0.522, .244, .104), (0.79, .272, .122), (0.802, .28, .13), (0.806, .272, .122),
            (0.795, .26, .11), (0.535, .23, .09), (0.53, 0, 0)]
    mesh_obj('basket', lathe([(z, rx, ry, by) for z, rx, ry in rows], 32, expo=4.5), M['red'], ol=0.007, olc=INK['red'])
    # groceries: leeks and oranges, kept below chest height
    for i, (x, tilt) in enumerate(((-0.13, -0.10), (-0.07, -0.03))):
        b = Vector((x, by, 0.58)); t = Vector((x + tilt, by + 0.02, 0.98))
        mesh_obj('leek', tube([b, b.lerp(t, 0.6)], 0.024, 8), M['leekw'], ol=0.005, olc=INK['veg'])
        for k in (-1, 0, 1):
            tip = t + Vector((k * 0.06 + tilt, k * 0.02, 0.10 - abs(k) * 0.05))
            mesh_obj('leaf', tube(catmull([b.lerp(t, 0.55), t, tip], 4), [x_[0] for x_ in catmull([(0.026,), (0.024,), (0.008,)], 4)], 8), M['leekg'], ol=0.005, olc=INK['veg'])
    for x, y, z, r in ((0.10, by - 0.02, 0.80, 0.068), (0.185, by + 0.03, 0.79, 0.062), (0.03, by + 0.04, 0.775, 0.06)):
        mesh_obj('orange', ellipsoid((x, y, z), (r, r, r * 0.93), 12, 8), M['orange'], ol=0.005, olc='#7a2a12')

head, face = build_head(); build_hair(); build_glasses(); build_body(); build_walker()
print('TRIS', TRIS)
assert 15000 < TRIS < 42000, TRIS   # ponytail: budget check is the only self-test this style frame needs

# ---------- stage ----------
def stage():
    SC.render.engine = 'BLENDER_EEVEE'; SC.eevee.taa_render_samples = 64
    SC.view_settings.view_transform = 'AgX'; SC.view_settings.look = 'AgX - Punchy'; SC.view_settings.exposure = 0.75
    SC.render.image_settings.file_format = 'PNG'; SC.render.film_transparent = False
    w = bpy.data.worlds.new('World'); SC.world = w; w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    bg = N['Background']; bg.inputs[0].default_value = (0.55, 0.62, 0.72, 1); bg.inputs[1].default_value = 0.35
    cam_bg = N.new('ShaderNodeBackground'); cam_bg.inputs[0].default_value = C('#bcd3ea'); cam_bg.inputs[1].default_value = 0.6
    lp = N.new('ShaderNodeLightPath'); mx = N.new('ShaderNodeMixShader')
    L.new(lp.outputs['Is Camera Ray'], mx.inputs[0]); L.new(bg.outputs[0], mx.inputs[1]); L.new(cam_bg.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], N['World Output'].inputs['Surface'])
    for name, d, e, col in (('key', KEY_DIR, KEY_E, (1.0, 0.86, 0.68)), ('fill', FILL_DIR, 0.25, (0.7, 0.8, 1.0)), ('rim', RIM_DIR, 2.2, (1.0, 0.9, 0.75))):
        ld = bpy.data.lights.new(name, 'SUN'); ld.energy = e; ld.color = col; ld.angle = math.radians(1.5)
        o = bpy.data.objects.new(name, ld); SC.collection.objects.link(o); o.location = d * 8
        o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    me = bpy.data.meshes.new('floor'); me.from_pydata([(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)], [], [(0, 1, 2, 3)])
    fl = bpy.data.objects.new('floor', me); SC.collection.objects.link(fl)
    fm = bpy.data.materials.new('floor'); fm.use_nodes = True
    b = fm.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0.22, 0.215, 0.21, 1); b.inputs['Roughness'].default_value = 0.9
    me.materials.append(fm)
    cd = bpy.data.cameras.new('cam'); cd.clip_start = 0.1; cd.clip_end = 200
    cam = bpy.data.objects.new('cam', cd); SC.collection.objects.link(cam); SC.camera = cam
    return cam

CAM = stage()
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=HERE + '/ahma_toon.blend')

def shoot(path, w, h, az_deg, target, vis, lens=70, cam_z=None, expr='smile'):
    """az 0 = front (+Y). vis = metres visible along the larger image side."""
    SC.render.resolution_x = w; SC.render.resolution_y = h; CAM.data.lens = lens
    dist = vis * lens / 36.0; a = math.radians(az_deg); t = Vector(target)
    CAM.location = (t.x + math.sin(a) * dist, t.y + math.cos(a) * dist, cam_z if cam_z is not None else t.z)
    CAM.rotation_euler = (t - CAM.location).to_track_quat('-Z', 'Y').to_euler()
    for ob in (head, face):
        for kb in ob.data.shape_keys.key_blocks[1:]: kb.value = 1.0 if kb.name == expr else 0.0
    SC.render.filepath = path; bpy.ops.render.render(write_still=True)

def stitch(tiles, out, width=1600):
    arrs = []
    for p in tiles:
        im = bpy.data.images.load(p); w, h = im.size
        a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); arrs.append(a.reshape(h, w, 4)); bpy.data.images.remove(im); os.remove(p)
    a = np.concatenate(arrs, axis=1)[:, :width]
    im = bpy.data.images.new('stitch', a.shape[1], a.shape[0], alpha=True); im.pixels.foreach_set(a.ravel())
    im.filepath_raw = out; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)

TMP = os.environ.get('TMPD', '/tmp/lunchliao-scratch')
if 'hero' in SHOTS: shoot(OUT + '/hero.png', 1600, 1800, 30, (0, 0.28, 1.08), 2.75, 70, cam_z=1.25)
if 'face' in SHOTS: shoot(OUT + '/face.png', 1600, 1600, 28, (0, 0.12, 1.68), 1.22, 85, cam_z=1.70)
if 'expr' in SHOTS:
    tiles = []
    for k in EXPR:
        tiles.append(f'{TMP}/toon_expr_{k}.png'); shoot(tiles[-1], 400, 440, 0, (0, 0.1, 1.70), 1.27, 85, expr=k)
    stitch(tiles, OUT + '/expressions.png')
if 'turn' in SHOTS:
    tiles = []
    for i, az in enumerate((0, 90, 180)):
        tiles.append(f'{TMP}/toon_turn_{i}.png'); shoot(tiles[-1], 534, 900, az, (0, 0.30, 1.08), 2.75, 70)
    stitch(tiles, OUT + '/turn.png')
if 'dbg' in SHOTS:
    shoot(TMP + '/toon_dbg_feet.png', 900, 700, 30, (0, 0.2, 0.2), 1.3, 70, cam_z=0.6)
    shoot(TMP + '/toon_dbg_hand.png', 900, 700, 30, (0.1, 0.45, 0.95), 1.1, 70, cam_z=1.3)
print('DONE TRIS', TRIS)
