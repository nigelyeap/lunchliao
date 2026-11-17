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
    img[dd > .5] = gold
    img[(dd > .44) & (dd <= .5)] = red * .55
    a = np.concatenate([img, np.ones((n, n, 1))], axis=2).astype(np.float32)
    im = bpy.data.images.new('lion_scales', n, n, alpha=False); im.pixels.foreach_set(a.ravel())
    p = os.path.join(WORK, 'lion_scales.png'); im.filepath_raw = p; im.file_format = 'PNG'; im.save(); im.pack(); return im

def cloth_mat():
    m = mat('cloth', '#D8232A', .42, coat=.25); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = scale_image(); nt.links.new(tx.outputs['Color'], b.inputs['Base Color']); return m

# ---- palette ----------------------------------------------------------------------------------
M.update(
    red=mat('red', '#D8232A', .34, coat=.45), redd=mat('red_dark', '#8E141A', .6),
    gold=mat('gold', '#F5B52A', .3, coat=.5), green=mat('green', '#16A85A', .3, coat=.5),
    fur=mat('fur', '#FFF6E8', .75, sss=.12), eyew=mat('eye_white', '#FFFDF8', .2, coat=.6),
    mirror=mat('mirror', '#EAF1F8', .04, metal=1.0), mouth=mat('mouth', '#C8384A', .5), nostril=mat('nostril', '#3A0D14', .5),
    pants=mat('pants', '#F6BE2C', .85, sss=.08), shoe=mat('shoe', '#1D1A22', .38, coat=.35), sole=mat('sole', '#F3F1F8', .4),
    shirt=mat('shirt', '#2A1F26', .6), blue=mat('blue', '#2F6FD6', .3, coat=.5), black=mat('black', '#1E1A1E', .35, coat=.4),
)
POMC = ['#E8303A', '#FFD23C', '#2BC46A', '#3C8BF0', '#FF7FB6', '#FF8A1E']
for i, hx in enumerate(POMC): M['pom%d' % i] = mat('pom%d' % i, hx, .9, sss=.1)
M['cloth'] = cloth_mat()

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

# ---------------------------------------------------------------- head geometry (v3: Hok San style, built at v2 size then shrunk by HK)
HC = V((0, .17, 1.86)); HR = V((.80, .52, .52)); PE = 2.6        # superellipsoid head shell
JC = V((0, .23, 1.70)); JRO = V((.70, .48, .32)); JRI = V((.62, .41, .26))   # jaw bowl centre, outer and inner radii
JP = V((0, -.16, 1.70))                                          # jaw hinge
JAW0 = 10                                                        # rest pose jaw just parted so the teeth read
PAL = (.74, .50)                                                 # palate (mouth roof) radii around JC
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

def line_image(name, bg, fg, curves, w, n=512):
    v, u = (np.mgrid[0:n, 0:n] + .5) / n; ink = np.zeros((n, n), bool)
    for P in curves:
        P = np.array(P); seg = np.linspace(0, len(P) - 1, len(P) * 4)
        xs = np.interp(seg, np.arange(len(P)), P[:, 0]); ys = np.interp(seg, np.arange(len(P)), P[:, 1])
        for x, y in zip(xs, ys):
            i0, i1 = max(0, int((y - w) * n) - 1), min(n, int((y + w) * n) + 2); j0, j1 = max(0, int((x - w) * n) - 1), min(n, int((x + w) * n) + 2)
            if i0 < i1 and j0 < j1: ink[i0:i1, j0:j1] |= (u[i0:i1, j0:j1] - x) ** 2 + (v[i0:i1, j0:j1] - y) ** 2 < w * w
    img = np.where(ink[..., None], np.array(H.srgb(fg)), np.array(H.srgb(bg)))
    a = np.concatenate([img, np.ones((n, n, 1))], axis=2).astype(np.float32)
    im = bpy.data.images.new(name, n, n, alpha=False); im.pixels.foreach_set(a.ravel())
    im.filepath_raw = os.path.join(WORK, name + '.png'); im.file_format = 'PNG'; im.save(); im.pack(); return im

def tex_mat(name, im, rough=.32, coat=.5):
    m = mat(name, '#FFFFFF', rough, coat=coat); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = im; nt.links.new(tx.outputs['Color'], b.inputs['Base Color']); return m

