"""Ice Cream Uncle (key `ice`), style `toy` (designer vinyl collectible). Game-ready: rig, skin, 6 shape keys, 4 clips, glb.
Run: blender -b -P ice.py -- build rig anim export verify shots      (stages run in the order given)
Axes: Z up, hero faces +Y. Built from gym.py (toy quality bar): same helpers, face, rig, weights, anim and export code.
The cart (freezer box, frame, wheels, umbrella) is its own skinned mesh CART on the `prop` bone so the game can show or hide it."""
import bpy, sys, os, math, importlib.util
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HD = os.path.dirname(os.path.abspath(__file__))
RT = os.path.abspath(os.path.join(HD, '..', '..', '..'))
WORK = os.path.join(HD, '_tmp_ice'); SHOTS = os.path.join(RT, 'shots', 'heroes_toy', 'ice'); OUT_GLB = os.path.join(RT, 'assets', 'heroes', 'ice.glb')
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
HEIGHT = 1.80
GSF = os.path.join(WORK, 'gs.txt')
GS = float(open(GSF).read()) if os.path.exists(GSF) else 1.0      # final uniform scale, measured in stage_build so the hero is exactly HEIGHT tall

def openb(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, name)); globals()['SC'] = bpy.context.scene

# ---- palette ----------------------------------------------------------------------------------
M.update(
    skin=mat('skin', '#E3A57A', .42, sss=.12), nose=mat('nose', '#DC9268', .42, sss=.12), blush=mat('blush', '#E58A7E', .5),
    hair=mat('hair', '#4A464E', .35, coat=.3), brow=mat('brow', '#2A2326', .45),
    shirt=mat('singlet', '#F4F4EE', .55), sleeve=mat('sleeve', '#F4F6F8', .5), bluep=mat('sky_pipe', '#8FD0EF', .35, coat=.3), cdred=mat('cart_darkred', '#8E141B', .4, coat=.4), cream=mat('cream', '#FFF3DC', .5), cone=mat('cone', '#C98A3C', .55),
    shorts=mat('shorts', '#C9B48A', .6), shortsd=mat('shorts_dark', '#A8936A', .6),
    belt=mat('belt', '#4A3426', .55), pouch=mat('pouch', '#3E8E5A', .45, coat=.2), snap=mat('snap', '#E9C25A', .25, metal=1.0),
    sole=mat('sole', '#2C5E9E', .45, coat=.3), strap=mat('strap', '#F4F6F8', .4),
    hat=mat('hat', '#EFE3C4', .7), hatb=mat('hat_band', '#2C7FB8', .45),
    gunb=mat('nozzle_body', '#7FB8E0', .25, coat=.6), gunp=mat('nozzle_tube', '#DDE8F0', .2, coat=.5), gund=mat('nozzle_dark', '#2C7FB8', .3, coat=.4),
    frost=mat('frost', '#E8F7FF', .15, coat=1.0),
    wafer=mat('wafer', '#D9A35B', .55), waferd=mat('wafer_dark', '#B8813F', .6), yam=mat('yam', '#9B6FC4', .35, coat=.4),
    lip=mat('lip', '#C2655A', .4, coat=.3), mouth=mat('mouth', '#5E1A28', .45),
    # cart
    cred=mat('cart_red', '#C8202A', .3, coat=.6), cdark=mat('cart_dark', '#3A2A2C', .5), cwhite=mat('cart_white', '#F7F5EF', .35, coat=.3),
    steel=mat('steel', '#C9D1D8', .3, metal=.9), steel2=mat('steel_light', '#DDE3E8', .25, metal=.85), cblue=mat('cart_blue', '#2E6FC8', .3, coat=.5),
    tyre=mat('tyre', '#2B2A2E', .7), brass=mat('brass', '#E2B24A', .22, metal=1.0),
    ured=mat('umb_red', '#D8262E', .45), uyel=mat('umb_yellow', '#F6C531', .45),
    bpink=mat('bread_pink', '#F08BB0', .5), byel=mat('bread_yellow', '#F4D35E', .5), bgrn=mat('bread_green', '#7CC576', .5), crust=mat('crust', '#E9C08A', .6),
)

# ---- proportions ------------------------------------------------------------------------------
HC = V((0, 0, 1.30)); HR = V((0.50, 0.47, 0.43))                      # head centre and radii (globals used by surf())
TR = [(.44, .31, .23), (.50, .335, .245), (.58, .36, .26), (.66, .37, .26), (.72, .36, .245), (.77, .32, .22), (.80, .26, .195),
      (.83, .2, .17), (.86, .165, .15), (.90, .155, .145), (.96, .155, .145)]
_a = np.array(TR); ZS = np.linspace(TR[0][0], TR[-1][0], 22); RXs = np.interp(ZS, _a[:, 0], _a[:, 1]); RYs = np.interp(ZS, _a[:, 0], _a[:, 2])
for _ in range(3):
    RXs[1:-1] = (RXs[:-2] + 2 * RXs[1:-1] + RXs[2:]) / 4; RYs[1:-1] = (RYs[:-2] + 2 * RYs[1:-1] + RYs[2:]) / 4
rxz = lambda z: float(np.interp(z, ZS, RXs)); ryz = lambda z: float(np.interp(z, ZS, RYs))
def bel(z): return .085 * math.exp(-((z - .6) / .13) ** 2)                   # pot belly, front only
def tp(t, z, off):
    return V(((rxz(z) + off) * math.cos(t), (ryz(z) + off) * math.sin(t) + bel(z) * max(0.0, math.sin(t)) ** 1.5, z))
