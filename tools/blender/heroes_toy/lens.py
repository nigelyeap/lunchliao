"""Long Lens Lim / Birdwatcher (key lens), style `toy`. Game-ready: rig, skin, 6 shape keys, 4 clips, glb.
Run: blender -b -P lens.py -- build rig anim export verify shots      (stages run in the order given)
Axes: Z up, hero faces +Y. Reuses the toy helpers from styles/toy/ahma_toy.py (exec'd, not modified), the head, face and
weight code from heroes_toy/gym.py (copied) and the two-hand prop IK from heroes_toy/ahma.py (copied).
Retired uncle bird photographer: bucket hat, grey hair, white brows, glasses, khaki vest with pockets, big white telephoto."""
import bpy, sys, os, math, importlib.util
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HD = os.path.dirname(os.path.abspath(__file__))
RT = os.path.abspath(os.path.join(HD, '..', '..', '..'))
WORK = os.path.join(HD, '_tmp_lens'); SHOTS = os.path.join(RT, 'shots', 'heroes_toy', 'lens'); OUT_GLB = os.path.join(RT, 'assets', 'heroes', 'lens.glb')
os.makedirs(WORK, exist_ok=True); os.makedirs(SHOTS, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build']

sys.path.insert(0, os.path.join(RT, 'tools', 'blender', 'heroes'))
TOY = os.path.join(RT, 'tools', 'blender', 'styles', 'toy', 'ahma_toy.py')
_src = open(TOY).read().split('# ---------------------------------------------------------------- main')[0]
_src = _src.replace("OUT = os.path.join(ROOT, 'shots', 'styles', 'toy')", "OUT = %r" % SHOTS).replace("TMP = os.path.join(HERE, '_tmp')", "TMP = %r" % WORK)
_src = _src.replace("HERE = os.path.dirname(os.path.abspath(__file__))", "HERE = %r" % os.path.dirname(TOY))
exec(compile(_src, TOY, 'exec'), globals())          # mat, mk, ell, tor, sweep, fillet, bez, rbox, stage, shoot, row, surf, sph_vf, M, V, Z, H, SC, HERO
HEIGHT = 1.88
GSF = os.path.join(WORK, 'gs.txt')
GS = float(open(GSF).read()) if os.path.exists(GSF) else 1.0

def ss(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)

def openb(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, name)); globals()['SC'] = bpy.context.scene

# ---- palette (old lens: khaki #b8a878, dark khaki #8f8259, hat #c9b98a, grey hair, white brows, black glasses, white lens, red ring)
M.update(
    skin=mat('skin', '#8A5A3C', .42, sss=.06), nose=mat('nose', '#80523A', .42, sss=.06), blush=mat('blush', '#94484E', .55),
    hair=mat('hair', '#B4B2AE', .35, coat=.25), brow=mat('brow', '#F1EFEA', .45), lip=mat('lip', '#9E4E4A', .4, coat=.3), mouth=mat('mouth', '#5E1A28', .45),
    vest=mat('vest', '#B8A878', .62), vestd=mat('vest_dark', '#8F8259', .6), shirt=mat('shirt', '#5F6B45', .6), pipe=mat('pipe_red', '#D8322B', .35, coat=.3),
    pants=mat('pants', '#3A3630', .62), sock=mat('sock', '#F2EFE8', .6), shoe=mat('shoe', '#6B4A30', .4, coat=.3), sole=mat('sole', '#EDE4D0', .5),
    hat=mat('hat', '#C9B98A', .7), hatband=mat('hatband', '#4A3F32', .6), frame=mat('frame', '#1C1C1C', .2, coat=1.0), btn=mat('btn', '#E9E2CF', .35, coat=.4),
    cam=mat('cam', '#1C1C1C', .35, coat=.3), rubber=mat('rubber', '#2E2E31', .75), lensw=mat('lens_white', '#F2F2EE', .28, coat=.6),
    glass=mat('glass', '#16294A', .05, coat=1.0, spec=.9), metal=mat('metal', '#C9CCD2', .25, metal=1.0), red=mat('red', '#E8312A', .3, coat=.5),
    watch=mat('watch', '#2A2A2E', .4, coat=.4), gold=mat('gold', '#F0B94A', .22, metal=1.0),
)

# ---- proportions (raw design units, scaled by GS at the end of build) ---------------------------
HC = V((0, 0, 1.30)); HR = V((0.50, 0.47, 0.43))
TR = [(.44, .30, .22), (.50, .32, .245), (.57, .335, .26), (.64, .335, .255), (.70, .33, .235), (.75, .325, .21), (.785, .29, .19),
      (.81, .22, .165), (.84, .16, .145), (.90, .15, .135), (.96, .15, .135)]
_a = np.array(TR); ZS = np.linspace(TR[0][0], TR[-1][0], 22); RXs = np.interp(ZS, _a[:, 0], _a[:, 1]); RYs = np.interp(ZS, _a[:, 0], _a[:, 2])
for _ in range(3):
    RXs[1:-1] = (RXs[:-2] + 2 * RXs[1:-1] + RXs[2:]) / 4; RYs[1:-1] = (RYs[:-2] + 2 * RYs[1:-1] + RYs[2:]) / 4
rxz = lambda z: float(np.interp(z, ZS, RXs)); ryz = lambda z: float(np.interp(z, ZS, RYs))
def tsurf(a_deg, z, off):
    a = math.radians(a_deg); return V(((rxz(z) + off) * math.cos(a), (ryz(z) + off) * math.sin(a), z))
def tnorm(a_deg, z):
    a = math.radians(a_deg); return V((math.cos(a) / rxz(z), math.sin(a) / ryz(z), 0)).normalized()
ZH = .45
def ztop(a):                                  # vest: V neck in front, round back neck, deep armholes, straps over the shoulders
    c = abs(math.cos(a)); d = abs(((math.degrees(a) - 90 + 180) % 360) - 180)
    z = .855 - .015 * ss(-.3, .3, math.sin(a))
    if d < 30: z = min(z, .60 + (.84 - .60) * (d / 30) ** .9)
    return z - ss(.85, .975, c) ** 1.2 * (z - .58)
