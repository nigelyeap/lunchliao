"""Recess Rascal, style `toy` (designer vinyl collectible). Game-ready: rig, skin, 6 shape keys, 4 clips, glb.
Run: blender -b -P rascal.py -- build rig anim export verify shots      (stages run in the order given)
Axes: Z up, hero faces +Y. Built on gym.py: same toy helpers (ahma_toy.py, exec'd), same face, rig, weights and export code.
Identity (ref/chope.html buildRascal + viewmodel, chope-src rascal_blender.py): sun yellow school cap and a huge yellow
backpack with a blue bottle, white school shirt with a pointed collar, pocket badge and name tag, navy shorts with a belt,
white socks and canvas shoes, freckles and a cheek plaster. Paper shuriken in the right hand, mint ruler in the left."""
import bpy, sys, os, math, importlib.util
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HD = os.path.dirname(os.path.abspath(__file__))
RT = os.path.abspath(os.path.join(HD, '..', '..', '..'))
KEY = 'rascal'
WORK = os.path.join(HD, '_tmp_rascal'); SHOTS = os.path.join(RT, 'shots', 'heroes_toy', KEY); OUT_GLB = os.path.join(RT, 'assets', 'heroes', KEY + '.glb')
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
HEIGHT = 1.41
GSF = os.path.join(WORK, 'gs.txt')
GS = float(open(GSF).read()) if os.path.exists(GSF) else 1.0     # final uniform scale, measured in stage_build so the hero is exactly HEIGHT tall

def openb(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, name)); globals()['SC'] = bpy.context.scene

# ---- palette ----------------------------------------------------------------------------------
M.update(
    skin=mat('skin', '#EDB58C', .42, sss=.12), nose=mat('nose', '#E7A27A', .42, sss=.12), blush=mat('blush', '#EE8E86', .5),
    hair=mat('hair', '#1E1713', .78, spec=.2), brow=mat('brow', '#241A16', .45),
    sun=mat('sun', '#EBB800', .55, spec=.25), sun2=mat('sun2', '#CC9A00', .55, spec=.25),
    shirt=mat('shirt', '#F7F7F2', .55), shirt2=mat('shirt2', '#E2E3DA', .55), button=mat('button', '#FFFFFF', .25, coat=.5),
    navy=mat('navy', '#24305E', .55), navy2=mat('navy2', '#18203F', .5), buckle=mat('buckle', '#C9CDD3', .25, metal=1.0),
    badge=mat('badge', '#C8323A', .35, coat=.4), gold=mat('gold2', '#E8C04A', .3, metal=.6),
    sock=mat('sock', '#F8F7F2', .6), shoe=mat('shoe', '#F1EFE8', .5), sole=mat('sole', '#C9CFD6', .45),
    freck=mat('freck', '#B87A55', .5), plaster=mat('plaster', '#F2D2A4', .45), plas2=mat('plas2', '#E6BC86', .5),
    ruler=mat('ruler', '#86DCC4', .12, coat=1.0), tick=mat('tick', '#1F3A4A', .4),
    paper=mat('paper', '#FFF6DA', .55), paper2=mat('paper2', '#7FC4F2', .5),
    bottle=mat('bottle', '#3E95E0', .2, coat=1.0), lid=mat('lid', '#F7F7F2', .3),
    lip=mat('lip', '#D47567', .4, coat=.3), mouth=mat('mouth', '#5E1A28', .45),
)

# ---- proportions (pre-scale units: the hero is about 1.78 tall before GS) ----------------------
HC = V((0, 0, 1.24)); HR = V((0.47, 0.44, 0.45))                      # head centre and radii (globals used by surf())
TR = [(.38, .255, .20), (.44, .275, .215), (.52, .285, .225), (.60, .28, .215), (.66, .27, .20), (.70, .25, .185), (.73, .215, .165),
      (.755, .16, .135), (.775, .12, .108), (.80, .108, .10), (.86, .108, .10)]
_a = np.array(TR); ZS = np.linspace(TR[0][0], TR[-1][0], 22); RXs = np.interp(ZS, _a[:, 0], _a[:, 1]); RYs = np.interp(ZS, _a[:, 0], _a[:, 2])
for _ in range(3):
    RXs[1:-1] = (RXs[:-2] + 2 * RXs[1:-1] + RXs[2:]) / 4; RYs[1:-1] = (RYs[:-2] + 2 * RYs[1:-1] + RYs[2:]) / 4
rxz = lambda z: float(np.interp(z, ZS, RXs)); ryz = lambda z: float(np.interp(z, ZS, RYs))
def tsurf(a_deg, z, off):
    a = math.radians(a_deg); return V(((rxz(z) + off) * math.cos(a), (ryz(z) + off) * math.sin(a), z))
ZH = .455                                      # shirt hem, tucked into the shorts
def ztop(a):                                   # school shirt neckline: low at the front where the collar opens
    return .772 - .03 * ss(.55, 1.0, math.sin(a))
def soff(z): return .012 + .006 * ss(.55, .68, z)

SHD = {1: V((.255, 0, .655)), -1: V((-.255, 0, .655))}
ELB = {1: V((.335, -.02, .46)), -1: V((-.335, -.01, .465))}
CR = V((.375, .15, .60)); NR = V((0, .22, 1)).normalized()            # right fist (paper shuriken), grip axis
CL = V((-.37, .15, .355)); NL = V((-.06, .55, .83)).normalized()      # left fist (ruler), grip axis
RHO_R, RHO_L = .022, .03
LEGX = .125; BAG = V((0, -.36, .58))

def gframe(n, s):
    e1 = V((s, 0, 0)); e1 = (e1 - n * e1.dot(n)).normalized(); return e1, n.cross(e1).normalized()
def gp(C, n, s, th, rho, h):
    e1, e2 = gframe(n, s); a = math.radians(th); return C + (e1 * math.cos(a) + e2 * math.sin(a)) * rho + n * h
def wrist(k):
    C, n = (CR, NR) if k == 1 else (CL, NL); e1, _ = gframe(n, k); return C - n * .07 + e1 * .035

def loop_pts(f, n=64, close=True):
    p = [f(2 * math.pi * i / n) for i in range(n)]
    return p + [p[0]] if close else p

