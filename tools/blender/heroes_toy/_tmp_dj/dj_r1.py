"""Nightclub DJ, style `toy` (designer vinyl collectible). Game-ready: rig, skin, 6 shape keys, 4 clips, glb.
Run: blender -b -P dj.py -- build rig anim export verify shots      (stages run in the order given)
Axes: Z up, hero faces +Y. Built from gym.py (toy quality bar): same helpers, face, rig, weights, anim and export code.
Identity: ref/chope.html HEROES.dj (Support, size .95, body 0xe040c0), buildDj viewmodel (dark sleeves, launchpad with pink and
cyan pads in the right hand, mic in the left) and proto-dj (high dark brown ponytail, big black cans with a pink ring, gold hoops and chain,
wide-leg pants, platform soles). The floating booth stays a game-side effect, it is too wide for the +-0.8 prop box."""
import bpy, sys, os, math, importlib.util
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HD = os.path.dirname(os.path.abspath(__file__))
RT = os.path.abspath(os.path.join(HD, '..', '..', '..'))
WORK = os.path.join(HD, '_tmp_dj'); SHOTS = os.path.join(RT, 'shots', 'heroes_toy', 'dj'); OUT_GLB = os.path.join(RT, 'assets', 'heroes', 'dj.glb')
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
GS = 1.0                                      # final uniform scale, measured in stage_build so the hero is exactly HEIGHT tall
_gs = os.path.join(WORK, 'gs.txt')
if os.path.exists(_gs): GS = float(open(_gs).read())

def openb(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, name)); globals()['SC'] = bpy.context.scene

def glow(m, hexcol, k):
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Emission Color'].default_value = (*H.srgb(hexcol), 1); b.inputs['Emission Strength'].default_value = k
    return m

# ---- palette ----------------------------------------------------------------------------------
PINK = '#FF3FB4'; CYAN = '#33E6FF'; PURP = '#B44CFF'
M.update(
    skin=mat('skin', '#EDB48E', .42, sss=.12), nose=mat('nose', '#E9A27E', .42, sss=.12), blush=mat('blush', '#F08C96', .5),
    hair=mat('hair', '#3A261B', .32, coat=.4), brow=mat('brow', '#3A2419', .45),
    top=mat('top', '#E040C0', .5), pants=mat('pants', '#E040C0', .55), jacket=mat('jacket', '#1B1A24', .5, coat=.2),
    trim=mat('trim', PINK, .4, coat=.3), belt=mat('belt', '#141218', .45, coat=.3), gold=mat('gold', '#E8B94A', .28, metal=1.0),
    shoe=mat('shoe', '#1B1920', .35, coat=.4), sole=mat('sole', '#F3F1F8', .45),
    can=mat('can', '#141218', .35, coat=.5), cushion=mat('cushion', '#2A2533', .7),
    pad=mat('pad', '#1E1A22', .4, coat=.4), padg=mat('padg', '#2A2533', .5),
    bpink=glow(mat('bpink', PINK, .3, coat=.6), PINK, 1.6), bcyan=glow(mat('bcyan', CYAN, .3, coat=.6), CYAN, 1.6), bpurp=glow(mat('bpurp', PURP, .3, coat=.6), PURP, 1.6),
    micb=mat('micb', '#1E1A22', .35, coat=.4), grille=mat('grille', '#9AA0AA', .35, metal=1.0), cyan=glow(mat('cyan', CYAN, .3, coat=.5), CYAN, 1.2),
    lip=mat('lip', '#E0607E', .4, coat=.3), mouth=mat('mouth', '#5E1A28', .45),
)

# ---- proportions ------------------------------------------------------------------------------
HC = V((0, 0, 1.24)); HR = V((0.48, 0.45, 0.42))                      # head centre and radii (globals used by surf())
TR = [(.44, .26, .2), (.50, .24, .185), (.56, .235, .18), (.62, .25, .19), (.68, .285, .2), (.73, .31, .205), (.765, .29, .19),
      (.79, .22, .16), (.815, .15, .13), (.86, .13, .12), (.94, .13, .12)]
_a = np.array(TR); ZS = np.linspace(TR[0][0], TR[-1][0], 22); RXs = np.interp(ZS, _a[:, 0], _a[:, 1]); RYs = np.interp(ZS, _a[:, 0], _a[:, 2])
for _ in range(3):
    RXs[1:-1] = (RXs[:-2] + 2 * RXs[1:-1] + RXs[2:]) / 4; RYs[1:-1] = (RYs[:-2] + 2 * RYs[1:-1] + RYs[2:]) / 4
rxz = lambda z: float(np.interp(z, ZS, RXs)); ryz = lambda z: float(np.interp(z, ZS, RYs))
def tsurf(a_deg, z, off):
    a = math.radians(a_deg); return V(((rxz(z) + off) * math.cos(a), (ryz(z) + off) * math.sin(a), z))
