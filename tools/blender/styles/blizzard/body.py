"""Ah Ma body, clothes and walker. World units, hero faces +Y, floor z=0. Her right is +X."""
import bpy, math, numpy as np
import bl, head
from bl import lin
from sdf import Grid, sphere, ellipsoid, capsule, tube, torus, rbox, sstep

HEAD = (0, 0.075, 1.68)
HX, HY, HZ, GR = 0.33, 0.43, 0.86, 0.027          # walker handle axis (along Y), grip radius
SH = np.array((0.27, -0.02, 1.20), np.float32)    # shoulder, +X side
EL = np.array((0.43, 0.03, 0.98), np.float32)     # elbow
WR = np.array((HX + 0.005, HY - 0.12, HZ + GR + 0.055), np.float32)   # wrist
CF = EL + 0.60 * (WR - EL)                         # sleeve cuff
FD = (WR - EL) / np.linalg.norm(WR - EL)
HEM = 0.59; BC = (0, 0.045)                        # hem height, torso axis (x, y)
CONST = repr((HX, HY, HZ, GR, SH.tolist(), EL.tolist(), HEM))

def unit(v): v = np.asarray(v, np.float32); return v / np.linalg.norm(v)

def blouse_grid():
    g = Grid((-0.62, -0.42, 0.52), (0.62, 0.50, 1.42), 0.006)
    g.add(ellipsoid((0, -0.01, 1.06), (0.30, 0.235, 0.25)))
    g.add(ellipsoid((0, 0.05, 0.86), (0.37, 0.31, 0.29)), k=0.08)
    g.add(ellipsoid((0, -0.08, 1.13), (0.25, 0.17, 0.17)), k=0.08)
    g.add(ellipsoid((0, 0.045, 0.66), (0.40, 0.335, 0.22)), k=0.06)
    for sx in (1, -1):
        m = np.array((sx, 1, 1), np.float32); S, E, C = SH * m, EL * m, CF * m
        g.add(sphere(S, 0.115), k=0.06); g.add(capsule(S, E, 0.112, 0.10), k=0.05); g.add(capsule(E, C, 0.10, 0.09), k=0.03)
    def folds(d, x, y, z):   # soft drape folds toward the hem
        a = np.arctan2(x, y - BC[1]); w = 1 - sstep(0.62, 0.90, z)
        return d + (0.007 * np.sin(9 * a + 1.3) + 0.004 * np.sin(17 * a)) * w
    g.apply((-1, -1, 0.5), (1, 1, 0.92), folds)
    g.add(torus((0, 0.0, 1.30), unit((0, 0.10, 1)), 0.125, 0.028), k=0.015)
    g.cut(rbox((0, 0, HEM - 0.2), (1, 1, 0.2)), k=0.006)
    g.cut(ellipsoid((0, 0.045, HEM), (0.352, 0.29, 0.14)), k=0.008)
    g.cut(capsule((0, 0.0, 1.2), (0, 0.012, 1.5), 0.108), k=0.006)
    for sx in (1, -1):
        m = np.array((sx, 1, 1), np.float32); C = CF * m; D = FD * m
        g.cut(capsule(C - D * 0.04, C + D * 0.25, 0.07), k=0.006)
    return g

def slacks_grid():
    g = Grid((-0.40, -0.32, 0.02), (0.40, 0.40, 0.82), 0.006)
    g.add(ellipsoid((0, 0.03, 0.62), (0.33, 0.27, 0.17)))
    for sx in (1, -1):
        g.add(capsule((sx * 0.16, 0.03, 0.55), (sx * 0.17, 0.03, 0.14), 0.155, 0.118), k=0.04)
    g.cut(rbox((0, 0, -0.115), (1, 1, 0.2)), k=0.006)
    for sx in (1, -1):
        g.cut(capsule((sx * 0.17, 0.03, 0.0), (sx * 0.17, 0.03, 0.17), 0.098), k=0.006)
    return g

def foot_grid():
    g = Grid((0.07, -0.08, 0.0), (0.28, 0.27, 0.30), 0.003)
    g.add(capsule((0.17, 0.02, 0.27), (0.17, 0.02, 0.085), 0.052, 0.046))
    g.add(sphere((0.17, 0.0, 0.066), 0.05), k=0.03)
    g.add(ellipsoid((0.172, 0.10, 0.064), (0.062, 0.125, 0.036)), k=0.03)
    for x, y, r in ((0.132, 0.208, 0.023), (0.160, 0.218, 0.018), (0.182, 0.214, 0.0165), (0.202, 0.204, 0.0155), (0.219, 0.190, 0.0145)):
        g.add(sphere((x, y, 0.036 + r), r), k=0.010)
    g.cut(rbox((0.17, 0.1, -0.165), (1, 1, 0.2)), k=0.004)
    return g