def catmull(P, k=6, closed=False):
    P = [V(p) for p in P]; n = len(P); out = []
    for i in range(n if closed else n - 1):
        if closed: p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        else: p0 = P[i - 1] if i > 0 else P[0]; p1 = P[i]; p2 = P[i + 1]; p3 = P[i + 2] if i + 2 < n else P[-1]
        for s in range(k):
            t = s / k; out.append(.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed: out.append(P[-1])
    return out

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

def slab(name, outline, lift, m):
    """Thin closed plate: outline points sit on a surface, lift(p) gives the matching top point. Fan-triangulated round a centre."""
    import bmesh
    P = [V(p) for p in outline]; n = len(P); c0 = sum(P, V()) / n; c1 = lift(c0)
    T = [lift(p) for p in P]; vs = P + T + [c0, c1]; b0, b1 = 2 * n, 2 * n + 1; fs = []
    for i in range(n):
        j = (i + 1) % n; fs += [(b0, j, i), (b1, n + i, n + j), (i, j, n + j, n + i)]
    ob = mk(name, vs, fs, m); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free(); return ob

def rb(name, c, size, m, bevel=.01, rot=None):
    ob = rbox(name, c, size, m, bevel=bevel, rot=rot); ob.data.transform(ob.matrix_world); ob.matrix_world = Matrix.Identity(4); return ob

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
    lathe('torso', ZS, RXs, RYs, M['skin'], seg=16)
    seg = 72; J = 9; vs = []; fs = []
    for i in range(seg):                                                    # inner closing ring at the hem
        t = 2 * math.pi * i / seg; vs.append(V((rxz(ZH) * math.cos(t), ryz(ZH) * math.sin(t), ZH)))
    for j in range(J):
        for i in range(seg):
            t = 2 * math.pi * i / seg; z = ZH + (ztop(t) - ZH) * j / (J - 1); off = soff(z)
            vs.append(V(((rxz(z) + off) * math.cos(t), (ryz(z) + off) * math.sin(t), z)))
    for i in range(seg):                                                    # inner closing ring at the neckline
        t = 2 * math.pi * i / seg; zt = ztop(t); vs.append(V(((rxz(zt) - .004) * math.cos(t), (ryz(zt) - .004) * math.sin(t), zt)))
    R = J + 2
    for j in range(R - 1):
        for i in range(seg): fs.append((j * seg + i, (j + 1) * seg + i, (j + 1) * seg + (i + 1) % seg, j * seg + (i + 1) % seg))
    mk('shirt', vs, fs, M['shirt'])
    # collar band round the neckline and two pointed collar flaps lying on the chest
    ring('collar_band', [tsurf(360 * i / 48, ztop(2 * math.pi * i / 48) + .006, soff(.77) + .01) for i in range(48)], .014, M['shirt2'], seg=6)
    for s in (1, -1):
        A = lambda a: a if s > 0 else 180 - a
        pts = [(28, .778), (55, .772), (80, .748), (79, .735), (74, .688), (60, .712), (40, .748)]
        ol = catmull([tsurf(A(a), z, soff(z) + .004) for a, z in pts], 3, closed=True)
        slab('collar', ol, lambda p: p + V((p.x, p.y, 0)).normalized() * .014 + V((0, 0, .002)), M['shirt'])
    sweep('placket', [tsurf(90, z, soff(z) + .002) for z in (.74, .66, .58, .50, .462)], .0075, M['shirt2'], seg=6)
    for z in (.50, .575, .65, .72): ell('button', tsurf(90, z, soff(z) + .01), (.012, .006, .012), M['button'], seg=10)
    # pocket with the school badge (his left), navy name tag (his right)
    ol = [tsurf(a, z, soff(z) + .002) for a, z in catmull([(102, .655), (124, .655), (124, .585), (119, .565), (107, .565), (102, .585)], 2, closed=True)]
    slab('pocket', ol, lambda p: p + V((p.x, p.y, 0)).normalized() * .006, M['shirt2'])
    p = tsurf(113, .625, soff(.62) + .01); n = V((p.x, p.y, 0)).normalized()
    ell('badge', p, (.022, .022, .026), M['badge'], rot=n.to_track_quat('Y', 'Z').to_matrix(), seg=12)
    ell('badge', p + n * .006 + V((0, 0, .004)), (.01, .01, .011), M['gold'], rot=n.to_track_quat('Y', 'Z').to_matrix(), seg=10)
    ol = [tsurf(a, z, soff(z) + .002) for a, z in [(58, .672), (76, .672), (76, .645), (58, .645)]]
    slab('tag', ol, lambda p: p + V((p.x, p.y, 0)).normalized() * .007, M['navy'])

def build_legs():
    zs = [.33, .36, .40, .44, .48, .497]; k = [.80, .90, .97, 1.0, 1.0, 1.0]
    lathe('shorts_top', zs, [(rxz(max(z, .38)) + .03) * f for z, f in zip(zs, k)], [(ryz(max(z, .38)) + .03) * f for z, f in zip(zs, k)], M['navy'])
    tor('belt', (0, 0, .49), Z, rxz(.49) + .03, .02, M['navy2'], seg=40, rseg=4, squash=(1, (ryz(.49) + .03) / (rxz(.49) + .03), 1))
    rb('buckle', (0, ryz(.49) + .055, .49), (.07, .02, .045), M['buckle'], bevel=.008)
    for s in (-1, 1):
        x = s * LEGX
        sweep('shortleg', [(x, 0, .43), (x, .005, .36), (x, .01, .295)], [.128, .128, .126], M['navy'], seg=18, lip=(.01, .10))
        tor('shorthem', (x, .01, .298), Z, .126, .009, M['navy2'], seg=20, rseg=4)
        sweep('calf', [(x, .005, .33), (x, .0, .21), (x, 0, .12)], [.066, .062, .054], M['skin'], seg=16)
        sweep('sock', [(x, 0, .165), (x, 0, .07)], [.06, .058], M['sock'], seg=16, round_caps=False)
        tor('sockcuff', (x, 0, .165), Z, .06, .009, M['sock'], seg=20, rseg=4)
        tor('sockstripe', (x, 0, .145), Z, .061, .005, M['navy'], seg=20, rseg=4)
        ell('shoe', (x, .045, .07), (.095, .165, .07), M['shoe'], seg=16)
        ell('shoe_sole', (x, .05, .03), (.104, .178, .032), M['sole'], seg=16)
        ell('shoe_toe', (x, .155, .052), (.072, .065, .045), M['sole'], seg=14)
        ell('shoe_tongue', (x, .02, .128), (.045, .05, .025), M['navy'], seg=12)
        for j, yy in enumerate((.045, .1)):
            zz = .132 - .02 * j
            sweep('shoe_lace', [(x - .04, yy, zz - .004), (x, yy + .004, zz + .006), (x + .04, yy, zz - .004)], .008, M['navy'], seg=4)
        ell('shoe_heel', (x, -.105, .085), (.045, .025, .045), M['navy'], seg=12)

def arm_soup(k):
    S, E = SHD[k], ELB[k]; W = wrist(k); sd = 'r' if k == 1 else 'l'
    so = H.Soup('arm_' + sd); so.sphere(S, .078, seg=16); so.capsule(S, E, .072, .06); so.capsule(E, W, .058, .046); so.sphere(W, .046, seg=14)
    a, _ = so.remesh(voxel=.009, smooth=5, smooth_factor=.55, target_tris=740); H.set_material(a, M['skin']); a.name = 'arm_' + sd; reg(a)
    d = (E - S).normalized()
    sweep('sleeve_' + sd, [S + d * .015, S + d * .08, S + d * .125], [.092, .09, .087], M['shirt'], seg=20, lip=(.012, .07))
    tor('sleevehem_' + sd, S + d * .122, d, .087, .008, M['shirt2'], seg=24, rseg=5)

def fist(k, C, n, rho, name):
    """Chunky fist round a grip axis n at C: palm on the outer side, four fingers wrapping under, thumb over the top."""
    sd = 'r' if k == 1 else 'l'; e1, e2 = gframe(n, k); W = wrist(k)
    R = Matrix((e1, e2, n)).transposed()
    h = H.Soup(name); palm = C + e1 * (rho + .03)
    h.ellipsoid(palm, (.034, .05, .07), rot=R.to_4x4()); h.capsule(W, palm - n * .02, .046, .042)
    rf = .019
    for j, dz in enumerate((.054, .018, -.018, -.052)):
        pts = [gp(C, n, k, th, rho + rf * .9, dz) for th in (25, -25, -75, -125, -165)]
        r = rf - .002 * (j == 3)
        for p0, p1 in zip(pts[:-1], pts[1:]): h.capsule(p0, p1, r + .001, r, seg=12)
    th = [palm + e2 * .03 + n * .03, gp(C, n, k, 70, rho + .022, .072), gp(C, n, k, 120, rho + .02, .078), gp(C, n, k, 160, rho + .016, .074)]
    for p0, p1, r0, r1 in zip(th[:-1], th[1:], (.028, .025, .023), (.025, .023, .02)): h.capsule(p0, p1, r0, r1, seg=12)
    hd, _ = h.remesh(voxel=.0055, smooth=5, smooth_factor=.5, target_tris=740); H.set_material(hd, M['skin']); hd.name = name; reg(hd)

def build_ruler():
    n = NL; e1, e2 = gframe(n, -1); w, t, a, b = .03, .007, -.06, .40
    def box(name, c, hw, ht, h0, h1, m):
        P = [c + e1 * x + e2 * y + n * h for h in (h0, h1) for x, y in ((-hw, -ht), (hw, -ht), (hw, ht), (-hw, ht))]
        fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]; return mk(name, P, fs, m)
    ob = box('ruler', CL, w, t, a, b, M['ruler'])
    bv = ob.modifiers.new('bev', 'BEVEL'); bv.width = .005; bv.segments = 2; H.apply_mod(ob, bv)
    for i in range(14):
        L = .03 if i % 5 == 0 else .016; h = .10 + i * .021
        for sg in (1, -1): box('ruler_tick', CL + e1 * (-w + L / 2 + .002) + e2 * sg * (t + .0008), L / 2, .0009, h, h + .004, M['tick'])

