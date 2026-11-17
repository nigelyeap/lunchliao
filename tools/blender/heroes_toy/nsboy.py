"""NSF (key nsboy), style `toy` (designer vinyl collectible). Game-ready: rig, skin, 6 shape keys, 4 clips, glb.
Run: blender -b -P nsboy.py -- build rig anim export verify shots      (stages run in the order given)
Axes: Z up, hero faces +Y. Built on heroes_toy/gym.py: same toy helpers (styles/toy/ahma_toy.py, exec'd),
same face system, rig layout, weights, export and shot cameras. Animation reuses OG.Pose / OG.make_action
from heroes/gym.py with an NSF pose_frame (two-hand rifle hold solved with a two-bone IK)."""
import bpy, sys, os, math, importlib.util
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HD = os.path.dirname(os.path.abspath(__file__))
RT = os.path.abspath(os.path.join(HD, '..', '..', '..'))
WORK = os.path.join(HD, '_tmp_nsboy'); SHOTS = os.path.join(RT, 'shots', 'heroes_toy', 'nsboy'); OUT_GLB = os.path.join(RT, 'assets', 'heroes', 'nsboy.glb')
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
exec(compile(_src, TOY, 'exec'), globals())          # mat, mk, ell, tor, sweep, rbox, stage, shoot, row, surf, sph_vf, M, V, Z, H, SC, HERO
ss = OG.smoothstep
HEIGHT = 1.88
GSF = os.path.join(WORK, 'gs.txt')
GS = float(open(GSF).read()) if os.path.exists(GSF) else 1.0     # final uniform scale, measured in stage_build

def openb(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, name)); globals()['SC'] = bpy.context.scene