def voff(z): return .014 + .045 * (1 - ss(ZH, .56, z)) + .02 * ss(.76, .85, z)

SHD = {1: V((.355, 0, .72)), -1: V((-.355, 0, .72))}
ELB = {1: V((.40, .10, .50)), -1: V((-.31, .21, .50))}
CAM = V((.03, .36, .67)); CB_H = V((.10, .065, .075))              # camera body centre and half size
LX, LZ = CAM.x, CAM.z; LY0, LY1 = .425, .86                          # lens axis (along +Y) and its span
GRIP = V((.112, .435, .665))
WR_R = V((.205, .295, .615)); PALM_R = V((.168, .37, .665))
WR_L = V((-.10, .47, .54)); PALM_L = V((-.005, .55, .556))
LEGX = .16

def lens_r(y):                                # white barrel radius along the lens
    return float(np.interp(y, [LY0, .47, .56, .70, .80, LY1], [.066, .074, .083, .085, .092, .096]))

def catmull(P, k=6):
    P = [V(p) for p in P]; n = len(P); out = []
    for i in range(n - 1):
        p0 = P[i - 1] if i > 0 else P[0]; p1 = P[i]; p2 = P[i + 1]; p3 = P[i + 2] if i + 2 < n else P[-1]
        for s in range(k):
            t = s / k; out.append(.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1]); return out

def ring(name, pts, r, m, seg=8):
    """Closed tube along a loop around the body (no end caps, so no seam or tab)."""
    import bmesh
    P = [V(p) for p in pts]; n = len(P); cen = sum(P, V()) / n; vs = []; fs = []
    for i, p in enumerate(P):
        T = (P[(i + 1) % n] - P[i - 1]).normalized(); N = V((p.x - cen.x, p.y - cen.y, 0)).normalized(); B = N.cross(T).normalized()
        vs += [p + (N * math.cos(2 * math.pi * k / seg) + B * math.sin(2 * math.pi * k / seg)) * r for k in range(seg)]
    for i in range(n):
        j = (i + 1) % n; fs += [(i * seg + k, i * seg + (k + 1) % seg, j * seg + (k + 1) % seg, j * seg + k) for k in range(seg)]
    ob = mk(name, vs, fs, m); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free(); return ob

def loop_tube(name, pts, nrm, r, m, seg=6):
    """Closed tube along a planar loop with plane normal nrm (glasses frames)."""
    import bmesh
    P = [V(p) for p in pts]; n = len(P); vs = []; fs = []
    for i, p in enumerate(P):
        T = (P[(i + 1) % n] - P[i - 1]).normalized(); B = nrm.cross(T).normalized()
        vs += [p + (nrm * math.cos(2 * math.pi * k / seg) + B * math.sin(2 * math.pi * k / seg)) * r for k in range(seg)]
    for i in range(n):
        j = (i + 1) % n; fs += [(i * seg + k, i * seg + (k + 1) % seg, j * seg + (k + 1) % seg, j * seg + k) for k in range(seg)]
    ob = mk(name, vs, fs, m); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free(); return ob

def lathe(name, zs, rx, ry, m, seg=28, off=0.0, mats=None):
    vs = []; fs = []; mi = []
    for z, a, b in zip(zs, rx, ry):
        for i in range(seg):
            t = 2 * math.pi * i / seg; vs.append(V(((a + off) * math.cos(t), (b + off) * math.sin(t), z)))
    for j in range(len(zs) - 1):
        for i in range(seg):
            fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i)); mi.append(mats(.5 * (zs[j] + zs[j + 1])) if mats else 0)
    fs.append(tuple(range(seg - 1, -1, -1))); mi.append(0)
    return mk(name, vs, fs, m, mat_idx=mi if mats else None)

def prof_lathe(name, cen, rx, ry, prof, m, seg=48):
    """Closed ring: a closed (dr, dz) profile swept round an ellipse (rx, ry) at cen. Hat brim."""
    vs = []; fs = []; k = len(prof)
    for i in range(seg):
        t = 2 * math.pi * i / seg
        for dr, dz in prof: vs.append(V((cen[0] + (rx + dr) * math.cos(t), cen[1] + (ry + dr) * math.sin(t), cen[2] + dz)))
    for i in range(seg):
        for j in range(k):
            a = i * k + j; b = ((i + 1) % seg) * k + j; c = ((i + 1) % seg) * k + (j + 1) % k; d = i * k + (j + 1) % k; fs.append((a, b, c, d))
    import bmesh
    ob = mk(name, vs, fs, m); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free(); return ob

def onbody(a_deg, z, off):                      # frame for parts sitting on the vest: x = tangent, y = outward, z = up
    n = tnorm(a_deg, z); t = Z.cross(n).normalized() * -1
    return tsurf(a_deg, z, off), Matrix(((t.x, n.x, 0), (t.y, n.y, 0), (t.z, n.z, 1)))

