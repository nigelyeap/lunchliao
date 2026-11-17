"""Hawker Centre, toy playset style. Run: /opt/homebrew/bin/blender -b -P tools/blender/maps_toy/hawker.py [-- preview]
Builds from layouts/hawker_solids_v3.json (colliders, dense table rows from hawker_tables.py) plus prop positions in hawker_expanded.json. Look follows hawker_REF.md (Old Airport Road Food Centre).
Game coords (x, y up, z) map to Blender (x, -z, y). Every collider-bound shape uses the collider's own numbers.
Sign atlases come from hawker_signs.py (system python3 + PIL), run it first if assets/maps/hawker_tex is empty."""
import bpy, bmesh, sys, os, json, math, random
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
TEX = os.path.join(ROOT, 'assets', 'maps', 'hawker_tex')
OUT = os.path.join(ROOT, 'shots', 'maps_toy', 'hawker')
PREVIEW = 'preview' in sys.argv
os.makedirs(OUT, exist_ok=True); os.makedirs(TEX, exist_ok=True)
X = json.load(open(os.path.join(HERE, 'layouts', 'hawker_expanded.json')))
rnd = random.Random(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
V = Vector

# ---------------------------------------------------------------- materials (same recipe as heroes_toy mat())
def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c]

MATS = {}
def mat(name, hexcol='#ffffff', rough=.42, metal=0.0, coat=0.0, emit=0.0, alpha=1.0, img=None):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(hexcol), 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .08
    if emit:
        b.inputs['Emission Color'].default_value = (*srgb(hexcol), 1); b.inputs['Emission Strength'].default_value = emit
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha; m.surface_render_method = 'BLENDED'; m.use_backface_culling = True
    if img:
        t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(img)
        m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    MATS[name] = m; return m

def cmat(hexcol, rough=.42, coat=.15):
    """Flat plastic colour, one material per hex."""
    return mat('c_' + hexcol.lstrip('#').lower(), hexcol, rough, coat=coat)


# ---------------------------------------------------------------- geometry buckets (one mesh per group + material)
B = {}      # (group, matname) -> dict(v=[], f=[], uv=[])
def bucket(m, grp):
    k = (grp, m.name)
    if k not in B: B[k] = dict(m=m, v=[], f=[], uv=[])
    return B[k]

def emit(m, verts, faces, grp='MAP', uvs=None):
    b = bucket(m, grp); o = len(b['v']); b['v'].extend(verts)
    for i, f in enumerate(faces):
        b['f'].append([o + j for j in f]); b['uv'].append(uvs[i] if uvs else None)

_cache = {}
def _rbox(w, d, h, bev):
    k = (round(w, 4), round(d, 4), round(h, 4), bev)
    if k not in _cache:
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
        for v in bm.verts: v.co = V((v.co.x * w, v.co.y * d, v.co.z * h))
        bv = min(bev, w * .45, d * .45, h * .45)
        if bv > 0: bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bv, segments=2, profile=.5, affect='EDGES')
        bm.verts.index_update()
        _cache[k] = ([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces]); bm.free()
    return _cache[k]

def box(x, z, w, d, h, y0, m, bev=.05, grp='MAP'):
    """Axis box in game coords: centre x,z, size w (x) d (z) h (y), base at y0."""
    vs, fs = _rbox(w, d, h, bev); c = V((x, -z, y0 + h / 2)); emit(m, [v + c for v in vs], fs, grp)

def prism(x, z, w, d, h, y0, r, m, eb=.03, seg=5, grp='MAP', taper=0.0):
    """Rounded-rectangle column with a soft top edge. taper shrinks the base."""
    def ring(ins, y):
        ww, dd, rr = w / 2 - ins, d / 2 - ins, max(r - ins, .005); pts = []
        for cx, cy, a0 in ((ww - rr, dd - rr, 0), (-ww + rr, dd - rr, 90), (-ww + rr, -dd + rr, 180), (ww - rr, -dd + rr, 270)):
            for i in range(seg + 1):
                a = math.radians(a0 + 90 * i / seg); pts.append(V((x + cx + rr * math.cos(a), -z + cy + rr * math.sin(a), y)))
        return pts
    rings = [ring(eb + taper, y0), ring(taper, y0 + eb), ring(0, y0 + h - eb), ring(eb * .3, y0 + h - eb * .3), ring(eb, y0 + h)]
    n = len(rings[0]); vs = [p for rg in rings for p in rg]; fs = [list(range(n - 1, -1, -1))]
    for j in range(len(rings) - 1):
        for i in range(n): fs.append([j * n + i, j * n + (i + 1) % n, (j + 1) * n + (i + 1) % n, (j + 1) * n + i])
    fs.append([(len(rings) - 1) * n + i for i in range(n)]); emit(m, vs, fs, grp)

def lathe(x, z, y0, prof, m, seg=20, grp='MAP'):
    """Revolve (radius, height) points about the vertical axis. Ends are capped."""
    n = seg; vs = []
    for r, y in prof:
        for i in range(n):
            a = 2 * math.pi * i / n; vs.append(V((x + r * math.cos(a), -z + r * math.sin(a), y0 + y)))
    fs = [list(range(n - 1, -1, -1))]
    for j in range(len(prof) - 1):
        for i in range(n): fs.append([j * n + i, j * n + (i + 1) % n, (j + 1) * n + (i + 1) % n, (j + 1) * n + i])
    fs.append([(len(prof) - 1) * n + i for i in range(n)]); emit(m, vs, fs, grp)

