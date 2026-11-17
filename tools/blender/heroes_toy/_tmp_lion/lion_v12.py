"""Lion Dancer (key `lion`), style `toy`. Two-person cloth Singapore lion: big head on the front performer, cloth body over the rear one.
Run: blender -b -P lion.py -- build rig anim export verify shots      (stages run in the order given; `look` renders a quick check of the build)
Axes: Z up, hero faces +Y. Reuses the toy helpers from styles/toy/ahma_toy.py (exec'd) and Pose / rest_mat from heroes/gym.py (imported), like heroes_toy/gym.py.
Rig: the SCALE.md humanoid bones drive the front performer and the head. Extra bones: rear, rthigh/rshin/rfoot .l/.r, tail (rear performer).
`prop` is the jaw hinge, so the upper-body-only attack clip can chomp. Extra clips feed, pounce, shake (the loader looks clips up by name and ignores extras)."""
import bpy, sys, os, math, importlib.util
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HD = os.path.dirname(os.path.abspath(__file__))
RT = os.path.abspath(os.path.join(HD, '..', '..', '..'))
WORK = os.path.join(HD, '_tmp_lion'); SHOTS = os.path.join(RT, 'shots', 'heroes_toy', 'lion'); OUT_GLB = os.path.join(RT, 'assets', 'heroes', 'lion.glb')
os.makedirs(WORK, exist_ok=True); os.makedirs(SHOTS, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build']

sys.path.insert(0, os.path.join(RT, 'tools', 'blender', 'heroes'))
_sp = importlib.util.spec_from_file_location('og_gym', os.path.join(RT, 'tools', 'blender', 'heroes', 'gym.py'))
OG = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(OG)
TOY = os.path.join(RT, 'tools', 'blender', 'styles', 'toy', 'ahma_toy.py')
_src = open(TOY).read().split('# ---------------------------------------------------------------- main')[0]
_src = _src.replace("OUT = os.path.join(ROOT, 'shots', 'styles', 'toy')", "OUT = %r" % SHOTS).replace("TMP = os.path.join(HERE, '_tmp')", "TMP = %r" % WORK)
_src = _src.replace("HERE = os.path.dirname(os.path.abspath(__file__))", "HERE = %r" % os.path.dirname(TOY))
exec(compile(_src, TOY, 'exec'), globals())          # mat, mk, ell, tor, sweep, stage, shoot, row, sph_vf, M, V, Z, H, SC, HERO
ss = OG.smoothstep
HEIGHT = 2.54                                  # 1.88 x size 1.35, feet to horn tip
GS = 1.0                                       # set in stage_build
GS_BODY = 0.9372694419588402                   # v2 scale, frozen so the body frame stays exactly as approved

def openb(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, name)); globals()['SC'] = bpy.context.scene

# ---- cloth print: gold-edged fish scales on red ------------------------------------------------
def scale_image(n=512, k=4):
    v, u = (np.mgrid[0:n, 0:n] + .5) / n
    best = np.full((n, n), 9.0); dd = np.zeros((n, n))
    for j in range(k):
        for i in range(k):
            cx = (i + .5 * (j % 2)) / k; cy = j / k
            dx = ((u - cx + .5) % 1 - .5) * k; dy = ((v - cy + .5) % 1 - .5) * k
            d = np.hypot(dx, dy); m = (d < .62) & (dy < best)
            best[m] = dy[m]; dd[m] = d[m]
    red = np.array(H.srgb('#D8232A')); redl = np.array(H.srgb('#EE4A3C')); gold = np.array(H.srgb('#F7C23E'))
    t = np.clip(dd / .5, 0, 1)[..., None]
    img = redl * (1 - t) + red * t
    img[dd > .46] = red * .8                                     # v6: tone on tone scale edge, one gold dot per scale (pastel ref dots)
    img[dd < .06] = gold
    a = np.concatenate([img, np.ones((n, n, 1))], axis=2).astype(np.float32)
    im = bpy.data.images.new('lion_scales', n, n, alpha=False); im.pixels.foreach_set(a.ravel())
    p = os.path.join(WORK, 'lion_scales.png'); im.filepath_raw = p; im.file_format = 'PNG'; im.save(); im.pack(); return im

def cloth_mat():
    m = mat('cloth', '#D8232A', .62, coat=.08); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = scale_image(); nt.links.new(tx.outputs['Color'], b.inputs['Base Color']); return m

# ---- palette ----------------------------------------------------------------------------------
M.update(
    red=mat('red', '#D8232A', .34, coat=.45), redd=mat('red_dark', '#8E141A', .6),
    gold=mat('gold', '#F5B52A', .3, coat=.5), green=mat('green', '#16A85A', .3, coat=.5),
    fur=mat('fur', '#FFF6E8', .75, sss=.12), eyew=mat('eye_white', '#FFFDF8', .2, coat=.6),
    mirror=mat('mirror', '#EAF1F8', .04, metal=1.0), mouth=mat('mouth', '#4A0810', .6), nostril=mat('nostril', '#3A0D14', .5),
    pants=mat('pants', '#F6BE2C', .85, sss=.08), shoe=mat('shoe', '#1D1A22', .38, coat=.35), sole=mat('sole', '#F3F1F8', .4),
    shirt=mat('shirt', '#2A1F26', .6), blue=mat('blue', '#2F6FD6', .3, coat=.5), black=mat('black', '#1E1A1E', .35, coat=.4),
)
POMC = ['#E8303A', '#FFD23C', '#2BC46A', '#3C8BF0', '#FF7FB6', '#FF8A1E']
for i, hx in enumerate(POMC): M['pom%d' % i] = mat('pom%d' % i, hx, .9, sss=.1)
M['cloth'] = cloth_mat(); M['bib'] = mat('bib', '#B30E28', .7); M['sheet'] = mat('mouth_sheet', '#D8344A', .5, coat=.15)

# ---- shared helpers (gym.py) ------------------------------------------------------------------
def catmull(P, k=6):
    P = [V(p) for p in P]; n = len(P); out = []
    for i in range(n - 1):
        p0 = P[i - 1] if i > 0 else P[0]; p1 = P[i]; p2 = P[i + 1]; p3 = P[i + 2] if i + 2 < n else P[-1]
        for s in range(k):
            t = s / k; out.append(.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1]); return out

def fix_normals(ob):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free(); return ob

def fluff(name, c, axis, R, r, m, bumps=9, seg=54, rseg=8, amp=.38):
    """Puffy fur ring: a torus whose tube swells into `bumps` round tufts."""
    t, u, n = frame_from(axis); c = V(c); vs = []; fs = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; d = t * math.cos(a) + u * math.sin(a); rr = r * (1 + amp * abs(math.sin(bumps * a / 2)) - amp * .5)
        for j in range(rseg):
            b = 2 * math.pi * j / rseg; vs.append(c + d * (R + rr * math.cos(b)) + n * (rr * math.sin(b)))
    for i in range(seg):
        for j in range(rseg):
            fs.append((i * rseg + j, ((i + 1) % seg) * rseg + j, ((i + 1) % seg) * rseg + (j + 1) % rseg, i * rseg + (j + 1) % rseg))
    return mk(name, vs, fs, m)

def blobs(name, pts, m, voxel=.016, tris=1500, smooth=8):
    so = H.Soup(name)
    for p, r in pts: so.sphere(V(p), r, seg=14)
    ob, _ = so.remesh(voxel=voxel, smooth=smooth, smooth_factor=.6, target_tris=tris); H.set_material(ob, m); ob.name = name; return reg(ob)

def frame_mat(t, n, u): return Matrix((t, n, u)).transposed()      # columns t, n, u

# ---------------------------------------------------------------- head geometry (v4: Hok San frame, built at v2 size then shrunk by HK)
# The head is a rigid frame: a boxy superellipsoid shell sheared so the flat forehead leans back (a wedge from the side),
# a square shovel jaw that juts past it, and directional fur clumps (lip hangs down, brows and rim sweep back).
from mathutils.bvhtree import BVHTree
HC = V((0, .10, 2.02)); HR = V((.70, .44, .52)); HX = (4.0, 5.0, 3.5)   # shell centre, radii, superellipse exponent per axis
LEAN, TAPY, TAPX = .34, .20, .08                                     # forehead lean back, depth taper and width flare with height
JC = V((0, .18, 1.69)); JRO = V((.66, .48, .38)); JRI = V((.58, .40, .31)); JE = 3.2   # shovel jaw centre, outer and inner radii, squareness
JP = V((0, -.20, 1.69))                                          # jaw hinge
JAW0 = 22                                                        # rest pose jaw just parted so the teeth read
HK = .78; HPV = V((0, .15, 1.95)); HOFF = V((0, .03, -.11))      # head shrink, its pivot, and a drop so it sits inside the cloth frame
def HS(p): return HPV + (V(p) - HPV) * HK + HOFF
# ---- painted linework: black cloud swirls on gold (face panels) and on orange (cheek balls) ----
def swirl(c, R, turns, s, a0=0.0, tail=1.0):
    N = max(12, int(28 * turns)); P = []
    for k in range(int(10 * tail), 0, -1):
        f = k / 10; a = a0 - s * f * 1.3; r = R * (1 + 1.1 * f); P.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    for k in range(N + 1):
        a = a0 + s * turns * 2 * math.pi * k / N; r = R * (1 - .85 * k / N); P.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return P

