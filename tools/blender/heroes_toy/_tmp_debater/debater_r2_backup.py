"""Head Prefect (debater), style `toy` (designer vinyl collectible). Game-ready: rig, skin, 6 shape keys, 4 clips, glb.
Run: blender -b -P debater.py -- build rig anim export verify shots      (stages run in the order given)
Axes: Z up, hero faces +Y. Built on gym.py: the toy helpers from styles/toy/ahma_toy.py (exec'd, not modified),
the Pose / make_action code from heroes/gym.py (imported, not modified), gym's face, rig, weights, export and shots."""
import bpy, sys, os, math, importlib.util
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HD = os.path.dirname(os.path.abspath(__file__))
RT = os.path.abspath(os.path.join(HD, '..', '..', '..'))
KEY = 'debater'
WORK = os.path.join(HD, '_tmp_' + KEY); SHOTS = os.path.join(RT, 'shots', 'heroes_toy', KEY); OUT_GLB = os.path.join(RT, 'assets', 'heroes', KEY + '.glb')
os.makedirs(WORK, exist_ok=True); os.makedirs(SHOTS, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build']

sys.path.insert(0, os.path.join(RT, 'tools', 'blender', 'heroes'))
_sp = importlib.util.spec_from_file_location('og_gym', os.path.join(RT, 'tools', 'blender', 'heroes', 'gym.py'))
OG = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(OG)
TOY = os.path.join(RT, 'tools', 'blender', 'styles', 'toy', 'ahma_toy.py')
_src = open(TOY).read().split('# ---------------------------------------------------------------- main')[0]
_src = _src.replace("OUT = os.path.join(ROOT, 'shots', 'styles', 'toy')", "OUT = %r" % SHOTS).replace("TMP = os.path.join(HERE, '_tmp')", "TMP = %r" % WORK)
_src = _src.replace("HERE = os.path.dirname(os.path.abspath(__file__))", "HERE = %r" % os.path.dirname(TOY))
exec(compile(_src, TOY, 'exec'), globals())          # mat, mk, ell, tor, sweep, fillet, bez, stage, shoot, row, surf, sph_vf, M, V, Z, H, SC, HERO
ss = OG.smoothstep
HEIGHT = 1.69
GS_FILE = os.path.join(WORK, 'gs.txt')
GS = float(open(GS_FILE).read()) if os.path.exists(GS_FILE) else 1.0     # final uniform scale, measured in stage_build

def openb(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, name)); globals()['SC'] = bpy.context.scene

# ---- palette (HEROES body 0x7b2436 = blazer maroon; gold piping; white blouse; slate pleated skirt) ----------
M.update(
    skin=mat('skin', '#EDB48C', .42, sss=.12), nose=mat('nose', '#E7A07A', .42, sss=.12), blush=mat('blush', '#EE8F92', .5),
    hair=mat('hair', '#1C1719', .28, coat=.45), brow=mat('brow', '#211A1C', .45),
    maroon=mat('maroon', '#7B2436', .5, coat=.15), dmaroon=mat('dmaroon', '#561726', .5), gold=mat('gold', '#E8B93E', .3, coat=.5),
    goldm=mat('gold_metal', '#E2B547', .22, metal=1.0), shirt=mat('shirt', '#F7F6F0', .55), skirt=mat('skirt', '#5A6274', .55),
    skirt_in=mat('skirt_in', '#3E4452', .7), sock=mat('sock', '#F7F6F0', .6), shoe=mat('shoe', '#17151A', .25, coat=1.0), sole=mat('sole', '#2E2A31', .6),
    cream=mat('cream', '#F2E6CF', .5), ink=mat('ink', '#26232A', .5, coat=.3), wood=mat('wood', '#8A5E3A', .45, coat=.6),
    rim=mat('rim', '#221B1F', .2, coat=1.0), lip=mat('lip', '#D26470', .4, coat=.3), mouth=mat('mouth', '#5E1A28', .45), team=mat('team', '#F7F6F0', .4),
)

# ---- proportions (build units; GS scales to HEIGHT) ---------------------------------------------
HC = V((0, 0, 1.255)); HR = V((0.47, 0.45, 0.43))
TR = [(.40, .215, .165), (.47, .22, .17), (.55, .228, .168), (.62, .25, .178), (.69, .275, .188), (.74, .285, .19), (.775, .27, .18),
      (.80, .225, .162), (.825, .16, .13), (.85, .12, .105)]
_a = np.array(TR); ZS = np.linspace(TR[0][0], TR[-1][0], 22); RXs = np.interp(ZS, _a[:, 0], _a[:, 1]); RYs = np.interp(ZS, _a[:, 0], _a[:, 2])
for _ in range(3):
    RXs[1:-1] = (RXs[:-2] + 2 * RXs[1:-1] + RXs[2:]) / 4; RYs[1:-1] = (RYs[:-2] + 2 * RYs[1:-1] + RYs[2:]) / 4
rxz = lambda z: float(np.interp(z, ZS, RXs)); ryz = lambda z: float(np.interp(z, ZS, RYs))
def tsurf(a_deg, z, off):
    a = math.radians(a_deg); return V(((rxz(z) + off) * math.cos(a), (ryz(z) + off) * math.sin(a), z))
ZH = .42                                       # blazer hem
VZ = .585                                      # bottom of the blazer V
def ztop(a):                                   # blazer neckline: high round collar at the back, a V to the waist button in front
    da = abs(math.atan2(math.sin(a - math.pi / 2), math.cos(a - math.pi / 2)))
    return .835 - (.835 - VZ) * max(0.0, 1 - da / .78) ** 1.15
def soff(z): return .014 + .032 * (1 - ss(ZH, .53, z)) + .012 * ss(.77, .84, z)