def sole_grid():
    g = Grid((0.07, -0.10, 0.0), (0.28, 0.29, 0.06), 0.003)
    g.add(ellipsoid((0.172, 0.095, 0.02), (0.088, 0.18, 0.06)))
    g.cut(rbox((0.17, 0.1, 0.237), (1, 1, 0.2)), k=0.006); g.cut(rbox((0.17, 0.1, -0.196), (1, 1, 0.2)), k=0.004)
    return g

def hand_grid():
    g = Grid((0.22, -0.04, 0.76), (0.52, 0.56, 1.08), 0.003)
    f = Grid.__new__(Grid); f.__dict__.update(g.__dict__); f.d = g.d.copy()
    rho = GR + 0.013
    for i, yo in enumerate((-0.040, -0.0135, 0.0135, 0.040)):
        th = np.radians(np.linspace(80, -155 + 8 * abs(i - 1.5), 12))
        pts = [(HX + rho * math.cos(t), HY + yo, HZ + rho * math.sin(t)) for t in th]
        f.add(tube(pts, list(np.linspace(0.0142, 0.0112, 12))), k=0.004)
    th = np.radians(np.linspace(118, 235, 9))
    f.add(tube([(HX + rho * math.cos(t), HY - 0.035 + 0.03 * i / 8, HZ + rho * math.sin(t)) for i, t in enumerate(th)],
               list(np.linspace(0.0165, 0.013, 9))), k=0.004)
    g.add(ellipsoid((HX, HY, HZ + GR + 0.02), (0.05, 0.06, 0.026)))
    g.d = np.minimum(g.d, 1.0); from sdf import smin
    g.d = smin(g.d, f.d, 0.012)
    P0 = (HX, HY - 0.045, HZ + GR + 0.028)
    g.add(capsule(P0, WR, 0.036, 0.039), k=0.025, m=0.1); g.add(capsule(WR, EL, 0.039, 0.054), k=0.02, m=0.1)
    return g

