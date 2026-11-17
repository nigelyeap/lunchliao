"""Stinky Uncle, style `toy` (designer vinyl collectible). Game-ready: rig, skin, 6 shape keys, 4 clips, glb.
Run: blender -b -P uncle.py -- build rig anim export verify shots      (stages run in the order given)
Axes: Z up, hero faces +Y. Built on gym.py: same toy helpers (styles/toy/ahma_toy.py, exec'd), same rig, weights,
animation (heroes/gym.py Pose / make_action, imported) and export code. Look: a pear. Bald comb-over, big ears, red bulb nose,
cream singlet with green stink dots over a heavy low belly, kopi-brown shorts, chubby arms, blue slippers,
rolled newspaper in the right fist and a kopi bag hanging off its red string in the left."""
import bpy, sys, os, math, json, random, importlib.util
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HD = os.path.dirname(os.path.abspath(__file__))
RT = os.path.abspath(os.path.join(HD, '..', '..', '..'))
WORK = os.path.join(HD, '_tmp_uncle'); SHOTS = os.path.join(RT, 'shots', 'heroes_toy', 'uncle'); OUT_GLB = os.path.join(RT, 'assets', 'heroes', 'uncle.glb')
os.makedirs(WORK, exist_ok=True); os.makedirs(SHOTS, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build']

# ---- reuse: old gym (animation) and the toy style helpers ------------------------------------
sys.path.insert(0, os.path.join(RT, 'tools', 'blender', 'heroes'))
_sp = importlib.util.spec_from_file_location('og_gym', os.path.join(RT, 'tools', 'blender', 'heroes', 'gym.py'))
OG = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(OG)
TOY = os.path.join(RT, 'tools', 'blender', 'styles', 'toy', 'ahma_toy.py')
_src = open(TOY).read().split('# ---------------------------------------------------------------- main')[0]
_src = _src.replace("OUT = os.path.join(ROOT, 'shots', 'styles', 'toy')", "OUT = %r" % SHOTS).replace("TMP = os.path.join(HERE, '_tmp')", "TMP = %r" % WORK)
_src = _src.replace("HERE = os.path.dirname(os.path.abspath(__file__))", "HERE = %r" % os.path.dirname(TOY))
exec(compile(_src, TOY, 'exec'), globals())          # mat, mk, ell, tor, sweep, fillet, bez, stage, shoot, row, surf, sph_vf, M, V, Z, H, SC, HERO
ss = OG.smoothstep
HEIGHT = 1.88
GS_FILE = os.path.join(WORK, 'gs.json')
GS = json.load(open(GS_FILE))['gs'] if os.path.exists(GS_FILE) else 1.0   # set in stage_build so the hero is exactly HEIGHT tall

def openb(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, name)); globals()['SC'] = bpy.context.scene

# ---- palette ----------------------------------------------------------------------------------
def singlet_image(n=1024):
    """Cream singlet, green stink polka dots, one kopi drip on the belly. u runs round the body (front at .25, tiles), v is height."""
    rnd = random.Random(11)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / n
    img = np.empty((n, n, 3), np.float32); img[:] = (0.955, 0.925, 0.82)
    img -= (np.sin(xx * 2 * np.pi * 110) * .5 + .5)[..., None] * .02           # fine rib
    def blob(cx, cy, rx, ry, col):
        dx = np.abs(xx - cx); dx = np.minimum(dx, 1 - dx); dy = yy - cy
        a = np.clip((1 - np.sqrt((dx / rx) ** 2 + (dy / ry) ** 2)) * min(rx * 2.8, ry * .55) * n / 1.5 + .5, 0, 1)[..., None]
        img[:] = img * (1 - a) + np.array(col, np.float32) * a
    g = (0.46, 0.70, 0.20)
    for iy in range(7):                      # 1 v = .46 m, 1 u = about 2.7 m, so dots are narrow in u and tall in v
        for ix in range(28):
            blob((ix + .5 * (iy % 2) + rnd.uniform(-.15, .15)) / 28, (iy + .5 + rnd.uniform(-.1, .1)) / 7, .0085, .05, g)
    sc = (0.62, 0.42, 0.24)
    blob(.268, .34, .012, .065, sc); blob(.262, .25, .005, .05, sc)          # kopi stain and drip, front right of the belly
    im = bpy.data.images.new('singlet', n, n, alpha=False)
    im.pixels.foreach_set(np.concatenate([img, np.ones((n, n, 1), np.float32)], axis=2).ravel()); im.pack(); return im

