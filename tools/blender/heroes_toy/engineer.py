"""Engineer Encik, style `toy` (designer vinyl collectible). Game-ready: rig, skin, 6 shape keys, 4 clips, glb.
Run: blender -b -P engineer.py -- build rig anim export verify shots      (stages run in the order given)
Axes: Z up, hero faces +Y. Built on heroes_toy/gym.py: same toy helpers (exec'd from styles/toy/ahma_toy.py),
same face mesh and shape keys, same rig, weights, Pose / make_action and export code.
Look: navy short-sleeve work shirt and trousers (HEROES body 0x23395b), lime hi-vis vest with silver bands,
white hard hat with a crest, moustache, tool belt with spanner, foam dart blaster (R), red toolbox (L), clipboard on the back."""
import bpy, sys, os, math, importlib.util, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HD = os.path.dirname(os.path.abspath(__file__))
RT = os.path.abspath(os.path.join(HD, '..', '..', '..'))
KEY = 'engineer'
WORK = os.path.join(HD, '_tmp_' + KEY); SHOTS = os.path.join(RT, 'shots', 'heroes_toy', KEY); OUT_GLB = os.path.join(RT, 'assets', 'heroes', KEY + '.glb')
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
GSF = os.path.join(WORK, 'gs.json')
GS = json.load(open(GSF))['gs'] if os.path.exists(GSF) else 1.0      # final uniform scale, measured in stage_build

def openb(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, name)); globals()['SC'] = bpy.context.scene

# ---- palette ----------------------------------------------------------------------------------
M.update(
    skin=mat('skin', '#B07650', .42, sss=.08), nose=mat('nose', '#A66C48', .42, sss=.08), blush=mat('blush', '#B0625A', .52),
    hair=mat('hair', '#1D1A22', .45, coat=.12), brow=mat('brow', '#211A1E', .45),
    navy=mat('navy', '#23395B', .55), navyd=mat('navy_dark', '#1A2A44', .6),
    lime=mat('lime', '#D4F03C', .4, coat=.25), steel=mat('steel', '#C9CFD6', .25, metal=.85), band=mat('band', '#DDE2E8', .3, coat=.6),
    hat=mat('hat', '#F4F3EF', .25, coat=.7), boot=mat('boot', '#5A3A26', .5, coat=.2), sole=mat('sole', '#2E2A28', .6), pad=mat('pad', '#2E2A28', .55),
    belt=mat('belt', '#5A3A26', .55), pouch=mat('pouch', '#8A5A2B', .55), tape=mat('tape', '#F2B630', .35, coat=.4),
    tbox=mat('toolbox', '#B8442A', .35, coat=.5), tboxd=mat('toolbox_dark', '#6E2E1A', .45), grip=mat('grip', '#2E2A28', .7),
    white=mat('white', '#F7F6F2', .3, coat=.3), dart=mat('dart', '#7FD15A', .35, coat=.4), red=mat('red', '#D63A3A', .45),
    board=mat('board', '#8A5A2B', .5), paper=mat('paper', '#FBF8F0', .6), photo=mat('photo', '#8FB6E0', .4),
    lip=mat('lip', '#A85A52', .4, coat=.3), mouth=mat('mouth', '#5E1A28', .45),
)

# ---- proportions: barrel build, soft round belly ---------------------------------------------
HC = V((0, 0, 1.30)); HR = V((0.50, 0.47, 0.43))                      # head centre and radii (globals used by surf())
TR = [(.44, .30, .24), (.50, .325, .27), (.56, .35, .295), (.62, .36, .30), (.68, .35, .28), (.73, .32, .24), (.77, .27, .205),
      (.80, .215, .18), (.83, .18, .16), (.88, .17, .155), (.96, .17, .155)]
_a = np.array(TR); ZS = np.linspace(TR[0][0], TR[-1][0], 22); RXs = np.interp(ZS, _a[:, 0], _a[:, 1]); RYs = np.interp(ZS, _a[:, 0], _a[:, 2])
for _ in range(3):
    RXs[1:-1] = (RXs[:-2] + 2 * RXs[1:-1] + RXs[2:]) / 4; RYs[1:-1] = (RYs[:-2] + 2 * RYs[1:-1] + RYs[2:]) / 4
rxz = lambda z: float(np.interp(z, ZS, RXs)); ryz = lambda z: float(np.interp(z, ZS, RYs))
def belly(a, z): return 1 + .13 * max(0.0, math.sin(a)) ** 2 * ss(.42, .55, z) * (1 - ss(.64, .76, z))      # front bulge only
def tpt(a, z, off):                          # point on the body (a in radians) pushed out by off
    return V(((rxz(z) + off) * math.cos(a), (ryz(z) * belly(a, z) + off) * math.sin(a), z))
def tsurf(a_deg, z, off): return tpt(math.radians(a_deg), z, off)

ZH = .45                                     # shirt hem (tucked under the belt)
def zshirt(a):                               # short-sleeve work shirt: round neck at the neck base, armholes at the joint
    c = abs(math.cos(a)); f = ss(-.3, .3, math.sin(a)); z = .855 - .02 * f
    return z - ss(.92, .995, c) ** 1.2 * (z - .58)
ZV = .50                                     # vest hem
def zvest(a):                                # hi-vis vest: deep V at the front, narrow shoulder straps, wide armholes
    c = abs(math.cos(a)); d = abs(a % (2 * math.pi) - math.pi / 2)
    z = .845 - .02 * ss(-.3, .3, math.sin(a)) - .175 * ss(0, 1, max(0.0, 1 - d / .44))
    return z - ss(.80, .97, c) ** 1.2 * (z - .655)

