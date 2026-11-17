"""Ah Ma, style `toy`: designer vinyl collectible. Run: blender -b -P ahma_toy.py [-- quick]
Builds the figure, saves ahma_toy.blend and renders the four bake-off shots.
Axes: Z up, hero faces +Y. Everything is clean primitives, sweeps and lathes (no sculpt noise)."""
import bpy, sys, os, math, random
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'blender', 'heroes'))
import hero_lib as H
OUT = os.path.join(ROOT, 'shots', 'styles', 'toy')
TMP = os.path.join(HERE, '_tmp')
QUICK = 'quick' in sys.argv
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
    hair=mat('hair', '#ECE7F2', .33, coat=.25),
    brow=mat('brow', '#A9A4B0', .45),
    eye=mat('eye', '#1A1214', .08, coat=1.0),
    white=mat('white', '#FFFDF8', .25),
    mouth=mat('mouth', '#7B2331', .45),
    tongue=mat('tongue', '#F2818C', .35),
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
    m = bpy.data.materials.new('lens'); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); gl = nt.nodes.new('ShaderNodeBsdfGlossy'); add = nt.nodes.new('ShaderNodeAddShader')
    tr.inputs['Color'].default_value = (.97, .98, 1, 1)
    gl.inputs['Color'].default_value = (.16, .17, .2, 1); gl.inputs['Roughness'].default_value = .03
    nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(gl.outputs[0], add.inputs[1]); nt.links.new(add.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'BLENDED'; return m
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

def sweep(name, pts, radii, m, seg=14, uvrep=None, round_caps=True, lip=None):
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
HC = V((0, -0.01, 1.52)); HR = V((0.58, 0.55, 0.52))    # head centre and radii

def surf(fx, fz, off=0.0):
    """Face coordinates (x right of centre, z above centre) -> point on the front of the head, normal, tangent, up."""
    k = max(1e-4, 1 - (fx / HR.x) ** 2 - (fz / HR.z) ** 2); y = HR.y * math.sqrt(k)
    n = V((fx / HR.x ** 2, y / HR.y ** 2, fz / HR.z ** 2)).normalized()
    t = n.cross(Z).normalized(); u = t.cross(n).normalized()
    return HC + V((fx, y, fz)) + n * off, n, t, u

# ---------------------------------------------------------------- body
def build_body():
    cz = [.455, .50, .60, .72, .84, .93, 1.00, 1.05, 1.09]; cr = [.455, .475, .47, .435, .385, .33, .255, .17, .06]
    zs = np.linspace(cz[0], cz[-1], 26); rs = np.interp(zs, cz, cr)
    for _ in range(3): rs[1:-1] = (rs[:-2] + 2 * rs[1:-1] + rs[2:]) / 4
    global BR
    BR = lambda z: float(np.interp(z, zs, rs))
    rows = [(.36, .50), (.43, .462)] + list(zip(rs, zs)); seg = 48; vs = []; fs = []; uvs = []
    for r, z in rows:
        for i in range(seg):
            a = 2 * math.pi * i / seg; vs.append(V((r * math.cos(a), BY + .88 * r * math.sin(a), z)))
    for j in range(len(rows) - 1):
        for i in range(seg):
            fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
            v0 = rows[j][1] * 1.45; v1 = rows[j + 1][1] * 1.45
            uvs.append([(i / seg * 4, v0), ((i + 1) / seg * 4, v0), ((i + 1) / seg * 4, v1), (i / seg * 4, v1)])
    fs.append(tuple(range((len(rows) - 1) * seg, len(rows) * seg))); uvs.append([(0, 0)] * seg)
    mk('blouse', vs, fs, M['floral'], uvs)
    tor('hem_piping', (0, BY, .458), Z, .458, .014, M['pipe'], seg=56, rseg=8, squash=(1, .88, 1))
    # frog buttons down the front
    for z in (.60, .74, .87):
        y = BY + .88 * BR(z) + .004
        sweep('frog_bar', [(-.05, y - .002, z), (0, y + .004, z), (.05, y - .002, z)], .011, M['pipe'], seg=8)
        ell('frog_knot', (0, y + .008, z), (.022, .018, .022), M['pipe'], seg=16)
    # hips and legs (slacks)
    ell('hips', (0, BY, .50), (.37, .32, .13), M['navy'])
    for s in (-1, 1):
        sweep('leg', [(s * .19, BY, .56), (s * .195, BY, .36), (s * .2, BY, .15)], [.19, .18, .17], M['navy'], seg=24, lip=(.012, .12))
        sweep('cuff', [(s * .2, BY, .158), (s * .2, BY, .15)], .174, M['navy'], seg=24, round_caps=False)
        ell('foot', (s * .2, BY + .09, .088), (.1, .175, .058), M['skin'])
        ell('sole', (s * .2, BY + .085, .034), (.125, .215, .034), M['red'])
        post = V((s * .2, BY + .21, .10))
        for o in (-1, 1):
            sweep('strap', bez(post, (s * .2 + o * .085, BY + .15, .185), (s * .2 + o * .112, BY + .02, .05)), .017, M['red'], seg=8)
        ell('strap_post', post, (.02, .02, .025), M['red'], seg=12)

def build_arms():
    for s in (-1, 1):
        S = V((s * .30, BY + .05, .955)); E = V((s * .56, BY + .13, .80)); Wr = V((s * .455, .365, .945))
        path = bez(S, E, E.lerp(Wr, .25), 9)
        sweep('sleeve', path, [.125, .135, .14, .138, .132, .122, .112, .103, .097], M['floral'], seg=20, uvrep=(1, 1.3), lip=(.004, .088))
        tor('cuff_piping', path[-1], path[-1] - path[-2], .096, .0125, M['pipe'], seg=28, rseg=6)
        sweep('forearm', [path[-2], Wr], [.082, .064], M['skin'], seg=16)
        if s == 1: tor('bangle', path[-2].lerp(Wr, .72), Wr - path[-2], .078, .022, M['jade'], seg=40, rseg=12)
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
        hand, _ = so.remesh(voxel=.0065, smooth=6, smooth_factor=.6, target_tris=1300)
        H.set_material(hand, M['skin']); reg(hand)

# ---------------------------------------------------------------- head
def build_head():
    ell('head', HC, HR, M['skin'], seg=56)
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
    hair, _ = so.remesh(voxel=.013, smooth=10, smooth_factor=.6, target_tris=5800)
    H.set_material(hair, M['hair']); reg(hair)
    for s in (-1, 1):
        ell('ear', HC + V((s * .57, -.03, -.05)), (.045, .085, .105), M['skin'], seg=20)
        ell('stud', HC + V((s * .612, -.01, -.115)), (.026, .026, .026), M['gold'], seg=16)
    p, n, t, u = surf(0, -.115); ell('nose', p + n * .004, (.052, .042, .04), M['nose'], seg=24)

    # glasses
    EX, EZ = .215, -.01; RR = .15
    cs = {}
    for s in (-1, 1):
        p, n, t, u = surf(s * EX, EZ); ng = V((s * .13, 1, -.04)).normalized(); c = p + n * .075
        tg = ng.cross(Z).normalized(); cs[s] = (c, tg, ng)
        tor('rim', c, ng, RR, .017, M['rim'], seg=44, rseg=8)
        # lens disc
        vs = [c] + [c + (tg * math.cos(a) + tg.cross(ng) * math.sin(a)) * RR for a in [2 * math.pi * i / 40 for i in range(40)]]
        mk('lens', vs, [(0, 1 + i, 1 + (i + 1) % 40) for i in range(40)], M['lens']).visible_shadow = False
        outer = c + tg * (s * (RR + .005))
        ell('hinge', outer, (.022, .02, .022), M['gold'], seg=12)
        sweep('temple', fillet([outer, HC + V((s * .575, .30, .06)), HC + V((s * .60, .0, .055))], .12), .012, M['rim'], seg=8)
    a = cs[-1][0] + cs[-1][1] * RR; b = cs[1][0] - cs[1][1] * RR
    sweep('bridge', bez(a + Z * .03, (a + b) * .5 + V((0, .03, .075)), b + Z * .03, 8), .013, M['gold'], seg=8)

# ---------------------------------------------------------------- face (one mesh, four shape keys)
EXPR = {
    'smile': dict(bz=.185, tilt=-.006, arch=.022, eye='bead', es=(1, 1), cut=None, hl=.026, wr=0, w=.20, curve=.036, up=0, dn=0, teeth=0, tongue=0, cz=-.265),
    'angry': dict(bz=.058, tilt=.058, arch=-.004, eye='bead', es=(1.02, 1), cut=(.016, .55), hl=.0, wr=-.02, w=.19, curve=-.042, up=.022, dn=.036, teeth=1, tongue=0, cz=-.255),
    'grin':  dict(bz=.205, tilt=-.012, arch=.034, eye='arc', es=(1, 1), cut=None, hl=.026, wr=.022, w=.33, curve=.062, up=.004, dn=.112, teeth=.036, tongue=.05, cz=-.28),
    'ult':   dict(bz=.185, tilt=.066, arch=.004, eye='bead', es=(1.12, 1.16), cut=None, hl=.03, wr=.012, w=.26, curve=.006, up=.05, dn=.11, teeth=.036, tongue=.07, cz=-.265),
}
FM = ['brow', 'eye', 'white', 'line', 'mouth', 'teeth', 'tongue', 'blush']
EXe, EZe = .215, -.01

def face_geo(e):
    vs = []; fs = []; mi = []
    def add(v, f, m):
        o = len(vs); vs.extend(v); fs.extend([tuple(i + o for i in ff) for ff in f]); mi.extend([FM.index(m)] * len(f))
    def hide(v): return [HC.copy() for _ in v]
    def stroke(pts, rw, rn, off, m, show=True, seg=8):
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
    def patch(x0, x1, lo, hi, off, m, nx=28, ny=6):
        v = []
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx; a, b = lo(x), hi(x)
            for j in range(ny + 1): v.append(surf(x, a + (b - a) * j / ny, off)[0])
        f = [(i * (ny + 1) + j, (i + 1) * (ny + 1) + j, (i + 1) * (ny + 1) + j + 1, i * (ny + 1) + j + 1) for i in range(nx) for j in range(ny)]
        add(v, f, m)
    for s in (-1, 1):
        # brow (s=-1..1 runs inner to outer)
        stroke([(s * (EXe + q * .095), e['bz'] + q * e['tilt'] + e['arch'] * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .03, .016, .004, 'brow')
        bead = e['eye'] == 'bead'; a, c = .056 * e['es'][0], .07 * e['es'][1]
        blob(s * EXe, EZe, (a, .036, c), 0, 'eye', show=bead, seg=24, cut=(e['cut'][0], e['cut'][1] * s) if e['cut'] else None)
        blob(s * EXe, EZe, (.019, .012, .019), .028, 'white', show=bead, seg=12, d=(.02, e['hl']))
        blob(s * EXe, EZe, (.008, .006, .008), .026, 'white', show=bead, seg=8, d=(-.022, -.03))
        pass
        stroke([(s * EXe + .066 * math.cos(ph), EZe - .028 + .062 * math.sin(ph)) for ph in [math.radians(168 - 156 * i / 11) for i in range(12)]], .0145, .011, .005, 'eye', show=not bead)
        # blush decal, conforms to the head
        v = [surf(s * .375, -.195, .0025)[0]]; f = []
        for j in range(1, 4):
            for i in range(20):
                ang = 2 * math.pi * i / 20; v.append(surf(s * .375 + .08 * j / 3 * math.cos(ang), -.195 + .058 * j / 3 * math.sin(ang), .0025 if j < 3 else .0)[0])
        ri = lambda j, i: 1 + (j - 1) * 20 + i % 20
        f += [(0, ri(1, i), ri(1, i + 1)) for i in range(20)]
        f += [(ri(j, i), ri(j + 1, i), ri(j + 1, i + 1), ri(j, i + 1)) for j in (1, 2) for i in range(20)]
        add(v, f, 'blush')
    # two gentle forehead lines (age, kept as clean debossed-print strokes)
    for z0, hw0 in ((.262, .12), (.305, .09)):
        stroke([(q * hw0, z0 + e['wr'] + .012 * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .0075, .004, .001, 'line')
    # mouth
    w = e['w']; hw = w / 2
    def env(x): return max(0.0, 1 - (x / hw) ** 2) ** .5
    def zc(x): return e['cz'] + e['curve'] * (x / hw) ** 2
    def half(x): return .0075 * min(1.0, env(x) * 2.5)
    def up(x): return zc(x) + e['up'] * env(x) + half(x)
    def lo(x): return zc(x) - e['dn'] * env(x) - half(x)
    patch(-hw, hw, lo, up, .003, 'mouth')
    tw = hw * .9
    if e['teeth'] >= 1: patch(-tw, tw, lambda x: lo(x) + .006 * env(x), lambda x: up(x) - .006 * env(x), .005, 'teeth')
    else: patch(-tw, tw, lambda x: max(lo(x), up(x) - e['teeth'] * (1.15 - .4 * (x / tw) ** 2)) if e['teeth'] else up(x), up, .005, 'teeth')
    gw = hw * .62
    patch(-gw, gw, lo, lambda x: min(up(x), lo(x) + e['tongue'] * max(0.0, 1 - (x / gw) ** 2) ** .5), .005, 'tongue')
    return vs, fs, mi

def build_face():
    vs, fs, mi = face_geo(EXPR['smile'])
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
        pts = [(s * .495, .21, .05), (s * .455, .30, .90), (s * .455, .76, .90), (s * .495, .90, .05)]
        sweep('walker_side', fillet(pts, .07, 8), .021, M['alu'], seg=12)
        sweep('grip', [(s * .455, .37, .90), (s * .455, .57, .90)], .033, M['grip'], seg=16)
        for a, b in ((pts[0], pts[1]), (pts[3], pts[2])):
            a, b = V(a), V(b); d = (b - a).normalized()
            sweep('leg_ext', [a + d * .0, a + d * .30], .026, M['alu'], seg=12)          # telescoping lower leg
            for k in range(3): ell('adj_pin', a + d * (.16 + k * .045) + V((s * .026, 0, 0)), (.008, .011, .011), M['gold'], seg=8)
            sweep('rubber_foot', [a - d * .05, a - d * .035, a + d * .04], [.038, .034, .031], M['rubber'], seg=12)
        # side brace
        a = V(pts[0]).lerp(V(pts[1]), .42); b = V(pts[3]).lerp(V(pts[2]), .42)
        sweep('brace', [a, b], .016, M['alu'], seg=10)
    # front crossbars
    fz = lambda z: (.495 - .04 * (z - .05) / .85, .90 - .14 * (z - .05) / .85)
    for z in (.74, .40):
        x, y = fz(z); sweep('crossbar', fillet([(-x, y, z), (-x * .6, y + .05, z), (x * .6, y + .05, z), (x, y, z)], .08), .018, M['alu'], seg=10)
    # red basket hung on the upper crossbar
    c = V((0, .955, .615)); sz = (.52, .2, .25)
    rbox('basket', c, sz, M['red'], bevel=.035, open_top=True, taper=.9, solid=.014)
    t = c.z + sz[2] / 2; hx, hy = sz[0] / 2, sz[1] / 2
    rimp = fillet([(-hx + .05, c.y - hy, t), (hx, c.y - hy, t), (hx, c.y + hy, t), (-hx, c.y + hy, t), (-hx, c.y - hy, t), (-hx + .05, c.y - hy, t)], .035, 5)
    sweep('basket_rim', rimp, .014, M['red'], seg=8, round_caps=False)
    for k in range(7):
        rbox('basket_slot', (-.18 + k * .06, c.y + hy - .008 + .004, c.z + .01), (.026, .012, .13), M['redd'], bevel=.005, bseg=1)
    for s in (-1, 1):
        sweep('basket_hook', fillet([(s * .16, c.y - hy, t - .02), (s * .16, c.y - hy - .0, t + .145), (s * .16, .80, t + .145), (s * .16, .80, t + .09)], .028, 5), .011, M['alu'], seg=8)
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

# ---------------------------------------------------------------- main
build_body(); build_arms(); build_head(); face = build_face(); build_walker()
root = bpy.data.objects.new('AhMa_toy', None); SC.collection.objects.link(root)
for o in HERO: o.parent = root
tris = sum(H.tri_count(o) for o in HERO)
print('TOY_TRIS', tris, 'objects', len(HERO))
agg = {}
for o in HERO: agg[o.name.split('.')[0]] = agg.get(o.name.split('.')[0], 0) + H.tri_count(o)
print('TOY_TOP', sorted(agg.items(), key=lambda kv: -kv[1])[:16])
cam = stage()
set_expr(face, 'smile')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'ahma_toy.blend'))

only = [a for a in sys.argv if a in ('hero', 'face', 'expr', 'turn')]
def want(k): return not only or k in only
if want('hero'): shoot(cam, os.path.join(OUT, 'hero.png'), 1600, 1600, 32, 8, (0, .25, 1.08), 2.75, cam_z=1.0)
if want('face'): shoot(cam, os.path.join(OUT, 'face.png'), 1600, 1600, 32, 7, (0, .05, 1.47), 1.75)
if want('expr'):
    ps = []
    for name in ('smile', 'angry', 'grin', 'ult'):
        set_expr(face, name); p = os.path.join(TMP, 'e_%s.png' % name); ps.append(p)
        shoot(cam, p, 400, 440, 0, 7, (0, 0, 1.53), 1.42)
    row(ps, os.path.join(OUT, 'expressions.png')); set_expr(face, 'smile')
if want('turn'):
    ps = []
    for i, ang in enumerate((0, 90, 180)):
        root.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
        t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((0, .22, 1.08)); p = os.path.join(TMP, 't_%d.png' % i); ps.append(p)
        shoot(cam, p, 534, 800, 0, 9, t, 1.78)
    root.rotation_euler = (0, 0, 0); row(ps, os.path.join(OUT, 'turn.png'))