# ---- palette ----------------------------------------------------------------------------------
TILE = .6                                                             # camo tile size in metres (pre-scale)
CAMO = ['#5D7A3A', '#8FA35E', '#7A6142', '#262820']                    # olive base, light green, brown, near black
def camo_image(n=512, cells=32, seed=11):
    """Tileable pixel camo. Periodic noise (FFT low pass) thresholded into 4 colours, upsampled with hard pixels."""
    rng = np.random.default_rng(seed); k = np.fft.fftfreq(cells); kk = k[:, None] ** 2 + k[None, :] ** 2
    def field(sc):
        return np.real(np.fft.ifft2(np.fft.fft2(rng.standard_normal((cells, cells))) * np.exp(-kk * sc * sc * 40)))
    a, b, c = field(1.0), field(1.1), field(.8)
    lab = np.zeros((cells, cells), int)
    lab[a > np.percentile(a, 66)] = 1; lab[b > np.percentile(b, 80)] = 2; lab[c > np.percentile(c, 90)] = 3
    pal = np.array([[int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)] for h in CAMO], np.float32)   # image is sRGB tagged
    img = pal[np.kron(lab, np.ones((n // cells, n // cells), int))]
    im = bpy.data.images.new('nsboy_camo', n, n, alpha=False)
    im.pixels.foreach_set(np.concatenate([img, np.ones((n, n, 1), np.float32)], axis=2).ravel()); im.pack(); return im

def camo_mat():
    m = mat('camo', CAMO[0], .62); nt = m.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = camo_image(); t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color']); return m

M.update(
    skin=mat('skin', '#E3A47A', .42, sss=.12), nose=mat('nose', '#D99068', .42, sss=.12), blush=mat('blush', '#E58C7C', .5),
    hair=mat('hair', '#3A322C', .85), hairfade=mat('hairfade', '#57463A', .82), brow=mat('brow', '#2A201B', .45),
    camo=camo_mat(), olive=mat('olive', '#5D7A3A', .6), flap=mat('flap', '#46602B', .6), tape=mat('tape', '#3B4A2A', .65),
    inband=mat('inband', '#A7A47A', .7), web=mat('web', '#4A5232', .7), buckle=mat('buckle', '#5C5F57', .35, metal=.4),
    boot=mat('boot', '#18181B', .3, coat=.45), sole=mat('sole', '#2C2C31', .55),
    beret=mat('beret', '#B80A62', .55, coat=.1), bband=mat('bband', '#1C1C20', .35, coat=.3), badge=mat('badge', '#E2B84A', .25, metal=.7, coat=.5),
    pack=mat('pack', '#566C36', .6), matroll=mat('matroll', '#8A8F5A', .7), bottle=mat('bottle', '#3E4A2C', .45), cap=mat('cap', '#1C1C20', .4),
    gun=mat('gun', '#1A1A1A', .45, coat=.15), gun2=mat('gun2', '#242424', .5), sight=mat('sight', '#2E2E2E', .4),
    band=mat('band', '#E8312A', .35, coat=.3), watch=mat('watch', '#151518', .3, coat=.4), wface=mat('wface', '#9FB0A0', .2, coat=.6),
    lip=mat('lip', '#C9705F', .4, coat=.3), mouth=mat('mouth', '#5E1A28', .45),
)

# ---- proportions ------------------------------------------------------------------------------
HC = V((0, 0, 1.255)); HR = V((0.50, 0.47, 0.43))                      # head centre and radii (globals used by surf())
TR = [(.44, .25, .18), (.50, .25, .18), (.58, .26, .185), (.65, .30, .20), (.71, .34, .215), (.755, .335, .205), (.785, .28, .19),
      (.805, .21, .17), (.83, .15, .135), (.87, .14, .125), (.92, .14, .125)]
_a = np.array(TR); ZS = np.linspace(TR[0][0], TR[-1][0], 22); RXs = np.interp(ZS, _a[:, 0], _a[:, 1]); RYs = np.interp(ZS, _a[:, 0], _a[:, 2])
for _ in range(3):
    RXs[1:-1] = (RXs[:-2] + 2 * RXs[1:-1] + RXs[2:]) / 4; RYs[1:-1] = (RYs[:-2] + 2 * RYs[1:-1] + RYs[2:]) / 4
rxz = lambda z: float(np.interp(z, ZS, RXs)); ryz = lambda z: float(np.interp(z, ZS, RYs))
def tsurf(a_deg, z, off):
    a = math.radians(a_deg); return V(((rxz(z) + off) * math.cos(a), (ryz(z) + off) * math.sin(a), z))
def tframe(a_deg, z, tilt=0.0):
    """Rotation whose x is the torso tangent, y the outward normal, z up (for boxes sitting on the shirt)."""
    a = math.radians(a_deg); n = V((math.cos(a) / rxz(z), math.sin(a) / ryz(z), 0)).normalized(); t = n.cross(V((0, 0, 1)))
    R = Matrix((t, n, V((0, 0, 1)))).transposed()
    return Matrix.Rotation(math.radians(tilt), 3, n) @ R
ZH = .47
def ztop(a): return .835 - .015 * ss(-.3, .3, math.sin(a))             # mandarin collar base, a touch lower at the front
def shirt_off(z): return .012 + .03 * (1 - ss(ZH, .56, z))             # bloused just above the belt

SHD = {1: V((.40, 0, .70)), -1: V((-.40, 0, .70))}
ELB = {1: V((.47, .07, .48)), -1: V((-.36, .14, .50))}
LEGX = .15
PACK = V((0, -.30, .66))

# ---- rubber band rifle, held at port arms across the body (butt at the right hip, muzzle up to the left)
RB = V((.30, .31, .36)); RMZ = V((-.30, .42, .86)); RL = (RMZ - RB).length; RU = (RMZ - RB).normalized()
_h = V((.55, 0, .70)); RW = (_h - RU * _h.dot(RU)).normalized(); RV = RU.cross(RW); VF = RV if RV.y > 0 else -RV
RROT = Matrix((RU, RW.cross(RU), RW)).transposed()                     # right handed: x along the rifle, z its top
def rp(a, s, w): return RB + RU * a + RV * s + RW * w
GA = (RW + RU * .25).normalized()                                      # pistol grip axis, pointing up into the stock
GC = rp(.20, 0, -.10)                                                 # pistol grip centre (right hand)
FC = rp(.50, 0, -.004)                                                 # under the handguard (left hand)
def fist_frame(A, front):
    ef = (front - A * front.dot(A)).normalized(); ei = A.cross(ef).normalized()
    if ei.dot(VF) > 0: ei = -ei                                         # thumb on the body side, knuckles to the front
    return A, ef, ei
FR = fist_frame(GA, RU); FL = fist_frame(RU, RW)
WR_R = GC - FR[1] * .10 + FR[2] * .03
WR_L = FC - FL[1] * .10 + FL[2] * .02

def loop_pts(f, n=64, close=True):
    p = [f(2 * math.pi * i / n) for i in range(n)]
    return p + [p[0]] if close else p

def catmull(P, k=6, closed=False):
    P = [V(p) for p in P]; n = len(P); out = []
    for i in range(n - 1):
        p0 = P[i - 1] if i > 0 else P[0]; p1 = P[i]; p2 = P[i + 1]; p3 = P[i + 2] if i + 2 < n else P[-1]
        for s in range(k):
            t = s / k; out.append(.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1]); return out

def fix_normals(ob):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free(); return ob

def ring(name, pts, r, m, seg=8):
    """Closed tube along a loop (no end caps, so no seam or tab)."""
    P = [V(p) for p in pts]; n = len(P); cen = sum(P, V()) / n; vs = []; fs = []
    for i, p in enumerate(P):
        T = (P[(i + 1) % n] - P[i - 1]).normalized(); N = V((p.x - cen.x, p.y - cen.y, 0)).normalized(); B = N.cross(T).normalized()
        vs += [p + (N * math.cos(2 * math.pi * k / seg) + B * math.sin(2 * math.pi * k / seg)) * r for k in range(seg)]
    for i in range(n):
        j = (i + 1) % n; fs += [(i * seg + k, i * seg + (k + 1) % seg, j * seg + (k + 1) % seg, j * seg + k) for k in range(seg)]
    return fix_normals(mk(name, vs, fs, m))

def box(name, c, size, m, rot=None, bevel=.01, bseg=2):
    ob = rbox(name, c, size, m, bevel=bevel, rot=rot, bseg=bseg); ob.data.transform(ob.matrix_world); ob.matrix_world = Matrix.Identity(4); return ob

def band(name, z0, z1, rin, rout, m, seg=64, dz=None):
    """Flat band with a rectangular section. rin/rout are (rx, ry). dz(t) shifts the band per angle."""
    prof = [(z0, rout), (z1, rout), (z1, rin), (z0, rin)]; vs = []; fs = []
    for i in range(seg):
        t = 2 * math.pi * i / seg; d = dz(t) if dz else 0.0
        vs += [V((r[0] * math.cos(t), r[1] * math.sin(t), z + d)) for z, r in prof]
    for i in range(seg):
        j = (i + 1) % seg; fs += [(i * 4 + k, j * 4 + k, j * 4 + (k + 1) % 4, i * 4 + (k + 1) % 4) for k in range(4)]
    return fix_normals(mk(name, vs, fs, m))

# ---------------------------------------------------------------- body
def lathe(name, zs, rx, ry, m, seg=28, off=0.0, uv=None):
    vs = []; fs = []; uvs = []
    for z, a, b in zip(zs, rx, ry):
        for i in range(seg):
            t = 2 * math.pi * i / seg; vs.append(V(((a + off) * math.cos(t), (b + off) * math.sin(t), z)))
    for j in range(len(zs) - 1):
        for i in range(seg):
            fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
            if uv: uvs.append([(i / seg * uv, zs[j] / TILE), ((i + 1) / seg * uv, zs[j] / TILE), ((i + 1) / seg * uv, zs[j + 1] / TILE), (i / seg * uv, zs[j + 1] / TILE)])
    fs.append(tuple(range(seg - 1, -1, -1))); uvs.append([(0, 0)] * seg)
    return mk(name, vs, fs, m, uvs if uv else None)

def build_torso():
    lathe('torso', ZS, RXs, RYs, M['skin'], seg=18)
    seg = 96; J = 10; UR = 2; vs = []; fs = []; uvc = []
    for i in range(seg):                                                    # inner closing ring at the hem (tucked under the belt)
        t = 2 * math.pi * i / seg; vs.append(V((rxz(ZH) * math.cos(t), ryz(ZH) * math.sin(t), ZH)))
    for j in range(J):
        for i in range(seg):
            t = 2 * math.pi * i / seg; zt = ztop(t); z = ZH + (zt - ZH) * j / (J - 1); off = shirt_off(z)
            vs.append(V(((rxz(z) + off) * math.cos(t), (ryz(z) + off) * math.sin(t), z)))
    for i in range(seg):                                                    # inner closing ring at the collar
        t = 2 * math.pi * i / seg; zt = ztop(t); vs.append(V(((rxz(zt) - .004) * math.cos(t), (ryz(zt) - .004) * math.sin(t), zt)))
    R = J + 2
    for j in range(R - 1):
        for i in range(seg):
            q = (j * seg + i, (j + 1) * seg + i, (j + 1) * seg + (i + 1) % seg, j * seg + (i + 1) % seg); fs.append(q)
            uvc.append([((i + (k in (2, 3))) / seg * UR, vs[v].z / TILE) for k, v in enumerate(q)])
    mk('shirt', vs, fs, M['camo'], uvc)
    zc = lambda t: -.015 * ss(-.3, .3, math.sin(t))
    band('collar', .818, .875, (rxz(.84) + .004, ryz(.84) + .004), (rxz(.84) + .026, ryz(.84) + .026), M['olive'], seg=48, dz=zc)
    sweep('placket', [tsurf(90, z, shirt_off(z) + .002) for z in (.50, .62, .74, .80)], .011, M['flap'], seg=8)
    for z in (.56, .66, .76): ell('button', tsurf(90, z, shirt_off(z) + .012), (.012, .008, .012), M['tape'], seg=10)
    for s in (-1, 1):                                                       # slanted chest pocket flaps
        a = 90 - s * 34; z = .70
        box('pocket', tsurf(a, z, .022), (.12, .022, .052), M['flap'], rot=tframe(a, z, s * 14), bevel=.01)
        ell('button', tsurf(a, z - .01, .036), (.011, .008, .011), M['tape'], seg=10)
    box('tape', tsurf(90 - 34, .775, .016), (.11, .012, .026), M['tape'], rot=tframe(90 - 34, .775), bevel=.005)   # blank name tape
    box('tape', tsurf(90 + 34, .775, .016), (.11, .012, .026), M['tape'], rot=tframe(90 + 34, .775), bevel=.005)
    box('rank', tsurf(90, .70, .022), (.05, .016, .07), M['beret'], rot=tframe(90, .70), bevel=.008)                # team colour rank slip

def build_legs():
    zs = [.30, .34, .39, .44, .48, .505]
    lathe('trouser', zs, [.27, .285, .295, .30, .30, .29], [.19, .205, .215, .225, .228, .222], M['camo'], seg=40, uv=2)
    band('belt', .448, .497, (.296, .224), (.314, .242), M['web'], seg=48)
    box('buckle', (0, .252, .472), (.075, .022, .056), M['buckle'], bevel=.008)
    sweep('bbottle', [(-.29, -.10, .34), (-.29, -.10, .47)], [.052, .052], M['bottle'], seg=16)
    sweep('bcap', [(-.29, -.10, .47), (-.29, -.10, .51)], [.03, .028], M['cap'], seg=12)
    for s in (-1, 1):
        x = s * LEGX
        sweep('tleg', [(x, 0, .46), (x, .008, .32), (x, 0, .215)], [.135, .128, .138], M['camo'], seg=18, uvrep=(2, 1 / TILE))
        tor('tblouse', (x, 0, .215), Z, .128, .034, M['flap'], seg=20, rseg=5)
        sweep('boot', [(x, 0, .24), (x, 0, .06)], [.098, .098], M['boot'], seg=18, round_caps=False)
        ell('boot_foot', (x, .05, .062), (.104, .165, .068), M['boot'], seg=16)
        ell('boot_toe', (x, .12, .056), (.098, .10, .058), M['boot'], seg=16)
        ell('boot_sole', (x, .06, .026), (.112, .186, .028), M['sole'], seg=16)
        for zl in (.10, .145, .19):
            sweep('lace', [V((x + .102 * math.cos(math.radians(a)), .102 * math.sin(math.radians(a)), zl)) for a in (55, 90, 125)], .009, M['beret'], seg=5)
        for yl, zl in ((.10, .118), (.145, .108)): ell('lace', (x, yl, zl), (.04, .012, .01), M['beret'], seg=10)

def fist(name, C, F, rho, W, rf=.021, levels=(.078, .026, -.026, -.078), th_dz=.128, fa=(250, 195, 140, 95, 55)):
    """Fist wrapped round a bar: palm on one side, four fingers round the outer side, thumb over the inner side (gym's bottle grip)."""
    A, ef, ei = F; palm = C - ef * (rho + .008)
    h = H.Soup(name); h.ellipsoid(palm, (.062, .046, .108), rot=Matrix((ei, -ef, A)).transposed().to_4x4()); h.capsule(W, palm + A * .03, .062, .058)
    def arc(dz, th, r_, ra, rb):
        pts = [C + (ei * math.cos(math.radians(t)) + ef * math.sin(math.radians(t))) * r_ + A * dz for t in th]
        for p0, p1, r0, r1 in zip(pts[:-1], pts[1:], [ra] + [rf] * 5, [rf] * (len(pts) - 2) + [rb]): h.capsule(p0, p1, r0, r1, seg=12)
    for k, dz in enumerate(levels): arc(dz, fa, rho, rf + .002, rf * (.85 if k == 3 else .95))
    arc(th_dz, (305, 350, 20, 52), rho + .005, .031, .022)
    hd, _ = h.remesh(voxel=.0065, smooth=5, smooth_factor=.5, target_tris=1100); H.set_material(hd, M['skin']); hd.name = name; reg(hd)

def build_arm(k):
    sd = 'r' if k > 0 else 'l'; S, E = SHD[k], ELB[k]; W = WR_R if k > 0 else WR_L
    so = H.Soup('arm_' + sd); so.sphere(S, .10, seg=20); so.capsule(S, E, .095, .086); so.capsule(E, W, .084, .06); so.sphere(W, .06)
    a, _ = so.remesh(voxel=.011, smooth=5, smooth_factor=.55, target_tris=1000); H.set_material(a, M['skin']); a.name = 'arm_' + sd; reg(a)
    sp = S + V((-k * .07, 0, .015)); se = S.lerp(E, .66)                       # sleeve rolled above the elbow
    sweep('sleeve_' + sd, [sp, S, S.lerp(E, .35), se], [.125, .135, .126, .116], M['camo'], seg=18, uvrep=(1, 1 / TILE))
    tor('roll_' + sd, se, E - S, .112, .03, M['inband'], seg=24, rseg=7)
    if k < 0:                                                                   # black digital watch on the left wrist
        c = E.lerp(W, .82); ax = (W - E).normalized(); tor('watch_l', c, ax, .066, .016, M['watch'], seg=24, rseg=6)
        n = (VF - ax * VF.dot(ax)).normalized(); R = Matrix((ax.cross(n), n, ax)).transposed()
        box('watch_l', c + n * .072, (.05, .022, .05), M['watch'], rot=R, bevel=.008); box('watchf_l', c + n * .084, (.034, .006, .032), M['wface'], rot=R, bevel=.003)
    if k > 0: fist('hand_r', GC, FR, .052, WR_R, rf=.019, levels=(.054, .018, -.018, -.054), th_dz=.08)
    else: fist('hand_l', FC, FL, .055, WR_L, th_dz=.105, fa=(250, 205, 160, 120))

def bar(name, pts, w, d, m, bevel=.007):
    """Rectangular section swept in the rifle plane (curved magazine). w across in the RU-RW plane, d along RV."""
    pts = [V(q) for q in pts]; vs = []; fs = []; n = len(pts)
    for i, q in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized(); u = RV.cross(t).normalized()
        vs += [q + u * su * w / 2 + RV * sv * d / 2 for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for i in range(n - 1):
        fs += [(i * 4 + k, i * 4 + (k + 1) % 4, (i + 1) * 4 + (k + 1) % 4, (i + 1) * 4 + k) for k in range(4)]
    fs += [(3, 2, 1, 0), tuple((n - 1) * 4 + k for k in range(4))]
    ob = fix_normals(mk(name, vs, fs, m)); bv = ob.modifiers.new('bev', 'BEVEL'); bv.width = bevel; bv.segments = 2; bv.limit_method = 'ANGLE'
    H.apply_mod(ob, bv); w_ = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); w_.keep_sharp = True; H.apply_mod(ob, w_); return ob

def build_rifle():
    """Chunky toy rifle seen side-on: stock, receiver with carry handle, pistol grip, curved magazine, handguard, barrel, front sight."""
    bx = lambda name, a, w, size, m, bev=.012: box(name, rp(a, 0, w), size, m, rot=RROT, bevel=bev, bseg=2)
    bx('rf_butt', .025, -.022, (.05, .056, .15), M['gun2'], .016)                  # butt plate
    bar('rf_stock', [rp(.04, 0, -.03), rp(.12, 0, -.018), rp(.20, 0, -.004)], .085, .05, M['gun'], .012)
    bx('rf_body', .32, 0, (.25, .062, .10), M['gun'])                               # receiver
    sweep('rf_handle', [rp(.23, 0, .05), rp(.25, 0, .10), rp(.37, 0, .10), rp(.39, 0, .05)], .016, M['gun2'], seg=8)
    bx('rf_rsight', .245, .118, (.03, .026, .03), M['sight'], .006)                 # rear sight on the handle
    gr = Matrix((FR[1], FR[2], FR[0])).transposed()
    if gr.determinant() < 0: gr = Matrix((FR[1], -FR[2], FR[0])).transposed()
    box('rf_grip', GC, (.05, .046, .15), M['gun'], rot=gr, bevel=.013)
    sweep('rf_guard', [rp(.235, 0, -.05), rp(.255, 0, -.088), rp(.30, 0, -.088), rp(.31, 0, -.05)], .007, M['gun'], seg=6, round_caps=False)
    bx('rf_trig', .275, -.064, (.012, .014, .034), M['sight'], .004)
    bar('rf_mag', [rp(.335, 0, -.04), rp(.34, 0, -.11), rp(.355, 0, -.17), rp(.385, 0, -.22)], .065, .046, M['gun2'], .01)
    bx('rf_hguard', .555, .002, (.20, .07, .078), M['gun2'], .018)                   # fat handguard (left hand underneath)
    sweep('rf_barrel', [rp(.63, 0, .012), rp(RL - .02, 0, .012)], .017, M['gun'], seg=10)
    sweep('rf_muzzle', [rp(RL - .045, 0, .012), rp(RL + .005, 0, .012)], .025, M['gun'], seg=10)
    bx('rf_fsbase', .665, .035, (.035, .036, .04), M['gun'], .008)                  # front sight post
    bx('rf_fsight', .668, .075, (.016, .016, .05), M['sight'], .005)
    for a in (RL - .09, RL - .07): tor('rf_loop', rp(a, 0, .012), RU, .022, .0065, M['band'], seg=16, rseg=4)   # red band loops (toy band gun)

def build_pack():
    box('pack', PACK, (.40, .16, .36), M['pack'], bevel=.035, bseg=3)
    box('pack_flap', PACK + V((0, -.006, .15)), (.41, .175, .08), M['flap'], bevel=.025, bseg=3)
    for x in (-.11, .11): box('pack_strap', PACK + V((x, -.082, .03)), (.03, .012, .30), M['web'], bevel=.004)
    sweep('mat', [(-.21, -.30, .425), (.21, -.30, .425)], [.065, .065], M['matroll'], seg=18)
    for x in (-.13, .13): tor('mat_strap', (x, -.30, .425), (1, 0, 0), .068, .009, M['web'], seg=20, rseg=5)
    path = [(-80, .70), (-55, .78), (-25, .815), (5, .82), (35, .78), (58, .70), (70, .60), (60, .54), (30, .52), (-5, .52), (-45, .55), (-80, .64)]
    pts = catmull([tsurf(a, z, shirt_off(z) + .02) for a, z in path], 3)
    for sg in (1, -1): sweep('pstrap', [V((sg * p.x, p.y, p.z)) for p in pts], .017, M['web'], seg=6, round_caps=False)

def build_body_all():
    build_torso(); build_legs(); build_arm(1); build_arm(-1); build_rifle(); build_pack()

# ---------------------------------------------------------------- head
HOLE = (0.0, -.245, .215, .14)

def jaw(p):                                   # gentle jaw (slim lad): only a little wider and flatter low down. p is a world point
    d = p - HC; t = ss(-.08, -.33, d.z); z = d.z
    if z < -.33: z = -.33 + (z + .33) * .4
    return HC + V((d.x * (1 + .10 * t), d.y * (1 + .06 * t), z))

HOLE_AB = (.19, .125)                          # head hole half-sizes in pre-jaw face coords. The face skin ring starts on this exact boundary

def _head_grid():
    vs, fs = sph_vf(48, 24); Q = [HC + V((v.x * HR.x, v.y * HR.y, v.z * HR.z)) for v in vs]
    cx, cz = HOLE[0], HOLE[1]; a, b = HOLE_AB; keep = []
    for f in fs:
        c = sum((Q[i] for i in f), V()) / len(f); fx = c.x - HC.x; fz = c.z - HC.z
        if c.y > HC.y and ((fx - cx) / a) ** 2 + ((fz - cz) / b) ** 2 < 1: continue
        keep.append(f)
    ks = {i for f in keep for i in f}
    kept = set(map(tuple, keep)); gone = {i for f in fs if tuple(f) not in kept for i in f}
    for i in ks & gone:                        # snap the staircase boundary onto the exact ellipse so the skin ring joins a smooth edge
        fx = Q[i].x - HC.x - cx; fz = Q[i].z - HC.z - cz; th = math.atan2(fz / b, fx / a)
        Q[i] = surf(cx + a * math.cos(th), cz + b * math.sin(th))[0]
    return Q, keep

def hole_loop():                               # ordered pre-jaw points around the head hole (counter-clockwise seen from the front)
    Q, keep = _head_grid(); cnt = {}
    for f in keep:
        for i in range(len(f)):
            e = (f[i], f[(i + 1) % len(f)]); k = tuple(sorted(e)); cnt[k] = cnt.get(k, 0) + 1
    near = lambda i: Q[i].y > HC.y and abs(Q[i].x - HC.x) < HOLE_AB[0] * 1.6 and abs(Q[i].z - HC.z - HOLE[1]) < HOLE_AB[1] * 1.6
    nxt = {}
    for f in keep:
        for i in range(len(f)):
            a_, b_ = f[i], f[(i + 1) % len(f)]
            if cnt[tuple(sorted((a_, b_)))] == 1 and near(a_) and near(b_): nxt[b_] = a_      # reverse so the walk goes the other way round
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

BZ0, BZ1 = .20, .09                            # beret band height (pre-jaw head coords): lower on his right (+x)
def beret_pt(a, s):
    el_b = math.asin((BZ0 - BZ1 * math.cos(a)) / HR.z); el = el_b + (math.pi / 2 - el_b) * s
    sp = math.sin(math.pi * min(1.0, s * 1.25)) ** .7; flop = max(0.0, math.cos(a)) ** 1.5
    b = .03 + (.075 + .065 * flop) * sp; bz = .03 + .025 * s + .03 * sp
    return HC + V(((HR.x + b) * math.cos(el) * math.cos(a) + .04 * s, (HR.y + b) * math.cos(el) * math.sin(a), (HR.z + bz) * math.sin(el) - .075 * flop * sp))

def build_beret():
    seg = 40; NJ = 11; vs = []; fs = []
    for j in range(NJ):
        for i in range(seg): vs.append(beret_pt(2 * math.pi * i / seg, j / NJ))
    vs.append(beret_pt(0, 1.0))
    for j in range(NJ - 1):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
    top = len(vs) - 1
    for i in range(seg): fs.append(((NJ - 1) * seg + i, (NJ - 1) * seg + (i + 1) % seg, top))
    ob = fix_normals(mk('h_beret', vs, fs, M['beret'])); sm = ob.modifiers.new('sm', 'SMOOTH'); sm.factor = .5; sm.iterations = 3; H.apply_mod(ob, sm)
    ring('h_bband', [beret_pt(2 * math.pi * i / 40, 0) for i in range(40)], .022, M['bband'], seg=6)
    a = math.radians(112); p = beret_pt(a, .13); n = (p - HC - V((0, 0, .1))).normalized(); t = n.cross(V((0, 0, 1))).normalized(); R = Matrix((t, n, t.cross(n) * -1)).transposed()
    ell('h_badge', p + n * .006, (.044, .016, .05), M['badge'], rot=R, seg=20)
    ell('h_badge', p + n * .02, (.022, .01, .025), M['badge'], rot=R, seg=14)

def build_head():
    head_surface()
    def thr(az): a = math.radians(az); return 3 + 35 * math.cos(a) + 3 * math.cos(2 * a)        # smooth all round: rounded nape, no V
    NA, NE = 64, 9; vs = []; fs = []; mi = []        # NS crop: a thin cap just off the skull, the lowest band a soft fade
    for j in range(NE):
        t = (j / NE) ** 1.4; off = .002 + .014 * ss(0, .3, t)
        for i in range(NA):
            ph = 2 * math.pi * i / NA; e0 = math.radians(thr(abs(math.degrees(math.atan2(math.sin(ph), math.cos(ph))))))
            el = e0 + (math.radians(88) - e0) * t
            vs.append(jaw(HC + V(((HR.x + off) * math.cos(el) * math.sin(ph), (HR.y + off) * math.cos(el) * math.cos(ph), (HR.z + off) * math.sin(el)))))
    vs.append(HC + V((0, 0, HR.z + .016)))
    for j in range(NE - 1):
        for i in range(NA): fs.append((j * NA + i, (j + 1) * NA + i, (j + 1) * NA + (i + 1) % NA, j * NA + (i + 1) % NA)); mi.append(int(j == 0))
    for i in range(NA): fs.append(((NE - 1) * NA + i, NE * NA, (NE - 1) * NA + (i + 1) % NA)); mi.append(0)
    fix_normals(mk('h_hair', vs, fs, [M['hair'], M['hairfade']], mat_idx=mi))
    for s in (-1, 1):                           # ears that stick out
        R = Matrix.Rotation(math.radians(s * 28), 3, 'Z')
        ell('h_ear', HC + V((s * .495, -.035, -.035)), (.045, .088, .115), M['skin'], rot=R, seg=12)
        ell('h_earin', HC + V((s * .515, -.005, -.035)), (.018, .05, .07), M['nose'], rot=R, seg=10)
    p, n_, t, u = surf(0, -.085); ell('h_nose', p + n_ * .004, (.055, .048, .048), M['nose'], seg=18)
    build_beret()

# ---------------------------------------------------------------- face (one mesh, six shape keys)
FM = ['skin', 'brow', 'eye', 'white', 'line', 'mouth', 'lip', 'teeth', 'tongue', 'blush']
EXe, EZe = .185, -.02
_I = dict(bz=.14, tilt=.03, arch=.006, eye='bead', es=(.8, .72), cut=(.02, 0), hl=.006, w=.2, curve=.038, up=0, dn=0, teeth=0, tongue=0, cz=-.235, arc=.058)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'eye': 'arc', 'arc': -.022, 'bz': .15},
    'mouth_open': {**_I, 'w': .2, 'curve': .012, 'up': .006, 'dn': .085, 'teeth': .032, 'tongue': .05},
    'smile': {**_I, 'w': .25, 'curve': .055, 'bz': .175, 'tilt': -.01},
    'angry': dict(bz=.05, tilt=.09, arch=-.004, eye='bead', es=(1.08, .95), cut=(.012, .6), hl=.0, w=.21, curve=-.055, up=.018, dn=.05, teeth=.034, tongue=0, cz=-.24, arc=.058),
    'grin': dict(bz=.19, tilt=-.012, arch=.034, eye='arc', es=(1, 1), cut=None, hl=.026, w=.32, curve=.06, up=.004, dn=.085, teeth=.034, tongue=.05, cz=-.25, arc=.062),
    'ult': dict(bz=.07, tilt=.075, arch=-.002, eye='bead', es=(1.0, .9), cut=(.014, .5), hl=.008, w=.28, curve=.0, up=.05, dn=.10, teeth=.036, tongue=.07, cz=-.25, arc=.058),
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
        stroke([(s * (EXe + q * .105), e['bz'] + EZe + q * e['tilt'] + e['arch'] * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .056, .03, .006, 'brow')
        bead = e['eye'] == 'bead'; a, c = .06 * e['es'][0], .075 * e['es'][1]
        blob(s * EXe, EZe, (a, .036, c), 0, 'eye', show=bead, seg=16, cut=(e['cut'][0], e['cut'][1] * s) if e['cut'] else None)
        blob(s * EXe, EZe, (.011, .01, .011), .028, 'white', show=bead, seg=10, d=(.016, e['hl']))
        blob(s * EXe, EZe, (.004, .004, .004), .026, 'white', show=bead, seg=6, d=(-.02, -.02))
        stroke([(s * EXe + .07 * math.cos(ph), EZe - .03 + e['arc'] * 1.05 * math.sin(ph)) for ph in [math.radians(168 - 156 * i / 11) for i in range(12)]], .016, .012, .005, 'eye', show=not bead)
        v = [surf(s * .31, -.17, .0025)[0]]; f = []
        for j in range(1, 4):
            for i in range(14):
                ang = 2 * math.pi * i / 14; v.append(surf(s * .31 + .042 * j / 3 * math.cos(ang), -.17 + .03 * j / 3 * math.sin(ang), .0025 if j < 3 else .0)[0])
        ri = lambda j, i: 1 + (j - 1) * 14 + i % 14
        f += [(0, ri(1, i), ri(1, i + 1)) for i in range(14)]
        f += [(ri(j, i), ri(j + 1, i), ri(j + 1, i + 1), ri(j, i + 1)) for j in (1, 2) for i in range(14)]
        add(v, f, 'blush')
    add([HC.copy(), HC.copy(), HC.copy()], [(0, 1, 2)], 'line')                       # keeps the slot used
    # mouth: skin ring, lips, a real cavity, one upper tooth row and a tongue (same build as gym)
    cx0, cz0 = HOLE[0], HOLE[1]; hw = e['w'] / 2; U = e['up'] + .0065; D = e['dn'] + .0065
    def zc(x): return e['cz'] + e['curve'] * (x / hw) ** 2
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
    zmax = max(v.co.z for o in HERO for v in o.data.vertices); zmin = min(v.co.z for o in HERO for v in o.data.vertices)
    gs = HEIGHT / zmax; globals()['GS'] = gs; open(GSF, 'w').write(repr(gs)); print('[build] pre-scale z', round(zmin, 4), round(zmax, 4), 'GS', round(gs, 4))
    for o in HERO:
        for v in o.data.vertices: v.co *= gs
        if o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks:
                for v in kb.data: v.co *= gs
    stage()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'nsboy_build.blend'))

# ---------------------------------------------------------------- rig + weights
def eyepos(s): return surf(s * EXe, EZe)[0]
BONES = [
    ('root', (0, 0, 0), (0, 0, .25), None), ('hips', (0, 0, .50), (0, 0, .60), 'root'), ('spine', (0, 0, .60), (0, 0, .70), 'hips'),
    ('chest', (0, 0, .70), (0, 0, .80), 'spine'), ('neck', (0, 0, .80), (0, .01, .90), 'chest'), ('head', (0, .01, .90), (0, .02, 1.74), 'neck'),
    ('eye.l', tuple(eyepos(-1)), tuple(eyepos(-1) + V((0, .06, 0))), 'head'), ('eye.r', tuple(eyepos(1)), tuple(eyepos(1) + V((0, .06, 0))), 'head'),
    ('upperarm.l', tuple(SHD[-1]), tuple(ELB[-1]), 'chest'), ('lowerarm.l', tuple(ELB[-1]), tuple(WR_L), 'upperarm.l'),
    ('hand.l', tuple(WR_L), tuple(FC), 'lowerarm.l'), ('handslot.l', tuple(FC), tuple(FC + RU * .08), 'hand.l'),
    ('upperarm.r', tuple(SHD[1]), tuple(ELB[1]), 'chest'), ('lowerarm.r', tuple(ELB[1]), tuple(WR_R), 'upperarm.r'),
    ('hand.r', tuple(WR_R), tuple(GC), 'lowerarm.r'), ('handslot.r', tuple(GC), tuple(GC + RU * .1), 'hand.r'),
    ('upperleg.l', (-LEGX, .02, .52), (-LEGX, .01, .29), 'hips'), ('lowerleg.l', (-LEGX, .01, .29), (-LEGX, 0, .10), 'upperleg.l'),
    ('foot.l', (-LEGX, 0, .10), (-LEGX, .12, .03), 'lowerleg.l'), ('toes.l', (-LEGX, .12, .03), (-LEGX, .26, .02), 'foot.l'),
    ('upperleg.r', (LEGX, .02, .52), (LEGX, .01, .29), 'hips'), ('lowerleg.r', (LEGX, .01, .29), (LEGX, 0, .10), 'upperleg.r'),
    ('foot.r', (LEGX, 0, .10), (LEGX, .12, .03), 'lowerleg.r'), ('toes.r', (LEGX, .12, .03), (LEGX, .26, .02), 'foot.r'),
    ('prop', tuple(PACK), tuple(PACK + V((0, 0, .3))), 'chest'),
]
RIGID = {'eye.l', 'eye.r'}                    # props ride deforming handslot / prop bones so they follow the pose

def make_rig():
    arm = bpy.data.armatures.new('nsboy_rig'); ob = bpy.data.objects.new('nsboy_rig', arm); bpy.context.scene.collection.objects.link(ob)
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

TRUNK = ([(0, 0, .45), (0, 0, .60), (0, 0, .70), (0, 0, .80), (0, 0, .90), (0, 0, 1.0)], ['hips', 'spine', 'chest', 'neck', 'head'], [.06, .05, .04, .05])
def trunk(p): return chain(p, *TRUNK)
def leg(p, s):
    x = s * LEGX; sd = 'l' if s < 0 else 'r'
    return chain(p, [(x, 0, .62), (x, .01, .29), (x, 0, .10), (x, .12, .03)], ['upperleg.' + sd, 'lowerleg.' + sd, 'foot.' + sd], [.06, .04])
def scale(w, f): return {k: v * f for k, v in w.items()}
def merge(*ws):
    o = {}
    for w in ws:
        for k, v in w.items(): o[k] = o.get(k, 0) + v
    return o

def weights_for(name, p):
    n = name.split('.')[0]; s = -1 if p.x < 0 else 1
    if n.startswith('h_'): return {'head': 1.0}
    if n.startswith('rf_'): return {'handslot.r': 1.0}
    if n.startswith('hand_'): return {'hand.' + n[-1]: 1.0}
    if n.startswith(('arm_', 'sleeve_', 'roll_', 'watch')):
        sd = n[-1]; k = 1 if sd == 'r' else -1; S, E = SHD[k], ELB[k]; W = WR_R if k == 1 else WR_L; tip = GC if k == 1 else FC
        w = chain(p, [S, E, W, tip], ['upperarm.' + sd, 'lowerarm.' + sd, 'hand.' + sd], [.11, .09])
        wc = 1 - ss(-.08, .2, (p - S).dot((E - S).normalized()))
        return merge(scale(w, 1 - wc), {'chest': wc})
    if n.startswith(('pack', 'mat')): return {'prop': 1.0}
    if n in ('torso', 'shirt', 'collar', 'placket', 'button', 'pocket', 'tape', 'rank', 'pstrap'): return trunk(p)
    if n in ('belt', 'buckle', 'bbottle', 'bcap'): return {'hips': 1.0}
    if n == 'trouser':
        u = ss(.52, .40, p.z) * ss(.03, .13, abs(p.x)); return merge(scale(leg(p, s), u), scale({'hips': 1.0}, 1 - u))
    if n.startswith(('tleg', 'tblouse', 'boot', 'lace')):
        w = leg(p, s)
        if n.startswith(('boot_', 'lace')):
            sd = 'l' if s < 0 else 'r'; t = ss(.15, .24, p.y); wf = w.pop('foot.' + sd, 0.0); w['foot.' + sd] = wf * (1 - t); w['toes.' + sd] = wf * t
        h = ss(.44, .52, p.z) if n.startswith('tleg') else 0.0
        return merge(scale(w, 1 - h), {'hips': h})
    print('[weights] unclassified', name); return {'hips': 1.0}

def unjaw(d):                                  # inverse of jaw() on a head-relative offset
    z = d.z if d.z >= -.33 else -.33 + (d.z + .33) / .4; t = ss(-.08, -.33, z)
    return V((d.x / (1 + .10 * t), d.y / (1 + .06 * t), z))

def skin_normal(p):
    """Exact normal of jaw(ellipsoid) at world point p (pre-scale): ellipsoid gradient pushed through the jaw Jacobian."""
    q = unjaw(p - HC); g = V((q.x / HR.x ** 2, q.y / HR.y ** 2, q.z / HR.z ** 2)); e = 1e-4; J = Matrix.Identity(3)
    for k in range(3):
        dq = V((0, 0, 0)); dq[k] = e; c = (jaw(HC + q + dq) - jaw(HC + q - dq)) / (2 * e)
        for r in range(3): J[r][k] = c[r]
    return (J.inverted().transposed() @ g).normalized()

def smooth_skin(head):
    """Weld the face skin ring onto the head hole and give the skin one smooth analytic normal field (no seam, no chin facets)."""
    import bmesh
    from mathutils.kdtree import KDTree
    seam = [jaw(q) * GS for q in LOOP]; kd = KDTree(len(seam))
    for i, q in enumerate(seam): kd.insert(q, i)
    kd.balance(); bm = bmesh.new(); bm.from_mesh(head.data)
    vs = [v for v in bm.verts if kd.find(v.co)[2] < 1e-5]
    n0 = len(bm.verts); bmesh.ops.remove_doubles(bm, verts=vs, dist=1e-5); print('[rig] seam welded', n0 - len(bm.verts), 'of', len(seam))
    bm.to_mesh(head.data); bm.free(); head.data.update()
    me = head.data; skin = {i for i, m in enumerate(me.materials) if m.name.startswith('skin')}
    on = [False] * len(me.vertices)
    for f in me.polygons:
        if f.material_index in skin:
            for i in f.vertices: on[i] = True
    ns = []
    for v in me.vertices:
        p = v.co / GS; q = unjaw(p - HC); r = (q.x / HR.x) ** 2 + (q.y / HR.y) ** 2 + (q.z / HR.z) ** 2
        ns.append(skin_normal(p) if on[v.index] and abs(r - 1) < .02 else v.normal.copy())
    me.normals_split_custom_set_from_vertices(ns)

def stage_rig():
    openb('nsboy_build.blend'); O = bpy.data.objects
    parts = [o for o in O if o.type == 'MESH' and o.name != 'cyc']
    for o in parts:
        o.data.update()
        if not o.data.uv_layers: o.data.uv_layers.new(name='UVMap')        # join keeps only the active object's UV layers
        for v in o.data.vertices:
            for b, w in weights_for(o.name, v.co / GS).items():
                if w > 1e-3:
                    g = o.vertex_groups.get(b) or o.vertex_groups.new(name=b); g.add([v.index], w, 'REPLACE')
    heads = [o for o in parts if o.name.startswith('h_')]; heads.sort(key=lambda o: o.name != 'h_face')
    bodies = [o for o in parts if not o.name.startswith('h_')]
    head = H.join(heads, 'nsboy_head'); body = H.join(bodies, 'nsboy_body'); smooth_skin(head); rig = make_rig()
    for ob in (head, body):
        ob.parent = rig; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = rig
        for v in ob.data.vertices:
            tot = sum(g.weight for g in v.groups)
            if tot < .5: print('[rig] weak vertex', ob.name, v.index, tot)
    for b in rig.data.bones: b.use_deform = b.name not in RIGID
    print('[rig] shape keys', [k.name for k in head.data.shape_keys.key_blocks], 'tris', H.tri_count(head), H.tri_count(body))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'nsboy_rig.blend'))