def ball(x, y, z, rx, ry, rz, m, grp='MAP', seg=14):
    prof = [(math.sin(math.pi * j / (seg // 2)) * 1.0, -math.cos(math.pi * j / (seg // 2))) for j in range(1, seg // 2)]
    n = seg; vs = []
    for r, yy in prof:
        for i in range(n):
            a = 2 * math.pi * i / n; vs.append(V((x + rx * r * math.cos(a), -z + rz * r * math.sin(a), y + ry * yy)))
    fs = [list(range(n - 1, -1, -1))]
    for j in range(len(prof) - 1):
        for i in range(n): fs.append([j * n + i, j * n + (i + 1) % n, (j + 1) * n + (i + 1) % n, (j + 1) * n + i])
    fs.append([(len(prof) - 1) * n + i for i in range(n)]); emit(m, vs, fs, grp)

def quad(m, c, nrm, w, h, uv=(0, 0, 1, 1), up=(0, 0, 1), grp='MAP'):
    """Flat textured card. c and nrm are Blender coords. Faces nrm."""
    c, N, U = V(c), V(nrm).normalized(), V(up); R = U.cross(N).normalized()
    vs = [c - R * w / 2 - U * h / 2, c + R * w / 2 - U * h / 2, c + R * w / 2 + U * h / 2, c - R * w / 2 + U * h / 2]
    u0, v0, u1, v1 = uv; emit(m, vs, [[0, 1, 2, 3]], grp, [[(u0, v0), (u1, v0), (u1, v1), (u0, v1)]])

def floor_quad(m, x0, x1, z0, z1, y, tile=None, grp='MAP'):
    vs = [V((x0, -z0, y)), V((x1, -z0, y)), V((x1, -z1, y)), V((x0, -z1, y))]
    if (vs[1] - vs[0]).cross(vs[2] - vs[0]).z < 0: vs.reverse()
    emit(m, vs, [[0, 1, 2, 3]], grp, [[(v.x / tile, v.y / tile) for v in vs]] if tile else None)

# ---------------------------------------------------------------- palette (BRIEF Update 4: real place, see hawker_REF.md)
S = json.load(open(os.path.join(HERE, 'layouts', 'hawker_solids_v3.json')))
L = json.load(open(os.path.join(HERE, 'layouts', 'hawker.json')))['look']   # sun direction only

def floor_png(path, n=512):
    """2 x 2 light grey floor tiles (1.2 m repeat) with thin grout."""
    r = random.Random(5); img = np.empty((n, n, 3), np.float32); h = n // 2
    for i in range(2):
        for j in range(2):
            t = r.uniform(-.015, .015); c = (0.80, 0.57, 0.43) if (i + j) % 2 else (0.74, 0.49, 0.36); img[i * h:(i + 1) * h, j * h:(j + 1) * h] = [v + t for v in c]
    yy, xx = np.mgrid[0:n, 0:n]; g = np.minimum(np.minimum(xx % h, yy % h), h - 1 - np.maximum(xx % h, yy % h))
    img[g < 2] = (0.55, 0.36, 0.27)
    im = bpy.data.images.new('floor', n, n, alpha=False)
    im.pixels.foreach_set(np.concatenate([img ** 2.2, np.ones((n, n, 1), np.float32)], axis=2).ravel())
    im.filepath_raw = path; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
floor_png(os.path.join(TEX, 'floor.png'))

A = ['#3f9b6c', '#f0c040', '#e8843a', '#3f7fbf']   # REF 7 accent set: green, yellow, orange, blue
AM = [mat('acc_' + n, c, .32, coat=.4) for n, c in zip(('green', 'yellow', 'orange', 'blue'), A)]
tx = lambda n: os.path.join(TEX, n + '.png')
M = dict(
    floor=mat('floor_tile', img=tx('floor'), rough=.35, coat=.3), asph=mat('asphalt', '#6f7f95', .8), pave=mat('pavement', '#b8a07a', .7),
    grass=mat('grass', '#6fae5a', .8), court=mat('court_paving', '#c9784f', .5), mat_=mat('spawn_mat', '#d9a04e', .5),
    paint=mat('paint_yellow', '#d9b24e', .5), slab=mat('slab_mint', '#8cc9b0', .55), beam=mat('beam_green', '#3f9b6c', .55),
    tile=mat('tile_aqua', '#5fb0c4', .15, coat=.6), skirt=mat('skirting', '#3d6f80', .4), concrete=mat('concrete', '#c99a6e', .7),
    steel=mat('steel', '#d5d9dd', .25, metal=1.0), steelD=mat('steel_dark', '#8f959b', .35, metal=1.0), zinc=mat('zinc', '#7fa6c9', .35, metal=.6),
    white=mat('white', '#fbf8f0', .35, coat=.3), dark=mat('dark', '#2a2420', .5), glass=mat('glass', '#cfe8ee', .1, alpha=.35),
    mesh=mat('fence_mesh', '#7fae8c', .5, alpha=.5), top=mat('table_top', '#3f7fbf', .25, coat=.5), ped=mat('pedestal', '#b9bdc0', .4),
    leaf=mat('leaf', '#4aa24e', .45, coat=.2), leafD=mat('leaf_dark', '#2f7f43', .45, coat=.2), trunk=mat('trunk', '#8a6a4a', .6),
    terra=mat('terracotta', '#c96a48', .5), glow=mat('glow', '#fff6e0', emit=6.0), steam=mat('steam', '#ffffff', .9, alpha=.7),
    signs=mat('signs', img=tx('signs'), rough=.35, coat=.3), menus=mat('menus', img=tx('menus'), rough=.35, coat=.3),
    extras=mat('extras', img=tx('extras'), rough=.35, coat=.3), tissue=mat('tissue', '#ffffff', .5), soup=mat('soup', '#e2a94e', .3, coat=.5),
    hdb=mat('hdb_white', '#d98a78', .6), hdbwin=mat('hdb_window', '#7f8fa0', .2, coat=.6), binG=mat('bin_green', '#2f8d57', .4, coat=.3),
    binD=mat('bin_dark', '#1d5f4a', .4),
)
TRAYS = ['#d9534a', '#e3a92b', '#3f8fb5', '#8a5a44']; CRATE = ['#d9534a', '#3f8fb5', '#e3a92b', '#3f9b6c']
ROOF_Y = 7.2; ORG = {}
EX = lambda x, y, w, h: (x / 2048, 1 - (y + h) / 2048, (x + w) / 2048, 1 - y / 2048)
E_GRADE, E_NOSM, E_TRAY, E_WC, E_TR2, E_NAME = EX(0, 0, 512, 512), EX(512, 0, 512, 512), EX(1024, 0, 1024, 512), EX(0, 512, 1024, 256), EX(1024, 512, 1024, 256), EX(0, 768, 2048, 256)
def card(m, x, y, z, n, w, h, uv, grp='MAP'):
    """Sign card at game x,y,z facing game normal n=(nx,nz)."""
    quad(m, (x, -z, y), (n[0], -n[1], 0), w, h, uv, grp=grp)

# ---------------------------------------------------------------- shell: ground, floor, slab, beams, lights, upper storey, skyline
def tree(x, z, s=1.0):
    lathe(x, z, 0, [(.22 * s, 0), (.16 * s, 3 * s)], M['trunk'], 8, 'HDB')
    for j, (ox, oy, oz, r) in enumerate(((0, 4.2, 0, 2.1), (1.2, 3.4, .5, 1.5), (-1.1, 3.5, -.6, 1.6))):
        ball(x + ox * s, oy * s, z + oz * s, r * s, r * s * .85, r * s, M['leaf'] if j else M['leafD'], 'HDB', 10)

def shell():
    floor_quad(M['asph'], -200, 200, -200, 200, -.04); floor_quad(M['pave'], -52, 52, -36, 36, -.02)
    floor_quad(M['floor'], -45.3, 45.3, -23.8, 23.8, 0, tile=1.2)
    for s in (-1, 1): floor_quad(M['asph'], -45.3, 45.3, s * 23.8, s * 30.1, 0)
    floor_quad(M['court'], -5.2, 5.2, -5.2, 5.2, .004)
    for sx in (-41, 41): floor_quad(M['mat_'], sx - 2.5, sx + 2.5, -5.5, 5.5, .004)
    # slab with a skylight over the courtyard (REF 4), kerb and glazing bars
    for cx, cz, w, d in ((-25.75, 0, 39.5, 47.6), (25.75, 0, 39.5, 47.6), (0, 13.4, 12, 20.8), (0, -13.4, 12, 20.8)): box(cx, cz, w, d, .4, ROOF_Y, M['slab'], .05, 'ROOF')
    for s in (-1, 1):
        box(0, s * 3.15, 12.6, .3, .9, ROOF_Y, M['beam'], .04, 'ROOF'); box(s * 6.15, 0, .3, 6, .9, ROOF_Y, M['beam'], .04, 'ROOF')
        box(0, s * 23.95, 91.6, .3, .5, 6.8, M['paint'], .05, 'ROOF'); box(0, s * 23.95, 91.6, .34, .5, 7.3, AM[2], .05, 'ROOF')
        box(s * 45.65, 0, .3, 48.2, .5, 6.8, M['paint'], .05, 'ROOF'); box(s * 45.65, 0, .34, 48.2, .5, 7.3, AM[2], .05, 'ROOF')
    for bx in (-4, -2, 0, 2, 4): box(bx, 0, .1, 6, .12, ROOF_Y + .8, M['steelD'], 0, 'ROOF')
    x = -43.5   # beam grid (REF 2), bottoms at 6.8 so pillar tops meet it
    while x <= 43.5 + 1e-6:
        if abs(x) < 6:
            for s in (-1, 1): box(x, s * 13.4, .3, 20.6, .4, 6.8, M['beam'], .03, 'ROOF')
        else: box(x, 0, .3, 47.4, .4, 6.8, M['beam'], .03, 'ROOF')
        x += 4
    for z in (-13, -4.5, 4.5, 13): box(0, z, 90.8, .3, .4, 6.8, M['beam'], .03, 'ROOF')
    # second storey shop ring above the stall rows (REF: shops upstairs)
    for s in (-1, 1):
        box(0, s * 19.8, 91, 8, 3.2, 7.6, M['hdb'], .06, 'ROOF'); box(0, s * 19.8, 91.3, 8.3, .4, 10.8, AM[3], .06, 'ROOF'); box(0, s * 19.8, 92, 9, .25, 11.2, M['slab'], .05, 'ROOF')
        for i, x in enumerate(range(-42, 43, 6)):
            for f in (-1, 1):
                box(x, s * 19.8 + f * 4.02, 2.2, .06, 2.3, 7.6, AM[i % 4], 0, 'ROOF'); box(x + 2.4, s * 19.8 + f * 4.02, 1.8, .06, 1.1, 8.6, M['hdbwin'], 0, 'ROOF')
    fans = [(p['x'], p['z']) for p in X['props'] if p['k'] == 'fan']
    for p in X['props']:
        if p['k'] != 'tube' or (abs(p['x']) < 7 and abs(p['z']) < 4) or any(math.hypot(p['x'] - fx, p['z'] - fz) < 2.4 for fx, fz in fans): continue
        box(p['x'], p['z'], 1.75, .2, .06, 6.2, M['white'], .02, 'LIGHTS'); box(p['x'], p['z'], 1.6, .08, .06, 6.15, M['glow'], .02, 'LIGHTS')
        for dx in (-.6, .6): box(p['x'] + dx, p['z'], .02, .02, .55, 6.26, M['steelD'], 0, 'LIGHTS')
    for i, (fx, fz) in enumerate(fans): fan(i, fx, fz)
    # skyline: white HDB slab blocks with corridor bands, a coloured stair core and a block number
    for i, o in enumerate(X['outside']):
        if o['k'] != 'hdb': continue
        g = 'HDB_FRONT' if o['z'] > 30 else 'HDB'; lx = o['w'] > o['d']
        box(o['x'], o['z'], o['w'], o['d'], o['h'], 0, cmat(('#d98a78', '#7fb2d6', '#d9b862', '#86c296')[(i + 1) % 4], .6, 0), .2, g); box(o['x'], o['z'], o['w'] + .6, o['d'] + .6, .6, o['h'], AM[i % 4], .1, g)
        for y in np.arange(2.2, o['h'] - 1.5, 2.9):
            if lx: box(o['x'], o['z'], o['w'] - 3.4, o['d'] + .12, 1.2, y, M['hdbwin'], 0, g)
            else: box(o['x'], o['z'], o['w'] + .12, o['d'] - 3.4, 1.2, y, M['hdbwin'], 0, g)
        n = (0, -1 if o['z'] > 0 else 1) if lx else (-1 if o['x'] > 0 else 1, 0)
        if lx:
            cx, cz = o['x'] - o['w'] / 2 + 1.1, o['z'] + n[1] * (o['d'] / 2 + .1); box(cx, cz, 2.0, .3, o['h'], 0, AM[i % 4], .05, g)
            card(M['extras'], cx + 4, o['h'] - 3.2, cz, n, 4, 4, EX((i % 4) * 256, 1024, 256, 256), g)
        else:
            cx, cz = o['x'] + n[0] * (o['w'] / 2 + .1), o['z'] - o['d'] / 2 + 1.1; box(cx, cz, .3, 2.0, o['h'], 0, AM[i % 4], .05, g)
            card(M['extras'], cx, o['h'] - 3.2, cz + 4, n, 4, 4, EX((i % 4) * 256, 1024, 256, 256), g)
    for x, z in ((-30, 35), (30, -35)): tree(x, z, .8)   # Nigel: less greenery, two street trees only

def fan(i, x, z):
    """Large slow ceiling fan (REF: HVLS fans added in 2024). One object, origin on its axis."""
    g = 'FAN_%02d' % i; ORG[g] = (x, -z, 6.3)
    box(x, z, .06, .06, .5, 6.3, M['steel'], 0, g); lathe(x, z, 6.2, [(.12, 0), (.24, .03), (.24, .14), (.14, .18)], M['steel'], 16, g)
    for k in range(5):
        a = k * 2 * math.pi / 5; ca, sa = math.cos(a), math.sin(a); vs = []
        for u, w in ((.2, .06), (.6, .11), (1.9, .12), (2.05, .07)):
            for sgn in (-1, 1): vs.append(V((x + ca * u - sa * w * sgn, -z + sa * u + ca * w * sgn, 6.27 + .025 * sgn)))
        t = [v + V((0, 0, .02)) for v in vs]; n = len(vs)
        emit(M['steel'], vs + t, [[0, 1, 3, 2], [2, 3, 5, 4], [4, 5, 7, 6], [n + 2, n + 3, n + 1, n], [n + 4, n + 5, n + 3, n + 2], [n + 6, n + 7, n + 5, n + 4]], g)

# ---------------------------------------------------------------- stalls (collider: counter 6.6x2x1.1, wall 7.4x.6x6.8, awning 6.9x1.24 at 3.25)
NST = [0]
def stall(p, ci):
    x, z = p['x'], p['z']; side = (-1 if p.get('in') else 1) * (1 if z > 0 else -1); acc = AM[ci % 4]
    front = z - side; wzc = z + side * 1.9; wz = wzc - side * .3; ny = side; cs = -side   # cs: customer's left to right along x
    box(x, z, 6.6, 2, 1.03, 0, acc, .05); box(x, z, 6.6, 2, .07, 1.03, M['steel'], .02)
    box(x, front, 6.3, .04, .12, .62, M['white'], .015); box(x, front, 6.4, .04, .12, 0, M['skirt'], 0)
    box(x, wzc, 7.4, .6, 3.3, 0, M['tile'], .04); box(x, wzc, 7.4, .6, 2.9, 3.3, M['paint'], .04)
    box(x, wzc, 7.4, .6, .3, 6.2, acc, .04); box(x, wzc, 7.4, .6, .3, 6.5, M['paint'], .04)
    box(x, wz - side * .4, 7.4, .5, .5, 5.0, M['steel'], .05); box(x - 2.2 * cs, wz - side * .4, .4, .4, 1.6, 3.4, M['steel'], .04)   # exhaust duct (REF: mechanical exhaust)
    # signboard lightbox standing on the awning front edge, menu board and hygiene grade on the wall
    sz = z + side * .31; box(x, sz, 5.76, .14, 1.56, 3.35, acc, .03)
    c, rw = ci % 2, ci // 2; quad(M['signs'], (x, -(sz - side * .075), 4.13), (0, ny, 0), 5.6, 1.4, (c / 2, 1 - (rw + 1) / 8, (c + 1) / 2, 1 - rw / 8))
    mx = x + 1.7 * cs; box(mx, wz - side * .02, 1.62, .04, 1.62, 1.19, M['dark'], .015)
    c, rw = ci % 4, ci // 4; quad(M['menus'], (mx, -(wz - side * .045), 2.0), (0, ny, 0), 1.5, 1.5, (c / 4, 1 - (rw + 1) / 4, (c + 1) / 4, 1 - rw / 4))
    quad(M['extras'], (x - .1 * cs, -(wz - side * .012), 2.1), (0, ny, 0), .5, .5, E_GRADE)
    for sy in (1.5, 2.3): box(x - 1.9 * cs, wz - side * .15, 2.4, .3, .04, sy, M['steel'], .01)
    for j in range(5): lathe(x - (1.0 + j * .42) * cs, wz - side * .15, 1.54, [(.12, 0), (.13, .02), (.13, .2), (.1, .22)], cmat(TRAYS[(ci + j) % 4], .35, .3), 10)
    az = z + side * .85; box(x, az, 6.9, 1.24, .1, 3.25, acc, .04); box(x, az, 3, .1, .06, 3.17, M['glow'], .02)
    for dx in (-3.37, 3.37): box(x + dx, (wz + az - side * .62) / 2, .14, abs(wz - (az - side * .62)), .8, 2.45, M['paint'], .04)
    # glass display case, stockpots with steam (separate STEAM_ objects), bowls, sauce bottles, trays
    gx, gz = x - .5 * cs, z - side * .5
    box(gx, gz, .9, .5, .42, 1.1, M['glass'], .02); box(gx, gz, .94, .54, .04, 1.52, M['steel'], .01)
    for j in range(3): ball(gx + (j - 1) * .26, 1.2, gz, .1, .08, .1, cmat(('#e9c47a', '#c96a48', '#8fbf78')[(j + ci) % 3], .5, .1), seg=8)
    g = 'STEAM_%02d' % NST[0]; NST[0] += 1; ORG[g] = (x - 1.8 * cs, -(z + side * .3), 2.0)
    for k, (dx, s) in enumerate(((-2.2, 1.0), (-1.35, .72))):
        px, pz = x + dx * cs, z + side * .3
        lathe(px, pz, 1.1, [(.3 * s, 0), (.34 * s, .03), (.34 * s, .5 * s), (.36 * s, .52 * s), (.36 * s, .55 * s)], M['steel'], 16)
        lathe(px, pz, 1.1 + .55 * s, [(.36 * s, 0), (.3 * s, .05 * s), (.08 * s, .09 * s), (.05 * s, .15 * s), (.03 * s, .16 * s)], M['steel'], 16)
        for ox, oy, rr in ((0, .95, .16), (.1, 1.25, .21), (-.06, 1.6, .26)): ball(px + ox * s, 1.2 + oy * s, pz, rr * s, rr * s * .85, rr * s, M['steam'], g, 12)
    for j in range(4): lathe(x + 1.2 * cs, z + side * .35, 1.1 + j * .045, [(.07, 0), (.1, .01), (.15, .09), (.14, .09)], M['white'], 12)
    for j, c2 in enumerate(('#d23b2a', '#3a2418', '#e3c46a')):
        lathe(x + (.3 + j * .17) * cs, z - side * .6, 1.1, [(.045, 0), (.05, .01), (.05, .16), (.02, .2), (.025, .25)], cmat(c2, .25, .6), 8)
    for j in range(3): box(x + 2.5 * cs, z + side * .1, .52, .38, .03, 1.1 + j * .032, cmat(TRAYS[(ci + j) % 4], .35, .3), .012)

# ---------------------------------------------------------------- furniture and fixtures, one per collider
NT = [0]; ZONES = [(q['x'], q['z']) for q in X['zones']]
def table(x, z):
    zone = (x, z) in ZONES; i = NT[0]; NT[0] += 1
    prism(x, z, 1.5, 1.5, .1, .76, .12, AM[2] if zone else TOPC(x, z), .025); prism(x, z, .5, .5, .76, 0, .12, M['ped'], .03)
    quad(M['extras'], (x, -z, .862), (0, 0, 1), .34, .34, EX((i % 8) * 128, 1280 + (i // 8 % 4) * 128, 128, 128), up=(0, 1, 0))
    # no plates, trays or cups on tables (Nigel 2026-11-16)

TOPC = lambda x, z: (M['top'], AM[1], M['top'], AM[0])[(x > 0) * 2 + (z > 0)]   # blue, yellow, blue, green halls
def stool(x, z):
    t = min(ZONES + TABS, key=lambda q: (q[0] - x) ** 2 + (q[1] - z) ** 2)
    prism(x, z, .5, .5, .1, .34, .23, AM[2] if t in ZONES else TOPC(*t), .03, seg=4); prism(x, z, .2, .2, .34, 0, .09, M['ped'], .02, seg=3)

def dado(x, z, w, d, h, th=1.5, acc=0, top=None):
    """Tiled lower wall, accent line, white paint above. Same footprint as the collider."""
    box(x, z, w, d, .15, 0, M['skirt'], .03); box(x, z, w, d, th - .15, .15, M['tile'], .03); box(x, z, w, d, .12, th, AM[acc], .03)
    box(x, z, w, d, h - th - .12, th + .12, top or M['paint'], .04)

def rack(x, z, w, d, h, i):
    ax = d > w; Ln, Th = (d, w) if ax else (w, d)
    def bx(l, t, sl, st, hh, y, m, bev=.01): box(x + (t if ax else l), z + (l if ax else t), st if ax else sl, sl if ax else st, hh, y, m, bev)
    if i % 2: dado(x, z, w, d, h, 1.2, i % 4); return
    for y in (0, .5, 1.0, 1.5, h - .05): bx(0, 0, Ln, Th, .05, y, M['steel'])
    for sl in (-1, 1):
        for st in (-1, 1): bx(sl * (Ln / 2 - .04), st * (Th / 2 - .04), .08, .08, h, 0, M['steelD'], 0)
    bx(0, 0, Ln - .1, .04, h, 0, M['steelD'], 0)
    for y in (.05, .55, 1.05, 1.55):
        for q in (-.8, 0, .8):
            if rnd.random() < .8: bx(q + rnd.uniform(-.08, .08), 0, .5, Th - .1, .03 * rnd.randint(2, 7), y, cmat(TRAYS[rnd.randrange(4)], .35, .3))

def fence(x, z, w, d, h):
    ax = d > w; Ln = max(w, d)
    box(x, z, w, d, 1.2, 0, M['concrete'], .04); box(x, z, w, d, .25, h - .25, M['concrete'], .04)
    box(x, z, .06 if ax else w - .1, d - .1 if ax else .06, h - 1.45, 1.2, M['mesh'], 0)
    n = max(2, round(Ln / 3)) 
    for k in range(n + 1):
        q = -Ln / 2 + .15 + k * (Ln - .3) / n; box(x + (0 if ax else q), z + (q if ax else 0), .6 if ax else .3, .3 if ax else .6, h - 1.45, 1.2, M['concrete'], .03)

def island(x, z, w, d, h, i):
    box(x, z, w, d, .15, 0, M['skirt'], .03); box(x, z, w, d, 1.85, .15, M['tile'], .04); box(x, z, w, d, h - 2.06, 2.0, AM[(i * 2 + 2) % 4], .04); box(x, z, w, d, .06, h - .06, M['skirt'], .03)
    for s in (-1, 1):
        fz = z + s * d / 2
        for j, dx in enumerate((-3.3, 0, 3.3)):
            k = (i * 6 + (s > 0) * 3 + j); shut = k % 4 == 3
            box(x + dx, fz + s * .01, 2.6, .04, 1.0, .95, M['zinc'] if shut else M['dark'], 0); box(x + dx, fz + s * .03, 2.8, .08, .06, .9, M['steel'], .01)
            c, rw = k % 2, (k % 16) // 2; card(M['signs'], x + dx, 2.3, fz + s * .012, (0, s), 2.2, .55, (c / 2, 1 - (rw + 1) / 8, (c + 1) / 2, 1 - rw / 8))
            if not shut:
                c, rw = k % 4, (k % 16) // 4; card(M['menus'], x + dx + .75, 1.45, fz + s * .035, (0, s), .8, .8, (c / 4, 1 - (rw + 1) / 4, (c + 1) / 4, 1 - rw / 4))
                box(x + dx - .4, fz + s * .035, 1.4, .02, .05, 1.85, M['glow'], 0)
            card(M['extras'], x + dx - 1.55, 1.5, fz + s * .012, (0, s), .34, .34, E_GRADE)
    for s in (-1, 1): card(M['extras'], x + s * (w / 2 + .012), 1.45, z, (s, 0), .7, .7, E_NOSM)

def draw(s, i):
    x0, y0, z0, x1, y1, z1 = s[:6]; f = s[6] if len(s) > 6 else ''
    x, z, w, d, h = (x0 + x1) / 2, (z0 + z1) / 2, x1 - x0, z1 - z0, y1 - y0; k = (round(w, 2), round(d, 2), round(h, 2)); sx = 1 if x > 0 else -1; sz = 1 if z > 0 else -1
    if f == 'i':   # lane canopy: zinc sheet cantilevered above head height
        box(x, z, w, d, h, y0, M['zinc'], .03, 'CANOPY'); box(x, z + sz * (d / 2 - .05), w, .1, .3, y0 - .3, AM[0], .03, 'CANOPY')
    elif k == (.48, .48, .44): stool(x, z)
    elif k == (1.5, 1.5, .86): table(x, z)
    elif k in ((6.6, 2.0, 1.1), (7.4, .6, 6.8), (6.9, 1.24, .1)): pass   # drawn by stall()
    elif k == (.9, .9, 6.8):
        dado(x, z, w, d, 2.1, 1.5, (i + 1) % 4, AM[i % 4]); box(x, z, w, d, h - 2.1, 2.1, AM[i % 4], .04)
        if i % 3 == 0: card(M['extras'], x - sx * (w / 2 + .012), 2.6, z, (-sx, 0), .5, .5, E_NOSM)
    elif k in ((.8, 2.6, 2.0), (2.6, .8, 2.0)):
        if not any(q[0] < x < q[3] and q[2] < z < q[5] and q[4] > 2.5 and q[3] - q[0] == 10 for q in S): rack(x, z, w, d, h, i)
    elif k in ((.6, 6.6, 4.5), (90.6, .6, 4.5)): fence(x, z, w, d, h)
    elif k in ((2.1, .6, 3.0), (6.5, .6, 3.0)): dado(x, z, w, d, h, 1.2, 0)
    elif k == (.6, 8.0, 3.0):
        dado(x, z, w, d, h, 1.2, 3)
        card(M['extras'], x - sx * .312, 2.1, z, (-sx, 0), .9, .9, E_NOSM); card(M['extras'], x + sx * .312, 2.1, z, (sx, 0), .9, .9, E_NOSM)
    elif k == (.8, 47.6, 6.8):
        dado(x, z, w, d, h, 1.5, 2); xi = x - sx * .4
        box(xi - sx * .03, 0, .06, 14.4, 2.0, 4.0, AM[2], .02); card(M['extras'], xi - sx * .07, 5.0, 0, (-sx, 0), 14, 1.75, E_NAME)
    elif k == (5.0, 13.0, 6.8):   # corner blocks: toilets on two, stores with roller shutters on the others
        dado(x, z, w, d, h, 1.5, 3 if sx * sz > 0 else 1); xi = x - sx * (w / 2 + .012); zc = z + sz * 1.5
        if sx * sz > 0:
            card(M['extras'], xi, 3.3, zc, (-sx, 0), 4, 1, E_WC)
            for j, (dz, c, px) in enumerate(((-1.3, '#2b5fa8', 1024), (1.3, '#c2477f', 1280))):
                box(xi, zc + dz, .03, 1.2, 2.2, 0, cmat(c, .35, .3), 0); card(M['extras'], xi - sx * .02, 1.6, zc + dz, (-sx, 0), .5, .5, EX(px, 1024, 256, 256))
        else:
            for dz in (-1.6, 1.6): box(xi, zc + dz, .03, 2.6, 2.6, 0, M['zinc'], 0)
    elif k == (1.6, 1.6, 2.2):   # stacked drink crates
        for a in (-.4, .4):
            for b in (-.4, .4):
                for t in range(4): box(x + a, z + b, .8, .8, .55, t * .55, cmat(CRATE[rnd.randrange(4)], .4, .3), .04)
    elif k == (1.2, .8, 1.05):
        for a in (-.3, .3):
            box(x + a, z, .6, .8, .55, 0, cmat(CRATE[rnd.randrange(4)], .4, .3), .04); box(x + a, z, .6, .8, .5, .55, cmat(CRATE[rnd.randrange(4)], .4, .3), .04)
    elif k == (1.3, 1.1, 1.3): box(x, z, w, d, h - .16, 0, M['binG'], .05); box(x, z, w, d, .16, h - .16, M['binD'], .04)
    elif k == (.64, .64, .55):
        prism(x, z, .64, .64, .55, 0, .2, M['terra'], .04, taper=.05)
        for j in range(3):
            a = j / 3 * 6.283; ball(x + math.cos(a) * .08, .68, z + math.sin(a) * .08, .14, .14, .14, M['leaf'] if j % 2 else M['leafD'], seg=8)
    elif k == (.62, .62, .88): prism(x, z, .62, .62, .78, 0, .2, M['binG'], .03, taper=.04); prism(x, z, .62, .62, .1, .78, .2, M['binD'], .03)
    elif k == (1.5, 1.5, .8):   # umbrella table (REF 8): top at collider height, canopy above head height
        prism(x, z, 1.5, 1.5, .08, .72, .12, M['top'], .025); prism(x, z, .5, .5, .72, 0, .12, M['ped'], .03)
        lathe(x, z, .8, [(.035, 0), (.035, 1.9)], M['steelD'], 8); lathe(x, z, 2.35, [(1.7, 0), (1.72, .05), (.06, .62), (.03, .7)], AM[i % 4], 8, 'UMB')
    elif k == (6.0, 2.4, 3.0): box(x, z, w, d, h - .5, .5, AM[1], .05); box(x, z, w - .3, d - .2, .5, 0, M['dark'], .04); box(x, z, w + .02, d + .02, .5, 1.6, AM[3], 0)
    elif k == (1.8, 2.3, 2.4):
        box(x, z, w, d, h - .5, .5, AM[3], .05); box(x, z, w - .2, d - .2, .5, 0, M['dark'], .04); box(x, z, w + .02, d - .3, .7, 1.45, M['hdbwin'], 0)
    elif k == (4.8, 5.2, .9): box(x, z, w, d, h - .1, 0, M['concrete'], .04); box(x, z, w, d, .1, h - .1, AM[1], .03)
    elif k == (6.0, 3.2, 2.8):   # bin centre
        dado(x, z, w, d, h, 1.2, 0); box(x, z - sz * (d / 2 + .01), 3.2, .03, 2.3, 0, M['binG'], 0)
    elif k == (3.5, 4.0, 2.6):   # exhaust plant
        box(x, z, w, d, h, 0, M['steel'], .05)
        for y in np.arange(.5, 2.2, .3): box(x, z - sz * (d / 2 + .01), 2.6, .03, .12, y, M['steelD'], 0)
    elif k == (4.0, 2.2, 1.9): box(x, z, w, d, h - .2, 0, M['binG'], .05); box(x, z, w, d, .2, h - .2, M['binD'], .04)
    elif k == (1.0, .8, 1.6):
        box(x, z, w, d, h, 0, AM[3], .05); box(x - .08, z - sz * .395, .68, .03, .9, .55, M['glow'], .02); box(x + .36, z - sz * .395, .16, .03, .3, .8, M['dark'], .01)
    elif k in ((4.0, .6, 1.0), (.6, 4.0, 1.0)):   # courtyard planter ring (REF 5)
        box(x, z, w, d, .15, 0, M['skirt'], .03); box(x, z, w, d, .73, .15, M['tile'], .04); box(x, z, w, d, .12, .88, M['concrete'], .04)
    elif k == (10.0, 4.0, 2.6): island(x, z, w, d, h, int(x > 0))
    elif k == (2.0, 1.5, 1.1):   # tray return station (REF 11) with the four-language sign hung above
        box(x, z, w, d, 1.04, 0, M['steel'], .04); box(x, z, w, d, .06, 1.04, M['steelD'], .02)
        for j, q in enumerate((-.5, .1)): box(x + q, z, .52, .38, .04 * (4 + j * 3), 1.1, cmat(TRAYS[j], .35, .3), .012)
        for s2 in (-1, 1):
            box(x, z + s2 * (d / 2 + .005), 1.9, .02, .6, .3, AM[0], 0); card(M['extras'], x, .6, z + s2 * (d / 2 + .02), (0, s2), 1.8, .45, E_TR2)
            card(M['extras'], x + s2 * .04, 3.4, z, (s2, 0), 2.0, 1.0, E_TRAY); box(x, z + s2 * .8, .03, .03, 2.9, 3.9, M['steelD'], 0)
        box(x, z, .06, 2.06, 1.06, 2.87, AM[0], .02)
    else:
        print('UNMATCHED', k, x, z); box(x, z, w, d, h, y0, M['concrete'], .05)

# ---------------------------------------------------------------- build
TABS = [((s[0] + s[3]) / 2, (s[2] + s[5]) / 2) for s in S if round(s[3] - s[0], 2) == 1.5 and round(s[4], 2) == .86]
shell()
for i, s in enumerate(S): draw(s, i)
SP = [p for p in X['props'] if p['k'] == 'stall']
RW = sorted([p for p in SP if 'row' not in p], key=lambda p: ((p['z'] > 0), p['x']))
for p in SP: stall(p, RW.index(p) if 'row' not in p else (p['row'] if p['x'] < 0 else p.get('mrow', p['row'])))

# collider check: every v2 solid has a visual top with the same footprint, within 5 cm
from mathutils.bvhtree import BVHTree
SKIP = ('ROOF', 'CANOPY', 'LIGHTS', 'FAN', 'STEAM', 'HDB', 'UMB'); bv, bf = [], []
for (grp, mn), b in B.items():
    if grp.startswith(SKIP): continue
    o = len(bv); bv.extend(b['v']); bf.extend([[o + j for j in f] for f in b['f']])
bvh = BVHTree.FromPolygons(bv, bf); bad = []; nchk = 0
def top_at(px, pz, y):
    hit = bvh.ray_cast(V((px, -pz, y + .25)), V((0, 0, -1)))[0]; return hit.z if hit else -9
for s in S:
    if len(s) > 6 and s[6] == 'i': continue
    x0, y0, z0, x1, y1, z1 = s[:6]; nchk += 1; e = .07
    ins = [abs(top_at(px, pz, y1) - y1) <= .05 for px in (x0 + e, x1 - e) for pz in (z0 + e, z1 - e)]
    out = []
    for px, pz in ((x0 - e, (z0 + z1) / 2), (x1 + e, (z0 + z1) / 2), ((x0 + x1) / 2, z0 - e), ((x0 + x1) / 2, z1 + e)):
        if any(q is not s and q[0] <= px <= q[3] and q[2] <= pz <= q[5] for q in S): continue
        out.append(abs(top_at(px, pz, y1) - y1) > .05)
    if not (all(ins) and all(out)): bad.append(([round(v, 2) for v in s[:6]], ins, out))
print('COLLIDER CHECK %d solids, %d pass, %d fail' % (nchk, nchk - len(bad), len(bad)))
for b in bad[:30]: print('  FAIL', b)
NEW = [s for s in S if (round(s[3] - s[0], 2), round(s[5] - s[2], 2), round(s[4] - s[1], 2)) in ((10, 4, 2.6), (4, .6, 1), (.6, 4, 1), (2, 1.5, 1.1), (1.5, 1.5, .8), (.6, 8, 3))]
for n in NEW:
    for q in S:
        cx, cz = (q[0] + q[3]) / 2, (q[2] + q[5]) / 2
        if q is not n and n[0] < cx < n[3] and n[2] < cz < n[5]: print('INSIDE NEW COLLIDER', [round(v, 2) for v in q[:6]], 'in', n[:6])
    for p in X['props']:
        if p['k'] not in ('stall', 'tube', 'fan') and n[0] - .3 < p['x'] < n[3] + .3 and n[2] - .3 < p['z'] < n[5] + .3: print('PROP IN NEW COLLIDER', p)

col = bpy.data.collections.new('hawker'); SC.collection.children.link(col); OBJ = {}
for (grp, mn), b in B.items():
    me = bpy.data.meshes.new(grp + '_' + mn); org = V(ORG.get(grp, (0, 0, 0)))
    me.from_pydata([tuple(v - org) for v in b['v']], [], b['f']); me.materials.append(b['m'])
    if any(u is not None for u in b['uv']):
        uv = me.uv_layers.new(name='UVMap'); flat = []
        for f, u in zip(b['f'], b['uv']):
            for i in range(len(f)): flat.extend(u[i] if u else (0, 0))
        uv.data.foreach_set('uv', flat)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons)); me.update()
    ob = bpy.data.objects.new(grp + '_' + mn, me); ob.location = org; col.objects.link(ob); OBJ.setdefault(grp, []).append(ob)
    wn = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.weight = 60; wn.keep_sharp = False
for grp, obs in list(OBJ.items()):   # one object per moving part (FAN_xx, STEAM_xx)
    if not grp.startswith(('FAN_', 'STEAM_')): continue
    if len(obs) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs: o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]; bpy.ops.object.join(); OBJ[grp] = [obs[0]]
    obs[0].name = grp

dg = bpy.context.evaluated_depsgraph_get()
tris = sum(len(o.evaluated_get(dg).data.loop_triangles) or sum(len(p.vertices) - 2 for p in o.data.polygons) for o in col.objects)
print('HAWKER draws', sum(len(o.material_slots) for o in col.objects)); print('HAWKER tris', tris, 'materials', len({s.material.name for o in col.objects for s in o.material_slots}), 'objects', len(col.objects))

# ---------------------------------------------------------------- export (map only)
bpy.ops.object.select_all(action='DESELECT')
for o in col.objects: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'maps', 'hawker.glb'), export_format='GLB', use_selection=True,
                          export_apply=True, export_yup=True, export_image_format='AUTO', export_animations=False)

# ---------------------------------------------------------------- lighting and shots
def look_at(o, t):
    o.rotation_euler = (V(t) - o.location).to_track_quat('-Z', 'Y').to_euler()

w = bpy.data.worlds.new('World'); SC.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (.45, .62, .95, 1); bg.inputs[1].default_value = .8
sx, sy, sz = L['sun'][2] if isinstance(L['sun'][-1], (list, tuple)) else L['sun']
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.6; sd.color = (1.0, .9, .74); sd.angle = math.radians(2.5)
sun = bpy.data.objects.new('sun', sd); SC.collection.objects.link(sun); sun.location = (sx, -sz, sy); look_at(sun, (0, 0, 0))
HALL = []
for ax in (-30, -10, 10, 30):
    for az in (-11, 11):
        d = bpy.data.lights.new('hall', 'AREA'); d.shape = 'RECTANGLE'; d.size = 16; d.size_y = 16; d.energy = 4500; d.color = (1.0, .93, .82)
        o = bpy.data.objects.new('hall', d); SC.collection.objects.link(o); o.location = (ax, -az, 6.7); HALL.append(o)
        u = bpy.data.lights.new('bounce', 'AREA'); u.shape = 'RECTANGLE'; u.size = 16; u.size_y = 16; u.energy = 2200; u.color = (1.0, .9, .76)
        o = bpy.data.objects.new('bounce', u); SC.collection.objects.link(o); o.location = (ax, -az, 4.2); o.rotation_euler = (math.pi, 0, 0)
SC.render.engine = 'BLENDER_EEVEE'; SC.eevee.taa_render_samples = 12 if PREVIEW else 24
SC.view_settings.view_transform = 'AgX'; SC.view_settings.look = 'AgX - Punchy'; SC.view_settings.exposure = -.35
SC.render.image_settings.file_format = 'PNG'
for k, v in (('use_shadows', True), ('use_raytracing', True), ('shadow_ray_count', 2), ('shadow_step_count', 8)):
    try: setattr(SC.eevee, k, v)
    except Exception: pass
cd = bpy.data.cameras.new('cam'); cd.clip_start = .1; cd.clip_end = 600; cam = bpy.data.objects.new('cam', cd); SC.collection.objects.link(cam); SC.camera = cam

def hide(groups, on=True):
    for g, obs in OBJ.items():
        if g.startswith(tuple(groups)):
            for o in obs: o.hide_render = on

def hero(name, x, z, face):
    """Import a toy hero for scale. face = game (x, z) point it looks at."""
    p = os.path.join(ROOT, 'assets', 'heroes', name + '.glb')
    if not os.path.exists(p): return
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p)
    roots = [o for o in set(bpy.data.objects) - before if o.parent is None]
    dx, dy = face[0] - x, -(face[1] - z); a = math.atan2(-dx, dy)
    for o in roots:
        o.rotation_mode = 'XYZ'; o.matrix_world = Matrix.Translation((x, -z, 0)) @ Matrix.Rotation(a, 4, 'Z') @ o.matrix_world

def shoot(name, pos, tgt, lens=24, w=1600, h=900, ortho=None):
    cam.location = (pos[0], -pos[2], pos[1]); look_at(cam, (tgt[0], -tgt[2], tgt[1])); cd.lens = lens
    cd.type = 'ORTHO' if ortho else 'PERSP'
    if ortho: cd.ortho_scale = ortho
    SC.render.resolution_x = w; SC.render.resolution_y = h
    SC.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True)