def textured(name, img, base, rough):
    m = mat(name, base, rough); nt = m.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
    nt.links.new(t.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color']); return m

M.update(
    skin=mat('skin', '#E3A57A', .42, sss=.12), nose=mat('nose', '#E0765F', .38, sss=.12, coat=.2), blush=mat('blush', '#DE8A74', .5),
    line=mat('line', '#C98863', .45), hair=mat('hair', '#5B534D', .4, coat=.2), brow=mat('brow', '#8E877E', .45),
    singlet=textured('singlet', singlet_image(), '#F3ECD2', .55), green=mat('green', '#6FAE2C', .35, coat=.3),
    shorts=mat('shorts', '#6B4423', .55), tan=mat('tan', '#C99A62', .45),
    slip=mat('slipper', '#2F6FC4', .3, coat=.4), slipd=mat('slipper_sole', '#1F4A8A', .45),
    paper=mat('paper', '#EEE9DC', .6), ink=mat('ink', '#8E8B84', .55), red=mat('red', '#D3202D', .35, coat=.3),
    kopi=mat('kopi', '#9A5B2C', .12, coat=1.0, sss=.2), bag=mat('bag', '#E7DCCB', .1, coat=1.0), straw=mat('straw', '#F2F2EE', .3, coat=.3),
    lip=mat('lip', '#C26A5C', .4, coat=.3), mouth=mat('mouth', '#5E1A28', .45), pick=mat('pick', '#E2C58E', .5),
)

# ---- proportions ------------------------------------------------------------------------------
HC = V((0, 0, 1.33)); HR = V((0.47, 0.45, 0.44))                      # head centre and radii (globals used by surf())
# pear torso: (z, rx, ry, cy). Narrow shoulders, heavy belly low and forward
TR = [(.34, .37, .34, .02), (.40, .405, .37, .025), (.46, .455, .425, .05), (.54, .475, .455, .075), (.62, .455, .43, .065), (.70, .43, .35, .035),
      (.76, .41, .28, .01), (.80, .37, .23, -.005), (.84, .27, .18, -.01), (.88, .16, .14, 0), (.95, .14, .13, 0)]
_a = np.array(TR); ZS = np.linspace(TR[0][0], TR[-1][0], 24)
RXs = np.interp(ZS, _a[:, 0], _a[:, 1]); RYs = np.interp(ZS, _a[:, 0], _a[:, 2]); CYs = np.interp(ZS, _a[:, 0], _a[:, 3])
for _ in range(3):
    for A_ in (RXs, RYs, CYs): A_[1:-1] = (A_[:-2] + 2 * A_[1:-1] + A_[2:]) / 4
rxz = lambda z: float(np.interp(z, ZS, RXs)); ryz = lambda z: float(np.interp(z, ZS, RYs)); cyz = lambda z: float(np.interp(z, ZS, CYs))
def tsurf(a_deg, z, off):
    a = math.radians(a_deg); return V(((rxz(z) + off) * math.cos(a), cyz(z) + (ryz(z) + off) * math.sin(a), z))
def tpt(a, z, off): return V(((rxz(z) + off) * math.cos(a), cyz(z) + (ryz(z) + off) * math.sin(a), z))
def spt(a, z, off):
    """Singlet point: follows the torso above the belly, then hangs nearly straight from the widest point instead of tucking under."""
    if z >= .54: return tpt(a, z, off)
    k = 1 - .13 * ss(.54, ZH, z); return V(((rxz(.54) * k + off) * math.cos(a), cyz(.54) + (ryz(.54) * k + off) * math.sin(a), z))
ZH = .355                                    # singlet hem (sides); hangs long over the shorts waistband
def zh(a): return ZH - .02 * ss(0, 1, math.sin(a)) + .01 * ss(0, 1, -math.sin(a))   # front drops with the belly, back sits a touch higher
def ztop(a):
    """Singlet top edge: scoop neck (deep in front), straps over the shoulders, deep round armholes at the sides."""
    c = abs(math.cos(a)); ZS_, ZA = .83, .60
    D = .065 + .02 * ss(-.4, .4, math.sin(a))                       # front U a little deeper than the back U
    return ZS_ - D * max(0.0, 1 - (c / .62) ** 2) - (ZS_ - ZA) * ss(.72, 1.0, c) ** .8   # wide U flows into the straps, then the armhole
def atop(a):
    """Angle where the top edge actually sits. Across the neck and straps the edge is the analytic curve z = U(x) with
    x = RN*cos(a), mirrored in X. The angle is re-solved per height so the torso narrowing at the shoulder cannot bend it."""
    global _AT
    if _AT is None:                                                 # cp per angle, made monotonic outward from the centre line
        A = np.linspace(-math.pi, math.pi, 4001); CP = np.zeros_like(A)
        for i, b in enumerate(A):
            c = math.cos(b); z = ztop(b); R = rxz(z) + soff(z)
            CP[i] = c * (RN + (R - RN) * ss(.72, 1.0, abs(c))) / R
        for lo, hi in ((-math.pi / 2, 0), (math.pi / 2, 0), (-math.pi / 2, -math.pi), (math.pi / 2, math.pi)):
            idx = np.where((A >= min(lo, hi)) & (A <= max(lo, hi)))[0]
            idx = idx[np.argsort(np.abs(A[idx] - lo))]               # walk from the centre line (lo) out to the side
            m = 0.0
            for i in idx: m = max(m, abs(CP[i])); CP[i] = math.copysign(m, CP[i])
        _AT = (A, np.clip(CP, -1, 1))
    a = (a + math.pi) % (2 * math.pi) - math.pi; cp = float(np.interp(a, *_AT))
    return math.atan2(math.copysign(math.sqrt(max(0.0, 1 - cp * cp)), math.sin(a)), cp)
_AT = None
def adiff(b, a): return (b - a + math.pi) % (2 * math.pi) - math.pi
def soff(z): return .012 + .02 * (1 - ss(ZH, .52, z)) + .006 * ss(.74, .84, z)

SHD = {1: V((.33, -.01, .665)), -1: V((-.33, -.01, .665))}
ELB = {1: V((.60, .0, .53)), -1: V((-.60, .0, .53))}
CB = {1: V((.615, .19, .335)), -1: V((-.615, .19, .335))}             # grip centres: newspaper (right), kopi string (left)
WR = {1: CB[1] + V((0, -.11, .075)), -1: CB[-1] + V((0, -.11, .075))}
GRIP = {1: .046, -1: .016}
LEGX = .165; PROPP = V((0, -.30, .62))

def loop_pts(f, n=64, close=True):
    p = [f(2 * math.pi * i / n) for i in range(n)]
    return p + [p[0]] if close else p

def ring(name, pts, r, m, seg=8):
    """Closed tube along a loop (no end caps, so no seam or tab)."""
    import bmesh
    P = [V(p) for p in pts]; n = len(P); cen = sum(P, V()) / n; vs = []; fs = []
    for i, p in enumerate(P):
        T = (P[(i + 1) % n] - P[i - 1]).normalized(); N = V((p.x - cen.x, p.y - cen.y, 0)).normalized(); B = N.cross(T).normalized()
        vs += [p + (N * math.cos(2 * math.pi * k / seg) + B * math.sin(2 * math.pi * k / seg)) * r for k in range(seg)]
    for i in range(n):
        j = (i + 1) % n; fs += [(i * seg + k, i * seg + (k + 1) % seg, j * seg + (k + 1) % seg, j * seg + k) for k in range(seg)]
    ob = mk(name, vs, fs, m); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free(); return ob

# ---------------------------------------------------------------- body
def build_torso():
    seg = 28; vs = []; fs = []
    for z in ZS:
        for i in range(seg): vs.append(tpt(2 * math.pi * i / seg, float(z), 0))
    for j in range(len(ZS) - 1):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
    fs.append(tuple(range(seg - 1, -1, -1))); mk('torso', vs, fs, M['skin'])
    # singlet: one closed shell with thickness. inner ring at the hem, J rows up to the cut edge, inner ring at the neck and armholes
    global RN; RN = rxz(.83) + soff(.83)
    seg = 84; J = 11; A = [2 * math.pi * i / seg for i in range(seg)]; rows = [[spt(a, zh(a), soff(zh(a)) - .012) for a in A]]
    for j in range(J):
        rows.append([spt(a + adiff(atop(a), a) * j / (J - 1), zh(a) + (ztop(a) - zh(a)) * j / (J - 1), soff(zh(a) + (ztop(a) - zh(a)) * j / (J - 1))) for a in A])
    rows.append([tpt(atop(a), ztop(a), soff(ztop(a)) - .012) for a in A])   # thin rim, fully under the piping
    vs = [p for r in rows for p in r]; fs = []; uvs = []
    uvv = lambda p: (p.z - .33) / .46
    for j in range(len(rows) - 1):
        for i in range(seg):
            i2 = (i + 1) % seg; u0 = i / seg; u1 = (i + 1) / seg
            fs.append((j * seg + i, (j + 1) * seg + i, (j + 1) * seg + i2, j * seg + i2))
            uvs.append([(u0, uvv(rows[j][i])), (u0, uvv(rows[j + 1][i])), (u1, uvv(rows[j + 1][i2])), (u1, uvv(rows[j][i2]))])
    mk('singlet', vs, fs, M['singlet'], uvs)
    ring('pipe_top', [tpt(atop(2 * math.pi * i / 72), ztop(2 * math.pi * i / 72), soff(ztop(2 * math.pi * i / 72)) - .002) for i in range(72)], .011, M['green'], seg=6)
    ring('pipe_hem', [spt(2 * math.pi * i / 64, zh(2 * math.pi * i / 64) + .006, soff(zh(2 * math.pi * i / 64)) + .003) for i in range(64)], .011, M['green'], seg=6)

def build_neck():
    ell('neck_col', (0, 0, .90), (.165, .15, .11), M['skin'], seg=20)

def build_legs():
    """Shorts: one closed remeshed shell (hips + two baggy legs), cut at the hem and finished with a rolled cuff."""
    import bmesh
    so = H.Soup('hips_sh'); so.ellipsoid(V((0, .03, .45)), (.41, .37, .1))
    for s in (-1, 1): so.capsule(V((s * (LEGX + .01), .03, .45)), V((s * (LEGX + .045), .03, .26)), .17, .148)
    sh, _ = so.remesh(voxel=.012, smooth=6, smooth_factor=.5, target_tris=2400); H.set_material(sh, M['shorts']); sh.name = 'hips_sh'; reg(sh)
    ZHEM = .25; bm = bmesh.new(); bm.from_mesh(sh.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, ZHEM), plane_no=(0, 0, 1), clear_inner=True)
    edge = [v.co.copy() for v in bm.verts if v.is_boundary]; bm.to_mesh(sh.data); bm.free()
    for s in (-1, 1):
        pts = [p for p in edge if p.x * s > 0]; c = sum(pts, V()) / len(pts); r = sum(((p - c).xy.length for p in pts)) / len(pts)
        tor('shorthem', (c.x, c.y, c.z + .004), Z, r - .006, .022, M['tan'], seg=28, rseg=6)
    for s in (-1, 1):
        x = s * LEGX
        sweep('leg', [(x, .03, .34), (x, .03, .20), (x, .03, .07)], [.062, .058, .053], M['skin'], seg=16)
        ell('foot', (x, .095, .055), (.066, .135, .042), M['skin'], seg=18)
        for t in range(4): ell('toe', (x + s * (.034 - .022 * t) - s * .004, .215, .045), (.019, .022, .02), M['skin'], seg=10)
        ell('sole', (x, .09, .018), (.098, .185, .02), M['slipd'], seg=16)
        ell('sole_top', (x, .09, .034), (.092, .178, .01), M['slip'], seg=16)
        post = V((x - s * .012, .19, .055))
        for o in (-1, 1):
            sweep('strap', bez(post, (x + o * .07, .14, .1), (x + o * .088, .03, .036)), .016, M['slip'], seg=6)
        ell('strap_post', post, (.018, .018, .022), M['slip'], seg=12)