PU = (-.85, 1.30, 1.70)                                          # panel UV: x and z mapped into the square texture
def puv(p): return ((p.x - PU[0]) / PU[2], (p.z - PU[1]) / PU[2])

def panel_curves():
    C = []
    for j, z in enumerate(np.arange(1.36, 2.42, .13)):
        for x in np.arange(.07 + .07 * (j % 2), .86, .14):
            for s in (-1, 1):
                q = ((s * x - PU[0]) / PU[2], (z - PU[1]) / PU[2]); C.append(swirl(q, .027, 1.5, s, a0=(math.pi if s < 0 else 0) + .7 * j, tail=.8))
    return C
def cheek_curves():
    return [swirl((.5, .5), .2, 1.5, 1, a0=.4), swirl((.22, .78), .07, 1.2, -1, a0=2.0, tail=.6), swirl((.78, .24), .07, 1.2, -1, a0=5.0, tail=.6)]

M.update(rfur=mat('red_fur', '#9C0410', .92, spec=.25), bfur=mat('black_fur', '#181214', .92),
         iris=mat('iris', '#7A4A1E', .75, spec=.2), eyew=mat('eye_white', '#FFFDF8', .45))
M['panel'] = tex_mat('panel', line_image('lion_panel', '#FFD22E', '#1A1210', panel_curves(), .0065))
M['cheek'] = tex_mat('cheek', line_image('lion_cheek', '#F48A22', '#1A1210', cheek_curves(), .022))

def ellp(name, c, r, m, seg=16, rot=None):
    vs, fs = sph_vf(seg, seg // 2); c = V(c); R = rot if rot is not None else Matrix.Identity(3)
    P = [c + R @ V((v.x * r[0], v.y * r[1], v.z * r[2])) for v in vs]
    return mk(name, P, fs, m, uvs=[[puv(P[i]) for i in f] for f in fs])

def shell_n(p):
    q = p - HC; return V(tuple(math.copysign(abs(q[i] / HR[i]) ** (PE - 1) / HR[i], q[i]) for i in range(3))).normalized()

def shell_pt(d):
    d = V(d).normalized(); s = sum(abs(d[i] / HR[i]) ** PE for i in range(3)) ** (-1 / PE); return HC + d * s

def hsurf(fx, fz, off=0.0):
    k = max(1e-5, 1 - abs(fx / HR.x) ** PE - abs(fz / HR.z) ** PE); p = HC + V((fx, HR.y * k ** (1 / PE), fz)); n = shell_n(p)
    t = n.cross(Z).normalized(); u = t.cross(n).normalized(); return p + n * off, n, t, u

def palate_r(p): return math.hypot(p.x / PAL[0], (p.y - JC.y) / PAL[1])

def build_shell():
    vs, fs = sph_vf(44, 22); P = []
    for v in vs:
        p = shell_pt(v)
        if p.z < JC.z:                                            # flatten the mouth roof inside the jaw so the jaw closes on it
            w = ss(1.05, .78, palate_r(p)); p.z += (JC.z + .004 - p.z) * w
        P.append(p)
    mi = []
    for f in fs:                                                  # red back and crown, painted gold panel on the face, pink mouth roof
        c = sum((P[i] for i in f), V()) / len(f)
        mi.append(1 if c.z < JC.z + .02 and palate_r(c) < .86 else 2 if shell_n(c).y > .3 and c.z < HC.z + .44 else 0)
    mk('h_shell', P, fs, [M['red'], M['mouth'], M['panel']], mat_idx=mi, uvs=[[puv(P[i]) for i in f] for f in fs])

def revolve(name, prof, c, mats, seg=40, mrun=None):
    """prof: list of (rx, ry, dz). First and last with rx==0 become poles. mrun: material index per profile segment."""
    c = V(c); vs = []; fs = []; mi = []; rings = []
    for rx, ry, dz in prof:
        if rx == 0: vs.append(c + V((0, 0, dz))); rings.append([len(vs) - 1] * seg)
        else:
            rings.append(list(range(len(vs), len(vs) + seg)))
            vs += [c + V((rx * math.cos(2 * math.pi * i / seg), ry * math.sin(2 * math.pi * i / seg), dz)) for i in range(seg)]
    for j in range(len(rings) - 1):
        a, b = rings[j], rings[j + 1]
        for i in range(seg):
            q = [a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]]; q = [x for k, x in enumerate(q) if x not in q[:k]]
            fs.append(tuple(q)); mi.append(mrun[j] if mrun else 0)
    return fix_normals(mk(name, vs, fs, mats, mat_idx=mi))

