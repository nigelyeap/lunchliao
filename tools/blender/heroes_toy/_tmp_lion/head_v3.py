# ---------------------------------------------------------------- head geometry (v3: Hok San style, built at v2 size then shrunk by HK)
HC = V((0, .17, 1.86)); HR = V((.80, .52, .52)); PE = 2.6        # superellipsoid head shell
JC = V((0, .23, 1.70)); JRO = V((.70, .48, .32)); JRI = V((.62, .41, .26))   # jaw bowl centre, outer and inner radii
JP = V((0, -.16, 1.70))                                          # jaw hinge
JAW0 = 10                                                        # rest pose jaw just parted so the teeth read
PAL = (.74, .50)                                                 # palate (mouth roof) radii around JC
HK = .76; HPV = V((0, .15, 1.95))                                # head shrink and its pivot, so the head sits inside the cloth frame
def HS(p): return HPV + (V(p) - HPV) * HK

# ---- painted linework: black cloud swirls on gold (face panels) and on orange (cheek balls) ----
def swirl(c, R, turns, s, a0=0.0, tail=1.0):
    N = max(12, int(28 * turns)); P = []
    for k in range(int(10 * tail), 0, -1):
        f = k / 10; a = a0 - s * f * 1.3; r = R * (1 + 1.1 * f); P.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    for k in range(N + 1):
        a = a0 + s * turns * 2 * math.pi * k / N; r = R * (1 - .85 * k / N); P.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return P

def line_image(name, bg, fg, curves, w, n=512):
    v, u = (np.mgrid[0:n, 0:n] + .5) / n; ink = np.zeros((n, n), bool)
    for P in curves:
        P = np.array(P); seg = np.linspace(0, len(P) - 1, len(P) * 4)
        xs = np.interp(seg, np.arange(len(P)), P[:, 0]); ys = np.interp(seg, np.arange(len(P)), P[:, 1])
        for x, y in zip(xs, ys):
            i0, i1 = max(0, int((y - w) * n) - 1), min(n, int((y + w) * n) + 2); j0, j1 = max(0, int((x - w) * n) - 1), min(n, int((x + w) * n) + 2)
            if i0 < i1 and j0 < j1: ink[i0:i1, j0:j1] |= (u[i0:i1, j0:j1] - x) ** 2 + (v[i0:i1, j0:j1] - y) ** 2 < w * w
    img = np.where(ink[..., None], np.array(H.srgb(fg)), np.array(H.srgb(bg)))
    a = np.concatenate([img, np.ones((n, n, 1))], axis=2).astype(np.float32)
    im = bpy.data.images.new(name, n, n, alpha=False); im.pixels.foreach_set(a.ravel())
    im.filepath_raw = os.path.join(WORK, name + '.png'); im.file_format = 'PNG'; im.save(); im.pack(); return im

def tex_mat(name, im, rough=.32, coat=.5):
    m = mat(name, '#FFFFFF', rough, coat=coat); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = im; nt.links.new(tx.outputs['Color'], b.inputs['Base Color']); return m

PU = (-.85, 1.30, 1.70)                                          # panel UV: x and z mapped into the square texture
def puv(p): return ((p.x - PU[0]) / PU[2], (p.z - PU[1]) / PU[2])

def panel_curves():
    C = []
    for j, z in enumerate(np.arange(1.36, 2.42, .17)):
        for x in np.arange(.10 + .085 * (j % 2), .86, .19):
            for s in (-1, 1):
                q = ((s * x - PU[0]) / PU[2], (z - PU[1]) / PU[2]); C.append(swirl(q, .036, 1.35, s, a0=(math.pi if s < 0 else 0) + .7 * j, tail=.8))
    return C
def cheek_curves():
    return [swirl((.5, .5), .2, 1.5, 1, a0=.4), swirl((.22, .78), .07, 1.2, -1, a0=2.0, tail=.6), swirl((.78, .24), .07, 1.2, -1, a0=5.0, tail=.6)]

M.update(rfur=mat('red_fur', '#D81E24', .88, sss=.1), bfur=mat('black_fur', '#181214', .92),
         iris=mat('iris', '#7A4A1E', .42), eyew=mat('eye_white', '#FFFDF8', .45))