SHD = {1: V((.30, 0, .74)), -1: V((-.30, 0, .74))}
ELB = {1: V((.385, .0, .52)), -1: V((-.385, .0, .52))}
WR_R = V((.43, .17, .475)); GRIP = V((.43, .255, .47)); GR = .026          # megaphone pistol grip in the right fist
WR_L = V((-.42, .15, .47)); PALM_L = V((-.42, .25, .475)); BB = V((-.42, .27, .50)); BBR = .075   # desk bell on the left palm
MEG_Y0, MEG_Y1 = .10, .60                                                    # megaphone: throat end and mouth (along +Y)
def meg_r(y): return .042 + (.155 - .042) * ((y - MEG_Y0) / (MEG_Y1 - MEG_Y0)) ** 1.15
MEG_Z = GRIP.z + .095 + meg_r(GRIP.y) - .006; MEG_X = GRIP.x
LEGX = .095

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

def ring(name, pts, r, m, seg=8):
    """Closed tube along a loop (no end caps, so no seam or tab)."""
    P = [V(p) for p in pts]; n = len(P); cen = sum(P, V()) / n; vs = []; fs = []
    for i, p in enumerate(P):
        T = (P[(i + 1) % n] - P[i - 1]).normalized(); N = V((p.x - cen.x, p.y - cen.y, 0)).normalized(); B = N.cross(T).normalized()
        vs += [p + (N * math.cos(2 * math.pi * k / seg) + B * math.sin(2 * math.pi * k / seg)) * r for k in range(seg)]
    for i in range(n):
        j = (i + 1) % n; fs += [(i * seg + k, i * seg + (k + 1) % seg, j * seg + (k + 1) % seg, j * seg + k) for k in range(seg)]
    return fix_normals(mk(name, vs, fs, m))

def slab(name, outline, nrm, th, m):
    """Flat piece with thickness: outline points (world), pushed back along nrm by th. Rounded by the caller's fillet."""
    n = len(outline); top = [V(p) for p in outline]; bot = [p - V(nrm) * th for p in top]
    fs = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))] + [(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)]
    ob = fix_normals(mk(name, top + bot, fs, m))
    ob.data.polygons[0].use_smooth = False; ob.data.polygons[1].use_smooth = False
    return ob

def surf_slab(name, pts2, a0, zf, off, th, m, k=4, r=.008):
    """Outline given as (angle_deg, z) pairs on the torso, at offset off. Normal taken from the outline centre."""
    P = [tsurf(a, z, off) for a, z in pts2]; P = fillet(P + [P[0]], r, k)[:-1]
    c = sum(P, V()) / len(P); nrm = V((c.x / rxz(c.z) ** 2, c.y / ryz(c.z) ** 2, 0)).normalized()
    return slab(name, [p + nrm * .002 for p in P], nrm, th, m)

# ---------------------------------------------------------------- body
def lathe(name, zs, rx, ry, m, seg=28, off=0.0):
    vs = []; fs = []
    for z, a, b in zip(zs, rx, ry):
        for i in range(seg):
            t = 2 * math.pi * i / seg; vs.append(V(((a + off) * math.cos(t), (b + off) * math.sin(t), z)))
    for j in range(len(zs) - 1):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
    fs.append(tuple(range(seg - 1, -1, -1))); return mk(name, vs, fs, m)

def build_torso():
    lathe('torso', ZS, RXs, RYs, M['shirt'], seg=20)                         # the blouse, seen inside the V
    seg = 96; J = 9; vs = []; fs = []
    for i in range(seg):                                                     # inner closing ring at the hem
        t = 2 * math.pi * i / seg; vs.append(V(((rxz(ZH) + .004) * math.cos(t), (ryz(ZH) + .004) * math.sin(t), ZH)))
    for j in range(J):
        for i in range(seg):
            t = 2 * math.pi * i / seg; zt = ztop(t); z = ZH + (zt - ZH) * j / (J - 1); off = soff(z)
            vs.append(V(((rxz(z) + off) * math.cos(t), (ryz(z) + off) * math.sin(t), z)))
    for i in range(seg):                                                     # inner closing ring at the neckline and lapel edge
        t = 2 * math.pi * i / seg; zt = ztop(t); vs.append(V(((rxz(zt) + .002) * math.cos(t), (ryz(zt) + .002) * math.sin(t), zt)))
    R = J + 2
    for j in range(R - 1):
        for i in range(seg): fs.append((j * seg + i, (j + 1) * seg + i, (j + 1) * seg + (i + 1) % seg, j * seg + (i + 1) % seg))
    fix_normals(mk('blazer', vs, fs, M['maroon']))
    ring('pipe_neck', [tsurf(360 * i / 128, ztop(2 * math.pi * i / 128), soff(ztop(2 * math.pi * i / 128)) * .55 + .004) for i in range(128)][::2], .0085, M['gold'], seg=5)
    ring('pipe_hem', [tsurf(360 * i / 48, ZH + .004, soff(ZH) + .002) for i in range(48)], .009, M['gold'], seg=5)
    # gold buttons below the V, pocket flaps, prefect badge on the wearer's left chest
    for z in (VZ - .035, VZ - .105): ell('button', tsurf(90, z, soff(z) + .006), (.017, .012, .017), M['goldm'], seg=12)
    a = 90 + 40; z = .69; c = tsurf(a, z, soff(z) + .004); rot = Matrix.Rotation(math.radians(a - 90), 3, 'Z')
    sh = [(-.042, .035), (.042, .035), (.042, -.005), (0, -.05), (-.042, -.005)]
    def badge(name, scale, push, m):
        pts = [c + rot @ V((x * scale, push, zz * scale)) for x, zz in sh]; pts = fillet(pts + [pts[0]], .01 * scale, 3)[:-1]
        return slab(name, pts, rot @ V((0, 1, 0)), .012, m)
    badge('badge', 1.0, .004, M['goldm']); badge('badge_in', .72, .009, M['maroon'])
    # blouse collar points and the tie
    for s in (-1, 1):
        surf_slab('collar', [(90 - s * 62, .852), (90 - s * 4, .815), (90 - s * 24, .735)], 0, 0, .026, .012, M['shirt'], r=.012)
    ring('collar_band', [V((.13 * math.cos(2 * math.pi * i / 32), .12 * math.sin(2 * math.pi * i / 32) - .004, .842)) for i in range(32)], .016, M['shirt'], seg=6)
    ell('tie_knot', tsurf(90, .808, .016), (.026, .02, .024), M['dmaroon'], seg=14)
    tz = [(.79, .019), (.70, .03), (.635, .036), (.605, .0)]
    out = [tsurf(90 - math.degrees(w / .2), z, .012) for z, w in tz] + [tsurf(90 + math.degrees(w / .2), z, .012) for z, w in tz[::-1][1:]]
    slab('tie', fillet(out + [out[0]], .006, 3)[:-1], V((0, 1, 0)), .008, M['dmaroon'])
    for z0 in (.74, .675):
        sweep('tie_stripe', [tsurf(90 - 4, z0 + .009, .0215), tsurf(90 + 4, z0 - .009, .0215)], .0055, M['gold'], seg=6)