def build_jaw():
    prof = [(0, 0, -JRI.z)]; mr = []
    for k in range(1, 7):
        ph = math.radians(180 - 85 * k / 6); prof.append((JRI.x * math.sin(ph), JRI.y * math.sin(ph), JRI.z * math.cos(ph))); mr.append(2)
    prof.append((JRI.x, JRI.y, .006)); mr.append(2)
    prof.append(((JRI.x + JRO.x) / 2 - .01, (JRI.y + JRO.y) / 2 - .01, .03)); mr.append(1)
    prof.append((JRO.x + .012, JRO.y + .012, .012)); mr.append(1)
    for k in range(0, 7):
        ph = math.radians(95 + 80 * k / 6); prof.append((JRO.x * math.sin(ph), JRO.y * math.sin(ph), JRO.z * math.cos(ph))); mr.append(1 if k == 0 else 0)
    prof.append((0, 0, -JRO.z)); mr.append(0)
    revolve('j_jaw', prof, JC, [M['rfur'], M['gold'], M['mouth']], seg=40, mrun=mr)
    ell('j_tongue', JC + V((0, .05, -.09)), (.36, .27, .08), M['tongue'], seg=20)
    for k in range(9):                                            # lower teeth on the inner lip, fangs at the ends
        th = math.radians(36 + 108 * k / 8); big = k in (0, 8)
        p = JC + V((JRI.x * .97 * math.cos(th), JRI.y * .97 * math.sin(th), .03 + (.03 if big else 0)))
        ell('j_tooth', p, (.032, .024, .055 if big else .035), M['teeth'], seg=8)
    # the big red fur lower lip and chin: a fat lumpy roll round the jaw rim, chunky clumps hanging under it
    pts = []
    for i in range(26):
        a = math.radians(-14 + 208 * i / 25); pts.append((JC + V(((JRO.x + .04) * math.cos(a), (JRO.y + .05) * math.sin(a), -.01)), .105 + .02 * math.sin(i * 2.1)))
    for row, (dz, sc, r) in enumerate(((-.17, .92, .11), (-.29, .70, .1))):
        n = 9 - 2 * row
        for i in range(n):
            th = math.radians(18 + 144 * i / max(1, n - 1)); pts.append((JC + V((JRO.x * sc * math.cos(th), JRO.y * (.7 + .3 * sc) * math.sin(th) + .04, dz)), r))
    blobs('j_lipfur', pts, M['rfur'], voxel=.022, tris=1500)

def on_head(fx, fz, off=0.0): return hsurf(fx, fz, off)[0]

