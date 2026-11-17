"""Ah Ma head family, built in head-local metres (origin = skull centre, face toward +Y)."""
import bpy, math, numpy as np
from sdf import *
import bl
from bl import lin, hexs

ER = 0.068
def EC(sx): return np.array((sx * 0.115, 0.196, 0.005), np.float32)
EW, EHU, EHL, ETILT = 50., 27., 17., 4.
MZ, MHW, SM = -0.160, 0.082, 0.006
CONST = repr((ER, EC(1).tolist(), EW, EHU, EHL, ETILT, MZ, MHW, SM))
DEG = math.pi / 180
def mx(*a):
    r = a[0]
    for b in a[1:]: r = np.maximum(r, b)
    return r

def zl(x): return MZ + SM * np.minimum(np.abs(x) / MHW, 1.3) ** 2
def lip_top(x):
    q = np.clip(1 - (x / MHW) ** 2, 0, 1); return zl(x) + 0.019 * q ** 0.6 * (1 - 0.22 * np.exp(-(x / 0.014) ** 2))
def lip_bot(x):
    q = np.clip(1 - (x / MHW) ** 2, 0, 1); return zl(x) - 0.025 * q ** 0.55
def lip_mask(x, z, e=0.004):
    return sstep(-e, e, z - lip_bot(x)) * sstep(-e, e, lip_top(x) - z) * sstep(1.02, 0.9, np.abs(x) / MHW)

def eye_frame(sx):
    f = np.array((sx * 0.10, 1, 0), np.float32); f /= np.linalg.norm(f)
    o = sx * np.array((f[1], -f[0], 0), np.float32)   # outer (lateral) direction
    return f, o

def eye_ang(sx, x, y, z):
    c = EC(sx); f, o = eye_frame(sx)
    vx, vy, vz = x - c[0], y - c[1], z - c[2]
    dist = np.sqrt(vx * vx + vy * vy + vz * vz) + 1e-9
    vf = vx * f[0] + vy * f[1]; vo = vx * o[0] + vy * o[1]
    az = np.arctan2(vo, vf) / DEG; el = np.arcsin(np.clip(vz / dist, -1, 1)) / DEG
    t = ETILT * DEG
    return dist, vf, az * math.cos(t) + el * math.sin(t), -az * math.sin(t) + el * math.cos(t)

def lid_curves(az):
    q = 1 - (az / EW) ** 2; a = np.abs(q)
    return EHU * np.sign(q) * a ** 0.75, -EHL * np.sign(q) * a ** 0.9

def eye_open(sx):
    def fn(x, y, z):
        dist, vf, az, el = eye_ang(sx, x, y, z); up, lo = lid_curves(az)
        return np.maximum(np.maximum(el - up, lo - el) * DEG * ER, np.maximum((ER - 0.025) - dist, -vf))
    c = EC(sx); return custom(fn, c - (ER + 0.04), c + (ER + 0.04))