def build_arm(s):
    sd = 'r' if s > 0 else 'l'; S, E, W = SHD[s], ELB[s], WR[s]
    so = H.Soup('arm_' + sd); so.sphere(S, .1, seg=18); so.capsule(V((s * .29, -.01, .74)), S, .085, .1); so.capsule(S, E, .1, .095)   # soft shoulder bridge into the torso; so.capsule(S.lerp(E, .3), S.lerp(E, .7) + V((0, .015, 0)), .112, .104); so.capsule(E, W, .094, .062); so.sphere(W, .062)
    a, _ = so.remesh(voxel=.01, smooth=6, smooth_factor=.55, target_tris=1000); H.set_material(a, M['skin']); a.name = 'arm_' + sd; reg(a)

def build_fist(s):
    """Fist round a vertical grip at CB[s]: palm behind the grip, four fingers round the outer side, thumb over the inner side.
    gym.py's shaker-bottle fist, mirrored for the right hand."""
    sd = 'r' if s > 0 else 'l'; C = CB[s]; Wr = WR[s]; gr = GRIP[s]
    mir = (lambda t: t) if s < 0 else (lambda t: 180 - t)
    palm = C + V((0, -.068, 0)); h = H.Soup('hand_' + sd); h.ellipsoid(palm, (.058, .044, .1)); h.capsule(Wr, palm + V((0, 0, .035)), .062, .058)
    rho = gr + .02; rf = .0205
    def arc(z, th, rho, ra, rb):
        pts = [V((C.x + rho * math.cos(math.radians(mir(t))), C.y + rho * math.sin(math.radians(mir(t))), z)) for t in th]
        for p0, p1, r0, r1 in zip(pts[:-1], pts[1:], [ra] + [rf] * 5, [rf] * 4 + [rb]): h.capsule(p0, p1, r0, r1, seg=12)
    for k, dz in enumerate((.072, .024, -.024, -.072)):
        arc(C.z + dz, (250, 195, 140, 95, 55), rho, rf + .002, rf * (.85 if k == 3 else .95))
    arc(C.z + .118, (305, 350, 20, 52), gr + .025, .031, .022)
    hd, _ = h.remesh(voxel=.006, smooth=5, smooth_factor=.5, target_tris=950); H.set_material(hd, M['skin']); hd.name = 'hand_' + sd; reg(hd)