# ---------------------------------------------------------------- body
def build_torso():
    lathe('torso', ZS, RXs, RYs, [M['shirt'], M['skin']], mats=lambda z: 1 if z > .845 else 0)
    seg = 80; J = 9; vs = []; fs = []
    for i in range(seg):                                                    # inner closing ring at the hem
        t = 2 * math.pi * i / seg; vs.append(V((rxz(ZH) * math.cos(t), ryz(ZH) * math.sin(t), ZH)))
    for j in range(J):
        for i in range(seg):
            t = 2 * math.pi * i / seg; zt = ztop(t); z = ZH + (zt - ZH) * j / (J - 1); off = voff(z)
            vs.append(V(((rxz(z) + off) * math.cos(t), (ryz(z) + off) * math.sin(t), z)))
    for i in range(seg):                                                    # inner closing ring at the neckline
        t = 2 * math.pi * i / seg; zt = ztop(t); vs.append(V(((rxz(zt) - .004) * math.cos(t), (ryz(zt) - .004) * math.sin(t), zt)))
    R = J + 2
    for j in range(R - 1):
        for i in range(seg): fs.append((j * seg + i, (j + 1) * seg + i, (j + 1) * seg + (i + 1) % seg, j * seg + (i + 1) % seg))
    mk('vest', vs, fs, M['vest'])
    ring('pipe_neck', [tsurf(360 * i / 96, ztop(2 * math.pi * i / 96), voff(ztop(2 * math.pi * i / 96)) + .004) for i in range(96)], .009, M['pipe'], seg=4)
    ring('pipe_hem', [tsurf(360 * i / 64, ZH + .004, voff(ZH) + .002) for i in range(64)], .010, M['pipe'], seg=5)
    # zip line from the bottom of the V to the hem
    sweep('zip', [tsurf(90, z, voff(z) + .002) for z in np.linspace(.60, ZH + .01, 8)], .008, M['vestd'], seg=6)
    # pockets: two chest, two big lower, each with a darker flap and a button
    for a, z, w, h in ((60, .695, .095, .085), (120, .695, .095, .085), (64, .535, .125, .105), (116, .535, .125, .105)):
        p, Rm = onbody(a, z, voff(z) + .012)
        rbox('pocket', p, (w, .026, h), M['vest'], bevel=.008, rot=Rm, bseg=2)
        p2, _ = onbody(a, z + h * .42, voff(z + h * .42) + .022)
        rbox('flap', p2, (w * 1.06, .022, h * .32), M['vestd'], bevel=.007, rot=Rm, bseg=2)
        p3, _ = onbody(a, z + h * .38, voff(z + h * .38) + .036); ell('button', p3, (.011, .008, .011), M['btn'], rot=Rm, seg=10)
    # shirt collar and buttons inside the V
    tor('collar', (0, .004, .838), Z, .165, .022, M['shirt'], seg=28, rseg=5, squash=(1, .92, 1))
    for z in (.65, .72, .79): ell('button', tsurf(90, z, .006), (.012, .008, .012), M['btn'], seg=10)

def build_legs():
    ell('pants_hip', (0, 0, .46), (.315, .235, .12), M['pants'], seg=20)
    for s in (-1, 1):
        x = s * LEGX
        sweep('pantleg', [(x, 0, .50), (x, .005, .34), (x, .01, .17)], [.155, .14, .125], M['pants'], seg=18, lip=(.01, .09))
        tor('pantcuff', (x, .01, .175), Z, .126, .012, M['pants'], seg=20, rseg=4)
        p = V((x + s * .135, 0, .34)); Rm = Matrix.Rotation(math.radians(90 * s), 3, 'Z')
        rbox('cargo', p, (.10, .03, .10), M['pants'], bevel=.008, rot=Rm, bseg=2)
        rbox('cargoflap', p + V((s * .014, 0, .045)), (.106, .022, .03), M['pants'], bevel=.006, rot=Rm, bseg=2)
        sweep('sock', [(x, .01, .19), (x, .01, .10)], [.092, .088], M['sock'], seg=18, round_caps=False)
        ell('shoe', (x, .07, .072), (.11, .19, .08), M['shoe'], seg=14)
        ell('shoe_sole', (x, .075, .03), (.118, .205, .034), M['sole'], seg=14)
        ell('shoe_tongue', (x, .035, .135), (.05, .055, .03), M['sole'], seg=10)
        for k in range(2): tor('shoe_lace', (x, .08 + .04 * k, .125 - .025 * k), (0, .55, 1), .03, .0065, M['sole'], seg=10, rseg=4, squash=(1.4, 1, 1))

def build_arm(k):
    S, E = SHD[k], ELB[k]; W = WR_R if k == 1 else WR_L; sd = 'r' if k == 1 else 'l'
    so = H.Soup('arm_' + sd); so.sphere(S, .12, seg=18); so.capsule(S, E, .112, .088); so.capsule(E, W, .088, .062); so.sphere(W, .062)
    a, _ = so.remesh(voxel=.011, smooth=5, smooth_factor=.55, target_tris=720); H.set_material(a, M['skin']); a.name = 'arm_' + sd; reg(a)
    d = (E - S).normalized()
    sweep('sleeve_' + sd, [S - d * .04, S.lerp(E, .45), S.lerp(E, .8)], [.135, .128, .118], M['shirt'], seg=20, lip=(.012, .09))
    tor('sleevecuff_' + sd, S.lerp(E, .8) - d * .004, d, .118, .011, M['vestd'], seg=24, rseg=5)

def build_hand_r():
    """Right hand on the camera grip: palm on the right side, four fingers round the front of the grip, thumb on the back."""
    h = H.Soup('hand_r'); h.ellipsoid(PALM_R, (.03, .068, .075)); h.capsule(WR_R, PALM_R + V((.0, -.02, -.01)), .062, .055)
    rf = .019
    for k, dz in enumerate((.052, .018, -.016, -.05)):
        r = rf - .0015 * (k == 3); rho = .05 + r
        pts = [V((GRIP.x + rho * math.cos(math.radians(t)), GRIP.y + rho * math.sin(math.radians(t)), GRIP.z + dz)) for t in (-30, 10, 50, 95, 135)]
        pts[0] = V((PALM_R.x + .01, PALM_R.y + .03, GRIP.z + dz))
        for p0, p1, r0, r1 in zip(pts[:-1], pts[1:], (r + .003, r + .001, r, r), (r + .001, r, r, r * .85)): h.capsule(p0, p1, r0, r1, seg=12)
    by = CAM.y - CB_H.y - .02
    th = [PALM_R + V((-.01, -.05, .03)), V((.13, by, .71)), V((.095, by, .735)), V((.07, by + .004, .745))]
    for p0, p1, r0, r1 in zip(th[:-1], th[1:], (.03, .027, .025), (.027, .025, .022)): h.capsule(p0, p1, r0, r1, seg=12)
    hd, _ = h.remesh(voxel=.0065, smooth=5, smooth_factor=.5, target_tris=950); H.set_material(hd, M['skin']); hd.name = 'hand_r'; reg(hd)

