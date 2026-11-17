"""Ah Ma, game-ready, style `toy`. Run: blender -b -P ahma.py -- [build] [export] [verify] [shots]
build: geometry + rig + shape keys + clips -> _tmp_ahma/ahma_rig.blend. export: glb. shots: beauty/turnaround/expressions/anim_sheet.
Axes: Z up, hero faces +Y (exporter makes it Y up, facing -Z)."""
import bpy, sys, os, math, random
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'blender', 'heroes'))
import hero_lib as H
OUT = os.path.join(ROOT, 'shots', 'heroes_toy', 'ahma')
TMP = os.path.join(HERE, '_tmp_ahma')
OUT_GLB = os.path.join(ROOT, 'assets', 'heroes', 'ahma.glb')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build']
QUICK = 'quick' in ARGS
os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
HERO = []          # every object that belongs to the figure
V = Vector
Z = V((0, 0, 1))

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
    skin=mat('skin', '#F7C29A', .42, sss=.12),
    nose=mat('nose', '#F3AE88', .42, sss=.12),
    blush=mat('blush', '#F2909A', .5),
    line=mat('line', '#DB9E78', .45),
    hair=mat('hair', '#ECE7F2', .5, coat=.08),
    brow=mat('brow', '#76707E', .45),
    eye=mat('eye', '#1A1214', .08, coat=1.0),
    white=mat('white', '#FFFDF8', .25),
    mouth=mat('mouth', '#7B2331', .45),
    tongue=mat('tongue', '#F2818C', .35),
    lip=mat('lip', '#B8404E', .4),
    collar=mat('collar', '#F6EAD6', .5),
    teeth=mat('teeth', '#FFFAF0', .25),
    rim=mat('rim', '#6A3420', .15, coat=1.0),
    gold=mat('gold', '#F0B94A', .22, metal=1.0),
    jade=mat('jade', '#3DB57C', .12, coat=1.0, sss=.3),
    pipe=mat('piping', '#D63C8C', .35),
    navy=mat('slacks', '#252C4E', .5),
    red=mat('red', '#DB2A2E', .3, coat=.4),
    redd=mat('red_dark', '#8E1418', .4),
    alu=mat('aluminium', '#DADDE2', .22, metal=1.0),
    grip=mat('grip', '#4B4B52', .75),
    rubber=mat('rubber', '#3A3A40', .6),
    tissue=mat('tissue', '#FFFFFF', .45),
    tgreen=mat('tissue_green', '#2E9E6B', .45),
)

def floral_image(n=1024):
    """Tileable floral print: 5-petal blossoms on cream. Drawn with distance fields, so edges are clean."""
    rnd = random.Random(7)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / n
    img = np.empty((n, n, 3), np.float32); img[:] = (0.965, 0.915, 0.83)
    def blob(cx, cy, r, col):
        dx = np.abs(xx - cx); dx = np.minimum(dx, 1 - dx); dy = np.abs(yy - cy); dy = np.minimum(dy, 1 - dy)
        a = np.clip((r - np.sqrt(dx * dx + dy * dy)) * n / 1.5 + .5, 0, 1)[..., None]
        img[:] = img * (1 - a) + np.array(col, np.float32) * a
    cols = [((0.92, 0.36, 0.52), (0.99, 0.84, 0.36)), ((0.16, 0.62, 0.64), (0.99, 0.93, 0.80)), ((0.97, 0.60, 0.68), (0.86, 0.24, 0.42))]
    g = 4; k = 0
    for iy in range(g):
        for ix in range(g):
            cx = (ix + .5 + (.5 if iy % 2 else 0) + rnd.uniform(-.12, .12)) / g; cy = (iy + .5 + rnd.uniform(-.12, .12)) / g
            pet, mid = cols[(ix + iy * 2 + k) % 3]; r = rnd.uniform(.034, .042); a0 = rnd.uniform(0, 6.28)
            for l in range(2):   # two leaves
                la = a0 + .6 + l * 3.3; blob(cx + math.cos(la) * r * 2.25, cy + math.sin(la) * r * 2.25, r * .5, (0.36, 0.66, 0.42))
            for p in range(5):
                a = a0 + p * 6.2832 / 5; blob(cx + math.cos(a) * r * 1.05, cy + math.sin(a) * r * 1.05, r * .78, pet)
            blob(cx, cy, r * .55, mid)
            # tiny bud between blossoms
            bx = cx + .5 / g + rnd.uniform(-.02, .02); by = cy + .5 / g + rnd.uniform(-.02, .02)
            blob(bx, by, .013, cols[(ix + iy + 1) % 3][0])
    im = bpy.data.images.new('floral', n, n, alpha=False)
    rgba = np.concatenate([img, np.ones((n, n, 1), np.float32)], axis=2)
    im.pixels.foreach_set(rgba.ravel()); im.pack(); return im

def floral_mat():
    m = mat('floral', '#F6EAD6', .5)
    nt = m.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = floral_image()
    nt.links.new(t.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color']); return m
M['floral'] = floral_mat()

def lens_mat():
    m = bpy.data.materials.new('lens'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (.16, .17, .2, 1); b.inputs['Roughness'].default_value = .03
    b.inputs['Alpha'].default_value = .14; m.surface_render_method = 'BLENDED'
    return m
M['lens'] = lens_mat()

# ---------------------------------------------------------------- mesh helpers
def mk(name, verts, faces, m, uvs=None, mat_idx=None):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    for mm in (m if isinstance(m, (list, tuple)) else [m]): me.materials.append(mm)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    if mat_idx: me.polygons.foreach_set('material_index', mat_idx)
    if uvs:
        uv = me.uv_layers.new(name='UVMap')
        flat = [c for f in uvs for co in f for c in co]; uv.data.foreach_set('uv', flat)
    ob = bpy.data.objects.new(name, me); SC.collection.objects.link(ob); HERO.append(ob); return ob

def reg(ob):
    HERO.append(ob); return ob

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

def sweep(name, pts, radii, m, seg=14, uvrep=None, round_caps=True, lip=None, lipm=None):
    """Tube along pts with per-point radius. Caps are small domes. lip=(depth, r) folds the far end inward (sleeve opening)."""
    pts = [V(p) for p in pts]; n = len(pts)
    if isinstance(radii, (int, float)): radii = [radii] * n
    T = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    N = frame_from(T[0])[0]; rings = []
    def ring(c, Nn, Bn, r): return [c + (Nn * math.cos(2 * math.pi * i / seg) + Bn * math.sin(2 * math.pi * i / seg)) * r for i in range(seg)]
    def dome(c, t, Nn, Bn, r, sign):
        return [ring(c + t * (sign * r * math.sin(a)), Nn, Bn, r * math.cos(a)) for a in (math.radians(35), math.radians(65), math.radians(89))]
    N0 = N
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
    if lipm is not None:
        R = len(rings); mi = [1 if j >= R - 3 else 0 for j in range(R - 1) for i in range(seg)] + [0, 1]
        return mk(name, vs, fs, [m, lipm], uvs, mat_idx=mi)
    return mk(name, vs, fs, m, uvs)

def rbox(name, c, size, m, bevel=.01, rot=None, open_top=False, taper=1.0, solid=0.0, bseg=4):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); ob = bpy.context.object; ob.name = name
    for v in ob.data.vertices:
        k = taper if v.co.z < 0 else 1.0
        v.co = V((v.co.x * size[0] * k, v.co.y * size[1] * k, v.co.z * size[2]))
    if open_top:
        import bmesh
        bm = bmesh.new(); bm.from_mesh(ob.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > .9], context='FACES'); bm.to_mesh(ob.data); bm.free()
    b = ob.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = bseg; b.limit_method = 'ANGLE'; H.apply_mod(ob, b)
    if solid:
        s = ob.modifiers.new('sol', 'SOLIDIFY'); s.thickness = solid; s.offset = 0; H.apply_mod(ob, s)
    H.shade_smooth(ob)
    w = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); w.keep_sharp = True; H.apply_mod(ob, w)
    ob.data.materials.append(m)
    ob.matrix_world = Matrix.Translation(V(c)) @ (rot.to_4x4() if rot is not None else Matrix.Identity(4))
    return reg(ob)