# ---------------------------------------------------------------- animation (OG.Pose / OG.make_action reused, NSF pose_frame)
X, Y, Zx = OG.X, OG.Y, OG.Z
ar = OG.axis_rot
def basis_rot(u, w):
    u = V(u).normalized(); w = (V(w) - u * V(w).dot(u)).normalized()
    return (Matrix((u, u.cross(w), w)).transposed() @ Matrix((RU, RV, RW))).to_quaternion()   # maps (RU, RV, RW) onto (u, u x w, w)
D_AIM = basis_rot((-.55, 1, 0), (0, 0, 1))
G_AIM = V((.12, .34, .56))     # toy arms are short: blade the chest so the left hand reaches the fore-end
YAW = 65                       # attack and ult turn the body left so the rifle lies across the camera (side-on)

def rest_head(rig, n): return rig.data.bones[n].head_local.copy()
def rest_tail(rig, n): return rig.data.bones[n].tail_local.copy()

def ik_arm(P, rig, sd, W, D, pole):
    S = rig.pose.bones['upperarm.' + sd].head.copy()
    L1 = (rest_tail(rig, 'upperarm.' + sd) - rest_head(rig, 'upperarm.' + sd)).length; L2 = (rest_tail(rig, 'lowerarm.' + sd) - rest_head(rig, 'lowerarm.' + sd)).length
    d = W - S; dist = d.length; dn = d.normalized(); cl = max(abs(L1 - L2) + 1e-4, min(L1 + L2 - 1e-4, dist))
    if abs(cl - dist) > .02 * GS: print('[ik] %s reach %.3f of %.3f' % (sd, dist, L1 + L2))
    a = (L1 * L1 - L2 * L2 + cl * cl) / (2 * cl); h = math.sqrt(max(0.0, L1 * L1 - a * a))
    pn = (pole - dn * pole.dot(dn)).normalized(); E = S + dn * a + pn * h; Wc = S + dn * cl
    P.aim('upperarm.' + sd, E - S); P.aim('lowerarm.' + sd, Wc - E); P.rot('hand.' + sd, P.acc('lowerarm.' + sd).inverted() @ D)