def head_grid():
    g = Grid((-0.37, -0.36, -0.47), (0.37, 0.40, 0.37), 0.0025)
    g.add(ellipsoid((0, -0.02, 0.04), (0.29, 0.31, 0.29)))
    g.add(ellipsoid((0, 0.03, -0.12), (0.228, 0.25, 0.19)), k=0.10)
    g.add(ellipsoid((0, 0.205, -0.155), (0.115, 0.09, 0.08)), k=0.06)      # muzzle
    g.add(sphere((0, 0.215, -0.252), 0.06), k=0.05)                         # chin
    g.add(ellipsoid((0, 0.08, -0.285), (0.15, 0.13, 0.06)), k=0.06)          # soft under-chin
    g.add(capsule((0, -0.04, -0.2), (0, -0.07, -0.47), 0.105, 0.11), k=0.05)
    for sx in (1, -1):
        g.add(sphere((sx * 0.148, 0.175, -0.08), 0.10), k=0.08)             # cheek
        g.add(sphere((sx * 0.115, 0.16, -0.21), 0.05), k=0.07)              # jowl
        g.add(ellipsoid((sx * 0.2, 0.12, -0.03), (0.07, 0.09, 0.05)), k=0.05)
        g.cut(sphere((sx * 0.115, 0.335, 0.012), 0.075), k=0.05)            # socket
        g.add(capsule((sx * 0.045, 0.262, 0.088), (sx * 0.2, 0.2, 0.09), 0.03, 0.026), k=0.045)
        R = rot('z', sx * 25)
        g.add(ellipsoid((sx * 0.30, -0.03, -0.035), (0.022, 0.05, 0.085), R), k=0.02)
        g.cut(ellipsoid((sx * 0.325, -0.03, -0.02), (0.016, 0.028, 0.045), R), k=0.012)
        g.add(sphere((sx * 0.296, -0.012, -0.118), 0.028), k=0.02)
    # nose
    n = Grid((-0.09, 0.2, -0.13), (0.09, 0.40, 0.05), 0.0025)
    n.add(capsule((0, 0.272, 0.012), (0, 0.325, -0.058), 0.02, 0.034))
    n.add(sphere((0, 0.332, -0.062), 0.039), k=0.02)
    for sx in (1, -1): n.add(sphere((sx * 0.04, 0.302, -0.072), 0.029), k=0.02)
    g.add(custom(lambda x, y, z: n.sample(np.stack(np.broadcast_arrays(x, y, z), -1).reshape(-1, 3)).reshape(np.broadcast(x, y, z).shape),
                 n.lo + 0.03, n.lo + n.h * n.n - 0.03), k=0.03, m=0.0)
    for sx in (1, -1): g.cut(sphere((sx * 0.021, 0.322, -0.098), 0.013), k=0.008)
    # eyelid shells
    for sx in (1, -1):
        g.add(sphere(EC(sx), ER + 0.012), k=0.022)
    # lips, then wrinkles as frontal displacement
    g.front((-0.1, MZ - 0.04), (0.1, MZ + 0.04), lambda X, Z: -0.0065 * lip_mask(X, Z), ymin=0.15)
    for sx in (1, -1):
        g.groove([(sx * 0.05, -0.058), (sx * 0.083, -0.105), (sx * 0.107, -0.15), (sx * 0.113, -0.195)], 0.0055, 0.0075, ymin=0.12)
        g.groove([(sx * 0.06, -0.056), (sx * 0.115, -0.074), (sx * 0.168, -0.056)], 0.002, 0.008, ymin=0.12)
        for dz in (0.034, 0.008, -0.02):
            g.groove([(sx * 0.188, 0.01), (sx * 0.237, dz)], 0.0028, 0.0045, ymin=0.05)
    g.groove([(-0.13, 0.16), (-0.05, 0.168), (0.05, 0.168), (0.13, 0.16)], 0.0025, 0.007, ymin=0.12)
    g.groove([(-0.1, 0.2), (0, 0.207), (0.1, 0.2)], 0.002, 0.007, ymin=0.12)
    g.groove([(-0.045, MZ - 0.043), (0, MZ - 0.048), (0.045, MZ - 0.043)], 0.004, 0.008, ymin=0.15)
    g.groove([(0, -0.108), (0, -0.14)], 0.0028, 0.008, ymin=0.15)
    # eye openings
    for sx in (1, -1):
        g.cut(sphere(EC(sx), ER + 0.0015), k=0.0)
        g.cut(eye_open(sx), k=0.003)
    # mouth slit and cavity
    def slit(x, y, z):
        return (np.sqrt((x / (MHW * 1.02)) ** 2 + ((z - zl(x)) / 0.006) ** 2 + ((y - 0.28) / 0.06) ** 2) - 1) * 0.006
    g.cut(custom(slit, (-0.1, 0.2, MZ - 0.03), (0.1, 0.36, MZ + 0.03)), k=0.003)
    g.cut(ellipsoid((0, 0.215, MZ - 0.01), (0.07, 0.062, 0.036)), k=0.004)
    return g