def build_head():
    build_shell(); build_jaw()
    for k in range(9):                                            # upper teeth hanging from the mouth roof
        th = math.radians(32 + 116 * k / 8); big = k in (0, 8)
        ell('h_tooth', JC + V((.60 * math.cos(th), .43 * math.sin(th), -.035 - (.02 if big else 0))), (.034, .026, .055 if big else .04), M['teeth'], seg=8)
    ul = [JC + V(((JRO.x + .03) * math.cos(math.radians(a)), (JRO.y + .015) * math.sin(math.radians(a)), .05 + .035 * math.sin(math.radians(a)) ** 4)) for a in np.linspace(-6, 186, 34)]
    sweep('h_lip', ul, .05, M['gold'], seg=7)
    # painted forehead column rising from the nose to the mirror, gold with black linework
    p, n, t, u = hsurf(0, .10); ellp('h_column', p + n * .0, (.15, .10, .24), M['panel'], seg=18)
    p, n, t, u = hsurf(0, -.08); NO = p + n * .05
    ellp('h_nose', NO, (.16, .11, .10), M['panel'], seg=18)
    for s in (-1, 1): ell('h_nostril', NO + V((s * .07, .09, -.035)), (.04, .025, .028), M['nostril'], seg=12)
    # forehead mirror in a thick red fur ring, red flower on the crown above it
    p, n, t, u = hsurf(0, .33); MC = p + n * .07
    ell('h_mirror', MC, (.10, .02, .10), M['mirror'], rot=frame_mat(t, n, u), seg=20)
    tor('h_mirror_rim', MC + n * .004, n, .105, .02, M['gold'], seg=28, rseg=5)
    fluff('h_mirror_fur', MC - n * .01, n, .16, .055, M['rfur'], bumps=11, seg=33, rseg=6, amp=.5)
    q = shell_pt((0, .42, 1)); qn = shell_n(q); FC = q + qn * .09
    for k in range(7):
        a = 2 * math.pi * k / 7; d = V((math.cos(a), 0, math.sin(a))); ell('h_petal', FC + d * .07 + V((0, .02, 0)), (.07, .04, .07), M['rfur'], seg=10)
    ell('h_flower', FC + V((0, .05, 0)), (.045, .04, .045), M['gold'], seg=12)
    # eyes: white globe, flat bronze iris dome (in the face mesh), set deep in a heavy red fur socket
    for s in (-1, 1):
        c, f, t, u = eye_frame(s)
        ell('h_eyeball', c, (ER, ER, ER), M['eyew'], seg=16)
        fluff('h_eyefur', c - f * .03, f, .205, .06, M['rfur'], bumps=9, seg=27, rseg=6, amp=.45)
    # black fur tufts under the eyes, round the cheek balls and at the nose sides
    pts = []
    for s in (-1, 1):
        for fx, fz, r in ((.17, -.15, .095), (.40, -.13, .1), (.56, -.05, .075), (.08, -.22, .06)):
            pts.append((on_head(s * fx, fz, .05), r)); pts.append((on_head(s * (fx + .03), fz - .03, .07), r * .8))
    blobs('h_blackfur', pts, M['bfur'], voxel=.02, tris=1000)
    # red fur: a thick rim round the whole face, big lobes on the top corners, and a ring round the back
    pts = []
    for i in range(30):
        a = math.radians(-24 + 228 * i / 29); d = V((math.cos(a), -.05, math.sin(a) * .95))
        q = shell_pt(d); pts.append((q + shell_n(q) * .05, .11 + .025 * math.sin(3.7 * i)))
    for s in (-1, 1):
        for d, r in (((.74, .2, .66), .22), ((.56, .3, .84), .19), ((.92, 0, .42), .17), ((.36, .2, .95), .15), ((.88, .2, .1), .14)):
            q = shell_pt((s * d[0], d[1], d[2])); pts.append((q + shell_n(q) * .07, r))
    for i in range(20):
        a = 2 * math.pi * i / 20; d = V((math.cos(a) * .95, -.70, math.sin(a) * .85))
        q = shell_pt(d); pts.append((q + shell_n(q) * .02, .08 + .015 * math.sin(5 * a)))
    blobs('h_furring', pts, M['rfur'], voxel=.024, tris=2600)
    col = [shell_pt(V((math.cos(a) * .95, -.86, math.sin(a) * .85))) for a in np.linspace(0, 2 * math.pi, 33)]
    sweep('h_collar', [q + shell_n(q) * .01 for q in col], .03, M['gold'], seg=6, round_caps=False)

# ---------------------------------------------------------------- face (one mesh, keyed): lids, irises, brows, cheek balls
ER = .15; EXs, EZs = .31, .11
def eye_frame(s):
    p, n, t, u = hsurf(s * EXs, EZs)
    f = (n + V((0, .35, 0))).normalized(); t2 = f.cross(Z).normalized(); u2 = t2.cross(f).normalized()
    return p + f * .06, f, t2, u2