def build_skirt():
    """A-line pleated skirt: one closed shell (outer pleats, folded hem, inner face)."""
    seg = 90; N = 18
    zo = np.linspace(.46, .25, 10)
    def rad(z): return float(np.interp(z, [.25, .36, .43, .52], [.335, .29, .246, .232]))
    def pl(t, z):
        f = (t * N / (2 * math.pi)) % 1.0; tri = 1 - 4 * abs(f - .5); return .02 * ss(.47, .27, z) * tri
    rows = [(z, 0.0) for z in zo] + [(.25, -.012), (.31, -.012), (.38, -.012), (.45, -.012)]
    vs = []; fs = []; mi = []
    for z, d in rows:
        for i in range(seg):
            t = 2 * math.pi * i / seg; r = rad(z) + pl(t, z) + d; vs.append(V((r * math.cos(t), r * .8 * math.sin(t), z)))
    nr = len(rows)
    for j in range(nr):
        k = (j + 1) % nr
        for i in range(seg):
            fs.append((j * seg + i, k * seg + i, k * seg + (i + 1) % seg, j * seg + (i + 1) % seg)); mi.append(0 if j < len(zo) - 1 else 1)
    fix_normals(mk('skirt', vs, fs, [M['skirt'], M['skirt_in']], mat_idx=mi))

def build_legs():
    for s in (-1, 1):
        x = s * LEGX
        sweep('leg', [(x, .01, .47), (x, .01, .33), (x, 0, .19), (x, 0, .08)], [.08, .068, .056, .047], M['skin'], seg=14)
        sweep('sock', [(x, 0, .235), (x, 0, .06)], [.068, .056], M['sock'], seg=18, round_caps=False)
        tor('sockband', (x, 0, .225), Z, .067, .008, M['maroon'], seg=16, rseg=5)
        ell('shoe', (x, .04, .052), (.078, .135, .055), M['shoe'], seg=13)
        ell('shoe_sole', (x, .045, .018), (.083, .142, .02), M['sole'], seg=12)
        sweep('shoe_strap', bez((x - .074, .035, .055), (x, .045, .125), (x + .074, .035, .055), 9), .011, M['shoe'], seg=6)
        ell('shoe_buckle', (x + s * .07, .036, .07), (.008, .016, .016), M['goldm'], seg=10)

def arm_soup(k, W, name):
    S, E = SHD[k], ELB[k]; C = E.lerp(W, .78)
    so = H.Soup(name); so.sphere(S, .1, seg=20); so.capsule(S, E, .09, .078); so.capsule(E, C, .078, .07); so.sphere(C, .07)
    a, _ = so.remesh(voxel=.009, smooth=5, smooth_factor=.55, target_tris=700); H.set_material(a, M['maroon']); a.name = name; reg(a)
    tor('cuffpipe_' + name[-1], C - (W - E).normalized() * .004, W - E, .07, .007, M['gold'], seg=20, rseg=5)
    sweep('cuff_' + name[-1], [C - (W - E).normalized() * .002, C + (W - E).normalized() * .03], [.06, .058], M['shirt'], seg=20, round_caps=False)
    return C

def build_arm_r():
    C = arm_soup(1, WR_R, 'arm_r')
    sweep('wrist_r', [C, WR_R], [.042, .04], M['skin'], seg=14)
    # fist round the pistol grip: palm behind the grip, four fingers round the outer side to the front, thumb over the inner side
    palm = GRIP + V((0, -.058, 0)); h = H.Soup('hand_r'); h.ellipsoid(palm, (.05, .036, .082)); h.capsule(WR_R, palm + V((0, 0, .03)), .045, .05)
    rho = GR + .017; rf = .0165
    def arc(z, th, rho, ra, rb):
        pts = [V((GRIP.x + rho * math.cos(math.radians(t)), GRIP.y + rho * math.sin(math.radians(t)), z)) for t in th]
        for p0, p1, r0, r1 in zip(pts[:-1], pts[1:], [ra] + [rf] * 5, [rf] * 4 + [rb]): h.capsule(p0, p1, r0, r1, seg=12)
    for kk, dz in enumerate((.06, .02, -.02, -.06)):
        arc(GRIP.z + dz, (-70, -15, 40, 85, 125), rho, rf + .002, rf * (.85 if kk == 3 else .95))
    arc(GRIP.z + .098, (235, 190, 160, 128), GR + .02, .026, .018)
    hd, _ = h.remesh(voxel=.0055, smooth=5, smooth_factor=.5, target_tris=760); H.set_material(hd, M['skin']); hd.name = 'hand_r'; reg(hd)