def hold(P, rig, D, G):
    """Both hands on the rifle: the rifle turns by D and its grip centre goes to G (armature space)."""
    bpy.context.view_layer.update()
    gr = rest_head(rig, 'handslot.r'); qc = P.acc('chest')
    for sd in ('r', 'l'):
        Wr = rest_head(rig, 'hand.' + sd); S = rest_head(rig, 'upperarm.' + sd); E = rest_head(rig, 'lowerarm.' + sd)
        pole = qc @ (E - (S + Wr) * .5)
        ik_arm(P, rig, sd, G + D @ (Wr - gr), D, pole)

def port(P, rig):
    """Grip position and rifle rotation of the rest hold, carried by the posed chest."""
    bpy.context.view_layer.update(); ch = rig.pose.bones['chest']; qc = P.acc('chest')
    return qc, ch.head + qc @ (rest_head(rig, 'handslot.r') - rest_head(rig, 'chest'))

def nsf_pose(rig, t, kind):
    P = OG.Pose(rig); s = math.sin(2 * math.pi * t); c = math.cos(2 * math.pi * t)
    if kind == 'idle':                     # at ease with the rifle at port arms: breathe, glance round
        P.rot('spine', ar(X, 1.0 * s)); P.rot('chest', ar(X, 2.0 * s) @ ar(Zx, 1.5 * c)); P.rot('head', ar(X, -1.5 * s) @ ar(Zx, 6.0 * c))
        OG.hips_lift(rig, 0.006 * s)
    elif kind == 'run':                    # double time, rifle held at port arms
        for k, sg in ((-1, 1), (1, -1)):
            sd = 'l' if k < 0 else 'r'
            P.rot('upperleg.' + sd, ar(X, 40 * s * sg)); P.rot('lowerleg.' + sd, ar(X, -60 * max(0.0, -s * sg)))
            P.rot('foot.' + sd, ar(X, 15 * max(0.0, -s * sg)))
        P.rot('spine', ar(X, 6)); P.rot('chest', ar(X, 6) @ ar(Zx, 5 * s)); P.rot('head', ar(X, -10) @ ar(Zx, -4 * s))
        OG.hips_lift(rig, 0.035 * abs(s) - 0.012)
    elif kind == 'attack':                 # snap the rifle up to aim, fire one band (kick), come back to port arms
        r = ss(0, .3, t) * (1 - ss(.72, 1, t)); k = math.sin(math.pi * max(0.0, min(1.0, (t - .32) / .16)))
        Yq = ar(Zx, YAW * r); P.rot('hips', Yq)
        P.rot('spine', ar(X, 3 * r)); P.rot('chest', ar(Zx, -35 * r) @ ar(X, -3 * k)); P.rot('head', ar(Zx, 35 * r) @ ar(X, 3 * r))
        qp, gp = port(P, rig)
        D = Yq @ ar(X, 9 * k) @ (Yq.inverted() @ qp).slerp(D_AIM, r); G = gp.lerp(Yq @ (G_AIM * GS), r) + Yq @ V((0, -.04, .015)) * k * GS
        hold(P, rig, D, G)
    elif kind == 'ult':                    # Live Firing: braced wide stance, rifle up and spraying
        P.rot('upperleg.l', ar(Y, 13) @ ar(X, 12)); P.rot('upperleg.r', ar(Y, -13) @ ar(X, 12))
        P.rot('lowerleg.l', ar(X, -24)); P.rot('lowerleg.r', ar(X, -24)); P.rot('foot.l', ar(X, 12)); P.rot('foot.r', ar(X, 12))
        OG.hips_lift(rig, -0.03 * GS)
        Yq = ar(Zx, YAW); P.rot('hips', Yq)
        P.rot('spine', ar(X, -4)); P.rot('chest', ar(Zx, -35) @ ar(X, -4)); P.rot('head', ar(Zx, 35) @ ar(X, -6))
        hold(P, rig, Yq @ ar(X, 12) @ D_AIM, Yq @ ((G_AIM + V((0, .02, .03))) * GS))
    return P
