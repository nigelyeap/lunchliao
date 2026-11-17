"""Changkat Food Centre Roof Carpark, toy playset. Run: /opt/homebrew/bin/blender -b -P tools/blender/maps_toy/carpark.py [-- preview]
Builds from carpark_layout.py (v3 layout: typed items that are also the colliders in layouts/carpark_solids_v3.json) and layouts/carpark_expanded.json (outside world, sign wording).
Look follows carpark_REF.md: an HDB rooftop carpark over a food centre, People's Park yellow slab behind.
Writes assets/maps/carpark.glb, the five shots, and runs a collider self-check (prints COLLIDER CHECK PASS or FAIL).
Game coords (x, y up, z) map to Blender (x, -z, y). Sign atlas comes from carpark_signs.py (system python + Pillow).
Authoring convention below: sizes are (w along x, d along game z, h up), positions are game (x, z, y0=bottom)."""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
LAY = os.path.join(HERE, 'layouts')
OUT = os.path.join(ROOT, 'shots', 'maps_toy', 'carpark')
TEX = os.path.join(ROOT, 'assets', 'maps', 'carpark_tex')
PREVIEW = 'preview' in sys.argv
os.makedirs(OUT, exist_ok=True)
X = json.load(open(os.path.join(LAY, 'carpark_expanded.json')))
RAW = json.load(open(os.path.join(LAY, 'carpark.json')))
sys.path.insert(0, HERE); import carpark_layout
ITEMS, SOL = carpark_layout.ITEMS, carpark_layout.SOLIDS
LOOK = RAW['look']

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
PI = math.pi

# ---------------------------------------------------------------- materials
def srgb(h):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(c * 2 for c in h)
    f = lambda c: c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
    return tuple(f(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))

MATS = {}
def mat(name, hexcol, rough=.45, metal=0.0, coat=0.0, emit=0.0):
    if name in MATS: return name
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(hexcol), 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .08
    if emit:
        b.inputs['Emission Color'].default_value = (*srgb(hexcol), 1); b.inputs['Emission Strength'].default_value = emit
    MATS[name] = m; return name

def cmat(hexcol, rough=.4, coat=.15):       # plastic in any colour, cached by hex
    return mat('c_' + hexcol.lstrip('#'), hexcol, rough, coat=coat)

# palette: see carpark_REF.md section 5 for the source of each colour
mat('floor', '#b99b72', .8)                   # bare concrete deck
mat('o_cap', '#f0dcae', .6)
mat('o_glass', '#6f8796', .3)
mat('o_ochre', '#e39a1f', .6)                 # People's Park "old school yellow" slab
mat('o_green', '#3f8f63', .6)                 # its green bands
mat('o_maroon', '#9c2f33', .6)                # its maroon accents
mat('conc', '#a88a63', .7)                    # kerbs, platform, deck slab
mat('cream', '#d98866', .55)                  # painted parapets, columns
mat('cap', '#f3e3bf', .4, coat=.2)            # white trims
mat('tile', '#63a886', .5)                    # stair and lift core walls, painted off-white
mat('teal', '#2c7a58', .4, coat=.2)           # core dado band, People's Park green
mat('maroon', '#9c2f33', .4, coat=.2)
mat('ochre', '#e3a224', .45, coat=.2)
mat('sage', '#6f9cc4', .6)                    # vent shafts and screen walls, plain painted concrete
mat('dark', '#3b3633', .5)
mat('rubber', '#2a2623', .7)
mat('steel', '#b9bec4', .3, metal=1.0)
mat('glass', '#4f6b82', .08, coat=1.0)
mat('cglass', '#27384a', .1, coat=1.0)        # tinted car glass
mat('under', '#7d5a45', .8)                   # roof undersides
mat('yellow', '#f4b31c', .45, coat=.2)        # aisle paint, kerb stripes
mat('white', '#f6f1e4', .5)                   # lot lines
mat('red', '#c8221b', .35, coat=.4)
mat('sred', '#f02a1a', .4, emit=.6)            # season lot lines, lit a little so they stay red in shadow
mat('blue', '#1f5fae', .35, coat=.4)
mat('green', '#2f7d4f', .4, coat=.3)
mat('leaf', '#4fa53c', .55)
mat('leaf2', '#3f8a3a', .55)
mat('soil', '#7a5538', .8)
mat('trunk', '#7a5538', .6)
mat('grass', '#6a9f55', .9)
mat('road', '#55595c', .8)
mat('lamp', '#fff1c9', .3, emit=4.0)
mat('head', '#fff6e6', .2, emit=1.5)
mat('tail', '#e04030', .25, coat=.6)
mat('lift', '#9aa3a8', .28, metal=1.0)
PASTEL = ['#e8746a', '#4fb58a', '#f0b93a', '#e0709c', '#3f9bd0', '#f1e2bd', '#ee8a4a', '#7dbb4e', '#f29b7a', '#35b0a6']
COUPON = ['#e8bf3f', '#d98a8a', '#9ec9df', '#b9d8a8']

