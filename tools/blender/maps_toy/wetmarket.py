"""Pasar Lorong Tiga (wetmarket), toy playset look.
Run: /opt/homebrew/bin/blender -b -P tools/blender/maps_toy/wetmarket.py [-- preview]
Builds from layouts/wetmarket_expanded.json and layouts/wetmarket_solids_v2.json (Update 3 layout), checks every v2 collider against the visual
geometry, exports assets/maps/wetmarket.glb and renders shots/maps_toy/wetmarket/*.png.
Builders take game coordinates (x, y up, z). Geometry is stored in Blender space: (x, -z, y)."""
import bpy, sys, os, math, json, random, subprocess, shutil
from itertools import product
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
TEX = os.path.join(ROOT, 'assets', 'maps', 'wetmarket_tex')
SHOTS = os.path.join(ROOT, 'shots', 'maps_toy', 'wetmarket')
GLB = os.path.join(ROOT, 'assets', 'maps', 'wetmarket.glb')
PREVIEW = 'preview' in sys.argv
os.makedirs(SHOTS, exist_ok=True)
if not PREVIEW or not os.path.exists(os.path.join(TEX, 'nosmoke.png')):
    subprocess.run([shutil.which('python3') or 'python3', os.path.join(HERE, 'wetmarket_tex.py'), TEX], check=True)

X = json.load(open(os.path.join(HERE, 'layouts', 'wetmarket_expanded.json')))
SOLIDS = json.load(open(os.path.join(HERE, 'layouts', 'wetmarket_solids_v2.json')))
SUN = json.load(open(os.path.join(HERE, 'layouts', 'wetmarket.json')))['look']['sun'][2]     # the old look block gives the sun direction only
BOXES = [b + [0, 's'][len(b) - 6:] for b in X['boxes']]      # x,z,w,d,h,col,y0,flags


def _aabb(b): return [b[0] - b[2] / 2, b[6], b[1] - b[3] / 2, b[0] + b[2] / 2, b[6] + b[4], b[1] + b[3] / 2]


def _same(a, s): return all(abs(a[i] - s[i]) <= .02 for i in range(6))


_used = set(); _keep = []
for b in BOXES:                                     # Update 3: a collider box that is not in v2 was removed
    if 'v' in b[7] and 'i' not in b[7]: _keep.append(b); continue
    hit = [i for i, s in enumerate(SOLIDS) if _same(_aabb(b), s)]
    if hit: _used.update(hit); _keep.append(b)
print('LAYOUT v2: %d old boxes dropped' % (len(BOXES) - len(_keep)))
BOXES = _keep
ROOF_Y = 6.4
rnd = random.Random(7)
PI = math.pi

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene

# ------------------------------------------------------------------ materials (flat toy colours, a few clean prints)
MAT = dict(      # name: (hex, rough, metal, coat, extras)
    floor=('#b8927a', .3, 0, .3, dict(tex='floor.png', uv=1.2)),
    ground=('#a09482', .8, 0, 0, {}),
    tile_white=('#3f93c4', .22, 0, .5, dict(tex='tile_white.png', uv=.4)),
    tile_green=('#2fa37e', .22, 0, .5, dict(tex='tile_green.png', uv=.4)),
    wall=('#a8a59b', .55, 0, 0, {}),
    wall_mint=('#a8a59b', .5, 0, 0, {}),
    trim=('#d9583a', .3, 0, .4, {}),
    cap=('#e07b39', .45, 0, 0, {}),
    glass=('#fff0cf', .2, 0, .3, dict(emit=('#ffd98a', .9))),
    roof=('#71a89f', .5, 0, 0, dict(tex='zinc.png', uv=1.0)),
    skylight=('#fff3d6', .3, 0, 0, dict(emit=('#ffe9bd', 1.6))),
    nosmoke=('#ffffff', .35, 0, .4, dict(tex='nosmoke.png', raw_uv=True)),
    chicken=('#f3dfae', .3, 0, .6, {}), meat=('#d9605a', .3, 0, .6, {}), fat=('#f7e9e0', .3, 0, .6, {}), comb=('#d8362f', .3, 0, .5, {}),
    styro_lid=('#e2e8e6', .6, 0, 0, {}), strap=('#2f6fb0', .4, 0, .2, {}),
    steel=('#d5d9de', .25, 1, 0, {}),
    steel_dark=('#9a9890', .4, 0, 0, {}),
    canopy=('#3fa57c', .4, 0, .3, {}),
    canopy_tan=('#e8a83a', .4, 0, .3, {}),
    concrete=('#b0aca2', .7, 0, 0, {}),
    hazard=('#f2c230', .4, 0, .2, dict(tex='hazard.png', uv=.6)),
    shutter=('#d9583a', .35, 0, 0, {}),
    ice=('#eef6f7', .15, 0, .8, {}),
    fish_a=('#a9bccb', .2, 0, 1, {}), fish_b=('#7f9bb3', .2, 0, 1, {}), fish_c=('#ee8f86', .2, 0, 1, {}), fish_d=('#f2c66a', .2, 0, 1, {}),
    eye=('#1a1214', .08, 0, 1, {}),
    white=('#fbf8f0', .3, 0, .3, {}),
    red=('#d8362f', .3, 0, .5, {}), yellow=('#e9c45a', .3, 0, .5, {}), orange=('#ee7b2e', .35, 0, .4, {}), blue=('#2f6fb0', .35, 0, .4, {}),
    green=('#4fa04a', .4, 0, .3, {}), green_d=('#2f7d4f', .4, 0, .3, {}), leaf=('#3f8f45', .45, 0, .2, {}),
    purple=('#7c4a9c', .35, 0, .4, {}), tomato=('#e2463a', .3, 0, .5, {}), brown=('#8a5a2b', .5, 0, 0, {}),
    egg=('#f3dcc0', .35, 0, .3, {}), tray_grey=('#aab0b5', .5, 0, 0, {}), tray_blue=('#5aa6d6', .4, 0, .3, {}),
    sack=('#cdb48a', .7, 0, 0, {}), kopi=('#5a3216', .3, 0, .4, {}), terracotta=('#c5673f', .5, 0, .2, {}),
    carton=('#c9a272', .65, 0, 0, {}), carton_d=('#b98a5a', .65, 0, 0, {}), styro=('#f6f6f2', .6, 0, 0, {}),
    marble=('#e9c9a0', .2, 0, .6, {}), stool_a=('#d98a8a', .35, 0, .5, {}), stool_b=('#a6d6be', .35, 0, .5, {}),
    pink=('#e86a9a', .35, 0, .4, {}), soil=('#5a4030', .8, 0, 0, {}),
    lamp_in=('#fff6dc', .4, 0, 0, dict(emit=('#fff1c9', 1.2))),
    bulb=('#fff6dc', .3, 0, 0, dict(emit=('#fff1c9', 6))),
    tube=('#fffbea', .3, 0, 0, dict(emit=('#fffbea', 5))),
    puddle=('#4f86a8', .04, 0, 1, dict(alpha=.45)),
    sign=('#ffffff', .35, 0, .4, dict(tex='signs.png', raw_uv=True)),
    sign_frame=('#2b3136', .4, 0, .3, {}),
    grate=('#4a4f55', .5, .8, 0, {}),
    hdb_a=('#85c7a6', .7, 0, 0, {}), hdb_b=('#f0a39a', .7, 0, 0, {}), hdb_band=('#f3d998', .7, 0, 0, {}),
)


