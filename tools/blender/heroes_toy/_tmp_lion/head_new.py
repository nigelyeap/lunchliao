    ell('j_tongue', JC + V((0, .05, -.13)), (.34, .26, .07), M['tongue'], seg=24)
    for k in range(9):                                            # lower teeth on the inner lip, fangs at the ends
        th = math.radians(36 + 108 * k / 8); big = k in (0, 8)
        p = JC + V((JRI.x * .97 * math.cos(th), JRI.y * .97 * math.sin(th), .03 + (.03 if big else 0)))
        ell('j_tooth', p, (.032, .024, .055 if big else .035), M['teeth'], seg=8)
    # big fluffy lower lip: white fur roll round the jaw rim
    lp = [JC + V(((JRO.x + .02) * math.cos(math.radians(a)), (JRO.y + .02) * math.sin(math.radians(a)), .0)) for a in np.linspace(-8, 188, 44)]
    sweep('j_lipfur', lp, [.05 * (1 + .25 * abs(math.sin(i * 1.3))) for i in range(len(lp))], M['fur'], seg=7)
    # beard: long white fur hanging under the chin, rides the jaw
    pts = []
    for row, (dz, sc, r) in enumerate(((-.24, .86, .07), (-.32, .66, .075), (-.42, .44, .075), (-.52, .22, .07))):
        n = 11 - 2 * row
        for i in range(n):
            th = math.radians(14 + 152 * i / max(1, n - 1)); pts.append((JC + V((JRO.x * sc * math.cos(th), JRO.y * (.62 + .3 * sc) * math.sin(th) + .05, dz)), r))
    blobs('j_beard', pts, M['fur'], voxel=.02, tris=1100)

def on_head(fx, fz, off=0.0): return hsurf(fx, fz, off)[0]

def scroll(name, fx, fz, R, turns, s, m, r0=.02, rot=0.0):
    """Painted swirl: a flat spiral tube laid on the shell (raised paint line)."""
    N = int(14 * turns) + 4; pts = []
    for k in range(N + 1):
        a = rot + turns * 2 * math.pi * k / N; r = R * (1 - .8 * k / N)
        pts.append(on_head(fx + s * r * math.cos(a), fz + r * math.sin(a), .006))
    sweep(name, pts, list(np.linspace(r0, r0 * .45, len(pts))), m, seg=6)

def pompom(c, r, i):
    ell('h_pom', c, (r, r, r), M['pom%d' % (i % len(POMC))], seg=10)