def line_image(name, bg, fg, curves, w0, n=512, dots=()):
    v, u = (np.mgrid[0:n, 0:n] + .5) / n; img = np.empty((n, n, 3)); img[:] = np.array(H.srgb(bg))
    for P in list(curves) + [([(x, y), (x, y)], r, c) for x, y, r, c in dots]:
        P, w, col = P if isinstance(P, tuple) else (P, w0, fg); col = np.array(H.srgb(col))
        P = np.array(P); seg = np.linspace(0, len(P) - 1, len(P) * 4)
        xs = np.interp(seg, np.arange(len(P)), P[:, 0]); ys = np.interp(seg, np.arange(len(P)), P[:, 1])
        for x, y in zip(xs, ys):
            i0, i1 = max(0, int((y - w) * n) - 1), min(n, int((y + w) * n) + 2); j0, j1 = max(0, int((x - w) * n) - 1), min(n, int((x + w) * n) + 2)
            if i0 < i1 and j0 < j1: img[i0:i1, j0:j1][(u[i0:i1, j0:j1] - x) ** 2 + (v[i0:i1, j0:j1] - y) ** 2 < w * w] = col
    a = np.concatenate([img, np.ones((n, n, 1))], axis=2).astype(np.float32)
    im = bpy.data.images.new(name, n, n, alpha=False); im.pixels.foreach_set(a.ravel())
    im.filepath_raw = os.path.join(WORK, name + '.png'); im.file_format = 'PNG'; im.save(); im.pack(); return im

def tex_mat(name, im, rough=.32, coat=.5):
    m = mat(name, '#FFFFFF', rough, coat=coat); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = im; nt.links.new(tx.outputs['Color'], b.inputs['Base Color']); return m

PU = (-.85, 1.30, 1.70)                                          # panel UV: x and z mapped into the square texture
def puv(p): return ((p.x - PU[0]) / PU[2], (p.z - PU[1]) / PU[2])

WAVY = (1.775, 1.835)                                            # v6: two wavy crimson bands and a dot row on the muzzle instead of swirls
def puvx(x, z): return ((x - PU[0]) / PU[2], (z - PU[1]) / PU[2])
def panel_curves(): return []                                  # v8: plain gold face, the temples are hidden by the eyes anyway
def panel_dots(): return []
def cheek_curves():
    return [swirl((.5, .5), .2, 1.5, 1, a0=.4)]

M.update(rfur=mat('red_fur', '#9C0410', .92, spec=.25), bfur=mat('black_fur', '#181214', .92),
         iris=mat('iris', '#7A4A1E', .75, spec=.2), eyew=mat('eye_white', '#FFFDF8', .45))
M['panel'] = tex_mat('panel', line_image('lion_panel', '#FFD22E', '#1A1210', panel_curves(), .0065, dots=panel_dots()))
M['cheek'] = tex_mat('cheek', line_image('lion_cheek', '#F48A22', '#1A1210', cheek_curves(), .022))