def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4) for v in c]


def make_mat(name):
    hx, rough, metal, coat, ex = MAT[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(hx), 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .08
    if ex.get('tex'):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(TEX, ex['tex']))
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if ex.get('emit'):
        b.inputs['Emission Color'].default_value = (*srgb(ex['emit'][0]), 1); b.inputs['Emission Strength'].default_value = ex['emit'][1]
    if ex.get('alpha'):
        b.inputs['Alpha'].default_value = ex['alpha']
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    return m


def flat(hexcol):
    """material for a raw map colour that has no named material"""
    n = 'c_' + hexcol.lstrip('#').lower()
    if n not in MAT: MAT[n] = (hexcol, .45, 0, .2, {})
    return n


# ------------------------------------------------------------------ geometry buffers, merged by (object, material)
BUF = {}        # (obj, mat) -> [verts, faces, uvs]
CHK = []        # verts since mark(), for the collider check
COVER = []      # visual AABBs in game coords [minx,miny,minz,maxx,maxy,maxz]
OBJ = ['MAP']   # current target object
ORIGIN = {}     # object name -> blender-space origin


def emit(m, vs, fs, M=None, uv=None, flip=False):
    b = BUF.setdefault((OBJ[0], m), [[], [], []]); n = len(b[0])
    w = [tuple(M @ Vector(v)) for v in vs] if M is not None else [tuple(v) for v in vs]
    b[0].extend(w); CHK.extend(w)
    b[1].extend([tuple(i + n for i in (reversed(f) if flip else f)) for f in fs])
    b[2].extend(uv if uv else [None] * len(fs))


def mark(): CHK.clear()


def done():
    xs = [v[0] for v in CHK]; ys = [v[1] for v in CHK]; zs = [v[2] for v in CHK]
    COVER.append([min(xs), min(zs), -max(ys), max(xs), max(zs), -min(ys)])


def T(x, y, z, ry=0.0):
    return Matrix.Translation((x, -z, y)) @ Matrix.Rotation(ry, 4, 'Z')


def box_vf(w, d, h, b):
    hs = (w / 2, d / 2, h / 2); b = min(b, hs[0] * .49, hs[1] * .49, hs[2] * .49)
    vs = []; idx = {}
    for a in range(3):
        for s in product((-1, 1), repeat=3):
            p = [s[i] * (hs[i] - b) for i in range(3)]; p[a] = s[a] * hs[a]
            idx[(a, s)] = len(vs); vs.append(tuple(p))
    fs = []
    for a in range(3):
        o = [i for i in range(3) if i != a]
        for sa in (-1, 1):
            q = []
            for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                s = [0, 0, 0]; s[a] = sa; s[o[0]] = u; s[o[1]] = v; q.append(idx[(a, tuple(s))])
            fs.append(q)
    for a, c, e in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
        for sa in (-1, 1):
            for sc in (-1, 1):
                s1 = [0, 0, 0]; s1[a] = sa; s1[c] = sc; s1[e] = -1; s2 = list(s1); s2[e] = 1
                fs.append([idx[(a, tuple(s1))], idx[(a, tuple(s2))], idx[(c, tuple(s2))], idx[(c, tuple(s1))]])
    for s in product((-1, 1), repeat=3): fs.append([idx[(0, s)], idx[(1, s)], idx[(2, s)]])
    out = []
    for f in fs:                                            # convex: point every face outward
        p = [Vector(vs[i]) for i in f[:3]]; n = (p[1] - p[0]).cross(p[2] - p[0])
        out.append(f if n.dot(p[0] + p[1] + p[2]) > 0 else f[::-1])
    return vs, out


def box(m, x, z, w, d, y0, h, b=.03, ry=0.0, M=None):
    vs, fs = box_vf(w, d, h, b)
    emit(m, vs, fs, (M if M is not None else T(x, y0 + h / 2, z, ry)))


def lathe_vf(prof, seg=16):
    """prof: (radius, height) pairs from bottom to top. radius 0 closes the end."""
    vs = []; rings = []
    for r, y in prof:
        if r < 1e-6: rings.append([len(vs)]); vs.append((0, 0, y))
        else:
            rings.append(list(range(len(vs), len(vs) + seg)))
            vs += [(r * math.cos(2 * PI * i / seg), r * math.sin(2 * PI * i / seg), y) for i in range(seg)]
    fs = []
    for a, c in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            if len(a) == 1 and len(c) == 1: continue
            if len(a) == 1: fs.append([a[0], c[j], c[i]])
            elif len(c) == 1: fs.append([a[i], a[j], c[0]])
            else: fs.append([a[i], a[j], c[j], c[i]])
    return vs, fs


def lathe(m, x, y, z, prof, seg=16, M=None, flip=False):
    vs, fs = lathe_vf(prof, seg); emit(m, vs, fs, M if M is not None else T(x, y, z), flip=flip)


def ball_prof(n=4):
    return [(math.sin(PI * i / n), -math.cos(PI * i / n)) for i in range(n + 1)]


def blob(m, x, y, z, rx, ry_, rz, seg=8, n=4, M=None):
    """ellipsoid centred at game (x,y,z) with radii along game x, y(up), z"""
    S = Matrix.Diagonal((rx, rz, ry_, 1))
    lathe(m, 0, 0, 0, ball_prof(n), seg, (M if M is not None else T(x, y, z)) @ S)