def build_props():
    # rolled newspaper in the right fist, upright: newsprint roll, two grey print bands, a red headline band, inked ends
    C = CB[1]; r = GRIP[1]
    sweep('paper', [(C.x, C.y, C.z - .13), (C.x, C.y, C.z + .30)], [r, r * 1.04], M['paper'], seg=24, round_caps=False)
    for z, m_ in ((C.z - .095, 'ink'), (C.z + .17, 'red'), (C.z + .225, 'ink'), (C.z + .26, 'ink')):
        tor('paper_band', (C.x, C.y, z), Z, r * 1.03, .0045 if m_ == 'ink' else .007, M[m_], seg=20, rseg=4)
    for z, rr in ((C.z - .13, r), (C.z + .30, r * 1.04)):
        tor('paper_end', (C.x, C.y, z), Z, rr * .55, .006, M['ink'], seg=20, rseg=5)
        ell('paper_cap', (C.x, C.y, z), (rr * .985, rr * .985, .006), M['paper'], seg=14)
    # kopi in a plastic bag: the fist holds the red string bundle, the bag hangs below with a straw out of the knot
    C = CB[-1]
    sweep('string', [(C.x, C.y, C.z + .09), (C.x, C.y, C.z - .10)], [.013, .015], M['red'], seg=10)
    tor('string_loop', (C.x, C.y + .015, C.z + .11), (1, 0, 0), .028, .006, M['red'], seg=20, rseg=5)
    K = C + V((0, 0, -.115))
    prof = [(0, .0), (.02, -.004), (.023, -.025), (.045, -.06), (.064, -.10), (.074, -.14), (.071, -.17), (.055, -.19), (.027, -.20), (0, -.202)]
    seg = 28; vs = []; fs = []
    for rr, dz in prof:
        for i in range(seg):
            t = 2 * math.pi * i / seg; vs.append(K + V((rr * math.cos(t), rr * .9 * math.sin(t), dz)))
    for j in range(len(prof) - 1):
        for i in range(seg): fs.append((j * seg + i, (j + 1) * seg + i, (j + 1) * seg + (i + 1) % seg, j * seg + (i + 1) % seg))
    ob = mk('kopi_bag', vs, fs, [M['bag'], M['kopi']])
    lvl = K.z - .06
    for p in ob.data.polygons:
        p.material_index = 1 if sum(ob.data.vertices[i].co.z for i in p.vertices) / len(p.vertices) < lvl else 0
    tor('kopi_knot', K + V((0, 0, -.006)), Z, .022, .01, M['red'], seg=18, rseg=6)
    sweep('straw', [K + V((.012, .005, -.03)), K + V((.03, .02, .07))], .0075, M['straw'], seg=8)
    tor('straw_band', K + V((.026, .017, .05)), V((.018, .015, .1)), .0078, .002, M['red'], seg=12, rseg=4)

def build_body_all():
    build_torso(); build_neck(); build_legs()
    for s in (-1, 1): build_arm(s); build_fist(s)
    build_props()

# ---------------------------------------------------------------- head
HOLE = (0.0, -.245, .215, .14)

def jaw(p):                                   # jowls: widen and soften the lower head into a pear. p is a world point
    d = p - HC; t = ss(-.02, -.30, d.z); z = d.z
    z = z + .55 * .03 * math.log1p(math.exp((-.34 - z) / .03))
    return HC + V((d.x * (1 + .20 * t), d.y * (1 + .10 * t), z))

HOLE_AB = (.19, .125)

def _head_grid():
    vs, fs = sph_vf(56, 28); Q = [HC + V((v.x * HR.x, v.y * HR.y, v.z * HR.z)) for v in vs]
    cx, cz = HOLE[0], HOLE[1]; a, b = HOLE_AB; keep = []
    for f in fs:
        c = sum((Q[i] for i in f), V()) / len(f); fx = c.x - HC.x; fz = c.z - HC.z
        if c.y > HC.y and ((fx - cx) / a) ** 2 + ((fz - cz) / b) ** 2 < 1: continue
        keep.append(f)
    ks = {i for f in keep for i in f}
    kept = set(map(tuple, keep)); gone = {i for f in fs if tuple(f) not in kept for i in f}
    for i in ks & gone:
        fx = Q[i].x - HC.x - cx; fz = Q[i].z - HC.z - cz; th = math.atan2(fz / b, fx / a)
        Q[i] = surf(cx + a * math.cos(th), cz + b * math.sin(th))[0]
    return Q, keep

def hole_loop():
    Q, keep = _head_grid(); cnt = {}
    for f in keep:
        for i in range(len(f)):
            e = (f[i], f[(i + 1) % len(f)]); k = tuple(sorted(e)); cnt[k] = cnt.get(k, 0) + 1
    near = lambda i: Q[i].y > HC.y and abs(Q[i].x - HC.x) < HOLE_AB[0] * 1.6 and abs(Q[i].z - HC.z - HOLE[1]) < HOLE_AB[1] * 1.6
    nxt = {}
    for f in keep:
        for i in range(len(f)):
            a_, b_ = f[i], f[(i + 1) % len(f)]
            if cnt[tuple(sorted((a_, b_)))] == 1 and near(a_) and near(b_): nxt[b_] = a_
    st = min(nxt, key=lambda i: Q[i].x); loop = [st]; c = nxt[st]
    while c != st: loop.append(c); c = nxt[c]
    pts = [Q[i] for i in loop]
    ang = lambda q: math.atan2(q.z - HC.z - HOLE[1], q.x - HC.x)
    if sum(math.sin(ang(pts[(i + 1) % len(pts)]) - ang(pts[i])) for i in range(len(pts))) < 0: pts.reverse()
    return pts