OG.pose_frame = nsf_pose

def stage_anim():
    openb('nsboy_rig.blend'); SC.render.fps = OG.FPS; rig = bpy.data.objects['nsboy_rig']
    acts = [OG.make_action(rig, 'idle', 'idle', 60), OG.make_action(rig, 'run', 'run', 24), OG.make_action(rig, 'attack', 'attack', 18, loop=False), OG.make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'nsboy_anim.blend')); print('[anim] actions', [a.name for a in acts])

def stage_export():
    openb('nsboy_anim.blend'); O = bpy.data.objects; rig = O['nsboy_rig']; OG.reset_pose(rig)
    for k in O['nsboy_head'].data.shape_keys.key_blocks: k.value = 0.0
    H.select_only([O['nsboy_head'], O['nsboy_body'], rig], rig)
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
    print(f'[verify] tris {sum(H.tri_count(o) for o in meshes)}; X {lo.x:.3f}..{hi.x:.3f} height(Z after import) {hi.z - lo.z:.3f} zmin {lo.z:.3f} depth(Y) {lo.y:.3f}..{hi.y:.3f}')
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
    a = np.concatenate(ims[::-1], axis=0); h, w = a.shape[:2]      # pixel rows run bottom-up, so reverse to keep idle on top
    o = bpy.data.images.new('v', w, h, alpha=False); o.pixels.foreach_set(a.ravel()); o.filepath_raw = out; o.file_format = 'PNG'; o.save()