def rprism(m, x, z, w, d, y0, h, rad=.1, b=.02, ry=0.0, n=4):
    """rounded-rectangle slab with chamfered top and bottom edges"""
    def ring(inset, y):
        pts = []; r = max(rad - inset, .002)
        for k, (sx, sz) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
            for i in range(n + 1):
                a = k * PI / 2 + PI / 2 * i / n
                pts.append((sx * (w / 2 - rad) + r * math.cos(a), sz * (d / 2 - rad) + r * math.sin(a), y))
        return pts
    b = min(b, h * .49); rs = [ring(b, 0), ring(0, b), ring(0, h - b), ring(b, h)]; k = len(rs[0])
    vs = [p for r in rs for p in r]; fs = [list(range(k))[::-1], list(range(3 * k, 4 * k))]
    for a in range(3):
        for i in range(k):
            j = (i + 1) % k; fs.append([a * k + i, a * k + j, (a + 1) * k + j, (a + 1) * k + i])
    emit(m, vs, fs, T(x, y0, z, ry))


def cyl(m, x, z, r, y0, h, seg=12, b=.01, r2=None):
    r2 = r if r2 is None else r2
    lathe(m, x, y0, z, [(0, 0), (r - b, 0), (r, b), (r2, h - b), (r2 - b, h), (0, h)], seg)


# ------------------------------------------------------------------ lookups
def inside(px, pz, b, pad=0.0):
    return abs(px - b[0]) <= b[2] / 2 + pad and abs(pz - b[1]) <= b[3] / 2 + pad


CANOPY = [b for b in BOXES if 'v' in b[7] and b[6] > 3 and b[4] <= .15]


def canopy_over(px, pz, pad=0.0):
    for b in CANOPY:
        if inside(px, pz, b, pad): return b[6]
    return None


def solid_at(px, py, pz):
    return any(s[0] <= px <= s[3] and s[1] <= py <= s[4] and s[2] <= pz <= s[5] for s in SOLIDS)


SIGN_KIND = {1: 'fish', 12: 'fish', 2: 'veg', 3: 'ayam', 4: 'tofu', 5: 'spice', 7: 'kopi', 11: 'dry'}


def stall_kind(x, z, w):
    best = None
    for p in X['signs']['place']:
        if p['row'] in SIGN_KIND and abs(p['x'] - x) < w / 2 + 1 and abs(p['z'] - z) < 1.7:
            dd = abs(p['x'] - x) + abs(p['z'] - z)
            if best is None or dd < best[0]: best = (dd, SIGN_KIND[p['row']])
    return best[1] if best else 'veg'


# ------------------------------------------------------------------ props and goods
FISH = ['fish_a', 'fish_b', 'fish_a', 'fish_c', 'fish_d']


def fish(x, y, z, ry, L=.5, m=None):
    m = m or rnd.choice(FISH); M = T(x, y, z, ry)
    prof = [(0, -1), (.55, -.78), (.9, -.35), (1, .05), (.8, .5), (.4, .85), (.16, 1)]
    vs, fs = lathe_vf(prof, 8)
    emit(m, vs, fs, M @ Matrix.Diagonal((L / 2, L * .17, L * .085, 1)) @ Matrix.Rotation(-PI / 2, 4, 'Y'))
    vs, fs = box_vf(L * .24, L * .24, L * .035, .004)
    emit(m, vs, fs, M @ Matrix.Translation((-L * .56, 0, 0)) @ Matrix.Rotation(PI / 4, 4, 'Z'))
    lathe('eye', 0, 0, 0, [(1, 0), (.8, .6), (0, 1)], 6, M @ Matrix.Translation((L * .3, L * .03, L * .06)) @ Matrix.Diagonal((L * .035,) * 3 + (1,)))


def tray(m, x, z, w, d, y, ry):
    box(m, 0, 0, w, d, 0, .05, .012, M=T(x, y + .025, z, ry))


def goods(kind, x, z, w, d, top):
    """low goods on a counter top (all under 0.22 m, inside the footprint)"""
    ax = w >= d; L = max(w, d); dp = min(w, d); n = max(1, int(L / .95)); step = L / n
    for i in range(n):
        o = -L / 2 + step * (i + .5); cx, cz = (x + o, z) if ax else (x, z + o); ry = 0 if ax else PI / 2
        tw, td = step - .16, dp - .2; M = T(cx, top, cz, ry)
        P = lambda lx, lz: (M @ Vector((lx, -lz, 0)))          # local tray point -> blender
        def at(lx, lz): p = P(lx, lz); return p.x, -p.y
        k = kind if kind != 'veg' else rnd.choice(['veg_g', 'veg_r', 'veg_p', 'veg_o'])
        if k == 'fish':
            tray('steel', cx, cz, tw, td, top, ry); box('ice', 0, 0, tw - .06, td - .06, 0, .07, .02, M=T(cx, top + .075, cz, ry))
            for j in (-1, 1):
                a, c = at(j * tw * .22 + rnd.uniform(-.03, .03), rnd.uniform(-.03, .03)); fish(a, top + .135, c, ry + PI / 2 + rnd.uniform(-.35, .35), min(.42, td * .8))
        elif k.startswith('veg'):
            tray({'veg_g': 'green_d', 'veg_r': 'yellow', 'veg_p': 'tray_blue', 'veg_o': 'green_d'}[k], cx, cz, tw, td, top, ry)
            m = {'veg_g': 'green', 'veg_r': 'tomato', 'veg_p': 'purple', 'veg_o': 'orange'}[k]
            for u in (-1, 0, 1):
                for v in (-1, 1):
                    a, c = at(u * tw * .3, v * td * .22)
                    if k == 'veg_p': blob(m, a, top + .1, c, .05, .05, .11, 6, 3, M=T(a, top + .1, c, ry))
                    else: blob(m, a, top + .12, c, .09, .08, .09, 6, 3)
        elif k == 'ayam':
            tray('steel', cx, cz, tw, td, top, ry)
            for u in (-1, 1):
                a, c = at(u * tw * .24, 0); blob('chicken', a, top + .12, c, .15, .08, .11, 8, 4, M=T(a, top + .12, c, ry))
                a, c = at(u * tw * .24 + .15, 0); blob('chicken', a, top + .1, c, .05, .04, .04, 6, 3)
        elif k == 'egg':
            tray('tray_grey', cx, cz, tw, td, top, ry)
            for u in range(4):
                for v in range(3):
                    a, c = at((u - 1.5) * tw * .21, (v - 1) * td * .27); blob('egg' if (u + v) % 3 else 'white', a, top + .1, c, .04, .055, .04, 6, 3)
        elif k == 'tofu':
            tray('tray_blue', cx, cz, tw, td, top, ry)
            for u in (-1, 0, 1):
                for v in (-1, 1):
                    a, c = at(u * tw * .29, v * td * .22); box('white', a, c, .16, .16, top + .05, .09, .02, ry)
        elif k == 'spice':
            for u in (-1, 1):
                a, c = at(u * tw * .26, 0)
                lathe('steel', a, top, c, [(0, 0), (.1, 0), (.17, .09), (.16, .1), (0, .08)], 12)
                lathe(rnd.choice(['red', 'yellow', 'orange', 'brown']), a, top + .08, c, [(0, 0), (.15, 0), (.07, .08), (0, .11)], 10)
        elif k == 'kopi':
            tray('brown', cx, cz, tw, td, top, ry)
            for u in (-1, 0, 1):
                a, c = at(u * tw * .28, 0)
                lathe('white', a, top + .05, c, [(0, 0), (.04, 0), (.055, .1), (0, .1)], 10)
                lathe('kopi', a, top + .145, c, [(0, 0), (.048, 0), (0, .006)], 10)
        elif k == 'dry':
            for u in (-1, 1):
                a, c = at(u * tw * .26, 0)
                lathe('sack', a, top, c, [(0, 0), (.15, 0), (.19, .08), (.17, .16), (0, .15)], 10)
                lathe(rnd.choice(['brown', 'white', 'red', 'yellow']), a, top + .14, c, [(0, 0), (.16, 0), (.08, .05), (0, .07)], 10)