def head_surface():
    Q, keep = _head_grid(); P = [jaw(q) for q in Q]
    used = sorted({i for f in keep for i in f}); remap = {o: n for n, o in enumerate(used)}
    return mk('h_head', [P[i] for i in used], [tuple(remap[i] for i in f) for f in keep], M['skin'])

def on_head(d, off):
    d = V(d).normalized(); return HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z)) * (1 + off)

def build_head():
    head_surface()
    # no back hair: the back of the skull is bald, only the comb-over and the brows carry hair
    # comb-over: salt-and-pepper strands from a low left parting over the bald top, ends tucked on the right
    for k, yk in enumerate(np.linspace(-.36, .30, 7)):
        P = [on_head((math.cos(math.radians(ph)), yk * (1 - .25 * abs(ph - 90) / 70), math.sin(math.radians(ph))), .002 + .004 * math.sin(math.radians(ph)))
             for ph in np.linspace(158, 30, 9)]
        sweep('h_comb', P, [.024] * len(P), M['hair'], seg=6)
    for s in (-1, 1):
        ell('h_ear', HC + V((s * .455, -.04, -.03)), (.05, .085, .125), M['skin'], seg=20)
        ell('h_ear_in', HC + V((s * .48, -.025, -.03)), (.025, .05, .08), M['line'], seg=16)
    p, n_, t, u = surf(0, -.09); ell('h_nose', p + n_ * .015, (.078, .066, .068), M['nose'], seg=24)

# ---------------------------------------------------------------- face (one mesh, six shape keys)
FM = ['skin', 'brow', 'eye', 'white', 'line', 'mouth', 'lip', 'teeth', 'tongue', 'blush', 'pick']
EXe, EZe = .175, -.005
_I = dict(bz=.125, tilt=.03, arch=.004, eye='bead', es=(.82, .7), cut=(.022, -.08), hl=.006, w=.18, curve=.022, up=0, dn=0, teeth=0, tongue=0, cz=-.245, arc=.058, tilt_m=.012)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'eye': 'arc', 'arc': -.022, 'bz': .13},
    'mouth_open': {**_I, 'w': .19, 'curve': .012, 'up': .006, 'dn': .08, 'teeth': .03, 'tongue': .048, 'tilt_m': 0},
    'smile': {**_I, 'w': .24, 'curve': .05, 'bz': .15, 'tilt': -.01, 'tilt_m': 0},
    'angry': dict(bz=.035, tilt=.09, arch=-.004, eye='bead', es=(1.05, .9), cut=(.008, .6), hl=.0, w=.2, curve=-.055, up=.018, dn=.05, teeth=.032, tongue=0, cz=-.25, arc=.058, tilt_m=0),
    'grin': dict(bz=.17, tilt=-.012, arch=.034, eye='arc', es=(1, 1), cut=None, hl=.026, w=.31, curve=.06, up=.004, dn=.085, teeth=.032, tongue=.05, cz=-.255, arc=.062, tilt_m=0),
    'ult': dict(bz=.2, tilt=-.02, arch=.03, eye='bead', es=(1.3, 1.25), cut=None, hl=.012, w=.33, curve=.02, up=.04, dn=.125, teeth=.032, tongue=.09, cz=-.24, arc=.07, tilt_m=0),
}