SHD = {1: V((.40, 0, .70)), -1: V((-.40, 0, .70))}
ELB = {1: V((.52, -.03, .47)), -1: V((-.53, -.02, .48))}
CG = V((.47, .29, .40)); WR_R = CG + V((0, -.10, .075))                   # blaster grip centre (vertical) and right wrist
CBL = V((-.575, .03, .30)); WR_L = V((-.55, .02, .40))                    # toolbox handle centre (along Y) and left wrist
LEGX = .175; CLIP = V((0, -.33, .60))

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
def lathe_body(name, m, seg=20):
    vs = []; fs = []
    for z in ZS:
        for i in range(seg): vs.append(tpt(2 * math.pi * i / seg, z, 0))
    for j in range(len(ZS) - 1):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
    fs.append(tuple(range(seg - 1, -1, -1))); return mk(name, vs, fs, m)

def shell(name, zlo, ztop, off, m, seg=112, J=8):
    """One closed garment: inner ring at the hem, J outer rings up to the top edge, inner ring at the top edge (real thickness)."""
    vs = []; fs = []
    for i in range(seg): vs.append(tpt(2 * math.pi * i / seg, zlo, off(zlo) - .014))
    for j in range(J):
        for i in range(seg):
            t = 2 * math.pi * i / seg; zt = ztop(t); z = zlo + (zt - zlo) * j / (J - 1); vs.append(tpt(t, z, off(z)))
    for i in range(seg):
        t = 2 * math.pi * i / seg; zt = ztop(t); vs.append(tpt(t, zt, off(zt) - .014))
    R = J + 2
    for j in range(R - 1):
        for i in range(seg): fs.append((j * seg + i, (j + 1) * seg + i, (j + 1) * seg + (i + 1) % seg, j * seg + (i + 1) % seg))
    return mk(name, vs, fs, m)

def strip(name, z0, h, off, m, seg=64):
    """Reflective band lying on the vest: edges tucked into the vest, raised middle."""
    prof = [(-h, off - .006), (-h * .7, off + .005), (h * .7, off + .005), (h, off - .006)]; vs = []; fs = []
    for dz, o in prof:
        for i in range(seg): vs.append(tpt(2 * math.pi * i / seg, z0 + dz, o))
    for j in range(len(prof) - 1):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
    return mk(name, vs, fs, m)

def build_torso():
    lathe_body('torso', M['skin'])
    shell('shirt', ZH, zshirt, lambda z: .014 + .012 * ss(.76, .85, z), M['navy'], seg=72, J=7)
    ring('collar', [tpt(2 * math.pi * i / 48, zshirt(2 * math.pi * i / 48) - .004, .03) for i in range(48)], .02, M['navy'], seg=6)
    shell('vest', ZV, zvest, lambda z: .042 + .012 * (1 - ss(ZV, .56, z)) + .01 * ss(.76, .85, z), M['lime'], seg=80, J=8)
    ring('vpipe', [tpt(2 * math.pi * i / 64, zvest(2 * math.pi * i / 64), .045 + .01 * ss(.76, .85, zvest(2 * math.pi * i / 64))) for i in range(64)], .008, M['band'], seg=5)
    for z0 in (.545, .615): strip('vband', z0, .019, .054 + .012 * (1 - ss(ZV, .56, z0)), M['band'])
    # zip line down the front of the vest, under the V
    sweep('vzip', [tpt(math.pi / 2, z, .058) for z in (ZV + .01, .58, .66)], .007, M['navyd'], seg=6)
    # lanyard and ID card in the V of the vest
    card = tpt(math.pi / 2, .705, .05)
    for sg in (-1, 1):
        pts = [tpt(math.radians(90 - sg * 52), .842, .035), tpt(math.radians(90 - sg * 30), .80, .032), tpt(math.radians(90 - sg * 9), .765, .036)]
        sweep('lanyard', pts + [card + V((sg * .012, .004, .045))], .0075, M['red'], seg=6)
    rbox('idcard', card, (.075, .012, .095), M['white'], bevel=.008, bseg=2)
    rbox('idphoto', card + V((0, .007, .012)), (.042, .004, .04), M['photo'], bevel=.004, bseg=1)
    # tool belt: band, buckle, pouch, tape measure, spanner on the left hip
    ring('belt', [V((.355 * math.cos(t), .30 * math.sin(t), .475)) for t in [2 * math.pi * i / 48 for i in range(48)]], .03, M['belt'], seg=6)
    rbox('buckle', (0, .325, .475), (.09, .02, .065), M['steel'], bevel=.01, bseg=2)
    rbox('buckle_in', (0, .332, .475), (.05, .012, .03), M['belt'], bevel=.006, bseg=1)
    r = Matrix.Rotation(math.radians(-38), 3, 'Z')
    rbox('pouch', (.30, .19, .40), (.10, .11, .13), M['pouch'], bevel=.025, rot=r)
    rbox('pouch_flap', (.30, .19, .455), (.11, .12, .04), M['belt'], bevel=.015, rot=r)
    ax = V((math.cos(math.radians(-25)), math.sin(math.radians(-25)), 0)) * 0 + V((1, 0, 0))
    sweep('tape', [(-.24, .25, .43), (-.24, .30, .43)], .055, M['tape'], seg=18)
    ell('tape_hub', (-.24, .306, .43), (.022, .006, .022), M['grip'], seg=12)
    # spanner hanging on the left hip: handle down, open jaw on top
    sp = [V((-.335, .02, .44)), V((-.35, .03, .30))]
    sweep('spanner', sp, [.016, .014], M['steel'], seg=8)
    tor('spanner_jaw', V((-.333, .02, .47)), (0, 1, 0), .032, .012, M['steel'], seg=16, rseg=6)
    tor('spanner_ring', V((-.352, .03, .275)), (0, 1, 0), .022, .009, M['steel'], seg=14, rseg=6)
    # clipboard slung on the back
    rc = Matrix.Rotation(math.radians(-8), 3, 'X')
    rbox('clip_board', CLIP, (.24, .02, .30), M['board'], bevel=.01, rot=rc, bseg=2)
    rbox('clip_paper', CLIP + V((0, -.012, -.015)), (.20, .006, .24), M['paper'], bevel=.003, rot=rc, bseg=1)
    rbox('clip_clamp', CLIP + V((0, -.016, .135)), (.10, .02, .035), M['steel'], bevel=.008, rot=rc, bseg=2)
    for sg in (-1, 1):
        pts = [tpt(math.radians(-90 + sg * 25), .69, .062), tpt(math.radians(-90 + sg * 55), .76, .06), tpt(math.radians(90 - sg * 55 - 180 * 0) if False else math.radians(-90 + sg * 80), .82, .05)]
        sweep('clip_strap', pts, .011, M['belt'], seg=6)

