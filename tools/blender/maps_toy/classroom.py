"""Classroom block, two storeys, toy playset. Run: /opt/homebrew/bin/blender -b -P tools/blender/maps_toy/classroom.py [-- preview] [-- only=ground_c,detail]
Model: a 1980s-90s Singapore neighbourhood school (classroom_REF.md). Colliders: layouts/classroom_solids_v4.json, written by classroom_layout4.py (v3 layout stretched by LAYOUT.fx, fz).
Dressing with no collider is authored in v3 coordinates and remapped in push(): per vertex, or rigidly by its anchor when it has a matrix M. RAW skips the remap.
Every collider is dressed by its kind, so the visual footprint is the collider. The north half (z < 0) is authored and pushed twice, the second time mirrored in z.
Game (x, y up, z) maps to Blender (x, -z, y). Authoring: B(material, x, z, y0, w along x, d along z, h)."""
import bpy, bmesh, sys, os, json, math, subprocess
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import classroom_layout4 as LAYOUT
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
LAY = os.path.join(HERE, 'layouts')
OUT = os.path.join(ROOT, 'shots', 'maps_toy', 'classroom')
TEX = os.path.join(ROOT, 'assets', 'maps', 'classroom_tex')
TMP = '/tmp/lunchliao-scratch'
if not os.path.isdir(TMP): TMP = bpy.app.tempdir
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW = 'preview' in ARGS
ONLY = next((a[5:].split(',') for a in ARGS if a.startswith('only=')), None)
os.makedirs(OUT, exist_ok=True)
X = json.load(open(os.path.join(LAY, 'classroom_expanded.json')))
SUN = json.load(open(os.path.join(LAY, 'classroom.json')))['look']['sun'][2]
SOL = json.load(open(os.path.join(LAY, 'classroom_solids_v4.json')))
TAG = LAYOUT.tagged()
assert [b for b, _ in TAG] == SOL, 'run classroom_layout4.py first: v4 file is stale'
FX, FZ = LAYOUT.fx, LAYOUT.fz
UP = LAYOUT.UP; PI = math.pi

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene

# ---------------------------------------------------------------- materials (palette: see classroom_REF.md section 5)
def srgb(h):
    h = h.lstrip('#'); f = lambda c: c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
    return tuple(f(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))
MATS = {}
def mat(name, hexcol, rough=.45, metal=0.0, coat=0.0, emit=0.0):
    if name in MATS: return name
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(hexcol), 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .08
    if emit: b.inputs['Emission Color'].default_value = (*srgb(hexcol), 1); b.inputs['Emission Strength'].default_value = emit
    MATS[name] = m; return name
def cmat(hexcol, rough=.4, coat=.15): return mat('c_' + hexcol.lstrip('#'), hexcol, rough, coat=coat)

mat('wall', '#d9b45a', .6)                 # cream emulsion on walls, pillars, beams
mat('dado', '#226b4c', .35, coat=.25)      # gloss pale green dado to 1 m
mat('ceil', '#8fbcd4', .7)                 # white slab soffits
mat('screed', '#b9604a', .75)              # cement screed corridor and bridge
mat('vinyl', '#6aa884', .5, coat=.1)       # grey-green classroom floor tile
mat('terrazzo', '#c2bcae', .4, coat=.2)    # stairs, planters
mat('green', '#1f6b4f', .35, coat=.35)     # school green: louvre frames, rails
mat('glass', '#8fd0c4', .08, coat=1.0)     # louvre slats
mat('glassg', '#6f9f92', .15, coat=.8)     # far windows
mat('yellow', '#e9b82c', .45, coat=.2)     # stair nosing
mat('board', '#2f5b47', .6)
mat('wood', '#c9995c', .45, coat=.2)       # desk tops, frames
mat('wood2', '#a8743f', .5, coat=.15)      # chairs, teacher desk body
mat('steel', '#7f8c95', .35, metal=.6)     # desk frames
mat('inox', '#c9ced2', .25, metal=1.0)     # water cooler, flagpoles
mat('locker', '#d07a34', .35, coat=.3)
mat('locker2', '#e79a4a', .3, coat=.4)
mat('dark', '#3a3a36', .5)
mat('felt', '#3f7a55', .9)                 # noticeboard
mat('paper', '#fbf8ee', .7)
mat('trim', '#fbf8ee', .4, coat=.2)
mat('clay', '#b5653f', .6)
mat('leaf', '#4f9442', .55); mat('leaf2', '#3b7f3a', .55); mat('trunk', '#7a5538', .6)
mat('bin', '#2f7d4f', .4, coat=.3)
mat('lamp', '#fff4d6', .3, emit=5.0)
mat('roofred', '#c2452d', .55)             # clay-red pitched roof
mat('tarmac', '#5a7f9c', .85)
mat('line', '#f1eee4', .6); mat('grass', '#86ad68', .9)
mat('red', '#d8232a', .4, coat=.3)
mat('beam', '#3d7fae', .5, coat=.15)       # painted pillars and beams
mat('planter', '#2f6fa8', .35, coat=.4)
mat('o_cap', '#e3c594', .6)
mat('mirror', '#cfe6ee', .06, metal=.9)

# ---------------------------------------------------------------- geometry buckets (one mesh per material)
BK = {}; MIR = False; TRK = None; RAW = False
def push(m, verts, faces, M=None):
    b = BK.setdefault(m, ([], [])); n = len(b[0])
    if M is not None:
        verts = [tuple(M @ Vector(v)) for v in verts]
        if not RAW:                                                # a fitting authored round an origin moves with it, unstretched
            t = M.translation; dx, dy = FX(t[0]) - t[0], -FZ(-t[1]) - t[1]; verts = [(v[0] + dx, v[1] + dy, v[2]) for v in verts]
    elif not RAW: verts = [(FX(v[0]), -FZ(-v[1]), v[2]) for v in verts]
    if TRK is not None:
        for v in verts:
            for i in range(3): TRK[i] = min(TRK[i], v[i]); TRK[i + 3] = max(TRK[i + 3], v[i])
    if MIR: verts = [(v[0], -v[1], v[2]) for v in verts]; faces = [f[::-1] for f in faces]
    b[0].extend(verts); b[1].extend([tuple(i + n for i in f) for f in faces])

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
def B(m, x, z, y0, w, d, h, r=.03, seg=1, M=None):
    vs, fs = _rbox(w, d, h, r, seg); push(m, [(v[0] + x, v[1] - z, v[2] + y0 + h / 2) for v in vs], fs, M)