def build_star():
    """Origami paper shuriken pinched in the right fist: two-tone blades, one point tucked in the hand."""
    n = NR; e1, e2 = gframe(n, 1); c = CR + n * .155; tk = .007
    pts = []
    for i in range(8):
        a = math.radians(-90 + 45 * i); r = .10 if i % 2 == 0 else .036
        pts.append(c + (e1 * math.cos(a) + n * math.sin(a)) * r)
    vs = [c + e2 * tk, c - e2 * tk] + [p + e2 * tk for p in pts] + [p - e2 * tk for p in pts]
    fs = []; mi = []
    for i in range(8):
        j = (i + 1) % 8; m = 0 if (i // 1) % 2 == 0 else 1
        fs.append((0, 2 + i, 2 + j)); mi.append(m); fs.append((1, 10 + j, 10 + i)); mi.append(1 - m)
        fs.append((2 + i, 10 + i, 10 + j, 2 + j)); mi.append(0)
    mk('star', vs, fs, [M['paper'], M['paper2']], mat_idx=mi)
    ell('star_dot', c, (.016, .011, .016), M['sun'], rot=Matrix((e1, e2, n)).transposed(), seg=10)

def build_arms():
    for k in (1, -1): arm_soup(k)
    fist(1, CR, NR, RHO_R, 'hand_r'); fist(-1, CL, NL, RHO_L, 'hand_l')
    build_ruler(); build_star()

def build_bag():
    rb('bag', BAG, (.62, .26, .56), M['sun'], bevel=.08)
    rb('bag_pocket', BAG + V((0, -.15, -.07)), (.44, .08, .30), M['navy'], bevel=.035)
    sweep('bag_zip', [BAG + V((-.18, -.19, .075)), BAG + V((0, -.193, .08)), BAG + V((.18, -.19, .075))], .006, M['sun2'], seg=6)
    rb('bag_pull', BAG + V((.12, -.198, .045)), (.022, .01, .05), M['sun'], bevel=.006)
    rb('bag_flap', BAG + V((0, -.02, .255)), (.58, .27, .08), M['sun2'], bevel=.035)
    sweep('bag_handle', [BAG + V((-.08, -.02, .29)), BAG + V((-.06, -.02, .34)), BAG + V((.06, -.02, .34)), BAG + V((.08, -.02, .29))], .016, M['sun2'], seg=8)
    rb('bag_side', BAG + V((.30, -.02, -.12)), (.06, .2, .2), M['sun2'], bevel=.025)
    bx = BAG + V((.33, -.02, -.17))
    sweep('bottle', [bx, bx + V((0, 0, .26))], [.05, .052], M['bottle'], seg=20)
    sweep('bottle_lid', [bx + V((0, 0, .265)), bx + V((0, 0, .31))], [.038, .034], M['lid'], seg=16)
    def rrect(hx, hz, r, y, n=12):                         # rounded rectangle in the bag's xz plane
        out = []
        for cx, cz, a0 in ((hx - r, hz - r, 0), (-hx + r, hz - r, 90), (-hx + r, -hz + r, 180), (hx - r, -hz + r, 270)):
            out += [BAG + V((cx + r * math.cos(math.radians(a0 + 90 * k / n)), 0, cz + r * math.sin(math.radians(a0 + 90 * k / n)))) for k in range(n)]
        return [V((p.x, y, p.z)) for p in out] + [V((out[0].x, y, out[0].z))]
    for y in (-.466, -.254): sweep('bag_trim', rrect(.287, .257, .07, y), .015, M['navy'], seg=5, round_caps=False)
    path = [(.135, -.255, .80), (.16, -.17, .795), (.172, -.07, .785), (.18, .05, .765), (.195, .14, .70), (.225, .16, .635),
            tsurf(30, .62, .03), tsurf(0, .605, .028), tsurf(-40, .565, .03), (.235, -.225, .41), (.25, -.25, .345)]
    pts = catmull(path, 3)
    for sg in (1, -1): ribbon('strap', [V((sg * p.x, p.y, p.z)) for p in pts], .054, .015, M['sun'])

def ribbon(name, pts, w, t, m):
    """Flat padded strap: a rounded-rect section swept along pts, lying flat on the body."""
    import bmesh
    prof = [(-.5, 0), (-.46, .4), (-.32, .5), (.32, .5), (.46, .4), (.5, 0), (.46, -.4), (.32, -.5), (-.32, -.5), (-.46, -.4)]; n = len(pts); vs = []; fs = []
    for i, p in enumerate(pts):
        T = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized(); N = p - V((0, 0, min(p.z, .62)))
        N = (N - T * N.dot(T)).normalized(); B = T.cross(N)
        vs += [p + B * (u * w) + N * (v * t) for u, v in prof]
    k = len(prof)
    for i in range(n - 1): fs += [(i * k + j, i * k + (j + 1) % k, (i + 1) * k + (j + 1) % k, (i + 1) * k + j) for j in range(k)]
    fs += [tuple(range(k)), tuple((n - 1) * k + j for j in range(k))]
    ob = mk(name, vs, fs, m); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free(); return ob

def build_neck():
    ell('neck_col', (0, 0, .81), (.118, .108, .1), M['skin'], seg=18)

def build_body_all():
    build_torso(); build_legs(); build_arms(); build_bag(); build_neck()

# ---------------------------------------------------------------- head
HOLE = (0.0, -.235, 0, 0)

def jaw(p):                                   # chubby kid cheeks: the lower head widens a little and the chin rounds off
    d = p - HC; t = ss(-.04, -.28, d.z); z = d.z
    if z < -.30: z = -.30 + (z + .30) * .5
    return HC + V((d.x * (1 + .10 * t), d.y * (1 + .05 * t), z))

HOLE_AB = (.17, .115)

def _head_grid():
    vs, fs = sph_vf(60, 28); Q = [HC + V((v.x * HR.x, v.y * HR.y, v.z * HR.z)) for v in vs]
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

def hp(ang, el, off, zk=1.0):
    """Head point by azimuth from the front (deg, + toward his right) and elevation (deg)."""
    a, e = math.radians(ang), math.radians(el); d = V((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    return HC + V((d.x * (HR.x + off), d.y * (HR.y + off), d.z * (HR.z + off) * zk))
def el_rim(ang): return 21 + 15 * math.cos(math.radians(ang))
CAP_OFF = .052

def build_cap():
    seg = 56; J = 9; vs = []; fs = []
    for i in range(seg):                                   # inner closing ring tucked under the rim
        ang = 360 * i / seg; vs.append(hp(ang, el_rim(ang) - 1.5, .012))
    for j in range(J):
        for i in range(seg):
            ang = 360 * i / seg; e0 = el_rim(ang); el = e0 + (88 - e0) * (j / (J - 1)) ** 1.15
            vs.append(hp(ang, el, CAP_OFF, 1.05) if j else hp(ang, el - 1.5, CAP_OFF - .006))
    top = len(vs); vs.append(hp(0, 90, CAP_OFF, 1.05))
    for j in range(J):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
    for i in range(seg): fs.append((J * seg + i, J * seg + (i + 1) % seg, top))
    import bmesh
    ob = mk('h_cap', vs, fs, M['sun']); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    ring('h_caprim', [hp(360 * i / 48, el_rim(360 * i / 48) - .5, CAP_OFF - .002) for i in range(48)], .011, M['sun'], seg=6)
    for k in range(6):                                     # panel seams and the top button
        ang = 30 + 60 * k
        sweep('h_capseam', [hp(ang, el_rim(ang) + 2 + (86 - el_rim(ang)) * q / 7, CAP_OFF + .004, 1.05) for q in range(6)], .0045, M['sun2'], seg=4)
    ell('h_capbtn', hp(0, 90, CAP_OFF + .008, 1.05), (.034, .034, .02), M['sun'], seg=14)
    for s in (-1, 1): ell('h_capeye', hp(s * 62, 52, CAP_OFF + .002, 1.05), (.012, .012, .012), M['sun2'], seg=8)
    # brim: a curved slab out the front, tipped up a touch
    NU, NV = 36, 4; T = []; B = []
    for i in range(NU + 1):
        ang = -58 + 116 * i / NU; root = hp(ang, el_rim(ang) + 1.5, CAP_OFF - .02)
        f = math.cos(math.radians(ang) * 90 / 58) ** .55; Ln = .03 + .21 * f
        out = V((math.sin(math.radians(ang)), math.cos(math.radians(ang)), 0))
        for j in range(NV + 1):
            v = j / NV; p = root + out * Ln * v + V((0, 0, .02 * v - .025 * v * v * f)); T.append(p + V((0, 0, .011))); B.append(p - V((0, 0, .011)))
    vs = T + B; nb = len(T); fs = []; W = NV + 1
    for i in range(NU):
        for j in range(NV):
            a_, b_, c_, d_ = i * W + j, (i + 1) * W + j, (i + 1) * W + j + 1, i * W + j + 1
            fs.append((a_, d_, c_, b_)); fs.append((nb + a_, nb + b_, nb + c_, nb + d_))
    for i in range(NU):                                     # outer edge, inner edge
        a_, b_ = i * W + NV, (i + 1) * W + NV; fs.append((a_, b_, nb + b_, nb + a_))
        a_, b_ = i * W, (i + 1) * W; fs.append((a_, nb + a_, nb + b_, b_))
    for i in (0, NU):
        for j in range(NV):
            a_, b_ = i * W + j, i * W + j + 1; fs.append((a_, b_, nb + b_, nb + a_))
    ob = mk('h_brim', vs, fs, M['sun']); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()

def build_hair():
    """Smooth toy hair: one shell hugging the skull under the cap, soft clumps at the back, a rounded nape lip."""
    import bmesh
    thr = lambda ang: float(np.interp(abs(ang), [0, 42, 58, 75, 95, 115, 140, 180], [99, 99, 26, 14, 10, -8, -34, -50]))
    seg = 72; J = 8; vs = []; fs = []
    for j in range(J):
        for i in range(seg):
            ang = 360 * i / seg - 180; eb = min(thr(ang), el_rim(ang) - 2); et = el_rim(ang) + 9
            lobe = (.5 + .5 * math.cos(math.radians(ang) * 6)) * ss(35, 80, abs(ang))
            if j == 0: el, off = eb, -.004
            elif j == 1: el, off = eb + 1.4, .018
            elif j == 2: el, off = eb + 3.8, .03
            else:
                t = (j - 3) / (J - 4); el = eb + 7 + (et - eb - 7) * t
                off = .033 + .02 * lobe * math.sin(math.pi * min(1, t * 1.6 + .25)) * (1 - t * .6) - .006 * t
            if j == 2: off += .008 * lobe
            vs.append(jaw(hp(ang, el, off)))
    for j in range(J - 1):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
    ob = mk('h_hair', vs, fs, M['hair']); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    so = H.Soup('fringe')                                   # one fringe piece: a base band with five soft points fused into it
    for a0 in range(-46, 46, 11): so.capsule(hp(a0, el_rim(a0) - 4, .014), hp(a0 + 11, el_rim(a0 + 11) - 4, .014), .046, .046, seg=10)
    for ang, dr in ((-34, -10), (-17, -5), (0, 1), (17, 6), (34, 10)):      # chunky rounded tufts, down and out
        e0 = el_rim(ang); a_ = hp(ang, e0 - 3, .02); b_ = hp(ang + dr, e0 - 12, .03); z = (b_ - a_).normalized()
        y = (a_ - HC).normalized(); y = (y - z * y.dot(z)).normalized(); x = y.cross(z)
        so.ellipsoid((a_ + b_) * .5, (.058, .034, .07), rot=Matrix((x, y, z)).transposed().to_4x4(), seg=14)
    fr, _ = so.remesh(voxel=.009, smooth=12, smooth_factor=.6, target_tris=600); H.set_material(fr, M['hair']); fr.name = 'h_fringe'; reg(fr)

def build_head():
    head_surface(); build_cap()
    build_hair()
    for s in (-1, 1):
        ell('h_ear', HC + V((s * .455, -.02, -.04)), (.05, .08, .1), M['skin'], seg=14)
        ell('h_bud', HC + V((s * .49, -.0, -.04)), (.018, .045, .06), M['nose'], seg=12)
    p, n_, t, u = surf(0, -.1); ell('h_nose', p + n_ * .002, (.048, .04, .04), M['nose'], seg=18)
    for s, fr in ((-1, ((.22, -.115), (.255, -.128), (.29, -.112), (.24, -.142))), (1, ((.22, -.115), (.25, -.132)))):
        for fx, fz in fr:
            p, n_, t, u = surf(s * fx, fz); ell('h_freck', p, (.01, .004, .009), M['freck'], rot=Matrix((t, n_, u)).transposed(), seg=8)
    p, n_, t, u = surf(.315, -.06); R = Matrix((t, n_, u)).transposed() @ Matrix.Rotation(math.radians(32), 3, 'Y')    # cheek plaster, his right
    ell('h_plaster', p + n_ * .002, (.06, .009, .024), M['plaster'], rot=R, seg=14)
    ell('h_plaspad', p + n_ * .008, (.02, .006, .016), M['plas2'], rot=R, seg=10)

# ---------------------------------------------------------------- face (one mesh, six shape keys)
FM = ['skin', 'brow', 'eye', 'white', 'line', 'mouth', 'lip', 'teeth', 'tongue', 'blush']
EXe, EZe = .17, -.03
_I = dict(bz=.155, tilt=-.01, arch=.012, eye='bead', es=(1, 1), cut=(.055, 0), hl=.01, w=.17, curve=.028, up=0, dn=0, teeth=0, tongue=0, cz=-.225, arc=.062)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'eye': 'arc', 'arc': -.024, 'bz': .16},
    'mouth_open': {**_I, 'w': .19, 'curve': .012, 'up': .006, 'dn': .08, 'teeth': .03, 'tongue': .045},
    'smile': {**_I, 'w': .23, 'curve': .05, 'bz': .175, 'tilt': -.015},
    'angry': dict(bz=.05, tilt=.095, arch=-.006, eye='bead', es=(1.05, .9), cut=(.008, .65), hl=.0, w=.19, curve=-.055, up=.018, dn=.05, teeth=.03, tongue=0, cz=-.235, arc=.06),
    'grin': dict(bz=.2, tilt=-.016, arch=.034, eye='arc', es=(1, 1), cut=None, hl=.026, w=.29, curve=.062, up=.004, dn=.08, teeth=.03, tongue=.05, cz=-.24, arc=.066),
    'ult': dict(bz=.085, tilt=.07, arch=.0, eye='bead', es=(1.05, .92), cut=(.02, .35), hl=.008, w=.25, curve=.004, up=.04, dn=.088, teeth=.03, tongue=.065, cz=-.24, arc=.06),
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
        stroke([(s * (EXe + q * .095), e['bz'] + EZe + q * e['tilt'] + e['arch'] * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .05, .028, .006, 'brow')
        bead = e['eye'] == 'bead'; a, c = .066 * e['es'][0], .082 * e['es'][1]
        blob(s * EXe, EZe, (a, .038, c), 0, 'eye', show=bead, seg=16, cut=(e['cut'][0], e['cut'][1] * s) if e['cut'] else None)
        blob(s * EXe, EZe, (.014, .01, .014), .03, 'white', show=bead, seg=10, d=(.018, e['hl'] + .012))
        blob(s * EXe, EZe, (.006, .005, .006), .028, 'white', show=bead, seg=6, d=(-.022, -.025))
        stroke([(s * EXe + .07 * math.cos(ph), EZe - .03 + e['arc'] * 1.05 * math.sin(ph)) for ph in [math.radians(168 - 156 * i / 11) for i in range(12)]], .016, .012, .005, 'eye', show=not bead)
        v = [surf(s * .3, -.165, .0025)[0]]; f = []
        for j in range(1, 4):
            for i in range(14):
                ang = 2 * math.pi * i / 14; v.append(surf(s * .3 + .045 * j / 3 * math.cos(ang), -.165 + .032 * j / 3 * math.sin(ang), .0025 if j < 3 else .0)[0])
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
        lipo = (ox + .013 * math.cos(th), oz + .015 * math.sin(th))
        sc = lambda t: (cen[0] + (ox - cen[0]) * t, cen[1] + (oz - cen[1]) * t)
        rings.append([q0.copy(), surf(*lerpp(outer, lipo, .3), 0)[0], surf(*lerpp(outer, lipo, .6), .0006)[0], surf(*lerpp(outer, lipo, .85), .0025)[0], surf(*lipo, .0055)[0],
                      surf(*lerpp(lipo, (ox, oz), .5), .011)[0], surf(ox, oz, .0055)[0],
                      surf(ox, oz, -.012)[0], surf(*sc(.88), -.04)[0], surf(*sc(.62), -.068)[0], surf(*sc(.28), -.088)[0]])
    NTH = len(LOOP); nr = len(rings[0]); v = [rings[k][r] for r in range(nr) for k in range(NTH)] + [surf(cen[0], cen[1], -.092)[0]]
    f = []; fm = []; mats = ['skin', 'skin', 'skin', 'skin', 'lip', 'lip', 'mouth', 'mouth', 'mouth', 'mouth']
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
    # weld the face onto the head along the mouth-hole seam so the skin shades as one surface (no visible patch)
    import bmesh
    hd = bpy.data.objects['h_head']; HERO.remove(hd); ob = H.join([ob, hd], 'h_face')
    seam = [jaw(q) for q in LOOP]
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    sv = [v for v in bm.verts if min((v.co - q).length for q in seam) < 1e-5]
    bmesh.ops.remove_doubles(bm, verts=sv, dist=1e-5); bm.to_mesh(ob.data); bm.free()
    print('[face] seam verts welded', len(sv), '->', len(sv) // 2)
    return ob

# ---------------------------------------------------------------- build stage
def stage_build():
    build_body_all(); build_head(); build_face()
    tris = sum(H.tri_count(o) for o in HERO); print('TOY_TRIS', tris, 'objects', len(HERO))
    agg = {}
    for o in HERO: agg[o.name.split('.')[0]] = agg.get(o.name.split('.')[0], 0) + H.tri_count(o)
    print('TOY_TOP', sorted(agg.items(), key=lambda kv: -kv[1])[:40])
    for o in HERO: o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    zmin = min(v.co.z for o in HERO for v in o.data.vertices); zmax = max(v.co.z for o in HERO for v in o.data.vertices)
    xs = [abs(v.co.x) for o in HERO for v in o.data.vertices]
    gs = HEIGHT / (zmax - min(0.0, zmin)); globals()['GS'] = gs; open(GSF, 'w').write('%.6f' % gs)
    print('[build] raw height %.3f zmin %.4f -> GS %.4f, |x| max %.3f' % (zmax - zmin, zmin, gs, max(xs) * gs))
    for o in HERO:
        for v in o.data.vertices: v.co *= GS
        if o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks:
                for v in kb.data: v.co *= GS
    stage()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'rascal_build.blend'))

# ---------------------------------------------------------------- rig + weights
def eyepos(s): return surf(s * EXe, EZe)[0]
BONES = [
    ('root', (0, 0, 0), (0, 0, .2), None), ('hips', (0, 0, .42), (0, 0, .52), 'root'), ('spine', (0, 0, .52), (0, 0, .62), 'hips'),
    ('chest', (0, 0, .62), (0, 0, .76), 'spine'), ('neck', (0, 0, .76), (0, .01, .86), 'chest'), ('head', (0, .01, .86), (0, .02, 1.66), 'neck'),
    ('eye.l', tuple(eyepos(-1)), tuple(eyepos(-1) + V((0, .06, 0))), 'head'), ('eye.r', tuple(eyepos(1)), tuple(eyepos(1) + V((0, .06, 0))), 'head'),
    ('upperarm.l', tuple(SHD[-1]), tuple(ELB[-1]), 'chest'), ('lowerarm.l', tuple(ELB[-1]), tuple(wrist(-1)), 'upperarm.l'),
    ('hand.l', tuple(wrist(-1)), tuple(CL), 'lowerarm.l'), ('handslot.l', tuple(CL), tuple(CL + NL * .08), 'hand.l'),
    ('upperarm.r', tuple(SHD[1]), tuple(ELB[1]), 'chest'), ('lowerarm.r', tuple(ELB[1]), tuple(wrist(1)), 'upperarm.r'),
    ('hand.r', tuple(wrist(1)), tuple(CR), 'lowerarm.r'), ('handslot.r', tuple(CR), tuple(CR + NR * .08), 'hand.r'),
    ('upperleg.l', (-LEGX, .02, .46), (-LEGX, .01, .27), 'hips'), ('lowerleg.l', (-LEGX, .01, .27), (-LEGX, 0, .09), 'upperleg.l'),
    ('foot.l', (-LEGX, 0, .09), (-LEGX, .10, .03), 'lowerleg.l'), ('toes.l', (-LEGX, .10, .03), (-LEGX, .21, .02), 'foot.l'),
    ('upperleg.r', (LEGX, .02, .46), (LEGX, .01, .27), 'hips'), ('lowerleg.r', (LEGX, .01, .27), (LEGX, 0, .09), 'upperleg.r'),
    ('foot.r', (LEGX, 0, .09), (LEGX, .10, .03), 'lowerleg.r'), ('toes.r', (LEGX, .10, .03), (LEGX, .21, .02), 'foot.r'),
    ('prop', tuple(BAG + V((0, .1, .2))), tuple(BAG + V((0, .1, .45))), 'chest'),
]
RIGID = {'eye.l', 'eye.r'}

def make_rig():
    arm = bpy.data.armatures.new('rascal_rig'); ob = bpy.data.objects.new('rascal_rig', arm); bpy.context.scene.collection.objects.link(ob)
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

TRUNK = ([(0, 0, .36), (0, 0, .52), (0, 0, .62), (0, 0, .76), (0, 0, .86), (0, 0, .95)], ['hips', 'spine', 'chest', 'neck', 'head'], [.05, .04, .035, .035])
def trunk(p): return chain(p, *TRUNK)
def leg(p, s):
    x = s * LEGX; sd = 'l' if s < 0 else 'r'
    return chain(p, [(x, 0, .56), (x, .01, .27), (x, 0, .09), (x, .10, .03)], ['upperleg.' + sd, 'lowerleg.' + sd, 'foot.' + sd], [.05, .035])
def scale(w, f): return {k: v * f for k, v in w.items()}
def merge(*ws):
    o = {}
    for w in ws:
        for k, v in w.items(): o[k] = o.get(k, 0) + v
    return o

def weights_for(name, p):
    n = name.split('.')[0]; s = -1 if p.x < 0 else 1
    if n.startswith('h_'): return {'head': 1.0}
    if n.startswith('star'): return {'handslot.r': 1.0}
    if n.startswith('ruler'): return {'handslot.l': 1.0}
    if n.startswith(('bag', 'bottle')): return {'prop': 1.0}
    if n.startswith('hand_'): return {'hand.' + n[-1]: 1.0}
    if n.startswith(('arm_', 'sleeve')):
        sd = n[-1]; k = 1 if sd == 'r' else -1; S, E = SHD[k], ELB[k]; W = wrist(k); tip = CR if k == 1 else CL
        w = chain(p, [S, E, W, tip], ['upperarm.' + sd, 'lowerarm.' + sd, 'hand.' + sd], [.07, .05])
        wc = 1 - ss(-.05, .1, (p - S).dot((E - S).normalized()))
        return merge(scale(w, 1 - wc), {'chest': wc})
    if n in ('torso', 'shirt', 'placket', 'button', 'pocket', 'badge', 'tag', 'strap') or n.startswith(('collar', 'neck')): return trunk(p)
    if n in ('belt', 'buckle'): return {'hips': 1.0}
    if n == 'shorts_top':
        u = ss(.44, .36, p.z) * ss(.02, .10, abs(p.x)); return merge(scale(leg(p, s), u), scale({'hips': 1.0}, 1 - u))
    if n.startswith(('shortleg', 'shorthem', 'calf', 'sock', 'shoe')):
        w = leg(p, s)
        if n.startswith('shoe'):
            sd = 'l' if s < 0 else 'r'; t = ss(.11, .18, p.y); wf = w.pop('foot.' + sd, 0.0); w['foot.' + sd] = wf * (1 - t); w['toes.' + sd] = wf * t
        h = ss(.42, .49, p.z) if n.startswith(('shortleg', 'shorthem')) else 0.0
        return merge(scale(w, 1 - h), {'hips': h})
    print('[weights] unclassified', name); return {'hips': 1.0}

def stage_rig():
    openb('rascal_build.blend'); O = bpy.data.objects
    parts = [o for o in O if o.type == 'MESH' and o.name != 'cyc']
    for o in parts:
        o.data.update()
        for v in o.data.vertices:
            for b, w in weights_for(o.name, v.co / GS).items():
                if w > 1e-3:
                    g = o.vertex_groups.get(b) or o.vertex_groups.new(name=b); g.add([v.index], w, 'REPLACE')
    heads = [o for o in parts if o.name.startswith('h_')]; heads.sort(key=lambda o: o.name != 'h_face')
    bodies = [o for o in parts if not o.name.startswith('h_')]
    head = H.join(heads, 'rascal_head'); body = H.join(bodies, 'rascal_body'); rig = make_rig()
    for ob in (head, body):
        ob.parent = rig; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = rig
        for v in ob.data.vertices:
            tot = sum(g.weight for g in v.groups)
            if tot < .5: print('[rig] weak vertex', ob.name, v.index, tot)
    for b in rig.data.bones: b.use_deform = b.name not in RIGID
    print('[rig] shape keys', [k.name for k in head.data.shape_keys.key_blocks], 'tris', H.tri_count(head), H.tri_count(body))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'rascal_rig.blend'))

# ---------------------------------------------------------------- animation (OG.Pose / OG.make_action reused, rascal's own poses)
X_, Y_, Z_ = OG.X, OG.Y, OG.Z
ar = OG.axis_rot
def mixd(*ds):
    """Blend directions: mixd(a, (b, u), (c, v)...) lerps a toward b by u, then toward c by v."""
    d = V(ds[0])
    for b, u in ds[1:]: d = d.lerp(V(b), u)
    return d.normalized()
REST = {}
def rest_dirs(rig):
    if not REST:
        for b in ('upperarm.r', 'lowerarm.r', 'upperarm.l', 'lowerarm.l'):
            bb = rig.data.bones[b]; REST[b] = (bb.tail_local - bb.head_local).normalized()
    return REST

def rascal_pose(rig, t, kind):
    P = OG.Pose(rig); s = math.sin(2 * math.pi * t); c = math.cos(2 * math.pi * t); R = rest_dirs(rig)
    if kind == 'idle':      # fidgety kid: bounce, cheeky head tilt, the star waggles, the ruler taps
        P.rot('spine', ar(X_, 1.5 * s)); P.rot('chest', ar(X_, 2 * s) @ ar(Z_, 3 * c)); P.rot('head', ar(Z_, -6 * c) @ ar(Y_, 4 * s))
        P.rot('upperarm.r', ar(X_, 4 * s)); P.rot('lowerarm.r', ar(X_, 7 * s)); P.rot('hand.r', ar(Y_, 10 * c))
        P.rot('upperarm.l', ar(Y_, -3 * s)); P.rot('lowerarm.l', ar(X_, 5 * c))
        P.rot('prop', ar(X_, 2 * s)); OG.hips_lift(rig, .008 * abs(s))
    elif kind == 'run':     # fast little legs, arms out, the backpack bounces
        for k, sg in ((-1, 1), (1, -1)):
            side = 'l' if k < 0 else 'r'
            P.rot('upperleg.' + side, ar(X_, 45 * s * sg)); P.rot('lowerleg.' + side, ar(X_, -70 * max(0.0, -s * sg)))
            P.rot('foot.' + side, ar(X_, 18 * max(0.0, -s * sg)))
        P.rot('spine', ar(X_, 6)); P.rot('chest', ar(X_, 9) @ ar(Z_, 7 * s)); P.rot('head', ar(X_, -10) @ ar(Z_, -5 * s))
        P.rot('upperarm.l', ar(X_, -40 * s) @ ar(Y_, -14)); P.rot('lowerarm.l', ar(X_, 35))
        P.rot('upperarm.r', ar(X_, 40 * s) @ ar(Y_, 14)); P.rot('lowerarm.r', ar(X_, 30))
        P.rot('prop', ar(X_, -10 * abs(s))); OG.hips_lift(rig, .03 * abs(s) - .01)
    elif kind == 'attack':  # Paper Shuriken flick: cock the right arm back and out, whip it forward across, recover
        u = ss(0, .3, t); v = ss(.3, .42, t); w = ss(.5, 1.0, t)
        P.rot('chest', ar(Z_, (-22 * u * (1 - v) + 18 * v) * (1 - w))); P.rot('head', ar(Z_, (14 * u * (1 - v) - 10 * v) * (1 - w)))
        P.aim('upperarm.r', mixd(R['upperarm.r'], ((.85, -.45, .3), u), ((.25, .95, .05), v), (R['upperarm.r'], w)))
        P.aim('lowerarm.r', mixd(R['lowerarm.r'], ((.2, -.3, .93), u), ((-.35, .93, .05), v), (R['lowerarm.r'], w)))
        P.rot('hand.r', ar(X_, (-30 * u + 70 * v) * (1 - w)))
        P.rot('upperarm.l', ar(X_, -20 * v * (1 - w)) @ ar(Y_, -15 * v * (1 - w)))
        OG.hips_lift(rig, -.02 * v * (1 - w))
    elif kind == 'ult':     # PSLE Slash charge: crouched low, ruler cocked up over the shoulder, eyes on the target
        P.rot('spine', ar(X_, 12)); P.rot('chest', ar(X_, 16) @ ar(Z_, -12)); P.rot('head', ar(X_, -22) @ ar(Z_, 10))
        for k in (-1, 1):
            side = 'l' if k < 0 else 'r'
            P.rot('upperleg.' + side, ar(X_, 55) @ ar(Y_, k * -10)); P.rot('lowerleg.' + side, ar(X_, -90)); P.rot('foot.' + side, ar(X_, 35))
        P.aim('upperarm.l', (-.35, .15, .92)); P.aim('lowerarm.l', (-.05, .1, .99)); P.rot('hand.l', ar(X_, -100))
        P.aim('upperarm.r', (.45, .65, -.6)); P.aim('lowerarm.r', (.25, .95, .1))
        P.rot('prop', ar(X_, 8)); OG.hips_lift(rig, -.11)
    return P
OG.pose_frame = rascal_pose

def stage_anim():
    openb('rascal_rig.blend'); SC.render.fps = OG.FPS; rig = bpy.data.objects['rascal_rig']
    acts = [OG.make_action(rig, 'idle', 'idle', 60), OG.make_action(rig, 'run', 'run', 24), OG.make_action(rig, 'attack', 'attack', 18, loop=False), OG.make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'rascal_anim.blend')); print('[anim] actions', [a.name for a in acts])