ZH = .50                                       # crop top hem (the belt sits on it)
def ztop(a):                                   # crop top: round neck at the neck base, front a touch lower
    return .80 - .025 * ss(-.3, .3, math.sin(a))

SHD = {1: V((.33, -.01, .70)), -1: V((-.33, -.01, .70))}
ELB = {1: V((.50, .03, .45)), -1: V((-.51, .0, .45))}
# launchpad in the right hand: tilted 40 deg so the pads face the crowd. Local axes u (width), v (depth, toward the crowd), n (up out of the pads)
PT = math.radians(40); PU = V((1, 0, 0)); PN = V((0, math.sin(PT), math.cos(PT))); PV = PN.cross(PU)
PC = V((.27, .33, .55)); PW, PD, PTH = .34, .23, .05
PR = Matrix((PU, PV, PN)).transposed()
WR_R = PC + PU * (PW / 2 + .07) - PN * .01
CB = V((-.43, .27, .52)); BOT_R = .036                                  # mic handle (vertical) in the left fist
WR_L = CB + V((0, -.13, -.01))
LEGX = .155

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

def fixn(ob):
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
    return fixn(mk(name, vs, fs, m))

def shell(name, P, nu, nv, m):
    """Closed garment panel with real thickness: P(u, v, k) gives the outer (k=0) and inner (k=1) surface, u and v in [0, 1]."""
    g = lambda i, j, k: k * (nu + 1) * (nv + 1) + i * (nv + 1) + j
    vs = [P(i / nu, j / nv, k) for k in (0, 1) for i in range(nu + 1) for j in range(nv + 1)]; fs = []
    for i in range(nu):
        for j in range(nv):
            fs.append((g(i, j, 0), g(i + 1, j, 0), g(i + 1, j + 1, 0), g(i, j + 1, 0))); fs.append((g(i, j + 1, 1), g(i + 1, j + 1, 1), g(i + 1, j, 1), g(i, j, 1)))
    for i in range(nu):
        for j in (0, nv): fs.append((g(i, j, 0), g(i, j, 1), g(i + 1, j, 1), g(i + 1, j, 0)))
    for j in range(nv):
        for i in (0, nu): fs.append((g(i, j, 0), g(i, j + 1, 0), g(i, j + 1, 1), g(i, j, 1)))
    return fixn(mk(name, vs, fs, m))

# ---------------------------------------------------------------- body
def lathe(name, zs, rx, ry, m, seg=28, off=0.0):
    vs = []; fs = []
    for z, a, b in zip(zs, rx, ry):
        for i in range(seg):
            t = 2 * math.pi * i / seg; vs.append(V(((a + off) * math.cos(t), (b + off) * math.sin(t), z)))
    for j in range(len(zs) - 1):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
    fs.append(tuple(range(seg - 1, -1, -1))); return mk(name, vs, fs, m)

ZJ = .555; OPEN = math.radians(30)              # jacket hem and the half-angle of its open front
def zjack(a):                                   # jacket neckline: high round collar at the back, dropping into the open front
    return .815 - .14 * ss(.25, .9, math.sin(a)) ** 1.3

def build_torso():
    lathe('torso', ZS, RXs, RYs, M['skin'], seg=20)
    seg = 64; J = 8; vs = []; fs = []
    for i in range(seg):                                                    # inner closing ring at the hem
        t = 2 * math.pi * i / seg; vs.append(V((rxz(ZH) * math.cos(t), ryz(ZH) * math.sin(t), ZH)))
    for j in range(J):
        for i in range(seg):
            t = 2 * math.pi * i / seg; zt = ztop(t); z = ZH + (zt - ZH) * j / (J - 1)
            off = .014 + .012 * (1 - ss(ZH, .56, z)); vs.append(V(((rxz(z) + off) * math.cos(t), (ryz(z) + off) * math.sin(t), z)))
    for i in range(seg):                                                    # inner closing ring at the neckline
        t = 2 * math.pi * i / seg; zt = ztop(t); vs.append(V(((rxz(zt) - .004) * math.cos(t), (ryz(zt) - .004) * math.sin(t), zt)))
    R = J + 2
    for j in range(R - 1):
        for i in range(seg): fs.append((j * seg + i, (j + 1) * seg + i, (j + 1) * seg + (i + 1) % seg, j * seg + (i + 1) % seg))
    mk('top', vs, fs, M['top'])
    ring('pipe_neck', [tsurf(360 * i / 64, ztop(2 * math.pi * i / 64), .017) for i in range(64)], .007, M['trim'], seg=6)
    # cropped bomber: one closed shell round the back and sides, open at the front
    a0 = math.pi / 2 + OPEN; a1 = math.pi / 2 + 2 * math.pi - OPEN
    def jz(u, v):
        a = a0 + (a1 - a0) * u; return a, ZJ + (zjack(a) - ZJ) * v
    def JP(u, v, k):
        a, z = jz(u, v); off = (.058 + .01 * ss(.6, .72, z) if k == 0 else .03) + .012 * (1 - ss(ZJ, ZJ + .05, z))
        return V(((rxz(z) + off) * math.cos(a), (ryz(z) + off) * math.sin(a), z))
    shell('jacket', JP, 48, 8, M['jacket'])
    edge = [JP(i / 48, 1, 0) for i in range(49)] + [JP(1, 1 - j / 4, 0) for j in range(1, 5)] + [JP(1 - i / 48, 0, 0) for i in range(1, 49)] + [JP(0, j / 4, 0) for j in range(1, 4)]
    ring('pipe_jacket', edge, .013, M['trim'], seg=6)
    hem = [JP(i / 36, 0, 0) + V((0, 0, .022)) for i in range(37)]
    sweep('pipe_hemband', hem, .02, M['trim'], seg=6)
    tor('chain', (0, .005, .815), (0, .25, 1), .155, .009, M['gold'], seg=40, rseg=5, squash=(1, .95, 1))
    ell('chain_pend', (0, .16, .755), (.022, .012, .03), M['gold'], seg=12)