def BS(m, b, g=0.0, r=.03, y0=None, y1=None, seg=1):
    """Box from a collider [minx, miny, minz, maxx, maxy, maxz], grown by g in plan."""
    ya = b[1] if y0 is None else y0; yb = b[4] if y1 is None else y1
    B(m, (b[0] + b[3]) / 2, (b[2] + b[5]) / 2, ya, b[3] - b[0] + 2 * g, b[5] - b[2] + 2 * g, yb - ya, r, seg)
_cy = {}
def C(m, x, z, y, r, length, axis='y', seg=20, r2=None, bev=0.0, M=None):
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
    vs, fs = _ico[sub]; push(m, [(v[0] * rx + x, v[1] * rz - z, v[2] * ry_ + y) for v in vs], fs, M)
def place(x, z, ry=0.0, y=0.0):
    """Matrix for a prop authored round its own origin, front = local game +z."""
    return Matrix.Translation((x, -z, y)) @ Matrix.Rotation(ry, 4, 'Z')

# ---------------------------------------------------------------- signs (textured quads, never mirrored as geometry)
UV = json.load(open(os.path.join(TEX, 'signs.json'))); SQ = ([], [], [])
def sign(name, x, z, y, w, h, ry=0.0, backing=True):
    """Sign centred on game (x, y, z), facing ry (0 faces +z, pi/2 faces +x). The south copy swaps E classes for N and the arrow."""
    global RAW; raw = RAW
    if not raw: x, z = FX(x), FZ(z)
    RAW = True; M = place(x, z, ry, y)
    if backing: B('trim', 0, -.012, -h / 2 - .02, w + .04, .024, h + .04, r=.008, M=M)
    if MIR:
        name = {'bridgeR': 'bridgeL', 'boys': 'girls'}.get(name, name.replace('E', 'N') if name[0] in '34' else name); M = place(x, -z, PI - ry, y)
    u0, v0, u1, v1 = UV[name]; n = len(SQ[0])
    SQ[0].extend(tuple(M @ Vector(q)) for q in ((-w / 2, -.026, -h / 2), (w / 2, -.026, -h / 2), (w / 2, -.026, h / 2), (-w / 2, -.026, h / 2)))
    SQ[1].append((n, n + 1, n + 2, n + 3)); SQ[2].extend([(u0, v0), (u1, v0), (u1, v1), (u0, v1)]); RAW = raw

# ---------------------------------------------------------------- props
def desk(x, z, y, ry=-PI / 2):
    M = place(x, z, ry, y)
    B('wood', 0, 0, .68, .55, .45, .04, r=.012, M=M); B('steel', 0, .02, .57, .5, .36, .1, r=.01, M=M)
    for sx in (-.245, .245):
        for sz in (-.195, .195): B('steel', sx, sz, 0, .03, .03, .68, r=0, M=M)
    B('wood2', 0, -.455, .4, .38, .38, .035, r=.012, M=M); B('wood2', 0, -.645, .56, .38, .04, .19, r=.012, M=M)
    for sx in (-.17, .17):
        B('steel', sx, -.29, 0, .025, .025, .4, r=0, M=M); B('steel', sx, -.645, 0, .025, .025, .58, r=0, M=M)

def railing(b):
    x0, y0, z0, x1, y1, z1 = b[:6]; alongx = (x1 - x0) > (z1 - z0)
    BS('wall', b, y1=y0 + .12, r=.02); BS('green', b, y0=y1 - .07, r=.02)
    n = max(2, round(((x1 - x0) if alongx else (z1 - z0)) / .18))
    for i in range(n + 1):
        t = i / n
        B('green', x0 + .02 + (x1 - x0 - .04) * t if alongx else (x0 + x1) / 2, (z0 + z1) / 2 if alongx else z0 + .02 + (z1 - z0 - .04) * t, y0 + .12, .03, .03, y1 - y0 - .19, r=0)

def window(b):
    """Green timber frame with glass louvre slats in the 1.0 to 2.4 opening."""
    x0, y0, z0, x1 = b[0], b[1], b[2], b[3]; zc = (b[2] + b[5]) / 2; w = x1 - x0; ya, yb = y0 + 1.0, y0 + 2.4
    for y in (ya, yb - .06): B('green', (x0 + x1) / 2, zc, y, w, .14, .06, r=.01)
    for i in range(5): B('green', x0 + .03 + (w - .06) * i / 4, zc, ya, .06, .14, 1.4, r=.01)
    for p in range(4):
        xc = x0 + w * (p + .5) / 4
        for s in range(8):
            M = Matrix.Translation((xc, -zc, ya + .13 + s * .168)) @ Matrix.Rotation(math.radians(38), 4, 'X')
            B('glass', 0, 0, -.004, w / 4 - .08, .17, .008, r=0, M=M)

def locker(b):
    """Low locker bank against a wall, doors on the +z face."""
    BS('locker', b); x0, y0, x1, z1 = b[0], b[1], b[3], b[5]
    n = max(1, round((x1 - x0) / .4)); rows = max(1, round((b[4] - y0) / .47)); cw = (x1 - x0) / n; rh = (b[4] - y0 - .06) / rows
    for i in range(n):
        for j in range(rows):
            xc = x0 + cw * (i + .5); yy = y0 + .04 + j * rh
            B('locker2', xc, z1 + .004, yy, cw - .04, .012, rh - .04, r=.005); B('dark', xc, z1 + .011, yy + rh - .14, cw * .5, .004, .05, r=0); B('inox', xc + cw * .3, z1 + .014, yy + rh * .4, .025, .012, .07, r=.004)