def counter(x, z, w, d, y0, h):
    mark(); box('tile_white', x, z, w, d, y0, h - .08, .03); box('steel', x, z, w, d, y0 + h - .08, .08, .025); done()
    goods(stall_kind(x, z, max(w, d)), x, z, w, d, y0 + h)


def plate(i, x, y, z, ry, s=.3):
    """square stall number plate from the sign atlas (cells 13..15), facing game +z at ry=0"""
    c = 13 + (i % 12) // 4; u0 = (c % 2) * .5 + (i % 4) * .125; v1 = 1 - (c // 2) / 8; M = T(x, y, z, ry)
    emit('sign', [(-s / 2, 0, -s / 2), (s / 2, 0, -s / 2), (s / 2, 0, s / 2), (-s / 2, 0, s / 2)], [(0, 1, 2, 3)], M,
         uv=[[(u0, v1 - .125), (u0 + .125, v1 - .125), (u0 + .125, v1), (u0, v1)]])


def nosmoke(x, y, z, ry, s=.6):
    M = T(x, y, z, ry)
    emit('nosmoke', [(-s / 2, 0, -s / 2), (s / 2, 0, -s / 2), (s / 2, 0, s / 2), (-s / 2, 0, s / 2)], [(0, 1, 2, 3)], M, uv=[[(0, 0), (1, 0), (1, 1), (0, 1)]])


def rail(x, z, w, kind):
    """REF 2.4: meat hung openly on a hook rail over the counter. Rail at 2.5 m, lowest point about 1.95 m, over the counter footprint only."""
    y = 2.5; box('steel_dark', x, z, w - .3, .04, y, .04, .01)
    for s in (-1, 1): box('steel_dark', x + s * (w / 2 - .25), z, .025, .025, y + .04, ROOF_Y - y - .04, .004)
    n = max(1, int((w - .8) / .5))
    for i in range(n):
        hx = x - (n - 1) * .25 + i * .5; box('steel', hx, z, .012, .012, y - .12, .12, .003)
        if kind == 'ayam':
            blob('chicken', hx, y - .34, z, .1, .2, .085, 8, 4); blob('chicken', hx, y - .58, z, .035, .07, .035, 6, 3); blob('comb', hx, y - .65, z, .03, .03, .02, 6, 3)
        else:
            box('meat', hx, z, .2, .07, y - .52, .4, .03); box('fat', hx, z, .205, .074, y - .34, .06, .01)


def shutter_unit(s):
    """Update 3: closed stall unit, static. Tiled piers, rolled-down shutter on both long faces, fascia with the unit number."""
    x, z = (s[0] + s[3]) / 2, (s[2] + s[5]) / 2; w, d, h = s[3] - s[0], s[5] - s[2], s[4]
    mark(); box('tile_green', x, z, w, d, 0, .22, .03)
    for e in (-1, 1): box('tile_white', x + e * (w / 2 - .14), z, .28, d, .22, h - .62, .03)
    box('wall', x, z, w - .5, d - .14, .22, h - .62, .01); box('trim', x, z, w, d, h - .4, .4, .04); done()
    n = 12; sh = (h - .62) / n
    for e in (-1, 1):
        for i in range(n): box('shutter', x, z + e * (d / 2 - .045), w - .56, .06, .22 + i * sh, sh, .022)
        box('steel_dark', x, z + e * (d / 2 - .02), .5, .03, .24, .07, .01)                      # pull handle
        box('yellow', x + .5, z + e * (d / 2 - .015), .08, .03, .25, .1, .012)                   # padlock
        plate(SHUT.setdefault(id(s), len(SHUT)) * 2 + (e > 0), x, h - .2, z + e * (d / 2 + .006), 0 if e > 0 else PI, .3)


SHUT = {}


def icebox(s, k):
    """Update 3: polystyrene fish boxes on a pallet (REF 2.5 and 2.11). The top box of one stack is open: fish on ice."""
    x, z = (s[0] + s[3]) / 2, (s[2] + s[5]) / 2; w, h = s[3] - s[0], s[4]; lh = (h - .12) / 3; q = w / 2
    mark(); box('tray_blue', x, z, w, w, 0, .12, .03)
    for i, (ex, ez) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        for j in range(3):
            y0 = .12 + j * lh; bx, bz = x + ex * q / 2, z + ez * q / 2
            box('styro', bx, bz, q, q, y0, lh - .06, .04); box('styro_lid', bx, bz, q, q, y0 + lh - .06, .06, .02)
            box('strap' if (i + j + k) % 2 else 'red', bx, bz, .07, q + .006, y0 + .01, lh - .02, .01)
    done()
    bx, bz = x - q / 2, z + q / 2 * (1 if k % 2 else -1)
    box('ice', bx, bz, q - .1, q - .1, h, .05, .02)
    for j in (-1, 1): fish(bx + j * .1, h + .085, bz, PI / 2 + j * .3, .4)