def build_legs():
    ell('hips_sh', (0, 0, .44), (.345, .27, .12), M['navy'], seg=20)
    for s in (-1, 1):
        x = s * LEGX
        sweep('trouser', [(x, 0, .49), (x, .005, .36), (x, .01, .22), (x, .0, .13)], [.17, .158, .145, .14], M['navy'], seg=24, lip=(.01, .12))
        kp = rbox('kneepad', (x, .17, .29), (.12, .03, .13), M['navyd'], bevel=.014, bseg=3)
        for v in kp.data.vertices: v.co.y -= v.co.x ** 2 / (2 * .16)       # wrap the flat pad round the knee
        tor('kneestrap', (x, .008, .29), Z, .155, .007, M['navyd'], seg=24, rseg=4)
        bo = H.Soup('boot'); bo.ellipsoid(V((x, .06, .10)), (.13, .2, .1)); bo.ellipsoid(V((x, .16, .09)), (.115, .11, .08))
        bo.capsule(V((x, -.005, .10)), V((x, -.005, .19)), .124, .124)
        bt, _ = bo.remesh(voxel=.012, smooth=6, smooth_factor=.5, target_tris=700); H.set_material(bt, M['boot']); bt.name = 'boot'; reg(bt)
        tor('boot_collar', (x, .004, .185), Z, .112, .014, M['boot'], seg=18, rseg=5)       # sits inside the trouser hem, no notches
        ell('boot_sole', (x, .065, .032), (.138, .215, .036), M['sole'], seg=14)

def build_arm(k):
    sd = 'r' if k == 1 else 'l'; S, E = SHD[k], ELB[k]; W = WR_R if k == 1 else WR_L
    so = H.Soup('arm_' + sd); so.sphere(S, .105, seg=24); so.capsule(S, E, .104, .098); so.capsule(E, W, .098, .07); so.sphere(W, .07)
    a, _ = so.remesh(voxel=.011, smooth=5, smooth_factor=.55, target_tris=900); H.set_material(a, M['skin']); a.name = 'arm_' + sd; reg(a)
    d = (E - S).normalized()
    s0 = S - d * .02 + V((0, 0, .015)); A = [math.radians(x) for x in (84, 72, 60, 48, 36, 24, 12)]   # fine shoulder dome (sweep's own cap has 3 rings)
    sweep('sleeve_' + sd, [s0 - d * .135 * math.sin(t) for t in A] + [s0, S.lerp(E, .62)], [.135 * math.cos(t) for t in A] + [.135, .122], M['navy'],
          seg=32, round_caps=False, lip=(.012, .105))
    tor('cuff_' + sd, S.lerp(E, .62) - d * .006, d, .121, .011, M['lime'], seg=24, rseg=6)
    tor('watch_' + sd, E.lerp(W, .82), W - E, .074, .013, M['grip'], seg=20, rseg=6) if k == -1 else None

def build_hand_r():
    """Right fist round the blaster grip: palm behind, four fingers round the outer side to the front, thumb over the inner side."""
    palm = CG + V((0, -.072, .005)); h = H.Soup('hand_r'); h.ellipsoid(palm, (.06, .046, .1)); h.capsule(WR_R, palm + V((0, 0, .04)), .07, .064)
    rr = .036 + .021; rf = .021
    def arc(z, th, rho, ra, rb):
        pts = [V((CG.x + rho * math.cos(math.radians(t)), CG.y + rho * math.sin(math.radians(t)), z)) for t in th]
        for p0, p1, r0, r1 in zip(pts[:-1], pts[1:], [ra] + [rf] * 5, [rf] * 4 + [rb]): h.capsule(p0, p1, r0, r1, seg=12)
    for k, dz in enumerate((.072, .024, -.024, -.072)):
        arc(CG.z + dz, (290, 345, 40, 85, 125), rr, rf + .002, rf * (.85 if k == 3 else .95))
    arc(CG.z + .118, (235, 190, 160, 128), .036 + .026, .032, .022)
    arc(CG.z + .088, (205, 155, 105, 60, 25), .036 + .042, .031, .024)        # thumb wraps over the front and lies on the index finger, visible from outside
    hd, _ = h.remesh(voxel=.0065, smooth=5, smooth_factor=.5, target_tris=750); H.set_material(hd, M['skin']); hd.name = 'hand_r'; reg(hd)
    # foam dart blaster: navy grip, lime body, white barrel and drum, green dart tip
    sweep('bl_grip', [CG + V((0, -.01, -.11)), CG + V((0, .015, .10))], [.034, .037], M['navyd'], seg=14)
    rbox('bl_body', CG + V((0, .12, .165)), (.105, .36, .115), M['lime'], bevel=.03, bseg=3)
    rbox('bl_stripe', CG + V((0, .12, .165)), (.11, .07, .12), M['navy'], bevel=.02, bseg=2)
    sweep('bl_barrel', [CG + V((0, .29, .165)), CG + V((0, .45, .165))], .034, M['white'], seg=16)
    tor('bl_muzzle', CG + V((0, .45, .165)), (0, 1, 0), .034, .01, M['navy'], seg=18, rseg=6)
    ell('bl_dart', CG + V((0, .475, .165)), (.026, .03, .026), M['dart'], seg=12)
    sweep('bl_drum', [CG + V((-.062, .07, .245)), CG + V((.062, .07, .245))], .055, M['white'], seg=18)
    for x in (-.064, .064): ell('bl_drumcap', CG + V((x, .07, .245)), (.01, .036, .036), M['navy'], seg=12)
    tor('bl_guard', CG + V((0, .07, .07)), (1, 0, 0), .04, .009, M['navyd'], seg=16, rseg=6)
    sweep('bl_trigger', [CG + V((0, .055, .10)), CG + V((0, .062, .065))], .009, M['steel'], seg=6)