def build_megaphone():
    """Maroon horn, cream inside, gold mouth rim, white team band, dark mouthpiece and a pistol grip in the right fist."""
    n = 16; seg = 26; ys = np.linspace(MEG_Y0, MEG_Y1, n); th = .01; vs = []; fs = []; mi = []
    rows = [(y, meg_r(y)) for y in ys] + [(MEG_Y1 - .004, meg_r(MEG_Y1) - th), (MEG_Y1 - .05, meg_r(MEG_Y1 - .05) - th), (MEG_Y0 + .14, meg_r(MEG_Y0 + .14) - th)]
    for y, r in rows:
        for i in range(seg):
            t = 2 * math.pi * i / seg; vs.append(V((MEG_X + r * math.cos(t), y, MEG_Z + r * math.sin(t))))
    nr = len(rows)
    for j in range(nr - 1):
        for i in range(seg):
            fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i)); mi.append(0 if j < n - 1 else 1)
    fs.append(tuple(range(seg - 1, -1, -1))); mi.append(0); fs.append(tuple(range((nr - 1) * seg, nr * seg))); mi.append(1)
    fix_normals(mk('mega', vs, fs, [M['maroon'], M['cream']], mat_idx=mi))
    tor('mega_rim', (MEG_X, MEG_Y1 - .002, MEG_Z), (0, 1, 0), meg_r(MEG_Y1) - .002, .014, M['goldm'], seg=32, rseg=6)
    yb = MEG_Y0 + .19; tor('mega_band', (MEG_X, yb, MEG_Z), (0, 1, 0), meg_r(yb) + .002, .011, M['team'], seg=24, rseg=5)
    sweep('mega_mouth', [(MEG_X, MEG_Y0 - .085, MEG_Z), (MEG_X, MEG_Y0 + .02, MEG_Z)], [.036, .04], M['dmaroon'], seg=18)
    sweep('mega_grip', [(GRIP.x, GRIP.y, GRIP.z - .1), (GRIP.x, GRIP.y, MEG_Z - meg_r(GRIP.y) + .01)], [GR, GR + .002], M['ink'], seg=14)
    sweep('mega_trigger', bez((GRIP.x, GRIP.y + .02, GRIP.z + .085), (GRIP.x, GRIP.y + .05, GRIP.z + .07), (GRIP.x, GRIP.y + .045, GRIP.z + .045), 6), .008, M['ink'], seg=6)

def build_arm_l():
    C = arm_soup(-1, WR_L, 'arm_l')
    sweep('wrist_l', [C, WR_L], [.042, .04], M['skin'], seg=14)
    # palm up under the bell, fingers curl up the front of the wooden base, thumb up its outer side
    h = H.Soup('hand_l'); h.ellipsoid(PALM_L, (.058, .07, .026)); h.capsule(WR_L, PALM_L + V((0, -.03, 0)), .042, .045)
    rf = .0165
    for kk, xk in enumerate((-.036, -.012, .012, .036)):
        x = PALM_L.x + xk; r = rf - .002 * (kk == 0)
        pts = [V((x, PALM_L.y + .05, PALM_L.z)), V((x, BB.y + BBR + .006, BB.z - .004)), V((x, BB.y + BBR + .018, BB.z + .014)), V((x, BB.y + BBR + .006, BB.z + .032))]
        for p0, p1, r0, r1 in zip(pts[:-1], pts[1:], (r + .002, r, r), (r, r, r * .85)): h.capsule(p0, p1, r0, r1, seg=12)
    th = [PALM_L + V((-.05, -.01, 0)), V((BB.x - BBR - .014, BB.y - .03, BB.z + .002)), V((BB.x - BBR - .012, BB.y + .005, BB.z + .02)), V((BB.x - BBR - .004, BB.y + .03, BB.z + .034))]
    for p0, p1, r0, r1 in zip(th[:-1], th[1:], (.024, .021, .019), (.021, .019, .016)): h.capsule(p0, p1, r0, r1, seg=12)
    hd, _ = h.remesh(voxel=.0055, smooth=5, smooth_factor=.5, target_tris=760); H.set_material(hd, M['skin']); hd.name = 'hand_l'; reg(hd)
    # desk bell
    sweep('bell_base', [(BB.x, BB.y, BB.z), (BB.x, BB.y, BB.z + .036)], [BBR, BBR - .004], M['wood'], seg=28, round_caps=False)
    tor('bell_base_lip', (BB.x, BB.y, BB.z + .036), Z, BBR - .006, .006, M['wood'], seg=20, rseg=5)
    ell('bell_dome', (BB.x, BB.y, BB.z + .036), (.06, .06, .056), M['goldm'], seg=18)
    sweep('bell_stem', [(BB.x, BB.y, BB.z + .085), (BB.x, BB.y, BB.z + .108)], .008, M['goldm'], seg=8)
    ell('bell_button', (BB.x, BB.y, BB.z + .112), (.017, .017, .011), M['goldm'], seg=12)

def build_neck():
    sweep('neck_col', [(0, -.005, .78), (0, 0, .92)], [.112, .116], M['skin'], seg=20)

def build_body_all():
    build_torso(); build_skirt(); build_legs(); build_arm_r(); build_megaphone(); build_arm_l(); build_neck()