def build_hand_l():
    """Left hand cradles the lens from below: palm under the barrel, fingers up the right side, thumb up the left side."""
    h = H.Soup('hand_l'); h.ellipsoid(PALM_L, (.07, .062, .026)); h.capsule(WR_L, PALM_L + V((-.03, 0, 0)), .062, .05)
    rf = .019
    for k, y in enumerate((PALM_L.y + .045, PALM_L.y + .015, PALM_L.y - .015, PALM_L.y - .045)):
        rho = lens_r(y) + rf + .002; r = rf - .0015 * (k == 0)
        pts = [V((LX + rho * math.cos(math.radians(p)), y, LZ + rho * math.sin(math.radians(p)))) for p in (-70, -38, -6, 24, 50)]
        for p0, p1, r0, r1 in zip(pts[:-1], pts[1:], (r + .003, r + .001, r, r), (r + .001, r, r, r * .85)): h.capsule(p0, p1, r0, r1, seg=12)
    y = PALM_L.y - .01; rho = lens_r(y) + .024
    th = [PALM_L + V((-.05, -.01, .0))] + [V((LX + rho * math.cos(math.radians(p)), y + .01, LZ + rho * math.sin(math.radians(p)))) for p in (-140, -165, -188)]
    for p0, p1, r0, r1 in zip(th[:-1], th[1:], (.03, .027, .025), (.027, .025, .022)): h.capsule(p0, p1, r0, r1, seg=12)
    hd, _ = h.remesh(voxel=.0065, smooth=5, smooth_factor=.5, target_tris=950); H.set_material(hd, M['skin']); hd.name = 'hand_l'; reg(hd)
    d = (WR_L - ELB[-1]).normalized(); c = ELB[-1].lerp(WR_L, .82)
    tor('watch_l', c, d, .051, .011, M['watch'], seg=24, rseg=6)
    up = V((0, 0, 1)) - d * d.z; up.normalize()
    ell('watchface_l', c + up * .06, (.03, .03, .012), M['gold'], rot=Matrix((d.cross(up), d, up)).transposed(), seg=14)

def build_camera():
    rbox('cam_body', CAM, (CB_H.x * 2, CB_H.y * 2, CB_H.z * 2), M['cam'], bevel=.022, bseg=3)
    rbox('cam_prism', CAM + V((-.005, -.012, CB_H.z + .03)), (.085, .085, .07), M['cam'], bevel=.018, bseg=3)
    rbox('cam_grip', GRIP, (.075, .055, .15), M['rubber'], bevel=.022, bseg=3)
    sweep('cam_btn', [GRIP + V((0, -.005, .075)), GRIP + V((0, -.005, .088))], .016, M['red'], seg=12)
    rbox('cam_eyecup', CAM + V((-.005, -CB_H.y - .02, CB_H.z + .02)), (.06, .03, .045), M['rubber'], bevel=.01, bseg=2)
    sweep('cam_dial', [CAM + V((-.07, 0, CB_H.z)), CAM + V((-.07, 0, CB_H.z + .02))], .022, M['metal'], seg=14)
    ys = np.linspace(LY0, LY1, 12)
    sweep('cam_lens', [V((LX, y, LZ)) for y in ys], [lens_r(y) for y in ys], M['lensw'], seg=28, round_caps=False)
    sweep('cam_mount', [V((LX, CAM.y + CB_H.y - .01, LZ)), V((LX, LY0 + .012, LZ))], [.07, .07], M['metal'], seg=28, round_caps=False)
    sweep('cam_focus', [V((LX, .615, LZ)), V((LX, .68, LZ))], [.0895, .0895], M['rubber'], seg=28, round_caps=False)
    tor('cam_redring', (LX, .785, LZ), (0, 1, 0), lens_r(.785) + .002, .011, M['red'], seg=32, rseg=6)
    tor('cam_collar', (LX, .50, LZ), (0, 1, 0), lens_r(.50) + .003, .012, M['lensw'], seg=28, rseg=5)
    sweep('cam_hood', [V((LX, LY1 - .02, LZ)), V((LX, LY1 + .07, LZ))], [.104, .112], M['cam'], seg=28, round_caps=False, lip=(.006, .1))
    ell('cam_glass', (LX, LY1 + .005, LZ), (.084, .012, .084), M['glass'], seg=16)

def build_neck():
    ell('neck_col', (0, 0, .875), (.17, .155, .115), M['skin'], seg=20)

def build_body_all():
    build_torso(); build_legs(); build_arm(1); build_arm(-1); build_hand_r(); build_hand_l(); build_camera(); build_neck()

# ---------------------------------------------------------------- head (head surface, hole and face system from gym.py)
HOLE = (0.0, -.245, .215, .14)

def jaw(p):                                   # soft jaw: widen and flatten the lower head a little
    d = p - HC; t = ss(-.08, -.33, d.z)
    return HC + V((d.x * (1 + .16 * t), d.y * (1 + .1 * t), jz(d.z)))

JK = .025
def jz(z): return z + .6 * JK * float(np.logaddexp(0.0, (-.33 - z) / JK))   # smooth version of the old hard flatten below -.33
def jaw_inv(w):
    d = w - HC; lo, hi = -1.5, 1.5
    for _ in range(48):
        m = .5 * (lo + hi)
        if jz(m) < d.z: lo = m
        else: hi = m
    z = .5 * (lo + hi); t = ss(-.08, -.33, z); return V((d.x / (1 + .16 * t), d.y / (1 + .1 * t), z))
def head_n(w):                               # exact normal of the jaw-shaped head surface at w (gradient of its implicit form)
    def F(q): d = jaw_inv(q); return (d.x / HR.x) ** 2 + (d.y / HR.y) ** 2 + (d.z / HR.z) ** 2
    e = 1e-4; return V([(F(w + V(a) * e) - F(w - V(a) * e)) for a in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]).normalized()
def head_normals(ob, skip_mats=()):
    me = ob.data; oth = {v for p in me.polygons if p.material_index in skip_mats for v in p.vertices}
    me.normals_split_custom_set_from_vertices([tuple(head_n(v.co)) if v.index not in oth else tuple(v.normal) for v in me.vertices])

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