def tsurf(a_deg, z, off): return tp(math.radians(a_deg), z, off)
ZH = .47
def ztop(a):                                  # white singlet: scooped neck front and back, narrow straps, deep armholes
    c = abs(math.cos(a)); n = .85 - (.07 if math.sin(a) > 0 else .035) * (1 - ss(.3, .58, c))
    return n - ss(.8, .9, c) * (n - .6)

SHD = {1: V((.40, 0, .70)), -1: V((-.40, 0, .70))}
ELB = {1: V((.52, -.03, .48)), -1: V((-.52, .0, .46))}
WR_R = V((.53, .21, .50)); CR = V((.53, .32, .49)); GRIP_R = .040               # frost nozzle pistol grip (vertical) in the right fist
CS = .62; DY = .23                                                             # old game cart (three.js metres, x mirrored, y up) shrunk to toy scale so the bar meets his hands
def o(x, y, z): return V((-x * CS, z * CS + DY, y * CS))
BAR_R = .025; CL = o(.3, .95, .6); WR_L = CL + V((0, -.115, -.03))               # left fist round the cart push bar
def _elbow(S, W, L1, L2, pole):
    d = (W - S).length; u = (W - S) / d; a = (L1 * L1 - L2 * L2 + d * d) / (2 * d); h = math.sqrt(max(0.0, L1 * L1 - a * a))
    q = V(pole) - u * V(pole).dot(u); return S + u * a + q.normalized() * h
ELB[-1] = _elbow(SHD[-1], WR_L, .27, .29, (-1, -.2, -1.2))
LEGX = .16
PROP = o(-.2, .3, 1.15)                                                        # prop bone at the cart, parented to root

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