def ellp(name, c, r, m, seg=16, rot=None):
    vs, fs = sph_vf(seg, seg // 2); c = V(c); R = rot if rot is not None else Matrix.Identity(3)
    P = [c + R @ V((v.x * r[0], v.y * r[1], v.z * r[2])) for v in vs]
    return mk(name, P, fs, m, uvs=[[puv(P[i]) for i in f] for f in fs])

M.update(rfur=mat('red_fur', '#C8102E', .9, spec=.2), bronze=mat('eye_bronze', '#6E3F16', .42, metal=.35),
         eyew=mat('eye_blank', '#D9D0BC', .95, spec=.05))

def sgp(c, e): return math.copysign(abs(c) ** e, c)
def sup(v, ex):                                                  # sphere point pushed out to a superellipsoid (one exponent)
    return v * sum(abs(c) ** ex for c in v) ** (-1 / ex)

def canon(d):                                                    # unit superellipsoid point along d, per-axis exponents HX
    d = V(d).normalized(); lo, hi = 0.0, 2.0
    for _ in range(36):
        s = (lo + hi) / 2
        if sum(abs(d[i] * s) ** HX[i] for i in range(3)) > 1: hi = s
        else: lo = s
    return d * lo

def shell_raw(d):
    q = canon(d)
    p = V((q.x * HR.x * (1 + TAPX * q.z), HC.y + q.y * HR.y * (1 - TAPY * q.z) - LEAN * HR.z * q.z, HC.z + q.z * HR.z))
    p.z = max(p.z, JC.z + .004); return p                         # flat mouth roof that the jaw closes on

SV, SF = sph_vf(44, 22); SP = [shell_raw(v) for v in SV]
BVH = BVHTree.FromPolygons([tuple(p) for p in SP], SF)
def _cast(o, d):
    hit = BVH.ray_cast(V(o), V(d).normalized())[0]
    if hit is None: raise ValueError('shell ray missed %s %s' % (tuple(o), tuple(d)))
    return hit
def _front(fx, z): return _cast((fx, 5, z), (0, -1, 0))

def hsurf(fx, fz, off=0.0):                                      # point on the face front at (x, HC.z + fz), its normal, side and up axes
    z = HC.z + fz; p = _front(fx, z); e = .03
    n = (_front(fx, z + e) - _front(fx, z - e)).cross(_front(fx + e, z) - _front(fx - e, z)).normalized()
    if n.y < 0: n = -n
    t = n.cross(Z).normalized(); u = t.cross(n).normalized(); return p + n * off, n, t, u
def on_head(fx, fz, off=0.0): return hsurf(fx, fz, off)[0]

def shell_pn(d):                                                 # shell point along a direction from the centre, with outward normal
    d = V(d).normalized(); a = frame_from(d)[0]; b = d.cross(a); e = .03; p = shell_raw(d)
    n = (shell_raw(d + a * e) - shell_raw(d - a * e)).cross(shell_raw(d + b * e) - shell_raw(d - b * e)).normalized()
    if n.dot(p - HC) < 0: n = -n
    return p, n

def ring_shell(z, angs, cy, inset=0.0):                          # horizontal ring of shell points (angle 90 deg = front)
    out = []
    for a in angs:
        r = V((math.cos(a), math.sin(a), 0)); out.append(_cast(V((0, cy, z)) + r * 3, -r) - r * inset)
    return out

def sell(name, c, r, m, R, ex=6.0, seg=16):                      # bevelled slab: superellipsoid in frame R
    vs, fs = sph_vf(seg, seg // 2); c = V(c); P = [c + R @ V((q.x * r[0], q.y * r[1], q.z * r[2])) for q in (sup(v, ex) for v in vs)]
    return mk(name, P, fs, m, uvs=[[puv(P[i]) for i in f] for f in fs])

# ---- directional fur: flattened tapering clumps that lie along a flow direction ----
def clump_vf(root, dirv, L, w, out, bend=0.0, flat=.5, n=5, seg=5):
    dirv = V(dirv).normalized(); out = V(out).normalized(); root = V(root)
    P = [root + dirv * (L * k / n) + out * (bend * L * (k / n) ** 2) for k in range(n + 1)]
    vs = [root - dirv * (w * .3)]; fs = []; rings = []
    for k in range(n):
        t = k / n; T = (P[k + 1] - P[k]).normalized(); S = out.cross(T)
        if S.length < 1e-5: S = frame_from(T)[0]
        S.normalize(); Nn = T.cross(S); r = w * min(1.0, (t + .25) / .4) * math.sqrt(max(0.0, 1 - t * t))      # round lobe with a blunt tip
        rings.append(len(vs)); vs += [P[k] + (S * math.cos(a) + Nn * (math.sin(a) * flat)) * r for a in [2 * math.pi * i / seg for i in range(seg)]]
    vs.append(P[n]); tip = len(vs) - 1
    for i in range(seg): fs.append((0, rings[0] + (i + 1) % seg, rings[0] + i))
    for j in range(n - 1):
        a, b = rings[j], rings[j + 1]
        for i in range(seg): fs.append((a + i, a + (i + 1) % seg, b + (i + 1) % seg, b + i))
    for i in range(seg): fs.append((rings[-1] + i, rings[-1] + (i + 1) % seg, tip))
    return vs, fs

def clumps(name, specs, m):
    vs = []; fs = []
    for sp in specs:
        v, f = clump_vf(*sp); o = len(vs); vs += v; fs += [tuple(i + o for i in ff) for ff in f]
    return fix_normals(mk(name, vs, fs, m))

def build_shell():
    mi = []
    for f in SF:
        c = sum((SP[i] for i in f), V()) / len(f); q = sum((SV[i] for i in f), V()) / len(f)
        mi.append(1 if c.z < JC.z + .012 else 2 if q.normalized().y > .42 and q.normalized().z < .84 else 0)
    mk('h_shell', SP, SF, [M['rfur'], M['mouth'], M['panel']], mat_idx=mi, uvs=[[puv(SP[i]) for i in f] for f in SF])

def revolve(name, prof, c, mats, seg=40, mrun=None, je=2.0):
    """prof: list of (rx, ry, dz). First and last with rx==0 become poles. Rings are superellipses with exponent je."""
    c = V(c); vs = []; fs = []; mi = []; rings = []
    for rx, ry, dz in prof:
        if rx == 0: vs.append(c + V((0, 0, dz))); rings.append([len(vs) - 1] * seg)
        else:
            rings.append(list(range(len(vs), len(vs) + seg)))
            vs += [c + V((rx * sgp(math.cos(2 * math.pi * i / seg), 2 / je), ry * sgp(math.sin(2 * math.pi * i / seg), 2 / je), dz)) for i in range(seg)]
    for j in range(len(rings) - 1):
        a, b = rings[j], rings[j + 1]
        for i in range(seg):
            q = [a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]]; q = [x for k, x in enumerate(q) if x not in q[:k]]
            fs.append(tuple(q)); mi.append(mrun[j] if mrun else 0)
    return fix_normals(mk(name, vs, fs, mats, mat_idx=mi))

def jring(rx, ry, a): return V((rx * sgp(math.cos(a), 2 / JE), ry * sgp(math.sin(a), 2 / JE), 0))

TONGUE = True
def build_jaw():
    # v6: the mouth is a smooth flat sheet stretched across the jaw frame, like the cloth panel of a real head. No teeth.
    prof = [(0, 0, -.03), (JRI.x * .55, JRI.y * .55, -.024), (JRI.x, JRI.y, .004)]; mr = [2, 2]
    prof.append(((JRI.x + JRO.x) / 2 - .01, (JRI.y + JRO.y) / 2 - .01, .03)); mr.append(1)
    prof.append((JRO.x + .012, JRO.y + .012, .012)); mr.append(1)
    for k in range(0, 7):
        ph = math.radians(95 + 80 * k / 6); prof.append((JRO.x * math.sin(ph), JRO.y * math.sin(ph), JRO.z * math.cos(ph))); mr.append(1 if k == 0 else 0)
    prof.append((0, 0, -JRO.z)); mr.append(0)
    revolve('j_jaw', prof, JC, [M['rfur'], M['gold'], M['sheet']], seg=40, mrun=mr, je=JE)
    if TONGUE: ell('j_tongue', JC + V((0, .12, -.018)), (.27, .24, .035), M['tongue'], seg=20)      # low flat pad lying on the sheet
    sweep('j_lipgold', [JC + jring(JRI.x + .03, JRI.y + .03, math.radians(a)) + V((0, 0, .02)) for a in np.linspace(-14, 194, 34)], .045, M['gold'], seg=7)
    # one clean fur roll round the outside of the lower jaw, kept below the gold lip so the mouth reads
    sweep('j_lipfur', [JC + jring(JRO.x + .02, JRO.y + .02, math.radians(a)) + V((0, 0, -.10)) for a in np.linspace(-14, 194, 40)], .14, M['rfur'], seg=10)

def build_head():
    build_shell(); build_jaw()
    sweep('h_lip', ring_shell(JC.z + .05, [math.radians(a) for a in np.linspace(-10, 190, 34)], .10, inset=-.015), .045, M['gold'], seg=7)
    # flat forehead plate, painted gold, rising from the nose to the mirror
    p, n, t, u = hsurf(0, .10); sell('h_plate', p + n * .02, (.25, .06, .28), M['panel'], frame_mat(t, n, u), ex=5)
    angs = list(np.linspace(-12, 192, 36)); ring = ring_shell(JC.z + .12, [math.radians(a) for a in angs], .10, inset=-.03)
    fr = [math.sin(math.radians(max(0, min(180, a)))) ** 2 for a in angs]
    sweep('h_lipfur', [q + V((0, .03 * f, .03 * f)) for q, f in zip(ring, fr)], [.07 + .03 * f for f in fr], M['rfur'], seg=10)
    # mirror high on the forehead: raised gold frame, red fur ring of short radial clumps
    p, n, t, u = hsurf(0, .36); MC = p + n * .09; fr = frame_mat(t, n, u)
    sell('h_mirror_frame', MC, (.15, .04, .15), M['gold'], fr, ex=2.4, seg=20)
    ell('h_mirror', MC + n * .025, (.10, .02, .10), M['mirror'], rot=fr, seg=20)
    tor('h_mirror_rim', MC + n * .035, n, .11, .02, M['gold'], seg=28, rseg=5)
    specs = []
    for k in range(14):
        a = 2 * math.pi * k / 14; d = t * math.cos(a) + u * math.sin(a); specs.append((MC + d * .14 - n * .01, d + n * .3, .11, .075, n, 0.0))
    clumps('h_mirror_fur', specs, M['rfur'])
    q, qn = shell_pn((0, .45, 1)); FC = q + qn * .08
    for k in range(7):
        a = 2 * math.pi * k / 7; d = V((math.cos(a), 0, math.sin(a))); ell('h_petal', FC + d * .07 + V((0, .02, 0)), (.07, .04, .07), M['rfur'], seg=8)
    ell('h_flower', FC + V((0, .05, 0)), (.045, .04, .045), M['gold'], seg=12)
    # eyes: dark bronze ball, gold rim, pale socket ring (lids, pupil, brows live in the keyed face mesh)
    for s in (-1, 1):
        c, f, t, u = eye_frame(s)
        ell('h_eyeball', c, (ER, ER, ER), M['eyew'], seg=20)       # v9: blank ball, black rim, two more black rings on the ball (costume target eye)
        tor('h_socket', c - f * .03, f, ER + .035, .04, M['bfur'], seg=22, rseg=5)
        for rr, mr_ in ((.112, .018), (.062, .015)):
            tor('h_eyering', c + f * (math.sqrt(ER * ER - rr * rr) - .004), f, rr, mr_, M['bfur'], seg=20, rseg=4)
    # black fur fringe hanging under each eye along the cheek
    base = []; specs = []
    for s in (-1, 1):
        row = []
        for k in range(8):
            p, n, _, _ = hsurf(s * (.13 + .07 * k), EZs - .26 + .10 * (k / 7) ** 1.5, .02); row.append(p)
            specs.append((p, -Z + n * .35, .13, .085, n, .05))
        sweep('h_blackbase', row, .05, M['bfur'], seg=6)
    clumps('h_blackfur', specs, M['bfur'])
    # red fur: a front rim sweeping back, a second row behind it, a ring round the back, big lobes on the top corners
    specs = []
    for row, (yd, n, L, w) in enumerate(((.30, 20, .26, .16), (-.15, 16, .28, .16), (-.65, 12, .26, .15))):
        for i in range(n):
            a = 2 * math.pi * i / n if row == 2 else math.radians(-18 + 216 * (i + .5 * row) / n)
            p, nn = shell_pn((math.cos(a), yd, math.sin(a)))
            if p.z < JC.z + .06: continue
            rad = V((math.cos(a), 0, math.sin(a))); specs.append((p - nn * .02, rad * .3 + V((0, -.9, .05)), L, w, nn, -.06))
    for s in (-1, 1):
        for d, L, w in (((.70, .05, .82), .36, .16), ((.55, .15, .92), .32, .15), ((.82, -.05, .62), .32, .14), ((.62, -.25, .85), .30, .14), ((.40, .0, .98), .26, .12)):
            p, nn = shell_pn((s * d[0], d[1], d[2])); specs.append((p - nn * .02, V((s * .45, -.7, .55)), L, w * 1.15, nn, .05))
    clumps('h_rimfur', specs, M['rfur'])
    col = [shell_pn((math.cos(a) * .95, -.9, math.sin(a) * .85))[0] for a in np.linspace(0, 2 * math.pi, 33)]
    sweep('h_collar', [q + V((0, -.01, 0)) for q in col], .03, M['gold'], seg=6, round_caps=False)

# ---------------------------------------------------------------- face (one mesh, keyed): lids, pupils, brows, cheek balls
ER = .16; EXs, EZs = .44, .16
def eye_frame(s):                                                # eyes set high and wide, turned out to the sides
    p, n, t, u = hsurf(s * EXs, EZs)
    f = (n + V((s * .30, .05, .04))).normalized(); t2 = f.cross(Z).normalized(); u2 = t2.cross(f).normalized()
    return p + f * .03, f, t2, u2

FM = ['rfur', 'gold', 'cheek']
_I = dict(lu=56, ll=34, tilt=16, bp=26, bti=-8, ps=1.0, cz=0.0, jaw=0)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'lu': 101, 'll': 80, 'bp': 22},
    'mouth_open': {**_I, 'jaw': 20},
    'smile': {**_I, 'll': 66, 'lu': 50, 'tilt': 0, 'bp': 6, 'bti': 4, 'cz': .03, 'jaw': 4},
    'angry': {**_I, 'lu': 78, 'll': 46, 'tilt': 30, 'bp': 40, 'bti': -22, 'ps': .8, 'jaw': 8},
    'grin': {**_I, 'lu': 66, 'll': 76, 'tilt': 4, 'bp': 4, 'bti': 0, 'cz': .04, 'jaw': 12},
    'ult': {**_I, 'lu': 58, 'll': 42, 'tilt': 26, 'bp': 34, 'bti': -20, 'ps': .7, 'cz': .02, 'jaw': 18},
}