def stage_export():
    openb('rascal_anim.blend'); O = bpy.data.objects; rig = O['rascal_rig']; OG.reset_pose(rig)
    for k in O['rascal_head'].data.shape_keys.key_blocks: k.value = 0.0
    H.select_only([O['rascal_head'], O['rascal_body'], rig], rig)
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
    a = np.concatenate(ims[::-1], axis=0); h, w = a.shape[:2]
    o = bpy.data.images.new('v', w, h, alpha=False); o.pixels.foreach_set(a.ravel()); o.filepath_raw = out; o.file_format = 'PNG'; o.save()

def stage_shots():
    openb('rascal_anim.blend'); O = bpy.data.objects; rig = O['rascal_rig']; head = O['rascal_head']; cam = O['cam']
    only = [a for a in ARGS if a in ('beauty', 'turn', 'expr', 'sheet', 'detail')]
    want = lambda k: (not only and k != 'detail') or k in only
    g = GS; play(rig, 'idle', 0); set_key(head, 'none')
    if want('beauty'): shoot(cam, os.path.join(SHOTS, 'beauty.png'), 1600, 1600, 32, 8, (0, .15 * g, .9 * g), 1.75, cam_z=.86 * g)
    if want('detail'):
        for nm, tgt, wd, az in (('face', HC * g + V((0, 0, -.05)), .75, 15), ('hand_r', CR * g + V((0, 0, .05)), .42, 20), ('hand_l', CL * g + V((0, .08, .05)), .5, 20),
                                ('hem', V((0, 0, .3)) * g, .95, 25), ('neck', V((0, .1, .78)) * g, .55, 10), ('back', V((0, 0, .9)) * g, 1.5, 160)):
            shoot(cam, os.path.join(WORK, 'd_%s.png' % nm), 800, 800, az, 7, tgt, wd)
    if want('turn'):
        ps = []
        for i, ang in enumerate((0, 90, 180)):
            rig.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
            t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((0, .08 * g, .9 * g)); p = os.path.join(WORK, 't_%d.png' % i); ps.append(p)
            shoot(cam, p, 534, 800, 0, 9, t, 1.35)
        rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(SHOTS, 'turnaround.png'))
    if want('expr'):
        ps = []
        for name in ('smile', 'angry', 'grin', 'ult'):
            set_key(head, name); p = os.path.join(WORK, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, 0, (HC.z - .02) * g), 1.0)
        row(ps, os.path.join(SHOTS, 'expressions.png')); set_key(head, 'none')
    if want('sheet'):
        rows = []
        for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
            ps = []
            for i in range(4):
                play(rig, name, min(n, int(i * n / 4)) if name != 'ult' else (0 if i < 2 else 2)); p = os.path.join(WORK, 'a_%s_%d.png' % (name, i)); ps.append(p)
                shoot(cam, p, 400, 440, 25, 8, (0, .1 * g, .92 * g), 1.75, cam_z=.92 * g)
            r = os.path.join(WORK, 'arow_%s.png' % name); row(ps, r); rows.append(r)
        vstack(rows, os.path.join(SHOTS, 'anim_sheet.png'))

STAGES = dict(build=stage_build, rig=stage_rig, anim=stage_anim, export=stage_export, verify=stage_verify, shots=stage_shots)
for a in ARGS:
    if a in STAGES: STAGES[a]()