def build_hand_l():
    """Left fist hooked round the toolbox handle (handle runs along Y): fingers curl under it from the inner side, thumb over the top."""
    palm = CBL + V((.035, 0, .045)); h = H.Soup('hand_l'); h.ellipsoid(palm, (.045, .085, .065)); h.capsule(WR_L, palm, .07, .062)
    rf = .021; rho = .016 + .021
    for k, dy in enumerate((-.051, -.017, .017, .051)):
        pts = [V((CBL.x + rho * math.cos(math.radians(t)), CBL.y + dy, CBL.z + rho * math.sin(math.radians(t)))) for t in (55, 5, -55, -115, -170)]
        r = rf * (.85 if k in (0, 3) else 1.0)
        for p0, p1, r0, r1 in zip(pts[:-1], pts[1:], [r + .002, r, r, r], [r, r, r, r * .9]): h.capsule(p0, p1, r0, r1, seg=12)
    tp = [palm + V((-.01, .07, .02)), CBL + V((-.005, .085, .045)), CBL + V((-.035, .07, .03))]
    for p0, p1, r0, r1 in zip(tp[:-1], tp[1:], (.03, .026), (.026, .022)): h.capsule(p0, p1, r0, r1, seg=12)
    hd, _ = h.remesh(voxel=.0065, smooth=5, smooth_factor=.5, target_tris=750); H.set_material(hd, M['skin']); hd.name = 'hand_l'; reg(hd)
    # red toolbox hanging below the hand
    sweep('tbox_handle', [CBL + V((0, -.09, 0)), CBL + V((0, .09, 0))], .016, M['grip'], seg=10)
    for dy in (-.09, .09): sweep('tbox_post', [CBL + V((0, dy, .0)), CBL + V((0, dy, -.06))], .014, M['grip'], seg=8)
    bc = CBL + V((0, 0, -.135))
    rbox('tbox', bc, (.15, .38, .145), M['tbox'], bevel=.022, bseg=3)
    rbox('tbox_lid', bc + V((0, 0, .06)), (.158, .388, .035), M['tboxd'], bevel=.012, bseg=2)
    for dy in (-.11, .11): rbox('tbox_latch', bc + V((-.08, dy, .045)), (.014, .04, .04), M['steel'], bevel=.006, bseg=1)

def build_neck():
    ell('neck_col', (0, 0, .88), (.2, .18, .12), M['skin'], seg=20)

def build_body_all():
    build_torso(); build_legs(); build_arm(1); build_arm(-1); build_hand_r(); build_hand_l(); build_neck()

# ---------------------------------------------------------------- head
HOLE = (0.0, -.245, .215, .14)

def jaw(p):                                   # soft full jaw: a little wider and rounder low down
    d = p - HC; t = ss(-.08, -.33, d.z); z = d.z
    if z < -.35: z = -.35 + (z + .35) * .5
    return HC + V((d.x * (1 + .12 * t), d.y * (1 + .1 * t), z))

HOLE_AB = (.19, .125)

def _head_grid():
    vs, fs = sph_vf(48, 24); Q = [HC + V((v.x * HR.x, v.y * HR.y, v.z * HR.z)) for v in vs]
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
    keep = [f for f in keep if sum(P[i].z for i in f) / len(f) < HATC.z + .05]
    used = sorted({i for f in keep for i in f}); remap = {o: n for n, o in enumerate(used)}
    ob = mk('h_head', [P[i] for i in used], [tuple(remap[i] for i in f) for f in keep], M['skin'])
    ob.data.normals_split_custom_set_from_vertices([snormal(Q[i]) for i in used])   # analytic normals: smooth cheeks and jaw at no tri cost
    return ob

def snormal(q, e=.004):
    """Normal of the jawed head surface at ellipsoid point q, by central differences through jaw()."""
    d = q - HC; n = V((d.x / HR.x ** 2, d.y / HR.y ** 2, d.z / HR.z ** 2)).normalized()
    t1 = (V((0, 0, 1)).cross(n) if abs(n.z) < .95 else V((1, 0, 0)).cross(n)).normalized(); t2 = n.cross(t1)
    m = (jaw(q + t1 * e) - jaw(q - t1 * e)).cross(jaw(q + t2 * e) - jaw(q - t2 * e)).normalized()
    return tuple(m if m.dot(n) > 0 else -m)