def cooler(b):
    """Stainless floor-standing water cooler: basin on top, raised spout tube."""
    x0, y0, z0, x1, z1 = b[0], b[1], b[2], b[3], b[5]; xc, zc = (x0 + x1) / 2, (z0 + z1) / 2
    BS('inox', b, y1=y0 + 1.06, r=.03); B('steel', xc, zc, y0 + 1.052, x1 - x0 - .1, z1 - z0 - .1, .012, r=0)
    C('inox', xc - .16, zc - .1, y0 + 1.17, .02, .22, seg=10); C('inox', xc - .09, zc - .1, y0 + 1.28, .02, .18, 'x', seg=10); C('inox', xc - .01, zc - .1, y0 + 1.24, .016, .08, seg=10)
    C('steel', xc + .16, zc - .1, y0 + 1.09, .03, .06, seg=10); C('dark', xc, zc + .04, y0 + 1.06, .03, .006, seg=10)
    B('dark', xc, z1 + .003, y0 + .1, x1 - x0 - .16, .008, .3, r=0); B('steel', xc, z1 + .012, y0 + .78, x1 - x0 - .2, .03, .05, r=.01)

def picnic(b, top):
    """Wooden planks on two trestle legs. Table when top, else bench."""
    x0, y0, z0, x1, y1, z1 = b[:6]; w = x1 - x0; n = 3 if top else 2
    for i in range(n): B('wood', x0 + w * (i + .5) / n, (z0 + z1) / 2, y1 - .05, w / n - .015, z1 - z0, .05, r=.012)
    for z in (z0 + .25, z1 - .25): B('wood2', (x0 + x1) / 2, z, y0, w - .1, .08, y1 - y0 - .05, r=.01); B('wood2', (x0 + x1) / 2, z, y1 - .11, w - .02, .1, .06, r=.01)

def tiles(): return (cmat('#e58aa6'), cmat('#c94f7c')) if MIR else (cmat('#4f9fc9'), cmat('#2f6fa8'))
def cubicles(b):
    t, t2 = tiles(); x0, y0, x1, z1 = b[0], b[1], b[3], b[5]; w = (x1 - x0) / 2
    BS('dark', b, g=-.03, y1=y0 + .15, r=0); BS(t2, b, y0=y0 + .15, r=.015)
    for i in range(2):
        xc = x0 + w * (i + .5)
        B('trim', xc, z1 + .006, y0 + .2, w - .22, .014, 1.7, r=.01); S('inox', xc + w * .3, z1 + .02, y0 + 1.0, .025, .025, .025, 1)
        C('red' if i else 'bin', xc + w * .3, z1 + .016, y0 + 1.12, .025, .01, 'z', seg=10)

def sinks(b):
    """Sink counter on the east wall with three basins, taps and a mirror."""
    t, t2 = tiles(); x0, y0, z0, x1, z1 = b[0], b[1], b[2], b[3], b[5]; xc = (x0 + x1) / 2
    BS(t2, b, g=-.02, y1=y0 + .8, r=.01); BS('terrazzo', b, y0=y0 + .8, y1=y0 + .86, r=.015)
    for i in range(3):
        z = z0 + (z1 - z0) * (i + .5) / 3
        S('trim', xc - .04, z, y0 + .86, .17, .025, .24); C('dark', xc - .04, z, y0 + .886, .02, .004, seg=8)
        C('inox', x1 - .07, z, y0 + .92, .016, .13, seg=8); C('inox', x1 - .13, z, y0 + .985, .014, .14, 'x', seg=8)
    global TRK; k = TRK; TRK = None                                # the mirror hangs on the wall above the collider
    B('trim', x1 - .04, (z0 + z1) / 2, y0 + 1.16, .02, z1 - z0 + .1, .9, r=.006); B('mirror', x1 - .054, (z0 + z1) / 2, y0 + 1.2, .012, z1 - z0, .82, r=0); TRK = k

def urinals(b):
    """Boys: four urinals on a tiled duct. Girls (the mirrored copy): the same box is a tiled vanity ledge with a mirror."""
    t, t2 = tiles(); x0, y0, z0, x1, z1 = b[0], b[1], b[2], b[3], b[5]; xc = (x0 + x1) / 2
    if MIR:
        BS(t2, b, y1=b[4] - .05, r=.01); BS('terrazzo', b, y0=b[4] - .05, r=.015)
        B('trim', xc, z0 + .04, b[4] + .1, x1 - x0 - .3, .02, .9, r=.006); B('mirror', xc, z0 + .054, b[4] + .14, x1 - x0 - .38, .012, .82, r=0)
        return
    B(t2, xc, z0 + .05, y0, x1 - x0, .1, b[4] - y0, r=.01)
    for i in range(4):
        x = x0 + (x1 - x0) * (i + .5) / 4
        B('trim', x, z1 - .14, y0 + .3, .42, .28, .86, r=.09, seg=2); B('ceil', x, z1 - .002, y0 + .42, .2, .01, .56, r=0); C('inox', x, z1 - .2, y0 + 1.18, .02, .04, seg=8)
    for i in range(5): B('trim', x0 + .015 + (x1 - x0 - .03) * i / 4, z1 - .16, y0 + .35, .03, .32, .85, r=.006)

