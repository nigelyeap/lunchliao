"""Delivery Driver (rider), style `toy` (designer vinyl collectible). Game-ready: rig, skin, 6 shape keys, 4 clips, glb.
Run: blender -b -P rider.py -- build rig anim export verify shots      (stages run in the order given)
Axes: Z up, hero faces +Y. Built on gym.py: same toy helpers (styles/toy/ahma_toy.py, exec'd), same face, rig,
weights, animation (heroes/gym.py Pose / make_action) and export. Rider parts: vented half-shell helmet with visor and
chin strap, green zip jacket with reflective band, dark sun sleeves, cube delivery bag on the `prop` bone,
a fan of three giant chopsticks in the right fist and a phone in the left hand. Generic look, no brand marks."""
import bpy, sys, os, math, importlib.util
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HD = os.path.dirname(os.path.abspath(__file__))
RT = os.path.abspath(os.path.join(HD, '..', '..', '..'))
KEY = 'rider'
WORK = os.path.join(HD, '_tmp_rider'); SHOTS = os.path.join(RT, 'shots', 'heroes_toy', KEY); OUT_GLB = os.path.join(RT, 'assets', 'heroes', KEY + '.glb')
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
HEIGHT = 1.80
GS_FILE = os.path.join(WORK, 'gs.txt')
GS = float(open(GS_FILE).read()) if os.path.exists(GS_FILE) else 1.0      # uniform scale, measured in stage_build so the hero is exactly HEIGHT tall

def openb(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, name)); globals()['SC'] = bpy.context.scene

# ---- palette (HEROES body 0x2ebd59 is the jacket, bag and helmet; the rest from the old buildRider) ----
M.update(
    skin=mat('skin', '#DCA174', .42, sss=.12), nose=mat('nose', '#D68E64', .42, sss=.12), blush=mat('blush', '#D9806A', .5),
    hair=mat('hair', '#1D1A22', .3, coat=.35), brow=mat('brow', '#241C20', .45),
    green=mat('green', '#2EBD59', .4, coat=.3), dgreen=mat('dgreen', '#1C7A3A', .45, coat=.2), dchar=mat('dchar', '#1F2226', .4, coat=.4),
    under=mat('under', '#2A2D33', .7), sleeve=mat('sleeve', '#2A2D33', .62), gaiter=mat('gaiter', '#4A4F58', .7),
    refl=mat('reflective', '#D5DAE2', .22, metal=.65), white=mat('white', '#F4F4F2', .35, coat=.2),
    shorts=mat('shorts', '#2B3242', .6), sock=mat('sock', '#F5F3F0', .6), shoe=mat('shoe', '#25282E', .38, coat=.3), sole=mat('sole', '#EFEDE8', .5),
    wood=mat('wood', '#E8D9B0', .5, coat=.2), wrap=mat('wrap', '#F4F1E6', .6),
    case=mat('case', '#1E1A18', .35, coat=.5), screen=mat('screen', '#7FD1C2', .15, coat=1.0), lamp=mat('lamp', '#FFF3B0', .2, coat=.6),
    lip=mat('lip', '#C9625F', .4, coat=.3), mouth=mat('mouth', '#5E1A28', .45),
)

# ---- proportions (pre-scale units, gym's head) ---------------------------------------------------
HC = V((0, 0, 1.30)); HR = V((0.50, 0.47, 0.43))                      # head centre and radii (globals used by surf())
TR = [(.44, .27, .19), (.50, .28, .19), (.58, .30, .20), (.66, .34, .215), (.72, .37, .22), (.76, .365, .21), (.79, .31, .19),
      (.81, .24, .17), (.83, .18, .15), (.88, .155, .14), (.96, .155, .14)]
_a = np.array(TR); ZS = np.linspace(TR[0][0], TR[-1][0], 22); RXs = np.interp(ZS, _a[:, 0], _a[:, 1]); RYs = np.interp(ZS, _a[:, 0], _a[:, 2])
for _ in range(3):
    RXs[1:-1] = (RXs[:-2] + 2 * RXs[1:-1] + RXs[2:]) / 4; RYs[1:-1] = (RYs[:-2] + 2 * RYs[1:-1] + RYs[2:]) / 4
rxz = lambda z: float(np.interp(z, ZS, RXs)); ryz = lambda z: float(np.interp(z, ZS, RYs))
def tsurf(a_deg, z, off):
    a = math.radians(a_deg); return V(((rxz(z) + off) * math.cos(a), (ryz(z) + off) * math.sin(a), z))
ZH = .455                                                              # jacket hem
def jo(z): return .012 + .045 * (1 - ss(ZH, .57, z))                   # jacket offset over the body (flares a little at the hem)
def ztop(a): return .835 - .015 * ss(-.3, .3, math.sin(a))             # jacket neckline (front a touch lower), sleeves are separate

SHD = {1: V((.33, 0, .70)), -1: V((-.33, 0, .70))}
ELB = {s: V((s * .45, .16, .55)) for s in (1, -1)}                    # both arms reach forward to the scooter handlebar
WRI = {s: V((s * .40, .40, .53)) for s in (1, -1)}
GRIP = {s: WRI[s] + (WRI[s] - ELB[s]).normalized() * .10 for s in (1, -1)}   # fist centres on the bar, in line with the forearm
BAR_Y, BAR_Z = GRIP[1].y, GRIP[1].z
GR = GRIP[1]; SN = V((.45, .55, .70)).normalized()                      # chopstick fan axis out of the right fist
FA = (WRI[-1] - ELB[-1]).normalized(); PL = FA; PN = (V((0, 0, 1)) - FA * FA.z).normalized(); PW = PL.cross(PN)
PC = ELB[-1].lerp(WRI[-1], .5); PH = PC + PN * .082                   # wrist phone strapped on top of the left forearm, screen up
TIP = GRIP
LIFT = .16                                                             # scooter deck top above the floor (pre-scale units)
LV = V((0, 0, LIFT))
EXTRA = ('sc_', 'h_umb', 'bag_flag')                                   # scooter, umbrella hat and whip flag: outside the 1.80 body height
LEGX = .15
BAG = V((0, -.43, .64)); BAGS = V((.50, .38, .44))

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