def build_hair():
    """Grey hair as one smooth shell over the sides and back, from under the hat brim down to the nape. Clean edge, no lumps."""
    def thr(az): return float(np.interp(az, [0, 35, 62, 75, 100, 125, 180], [54, 50, 26, 12, 10, -22, -56]))
    NC, NR, HI = 60, 12, 34.0; vs = []; fs = []
    for i in range(NC + 1):
        ph = 58 + (302 - 58) * i / NC; af = min(ph, 360 - ph); lo = thr(af); tp = ss(58, 74, af)
        for j in range(NR + 1):
            u = j / NR; el = math.radians(lo + (HI - lo) * u); a = math.radians(ph)
            q = HC + V((math.cos(el) * math.sin(a) * HR.x, math.cos(el) * math.cos(a) * HR.y, math.sin(el) * HR.z)); w = jaw(q)
            vs.append(w + head_n(w) * max(.004, (.006 + .03 * ss(0, .45, u)) * tp))
    for i in range(NC):
        for j in range(NR): fs.append((i * (NR + 1) + j, (i + 1) * (NR + 1) + j, (i + 1) * (NR + 1) + j + 1, i * (NR + 1) + j + 1))
    import bmesh
    ob = mk('h_hair', vs, fs, M['hair']); bm = bmesh.new(); bm.from_mesh(ob.data)
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(c - HC) < 0: f.normal_flip()
    bm.to_mesh(ob.data); bm.free()

HAT_Z = .27                                    # crown base, above the head centre
def build_head():
    head_normals(head_surface())
    build_hair()
    for s in (-1, 1): ell('h_ear', HC + V((s * .49, -.03, -.04)), (.045, .08, .1), M['skin'], seg=16)
    p, n_, t, u = surf(0, -.085); ell('h_nose', p + n_ * .004, (.066, .054, .055), M['nose'], seg=18)
    # bucket hat: domed crown, band, sloping brim with a stitch line
    z0 = HC.z + HAT_Z; k0 = math.sqrt(1 - (HAT_Z / HR.z) ** 2); bx, by = HR.x * k0 + .03, HR.y * k0 + .03
    dz = [0, .05, .10, .14, .17, .19, .203, .208]; fr = [1, .985, .96, .93, .885, .79, .55, .05]
    lathe('h_hat', [z0 + q for q in dz], [bx * f for f in fr], [by * f for f in fr], M['hat'], seg=40)
    tor('h_hatband', (0, 0, z0 + .035), Z, bx - .002, .015, M['hatband'], seg=40, rseg=5, squash=(1, by / bx, 1))
    prof = [(-.01, .012), (.06, -.014), (.12, -.048), (.165, -.082), (.18, -.098), (.17, -.108), (.115, -.068), (.055, -.032), (-.01, -.012)]
    prof_lathe('h_brim', (0, 0, z0), bx, by, prof, M['vest'], seg=48)
    tor('h_stitch', (0, 0, z0 - .044), Z, bx + .115, .0045, M['vestd'], seg=48, rseg=3, squash=(1, (by + .115) / (bx + .115), 1))
    # glasses: rounded rectangle frames, a bridge over the nose, temples to the ears. Frames only, so eyes stay readable
    cs = {}
    for s in (-1, 1):
        p, n_, t, u = surf(s * EXe, EZe); c = p + n_ * .042; hx, hz = .092, .074
        corners = [c + t * x + u * z for x, z in ((-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz))]
        pts = fillet(corners + [corners[0], corners[1]], .034, 5)[1:-1]
        loop_tube('h_glass', pts, n_, .011, M['frame'], seg=6); cs[s] = (c, t, u, n_, hx)
        outer = c + t * (s * hx) + u * .03
        ell('h_hinge', outer, (.016, .016, .016), M['frame'], seg=10)
        sweep('h_temple', fillet([outer, HC + V((s * .49, .2, .02)), HC + V((s * .47, .0, .02))], .1), .009, M['frame'], seg=6)
    a = cs[-1][0] + cs[-1][1] * cs[-1][4] + cs[-1][2] * .02; b = cs[1][0] - cs[1][1] * cs[1][4] + cs[1][2] * .02
    sweep('h_bridge', bez(a, (a + b) * .5 + V((0, .035, .02)), b, 8), .01, M['frame'], seg=6)

# ---------------------------------------------------------------- face (one mesh, six shape keys), same build as gym
FM = ['skin', 'brow', 'eye', 'white', 'line', 'mouth', 'lip', 'teeth', 'tongue', 'blush']
EXe, EZe = .185, -.02
_I = dict(bz=.14, tilt=.03, arch=.008, eye='bead', es=(.8, .72), cut=(.02, 0), hl=.006, w=.19, curve=.03, up=0, dn=0, teeth=0, tongue=0, cz=-.235, arc=.058)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'eye': 'arc', 'arc': -.022, 'bz': .145},
    'mouth_open': {**_I, 'w': .2, 'curve': .012, 'up': .006, 'dn': .085, 'teeth': .032, 'tongue': .05},
    'smile': {**_I, 'w': .25, 'curve': .05, 'bz': .162, 'tilt': -.005},
    'angry': dict(bz=.06, tilt=.085, arch=-.004, eye='bead', es=(1.02, .9), cut=(.012, .6), hl=.0, w=.2, curve=-.052, up=.018, dn=.05, teeth=.034, tongue=0, cz=-.24, arc=.058),
    'grin': dict(bz=.168, tilt=-.012, arch=.03, eye='arc', es=(1, 1), cut=None, hl=.026, w=.32, curve=.06, up=.004, dn=.085, teeth=.034, tongue=.05, cz=-.25, arc=.062),
    'ult': dict(bz=.12, tilt=.06, arch=.004, eye='bead', es=(.95, .85), cut=(.02, 0), hl=.008, w=.27, curve=.006, up=.045, dn=.095, teeth=.034, tongue=.07, cz=-.25, arc=.058),
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
        stroke([(s * (EXe + q * .105), e['bz'] + EZe + q * e['tilt'] + e['arch'] * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .062, .038, .006, 'brow')
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
        # age: one crow's foot line at the outer eye corner
        stroke([(s * (EXe + .108 + .012 * q), EZe - .005 + .03 * q) for q in (-1, -.5, 0, .5, 1)], .006, .004, .003, 'line')
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
    ob = mk('h_face', vs, fs, [M[k] for k in FM], mat_idx=mi); head_normals(ob, skip_mats=set(range(1, len(FM)))); ob.shape_key_add(name='Basis')
    for name in KEYS:
        k = ob.shape_key_add(name=name); k.data.foreach_set('co', [c for v in face_geo(EXPR[name])[0] for c in v])
    return ob

# ---------------------------------------------------------------- build stage
def stage_build():
    build_body_all(); build_head(); build_face()
    tris = sum(H.tri_count(o) for o in HERO); print('TOY_TRIS', tris, 'objects', len(HERO))
    agg = {}
    for o in HERO: agg[o.name.split('.')[0]] = agg.get(o.name.split('.')[0], 0) + H.tri_count(o)
    print('TOY_TOP', sorted(agg.items(), key=lambda kv: -kv[1])[:40])
    for o in HERO: o.data.update()
    top = max((o.matrix_world @ v.co).z for o in HERO for v in o.data.vertices)
    gs = HEIGHT / top; globals()['GS'] = gs; open(GSF, 'w').write(repr(gs)); print('TOY_RAW_TOP', round(top, 4), 'GS', round(gs, 4))
    for o in HERO:
        for v in o.data.vertices: v.co *= gs
        if o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks:
                for v in kb.data: v.co *= gs
    stage()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'lens_build.blend'))