def cabinet(b):
    """Low cubby shelf along the east partition, open to the room (west face)."""
    BS('wood', b); x0 = b[0]; n = 12; L = b[5] - b[2]; cols = ['#d98a8a', '#9ec9df', '#f2d27c', '#a6d6be', '#c7b5d9', '#e39a4f']
    for i in range(n):
        zc = b[2] + L * (i + .5) / n
        for j in range(2):
            yy = b[1] + .1 + j * .55; B('dark', x0 - .003, zc, yy, .008, L / n - .06, .47, r=0)
            if (i * 7 + j * 3) % 4: B(cmat(cols[(i * 5 + j) % 6]), x0 + .0, zc + .02, yy + .02, .03, L / n * .55, .3 if (i + j) % 3 else .2, r=.012)

def noticeboard(x, z, y, w, h, ry):
    M = place(x, z, ry, y); B('wood', 0, -.015, 0, w, .03, h, r=.012, M=M); B('felt', 0, -.02, .05, w - .1, .03, h - .1, r=.005, M=M)
    cols = [cmat('#f2c230'), cmat('#e8574a'), cmat('#4aa3df'), cmat('#f08a3c'), cmat('#e86a9a'), cmat('#8fd06a')]; n = max(2, int(w / .32))
    for i in range(n):
        for j in range(2):
            if (i + 2 * j) % 5 == 4: continue
            B(cols[(i * 2 + j) % 6], -w / 2 + .12 + (w - .24) * (i + .5) / n, -.037, .12 + j * (h / 2 - .08) + (.03 if i % 2 else 0), .2, .006, .28, r=0, M=M)

FANS = []
def fan(x, z, y): x, z = (x, z) if RAW else (FX(x), FZ(z)); FANS.append((x, z if not MIR else -z, y))
def tube(x, z, y, ry=0.0):
    M = place(x, z, ry, y); B('trim', 0, 0, -.02, 1.3, .12, .04, r=.01, M=M); B('lamp', 0, 0, -.05, 1.2, .05, .035, r=.012, M=M)

# ---------------------------------------------------------------- colliders by kind
RXS = LAYOUT.RXS; Z95 = FZ(-9.5); EA = (FX(17) - .01, FZ(-15.75) + .01)   # classroom wall line, east stair flight A
def dress(b, k):
    y0 = b[1]; h = b[4] - b[1]
    if k == 'wall':
        BS('wall', b)
        if h > 3.1: BS('dado', b, g=.012, y1=y0 + 1.0, r=.008)
    elif k == 'pillar': BS('beam', b); BS('dado', b, g=.012, y1=y0 + 1.0, r=.008)
    elif k == 'lintel': BS('wall', b)
    elif k == 'post': BS('beam', b)
    elif k == 'sill': BS('dado', b, g=.012, y1=b[4] - .04, r=.008); BS('trim', b, g=.03, y0=b[4] - .04, r=.012)
    elif k == 'win': window(b)
    elif k in ('slab', 'roof'):
        BS('ceil', b, r=.02)
        if k == 'slab':                                            # floor finish on top: vinyl in rooms, screed on corridor and bridge
            for za, zb, m in ((b[2], min(b[5], Z95), 'vinyl'), (max(b[2], Z95), b[5], 'screed')):
                if zb - za > .3: B(m, (b[0] + b[3]) / 2, (za + zb) / 2, b[4], b[3] - b[0], zb - za, .015, r=0)
    elif k in ('parapet', 'guard'): railing(b)
    elif k in ('stair', 'landing'):
        BS('terrazzo', b, r=.015)
        if k == 'stair':
            east_up = b[0] >= EA[0] and b[5] <= EA[1]                # flight A of the east stair rises east
            B('yellow', b[0] + .04 if east_up else b[3] - .04, (b[2] + b[5]) / 2, b[4] - .01, .07, b[5] - b[2] - .08, .014, r=0)
    elif k == 'desk': desk(b[0] + .225, (b[2] + b[5]) / 2, y0)
    elif k in ('ptable', 'pbench'): picnic(b, k == 'ptable')
    elif k == 'screen':
        t, t2 = tiles(); BS(t, b, y1=y0 + 2.2, r=.01); BS(t2, b, g=.004, y0=y0 + 2.2, y1=y0 + 2.28, r=0); BS('wall', b, y0=y0 + 2.28, r=.01)
    elif k == 'cubicles': cubicles(b)
    elif k == 'sinks': sinks(b)
    elif k == 'urinals': urinals(b)
    elif k == 'tdesk':
        BS('wood2', b, g=-.03, y1=b[4] - .04); BS('wood', b, y0=b[4] - .04, r=.015)
        B('wood', b[3] - .028, (b[2] + b[5]) / 2 - .3, y0 + .3, .012, .5, .3, r=.004)
    elif k == 'cabinet': cabinet(b)
    elif k == 'locker': locker(b)
    elif k == 'cooler': cooler(b)
    elif k == 'bin':
        xc, zc = (b[0] + b[3]) / 2, (b[2] + b[5]) / 2; C('bin', xc, zc, y0 + .4, .27, .8, seg=18, r2=.31); C('dark', xc, zc, y0 + .84, .31, .08, seg=18, bev=.02)
    elif k == 'plant':
        xc, zc = (b[0] + b[3]) / 2, (b[2] + b[5]) / 2; C('clay', xc, zc, y0 + .15, .2, .3, seg=16, r2=.27); S('leaf', xc, zc, y0 + .37, .32, .18, .32)
    else: raise ValueError(k)

BAD = []
def colliders():
    global TRK, RAW
    RAW = True                                                     # v4 colliders are already in new coordinates
    for b, k in TAG:
        if b[2] >= 0 and 'x' not in b[6]: continue                 # south copies come from the mirror pass
        if MIR and 'x' in b[6]: continue
        TRK = [1e9] * 3 + [-1e9] * 3; dress(b, k); t = TRK; TRK = None
        if MIR or k == 'win': continue                             # a window collider is full height, its sill and lintel are separate colliders
        got = (t[0], t[2], -t[4], t[3], t[5], -t[1]); err = max(abs(g - w) for g, w in zip(got, b[:6]))
        if err > .05: BAD.append((k, [round(v, 3) for v in got], b))
    RAW = False