def sbox(name, c, half, m, p=.18, seg=16, rot=None):
    """Rounded box (superellipsoid). p near 0 = sharp box, 1 = ellipsoid."""
    vs, fs = sph_vf(seg, seg // 2); c = V(c); R = rot if rot is not None else Matrix.Identity(3)
    sg = lambda x: math.copysign(abs(x) ** p, x)
    return mk(name, [c + R @ V((sg(v.x) * half[0], sg(v.y) * half[1], sg(v.z) * half[2])) for v in vs], fs, m)

# ---------------------------------------------------------------- body
def build_torso():
    zs = [z for z in ZS if z > .55]; vs = []; fs = []; seg = 24
    for z in zs:
        for i in range(seg): vs.append(tp(2 * math.pi * i / seg, z, 0))
    for j in range(len(zs) - 1):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
    mk('torso', vs, fs, M['skin'])
    seg = 72; J = 10; vs = []; fs = []
    offz = lambda z: .02 + .028 * (1 - ss(ZH, .56, z)) + .012 * ss(.76, .84, z)
    for i in range(seg): vs.append(tp(2 * math.pi * i / seg, ZH, 0))                 # inner closing ring at the hem
    for j in range(J):
        for i in range(seg):
            t = 2 * math.pi * i / seg; zt = ztop(t); z = ZH + (zt - ZH) * j / (J - 1); vs.append(tp(t, z, offz(z)))
    for i in range(seg):                                                               # inner closing ring at the neckline
        t = 2 * math.pi * i / seg; vs.append(tp(t, ztop(t), -.004))
    R = J + 2
    for j in range(R - 1):
        for i in range(seg): fs.append((j * seg + i, (j + 1) * seg + i, (j + 1) * seg + (i + 1) % seg, j * seg + (i + 1) % seg))
    mk('tank', vs, fs, M['shirt'])
    ring('pipe_neck', [tp(2 * math.pi * i / 64, ztop(2 * math.pi * i / 64) + .002, offz(ztop(2 * math.pi * i / 64)) + .004) for i in range(64)], .012, M['bluep'], seg=6)
    ring('pipe_hem', [tp(2 * math.pi * i / 36, ZH + .006, offz(ZH) + .006) for i in range(36)], .011, M['bluep'], seg=5)
    # money belt over the shirt and the green waist pouch, front left
    zb = .545; ring('belt', [tp(2 * math.pi * i / 40, zb, offz(zb) + .012) for i in range(40)], .017, M['belt'], seg=6)
    a = math.radians(118); p = tp(a, zb - .01, offz(zb) + .06); nrm = V((math.cos(a), math.sin(a), 0)).normalized()
    R3 = Matrix((nrm.cross(Z).normalized() * -1, nrm, Z)).transposed()
    sbox('pouch', p, (.105, .045, .075), M['pouch'], p=.3, seg=16, rot=R3)
    sbox('pouch_flap', p + nrm * .035 + V((0, 0, .04)), (.108, .018, .042), M['pouch'], p=.3, seg=12, rot=R3)
    ell('pouch_snap', p + nrm * .056 + V((0, 0, .02)), (.016, .01, .016), M['snap'], rot=R3, seg=12)

def build_legs():
    ell('hips_sh', (0, 0, .45), (.31, .23, .12), M['shorts'], seg=20)
    for s in (-1, 1):
        x = s * LEGX
        sweep('shortleg', [(x, 0, .49), (x, .005, .36), (x, .01, .25)], [.152, .152, .148], M['shorts'], seg=18, lip=(.01, .10))
        tor('shorthem', (x, .01, .252), Z, .149, .010, M['shortsd'], seg=24, rseg=5)
        sweep('calf', [(x, .01, .30), (x, .0, .17), (x, 0, .06)], [.092, .084, .072], M['skin'], seg=18)
        sweep('shoe_foot', [(x, -.04, .055), (x, .16, .05)], [.068, .062], M['skin'], seg=16)
        for k, dx in enumerate((-.04, -.013, .014, .04)):
            ell('shoe_toe', (x + s * dx * -1, .215 - .012 * abs(dx) / .04, .052), (.019 - .002 * (k == 0 or k == 3), .022, .02), M['skin'], seg=8)
        ell('shoe_sole', (x, .06, .022), (.1, .2, .024), M['sole'], seg=16)
        pts = catmull([(x - .075, .0, .03), (x - .05, .07, .085), (x, .17, .066), (x + .05, .07, .085), (x + .075, .0, .03)], 4)
        sweep('shoe_strap', pts, .014, M['strap'], seg=6)

def fist(name, C, W, s, R, palm_z=.04, rot=None):
    """Chunky fist round a cylinder at C (radius R, vertical, or along rot's z), wrist at W. s = +1 right hand, -1 left. Fingers wrap the outer side, thumb over the top."""
    Rm = rot or Matrix.Identity(3); T = lambda p: C + Rm @ (V(p) - C)
    palm = T(C + V((0, -(R + .03), 0))); h = H.Soup(name)
    rr = Rm @ V((.06, .046, .105)); h.ellipsoid(palm, tuple(abs(c) for c in rr)); h.capsule(W, palm + Rm @ V((0, 0, palm_z)), .066, .062)
    rho = R + .021; rf = .021
    mir = (lambda t: t) if s < 0 else (lambda t: 180 - t)
    def arc(z, th, rho, ra, rb):
        pts = [T((C.x + rho * math.cos(math.radians(mir(t))), C.y + rho * math.sin(math.radians(mir(t))), z)) for t in th]
        for p0, p1, r0, r1 in zip(pts[:-1], pts[1:], [ra] + [rf] * 5, [rf] * 4 + [rb]): h.capsule(p0, p1, r0, r1, seg=12)
    for k, dz in enumerate((.075, .025, -.025, -.075)):
        arc(C.z + dz, (250, 195, 140, 95, 55), rho, rf + .002, rf * (.85 if k == 3 else .95))
    arc(C.z + .122, (305, 350, 20, 52), R + .026, .032, .023)
    hd, _ = h.remesh(voxel=.0065, smooth=5, smooth_factor=.5, target_tris=850); H.set_material(hd, M['skin']); hd.name = name; reg(hd)

def arm(sd, k, W):
    S, E = SHD[k], ELB[k]
    so = H.Soup('arm_' + sd); so.sphere(S, .118, seg=20); so.capsule(S, E, .104, .086); so.capsule(E, W, .084, .062); so.sphere(W, .062)
    a, _ = so.remesh(voxel=.011, smooth=5, smooth_factor=.55, target_tris=720); H.set_material(a, M['skin']); a.name = 'arm_' + sd; reg(a)

def build_arm_r():
    arm('r', 1, WR_R); fist('hand_r', CR, WR_R, 1, GRIP_R)
    # frost nozzle: dark blue pistol grip, light blue body, pale tube, blue ring tip (buildIce viewmodel colours)
    sweep('gun_grip', [(CR.x, CR.y - .012, CR.z - .125), (CR.x, CR.y, CR.z + .2)], [GRIP_R, GRIP_R + .003], M['gund'], seg=18)
    bz = CR.z + .215; y0 = CR.y - .1
    sweep('gun_body', [(CR.x, y0, bz), (CR.x, CR.y + .17, bz)], [.064, .066], M['gunb'], seg=24)
    for dy in (-.03, .1): tor('gun_band', (CR.x, CR.y + dy, bz), (0, 1, 0), .067, .008, M['gund'], seg=20, rseg=5)
    sweep('gun_tube', [(CR.x, CR.y + .17, bz), (CR.x, CR.y + .33, bz)], [.044, .03], M['gunp'], seg=18, round_caps=False)
    tor('gun_tip', (CR.x, CR.y + .33, bz), (0, 1, 0), .03, .011, M['gund'], seg=18, rseg=6)
    ell('gun_cap', (CR.x, y0 - .01, bz), (.05, .03, .05), M['gund'], seg=16)
    sweep('gun_guard', fillet([(CR.x, CR.y + .03, bz - .06), (CR.x, CR.y + .09, bz - .065), (CR.x, CR.y + .085, CR.z + .05)], .02, 3), .009, M['gund'], seg=6)
    for i, (dx, dz) in enumerate(((0, .0), (.022, .018), (-.02, .02))):          # a puff of frost at the tip
        ell('gun_frost', (CR.x + dx, CR.y + .36 + .02 * i, bz + dz), (.026 - .005 * i,) * 3, M['frost'], seg=10)

def build_arm_l():
    arm('l', -1, WR_L); fist('hand_l', CL, WR_L, -1, BAR_R, rot=Matrix.Rotation(math.radians(90), 3, 'Y'))

def build_neck():
    ell('neck_col', (0, 0, .87), (.17, .155, .12), M['skin'], seg=20)

def build_body_all():
    build_torso(); build_legs(); build_arm_r(); build_arm_l(); build_neck()

# ---------------------------------------------------------------- cart (separate object CART)
def build_cart():
    def B(nm, w, h, d, x, y, z, m, p=.12, seg=16, ry=0.0, rx=0.0):
        R = Matrix.Rotation(-ry, 3, 'Z') @ Matrix.Rotation(-rx, 3, 'X')
        sbox(nm, o(x, y, z), (w / 2 * CS, d / 2 * CS, h / 2 * CS), m, p=p, seg=seg, rot=R)
    def Rod(nm, a, b, r, m, seg=8): sweep(nm, [o(*a), o(*b)], r * CS * 1.4, m, seg=seg)    # rods a touch chunkier for the toy read
    def Wheel(r, t, x, y, z, hub):
        tor('cart_tyre', o(x, y, z), (1, 0, 0), r * CS, t * CS, M['tyre'], seg=16, rseg=5)
        ell('cart_hub', o(x, y, z), (.05 * CS, r * .5 * CS, r * .5 * CS), hub, seg=8)
    bx, bz = -.45, 1.175
    # freezer box: dark base band, red body, white trims, steel lid with a raised lip, two hatches with handles
    B('cart_base', 1.12, .1, .97, bx, .37, bz, M['cdred'], p=.14, seg=14)
    B('cart_box', 1.1, .5, .95, bx, .67, bz, M['cred'], p=.1, seg=18)
    for y in (.435, .9): B('cart_trim', 1.13, .024, .98, bx, y, bz, M['cwhite'], p=.1, seg=12)
    B('cart_lid', 1.14, .05, .99, bx, .945, bz, M['steel'], p=.1, seg=14)
    rr = [o(x, .99, z) for x, z in ((-1.0, .69), (.1, .69), (.1, 1.66), (-1.0, 1.66))]
    ring('cart_lip', fillet(rr + [rr[0], rr[1]], .06, 4)[1:-1], .016 * CS, M['steel2'], seg=6)
    for x in (-.72, -.18):
        B('cart_hatch', .5, .022, .84, x, .98, bz, M['steel2'], p=.1, seg=12)
        q = [o(x - .06, .985, .8), o(x - .06, 1.03, .8), o(x + .06, 1.03, .8), o(x + .06, .985, .8)]
        sweep('cart_handle', fillet(q, .015, 3), .011 * CS, M['cdark'], seg=5)
    # painted cream panels with a raised cone, scoops and a wafer sandwich: outer side and front
    for side in ('x', 'z'):
        if side == 'x': c = o(-1.0, .67, bz); nrm = V((1, 0, 0)); tg = V((0, 1, 0)); half = (.006, .4 * CS, .17 * CS)
        else: c = o(bx, .67, 1.65); nrm = V((0, 1, 0)); tg = V((-1, 0, 0)); half = (.45 * CS, .006, .17 * CS)
        sbox('cart_panel', c + nrm * .01, half, M['cream'], p=.2, seg=12)
        k = c + nrm * .03 - tg * .18 * CS; sweep('cart_cone', [k + V((0, 0, -.12 * CS)), k + V((0, 0, .02 * CS))], [.012 * CS, .055 * CS], M['cone'], seg=10)
        for i, mm in enumerate((M['bpink'], M['bgrn'])): ell('cart_scoop', k + V((0, 0, (.06 + .06 * i) * CS)), (.06 * CS,) * 3, mm, seg=10)
        w = c + nrm * .03 + tg * .2 * CS
        for i, (mm, dz) in enumerate(((M['wafer'], .06), (M['yam'], 0), (M['wafer'], -.06))):
            sbox('cart_sand', w + V((0, 0, dz * CS)), tuple(.03 * CS if abs(a) > .5 else (.12 * CS if b == 0 else .028 * CS) for a, b in zip(nrm, (0, 0, 1))), mm, p=.3, seg=8)
    # lid props: wafer stack, rainbow bread, brass bell
    for i in range(5): B('cart_wafer', .16, .018, .09, -.1, 1.0 + i * .018, 1.45, M['wafer'] if i % 2 == 0 else M['cream'], p=.15, seg=8, ry=.2)
    for i, mm in enumerate((M['bpink'], M['bgrn'], M['byel'])): B('cart_bread', .22, .03, .12, -.52, 1.01 + i * .03, 1.48, mm, p=.3, seg=8, ry=-.15)
    Rod('cart_bellpost', (-.86, .99, .84), (-.86, 1.05, .84), .01, M['brass'], seg=6)
    ell('cart_bell', o(-.86, 1.07, .84), (.05 * CS, .05 * CS, .04 * CS), M['brass'], seg=14)
    # sidecar wheels, push bar with grips, hitch to the scooter
    Wheel(.15, .045, -1.06, .17, bz, M['steel']); Wheel(.15, .045, .16, .17, bz, M['steel'])
    Rod('cart_push', (-.825, .95, .6), (.325, .95, .6), .025, M['steel'])
    for x in (-.75, .05): Rod('cart_post', (x, .95, .58), (x, .95, .71), .02, M['steel'])
    for x in (-.825, .325): ell('cart_cap', o(x, .95, .6), (.03 * CS,) * 3, M['cdark'], seg=8)
    Rod('cart_hitch', (.1, .42, 1.2), (.42, .42, 1.2), .025, M['steel2'])
    # blue step-through scooter on his left
    sx = .5
    for z in (.82, 1.86): Wheel(.2, .055, sx, .24, z, M['steel'])
    B('cart_floor', .22, .06, .62, sx, .34, 1.3, M['cblue'], p=.25, seg=12)
    B('cart_rear', .28, .26, .48, sx, .52, .95, M['cblue'], p=.35, seg=16)
    B('cart_seat', .26, .08, .42, sx, .69, .95, M['cdark'], p=.4, seg=12)
    B('cart_shield', .3, .5, .08, sx, .6, 1.64, M['cblue'], p=.3, seg=14, rx=-.18)
    B('cart_fender', .14, .05, .3, sx, .47, 1.86, M['cblue'], p=.4, seg=10)
    Rod('cart_column', (sx, .62, 1.77), (sx, 1.24, 1.66), .035, M['steel2'])
    Rod('cart_handlebar', (sx - .25, 1.26, 1.74), (sx + .25, 1.26, 1.74), .02, M['steel'])
    for d in (-1, 1): Rod('cart_grip', (sx + d * .16, 1.26, 1.74), (sx + d * .27, 1.26, 1.74), .03, M['cdark'])
    ell('cart_lamp', o(sx, 1.18, 1.84), (.06 * CS,) * 3, M['cream'], seg=12)
    # big umbrella from the front outer corner: 8 panels red and yellow, double sided, rim above head height
    ux, uz = -.95, 1.6; P0 = o(ux, 0, uz); top = 2.45; Rc = 1.25; drop = .34                 # rim at 2.11 raw, clear above the hat
    sweep('cart_pole', [o(ux, .92, uz), V((P0.x, P0.y, top + .01))], .022, M['steel'], seg=8)
    nphi = 6; nr = 7; vs = [V((P0.x, P0.y, top))]; fs = []; fm = []; N = 8 * nphi
    for j in range(1, nr + 1):
        for i in range(N):
            ph = 2 * math.pi * i / N; fr = (i % nphi) / nphi; u = j / nr
            r = Rc * u * (1 - .06 * math.sin(math.pi * fr) * u ** 3)
            z = top - drop * u ** 1.4 + .04 * math.sin(math.pi * fr) * math.sin(math.pi * u)
            vs.append(V((P0.x + r * math.cos(ph), P0.y + r * math.sin(ph), z)))
    idx = lambda j, i: 1 + (j - 1) * N + i % N
    for i in range(N): fs.append((0, idx(1, i), idx(1, i + 1))); fm.append((i // nphi) % 2)
    for j in range(1, nr):
        for i in range(N): fs.append((idx(j, i), idx(j + 1, i), idx(j + 1, i + 1), idx(j, i + 1))); fm.append((i // nphi) % 2)
    mk('cart_canopy', vs, fs, [M['ured'], M['uyel']], mat_idx=fm)
    for m_ in (M['ured'], M['uyel']): m_.use_backface_culling = False
    for i in range(8):
        ph = 2 * math.pi * i / 8; ell('cart_tip', V((P0.x + Rc * math.cos(ph), P0.y + Rc * math.sin(ph), top - drop)), (.02,) * 3, M['cwhite'], seg=6)
    ell('cart_finial', V((P0.x, P0.y, top + .03)), (.035, .035, .04), M['cwhite'], seg=12)
    sbox('cart_runner', V((P0.x, P0.y, top - .55)), (.035, .035, .035), M['cwhite'], p=.4, seg=10)

# ---------------------------------------------------------------- head
HOLE = (0.0, -.245, .215, .14)

def jaw(p):                                   # soft round jowls: widen the lower head a little
    d = p - HC; t = ss(-.08, -.33, d.z); z = d.z
    if z < -.33: z = -.33 + (z + .33) * .4
    return HC + V((d.x * (1 + .14 * t), d.y * (1 + .10 * t), z))

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
    used = sorted({i for f in keep for i in f}); remap = {o: n for n, o in enumerate(used)}
    return mk('h_head', [P[i] for i in used], [tuple(remap[i] for i in f) for f in keep], M['skin'])

def hzb(a): return HC.z + .255 + .05 * math.sin(a)          # hat base line: pushed back, front higher than the back
def hrad(a, z, off):
    k = math.sqrt(max(0.0, 1 - ((z - HC.z) / HR.z) ** 2)); return V(((HR.x * k + off) * math.cos(a), (HR.y * k + off) * math.sin(a), z))

def build_hat():
    n = 48; top = HC.z + .50; TRX, TRY = .36, .345
    rows = []
    for j, u in enumerate((0, .2, .45, .7, .88, 1.0)):
        rows.append([])
        for i in range(n):
            a = 2 * math.pi * i / n; b = hrad(a, hzb(a), .03); w = ss(0, 1, u) * .9 + .1 * u
            x = b.x + (TRX * math.cos(a) - b.x) * w; y = b.y + (TRY * math.sin(a) - b.y) * w; z = b.z + (top - b.z) * u
            bulge = .018 * math.sin(math.pi * u); rows[-1].append(V((x * (1 + bulge), y * (1 + bulge), z)))
    band = [rows[0][i].lerp(rows[1][i], .55) for i in range(n)]
    for f, dz in ((.85, .022), (.55, .038)):
        rows.append([V((TRX * f * math.cos(2 * math.pi * i / n), TRY * f * math.sin(2 * math.pi * i / n), top + dz)) for i in range(n)])
    vs = [p for r in rows for p in r] + [V((0, 0, top + .045))]; fs = []
    for j in range(len(rows) - 1):
        for i in range(n): fs.append((j * n + i, j * n + (i + 1) % n, (j + 1) * n + (i + 1) % n, (j + 1) * n + i))
    cv = len(vs) - 1; L = len(rows) - 1
    for i in range(n): fs.append((L * n + i, L * n + (i + 1) % n, cv))
    mk('h_hat', vs, fs, M['hat'])
    # brim: closed cross-section loop, sloping down and out
    prof = [(0, 0), (.06, -.016), (.13, -.04), (.17, -.058), (.178, -.072), (.165, -.08), (.12, -.064), (.05, -.04), (0, -.026)]
    vs = []; fs = []
    for i in range(n):
        a = 2 * math.pi * i / n; b = hrad(a, hzb(a), .03); d = V((math.cos(a), math.sin(a), 0)); ext = 1 + .2 * max(0, math.sin(a))
        vs += [b + d * (pr * ext) + V((0, 0, pz)) for pr, pz in prof]
    P = len(prof)
    for i in range(n):
        for k in range(P):
            fs.append((i * P + k, ((i + 1) % n) * P + k, ((i + 1) % n) * P + (k + 1) % P, i * P + (k + 1) % P))
    import bmesh
    ob = mk('h_brim', vs, fs, M['hat']); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    ring('h_hatband', [V((q.x * 1.02, q.y * 1.02, q.z)) for q in band], .022, M['hatb'], seg=6)

def build_head():
    head_surface(); build_hat()
    import random; so = H.Soup('hair'); n = 260
    for i in range(n):                                       # short grey hair under the hat: sides and back only
        z = 1 - 2 * (i + .5) / n; a = i * 2.39996; r = math.sqrt(1 - z * z); d = V((r * math.cos(a), r * math.sin(a), z))
        az = math.degrees(math.atan2(abs(d.x), d.y)); el = math.degrees(math.asin(d.z))
        lo = float(np.interp(az, [0, 70, 85, 110, 180], [90, 90, -6, -22, -30])); hi = 30
        if not (lo < el < hi): continue
        so.sphere(HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z)) * .94, .075, seg=12)
    hair, _ = so.remesh(voxel=.013, smooth=16, smooth_factor=.7, target_tris=900); H.set_material(hair, M['hair']); hair.name = 'h_hair'; reg(hair)
    for s in (-1, 1):
        ell('h_ear', HC + V((s * .49, -.03, -.04)), (.04, .075, .095), M['skin'], seg=18)
    p, n_, t, u = surf(0, -.085); ell('h_nose', p + n_ * .004, (.066, .054, .054), M['nose'], seg=22)
    for s in (-1, 1):                                        # friendly smile creases at the eye corners
        for k, dz in enumerate((.012, -.022)):
            q = surf(s * .275, -.02 + dz)[0]; ell('h_crease', q, (.022, .006, .005), M['nose'], rot=Matrix.Rotation(math.radians(s * (18 - 36 * k)), 3, 'Y'), seg=8)

# ---------------------------------------------------------------- face (one mesh, six shape keys), same build as gym
FM = ['skin', 'brow', 'eye', 'white', 'line', 'mouth', 'lip', 'teeth', 'tongue', 'blush']
EXe, EZe = .185, -.02
_I = dict(bz=.14, tilt=.0, arch=.016, eye='bead', es=(.8, .72), cut=(.02, 0), hl=.006, w=.21, curve=.04, up=0, dn=0, teeth=0, tongue=0, cz=-.235, arc=.058)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'eye': 'arc', 'arc': -.022, 'bz': .145},
    'mouth_open': {**_I, 'w': .2, 'curve': .012, 'up': .006, 'dn': .085, 'teeth': .032, 'tongue': .05},
    'smile': {**_I, 'w': .26, 'curve': .055, 'bz': .17, 'tilt': -.012},
    'angry': dict(bz=.05, tilt=.09, arch=-.004, eye='bead', es=(1.08, .95), cut=(.012, .6), hl=.0, w=.2, curve=-.055, up=.018, dn=.05, teeth=.034, tongue=0, cz=-.24, arc=.058),
    'grin': dict(bz=.18, tilt=-.012, arch=.03, eye='arc', es=(1, 1), cut=None, hl=.026, w=.32, curve=.06, up=.004, dn=.085, teeth=.034, tongue=.05, cz=-.25, arc=.062),
    'ult': dict(bz=.17, tilt=.05, arch=.004, eye='bead', es=(.95, .85), cut=(.02, 0), hl=.008, w=.27, curve=.006, up=.045, dn=.095, teeth=.034, tongue=.07, cz=-.25, arc=.058),
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
        stroke([(s * (EXe + q * .105), e['bz'] + EZe + q * e['tilt'] + e['arch'] * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .05, .03, .006, 'brow')
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
    build_body_all(); build_head(); build_face(); build_cart()
    hero = [o for o in HERO if not o.name.startswith('cart')]
    tris = sum(H.tri_count(o) for o in HERO); print('TOY_TRIS', tris, 'hero', sum(H.tri_count(o) for o in hero), 'objects', len(HERO))
    agg = {}
    for o in HERO: agg[o.name.split('.')[0]] = agg.get(o.name.split('.')[0], 0) + H.tri_count(o)
    print('TOY_TOP', sorted(agg.items(), key=lambda kv: -kv[1]))
    zmax = max(v.co.z for o in hero for v in o.data.vertices); zmin = min(v.co.z for o in hero for v in o.data.vertices)
    gs = HEIGHT / (zmax - zmin); globals()['GS'] = gs; open(GSF, 'w').write(repr(gs)); print('TOY_RAW_H', zmax - zmin, 'zmin', zmin, 'GS', gs)
    for o in HERO:
        for v in o.data.vertices: v.co *= GS
        if o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks:
                for v in kb.data: v.co *= GS
    stage()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'ice_build.blend'))

# ---------------------------------------------------------------- rig + weights
def eyepos(s): return surf(s * EXe, EZe)[0]
BONES = [
    ('root', (0, 0, 0), (0, 0, .25), None), ('hips', (0, 0, .50), (0, 0, .60), 'root'), ('spine', (0, 0, .60), (0, 0, .70), 'hips'),
    ('chest', (0, 0, .70), (0, 0, .80), 'spine'), ('neck', (0, 0, .80), (0, .01, .90), 'chest'), ('head', (0, .01, .90), (0, .02, 1.74), 'neck'),
    ('eye.l', tuple(eyepos(-1)), tuple(eyepos(-1) + V((0, .06, 0))), 'head'), ('eye.r', tuple(eyepos(1)), tuple(eyepos(1) + V((0, .06, 0))), 'head'),
    ('upperarm.l', tuple(SHD[-1]), tuple(ELB[-1]), 'chest'), ('lowerarm.l', tuple(ELB[-1]), tuple(WR_L), 'upperarm.l'),
    ('hand.l', tuple(WR_L), tuple(CL + V((0, -.03, .0))), 'lowerarm.l'), ('handslot.l', tuple(CL), tuple(CL + V((0, .08, 0))), 'hand.l'),
    ('upperarm.r', tuple(SHD[1]), tuple(ELB[1]), 'chest'), ('lowerarm.r', tuple(ELB[1]), tuple(WR_R), 'upperarm.r'),
    ('hand.r', tuple(WR_R), tuple(CR + V((0, -.03, 0))), 'lowerarm.r'), ('handslot.r', tuple(CR), tuple(CR + V((0, .1, 0))), 'hand.r'),
    ('upperleg.l', (-LEGX, .02, .52), (-LEGX, .01, .28), 'hips'), ('lowerleg.l', (-LEGX, .01, .28), (-LEGX, 0, .08), 'upperleg.l'),
    ('foot.l', (-LEGX, 0, .08), (-LEGX, .11, .03), 'lowerleg.l'), ('toes.l', (-LEGX, .11, .03), (-LEGX, .24, .02), 'foot.l'),
    ('upperleg.r', (LEGX, .02, .52), (LEGX, .01, .28), 'hips'), ('lowerleg.r', (LEGX, .01, .28), (LEGX, 0, .08), 'upperleg.r'),
    ('foot.r', (LEGX, 0, .08), (LEGX, .11, .03), 'lowerleg.r'), ('toes.r', (LEGX, .11, .03), (LEGX, .24, .02), 'foot.r'),
    ('prop', tuple(PROP), tuple(PROP + V((0, 0, .3))), 'root'),
]
RIGID = {'eye.l', 'eye.r'}

def make_rig():
    arm = bpy.data.armatures.new('ice_rig'); ob = bpy.data.objects.new('ice_rig', arm); bpy.context.scene.collection.objects.link(ob)
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
    return chain(p, [(x, 0, .62), (x, .01, .28), (x, 0, .08), (x, .11, .03)], ['upperleg.' + sd, 'lowerleg.' + sd, 'foot.' + sd], [.06, .04])
def scale(w, f): return {k: v * f for k, v in w.items()}
def merge(*ws):
    o = {}
    for w in ws:
        for k, v in w.items(): o[k] = o.get(k, 0) + v
    return o

def weights_for(name, p):
    n = name.split('.')[0]; s = -1 if p.x < 0 else 1
    if n.startswith('cart'): return {'prop': 1.0}
    if n.startswith('h_'): return {'head': 1.0}
    if n.startswith('gun'): return {'handslot.r': 1.0}
    if n.startswith('waf'): return {'handslot.l': 1.0}
    if n.startswith('hand_'): return {'hand.' + n[-1]: 1.0}
    if n.startswith(('arm_', 'sleeve_', 'cuff_')):
        sd = n[-1]; k = 1 if sd == 'r' else -1; S, E = SHD[k], ELB[k]; W = WR_R if k == 1 else WR_L; tip = CR if k == 1 else CL
        w = chain(p, [S, E, W, tip], ['upperarm.' + sd, 'lowerarm.' + sd, 'hand.' + sd], [.09, .08])
        wc = 1 - ss(-.06, .16, (p - S).dot((E - S).normalized()))
        return merge(scale(w, 1 - wc), {'chest': wc})
    if n in ('torso', 'tank', 'belt') or n.startswith(('pipe', 'neck', 'pouch')): return trunk(p)
    if n == 'hips_sh':
        u = ss(.52, .40, p.z) * ss(.03, .13, abs(p.x)); return merge(scale(leg(p, s), u), scale({'hips': 1.0}, 1 - u))
    if n.startswith(('shortleg', 'shorthem', 'calf', 'shoe')):
        w = leg(p, s)
        if n.startswith('shoe'):
            sd = 'l' if s < 0 else 'r'; t = ss(.1, .18, p.y); wf = w.pop('foot.' + sd, 0.0); w['foot.' + sd] = wf * (1 - t); w['toes.' + sd] = wf * t
        h = ss(.44, .52, p.z) if n.startswith(('shortleg', 'shorthem')) else 0.0
        return merge(scale(w, 1 - h), {'hips': h})
    print('[weights] unclassified', name); return {'hips': 1.0}

def stage_rig():
    openb('ice_build.blend'); O = bpy.data.objects
    parts = [o for o in O if o.type == 'MESH' and o.name != 'cyc']
    for o in parts:
        o.data.update()
        for v in o.data.vertices:
            for b, w in weights_for(o.name, v.co / GS).items():
                if w > 1e-3:
                    g = o.vertex_groups.get(b) or o.vertex_groups.new(name=b); g.add([v.index], w, 'REPLACE')
    heads = [o for o in parts if o.name.startswith('h_')]; heads.sort(key=lambda o: o.name != 'h_face')
    carts = [o for o in parts if o.name.startswith('cart')]
    bodies = [o for o in parts if not o.name.startswith(('h_', 'cart'))]
    head = H.join(heads, 'ice_head'); body = H.join(bodies, 'ice_body'); cart = H.join(carts, 'CART'); rig = make_rig()
    for ob in (head, body, cart):
        ob.parent = rig; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = rig
        for v in ob.data.vertices:
            tot = sum(g.weight for g in v.groups)
            if tot < .5: print('[rig] weak vertex', ob.name, v.index, tot)
    for b in rig.data.bones: b.use_deform = b.name not in RIGID
    print('[rig] shape keys', [k.name for k in head.data.shape_keys.key_blocks], 'tris', H.tri_count(head), H.tri_count(body), H.tri_count(cart))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'ice_rig.blend'))

