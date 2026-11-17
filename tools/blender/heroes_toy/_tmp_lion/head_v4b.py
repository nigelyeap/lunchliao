M.update(rfur=mat('red_fur', '#C8102E', .9, spec=.2), bronze=mat('eye_bronze', '#6E3F16', .42, metal=.35),
         iris=mat('iris', '#160B06', .6), eyew=mat('eye_ring', '#F3E9D2', .5))

def sgp(c, e): return math.copysign(abs(c) ** e, c)
def sup(v, ex):                                                  # sphere point pushed out to a superellipsoid (one exponent)
    return v * sum(abs(c) ** ex for c in v) ** (-1 / ex)

def canon(d):                                                    # unit superellipsoid point along d, per-axis exponents HX
    d = V(d).normalized(); lo, hi = 0.0, 2.0
    for _ in range(36):
        s = (lo + hi) / 2
        if sum(abs(d[i] * s) ** HX[i] for i in range(3)) > 1: hi = s
        else: lo = s
    return d * lo

def shell_raw(d):
    q = canon(d)
    p = V((q.x * HR.x * (1 + TAPX * q.z), HC.y + q.y * HR.y * (1 - TAPY * q.z) - LEAN * HR.z * q.z, HC.z + q.z * HR.z))
    p.z = max(p.z, JC.z + .004); return p                         # flat mouth roof that the jaw closes on

SV, SF = sph_vf(44, 22); SP = [shell_raw(v) for v in SV]
BVH = BVHTree.FromPolygons([tuple(p) for p in SP], SF)
def _cast(o, d):
    hit = BVH.ray_cast(V(o), V(d).normalized())[0]
    if hit is None: raise ValueError('shell ray missed %s %s' % (tuple(o), tuple(d)))
    return hit
def _front(fx, z): return _cast((fx, 5, z), (0, -1, 0))

def hsurf(fx, fz, off=0.0):                                      # point on the face front at (x, HC.z + fz), its normal, side and up axes
    z = HC.z + fz; p = _front(fx, z); e = .03
    n = (_front(fx, z + e) - _front(fx, z - e)).cross(_front(fx + e, z) - _front(fx - e, z)).normalized()
    if n.y < 0: n = -n
    t = n.cross(Z).normalized(); u = t.cross(n).normalized(); return p + n * off, n, t, u
def on_head(fx, fz, off=0.0): return hsurf(fx, fz, off)[0]

def shell_pn(d):                                                 # shell point along a direction from the centre, with outward normal
    d = V(d).normalized(); a = frame_from(d)[0]; b = d.cross(a); e = .03; p = shell_raw(d)
    n = (shell_raw(d + a * e) - shell_raw(d - a * e)).cross(shell_raw(d + b * e) - shell_raw(d - b * e)).normalized()
    if n.dot(p - HC) < 0: n = -n
    return p, n

def ring_shell(z, angs, cy, inset=0.0):                          # horizontal ring of shell points (angle 90 deg = front)
    out = []
    for a in angs:
        r = V((math.cos(a), math.sin(a), 0)); out.append(_cast(V((0, cy, z)) + r * 3, -r) - r * inset)
    return out