# ---------------------------------------------------------------- geometry buckets (one mesh per material)
BK = {}
def push(m, verts, faces, M=None):
    b = BK.setdefault(m, ([], [])); n = len(b[0])
    b[0].extend([tuple(M @ Vector(v)) for v in verts] if M is not None else verts)
    b[1].extend([tuple(i + n for i in f) for f in faces])

_rb = {}
def _rbox(w, d, h, r, seg):
    k = (round(w, 4), round(d, 4), round(h, 4), round(r, 4), seg)
    if k not in _rb:
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
        for v in bm.verts: v.co = Vector((v.co.x * w, v.co.y * d, v.co.z * h))
        r = min(r, .45 * min(w, d, h))
        if r > .004: bmesh.ops.bevel(bm, geom=bm.edges[:], offset=r, segments=seg, affect='EDGES', profile=.5)
        bm.verts.index_update()
        _rb[k] = ([tuple(v.co) for v in bm.verts], [tuple(v.index for v in f.verts) for f in bm.faces]); bm.free()
    return _rb[k]

def B(m, x, z, y0, w, d, h, r=.04, seg=1, M=None):
    """Bevelled box. Footprint w x d centred on game (x, z), from y0 to y0+h."""
    vs, fs = _rbox(w, d, h, r, seg)
    push(m, [(v[0] + x, v[1] - z, v[2] + y0 + h / 2) for v in vs], fs, M)

_cy = {}
def C(m, x, z, y, r, length, axis='y', seg=20, r2=None, bev=0.0, M=None):
    """Cylinder centred on game (x, z, y). axis: 'y' up, 'x', or 'z' (game z)."""
    r2 = r if r2 is None else r2; k = (round(r, 4), round(r2, 4), round(length, 4), seg, round(bev, 4))
    if k not in _cy:
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r2, depth=length)
        if bev: bmesh.ops.bevel(bm, geom=list({e for f in bm.faces if len(f.verts) > 4 for e in f.edges}), offset=bev, segments=2, affect='EDGES', profile=.5)
        bm.verts.index_update()
        _cy[k] = ([tuple(v.co) for v in bm.verts], [tuple(v.index for v in f.verts) for f in bm.faces]); bm.free()
    vs, fs = _cy[k]
    if axis == 'x': vs = [(v[2], v[1], v[0]) for v in vs]; fs = [f[::-1] for f in fs]
    elif axis == 'z': vs = [(v[0], v[2], v[1]) for v in vs]; fs = [f[::-1] for f in fs]
    push(m, [(v[0] + x, v[1] - z, v[2] + y) for v in vs], fs, M)

_ico = {}
def S(m, x, z, y, rx, ry_, rz, sub=2, M=None):
    if sub not in _ico:
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1); bm.verts.index_update()
        _ico[sub] = ([tuple(v.co) for v in bm.verts], [tuple(v.index for v in f.verts) for f in bm.faces]); bm.free()
    vs, fs = _ico[sub]
    push(m, [(v[0] * rx + x, v[1] * rz - z, v[2] * ry_ + y) for v in vs], fs, M)

def place(x, z, ry=0.0, y=0.0):
    """Matrix for a prop authored around its own origin with front = local game +z."""
    return Matrix.Translation((x, -z, y)) @ Matrix.Rotation(ry, 4, 'Z')