HATC = HC + V((0, -.015, .215)); HATR = V((.495, .475, .30))             # hard hat dome (upper half ellipsoid)
def build_hat():
    n = 40; rows = 10; vs = []; fs = []
    for j in range(rows + 1):
        el = math.radians(-6 + 96 * j / rows) if j < rows else math.pi / 2
        for i in range(n):
            t = 2 * math.pi * i / n; vs.append(HATC + V((HATR.x * math.cos(el) * math.cos(t), HATR.y * math.cos(el) * math.sin(t), HATR.z * math.sin(el))))
    for j in range(rows):
        for i in range(n): fs.append((j * n + i, j * n + (i + 1) % n, (j + 1) * n + (i + 1) % n, (j + 1) * n + i))
    mk('h_hat', vs, fs, M['hat'])
    # brim: closed section swept round the base, longer peak at the front
    prof = [(-.03, .02), (0.0, .012), (1.0, -.03), (1.0, -.052), (0.0, -.022), (-.03, -.01)]
    vs = []; fs = []; z0 = HATC.z - .03
    for i in range(n * 2):
        t = 2 * math.pi * i / (n * 2); L = .095 + .085 * max(0.0, math.sin(t)) ** 2 - .02 * max(0.0, -math.sin(t))
        base = V((HATR.x * math.cos(t) * .99, HATR.y * math.sin(t) * .99, 0)); dirv = V((math.cos(t), math.sin(t), 0))
        for d, dz in prof: vs.append(V((HATC.x, HATC.y, z0)) + base + dirv * (d * L if abs(d) > .5 else d) + V((0, 0, dz)))
    P = len(prof)
    for i in range(n * 2):
        j = (i + 1) % (n * 2)
        for k in range(P): fs.append((i * P + k, j * P + k, j * P + (k + 1) % P, i * P + (k + 1) % P))
    mk('h_brim', vs, fs, M['hat'])
    pts = [HATC + V((0, HATR.y * math.cos(math.radians(a)) * 1.0, HATR.z * math.sin(math.radians(a)) * 1.0)) for a in range(25, 170, 12)]
    sweep('h_ridge', pts, [.03] * len(pts), M['hat'], seg=10)
    p = HATC + V((0, HATR.y * math.cos(math.radians(32)), HATR.z * math.sin(math.radians(32))))
    nrm = V((0, math.cos(math.radians(32)) / HATR.y, math.sin(math.radians(32)) / HATR.z)).normalized()
    rot = V((0, 1, 0)).rotation_difference(nrm).to_matrix()
    rbox('h_badge', p + nrm * .002, (.12, .02, .065), M['lime'], bevel=.012, rot=rot, bseg=2)
    rbox('h_badge_in', p + nrm * .01, (.07, .012, .025), M['navy'], bevel=.006, rot=rot, bseg=1)

def build_head():
    head_surface()
    # short-crop hair: one smooth band round the sides and back, edges tuck into the skin, soft scallop on the lower edge
    na, ne = 64, 8; vs = []; fs = []
    def hp(az, el, off):
        a, e = math.radians(az), math.radians(el)
        d = V((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))); q = jaw(HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z)))
        n_ = V((d.x / HR.x, d.y / HR.y, d.z / HR.z)).normalized(); return q + n_ * off
    PRO = [-.004 + .03 * math.sqrt(max(0.0, 1 - (1 - k / ne) ** 2)) for k in range(ne + 1)]   # rounded lip at the nape, edge tucks into the skin
    for i in range(na + 1):
        u = i / na; az = 52 + 256 * u; a2 = az if az <= 180 else 360 - az
        lo = float(np.interp(a2, [52, 70, 100, 140, 180], [14, 7, 0, -9, -14]))                    # clean gently curved nape line
        hi = 27.0; tp = ss(0, .08, u) * ss(1, .92, u)
        for k in range(ne + 1):
            el = lo + (hi - lo) * (k / ne) ** 1.3; vs.append(hp(az, el, -.006 + (PRO[k] + .006) * tp))
    for i in range(na):
        for k in range(ne): fs.append((i * (ne + 1) + k, i * (ne + 1) + k + 1, (i + 1) * (ne + 1) + k + 1, (i + 1) * (ne + 1) + k))
    mk('h_hair', vs, fs, M['hair'])
    for s in (-1, 1):
        ell('h_ear', HC + V((s * .49, -.03, -.05)), (.045, .075, .095), M['skin'], seg=14)
    p, n_, t, u = surf(0, -.085); ell('h_nose', p + n_ * .006, (.068, .056, .056), M['nose'], seg=18)
    build_hat()

# ---------------------------------------------------------------- face (one mesh, six shape keys)
FM = ['skin', 'brow', 'eye', 'white', 'line', 'mouth', 'lip', 'teeth', 'tongue', 'blush']
EXe, EZe = .185, -.02
_I = dict(bz=.115, tilt=.0, arch=.016, eye='bead', es=(.86, .86), cut=None, hl=.006, w=.19, curve=.03, up=0, dn=0, teeth=0, tongue=0, cz=-.25, arc=.058, mz=0.0)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'eye': 'arc', 'arc': -.022, 'bz': .115},
    'mouth_open': {**_I, 'w': .2, 'curve': .012, 'up': .006, 'dn': .085, 'teeth': .032, 'tongue': .05},
    'smile': {**_I, 'w': .25, 'curve': .05, 'bz': .13, 'tilt': -.01, 'mz': .01},
    'angry': dict(bz=.045, tilt=.095, arch=-.006, eye='bead', es=(1.08, .95), cut=(.012, .62), hl=.0, w=.2, curve=-.055, up=.016, dn=.05, teeth=.034, tongue=0, cz=-.255, arc=.058, mz=-.012),
    'grin': dict(bz=.14, tilt=-.012, arch=.034, eye='arc', es=(1, 1), cut=None, hl=.026, w=.32, curve=.06, up=.004, dn=.085, teeth=.034, tongue=.05, cz=-.265, arc=.062, mz=.014),
    'ult': dict(bz=.135, tilt=.06, arch=.004, eye='bead', es=(1.0, 1.0), cut=(.02, 0), hl=.008, w=.27, curve=.006, up=.03, dn=.105, teeth=.034, tongue=.07, cz=-.265, arc=.058, mz=0.0),
}

LOOP = hole_loop()