# ---------------------------------------------------------------- rig + weights (gym pattern; camera on the `prop` bone, hands IK to it)
def eyepos(s): return surf(s * EXe, EZe)[0]
BONES = [
    ('root', (0, 0, 0), (0, 0, .25), None), ('hips', (0, 0, .50), (0, 0, .60), 'root'), ('spine', (0, 0, .60), (0, 0, .70), 'hips'),
    ('chest', (0, 0, .70), (0, 0, .80), 'spine'), ('neck', (0, 0, .80), (0, .01, .90), 'chest'), ('head', (0, .01, .90), (0, .02, 1.74), 'neck'),
    ('eye.l', tuple(eyepos(-1)), tuple(eyepos(-1) + V((0, .06, 0))), 'head'), ('eye.r', tuple(eyepos(1)), tuple(eyepos(1) + V((0, .06, 0))), 'head'),
    ('upperarm.l', tuple(SHD[-1]), tuple(ELB[-1]), 'chest'), ('lowerarm.l', tuple(ELB[-1]), tuple(WR_L), 'upperarm.l'),
    ('hand.l', tuple(WR_L), tuple(PALM_L + V((.05, 0, 0))), 'lowerarm.l'), ('handslot.l', tuple(PALM_L + V((0, 0, .03))), tuple(PALM_L + V((0, .08, .03))), 'hand.l'),
    ('upperarm.r', tuple(SHD[1]), tuple(ELB[1]), 'chest'), ('lowerarm.r', tuple(ELB[1]), tuple(WR_R), 'upperarm.r'),
    ('hand.r', tuple(WR_R), tuple(PALM_R + V((0, .05, 0))), 'lowerarm.r'), ('handslot.r', tuple(GRIP), tuple(GRIP + V((0, .08, 0))), 'hand.r'),
    ('upperleg.l', (-LEGX, .02, .52), (-LEGX, .01, .29), 'hips'), ('lowerleg.l', (-LEGX, .01, .29), (-LEGX, 0, .10), 'upperleg.l'),
    ('foot.l', (-LEGX, 0, .10), (-LEGX, .12, .03), 'lowerleg.l'), ('toes.l', (-LEGX, .12, .03), (-LEGX, .26, .02), 'foot.l'),
    ('upperleg.r', (LEGX, .02, .52), (LEGX, .01, .29), 'hips'), ('lowerleg.r', (LEGX, .01, .29), (LEGX, 0, .10), 'upperleg.r'),
    ('foot.r', (LEGX, 0, .10), (LEGX, .12, .03), 'lowerleg.r'), ('toes.r', (LEGX, .12, .03), (LEGX, .26, .02), 'foot.r'),
    ('prop', tuple(CAM), tuple(CAM + V((0, 0, .3))), 'root'),
]
RIGID = {'eye.l', 'eye.r', 'handslot.l', 'handslot.r'}

def make_rig():
    arm = bpy.data.armatures.new('lens_rig'); ob = bpy.data.objects.new('lens_rig', arm); bpy.context.scene.collection.objects.link(ob)
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
    if n.startswith('cam_'): return {'prop': 1.0}
    if n.startswith('hand_'): return {'hand.' + n[-1]: 1.0}
    if n.startswith(('arm_', 'sleeve_', 'sleevecuff_', 'watch')):
        sd = n[-1]; k = 1 if sd == 'r' else -1; S, E = SHD[k], ELB[k]; W = WR_R if k == 1 else WR_L; tip = PALM_R if k == 1 else PALM_L
        w = chain(p, [S, E, W, tip], ['upperarm.' + sd, 'lowerarm.' + sd, 'hand.' + sd], [.1, .08])
        wc = 1 - ss(-.08, .16, (p - S).dot((E - S).normalized()))
        return merge(scale(w, 1 - wc), {'chest': wc})
    if n in ('torso', 'vest', 'zip', 'pocket', 'flap', 'button', 'collar') or n.startswith(('pipe', 'neck')): return trunk(p)
    if n == 'pants_hip':
        u = ss(.52, .40, p.z) * ss(.03, .13, abs(p.x)); return merge(scale(leg(p, s), u), scale({'hips': 1.0}, 1 - u))
    if n.startswith(('pantleg', 'pantcuff', 'cargo', 'sock', 'shoe')):
        w = leg(p, s)
        if n.startswith('shoe'):
            sd = 'l' if s < 0 else 'r'; t = ss(.15, .24, p.y); wf = w.pop('foot.' + sd); w['foot.' + sd] = wf * (1 - t); w['toes.' + sd] = wf * t
        h = ss(.44, .52, p.z) if n.startswith('pantleg') else 0.0
        return merge(scale(w, 1 - h), {'hips': h})
    print('[weights] unclassified', name); return {'hips': 1.0}