def face_geo(e):
    vs = []; fs = []; mi = []; uv = []
    def add(v, f, m, uvv=None):
        o = len(vs); vs.extend(v); uv.extend(uvv or [(0, 0)] * len(v))
        fs.extend([tuple(i + o for i in ff) for ff in f]); mi.extend(m if isinstance(m, list) else [FM.index(m)] * len(f))
    def ellv(c, r, fr, seg=16):
        sv, sf = sph_vf(seg, seg // 2); return [c + fr @ V((q.x * r[0], q.y * r[1], q.z * r[2])) for q in sv], sf, sv
    def cap(c, f, t, u, ro, ri, ph_end, down, rot, seg=16, nr=4):
        ax = -u if down else u; Rm = Matrix.Rotation(rot, 3, f)
        def d(ph, az): return Rm @ (ax * math.cos(ph) + (t * math.cos(az) + f * math.sin(az)) * math.sin(ph))
        azs = [2 * math.pi * i / seg for i in range(seg)]; v = [c + Rm @ ax * ro]; rings = []
        for k in range(1, nr + 1):
            ph = ph_end * k / nr; rings.append(len(v)); v += [c + d(ph, a) * ro for a in azs]
        rings.append(len(v)); v += [c + d(ph_end + math.radians(5), a) * (ro + ri) / 2 for a in azs]
        for k in range(nr, 0, -1):
            ph = ph_end * k / nr; rings.append(len(v)); v += [c + d(ph, a) * ri for a in azs]
        v.append(c + Rm @ ax * ri); last = len(v) - 1; f_ = []; m_ = []
        for i in range(seg): f_.append((0, rings[0] + i, rings[0] + (i + 1) % seg)); m_.append(0)
        for j in range(len(rings) - 1):
            a, b = rings[j], rings[j + 1]; edge = j in (nr - 1, nr)
            for i in range(seg): f_.append((a + i, b + i, b + (i + 1) % seg, a + (i + 1) % seg)); m_.append(0)
        for i in range(seg): f_.append((last, rings[-1] + (i + 1) % seg, rings[-1] + i)); m_.append(0)
        add(v, f_, m_)
    for s in (-1, 1):
        c, f, t, u = eye_frame(s)
        cap(c, f, t, u, ER + .06, ER + .022, math.radians(e['lu']), False, math.radians(-s * e['tilt']))
        cap(c, f, t, u, ER + .055, ER + .02, math.radians(e['ll']), True, 0.0)
        fr = Matrix((t, f, u)).transposed(); ps = e['ps']
        # heavy brow: red fur clumps along an arc over the eye, sweeping up and back
        for i in range(9):
            q = i / 4 - 1; ph = math.radians(e['bp'] + e['bti'] * q)
            dc = (u * math.cos(ph) + f * math.sin(ph) + t * (s * q * 1.05)).normalized(); base = c + dc * .25 + u * (.06 + .05 * max(0, q)) + f * .04
            v, f_ = clump_vf(base, -f * .35 + u * .55 + t * (s * .40 * (q + .4)), .30 - .05 * abs(q), .16, dc, .12); add(v, f_, 'rfur')
        # orange cheek ball with a black swirl on the nose bridge, between and just below the eyes
        p, n_, t_, u_ = hsurf(s * .20, -.01, .11)
        v, f_, sv = ellv(p + V((0, 0, e['cz'])), (.13, .13, .13), Matrix((t_, n_, u_)).transposed(), 16)
        add(v, f_, 'cheek', [(.5 + s * .5 * q.x, .5 + .5 * q.z) for q in sv])
    return vs, fs, mi, uv

KEYS = ['blink', 'mouth_open', 'smile', 'angry', 'grin', 'ult']
def build_face():
    vs, fs, mi, uv = face_geo(EXPR['idle'])
    ob = mk('h_face', vs, fs, [M[k] for k in FM], mat_idx=mi, uvs=[[uv[i] for i in f] for f in fs]); fix_normals(ob); ob.shape_key_add(name='Basis')
    for name in KEYS:
        k = ob.shape_key_add(name=name); k.data.foreach_set('co', [c for v in face_geo(EXPR[name])[0] for c in v])
        k.value = 0.0
    return ob

# ---------------------------------------------------------------- body: cloth, performers, tail
Y0, Y1 = -.08, -1.40
def cloth_dims(s):
    top = float(np.interp(s, [0, .1, .3, .55, .8, 1], [2.10, 1.96, 1.76, 1.62, 1.54, 1.44]))   # front end tucks under the smaller head
    w = float(np.interp(s, [0, .2, .45, .7, .85, 1], [.50, .62, .68, .68, .66, .62]))
    puff = math.sin(math.pi * ss(.2, 1.0, s)) ; top += .05 * puff; w += .04 * puff          # v6: the back billows up between the dancers
    rump = 1 - math.sqrt(max(0.0, 1 - (max(0.0, s - .76) / .24) ** 2)); w *= 1 - .8 * rump; top -= .30 * rump      # v6: the rump rounds over and closes small
    hem = float(np.interp(s, [0, .5, 1], [.62, .56, .58]))
    return top, w, hem

# v6 billowy cape: three tiers a side, shingled from the spine down to the hem and running the whole length (the pastel ref's stacked
# wavy ruffle bands). Each tier flares out to its lower edge, then the next starts tucked in under it. Every edge ripples in and out and
# scallops up and down along the body, more towards the back, so the cloth reads as flowing. Widths never go inside the v5 cloth.
NS = 30
ZT, NG = 1.24, 28                                                # v12 gown front: top tucks under the jaw, columns round the front
def gown_pt(a, z):
    t = (z - .62) / (ZT - .62); c, s = math.cos(a), max(0.0, math.sin(a)); e = .6
    rx = .50 + (.07 - .05 * t) * s; ry = .66 - .07 * t
    return V((rx * math.copysign(abs(c) ** e, c), Y0 + ry * s ** e, z))
TB = (0.0, .36, .68, 1.0)                                        # tier edges as a fraction of the way from spine to hem
TF = ((.25, .5, .75, 1.0), (.1, .45, .85, 1.0), (.1, .45, .85, 1.0))
TA, TR, TS, TK, TP = (.03, .045, .06), (.02, .035, .055), (.02, .035, .045), (19.0, 23.0, 17.0), (0.0, 2.1, 4.0)   # flare, ripple, scallop, wave number, phase
SIDE = [(k, f) for k in range(3) for f in TF[k]]                 # spine outwards
DESC = [(1, k, f) for k, f in reversed(SIDE)] + [(0, 0, 0.0)] + [(-1, k, f) for k, f in SIDE]      # right hem, over the spine, left hem
NP = len(DESC)
GOLDQ = {i for i in range(NP - 1) if {DESC[i][2], DESC[i + 1][2]} == {.85, 1.0}}      # gold strip just above each tier edge
ROPES = [i for i, (sd, k, f) in enumerate(DESC) if f == 1.0 and k < 2]

def cloth_prof(j):
    s = j / NS; top, w, hem = cloth_dims(s); y = Y0 + (Y1 - Y0) * s; hv = min(.85 * w, top - hem - .08, .42); zc = top - hv
    B = [(w, hem + (zc - hem) * k / 20) for k in range(20)] + [(w * math.cos(a), zc + hv * math.sin(a)) for a in np.linspace(0, math.pi, 61)]
    B += [(-w, hem + (zc - hem) * k / 20) for k in range(19, -1, -1)]; B = np.array(B)
    L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(B, axis=0).T))]); L /= L[-1]
    at = lambda q: V((float(np.interp(q, L, B[:, 0])), 0, float(np.interp(q, L, B[:, 1]))))
    live = ss(0, .14, s) * (.45 + .55 * ss(1.0, .9, s)); back = 1 + .5 * s; P = []
    for sd, k, f in DESC:
        t = TB[k] + (TB[k + 1] - TB[k]) * f; q = (1 - sd * t) / 2; p = at(q)
        tg = (at(min(1, q + .004)) - at(max(0, q - .004))).normalized(); n = V((tg.z, 0, -tg.x))
        if n.dot(V((p.x, 0, p.z - hem - .2))) < 0: n = -n
        down = tg * (1 if sd < 0 else -1)
        kw, g = (k - 1, .85) if (k and f < .2) else (k, f * f if k == 0 else f)       # the tucked top of a tier rides with the edge above it
        th = TK[kw] * y + TP[kw] + sd * .9
        p = p + n * (TA[k] * f ** 1.3 * ss(0, .18, s) * back + TR[kw] * g * live * back * math.sin(th)) + down * (TS[kw] * g * live * math.sin(th + .8))
        p.y = y; P.append(p)
    return P