# ---------------------------------------------------------------- dressing with no collider (decals, wall fittings, things above head height, outside)
def storey(y):
    """Fittings of one storey of the north block. y = floor level."""
    L2 = y > 1; pre = '4E' if L2 else '3E'
    for i, xr in enumerate(RXS):
        sign(pre + str(i + 1), xr + 1.4, -9.5, y + 2.8, .8, .27)                            # class plate over the front door
        M = place(xr + .125, -13.6, PI / 2, y)                                                # green board on the west partition
        B('wood', 0, -.02, .9, 4.5, .04, 1.3, r=.015, M=M); B('wood', 0, -.06, .9, 4.3, .08, .03, r=.01, M=M)
        sign('board', xr + .125 + .02, -13.6, y + 1.57, 4.3, 1.17, PI / 2, backing=False)
        sign('flag', xr + .125, -13.6, y + 2.6, .48, .32, PI / 2)
        C('trim', xr + .145, -11.9, y + 2.6, .17, .04, 'x', 20); C('dark', xr + .17, -11.9, y + 2.6, .02, .02, 'x', 8)
        B('dark', xr + .17, -11.9, y + 2.6, .008, .012, .12, r=0); B('dark', xr + .17, -11.86, y + 2.595, .008, .09, .012, r=0)
        noticeboard(xr + 4.1, -17.75, y + 1.0, 2.6, 1.1, 0)                                   # class noticeboard on the back wall
    noticeboard(-21, -9.5, y + 1.0, 1.7, 1.1, 0)                                              # corridor noticeboard outside the stair room
    sign('norun', -21, -9.5, y + 2.6, 1.8, .28)
    sign('stair1', -23, -9.5, y + 2.8, 1.3, .32); sign('stair2', 17.5, -10.475, y + 2.45, 1.3, .32, -PI / 2)
    # toilet beside the east stair: signs over both doors, wall tiles to 2.2 m, chequer floor (boys north, girls on the mirrored side)
    sign('boys', 18.7, -9.5, y + 2.6, 1.0, .44)
    t, t2 = tiles()
    for x, z, w, d in ((17.825, -9.765, .35, .03), (21.825, -9.765, 4.85, .03), (17.665, -11.6, .03, 3.7), (19.9, -13.435, 4.5, .03),
                       (22.165, -15.6, .03, 4.3), (24.235, -13.75, .03, 8), (23.2, -17.735, 2.1, .03)):
        gx, gz = (.006 if w < .1 else 0), (.006 if d < .1 else 0)
        B(t, x, z, y, w, d, 2.2, r=0); B(t2, x, z, y + 2.2, w + gx, d + gz, .08, r=0)
        for i in range(1, 5): B(t2, x, z, y + i * .44 - .006, w + gx, d + gz, .012, r=0)                       # grout lines, .44 m tiles
        n = round(max(w, d) / .44)
        for i in range(1, n): B(t2, x + (w * (i / n - .5) if gz else 0), z + (d * (i / n - .5) if gx else 0), y, .012 if gz else w + gx, .012 if gx else d + gz, 2.2, r=0)
    f1, f2 = cmat('#b98a5e'), cmat('#8f6a4a')
    for xa, xb, za, zb, nx, nz in ((17.65, 24.25, -13.45, -9.75, 15, 8), (22.15, 24.25, -16.55, -13.45, 5, 7)):
        B(f1, (xa + xb) / 2, (za + zb) / 2, y + .016, xb - xa, zb - za, .01, r=0)
        for i in range(nx):
            for j in range(nz):
                if (i + j) % 2: B(f2, xa + (xb - xa) * (i + .5) / nx, za + (zb - za) * (j + .5) / nz, y + .018, (xb - xa) / nx, (zb - za) / nz, .011, r=0)
    tube(23.2, -15.2, y + 3.12, PI / 2)
    sign('lvl6' if L2 else 'lvl5', -24.5, -7.75, y + 2.3, 1.2, .37, PI / 2)
    sign('keepleft', -20.7, -17.75, y + 2.5, 1.0, .31); sign('keepleft', 18.5, -17.75, y + 2.5, 1.0, .31)
    M = place(14.5, -7.8, -PI / 2, y + 2.72); B('trim', 0, .02, -.24, 1.9, .04, .46, r=.012, M=M)     # hanging sign under the beam, above head height
    sign('bridgeR', 14.5, -7.8, y + 2.72, 1.75, .36, -PI / 2, backing=False)
    for x in (-17.5, -9.5, -1.5, 6.5, 14.5, 24.1): B('beam', x, -7.85, y + 2.9, .28, 3.1, .3, r=.02)   # corridor beams
    B('beam', 0, -6.075, y + 2.85, 49, .15, .35, r=.02)                                       # edge beam
    for p in X['props']:
        if p['z'] >= 0 and not (p['k'] == 'tube' and p.get('ry')): continue
        if p['k'] == 'fan': fan(p['x'], p['z'], y + p['y'])
        elif p['k'] == 'tube' and not (p.get('ry') and MIR): tube(p['x'], p['z'], y + p['y'], p.get('ry', 0))
    for x, z in ((19.5, -15), (16, -11.5), (23, -11.5)): tube(x, z, y + 3.12)                  # stair hall lights
    B('dark', -1.2, -6.3, y + .0, .3, .3, .28, r=.06, seg=2); C('wood', -1.05, -6.42, y + .62, .018, 1.3, seg=8)   # pail and mop by the parapet (0.3 m, decoration)
    B('paper', -1.05, -6.42, y + .02, .22, .1, .1, r=.03)