def face_geo(e):
    vs = []; fs = []; mi = []
    def add(v, f, m):
        o = len(vs); vs.extend(v); fs.extend([tuple(i + o for i in ff) for ff in f]); mi.extend([FM.index(m)] * len(f))
    def hide(v): return [HC.copy() for _ in v]
    def stroke(pts, rw, rn, off, m, show=True, seg=8, pw=.45):
        P = [surf(x, z, off) for x, z in pts]; n = len(P); v = []
        for i in range(n):
            p, nn, _, _ = P[i]; tan = (P[min(i + 1, n - 1)][0] - P[max(i - 1, 0)][0]).normalized(); side = nn.cross(tan).normalized()
            f = math.sin(math.pi * i / (n - 1)) ** pw if 0 < i < n - 1 else 0.0
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
        stroke([(s * (EXe + q * .105), e['bz'] + EZe + q * e['tilt'] + e['arch'] * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .058, .032, .006, 'brow')
        bead = e['eye'] == 'bead'; a, c = .06 * e['es'][0], .075 * e['es'][1]
        blob(s * EXe, EZe, (a, .036, c), 0, 'eye', show=bead, seg=16, cut=(e['cut'][0], e['cut'][1] * s) if e['cut'] else None)
        blob(s * EXe, EZe, (.012, .01, .012), .028, 'white', show=bead, seg=10, d=(.016, e['hl'] + .01))
        blob(s * EXe, EZe, (.005, .004, .005), .026, 'white', show=bead, seg=6, d=(-.02, -.02))
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
    # moustache: two thick lobes riding on the upper lip, ends follow the mouth curve
    mzc = e['cz'] + U + .048 + e['mz']
    for s in (-1, 1):
        pts = [(s * x, mzc - .012 * (x / .13) ** 2 + .6 * e['curve'] * (x / .16) ** 2 * (1 if e['curve'] > 0 else 1.4) - .02 * ss(.08, .14, x)) for x in np.linspace(.004, .145, 9)]
        stroke(pts, .03, .022, .012, 'brow', pw=.55)
    globals()['_FACE_RAW'] = vs
    return [jaw(q) for q in vs], fs, mi

KEYS = ['blink', 'mouth_open', 'smile', 'angry', 'grin', 'ult']
def build_face():
    vs, fs, mi = face_geo(EXPR['idle'])
    ob = mk('h_face', vs, fs, [M[k] for k in FM], mat_idx=mi)
    raw = list(_FACE_RAW); bad = {i for f, m in zip(fs, mi) if FM[m] != 'skin' for i in f}
    ob.data.normals_split_custom_set_from_vertices([(0, 0, 0) if i in bad else snormal(raw[i]) for i in range(len(vs))])   # match h_head at the patch seam
    ob.shape_key_add(name='Basis')
    for name in KEYS:
        k = ob.shape_key_add(name=name); k.data.foreach_set('co', [c for v in face_geo(EXPR[name])[0] for c in v])
    return ob

# ---------------------------------------------------------------- build stage
def stage_build():
    build_body_all(); build_head(); build_face()
    for o in HERO:                                   # rbox places by matrix: bake every transform into the mesh
        if o.matrix_world != Matrix.Identity(4): o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    tris = sum(H.tri_count(o) for o in HERO); print('TOY_TRIS', tris, 'objects', len(HERO))
    agg = {}
    for o in HERO: agg[o.name.split('.')[0]] = agg.get(o.name.split('.')[0], 0) + H.tri_count(o)
    print('TOY_TOP', sorted(agg.items(), key=lambda kv: -kv[1])[:40])
    lo = min(v.co.z for o in HERO for v in o.data.vertices); hi = max(v.co.z for o in HERO for v in o.data.vertices)
    xs = max(abs(v.co.x) for o in HERO for v in o.data.vertices)
    gs = HEIGHT / (hi - lo); globals()['GS'] = gs; json.dump({'gs': gs, 'lo': lo, 'hi': hi}, open(GSF, 'w'))
    print('TOY_SIZE local lo %.3f hi %.3f |x| %.3f -> GS %.4f, |x| final %.3f' % (lo, hi, xs, gs, xs * gs))
    for o in HERO:
        for v in o.data.vertices: v.co *= GS
        if o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks:
                for v in kb.data: v.co *= GS
    stage()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, KEY + '_build.blend'))

# ---------------------------------------------------------------- rig + weights
def eyepos(s): return surf(s * EXe, EZe)[0]
BONES = [
    ('root', (0, 0, 0), (0, 0, .25), None), ('hips', (0, 0, .50), (0, 0, .60), 'root'), ('spine', (0, 0, .60), (0, 0, .70), 'hips'),
    ('chest', (0, 0, .70), (0, 0, .80), 'spine'), ('neck', (0, 0, .80), (0, .01, .90), 'chest'), ('head', (0, .01, .90), (0, .02, 1.74), 'neck'),
    ('eye.l', tuple(eyepos(-1)), tuple(eyepos(-1) + V((0, .06, 0))), 'head'), ('eye.r', tuple(eyepos(1)), tuple(eyepos(1) + V((0, .06, 0))), 'head'),
    ('upperarm.l', tuple(SHD[-1]), tuple(ELB[-1]), 'chest'), ('lowerarm.l', tuple(ELB[-1]), tuple(WR_L), 'upperarm.l'),
    ('hand.l', tuple(WR_L), tuple(CBL), 'lowerarm.l'), ('handslot.l', tuple(CBL), tuple(CBL + V((0, .08, 0))), 'hand.l'),
    ('upperarm.r', tuple(SHD[1]), tuple(ELB[1]), 'chest'), ('lowerarm.r', tuple(ELB[1]), tuple(WR_R), 'upperarm.r'),
    ('hand.r', tuple(WR_R), tuple(CG + V((0, .02, 0))), 'lowerarm.r'), ('handslot.r', tuple(CG), tuple(CG + V((0, .1, 0))), 'hand.r'),
    ('upperleg.l', (-LEGX, .02, .52), (-LEGX, .01, .29), 'hips'), ('lowerleg.l', (-LEGX, .01, .29), (-LEGX, 0, .10), 'upperleg.l'),
    ('foot.l', (-LEGX, 0, .10), (-LEGX, .12, .03), 'lowerleg.l'), ('toes.l', (-LEGX, .12, .03), (-LEGX, .26, .02), 'foot.l'),
    ('upperleg.r', (LEGX, .02, .52), (LEGX, .01, .29), 'hips'), ('lowerleg.r', (LEGX, .01, .29), (LEGX, 0, .10), 'upperleg.r'),
    ('foot.r', (LEGX, 0, .10), (LEGX, .12, .03), 'lowerleg.r'), ('toes.r', (LEGX, .12, .03), (LEGX, .26, .02), 'foot.r'),
    ('prop', tuple(CLIP), tuple(CLIP + V((0, 0, .3))), 'chest'),
]
RIGID = {'eye.l', 'eye.r'}