def paint_face(path):
    W, H = 1184, 1344
    X = np.linspace(-0.37, 0.37, W, dtype=np.float32)[None, :]; Z = np.linspace(0.37, -0.47, H, dtype=np.float32)[:, None]
    img = np.zeros((H, W, 3), np.float32) + hexs('#dfa57f')
    def blob(cx, cz, s, col, a, sz=None):
        nonlocal img
        w = a * np.exp(-(((X - cx) / s) ** 2 + ((Z - cz) / (sz or s)) ** 2))[..., None]
        img = img * (1 - w) + hexs(col) * w
    blob(0, 0.2, 0.2, '#e9b991', .5, 0.09)                      # lighter forehead
    for sx in (1, -1):
        blob(sx * 0.165, -0.085, 0.06, '#d9705f', .5)            # blush
        blob(sx * 0.115, 0.0, 0.085, '#c9806a', .35, 0.05)       # warm eye area
        blob(sx * 0.33, -0.04, 0.05, '#d57a66', .5, 0.1)         # ears
    blob(0, -0.06, 0.035, '#da7a66', .4)                         # nose
    blob(0, -0.26, 0.06, '#d98f74', .3)                          # chin
    blob(0, -0.42, 0.3, '#c98a68', .5, 0.08)                     # neck
    m = lip_mask(X, Z, 0.0025)[..., None]
    lipc = hexs('#b9525a') * (1 - 0.25 * sstep(0.012, 0.0, np.abs(Z - zl(X))))[..., None]
    lipc = lipc + 0.10 * np.exp(-((X / 0.03) ** 2 + ((Z - (MZ - 0.014)) / 0.006) ** 2))[..., None]
    img = img * (1 - 0.92 * m) + lipc * 0.92 * m
    return bl.save_png(path, img)

EXPR = {
    'smile': dict(J=-0.0105, W=0.013, H=0.013, C=0.006, AL=5, AU=1),
    'angry': dict(J=-0.0105, W=-0.004, H=-0.012, BD=0.024, BI=0.010, BO=0.006, AU=7, AL=7, U=-0.002),
    'grin':  dict(J=0.03, U=0.009, W=0.022, H=0.02, C=0.014, AL=15, AU=4, BO=0.006, BD=-0.008),
    'ult':   dict(J=0.075, U=0.012, W=-0.004, H=-0.012, BD=0.022, BI=0.008, BO=0.012, AU=-7, AL=-2),
}

def field(P, e, mode='skin'):
    g = lambda k: e.get(k, 0.0)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]; D = np.zeros_like(P)
    if mode == 'jaw':
        D[:, 2] = -g('J'); D[:, 1] = -0.3 * g('J'); return D
    wf = sstep(0.0, 0.10, y); a = x / MHW; aa = np.abs(a); zline = zl(x)
    low = sstep(0, 1, (zline - z) / (0.0005 + 0.08 * sstep(0.8, 1.25, aa)))
    wj = wf * sstep(0.31, 0.15, np.abs(x)) * sstep(-0.42, -0.31, z)
    D[:, 2] += -g('J') * low * wj; D[:, 1] += -0.3 * g('J') * low * wj
    D[:, 2] += g('U') * (1 - low) * np.exp(-((z - zline) / 0.04) ** 2) * np.clip(1 - (a / 1.25) ** 2, 0, 1) * wf
    L = np.where(aa <= 1, a, np.sign(a) * np.exp(-((aa - 1) / 0.9) ** 2)); gz = np.exp(-((z - zline) / 0.06) ** 2) * wf
    D[:, 0] += g('W') * L * gz; D[:, 2] += g('H') * L * L * gz; D[:, 1] += -0.45 * np.abs(g('W') * L * gz)
    for sx in (1, -1):
        c = np.exp(-(((x - sx * 0.15) ** 2 + (z + 0.075) ** 2) / 0.07 ** 2)) * wf
        D[:, 2] += g('C') * c; D[:, 1] += 0.35 * g('C') * c
    ax = np.abs(x); wb = np.exp(-((z - 0.105) / 0.045) ** 2) * wf * sstep(0.27, 0.2, ax); t = np.clip((ax - 0.04) / 0.16, 0, 1)
    D[:, 2] += wb * (-g('BD') * (1 - t) + g('BO') * t); D[:, 0] += -np.clip(x / 0.04, -1, 1) * g('BI') * wb * (1 - t)
    D[:, 1] += 0.25 * abs(g('BD')) * (1 - t) * wb
    Q = P + D
    for sx in (1, -1):
        c = EC(sx); f, o = eye_frame(sx); axv = np.array((-f[1], f[0], 0), np.float32)
        v = P - c; dist = np.linalg.norm(v, axis=1) + 1e-9; vf = v @ f
        el = np.arcsin(np.clip(v[:, 2] / dist, -1, 1)) / DEG
        w = sstep(1.55 * ER, 1.22 * ER, dist) * sstep(0.0, 0.25, vf / dist) * sstep(2, 9, np.abs(el))
        th = (np.where(el > 0, g('AU'), -g('AL')) * w * DEG)[:, None]
        vr = v * np.cos(th) + np.cross(axv[None], v) * np.sin(th) + axv[None] * (v @ axv)[:, None] * (1 - np.cos(th))
        m = (w > 0)[:, None]
        Q = np.where(m, c + vr + D * (1 - w[:, None]), Q)
    return Q - P