FM = ['rfur', 'gold', 'iris', 'cheek']
_I = dict(lu=52, ll=32, tilt=0, bp=12, bti=0, ps=1.0, cz=0.0, jaw=0)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'lu': 101, 'll': 80, 'bp': 20},
    'mouth_open': {**_I, 'jaw': 30},
    'smile': {**_I, 'll': 64, 'lu': 56, 'bp': 6, 'cz': .03, 'jaw': 9},
    'angry': {**_I, 'lu': 86, 'll': 44, 'tilt': 26, 'bp': 42, 'bti': -18, 'ps': .85, 'jaw': 13},
    'grin': {**_I, 'lu': 76, 'll': 84, 'tilt': -8, 'bp': 2, 'bti': 4, 'cz': .04, 'jaw': 22},
    'ult': {**_I, 'lu': 40, 'll': 28, 'bp': -8, 'bti': 8, 'ps': .8, 'cz': .02, 'jaw': 40},
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
            for i in range(seg): f_.append((a + i, b + i, b + (i + 1) % seg, a + (i + 1) % seg)); m_.append(1 if edge else 0)
        for i in range(seg): f_.append((last, rings[-1] + (i + 1) % seg, rings[-1] + i)); m_.append(0)
        add(v, f_, m_)
    for s in (-1, 1):
        c, f, t, u = eye_frame(s)
        cap(c, f, t, u, .172, .16, math.radians(e['lu']), False, math.radians(-s * e['tilt']))
        cap(c, f, t, u, .168, .156, math.radians(e['ll']), True, 0.0)
        fr = Matrix((t, f, u)).transposed(); ps = e['ps']
        v, f_, _ = ellv(c + f * (ER - .035), (.082 * ps, .05, .082 * ps), fr, 14); add(v, f_, 'iris')
        # heavy red fur brow: a lumpy tube arching over the eye, outer end swept up and out
        Q = [i / 6 - 1 for i in range(13)]; P = []
        for q in Q:
            ph = math.radians(e['bp'] + e['bti'] * q)
            P.append(c + (u * math.cos(ph) + f * math.sin(ph) + t * (s * q * 1.05)).normalized() * .24 + u * (.05 * max(0, q)))
        n = len(P); seg = 8; v = []
        for i in range(n):
            tan = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized(); out = (P[i] - c).normalized(); side = out.cross(tan).normalized(); nn = tan.cross(side).normalized()
            q = Q[i]; r = .12 * (1 + .12 * math.cos(5 * math.pi * q)) * (math.sin(math.pi * (q + 1) / 2) ** .35 if 0 < i < n - 1 else 0.0)
            v += [P[i] + (side * math.cos(a) + nn * math.sin(a)) * r for a in [2 * math.pi * k / seg for k in range(seg)]]
        f_ = [(i * seg + k, i * seg + (k + 1) % seg, (i + 1) * seg + (k + 1) % seg, (i + 1) * seg + k) for i in range(n - 1) for k in range(seg)]
        add(v, f_, 'rfur')
        # orange cheek ball with a black swirl, sitting forward under the inner eye (rises with smile and grin)
        p, n_, t_, u_ = hsurf(s * .21, -.03, .12)
        v, f_, sv = ellv(p + V((0, 0, e['cz'])), (.12, .12, .12), Matrix((t_, n_, u_)).transposed(), 16)
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
Y0, Y1 = .02, -1.40
def cloth_dims(s):
    top = float(np.interp(s, [0, .1, .3, .55, .8, 1], [2.10, 1.90, 1.68, 1.60, 1.54, 1.44]))   # front end tucks under the smaller head
    w = float(np.interp(s, [0, .2, .45, .7, .85, 1], [.74, .84, .90, .90, .86, .78]))
    w *= .78 + .22 * math.sqrt(max(0.0, 1 - (max(0.0, s - .86) / .14) ** 2))
    hem = float(np.interp(s, [0, .5, 1], [.62, .56, .58]))
    return top, w, hem

def cloth_prof(s):
    top, w, hem = cloth_dims(s); y = Y0 + (Y1 - Y0) * s; hv = min(.85 * w, top - hem - .08, .42); zc = top - hv; P = []
    side = [hem + (zc - hem) * j / 4 for j in range(4)]
    def flare(x, z, sg):
        d = ss(zc, hem, z); return x * (1 + .1 * d) + sg * .02 * math.sin(y * 13 + sg) * d
    for z in side: P.append(V((flare(w, z, 1), y, z)))
    for i in range(19):
        a = math.pi * i / 18; P.append(V((w * math.cos(a), y, zc + hv * math.sin(a))))
    for z in reversed(side): P.append(V((flare(-w, z, -1), y, z)))
    return P