# ---------------------------------------------------------------- proportions
BY = -0.05                                # body centre in Y
HC = V((0, -0.01, 1.66)); HR = V((0.58, 0.55, 0.52))    # head centre and radii

def surf(fx, fz, off=0.0):
    """Face coordinates (x right of centre, z above centre) -> point on the front of the head, normal, tangent, up."""
    k = max(1e-4, 1 - (fx / HR.x) ** 2 - (fz / HR.z) ** 2); y = HR.y * math.sqrt(k)
    n = V((fx / HR.x ** 2, y / HR.y ** 2, fz / HR.z ** 2)).normalized()
    t = n.cross(Z).normalized(); u = t.cross(n).normalized()
    return HC + V((fx, y, fz)) + n * off, n, t, u

# ---------------------------------------------------------------- body
def build_body():
    cz = [.455, .50, .60, .72, .84, .93, 1.00, 1.04, 1.06]; cr = [.455, .475, .47, .435, .385, .33, .26, .185, .15]
    zs = np.linspace(cz[0], cz[-1], 26); rs = np.interp(zs, cz, cr)
    for _ in range(3): rs[1:-1] = (rs[:-2] + 2 * rs[1:-1] + rs[2:]) / 4
    global BR
    BR = lambda z: float(np.interp(z, zs, rs))
    rows = [(.36, .50), (.43, .462)] + list(zip(rs, zs)); seg = 48; vs = []; fs = []; uvs = []
    for r, z in rows:
        for i in range(seg):
            a = 2 * math.pi * i / seg; vs.append(V((r * math.cos(a), BY + .88 * r * math.sin(a), z)))
    ntile = lambda z: 4     # same whole tile count on every ring: no seam and no shear smear where rings change count
    va = [0.0]
    for j in range(1, len(rows)): va.append(va[-1] + math.hypot(rows[j][0] - rows[j - 1][0], rows[j][1] - rows[j - 1][1]) * 1.35)
    for j in range(len(rows) - 1):
        for i in range(seg):
            fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
            n0 = ntile(rows[j][1]); n1 = ntile(rows[j + 1][1])
            uvs.append([(i / seg * n0, va[j]), ((i + 1) / seg * n0, va[j]), ((i + 1) / seg * n1, va[j + 1]), (i / seg * n1, va[j + 1])])
    fs.append(tuple(range((len(rows) - 1) * seg, len(rows) * seg))); uvs.append([(0, 0)] * seg)
    mk('blouse', vs, fs, M['floral'], uvs)
    tor('hem_piping', (0, BY, .458), Z, .458, .014, M['pipe'], seg=44, rseg=6, squash=(1, .88, 1))
    # neck and rolled collar: a short visible neck, then a piped stand collar so the head never sits on the shoulders
    # mandarin stand collar: a closed band with real thickness, piped on the top edge. A short neck shows above it
    prof = [(.205, .995), (.19, 1.04), (.172, 1.09), (.163, 1.118), (.152, 1.13), (.141, 1.118), (.146, 1.06), (.16, .995)]
    seg = 40; vs = []; fs = []
    for r, z in prof:
        for i in range(seg):
            a = 2 * math.pi * i / seg; vs.append(V((r * math.cos(a), BY + .02 + .9 * r * math.sin(a), z)))
    P = len(prof)
    for j in range(P):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, ((j + 1) % P) * seg + (i + 1) % seg, ((j + 1) % P) * seg + i))
    mk('collar', vs, fs, M['collar'])
    tor('collar_piping', (0, BY + .02, 1.124), Z, .153, .011, M['pipe'], seg=32, rseg=6, squash=(1, .9, 1))
    sweep('neck', [(0, BY + .02, 1.0), (0, BY + .02, 1.3)], [.132, .132], M['skin'], seg=24, round_caps=False)
    # samfu da-jin placket: piped edge from the collar across the chest to the wearer's right armpit, then down the side seam
    bs = lambda a, z, off: V(((BR(z) + off) * math.cos(math.radians(a)), BY + .88 * (BR(z) + off) * math.sin(math.radians(a)), z))
    path = [(92, 1.0), (80, .985), (62, .955), (42, .915), (25, .875), (13, .82), (7, .74), (5, .62), (5, .47)]
    pts = []
    for (a0, z0), (a1, z1) in zip(path[:-1], path[1:]):
        for k in range(4):
            t = k / 4; pts.append(bs(a0 + (a1 - a0) * t, z0 + (z1 - z0) * t, .007))
    pts.append(bs(*path[-1], .007))
    sweep('placket', pts, .0125, M['pipe'], seg=6)
    for a, z in ((84, .99), (50, .932), (10, .79), (5, .66), (5, .55)):     # frog buttons across the placket
        p = bs(a, z, .012); nrm = V((p.x, (p.y - BY) / .88, 0)).normalized()
        q = bs(a - 1, z - .01, .012); tng = (q - p).normalized(); d = tng.cross(nrm).normalized()
        sweep('frog_bar', [p - d * .05 - nrm * .006, p + nrm * .004, p + d * .05 - nrm * .006], .011, M['pipe'], seg=6)
        ell('frog_knot', p + nrm * .008, (.022, .022, .022), M['pipe'], seg=10)
    # hips and legs (slacks)
    ell('hips', (0, BY, .50), (.37, .32, .13), M['navy'], seg=16)
    for s in (-1, 1):
        sweep('leg', [(s * .19, BY, .56), (s * .195, BY, .36), (s * .2, BY, .15)], [.19, .18, .17], M['navy'], seg=20, lip=(.012, .12), lipm=M['rubber'])
        sweep('cuff', [(s * .2, BY, .158), (s * .2, BY, .15)], .174, M['navy'], seg=20, round_caps=False)
        ell('foot', (s * .2, BY + .09, .088), (.1, .175, .058), M['skin'], seg=16)
        ell('sole', (s * .2, BY + .085, .034), (.125, .215, .034), M['red'], seg=16)
        post = V((s * .2, BY + .21, .10))
        for o in (-1, 1):
            sweep('strap', bez(post, (s * .2 + o * .085, BY + .15, .185), (s * .2 + o * .112, BY + .02, .05)), .017, M['red'], seg=6)
        ell('strap_post', post, (.02, .02, .025), M['red'], seg=12)