def build_legs():
    ell('hips_sh', (0, -.02, .45), (.29, .2, .11), M['pants'], seg=22)
    tor('belt', (0, 0, ZH), Z, rxz(ZH) + .025, .022, M['belt'], seg=40, rseg=6, squash=(1, (ryz(ZH) + .025) / (rxz(ZH) + .025), 1))
    ell('belt_buckle', (0, ryz(ZH) + .05, ZH), (.045, .015, .03), M['gold'], seg=14)
    for s in (-1, 1):
        x = s * LEGX
        sweep('pantleg', [(x, 0, .47), (x, .005, .34), (x, .01, .22), (s * (LEGX + .008), .015, .10)], [.15, .148, .158, .178], M['pants'], seg=22, lip=(.012, .13))
        tor('panthem', (s * (LEGX + .008), .015, .102), Z, .176, .009, M['trim'], seg=28, rseg=5)
        sweep('calf', [(x, .01, .26), (x, .01, .12)], [.085, .075], M['skin'], seg=14)
        ell('shoe', (x, .07, .09), (.105, .175, .07), M['shoe'], seg=16)
        ell('shoe_sole', (x, .075, .045), (.118, .19, .045), M['sole'], seg=16)
        tor('shoe_stripe', (x, .075, .066), Z, 1.0, .007, M['trim'], seg=40, rseg=4, squash=(.118, .19, 1))

def sleeve(sd, S, E, W):
    pts = catmull([S + V((0, 0, .015)), S.lerp(E, .5) + V((0, .01, 0)), E, E.lerp(W, .5), W], 3)
    n = len(pts); rad = [.105 - .03 * i / (n - 1) for i in range(n)]
    sweep('sleeve_' + sd, pts, rad, M['jacket'], seg=18, lip=(.012, .055))
    ell('sleeve_sh_' + sd, S + V((0, 0, .01)), (.12, .115, .12), M['jacket'], seg=18)
    d = (W - E).normalized(); tor('sleeve_cuff_' + sd, W - d * .012, d, .074, .014, M['trim'], seg=24, rseg=6)

def build_arm_r():
    S, E = SHD[1], ELB[1]; sleeve('r', S, E, WR_R)
    # tray grip on the outer edge of the pad: palm at the edge, four fingers under the pad, thumb on top
    edge = PC + PU * (PW / 2)
    h = H.Soup('hand_r'); palm = edge + PU * .035 - PN * .004
    h.ellipsoid(palm, (.04, .07, .06), rot=PR.to_4x4()); h.capsule(WR_R, palm, .056, .05)
    for k, dv in enumerate((-.06, -.02, .02, .06)):
        rf = .018 - .002 * (k == 0)
        p0 = edge + PU * .03 + PV * dv - PN * (PTH / 2 + .01); p1 = edge - PU * .045 + PV * dv * 1.05 - PN * (PTH / 2 + rf * .9)
        p2 = edge - PU * .085 + PV * dv * 1.1 - PN * (PTH / 2 + rf * .8)
        h.capsule(p0, p1, rf + .003, rf, seg=12); h.capsule(p1, p2, rf, rf * .85, seg=12)
    t0 = edge + PU * .035 + PV * .02 + PN * .02; t1 = edge - PU * .02 + PV * .03 + PN * (PTH / 2 + .016); t2 = edge - PU * .06 + PV * .025 + PN * (PTH / 2 + .014)
    h.capsule(palm, t0, .03, .024, seg=12); h.capsule(t0, t1, .024, .021, seg=12); h.capsule(t1, t2, .021, .018, seg=12)
    hd, _ = h.remesh(voxel=.0058, smooth=5, smooth_factor=.5, target_tris=1100); H.set_material(hd, M['skin']); hd.name = 'hand_r'; reg(hd)
    rbox('pad', PC, (PW, PD, PTH), M['pad'], bevel=.016, rot=PR, bseg=3)
    rbox('pad_face', PC + PN * (PTH / 2), (PW - .03, PD - .03, .008), M['padg'], bevel=.003, rot=PR, bseg=1)
    cols = [[PINK, CYAN, PURP, CYAN], [CYAN, PINK, CYAN, PURP], [PURP, CYAN, PINK, PINK]]
    key = {PINK: 'bpink', CYAN: 'bcyan', PURP: 'bpurp'}
    for j in range(3):
        for i in range(4):
            c = PC + PU * (-.115 + i * .066) + PV * (-.07 + j * .058) + PN * (PTH / 2 + .009)
            rbox('pad_btn', c, (.05, .044, .016), M[key[cols[j][i]]], bevel=.006, rot=PR, bseg=1)
    rbox('pad_strip', PC + PU * .0 + PV * (PD / 2 - .022) + PN * (PTH / 2 + .006), (PW - .07, .012, .01), M['bpink'], bevel=.003, rot=PR, bseg=1)
    for x in (-.13, .13):
        sweep('pad_knob', [PC + PU * x + PV * (PD / 2 - .022) + PN * (PTH / 2), PC + PU * x + PV * (PD / 2 - .022) + PN * (PTH / 2 + .025)], .014, M['grille'], seg=10)