def icetable(p):
    x, z, ry = p['x'], p['z'], p.get('ry', 0); W, D = p.get('w', 3), p.get('d', 1.4)
    mark(); box('tile_white', x, z, W, D, 0, .8, .03, ry); box('steel', x, z, W, D, .8, .12, .03, ry)
    box('ice', x, z, W - .14, D - .14, .9, .12, .04, ry); done()
    M = T(x, 0, z, ry)
    for i in range(int(W / .42)):
        p2 = M @ Vector((-W / 2 + .35 + i * .42 + rnd.uniform(-.04, .04), rnd.uniform(-.12, .12), 0))
        fish(p2.x, 1.065, -p2.y, ry + PI / 2 + rnd.uniform(-.4, .4), rnd.uniform(.5, .62))
    p2 = M @ Vector((-W / 2 + .45, 0, 0)); sx, sz = p2.x, -p2.y            # hanging scale over the table
    box('steel_dark', sx, sz, .016, .016, 2.12, ROOF_Y - 2.12, .002)
    lathe('white', 0, 0, 0, [(0, -.04), (.15, -.04), (.16, 0), (.15, .04), (0, .04)], 14, T(sx, 1.97, sz, ry) @ Matrix.Rotation(PI / 2, 4, 'X'))
    box('red', 0, 0, .02, .012, 0, .11, .003, M=T(sx, 1.99, sz, ry) @ Matrix.Translation((0, -.045, 0)))
    box('steel_dark', sx, sz, .012, .012, 1.66, .16, .002)
    lathe('steel', sx, 1.6, sz, [(0, 0), (.15, 0), (.22, .06), (.21, .07), (0, .03)], 14)
    p2 = M @ Vector((W / 2 - .4, D / 2 - .2, 0))                           # price card
    box('white', p2.x, -p2.y, .34, .02, 1.02, .2, .008, ry)


def crates(p):
    x, z = p['x'], p['z']; mark()
    for i, dx in enumerate((-.3, .3)):
        for j in range(3):
            m = flat(p['c']) if p.get('c') else ('blue' if (i + j + int(abs(x))) % 3 == 0 else 'orange')
            box(m, x + dx, z, .58, .78, j * .34, .34, .035)
            for sz in (-1, 1): box('sign_frame', x + dx, z + sz * .385, .2, .02, j * .34 + .2, .06, .008)
    done()
    for dx in (-.3, .3):
        m = rnd.choice(['green', 'tomato', 'orange', 'purple'])
        for u in (-1, 1):
            for v in (-1, 0, 1): blob(m, x + dx + u * .13, 1.03, z + v * .22, .11, .08, .11, 6, 3)


def bin_(p):
    x, z = p['x'], p['z']; mark()
    lathe('green_d', x, 0, z, [(0, 0), (.25, 0), (.27, .02), (.3, .78), (0, .78)], 14)
    lathe('green', x, .78, z, [(.31, 0), (.31, .06), (.27, .1), (0, .1)], 14); done()
    box('white', x, z + .285, .3, .02, .45, .12, .006)


def plant(p):
    x, z = p['x'], p['z']; mark()
    lathe('terracotta', x, 0, z, [(0, 0), (.22, 0), (.24, .02), (.3, .47), (.32, .49), (.32, .55), (.27, .55)], 14)
    lathe('soil', x, .5, z, [(.28, 0), (0, .02)], 14); done()
    for k in range(6):
        a = k / 6 * 2 * PI + rnd.uniform(-.2, .2); t = rnd.uniform(.3, .6); L = rnd.uniform(.45, .62)
        M = T(x, .52, z, a) @ Matrix.Rotation(t, 4, 'Y') @ Matrix.Translation((0, 0, L)) @ Matrix.Diagonal((.1, .035, L, 1))
        lathe(rnd.choice(['leaf', 'green', 'green_d']), 0, 0, 0, ball_prof(4), 6, M)


def table(p):
    x, z = p['x'], p['z']; mark()
    rprism('marble', x, z, 1.5, 1.5, .78, .08, .16, .02); rprism('steel_dark', x, z, 1.44, 1.44, .72, .06, .14, .01)
    cyl('steel_dark', x, z, .1, .04, .68, 12); rprism('steel_dark', x, z, .8, .8, 0, .05, .2, .015); done()
    for k in range(4):
        a = k * PI / 2 + PI / 4; sx, sz = x + math.cos(a) * 1.25, z + math.sin(a) * 1.25; m = ('stool_a', 'stool_b')[k % 2]
        mark(); rprism(m, sx, sz, .48, .48, .36, .08, .1, .02); rprism(m, sx, sz, .4, .4, 0, .36, .08, .01); done()


def lamp(p):
    x, z, y = p['x'], p['z'], p.get('y', 3.2)
    for s in X['signs']['place']:                         # a lamp that would poke through a signboard is left out
        along = abs(math.cos(s.get('ry', 0)))
        if abs(s['y'] - y) < s['h'] / 2 + .2 and ((along > .5 and abs(s['z'] - z) < .4 and abs(s['x'] - x) < s['w'] / 2 + .35) or
                                                   (along <= .5 and abs(s['x'] - x) < .4 and abs(s['z'] - z) < s['w'] / 2 + .35)): return
    m = flat(p['c']) if p.get('c') else 'red'; top = canopy_over(x, z) or ROOF_Y
    prof = [(.3, -.12), (.31, -.1), (.13, .1), (.1, .14), (0, .14)]
    lathe(m, x, y, z, prof, 14); lathe('lamp_in', x, y, z, [(.29, -.12), (.12, .09), (0, .09)], 14, flip=True)
    blob('bulb', x, y - .06, z, .07, .08, .07, 8, 4)
    box('steel_dark', x, z, .016, .016, y + .13, top - y - .13, .002)


def tube(p):
    x, z, y, ry = p['x'], p['z'], p.get('y', 4), p.get('ry', 0)
    box('tube', x, z, 1.6, .07, y - .035, .07, .02, ry); box('white', x, z, 1.75, .24, y + .035, .06, .015, ry)
    for s in (-.6, .6): box('steel_dark', x + s, z, .014, .014, y + .09, ROOF_Y - y - .09, .002)


FANS = 0