# ---------------------------------------------------------------- head
HOLE = (0.0, -.245, .215, .14)

def jaw(p):                                   # soft round cheeks, small chin
    d = p - HC; t = ss(-.06, -.32, d.z); z = d.z
    if z < -.34: z = -.34 + (z + .34) * .5
    return HC + V((d.x * (1 + .07 * t), d.y * (1 + .06 * t), z))

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

def anorm(q):
    """Smooth normal of the jawed head at the pre-jaw point q (ellipsoid normal through the jaw Jacobian)."""
    d = q - HC; n = V((d.x / HR.x ** 2, d.y / HR.y ** 2, d.z / HR.z ** 2)); e = 1e-4
    cols = [(jaw(q + ax * e) - jaw(q - ax * e)) / (2 * e) for ax in (V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1)))]
    J = Matrix(cols).transposed(); return (J.inverted().transposed() @ n).normalized()

def set_skin_normals(ob, pre, skin_idx):
    """Custom split normals from the analytic head surface on skin faces, so the low-poly head and the mouth patch shade as one smooth shell."""
    me = ob.data; cn = [V(c.vector) for c in me.corner_normals]; out = []
    for poly in me.polygons:
        for li in poly.loop_indices:
            out.append(tuple(anorm(pre[me.loops[li].vertex_index]) if poly.material_index in skin_idx else cn[li]))
    me.normals_split_custom_set(out)

def head_surface():
    Q, keep = _head_grid(); P = [jaw(q) for q in Q]
    used = sorted({i for f in keep for i in f}); remap = {o: n for n, o in enumerate(used)}
    ob = mk('h_head', [P[i] for i in used], [tuple(remap[i] for i in f) for f in keep], M['skin'])
    set_skin_normals(ob, [Q[i] for i in used], {0}); return ob

EXe, EZe = .175, -.025
TAIL = [V(p) for p in ((0, -.40, .24), (0, -.53, .25), (0, -.60, .17), (.005, -.635, .04), (.015, -.625, -.10), (.03, -.59, -.21), (.055, -.585, -.29), (.085, -.615, -.33))]
TAIL_R = [.052, .064, .076, .074, .066, .052, .034, .016]

def build_head():
    head_surface()
    import random; rnd = random.Random(5); so = H.Soup('hair'); n = 260
    def thr(az): return float(np.interp(az, [0, 20, 40, 52, 60, 75, 180], [27, 28, 31, 22, -30, -38, -38]))
    for i in range(n):
        z = 1 - 2 * (i + .5) / n; a = i * 2.39996; r = math.sqrt(1 - z * z); d = V((r * math.cos(a), r * math.sin(a), z))
        az = math.degrees(math.atan2(abs(d.x), d.y)); el = math.degrees(math.asin(d.z))
        if el < thr(az): continue
        so.sphere(HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z)) * (.89 - .02 * ss(.6, .95, d.z)), .115, seg=14)
    def hp(az, el, k=1.0):
        a = math.radians(az); e = math.radians(el)
        return HC + V((math.sin(a) * math.cos(e) * HR.x * k, math.cos(a) * math.cos(e) * HR.y * k, math.sin(e) * HR.z * k))
    for az in np.linspace(-50, 50, 13):                                            # side-swept fringe: tapered locks, lower on the wearer's left
        edge = 25.5 + 4.5 * (az + 50) / 100 + 1.8 * math.cos(math.radians(az) * 9)
        so.capsule(hp(az - 6, edge + 26, .93), hp(az, edge, 1.01), .055, .028, seg=12)
    for s in (-1, 1):                                                              # bob side panels: front edge frames the cheek, ends in a soft curl at the jaw
        for el in np.linspace(18, -34, 9):
            so.capsule(hp(s * 56, el + 6, .96), hp(s * (57 + 2 * ss(10, -30, el)), el, 1.02), .05, .045, seg=12)
        for az in np.linspace(57, 180, 12):
            so.capsule(hp(s * az, -24, .95), hp(s * az, -36 - 8 * ss(110, 160, az), 1.04 - .04 * ss(150, 180, az)), .06, .05, seg=12)
    pts = catmull([HC + p for p in TAIL], 4); rr = np.interp(np.linspace(0, 1, len(pts)), np.linspace(0, 1, len(TAIL_R)), TAIL_R)
    for p0, p1, r0, r1 in zip(pts[:-1], pts[1:], rr[:-1], rr[1:]): so.capsule(p0, p1, float(r0), float(r1), seg=14)
    hair, _ = so.remesh(voxel=.014, smooth=30, smooth_factor=.85, target_tris=2200); H.set_material(hair, M['hair']); hair.name = 'h_hair'; reg(hair)
    tor('h_scrunchie', HC + TAIL[1] + V((0, -.004, .002)), TAIL[2] - TAIL[0], .074, .026, M['maroon'], seg=20, rseg=6)
    for s in (-1, 1):
        ell('h_ear', HC + V((s * .455, -.03, -.05)), (.035, .062, .08), M['skin'], seg=14)
    p, n_, t, u = surf(0, -.1); ell('h_nose', p + n_ * .002, (.045, .036, .036), M['nose'], seg=20)
    # round glasses: dark rims, clear lenses, gold hinges
    RR = .118; cs = {}
    for s in (-1, 1):
        p, n_, t, u = surf(s * EXe, EZe); ng = V((s * .16, 1, -.03)).normalized(); c = p + n_ * .058
        tg = ng.cross(Z).normalized(); cs[s] = (c, tg, ng)
        tor('h_rim', c, ng, RR, .0125, M['rim'], seg=30, rseg=5)
        vs = [c] + [c + (tg * math.cos(a) + tg.cross(ng) * math.sin(a)) * RR for a in [2 * math.pi * i / 36 for i in range(36)]]
        mk('h_lens', vs, [(0, 1 + i, 1 + (i + 1) % 36) for i in range(36)], M['lens']).visible_shadow = False
        outer = c + tg * (s * (RR + .004))
        ell('h_hinge', outer, (.014, .013, .014), M['goldm'], seg=10)
        sweep('h_temple', fillet([outer, HC + V((s * .45, .22, -.005)), HC + V((s * .47, -.02, -.01))], .1), .009, M['rim'], seg=6)
    a = cs[-1][0] + cs[-1][1] * RR; b = cs[1][0] - cs[1][1] * RR
    sweep('h_bridge', bez(a + Z * .02, (a + b) * .5 + V((0, .02, .045)), b + Z * .02, 8), .0105, M['rim'], seg=8)