ARM = {}
def build_arms():
    for s in (-1, 1):
        S = V((s * .30, BY + .05, .955)); E = V((s * .56, BY + .13, .80)); Wr = V((s * .455, .365, .945))
        path = bez(S, E, E.lerp(Wr, .25), 9); ARM[s] = (S, path[-1].copy(), Wr)
        sweep('sleeve', path, [.125, .135, .14, .138, .132, .122, .112, .103, .097], M['floral'], seg=20, uvrep=(1, 1.3), lip=(.004, .088), lipm=M['collar'])
        tor('cuff_piping', path[-1], path[-1] - path[-2], .096, .0125, M['pipe'], seg=20, rseg=6)
        sweep('forearm', [path[-2], Wr], [.082, .064], M['skin'], seg=16)
        if s == 1: tor('bangle', path[-2].lerp(Wr, .72), Wr - path[-2], .078, .022, M['jade'], seg=24, rseg=6)
        # fist wrapped over the walker grip (grip axis runs along Y at x=s*.455, z=.90)
        gx = s * .455; so = H.Soup('hand')
        so.ellipsoid((gx, .46, .935), (.075, .095, .048))
        so.capsule(Wr, (gx, .43, .94), .058, .06)
        for k, y in enumerate((.395, .44, .485, .527)):
            r = .0235 - .002 * (k == 3)
            for a, b in zip([(gx + s * .02, y, .958), (gx + s * .066, y, .928), (gx + s * .07, y, .885)], [(gx + s * .066, y, .928), (gx + s * .07, y, .885), (gx + s * .038, y, .856)]):
                so.capsule(a, b, r, r, seg=12)
        so.capsule((gx - s * .045, .405, .935), (gx - s * .068, .46, .895), .027, .024, seg=12)
        so.capsule((gx - s * .068, .46, .895), (gx - s * .04, .485, .862), .024, .022, seg=12)
        hand, _ = so.remesh(voxel=.0065, smooth=6, smooth_factor=.6, target_tris=650)
        H.set_material(hand, M['skin']); reg(hand)

# ---------------------------------------------------------------- head
def build_head():
    head = ell('head', HC, HR, M['skin'], seg=48)
    p, n, t, u = surf(0, HOLE_C)
    cut = ell('mouth_cut', p, (HOLE_R[0] * .97, .3, HOLE_R[1] * .97), M['skin'], seg=32); HERO.remove(cut)
    H.boolean_cut(head, cut); H.shade_smooth(head)
    # the boolean leaves sliver triangles round the hole: give every vertex the exact ellipsoid normal so shading stays smooth
    me = head.data; me.normals_split_custom_set_from_vertices([V(((v.co.x - HC.x) / HR.x ** 2, (v.co.y - HC.y) / HR.y ** 2, (v.co.z - HC.z) / HR.z ** 2)).normalized() for v in me.vertices])
    # perm: a cloud of curls unioned into one smooth vinyl shell
    rnd = random.Random(3); so = H.Soup('hair'); n = 150
    def thr(az):   # hairline elevation (deg) by azimuth from front (deg)
        return float(np.interp(az, [0, 35, 65, 95, 180], [61, 54, 35, 10, -34]))
    for i in range(n):
        z = 1 - 2 * (i + .5) / n; a = i * 2.39996; r = math.sqrt(1 - z * z); d = V((r * math.cos(a), r * math.sin(a), z))
        az = math.degrees(math.atan2(abs(d.x), d.y)); el = math.degrees(math.asin(d.z))
        if el < thr(az): continue
        rim = el - thr(az) < 14
        rad = rnd.uniform(.125, .15) if rim else rnd.uniform(.14, .175)
        so.sphere(HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z)) * (.955 if rim else .93), rad, seg=20)
    hair, _ = so.remesh(voxel=.012, smooth=5, smooth_factor=.55, target_tris=2300)
    H.set_material(hair, M['hair']); reg(hair)
    for s in (-1, 1):
        ell('ear', HC + V((s * .57, -.03, -.05)), (.045, .085, .105), M['skin'], seg=14)
        ell('stud', HC + V((s * .612, -.01, -.115)), (.026, .026, .026), M['gold'], seg=10)
    p, n, t, u = surf(0, -.115); ell('nose', p + n * .004, (.052, .042, .04), M['nose'], seg=16)

    # glasses
    EX, EZ = .215, -.01; RR = .15
    cs = {}
    for s in (-1, 1):
        p, n, t, u = surf(s * EX, EZ); ng = V((s * .13, 1, -.04)).normalized(); c = p + n * .075
        tg = ng.cross(Z).normalized(); cs[s] = (c, tg, ng)
        tor('rim', c, ng, RR, .017, M['rim'], seg=32, rseg=6)
        # lens disc
        vs = [c] + [c + (tg * math.cos(a) + tg.cross(ng) * math.sin(a)) * RR for a in [2 * math.pi * i / 40 for i in range(40)]]
        mk('lens', vs, [(0, 1 + i, 1 + (i + 1) % 40) for i in range(40)], M['lens']).visible_shadow = False
        outer = c + tg * (s * (RR + .005))
        ell('hinge', outer, (.022, .02, .022), M['gold'], seg=12)
        sweep('temple', fillet([outer, HC + V((s * .575, .30, .06)), HC + V((s * .60, .0, .055))], .12), .012, M['rim'], seg=8)
    a = cs[-1][0] + cs[-1][1] * RR; b = cs[1][0] - cs[1][1] * RR
    sweep('bridge', bez(a + Z * .03, (a + b) * .5 + V((0, .03, .075)), b + Z * .03, 8), .013, M['gold'], seg=8)

# ---------------------------------------------------------------- face (one mesh, six shape keys)
NEUT = dict(bz=.185, tilt=-.004, arch=.02, eye='bead', es=(1, 1), cut=None, hl=.026, wr=0, w=.17, curve=.014, up=0, dn=0, teeth=0, tongue=0, cz=-.265, arcu=False)
def ex(**k):
    d = dict(NEUT); d.update(k); return d
EXPR = {
    'blink': ex(eye='arc', arcu=True, bz=.172),
    'mouth_open': ex(w=.19, curve=.01, up=.006, dn=.058, teeth=.028, tongue=.04, cz=-.262),
    'smile': ex(bz=.19, tilt=-.006, arch=.022, w=.21, curve=.04, cz=-.268),
    'angry': ex(bz=.205, tilt=.1, arch=-.022, es=(1.06, .8), cut=(.014, .6), hl=.0, wr=-.05, w=.25, curve=-.1, up=.02, dn=.048, teeth=.036, tongue=0, cz=-.268),
    'grin': ex(bz=.205, tilt=-.012, arch=.034, eye='arc', hl=.026, wr=.022, w=.33, curve=.062, up=.004, dn=.112, teeth=.04, tongue=.05, cz=-.28),
    'ult': ex(bz=.215, tilt=.09, arch=-.006, es=(1.12, 1.12), hl=.03, wr=-.03, w=.3, curve=-.004, up=.055, dn=.128, teeth=.042, tongue=.08, cz=-.27),
}
FM = ['brow', 'eye', 'white', 'line', 'mouth', 'teeth', 'tongue', 'blush', 'lip', 'skin']
EXe, EZe = .215, -.01
HOLE_C, HOLE_R = -.285, (.215, .14)          # face-plane ellipse cut out of the head, covered again by the skin ring of the face mesh
KM = 28                                       # points around the mouth outline