M['panel'] = tex_mat('panel', line_image('lion_panel', '#F7C531', '#1A1210', panel_curves(), .0065))
M['cheek'] = tex_mat('cheek', line_image('lion_cheek', '#F48A22', '#1A1210', cheek_curves(), .022))

def ellp(name, c, r, m, seg=16, rot=None):
    vs, fs = sph_vf(seg, seg // 2); c = V(c); R = rot if rot is not None else Matrix.Identity(3)
    P = [c + R @ V((v.x * r[0], v.y * r[1], v.z * r[2])) for v in vs]
    return mk(name, P, fs, m, uvs=[[puv(P[i]) for i in f] for f in fs])

def shell_n(p):
    q = p - HC; return V(tuple(math.copysign(abs(q[i] / HR[i]) ** (PE - 1) / HR[i], q[i]) for i in range(3))).normalized()

def shell_pt(d):
    d = V(d).normalized(); s = sum(abs(d[i] / HR[i]) ** PE for i in range(3)) ** (-1 / PE); return HC + d * s

def hsurf(fx, fz, off=0.0):
    k = max(1e-5, 1 - abs(fx / HR.x) ** PE - abs(fz / HR.z) ** PE); p = HC + V((fx, HR.y * k ** (1 / PE), fz)); n = shell_n(p)
    t = n.cross(Z).normalized(); u = t.cross(n).normalized(); return p + n * off, n, t, u

def palate_r(p): return math.hypot(p.x / PAL[0], (p.y - JC.y) / PAL[1])

def build_shell():
    vs, fs = sph_vf(44, 22); P = []
    for v in vs:
        p = shell_pt(v)
        if p.z < JC.z:                                            # flatten the mouth roof inside the jaw so the jaw closes on it
            w = ss(1.05, .78, palate_r(p)); p.z += (JC.z + .004 - p.z) * w
        P.append(p)
    mi = []
    for f in fs:                                                  # red back and crown, painted gold panel on the face, pink mouth roof
        c = sum((P[i] for i in f), V()) / len(f)
        mi.append(1 if c.z < JC.z + .02 and palate_r(c) < .86 else 2 if shell_n(c).y > .3 and c.z < HC.z + .44 else 0)
    mk('h_shell', P, fs, [M['red'], M['mouth'], M['panel']], mat_idx=mi, uvs=[[puv(P[i]) for i in f] for f in fs])

def revolve(name, prof, c, mats, seg=40, mrun=None):
    """prof: list of (rx, ry, dz). First and last with rx==0 become poles. mrun: material index per profile segment."""
    c = V(c); vs = []; fs = []; mi = []; rings = []
    for rx, ry, dz in prof:
        if rx == 0: vs.append(c + V((0, 0, dz))); rings.append([len(vs) - 1] * seg)
        else:
            rings.append(list(range(len(vs), len(vs) + seg)))
            vs += [c + V((rx * math.cos(2 * math.pi * i / seg), ry * math.sin(2 * math.pi * i / seg), dz)) for i in range(seg)]
    for j in range(len(rings) - 1):
        a, b = rings[j], rings[j + 1]
        for i in range(seg):
            q = [a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]]; q = [x for k, x in enumerate(q) if x not in q[:k]]
            fs.append(tuple(q)); mi.append(mrun[j] if mrun else 0)
    return fix_normals(mk(name, vs, fs, mats, mat_idx=mi))

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
    revolve('j_jaw', prof, JC, [M['rfur'], M['gold'], M['mouth']], seg=40, mrun=mr)
    ell('j_tongue', JC + V((0, .05, -.09)), (.36, .27, .08), M['tongue'], seg=20)
    for k in range(9):                                            # lower teeth on the inner lip, fangs at the ends
        th = math.radians(36 + 108 * k / 8); big = k in (0, 8)
        p = JC + V((JRI.x * .97 * math.cos(th), JRI.y * .97 * math.sin(th), .03 + (.03 if big else 0)))
        ell('j_tooth', p, (.032, .024, .055 if big else .035), M['teeth'], seg=8)
    # the big red fur lower lip and chin: a fat lumpy roll round the jaw rim, chunky clumps hanging under it
    pts = []
    for i in range(26):
        a = math.radians(-14 + 208 * i / 25); pts.append((JC + V(((JRO.x + .04) * math.cos(a), (JRO.y + .05) * math.sin(a), -.01)), .105 + .02 * math.sin(i * 2.1)))
    for row, (dz, sc, r) in enumerate(((-.17, .92, .11), (-.29, .70, .1))):
        n = 9 - 2 * row
        for i in range(n):
            th = math.radians(18 + 144 * i / max(1, n - 1)); pts.append((JC + V((JRO.x * sc * math.cos(th), JRO.y * (.7 + .3 * sc) * math.sin(th) + .04, dz)), r))
    blobs('j_lipfur', pts, M['rfur'], voxel=.022, tris=1500)