def build_cloth():
    outer = [cloth_prof(j) for j in range(NS + 1)]; TH = .018
    inner = []
    for P in outer:
        Q = []
        for i in range(NP):
            d = P[min(i + 1, NP - 1)] - P[max(i - 1, 0)]; nrm = V((d.z, 0, -d.x)).normalized()
            if i == 0 or i == NP - 1: nrm = V((math.copysign(1, P[i].x), 0, 0))
            Q.append(P[i] - nrm * TH * (1 if nrm.dot(V((P[i].x, 0, P[i].z - 1.0))) > 0 else -1))
        inner.append(Q)
    vs = [p for P in outer for p in P] + [p for P in inner for p in P]; IO = (NS + 1) * NP
    o = lambda j, i: j * NP + i; n_ = lambda j, i: IO + j * NP + i
    fs = []; mi = []; uvs = []
    arc = [[0.0] + list(np.cumsum([(P[i + 1] - P[i]).length for i in range(NP - 1)])) for P in outer]
    arc = [arc[NS // 2]] * (NS + 1)                               # one u per column, so the print does not shear row to row
    T = .30; TU = arc[0][-1] / round(arc[0][-1] / T)             # v12: whole print repeats from hem to hem, so the gown front matches both sides
    vc = [[0.0] * NP]
    for j in range(NS): vc.append([(Y0 - outer[j + 1][i].y)] * NP)      # v6: straight rows so the print does not shear across the ripples
    for j in range(NS):
        for i in range(NP - 1):
            fs.append((o(j, i), o(j, i + 1), o(j + 1, i + 1), o(j + 1, i))); lo = i == 0 or i == NP - 2; band = i < 2 or i >= NP - 3
            mi.append(1 if i in GOLDQ else 0)
            uvs.append([(arc[j][i] / TU, vc[j][i] / T), (arc[j][i + 1] / TU, vc[j][i + 1] / T), (arc[j + 1][i + 1] / TU, vc[j + 1][i + 1] / T), (arc[j + 1][i] / TU, vc[j + 1][i] / T)])
            fs.append((n_(j, i), n_(j + 1, i), n_(j + 1, i + 1), n_(j, i + 1))); mi.append(2); uvs.append([(0, 0)] * 4)
        for i in (0, NP - 1):                                    # hem edge strips
            fs.append((o(j, i), o(j + 1, i), n_(j + 1, i), n_(j, i))); mi.append(1); uvs.append([(0, 0)] * 4)
    for i in range(NP - 1):                                      # front cut edge (hidden under the head)
        fs.append((o(0, i), n_(0, i), n_(0, i + 1), o(0, i + 1))); mi.append(2); uvs.append([(0, 0)] * 4)
    for i in range(NP // 2):                                     # close the narrow rump seam at the back
        a, b = o(NS, i), o(NS, i + 1); c, d = o(NS, NP - 2 - i), o(NS, NP - 1 - i)
        if b == c: fs.append((a, b, d))
        else: fs.append((a, b, c, d))
        mi.append(0); uvs.append([(vs[k].x / .40, vs[k].z / .40) for k in fs[-1]])
    ob = mk('cloth', vs, fs, [M['cloth'], M['gold'], M['redd'], M['cloth']], uvs=uvs, mat_idx=mi); fix_normals(ob)
    # v12: the same garment carries on round the front performer and closes under the jaw. Its end columns sit on the cape's front edge,
    # rows match the lowest tier (gold strip above the hem), the print mirrors at the front centre.
    zr = [outer[0][i].z for i in range(4)] + [ZT]; A = [math.pi * i / NG for i in range(NG + 1)]
    zt = [ZT + .24 * ss(.34, .02, gown_pt(a, ZT).y - Y0) for a in A]      # the top climbs behind the jaw corners to meet the cape, no dark notch there
    gv = [gown_pt(a, z) for z in zr[:4] for a in A] + [V((q.x, q.y, zt[i])) for i, q in enumerate(gown_pt(a, ZT) for a in A)]; gf = []; gm = []; guv = []
    mid = [gown_pt(a, .93) for a in A]; d = [0.0] + list(np.cumsum([(mid[i + 1] - mid[i]).length for i in range(NG)]))
    gvv = [-min(x, d[-1] - x) / T for x in d]; gu = [arc[0][i] / TU for i in range(4)] + [(arc[0][3] + ZT - zr[3]) / TU]
    for r in range(4):
        for i in range(NG):
            gf.append((r * (NG + 1) + i, r * (NG + 1) + i + 1, (r + 1) * (NG + 1) + i + 1, (r + 1) * (NG + 1) + i)); gm.append(1 if r == 0 else 0)
            u1 = [gu[r + 1] + (zt[k] - ZT) / TU * (r == 3) for k in (i + 1, i)]
            guv.append([(gu[r], gvv[i]), (gu[r], gvv[i + 1]), (u1[0], gvv[i + 1]), (u1[1], gvv[i])])
    fix_normals(mk('gown', gv, gf, [M['cloth'], M['gold']], uvs=guv, mat_idx=gm))
    gout = lambda q, k: q + V((q.x, q.y - .1, 0)).normalized() * k
    ghem = [gown_pt(a, zr[0]) for a in A[1:-1]]
    for i in ROPES:                                              # wavy fur rope along the lower edge of each upper tier
        pts = [outer[j][i] + V((outer[j][i].x, 0, outer[j][i].z - .9)).normalized() * .01 for j in range(NS + 1)]
        sweep('clothband', pts, [.05 * (1 + .2 * math.sin(j * 1.9 + i)) * (.6 + .4 * ss(0, 3, j) * ss(NS, NS - 3, j)) for j in range(NS + 1)], M['fur'], seg=5)
    # fur roll along the hem and up the front edges
    left = [outer[j][-1] for j in range(NS + 1)]; right = [outer[j][0] for j in range(NS + 1)]
    fe = lambda P, idx: [P[k] for k in idx]
    path = ghem + left + list(reversed(right[:-1]))[1:] + ghem[:1]      # v12: one closed hem roll, round the front too
    path = [(gout(p, .012) if p.y > Y0 else p + V((math.copysign(.012, p.x), 0, 0))) + V((0, 0, -.01)) for p in path]
    L = [0.0] + list(np.cumsum([(path[i + 1] - path[i]).length for i in range(len(path) - 1)]))
    dense = []; rad = []
    for k in range(int(L[-1] / .045)):
        x = k * .045; i = min(int(np.searchsorted(L, x)) - 1, len(path) - 2); i = max(i, 0); t = (x - L[i]) / max(1e-6, L[i + 1] - L[i])
        dense.append(path[i].lerp(path[i + 1], t)); rad.append(.05 * (1 + .3 * abs(math.sin(math.pi * x / .135))))
    sweep('hemfur', dense, rad, M['fur'], seg=5)
    # gold zigzag fringe hanging below the hem on the sides and rump
    hem = left[1:] + list(reversed(right)) + ghem + left[:2]
    hem = [(gout(p, .03) if p.y > Y0 else p + V((math.copysign(.03, p.x), 0, 0))) + V((0, 0, -.03)) for p in hem]
    L2 = [0.0] + list(np.cumsum([(hem[i + 1] - hem[i]).length for i in range(len(hem) - 1)])); vs2 = []; fs2 = []
    for k in range(int(L2[-1] / .05)):
        x = k * .05; i = max(0, min(int(np.searchsorted(L2, x)) - 1, len(hem) - 2)); t = (x - L2[i]) / max(1e-6, L2[i + 1] - L2[i])
        q = hem[i].lerp(hem[i + 1], t); vs2 += [q, q + V((math.copysign(.012 * (k % 2), q.x), 0, -.13 if k % 2 else -.06))]
    for k in range(len(vs2) // 2 - 1): fs2.append((2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1))
    mk('fringe', vs2, fs2, M['gold'])
    # lengthwise rows of fur: a mane flowing back from the head along the spine and the shoulders of the cloth
    for k, fa in enumerate((.5,)):
        pts = []
        for j in range(2, NS - 1):
            P = outer[j]; i = int(round(fa * (NP - 1))); pts.append(P[i] + (P[i] - V((0, P[i].y, P[i].z - .3))).normalized() * .02)
        sweep('clothfur', pts, [(.06 if k == 0 else .045) * (1 + .25 * abs(math.sin(i * 1.3 + k))) for i in range(len(pts))], M['fur'], seg=6)

TAIL = [V((0, -1.30, 1.30)), V((0, -1.46, 1.38)), V((0, -1.58, 1.52)), V((0, -1.60, 1.66))]
def build_tail():
    tp = catmull(TAIL, 4); sweep('tail', tp, list(np.linspace(.13, .08, len(tp))), M['red'], seg=16)
    sweep('tail_under', [q + V((0, .05, -.06)) for q in tp[1:-1]], .07, M['fur'], seg=8)
    tor('tail_band', tp[len(tp) // 2], tp[len(tp) // 2 + 1] - tp[len(tp) // 2 - 1], .1, .018, M['gold'], seg=24, rseg=6)
    c = TAIL[-1] + V((0, -.02, .06)); pts = [(c, .1)]
    for a in np.linspace(0, 2 * math.pi, 7, endpoint=False):
        pts.append((c + V((math.cos(a) * .09, -.03 + .03 * math.sin(a), .03 + math.sin(a) * .07)), .07))
    pts.append((c + V((0, -.02, .13)), .07))
    blobs('tail_fur', pts, M['fur'], voxel=.02, tris=400)
    for k, a in enumerate((-.6, 0, .6)): ell('tail_pom', c + V((math.sin(a) * .1, -.04, .16 + .03 * math.cos(a))), (.05, .05, .05), M['pom%d' % (k * 2)], seg=10)

FL = {s: (V((s * .25, .22, .86)), V((s * .32, .32, .50)), V((s * .31, .22, .16))) for s in (-1, 1)}      # front performer hip, knee, ankle
RL = {s: (V((s * .27, -.95, .80)), V((s * .33, -.84, .46)), V((s * .32, -.97, .16))) for s in (-1, 1)}   # rear performer
def cyl_uv(ob, cx, cy, reps, T=.30):                             # wrap the cape scale print round a limb, whole repeats so it has no seam
    me = ob.data; uvl = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        a0 = None
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co; a = math.atan2(co.y - cy, co.x - cx) / (2 * math.pi)
            if a0 is None: a0 = a
            uvl.data[li].uv = ((a + round(a0 - a)) * reps, co.z / T)
    return ob

def build_leg(tag, s, hip, knee, ank):
    pts = catmull([hip, knee, ank], 5); rr = list(np.interp(np.linspace(0, 1, len(pts)), [0, .5, .85, 1], [.17, .16, .15, .12]))
    cyl_uv(sweep(tag + 'pants', pts, rr, M['cloth'], seg=12), knee.x, knee.y, 3)       # v9: trousers in the cape cloth, a fur wave trim at the knee
    for nm, c, R, r in (('ktrim', knee + V((0, 0, .02)), .165, .045), ('cuff', ank + V((0, 0, .05)), .135, .05)):   # v10: the cape's scalloped fur edge with gold piping
        ring = [c + V((R * math.cos(a), R * math.sin(a), .03 * math.sin(3 * a))) for a in np.linspace(0, 2 * math.pi, 16)]
        sweep(tag + nm, ring, r, M['fur'], seg=6, round_caps=False)
        sweep(tag + nm + 'g', [q + V((0, 0, r + .012)) for q in ring], .016, M['gold'], seg=4, round_caps=False)
    x, y = ank.x, ank.y
    ell(tag + 'shoe', (x, y + .07, .075), (.115, .2, .08), M['shoe'], seg=18)
    ell(tag + 'sole', (x, y + .075, .03), (.125, .21, .035), M['sole'], seg=18)
    ell(tag + 'shoetoe', (x, y + .2, .08), (.05, .04, .035), M['gold'], seg=12)

def build_performers():
    for s in (-1, 1):
        build_leg('f_', s, *FL[s]); build_leg('r_', s, *RL[s])
    # v12: a plain human trunk under the gown: hips, chest, shoulders, sleeves going up into the head. The gown hides nearly all of it.
    cyl_uv(ell('f_hips', (0, .20, .89), (.38, .22, .13), M['cloth'], seg=16), 0, .22, 7)
    cyl_uv(ell('torso', (0, .17, 1.02), (.33, .19, .20), M['cloth'], seg=14), 0, .17, 6)
    cyl_uv(ell('shoulders', (0, .17, 1.13), (.42, .17, .09), M['cloth'], seg=14), 0, .17, 6)
    for s in (-1, 1): cyl_uv(sweep('arm', [(s * .37, .17, 1.10), (s * .41, .19, 1.20), (s * .42, .21, 1.27)], [.085, .08, .07], M['cloth'], seg=8), s * .40, .19, 2)
    cyl_uv(ell('r_hips', (0, -.95, .83), (.43, .26, .18), M['cloth'], seg=22), 0, -.95, 7)

# ---------------------------------------------------------------- build stage
def scale_all(f):
    for o in HERO:
        for v in o.data.vertices: v.co *= f
        if o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks:
                for v in kb.data: v.co *= f

def stage_build():
    build_head(); build_face(); build_cloth(); build_tail(); build_performers()
    R0 = Matrix.Rotation(math.radians(-JAW0), 3, 'X')
    for o in HERO:
        if o.name.startswith('j_'):
            for v in o.data.vertices: v.co = R0 @ (v.co - JP) + JP
    for o in HERO:                                    # shrink the whole head (and the face keys) about the neck pivot
        if o.name.startswith(('h_', 'j_')):
            for v in o.data.vertices: v.co = HS(v.co)
            if o.data.shape_keys:
                for kb in o.data.shape_keys.key_blocks:
                    for v in kb.data: v.co = HS(v.co)
    tris = sum(H.tri_count(o) for o in HERO); print('TOY_TRIS', tris, 'objects', len(HERO))
    agg = {}
    for o in HERO: agg[o.name.split('.')[0]] = agg.get(o.name.split('.')[0], 0) + H.tri_count(o)
    print('TOY_TOP', sorted(agg.items(), key=lambda kv: -kv[1])[:20])
    top = max(v.co.z for o in HERO for v in o.data.vertices); gs = GS_BODY; print('[build] raw top', round(top, 3), 'GS', round(gs, 4), 'height', round(top * gs, 3))
    scale_all(gs); open(os.path.join(WORK, 'gs.txt'), 'w').write(repr(gs))
    stage()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'lion_build.blend'))

def load_gs():
    globals()['GS'] = float(open(os.path.join(WORK, 'gs.txt')).read())

def stage_look():
    openb('lion_build.blend'); load_gs(); cam = bpy.data.objects['cam']; SC.eevee.taa_render_samples = 24
    shoot(cam, os.path.join(WORK, 'look_34.png'), 900, 900, 35, 10, (0, -.35, 1.25), 3.8, cam_z=1.6)
    shoot(cam, os.path.join(WORK, 'look_face.png'), 700, 700, 12, 7, (0, .4, 1.85), 1.6)
    shoot(cam, os.path.join(WORK, 'look_side.png'), 900, 700, 90, 10, (0, -.35, 1.25), 3.6, cam_z=1.3)
    e = bpy.data.objects.new('spin', None); SC.collection.objects.link(e)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name != 'cyc': o.parent = e
    e.rotation_euler = (0, 0, math.radians(-150)); bpy.context.view_layer.update()
    shoot(cam, os.path.join(WORK, 'look_back.png'), 700, 700, 0, 10, (0, .2, 1.25), 3.4, cam_z=1.6)

# ---------------------------------------------------------------- rig + weights
def eyepos(s): return HS(eye_frame(s)[0])
BONES = [
    ('root', (0, 0, 0), (0, 0, .25), None), ('hips', (0, .22, .86), (0, .22, 1.0), 'root'), ('spine', (0, .22, 1.0), (0, .22, 1.18), 'hips'),
    ('chest', (0, .22, 1.18), (0, .24, 1.38), 'spine'), ('neck', (0, .24, 1.38), (0, .22, 1.52), 'chest'), ('head', (0, .22, 1.52), (0, .20, 2.40), 'neck'),
    ('eye.l', tuple(eyepos(-1)), tuple(eyepos(-1) + V((0, .08, 0))), 'head'), ('eye.r', tuple(eyepos(1)), tuple(eyepos(1) + V((0, .08, 0))), 'head'),
    # the front performer's arms reach up inside the head to hold it (no visible mesh)
    ('upperarm.l', (-.26, .22, 1.32), (-.32, .38, 1.50), 'chest'), ('lowerarm.l', (-.32, .38, 1.50), (-.28, .34, 1.74), 'upperarm.l'),
    ('hand.l', (-.28, .34, 1.74), (-.26, .36, 1.84), 'lowerarm.l'), ('handslot.l', (-.26, .36, 1.84), (-.26, .44, 1.84), 'hand.l'),
    ('upperarm.r', (.26, .22, 1.32), (.32, .38, 1.50), 'chest'), ('lowerarm.r', (.32, .38, 1.50), (.28, .34, 1.74), 'upperarm.r'),
    ('hand.r', (.28, .34, 1.74), (.26, .36, 1.84), 'lowerarm.r'), ('handslot.r', (.26, .36, 1.84), (.26, .44, 1.84), 'hand.r'),
    ('prop', tuple(HS(JP)), tuple(HS(JP) + V((0, .35, 0))), 'head'),
    ('rear', (0, -.95, .80), (0, -.95, 1.10), 'root'), ('tail', tuple(TAIL[0]), tuple(TAIL[-1]), 'rear'),
]
for s, sd in ((-1, 'l'), (1, 'r')):
    h, k, a = FL[s]; BONES += [('upperleg.' + sd, tuple(h), tuple(k), 'hips'), ('lowerleg.' + sd, tuple(k), tuple(a), 'upperleg.' + sd),
                               ('foot.' + sd, tuple(a), tuple(a + V((0, .12, -.1))), 'lowerleg.' + sd), ('toes.' + sd, tuple(a + V((0, .12, -.1))), tuple(a + V((0, .25, -.11))), 'foot.' + sd)]
    h, k, a = RL[s]; BONES += [('rthigh.' + sd, tuple(h), tuple(k), 'rear'), ('rshin.' + sd, tuple(k), tuple(a), 'rthigh.' + sd),
                               ('rfoot.' + sd, tuple(a), tuple(a + V((0, .2, -.11))), 'rshin.' + sd)]
RIGID = {'eye.l', 'eye.r'}

def make_rig():
    arm = bpy.data.armatures.new('lion_rig'); ob = bpy.data.objects.new('lion_rig', arm); bpy.context.scene.collection.objects.link(ob)
    H.select_only([ob], ob); bpy.ops.object.mode_set(mode='EDIT')
    for name, h, t, parent in BONES:
        b = arm.edit_bones.new(name); b.head = V(h) * GS; b.tail = V(t) * GS
        if parent: b.parent = arm.edit_bones[parent]; b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in arm.bones: b.use_deform = b.name not in RIGID
    return ob

def chain(p, pts, bones, bands):
    pts = [V(q) for q in pts]; best = None; acc = 0.0; cum = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]; d = b - a; L = d.length; t = max(0.0, min(1.0, (p - a).dot(d) / (L * L))); dist = (p - (a + d * t)).length
        if best is None or dist < best[0]: best = (dist, acc + t * L)
        acc += L; cum.append(acc)
    s = best[1]; ws = [1.0]
    for k in range(len(bones) - 1):
        a = ss(cum[k] - bands[k], cum[k] + bands[k], s); last = ws[-1]; ws[-1] = last * (1 - a); ws.append(last * a)
    return dict(zip(bones, ws))

def merge(*ws):
    o = {}
    for w in ws:
        for k, v in w.items(): o[k] = o.get(k, 0) + v
    return o
def scale(w, f): return {k: v * f for k, v in w.items()}

def leg_w(p, front):
    s = -1 if p.x < 0 else 1; sd = 'l' if s < 0 else 'r'; h, k, a = (FL if front else RL)[s]
    if front: w = chain(p, [h + V((0, 0, .1)), k, a, a + V((0, .25, -.1))], ['upperleg.' + sd, 'lowerleg.' + sd, 'foot.' + sd], [.06, .05])
    else: w = chain(p, [h + V((0, 0, .1)), k, a, a + V((0, .25, -.1))], ['rthigh.' + sd, 'rshin.' + sd, 'rfoot.' + sd], [.06, .05])
    if front and p.y > a.y + .14 and p.z < .14:
        wf = w.pop('foot.' + sd, 0); t = ss(.30, .40, p.y - a.y + .2); w['foot.' + sd] = wf * (1 - t); w['toes.' + sd] = w.get('toes.' + sd, 0) + wf * t
    up = ss(h.z - .02, h.z + .08, p.z); return merge(scale(w, 1 - up), scale(front_w(p, False), up) if front else {'rear': up})   # v12: thigh tops give way to the jaw with the trunk

def body_w(p):                                       # cloth, hem fur, spine fur: head at the front, chest in the middle, rear performer behind
    a = ss(-1.05, -.15, p.y); hd = .55 * ss(-.45, -.0, p.y)
    w = {'rear': 1 - a, 'chest': a * (1 - hd), 'head': a * hd}
    if p.y <= Y0: return w
    f = ss(Y0, .10, p.y); return merge(scale(w, 1 - f), scale(front_w(p), f))

def front_w(p, skirt=True):                          # v12 gown front and the trunk under it: the top rides the jaw bone so the open mouth never cuts through it,
    up = ss(.72, 1.14, p.z) if skirt else ss(.60, .98, p.z)      # the trunk gives way sooner, so it never bulges through the folded gown
                              # the hem stays with the hips and swings with the thighs like a skirt
    lg = .7 * ss(1.0, .7, p.z) * ss(.05, .3, p.y) if skirt else 0.0; l = ss(.15, -.15, p.x)
    return {'prop': up, 'upperleg.l': (1 - up) * lg * l, 'upperleg.r': (1 - up) * lg * (1 - l), 'hips': (1 - up) * (1 - lg)}

CLOTHP = ('cloth', 'hemfur', 'clothfur', 'fringe', 'clothband', 'gown')
def weights_for(name, p):
    n = name.split('.')[0]
    if n.startswith('j_'): return {'prop': 1.0}
    if n.startswith('h_'): return {'head': 1.0}
    if n in CLOTHP: return body_w(p)
    if n.startswith('tail'):
        t = ss(-1.28, -1.42, p.y); return {'rear': 1 - t, 'tail': t}
    if n in ('torso', 'shoulders', 'arm', 'f_hips'): return front_w(p, False)
    if n == 'r_hips': return {'rear': 1.0}
    if n.startswith('f_'): return leg_w(p, True)
    if n.startswith('r_'): return leg_w(p, False)
    print('[weights] unclassified', name); return {'hips': 1.0}

def belly_disp(p):                                   # rounds the cloth body out (Belly meter)
    f = ss(.1, -.35, p.y) * ss(-1.42, -.95, p.y); top, w, hem = cloth_dims(min(1, max(0, (p.y - Y0) / (Y1 - Y0))))
    up = ss(hem, top, p.z)
    return V((p.x * .24 * f, 0, (.05 + .06 * up) * f * ss(hem - .05, hem + .3, p.z)))

def stage_rig():
    openb('lion_build.blend'); load_gs(); O = bpy.data.objects
    parts = [o for o in O if o.type == 'MESH' and o.name != 'cyc']
    for o in parts:
        o.data.update()
        for v in o.data.vertices:
            for b, w in weights_for(o.name, v.co / GS).items():
                if w > 1e-3:
                    g = o.vertex_groups.get(b) or o.vertex_groups.new(name=b); g.add([v.index], w, 'REPLACE')
        if o.name.split('.')[0] in CLOTHP:
            g = o.vertex_groups.new(name='_belly'); g.add([v.index for v in o.data.vertices], 1.0, 'REPLACE')
    heads = [o for o in parts if o.name.startswith(('h_', 'j_'))]; heads.sort(key=lambda o: o.name != 'h_face')
    bodies = [o for o in parts if not o.name.startswith(('h_', 'j_'))]
    head = H.join(heads, 'lion_head'); body = H.join(bodies, 'lion_body'); rig = make_rig()
    for o_ in (head, body):                                      # join leaves the UV layer not render-active, so prints sampled texel 0
        if o_.data.uv_layers: o_.data.uv_layers[0].active_render = True; o_.data.uv_layers.active_index = 0
    # jaw keys: every vertex on the prop (jaw) group swings about the hinge by the key's jaw angle
    gi = head.vertex_groups['prop'].index; jv = [v.index for v in head.data.vertices if any(g.group == gi and g.weight > .5 for g in v.groups)]
    kb0 = head.data.shape_keys.key_blocks['Basis']
    for name in KEYS:
        kb = head.data.shape_keys.key_blocks[name]; R = Matrix.Rotation(math.radians(-EXPR[name]['jaw']), 3, 'X'); P = HS(JP) * GS
        for i in jv: kb.data[i].co = R @ (kb0.data[i].co - P) + P
    # belly key on the body
    body.shape_key_add(name='Basis'); kb = body.shape_key_add(name='belly'); kb.value = 0.0; gi = body.vertex_groups['_belly'].index
    for v in body.data.vertices:
        if any(g.group == gi for g in v.groups): kb.data[v.index].co = v.co + belly_disp(v.co / GS) * GS
    body.vertex_groups.remove(body.vertex_groups['_belly'])
    # v12: the gown front rides the jaw bone, so it needs the head's jaw keys too (same names, the game drives every mesh that has `blink`)
    gp = body.vertex_groups['prop'].index
    for name in KEYS:
        kb = body.shape_key_add(name=name); kb.value = 0.0; R = Matrix.Rotation(math.radians(-EXPR[name]['jaw']), 3, 'X'); P = HS(JP) * GS
        for v in body.data.vertices:
            w = sum(g.weight for g in v.groups if g.group == gp)
            if w > 0: kb.data[v.index].co = v.co + w * (R @ (v.co - P) + P - v.co)
    for ob in (head, body):
        ob.parent = rig; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = rig
        for v in ob.data.vertices:
            tot = sum(g.weight for g in v.groups)
            if tot < .5: print('[rig] weak vertex', ob.name, v.index, tot)
    print('[rig] shape keys', [k.name for k in head.data.shape_keys.key_blocks], 'tris', H.tri_count(head), H.tri_count(body))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'lion_rig.blend'))

# ---------------------------------------------------------------- animation (OG.Pose: world-axis rotations stacked down the chain)
AX = lambda ax, d: OG.axis_rot(ax, d)
X_, Y_, Z_ = (1, 0, 0), (0, 1, 0), (0, 0, 1)
KB = ['hips', 'spine', 'chest', 'neck', 'head', 'upperarm.l', 'lowerarm.l', 'hand.l', 'upperarm.r', 'lowerarm.r', 'hand.r',
      'upperleg.l', 'lowerleg.l', 'foot.l', 'upperleg.r', 'lowerleg.r', 'foot.r', 'prop', 'rear', 'tail',
      'rthigh.l', 'rshin.l', 'rfoot.l', 'rthigh.r', 'rshin.r', 'rfoot.r']
LOC = ('hips', 'spine', 'rear')

def put(rig, name, d):
    rig.pose.bones[name].location = OG.rest_mat(rig, name).to_3x3().inverted() @ (V(d) * GS)

# X rotation: + tips an upright bone back (-Y), swings a hanging leg forward (+Y); - opens the jaw (prop points +Y)
def legs(P, s1, s2, amp=34):
    for sd, sg in (('l', 1), ('r', -1)):
        a = s1 * sg; P.rot('upperleg.' + sd, AX(X_, amp * a)); P.rot('lowerleg.' + sd, AX(X_, -50 * max(0.0, -a))); P.rot('foot.' + sd, AX(X_, 12 * max(0.0, -a)))
        b = s2 * sg; P.rot('rthigh.' + sd, AX(X_, amp * b)); P.rot('rshin.' + sd, AX(X_, -50 * max(0.0, -b))); P.rot('rfoot.' + sd, AX(X_, 12 * max(0.0, -b)))

def lion_pose(rig, t, kind):
    P = OG.Pose(rig); s = math.sin(2 * math.pi * t); c = math.cos(2 * math.pi * t)
    if kind == 'idle':                               # head looks around, little jaw flap, breathing, tail sway
        P.rot('chest', AX(X_, 1.5 * s)); P.rot('neck', AX(Z_, 6 * s))
        P.rot('head', AX(Z_, 10 * s) @ AX(X_, -4 * math.sin(4 * math.pi * t)) @ AX(Y_, 4 * c))
        P.rot('prop', AX(X_, -9 * max(0.0, math.sin(2 * math.pi * (t - .55) * 3)) * (.55 <= t < .72)))
        P.rot('tail', AX(Z_, 14 * s) @ AX(X_, -5 * c))
        put(rig, 'hips', (0, 0, .012 * math.sin(4 * math.pi * t))); put(rig, 'rear', (0, 0, .014 * math.sin(4 * math.pi * t + 1.2)))
    elif kind == 'run':                              # both performers run, the rear a quarter cycle behind; head bobs, jaw flaps
        legs(P, s, math.sin(2 * math.pi * t - math.pi / 2))
        P.rot('spine', AX(X_, -5)); P.rot('chest', AX(Z_, 4 * s)); P.rot('head', AX(X_, -7 * math.sin(4 * math.pi * t) + 3) @ AX(Z_, -5 * s))
        P.rot('prop', AX(X_, -10 * abs(s))); P.rot('tail', AX(X_, -12 * math.sin(4 * math.pi * t)) @ AX(Z_, 8 * s))
        put(rig, 'hips', (0, 0, .04 * abs(s) - .015)); put(rig, 'rear', (0, 0, .04 * abs(c) - .015))
    elif kind == 'attack':                           # chomp: rear back with the jaw wide, lunge and snap shut, recover
        if t < .35: u = ss(0, .35, t); lean = 10 * u; jaw = 37 * u; push = -.04 * u
        elif t < .55: u = (t - .35) / .2; lean = 10 - 32 * u; jaw = 37 * (1 - ss(.3, .85, u)); push = -.04 + .26 * u
        else: u = (t - .55) / .45; lean = -22 * (1 - ss(0, 1, u)); jaw = 6 * math.sin(u * math.pi); push = .22 * (1 - ss(0, 1, u))
        P.rot('spine', AX(X_, lean * .3)); P.rot('chest', AX(X_, lean * .3)); P.rot('head', AX(X_, lean * (1.6 if lean > 0 else .6))); P.rot('prop', AX(X_, -jaw))   # v11: head tips up more on the rear back so the wide jaw clears the chest cloth
        put(rig, 'spine', (0, push, -.25 * max(0.0, -lean) / 22 * .3))
    elif kind == 'ult':                              # King of the Jungle: head reared up high, jaw wide, roar
        P.rot('spine', AX(X_, 5)); P.rot('chest', AX(X_, 6)); P.rot('neck', AX(X_, 6)); P.rot('head', AX(X_, 10)); P.rot('prop', AX(X_, -36))
        put(rig, 'spine', (0, 0, .12))
    elif kind == 'feed':                             # Feed the Lion: head low and forward, jaw held wide, a hungry tremble
        P.rot('spine', AX(X_, -10)); P.rot('chest', AX(X_, -8)); P.rot('neck', AX(X_, -6)); P.rot('head', AX(X_, 14 + 2 * s) @ AX(Z_, 3 * math.sin(6 * math.pi * t)))   # v11: body bows, head tips up, so the jaw stays clear of the chest cloth
        P.rot('prop', AX(X_, -30 - 3 * math.sin(6 * math.pi * t))); P.rot('tail', AX(X_, -15) @ AX(Z_, 10 * s))
        for sd in 'lr': P.rot('upperleg.' + sd, AX(X_, 20)); P.rot('lowerleg.' + sd, AX(X_, -38)); P.rot('foot.' + sd, AX(X_, 18))
        put(rig, 'hips', (0, .05, -.12)); put(rig, 'spine', (0, .1, -.05))
    elif kind == 'pounce':                           # crouch, stretch out long through the air, land
        e = ss(.15, .45, t) * (1 - ss(.75, 1, t)); cr = (1 - ss(0, .2, t)) * ss(-.01, .1, t) + ss(.8, 1, t) * (1 - ss(.95, 1.01, t))
        for sd in 'lr':
            P.rot('upperleg.' + sd, AX(X_, 60 * e + 20 * cr)); P.rot('lowerleg.' + sd, AX(X_, -15 * e - 40 * cr))
            P.rot('rthigh.' + sd, AX(X_, -55 * e + 20 * cr)); P.rot('rshin.' + sd, AX(X_, 20 * e - 40 * cr))
        P.rot('spine', AX(X_, -8 * e)); P.rot('head', AX(X_, 8 * e)); P.rot('prop', AX(X_, -26 * e)); P.rot('tail', AX(X_, 35 * e))
        put(rig, 'hips', (0, .3 * e, .35 * e - .12 * cr)); put(rig, 'rear', (0, -.3 * e, .3 * e - .12 * cr))
    elif kind == 'shake':                            # Firecracker Shake: head whips side to side, jaw loose
        d = 1 - ss(.6, 1, t)
        P.rot('chest', AX(Z_, 8 * math.sin(4 * math.pi * t) * d)); P.rot('neck', AX(Z_, 12 * math.sin(4 * math.pi * t - .5) * d))
        P.rot('head', AX(Z_, 26 * math.sin(4 * math.pi * t - 1) * d) @ AX(Y_, 14 * math.sin(4 * math.pi * t - 1) * d))
        P.rot('prop', AX(X_, -22 * abs(math.sin(4 * math.pi * t)) * d)); P.rot('tail', AX(Z_, -25 * math.sin(4 * math.pi * t) * d))
        put(rig, 'hips', (0, 0, .03 * abs(math.sin(4 * math.pi * t)) * d))
    return P

def make_action(rig, name, frames, loop=True):
    act = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act
    for f in range(frames + 1):
        t = (f % frames) / frames if loop else min(f, frames) / frames
        SC.frame_set(f); lion_pose(rig, t, name)
        for n in KB:
            pb = rig.pose.bones[n]; pb.keyframe_insert('rotation_quaternion', frame=f)
            if n in LOC: pb.keyframe_insert('location', frame=f)
    act.frame_range = (0, frames); act.use_frame_range = True; act.use_fake_user = True; return act

CLIPS = [('idle', 60, True), ('run', 24, True), ('attack', 18, False), ('ult', 2, True), ('feed', 30, True), ('pounce', 20, False), ('shake', 18, False)]
def stage_anim():
    openb('lion_rig.blend'); load_gs(); SC.render.fps = OG.FPS; rig = bpy.data.objects['lion_rig']
    acts = [make_action(rig, n, f, loop) for n, f, loop in CLIPS]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'lion_anim.blend')); print('[anim] actions', [a.name for a in acts])