def frame_m(a, b, c): return Matrix((tuple(a), tuple(b), tuple(c))).transposed()     # columns a, b, c

def rb(name, c, size, m, rot=None, bevel=.01, bseg=4):
    ob = rbox(name, c, size, m, bevel=bevel, rot=rot, bseg=bseg); H.apply_transforms(ob); return ob

# ---------------------------------------------------------------- body
def lathe(name, zs, rx, ry, m, seg=28, off=0.0):
    vs = []; fs = []
    for z, a, b in zip(zs, rx, ry):
        for i in range(seg):
            t = 2 * math.pi * i / seg; vs.append(V(((a + off) * math.cos(t), (b + off) * math.sin(t), z)))
    for j in range(len(zs) - 1):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
    fs.append(tuple(range(seg - 1, -1, -1))); return mk(name, vs, fs, m)

def band(name, z0, z1, d_out, d_in, m, seg=40):
    """Closed thick strip round the jacket between z0 and z1 (reflective tape, hem trim)."""
    rings = [[tsurf(360 * i / seg, z, jo(z) + d) for i in range(seg)] for z, d in ((z0, d_in), (z0, d_out), (z1, d_out), (z1, d_in))]
    vs = [p for r in rings for p in r]; fs = []
    for j in range(4):
        k = (j + 1) % 4; fs += [(j * seg + i, j * seg + (i + 1) % seg, k * seg + (i + 1) % seg, k * seg + i) for i in range(seg)]
    return fix_normals(mk(name, vs, fs, m))

def build_torso():
    lathe('torso', ZS, RXs, RYs, M['under'], seg=16)
    seg = 64; J = 9; vs = []; fs = []
    for i in range(seg):                                                    # inner closing ring at the hem
        t = 2 * math.pi * i / seg; vs.append(V((rxz(ZH) * math.cos(t), ryz(ZH) * math.sin(t), ZH)))
    for j in range(J):
        for i in range(seg):
            t = 2 * math.pi * i / seg; z = ZH + (ztop(t) - ZH) * j / (J - 1); off = jo(z)
            vs.append(V(((rxz(z) + off) * math.cos(t), (ryz(z) + off) * math.sin(t), z)))
    for i in range(seg):                                                    # inner closing ring at the neckline
        t = 2 * math.pi * i / seg; zt = ztop(t); vs.append(V(((rxz(zt) - .004) * math.cos(t), (ryz(zt) - .004) * math.sin(t), zt)))
    R = J + 2
    for j in range(R - 1):
        for i in range(seg): fs.append((j * seg + i, (j + 1) * seg + i, (j + 1) * seg + (i + 1) % seg, j * seg + (i + 1) % seg))
    mk('jacket', vs, fs, M['green'])
    band('band_refl', .595, .645, .009, -.002, M['refl'])
    band('band_hem', ZH, ZH + .035, .01, -.004, M['dgreen'])
    zp = [tsurf(90, z, jo(z) + .004) for z in np.linspace(ZH + .02, .815, 12)]
    sweep('zip', zp, .0085, M['refl'], seg=8)
    ell('zip_pull', tsurf(90, .785, jo(.785) + .014), (.013, .007, .022), M['refl'], seg=12)
    # stand collar, white piping, grey neck gaiter above it
    tor('neck_collar', (0, -.005, .825), Z, .19, .034, M['green'], seg=28, rseg=7, squash=(1, .86, 1.3))
    tor('neck_pipe', (0, -.005, .862), Z, .19, .008, M['white'], seg=28, rseg=5, squash=(1, .86, 1))
    ell('neck_gaiter', (0, 0, .89), (.165, .15, .075), M['gaiter'], seg=20)
    for z, R_ in ((.875, .162), (.91, .152)): tor('neck_fold', (0, 0, z), Z, R_, .011, M['gaiter'], seg=20, rseg=4, squash=(1, .91, 1))

def build_legs():
    ell('hips_sh', (0, 0, .45), (.30, .20, .12), M['shorts'], seg=20)
    for s in (-1, 1):
        x = s * LEGX
        sweep('shortleg', [(x, 0, .49), (x, .005, .38), (x, .01, .29)], [.15, .148, .143], M['shorts'], seg=18, lip=(.01, .09))
        tor('shorthem', (x, .01, .292), Z, .144, .009, M['green'], seg=20, rseg=4)
        sweep('calf', [(x, .01, .32), (x, .0, .20), (x, 0, .12)], [.086, .078, .066], M['skin'], seg=14)
        sweep('sock', [(x, 0, .17), (x, 0, .085)], [.08, .076], M['sock'], seg=20, round_caps=False)
        tor('sockcuff', (x, 0, .17), Z, .08, .008, M['green'], seg=16, rseg=4)
        ell('shoe', (x, .07, .075), (.105, .19, .08), M['shoe'], seg=12)
        ell('shoe_sole', (x, .075, .032), (.113, .205, .036), M['sole'], seg=12)
        ell('shoe_tongue', (x, .035, .145), (.045, .05, .028), M['green'], seg=10)
        ell('shoe_heel', (x, -.09, .085), (.045, .028, .045), M['green'], seg=10)
        ell('shoe_lace', (x, .115, .128), (.05, .05, .012), M['white'], rot=Matrix.Rotation(math.radians(-28), 3, 'X'), seg=10)

def sleeve_arm(s):
    sd = 'r' if s > 0 else 'l'; S, E, W = SHD[s], ELB[s], WRI[s]
    so = H.Soup('arm_' + sd); so.sphere(S, .128, seg=20); so.capsule(S, E, .124, .104)
    a, _ = so.remesh(voxel=.011, smooth=5, smooth_factor=.55, target_tris=600); H.set_material(a, M['green']); a.name = 'arm_' + sd; reg(a)
    ax = E - S
    tor('cuff_' + sd, S.lerp(E, .97), ax, .102, .017, M['dgreen'], seg=20, rseg=6)
    tor('sband_' + sd, S.lerp(E, .58), ax, .113, .012, M['refl'], seg=20, rseg=5)
    fo = H.Soup('fore_' + sd); fo.capsule(E, W, .08, .06); fo.sphere(W, .06)
    f, _ = fo.remesh(voxel=.009, smooth=5, smooth_factor=.55, target_tris=420); H.set_material(f, M['sleeve']); f.name = 'fore_' + sd; reg(f)
    tor('wcuff_' + sd, E.lerp(W, .9), W - E, .062, .011, M['gaiter'], seg=24, rseg=6)