def build_head():
    build_shell(); build_jaw()
    for k in range(9):                                            # upper teeth hanging from the mouth roof
        th = math.radians(32 + 116 * k / 8); big = k in (0, 8)
        ell('h_tooth', JC + V((.52 * math.cos(th), .36 * math.sin(th), -.035 - (.02 if big else 0))), (.034, .026, .055 if big else .04), M['teeth'], seg=8)
    # upper lip: a fat curved gold lip with a white fur fringe (Fut San curl)
    ul = [JC + V(((JRO.x + .03) * math.cos(math.radians(a)), (JRO.y + .015) * math.sin(math.radians(a)), .05 + .035 * math.sin(math.radians(a)) ** 4)) for a in np.linspace(-6, 186, 40)]
    sweep('h_lip', ul, .045, M['gold'], seg=8)
    sweep('h_lipfur', [q + V((0, .02, -.035)) for q in ul], [.032 * (1 + .3 * abs(math.sin(i * 1.7))) for i in range(len(ul))], M['fur'], seg=6)
    # nose: big gold ball, nostrils, a gold bridge up to the mirror
    p, n, t, u = hsurf(0, -.06); NO = p + n * .04
    ell('h_nose', NO, (.17, .12, .11), M['gold'], seg=20)
    for s in (-1, 1): ell('h_nostril', NO + V((s * .07, .095, -.035)), (.04, .025, .028), M['nostril'], seg=14)
    br = [hsurf(0, z, .012)[0] for z in (-.0, .07, .14, .2)]
    sweep('h_bridge', br, [.05, .04, .035, .03], M['gold'], seg=14)
    # big round forehead mirror, gold rim, black ring
    p, n, t, u = hsurf(0, .31)
    ell('h_mirror', p + n * .014, (.13, .02, .13), M['mirror'], rot=frame_mat(t, n, u), seg=24)
    tor('h_mirror_rim', p + n * .016, n, .135, .026, M['gold'], seg=40, rseg=8)
    tor('h_mirror_ring', p + n * .006, n, .175, .016, M['black'], seg=40, rseg=6)
    # painted scrolls: gold and green swirls on the cheeks and head sides, blue ones on the forehead
    for s in (-1, 1):
        scroll('h_scroll', s * .60, .14, .13, 1.4, s, M['gold'], r0=.022, rot=math.pi)
        scroll('h_scroll', s * .62, -.18, .10, 1.2, s, M['green'], r0=.02, rot=0)
        scroll('h_scroll', s * .22, .40, .07, 1.1, s, M['blue'], r0=.016, rot=-math.pi / 2)
        scroll('h_scroll', s * .45, .36, .08, 1.2, -s, M['green'], r0=.017, rot=math.pi / 2)
        tor('h_cheekring', on_head(s * .70, -.02, .006), shell_n(on_head(s * .70, -.02)), .07, .018, M['black'], seg=24, rseg=6)
    # single horn
    p, n, t, u = hsurf(0, .47)
    hp = catmull([p - n * .03, p + n * .06 + V((0, .02, .08)), p + V((0, .05, .2)), p + V((0, -.01, .3))], 5)
    sweep('h_horn', hp, list(np.linspace(.09, .04, len(hp))), M['gold'], seg=16)
    for k in (.25, .55):
        i = int(k * (len(hp) - 1)); tor('h_hornband', hp[i], hp[i + 1] - hp[i - 1], .09 - .048 * k + .004, .015, M['green'], seg=24, rseg=6)
    ell('h_horntip', hp[-1] + V((0, 0, .02)), (.06, .06, .06), M['pom0'], seg=14)
    crest = [shell_pt((0, math.cos(math.radians(a)), math.sin(math.radians(a)))) for a in (75, 90, 105, 120, 135, 150)]
    sweep('h_crest', [q + shell_n(q) * .008 for q in crest], .035, M['gold'], seg=12)
    # pom-poms: a crown over the top, round the horn, down the sides
    i = 0
    for b in (-62, -48, -34, -20, 20, 34, 48, 62):
        q = shell_pt((math.sin(math.radians(b)) * 1.3, .30, math.cos(math.radians(b)))); pompom(q + shell_n(q) * .045, .065, i); i += 1
    for b in (-55, -30, 0, 30, 55):
        q = shell_pt((math.sin(math.radians(b)) * 1.3, -.25, math.cos(math.radians(b)))); pompom(q + shell_n(q) * .045, .06, i + 2); i += 1
    for s in (-1, 1):
        for k, z in enumerate((.2, .0, -.2)):
            q = shell_pt((s, .15, z)); pompom(q + shell_n(q) * .045, .058, i + k * 2 + (s > 0)); 
    for s in (-1, 1):
        for k in range(3): pompom(hp[2 + k * 2] + V((s * (.08 - .01 * k), .02, 0)), .04, k + (s > 0) * 3)
    # ears: gold with green inner and a fur edge, set on the top corners, a pom on the tip
    for s in (-1, 1):
        q = shell_pt((s * .80, -.15, .70)); nn = shell_n(q); c = q + nn * .05
        R = (Matrix.Rotation(math.radians(-s * 32), 3, 'Y'))
        ell('h_ear', c, (.10, .055, .16), M['gold'], rot=R, seg=18)
        ell('h_earin', c + V((0, .04, .01)), (.06, .025, .11), M['green'], rot=R, seg=16)
        pompom(c + R @ V((0, 0, .17)), .055, 3 + s)
    # eye sockets: gold rings the eyes sit in
    for s in (-1, 1):
        c, f, t, u = eye_frame(s); tor('h_socket', c - f * .07, f, .165, .03, M['gold'], seg=30, rseg=6)
        ell('h_eyeball', c, (ER, ER, ER), M['eyew'], seg=20)
    # fur mane: a thick white halo round the face edge, and a ring round the back rim
    pts = []
    for i in range(34):
        a = math.radians(-28 + 236 * i / 33); d = V((math.cos(a), -.02, math.sin(a) * .95))
        q = shell_pt(d); pts.append((q + shell_n(q) * .035, .085 + .02 * math.sin(4.3 * i)))
    for i in range(24):
        a = 2 * math.pi * i / 24; d = V((math.cos(a) * .95, -.70, math.sin(a) * .85))
        q = shell_pt(d); pts.append((q + shell_n(q) * .02, .07 + .012 * math.sin(5 * a)))
    blobs('h_furring', pts, M['fur'], voxel=.022, tris=2200)
    # gilded collar band behind the fur at the back opening
    col = [shell_pt(V((math.cos(a) * .95, -.86, math.sin(a) * .85))) for a in np.linspace(0, 2 * math.pi, 33)]
    sweep('h_collar', [q + shell_n(q) * .01 for q in col], .03, M['gold'], seg=6, round_caps=False)