ONLY = [a for a in sys.argv if a.startswith('only=')]; ONLY = ONLY[0][5:].split(',') if ONLY else None
def want(n): return not ONLY or n in ONLY
hero('ahma', -20.6, -18.6, (-27, -18.2)); hero('tarik', -17.6, -19.3, (-27, -18.2)); hero('siao', -22.4, -19.2, (-22.2, -21))
hero('gym', -15.8, 1.2, (-22, 1)); hero('ahma', -12.6, -2.6, (-22, 1))
if want('ground_a'): shoot('ground_a', (-27.2, 1.6, -18.0), (-10, 1.9, -19.6), lens=20)          # south stall lane
if want('ground_b'): shoot('ground_b', (-22.0, 1.6, 1.6), (0, 1.5, 0), lens=20)                   # centre lane to the courtyard
if want('detail'): shoot('detail', (-17.6, 1.7, -15.6), (-22.6, 2.3, -21.6), lens=24)             # stall front close-up
if want('table'): shoot('table', (-15.6, 1.9, -2.6), (-17.9, .5, -5.22), lens=28)                 # one table set: stools face each other, no plates
# overview and top view: roof lifted off, like a playset with the lid removed
hide(['ROOF', 'CANOPY', 'HDB_FRONT', 'LIGHTS'])
for o in HALL: o.data.energy = 1800
if want('overview'): shoot('overview', (-38, 62, 66), (0, 0, 3), lens=30)
if want('topdown_check'):
    hide(['FAN', 'UMB', 'HDB', 'STEAM']); vs, fs = [], []; t = .07
    for s in S:
        x0, _, z0, x1, _, z1 = s[:6]
        for a, b, c, d in ((x0, z0, x1, z0 + t), (x0, z1 - t, x1, z1), (x0, z0, x0 + t, z1), (x1 - t, z0, x1, z1)):
            o = len(vs); vs += [(a, -b, 60), (c, -b, 60), (c, -d, 60), (a, -d, 60)]; fs.append([o, o + 1, o + 2, o + 3])
    me = bpy.data.meshes.new('chk'); me.from_pydata(vs, [], fs); me.materials.append(mat('chk_red', '#ff0000', emit=1.0))
    SC.collection.objects.link(bpy.data.objects.new('chk', me))
    shoot('topdown_check', (0, 150, .001), (0, 0, 0), w=1600, h=1090, ortho=94)
print('HAWKER done')