def fist(s):
    """Chunky fist wrapped over the handlebar grip: palm behind and above, four fingers over the top and under, thumb under from behind."""
    sd = 'r' if s > 0 else 'l'; sleeve_arm(s); W, G = WRI[s], GRIP[s]
    n, up, fw = V((1, 0, 0)), V((0, 0, 1)), V((0, 1, 0)); rf = .026; rho = .038 + rf
    h = H.Soup('hand_' + sd); palm = G - fw * .052 + up * .036
    h.ellipsoid(palm, (.088, .056, .048), rot=Quaternion())
    h.capsule(W - (G - W).normalized() * .012, palm, .046, .052)          # thinner than the sleeve end, so no skin and sleeve surfaces meet at the cuff
    def arc(ax, phis, rad, r0, r1):
        pts = [G + n * ax + (up * math.cos(math.radians(p)) + fw * math.sin(math.radians(p))) * rad for p in phis]
        m = len(pts) - 1
        for p0, p1, a, b in zip(pts[:-1], pts[1:], [r0] + [rf] * (m - 1), [rf] * (m - 1) + [r1]): h.capsule(p0, p1, a, b, seg=12)
    for k, ax in enumerate((-.066, -.022, .022, .066)):                   # index finger on the inner side
        arc(s * ax, (-55, -5, 45, 95, 145, 185), rho, rf + .003, rf * (.8 if k == 3 else .9))
    arc(-s * .098, (240, 205, 170), .038 + .028, .032, .024)               # thumb
    hd, _ = h.remesh(voxel=.0065, smooth=5, smooth_factor=.5, target_tris=800); H.set_material(hd, M['skin']); hd.name = 'hand_' + sd; reg(hd)

def build_arm_r():
    """Right fist on the bar, clutching the paper-wrapped base of three giant chopsticks that fan out forward and up."""
    fist(1); n = SN; base = GR + V((-.015, -.01, .035))
    sweep('wrap', [base - n * .06, base + n * .13], [.034, .034], M['wrap'], seg=16)
    tor('wrap_band', base + n * .11, n, .035, .006, M['green'], seg=20, rseg=5)
    k = n.cross(V((1, 0, 0))).normalized()
    for a in (-17, 0, 17):
        d = Quaternion(k, math.radians(a)) @ n; b0 = base - n * .04; L = .6
        sweep('stick', [b0, b0 + d * (L - .085)], [.017, .0135], M['wood'], seg=10, round_caps=False)
        sweep('stick_tip', [b0 + d * (L - .09), b0 + d * L], [.0145, .0125], M['dgreen'], seg=6)

def build_arm_l():
    """Left fist on the bar, a phone strapped on top of the forearm with the screen up (the old wrist phone)."""
    fist(-1); R = frame_m(PW, PL, PN); th = .02
    rb('phone', PH, (.095, .14, th), M['case'], rot=R, bevel=.008)
    rb('phone_scr', PH + PN * (th / 2 + .0005), (.081, .122, .002), M['screen'], rot=R, bevel=.0009, bseg=1)
    for dl in (-.042, .042): tor('phone_strap', PC + PL * dl, PL, .075, .009, M['dchar'], seg=16, rseg=4)

def build_bag():
    """Insulated cube bag on the back (prop bone): green box, dark green lid, reflective band, plain fork-and-spoon badge."""
    rb('bag', BAG, BAGS, M['green'], bevel=.05, bseg=5)
    rb('bag_lid', BAG + V((0, 0, BAGS.z / 2 + .005)), (BAGS.x + .02, BAGS.y + .02, .05), M['dgreen'], bevel=.02, bseg=4)
    rb('bag_band', BAG + V((0, 0, .06)), (BAGS.x + .008, BAGS.y + .008, .04), M['refl'], bevel=.012, bseg=3)
    by = BAG.y - BAGS.y / 2
    sweep('bag_badge', [(0, by + .002, .58), (0, by - .01, .58)], [.088, .088], M['white'], seg=32, round_caps=False)
    fy = by - .013
    sweep('bag_icon', [(.03, fy, .615), (.03, fy, .535)], .0065, M['dgreen'], seg=5)          # spoon
    ell('bag_icon', (.03, fy, .63), (.019, .005, .027), M['dgreen'], seg=8)
    sweep('bag_icon', [(-.03, fy, .608), (-.03, fy, .535)], .0065, M['dgreen'], seg=6)         # fork
    sweep('bag_icon', [(-.047, fy, .62), (-.013, fy, .62)], .007, M['dgreen'], seg=6)
    for x in (-.044, -.03, -.016): sweep('bag_icon', [(x, fy, .62), (x, fy, .66)], .0045, M['dgreen'], seg=6)
    rb('bag_handle', BAG + V((0, 0, BAGS.z / 2 + .04)), (.16, .03, .025), M['dchar'], bevel=.01, bseg=3)
    # shoulder straps: bag top, over the shoulder, down the chest, under the arm, back to the bag
    path = [(-78, .80), (-50, .815), (-18, .825), (15, .823), (42, .80), (60, .73), (65, .63), (65, .53), (45, .475), (10, .47), (-30, .48), (-60, .52), (-78, .57)]
    pts = catmull([tsurf(a, z, jo(z) + .02) for a, z in path], 2)
    for sg in (1, -1): sweep('strap', [V((sg * p.x, p.y, p.z)) for p in pts], .02, M['dchar'], seg=6, round_caps=False)
    cl = [tsurf(a, .655, jo(.655) + .028) for a in np.linspace(65, 115, 9)]
    sweep('strap_chest', cl, .012, M['dchar'], seg=6)
    rb('strap_clip', tsurf(90, .655, jo(.655) + .036), (.05, .018, .03), M['dgreen'], bevel=.008, bseg=3)
    # whip flag up the back left corner of the bag (old buildRider), clear of the umbrella hat
    fx, fy, ft = -.27, -.615, 2.30
    sweep('bag_flag_pole', [(fx, fy, .52), (fx, fy, ft)], .013, M['dchar'], seg=8)
    for z in (.60, .80): tor('bag_flag_clip', (fx, fy, z), Z, .019, .006, M['dchar'], seg=12, rseg=4)
    ell('bag_flag_knob', (fx, fy, ft + .01), (.026, .026, .026), M['green'], seg=12)
    def pennant(name, a, b, c, m, w):
        P = [V(a), V(b), V(c)]; vs = [p + V((d, 0, 0)) for d in (-w, w) for p in P]
        mk(name, vs, [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)], m)
    pennant('bag_flag', (fx, fy - .01, ft - .02), (fx, fy - .47, ft - .12), (fx, fy - .01, ft - .25), M['green'], .005)
    pennant('bag_flag_in', (fx, fy - .05, ft - .065), (fx, fy - .29, ft - .12), (fx, fy - .05, ft - .19), M['white'], .008)