def stage_rig():
    openb('lens_build.blend'); O = bpy.data.objects
    parts = [o for o in O if o.type == 'MESH' and o.name != 'cyc']
    for o in parts:
        o.data.update()
        for v in o.data.vertices:
            for b, w in weights_for(o.name, v.co / GS).items():
                if w > 1e-3:
                    g = o.vertex_groups.get(b) or o.vertex_groups.new(name=b); g.add([v.index], w, 'REPLACE')
    heads = [o for o in parts if o.name.startswith('h_')]; heads.sort(key=lambda o: o.name != 'h_face')
    bodies = [o for o in parts if not o.name.startswith('h_')]
    head = H.join(heads, 'lens_head'); body = H.join(bodies, 'lens_body'); rig = make_rig()
    for ob in (head, body):
        ob.parent = rig; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = rig
        for v in ob.data.vertices:
            tot = sum(g.weight for g in v.groups)
            if tot < .5: print('[rig] weak vertex', ob.name, v.index, tot)
    for b in rig.data.bones: b.use_deform = b.name not in RIGID
    print('[rig] shape keys', [k.name for k in head.data.shape_keys.key_blocks], 'tris', H.tri_count(head), H.tri_count(body))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'lens_rig.blend'))

# ---------------------------------------------------------------- animation (two-hand prop IK from ahma.py)
FPS = 30
def Mrest(rig, name): return rig.data.bones[name].matrix_local.to_3x3()
def rest_head(rig, name): return rig.data.bones[name].head_local.copy()
def axis_rot(axis, deg): return Quaternion(Vector(axis), math.radians(deg))
def set_world_rot(rig, pb, q):
    M3 = Mrest(rig, pb.name); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (M3.inverted() @ q.to_matrix() @ M3).to_quaternion()
def set_total(rig, pb, total, Dp):
    Dc = Dp.inverted() @ total; M3 = Mrest(rig, pb.name); pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = (M3.inverted() @ Dc.to_matrix() @ M3).to_quaternion()
def parent_D(rig, pb):
    p = pb.parent; return (p.matrix.to_3x3() @ rig.data.bones[p.name].matrix_local.to_3x3().inverted()).to_quaternion()

def ik_arm(rig, sd, T, hand_q):
    B = rig.pose.bones; U, L, Hd = B['upperarm.' + sd], B['lowerarm.' + sd], B['hand.' + sd]
    S0, E0, W0 = (rest_head(rig, n) for n in ('upperarm.' + sd, 'lowerarm.' + sd, 'hand.' + sd))
    Dp = parent_D(rig, U); Sp = U.matrix.translation.copy()
    u0 = E0 - S0; l0 = W0 - E0; L1, L2 = u0.length, l0.length
    T = Vector(T); dv = T - Sp; d = min(dv.length, (L1 + L2) * .995); d = max(d, abs(L1 - L2) + 1e-3); dirv = dv.normalized()
    if dv.length > (L1 + L2) * .995: print('[ik] %s short by %.3f' % (sd, dv.length - (L1 + L2) * .995))
    a = (L1 * L1 - L2 * L2 + d * d) / (2 * d); h = math.sqrt(max(L1 * L1 - a * a, 0))
    d0 = (Dp @ (W0 - S0)).normalized(); pv = Dp @ u0; pv = pv - d0 * pv.dot(d0)
    pn = pv - dirv * pv.dot(dirv); pn = pn.normalized() if pn.length > 1e-6 else Vector((0, 0, -1))
    Ep = Sp + dirv * a + pn * h; Tp = Sp + dirv * d
    q1 = (Dp @ u0).rotation_difference(Ep - Sp) @ Dp; set_total(rig, U, q1, Dp)
    q2 = (q1 @ l0).rotation_difference(Tp - Ep) @ q1; set_total(rig, L, q2, q1)
    set_total(rig, Hd, hand_q, q2)

def reset_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
def hips_lift(rig, dz):
    pb = rig.pose.bones['hips']; pb.location = Mrest(rig, 'hips').inverted() @ Vector((0, 0, dz))
def set_prop(rig, q, t):
    pb = rig.pose.bones['prop']; set_world_rot(rig, pb, q); pb.location = Mrest(rig, 'prop').inverted() @ Vector(t)

RAISE = V((0, .07, .21))                       # camera up to the chin, lens level: the "shot" pose
def pose_frame(rig, t, kind):
    reset_pose(rig); B = rig.pose.bones; X = (1, 0, 0); Y_ = (0, 1, 0); Z_ = (0, 0, 1); s = math.sin(2 * math.pi * t); c = math.cos(2 * math.pi * t)
    pq, pt = Quaternion(), Vector((0, 0, 0)); g = GS
    if kind == 'idle':                         # patient breathing, a slow look round for birds
        set_world_rot(rig, B['chest'], axis_rot(X, 1.5 * s)); set_world_rot(rig, B['head'], axis_rot(X, -1.5 * s) @ axis_rot(Z_, 7.0 * math.sin(2 * math.pi * t + .6)))
        hips_lift(rig, .005 * g * s); pq = axis_rot(X, 1.5 * c); pt = Vector((0, 0, .01 * g * s))
    elif kind == 'run':
        for k, sg in ((-1, 1), (1, -1)):
            sd = 'l' if k < 0 else 'r'
            set_world_rot(rig, B['upperleg.' + sd], axis_rot(X, 34 * s * sg))
            set_world_rot(rig, B['lowerleg.' + sd], axis_rot(X, -48 * max(0.0, -s * sg)))
            set_world_rot(rig, B['foot.' + sd], axis_rot(X, 15 * max(0.0, -s * sg)))
        set_world_rot(rig, B['spine'], axis_rot(X, 5)); set_world_rot(rig, B['chest'], axis_rot(X, 10) @ axis_rot(Z_, 4 * s)); set_world_rot(rig, B['head'], axis_rot(X, -8) @ axis_rot(Z_, -3 * s))
        hips_lift(rig, (.03 * abs(s) - .015) * g)
        pq = axis_rot(X, 4 * math.sin(4 * math.pi * t)) @ axis_rot(Z_, -4 * s); pt = Vector((0, .02 * g, (.03 * abs(s) - .005) * g))
    elif kind == 'attack':                     # snap the camera up, click (small kick), bring it back down
        if t < .28: u = ss(0, 1, t / .28); k = u; kick = 0.0
        elif t < .55: u = (t - .28) / .27; k = 1.0; kick = math.sin(min(1.0, u * 2.5) * math.pi) * (1 - u)
        else: u = (t - .55) / .45; k = 1 - ss(0, 1, u); kick = 0.0
        pq = axis_rot(X, 6 * kick); pt = RAISE * g * k + Vector((0, -.025 * g * kick, .01 * g * kick))
        set_world_rot(rig, B['chest'], axis_rot(X, 4 * k - 3 * kick)); set_world_rot(rig, B['spine'], axis_rot(X, 2 * k))
        set_world_rot(rig, B['head'], axis_rot(X, -7 * k) @ axis_rot(Y_, 5 * k))
    elif kind == 'ult':                        # Golden Ratio: braced stance, camera up, locked on
        pt = RAISE * g + Vector((0, .02 * g, -.01 * g)); pq = axis_rot(X, 3)
        for k, sd in ((-1, 'l'), (1, 'r')):
            set_world_rot(rig, B['upperleg.' + sd], axis_rot(Y_, -9 * k) @ axis_rot(X, 14 if k < 0 else -6))
            set_world_rot(rig, B['lowerleg.' + sd], axis_rot(Y_, -9 * k) @ axis_rot(X, -14 if k < 0 else -2))
        set_world_rot(rig, B['spine'], axis_rot(X, 4)); set_world_rot(rig, B['chest'], axis_rot(X, 5)); set_world_rot(rig, B['head'], axis_rot(X, -6) @ axis_rot(Y_, 6))
        hips_lift(rig, -.025 * g)
    set_prop(rig, pq, pt); bpy.context.view_layer.update()
    PIV = rest_head(rig, 'prop')
    for k in (-1, 1):
        sd = 'l' if k < 0 else 'r'
        W0 = rest_head(rig, 'hand.' + sd); T = PIV + pq @ (W0 - PIV) + pt
        ik_arm(rig, sd, T, pq); bpy.context.view_layer.update()

