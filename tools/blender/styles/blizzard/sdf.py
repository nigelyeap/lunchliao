"""Tiny numpy SDF sculpting kit: dense grid, smooth booleans, OpenVDB meshing (bundled with Blender)."""
import numpy as np, math
import openvdb as vdb

def smin(a, b, k):
    if k <= 0: return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)

def smax(a, b, k): return -smin(-a, -b, k)

def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

def rot(axis, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    if axis == 'x': return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float32)
    if axis == 'y': return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float32)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float32)

class Prim:
    def __init__(s, fn, lo, hi): s.fn = fn; s.lo = np.array(lo, np.float32); s.hi = np.array(hi, np.float32)

def sphere(c, r):
    c = np.array(c, np.float32)
    return Prim(lambda x, y, z: np.sqrt((x - c[0]) ** 2 + (y - c[1]) ** 2 + (z - c[2]) ** 2) - r, c - r, c + r)

def ellipsoid(c, rad, R=None):
    c = np.array(c, np.float32); rad = np.array(rad, np.float32)
    def fn(x, y, z):
        px, py, pz = x - c[0], y - c[1], z - c[2]
        if R is not None:
            px, py, pz = (R[0, 0] * px + R[1, 0] * py + R[2, 0] * pz, R[0, 1] * px + R[1, 1] * py + R[2, 1] * pz,
                          R[0, 2] * px + R[1, 2] * py + R[2, 2] * pz)
        k0 = np.sqrt((px / rad[0]) ** 2 + (py / rad[1]) ** 2 + (pz / rad[2]) ** 2)
        k1 = np.sqrt((px / rad[0] ** 2) ** 2 + (py / rad[1] ** 2) ** 2 + (pz / rad[2] ** 2) ** 2) + 1e-9
        return np.where(k0 < 1, (k0 - 1) * rad.min(), k0 * (k0 - 1) / k1)
    m = rad.max()
    return Prim(fn, c - m, c + m)

def capsule(a, b, ra, rb=None):
    a = np.array(a, np.float32); b = np.array(b, np.float32); rb = ra if rb is None else rb
    ba = b - a; L2 = float(ba @ ba) + 1e-12
    def fn(x, y, z):
        px, py, pz = x - a[0], y - a[1], z - a[2]
        t = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / L2, 0, 1)
        return np.sqrt((px - t * ba[0]) ** 2 + (py - t * ba[1]) ** 2 + (pz - t * ba[2]) ** 2) - (ra + (rb - ra) * t)
    m = max(ra, rb)
    return Prim(fn, np.minimum(a, b) - m, np.maximum(a, b) + m)

def tube(pts, radii):
    """Polyline of tapered capsules."""
    ps = [capsule(pts[i], pts[i + 1], radii[i], radii[i + 1]) for i in range(len(pts) - 1)]
    def fn(x, y, z):
        d = ps[0].fn(x, y, z)
        for p in ps[1:]: d = np.minimum(d, p.fn(x, y, z))
        return d
    return Prim(fn, np.min([p.lo for p in ps], 0), np.max([p.hi for p in ps], 0))

def torus(c, n, R, r):
    c = np.array(c, np.float32); n = np.array(n, np.float32); n /= np.linalg.norm(n)
    def fn(x, y, z):
        px, py, pz = x - c[0], y - c[1], z - c[2]
        h = px * n[0] + py * n[1] + pz * n[2]
        q = np.sqrt(np.maximum(px * px + py * py + pz * pz - h * h, 0))
        return np.sqrt((q - R) ** 2 + h * h) - r
    return Prim(fn, c - (R + r), c + (R + r))

def rbox(c, half, R=None, rnd=0.0):
    c = np.array(c, np.float32); half = np.array(half, np.float32)
    def fn(x, y, z):
        px, py, pz = x - c[0], y - c[1], z - c[2]
        if R is not None:
            px, py, pz = (R[0, 0] * px + R[1, 0] * py + R[2, 0] * pz, R[0, 1] * px + R[1, 1] * py + R[2, 1] * pz,
                          R[0, 2] * px + R[1, 2] * py + R[2, 2] * pz)
        qx, qy, qz = np.abs(px) - half[0] + rnd, np.abs(py) - half[1] + rnd, np.abs(pz) - half[2] + rnd
        return (np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
                + np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0) - rnd)
    m = float(np.linalg.norm(half))
    return Prim(fn, c - m, c + m)

def custom(fn, lo, hi): return Prim(fn, lo, hi)