def on_head(fx, fz, off=0.0): return hsurf(fx, fz, off)[0]

def build_head():
    build_shell(); build_jaw()
    for k in range(9):                                            # upper teeth hanging from the mouth roof
        th = math.radians(32 + 116 * k / 8); big = k in (0, 8)
        ell('h_tooth', JC + V((.60 * math.cos(th), .43 * math.sin(th), -.035 - (.02 if big else 0))), (.034, .026, .055 if big else .04), M['teeth'], seg=8)
    ul = [JC + V(((JRO.x + .03) * math.cos(math.radians(a)), (JRO.y + .015) * math.sin(math.radians(a)), .05 + .035 * math.sin(math.radians(a)) ** 4)) for a in np.linspace(-6, 186, 34)]
    sweep('h_lip', ul, .05, M['gold'], seg=7)
    # painted forehead column rising from the nose to the mirror, gold with black linework
    p, n, t, u = hsurf(0, .10); ellp('h_column', p + n * .0, (.15, .10, .24), M['panel'], seg=18)
    p, n, t, u = hsurf(0, -.08); NO = p + n * .05
    ellp('h_nose', NO, (.16, .11, .10), M['panel'], seg=18)
    for s in (-1, 1): ell('h_nostril', NO + V((s * .07, .09, -.035)), (.04, .025, .028), M['nostril'], seg=12)
    # forehead mirror in a thick red fur ring, red flower on the crown above it
    p, n, t, u = hsurf(0, .33); MC = p + n * .07
    ell('h_mirror', MC, (.10, .02, .10), M['mirror'], rot=frame_mat(t, n, u), seg=20)
    tor('h_mirror_rim', MC + n * .004, n, .105, .02, M['gold'], seg=28, rseg=5)
    fluff('h_mirror_fur', MC - n * .01, n, .16, .055, M['rfur'], bumps=11, seg=33, rseg=6, amp=.5)
    q = shell_pt((0, .42, 1)); qn = shell_n(q); FC = q + qn * .09
    for k in range(7):
        a = 2 * math.pi * k / 7; d = V((math.cos(a), 0, math.sin(a))); ell('h_petal', FC + d * .07 + V((0, .02, 0)), (.07, .04, .07), M['rfur'], seg=10)
    ell('h_flower', FC + V((0, .05, 0)), (.045, .04, .045), M['gold'], seg=12)
    # eyes: white globe, flat bronze iris dome (in the face mesh), set deep in a heavy red fur socket
    for s in (-1, 1):
        c, f, t, u = eye_frame(s)
        ell('h_eyeball', c, (ER, ER, ER), M['eyew'], seg=16)
        fluff('h_eyefur', c - f * .03, f, .205, .06, M['rfur'], bumps=9, seg=27, rseg=6, amp=.45)
    # black fur tufts under the eyes, round the cheek balls and at the nose sides
    pts = []
    for s in (-1, 1):
        for k, fx in enumerate((.10, .19, .29, .39, .49, .57)):
            pts.append((on_head(s * fx, -.10 - .035 * math.sin(k * 1.7) - (.04 if k > 3 else 0), .03), .065 + .012 * (k % 2)))
        pts.append((on_head(s * .13, -.20, .04), .06)); pts.append((on_head(s * .62, .00, .02), .06))
    blobs('h_blackfur', pts, M['bfur'], voxel=.02, tris=1100)
    # red fur: a thick rim round the whole face, big lobes on the top corners, and a ring round the back
    pts = []
    for i in range(30):
        a = math.radians(-24 + 228 * i / 29); d = V((math.cos(a), -.05, math.sin(a) * .95))
        q = shell_pt(d); pts.append((q + shell_n(q) * .05, .11 + .025 * math.sin(3.7 * i)))
    for s in (-1, 1):
        for d, r in (((.78, .1, .62), .17), ((.62, .25, .80), .15), ((.90, -.05, .40), .14), ((.45, .10, .92), .13)):
            q = shell_pt((s * d[0], d[1], d[2])); pts.append((q + shell_n(q) * .07, r))
    for i in range(20):
        a = 2 * math.pi * i / 20; d = V((math.cos(a) * .95, -.70, math.sin(a) * .85))
        q = shell_pt(d); pts.append((q + shell_n(q) * .02, .08 + .015 * math.sin(5 * a)))
    blobs('h_furring', pts, M['rfur'], voxel=.024, tris=2600)
    col = [shell_pt(V((math.cos(a) * .95, -.86, math.sin(a) * .85))) for a in np.linspace(0, 2 * math.pi, 33)]
    sweep('h_collar', [q + shell_n(q) * .01 for q in col], .03, M['gold'], seg=6, round_caps=False)