# ---------------------------------------------------------------- face (one mesh, six shape keys)
FM = ['skin', 'brow', 'eye', 'white', 'line', 'mouth', 'lip', 'teeth', 'tongue', 'blush']
_I = dict(bz=.155, tilt=.012, arch=.012, eye='bead', es=(1.0, .98), cut=(.034, 0), hl=.008, w=.15, curve=.024, up=0, dn=0, teeth=0, tongue=0, cz=-.235, arc=.058)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'eye': 'arc', 'arc': -.022, 'bz': .16},
    'mouth_open': {**_I, 'w': .17, 'curve': .012, 'up': .006, 'dn': .08, 'teeth': .03, 'tongue': .045},
    'smile': {**_I, 'w': .22, 'curve': .05, 'bz': .175, 'tilt': -.01, 'cut': (.05, 0)},
    'angry': dict(bz=.11, tilt=.09, arch=-.006, eye='bead', es=(1.1, .92), cut=(.008, .62), hl=.0, w=.18, curve=-.056, up=.016, dn=.05, teeth=.03, tongue=0, cz=-.24, arc=.058),
    'grin': dict(bz=.185, tilt=-.014, arch=.03, eye='arc', es=(1, 1), cut=None, hl=.026, w=.29, curve=.06, up=.004, dn=.08, teeth=.03, tongue=.045, cz=-.25, arc=.062),
    'ult': dict(bz=.12, tilt=.085, arch=-.004, eye='bead', es=(1.1, 1.0), cut=(.02, .5), hl=.004, w=.25, curve=-.01, up=.05, dn=.1, teeth=.032, tongue=.065, cz=-.25, arc=.058),
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
        stroke([(s * (EXe + q * .085), e['bz'] + EZe + q * e['tilt'] + e['arch'] * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .04, .024, .006, 'brow')
        bead = e['eye'] == 'bead'; a, c = .064 * e['es'][0], .08 * e['es'][1]
        blob(s * EXe, EZe, (a, .036, c), 0, 'eye', show=bead, seg=16, cut=(e['cut'][0], e['cut'][1] * s) if e['cut'] else None)
        blob(s * EXe, EZe, (.013, .01, .013), .028, 'white', show=bead, seg=10, d=(.018, e['hl']))
        blob(s * EXe, EZe, (.005, .005, .005), .026, 'white', show=bead, seg=6, d=(-.022, -.022))
        top = min(c, e['cut'][0] + e['cut'][1] * a * .8) if e['cut'] else c                # lash flick at the outer top corner of each eye
        stroke([(s * (EXe + a * (.55 + .2 * i)), EZe + top * (.75 - .05 * i) + .006 * i * i) for i in range(5)], .009, .008, .006, 'eye', show=bead, seg=6)
        stroke([(s * EXe + .07 * math.cos(ph), EZe - .03 + e['arc'] * 1.05 * math.sin(ph)) for ph in [math.radians(168 - 156 * i / 11) for i in range(12)]], .016, .012, .005, 'eye', show=not bead)
        v = [surf(s * .29, -.165, .0025)[0]]; f = []
        for j in range(1, 4):
            for i in range(14):
                ang = 2 * math.pi * i / 14; v.append(surf(s * .29 + .045 * j / 3 * math.cos(ang), -.165 + .032 * j / 3 * math.sin(ang), .0025 if j < 3 else .0)[0])
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
    return [jaw(q) for q in vs], fs, mi, vs

KEYS = ['blink', 'mouth_open', 'smile', 'angry', 'grin', 'ult']
def build_face():
    vs, fs, mi, pre = face_geo(EXPR['idle'])
    ob = mk('h_face', vs, fs, [M[k] for k in FM], mat_idx=mi); set_skin_normals(ob, pre, {FM.index('skin')}); ob.shape_key_add(name='Basis')
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
    top = max(v.co.z for o in HERO for v in o.data.vertices); gs = HEIGHT / top
    print('TOY_TOP_Z', round(top, 4), 'GS', round(gs, 4)); open(GS_FILE, 'w').write(repr(gs)); globals()['GS'] = gs
    xs = [abs(v.co.x) for o in HERO for v in o.data.vertices]; print('TOY_MAXX', round(max(xs) * gs, 3))
    for o in HERO:
        for v in o.data.vertices: v.co *= gs
        if o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks:
                for v in kb.data: v.co *= gs
    stage()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, KEY + '_build.blend'))