class Grid:
    def __init__(s, lo, hi, h):
        s.lo = np.array(lo, np.float32); s.h = float(h)
        s.n = (np.ceil((np.array(hi) - s.lo) / h).astype(int) + 1)
        s.ax = [s.lo[i] + h * np.arange(s.n[i], dtype=np.float32) for i in range(3)]
        s.d = np.full(tuple(s.n), 1.0, np.float32)

    def _sl(s, lo, hi, m):
        sl = []
        for i in range(3):
            a = max(0, int(math.floor((lo[i] - m - s.lo[i]) / s.h)))
            b = min(int(s.n[i]), int(math.ceil((hi[i] + m - s.lo[i]) / s.h)) + 1)
            sl.append(slice(a, max(a, b)))
        return tuple(sl)

    def _xyz(s, sl):
        return s.ax[0][sl[0]][:, None, None], s.ax[1][sl[1]][None, :, None], s.ax[2][sl[2]][None, None, :]

    def add(s, p, k=0.0, m=0.06):
        sl = s._sl(p.lo, p.hi, k + m); s.d[sl] = smin(s.d[sl], p.fn(*s._xyz(sl)), k); return s

    def cut(s, p, k=0.0, m=0.02):
        sl = s._sl(p.lo, p.hi, k + m); s.d[sl] = smax(s.d[sl], -p.fn(*s._xyz(sl)), k); return s

    def inter(s, p, k=0.0):
        sl = s._sl(s.lo, s.lo + s.h * s.n, 0); s.d[sl] = smax(s.d[sl], p.fn(*s._xyz(sl)), k); return s

    def apply(s, lo, hi, f):
        """f(d, x, y, z) -> new d on the sub-box."""
        sl = s._sl(lo, hi, 0); s.d[sl] = f(s.d[sl], *s._xyz(sl)); return s

    def mesh(s):
        g = vdb.FloatGrid(1.0); g.copyFromArray(np.ascontiguousarray(s.d))
        P, T, Q = g.convertToPolygons(isovalue=0.0, adaptivity=0.0)
        V = s.lo[None, :] + P.astype(np.float32) * s.h
        T = T.astype(np.int32); Q = Q.astype(np.int32)
        # outward orientation: signed volume must be positive
        tri = np.concatenate([T, Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]]) if len(Q) else T
        a, b, c = V[tri[:, 0]], V[tri[:, 1]], V[tri[:, 2]]
        if float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum()) < 0:
            T = T[:, ::-1]; Q = Q[:, ::-1]
        return V, T, Q

    def sample(s, P):
        q = (np.asarray(P, np.float32) - s.lo) / s.h
        i = np.clip(np.floor(q).astype(int), 0, s.n - 2); f = np.clip(q - i, 0, 1)
        x, y, z = i[:, 0], i[:, 1], i[:, 2]; fx, fy, fz = f[:, 0], f[:, 1], f[:, 2]; d = s.d
        c00 = d[x, y, z] * (1 - fx) + d[x + 1, y, z] * fx; c10 = d[x, y + 1, z] * (1 - fx) + d[x + 1, y + 1, z] * fx
        c01 = d[x, y, z + 1] * (1 - fx) + d[x + 1, y, z + 1] * fx; c11 = d[x, y + 1, z + 1] * (1 - fx) + d[x + 1, y + 1, z + 1] * fx
        return (c00 * (1 - fy) + c10 * fy) * (1 - fz) + (c01 * (1 - fy) + c11 * fy) * fz

    def normal(s, P):
        e = s.h; P = np.asarray(P, np.float32)
        g = np.stack([s.sample(P + np.array(v, np.float32) * e) - s.sample(P - np.array(v, np.float32) * e)
                      for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))], 1)
        return g / (np.linalg.norm(g, axis=1, keepdims=True) + 1e-9)

    def ray(s, O, D, tmax=1.0):
        """First hit along rays from outside. Returns points (nan where no hit)."""
        O = np.asarray(O, np.float32).reshape(-1, 3); D = np.asarray(D, np.float32).reshape(-1, 3)
        D = D / np.linalg.norm(D, axis=1, keepdims=True)
        if len(D) == 1 and len(O) > 1: D = np.repeat(D, len(O), 0)
        st = s.h * 0.6; t = np.zeros(len(O), np.float32); hit = np.full(len(O), np.nan, np.float32)
        prev = s.sample(O)
        for _ in range(int(tmax / st)):
            t2 = t + st; cur = s.sample(O + D * t2[:, None])
            new = np.isnan(hit) & (cur < 0) & (prev >= 0)
            hit[new] = (t + st * prev / (prev - cur + 1e-12))[new]
            t = t2; prev = cur
        return O + D * hit[:, None]

    def ao(s, P, N, radii=(0.012, 0.03, 0.07)):
        a = np.zeros(len(P), np.float32)
        for r in radii: a += np.clip(s.sample(P + N * r) / r, 0, 1)
        return a / len(radii)

def _front(s, lo2, hi2, fn2d, ymin=0.05, ymax=10.0):
    """Frontal-projected displacement: d += fn2d(X, Z) for y in [ymin, ymax]. Positive = groove."""
    sl = s._sl((lo2[0], ymin, lo2[1]), (hi2[0], ymax, hi2[1]), 0)
    X = s.ax[0][sl[0]][:, None]; Z = s.ax[2][sl[2]][None, :]
    s.d[sl] += fn2d(X, Z).astype(np.float32)[:, None, :]; return s
Grid.front = _front

def _groove(s, pts, depth, sigma, ymin=0.05, ymax=10.0):
    pts = np.asarray(pts, np.float32); m = 3 * sigma
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
    def fn(X, Z):
        best = np.full(np.broadcast(X, Z).shape, 1e9, np.float32); u = np.zeros_like(best)
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]; ba = b - a
            t = np.clip(((X - a[0]) * ba[0] + (Z - a[1]) * ba[1]) / (ba @ ba), 0, 1)
            dd = np.sqrt((X - a[0] - t * ba[0]) ** 2 + (Z - a[1] - t * ba[1]) ** 2)
            m_ = dd < best; best = np.where(m_, dd, best); u = np.where(m_, cum[i] + t * (cum[i + 1] - cum[i]), u)
        return depth * np.exp(-(best / sigma) ** 2) * np.sin(np.pi * np.clip(u, 0, 1)) ** 0.6
    return s.front(pts.min(0) - m, pts.max(0) + m, fn, ymin, ymax)
Grid.groove = _groove