def add_keys(ob, mode='skin'):
    P = bl.co(ob); ob.shape_key_add(name='Basis')
    for nm, e in EXPR.items():
        k = ob.shape_key_add(name=nm); k.data.foreach_set('co', (P + field(P, e, mode)).ravel())

def set_expr(objs, name):
    for ob in objs:
        if ob.data.shape_keys:
            for k in ob.data.shape_keys.key_blocks[1:]: k.value = 1.0 if k.name == name else 0.0

def brow_grid():
    hg = bl.cached(head_grid, CONST)
    g = Grid((-0.24, 0.15, 0.06), (0.24, 0.34, 0.15), 0.002)
    for sx in (1, -1):
        xs = np.linspace(0.038, 0.208, 10); t = (xs - 0.038) / 0.17
        zs = 0.094 + 0.026 * np.sin(np.pi * t ** 0.75) ** 1.0 * (1 - 0.35 * t) + 0.004 * t
        hit = hg.ray(np.stack([sx * xs, np.full_like(xs, 0.5), zs], 1), [(0, -1, 0)], 0.5)
        pts = hit + np.array((0, -0.004, 0), np.float32)
        r = 0.0135 * (1 - t) ** 0.6 * (0.75 + 0.25 * np.sin(np.pi * np.clip(t * 1.6, 0, 1))) + 0.004
        g.add(tube(pts, r), m=0.01)
    return g

def lash_grid():
    g = Grid((-0.2, 0.17, -0.05), (0.2, 0.30, 0.06), 0.0015)
    for sx in (1, -1):
        def fn(x, y, z, sx=sx):
            dist, vf, az, el = eye_ang(sx, x, y, z); up, lo = lid_curves(az)
            up = np.where(az > 0, np.maximum(up, 1.0 + 0.25 * (az - EW)), up)
            th = 1.5 + 5.0 * sstep(-EW - 3, -EW + 30, az) * sstep(EW + 12, EW - 12, az)
            return mx(np.abs(dist - (ER + 0.0105)) - 0.006, (el - up - th) * DEG * ER, (up - 1.6 - el) * DEG * ER,
                      (az - EW - 12) * DEG * ER, (-EW - 3 - az) * DEG * ER, -vf)
        c = EC(sx); g.add(custom(fn, c - 0.085, c + 0.085), m=0.0)
    return g

def teeth_grid():
    g = Grid((-0.09, 0.17, MZ - 0.05), (0.09, 0.29, MZ + 0.03), 0.0015)
    def arch(rad, z0, z1, cy=0.197):
        def fn(x, y, z):
            rho = np.sqrt(x * x + (y - cy) ** 2); th = np.arctan2(x, y - cy) / DEG
            d = mx(np.abs(rho - rad) - 0.004, np.abs(z - (z0 + z1) / 2) - abs(z1 - z0) / 2 + 0.003, (np.abs(th) - 62) * DEG * rad) - 0.003
            return d + 0.0012 * np.exp(-(((th + 6.5) % 13 - 6.5) / 1.2) ** 2)
        return custom(fn, (-0.09, 0.17, min(z0, z1) - 0.01), (0.09, 0.29, max(z0, z1) + 0.01))
    g.add(arch(0.076, MZ + 0.018, MZ - 0.013), m=0); u = Grid.__new__(Grid); u.__dict__.update(g.__dict__); u.d = g.d.copy()
    g.d[:] = 1.0; g.add(arch(0.07, MZ - 0.017, MZ - 0.04), m=0)
    return u, g