# ---------------------------------------------------------------- face (one mesh, keyed): lids, irises, brows, cheek balls
ER = .15; EXs, EZs = .31, .11
def eye_frame(s):
    p, n, t, u = hsurf(s * EXs, EZs)
    f = (n + V((0, .35, 0))).normalized(); t2 = f.cross(Z).normalized(); u2 = t2.cross(f).normalized()
    return p + f * .06, f, t2, u2

FM = ['rfur', 'gold', 'iris', 'cheek']
_I = dict(lu=62, ll=40, tilt=0, bp=12, bti=0, ps=1.0, cz=0.0, jaw=0)
EXPR = {
    'idle': _I,
    'blink': {**_I, 'lu': 101, 'll': 80, 'bp': 20},
    'mouth_open': {**_I, 'jaw': 30},
    'smile': {**_I, 'll': 64, 'lu': 56, 'bp': 6, 'cz': .03, 'jaw': 9},
    'angry': {**_I, 'lu': 86, 'll': 44, 'tilt': 26, 'bp': 42, 'bti': -18, 'ps': .85, 'jaw': 13},
    'grin': {**_I, 'lu': 76, 'll': 84, 'tilt': -8, 'bp': 2, 'bti': 4, 'cz': .04, 'jaw': 22},
    'ult': {**_I, 'lu': 40, 'll': 28, 'bp': -8, 'bti': 8, 'ps': .8, 'cz': .02, 'jaw': 40},
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
        cap(c, f, t, u, .172, .16, math.radians(e['lu']), False, math.radians(-s * e['tilt']))
        cap(c, f, t, u, .168, .156, math.radians(e['ll']), True, 0.0)
        fr = Matrix((t, f, u)).transposed(); ps = e['ps']
        v, f_, _ = ellv(c + f * (ER - .035), (.098 * ps, .05, .098 * ps), fr, 14); add(v, f_, 'iris')
        # heavy red fur brow: a lumpy tube arching over the eye, outer end swept up and out
        Q = [i / 6 - 1 for i in range(13)]; P = []
        for q in Q:
            ph = math.radians(e['bp'] + e['bti'] * q)
            P.append(c + (u * math.cos(ph) + f * math.sin(ph) + t * (s * q * 1.05)).normalized() * .24 + u * (.05 * max(0, q)))
        n = len(P); seg = 8; v = []
        for i in range(n):
            tan = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized(); out = (P[i] - c).normalized(); side = out.cross(tan).normalized(); nn = tan.cross(side).normalized()
            q = Q[i]; r = .11 * (1 + .3 * math.cos(5 * math.pi * q)) * (math.sin(math.pi * (q + 1) / 2) ** .35 if 0 < i < n - 1 else 0.0)
            v += [P[i] + (side * math.cos(a) + nn * math.sin(a)) * r for a in [2 * math.pi * k / seg for k in range(seg)]]
        f_ = [(i * seg + k, i * seg + (k + 1) % seg, (i + 1) * seg + (k + 1) % seg, (i + 1) * seg + k) for i in range(n - 1) for k in range(seg)]
        add(v, f_, 'rfur')
        # orange cheek ball with a black swirl, sitting forward under the inner eye (rises with smile and grin)
        p, n_, t_, u_ = hsurf(s * .25, -.06, .1)
        v, f_, sv = ellv(p + V((0, 0, e['cz'])), (.105, .105, .105), Matrix((t_, n_, u_)).transposed(), 16)
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