def make_rig():
    arm = bpy.data.armatures.new(KEY + '_rig'); ob = bpy.data.objects.new(KEY + '_rig', arm); bpy.context.scene.collection.objects.link(ob)
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
    if n.startswith('bl_'): return {'handslot.r': 1.0}
    if n.startswith('tbox'): return {'handslot.l': 1.0}
    if n.startswith('clip'): return {'prop': 1.0}
    if n.startswith('hand_'): return {'hand.' + n[-1]: 1.0}
    if n.startswith(('sleeve_', 'cuff_')): return {'upperarm.' + n[-1]: 1.0}    # rigid: nearest-segment lookup pulled the cuff side onto the forearm
    if n.startswith(('arm_', 'watch_')):
        sd = n[-1]; k = 1 if sd == 'r' else -1; S, E = SHD[k], ELB[k]; W = WR_R if k == 1 else WR_L; tip = CG if k == 1 else CBL
        w = chain(p, [S, E, W, tip], ['upperarm.' + sd, 'lowerarm.' + sd, 'hand.' + sd], [.09, .07])
        return w                                       # rigid on the arm chain: any chest blend stretched the shoulder ball through the sleeve when raised
    if n in ('torso', 'shirt', 'vest', 'collar', 'vpipe', 'vband', 'vzip', 'lanyard', 'idcard', 'idphoto', 'belt', 'buckle', 'buckle_in',
             'pouch', 'pouch_flap', 'tape', 'tape_hub', 'spanner', 'spanner_jaw', 'spanner_ring') or n.startswith('neck'): return trunk(p)
    if n == 'hips_sh':
        u = ss(.52, .40, p.z) * ss(.03, .13, abs(p.x)); return merge(scale(leg(p, s), u), scale({'hips': 1.0}, 1 - u))
    if n.startswith(('knee', 'boot')):                # rigid by height or depth: no per-vertex jumps between chain segments
        sd = 'l' if s < 0 else 'r'
        if n.startswith('knee'): u = ss(.25, .33, p.z); return {'upperleg.' + sd: u, 'lowerleg.' + sd: 1 - u}
        t = ss(.15, .24, p.y); return {'foot.' + sd: 1 - t, 'toes.' + sd: t}
    if n.startswith('trouser'):
        w = leg(p, s)
        if n.startswith('boot'):
            sd = 'l' if s < 0 else 'r'; t = ss(.15, .24, p.y); wf = w.pop('foot.' + sd, 0.0); w['foot.' + sd] = wf * (1 - t); w['toes.' + sd] = wf * t
        h = ss(.44, .52, p.z) if n.startswith('trouser') else 0.0
        return merge(scale(w, 1 - h), {'hips': h})
    print('[weights] unclassified', name); return {'hips': 1.0}

def stage_rig():
    openb(KEY + '_build.blend'); O = bpy.data.objects
    parts = [o for o in O if o.type == 'MESH' and o.name != 'cyc']
    for o in parts:
        o.data.update()
        for v in o.data.vertices:
            for b, w in weights_for(o.name, v.co / GS).items():
                if w > 1e-3:
                    g = o.vertex_groups.get(b) or o.vertex_groups.new(name=b); g.add([v.index], w, 'REPLACE')
    heads = [o for o in parts if o.name.startswith('h_')]; heads.sort(key=lambda o: o.name != 'h_face')
    bodies = [o for o in parts if not o.name.startswith('h_')]
    head = H.join(heads, KEY + '_head'); body = H.join(bodies, KEY + '_body'); rig = make_rig()
    for ob in (head, body):
        ob.parent = rig; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = rig
        weak = sum(1 for v in ob.data.vertices if sum(g.weight for g in v.groups) < .5)
        if weak: print('[rig] weak vertices', ob.name, weak)
    for b in rig.data.bones: b.use_deform = b.name not in RIGID
    print('[rig] shape keys', [k.name for k in head.data.shape_keys.key_blocks], 'tris', H.tri_count(head), H.tri_count(body))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, KEY + '_rig.blend'))