def block_outside():
    """North block below and above the play levels."""
    B('ceil', -.25, -12, -.4, 49.5, 12, .4, r=.02)                                            # level 1 floor slab
    B('vinyl', -.125, -13.625, 0, 48.75, 8.25, .015, r=0); B('screed', 0, -7.75, 0, 49, 3.5, .015, r=0)
    B('wall', -.25, -13.75, -14, 49.5, 8.5, 13.6, r=.05)                                      # lower storeys
    for fy in (-3.5, -7, -10.5):
        B('ceil', -.25, -7.75, fy - .3, 49.5, 3.5, .3, r=.02); B('wall', -1.5, -6.075, fy, 32, .15, .12, r=.02); B('green', -1.5, -6.075, fy + 1.03, 32, .15, .07, r=.02)
        for i in range(65): B('green', -17.5 + i * .5, -6.075, fy + .12, .03, .03, .91, r=0)
        for xr in RXS: B('green', xr + 4, -9.49, fy + 1.0, 3.9, .04, 1.4, r=.01); B('glassg', xr + 4, -9.47, fy + 1.06, 3.78, .03, 1.28, r=0)
    for x in (-17.5, -9.5, -1.5, 6.5, 14.5, 24.125): B('beam', x, -6.3, -14, .45, .3, 13.6, r=.03)
    for fy in (-10.5, -7, -3.5, 0, 3.5):                                                      # louvre bands on the outer back wall
        for xc in (-21, -13.5, -5.5, 2.5, 10.5, 19.5): B('green', xc, -18.01, fy + 1.0, 5.6, .04, 1.4, r=.01); B('glassg', xc, -18.03, fy + 1.07, 5.44, .03, 1.26, r=0)
    for fy in (0, 3.5):                                                                       # vent blocks on the west gable
        for zc in (-15, -12, -9): B('green', -25.01, zc, fy + 1.6, .04, 1.6, .9, r=.01)
    a, b, c, d = (-25.7, 18.7, 7.0), (25.2, 18.7, 7.0), (25.2, 5.3, 7.0), (-25.7, 5.3, 7.0); e, f = (-19, 12, 9.3), (18.5, 12, 9.3)     # hip roof
    push('roofred', [a, b, c, d, e, f], [(4, 5, 1, 0), (3, 2, 5, 4), (2, 1, 5), (0, 3, 4)])

def tree(x, z, s=1.0, g=-14):
    C('trunk', x, z, g + 3 * s, .4 * s, 6 * s, seg=10, r2=.26 * s)
    for i, (dx, dz, dy, r) in enumerate([(0, 0, 8, 3.6), (2.2, 1, 6.8, 2.7), (-2, -.8, 7, 2.8), (.4, -2.1, 6.6, 2.5), (-.6, 2, 6.4, 2.4)]):
        S('leaf' if i % 2 == 0 else 'leaf2', x + dx * s, z + dz * s, g + dy * s, r * s, r * s * .7, r * s)

def hdb(x, z, w, d, h, col):
    c = mat('o_' + col[1:], col, .6); B('o_cap', x, z, -14, w, d, h, r=.3); B(c, x, z, -14 + h, w + .6, d + .6, .9, r=.2)
    fl = -14 + 2.9
    while fl < -14 + h - 1.5: B(c, x, z, fl, w + .3, d + .3, .9, r=.08); fl += 2.9

def site():
    """Things on the axis: bridge, courtyard, skyline. Built once."""
    B('ceil', 19.5, 0, -.4, 10, 12, .4, r=.02); B('screed', 19.5, 0, 0, 10, 12, .015, r=0)    # level 1 bridge deck
    for x in (14.85, 24.15):
        for z in (-5.6, 5.6): B('beam', x, z, -14, .5, .5, 13.6, r=.04)
    for y in (0, UP): B('beam', 19.5, 0, y + 2.9, .28, 12, .3, r=.02)                         # bridge spine beam
    for y in (0, UP):
        for i in range(24): B(cmat(('#e8344a', '#f2c230', '#4aa3df', '#8fd06a')[i % 4]), 19.5 + (.2 if i % 2 else -.2), -5.75 + i * .5, y + 2.6, .02, .26, .28, r=0)
        for z in (-5.9, 5.9): B(cmat('#e8344a'), 19.5, z, y + 2.74, 9.4, .06, .12, r=.02)
    p = [(14.1, -8, 7.0), (14.1, 8, 7.0), (24.9, -8, 7.0), (24.9, 8, 7.0), (19.5, -8, 8.0), (19.5, 8, 8.0)]
    push('roofred', p, [(0, 4, 5, 1), (2, 3, 5, 4)])
    B('grass', 0, 0, -14.4, 420, 420, .3, r=0); B('tarmac', 2, 0, -14.1, 96, 62, .1, r=0)     # parade square with a basketball court
    global RAW; RAW = True
    L = lambda x, z, w, d: B('line', x, z, -14.0, w, d, .012, r=0)
    cx, hw, hd = FX(-6.0), 13.0, 5.0
    L(cx, -hd, 2 * hw, .08); L(cx, hd, 2 * hw, .08); L(cx - hw, 0, .08, 2 * hd); L(cx + hw, 0, .08, 2 * hd); L(cx, 0, .08, 2 * hd)
    for i in range(32):
        a = i * 2 * PI / 32; B('line', 0, 0, -14.0, .36, .08, .012, r=0, M=place(cx + 1.8 * math.cos(a), 1.8 * math.sin(a), a))
    for s in (-1, 1):
        L(cx + s * (hw - 2.9), -1.8, 5.8, .08); L(cx + s * (hw - 2.9), 1.8, 5.8, .08); L(cx + s * (hw - 5.8), 0, .08, 3.6)
        C('inox', cx + s * (hw + .6), 0, -12.5, .07, 3, seg=10); B('trim', cx + s * (hw + .2), 0, -11.6, .06, 1.8, 1.1, r=.02); C('red', cx + s * (hw - .2), 0, -11.75, .24, .03, seg=16)
    RAW = False
    for i, z in enumerate((-1.6, 0, 1.6)):                                                    # flagpoles at the west end of the square
        B('terrazzo', -23.5, z, -14, .6, .6, .3, r=.05); C('inox', -23.5, z, -9.2, .05, 9.6, seg=10); S('inox', -23.5, z, -4.35, .09, .09, .09, 1)
        B('red' if i == 1 else cmat('#1f6b4f') if i == 0 else cmat('#e9b82c'), -23.0, z, -5.5, .9, .02, .6, r=0)
        if i == 1: B('paper', -23.0, z, -5.5, .9, .024, .3, r=0)
    B('wall', 40, 0, -14, 14, 20, 3.2, r=.1); B('roofred', 40, 0, -10.8, 16, 22, .35, r=.1)   # canteen shed past the bridge
    for i in range(4): B(cmat(['#d98a8a', '#9ec9df', '#f2d27c', '#a6d6be'][i]), 33.1, -7.5 + i * 5, -13.0, .1, 3.2, 1.4, r=.03)
    for x, z, s in ((-34, -24, 1.2), (-36, 6, 1.0), (-33, 26, 1.3), (-8, 27, 1.1), (16, 28, 1.2), (36, 24, 1.0), (52, -10, 1.3), (30, -26, 1.1), (4, -27, 1.2), (-16, -28, 1.0)): tree(x, z, s)
    for x, z, w, d, h, c in ((-70, -30, 12, 60, 40, '#f4c7c3'), (-20, -78, 70, 12, 36, '#a6d6be'), (62, -72, 60, 12, 44, '#f2d27c'), (95, 10, 12, 70, 38, '#9ec9df'), (30, 85, 80, 12, 34, '#c7b5d9'), (-75, 60, 50, 12, 30, '#f2d27c')):
        hdb(x, z, w, d, h, c)