# ---------------------------------------------------------------- rig + weights
def eyepos(s): return surf(s * EXe, EZe)[0]
MEG_TIP = V((MEG_X, MEG_Y1, MEG_Z))
BONES = [
    ('root', (0, 0, 0), (0, 0, .25), None), ('hips', (0, 0, .46), (0, 0, .56), 'root'), ('spine', (0, 0, .56), (0, 0, .66), 'hips'),
    ('chest', (0, 0, .66), (0, 0, .77), 'spine'), ('neck', (0, 0, .78), (0, .01, .88), 'chest'), ('head', (0, .01, .88), (0, .02, 1.72), 'neck'),
    ('eye.l', tuple(eyepos(-1)), tuple(eyepos(-1) + V((0, .06, 0))), 'head'), ('eye.r', tuple(eyepos(1)), tuple(eyepos(1) + V((0, .06, 0))), 'head'),
    ('upperarm.l', tuple(SHD[-1]), tuple(ELB[-1]), 'chest'), ('lowerarm.l', tuple(ELB[-1]), tuple(WR_L), 'upperarm.l'),
    ('hand.l', tuple(WR_L), tuple(PALM_L + V((0, .06, 0))), 'lowerarm.l'), ('handslot.l', tuple(BB), tuple(BB + V((0, 0, .08))), 'hand.l'),
    ('upperarm.r', tuple(SHD[1]), tuple(ELB[1]), 'chest'), ('lowerarm.r', tuple(ELB[1]), tuple(WR_R), 'upperarm.r'),
    ('hand.r', tuple(WR_R), tuple(GRIP + V((0, .03, 0))), 'lowerarm.r'), ('handslot.r', tuple(GRIP), tuple(GRIP + V((0, .1, 0))), 'hand.r'),
    ('upperleg.l', (-LEGX, .02, .48), (-LEGX, .01, .29), 'hips'), ('lowerleg.l', (-LEGX, .01, .29), (-LEGX, 0, .09), 'upperleg.l'),
    ('foot.l', (-LEGX, 0, .09), (-LEGX, .09, .025), 'lowerleg.l'), ('toes.l', (-LEGX, .09, .025), (-LEGX, .19, .02), 'foot.l'),
    ('upperleg.r', (LEGX, .02, .48), (LEGX, .01, .29), 'hips'), ('lowerleg.r', (LEGX, .01, .29), (LEGX, 0, .09), 'upperleg.r'),
    ('foot.r', (LEGX, 0, .09), (LEGX, .09, .025), 'lowerleg.r'), ('toes.r', (LEGX, .09, .025), (LEGX, .19, .02), 'foot.r'),
    ('prop', tuple(MEG_TIP), tuple(MEG_TIP + V((0, .1, 0))), 'handslot.r'),
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

TRUNK = ([(0, 0, .40), (0, 0, .56), (0, 0, .66), (0, 0, .78), (0, 0, .88), (0, 0, 1.0)], ['hips', 'spine', 'chest', 'neck', 'head'], [.05, .05, .04, .04])
def trunk(p): return chain(p, *TRUNK)
def leg(p, s):
    x = s * LEGX; sd = 'l' if s < 0 else 'r'
    return chain(p, [(x, 0, .60), (x, .01, .29), (x, 0, .09), (x, .09, .025)], ['upperleg.' + sd, 'lowerleg.' + sd, 'foot.' + sd], [.05, .035])
def scale(w, f): return {k: v * f for k, v in w.items()}
def merge(*ws):
    o = {}
    for w in ws:
        for k, v in w.items(): o[k] = o.get(k, 0) + v
    return o

def weights_for(name, p):
    n = name.split('.')[0]; s = -1 if p.x < 0 else 1
    if n.startswith('h_'): return {'head': 1.0}
    if n.startswith('mega'): return {'handslot.r': 1.0}
    if n.startswith('bell'): return {'handslot.l': 1.0}
    if n.startswith('hand_'): return {'hand.' + n[-1]: 1.0}
    if n.startswith(('arm_', 'cuff', 'wrist_')):
        sd = n[-1]; k = 1 if sd == 'r' else -1; S, E = SHD[k], ELB[k]; W = WR_R if k == 1 else WR_L; tip = GRIP if k == 1 else PALM_L
        w = chain(p, [S, E, W, tip], ['upperarm.' + sd, 'lowerarm.' + sd, 'hand.' + sd], [.07, .04])
        wc = 1 - ss(-.06, .14, (p - S).dot((E - S).normalized()))
        return merge(scale(w, 1 - wc), {'chest': wc})
    if n in ('torso', 'blazer') or n.startswith(('pipe', 'neck', 'collar', 'tie', 'badge', 'button')): return trunk(p)
    if n == 'skirt':
        u = .2 * ss(.49, .30, p.z) * ss(.0, .12, abs(p.x)); return merge(scale(leg(p, s), u), scale(trunk(p), 1 - u))
    if n.startswith(('leg', 'sock', 'shoe')):
        w = leg(p, s)
        if n.startswith('shoe'):
            sd = 'l' if s < 0 else 'r'; t = ss(.08, .15, p.y); wf = w.pop('foot.' + sd, 0.0); w['foot.' + sd] = wf * (1 - t); w['toes.' + sd] = wf * t
        h = ss(.40, .48, p.z) if n == 'leg' else 0.0
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
        weak = 0
        for v in ob.data.vertices:
            if sum(g.weight for g in v.groups) < .5: weak += 1
        print('[rig] weak vertices', ob.name, weak)
    for b in rig.data.bones: b.use_deform = b.name not in RIGID
    print('[rig] shape keys', [k.name for k in head.data.shape_keys.key_blocks], 'tris', H.tri_count(head), H.tri_count(body))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, KEY + '_rig.blend'))