def stage_export():
    openb('lion_anim.blend'); O = bpy.data.objects; rig = O['lion_rig']; OG.reset_pose(rig)
    for ob in (O['lion_head'], O['lion_body']):
        for k in ob.data.shape_keys.key_blocks: k.value = 0.0
    H.select_only([O['lion_head'], O['lion_body'], rig], rig)
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
                              export_animations=True, export_animation_mode='ACTIONS', export_nla_strips=True, export_skins=True, export_def_bones=False,
                              export_morph=True, export_morph_normal=False, export_image_format='AUTO', export_materials='EXPORT', export_texcoords=True,
                              export_normals=True, export_tangents=False, export_all_influences=False, export_optimize_animation_size=True)
    print('[export] wrote', OUT_GLB, os.path.getsize(OUT_GLB) // 1024, 'KB')

def stage_verify():
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps = 30; bpy.ops.import_scene.gltf(filepath=OUT_GLB)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('Icosphere')]
    rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    lo = V((1e9,) * 3); hi = V((-1e9,) * 3)
    for o in meshes:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co; lo = V(map(min, lo, w)); hi = V(map(max, hi, w))
    print(f'[verify] tris {sum(H.tri_count(o) for o in meshes)}; X {lo.x:.3f}..{hi.x:.3f} height(Z after import) {hi.z - lo.z:.3f} depth(Y) {lo.y:.3f}..{hi.y:.3f}')
    print('[verify] bones', [b.name for b in rig.data.bones])
    for o in meshes:
        if o.data.shape_keys: print('[verify] morphs on', o.name, [k.name for k in o.data.shape_keys.key_blocks])
        print(f'[verify] {o.name}: {H.tri_count(o)} tris, {len(o.data.materials)} mats')
        if o.data.shape_keys and 'blink' in o.data.shape_keys.key_blocks:
            lo2 = V((1e9,) * 3); hi2 = V((-1e9,) * 3)
            for v in o.data.vertices:
                w = o.matrix_world @ v.co; lo2 = V(map(min, lo2, w)); hi2 = V(map(max, hi2, w))
            c = (lo2 + hi2) / 2; hb = rig.data.bones['head']; lc = (rig.matrix_world @ hb.matrix_local).inverted() @ c
            print(f'[verify] head mesh bbox centre world {tuple(round(x, 3) for x in c)}, in head bone space y {lc.y:.3f} z {lc.z:.3f}, size {tuple(round(x, 3) for x in hi2 - lo2)}')
    print('[verify] actions', sorted((a.name, round(a.frame_range[1] - a.frame_range[0])) for a in bpy.data.actions))