def build_arm_l():
    S, E = SHD[-1], ELB[-1]; sleeve('l', S, E, WR_L)
    # fist round the mic handle: palm behind it, four fingers round the outer side, thumb over the inner side (gym's shaker grip)
    palm = CB + V((0, -.062, 0)); h = H.Soup('hand_l'); h.ellipsoid(palm, (.05, .038, .088)); h.capsule(WR_L, palm, .056, .05)
    rho = BOT_R + .018; rf = .018
    def arc(z, th, rho, ra, rb):
        pts = [V((CB.x + rho * math.cos(math.radians(t)), CB.y + rho * math.sin(math.radians(t)), z)) for t in th]
        for p0, p1, r0, r1 in zip(pts[:-1], pts[1:], [ra] + [rf] * 5, [rf] * 4 + [rb]): h.capsule(p0, p1, r0, r1, seg=12)
    for k, dz in enumerate((.063, .021, -.021, -.063)):
        arc(CB.z + dz, (250, 195, 140, 95, 55), rho, rf + .002, rf * (.85 if k == 3 else .95))
    arc(CB.z + .104, (305, 350, 20, 52), BOT_R + .022, .028, .02)
    hd, _ = h.remesh(voxel=.0058, smooth=5, smooth_factor=.5, target_tris=1000); H.set_material(hd, M['skin']); hd.name = 'hand_l'; reg(hd)
    sweep('mic', [(CB.x, CB.y, CB.z - .13), (CB.x, CB.y, CB.z + .12)], [.028, .04], M['micb'], seg=20)
    tor('mic_ring', (CB.x, CB.y, CB.z + .135), Z, .043, .009, M['cyan'], seg=24, rseg=6)
    ell('mic_head', (CB.x, CB.y, CB.z + .2), (.068, .068, .072), M['grille'], seg=20)
    tor('mic_band', (CB.x, CB.y, CB.z + .2), Z, .069, .006, M['micb'], seg=28, rseg=5)

def build_neck():
    ell('neck_col', (0, 0, .85), (.135, .125, .11), M['skin'], seg=20)

def build_body_all():
    build_torso(); build_legs(); build_arm_r(); build_arm_l(); build_neck()

# ---------------------------------------------------------------- head
HOLE = (0.0, -.235, .19, .125)

def jaw(p):                                   # soft round jaw: fuller cheeks, small chin. p is a world point
    d = p - HC; t = ss(-.06, -.32, d.z); c = ss(-.25, -.40, d.z)
    return HC + V((d.x * (1 + .05 * t - .12 * c), d.y * (1 + .1 * t), d.z))

HOLE_AB = (.17, .11)                           # head hole half-sizes in pre-jaw face coords. The face skin ring starts on this exact boundary

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

PONY = [(0, -.30, .37), (0, -.40, .45), (0, -.53, .42), (0, -.62, .25), (0, -.63, .0), (0, -.58, -.24), (0, -.50, -.40)]
CUP = .53                                      # headphone cup centre x (head local)