def build_scooter():
    """Delivery kick scooter under his feet (old buildRider): dark deck with green grip top, two wheels with white hubs and fenders,
    silver stem, white front fairing with a headlamp, dark handlebar with grips where his fists sit. Floor is at z = -LIFT."""
    fz = -LIFT; wz = fz + .18
    rb('sc_deck', (0, -.02, -.04), (.52, 1.0, .07), M['dchar'], bevel=.03, bseg=3)
    rb('sc_deck_top', (0, -.02, -.008), (.46, .9, .02), M['green'], bevel=.008, bseg=2)
    for y in (.72, -.72):
        tor('sc_tyre', (0, y, wz), V((1, 0, 0)), .12, .062, M['dchar'], seg=20, rseg=6)
        sweep('sc_hub', [(-.05, y, wz), (.05, y, wz)], .075, M['white'], seg=16, round_caps=False)
        sweep('sc_axle', [(-.075, y, wz), (.075, y, wz)], .022, M['refl'], seg=8, round_caps=False)
        arc = [(0, y + .23 * math.cos(math.radians(a)), wz + .23 * math.sin(math.radians(a))) for a in np.linspace(15 if y > 0 else 0, 165 if y > 0 else 180, 10)]
        sweep('sc_fender', arc, .034, M['white'], seg=6, round_caps=False)
        sweep('sc_fork', [(0, y - .26 * (1 if y > 0 else -1), -.03), (0, y, wz)], .03, M['dchar'], seg=6)
    S0 = V((0, .72, wz + .02)); S1 = V((0, BAR_Y, BAR_Z)); sd = (S1 - S0).normalized()
    sweep('sc_stem', [S0, S1], .036, M['refl'], seg=12)
    tilt = Matrix.Rotation(math.atan2(-sd.y, sd.z), 3, 'X')
    fc = S0.lerp(S1, .42) + V((0, .045, 0))
    rb('sc_fairing', fc, (.42, .05, .38), M['white'], rot=tilt, bevel=.02, bseg=3)
    lc = S0.lerp(S1, .72) + V((0, .07, 0)); ln = V((0, sd.z, -sd.y))
    sweep('sc_lamp', [lc - ln * .01, lc + ln * .025], .085, M['lamp'], seg=20, round_caps=False)
    tor('sc_lamp_ring', lc + ln * .02, ln, .088, .014, M['dgreen'], seg=16, rseg=4)
    sweep('sc_bar', [(-.47, BAR_Y, BAR_Z), (.47, BAR_Y, BAR_Z)], .024, M['dchar'], seg=10)
    for s in (-1, 1): sweep('sc_grip', [(s * .30, BAR_Y, BAR_Z), (s * .48, BAR_Y, BAR_Z)], .036, M['dchar'], seg=8)

def build_body_all():
    build_torso(); build_legs(); build_arm_r(); build_arm_l(); build_bag(); build_scooter()

# ---------------------------------------------------------------- head
HOLE = (0.0, -.245, .215, .14)

def jaw(p):                                   # square jaw: widen and flatten the lower head. p is a world point
    d = p - HC; t = ss(-.08, -.33, d.z); z = d.z
    if z < -.33: z = -.33 + (z + .33) * .4
    return HC + V((d.x * (1 + .24 * t), d.y * (1 + .14 * t), z))

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

# helmet: ellipsoid shell around the head, rim high at the front (over the brows), low at the back
HCH = HC + V((0, -.015, .035)); HRH = V((.56, .54, .50))
def rim_el(az_deg): return float(np.interp(abs(az_deg), [0, 40, 90, 140, 180], [32, 26, 8, -10, -18]))
def hp(az_deg, el_deg, s=1.0):
    a, e = math.radians(az_deg), math.radians(el_deg)
    return HCH + V((math.sin(a) * math.cos(e) * HRH.x * s, math.cos(a) * math.cos(e) * HRH.y * s, math.sin(e) * HRH.z * s))
def head_pt(az_deg, el_deg, off=0.0):
    a, e = math.radians(az_deg), math.radians(el_deg); d = V((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    p = jaw(HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z))); return p + (p - HC).normalized() * off