# ---------------------------------------------------------------- shots
def play(rig, name, frame):
    rig.animation_data.action = bpy.data.actions[name]; SC.frame_set(frame)

def set_key(head, name):
    for k in list(head.data.shape_keys.key_blocks) + [k for k in bpy.data.objects['lion_body'].data.shape_keys.key_blocks if k.name != 'belly']:   # the game drives the same keys on the body
        if k.name != 'Basis': k.value = 1.0 if k.name == name else 0.0

def vstack(paths, out):
    ims = []
    for p in paths:
        im = bpy.data.images.load(p); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); ims.append(a.reshape(h, w, 4))
    a = np.concatenate(ims[::-1], axis=0); h, w = a.shape[:2]
    o = bpy.data.images.new('v', w, h, alpha=False); o.pixels.foreach_set(a.ravel()); o.filepath_raw = out; o.file_format = 'PNG'; o.save()

BODY_T = (0, -.35, 1.25)
REF = os.path.join(WORK, 'ref1.png')
def stage_shots():
    openb('lion_anim.blend'); load_gs(); O = bpy.data.objects; rig = O['lion_rig']; head = O['lion_head']; cam = O['cam']
    only = [a for a in ARGS if a in ('beauty', 'turn', 'expr', 'sheet', 'extra', 'face', 'face34', 'far')]
    want = lambda k: not only or k in only
    play(rig, 'idle', 0); set_key(head, 'none')
    if want('beauty'): shoot(cam, os.path.join(SHOTS, 'beauty.png'), 1600, 1600, 35, 10, (0, -.3, 1.3), 3.9, cam_z=1.7)
    if want('turn'):
        ps = []
        for i, ang in enumerate((0, 90, 180)):
            rig.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
            t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((0, -.35, 1.3)); p = os.path.join(WORK, 't_%d.png' % i); ps.append(p)
            shoot(cam, p, 534, 800, 0, 10, t, 3.0, cam_z=1.4)
        rig.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
        row(ps, os.path.join(SHOTS, 'turnaround.png'))
    if want('expr'):
        ps = []
        for name in ('smile', 'angry', 'grin', 'ult'):
            set_key(head, name); p = os.path.join(WORK, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, .3, 1.80), 1.45)
        row(ps, os.path.join(SHOTS, 'expressions.png'))
        ps = []
        for name in ('none', 'blink', 'mouth_open'):
            set_key(head, name); p = os.path.join(WORK, 'e2_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 20, 7, (0, .3, 1.80), 1.45)
        row(ps, os.path.join(WORK, 'expressions_extra.png')); set_key(head, 'none')
    if want('face'):                                  # face close-up beside the reference photo
        p = os.path.join(WORK, 'face_front.png'); shoot(cam, p, 648, 550, 0, 6, (0, .3, 1.80), 1.40)
        if os.path.exists(REF): row([p, REF], os.path.join(WORK, 'face_vs_ref.png'))
    if want('face34'):                                # three-quarter from slightly below, the angle of the reference photo
        p = os.path.join(WORK, 'face_34.png'); shoot(cam, p, 648, 550, -32, 6, (0, .3, 1.78), 1.45, cam_z=1.55)
        if os.path.exists(REF): row([p, REF], os.path.join(WORK, 'face34_vs_ref.png'))
    if want('far'):                                   # gameplay distance, about 8 m out and raised
        shoot(cam, os.path.join(WORK, 'far.png'), 1200, 900, 25, 8, (0, -.3, 1.2), 6.0, cam_z=4.0)
    if want('sheet') or want('extra'):
        rows = []
        clips = CLIPS if want('sheet') else CLIPS[4:]
        for name, n, loop in clips:
            ps = []
            for i in range(4):
                fr = (0 if i < 2 else 2) if name == 'ult' else min(n, int(i * n / (4 if loop else 3)))
                play(rig, name, fr); p = os.path.join(WORK, 'a_%s_%d.png' % (name, i)); ps.append(p)
                shoot(cam, p, 400, 440, 35, 10, BODY_T, 3.9, cam_z=1.5)
            r = os.path.join(WORK, 'arow_%s.png' % name); row(ps, r); rows.append(r)
        vstack(rows[:4], os.path.join(SHOTS, 'anim_sheet.png')) if want('sheet') else None
        vstack(rows[4:] if want('sheet') else rows, os.path.join(SHOTS, 'anim_sheet_extra.png'))
        play(rig, 'idle', 0)

STAGES = dict(build=stage_build, look=stage_look, rig=stage_rig, anim=stage_anim, export=stage_export, verify=stage_verify, shots=stage_shots)
for a in ARGS:
    if a in STAGES: STAGES[a]()