def face_geo(e):
    vs = []; fs = []; mi = []
    def add(v, f, m):
        o = len(vs); vs.extend(v); fs.extend([tuple(i + o for i in ff) for ff in f]); mi.extend([FM.index(m)] * len(f))
    def hide(v): return [HC.copy() for _ in v]
    def stroke(pts, rw, rn, off, m, show=True, seg=6):
        P = [surf(x, z, off) for x, z in pts]; n = len(P); v = []
        for i in range(n):
            p, nn, _, _ = P[i]; tan = (P[min(i + 1, n - 1)][0] - P[max(i - 1, 0)][0]).normalized(); side = nn.cross(tan).normalized()
            f = math.sin(math.pi * i / (n - 1)) ** .45 if 0 < i < n - 1 else 0.0
            v += [p + (side * math.cos(a) * rw + nn * math.sin(a) * rn) * f for a in [2 * math.pi * k / seg for k in range(seg)]]
        f = [(i * seg + k, i * seg + (k + 1) % seg, (i + 1) * seg + (k + 1) % seg, (i + 1) * seg + k) for i in range(n - 1) for k in range(seg)]
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
        stroke([(s * (EXe + q * .095), e['bz'] + q * e['tilt'] + e['arch'] * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .046, .026, .004, 'brow')
        bead = e['eye'] == 'bead'; a, c = .056 * e['es'][0], .07 * e['es'][1]
        blob(s * EXe, EZe, (a, .036, c), 0, 'eye', show=bead, seg=16, cut=(e['cut'][0], e['cut'][1] * s) if e['cut'] else None)
        blob(s * EXe, EZe, (.019, .012, .019), .028, 'white', show=bead, seg=12, d=(.02, e['hl']))
        blob(s * EXe, EZe, (.008, .006, .008), .026, 'white', show=bead, seg=8, d=(-.022, -.03))
        if e['arcu']: pts = [(s * EXe + .066 * math.cos(ph), EZe + .022 - .05 * math.sin(ph)) for ph in [math.radians(168 - 156 * i / 11) for i in range(12)]]
        else: pts = [(s * EXe + .066 * math.cos(ph), EZe - .028 + .062 * math.sin(ph)) for ph in [math.radians(168 - 156 * i / 11) for i in range(12)]]
        stroke(pts, .0145, .011, .005, 'eye', show=not bead)
        # blush decal, conforms to the head
        v = [surf(s * .375, -.195, .0025)[0]]; f = []
        for j in range(1, 4):
            for i in range(20):
                ang = 2 * math.pi * i / 20; v.append(surf(s * .375 + .08 * j / 3 * math.cos(ang), -.195 + .058 * j / 3 * math.sin(ang), .0025 if j < 3 else .0)[0])
        ri = lambda j, i: 1 + (j - 1) * 20 + i % 20
        f += [(0, ri(1, i), ri(1, i + 1)) for i in range(20)]
        f += [(ri(j, i), ri(j + 1, i), ri(j + 1, i + 1), ri(j, i + 1)) for j in (1, 2) for i in range(20)]
        add(v, f, 'blush')
    for z0, hw0 in ((.262, .12), (.305, .09)):
        stroke([(q * hw0, z0 + e['wr'] + .012 * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .0075, .004, .001, 'line')
    # ---- mouth: lip ring, skin ring, recessed cavity, tongue and an upper tooth row, all real geometry
    w = e['w']; hw = w / 2
    env = lambda x: max(0.0, 1 - (x / hw) ** 2) ** .5
    zc = lambda x: e['cz'] + e['curve'] * (x / hw) ** 2
    half = lambda x: .0075 * min(1.0, env(x) * 2.5)
    upz = lambda x: zc(x) + e['up'] * env(x) + half(x)
    loz = lambda x: zc(x) - e['dn'] * env(x) - half(x)
    P = lambda x, z, off: surf(x, z, off)[0]
    edge = []; outd = []
    for k in range(KM):
        th = 2 * math.pi * k / KM; x = hw * math.cos(th); up_ = math.sin(th) >= 0
        z = upz(x) if up_ else loz(x); dz = 2 * e['curve'] * x / hw ** 2
        nrm = V((-dz, 1.0, 0)) if up_ else V((dz, -1.0, 0)); nrm = V((nrm.x, nrm.y, 0)).normalized()
        d = V((nrm.x + 2.0 * (x / hw) ** 6 * (1 if x > 0 else -1), nrm.y, 0)).normalized()     # (x, z) as (d.x, d.y)
        edge.append((x, z)); outd.append((d.x, d.y))
    def ring(dist, off): return [P(edge[k][0] + outd[k][0] * dist, edge[k][1] + outd[k][1] * dist, off) for k in range(KM)]
    def band(a, b, flip=False):
        v = a + b; f = []
        for k in range(KM):
            q = (k, (k + 1) % KM, KM + (k + 1) % KM, KM + k); f.append(tuple(reversed(q)) if flip else q)
        return v, f
    lw = .0105
    r0, r1, r2 = ring(0, -.006), ring(lw * .5, .010), ring(lw, .006)
    v, f = band(r0, r1); add(v, f, 'lip'); v, f = band(r1, r2); add(v, f, 'lip')
    # skin ring from the lip out to the hole edge (overlaps the head skin so there is no gap)
    NR = 4; rr = [[] for _ in range(NR + 1)]
    for k in range(KM):
        x2 = edge[k][0] + outd[k][0] * lw; z2 = edge[k][1] + outd[k][1] * lw
        ang = 2 * math.pi * k / KM; ox = HOLE_R[0] * 1.0 * math.cos(ang); oz = HOLE_C + HOLE_R[1] * 1.0 * math.sin(ang)
        for j in range(NR + 1):
            t = j / NR; rr[j].append(P(x2 + (ox - x2) * t, z2 + (oz - z2) * t, .006 - .0055 * t))
    for j in range(NR):
        v, f = band(rr[j], rr[j + 1]); add(v, f, 'skin')
    # cavity bowl
    zm = (upz(0) + loz(0)) * .5; openh = upz(0) - loz(0); D = min(.1, .035 + 1.2 * openh)
    rows = [r0]
    for t in (1 / 3, 2 / 3):
        rows.append([P(edge[k][0] * (1 - t * .94), edge[k][1] + (zm - edge[k][1]) * t * .94, -.006 - D * math.sin(t * math.pi / 2)) for k in range(KM)])
    bv = []; bf = []
    for r in rows: bv += r
    for j in range(len(rows) - 1):
        for k in range(KM): bf.append(tuple(reversed((j * KM + k, j * KM + (k + 1) % KM, (j + 1) * KM + (k + 1) % KM, (j + 1) * KM + k))))
    bv.append(P(0, zm, -.006 - D)); c = len(bv) - 1; lr = (len(rows) - 1) * KM
    for k in range(KM): bf.append((c, lr + (k + 1) % KM, lr + k))
    add(bv, bf, 'mouth')
    # tongue: a squashed ellipsoid resting on the cavity floor
    tg = e['tongue']; tt = .45
    tz = loz(0) + (zm - loz(0)) * tt; to = -.006 - D * math.sin(tt * math.pi / 2) + .012
    tr = (hw * .62, .017, max(.0004, tg * .55)) if tg else (.0004, .0004, .0004)
    sv, sf = sph_vf(14, 7); p, n, t_, u_ = surf(0, tz if tg else zm, to)
    add([p + t_ * (q.x * tr[0]) + u_ * (q.z * tr[2]) + n * (q.y * tr[1]) for q in sv], sf, 'tongue')
    # upper tooth row: six rounded blocks hanging from the upper lip
    nt = 6; th = e['teeth']; span = hw * .78; sp = 2 * span / (nt - 1)
    sq = lambda a: math.copysign(abs(a) ** .55, a)
    for j in range(nt):
        x = -span + j * sp; ztop = upz(x) + .003
        if th: hgt = th * (1 - .12 * (x / span) ** 2); rad = (sp * .5, .011, hgt * .5); zc_ = ztop - hgt * .5 + .002
        else: rad = (.0004, .0004, .0004); zc_ = ztop
        p, n, t_, u_ = surf(x, zc_, -.0035); sv, sf = sph_vf(8, 6)
        add([p + t_ * (sq(q.x) * rad[0]) + u_ * (sq(q.z) * rad[2]) + n * (sq(q.y) * rad[1]) for q in sv], sf, 'teeth')
    return vs, fs, mi

def build_face():
    vs, fs, mi = face_geo(NEUT)
    ob = mk('face', vs, fs, [M[k] for k in FM], mat_idx=mi)
    ob.shape_key_add(name='Basis')
    for name in EXPR:
        k = ob.shape_key_add(name=name); v2 = face_geo(EXPR[name])[0]
        k.data.foreach_set('co', [c for v in v2 for c in v])
    return ob

def set_expr(face, name):
    for k in face.data.shape_keys.key_blocks: k.value = 1.0 if k.name == name else 0.0

# ---------------------------------------------------------------- walker
def build_walker():
    for s in (-1, 1):
        pts = [(s * .495, .21, .087), (s * .455, .30, .90), (s * .455, .76, .90), (s * .495, .90, .087)]
        sweep('walker_side', fillet(pts, .07, 8), .021, M['alu'], seg=8)
        sweep('grip', [(s * .455, .37, .90), (s * .455, .57, .90)], .033, M['grip'], seg=12)
        for a, b in ((pts[0], pts[1]), (pts[3], pts[2])):
            a, b = V(a), V(b); d = (b - a).normalized()
            sweep('leg_ext', [a + d * .0, a + d * .30], .026, M['alu'], seg=8)          # telescoping lower leg
            for k in range(3): ell('adj_pin', a + d * (.16 + k * .045) + V((s * .026, 0, 0)), (.008, .011, .011), M['gold'], seg=6)
            sweep('rubber_foot', [a - d * .05, a - d * .035, a + d * .04], [.038, .034, .031], M['rubber'], seg=8)
        # side brace
        a = V(pts[0]).lerp(V(pts[1]), .42); b = V(pts[3]).lerp(V(pts[2]), .42)
        sweep('brace', [a, b], .016, M['alu'], seg=10)
    # front crossbars
    fz = lambda z: (.495 - .04 * (z - .05) / .85, .90 - .14 * (z - .05) / .85)
    for z in (.74, .40):
        x, y = fz(z); sweep('crossbar', fillet([(-x, y, z), (-x * .6, y + .05, z), (x * .6, y + .05, z), (x, y, z)], .08), .018, M['alu'], seg=6)
    # red basket hung on the upper crossbar
    c = V((0, .955, .615)); sz = (.52, .2, .25)
    rbox('basket', c, sz, M['red'], bevel=.035, open_top=True, taper=.9, solid=.014)
    t = c.z + sz[2] / 2; hx, hy = sz[0] / 2, sz[1] / 2
    rimp = fillet([(-hx + .05, c.y - hy, t), (hx, c.y - hy, t), (hx, c.y + hy, t), (-hx, c.y + hy, t), (-hx, c.y - hy, t), (-hx + .05, c.y - hy, t)], .035, 5)
    sweep('basket_rim', rimp, .014, M['red'], seg=8, round_caps=False)
    for k in range(7):
        rbox('basket_slot', (-.18 + k * .06, c.y + hy - .008 + .004, c.z + .01), (.026, .012, .13), M['redd'], bevel=.005, bseg=1)
    for s in (-1, 1):
        sweep('basket_hook', fillet([(s * .16, c.y - hy, t - .02), (s * .16, c.y - hy - .0, t + .145), (s * .16, .80, t + .145), (s * .16, .80, t + .09)], .028, 5), .011, M['alu'], seg=6)
    # chope: a packet of tissue in the basket
    r = Matrix.Rotation(math.radians(-14), 3, 'Y') @ Matrix.Rotation(math.radians(12), 3, 'X')
    rbox('tissue', c + V((.09, 0, .10)), (.2, .075, .13), M['tissue'], bevel=.02, rot=r)
    rbox('tissue_band', c + V((.09, 0, .10)), (.07, .079, .134), M['tgreen'], bevel=.02, rot=r)

# ---------------------------------------------------------------- stage
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
    lamp('key', 'AREA', (1.9, 4.9, 6.0), 1800, (1.0, .79, .54), 2.2)        # front-left (viewer), 45 deg up, golden
    lamp('fill', 'AREA', (-5.0, 3.5, 2.2), 420, (.62, .76, 1.0), 5.0)       # cool sky fill
    lamp('rim', 'SPOT', (-3.2, -4.6, 3.8), 5200, (1.0, .78, .52))            # warm rim from back-right
    # cyc: floor that curves up behind
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
    try: SC.eevee.use_shadows = True
    except Exception: pass
    try: SC.eevee.shadow_ray_count = 3; SC.eevee.shadow_step_count = 12
    except Exception: pass
    try: SC.eevee.use_raytracing = True
    except Exception: pass
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'HORIZONTAL'; cam = bpy.data.objects.new('cam', cd)
    SC.collection.objects.link(cam); SC.camera = cam; return cam

def shoot(cam, path, w, h, az, dist, target, width_m, cam_z=None):
    """az: degrees from front (+Y) toward -X. width_m: horizontal field at the target."""
    SC.render.resolution_x = w; SC.render.resolution_y = h; t = V(target); a = math.radians(az)
    cam.location = (t.x - dist * math.sin(a), t.y + dist * math.cos(a), cam_z if cam_z is not None else t.z)
    cam.data.lens = dist * 36 / width_m; look_at(cam, t)
    SC.render.filepath = path; bpy.ops.render.render(write_still=True)

def row(paths, out):
    ims = []
    for p in paths:
        im = bpy.data.images.load(p); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); ims.append(a.reshape(h, w, 4))
    a = np.concatenate(ims, axis=1)[:, :1600]; h, w = a.shape[:2]
    o = bpy.data.images.new('row', w, h, alpha=False); o.pixels.foreach_set(a.ravel()); o.filepath_raw = out; o.file_format = 'PNG'; o.save()

# ---------------------------------------------------------------- rig
SF = 1.0
def bones():
    """name, head, tail, parent. Design coordinates, already scaled by SF."""
    k = SF; v = lambda *a: tuple(x * k for x in a)
    B = [('root', v(0, 0, 0), v(0, 0, .25), None), ('hips', v(0, BY, .52), v(0, BY, .64), 'root'), ('spine', v(0, BY, .64), v(0, BY, .86), 'hips'),
         ('chest', v(0, BY, .86), v(0, BY, 1.02), 'spine'), ('neck', v(0, BY + .02, 1.02), v(0, BY + .02, HC.z - .27), 'chest'),
         ('head', v(0, HC.y + .02, HC.z - .27), v(0, HC.y + .02, HC.z + .5), 'neck')]
    for nm, sx_ in (('eye.l', -1), ('eye.r', 1)):
        p = surf(sx_ * EXe, EZe)[0]; B.append((nm, tuple(p * k), tuple((p + V((0, .06, 0))) * k), 'head'))
    for sx_, sd in ((-1, 'l'), (1, 'r')):
        S, E, Wr = ARM[sx_]; gx = sx_ * .455
        B += [('upperarm.' + sd, tuple(S * k), tuple(E * k), 'chest'), ('lowerarm.' + sd, tuple(E * k), tuple(Wr * k), 'upperarm.' + sd),
              ('hand.' + sd, tuple(Wr * k), v(gx, .53, .93), 'lowerarm.' + sd), ('handslot.' + sd, v(gx, .44, .935), v(gx, .52, .935), 'hand.' + sd)]
    for sx_, sd in ((-1, 'l'), (1, 'r')):
        B += [('upperleg.' + sd, v(sx_ * .19, BY, .56), v(sx_ * .195, BY, .36), 'hips'), ('lowerleg.' + sd, v(sx_ * .195, BY, .36), v(sx_ * .2, BY, .15), 'upperleg.' + sd),
              ('foot.' + sd, v(sx_ * .2, BY, .15), v(sx_ * .2, BY + .14, .05), 'lowerleg.' + sd), ('toes.' + sd, v(sx_ * .2, BY + .14, .05), v(sx_ * .2, BY + .30, .035), 'foot.' + sd)]
    B.append(('prop', (0, .70, 0), (0, .70, .3), 'root'))
    return B
RIGID = {'eye.l', 'eye.r', 'handslot.l', 'handslot.r'}     # prop deforms so the walker follows the hands in attack

def make_armature():
    arm = bpy.data.armatures.new('ahma_rig'); ob = bpy.data.objects.new('ahma_rig', arm)
    SC.collection.objects.link(ob); H.select_only([ob], ob)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, h, t, parent in bones():
        b = arm.edit_bones.new(name); b.head = h; b.tail = t
        if parent: b.parent = arm.edit_bones[parent]; b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in arm.bones: b.use_deform = b.name not in RIGID
    return ob

def ss(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)

def piece_weights(name, co, side):
    """Weights (dict bone -> w) for one vertex of a body piece. Design coordinates (before SF)."""
    z = co.z; sd = 'l' if side < 0 else 'r'
    if name in ('blouse', 'hem_piping', 'frog_bar', 'frog_knot', 'placket'):
        h = 1 - ss(.50, .74, z); c = ss(.80, 1.0, z); return {'hips': h, 'chest': c, 'spine': max(0.0, 1 - h - c)}
    if name in ('collar', 'collar_piping'): return {'chest': 1.0}
    if name == 'neck':
        hd = ss(1.2, 1.3, z); nk = ss(1.02, 1.14, z); return {'head': hd, 'neck': (1 - hd) * nk, 'chest': (1 - hd) * (1 - nk)}
    if name == 'hips': return {'hips': 1.0}
    if name in ('leg', 'cuff'):
        up = ss(.30, .42, z); top = ss(.44, .58, z); return {'hips': top, 'upperleg.' + sd: up * (1 - top), 'lowerleg.' + sd: (1 - up)}
    if name in ('foot', 'sole', 'strap', 'strap_post'): return {'foot.' + sd: 1.0}
    if name == 'sleeve':
        S, E, Wr = ARM[side]; ab = E - S; t = max(0.0, min(1.0, (co - S).dot(ab) / ab.length_squared)); u = ss(.0, .5, t)
        return {'upperarm.' + sd: u, 'chest': 1 - u}
    if name in ('forearm', 'bangle', 'cuff_piping'): return {'lowerarm.' + sd: 1.0}
    if name == 'hand': return {'hand.' + sd: 1.0}
    return {'chest': 1.0}

def set_groups(ob, fn):
    for g in list(ob.vertex_groups): ob.vertex_groups.remove(g)
    vg = {}
    for v in ob.data.vertices:
        for b, w in fn(v.co).items():
            if w <= 1e-4: continue
            if b not in vg: vg[b] = ob.vertex_groups.new(name=b)
            vg[b].add([v.index], w, 'REPLACE')

def skin(ob, rig):
    ob.parent = rig; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = rig

HEAD_N = {'head', 'hair', 'ear', 'stud', 'nose', 'lens', 'rim', 'hinge', 'temple', 'bridge', 'face', 'mouth_cut'}
WALK_N = {'walker_side', 'grip', 'leg_ext', 'adj_pin', 'rubber_foot', 'brace', 'crossbar', 'basket', 'basket_rim', 'basket_slot', 'basket_hook', 'tissue', 'tissue_band'}

def assemble():
    global SF
    top = max((o.matrix_world @ v.co).z for o in HERO for v in o.data.vertices)
    SF = 2.16 / top; print('TOY_TOP_RAW', round(top, 4), 'SF', round(SF, 4))
    import collections; cc = collections.Counter()
    for o in HERO: cc[o.name.split('.')[0]] += H.tri_count(o)
    print('TOY_BREAK', sorted(cc.items(), key=lambda kv: -kv[1]))
    # weights before scaling (design coordinates), then scale everything
    for o in HERO:
        base = o.name.split('.')[0]
        if base in HEAD_N or base in WALK_N: continue
        side = -1 if sum(v.co.x for v in o.data.vertices) < 0 else 1
        set_groups(o, lambda co, b=base, sd=side: piece_weights(b, co, sd))
    for o in HERO: o.data.transform(Matrix.Scale(SF, 4), shape_keys=True); o.data.update()
    heads = [o for o in HERO if o.name.split('.')[0] in HEAD_N]; walk = [o for o in HERO if o.name.split('.')[0] in WALK_N]
    body = [o for o in HERO if o not in heads and o not in walk]
    face = [o for o in heads if o.name == 'face'][0]; heads.remove(face); NF = len(face.data.vertices)
    # arms and neck weights were in design coords: the vertex positions scaled, weights are per vertex so they carry over
    rig = make_armature()
    hd = H.join([face] + heads, 'ahma_head'); bd = H.join(body, 'ahma_body'); wk = H.join(walk, 'ahma_walker')
    # skin-ring vertices get the exact ellipsoid normal so the ring shades like the head around it
    me = hd.data; sk = [i for i, m in enumerate(me.materials) if m.name == 'skin'][0]
    oth = {v for p in me.polygons if p.material_index != sk for v in p.vertices}
    c0 = HC * SF; r0 = HR * SF; cn = [Vector(n.vector) for n in me.corner_normals]
    for l in me.loops:
        vi = l.vertex_index
        if vi < NF and vi not in oth:
            w = me.vertices[vi].co; cn[l.index] = V(((w.x - c0.x) / r0.x ** 2, (w.y - c0.y) / r0.y ** 2, (w.z - c0.z) / r0.z ** 2)).normalized()
    me.normals_split_custom_set(cn)
    for o, bn in ((hd, 'head'), (wk, 'prop')):
        for g in list(o.vertex_groups): o.vertex_groups.remove(g)
        o.vertex_groups.new(name=bn).add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    for o in (hd, bd, wk): skin(o, rig)
    return rig, hd, bd, wk

# ---------------------------------------------------------------- animation
FPS = 30
def Mrest(rig, name): return rig.data.bones[name].matrix_local.to_3x3()
def rest_head(rig, name): return rig.data.bones[name].head_local.copy()
def axis_rot(axis, deg): return Quaternion(Vector(axis), math.radians(deg))
def set_world_rot(rig, pb, q):
    M3 = Mrest(rig, pb.name); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (M3.inverted() @ q.to_matrix() @ M3).to_quaternion()
def set_total(rig, pb, total, Dp):
    """Make the bone's accumulated armature-space rotation equal `total`, given the parent's accumulated rotation Dp."""
    Dc = Dp.inverted() @ total; M3 = Mrest(rig, pb.name); pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = (M3.inverted() @ Dc.to_matrix() @ M3).to_quaternion()
def parent_D(rig, pb):
    p = pb.parent; return (p.matrix.to_3x3() @ rig.data.bones[p.name].matrix_local.to_3x3().inverted()).to_quaternion()

def ik_arm(rig, sd, T, hand_q):
    """Two-bone arm IK: wrist to T (armature space), hand oriented by hand_q. Elbow keeps bending the way it rests."""
    B = rig.pose.bones; U, L, Hd = B['upperarm.' + sd], B['lowerarm.' + sd], B['hand.' + sd]
    S0, E0, W0 = (rest_head(rig, n) for n in ('upperarm.' + sd, 'lowerarm.' + sd, 'hand.' + sd))
    Dp = parent_D(rig, U); Sp = U.matrix.translation.copy()
    u0 = E0 - S0; l0 = W0 - E0; L1, L2 = u0.length, l0.length
    T = Vector(T); dv = T - Sp; d = min(dv.length, (L1 + L2) * .995); d = max(d, abs(L1 - L2) + 1e-3); dirv = dv.normalized()
    a = (L1 * L1 - L2 * L2 + d * d) / (2 * d); h = math.sqrt(max(L1 * L1 - a * a, 0))
    d0 = (Dp @ (W0 - S0)).normalized(); pv = Dp @ u0; pv = pv - d0 * pv.dot(d0)
    pn = pv - dirv * pv.dot(dirv); pn = pn.normalized() if pn.length > 1e-6 else Vector((0, 0, -1))
    Ep = Sp + dirv * a + pn * h; Tp = Sp + dirv * d
    q1 = (Dp @ u0).rotation_difference(Ep - Sp) @ Dp; set_total(rig, U, q1, Dp)
    q2 = (q1 @ l0).rotation_difference(Tp - Ep) @ q1; set_total(rig, L, q2, q1)
    set_total(rig, Hd, hand_q, q2)

def reset_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)

PIVOT = Vector((0, .70, 0))
def hips_lift(rig, dz):
    pb = rig.pose.bones['hips']; pb.location = Mrest(rig, 'hips').inverted() @ Vector((0, 0, dz))
def set_prop(rig, q, t):
    pb = rig.pose.bones['prop']; set_world_rot(rig, pb, q); pb.location = Mrest(rig, 'prop').inverted() @ Vector(t)

def pose_frame(rig, t, kind):
    reset_pose(rig); B = rig.pose.bones; X = (1, 0, 0); Z_ = (0, 0, 1); s = math.sin(2 * math.pi * t); c = math.cos(2 * math.pi * t)
    pq, pt = Quaternion(), Vector((0, 0, 0)); free = False
    if kind == 'idle':
        set_world_rot(rig, B['chest'], axis_rot(X, 2.0 * s)); set_world_rot(rig, B['head'], axis_rot(X, -1.5 * s) @ axis_rot(Z_, 2.0 * c)); hips_lift(rig, 0.006 * s)
    elif kind == 'run':
        for k, sg in ((-1, 1), (1, -1)):
            sd = 'l' if k < 0 else 'r'
            set_world_rot(rig, B['upperleg.' + sd], axis_rot(X, 32 * s * sg))
            set_world_rot(rig, B['lowerleg.' + sd], axis_rot(X, -45 * max(0.0, -s * sg)))
            set_world_rot(rig, B['foot.' + sd], axis_rot(X, 15 * max(0.0, -s * sg)))
        set_world_rot(rig, B['chest'], axis_rot(X, 9) @ axis_rot(Z_, 4 * s)); set_world_rot(rig, B['head'], axis_rot(X, -6) @ axis_rot(Z_, -3 * s))
        set_world_rot(rig, B['spine'], axis_rot(X, 4)); hips_lift(rig, 0.03 * abs(s) - 0.015)
        pq = axis_rot(X, 3 * math.sin(4 * math.pi * t)); pt = Vector((0, 0.0, 0.025 * abs(s)))
    elif kind == 'attack':
        if t < 0.33: u = t / 0.33; lift = 0.38 * math.sin(u * math.pi / 2); tilt = -40 * u; fwd = -0.05 * u
        elif t < 0.55: u = (t - 0.33) / 0.22; lift = 0.38 * (1 - u) ** 2; tilt = -40 + 60 * u; fwd = -0.05 + 0.30 * u
        else: u = (t - 0.55) / 0.45; lift = 0.0; tilt = 20 * (1 - u); fwd = 0.25 * (1 - u)
        pq = axis_rot(X, tilt); pt = Vector((0, fwd, lift))
        lean = -10 if t < 0.33 else (14 if t < 0.55 else 14 * (1 - u))
        set_world_rot(rig, B['chest'], axis_rot(X, lean)); set_world_rot(rig, B['spine'], axis_rot(X, lean * 0.5)); set_world_rot(rig, B['head'], axis_rot(X, -lean * 0.6))
        hips_lift(rig, -0.04 if 0.33 <= t < 0.7 else 0.0)
    elif kind == 'ult':
        set_world_rot(rig, B['chest'], axis_rot(X, -6)); set_world_rot(rig, B['head'], axis_rot(X, -8)); set_world_rot(rig, B['spine'], axis_rot(X, -3)); free = True
    set_prop(rig, pq, pt); bpy.context.view_layer.update()
    for k in (-1, 1):
        sd = 'l' if k < 0 else 'r'
        if free:
            Sp = B['upperarm.' + sd].matrix.translation; dirv = Vector((k * .75, .05, .66)).normalized()
            ik_arm(rig, sd, Sp + dirv * 10, axis_rot(X, 10))
        else:
            W0 = rest_head(rig, 'hand.' + sd); T = PIVOT + pq @ (W0 - PIVOT) + pt
            ik_arm(rig, sd, T, pq)
        bpy.context.view_layer.update()

ANIM_BONES = ['hips', 'spine', 'chest', 'neck', 'head', 'upperarm.l', 'lowerarm.l', 'hand.l', 'upperarm.r', 'lowerarm.r', 'hand.r',
              'upperleg.l', 'lowerleg.l', 'foot.l', 'upperleg.r', 'lowerleg.r', 'foot.r', 'prop']
def make_action(rig, name, kind, n):
    act = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act
    for f in range(n + 1):
        SC.frame_set(f); pose_frame(rig, (f % n) / n if kind != 'ult' else 0.0, kind)
        for b in ANIM_BONES:
            pb = rig.pose.bones[b]; pb.keyframe_insert('rotation_quaternion', frame=f)
            if b in ('hips', 'prop'): pb.keyframe_insert('location', frame=f)
    act.frame_range = (0, n); act.use_frame_range = True; act.use_fake_user = True; return act

def add_clips(rig):
    SC.render.fps = FPS
    acts = [make_action(rig, 'idle', 'idle', 60), make_action(rig, 'run', 'run', 24), make_action(rig, 'attack', 'attack', 18), make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    reset_pose(rig)

# ---------------------------------------------------------------- stage
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
    try: SC.eevee.use_shadows = True
    except Exception: pass
    try: SC.eevee.shadow_ray_count = 3; SC.eevee.shadow_step_count = 12
    except Exception: pass
    try: SC.eevee.use_raytracing = True
    except Exception: pass
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'HORIZONTAL'; cam = bpy.data.objects.new('cam', cd)
    SC.collection.objects.link(cam); SC.camera = cam; return cam

def shoot(cam, path, w, h, az, dist, target, width_m, cam_z=None):
    SC.render.resolution_x = w; SC.render.resolution_y = h; t = V(target); a = math.radians(az)
    cam.location = (t.x - dist * math.sin(a), t.y + dist * math.cos(a), cam_z if cam_z is not None else t.z)
    cam.data.lens = dist * 36 / width_m; look_at(cam, t)
    SC.render.filepath = path; bpy.ops.render.render(write_still=True)

def row(paths, out, cols=None, maxw=None):
    ims = []
    for p in paths:
        im = bpy.data.images.load(p); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); ims.append(a.reshape(h, w, 4))
    cols = cols or len(ims); rows = (len(ims) + cols - 1) // cols; h, w = ims[0].shape[:2]
    buf = np.zeros((h * rows, w * cols, 4), np.float32); buf[..., 3] = 1
    for i, a in enumerate(ims):
        r, c = divmod(i, cols); buf[(rows - 1 - r) * h:(rows - r) * h, c * w:(c + 1) * w] = a
    o = bpy.data.images.new('row', w * cols, h * rows, alpha=False); o.pixels.foreach_set(buf.ravel()); o.filepath_raw = out; o.file_format = 'PNG'; o.save()

def play(rig, name, frame):
    rig.animation_data.action = bpy.data.actions[name]; SC.frame_set(frame)
def set_expr(head, name):
    for k in head.data.shape_keys.key_blocks: k.value = 1.0 if k.name == name else 0.0

# ---------------------------------------------------------------- stages
BLEND = os.path.join(TMP, 'ahma_rig.blend')
def stage_build():
    build_body(); build_arms(); build_head(); build_face(); build_walker()
    rig, hd, bd, wk = assemble(); add_clips(rig)
    for o in (hd, bd, wk): print('TOY_PART', o.name, H.tri_count(o), 'tris,', len(o.data.vertices), 'verts,', [m.name for m in o.data.materials])
    print('TOY_TRIS', sum(H.tri_count(o) for o in (hd, bd, wk)))
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)

def stage_export():
    global SC
    bpy.ops.wm.open_mainfile(filepath=BLEND); SC = bpy.context.scene
    rig = bpy.data.objects['ahma_rig']; reset_pose(rig); rig.animation_data.action = None
    for k in bpy.data.objects['ahma_head'].data.shape_keys.key_blocks: k.value = 0.0
    objs = [bpy.data.objects[n] for n in ('ahma_head', 'ahma_body', 'ahma_walker')] + [rig]
    H.select_only(objs, rig)
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
                              export_animations=True, export_animation_mode='ACTIONS', export_nla_strips=True, export_skins=True, export_def_bones=False,
                              export_morph=True, export_morph_normal=False, export_image_format='AUTO', export_materials='EXPORT', export_texcoords=True,
                              export_normals=True, export_tangents=False, export_all_influences=False, export_optimize_animation_size=True)
    print('EXPORT wrote', OUT_GLB, os.path.getsize(OUT_GLB) // 1024, 'KB')

def stage_verify():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=OUT_GLB)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Icosphere']
    rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    lo = V((1e9,) * 3); hi = V((-1e9,) * 3)
    for o in meshes:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co; lo = V(map(min, lo, w)); hi = V(map(max, hi, w))
    print(f'VERIFY tris {sum(H.tri_count(o) for o in meshes)} height {hi.z - lo.z:.3f} (z {lo.z:.3f}..{hi.z:.3f}) X {lo.x:.3f}..{hi.x:.3f} Y {lo.y:.3f}..{hi.y:.3f} (nose side Y+ means glTF -Z)')
    print('VERIFY bones', len(rig.data.bones), [b.name for b in rig.data.bones])
    hb = rig.matrix_world @ rig.data.bones['head'].head_local; print('VERIFY head bone', tuple(round(x, 3) for x in hb))
    for o in meshes:
        print('VERIFY mesh', o.name, H.tri_count(o), 'tris', 'keys', [k.name for k in o.data.shape_keys.key_blocks][1:] if o.data.shape_keys else None)
    fr = 30 / bpy.context.scene.render.fps * bpy.context.scene.render.fps_base
    print('VERIFY actions (frames at 30fps, scene fps %s)' % bpy.context.scene.render.fps, [(a.name, round(a.frame_range[0] * fr), round(a.frame_range[1] * fr)) for a in bpy.data.actions])