# ---------------------------------------------------------------- props
def car(x, z, ry, idx, van=False):
    """Toy car inside the 1.8 x 4.2 x 1.45 collider, or a panel van inside 2.0 x 4.8 x 2.1. Front is local game +z. idx picks type and colour."""
    M = place(x, z, ry); model = 'van' if van else ('sedan', 'hatch', 'mpv', 'taxi', 'suv')[(idx * 3 + idx // 5) % 5]
    w, l, top = (1.9, 4.8, 2.1) if van else (1.8, 4.2, 1.45); hw, hl = w / 2, l / 2
    body = cmat(('#f1e2bd', '#3f9bd0', '#f0b93a', '#4fb58a')[idx % 4] if van else '#2f86d6' if model == 'taxi' else PASTEL[(idx * 7) % len(PASTEL)], .3, .5)
    belt, cz, cl, nw = dict(sedan=(.8, -.15, 2.1, 2), hatch=(.8, -.5, 2.6, 2), mpv=(.9, -.25, 3.3, 3), taxi=(.8, -.15, 2.1, 2), suv=(.92, -.45, 2.9, 3), van=(1.1, 0, l, 0))[model]
    if van:
        B(body, 0, 0, .28, w, l, top - .28, r=.2, seg=3, M=M); cw = w; wy0, wh = 1.2, .6      # one tall box body
        B('cglass', 0, hl - .005, wy0, 1.44, .03, wh, r=.01, M=M)                               # windscreen
        for sx in (-1, 1):
            B('cglass', sx * (hw - .005), hl - .9, wy0, .03, .85, wh - .05, r=.01, M=M)          # cab side windows
            B('dark', sx * (hw - .005), hl - 1.45, .5, .03, .03, 1.4, r=0, M=M)                  # cab door line
            B(body, sx * (hw - .05), hl - .42, 1.3, .1, .1, .22, r=.03, M=M)                     # mirror
            B('tail', sx * (hw - .3), -(hl - .02), .7, .12, .05, .5, r=.02, M=M)
        B('dark', hw - .005, -.4, .5, .03, .03, 1.4, r=0, M=M); B('dark', hw - .005, -1.05, 1.12, .03, 1.9, .04, r=0, M=M)   # sliding door line and its rail
        B('dark', 0, -(hl - .005), .5, .03, .03, 1.4, r=0, M=M); B('steel', .12, -(hl - .005), 1.1, .06, .04, .16, r=.01, M=M)   # rear doors
    else:
        rt = top - .08 if model == 'taxi' else top; cw = 1.56; wy0 = belt + .1; wh = rt - .14 - wy0
        B(body, 0, 0, .22, w, l, belt - .22, r=.2, seg=3, M=M)                                  # body
        B(body, 0, cz, belt - .06, cw, cl, rt - belt + .06, r=.12, seg=2, M=M)                  # cabin, roof top at the collider top
        for sg in (1, -1): B('cglass', 0, cz + sg * (cl / 2 - .005), wy0, cw - .36, .03, wh, r=.01, M=M)   # front and rear screens
        z0 = cz - cl / 2 + .18; sp = (cl - .36) / nw
        for sx in (-1, 1):
            for j in range(nw): B('cglass', sx * (cw / 2 - .005), z0 + (j + .5) * sp, wy0, .03, sp - .1, wh, r=.01, M=M)   # side windows, pillars between
            B(body, sx * (cw / 2 + .06), cz + cl / 2 - .3, belt + .06, .12, .1, .12, r=.03, M=M)  # mirror
            B('tail', sx * (hw - .4), -(hl - .02), .5, .34, .05, .14, r=.02, M=M)
        if model == 'taxi': B('head', 0, 0, rt, .5, .2, .08, r=.03, M=M)                         # roof sign, blank
        if model == 'suv': B('dark', 0, 0, .22, w + .01, l - .5, .16, r=.03, M=M)                # sill cladding
        if idx % 2 == 0: B(cmat(COUPON[idx % 4], .5, 0), .42, cz + cl / 2 + .12, belt, .2, .12, .012, r=0, M=M)   # coupon on the dashboard
    wr = .38 if van else .34
    for sx in (-1, 1):
        for sz in (-(hl - .78), hl - .78):
            C('dark', sx * (hw - .012), sz, wr, wr + .08, .03, 'x', 20, M=M)                     # wheel arch
            C('rubber', sx * (hw - .11), sz, wr, wr, .22, 'x', 20, bev=.05, M=M); C('cap', sx * (hw - .005), sz, wr, wr * .55, .03, 'x', 16, M=M)
        B('head', sx * (hw - .4), hl - .02, .62 if van else .46, .34, .05, .15, r=.02, M=M)
    for sg in (1, -1): B('dark', 0, sg * (hl - .07), .24, w - .1, .14, .18, r=.05, M=M)         # bumpers
    B('dark', 0, hl - .02, .64 if van else .48, .5, .04, .11, r=.01, M=M)                       # grille
    B('cap', 0, -(hl - .005), .5 if van else .34, .5, .03, .13, r=.01, M=M)                     # number plate, blank
    B('conc', 0, -(hl - .38), 0, 1.5, .16, .1, r=.03, M=M)                                      # wheel stop, under the tail
LINES = set()

def scooter(x, z, ry, col):
    M = place(x, z, ry); c = cmat(col, .3, .5)
    for sz in (-.6, .6): C('rubber', 0, sz, .26, .26, .12, 'x', 16, bev=.03, M=M)
    B(c, 0, -.15, .3, .3, .95, .34, r=.1, seg=2, M=M)                    # body
    B('dark', 0, -.3, .64, .32, .7, .12, r=.05, seg=2, M=M)              # seat
    B(c, 0, .5, .3, .34, .16, .62, r=.06, seg=2, M=M)                    # front shield
    C('steel', 0, .52, .98, .025, .6, 'x', 8, M=M)                        # handlebar
    C('head', 0, .6, .8, .07, .05, 'z', 12, M=M)

def lamppost(p):
    M = place(p['x'], p['z'], p.get('ry', 0))
    C('cream', 0, 0, .25, .15, .5, seg=12, M=M); C('steel', 0, 0, 3, .07, 6, seg=12, M=M)
    B('steel', 0, .6, 5.9, .1, 1.3, .08, r=.03, M=M); B('cap', 0, 1.1, 5.78, .34, .6, .12, r=.05, seg=2, M=M)
    B('lamp', 0, 1.1, 5.755, .26, .5, .03, r=.01, M=M)

def bin_(p):
    c = cmat(p.get('c', '#2f7d4f'), .4, .3)
    C(c, p['x'], p['z'], .4, .3, .8, seg=16, r2=.27, M=None); C('dark', p['x'], p['z'], .84, .31, .08, seg=16, bev=.02)

def tree(o):
    s = o.get('s', 1); x, z = o['x'], o['z']
    C('trunk', x, z, -3.6, .35 * s, 10.8, seg=10, r2=.22 * s)
    for i, (dx, dz, dy, r) in enumerate([(0, 0, 3.2, 3.0), (1.6, .8, 2.2, 2.2), (-1.5, -.6, 2.4, 2.3), (.3, -1.6, 2.0, 2.0)]):
        S('leaf' if i % 2 == 0 else 'leaf2', x + dx * s, z + dz * s, dy * s + 1.2, r * s, r * s * .8, r * s)

def hdb(o, i):
    """Slab block: corridor parapet bands, window bays, a stair core, block number, laundry poles on the near ones.
    Block 0 is the People's Park tower: ochre slab, green and maroon bands, portholes and fins on the roof."""
    x, z, w, d, h = o['x'], o['z'], o['w'], o['d'], o['h']; pp = i == 0
    if pp: w, d, h = 44, 12, 62; x, z = -20, -66
    body = 'o_ochre' if pp else cmat(('#e58f7a', '#6fb39a', '#e6b455', '#7aa6d0', '#dd8fa3')[i % 5], .6, 0)   # repainted HDB blocks in strong pastels
    B(body, x, z, -9, w, d, h + 9, r=.3); B('o_cap', x, z, h, w + .8, d + .8, .7, r=.2)
    lx = w >= d; ln = max(w, d); th = min(w, d); n = int(ln // 3.2); fl = -9 + 3.0; k = 0
    def P(m, a, off, y0, la, lt, hh):                             # box at a along the long axis, off across it
        B(m, x + (a if lx else off), z + (off if lx else a), y0, la if lx else lt, lt if lx else la, hh, r=0)
    while fl < h - 1.5:
        band = ('o_green' if k % 6 < 5 else 'o_maroon') if pp else 'o_cap'
        P(band, 0, 0, fl, ln + .4, th + .4, 1.0)                  # corridor parapet, both long faces
        for j in range(n):
            a = -ln / 2 + (j + .5) * ln / n
            for sg in (-1, 1): P('o_glass', a, sg * (th / 2 + .02), fl + 1.25, ln / n * .55, .06, 1.2)
        fl += 2.9; k += 1
    P('o_maroon' if pp else 'o_cap', 0, 0, -9, 4.2, th + 1.6, h + 12)   # stair and lift core through the middle
    for sg in (-1, 1): P('o_glass', 0, sg * (th / 2 + .82), -4, 1.2, .06, h + 2)
    if pp:
        for j in range(9): P('o_ochre', -ln / 2 + 3 + j * (ln - 6) / 8, 0, h + .7, .8, th * .7, 4.5)   # vertical roof fins
        for j in range(12):
            for sg in (-1, 1): C('o_glass', x - ln / 2 + 2.5 + j * (ln - 5) / 11, z + sg * (th / 2 + .22), h - 1.2, .7, .1, 'z', 16)   # portholes
    else:
        sgn = -1 if (z if lx else x) > 0 else 1                   # face toward the carpark
        key = ('blk335', 'blk334', 'blk336')[i % 3]
        if lx: quad(key, x + w / 2 - 3.5, z + sgn * (d / 2 + .26), 5, 2.5, y=h - 4, ry=0 if sgn > 0 else PI)
        else: quad(key, x + sgn * (w / 2 + .26), z + d / 2 - 3.5, 5, 2.5, y=h - 4, ry=PI / 2 if sgn > 0 else -PI / 2)
        if i in (1, 2, 5):                                        # laundry poles off the kitchen side, a few with washing
            fl = -9 + 3.0 + 1.6; k = 0
            while fl < h - 3:
                for j in range(n):
                    if (j + k) % 2: continue
                    a = -ln / 2 + (j + .5) * ln / n; off = sgn * (th / 2 + 1.3)
                    C('steel', x + (a if lx else off), z + (off if lx else a), fl, .04, 2.4, 'z' if lx else 'x', 5)
                    if (j * 3 + k) % 4 == 0: P(cmat(PASTEL[(j + k) % len(PASTEL)], .7, 0), a, off + sgn * .4, fl - .9, .08, 1.0, .9)
                fl += 2.9; k += 1

def parapet(x, z, w, d, h):
    B('cream', x, z, 0, w, d, h - .1); B('cap', x, z, h - .1, w + .04, d + .04, .1, r=.03)
    ln = max(w, d); ax = 'x' if w > d else 'z'; C('steel', x, z, 1.42, .035, ln - .2, ax, 8)     # steel pipe rail above the concrete parapet (inside the 6 m invisible wall)
    for i in range(int(ln // 3) + 1):
        o = -ln / 2 + .3 + i * (ln - .6) / int(ln // 3); C('steel', x + (o if w > d else 0), z + (0 if w > d else o), 1.25, .03, .34, seg=6)

def hedge(x, z, w, d):
    """Kerbed planter with a clipped hedge, top exactly at 1.5. Row end islands, medians and the corner gardens."""
    B('cream', x, z, 0, w, d, .6, r=.03); B('cap', x, z, .56, w, d, .08, r=.03); B('leaf', x, z, .6, w - .16, d - .16, .9, r=.16, seg=2)
    if min(w, d) > 2:                                           # big beds get a darker inner block so they do not read as one flat slab
        B('leaf2', x, z, .64, w - 1.2, d - 1.2, .87, r=.2, seg=2)

def dtree(x, z):
    """Small planter tree. Crown stays above 2.9 m so nothing hangs into the play space."""
    C('trunk', x, z, 2.3, .13, 3.4, seg=8, r2=.09); S('leaf', x, z, 4.3, 1.25, 1.05, 1.25); S('leaf2', x + .5, z + .3, 4.0, .85, .7, .85)

def core(x, z, w, d, h, kind, door):
    """Lift or stair core: tiled box, green dado, white cap, doors on the lobby face."""
    B('tile', x, z, 0, w, d, h); B('teal', x, z, 0, w + .03, d + .03, 1.0, r=.015); B('cap', x, z, h - .12, w + .04, d + .04, .12, r=.03)
    sg = 1 if door == 'N' else -1; fz = z + sg * (d / 2 + .012)
    if kind == 'lift':
        for dx in (-1.3, 1.3):
            B('dark', x + dx, fz, 0, 1.5, .03, 2.25, r=.01); B('lift', x + dx - .34, fz + sg * .012, .04, .66, .03, 2.1, r=.01); B('lift', x + dx + .34, fz + sg * .012, .04, .66, .03, 2.1, r=.01)
        B('steel', x, fz, 1.0, .16, .03, .3, r=.01); B('lamp', x, fz + sg * .012, 1.14, .06, .02, .06, r=.01)
    else:
        B('dark', x, fz, 0, 1.5, .03, 2.25, r=.01); B('yellow', x, fz + sg * .012, 0, 1.5, .03, .1, r=0)
        for j in range(4): B('conc', x, fz + sg * .02, .12 + j * .2, 1.3, .03, .05, r=0)      # the first steps showing through the doorway

def bay(b, op, red, n):
    """Painted lot: two side lines and a back line (shared lines drawn once), lot number at the open end. Red lines are season lots."""
    x0, z0, x1, z1 = b[0], b[2], b[3], b[5]; m = 'sred' if red else 'white'
    for q in (((x0, z0, x1, z0), (x0, z1, x1, z1), (x0, z0, x0, z1) if op == 'E' else (x1, z0, x1, z1)) if op in 'EW' else ((x0, z0, x0, z1), (x1, z0, x1, z1), (x0, z0, x1, z0) if op == 'N' else (x0, z1, x1, z1))):
        k = tuple(round(v, 2) for v in q)
        if k not in LINES: LINES.add(k); B(m, (q[0] + q[2]) / 2, (q[1] + q[3]) / 2, .004, q[2] - q[0] + .14, q[3] - q[1] + .14, .008 if red else .007, r=0)
    quad('lot%d' % (n % 24 + 1), (x0 + x1) / 2, (z0 + z1) / 2, .9, .45, floor=(dict(N=0, E=PI / 2, S=PI, W=-PI / 2)[op], 0, 1.9))

def arrow(x, z, ry):
    pts = [(-1.2, -.12), (.2, -.12), (.2, -.4), (1.2, 0), (.2, .4), (.2, .12), (-1.2, .12)]
    push('white', [(pz, -px, .006) for px, pz in pts], [(6, 5, 1, 0), (4, 3, 2)], place(x, z, ry))

def shell():
    B('floor', 0, 0, -.6, 90.4, 62.2, .6, r=.05)                         # deck slab, top at y 0
    B('cream', 0, 0, -9, 89.2, 61, 8.4, r=.2); B('teal', 0, 0, -1.6, 89.6, 61.4, .7, r=.1)   # food centre below, green fascia
    B('maroon', 0, 0, -5.6, 93, 64.6, .25, r=.1)                         # canopy over the stall fronts
    for i in range(22):                                                  # stall shutters under the canopy, south and north
        for sg in (1, -1): B(cmat(PASTEL[i % len(PASTEL)], .6, 0), -42 + i * 4, sg * 30.55, -8.9, 3.4, .12, 3.0, r=0)
    for sg in (1, -1): quad('0', -sg * 18, sg * 30.72, 16, 4, y=-3.6, ry=0 if sg > 0 else PI)
    B('grass', 0, 0, -9.2, 420, 420, .2, r=0)
    H, lw = 2.5, .16
    for x, z, w, d in ((0, H, 2 * H, lw), (0, -H, 2 * H, lw), (H, 0, lw, 2 * H), (-H, 0, lw, 2 * H)): B('yellow', x, z, .004, w, d, .008, r=0)
    for c in (-H, 0, H):
        for sg in (1, -1): B('yellow', 0, 0, .004, lw, (2 * H - abs(c)) * math.sqrt(2), .008, r=0, M=place(c / 2, -sg * c / 2, sg * PI / 4))
    for m in (1, -1):                                           # access road falling away outside the gantry
        x0, x1, za, zb = m * -14, m * -8, m * -36, m * -60
        push('road', [(x0, -za, 0), (x1, -za, 0), (x1, -zb, -9), (x0, -zb, -9), (x0, -za, -.5), (x1, -za, -.5), (x1, -zb, -9.5), (x0, -zb, -9.5)],
             [(0, 1, 2, 3), (7, 6, 5, 4), (0, 3, 7, 4), (1, 5, 6, 2)] if m > 0 else [(3, 2, 1, 0), (4, 5, 6, 7), (4, 7, 3, 0), (2, 6, 5, 1)])

# ---------------------------------------------------------------- signs (textured quads, one atlas)
UVR = json.load(open(os.path.join(TEX, 'signs.json'))); SQ = ([], [], [])
def quad(key, x, z, w, h, y=0.0, ry=0.0, floor=None, board=True):
    """Wall sign centred at game (x, z, y) facing local +z, or with floor=(ry, dx, dz) a floor decal offset in the prop's own frame."""
    u0, v0, u1, v1 = UVR[key]; vs, fs, uvs = SQ; w, h = w / 2, h / 2
    if floor:
        M = place(x, z, floor[0]); c = [(floor[1] - w, -floor[2] + h, .012), (floor[1] + w, -floor[2] + h, .012), (floor[1] + w, -floor[2] - h, .012), (floor[1] - w, -floor[2] - h, .012)]
        c = [c[3], c[2], c[1], c[0]]                              # text reads when you stand at the bay looking at the car
    else:
        M = place(x, z, ry, y)
        if board: B('cap', 0, -.012, -h - .03, w * 2 + .06, .03, h * 2 + .06, r=.01, M=M)
        c = [(-w, -.03, -h), (w, -.03, -h), (w, -.03, h), (-w, -.03, h)]
    n = len(vs); vs += [tuple(M @ Vector(q)) for q in c]; fs.append((n, n + 1, n + 2, n + 3)); uvs += [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]

def signs():
    img = bpy.data.images.load(os.path.join(TEX, 'signs.png'))
    m = bpy.data.materials.new('signs'); m.use_nodes = True; nt = m.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
    b = nt.nodes['Principled BSDF']; nt.links.new(t.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .8
    nt.links.new(t.outputs['Alpha'], b.inputs['Alpha']); m.surface_render_method = 'BLENDED'   # floor decals are see-through around the paint
    vs, fs, uvs = SQ
    me = bpy.data.meshes.new('signs'); me.from_pydata(vs, [], fs); l = me.uv_layers.new(name='UVMap')
    l.data.foreach_set('uv', [c for q in uvs for c in q]); me.materials.append(m)
    SC.collection.objects.link(bpy.data.objects.new('signs', me))

# ---------------------------------------------------------------- build
def build():
    shell(); n = 0; nb = 0; nl = 0
    for i in ITEMS:
        b = i['b']; k = i['k']; x, z, w, d, y0, h = (b[0] + b[3]) / 2, (b[2] + b[5]) / 2, b[3] - b[0], b[5] - b[2], b[1], b[4] - b[1]
        if k == 'parapet': parapet(x, z, w, d, h)
        elif k == 'hedge':
            hedge(x, z, w, d)
            for t in i['trees']:
                if abs(t[0]) > 32: dtree(*t)                    # review round: only the planter ends by the lift and stair cores keep a tree
            for t in i['lamps']:
                lamppost(dict(x=t[0], z=t[1], ry=nl * PI / 2)); nl += 1
                if nl % 3 == 0: quad('coupon', t[0], t[1] + .1, .7, .7, y=3.0)      # coupon parking boards on some lamp posts, above head height
        elif k == 'car': car(x, z, i['ry'], n, i['van']); n += 1
        elif k == 'bay': bay(b, i['op'], i['red'], nb); nb += 1
        elif k == 'arrow': arrow(x, z, i['ry'])
        elif k == 'core': core(x, z, w, d, h, i['kind'], i['door'])
        elif k == 'canopy':                                        # roof slab, dark underside, green fascia dropping 0.4 m (stays above 2.3 m)
            B('cream', x, z, y0, w, d, h, r=.03); B('cap', x, z, y0 + h - .06, w + .06, d + .06, .06, r=.02); B('under', x, z, y0 - .03, w - .16, d - .16, .03, r=0)
            for sg in (1, -1): B('teal', x, z + sg * (d / 2 - .04), y0 - .4, w, .08, h + .36, r=.01); B('teal', x + sg * (w / 2 - .04), z, y0 - .4, .08, d, h + .36, r=.01)
        elif k == 'col': B('cream', x, z, 0, w, d, h); B('yellow', x, z, 0, w + .03, d + .03, .45, r=.015); B('dark', x, z, .15, w + .035, d + .035, .15, r=.01)
        elif k == 'booth':
            B('cap', x, z, 0, w, d, h); B('glass', x, z, 1.1, w + .03, d + .03, .9, r=.015); B('blue', x, z, 0, w + .03, d + .03, .3, r=.015)
            sg = 1 if x > 0 else -1; quad('6', x + sg * (w / 2 + .012), z, 1.6, .4, y=2.3, ry=sg * PI / 2); quad('coupon', x + sg * (w / 2 + .012), z, .7, .7, y=.75, ry=sg * PI / 2)
        elif k == 'rack':
            C('steel', x, z, h - .03, .03, w, 'x', 8)
            for j in range(6): B('steel', x - w / 2 + .15 + j * (w - .3) / 5, z, 0, .05, .05, h - .03, r=0); B('steel', x - w / 2 + .15 + j * (w - .3) / 5, z, .5, .04, d - .1, .04, r=0)
        elif k == 'bin': bin_(dict(x=x, z=z))
        elif k != 'iwall': print('UNHANDLED', k)
    print('CARS', n, 'BAYS', nb)
    for m in (1, -1):                                             # lobby signs: wording from the map JSON signs block
        quad('level', m * -39.585, m * 9, 2.4, 1.2, y=2.7, ry=m * PI / 2); quad('1', m * -39.585, m * -9, 3.2, .8, y=2.9, ry=m * PI / 2)
        quad('2' if m > 0 else '3', m * -39.585, 0, 2.2, .55, y=3.3, ry=m * PI / 2)
        quad('10', m * -42.1, m * 5.785, 1.2, .35, y=2.6, ry=PI if m > 0 else 0); quad('5', m * -42.1, m * -5.785, 1.2, .35, y=2.6, ry=0 if m > 0 else PI)
        quad('slow', m * 11, m * 22, 2.4, .4, floor=(PI if m > 0 else 0, 0, 0))
    for i, o in enumerate([o for o in X['outside'] if o['k'] == 'hdb']): hdb(o, i)
    for o in X['outside']:
        if o['k'] == 'tree': tree(o)
    signs()
    tris = 0
    for name, (vs, fs) in BK.items():
        me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.materials.append(bpy.data.materials[MATS[name].name])
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons)); me.set_sharp_from_angle(angle=math.radians(50))
        ob = bpy.data.objects.new('map_' + name, me); SC.collection.objects.link(ob)
        if name.startswith('o_'): ob.visible_shadow = False      # far blocks must not black out the deck at this sun angle
        wn = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.keep_sharp = True; wn.weight = 100
        tris += sum(len(f) - 2 for f in fs)
    tris += len(SQ[1]) * 2
    print('TRIS', tris, 'MATERIALS', len(BK) + 1)

def collider_check():
    """Self-check against carpark_solids_v3.json. (1) every visible solid has geometry reaching its top within 5 cm.
    (2) nothing taller than 12 cm and lower than 2.3 m stands on open floor outside every collider (20 cm grid)."""
    from mathutils.bvhtree import BVHTree
    vs, fs = [], []
    for name, (v, f) in BK.items():
        if name.startswith('o_') or name in ('grass', 'road'): continue
        n = len(vs); vs += v; fs += [tuple(i + n for i in q) for q in f]
    T = BVHTree.FromPolygons([Vector(v) for v in vs], fs); bad = []
    for b in SOL:
        if b[6] == 'i': continue
        cx, cz, hw, hd = (b[0] + b[3]) / 2, (b[2] + b[5]) / 2, (b[3] - b[0]) / 2, (b[5] - b[2]) / 2; best = -99
        for sx, sz in ((0, 0), (.6, .6), (-.6, .6), (.6, -.6), (-.6, -.6)):
            hit = T.ray_cast(Vector((cx + sx * hw, -(cz + sz * hd), b[4] + .051)), Vector((0, 0, -1)))
            if hit[0] is not None: best = max(best, hit[0].z)
        if abs(best - b[4]) > .051: bad.append(('TOP', [round(v, 2) for v in b[:6]], b[6], round(best, 2)))
    sol = [b for b in SOL if b[1] < 2.3]; stray = 0
    for ix in range(-222, 223):
        for iz in range(-152, 153):
            x, z = ix * .2, iz * .2
            if any(b[0] - .06 <= x <= b[3] + .06 and b[2] - .06 <= z <= b[5] + .06 for b in sol): continue
            hit = T.ray_cast(Vector((x, -z, 2.3)), Vector((0, 0, -1)))
            if hit[0] is not None and hit[0].z > .12 and not any(b[0] - .2 <= x <= b[3] + .2 and b[2] - .2 <= z <= b[5] + .2 and b[4] >= hit[0].z for b in sol):   # wall-mounted fixtures within 20 cm of a taller collider are fine
                stray += 1
                if stray <= 25: bad.append(('STRAY', round(x, 1), round(z, 1), round(hit[0].z, 2)))
    for q in bad: print('CHECK', q)
    print('COLLIDER CHECK', 'PASS' if not bad else 'FAIL', len(bad), 'stray', stray)

def export():
    os.makedirs(os.path.join(ROOT, 'assets', 'maps'), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'maps', 'carpark.glb'), export_format='GLB', export_apply=True, export_yup=True)

# ---------------------------------------------------------------- stage and shots
def G(x, y, z): return Vector((x, -z, y))

def look_at(o, t): o.rotation_euler = (Vector(t) - o.location).to_track_quat('-Z', 'Y').to_euler()

def stage():
    w = bpy.data.worlds.new('World'); SC.world = w; w.use_nodes = True; nt = w.node_tree
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); cr = nt.nodes.new('ShaderNodeValToRGB')
    mp = nt.nodes.new('ShaderNodeMapRange'); mp.inputs[1].default_value = -.05; mp.inputs[2].default_value = .7
    sky = LOOK['sky'][::-1]; e = cr.color_ramp.elements
    e[0].position = 0; e[0].color = (*srgb(sky[0]), 1); e[1].position = 1; e[1].color = (*srgb(sky[-1]), 1)
    for i, c in enumerate(sky[1:-1]): n = e.new((.12, .4)[i]); n.color = (*srgb(c), 1)
    nt.links.new(tc.outputs['Generated'], sp.inputs[0]); nt.links.new(sp.outputs['Z'], mp.inputs[0]); nt.links.new(mp.outputs[0], cr.inputs[0])
    bg = nt.nodes['Background']; nt.links.new(cr.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 2.2
    d = bpy.data.lights.new('sun', 'SUN'); d.energy = 5.0; d.color = srgb(LOOK['sun'][0]); d.angle = math.radians(3)
    sx, sy, sz = LOOK['sun'][2]; o = bpy.data.objects.new('sun', d); SC.collection.objects.link(o)
    o.location = G(sx, sy, sz); look_at(o, (0, 0, 0))
    SC.render.engine = 'BLENDER_EEVEE'; SC.eevee.taa_render_samples = 24 if PREVIEW else 48
    SC.view_settings.view_transform = 'AgX'; SC.view_settings.look = 'AgX - Punchy'
    SC.render.image_settings.file_format = 'PNG'
    for k, v in (('use_shadows', True), ('use_raytracing', True), ('shadow_ray_count', 2), ('shadow_step_count', 8)):
        try: setattr(SC.eevee, k, v)
        except Exception: pass
    cd = bpy.data.cameras.new('cam'); cd.clip_start = .1; cd.clip_end = 600; cam = bpy.data.objects.new('cam', cd)
    SC.collection.objects.link(cam); SC.camera = cam; return cam

def hero(name, x, z, yaw, y=0):
    p = os.path.join(ROOT, 'assets', 'heroes', name + '.glb')
    if not os.path.exists(p): return
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p); new = [o for o in bpy.data.objects if o not in before]
    e = bpy.data.objects.new('HERO_' + name, None); SC.collection.objects.link(e)
    for o in new:
        if o.parent is None: o.parent = e
    e.location = G(x, y, z); e.rotation_euler = (0, 0, yaw)

def shot(cam, name, eye, tgt, lens=28, res=(1600, 900)):
    cam.data.type = 'PERSP'; cam.data.lens = lens; cam.location = G(*eye); look_at(cam, G(*tgt))
    SC.render.resolution_x, SC.render.resolution_y = res; SC.render.filepath = os.path.join(OUT, name); bpy.ops.render.render(write_still=True)

def topdown(cam):
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 96; cam.location = (0, 0, 120); cam.rotation_euler = (0, 0, 0)
    SC.render.resolution_x, SC.render.resolution_y = 1600, 1120; SC.render.filepath = os.path.join(OUT, 'topdown_check.png'); bpy.ops.render.render(write_still=True)
    import subprocess; subprocess.run(['/usr/bin/env', 'python3', os.path.join(HERE, 'carpark_check.py')], check=False)   # red collider outlines (Pillow)

build()
collider_check()
export()
cam = stage()
ONLY = [a for a in sys.argv if a.startswith('only=')]; ONLY = ONLY[0][5:].split(',') if ONLY else None
def want(n): return ONLY is None or n in ONLY
if want('topdown'): topdown(cam)
# heroes stand in for scale (render only, never exported). yaw: 0 faces Blender +Y (game -z)
hero('ahma', -1.6, -1.4, 1.9); hero('gym', 1.6, -2.4, 1.6); hero('tarik', -24.3, -8.2, 2.0); hero('siao', -21.2, -10.2, 1.5)
if want('overview'): shot(cam, 'overview.png', (-58, 46, 78), (-2, 0, 2), lens=30)
if want('ground_a'): shot(cam, 'ground_a.png', (-7.5, 1.6, -3.6), (3, 1.2, -1), lens=24)
if want('ground_b'): shot(cam, 'ground_b.png', (-32.5, 1.6, -7.6), (-20, 1.2, -10.4), lens=24)
if want('detail'): shot(cam, 'detail.png', (-20.5, 4.6, 24.5), (-39.6, 0.6, 2.5), lens=24)   # west lift lobby over the Rn cars