def build_head():
    head_surface()
    so = H.Soup('hair'); n = 260
    def thr(az): return float(np.interp(az, [0, 30, 60, 95, 140, 180], [40, 36, 8, -16, -34, -40]))
    for i in range(n):
        z = 1 - 2 * (i + .5) / n; a = i * 2.39996; r = math.sqrt(1 - z * z); d = V((r * math.cos(a), r * math.sin(a), z))
        az = math.degrees(math.atan2(abs(d.x), d.y)); el = math.degrees(math.asin(d.z))
        if el < thr(az): continue
        so.sphere(HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z)) * .86, .135, seg=12)
    for c in ((0, .1, .37), (.1, 0, .385), (-.1, 0, .385), (0, -.12, .365)): so.sphere(HC + V(c), .09, seg=14)   # smooth crown
    for s in (-1, 1):                          # curtain fringe parted in the middle, sweeping out past the brows
        P = [surf(s * fx, fz, .028)[0] for fx, fz in ((.025, .36), (.13, .33), (.25, .26), (.35, .15), (.41, .02), (.43, -.1))]
        for p0, p1, r0, r1 in zip(P[:-1], P[1:], (.05, .062, .062, .058, .052), (.062, .062, .058, .052, .04)): so.capsule(p0, p1, r0, r1, seg=14)
    hair, _ = so.remesh(voxel=.011, smooth=24, smooth_factor=.8, target_tris=2600); H.set_material(hair, M['hair']); hair.name = 'h_hair'; reg(hair)
    # high ponytail off the back of the crown with a pink tie
    pts = catmull([HC + V(p) for p in PONY], 3)
    rad = np.interp(np.linspace(0, 1, len(pts)), [0, .12, .35, .65, .85, 1], [.07, .095, .11, .1, .075, .03])
    sweep('h_pony', pts, list(rad), M['hair'], seg=14)
    tie = HC + V(PONY[0]); tor('h_tie', tie + V((0, -.012, .006)), (0, -.75, .66), .07, .022, M['trim'], seg=24, rseg=6)
    # big black cans: band over the crown, cups on the ears with a pink ring
    band = [HC + V((CUP * math.cos(t), -.03, .5 * math.sin(t))) for t in [math.radians(15 + 150 * i / 20) for i in range(21)]]
    sweep('h_band', band, .032, M['can'], seg=10)
    sweep('h_bandpad', band[6:15], .02, M['cushion'], seg=8)
    for s in (-1, 1):
        c = HC + V((s * CUP, -.03, -.04))
        sweep('h_cup', [c - V((s * .045, 0, 0)), c + V((s * .045, 0, 0))], .13, M['can'], seg=24)
        tor('h_cupring', c + V((s * .093, 0, 0)), (1, 0, 0), .095, .014, M['trim'], seg=24, rseg=5)
        tor('h_cushion', c - V((s * .05, 0, 0)), (1, 0, 0), .1, .03, M['cushion'], seg=20, rseg=5)
        sweep('h_yoke', [c + V((s * .02, 0, .1)), HC + V((s * (CUP - .005), -.03, .19))], .022, M['can'], seg=8)
        tor('h_hoop', HC + V((s * .44, .0, -.23)), (1, 0, 0), .04, .008, M['gold'], seg=24, rseg=5)
    p, n_, t, u = surf(0, -.1); ell('h_nose', p + n_ * .002, (.045, .036, .036), M['nose'], seg=20)

# ---------------------------------------------------------------- face (one mesh, six shape keys)
FM = ['skin', 'brow', 'eye', 'white', 'line', 'mouth', 'lip', 'teeth', 'tongue', 'blush']
EXe, EZe = .175, -.035
_I = dict(bz=.135, tilt=.015, arch=.016, eye='bead', es=(.95, .9), cut=(.03, 0), hl=.008, w=.15, curve=.032, up=0, dn=0, teeth=0, tongue=0, cz=-.225, arc=.058)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'eye': 'arc', 'arc': -.022, 'bz': .14},
    'mouth_open': {**_I, 'w': .17, 'curve': .012, 'up': .006, 'dn': .08, 'teeth': .03, 'tongue': .045},
    'smile': {**_I, 'w': .21, 'curve': .05, 'bz': .16, 'tilt': -.01},
    'angry': dict(bz=.045, tilt=.09, arch=-.004, eye='bead', es=(1.15, 1.0), cut=(.012, .6), hl=.0, w=.18, curve=-.05, up=.018, dn=.05, teeth=.03, tongue=0, cz=-.23, arc=.058),
    'grin': dict(bz=.18, tilt=-.012, arch=.03, eye='arc', es=(1, 1), cut=None, hl=.026, w=.28, curve=.06, up=.004, dn=.08, teeth=.03, tongue=.045, cz=-.235, arc=.062),
    'ult': dict(bz=.17, tilt=.05, arch=.01, eye='bead', es=(1.05, .95), cut=(.03, 0), hl=.008, w=.24, curve=.006, up=.04, dn=.09, teeth=.03, tongue=.065, cz=-.235, arc=.058),
}

LOOP = hole_loop()