def fan(p):
    global FANS
    x, z, y = p['x'], p['z'], p.get('y', 5.6)
    box('steel_dark', x, z, .04, .04, y + .06, ROOF_Y - y - .06, .005)
    OBJ[0] = 'FAN_%02d' % FANS; FANS += 1; ORIGIN[OBJ[0]] = (x, -z, y)
    lathe('white', x, y - .08, z, [(0, 0), (.14, 0), (.17, .06), (.14, .14), (0, .14)], 12)
    for k in range(3):
        a = k * 2 * PI / 3 + FANS
        box('white', 0, 0, 1.25, .18, 0, .025, .01, M=T(x, y, z, a) @ Matrix.Translation((.78, 0, 0)) @ Matrix.Rotation(.12, 4, 'X'))
    OBJ[0] = 'MAP'


PROPS = dict(icetable=icetable, crates=crates, bin=bin_, plant=plant, table=table, lamp=lamp, tube=tube, fan=fan)


# ------------------------------------------------------------------ structure
def wall_stack(x, z, w, d, h, dado='tile_green', upper='wall_mint', dh=1.2):
    mark(); box(dado, x, z, w, d, 0, dh, .025); box('trim', x, z, w, d, dh, .1, .02)
    box(upper, x, z, w, d, dh + .1, h - dh - .1 - .07, .025); box('cap', x, z, w, d, h - .07, .07, .02); done()


def outer_wall(x, z, w, d, h):
    mark(); box('tile_green', x, z, w, d, 0, 1.5, .03); box('trim', x, z, w, d, 1.5, .1, .02)
    box('wall', x, z, w, d, 1.6, 2.6, .03); box('glass', x, z, w, d, 4.2, 1.5, .03); box('wall', x, z, w, d, 5.7, h - 5.7, .03); done()
    L = max(w, d); n = int(L / 3)                           # mullions on the window band, 3 cm proud
    for i in range(n + 1):
        o = -L / 2 + L * i / n
        if w >= d: box('wall', x + o, z, .16, d + .06, 4.2, 1.5, .02)
        else: box('wall', x, z + o, w + .06, .16, 4.2, 1.5, .02)


def build_box(b):
    x, z, w, d, h, col, y0, f = b; c, _, tk = col.partition('@'); c = c.lower(); lo, hi = min(w, d), max(w, d)
    if 'i' in f and 'v' not in f: return                    # invisible wall: not dressed (the old game did not)
    if 'r' in f:
        OBJ[0] = 'ROOF'; mark(); box('roof', x, z, w, d, y0, h, .03); done()
        for i in range(-5, 6): box('steel_dark', i * 8 + 4 if i < 5 else 43.5, z, .14, d - 1.4, y0 - .26, .26, .02)
        for s in (-13, 0, 13): box('steel_dark', x, s + 6.5 if s else 0, w - 1.4, .12, y0 - .14, .14, .02)
        OBJ[0] = 'MAP'; return
    if 'v' in f:
        if y0 > 3 and h <= .15:
            mark(); box('canopy_tan' if c == '#d9b98a' else 'canopy', x, z, w, d, y0, h, .04); done()
            box('white', x, z, w - .5, d - .5, y0 - .012, .012, .004)     # pale underside panel
            for sx in (-1, 1):
                for sz in (-1, 1): box('steel_dark', x + sx * (w / 2 - .25), z + sz * (d / 2 - .25), .03, .03, y0 + h, ROOF_Y - y0 - h, .004)
        elif tk == 'grate': box('grate', x, z, w, d, 0, .012, .004)
        elif tk == 'hazard': box('hazard', x, z, w, d, y0, .012, .004)
        elif tk == 'shutter':
            n = 18
            for i in range(n): box('shutter', x, z, w, .06, y0 + i * d / n, d / n, .025)      # d is the height here (old data quirk)
        elif c == '#5a5f66' and h <= .1:                    # trolley deck with castors
            box('steel_dark', x, z, w, d, .035, .045, .012)
            for sx in (-1, 1):
                for sz in (-1, 1): blob('sign_frame', x + sx * (w / 2 - .12), .04, z + sz * (d / 2 - .1), .04, .04, .025, 8, 4)
        else: box('steel' if c == '#5a5f66' else flat(c), x, z, w, d, y0, h, .008)
        return
    if h >= 6 and lo <= .7 and hi > 20: return outer_wall(x, z, w, d, h)
    if tk == 'pillar':
        mark(); box('tile_green', x, z, w, d, 0, 1.5, .05); box('trim', x, z, w, d, 1.5, .1, .03); box('wall', x, z, w, d, 1.6, h - 1.6, .05); done(); return
    if c == '#dfe9e1':                                      # wash bay troughs
        mark(); box('tile_white', x, z, w, d, 0, h - .06, .03); box('steel', x, z, w, d, h - .06, .06, .02); done()
        box('steel_dark', x, z, w - .16, d - .16, h, .004, .001); return
    if tk == 'walltile' and h >= 2: return wall_stack(x, z, w, d, h)
    if c == '#cbc2b2' and .8 <= h <= 1.35: return counter(x, z, w, d, y0, h)
    if c == '#5aa04a':                                      # flower planters
        mark(); box('tile_white', x, z, w, d, 0, .6, .03); box('leaf', x, z, w - .12, d - .12, .6, h - .6, .12); done()
        n = int(hi / .32)
        for i in range(n):
            o = -hi / 2 + hi / n * (i + .5)
            blob(rnd.choice(['pink', 'yellow', 'white', 'red']), x + (o if w >= d else 0), h + .01, z + (0 if w >= d else o) + rnd.uniform(-.2, .2), .09, .06, .09, 6, 3)
        return
    if c == '#b8b2a6': mark(); box('concrete', x, z, w, d, y0, h, .04); done(); return
    if c in ('#b98a5a', '#c9a272'):                         # cartons on trolleys
        m = 'styro' if (c == '#c9a272' and int(abs(x * 3)) % 3 == 0) else ('carton_d' if c == '#b98a5a' else 'carton')
        mark(); box(m, x, z, w, d, y0, h, .025); done(); box('white' if m != 'styro' else 'blue', x, z, .1, d + .004, y0 + .002, h, .02); return
    mark(); box(flat(c), x, z, w, d, y0, h, .03); done()