LOOP = hole_loop()

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
        p, n, t, u = surf(fx, fz); sv, sf = sph_vf(seg, seg // 2); ct, st = math.cos(tilt), math.sin(tilt); v = []
        for q in sv:
            lx, lz = q.x * rad[0], q.z * rad[2]
            if cut: lz = min(lz, cut[0] + cut[1] * lx)
            v.append(p + t * (lx * ct - lz * st + d[0]) + u * (lx * st + lz * ct + d[1]) + n * (q.y * rad[1] + off))
        add(v if show else hide(v), sf, m)
    def patch(x0, x1, lo, hi, off, m, nx=20, ny=3):
        v = []
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx; a, b = lo(x), hi(x)
            for j in range(ny + 1): v.append(surf(x, a + (b - a) * j / ny, off)[0])
        f = [(i * (ny + 1) + j, i * (ny + 1) + j + 1, (i + 1) * (ny + 1) + j + 1, (i + 1) * (ny + 1) + j) for i in range(nx) for j in range(ny)]
        add(v, f, m)
    for s in (-1, 1):
        stroke([(s * (EXe + q * .1), e['bz'] + EZe + q * e['tilt'] + e['arch'] * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .05, .03, .006, 'brow')
        bead = e['eye'] == 'bead'; a, c = .06 * e['es'][0], .075 * e['es'][1]
        blob(s * EXe, EZe, (a, .036, c), 0, 'eye', show=bead, seg=16, cut=(e['cut'][0], e['cut'][1] * s) if e['cut'] else None)
        blob(s * EXe, EZe, (.011, .01, .011), .028, 'white', show=bead, seg=10, d=(.016, min(e['hl'], (e['cut'][0] if e['cut'] else 1) - .016)))
        blob(s * EXe, EZe, (.004, .004, .004), .026, 'white', show=bead, seg=6, d=(-.02, -.02))
        stroke([(s * EXe + .07 * math.cos(ph), EZe - .03 + e['arc'] * 1.05 * math.sin(ph)) for ph in [math.radians(168 - 156 * i / 11) for i in range(12)]], .016, .012, .005, 'eye', show=not bead)
        stroke([(s * EXe + .06 * math.cos(ph), EZe - .072 + .02 * math.sin(ph)) for ph in [math.radians(200 + 140 * i / 8) for i in range(9)]], .009, .006, .003, 'line')   # eye bags
        v = [surf(s * .30, -.16, .0025)[0]]; f = []
        for j in range(1, 4):
            for i in range(14):
                ang = 2 * math.pi * i / 14; v.append(surf(s * .30 + .045 * j / 3 * math.cos(ang), -.16 + .032 * j / 3 * math.sin(ang), .0025 if j < 3 else .0)[0])
        ri = lambda j, i: 1 + (j - 1) * 14 + i % 14
        f += [(0, ri(1, i), ri(1, i + 1)) for i in range(14)]
        f += [(ri(j, i), ri(j + 1, i), ri(j + 1, i + 1), ri(j, i + 1)) for j in (1, 2) for i in range(14)]
        add(v, f, 'blush')
    # mouth: skin ring, lips, a real cavity, one upper tooth row and a tongue (same build as gym). tilt_m lifts his left corner (smirk)
    cx0, cz0 = HOLE[0], HOLE[1]; hw = e['w'] / 2; U = e['up'] + .0065; D = e['dn'] + .0065
    def zc(x): return e['cz'] + e['curve'] * (x / hw) ** 2 - e['tilt_m'] * (x / hw)
    def opening(th):
        x = hw * math.cos(th); sn = math.sin(th); return x, zc(x) + (U if sn >= 0 else D) * sn
    cen = (0.0, e['cz'] + (U - D) * .3); rings = []
    lerpp = lambda p, q, t: (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
    for q0 in LOOP:
        outer = (q0.x - HC.x, q0.z - HC.z); th = math.atan2((outer[1] - cz0) / HOLE_AB[1], (outer[0] - cx0) / HOLE_AB[0]); ox, oz = opening(th)
        lipo = (ox + .014 * math.cos(th), oz + .016 * math.sin(th))
        sc = lambda t: (cen[0] + (ox - cen[0]) * t, cen[1] + (oz - cen[1]) * t)
        rings.append([q0.copy(), surf(*lerpp(outer, lipo, .5), 0)[0], surf(*lipo, .0065)[0],
                      surf(*lerpp(lipo, (ox, oz), .5), .0125)[0], surf(ox, oz, .006)[0],
                      surf(ox, oz, -.012)[0], surf(*sc(.88), -.04)[0], surf(*sc(.62), -.068)[0], surf(*sc(.28), -.088)[0]])
    NTH = len(LOOP); nr = len(rings[0]); v = [rings[k][r] for r in range(nr) for k in range(NTH)] + [surf(cen[0], cen[1], -.092)[0]]
    f = []; fm = []; mats = ['skin', 'skin', 'lip', 'lip', 'mouth', 'mouth', 'mouth', 'mouth']
    for r in range(nr - 1):
        for k in range(NTH):
            a_, b_ = r * NTH + k, r * NTH + (k + 1) % NTH; c_, d_ = (r + 1) * NTH + (k + 1) % NTH, (r + 1) * NTH + k
            f.append((a_, d_, c_, b_)); fm.append(mats[r])
    cv = nr * NTH
    for k in range(NTH): f.append(((nr - 1) * NTH + k, cv, (nr - 1) * NTH + (k + 1) % NTH)); fm.append('mouth')
    o = len(vs); vs.extend(v); fs.extend([tuple(i + o for i in ff) for ff in f]); mi.extend([FM.index(m) for m in fm])
    env = lambda x: max(0.0, 1 - (x / hw) ** 2) ** .5
    def up_e(x): return zc(x) + U * env(x)
    def lo_e(x): return zc(x) - D * env(x)
    tw = hw * .86; th_ = e['teeth']
    patch(-tw, tw, lambda x: up_e(x) - th_ * (1.1 - .45 * (x / tw) ** 2) if th_ else up_e(x) - .0005, lambda x: up_e(x) - .0005, -.011, 'teeth', nx=16, ny=2)
    gw = hw * .6; tg = e['tongue']
    patch(-gw, gw, lambda x: lo_e(x) + .004, lambda x: lo_e(x) + .004 + tg * max(0.0, 1 - (x / gw) ** 2) ** .5, -.036, 'tongue', nx=14, ny=2)
    # toothpick out of his right mouth corner (screen left), rides the corner in every expression
    cxp = -hw * .82; p0, nn, tt, uu = surf(cxp, zc(cxp) - .002, .0)
    a0 = p0 - nn * .02; a1 = p0 + nn * .05 + tt * -.075 + uu * -.03; seg = 6; v = []
    for i, (pp, r) in enumerate(((a0, .006), (a0.lerp(a1, .5), .0058), (a1, .0035))):
        dd = (a1 - a0).normalized(); sd_ = dd.cross(nn).normalized(); up_ = sd_.cross(dd)
        v += [pp + (sd_ * math.cos(2 * math.pi * k / seg) + up_ * math.sin(2 * math.pi * k / seg)) * r for k in range(seg)]
    f = [(i * seg + k, i * seg + (k + 1) % seg, (i + 1) * seg + (k + 1) % seg, (i + 1) * seg + k) for i in range(2) for k in range(seg)]
    f.append(tuple(range(2 * seg, 3 * seg))); add(v, f, 'pick')
    return [jaw(q) for q in vs], fs, mi

KEYS = ['blink', 'mouth_open', 'smile', 'angry', 'grin', 'ult']
def build_face():
    vs, fs, mi = face_geo(EXPR['idle'])
    ob = mk('h_face', vs, fs, [M[k] for k in FM], mat_idx=mi); ob.shape_key_add(name='Basis')
    for name in KEYS:
        k = ob.shape_key_add(name=name); k.data.foreach_set('co', [c for v in face_geo(EXPR[name])[0] for c in v])
    return ob

# ---------------------------------------------------------------- build stage
def stage_build():
    build_body_all(); build_head(); build_face()
    tris = sum(H.tri_count(o) for o in HERO); print('TOY_TRIS', tris, 'objects', len(HERO))
    agg = {}
    for o in HERO: agg[o.name.split('.')[0]] = agg.get(o.name.split('.')[0], 0) + H.tri_count(o)
    print('TOY_TOP', sorted(agg.items(), key=lambda kv: -kv[1])[:16])
    top = max(v.co.z for o in HERO for v in o.data.vertices); bot = min(v.co.z for o in HERO for v in o.data.vertices)
    gs = HEIGHT / top; globals()['GS'] = gs; json.dump({'gs': gs}, open(GS_FILE, 'w')); print('TOY_GS', round(gs, 4), 'raw height', round(top - bot, 3), 'bottom', round(bot, 3))
    for o in HERO:
        for v in o.data.vertices: v.co *= GS
        if o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks:
                for v in kb.data: v.co *= GS
    stage()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'uncle_build.blend'))

# ---------------------------------------------------------------- rig + weights
def eyepos(s): return surf(s * EXe, EZe)[0]
BONES = [
    ('root', (0, 0, 0), (0, 0, .25), None), ('hips', (0, 0, .44), (0, 0, .55), 'root'), ('spine', (0, 0, .55), (0, 0, .66), 'hips'),
    ('chest', (0, 0, .66), (0, 0, .78), 'spine'), ('neck', (0, 0, .78), (0, .01, .89), 'chest'), ('head', (0, .01, .89), (0, .02, 1.77), 'neck'),
    ('eye.l', tuple(eyepos(-1)), tuple(eyepos(-1) + V((0, .06, 0))), 'head'), ('eye.r', tuple(eyepos(1)), tuple(eyepos(1) + V((0, .06, 0))), 'head'),
    ('upperarm.l', tuple(SHD[-1]), tuple(ELB[-1]), 'chest'), ('lowerarm.l', tuple(ELB[-1]), tuple(WR[-1]), 'upperarm.l'),
    ('hand.l', tuple(WR[-1]), tuple(CB[-1] + V((0, -.03, 0))), 'lowerarm.l'), ('handslot.l', tuple(CB[-1]), tuple(CB[-1] + V((0, .08, 0))), 'hand.l'),
    ('upperarm.r', tuple(SHD[1]), tuple(ELB[1]), 'chest'), ('lowerarm.r', tuple(ELB[1]), tuple(WR[1]), 'upperarm.r'),
    ('hand.r', tuple(WR[1]), tuple(CB[1] + V((0, -.03, 0))), 'lowerarm.r'), ('handslot.r', tuple(CB[1]), tuple(CB[1] + V((0, .08, 0))), 'hand.r'),
    ('upperleg.l', (-LEGX, .03, .44), (-LEGX, .03, .21), 'hips'), ('lowerleg.l', (-LEGX, .03, .21), (-LEGX, .03, .06), 'upperleg.l'),
    ('foot.l', (-LEGX, .03, .06), (-LEGX, .13, .03), 'lowerleg.l'), ('toes.l', (-LEGX, .13, .03), (-LEGX, .25, .02), 'foot.l'),
    ('upperleg.r', (LEGX, .03, .44), (LEGX, .03, .21), 'hips'), ('lowerleg.r', (LEGX, .03, .21), (LEGX, .03, .06), 'upperleg.r'),
    ('foot.r', (LEGX, .03, .06), (LEGX, .13, .03), 'lowerleg.r'), ('toes.r', (LEGX, .13, .03), (LEGX, .25, .02), 'foot.r'),
    ('prop', tuple(PROPP), tuple(PROPP + V((0, 0, .3))), 'chest'),
]
RIGID = {'eye.l', 'eye.r'}

def make_rig():
    arm = bpy.data.armatures.new('uncle_rig'); ob = bpy.data.objects.new('uncle_rig', arm); bpy.context.scene.collection.objects.link(ob)
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

TRUNK = ([(0, 0, .38), (0, 0, .55), (0, 0, .66), (0, 0, .78), (0, 0, .89), (0, 0, 1.0)], ['hips', 'spine', 'chest', 'neck', 'head'], [.06, .05, .04, .04])
def trunk(p): return chain(V((0, 0, p.z)), *TRUNK)
def leg(p, s):
    x = s * LEGX; sd = 'l' if s < 0 else 'r'
    return chain(p, [(x, .03, .56), (x, .03, .21), (x, .03, .06), (x, .13, .03)], ['upperleg.' + sd, 'lowerleg.' + sd, 'foot.' + sd], [.06, .04])
def scale(w, f): return {k: v * f for k, v in w.items()}
def merge(*ws):
    o = {}
    for w in ws:
        for k, v in w.items(): o[k] = o.get(k, 0) + v
    return o

def weights_for(name, p):
    n = name.split('.')[0]; s = -1 if p.x < 0 else 1
    if n.startswith('h_'): return {'head': 1.0}
    if n.startswith('paper'): return {'handslot.r': 1.0}
    if n.startswith(('string', 'kopi', 'straw')): return {'handslot.l': 1.0}
    if n.startswith('hand_'): return {'hand.' + n[-1]: 1.0}
    if n.startswith('arm_'):
        sd = n[-1]; k = 1 if sd == 'r' else -1; S, E, W = SHD[k], ELB[k], WR[k]
        w = chain(p, [S, E, W, CB[k]], ['upperarm.' + sd, 'lowerarm.' + sd, 'hand.' + sd], [.08, .05])
        wc = 1 - ss(-.06, .14, (p - S).dot((E - S).normalized()))
        return merge(scale(w, 1 - wc), {'chest': wc})
    if n in ('torso', 'singlet') or n.startswith(('pipe', 'neck')): return trunk(p)
    if n == 'hips_sh':
        u = ss(.46, .36, p.z) * ss(.03, .13, abs(p.x)); return merge(scale(leg(p, s), u), scale({'hips': 1.0}, 1 - u))
    if n.startswith(('shorthem', 'leg', 'foot', 'toe', 'sole', 'strap')):
        w = leg(p, s)
        if n.startswith(('foot', 'toe', 'sole', 'strap')):
            sd = 'l' if s < 0 else 'r'; t = ss(.13, .2, p.y); wf = w.pop('foot.' + sd, 0.0); w['foot.' + sd] = wf * (1 - t); w['toes.' + sd] = w.get('toes.' + sd, 0) + wf * t
        h = 0.0
        return merge(scale(w, 1 - h), {'hips': h})
    print('[weights] unclassified', name); return {'hips': 1.0}

def stage_rig():
    openb('uncle_build.blend'); O = bpy.data.objects
    parts = [o for o in O if o.type == 'MESH' and o.name != 'cyc']
    for o in parts:
        o.data.update()
        for v in o.data.vertices:
            for b, w in weights_for(o.name, v.co / GS).items():
                if w > 1e-3:
                    g = o.vertex_groups.get(b) or o.vertex_groups.new(name=b); g.add([v.index], w, 'REPLACE')
    heads = [o for o in parts if o.name.startswith('h_')]; heads.sort(key=lambda o: o.name != 'h_face')
    bodies = sorted([o for o in parts if not o.name.startswith('h_')], key=lambda o: o.name != 'singlet')   # singlet first so the join keeps its UVMap
    head = H.join(heads, 'uncle_head'); body = H.join(bodies, 'uncle_body')
    import bmesh   # weld the face skin ring onto the head rim (same position in every shape key) so shading runs smooth across it
    bm = bmesh.new(); bm.from_mesh(head.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(head.data); bm.free()
    rig = make_rig()
    for ob in (head, body):
        ob.parent = rig; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = rig
        weak = sum(1 for v in ob.data.vertices if sum(g.weight for g in v.groups) < .5)
        if weak: print('[rig] weak vertices', ob.name, weak)
    for b in rig.data.bones: b.use_deform = b.name not in RIGID
    print('[rig] shape keys', [k.name for k in head.data.shape_keys.key_blocks], 'tris', H.tri_count(head), H.tri_count(body))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'uncle_rig.blend'))

# ---------------------------------------------------------------- animation (OG.pose_frame / OG.make_action reused)
_og_pose = OG.pose_frame
def _ult(rig):
    # Durian Drop: arms flung up and wide (newspaper and kopi high), chest out, head back, big laugh
    P = OG.Pose(rig); P.rot('spine', OG.axis_rot(OG.X, -4)); P.rot('chest', OG.axis_rot(OG.X, -7)); P.rot('head', OG.axis_rot(OG.X, -8))
    for k in (-1, 1):
        sd = 'l' if k < 0 else 'r'
        P.aim('upperarm.' + sd, (k * 0.85, 0.05, 0.52)); P.aim('lowerarm.' + sd, (k * 0.45, 0.1, 0.89)); P.aim('hand.' + sd, (k * 0.25, 0.75, 0.6))
    return P
def toy_pose(rig, t, kind):
    P = _ult(rig) if kind == 'ult' else _og_pose(rig, t, kind)
    P.rot('handslot.l', P.acc('hand.l').inverted())       # kopi bag keeps hanging straight down whatever the arm does
    return P
if 'handslot.l' not in OG.ANIM_BONES: OG.ANIM_BONES.append('handslot.l')
OG.pose_frame = toy_pose

def stage_anim():
    openb('uncle_rig.blend'); SC.render.fps = OG.FPS; rig = bpy.data.objects['uncle_rig']
    acts = [OG.make_action(rig, 'idle', 'idle', 60), OG.make_action(rig, 'run', 'run', 24), OG.make_action(rig, 'attack', 'attack', 18, loop=False), OG.make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'uncle_anim.blend')); print('[anim] actions', [a.name for a in acts])