def stage_shots():
    global SC
    bpy.ops.wm.open_mainfile(filepath=BLEND); SC = bpy.context.scene
    rig = bpy.data.objects['ahma_rig']; head = bpy.data.objects['ahma_head']; cam = stage()
    want = [a for a in ARGS if a in ('beauty', 'turn', 'expr', 'anim')]
    ok = lambda k: not want or k in want
    play(rig, 'idle', 0); set_expr(head, 'smile')
    if ok('beauty'): shoot(cam, os.path.join(OUT, 'beauty.png'), 1600, 1600, 32, 8, (0, .25, 1.08), 2.75, cam_z=1.0)
    if ok('turn'):
        ps = []
        for i, ang in enumerate((0, 90, 180)):
            rig.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
            t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((0, .22, 1.08)); p = os.path.join(TMP, 't_%d.png' % i); ps.append(p)
            shoot(cam, p, 534, 800, 0, 9, t, 1.78)
        rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(OUT, 'turnaround.png'))
    if ok('expr'):
        ps = []
        for name in ('smile', 'angry', 'grin', 'ult'):
            set_expr(head, name); p = os.path.join(TMP, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, 0, 1.67), 1.42)
        row(ps, os.path.join(OUT, 'expressions.png')); set_expr(head, 'smile')
    if ok('anim'):
        ps = []
        for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
            for i in range(4):
                play(rig, name, int(i * n / 4)); set_expr(head, 'ult' if name == 'ult' else ('angry' if name == 'attack' else 'smile'))
                p = os.path.join(TMP, 'a_%s_%d.png' % (name, i)); ps.append(p); shoot(cam, p, 400, 500, 28, 9, (0, .15, 1.1), 2.3, cam_z=1.1)
        row(ps, os.path.join(OUT, 'anim_sheet.png'), cols=4)

if 'build' in ARGS: stage_build()
if 'export' in ARGS: stage_export()
if 'verify' in ARGS: stage_verify()
if 'shots' in ARGS: stage_shots()