def sign(p):
    r = p['row']; w, h, ry = p['w'], p['h'], p.get('ry', 0); M = T(p['x'], p['y'], p['z'], ry)
    u0 = (r % 2) * .5; v1 = 1 - (r // 2) / 8; v0 = v1 - 1 / 8
    emit('sign', [(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)], [(0, 1, 2, 3)], M,
         uv=[[(u0, v0), (u0 + .5, v0), (u0 + .5, v1), (u0, v1)]])
    vs, fs = box_vf(w + .12, .05, h + .12, .02); emit('sign_frame', vs, fs, M @ Matrix.Translation((0, .03, 0)))
    back = M @ Vector((0, .2, 0)); far = M @ Vector((0, .95, 0)); top = p['y'] + h / 2 + .06
    if solid_at(back.x, p['y'], -back.y): return            # wall mounted
    cy = canopy_over(p['x'], p['z'])
    for s in (-1, 1):
        q = M @ Vector((s * (w / 2 - .3), .03, 0))
        if cy and cy > top - .1: box('steel_dark', q.x, -q.y, .03, .03, top, max(cy - top, .01), .004)
        elif canopy_over(far.x, -far.y, .05):                # arm back to the canopy edge
            vs, fs = box_vf(.04, .95, .04, .005); emit('steel_dark', vs, fs, M @ Matrix.Translation((s * (w / 2 - .3), .5, h / 2 + .03)))
        else: box('steel_dark', q.x, -q.y, .03, .03, top, ROOF_Y - top, .004)


def hdb(o):
    m = 'hdb_a' if o['c'].lower() == '#cfe8d8' else 'hdb_b'
    box(m, o['x'], o['z'], o['w'], o['d'], -.05, o['h'], .15)
    for i in range(int(o['h'] / 3)): box('hdb_band', o['x'], o['z'], o['w'] + .5, o['d'] + .5, i * 3 + 1.1, 1.0, .1)


def build():
    box('floor', 0, 0, 91.2, 57.2, -.2, .2, .0)
    box('grate', 0, 0, .9, .9, 0, .012, .004)                # floor drain in the B court (flat)
    box('ground', 0, 0, 400, 400, -.3, .25, .0)
    for b in BOXES: build_box(b)
    for p in X['props']:
        if not p.get('vis') or True:
            if p['k'] in PROPS: PROPS[p['k']](p)
    NEW = [s for s in SOLIDS if 'i' not in s[6] and not any(all(abs(c[i] - s[i]) <= .05 for i in range(6)) for c in COVER)]   # v2 colliders the old map does not have
    print('NEW COLLIDERS %d' % len(NEW)); [print('  new', [round(v, 2) for v in s[:6]]) for s in NEW]
    for p in X['props']:
        if p['k'] in ('icetable', 'crates', 'bin', 'plant', 'table') and any(s[0] - .3 < p['x'] < s[3] + .3 and s[2] - .3 < p['z'] < s[5] + .3 for s in NEW): print('PROP CLASH', p)
    for k, s in enumerate(NEW):
        w, d, h = s[3] - s[0], s[5] - s[2], s[4] - s[1]
        if h > 2: shutter_unit(s)
        elif abs(w - d) < .05: icebox(s, k)
        else: counter((s[0] + s[3]) / 2, (s[2] + s[5]) / 2, w, d, s[1], h)
    k = 0
    for b in sorted([b for b in BOXES if b[5].lower() == '#cbc2b2'] + [[(s[0] + s[3]) / 2, (s[2] + s[5]) / 2, s[3] - s[0], s[5] - s[2], s[4], '#cbc2b2', 0, 's'] for s in NEW if s[4] < 1.15 and s[3] - s[0] > 1.5]):
        x, z, w, d, h = b[:5]
        if not (.8 <= h <= 1.35) or w < d: continue
        plate(k, x - w / 2 - .006, .62, z, 3 * PI / 2); plate(k, x + w / 2 + .006, .62, z, PI / 2); k += 1      # REF 2.8: unit number on each block end
        kind = stall_kind(x, z, w)
        if w >= 3 and abs(abs(z) - 9) < .5 and (kind == 'ayam' or k % 2): rail(x, z, w, kind)
    for b in BOXES:                                          # four-language no-smoking plates on the pillars (wording: tools/signs/WORDING.md)
        if b[5].endswith('@pillar'):
            for e, ry in ((1, PI / 2), (-1, 3 * PI / 2)): nosmoke(b[0] + e * (b[2] / 2 + .006), 2.2, b[1], ry)
    OBJ[0] = 'ROOF'
    for i in (-1, 0, 1): box('skylight', i * 3, 0, 2.2, 8.4, ROOF_Y - .04, .03, .01)
    OBJ[0] = 'MAP'      # REF 2.10: bright court at B
    for p in X['signs']['place']: sign(p)
    for o in X['outside']: hdb(o)
    k = 0
    for hz in X['hazards']:
        if hz['k'] == 'wet': rprism('puddle', hz['x'], hz['z'], hz['w'], hz['d'], .002, .01, min(hz['w'], hz['d']) * .45, .004, n=6)
        elif hz['k'] == 'shutter':                           # closed until openAt: separate objects for the engine to slide up
            OBJ[0] = 'SHUTTER_%d' % k; k += 1; ORIGIN[OBJ[0]] = (hz['x'], -hz['z'], 0)
            for i in range(13): box('shutter', hz['x'], hz['z'], hz['w'], hz['d'], i * hz['h'] / 13, hz['h'] / 13, .03)
            OBJ[0] = 'MAP'


def to_objects():
    mats = {}; objs = []; tris = 0
    for (on, mn), (vs, fs, uvs) in BUF.items():
        if mn not in mats: mats[mn] = make_mat(mn)
        o3 = ORIGIN.get(on)
        if o3: vs = [(v[0] - o3[0], v[1] - o3[1], v[2] - o3[2]) for v in vs]
        me = bpy.data.meshes.new(on + '__' + mn); me.from_pydata(vs, [], fs)
        ex = MAT[mn][4]; sc = ex.get('uv', 1.0); uvl = me.uv_layers.new(name='UVMap').data; li = 0
        for f, fu in zip(fs, uvs):
            if fu is None:
                p = [Vector(vs[i]) for i in f[:3]]; n = (p[1] - p[0]).cross(p[2] - p[0])
                ax = max(range(3), key=lambda i: abs(n[i])); a, c = ((1, 2), (0, 2), (0, 1))[ax]
                off = o3 or (0, 0, 0)
                fu = [((vs[i][a] + off[a]) / sc, (vs[i][c] + off[c]) / sc) for i in f]
            for q in fu: uvl[li].uv = q; li += 1
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons)); me.materials.append(mats[mn])
        me.set_sharp_from_angle(angle=math.radians(52))
        ob = bpy.data.objects.new(on if (on != 'MAP' and on != 'ROOF' and len([1 for k in BUF if k[0] == on]) == 1) else on + '__' + mn, me)
        SC.collection.objects.link(ob)
        if o3: ob.location = o3
        bpy.context.view_layer.objects.active = ob
        wn = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.keep_sharp = True; wn.weight = 60
        bpy.ops.object.modifier_apply(modifier='wn')
        tris += sum(len(f) - 2 for f in fs); objs.append(ob)
    # a fan is one object: join its parts
    return objs, mats, tris