def stage_export():
    openb('uncle_anim.blend'); O = bpy.data.objects; rig = O['uncle_rig']; OG.reset_pose(rig)
    for k in O['uncle_head'].data.shape_keys.key_blocks: k.value = 0.0
    H.select_only([O['uncle_head'], O['uncle_body'], rig], rig)
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

def stage_shots():
    openb('uncle_anim.blend'); O = bpy.data.objects; rig = O['uncle_rig']; head = O['uncle_head']; cam = O['cam']
    only = [a for a in ARGS if a in ('beauty', 'turn', 'expr', 'sheet', 'hands')]
    want = lambda k: not only or k in only
    g = GS; play(rig, 'idle', 0); set_key(head, 'none')
    if want('beauty') and only != ['hands']: shoot(cam, os.path.join(SHOTS, 'beauty.png'), 1600, 1600, 32, 8, (0, .2 * g, .84 * g), 2.2 * g / 1.1, cam_z=.8 * g)
    if only == ['hands']:
        for nm, s in (('r', 1), ('l', -1)): shoot(cam, os.path.join(WORK, 'hand_%s.png' % nm), 700, 700, -25 * s, 7, CB[s] * g, .6)
        shoot(cam, os.path.join(WORK, 'face.png'), 800, 800, 0, 7, HC * g + V((0, 0, -.1)), 1.2)
    if want('turn') and only != ['hands']:
        ps = []
        for i, ang in enumerate((0, 90, 180)):
            rig.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
            t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((0, .1, .92 * g)); p = os.path.join(WORK, 't_%d.png' % i); ps.append(p)
            shoot(cam, p, 534, 800, 0, 9, t, 1.6 * g / 1.1)
        rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(SHOTS, 'turnaround.png'))
    if want('expr') and only != ['hands']:
        ps = []
        for name in ('smile', 'angry', 'grin', 'ult'):
            set_key(head, name); p = os.path.join(WORK, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, HC * g + V((0, 0, -.06)), 1.25 * g)
        row(ps, os.path.join(SHOTS, 'expressions.png')); set_key(head, 'none')
    if want('sheet') and only != ['hands']:
        rows = []
        for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
            ps = []
            for i in range(4):
                play(rig, name, min(n, int(i * n / 4)) if name != 'ult' else (0 if i < 2 else 2)); p = os.path.join(WORK, 'a_%s_%d.png' % (name, i)); ps.append(p)
                shoot(cam, p, 400, 440, 25, 8, (0, .15, .95 * g), 2.3 * g / 1.1, cam_z=.95 * g)
            r = os.path.join(WORK, 'arow_%s.png' % name); row(ps, r); rows.append(r)
        vstack(rows, os.path.join(SHOTS, 'anim_sheet.png'))

STAGES = dict(build=stage_build, rig=stage_rig, anim=stage_anim, export=stage_export, verify=stage_verify, shots=stage_shots)
for a in ARGS:
    if a in STAGES: STAGES[a]()