def stage_shots():
    openb('nsboy_anim.blend'); O = bpy.data.objects; rig = O['nsboy_rig']; head = O['nsboy_head']; cam = O['cam']
    only = [a for a in ARGS if a in ('beauty', 'turn', 'expr', 'sheet', 'hands')]
    want = lambda k: not only or k in only
    play(rig, 'idle', 0); set_key(head, 'none')
    if want('beauty') and only != ['hands']: shoot(cam, os.path.join(SHOTS, 'beauty.png'), 1600, 1600, 32, 8, (0, .2, .9), 2.3, cam_z=.85)
    if only == ['hands']:
        for nm, W in (('r', GC), ('l', FC)): shoot(cam, os.path.join(WORK, 'hand_%s.png' % nm), 700, 700, 0, 7, W * GS, .6)
    if want('turn') and only != ['hands']:
        ps = []
        for i, ang in enumerate((0, 90, 180)):
            rig.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
            t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((0, .12, .9)); p = os.path.join(WORK, 't_%d.png' % i); ps.append(p)
            shoot(cam, p, 534, 800, 0, 9, t, 1.75)
        rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(SHOTS, 'turnaround.png'))
    if want('expr') and only != ['hands']:
        ps = []
        for name in ('smile', 'angry', 'grin', 'ult'):
            set_key(head, name); p = os.path.join(WORK, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, 0, 1.265), 1.3)
        row(ps, os.path.join(SHOTS, 'expressions.png')); set_key(head, 'none')
    if want('sheet') and only != ['hands']:
        rows = []
        for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
            ps = []
            for i in range(4):
                play(rig, name, min(n, int(i * n / 4)) if name != 'ult' else (0 if i < 2 else 2)); p = os.path.join(WORK, 'a_%s_%d.png' % (name, i)); ps.append(p)
                shoot(cam, p, 400, 440, 25, 8, (0, .15, .92), 2.3, cam_z=.9)
            r = os.path.join(WORK, 'arow_%s.png' % name); row(ps, r); rows.append(r)
        vstack(rows, os.path.join(SHOTS, 'anim_sheet.png'))

STAGES = dict(build=stage_build, rig=stage_rig, anim=stage_anim, export=stage_export, verify=stage_verify, shots=stage_shots)
for a in ARGS:
    if a in STAGES: STAGES[a]()