def hair_thr(az):   # az degrees from front, returns min elevation of the hairline
    return np.interp(az, [0, 30, 60, 76, 86, 106, 120, 180], [38, 36, 22, 8, 15, 15, -18, -32])

def hair_grid():
    g = Grid((-0.43, -0.45, -0.24), (0.43, 0.43, 0.47), 0.003)
    C = np.array((0, -0.02, 0.04), np.float32); rad = np.array((0.29, 0.31, 0.29), np.float32)
    def region(x, y, z):
        vx, vy, vz = x - C[0], y - C[1], z - C[2] + 0.04; rr = np.sqrt(vx * vx + vy * vy + vz * vz) + 1e-9
        el = np.arcsin(np.clip(vz / rr, -1, 1)) / DEG; az = np.arctan2(np.abs(vx), vy) / DEG
        return (hair_thr(az) - el) * DEG * rr
    cap = ellipsoid(C, rad * 1.045)
    g.add(custom(lambda x, y, z: smax(cap.fn(x, y, z), region(x, y, z), 0.02), cap.lo, cap.hi))
    rng = np.random.default_rng(7); N = 250; i = np.arange(N) + 0.5
    ph = np.arccos(1 - 2 * i / N); th = np.pi * (1 + 5 ** 0.5) * i
    dirs = np.stack([np.sin(ph) * np.cos(th), np.sin(ph) * np.sin(th), np.cos(ph)], 1)
    def curl(c, r, a, w, phase):
        e1 = np.cross(a, (0.3, 0.5, 0.8)); e1 /= np.linalg.norm(e1); e2 = np.cross(a, e1)
        def fn(x, y, z):
            vx, vy, vz = x - c[0], y - c[1], z - c[2]; dist = np.sqrt(vx * vx + vy * vy + vz * vz) + 1e-9
            ux, uy, uz = vx / dist, vy / dist, vz / dist
            th_ = np.arccos(np.clip(ux * a[0] + uy * a[1] + uz * a[2], -1, 1))
            ph_ = np.arctan2(ux * e2[0] + uy * e2[1] + uz * e2[2], ux * e1[0] + uy * e1[1] + uz * e1[2])
            return dist - r + 0.13 * r * (0.5 + 0.5 * np.cos(2 * ph_ - w * th_ + phase)) ** 2
        return custom(fn, c - r, c + r)
    for d in dirs:
        el = math.asin(d[2]) / DEG; az = math.atan2(abs(d[0]), d[1]) / DEG
        if el < hair_thr(az) + 4: continue
        r = 0.05 + 0.02 * rng.random() + 0.012 * max(d[2], 0)
        c = (C + np.array((0, 0, -0.04)) + d * rad + d * 0.35 * r).astype(np.float32)
        t = rng.normal(size=3); t -= d * (t @ d); t /= np.linalg.norm(t)
        tilt = math.radians(rng.uniform(0, 55)); a = d * math.cos(tilt) + t * math.sin(tilt)
        g.add(curl(c, r, a, rng.uniform(6, 8) * rng.choice([-1, 1]), rng.uniform(0, 6.28)), k=0.012, m=0.03)
    return g