# ---------------------------------------------------------------- animation (OG.pose_frame / OG.make_action reused)
_og_pose = OG.pose_frame; AX = OG.axis_rot; X_, Y_, Z_ = OG.X, OG.Y, OG.Z
def toy_pose(rig, t, kind):
    if kind == 'attack':                               # Brain Freeze: nozzle up to aim, sweep the cone left and right, recoil buzz, recover
        P = OG.Pose(rig); e = ss(0, .18, t) * (1 - ss(.82, 1, t)); sw = math.sin(2 * math.pi * (t - .18) / .64) * ss(.18, .3, t) * (1 - ss(.7, .82, t))
        P.rot('spine', AX(X_, 4 * e)); P.rot('chest', AX(Z_, 12 * sw) @ AX(X_, 5 * e)); P.rot('head', AX(Z_, -6 * sw) @ AX(X_, -4 * e))
        P.rot('upperarm.r', AX(X_, 38 * e) @ AX(Y_, 6 * e)); P.rot('lowerarm.r', AX(X_, -12 * e + 2.5 * math.sin(14 * math.pi * t) * e))
        OG.hips_lift(rig, -0.015 * e)
    elif kind == 'ult':                                # Triple Scoop Spin: nozzle thrust up over the cart, head back, a cheer
        P = OG.Pose(rig); P.rot('spine', AX(X_, -3)); P.rot('chest', AX(X_, -6)); P.rot('head', AX(X_, -9))
        P.aim('upperarm.r', (.75, .15, .65)); P.aim('lowerarm.r', (.25, .2, .95)); P.aim('hand.r', (.15, .5, .85))
    else: P = _og_pose(rig, t, kind)
    P.rot('upperarm.l', P.acc('chest').inverted()); P.rot('lowerarm.l', Quaternion()); P.rot('hand.l', Quaternion())   # left fist locked to the bar
    return P