def collider_check():
    bad = []; undressed = 0
    for s in SOLIDS:
        if any(all(abs(c[i] - s[i]) <= .05 for i in range(6)) for c in COVER): continue
        if 'i' in s[6]: undressed += 1; continue
        bad.append(s)
    print('COLLIDER CHECK: %d solids, %d matched, %d invisible walls left undressed, %d FAIL' % (len(SOLIDS), len(SOLIDS) - undressed - len(bad), undressed, len(bad)))
    for s in bad[:40]: print('  FAIL', [round(v, 3) for v in s[:6]], s[6])
    return bad


# ------------------------------------------------------------------ stage and shots
def look_at(o, target):
    o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()


def stage():
    w = bpy.data.worlds.new('World'); SC.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (.86, .88, .90, 1); bg.inputs[1].default_value = .55
    sx, sy, sz = SUN
    d = bpy.data.lights.new('sun', 'SUN'); d.energy = 2.0; d.color = (1.0, .86, .68); d.angle = math.radians(3)
    o = bpy.data.objects.new('sun', d); SC.collection.objects.link(o); o.location = (sx, -sz, sy); look_at(o, (0, 0, 0))
    for x in (-30, -10, 10, 30):                             # warm bounce so the zinc ceiling does not go cold grey
        a = bpy.data.lights.new('bounce', 'AREA'); a.energy = 1800; a.size = 22; a.color = (1.0, .93, .82)
        o = bpy.data.objects.new('bounce', a); SC.collection.objects.link(o); o.location = (x, 0, -1.0); o.rotation_euler = (PI, 0, 0)
        if hasattr(a, 'use_shadow'): a.use_shadow = False
    SC.render.engine = 'BLENDER_EEVEE'; SC.eevee.taa_render_samples = 32
    SC.view_settings.view_transform = 'AgX'; SC.view_settings.look = 'AgX - Punchy'; SC.view_settings.exposure = -.25
    SC.render.image_settings.file_format = 'PNG'
    for k, v in (('use_shadows', True), ('use_raytracing', True)):
        try: setattr(SC.eevee, k, v)
        except Exception: pass
    cd = bpy.data.cameras.new('cam'); cd.clip_start = .1; cd.clip_end = 600
    cam = bpy.data.objects.new('cam', cd); SC.collection.objects.link(cam); SC.camera = cam; return cam


def hero(name, x, z, face):
    """drop a toy hero glb at game (x, z). face: blender Z rotation (0 = facing game -z)."""
    path = os.path.join(ROOT, 'assets', 'heroes', name + '.glb')
    if not os.path.exists(path): return
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    for o in set(bpy.data.objects) - before:
        if o.parent is None:
            o.rotation_mode = 'XYZ'; o.rotation_euler = (o.rotation_euler.x, o.rotation_euler.y, face); o.location = (x, -z, 0)


def shot(cam, name, loc, target, lens=28, res=(1600, 900), ortho=None):
    cam.location = (loc[0], -loc[2], loc[1]); look_at(cam, (target[0], -target[2], target[1]))
    cam.data.type = 'ORTHO' if ortho else 'PERSP'
    if ortho: cam.data.ortho_scale = ortho
    cam.data.lens = lens; SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(SHOTS, name); bpy.ops.render.render(write_still=True); print('shot', name)


build()
objs, mats, tris = to_objects()
bad = collider_check()
print('TRIS %d  MATERIALS %d  OBJECTS %d' % (tris, len(mats), len(objs)))
os.makedirs(os.path.dirname(GLB), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=GLB, export_format='GLB', export_yup=True, export_apply=True)
print('glb', GLB, os.path.getsize(GLB) // 1024, 'KB')

cam = stage()
roof = [o for o in objs if o.name.startswith('ROOF')]
high = roof + [o for o in objs if o.name.startswith('FAN_')]
for o in roof: o.visible_shadow = False
ONLY = [a for a in sys.argv if a.endswith('.png')]


def snap(name, *a, **k):
    if not ONLY or name in ONLY: shot(cam, name, *a, **k)


hero('ahma', -30.0, -1.0, PI / 2); hero('gym', -25.2, 1.5, PI / 2); hero('tarik', -18.5, -.6, -PI / 2)
hero('siao', -22.0, 13.0, PI / 2); hero('ahma', -15.5, 11.4, -PI / 2)
snap('ground_a.png', (-35.6, 1.6, -.7), (-8, 1.7, -.2), 22)
snap('ground_b.png', (-30.5, 1.6, 12.6), (-6, 1.6, 12.2), 22)
snap('detail.png', (-23.4, 1.6, 2.4), (-19.6, .95, -1.6), 30)
for o in high: o.hide_render = True
snap('overview.png', (-52, 50, 62), (-2, 0, 3), 30)
snap('topdown_check.png', (0, 120, 0), (0, 0, 0), res=(1600, 1000), ortho=96)
if not ONLY or 'topdown_check.png' in ONLY:                  # every v2 collider outlined in red (system python has PIL, Blender does not)
    subprocess.run(['/usr/bin/env', 'python3', '-c', """
import json, sys
from PIL import Image, ImageDraw
im = Image.open(sys.argv[1]).convert('RGB'); d = ImageDraw.Draw(im); k = im.width / 96
for s in json.load(open(sys.argv[2])):
    if 'r' in s[6]: continue
    d.rectangle([(s[0] + 48) * k, (s[2] + 30) * k, (s[3] + 48) * k, (s[5] + 30) * k], outline=(255, 0, 0) if 'i' not in s[6] else (255, 0, 255), width=2)
im.save(sys.argv[1])
""", os.path.join(SHOTS, 'topdown_check.png'), os.path.join(HERE, 'layouts', 'wetmarket_solids_v2.json')], check=True)