def build(parent, head_tris=None, hair_tris=None):
    objs = {}
    hg = bl.cached(head_grid, CONST)
    V, T, Q = hg.mesh(); kill = np.zeros(len(V), bool)
    for sx in (1, -1):
        v = V - EC(sx); d = np.linalg.norm(v, axis=1); f, _ = eye_frame(sx)
        kill |= (d < ER + 0.004) & ((v @ f) / d < math.cos(64 * DEG))
    V, T, Q = bl.prune(V, T, Q, kill)
    head = bl.mk('head', V, T, Q, parent)
    hi = bl.mk('head_hi', V, T, Q, parent) if head_tris else None
    if head_tris: bl.decimate(head, head_tris)
    P = bl.co(head); N = bl.nrm(head); ao = hg.ao(P, N) ** 0.9
    col = lin('#a8433a')[None] * (1 - ao[:, None]) + ao[:, None]
    cav = ((P[:, 0] / 0.074) ** 2 + ((P[:, 1] - 0.215) / 0.066) ** 2 + ((P[:, 2] - MZ + 0.01) / 0.04) ** 2 < 1) & (P[:, 1] < 0.272)
    col[cav] = (0.16, 0.035, 0.04)
    sock = np.zeros(len(P), bool)
    for sx in (1, -1): sock |= np.linalg.norm(P - EC(sx), axis=1) < ER + 0.003
    col[sock] *= 0.55
    bl.set_col(head, col, alpha=sstep(-0.02, 0.07, P[:, 1])); bl.set_uv(head, np.stack([(P[:, 0] + 0.37) / 0.74, (P[:, 2] + 0.47) / 0.84], 1))
    tex = paint_face(bl.HERE + '/tex_face.png')
    bl.use(head, bl.mat('skin', tex=tex, flat='#dfa57f', rough=.48, sss=.18, spec=.4))
    if hi: bl.bake(hi, head, bl.HERE + '/tex_head', 2048, ext=0.008)
    add_keys(head); objs['head'] = head

    bg = bl.cached(brow_grid, CONST); brow = bl.mk('brows', *bg.mesh(), parent); bl.decimate(brow, 300)
    bl.use(brow, bl.mat('brow', col='#5f5b66', rough=.7)); add_keys(brow); objs['brows'] = brow
    lg = bl.cached(lash_grid, CONST); lash = bl.mk('lashes', *lg.mesh(), parent); bl.decimate(lash, 300)
    bl.use(lash, bl.mat('lash', col='#2a1d1c', rough=.6)); add_keys(lash); objs['lashes'] = lash
    ug, lg2 = teeth_grid()
    up = bl.mk('teeth_upper', *ug.mesh(), parent); bl.decimate(up, 350)
    lo = bl.mk('teeth_lower', *lg2.mesh(), parent); bl.decimate(lo, 300); add_keys(lo, 'jaw')
    tm = bl.mat('teeth', col='#efe6d6', rough=.35, spec=.5)
    bl.use(up, tm); bl.use(lo, tm); objs['teeth_upper'] = up; objs['teeth_lower'] = lo
    tg = bl.prim('tongue', 'primitive_uv_sphere_add', parent, segments=16, ring_count=8, radius=1, location=(0, 0.2, MZ - 0.034))
    tg.scale = (0.045, 0.055, 0.012)
    with bl.ctx(tg): bpy.ops.object.transform_apply(location=True, scale=True)
    bl.use(tg, bl.mat('tongue', col='#c4575e', rough=.4)); add_keys(tg, 'jaw'); objs['tongue'] = tg

    for sx in (1, -1):
        e = bl.prim('eye_R' if sx > 0 else 'eye_L', 'primitive_uv_sphere_add', parent, segments=24, ring_count=12, radius=ER, location=EC(sx))
        e.rotation_euler = (0, 0, math.radians(-sx * 1.5)); bl.use(e, eye_mat()); objs[e.name] = e

    hgr = bl.cached(hair_grid, CONST); hair = bl.mk('hair', *hgr.mesh(), parent)
    P = bl.co(hair); N = bl.nrm(hair); ao = hgr.ao(P, N, (0.006, 0.02, 0.06))
    t = np.clip(ao * 1.25 - 0.1, 0, 1)[:, None] ** 1.3
    top = np.clip(0.5 + 0.5 * N[:, 2], 0, 1)[:, None]
    col = lin('#3d3a4e')[None] * (1 - t) + (lin('#b9b6c4')[None] * (1 - top) + lin('#f1eef0')[None] * top) * t
    bl.set_col(hair, col); bl.use(hair, bl.mat('hair', rough=.5, spec=.35, sheen=.2))
    if hair_tris:
        lo = bl.mk('hair', *hgr.mesh(), parent); hair.name = 'hair_hi'; bl.decimate(lo, hair_tris); bl.use(lo, hair.data.materials[0])
        bl.bake(hair, lo, bl.HERE + '/tex_hair', 2048, ('DIFFUSE', 'NORMAL'), ext=0.02); hair = lo
    objs['hair'] = hair
    objs.update(glasses(parent))
    gold = bpy.data.materials['gold']
    for sx in (1, -1):
        s = bl.prim('stud', 'primitive_uv_sphere_add', parent, segments=12, ring_count=6, radius=0.014, location=(sx * 0.325, -0.008, -0.125))
        bl.use(s, gold); objs['stud%d' % sx] = s
    return objs