OG.pose_frame = toy_pose

def stage_anim():
    openb('ice_rig.blend'); SC.render.fps = OG.FPS; rig = bpy.data.objects['ice_rig']
    acts = [OG.make_action(rig, 'idle', 'idle', 60), OG.make_action(rig, 'run', 'run', 24), OG.make_action(rig, 'attack', 'attack', 18, loop=False), OG.make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'ice_anim.blend')); print('[anim] actions', [a.name for a in acts])

def stage_export():
    openb('ice_anim.blend'); O = bpy.data.objects; rig = O['ice_rig']; OG.reset_pose(rig)
    for k in O['ice_head'].data.shape_keys.key_blocks: k.value = 0.0
    H.select_only([O['ice_head'], O['ice_body'], O['CART'], rig], rig)
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
                              export_animations=True, export_animation_mode='ACTIONS', export_nla_strips=True, export_skins=True, export_def_bones=False,
                              export_morph=True, export_morph_normal=False, export_image_format='AUTO', export_materials='EXPORT', export_texcoords=True,
                              export_normals=True, export_tangents=False, export_all_influences=False, export_optimize_animation_size=True)
    print('[export] wrote', OUT_GLB, os.path.getsize(OUT_GLB) // 1024, 'KB')

def stage_verify():
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps = 30; bpy.ops.import_scene.gltf(filepath=OUT_GLB)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('Icosphere')]
    rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    for grp in ('hero', 'all'):
        lo = V((1e9,) * 3); hi = V((-1e9,) * 3)
        for o in meshes:
            if grp == 'hero' and o.name.startswith('CART'): continue
            for v in o.data.vertices:
                w = o.matrix_world @ v.co; lo = V(map(min, lo, w)); hi = V(map(max, hi, w))
        print(f'[verify] {grp}: tris {sum(H.tri_count(o) for o in meshes if grp == "all" or not o.name.startswith("CART"))}; X {lo.x:.3f}..{hi.x:.3f} height(Z after import) {hi.z - lo.z:.3f} depth(Y) {lo.y:.3f}..{hi.y:.3f}')
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
    openb('ice_anim.blend'); O = bpy.data.objects; rig = O['ice_rig']; head = O['ice_head']; cam = O['cam']
    only = [a for a in ARGS if a in ('beauty', 'turn', 'expr', 'sheet', 'hands', 'nocart')]
    want = lambda k: not [a for a in only if a != 'nocart'] or k in only
    if 'nocart' in only: O['CART'].hide_render = True
    g = GS
    play(rig, 'idle', 0); set_key(head, 'none')
    if want('beauty'): shoot(cam, os.path.join(SHOTS, 'beauty.png'), 1600, 1600, 30, 10, (.35, .55, 1.15), 3.3, cam_z=1.5)
    if want('hands'):
        for nm, W in (('r', CR), ('l', CL), ('face', HC)): shoot(cam, os.path.join(WORK, 'close_%s.png' % nm), 700, 700, 20, 7, W * g, .7)
    if want('turn'):
        ps = []
        for i, ang in enumerate((0, 90, 180)):
            rig.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
            t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((.35, .55, 1.2)); p = os.path.join(WORK, 't_%d.png' % i); ps.append(p)
            shoot(cam, p, 534, 800, 0, 11, t, 2.9)
        rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(SHOTS, 'turnaround.png'))
    if want('expr'):
        ps = []
        for name in ('smile', 'angry', 'grin', 'ult'):
            set_key(head, name); p = os.path.join(WORK, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, 0, (HC.z - .02) * g), 1.25)
        row(ps, os.path.join(SHOTS, 'expressions.png')); set_key(head, 'none')
    if want('sheet'):
        rows = []
        for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
            ps = []
            for i in range(4):
                play(rig, name, min(n, int(i * n / 4)) if name != 'ult' else (0 if i < 2 else 2)); p = os.path.join(WORK, 'a_%s_%d.png' % (name, i)); ps.append(p)
                shoot(cam, p, 400, 440, 30, 10, (.35, .55, 1.15), 3.3, cam_z=1.5)
            r = os.path.join(WORK, 'arow_%s.png' % name); row(ps, r); rows.append(r)
        vstack(rows, os.path.join(SHOTS, 'anim_sheet.png'))

STAGES = dict(build=stage_build, rig=stage_rig, anim=stage_anim, export=stage_export, verify=stage_verify, shots=stage_shots)
for a in ARGS:
    if a in STAGES: STAGES[a]()