# ---------------------------------------------------------------- animation (OG.Pose / OG.make_action reused, own poses)
AX, AY, AZ = OG.X, OG.Y, OG.Z
R = OG.axis_rot
def deb_pose(rig, t, kind):
    P = OG.Pose(rig); s = math.sin(2 * math.pi * t); c = math.cos(2 * math.pi * t)
    if kind == 'idle':      # prim and upright: breathe, a small head tilt, megaphone and bell bob a little
        P.rot('chest', R(AX, 2 * s) @ R(AZ, 1.5 * c)); P.rot('head', R(AX, -1.5 * s) @ R(AY, 4 * c))
        P.rot('upperarm.r', R(AX, 2.5 * s)); P.rot('upperarm.l', R(AX, -2 * s)); P.rot('lowerarm.l', R(AX, 2 * s))
        OG.hips_lift(rig, .006 * s)
    elif kind == 'run':     # quick prefect trot: bell held steady, megaphone arm pumps
        for k, sg in ((-1, 1), (1, -1)):
            sd = 'l' if k < 0 else 'r'
            P.rot('upperleg.' + sd, R(AX, 30 * s * sg)); P.rot('lowerleg.' + sd, R(AX, -60 * max(0.0, -s * sg))); P.rot('foot.' + sd, R(AX, 15 * max(0.0, -s * sg)))
        P.rot('spine', R(AX, 6)); P.rot('chest', R(AX, 6) @ R(AZ, 5 * s)); P.rot('head', R(AX, -7) @ R(AZ, -4 * s))
        P.rot('upperarm.r', R(AX, -22 * s)); P.rot('lowerarm.r', R(AX, 10 + 8 * s))
        P.rot('upperarm.l', R(AX, 6 + 4 * s)); P.rot('lowerarm.l', R(AX, 4 * c))
        OG.hips_lift(rig, .03 * abs(s) - .012)
    elif kind == 'attack':  # Strong Words: lift the megaphone, lean back, shout forward, recover
        if t < .35: u = ss(0, .35, t); lift = 55 * u; lean = -8 * u
        elif t < .55: u = ss(.35, .55, t); lift = 55 - 10 * u; lean = -8 + 22 * u
        else: u = ss(.55, 1.0, t); lift = 45 * (1 - u); lean = 14 * (1 - u)
        P.rot('spine', R(AX, lean * .4)); P.rot('chest', R(AX, lean * .8) @ R(AZ, -lift * .15)); P.rot('head', R(AX, -lean * .5))
        P.rot('upperarm.r', R(AX, lift) @ R(AY, -lift * .3)); P.rot('lowerarm.r', R(AX, -lift * .55))
        P.rot('upperarm.l', R(AX, -lift * .2)); P.rot('lowerarm.l', R(AX, lift * .1))
        OG.hips_lift(rig, -.02 * ss(.35, .55, t) * (1 - ss(.55, 1, t)))
    elif kind == 'ult':     # Detention!: chest out, arms flung wide, megaphone and bell held high
        P.rot('spine', R(AX, -3)); P.rot('chest', R(AX, -7)); P.rot('head', R(AX, -6))
        for k in (-1, 1):
            sd = 'l' if k < 0 else 'r'
            P.aim('upperarm.' + sd, (k * .95, .12, .28)); P.aim('lowerarm.' + sd, (k * .75, .35, .55)); P.aim('hand.' + sd, (k * .4, .85, .35))
    return P
OG.pose_frame = deb_pose

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

# ---------------------------------------------------------------- shots (gym's stage and cameras, framed for a 1.69 m hero)
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
    only = [a for a in ARGS if a in ('beauty', 'turn', 'expr', 'sheet', 'hands')]
    want = lambda k: not only or k in only
    k = HEIGHT / 2.05; hz = HC.z * GS
    play(rig, 'idle', 0); set_key(head, 'none')
    if want('beauty'): shoot(cam, os.path.join(SHOTS, 'beauty.png'), 1600, 1600, 32, 8, (0, .2 * k, .9 * k), 2.3 * k, cam_z=.85 * k)
    if 'hands' in only:
        for nm, W in (('r', GRIP), ('l', BB)): shoot(cam, os.path.join(WORK, 'hand_%s.png' % nm), 700, 700, 0, 7, W * GS, .5)
        set_key(head, 'none'); shoot(cam, os.path.join(WORK, 'face.png'), 800, 800, 0, 7, (0, 0, hz - .05), .9)
        shoot(cam, os.path.join(WORK, 'neck.png'), 800, 800, 20, 7, (0, 0, .78 * GS), .7)
    if want('turn'):
        ps = []
        for i, ang in enumerate((0, 90, 180)):
            rig.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
            t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((0, .12 * k, .9 * k)); p = os.path.join(WORK, 't_%d.png' % i); ps.append(p)
            shoot(cam, p, 534, 800, 0, 9, t, 1.75 * k)
        rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(SHOTS, 'turnaround.png'))
    if want('expr'):
        ps = []
        for name in ('smile', 'angry', 'grin', 'ult'):
            set_key(head, name); p = os.path.join(WORK, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, 0, hz - .14), 1.3 * k * 1.08)
        row(ps, os.path.join(SHOTS, 'expressions.png')); set_key(head, 'none')
    if want('sheet'):
        rows = []
        for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
            ps = []
            for i in range(4):
                play(rig, name, min(n, int(i * n / 4)) if name != 'ult' else (0 if i < 2 else 2)); p = os.path.join(WORK, 'a_%s_%d.png' % (name, i)); ps.append(p)
                shoot(cam, p, 400, 440, 25, 8, (0, .15 * k, .92 * k), 2.3 * k, cam_z=.9 * k)
            r = os.path.join(WORK, 'arow_%s.png' % name); row(ps, r); rows.append(r)
        vstack(rows, os.path.join(SHOTS, 'anim_sheet.png'))

STAGES = dict(build=stage_build, rig=stage_rig, anim=stage_anim, export=stage_export, verify=stage_verify, shots=stage_shots)
for a in ARGS:
    if a in STAGES: STAGES[a]()