# ---------------------------------------------------------------- animation (OG.Pose / OG.make_action reused)
_og_pose = OG.pose_frame; R = OG.axis_rot; X_, Y_, Z_ = (1, 0, 0), (0, 1, 0), (0, 0, 1)
def toy_pose(rig, t, kind):
    if kind == 'idle': return _og_pose(rig, t, kind)
    P = OG.Pose(rig); s = math.sin(2 * math.pi * t)
    if kind == 'run':                                 # legs as gym; blaster held up front, toolbox swings gently
        for sg, side in ((1, 'l'), (-1, 'r')):
            P.rot('upperleg.' + side, R(X_, 38 * s * sg)); P.rot('lowerleg.' + side, R(X_, -55 * max(0.0, -s * sg))); P.rot('foot.' + side, R(X_, 15 * max(0.0, -s * sg)))
        P.rot('spine', R(X_, -5)); P.rot('chest', R(X_, -4) @ R(Z_, 5 * s)); P.rot('head', R(X_, 7) @ R(Z_, -4 * s))
        P.rot('upperarm.l', R(X_, -22 * s) @ R(Y_, -6)); P.rot('lowerarm.l', R(X_, 8))
        P.rot('upperarm.r', R(X_, 18 + 8 * s) @ R(Y_, 6)); P.rot('lowerarm.r', R(X_, 6))
        OG.hips_lift(rig, 0.035 * abs(s) - 0.015)
    elif kind == 'attack':                            # snap the blaster up to eye line, pop a dart (recoil), lower
        if t < .25: u = ss(0, 1, t / .25); kick = 0.0
        elif t < .55: u = 1.0; kick = math.sin(math.pi * (t - .25) / .3)
        else: u = 1 - ss(0, 1, (t - .55) / .45); kick = 0.0
        P.rot('spine', R(X_, 5 * kick)); P.rot('chest', R(Z_, 10 * u) @ R(X_, -3 * u + 6 * kick)); P.rot('head', R(Z_, -6 * u) @ R(X_, -4 * kick))
        P.rot('upperarm.r', R(X_, 55 * u - 14 * kick) @ R(Y_, -8 * u)); P.rot('lowerarm.r', R(X_, 12 * u + 28 * kick)); P.rot('hand.r', R(X_, 18 * kick))
        P.rot('upperarm.l', R(X_, -8 * u) @ R(Y_, -5 * u))
    elif kind == 'ult':                               # Claim OT: blaster punched up to the sky, toolbox out wide, chest out, shout
        P.rot('spine', R(X_, 3)); P.rot('chest', R(X_, 6)); P.rot('head', R(X_, 9))
        P.aim('upperarm.r', (0.97, 0.1, 0.2)); P.aim('lowerarm.r', (0.2, 0.15, 0.97)); P.aim('hand.r', (0.0, 0.5, 0.86))
        P.aim('upperarm.l', (-0.75, 0.25, -0.6)); P.aim('lowerarm.l', (-0.55, 0.6, -0.55))
    return P
OG.pose_frame = toy_pose

def stage_anim():
    openb(KEY + '_rig.blend'); SC.render.fps = OG.FPS; rig = bpy.data.objects[KEY + '_rig']
    acts = [OG.make_action(rig, 'idle', 'idle', 60), OG.make_action(rig, 'run', 'run', 24), OG.make_action(rig, 'attack', 'attack', 18, loop=False), OG.make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, KEY + '_anim.blend')); print('[anim] actions', [a.name for a in acts])

def stage_export():
    openb(KEY + '_anim.blend'); O = bpy.data.objects; rig = O[KEY + '_rig']; OG.reset_pose(rig)
    for k in O[KEY + '_head'].data.shape_keys.key_blocks: k.value = 0.0
    H.select_only([O[KEY + '_head'], O[KEY + '_body'], rig], rig)
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
    openb(KEY + '_anim.blend'); O = bpy.data.objects; rig = O[KEY + '_rig']; head = O[KEY + '_head']; cam = O['cam']
    only = [a for a in ARGS if a in ('beauty', 'turn', 'expr', 'sheet', 'zoom')]
    want = lambda k: not only or k in only
    k = HEIGHT / 2.05                                  # gym's framing, scaled to this hero
    play(rig, 'idle', 0); set_key(head, 'none')
    if want('beauty'): shoot(cam, os.path.join(SHOTS, 'beauty.png'), 1600, 1600, 32, 8, (0, .2, .9 * k), 2.3 * k, cam_z=.85 * k)
    if 'zoom' in only:
        for nm, c, az in (('hand_r', CG * GS, 20), ('hand_l', CBL * GS, -35), ('neck', V((0, .1, .8)) * GS, 15), ('hem', V((0, .2, .45)) * GS, 25), ('back', V((0, 0, .7)) * GS, 180)):
            shoot(cam, os.path.join(WORK, 'z_%s.png' % nm), 700, 700, az, 7, c, .8)
        play(rig, 'ult', 2); shoot(cam, os.path.join(WORK, 'z_ult.png'), 700, 700, 25, 7, V((.1, .1, .85)) * GS, 1.0)
        play(rig, 'attack', 7); shoot(cam, os.path.join(WORK, 'z_atk.png'), 700, 700, 30, 7, V((.2, .1, .85)) * GS, 1.2); play(rig, 'idle', 0)
    if want('turn'):
        ps = []
        for i, ang in enumerate((0, 90, 180)):
            rig.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
            t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((0, .12, .9 * k)); p = os.path.join(WORK, 't_%d.png' % i); ps.append(p)
            shoot(cam, p, 534, 800, 0, 9, t, 1.75 * k)
        rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(SHOTS, 'turnaround.png'))
    if want('expr'):
        ps = []
        for name in ('smile', 'angry', 'grin', 'ult'):
            set_key(head, name); p = os.path.join(WORK, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, 0, (HC.z - .06) * GS), 1.3 * GS / 1.1334)
        row(ps, os.path.join(SHOTS, 'expressions.png')); set_key(head, 'none')
    if want('sheet'):
        rows = []
        for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
            ps = []
            for i in range(4):
                play(rig, name, min(n, int(i * n / 4)) if name != 'ult' else (0 if i < 2 else 2)); p = os.path.join(WORK, 'a_%s_%d.png' % (name, i)); ps.append(p)
                shoot(cam, p, 400, 440, 25, 8, (0, .15, .92 * k), 2.3 * k, cam_z=.9 * k)
            r = os.path.join(WORK, 'arow_%s.png' % name); row(ps, r); rows.append(r)
        vstack(rows, os.path.join(SHOTS, 'anim_sheet.png'))

STAGES = dict(build=stage_build, rig=stage_rig, anim=stage_anim, export=stage_export, verify=stage_verify, shots=stage_shots)
for a in ARGS:
    if a in STAGES: STAGES[a]()