# ---------------------------------------------------------------- build
def build():
    global MIR
    for MIR in (False, True):
        colliders(); storey(0); storey(UP); block_outside()
    MIR = False; site()
    tris = 0
    for name, (vs, fs) in BK.items():
        me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.materials.append(MATS[name])
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons)); me.set_sharp_from_angle(angle=math.radians(40))
        ob = bpy.data.objects.new('map_' + name, me); SC.collection.objects.link(ob)
        if name.startswith('o_'): ob.visible_shadow = False
        tris += sum(len(f) - 2 for f in fs)
    img = bpy.data.images.load(os.path.join(TEX, 'signs.png')); m = bpy.data.materials.new('signs'); m.use_nodes = True; nt = m.node_tree
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; nt.links.new(t.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    nt.nodes['Principled BSDF'].inputs['Roughness'].default_value = .45
    me = bpy.data.meshes.new('signs'); me.from_pydata(SQ[0], [], SQ[1]); me.uv_layers.new(name='UVMap').data.foreach_set('uv', [c for q in SQ[2] for c in q]); me.materials.append(m)
    SC.collection.objects.link(bpy.data.objects.new('map_signs', me)); tris += 2 * len(SQ[1])
    # ceiling fans: one shared mesh, separate FAN_ objects so the engine can spin them round their local up axis
    BK.clear(); C('trim', 0, 0, .25, .02, .5, seg=8); C('trim', 0, 0, 0, .11, .1, seg=16, bev=.02)
    for i in range(3): B('wood2', 0, .4, -.01, .14, .62, .02, r=.008, M=Matrix.Rotation(i * 2 * PI / 3, 4, 'Z'))
    fm = bpy.data.meshes.new('fan')
    vs, fs, mi = [], [], []
    for j, (name, (v, f)) in enumerate(BK.items()):
        fm.materials.append(MATS[name]); n = len(vs); vs += v; fs += [tuple(i + n for i in q) for q in f]; mi += [j] * len(f)
    fm.from_pydata(vs, [], fs); fm.polygons.foreach_set('material_index', mi)
    for i, (x, z, y) in enumerate(FANS):
        o = bpy.data.objects.new('FAN_%02d' % i, fm); SC.collection.objects.link(o); o.location = (x, -z, y); o.rotation_euler = (0, 0, i * .7)
    tris += len(FANS) * sum(len(f) - 2 for f in fs)
    nm = len([m for m in bpy.data.materials if m.users])
    print('TRIS', tris, 'MATERIALS', nm, 'FANS', len(FANS))
    print('COLLIDER CHECK', 'PASS' if not BAD else 'FAIL', len(SOL) - 2 * len(BAD), '/', len(SOL), BAD[:6])
    json.dump(dict(tris=tris, materials=nm, bad=BAD), open(os.path.join(TMP, 'classroom_stats.json'), 'w'))

def export():
    for o in SC.objects: o.select_set(o.name.startswith(('map_', 'FAN_')))
    bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'maps', 'classroom.glb'), use_selection=True, export_yup=True, export_apply=True)

# ---------------------------------------------------------------- stage and shots
def G(x, y, z): return Vector((x, -z, y))
def look_at(o, t): o.rotation_euler = (Vector(t) - o.location).to_track_quat('-Z', 'Y').to_euler()