def sell(name, c, r, m, R, ex=6.0, seg=16):                      # bevelled slab: superellipsoid in frame R
    vs, fs = sph_vf(seg, seg // 2); c = V(c); P = [c + R @ V((q.x * r[0], q.y * r[1], q.z * r[2])) for q in (sup(v, ex) for v in vs)]
    return mk(name, P, fs, m, uvs=[[puv(P[i]) for i in f] for f in fs])

# ---- directional fur: flattened tapering clumps that lie along a flow direction ----
def clump_vf(root, dirv, L, w, out, bend=0.0, flat=.6, n=4, seg=5):
    dirv = V(dirv).normalized(); out = V(out).normalized(); root = V(root)
    P = [root + dirv * (L * k / n) + out * (bend * L * (k / n) ** 2) for k in range(n + 1)]
    vs = [root - dirv * (w * .3)]; fs = []; rings = []
    for k in range(n):
        t = k / n; T = (P[k + 1] - P[k]).normalized(); S = out.cross(T)
        if S.length < 1e-5: S = frame_from(T)[0]
        S.normalize(); Nn = T.cross(S); r = w * min(1.0, (t + .2) / .45) * (1 - t) ** .8
        rings.append(len(vs)); vs += [P[k] + (S * math.cos(a) + Nn * (math.sin(a) * flat)) * r for a in [2 * math.pi * i / seg for i in range(seg)]]
    vs.append(P[n]); tip = len(vs) - 1
    for i in range(seg): fs.append((0, rings[0] + (i + 1) % seg, rings[0] + i))
    for j in range(n - 1):
        a, b = rings[j], rings[j + 1]
        for i in range(seg): fs.append((a + i, a + (i + 1) % seg, b + (i + 1) % seg, b + i))
    for i in range(seg): fs.append((rings[-1] + i, rings[-1] + (i + 1) % seg, tip))
    return vs, fs

def clumps(name, specs, m):
    vs = []; fs = []
    for sp in specs:
        v, f = clump_vf(*sp); o = len(vs); vs += v; fs += [tuple(i + o for i in ff) for ff in f]
    return fix_normals(mk(name, vs, fs, m))

def build_shell():
    mi = []
    for f in SF:
        c = sum((SP[i] for i in f), V()) / len(f); q = sum((SV[i] for i in f), V()) / len(f)
        mi.append(1 if c.z < JC.z + .012 else 2 if q.normalized().y > .42 and q.normalized().z < .84 else 0)
    mk('h_shell', SP, SF, [M['rfur'], M['mouth'], M['panel']], mat_idx=mi, uvs=[[puv(SP[i]) for i in f] for f in SF])

def revolve(name, prof, c, mats, seg=40, mrun=None, je=2.0):
    """prof: list of (rx, ry, dz). First and last with rx==0 become poles. Rings are superellipses with exponent je."""
    c = V(c); vs = []; fs = []; mi = []; rings = []
    for rx, ry, dz in prof:
        if rx == 0: vs.append(c + V((0, 0, dz))); rings.append([len(vs) - 1] * seg)
        else:
            rings.append(list(range(len(vs), len(vs) + seg)))
            vs += [c + V((rx * sgp(math.cos(2 * math.pi * i / seg), 2 / je), ry * sgp(math.sin(2 * math.pi * i / seg), 2 / je), dz)) for i in range(seg)]
    for j in range(len(rings) - 1):
        a, b = rings[j], rings[j + 1]
        for i in range(seg):
            q = [a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]]; q = [x for k, x in enumerate(q) if x not in q[:k]]
            fs.append(tuple(q)); mi.append(mrun[j] if mrun else 0)
    return fix_normals(mk(name, vs, fs, mats, mat_idx=mi))

def jring(rx, ry, a): return V((rx * sgp(math.cos(a), 2 / JE), ry * sgp(math.sin(a), 2 / JE), 0))

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
    revolve('j_jaw', prof, JC, [M['rfur'], M['gold'], M['mouth']], seg=40, mrun=mr, je=JE)
    ell('j_tongue', JC + V((0, .08, -.10)), (.36, .30, .08), M['tongue'], seg=16)
    for k in range(9):                                            # lower teeth on the inner lip, fangs at the ends
        a = math.radians(30 + 120 * k / 8); big = k in (0, 8)
        ell('j_tooth', JC + jring(JRI.x * .96, JRI.y * .96, a) + V((0, 0, .03 + (.03 if big else 0))), (.034, .026, .06 if big else .038), M['teeth'], seg=8)
    # the big flat fur lower lip: a fat roll on the rim, three rows of clumps hanging down over the shovel jaw
    sweep('j_lipfur', [JC + jring(JRO.x + .02, JRO.y + .02, math.radians(a)) for a in np.linspace(-14, 194, 40)], .10, M['rfur'], seg=8)
    specs = []
    for row, (n, sc, dz, L, w) in enumerate(((19, 1.04, .02, .28, .11), (16, .93, -.15, .25, .10), (10, .68, -.28, .20, .09))):
        for i in range(n):
            a = math.radians(-6 + 192 * (i + .5 * (row % 2)) / n)
            out = V((math.cos(a), math.sin(a), -.25)).normalized()
            specs.append((JC + jring(JRO.x * sc, JRO.y * sc, a) + V((0, 0, dz)), V((math.cos(a) * .3, math.sin(a) * .3, -1)), L, w, out, .12))
    clumps('j_lipclump', specs, M['rfur'])