def face_geo(e):
    vs = []; fs = []; mi = []
    def add(v, f, m):
        o = len(vs); vs.extend(v); fs.extend([tuple(i + o for i in ff) for ff in f]); mi.extend([FM.index(m)] * len(f))
    def hide(v): return [HC.copy() for _ in v]
    def stroke(pts, rw, rn, off, m, show=True, seg=8, taper=.45):
        P = [surf(x, z, off) for x, z in pts]; n = len(P); v = []
        for i in range(n):
            p, nn, _, _ = P[i]; tan = (P[min(i + 1, n - 1)][0] - P[max(i - 1, 0)][0]).normalized(); side = nn.cross(tan).normalized()
            f = math.sin(math.pi * i / (n - 1)) ** taper if 0 < i < n - 1 else 0.0
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
        stroke([(s * (EXe + q * .095), e['bz'] + EZe + q * e['tilt'] + e['arch'] * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .044, .026, .006, 'brow')
        bead = e['eye'] == 'bead'; a, c = .068 * e['es'][0], .082 * e['es'][1]
        blob(s * EXe, EZe, (a, .038, c), 0, 'eye', show=bead, seg=16, cut=(e['cut'][0], e['cut'][1] * s) if e['cut'] else None)
        blob(s * EXe, EZe, (.013, .011, .013), .03, 'white', show=bead, seg=10, d=(.018, e['hl'] + .01))
        blob(s * EXe, EZe, (.005, .004, .005), .028, 'white', show=bead, seg=6, d=(-.022, -.024))
        top = min(c, e['cut'][0] + .01) if e['cut'] else c                # lash wing follows the top lid, so it drops with angry
        stroke([(s * (EXe + a * .55 + .03 * q), EZe + top * .8 + .028 * q * q + .012 * q) for q in [i / 4 for i in range(5)]], .011, .009, .02, 'eye', show=bead, seg=6, taper=.2)
        stroke([(s * EXe + .07 * math.cos(ph), EZe - .03 + e['arc'] * 1.05 * math.sin(ph)) for ph in [math.radians(168 - 156 * i / 11) for i in range(12)]], .015, .011, .005, 'eye', show=not bead)
        v = [surf(s * .29, -.165, .0025)[0]]; f = []
        for j in range(1, 4):
            for i in range(14):
                ang = 2 * math.pi * i / 14; v.append(surf(s * .29 + .046 * j / 3 * math.cos(ang), -.165 + .03 * j / 3 * math.sin(ang), .0025 if j < 3 else .0)[0])
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
        lipo = (ox + .014 * math.cos(th), oz + .017 * math.sin(th))
        sc = lambda t: (cen[0] + (ox - cen[0]) * t, cen[1] + (oz - cen[1]) * t)
        rings.append([q0.copy(), surf(*lerpp(outer, lipo, .5), 0)[0], surf(*lipo, .0065)[0],
                      surf(*lerpp(lipo, (ox, oz), .5), .0135)[0], surf(ox, oz, .006)[0],
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
    global GS
    build_body_all(); build_head(); build_face()
    for o in HERO:
        if o.matrix_world != Matrix.Identity(4): o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    tris = sum(H.tri_count(o) for o in HERO); print('TOY_TRIS', tris, 'objects', len(HERO))
    agg = {}
    for o in HERO: agg[o.name.split('.')[0]] = agg.get(o.name.split('.')[0], 0) + H.tri_count(o)
    print('TOY_TOP', sorted(agg.items(), key=lambda kv: -kv[1])[:16])
    top = max(v.co.z for o in HERO for v in o.data.vertices); GS = HEIGHT / top; open(_gs, 'w').write(repr(GS))
    xs = [v.co.x for o in HERO for v in o.data.vertices]; print('TOY_RAW_TOP', round(top, 4), 'GS', round(GS, 4), 'X', round(min(xs) * GS, 3), round(max(xs) * GS, 3))
    for o in HERO:
        for v in o.data.vertices: v.co *= GS
        if o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks:
                for v in kb.data: v.co *= GS
    stage()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'dj_build.blend'))

# ---------------------------------------------------------------- rig + weights
def eyepos(s): return surf(s * EXe, EZe)[0]
BONES = [
    ('root', (0, 0, 0), (0, 0, .25), None), ('hips', (0, 0, .48), (0, 0, .58), 'root'), ('spine', (0, 0, .58), (0, 0, .67), 'hips'),
    ('chest', (0, 0, .67), (0, 0, .77), 'spine'), ('neck', (0, 0, .77), (0, .01, .86), 'chest'), ('head', (0, .01, .86), (0, .02, 1.68), 'neck'),
    ('eye.l', tuple(eyepos(-1)), tuple(eyepos(-1) + V((0, .06, 0))), 'head'), ('eye.r', tuple(eyepos(1)), tuple(eyepos(1) + V((0, .06, 0))), 'head'),
    ('upperarm.l', tuple(SHD[-1]), tuple(ELB[-1]), 'chest'), ('lowerarm.l', tuple(ELB[-1]), tuple(WR_L), 'upperarm.l'),
    ('hand.l', tuple(WR_L), tuple(CB + V((0, -.03, .0))), 'lowerarm.l'), ('handslot.l', tuple(CB), tuple(CB + V((0, 0, .08))), 'hand.l'),
    ('upperarm.r', tuple(SHD[1]), tuple(ELB[1]), 'chest'), ('lowerarm.r', tuple(ELB[1]), tuple(WR_R), 'upperarm.r'),
    ('hand.r', tuple(WR_R), tuple(PC + PU * (PW / 2)), 'lowerarm.r'), ('handslot.r', tuple(PC), tuple(PC + PN * .1), 'hand.r'),
    ('upperleg.l', (-LEGX, .02, .50), (-LEGX, .01, .28), 'hips'), ('lowerleg.l', (-LEGX, .01, .28), (-LEGX, 0, .10), 'upperleg.l'),
    ('foot.l', (-LEGX, 0, .10), (-LEGX, .12, .03), 'lowerleg.l'), ('toes.l', (-LEGX, .12, .03), (-LEGX, .24, .02), 'foot.l'),
    ('upperleg.r', (LEGX, .02, .50), (LEGX, .01, .28), 'hips'), ('lowerleg.r', (LEGX, .01, .28), (LEGX, 0, .10), 'upperleg.r'),
    ('foot.r', (LEGX, 0, .10), (LEGX, .12, .03), 'lowerleg.r'), ('toes.r', (LEGX, .12, .03), (LEGX, .24, .02), 'foot.r'),
    ('prop', tuple(PC), tuple(PC + V((0, 0, .3))), 'chest'),        # no big prop: the bone marks the launchpad (the booth is a game effect)
]
RIGID = {'eye.l', 'eye.r'}                    # props ride deforming handslot bones so they follow the pose

def make_rig():
    arm = bpy.data.armatures.new('dj_rig'); ob = bpy.data.objects.new('dj_rig', arm); bpy.context.scene.collection.objects.link(ob)
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

TRUNK = ([(0, 0, .43), (0, 0, .58), (0, 0, .67), (0, 0, .77), (0, 0, .86), (0, 0, .96)], ['hips', 'spine', 'chest', 'neck', 'head'], [.06, .05, .04, .05])
def trunk(p): return chain(p, *TRUNK)
def leg(p, s):
    x = s * LEGX; sd = 'l' if s < 0 else 'r'
    return chain(p, [(x, 0, .60), (x, .01, .28), (x, 0, .10), (x, .12, .03)], ['upperleg.' + sd, 'lowerleg.' + sd, 'foot.' + sd], [.06, .04])
def scale(w, f): return {k: v * f for k, v in w.items()}
def merge(*ws):
    o = {}
    for w in ws:
        for k, v in w.items(): o[k] = o.get(k, 0) + v
    return o

def weights_for(name, p):
    n = name.split('.')[0]; s = -1 if p.x < 0 else 1
    if n.startswith('h_'): return {'head': 1.0}
    if n.startswith('pad'): return {'handslot.r': 1.0}
    if n.startswith('mic'): return {'handslot.l': 1.0}
    if n.startswith('hand_'): return {'hand.' + n[-1]: 1.0}
    if n.startswith('sleeve'):
        sd = n[-1]; k = 1 if sd == 'r' else -1; S, E = SHD[k], ELB[k]; W = WR_R if k == 1 else WR_L; tip = PC + PU * (PW / 2) if k == 1 else CB
        w = chain(p, [S, E, W, tip], ['upperarm.' + sd, 'lowerarm.' + sd, 'hand.' + sd], [.09, .05])
        wc = 1 - ss(-.1, .14, (p - S).dot((E - S).normalized()))
        return merge(scale(w, 1 - wc), {'chest': wc})
    if n in ('torso', 'top', 'jacket') or n.startswith(('pipe', 'neck', 'chain')): return trunk(p)
    if n.startswith(('hips_sh', 'belt')):
        u = ss(.48, .38, p.z) * ss(.03, .13, abs(p.x)); return merge(scale(leg(p, s), u), scale({'hips': 1.0}, 1 - u))
    if n.startswith(('pantleg', 'panthem', 'calf', 'shoe')):
        w = leg(p, s)
        if n.startswith('shoe'):
            sd = 'l' if s < 0 else 'r'; t = ss(.13, .22, p.y); wf = w.pop('foot.' + sd); w['foot.' + sd] = wf * (1 - t); w['toes.' + sd] = wf * t
        h = ss(.42, .50, p.z) if n.startswith('pantleg') else 0.0
        return merge(scale(w, 1 - h), {'hips': h})
    print('[weights] unclassified', name); return {'hips': 1.0}

def stage_rig():
    openb('dj_build.blend'); O = bpy.data.objects
    parts = [o for o in O if o.type == 'MESH' and o.name != 'cyc']
    for o in parts:
        o.data.update()
        for v in o.data.vertices:
            for b, w in weights_for(o.name, v.co / GS).items():
                if w > 1e-3:
                    g = o.vertex_groups.get(b) or o.vertex_groups.new(name=b); g.add([v.index], w, 'REPLACE')
    heads = [o for o in parts if o.name.startswith('h_')]; heads.sort(key=lambda o: o.name != 'h_face')
    bodies = [o for o in parts if not o.name.startswith('h_')]
    head = H.join(heads, 'dj_head'); body = H.join(bodies, 'dj_body'); rig = make_rig()
    for ob in (head, body):
        ob.parent = rig; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = rig
        for v in ob.data.vertices:
            tot = sum(g.weight for g in v.groups)
            if tot < .5: print('[rig] weak vertex', ob.name, v.index, tot)
    for b in rig.data.bones: b.use_deform = b.name not in RIGID
    print('[rig] shape keys', [k.name for k in head.data.shape_keys.key_blocks], 'tris', H.tri_count(head), H.tri_count(body))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'dj_rig.blend'))