def eye_mat():
    m = bpy.data.materials.get('eye')
    if m: return m
    m = bpy.data.materials.new('eye'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeVectorMath'); nz.operation = 'NORMALIZE'
    dt = nt.nodes.new('ShaderNodeVectorMath'); dt.operation = 'DOT_PRODUCT'; dt.inputs[1].default_value = (0, 1, 0)
    cr = nt.nodes.new('ShaderNodeValToRGB'); r = cr.color_ramp
    stops = [(0.0, '#e9e2d8'), (0.838, '#efe8de'), (0.848, '#1c0e08'), (0.885, '#5a2d14'), (0.952, '#8f4e1e'), (0.966, '#050404')]
    r.elements[0].position = 0; r.elements[0].color = (*lin(stops[0][1]), 1)
    r.elements[1].position = stops[1][0]; r.elements[1].color = (*lin(stops[1][1]), 1)
    for p, c in stops[2:]:
        el = r.elements.new(p); el.color = (*lin(c), 1)
    nt.links.new(tc.outputs['Object'], nz.inputs[0]); nt.links.new(nz.outputs['Vector'], dt.inputs[0])
    nt.links.new(dt.outputs['Value'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.12; b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.03
    return m

def glasses(parent):
    out = {}; gold = bl.mat('gold', col='#d9a441', rough=.28, metal=1.0)
    lens = bl.mat('lens', col='#dff1ff', rough=.03, alpha=.10, spec=1.0)
    RG, parts = 0.092, []
    for sx in (1, -1):
        c = (sx * 0.123, 0.296, -0.008); yaw = math.radians(-sx * 7)
        rim = bl.prim('rim', 'primitive_torus_add', parent, major_radius=RG, minor_radius=0.0065, major_segments=36, minor_segments=6, location=c)
        rim.rotation_euler = (math.pi / 2, 0, yaw); parts.append(rim)
        ln = bl.prim('lens_R' if sx > 0 else 'lens_L', 'primitive_circle_add', parent, radius=RG, vertices=40, fill_type='NGON', location=c)
        ln.rotation_euler = (math.pi / 2, 0, yaw); bl.use(ln, lens); out[ln.name] = ln
        hx = sx * (0.123 + RG * math.cos(math.radians(7)) + 0.004); hy = 0.296 - RG * math.sin(math.radians(7))
        pts = bl.smooth_path([(hx, hy, 0.0), (sx * 0.262, 0.2, 0.012), (sx * 0.302, 0.06, 0.02), (sx * 0.318, -0.045, 0.012), (sx * 0.312, -0.085, -0.03)], 24)
        parts.append(bl.tube_mesh('temple', pts, 0.0045, parent=parent, res=2))
    parts.append(bl.tube_mesh('bridge', bl.smooth_path([(-0.034, 0.304, 0.012), (0, 0.316, 0.03), (0.034, 0.304, 0.012)], 12), 0.0055, parent=parent, res=2))
    for p in parts:
        with bl.ctx(p): bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    fr = bl.join(parts, 'glasses'); bl.use(fr, gold); out['glasses'] = fr
    return out