def build_head():
    build_shell(); build_jaw()
    for k, p in enumerate(ring_shell(JC.z + .03, [math.radians(a) for a in np.linspace(-6, 186, 9)], .10, inset=.08)):
        big = k in (0, 8); ell('h_tooth', p + V((0, 0, -.05 - (.02 if big else 0))), (.034, .026, .06 if big else .042), M['teeth'], seg=8)
    sweep('h_lip', ring_shell(JC.z + .05, [math.radians(a) for a in np.linspace(-10, 190, 34)], .10, inset=-.015), .045, M['gold'], seg=7)
    # flat forehead plate, painted gold, rising from the nose to the mirror
    p, n, t, u = hsurf(0, .10); sell('h_plate', p + n * .02, (.25, .06, .28), M['panel'], frame_mat(t, n, u), ex=5)
    p, n, t, u = hsurf(0, -.20); NO = p + n * .05
    ellp('h_nose', NO, (.17, .11, .10), M['panel'], seg=18)
    for s in (-1, 1): ell('h_nostril', NO + t * (s * .075) + n * .09 - u * .035, (.04, .025, .028), M['nostril'], seg=12)
    # mirror high on the forehead: raised gold frame, red fur ring of short radial clumps
    p, n, t, u = hsurf(0, .31); MC = p + n * .09; fr = frame_mat(t, n, u)
    sell('h_mirror_frame', MC, (.15, .04, .15), M['gold'], fr, ex=2.4, seg=20)
    ell('h_mirror', MC + n * .025, (.10, .02, .10), M['mirror'], rot=fr, seg=20)
    tor('h_mirror_rim', MC + n * .035, n, .11, .02, M['gold'], seg=28, rseg=5)
    specs = []
    for k in range(14):
        a = 2 * math.pi * k / 14; d = t * math.cos(a) + u * math.sin(a); specs.append((MC + d * .14 - n * .01, d + n * .3, .11, .075, n, 0.0))
    clumps('h_mirror_fur', specs, M['rfur'])
    q, qn = shell_pn((0, .45, 1)); FC = q + qn * .08
    for k in range(7):
        a = 2 * math.pi * k / 7; d = V((math.cos(a), 0, math.sin(a))); ell('h_petal', FC + d * .07 + V((0, .02, 0)), (.07, .04, .07), M['rfur'], seg=10)
    ell('h_flower', FC + V((0, .05, 0)), (.045, .04, .045), M['gold'], seg=12)
    # eyes: dark bronze ball, gold rim, pale socket ring (lids, pupil, brows live in the keyed face mesh)
    for s in (-1, 1):
        c, f, t, u = eye_frame(s)
        ell('h_eyeball', c, (ER, ER, ER), M['bronze'], seg=16)
        tor('h_eyegold', c + f * (ER * .55), f, ER * .835, .016, M['gold'], seg=24, rseg=5)
        tor('h_socket', c - f * .03, f, ER + .035, .045, M['eyew'], seg=28, rseg=6)
    # black fur fringe hanging under each eye along the cheek
    base = []; specs = []
    for s in (-1, 1):
        row = []
        for k in range(8):
            p, n, _, _ = hsurf(s * (.13 + .07 * k), EZs - .26 + .10 * (k / 7) ** 1.5, .02); row.append(p)
            specs.append((p, -Z + n * .35, .15, .07, n, .1))
        sweep('h_blackbase', row, .05, M['bfur'], seg=6)
    clumps('h_blackfur', specs, M['bfur'])
    # red fur: a front rim sweeping back, a second row behind it, a ring round the back, big lobes on the top corners
    specs = []
    for row, (yd, n, L, w) in enumerate(((.30, 26, .28, .12), (-.15, 22, .30, .12), (-.65, 18, .26, .11))):
        for i in range(n):
            a = 2 * math.pi * i / n if row == 2 else math.radians(-18 + 216 * (i + .5 * row) / n)
            p, nn = shell_pn((math.cos(a), yd, math.sin(a)))
            if p.z < JC.z + .06: continue
            rad = V((math.cos(a), 0, math.sin(a))); specs.append((p - nn * .02, rad * .55 + V((0, -.8, .1)), L, w, nn, .12))
    for s in (-1, 1):
        for d, L, w in (((.70, .05, .82), .36, .16), ((.55, .15, .92), .32, .15), ((.82, -.05, .62), .32, .14), ((.62, -.25, .85), .30, .14), ((.40, .0, .98), .26, .12)):
            p, nn = shell_pn((s * d[0], d[1], d[2])); specs.append((p - nn * .02, V((s * .45, -.55, .75)), L, w, nn, .15))
    clumps('h_rimfur', specs, M['rfur'])
    col = [shell_pn((math.cos(a) * .95, -.9, math.sin(a) * .85))[0] for a in np.linspace(0, 2 * math.pi, 33)]
    sweep('h_collar', [q + V((0, -.01, 0)) for q in col], .03, M['gold'], seg=6, round_caps=False)