def build_helmet():
    NA, NE = 44, 9; vs = []; fs = []
    for s in (1.0, .93):
        for j in range(NE):
            for i in range(NA):
                az = 360 * i / NA - 180; e0 = rim_el(az); vs.append(hp(az, e0 + (88 - e0) * (j / (NE - 1)) ** .85, s))
    po, pi_ = len(vs), len(vs) + 1; vs += [HCH + V((0, 0, HRH.z)), HCH + V((0, 0, HRH.z * .93))]
    for L in (0, 1):
        o = L * NE * NA
        for j in range(NE - 1):
            fs += [(o + j * NA + i, o + j * NA + (i + 1) % NA, o + (j + 1) * NA + (i + 1) % NA, o + (j + 1) * NA + i) for i in range(NA)]
        top = o + (NE - 1) * NA; fs += [(top + i, top + (i + 1) % NA, po if L == 0 else pi_) for i in range(NA)]
    fs += [(i, NE * NA + i, NE * NA + (i + 1) % NA, (i + 1) % NA) for i in range(NA)]                 # rim strip
    fix_normals(mk('h_helmet', vs, fs, M['green']))
    ring('h_rim', [hp(360 * i / 48 - 180, rim_el(360 * i / 48 - 180), .965) for i in range(48)], .023, M['dchar'], seg=5)
    for x0, p0, p1 in ((-.25, 62, 118), (-.1, 48, 135), (.1, 48, 135), (.25, 62, 118)):            # four vent slots front to back
        k = math.sqrt(1 - (x0 / HRH.x) ** 2); ry, rz = HRH.y * k - .006, HRH.z * k - .006
        sweep('h_vent', [HCH + V((x0, ry * math.cos(math.radians(p)), rz * math.sin(math.radians(p)))) for p in np.linspace(p0, p1, 5)], .022, M['dchar'], seg=5)
    # visor: short dark peak following the front rim, tucked under it
    N = 26; vv = []; ff = []
    for i in range(N):
        az = -56 + 112 * i / (N - 1); o = V((math.sin(math.radians(az)), math.cos(math.radians(az)), 0))
        b = hp(az, rim_el(az) - 1.5, .985) - o * .01; dep = .035 + .085 * math.cos(math.radians(az / 56 * 90)) ** .7
        t = b + o * dep - V((0, 0, .03 * dep / .12))
        vv += [b + V((0, 0, .009)), t + V((0, 0, .006)), t - V((0, 0, .006)), b - V((0, 0, .009))]
    for i in range(N - 1): ff += [(4 * i + k, 4 * i + (k + 1) % 4, 4 * (i + 1) + (k + 1) % 4, 4 * (i + 1) + k) for k in range(4)]
    ff += [(0, 1, 2, 3), tuple(4 * (N - 1) + k for k in (3, 2, 1, 0))]
    fix_normals(mk('h_visor', vv, ff, M['dchar']))
    # chin strap: from the rim in front of each ear, down the jaw, under the chin
    side = [(77, 9), (75, -10), (68, -33), (52, -54), (28, -67)]
    path = [head_pt(a, e, .012) for a, e in side] + [head_pt(0, -71, .012)] + [head_pt(-a, e, .012) for a, e in reversed(side)]
    sweep('h_strap', catmull(path, 3), .011, M['dchar'], seg=5)
    for s in (-1, 1): ell('h_buckle', head_pt(s * 74, -18, .02), (.018, .018, .026), M['dchar'], seg=10)

def build_head():
    head_surface(); build_helmet()
    # short hair: a smooth band hugging the head under the helmet rim, temples round the back, gently scalloped lower edge
    NA, NR = 40, 6; az0 = 64; ring_ = []
    for i in range(NA):
        az = az0 + (360 - 2 * az0) * i / (NA - 1); az = az - 360 if az > 180 else az
        e0 = rim_el(az) + 3; e1 = rim_el(az) - 16                                 # straight clean nape line, no scallops
        tp = min(1.0, (abs(abs(az) - az0)) / 14)                                  # taper to nothing at the temples
        es = [e0 + (e1 - e0) * tp * j / (NR - 1) for j in range(NR)]
        outer = [head_pt(az, e, .004 + .016 * math.sqrt(max(0.0, 1 - (j / (NR - 1)) ** 2)) * tp) for j, e in enumerate(es)]   # rounded lip at the nape
        inner = [head_pt(az, e, -.012) for e in reversed(es)]
        ring_.append(outer + inner)
    K = 2 * NR; vs = [p for r in ring_ for p in r]; fs = []
    for i in range(NA - 1): fs += [(i * K + k, (i + 1) * K + k, (i + 1) * K + (k + 1) % K, i * K + (k + 1) % K) for k in range(K)]
    fs += [tuple(range(K)), tuple((NA - 1) * K + k for k in reversed(range(K)))]
    fix_normals(mk('h_hair', vs, fs, M['hair']))
    for s in (-1, 1): ell('h_ear', HC + V((s * .49, -.03, -.04)), (.04, .075, .095), M['skin'], seg=12)
    ell('h_bud', HC + V((.52, -.02, -.035)), (.022, .028, .028), M['dchar'], seg=14)
    p, n_, t, u = surf(0, -.085); ell('h_nose', p + n_ * .004, (.06, .05, .05), M['nose'], seg=18)
    build_umbrella()