# ---------------------------------------------------------------- animation (OG.pose_frame / OG.make_action reused)
_og_pose = OG.pose_frame
X = OG.X
def dj_pose(rig, t, kind):
    if kind == 'attack':                               # Glow Notes: punch the pad out at the crowd, quick recoil, mic hand bobs
        u = math.sin(math.pi * min(1.0, t / .45)) if t < .45 else 0.0; k = u * u * (3 - 2 * u) if u > 0 else 0.0
        P = OG.Pose(rig); P.rot('spine', OG.axis_rot(X, 4 * k)); P.rot('chest', OG.axis_rot(X, 6 * k) @ OG.axis_rot(OG.Z, -8 * k)); P.rot('head', OG.axis_rot(X, -6 * k))
        ua = (ELB[1] - SHD[1]).normalized(); la = (WR_R - ELB[1]).normalized()
        P.aim('upperarm.r', ua.lerp(V((.35, .85, .25)), k).normalized()); P.aim('lowerarm.r', la.lerp(V((.1, .95, .3)), k).normalized())
        P.rot('upperarm.l', OG.axis_rot(X, 8 * k)); return P
    if kind != 'ult': return _og_pose(rig, t, kind)
    P = OG.Pose(rig); P.rot('spine', OG.axis_rot(X, -4)); P.rot('chest', OG.axis_rot(X, -7)); P.rot('head', OG.axis_rot(X, 6))
    # Main Stage: mic punched straight up, pad thrown out wide
    P.aim('upperarm.l', (-.75, .25, .62)); P.aim('lowerarm.l', (-.35, .3, .89)); P.aim('hand.l', (-.2, .35, .92))
    P.aim('upperarm.r', (.92, .15, .35)); P.aim('lowerarm.r', (.7, .45, .55))
    return P