ANIM_BONES = ['hips', 'spine', 'chest', 'neck', 'head', 'upperarm.l', 'lowerarm.l', 'hand.l', 'upperarm.r', 'lowerarm.r', 'hand.r',
              'upperleg.l', 'lowerleg.l', 'foot.l', 'upperleg.r', 'lowerleg.r', 'foot.r', 'prop']
def make_action(rig, name, kind, n):
    act = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act
    for f in range(n + 1):
        SC.frame_set(f); pose_frame(rig, (f % n) / n if kind != 'ult' else 0.0, kind)
        for b in ANIM_BONES:
            pb = rig.pose.bones[b]; pb.keyframe_insert('rotation_quaternion', frame=f)
            if b in ('hips', 'prop'): pb.keyframe_insert('location', frame=f)
    act.frame_range = (0, n); act.use_frame_range = True; act.use_fake_user = True; return act

def stage_anim():
    openb('lens_rig.blend'); SC.render.fps = FPS; rig = bpy.data.objects['lens_rig']
    acts = [make_action(rig, 'idle', 'idle', 60), make_action(rig, 'run', 'run', 24), make_action(rig, 'attack', 'attack', 18), make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    reset_pose(rig)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'lens_anim.blend')); print('[anim] actions', [a.name for a in acts])

def stage_export():
    openb('lens_anim.blend'); O = bpy.data.objects; rig = O['lens_rig']; reset_pose(rig)
    for k in O['lens_head'].data.shape_keys.key_blocks: k.value = 0.0
    H.select_only([O['lens_head'], O['lens_body'], rig], rig)
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

# ---------------------------------------------------------------- shots (gym stage and cameras, scaled to this height)
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
    openb('lens_anim.blend'); O = bpy.data.objects; rig = O['lens_rig']; head = O['lens_head']; cam = O['cam']
    only = [a for a in ARGS if a in ('beauty', 'turn', 'expr', 'sheet', 'hands')]
    want = lambda k: not only or k in only
    r = HEIGHT / 2.05; hz = HC.z * GS
    play(rig, 'idle', 0); set_key(head, 'none')
    if 'hands' in only:
        shoot(cam, os.path.join(WORK, 'hands.png'), 900, 700, 20, 7, CAM * GS + V((0, .1, 0)), .95)
        shoot(cam, os.path.join(WORK, 'hands_side.png'), 900, 700, -70, 7, CAM * GS + V((0, .1, 0)), .95)
        shoot(cam, os.path.join(WORK, 'hands_low.png'), 900, 700, 35, 7, CAM * GS + V((0, .1, -.05)), .95, cam_z=.15)
        return
    if want('beauty'): shoot(cam, os.path.join(SHOTS, 'beauty.png'), 1600, 1600, 32, 8, (0, .2, .9 * r), 2.3 * r, cam_z=.85 * r)
    if want('turn'):
        ps = []
        for i, ang in enumerate((0, 90, 180)):
            rig.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
            t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((0, .12, .9 * r)); p = os.path.join(WORK, 't_%d.png' % i); ps.append(p)
            shoot(cam, p, 534, 800, 0, 9, t, 1.75 * r)
        rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(SHOTS, 'turnaround.png'))
    if want('expr'):
        ps = []
        for name in ('smile', 'angry', 'grin', 'ult'):
            set_key(head, name); p = os.path.join(WORK, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, 0, hz - .06), 1.3)
        row(ps, os.path.join(SHOTS, 'expressions.png')); set_key(head, 'none')
    if want('sheet'):
        rows = []
        for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
            ps = []
            for i in range(4):
                play(rig, name, min(n, int(i * n / 4)) if name != 'ult' else (0 if i < 2 else 2)); p = os.path.join(WORK, 'a_%s_%d.png' % (name, i)); ps.append(p)
                shoot(cam, p, 400, 440, 25, 8, (0, .15, .92 * r), 2.3 * r, cam_z=.9 * r)
            rr = os.path.join(WORK, 'arow_%s.png' % name); row(ps, rr); rows.append(rr)
        vstack(rows, os.path.join(SHOTS, 'anim_sheet.png'))

STAGES = dict(build=stage_build, rig=stage_rig, anim=stage_anim, export=stage_export, verify=stage_verify, shots=stage_shots)
for a in ARGS:
    if a in STAGES: STAGES[a]()