# ---------------------------------------------------------------- face (one mesh, keyed): lids, pupils, brows, cheek balls
ER = .16; EXs, EZs = .44, .16
def eye_frame(s):                                                # eyes set high and wide, turned out to the sides
    p, n, t, u = hsurf(s * EXs, EZs)
    f = (n + V((s * .30, .05, .04))).normalized(); t2 = f.cross(Z).normalized(); u2 = t2.cross(f).normalized()
    return p + f * .03, f, t2, u2

FM = ['rfur', 'gold', 'iris', 'cheek']
_I = dict(lu=58, ll=38, tilt=12, bp=14, bti=-6, ps=1.0, cz=0.0, jaw=0)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'lu': 101, 'll': 80, 'bp': 22},
    'mouth_open': {**_I, 'jaw': 30},
    'smile': {**_I, 'll': 66, 'lu': 56, 'tilt': 0, 'bp': 6, 'bti': 4, 'cz': .03, 'jaw': 9},
    'angry': {**_I, 'lu': 84, 'll': 50, 'tilt': 30, 'bp': 40, 'bti': -22, 'ps': .8, 'jaw': 14},
    'grin': {**_I, 'lu': 72, 'll': 76, 'tilt': 4, 'bp': 4, 'bti': 0, 'cz': .04, 'jaw': 22},
    'ult': {**_I, 'lu': 66, 'll': 46, 'tilt': 26, 'bp': 34, 'bti': -20, 'ps': .7, 'cz': .02, 'jaw': 40},
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
        cap(c, f, t, u, ER + .06, ER + .022, math.radians(e['lu']), False, math.radians(-s * e['tilt']))
        cap(c, f, t, u, ER + .055, ER + .02, math.radians(e['ll']), True, 0.0)
        fr = Matrix((t, f, u)).transposed(); ps = e['ps']
        v, f_, _ = ellv(c + f * (ER - .03), (.075 * ps, .05, .075 * ps), fr, 14); add(v, f_, 'iris')
        # heavy brow: red fur clumps along an arc over the eye, sweeping up and back
        for i in range(9):
            q = i / 4 - 1; ph = math.radians(e['bp'] + e['bti'] * q)
            dc = (u * math.cos(ph) + f * math.sin(ph) + t * (s * q * 1.05)).normalized(); base = c + dc * .27 + u * (.05 * max(0, q))
            v, f_ = clump_vf(base, -f * .55 + u * .40 + t * (s * .45 * (q + .4)), .26 - .04 * abs(q), .12, dc, .1); add(v, f_, 'rfur')
        # orange cheek ball with a black swirl on the nose bridge, between and just below the eyes
        p, n_, t_, u_ = hsurf(s * .20, -.05, .11)
        v, f_, sv = ellv(p + V((0, 0, e['cz'])), (.11, .11, .11), Matrix((t_, n_, u_)).transposed(), 16)
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