NS = 20
def build_cloth():
    outer = [cloth_prof(i / NS) for i in range(NS + 1)]; NP = len(outer[0]); TH = .018
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
    vc = [[0.0] * NP]
    for j in range(NS): vc.append([vc[-1][i] + (outer[j + 1][i] - outer[j][i]).length for i in range(NP)])
    for j in range(NS):
        for i in range(NP - 1):
            fs.append((o(j, i), o(j, i + 1), o(j + 1, i + 1), o(j + 1, i))); lo = i == 0 or i == NP - 2; band = i < 2 or i >= NP - 3
            mi.append(3 if lo else 1 if band else 0); T = .40
            uvs.append([(arc[j][i] / T, vc[j][i] / T), (arc[j][i + 1] / T, vc[j][i + 1] / T), (arc[j + 1][i + 1] / T, vc[j + 1][i + 1] / T), (arc[j + 1][i] / T, vc[j + 1][i] / T)])
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
    ob = mk('cloth', vs, fs, [M['cloth'], M['green'], M['redd'], M['blue']], uvs=uvs, mat_idx=mi); fix_normals(ob)
    # fur roll along the hem and up the front edges
    left = [outer[j][-1] for j in range(NS + 1)]; right = [outer[j][0] for j in range(NS + 1)]
    fe = lambda P, idx: [P[k] for k in idx]
    up_l = fe(outer[0], range(NP - 1, NP - 6, -1)); up_r = fe(outer[0], range(0, 5))
    path = list(reversed(up_l)) + left[1:] + list(reversed(right[:-1]))[1:] + up_r[1:]
    path = [p + V((math.copysign(.012, p.x), -.012 if abs(p.y - Y0) < .01 else 0, -.01)) for p in path]
    L = [0.0] + list(np.cumsum([(path[i + 1] - path[i]).length for i in range(len(path) - 1)]))
    dense = []; rad = []
    for k in range(int(L[-1] / .045)):
        x = k * .045; i = min(int(np.searchsorted(L, x)) - 1, len(path) - 2); i = max(i, 0); t = (x - L[i]) / max(1e-6, L[i + 1] - L[i])
        dense.append(path[i].lerp(path[i + 1], t)); rad.append(.05 * (1 + .3 * abs(math.sin(math.pi * x / .135))))
    sweep('hemfur', dense, rad, M['fur'], seg=5)
    # gold zigzag fringe hanging below the hem on the sides and rump
    hem = left[1:] + list(reversed(right[1:]))
    hem = [p + V((math.copysign(.03, p.x), 0, -.03)) for p in hem]
    L2 = [0.0] + list(np.cumsum([(hem[i + 1] - hem[i]).length for i in range(len(hem) - 1)])); vs2 = []; fs2 = []
    for k in range(int(L2[-1] / .05)):
        x = k * .05; i = max(0, min(int(np.searchsorted(L2, x)) - 1, len(hem) - 2)); t = (x - L2[i]) / max(1e-6, L2[i + 1] - L2[i])
        q = hem[i].lerp(hem[i + 1], t); vs2 += [q, q + V((math.copysign(.012 * (k % 2), q.x), 0, -.13 if k % 2 else -.06))]
    for k in range(len(vs2) // 2 - 1): fs2.append((2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1))
    mk('fringe', vs2, fs2, M['gold'])
    # lengthwise rows of fur: a mane flowing back from the head along the spine and the shoulders of the cloth
    for k, fa in enumerate((.5, .3, .7)):
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
def build_leg(tag, s, hip, knee, ank):
    pts = catmull([hip, knee, ank], 5); rr = list(np.interp(np.linspace(0, 1, len(pts)), [0, .5, .85, 1], [.17, .16, .15, .12]))
    sweep(tag + 'pants', pts, rr, M['pants'], seg=12)
    stripe = [p + V((s * (r - .004), 0, 0)) for p, r in zip(pts, rr)]
    sweep(tag + 'stripe', stripe[:-1], .018, M['red'], seg=6)
    fluff(tag + 'cuff', ank + V((0, 0, .04)), (0, 0, 1), .125, .065, M['fur'], bumps=9, seg=27, rseg=5)
    x, y = ank.x, ank.y
    ell(tag + 'shoe', (x, y + .07, .075), (.115, .2, .08), M['shoe'], seg=18)
    ell(tag + 'sole', (x, y + .075, .03), (.125, .21, .035), M['sole'], seg=18)
    ell(tag + 'shoetoe', (x, y + .2, .08), (.05, .04, .035), M['gold'], seg=12)

def build_performers():
    for s in (-1, 1):
        build_leg('f_', s, *FL[s]); build_leg('r_', s, *RL[s])
    ell('f_hips', (0, .22, .90), (.44, .25, .17), M['pants'], seg=22)
    # chest leans back behind the jaw's swing so the open mouth never shows the dancer through its floor
    ell('torso', (0, .06, 1.12), (.36, .17, .30), M['pants'], seg=18)
    ell('shoulders', (0, -.06, 1.30), (.52, .18, .13), M['pants'], seg=18)
    tor('sash', (0, .21, .99), Z, .38, .04, M['red'], seg=32, rseg=6, squash=(1, .62, 1))
    ell('r_hips', (0, -.95, .83), (.43, .26, .18), M['pants'], seg=22)

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
    up = ss(h.z - .02, h.z + .08, p.z); return merge(scale(w, 1 - up), {('hips' if front else 'rear'): up})

def body_w(p):                                       # cloth, hem fur, spine fur: head at the front, chest in the middle, rear performer behind
    a = ss(-1.05, -.15, p.y); hd = .55 * ss(-.45, -.0, p.y)
    return {'rear': 1 - a, 'chest': a * (1 - hd), 'head': a * hd}

def weights_for(name, p):
    n = name.split('.')[0]
    if n.startswith('j_'): return {'prop': 1.0}
    if n.startswith('h_'): return {'head': 1.0}
    if n in ('cloth', 'hemfur', 'clothfur', 'fringe'): return body_w(p)
    if n.startswith('tail'):
        t = ss(-1.28, -1.42, p.y); return {'rear': 1 - t, 'tail': t}
    if n in ('torso', 'sash', 'shoulders'): return chain(p, [(0, .22, .8), (0, .22, 1.0), (0, .22, 1.18), (0, .24, 1.5)], ['hips', 'spine', 'chest'], [.06, .06])
    if n == 'f_hips': return {'hips': 1.0}
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
        if o.name.split('.')[0] in ('cloth', 'hemfur', 'clothfur', 'fringe'):
            g = o.vertex_groups.new(name='_belly'); g.add([v.index for v in o.data.vertices], 1.0, 'REPLACE')
    heads = [o for o in parts if o.name.startswith(('h_', 'j_'))]; heads.sort(key=lambda o: o.name != 'h_face')
    bodies = [o for o in parts if not o.name.startswith(('h_', 'j_'))]
    head = H.join(heads, 'lion_head'); body = H.join(bodies, 'lion_body'); rig = make_rig()
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
        if t < .35: u = ss(0, .35, t); lean = 10 * u; jaw = 40 * u; push = -.04 * u
        elif t < .55: u = (t - .35) / .2; lean = 10 - 32 * u; jaw = 40 * (1 - ss(.3, .85, u)); push = -.04 + .26 * u
        else: u = (t - .55) / .45; lean = -22 * (1 - ss(0, 1, u)); jaw = 6 * math.sin(u * math.pi); push = .22 * (1 - ss(0, 1, u))
        P.rot('spine', AX(X_, lean * .3)); P.rot('chest', AX(X_, lean * .3)); P.rot('head', AX(X_, lean * .6)); P.rot('prop', AX(X_, -jaw))
        put(rig, 'spine', (0, push, -.25 * max(0.0, -lean) / 22 * .3))
    elif kind == 'ult':                              # King of the Jungle: head reared up high, jaw wide, roar
        P.rot('spine', AX(X_, 5)); P.rot('chest', AX(X_, 6)); P.rot('neck', AX(X_, 6)); P.rot('head', AX(X_, 10)); P.rot('prop', AX(X_, -36))
        put(rig, 'spine', (0, 0, .12))
    elif kind == 'feed':                             # Feed the Lion: head low and forward, jaw held wide, a hungry tremble
        P.rot('spine', AX(X_, -10)); P.rot('chest', AX(X_, -8)); P.rot('neck', AX(X_, -6)); P.rot('head', AX(X_, -10 + 2 * s) @ AX(Z_, 3 * math.sin(6 * math.pi * t)))
        P.rot('prop', AX(X_, -44 - 3 * math.sin(6 * math.pi * t))); P.rot('tail', AX(X_, -15) @ AX(Z_, 10 * s))
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
    for k in head.data.shape_keys.key_blocks:
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
    only = [a for a in ARGS if a in ('beauty', 'turn', 'expr', 'sheet', 'extra', 'face')]
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