OG.pose_frame = dj_pose

def stage_anim():
    openb('dj_rig.blend'); SC.render.fps = OG.FPS; rig = bpy.data.objects['dj_rig']
    acts = [OG.make_action(rig, 'idle', 'idle', 60), OG.make_action(rig, 'run', 'run', 24), OG.make_action(rig, 'attack', 'attack', 18, loop=False), OG.make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'dj_anim.blend')); print('[anim] actions', [a.name for a in acts])

def stage_export():
    openb('dj_anim.blend'); O = bpy.data.objects; rig = O['dj_rig']; OG.reset_pose(rig)
    for k in O['dj_head'].data.shape_keys.key_blocks: k.value = 0.0
    H.select_only([O['dj_head'], O['dj_body'], rig], rig)
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

# ---------------------------------------------------------------- shots (gym's stage and cameras)
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
    openb('dj_anim.blend'); O = bpy.data.objects; rig = O['dj_rig']; head = O['dj_head']; cam = O['cam']
    only = [a for a in ARGS if a in ('beauty', 'turn', 'expr', 'sheet', 'wrist')]
    want = lambda k: not only or k in only
    play(rig, 'idle', 0); set_key(head, 'none')
    if want('beauty') and only != ['wrist']: shoot(cam, os.path.join(SHOTS, 'beauty.png'), 1600, 1600, 32, 8, (0, .2, .9), 2.3, cam_z=.85)
    if only == ['wrist']:
        for nm, W in (('r', PC), ('l', CB)): shoot(cam, os.path.join(WORK, 'wrist_%s.png' % nm), 700, 700, 20, 7, W * GS, .6)
        shoot(cam, os.path.join(WORK, 'face.png'), 900, 900, 15, 7, HC * GS, 1.3)
        shoot(cam, os.path.join(WORK, 'back.png'), 900, 900, 160, 7, HC * GS - V((0, 0, .2)), 1.6)
    if want('turn') and only != ['wrist']:
        ps = []
        for i, ang in enumerate((0, 90, 180)):
            rig.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
            t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((0, .12, .9)); p = os.path.join(WORK, 't_%d.png' % i); ps.append(p)
            shoot(cam, p, 534, 800, 0, 9, t, 1.75)
        rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(SHOTS, 'turnaround.png'))
    if want('expr') and only != ['wrist']:
        ps = []
        for name in ('smile', 'angry', 'grin', 'ult'):
            set_key(head, name); p = os.path.join(WORK, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, 0, HC.z * GS + .02), 1.3)
        row(ps, os.path.join(SHOTS, 'expressions.png')); set_key(head, 'none')
    if want('sheet') and only != ['wrist']:
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