def stage():
    w = bpy.data.worlds.new('World'); SC.world = w; w.use_nodes = True; nt = w.node_tree
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); cr = nt.nodes.new('ShaderNodeValToRGB')
    mp = nt.nodes.new('ShaderNodeMapRange'); mp.inputs[1].default_value = -.05; mp.inputs[2].default_value = .7
    e = cr.color_ramp.elements; e[0].position = 0; e[0].color = (*srgb('#f8dfb8'), 1); e[1].position = 1; e[1].color = (*srgb('#74b0d6'), 1)
    n = e.new(.2); n.color = (*srgb('#d6e6e6'), 1)
    nt.links.new(tc.outputs['Generated'], sp.inputs[0]); nt.links.new(sp.outputs['Z'], mp.inputs[0]); nt.links.new(mp.outputs[0], cr.inputs[0])
    bg = nt.nodes['Background']; nt.links.new(cr.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 1.1
    d = bpy.data.lights.new('sun', 'SUN'); d.energy = 4.2; d.color = srgb('#ffd9a8'); d.angle = math.radians(3)
    o = bpy.data.objects.new('sun', d); SC.collection.objects.link(o); o.location = G(SUN[0], SUN[1], SUN[2]); look_at(o, (0, 0, 0))
    # warm fill under the slabs, one soft light per classroom, stair hall and corridor bay (render only)
    for s in (-1, 1):
        for y in (0, UP):
            pts = [(x, -13.6, 60) for x in (-21, -13.5, -5.5, 2.5, 10.5, 19.5)] + [(x, -7.75, 30) for x in (-21, -13.5, -5.5, 2.5, 10.5, 19.5)]
            for x, z, en in pts + ([(19.5, 0, 60)] if s < 0 else []):
                pl = bpy.data.lights.new('fill', 'POINT'); pl.energy = en * (1 if y else 1.3); pl.color = (1, .93, .8); pl.shadow_soft_size = .6; pl.use_shadow = False
                po = bpy.data.objects.new('fill', pl); SC.collection.objects.link(po); po.location = G(FX(x), y + 2.7, FZ(z * -s) if z else 0)
    SC.render.engine = 'BLENDER_EEVEE'; SC.eevee.taa_render_samples = 16 if PREVIEW else 48
    SC.view_settings.view_transform = 'AgX'; SC.view_settings.look = 'AgX - Punchy'; SC.render.image_settings.file_format = 'PNG'
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
    e.location = G(FX(x), y, FZ(z)); e.rotation_euler = (0, 0, yaw)

def want(n): return ONLY is None or n in ONLY
def shot(cam, name, eye, tgt, lens=28, res=(1600, 900), raw=False):
    """eye and tgt in v3 coordinates unless raw."""
    if not want(name): return
    if not raw: eye, tgt = [(FX(p[0]), p[1], FZ(p[2])) for p in (eye, tgt)]
    cam.data.type = 'PERSP'; cam.data.lens = lens; cam.data.clip_start = .1; cam.location = G(*eye); look_at(cam, G(*tgt))
    SC.render.resolution_x, SC.render.resolution_y = res; SC.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True)

def topdown(cam):
    """Two orthographic plans cut by the camera near plane (level 1 below the slab, level 2 below the roof). classroom_check.py draws the colliders on them."""
    if not want('topdown_check'): return
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 66; cam.data.clip_start = .01; cam.rotation_euler = (0, 0, 0)
    SC.render.resolution_x, SC.render.resolution_y = 1600, 1150
    hid = [o for o in SC.objects if o.name.startswith('HERO_') or o.parent and o.parent.name.startswith('HERO_')]
    for o in SC.objects:
        if o.name.startswith('HERO_'):
            for c in o.children_recursive: c.hide_render = True
    for i, y in enumerate((3.15, 6.65)):
        cam.location = (0, 0, y); SC.render.filepath = os.path.join(TMP, 'classroom_top%d.png' % (i + 1)); bpy.ops.render.render(write_still=True)
    for o in SC.objects:
        if o.name.startswith('HERO_'):
            for c in o.children_recursive: c.hide_render = False
    subprocess.run(['python3', os.path.join(HERE, 'classroom_check.py')], check=True)

build()
export()
cam = stage()
# heroes for scale (render only). yaw 0 faces game -z
hero('ahma', -6.5, -8.4, -PI / 2 + .5); hero('gym', -3.2, -7.2, -PI / 2 - .3); hero('tarik', 1.0, -8.6, -PI / 2 + .2)
hero('siao', 17.0, -2.6, .4); hero('gym', 22.2, 2.8, -.3); hero('tarik', 22.0, -8.0, PI / 2 + .4)
hero('tarik', 2.0, -7.3, PI / 2 - .3, UP); hero('ahma', 6.0, -8.5, PI / 2 + .3, UP); hero('siao', 12.5, -7.4, PI / 2, UP)
hero('ahma', 16.0, -12.2, PI / 2 + .6); hero('siao', 20.9, -15.8, PI / 2, 1.75)
topdown(cam)
shot(cam, 'overview', (-58, 30, 34), (2, 0, -3), lens=30)
shot(cam, 'ground_a', (-12.5, 1.6, -7.6), (6, 1.3, -7.9), lens=20)
shot(cam, 'ground_b', (19.3, 1.6, -8.6), (19.8, 1.2, 6), lens=20)
shot(cam, 'ground_c', (-4.5, UP + 1.6, -7.7), (14, UP + 1.3, -7.2), lens=20)
shot(cam, 'detail', (-2.1, UP + 1.6, -17.2), (-9.4, UP + 1.0, -12.6), lens=18)
shot(cam, 'toilet', (23.4, 1.6, -11.0), (19.0, .9, -13.2), lens=14)
shot(cam, 'toilet_entry', (18.7, 1.6, -6.8), (18.7, 1.4, -11), lens=20)
shot(cam, 'toilet_b', (22.6, 1.6, -10.2), (23.3, 1.0, -16.5), lens=14)
shot(cam, 'toilet_door', (15.6, 1.6, -6.6), (20.4, 1.25, -9.7), lens=20)
shot(cam, 'toilet_girls', (23.4, UP + 1.6, 11.0), (19.0, UP + .9, 13.2), lens=14)
# v4: level 2 bridge void over B, zone A room on level 2, the wider level 1 corridor (new coordinates)
shot(cam, 'l2_bridge', (19.2, UP + 1.7, -6.6), (24.9, .4, 1.5), lens=18, raw=True)
shot(cam, 'l2_zone_a', (7.4, UP + 1.7, -13.7), (2.0, UP + .5, -19.5), lens=16, raw=True)
shot(cam, 'corridor_l1', (-24.0, 1.6, -10.2), (10.0, 1.2, -10.4), lens=18, raw=True)