def cloth_mat(name, S=8.5):
    """Procedural floral print in object space (Voronoi cell points are the flower centres). Bake it for the game mesh."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; N = nt.nodes.new; L = nt.links.new
    def val(x, sock):
        if isinstance(x, (int, float)): sock.default_value = x
        else: L(x, sock)
    def M(op, a, b_=0.0, c=0.0):
        n = N('ShaderNodeMath'); n.operation = op; val(a, n.inputs[0]); val(b_, n.inputs[1]); val(c, n.inputs[2]); return n.outputs[0]
    def mix(f, a, b_):
        n = N('ShaderNodeMix'); n.data_type = 'RGBA'; val(f, n.inputs[0])
        for x, sk in ((a, n.inputs[6]), (b_, n.inputs[7])):
            if isinstance(x, str): sk.default_value = (*lin(x), 1)
            else: L(x, sk)
        return n.outputs[2]
    def ramp(f, stops):
        n = N('ShaderNodeValToRGB'); r = n.color_ramp; r.interpolation = 'CONSTANT'
        r.elements[0].position = 0; r.elements[0].color = (*lin(stops[0][1]), 1); r.elements[1].position = stops[1][0]; r.elements[1].color = (*lin(stops[1][1]), 1)
        for p, c in stops[2:]: r.elements.new(p).color = (*lin(c), 1)
        L(f, n.inputs[0]); return n.outputs[0]
    tc = N('ShaderNodeTexCoord')
    def cells(scale, rnd, off):
        mp = N('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale,) * 3; mp.inputs['Location'].default_value = (off,) * 3
        L(tc.outputs['Object'], mp.inputs['Vector'])
        v = N('ShaderNodeTexVoronoi'); v.voronoi_dimensions = '3D'; v.feature = 'F1'; v.inputs['Scale'].default_value = 1.0; v.inputs['Randomness'].default_value = rnd
        L(mp.outputs['Vector'], v.inputs['Vector'])
        d = N('ShaderNodeVectorMath'); d.operation = 'SUBTRACT'; L(mp.outputs['Vector'], d.inputs[0]); L(v.outputs['Position'], d.inputs[1])
        xyz = N('ShaderNodeSeparateXYZ'); L(d.outputs[0], xyz.inputs[0]); col = N('ShaderNodeSeparateXYZ'); L(v.outputs['Color'], col.inputs[0])
        ang = M('ADD', M('ARCTAN2', xyz.outputs[0], xyz.outputs[2]), M('MULTIPLY', col.outputs[0], 6.28))
        return v.outputs['Distance'], ang
    base = '#1b6f7c'
    d2, a2 = cells(S * 2.6, 0.9, 3.7)                                    # small cream blossoms
    t2 = M('DIVIDE', d2, M('MULTIPLY', 0.30, M('ADD', 0.72, M('MULTIPLY', 0.28, M('ABSOLUTE', M('COSINE', M('MULTIPLY', a2, 2.5)))))))
    bgc = ramp(t2, [(0, '#f2a43a'), (0.30, '#fff1d6'), (0.86, '#125058'), (1.0, base)])
    d, a = cells(S, 0.5, 0.0)                                            # peonies with leaves
    t = M('DIVIDE', d, M('MULTIPLY', 0.34, M('ADD', 0.82, M('MULTIPLY', 0.18, M('ABSOLUTE', M('COSINE', M('MULTIPLY', a, 2.5)))))))
    lobe = M('POWER', M('MAXIMUM', M('COSINE', M('ADD', M('MULTIPLY', a, 1.5), 0.9)), 0.0), 0.6)
    tl = M('DIVIDE', M('DIVIDE', d, 0.34), M('ADD', 0.9, M('MULTIPLY', lobe, 0.62)))
    leaf = ramp(tl, [(0, '#79c08a'), (0.90, '#79c08a'), (0.93, '#0f4f4a'), (1.0, base)])
    c = mix(M('LESS_THAN', tl, 1.0), bgc, leaf)
    fl = ramp(t, [(0, '#ffd866'), (0.17, '#c8405f'), (0.29, '#fbb7c4'), (0.60, '#d95c80'), (0.65, '#f48ea6'), (0.93, '#8d2346')])
    c = mix(M('LESS_THAN', t, 1.0), c, fl)
    at = N('ShaderNodeAttribute'); at.attribute_name = 'Col'
    mx = N('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
    L(c, mx.inputs[6]); L(at.outputs['Color'], mx.inputs[7]); L(mx.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .62; b.inputs['Sheen Weight'].default_value = .35; b.inputs['Specular IOR Level'].default_value = .3
    return m

def shade(ob, g, base, dark, radii=(0.012, 0.035, 0.08), pw=1.0):
    P = bl.co(ob); N = bl.nrm(ob); ao = (g.ao(P, N, radii) ** pw)[:, None]
    bl.set_col(ob, np.array(lin(dark))[None] * (1 - ao) + np.array(lin(base))[None] * ao)

def fillet(pts, r, n=6):
    pts = [np.asarray(p, np.float32) for p in pts]; out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a = pts[i] - unit(pts[i] - pts[i - 1]) * r; b = pts[i] + unit(pts[i + 1] - pts[i]) * r
        for t in np.linspace(0, 1, n): out.append((1 - t) ** 2 * a + 2 * t * (1 - t) * pts[i] + t * t * b)
    out.append(pts[-1]); return np.array(out, np.float32)

def clean(P):
    P = np.asarray(P, np.float32); return P[~np.isnan(P).any(1)]

def build(low=None):
    """low: dict of tri targets per part, or None for full sculpt resolution."""
    L = low or {}
    root = bpy.data.objects.new('ahma', None); bpy.context.scene.collection.objects.link(root)
    def empty(name, parent, loc=(0, 0, 0)):
        e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e); e.parent = parent; e.location = loc; return e
    he = empty('head_pivot', root, HEAD); he.rotation_euler = (math.radians(-7), math.radians(3), math.radians(-4))
    hobjs = head.build(he, L.get('head'), L.get('hair'))
    red = bl.mat('red_trim', col='#c4202b', rough=.45, spec=.5)

    # blouse
    bg = bl.cached(blouse_grid, CONST); blouse = bl.mk('blouse', *bg.mesh(), root)
    if 'blouse' in L: bl.decimate(blouse, L['blouse'])
    shade(blouse, bg, '#ffffff', '#3a3566')
    bl.use(blouse, cloth_mat('floral'))
    trims = []
    th = np.linspace(0, 2 * np.pi, 64, endpoint=False); dr = np.stack([np.sin(th), np.cos(th), 0 * th], 1).astype(np.float32)
    c = np.array((BC[0], BC[1], HEM + 0.009), np.float32)
    hem = clean(bg.ray(c + dr * 0.7, -dr, 0.7)); trims.append(bl.tube_mesh('hem_pipe', hem + dr[:len(hem)] * 0.002, 0.009, closed=True, res=1))
    n = unit((0, 0.10, 1)); u = unit(np.cross(n, (0, 1, 0))); v = np.cross(n, u)
    th2 = np.linspace(0, 2 * np.pi, 48, endpoint=False)
    col = np.array((0, 0.0, 1.30)) + n * 0.027 + 0.128 * (np.cos(th2)[:, None] * u + np.sin(th2)[:, None] * v)
    trims.append(bl.tube_mesh('collar_pipe', col.astype(np.float32), 0.008, closed=True, res=1))
    for sx in (1, -1):
        m = np.array((sx, 1, 1), np.float32); D = FD * m; Pc = CF * m + D * 0.052
        a = unit(np.cross(D, (0, 0, 1))); b = np.cross(D, a)
        rd = np.cos(th2)[:, None] * a + np.sin(th2)[:, None] * b
        ring = clean(bg.ray(Pc + rd * 0.2, -rd, 0.2))
        trims.append(bl.tube_mesh('cuff_pipe', ring, 0.009, closed=True, res=1))
    pl = bl.smooth_path([(0.0, 1.268), (0.06, 1.235), (0.13, 1.18), (0.185, 1.11), (0.205, 1.02), (0.21, 0.9), (0.215, 0.75), (0.22, HEM + 0.01)], 40)
    O = np.stack([-pl[:, 0], 0 * pl[:, 0] + 0.8, pl[:, 1]], 1)      # closes toward her left (-X)
    hit = clean(bg.ray(O, np.array((0, -1, 0), np.float32), 0.9))
    trims.append(bl.tube_mesh('placket', hit + np.array((0, 0.002, 0), np.float32), 0.0075, res=1))
    for i in (4, 11, 18, 25):
        p = hit[i]; nn = bg.normal(p[None])[0]; t = unit(hit[i + 1] - hit[i - 1]); bb = unit(np.cross(nn, t))
        bar = np.stack([p + nn * 0.004 + bb * s for s in np.linspace(-0.034, 0.034, 6)])
        bar[[0, -1]] -= nn * 0.004
        trims.append(bl.tube_mesh('frog', bar, 0.0065, res=1))
        k = bl.prim('knot', 'primitive_uv_sphere_add', None, segments=10, ring_count=6, radius=0.0135, location=tuple(p + nn * 0.008)); trims.append(k)
    tr = bl.join(trims, 'blouse_trim'); tr.parent = root; bl.use(tr, red)

    # slacks
    sg = bl.cached(slacks_grid, CONST); slacks = bl.mk('slacks', *sg.mesh(), root)
    if 'slacks' in L: bl.decimate(slacks, L['slacks'])
    shade(slacks, sg, '#34364f', '#0d0d18'); bl.use(slacks, bl.mat('slacks', rough=.7, sheen=.25, spec=.3))

    # per-side parts (+X built, -X mirrored by a negative-scale empty)
    skin = bl.mat('skin_body', rough=.5, sss=.18, spec=.4)
    sideR = empty('side_R', root); sideL = empty('side_L', root); sideL.scale = (-1, 1, 1)
    hg = bl.cached(hand_grid, CONST); V, T, Q = hg.mesh()
    kill = (V - EL) @ FD < 0.07; V, T, Q = bl.prune(V, T, Q, kill)
    hand = bl.mk('hand', V, T, Q, sideR)
    if 'hand' in L: bl.decimate(hand, L['hand'])
    shade(hand, hg, '#dfa57f', '#9c4636', (0.006, 0.015, 0.035)); bl.use(hand, skin)
    fp = empty('foot_pivot', sideR, (0.17, 0.02, 0)); fp.rotation_euler = (0, 0, math.radians(-9))
    off = np.array((0.17, 0.02, 0), np.float32)
    fg = bl.cached(foot_grid, CONST); V, T, Q = fg.mesh(); foot = bl.mk('foot', V - off, T, Q, fp)
    if 'foot' in L: bl.decimate(foot, L['foot'])
    P = bl.co(foot) + off; ao = fg.ao(P, bl.nrm(foot), (0.004, 0.012, 0.03))[:, None]
    bl.set_col(foot, np.array(lin('#9c4636'))[None] * (1 - ao) + np.array(lin('#dfa57f'))[None] * ao); bl.use(foot, skin)
    so = bl.cached(sole_grid, CONST); V, T, Q = so.mesh(); sole = bl.mk('slipper_sole', V - off, T, Q, fp)
    if 'sole' in L: bl.decimate(sole, L['sole'])
    slip = bl.mat('slipper', col='#d8261c', rough=.5, spec=.4); bl.use(sole, slip)
    straps = []
    for path in ([(0.146, 0.196), (0.128, 0.15), (0.108, 0.095), (0.093, 0.045)], [(0.146, 0.196), (0.178, 0.165), (0.215, 0.11), (0.238, 0.05)]):
        xy = bl.smooth_path([(a, b, 0) for a, b in path], 14)[:, :2]
        O = np.c_[xy, np.full(len(xy), 0.25, np.float32)]; D = np.array((0, 0, -1), np.float32)
        z = np.fmax(np.nan_to_num(fg.ray(O, D, 0.25)[:, 2], nan=0), np.nan_to_num(so.ray(O, D, 0.25)[:, 2], nan=0.03))
        pts = np.c_[xy, z + 0.006]; pts[-1, 2] = 0.03; pts[0, 2] -= 0.004
        straps.append(bl.tube_mesh('strap', pts - off, 0.0085, res=1))
    st = bl.join(straps, 'slipper_strap'); st.parent = fp; bl.use(st, slip)
    fpl = empty('foot_pivot_L', sideL, fp.location); fpl.rotation_euler = fp.rotation_euler
    for ob in (hand, foot, sole, st):
        d = bpy.data.objects.new(ob.name + '_L', ob.data); bpy.context.scene.collection.objects.link(d)
        d.parent = sideL if ob is hand else fpl
    jade = bl.mat('jade', col='#35b07a', rough=.18, sss=.3, coat=.6, spec=.6)
    bc = WR - FD * 0.045
    bang = bl.prim('jade_bangle', 'primitive_torus_add', sideL, major_radius=0.056, minor_radius=0.0125, major_segments=28, minor_segments=8, location=tuple(bc))
    from mathutils import Vector
    bang.rotation_euler = Vector(tuple(float(q) for q in FD)).to_track_quat('Z', 'Y').to_euler()
    bl.use(bang, jade)

    walker(root)
    return root, hobjs

def walker(root):
    alu = bl.mat('aluminium', col='#cfd4db', rough=.28, metal=1.0)
    rub = bl.mat('rubber', col='#3b3d46', rough=.75, spec=.3)
    redp = bl.mat('basket_red', col='#d8261c', rough=.35, spec=.5, coat=.3)
    A, R, B = [], [], []
    def leg(sx, top, foot):
        top = np.array(top, np.float32); foot = np.array(foot, np.float32); f = lambda z: top + (foot - top) * (top[2] - z) / top[2]
        A.append(bl.tube_mesh('leg_lo', np.stack([f(0.27), f(0.04)]), 0.0125, res=1))
        A.append(bl.tube_mesh('leg_collar', np.stack([f(0.262), f(0.232)]), 0.021, res=1))
        R.append(bl.tube_mesh('ferrule', np.stack([f(0.075), f(0.05), f(0.0)]), 0.02, res=1, radii=[0.9, 1.0, 1.35]))
        k = bl.prim('pin', 'primitive_uv_sphere_add', None, segments=8, ring_count=4, radius=0.006, location=tuple(f(0.20) + np.array((sx * 0.012, 0, 0)))); A.append(k)
        return f
    for sx in (1, -1):
        x = sx * HX; TB = (x, 0.28, HZ); TF = (x, 0.57, HZ); B0 = (sx * 0.365, 0.19, 0); F0 = (sx * 0.365, 0.72, 0)
        fb = leg(sx, TB, B0); ff = leg(sx, TF, F0)
        A.append(bl.tube_mesh('frame', fillet([fb(0.25), TB, TF, ff(0.25)], 0.06, 8), 0.017, res=2))
        A.append(bl.tube_mesh('brace', np.stack([fb(0.40), ff(0.40)]), 0.013, res=1))
        R.append(bl.tube_mesh('grip', np.array([(x, 0.325, HZ), (x, 0.335, HZ), (x, 0.52, HZ), (x, 0.53, HZ)], np.float32), GR, res=2, radii=[1.12, 1.0, 1.0, 1.12]))
    ffR = lambda z: np.array((HX, 0.57, HZ)) + (np.array((0.365, 0.72, 0)) - np.array((HX, 0.57, HZ))) * (HZ - z) / HZ
    for z in (0.66, 0.42):
        p = ffR(z); A.append(bl.tube_mesh('cross', np.array([(-p[0], p[1], z), (p[0], p[1], z)], np.float32), 0.015, res=1))
    # wire basket hung on the top crossbar
    y0 = ffR(0.66)[1] + 0.03; y1 = y0 + 0.23; zt, zb, hw = 0.70, 0.45, 0.25
    def loop(z, ins, r):
        pts = fillet([(0, y0 + ins, z), (hw - ins, y0 + ins, z), (hw - ins, y1 - ins, z), (-hw + ins, y1 - ins, z), (-hw + ins, y0 + ins, z), (0, y0 + ins, z)], 0.035, 5)[:-1]
        B.append(bl.tube_mesh('rim', pts, r, closed=True, res=1)); return pts
    top = loop(zt, 0, 0.009); bot = loop(zb, 0.022, 0.007)
    for f in (0.33, 0.66): loop(zt + (zb - zt) * f, 0.022 * f, 0.0045)
    def resample(P, n):
        P = np.vstack([P, P[:1]]); s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        t = np.linspace(0, s[-1], n, endpoint=False); return np.stack([np.interp(t, s, P[:, i]) for i in range(3)], 1)
    for a, b in zip(resample(top, 44), resample(bot, 44)): B.append(bl.tube_mesh('wire', np.stack([a, b]), 0.0042, res=0))
    for x in np.linspace(-hw + 0.06, hw - 0.06, 9): B.append(bl.tube_mesh('floor', np.array([(x, y0 + 0.022, zb), (x, y1 - 0.022, zb)], np.float32), 0.0042, res=0))
    for y in np.linspace(y0 + 0.06, y1 - 0.06, 3): B.append(bl.tube_mesh('floor', np.array([(-hw + 0.022, y, zb), (hw - 0.022, y, zb)], np.float32), 0.0042, res=0))
    for x in (-0.14, 0.14):
        B.append(bl.tube_mesh('hook', bl.smooth_path([(x, y0, zt), (x, y0 - 0.02, zt + 0.004), (x, y0 - 0.05, 0.685), (x, y0 - 0.052, 0.64)], 10), 0.007, res=1))
    w = bl.join(A, 'walker_frame'); w.parent = root; bl.use(w, alu)
    r = bl.join(R, 'walker_rubber'); r.parent = root; bl.use(r, rub)
    b = bl.join(B, 'walker_basket'); b.parent = root; bl.use(b, redp)
    # tissue packets (the hawker-centre seat chope)
    tis = bl.mat('tissue', col='#f3f1ea', rough=.4, coat=.4); band = bl.mat('tissue_band', col='#2f7fc4', rough=.4, coat=.4)
    for i, (x, y, z, rz, rx) in enumerate(((-0.10, y0 + 0.11, zb + 0.03, 12, 0), (0.05, y0 + 0.12, zb + 0.035, -20, 8), (-0.02, y0 + 0.11, zb + 0.085, 35, -6))):
        for nm, sc, mt in (('tissue', (0.075, 0.05, 0.022), tis), ('tissue_band', (0.03, 0.0515, 0.0235), band)):
            c = bl.prim(nm, 'primitive_cube_add', root, size=2, location=(x, y, z)); c.scale = sc
            c.rotation_euler = (math.radians(rx), 0, math.radians(rz))
            with bl.ctx(c): bpy.ops.object.transform_apply(scale=True)
            bv = c.modifiers.new('b', 'BEVEL'); bv.width = 0.012 if nm == 'tissue' else 0.004; bv.segments = 2; bl.apply_mod(c, bv); bl.smooth(c); bl.use(c, mt)