def build_umbrella():
    """Umbrella hat on a short pole above the helmet: eight wedges, green and white alternating, green knob (old buildRider)."""
    c = HCH + V((0, 0, HRH.z)); top = c.z + .255; R, Hc = .55, .14; N = 32; rs = (0.0, .25, .6, 1.0)
    sweep('h_umb_pole', [c - V((0, 0, .03)), c + V((0, 0, .2))], .016, M['dchar'], seg=8)
    vs = []; fs = []; mi = []
    for lay, dz in ((0, 0.0), (1, -.014)):
        for j, r in enumerate(rs):
            for i in range(N):
                a = 2 * math.pi * i / N; rr = R * r * (1 - .025 * math.cos(a * 8) * r)
                vs.append(V((c.x + rr * math.cos(a), c.y + rr * math.sin(a), top - Hc * r ** 1.25 + dz - .012 * r ** 4)))
    NR = len(rs)
    for lay in (0, 1):
        o = lay * NR * N
        for j in range(NR - 1):
            for i in range(N):
                q = (o + j * N + i, o + j * N + (i + 1) % N, o + (j + 1) * N + (i + 1) % N, o + (j + 1) * N + i)
                fs.append(q if lay == 0 else q[::-1]); mi.append((i * 8 // N) % 2)
    o = (NR - 1) * N
    for i in range(N): fs.append((o + i, o + NR * N + i, o + NR * N + (i + 1) % N, o + (i + 1) % N)); mi.append((i * 8 // N) % 2)
    fix_normals(mk('h_umb', vs, fs, [M['white'], M['green']], mat_idx=mi))
    ell('h_umb_knob', V((c.x, c.y, top + .012)), (.034, .034, .03), M['green'], seg=12)

# ---------------------------------------------------------------- face (one mesh, six shape keys; gym's build)
FM = ['skin', 'brow', 'eye', 'white', 'line', 'mouth', 'lip', 'teeth', 'tongue', 'blush']
EXe, EZe = .185, -.02
_I = dict(bz=.145, tilt=.02, arch=.004, eye='bead', es=(.8, .72), cut=(.02, 0), hl=.006, w=.19, curve=.03, up=0, dn=0, teeth=0, tongue=0, cz=-.235, arc=.058)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'eye': 'arc', 'arc': -.022, 'bz': .15},
    'mouth_open': {**_I, 'w': .2, 'curve': .012, 'up': .006, 'dn': .085, 'teeth': .032, 'tongue': .05},
    'smile': {**_I, 'w': .25, 'curve': .05, 'bz': .175, 'tilt': -.01},
    'angry': dict(bz=.055, tilt=.085, arch=-.004, eye='bead', es=(1.08, .95), cut=(.012, .6), hl=.0, w=.2, curve=-.052, up=.018, dn=.05, teeth=.034, tongue=0, cz=-.24, arc=.058),
    'grin': dict(bz=.19, tilt=-.012, arch=.034, eye='arc', es=(1, 1), cut=None, hl=.026, w=.32, curve=.06, up=.004, dn=.085, teeth=.034, tongue=.05, cz=-.25, arc=.062),
    'ult': dict(bz=.13, tilt=.095, arch=.012, eye='bead', es=(1.12, 1.08), cut=None, hl=.01, w=.22, curve=-.004, up=.06, dn=.105, teeth=.034, tongue=.06, cz=-.245, arc=.058),   # battle shout: wide eyes, hard brows, round open mouth
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
    add([HC.copy(), HC.copy(), HC.copy()], [(0, 1, 2)], 'line')
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
    print('TOY_TOP', sorted(agg.items(), key=lambda kv: -kv[1]))
    zs = [v.co.z for o in HERO if not o.name.startswith(EXTRA) for v in o.data.vertices]; gs = HEIGHT / (max(zs) - min(zs))
    globals()['GS'] = gs; open(GS_FILE, 'w').write(repr(gs)); print('[build] natural body height', max(zs) - min(zs), 'GS', gs)
    for o in HERO:                                  # scale to 1.80 body height, then lift so the scooter wheels sit on the floor
        for v in o.data.vertices: v.co = (v.co + LV) * GS
        if o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks:
                for v in kb.data: v.co = (v.co + LV) * GS
    za = [v.co.z for o in HERO for v in o.data.vertices]; zb = [v.co.z for o in HERO if not o.name.startswith(EXTRA) for v in o.data.vertices]
    print('[build] body height %.3f, total height with umbrella and flag %.3f, floor %.3f' % (max(zb) - min(zb), max(za) - min(za), min(za)))
    stage()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'rider_build.blend'))

# ---------------------------------------------------------------- rig + weights
def eyepos(s): return surf(s * EXe, EZe)[0]
BONES = [
    ('root', (0, 0, -LIFT), (0, 0, .25 - LIFT), None), ('hips', (0, 0, .50), (0, 0, .60), 'root'), ('spine', (0, 0, .60), (0, 0, .70), 'hips'),
    ('chest', (0, 0, .70), (0, 0, .80), 'spine'), ('neck', (0, 0, .80), (0, .01, .90), 'chest'), ('head', (0, .01, .90), (0, .02, 1.74), 'neck'),
    ('eye.l', tuple(eyepos(-1)), tuple(eyepos(-1) + V((0, .06, 0))), 'head'), ('eye.r', tuple(eyepos(1)), tuple(eyepos(1) + V((0, .06, 0))), 'head'),
    ('upperarm.l', tuple(SHD[-1]), tuple(ELB[-1]), 'chest'), ('lowerarm.l', tuple(ELB[-1]), tuple(WRI[-1]), 'upperarm.l'),
    ('hand.l', tuple(WRI[-1]), tuple(GRIP[-1]), 'lowerarm.l'), ('handslot.l', tuple(GRIP[-1]), tuple(GRIP[-1] + V((0, .08, 0))), 'hand.l'),
    ('upperarm.r', tuple(SHD[1]), tuple(ELB[1]), 'chest'), ('lowerarm.r', tuple(ELB[1]), tuple(WRI[1]), 'upperarm.r'),
    ('hand.r', tuple(WRI[1]), tuple(GR), 'lowerarm.r'), ('handslot.r', tuple(GR), tuple(GR + SN * .1), 'hand.r'),
    ('upperleg.l', (-LEGX, .02, .52), (-LEGX, .01, .29), 'hips'), ('lowerleg.l', (-LEGX, .01, .29), (-LEGX, 0, .10), 'upperleg.l'),
    ('foot.l', (-LEGX, 0, .10), (-LEGX, .12, .03), 'lowerleg.l'), ('toes.l', (-LEGX, .12, .03), (-LEGX, .26, .02), 'foot.l'),
    ('upperleg.r', (LEGX, .02, .52), (LEGX, .01, .29), 'hips'), ('lowerleg.r', (LEGX, .01, .29), (LEGX, 0, .10), 'upperleg.r'),
    ('foot.r', (LEGX, 0, .10), (LEGX, .12, .03), 'lowerleg.r'), ('toes.r', (LEGX, .12, .03), (LEGX, .26, .02), 'foot.r'),
    ('prop', tuple(BAG), tuple(BAG + V((0, 0, .3))), 'chest'),
]
RIGID = {'eye.l', 'eye.r'}

def make_rig():
    arm = bpy.data.armatures.new('rider_rig'); ob = bpy.data.objects.new('rider_rig', arm); bpy.context.scene.collection.objects.link(ob)
    H.select_only([ob], ob); bpy.ops.object.mode_set(mode='EDIT')
    for name, h, t, parent in BONES:
        b = arm.edit_bones.new(name); b.head = (V(h) + LV) * GS; b.tail = (V(t) + LV) * GS
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
    if n.startswith(('stick', 'wrap')): return {'handslot.r': 1.0}
    if n.startswith('phone'): return {'lowerarm.l': 1.0}
    if n.startswith('sc_'): return {'root': 1.0}
    if n.startswith('bag'): return {'prop': 1.0}
    if n.startswith('hand_'): return {'hand.' + n[-1]: 1.0}
    if n.startswith(('arm_', 'cuff_', 'sband_', 'fore_', 'wcuff_')):
        sd = n[-1]; k = 1 if sd == 'r' else -1; S, E, W = SHD[k], ELB[k], WRI[k]
        w = chain(p, [S, E, W, TIP[k]], ['upperarm.' + sd, 'lowerarm.' + sd, 'hand.' + sd], [.09, .06])
        wc = 1 - ss(-.08, .16, (p - S).dot((E - S).normalized()))
        return merge(scale(w, 1 - wc), {'chest': wc})
    if n in ('torso', 'jacket', 'zip', 'zip_pull') or n.startswith(('band', 'neck', 'strap')): return trunk(p)
    if n == 'hips_sh':
        u = ss(.52, .40, p.z) * ss(.03, .13, abs(p.x)); return merge(scale(leg(p, s), u), scale({'hips': 1.0}, 1 - u))
    if n.startswith(('shortleg', 'shorthem', 'calf', 'sock', 'shoe')):
        w = leg(p, s)
        if n.startswith('shoe'):
            sd = 'l' if s < 0 else 'r'; t = ss(.15, .24, p.y); wf = w.pop('foot.' + sd); w['foot.' + sd] = wf * (1 - t); w['toes.' + sd] = wf * t
        h = ss(.44, .52, p.z) if n.startswith(('shortleg', 'shorthem')) else 0.0
        return merge(scale(w, 1 - h), {'hips': h})
    print('[weights] unclassified', name); return {'hips': 1.0}

def stage_rig():
    openb('rider_build.blend'); O = bpy.data.objects
    parts = [o for o in O if o.type == 'MESH' and o.name != 'cyc']
    for o in parts:
        o.data.update()
        for v in o.data.vertices:
            for b, w in weights_for(o.name, v.co / GS - LV).items():
                if w > 1e-3:
                    g = o.vertex_groups.get(b) or o.vertex_groups.new(name=b); g.add([v.index], w, 'REPLACE')
    heads = [o for o in parts if o.name.startswith('h_')]; heads.sort(key=lambda o: o.name != 'h_face')
    bodies = [o for o in parts if not o.name.startswith('h_')]
    head = H.join(heads, 'rider_head'); body = H.join(bodies, 'rider_body')
    import bmesh   # weld the face skin ring onto the head rim (same position in every shape key) so shading runs smooth across it
    bm = bmesh.new(); bm.from_mesh(head.data); hc = (HC + LV) * GS; bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if (v.co - hc).length > .05], dist=1e-5)   # hidden face parts parked at HC stay apart
    bm.to_mesh(head.data); bm.free()
    rig = make_rig()
    for ob in (head, body):
        ob.parent = rig; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = rig
        weak = sum(1 for v in ob.data.vertices if sum(g.weight for g in v.groups) < .5)
        if weak: print('[rig] weak vertices', ob.name, weak)
    for b in rig.data.bones: b.use_deform = b.name not in RIGID
    print('[rig] shape keys', [k.name for k in head.data.shape_keys.key_blocks], 'tris', H.tri_count(head), H.tri_count(body))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'rider_rig.blend'))

# ---------------------------------------------------------------- animation (OG.Pose / OG.make_action reused, all four clips are rider poses)
_W = lambda p: (V(p) + LV) * GS                      # pre-scale body point to armature space
def _rest_dir(a, b): return (V(b) - V(a)).normalized()
RU, RL_ = _rest_dir(SHD[1], ELB[1]), _rest_dir(ELB[1], WRI[1])
def _mix(a, b, t): return V(a).normalized().lerp(V(b).normalized(), t).normalized()

def grip_world(rig, s):
    """Where the bar grip is now: it rides on the root bone with the scooter."""
    r = rig.pose.bones['root']; return r.matrix @ rig.data.bones['root'].matrix_local.inverted() @ _W(GRIP[s])

def reach(P, rig, s):
    """Two-bone reach: keep the fist on its handlebar grip whatever the body does."""
    sd = 'r' if s > 0 else 'l'; bpy.context.view_layer.update()
    S = rig.pose.bones['upperarm.' + sd].head.copy(); T = grip_world(rig, s)
    S0, E0, G0 = _W(SHD[s]), _W(ELB[s]), _W(GRIP[s]); a = (E0 - S0).length; b = (G0 - E0).length
    d = T - S; L = min(d.length, (a + b) * .999); u = d.normalized()
    ca = (a * a + L * L - b * b) / (2 * a * L); sa = math.sqrt(max(0.0, 1 - ca * ca))
    pole = (E0 - S0) - u * (E0 - S0).dot(u); pole = pole.normalized() if pole.length > 1e-6 else V((s, 0, -1)).normalized()
    E = S + u * a * ca + pole * a * sa
    P.aim('upperarm.' + sd, E - S); P.aim('lowerarm.' + sd, S + u * L - E)

def root_lift(rig, dz):
    pb = rig.pose.bones['root']; pb.location = rig.data.bones['root'].matrix_local.to_3x3().inverted() @ V((0, 0, dz))

def rider_pose(rig, t, kind):
    """Note: a positive X rotation tips a bone's top toward -Y (back), a leg's foot toward +Y (forward)."""
    P = OG.Pose(rig); X_, Y_, Z_ = OG.X, OG.Y, OG.Z; R = OG.axis_rot; s = math.sin(2 * math.pi * t); c = math.cos(2 * math.pi * t)
    if kind == 'idle':                         # riding: breathe, bob, look around, glance down at the wrist phone, hands stay on the bar
        g = ss(.48, .58, t) * (1 - ss(.78, .88, t))
        P.rot('chest', R(X_, 1.5 * s)); P.rot('head', R(X_, -1.0 * s - 14 * g) @ R(Z_, 4 * c * (1 - g) + 24 * g))
        OG.hips_lift(rig, .006 * s); reach(P, rig, 1); reach(P, rig, -1)
    elif kind == 'run':                        # kick-push: right foot swings back off the deck and pushes, left leg planted, knee giving
        u = .5 - .5 * c
        P.rot('upperleg.r', R(X_, -40 * u)); P.rot('lowerleg.r', R(X_, -35 * max(0.0, -s))); P.rot('foot.r', R(X_, 25 * u))
        P.rot('upperleg.l', R(X_, 18 * u)); P.rot('lowerleg.l', R(X_, -36 * u)); P.rot('foot.l', R(X_, 18 * u))
        OG.hips_lift(rig, -.022 * u)
        P.rot('spine', R(X_, -5)); P.rot('chest', R(X_, -4 - 3 * u) @ R(Z_, 3 * s)); P.rot('head', R(X_, 6) @ R(Z_, -2 * s))
        reach(P, rig, 1); reach(P, rig, -1)
    elif kind == 'attack':                     # Chopstick Fan flick: right fist leaves the bar, cocks the fan up and back, snaps it forward, returns
        WU, WL = (.85, -.25, .45), (.35, -.35, .87); SU, SL = (.4, .9, .2), (.15, .99, .02)
        if t < .4: u = ss(0, 1, t / .4); U, L = _mix(RU, WU, u), _mix(RL_, WL, u); tw, ln = -18 * u, -6 * u
        elif t < .55: u = (t - .4) / .15; U, L = _mix(WU, SU, u), _mix(WL, SL, u); tw, ln = -18 + 34 * u, -6 + 18 * u
        else: u = ss(0, 1, (t - .55) / .45); U, L = _mix(SU, RU, u), _mix(SL, RL_, u); tw, ln = 16 * (1 - u), 12 * (1 - u)
        P.rot('spine', R(X_, -ln * .4)); P.rot('chest', R(X_, -ln * .6) @ R(Z_, tw)); P.rot('head', R(Z_, -tw * .6))
        P.aim('upperarm.r', U); P.aim('lowerarm.r', L); reach(P, rig, -1)
    elif kind == 'ult':                        # Peak Hour Rush: scooter pops a wheelie on the back wheel, chopstick fan punched high, left fist on the bar
        th = 16; P.rot('root', R(X_, th)); root_lift(rig, .72 * GS * math.sin(math.radians(th)) + .004)
        P.rot('spine', R(X_, -7)); P.rot('chest', R(X_, -6) @ R(Z_, -10)); P.rot('head', R(X_, -4) @ R(Z_, 8))
        P.rot('upperleg.l', R(X_, 10)); P.rot('lowerleg.l', R(X_, -20)); P.rot('foot.l', R(X_, 10))
        P.aim('upperarm.r', (1, .05, .2)); P.aim('lowerarm.r', (.75, .25, .6)); reach(P, rig, -1)
    return P
OG.pose_frame = rider_pose
if 'root' not in OG.ANIM_BONES: OG.ANIM_BONES.insert(0, 'root')

def stage_anim():
    openb('rider_rig.blend'); SC.render.fps = OG.FPS; rig = bpy.data.objects['rider_rig']
    acts = [OG.make_action(rig, 'idle', 'idle', 60), OG.make_action(rig, 'run', 'run', 24), OG.make_action(rig, 'attack', 'attack', 18, loop=False), OG.make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'rider_anim.blend')); print('[anim] actions', [a.name for a in acts])

def stage_export():
    openb('rider_anim.blend'); O = bpy.data.objects; rig = O['rider_rig']; OG.reset_pose(rig)
    for k in O['rider_head'].data.shape_keys.key_blocks: k.value = 0.0
    H.select_only([O['rider_head'], O['rider_body'], rig], rig)
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

# ---------------------------------------------------------------- shots (gym's stage and cameras, targets scaled to this hero)
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
    openb('rider_anim.blend'); O = bpy.data.objects; rig = O['rider_rig']; head = O['rider_head']; cam = O['cam']
    only = [a for a in ARGS if a in ('beauty', 'turn', 'expr', 'sheet', 'hands')]
    want = lambda k: not only or k in only
    hz = (HC.z + LIFT) * GS
    play(rig, 'idle', 0); set_key(head, 'none')
    if 'hands' in only:
        for nm, W in (('r', GR), ('l', GRIP[-1])): shoot(cam, os.path.join(WORK, 'hand_%s.png' % nm), 700, 700, 35 if nm == 'r' else -35, 7, (W + LV) * GS, .55)
        shoot(cam, os.path.join(WORK, 'back.png'), 900, 900, 160, 8, (0, 0, 1.2), 2.7)
    if want('beauty') and 'hands' not in only: shoot(cam, os.path.join(SHOTS, 'beauty.png'), 1600, 1600, 32, 9, (0, .05, 1.2), 2.75, cam_z=1.15)
    if want('turn') and 'hands' not in only:
        ps = []
        for i, ang in enumerate((0, 90, 180)):
            rig.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
            t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((0, .0, 1.22)); p = os.path.join(WORK, 't_%d.png' % i); ps.append(p)
            shoot(cam, p, 534, 800, 0, 10, t, 1.85)
        rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(SHOTS, 'turnaround.png'))
    if want('expr') and 'hands' not in only:
        ps = []
        for name in ('smile', 'angry', 'grin', 'ult'):
            set_key(head, name); p = os.path.join(WORK, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, 0, hz + .02), 1.3)
        row(ps, os.path.join(SHOTS, 'expressions.png')); set_key(head, 'none')
    if want('sheet') and 'hands' not in only:
        rows = []
        for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
            ps = []
            for i in range(4):
                play(rig, name, min(n, int(i * n / 4)) if name != 'ult' else (0 if i < 2 else 2)); p = os.path.join(WORK, 'a_%s_%d.png' % (name, i)); ps.append(p)
                shoot(cam, p, 400, 440, 25, 10, (0, .05, 1.22), 2.85, cam_z=1.2)
            r = os.path.join(WORK, 'arow_%s.png' % name); row(ps, r); rows.append(r)
        vstack(rows, os.path.join(SHOTS, 'anim_sheet.png'))

STAGES = dict(build=stage_build, rig=stage_rig, anim=stage_anim, export=stage_export, verify=stage_verify, shots=stage_shots)
for a in ARGS:
    if a in STAGES: STAGES[a]()
