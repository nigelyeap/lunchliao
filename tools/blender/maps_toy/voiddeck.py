"""Blk 404 Void Deck, toy playset rebuild.
Run: /opt/homebrew/bin/blender -b -P tools/blender/maps_toy/voiddeck.py [-- shot names]
Game coords (x, y up, z) map to Blender (x, -z, y). All helpers below take game coords.
"""
import bpy, bmesh, json, math, os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
LAY = os.path.join(ROOT, 'tools/blender/maps_toy/layouts')
TEX = os.path.join(ROOT, 'assets/maps/voiddeck_tex')
SHOTS = os.path.join(ROOT, 'shots/maps_toy/voiddeck')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
X = json.load(open(os.path.join(LAY, 'voiddeck_expanded.json')))
SOL = json.load(open(os.path.join(LAY, 'voiddeck_solids_v2.json')))
RAW = json.load(open(os.path.join(LAY, 'voiddeck.json')))
os.makedirs(TEX, exist_ok=True); os.makedirs(SHOTS, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene

# ---------------------------------------------------------------- materials
def srgb(h):
    h = h.lstrip('#'); return tuple(((int(h[i:i + 2], 16) / 255) ** 2.2) for i in (0, 2, 4))

MATS = {}; PROJ = {}
def mat(hexcol, rough=.45, metal=0.0, coat=.15, emit=0.0, name=None):
    k = name or f'{hexcol}_{rough}_{metal}_{coat}_{emit}'
    if k in MATS: return MATS[k]
    m = bpy.data.materials.new(k); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(hexcol), 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .08
    if emit:
        b.inputs['Emission Color'].default_value = (*srgb(hexcol), 1); b.inputs['Emission Strength'].default_value = emit
    MATS[k] = m; return m

def save_img(name, a):
    """a: h x w x 3 sRGB floats, row 0 at the top."""
    h, w = a.shape[:2]; im = bpy.data.images.new(name, w, h, alpha=False)
    rgba = np.ones((h, w, 4), np.float32); rgba[..., :3] = a[::-1]
    im.pixels.foreach_set(rgba.ravel()); im.filepath_raw = os.path.join(TEX, name + '.png'); im.file_format = 'PNG'; im.save()
    return bpy.data.images.load(im.filepath_raw)

def mat_img(name, img, rough=.5, coat=.1, proj=None):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes['Principled BSDF']; t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Coat Weight'].default_value = coat
    MATS[name] = m
    if proj: PROJ[name] = proj       # (metres per repeat, v offset): box-projected UVs at the end
    return m

def rgb(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

def tex_tile(name, base, n, grout=.86, alt=.018, px=256, rnd=False):
    a = np.empty((px, px, 3), np.float32); c = rgb(base); s = px // n; g = np.random.default_rng(5)
    for i in range(n):
        for j in range(n):
            a[i * s:(i + 1) * s, j * s:(j + 1) * s] = np.clip(c * (1 + (alt * g.uniform(-1, 1) if rnd else alt if (i + j) % 2 else -alt)), 0, 1)
    for k in range(n):
        a[k * s:k * s + 2] = c * grout; a[:, k * s:k * s + 2] = c * grout
    return save_img(name, a)

def tex_facade(name, col, px=256):
    """One 3 m x 3 m HDB corridor module: slab edge, pastel parapet, recessed wall with a window and a door."""
    c = rgb(col); a = np.empty((px, px, 3), np.float32); P = lambda v: int(v * px)
    def R(u0, v0, u1, v1, k): a[px - P(v1):px - P(v0), P(u0):P(u1)] = k      # v from the bottom
    R(0, 0, 1, 1, np.clip(c * .78 + .05, 0, 1))          # recess, in shade
    R(0, 0, 1, .40, c)                                    # parapet
    R(0, 0, 1, .06, rgb('#fbf8f0')); R(0, .37, 1, .40, rgb('#fbf8f0'))
    R(.10, .50, .60, .90, rgb('#fbf8f0')); R(.13, .53, .34, .87, rgb('#8fb7cf')); R(.36, .53, .57, .87, rgb('#a9cbe0'))
    R(.70, .40, .90, .90, rgb('#8a6248')); R(.73, .43, .87, .87, rgb('#a77a5a'))
    R(0, 0, .035, 1, rgb('#fbf8f0')); R(.965, 0, 1, 1, rgb('#fbf8f0'))
    return save_img(name, a)

def tex_chess(name, px=256):
    a = np.empty((px, px, 3), np.float32); a[:] = rgb('#3a2417'); s = (px - 32) // 8
    for i in range(8):
        for j in range(8):
            a[16 + i * s:16 + (i + 1) * s, 16 + j * s:16 + (j + 1) * s] = rgb('#f3ecd9' if (i + j) % 2 else '#5a3a26')
    return save_img(name, a)

# ---------------------------------------------------------------- geometry buffers (one mesh per material)
BM = {}; GRP = ['']          # GRP 'hi_' marks roofs and towers, hidden in the top-down collider check
def bm_of(m):
    k = GRP[0] + m.name
    if k not in BM:
        BM[k] = (bmesh.new(), m); BM[k][0].loops.layers.uv.verify()
    return BM[k][0]

def box(m, x0, y0, z0, x1, y1, z1, bev=.03, seg=2):
    """Axis-aligned box from game-space min and max."""
    bm = bm_of(m); sx, sy, sz = x1 - x0, z1 - z0, y1 - y0
    M = Matrix.Translation(((x0 + x1) / 2, -(z0 + z1) / 2, (y0 + y1) / 2)) @ Matrix.Diagonal((sx, sy, sz, 1))
    r = bmesh.ops.create_cube(bm, size=1, matrix=M)
    b = min(bev, min(sx, sy, sz) * .3)
    if b > .004:
        es = list({e for v in r['verts'] for e in v.link_edges})
        for f in bmesh.ops.bevel(bm, geom=es, offset=b, segments=seg, affect='EDGES', profile=.5)['faces']: f.smooth = True

def cbox(m, x, z, w, d, y0, h, bev=.03, seg=2): box(m, x - w / 2, y0, z - d / 2, x + w / 2, y0 + h, z + d / 2, bev, seg)

def cyl(m, x, y0, z, r0, r1, h, n=24, bev=.02):
    bm = bm_of(m)
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r0, radius2=r1, depth=h, matrix=Matrix.Translation((x, -z, y0 + h / 2)))
    fs = {f for v in r['verts'] for f in v.link_faces}; caps = [f for f in fs if len(f.verts) > 4]
    for f in fs: f.smooth = f not in caps
    if bev > .004:
        for f in bmesh.ops.bevel(bm, geom=list({e for f in caps for e in f.edges}), offset=min(bev, h * .3), segments=2, affect='EDGES', profile=.5)['faces']: f.smooth = True

def ball(m, x, y, z, r, sc=(1, 1, 1), u=16, v=10):
    bm = bm_of(m)
    M = Matrix.Translation((x, -z, y)) @ Matrix.Diagonal((sc[0], sc[2], sc[1], 1))
    for vt in bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r, matrix=M, calc_uvs=True)['verts']:
        for f in vt.link_faces: f.smooth = True

def quad(m, c, w, h, ry, uv=(0, 0, 1, 1), flat=False):
    """Textured plane at game centre c. ry as in three.js: 0 faces +z, pi faces -z, pi/2 faces +x. flat: lies on the ground."""
    bm = bm_of(m); L = bm.loops.layers.uv.verify(); c = Vector(c)
    rt = Vector((math.cos(ry), 0, -math.sin(ry))); up = Vector((math.sin(ry), 0, math.cos(ry))) * -1 if flat else Vector((0, 1, 0))
    ps = [c - rt * w / 2 - up * h / 2, c + rt * w / 2 - up * h / 2, c + rt * w / 2 + up * h / 2, c - rt * w / 2 + up * h / 2]
    f = bm.faces.new([bm.verts.new((p.x, -p.z, p.y)) for p in ps])
    for l, t in zip(f.loops, [(uv[0], uv[1]), (uv[2], uv[1]), (uv[2], uv[3]), (uv[0], uv[3])]): l[L].uv = t

def finish():
    objs = []
    for name, (bm, m) in BM.items():
        bm.normal_update()
        if m.name in PROJ:
            s, zo = PROJ[m.name]; L = bm.loops.layers.uv.verify()
            for f in bm.faces:
                n = f.normal; a = max(range(3), key=lambda i: abs(n[i]))
                for l in f.loops:
                    c = l.vert.co
                    l[L].uv = ((c.x / s, c.y / s) if a == 2 else (c.y / s, (c.z - zo) / s) if a == 0 else (c.x / s, (c.z - zo) / s))
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m)
        o = bpy.data.objects.new('VD_' + name, me); SC.collection.objects.link(o); objs.append(o)
    BM.clear(); return objs

def hi(on=True): GRP[0] = 'hi_' if on else ''

def tube(m, pts, r, n=8, joints=True):
    """Round rail through game-space points."""
    bm = bm_of(m); P = [Vector((p[0], -p[2], p[1])) for p in pts]
    for a, b in zip(P, P[1:]):
        d = b - a
        M = Matrix.Translation((a + b) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        for v in bmesh.ops.create_cone(bm, cap_ends=False, segments=n, radius1=r, radius2=r, depth=d.length, matrix=M)['verts']:
            for f in v.link_faces: f.smooth = True
    for p in (P if joints else []):
        for v in bmesh.ops.create_uvsphere(bm, u_segments=n, v_segments=4, radius=r, matrix=Matrix.Translation(p))['verts']:
            for f in v.link_faces: f.smooth = True

def wheel(x, y, z, r, ax):
    """Bike wheel standing in the plane that contains game axis ax ('x' or 'z')."""
    R = Matrix.Rotation(math.pi / 2, 4, 'X' if ax == 'x' else 'Y')
    for m, rr, t in ((DARK, r, .05), (RIM, r * .8, .056)):
        bmesh.ops.create_cone(bm_of(m), cap_ends=True, segments=20, radius1=rr, radius2=rr, depth=t, matrix=Matrix.Translation((x, -z, y)) @ R)

def bike(x, z, ax, col, flip=1, hb=.22):
    P = (lambda u, y, v=0: (x + u * flip, y, z + v)) if ax == 'x' else (lambda u, y, v=0: (x + v, y, z + u * flip))
    fm = mat(col, .35, coat=.5)
    for u in (-.52, .52): wheel(*P(u, .31), .31, ax)
    tube(fm, [P(-.52, .31), P(-.18, .8), P(.32, .84), P(.52, .31)], .025, 6); tube(fm, [P(-.18, .8), P(0, .3), P(.32, .84)], .025, 6); tube(fm, [P(-.52, .31), P(0, .3)], .02, 6)
    tube(DARK, [P(.32, .84), P(.3, .96)], .02, 6); tube(DARK, [P(.3, .96, -hb), P(.3, .96, hb)], .02, 6)
    ball(DARK, *P(-.2, .88), .09, (1, .5, 1), 8, 6)

# ---------------------------------------------------------------- textures and palette (hex values traced to voiddeck_REF.md lines)
def tex_terrazzo(name, base, px=256):
    g = np.random.default_rng(3); a = np.empty((px, px, 3), np.float32); a[:] = rgb(base)
    chips = [rgb(c) for c in ('#fbf8f0', '#8a8f98', '#c9a66b', '#5e5a55', '#e8d9c0')]
    for _ in range(1100):
        i, j, s = g.integers(0, px - 4), g.integers(0, px - 4), g.integers(2, 5)
        a[i:i + s, j:j + s] = chips[g.integers(0, 5)]
    return save_img(name, a)

def shade(h, k): return '#%02x%02x%02x' % tuple(int(min(1, v * k) * 255) for v in rgb(h))
# Update 6: concrete grey on structure, colour on accents only (bands, stripes, signs, shutters, play equipment)
BLOCK = ['#d6988c', '#7fb5a3']                 # REF 12 hues (pink 404, mint 405), calmer than Update 5
BAND = ['#b8544a', '#2f8a74']                  # REF 10: dark lower band in each block's colour
SKY = {'#cfe8d8': '#8fc0ae', '#f7e3a1': '#d9c27a', '#e8d1ef': '#b7a3cc'}        # REF 12 skyline blocks
CREAM = mat('#c9c4b8', .6, coat=.05, name='wall_concrete'); WHITE = mat('#f4f1ea', .4, coat=.2); CEIL = mat('#ddd6c6', .7, coat=0, emit=.2, name='ceiling')
BEAM = mat('#bcb5a6', .6, coat=0, name='beam'); STRIPE = mat('#f2b632', .4, coat=.3, name='accent_stripe')
STEEL = mat('#c9ccd0', .25, metal=1.0, coat=0); RIM = mat('#b9bdc2', .3, metal=.8, coat=0, name='rim'); DARK = mat('#2b2b2b', .5)
POST = mat('#8f979c', .4, coat=.2, name='post_paint'); STONE = mat('#c4bfb4', .6, coat=.05); STONE2 = mat('#a8a399', .6, coat=.05)
KERB = mat('#b9b2a4', .65, coat=0); HEDGE = mat('#4f9440', .7, coat=0); TURF = mat('#74ad58', .85, coat=0); PATH = mat('#bdb7aa', .7, coat=0, name='path')
PAVE = mat('#c9b9a0', .7, coat=0, name='pavilion_pad'); EPDM = mat('#3f95b8', .8, coat=0, name='epdm_blue'); EPDM2 = mat('#c8704f', .8, coat=0, name='epdm_red')
LEAF = [mat(c, .65, coat=0) for c in ('#4f9440', '#3f8438', '#68a54c')]; TRUNK = mat('#7a5a40', .6, coat=0); TIMBER = mat('#a8744a', .55, coat=.1)
GLOW = mat('#fff6dc', .3, emit=4.0); RED = mat('#d3262b', .35, coat=.4); YEL = mat('#f2c230', .35, coat=.4)
BLUE = mat('#2f6fb0', .35, coat=.4); LIME = mat('#9ac83a', .4, coat=.4); TEAL = mat('#2f9f95', .4, coat=.4)
FLOOR = mat_img('floor_cement', tex_tile('vd_floor', '#cfc6b3', 2, grout=.86, alt=.02), .65, .05, proj=(2.0, 0))    # REF 4 cement screed floor
TERR = mat_img('terrazzo', tex_terrazzo('vd_terrazzo', '#b9b5aa'), .35, .4, proj=(1.0, 0))                          # REF 8, grey base
RING = [mat(c, .3, coat=.5) for c in ('#d3262b', '#f2c230', '#2f7fc4', '#3aa35a')]                                 # spring rider colours
CHESS = mat_img('chess', tex_chess('vd_chess'), .4, .3)                                                            # REF 5
if not os.path.exists(os.path.join(TEX, 'signs.json')):
    subprocess.run(['python3', os.path.join(os.path.dirname(__file__), 'voiddeck_signs.py')], check=True)
SIGNS = mat_img('signs', bpy.data.images.load(os.path.join(TEX, 'signs.png')), .4, .3)
SJ = json.load(open(os.path.join(TEX, 'signs.json')))
def suv(n):
    x, y, w, h = SJ['cells'][n]; S = SJ['size']; return (x / S, 1 - (y + h) / S, (x + w) / S, 1 - y / S)

def facade(col, base):
    k = f'facade_{col}_{base}'
    return MATS.get(k) or mat_img(k, tex_facade('vd_facade_' + col.lstrip('#'), col), .55, .1, proj=(3.0, base))

CLOTH = ['#e8452f', '#f2c230', '#2f7fc4', '#fbf8f0', '#e96aa0', '#3aa35a']
def tower(x, z, w, d, y0, h, col, laundry=0):
    dk = mat(shade(col, .72), .45, coat=.2); lt = mat(shade(col, .86), .5, coat=.1)
    cbox(facade(col, y0), x, z, w, d, y0, h, .12)
    for k in range(int(h // 3) + 1): cbox(dk, x, z, w + .5, d + .5, y0 + 3 * k - .1, .25, .05, 1)       # corridor slab edges
    for sx in (-1, 1):
        for sz in (-1, 1): cbox(dk, x + sx * w / 2, z + sz * d / 2, .9, .9, y0, h, .06, 1)              # corner pilasters
    cbox(lt, x, z, w + .7, d + .7, y0 + h, .5, .1)
    cbox(mat(col, .5, coat=.1), x, z, w * .3, d * .4, y0 + h + .5, 2.2, .15); cbox(dk, x, z, w * .3 + .3, d * .4 + .3, y0 + h + 2.7, .25, .08)
    if laundry:                                                                                           # REF 11: bamboo poles with washing
        g = np.random.default_rng(7); fx = x + laundry * w / 2; pole = mat('#d9b96a', .5, coat=.1)
        for k in range(6):
            for i in range(int(d // 3)):
                if g.random() < .35: continue
                py, pz = y0 + 3 * k + 1.25, z - d / 2 + 1.5 + i * 3 + g.uniform(-.6, .6)
                box(pole, min(fx, fx + laundry * 2), py, pz - .02, max(fx, fx + laundry * 2), py + .04, pz + .02, 0)
                for j in range(int(g.integers(2, 4))):
                    cx = fx + laundry * (.45 + j * .55); cbox(mat(CLOTH[int(g.integers(0, 6))], .7, coat=0), cx, pz, .42, .03, py - g.uniform(.5, .8), g.uniform(.5, .8) - .0, 0)

# ---------------------------------------------------------------- map boxes
def stripes(x, z, w, d, y0, h, n, ma, mb):
    for i in range(n): cbox(ma if i % 2 else mb, x - w / 2 + (i + .5) * w / n, z, w / n, d, y0, h, .015, 1)

def pyr(m, x, z, w, d, y0, h, top=.2):
    """Hipped roof: a four-sided frustum over a w x d footprint."""
    M = Matrix.Translation((x, -z, y0 + h / 2)) @ Matrix.Diagonal((w, d, h, 1)) @ Matrix.Rotation(math.pi / 4, 4, 'Z')
    bmesh.ops.create_cone(bm_of(m), cap_ends=True, segments=4, radius1=.7071, radius2=.7071 * top, depth=1, matrix=M)

def build_boxes():
    nplay = 0
    for b in X['boxes']:
        x, z, w, d, h, col = b[:6]; y0 = b[6] if len(b) > 6 else 0; f = b[7] if len(b) > 7 else 's'
        if 'i' in f: continue
        c, _, tk = col.partition('@'); c = c.lower(); blk = 0 if x < 0 else 1; lo = min(w, d); hi('r' in f)
        if tk == 'hdb': tower(x, z, w, d, y0, h, BLOCK[blk], laundry=1 if x < 0 else -1)
        elif tk == 'zinc': cbox(mat('#8a969b', .4, metal=.3, coat=.2, name='linkway_roof'), x, z, w, d, y0, h, .05); cbox(mat(BAND[blk], .4, coat=.3), x, z, w + .06, d + .06, y0 - .02, .12, .02, 1)
        elif tk == 'pillar':
            cbox(CREAM, x, z, w, d, y0, h, .08, 3); cbox(mat(BAND[blk], .4, coat=.3), x, z, w + .04, d + .04, 0, 1.2, .08, 3); cbox(STRIPE, x, z, w + .05, d + .05, 1.2, .12, .02, 1)
        elif tk == 'walltile':
            cbox(CREAM, x, z, w, d, y0, h, .05)
            if y0 == 0 and h >= 2: cbox(mat(BAND[blk], .4, coat=.3), x, z, w + .03, d + .03, 0, 1.2, .03, 1); cbox(STRIPE, x, z, w + .04, d + .04, 1.2, .12, .02, 1)
        elif tk == 'shutter':
            sm = mat('#4a7fb0', .4, metal=.3, coat=.3)
            for i in range(int(h / .15)): cbox(sm, x, z, w, d, y0 + i * .15, .14, .02, 1)
        elif c == '#e3c46a':
            if abs(x) < 3: cbox(BLUE if lo < .5 else POST, x, z, w, d, y0, h, .04)     # playground tower: blue steel posts, grey deck
            elif abs(abs(x) - 13.3) < .2: cbox(CREAM, x, z, w, d, y0, h, .05); cbox(TEAL, x, z, w + .06, d + .06, y0 + h - .1, .1, .03, 1)     # low concrete park walls, teal coping
            else: cbox(CREAM, x, z, w, d, y0, h, .08); cbox(YEL, x, z, w + .04, d + .04, y0 + h - .25, .25, .04, 1)                          # clock tower
        elif c == '#9ec9df': cbox(LIME, x, z, w, d, y0, h, .03)                       # HDPE deck panels
        elif c == '#c8221b':
            if 'x' in f: cbox(YEL, x, z, w, d, y0, h, .05); pyr(RED, x, z, w + .3, d + .3, y0 + h, 1.3, .12)     # playground tower roof
            elif 'r' in f: stripes(x, z, w, d, y0, h, 8, RED, YEL)                  # provision shop awning
            else: bike(x, z, 'z', CLOTH[int(abs(x) * 4) % 3])                         # shelter bikes
        elif c in ('#2b2b2b', '#3a3a3a'): continue                                    # old square wheels and bars, replaced by bike()
        elif c == '#5aa04a': cbox(KERB, x, z, w, d, 0, .4, .05); cbox(HEDGE, x, z, w - .04, d - .04, .36, h - .36, .2, 3)
        elif c == '#5f8f6a': cbox(KERB, x, z, w, d, 0, .3, .04); cbox(HEDGE, x, z, w - .04, d - .04, .28, h - .28, .15, 3)
        elif c == '#8fae8a':
            if 'r' in f: cbox(POST, x, z, w, d, y0, h, .04)                           # bicycle shelter roof, grey steel
            else: nplay += 1; cbox(mat('#2f9fd0', .4, coat=.4) if nplay % 2 else mat('#f2a03a', .4, coat=.4), x, z, w, d, y0, h, .1, 3)     # HDPE play blocks
        elif c == '#b5a48c': cbox(TERR, x, z, w, d, y0, h, .08, 3)
        elif c == '#e8e0d0': cbox(CEIL, x, z, w, d, y0, h, 0)
        elif c == '#5f9a6a': cbox(TURF, x, z, w, d, y0, h, 0)
        elif 'g' in f: cbox(GLOW, x, z, w, d, y0, h, .01)
        elif c == '#6d6f73': cbox(POST, x, z, w, d, y0, h, .03 if lo > .1 else .01)
        elif c == '#c9ccd0': cbox(mat('#2f5f4a', .4, coat=.3, name='park_steel'), x, z, w, d, y0, h, .02)       # pavilion posts
        elif c == '#f2f2ee': cbox(WHITE, x, z, w, d, y0, h, .03); pyr(mat('#a85a44', .6, coat=.05, name='pavilion_roof'), x, z, w + .8, d + .8, y0 + h, 1.7, .3)     # park pavilion: hipped tile roof
        elif c == '#2f5fa8': cbox(WHITE, x, z, w, d, y0, h, .01)                      # pavilion fascia
        else: cbox(mat(c, .45, coat=.2), x, z, w, d, y0, h, .02)
    hi(False)

def mbox(mt, m, x0, y0, z0, x1, y1, z1, bev=.03, seg=2):
    box(mt, min(m * x0, m * x1), y0, min(m * z0, m * z1), max(m * x0, m * x1), y1, max(m * z0, m * z1), bev, seg)

def build_ground():
    box(FLOOR, -45, -.4, -30, 45, 0, 30, 0)
    box(mat('#78ad5c', .85, coat=0), -200, -.6, -200, 200, -.04, 200, 0)
    box(EPDM, -9, 0, -6, 9, .03, 6, 0)                                                # playground rubber safety floor
    for j, (dx, dz) in enumerate(((-6, -3.6), (6, 3.6), (-5.2, 4), (5.2, -4))): cyl((EPDM2, YEL)[j % 2], dx, 0, dz, 1.2, 1.2, .036, 28, 0)
    for a in ((-9.3, -6.3, 9.3, -6), (-9.3, 6, 9.3, 6.3), (-9.3, -6, -9, 6), (9, -6, 9.3, 6)): box(KERB, a[0], 0, a[1], a[2], .04, a[3], 0)
    for m in (1, -1):
        mbox(TERR, m, -34, 0, 19.5, -26, .02, 23.5, 0)                                # terrazzo lift lobby floor
        mbox(mat('#8d8d88', .6, coat=0), m, -12.7, 0, -3, -12.4, .015, 29.8, 0)        # REF 11: drain grate strip
        hi()
        for bx in (-37.7, -29.7, -21.7, -13.8): mbox(BEAM, m, bx - .25, 3.8, -3.1, bx + .25, 4.2, 29.7, .03, 1)       # ceiling beams
        for bz in (2.9, 11.4, 19.9): mbox(BEAM, m, -44.4, 3.85, bz - .25, -13.1, 4.2, bz + .25, .03, 1)
        hi(False)

def build_stairs():
    for s in (b for b in SOL if b[6] == 'stair'): box(TEAL, s[0], s[1], s[2], s[3], s[4], s[5], .04)       # HDPE slide and steps

def build_play():
    """Mid strip: planter beds, rubber mounds, bike rack. Same colliders as before, no dragon."""
    for m in (1, -1):
        G = lambda x, y, z: (m * x, y, m * z)
        mbox(STONE, m, -8.5, 0, 2.0, -3.5, .75, 3.2, .05)                             # raised concrete planter bed with a clipped hedge
        mbox(HEDGE, m, -8.46, .7, 2.04, -3.54, 1.1, 3.16, .15, 3)
        x, z = m * -9.0, m * -13.0                                                    # rubber climbing mound
        ball(EPDM2, x, 0, z, 1.3, (1, 1.2 / 1.3, 1), 28, 14)
        for j in range(7): ball(RING[j % 4], x + .75 * math.cos(j * .9), .96, z + .75 * math.sin(j * .9), .09, (1, .6, 1), 8, 6)       # climbing holds
        mbox(TERR, m, -18.5, 0, -1.3, -15.5, .12, -.7, .03)                           # bike rack
        mbox(POST, m, -18.5, .12, -1.04, -15.5, 1.0, -.96, .02)
        for ex in (-18.44, -17, -15.56):
            tube(STEEL, [G(ex, .1, -1.26), G(ex, .9, -1.26), G(ex, .97, -1.19), G(ex, .97, -.81), G(ex, .9, -.74), G(ex, .1, -.74)], .03)
        bike(m * -17.72, m * -1.15, 'x', '#d3262b', m, .13); bike(m * -16.28, m * -.85, 'x', '#2f7fc4', -m, .13)

# ---------------------------------------------------------------- neighbourhood park and shop rows (colliders in voiddeck_park.py)
def ptree(x, z, kind):
    """Rain tree (wide umbrella) or angsana (tall dome). Trunk matches the 0.5 m collider, crown starts above 4 m."""
    g = GRP[0]; cyl(TRUNK, x, 0, z, .25, .22, 2.7, 12, 0); hi()
    wide = kind == 'rain'; R, cy, fl = (2.6, 5.9, .5) if wide else (2.0, 5.7, .9)
    for j in range(5):
        a = j * 1.257 + .3; c, s = math.cos(a), math.sin(a); ex, ez = x + c * R * .8, z + s * R * .8
        tube(TRUNK, [(x + c * .17, 2.55, z + s * .17), (x + c * .7, 4.0, z + s * .7), (ex, cy - .3, ez)], .1, 6)
        ball(LEAF[j % 3], ex, cy, ez, R * .75, (1, fl, 1), 14, 9)
    ball(LEAF[1], x, cy + (.5 if wide else .9), z, R, (1, fl, 1), 14, 9); GRP[0] = g

def palm(x, z):
    g = GRP[0]; cyl(mat('#9a8468', .7, coat=0), x, 0, z, .17, .15, 5, 10, 0); hi()
    for j in range(8):
        a = j * math.pi / 4; c, s = math.cos(a), math.sin(a)
        tube(LEAF[j % 3], [(x + c * d, y, z + s * d) for d, y in ((.3, 5.05), (1.0, 5.8), (1.9, 5.6), (2.6, 4.7))], .19, 6)       # chunky toy fronds
    ball(LEAF[1], x, 5.75, z, .42, (1, 1, 1), 10, 6)
    GRP[0] = g

def station(b, kind):
    """Outdoor fitness station on an open steel frame. b: game-space collider box."""
    x0, _, z0, x1, h, z1 = b; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; r = .05; ends = (x0 + r, x1 - r)
    for px in ends: cyl(BLUE, px, 0, cz, r, r, h - .04, 10, 0)
    tube(YEL, [(ends[0], h - .04, cz), (ends[1], h - .04, cz)], .04, 8)
    if kind == 'bars':                                                                # parallel bars
        for pz in (z0 + r, z1 - r):
            for px in ends: cyl(BLUE, px, 0, pz, r, r, .9, 10, 0)
            tube(YEL, [(ends[0], .9, pz), (ends[1], .9, pz)], .04, 8)
    elif kind == 'pullup': cyl(BLUE, cx, 0, cz, r, r, h - .04, 10, 0); tube(YEL, [(cx, 1.7, cz), (ends[1], 1.7, cz)], .04, 8)
    else:                                                                             # air walker: two swinging legs with foot plates
        for s in (-1, 1):
            tube(STEEL, [(cx + s * .2, h - .04, cz), (cx + s * .2, .3, cz + s * .14)], .035, 8); cbox(RED, cx + s * .2, cz + s * .14, .16, .34, .24, .06, .02, 1)
        tube(YEL, [(ends[0], .95, cz), (ends[1], .95, cz)], .03, 8)

def shopfront(m, x, z, ry, w, n):
    """Thin wall dressing: goods behind an open shutter, rolled shutter, signboard, pilasters. ry is the wall normal for the west half."""
    ry += math.pi if m < 0 else 0; x, z = m * x, m * z
    nx, nz = math.sin(ry), math.cos(ry); rx, rz = math.cos(ry), -math.sin(ry)
    def wb(mt, u, y0, ww, h, t):
        cbox(mt, x + rx * u + nx * t / 2, z + rz * u + nz * t / 2, *((ww, t) if abs(nz) > .5 else (t, ww)), y0, h, min(.015, t * .3), 1)
    quad(SIGNS, (x + nx * .05, 1.1, z + nz * .05), w, 2.2, ry, suv('f_' + n))
    for u in (-w / 2 - .08, w / 2 + .08): wb(WHITE, u, 0, .16, 2.96, .07)
    for i in range(4): wb(mat('#4a7fb0', .4, metal=.3, coat=.3), 0, 2.22 + i * .18, w, .17, .08)
    wb(mat('#3b4250', .5), 0, 2.96, 4.33, .84, .05); quad(SIGNS, (x + nx * .062, 3.38, z + nz * .062), 4.13, .8, ry, suv('b_' + n))

def build_park():
    import voiddeck_park
    for m in (1, -1):
        mbox(TURF, m, -44.6, 0, -29.5, -13.55, .02, -3.2, 0)                          # lawn over the whole open section
        for a in ((-44.6, -8, -13.55, -3.2), (-44.2, -25.5, -42, -8), (-16.2, -25.5, -14, -8), (-44.6, -29.5, 13, -25.5),          # looping footpath: apron, west leg, east leg, covered linkway
                  (-32, -9.5, -30, -8), (-27.6, -25.5, -25.4, -18.5), (-41.2, -25.5, -32.8, -21.4)): mbox(PATH, m, a[0], 0, a[1], a[2], .035, a[3], 0)
        mbox(PAVE, m, -36.5, 0, -18.5, -25.5, .045, -9.5, 0)                          # pavilion pad
        mbox(EPDM2, m, -19.9, 0, -16.4, -13.6, .045, -9.9, 0)                         # fitness corner rubber pad
        hi()
        for tx, tz, k in ((-48.5, -10, 'rain'), (-48.5, -23, 'angsana'), (-36, -34, 'rain'), (-22, -34, 'rain'), (-48.5, 12, 'angsana')): ptree(m * tx, m * tz, k)      # outside the hedges, no colliders needed
        hi(False)
        shopfront(m, -29, .8, 0, 5.2, 'kopi'); shopfront(m, -41.85, 24.5, math.pi, 4.6, 'tcm')
        shopfront(m, -36.65, 24.5, math.pi, 4.6, 'barber'); shopfront(m, -44.5, 21.6, math.pi / 2, 4.6, 'bakery')
    binm = mat('#2f7d4f', .4, coat=.3)
    for k, b, m in voiddeck_park.both():
        x0, _, z0, x1, h, z1 = b; x, z = (x0 + x1) / 2, (z0 + z1) / 2
        if k in ('rain', 'angsana'): ptree(x, z, k)
        elif k == 'palm': palm(x, z)
        elif k in ('bench', 'sbench'): box(STONE2, x0 + .03, 0, z0 + .03, x1 - .03, .37, z1 - .03, .03); box(TIMBER, x0, .36, z0, x1, h, z1, .03)
        elif k == 'bin': cyl(binm, x, 0, z, .27, .31, .8, 20, .03); cyl(YEL, x, .8, z, .31, .31, .08, 20, .02)
        elif k == 'lamp':
            pm = mat('#2f5f4a', .4, coat=.3, name='park_steel'); cyl(pm, x, 0, z, .09, .09, 3.6, 10, 0); cbox(GLOW, x, z, .2, .2, 3.6, .34, .03); cyl(pm, x, 3.94, z, .1, .1, .06, 12, 0)
        elif k == 'display':                                                          # medical hall table: red cloth, baskets of dried goods
            box(RED, x0, 0, z0, x1, h - .04, z1, .02); box(TIMBER, x0, h - .05, z0, x1, h, z1, .02)
            for j, u in enumerate((-.7, -.35, .35, .7)):
                px, pz = (x + u, z) if x1 - x0 > z1 - z0 else (x, z + u)
                cyl(mat('#c9a66b', .6, coat=0), px, h, pz, .14, .16, .1, 12, 0); ball(mat(('#b9742f', '#7a4a2a', '#a8352c', '#d9b96a')[j], .6, coat=0), px, h + .1, pz, .13, (1, .5, 1), 10, 6)
        elif k == 'case':                                                             # bakery glass case
            box(WHITE, x0, 0, z0, x1, .45, z1, .02); box(mat('#bfe0ee', .15, coat=.6, name='case_glass'), x0 + .02, .45, z0 + .02, x1 - .02, h, z1 - .02, .02)
        else: station(b, k)

# ---------------------------------------------------------------- props
def build_props():
    binm = mat('#2f7d4f', .4, coat=.3); bind = mat('#f2c230', .4, coat=.3); tube_h = mat('#d9d4c8', .4); leg = mat('#6d6f73', .35, metal=.8, coat=0)
    for i, p in enumerate(X['props']):
        k, x, z = p['k'], p['x'], p['z']; ry = p.get('ry', 0); along_z = abs(math.sin(ry)) > .7
        if k == 'stonetable':                                                         # REF 5: concrete chess table and stools
            cyl(STONE2, x, 0, z, .3, .2, .67, 20); cyl(STONE, x, .67, z, .6, .6, .1, 32, .03)
            quad(CHESS, (x, .7715, z), .5, .5, 0, flat=True)
            for j in range(4):
                a = j * math.pi / 2 + .4; cyl(STONE, x + math.cos(a) * 1.05, 0, z + math.sin(a) * 1.05, .2, .23, .42, 20, .04)
        elif k == 'table':                                                            # M6: kopitiam marble top and red plastic stools. Under the park pavilion: concrete
            pk = abs(abs(z) - 14) < .1; top, st = (STONE, STONE2) if pk else (mat('#3aa39a', .3, coat=.5), RED)
            cyl(leg, x, 0, z, .36, .3, .05, 20, .01); cyl(leg, x, .05, z, .07, .07, .75, 12, 0); cyl(top, x, .8, z, .75, .75, .06, 32, .02)
            for j in range(4):
                a = j * math.pi / 2 + math.pi / 4; sx, sz = x + math.cos(a) * 1.25, z + math.sin(a) * 1.25
                cyl(st, sx, 0, sz, .24, .21, .4, 16, 0); cyl(st, sx, .38, sz, .2, .24, .06, 20, .02)
        elif k == 'bench':
            w, d = (.45, 1.8) if along_z else (1.8, .45)
            cbox(TERR, x, z, w, d, .36, .1, .04)
            cbox(STONE2, x, z, w - .06, d - .06, 0, .37, .03)                     # solid concrete plinth, as on real void deck benches
        elif k == 'bin':
            cyl(binm, x, 0, z, .27, .31, .8, 20, .03); cyl(bind, x, .8, z, .31, .31, .08, 20, .02)
        elif k == 'tube':
            y = p.get('y', 4); hi()
            cbox(tube_h, x, z, 1.75, .24, y + .03, .07, .02); cbox(GLOW, x, z, 1.6, .07, y - .04, .07, .03); hi(False)
        elif k == 'vending':
            s = -1 if math.cos(ry) < 0 else 1
            cbox(mat('#2f7fc4', .35, coat=.5), x, z, 1, .8, 0, 1.6, .06, 3)
            quad(SIGNS, (x - .1 * s, .98, z + s * .405), .64, .9, 0 if s > 0 else math.pi, suv('vend'))
            cbox(DARK, x + .34 * s, z + s * .4, .2, .02, .8, .4, .01); cbox(DARK, x - .1 * s, z + s * .4, .66, .02, .2, .2, .01)
        elif k == 'crates':
            cm = [mat('#e8742a', .45, coat=.2), mat('#2f6fb0', .45, coat=.2)]
            for j, dx in enumerate((-.3, .3)):
                for t in range(3): cbox(cm[(j + t) % 2], x + dx, z, .6, .8, t * .35, .35, .03)
        elif k == 'spring':                                                           # spring riders
            m = RING[i % 4]
            cyl(leg, x, 0, z, .09, .09, .38, 10, 0); ball(m, x, .62, z, .25, (1.4, 1.1, 1)); ball(m, x + .27, .78, z, .12, (1, 1, .8)); ball(m, x + .36, .72, z, .07, (1.3, .8, .8))
            tube(STEEL, [(x + .12, .7, z - .24), (x + .12, .7, z + .24)], .02, 6)
        elif k == 'tree': tree(p)
    hi()
    for o in X['outside']:
        if o['k'] == 'tree': tree(o)
        else: tower(o['x'], o['z'], o['w'], o['d'], 0, o['h'], SKY.get(o['c'], o['c']))
    hi(False)

def tree(p):
    x, z, s = p['x'], p['z'], p.get('s', 1); g = GRP[0]
    cyl(TRUNK, x, 0, z, .25 * s, .21 * s, 3 * s, 12, 0); hi()
    for j, (dx, dy, dz, r) in enumerate([(0, 1.5, 0, 1.6), (-.9, .9, .5, 1.15), (.8, 1.0, -.6, 1.2), (.2, .8, .9, 1.0)]):
        ball(LEAF[j % 3], x + dx * s, 3 * s + dy * s + .15, z + dz * s, r * s, (1, .85, 1), 14, 9)
    GRP[0] = g

# ---------------------------------------------------------------- signs and wall dressing
def build_signs():
    frame = mat('#3b4250', .5)
    for p in X['signs']['place']:
        r = p['row']; ry = p.get('ry', 0); n = (math.sin(ry), math.cos(ry)); w, h = p['w'], p['h']
        quad(SIGNS, (p['x'], p['y'], p['z']), w, h, ry, suv(f'row{r}'))
        bx, bz = p['x'] - n[0] * .025, p['z'] - n[1] * .025
        if abs(n[0]) > .5: cbox(frame, bx, bz, .04, w + .1, p['y'] - h / 2 - .05, h + .1, .015)
        else: cbox(frame, bx, bz, w + .1, .04, p['y'] - h / 2 - .05, h + .1, .015)

def build_extras():
    """Lift lobby, letter boxes, notice board, shop front, clocks, birdcages. Thin wall dressing or above head height only."""
    door = mat('#b9bdc2', .3, metal=.9, coat=0); lb = mat('#2f6fb0', .4, coat=.4); lbd = mat('#f2b632', .4, coat=.4); frame = mat('#c8221b', .45, coat=.3); cage = mat('#b98a55', .5, coat=.1)
    for m in (1, -1):
        zf = m * 23.5; s = -m; face = 0 if s > 0 else math.pi          # lift core face, s points out of the wall
        for dx in (-30.65, -29.35):
            cbox(DARK, m * dx, zf + s * .02, 1.2, .04, 0, 2.2, .01)
            for h2 in (-.26, .26): cbox(door, m * dx + h2, zf + s * .045, .5, .03, .02, 2.1, .01)
            cbox(DARK, m * dx, zf + s * .03, .5, .05, 2.3, .18, .01); cbox(mat('#ff9a2e', .3, emit=5), m * dx, zf + s * .06, .22, .01, 2.34, .1, 0)
        cbox(STEEL, m * -30, zf + s * .03, .14, .04, 1.05, .3, .01)
        for bx in (-32.5, -27.5):                                      # REF 4: letter box banks
            cbox(lb, m * bx, zf + s * .04, 2.4, .08, .45, 1.4, .02)
            for i in range(8):
                for j in range(5):
                    cx, cy = m * (bx - 1.05 + i * .3), .52 + j * .27
                    cbox(lbd, cx, zf + s * .09, .26, .02, cy, .23, .008, 1); cbox(DARK, cx, zf + s * .102, .16, .006, cy + .16, .025, 0)
        nz = m * 23.35                                                 # REF 11: notice board by the lift lobby
        cbox(frame, m * -23.25, nz + s * .03, 1.8, .05, .9, 1.15, .015); quad(SIGNS, (m * -23.25, 1.475, nz + s * .062), 1.68, 1.03, face, suv('notice'))
        quad(SIGNS, (m * -29, 1.1, m * -3.2 + s * -.0 - m * .012), 5.2, 2.2, math.pi if m > 0 else 0, suv('shop'))        # mama shop goods (M5)
        quad(SIGNS, (m * -25.985, 1.75, m * -1.2), .5, .5, math.pi / 2 * m, suv('nosmoke'))                              # WORDING.md sign_nosmoke
        quad(SIGNS, (m * -26.6, 2.6, zf + s * .012), .5, .5, face, suv('nosmoke'))
        cx, cz = m * -9.3, m * 14.3                                    # playground clock
        for ry, ox, oz in ((0, 0, .912), (math.pi, 0, -.912), (math.pi / 2, .912, 0), (-math.pi / 2, -.912, 0)): quad(SIGNS, (cx + ox, 1.2, cz + oz), 1.0, 1.0, ry, suv('clock'))
        hi()
        quad(SIGNS, (m * -12.6, 31, m * 13.5), 10, 2.5, math.pi / 2 * m, suv('row0' if m > 0 else 'row1'))                # painted block number on the gable
        for bx, bz in ((-20, 26.2), (-18.6, 27.4), (-41.5, 12)):       # REF 6: birdcages hung in corners, above head height
            tube(STEEL, [(m * bx, 4.2, m * bz), (m * bx, 2.95, m * bz)], .012, 6, False)
            cyl(cage, m * bx, 2.55, m * bz, .19, .19, .34, 14, .02); cyl(cage, m * bx, 2.89, m * bz, .19, .03, .1, 14, 0)
        hi(False)

# ---------------------------------------------------------------- collider check
def collider_check(objs):
    """Ray test of every dressed v2 collider against the built meshes. Top within 5 cm, and each side face reached within 5 cm."""
    from mathutils.bvhtree import BVHTree
    vs, ps = [], []
    for o in objs:
        n = len(vs); vs += [v.co.copy() for v in o.data.vertices]; ps += [[n + i for i in p.vertices] for p in o.data.polygons]
    T = BVHTree.FromPolygons(vs, ps); bad = []; n = 0
    for s in SOL:
        x0, y0, z0, x1, y1, z1, f = s
        if 'i' in f or 'r' in f: continue
        n += 1; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; why = []
        h = T.ray_cast(Vector((cx, -cz, y1 + .25)), Vector((0, 0, -1)))
        roofed = any('r' in r[6] and r[0] <= cx <= r[3] and r[2] <= cz <= r[5] and -.05 <= r[1] - y1 <= .35 for r in SOL)     # a roof collider sits right on top
        if h[0] is None or (abs(h[0].z - y1) > .05 and not (roofed and h[0].z > y1)): why.append(f'top {None if h[0] is None else round(h[0].z, 2)}')
        for fr in (.15, .5, .85):
            y = y0 + (y1 - y0) * fr
            for o, d in (((x0 - .25, y, cz), (1, 0, 0)), ((x1 + .25, y, cz), (-1, 0, 0)), ((cx, y, z0 - .25), (0, 0, 1)), ((cx, y, z1 + .25), (0, 0, -1))):
                h = T.ray_cast(Vector((o[0], -o[2], o[1])), Vector((d[0], -d[2], d[1])))
                if h[0] is None or h[3] > .30: why.append(f'side@{fr}'); break
        if why: bad.append(([round(v, 2) for v in s[:6]], f, why))
    print(f'COLLIDER CHECK {n - len(bad)}/{n} pass')
    for b in bad: print('  FAIL', b)

def outlines():
    red = mat('#ff0000', .5, emit=1, name='chk_red'); GRP[0] = 'chk_'; t = .07
    for s in SOL:
        x0, _, z0, x1, _, z1 = s[:6]
        for a in ((x0, z0, x1, z0 + t), (x0, z1 - t, x1, z1), (x0, z0, x0 + t, z1), (x1 - t, z0, x1, z1)): box(red, a[0], 60, a[1], a[2], 60.05, a[3], 0)
    GRP[0] = ''; return finish()

# ---------------------------------------------------------------- lighting and shots
def look_at(o, t): o.rotation_euler = (Vector(t) - o.location).to_track_quat('-Z', 'Y').to_euler()

def stage():
    w = bpy.data.worlds.new('World'); SC.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (*srgb('#7fbfe6'), 1); bg.inputs[1].default_value = .8
    sx, sy, sz = RAW['look']['sun'][2]                        # sun direction only, as the brief says
    d = bpy.data.lights.new('sun', 'SUN'); d.energy = 3.6; d.color = (1, .9, .76); d.angle = .04
    o = bpy.data.objects.new('sun', d); SC.collection.objects.link(o); o.location = (sx, -sz, sy); look_at(o, (0, 0, 0))
    for m in (1, -1):          # warm fill under each block, so the void deck is not a cave
        for dx in (-36, -21):
            a = bpy.data.lights.new('deck', 'AREA'); a.shape = 'RECTANGLE'; a.size = 14; a.size_y = 30; a.energy = 2400; a.color = (1, .85, .66)
            ao = bpy.data.objects.new('deck', a); SC.collection.objects.link(ao); ao.location = (m * dx, -m * 13.3, 3.7)
    SC.render.engine = 'BLENDER_EEVEE'; SC.eevee.taa_render_samples = 32
    SC.view_settings.view_transform = 'AgX'; SC.view_settings.look = 'AgX - Punchy'
    SC.render.image_settings.file_format = 'PNG'
    for k, v in (('use_shadows', True), ('use_raytracing', True)):
        try: setattr(SC.eevee, k, v)
        except Exception: pass
    cd = bpy.data.cameras.new('cam'); cd.clip_end = 600; cam = bpy.data.objects.new('cam', cd); SC.collection.objects.link(cam); SC.camera = cam
    return cam

def shoot(cam, name, pos, tgt, lens=28, res=(1600, 900)):
    """pos and tgt in game coords."""
    cam.location = (pos[0], -pos[2], pos[1]); look_at(cam, (tgt[0], -tgt[2], tgt[1])); cam.data.lens = lens; cam.data.type = 'PERSP'
    SC.render.resolution_x, SC.render.resolution_y = res; SC.render.filepath = os.path.join(SHOTS, name + '.png')
    bpy.ops.render.render(write_still=True)

def hero(name, x, z, face):
    """face: game point (x, z) the hero looks at."""
    p = os.path.join(ROOT, 'assets/heroes', name + '.glb')
    if not os.path.exists(p): return
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=p)
    for o in set(bpy.data.objects) - before:
        if o.parent is None:
            o.location = (x, -z, 0); dx, dy = face[0] - x, -face[1] + z
            o.rotation_mode = 'XYZ'; o.rotation_euler = (o.rotation_euler[0], o.rotation_euler[1], math.atan2(dy, dx) - math.pi / 2)

# ---------------------------------------------------------------- main
build_ground(); build_boxes(); build_stairs(); build_play(); build_park(); build_props(); build_signs(); build_extras()
objs = finish()
tris = 0
for o in objs:
    o.data.calc_loop_triangles(); tris += len(o.data.loop_triangles)
print(f'VOIDDECK tris={tris} materials={len(MATS)} objects={len(objs)}')
collider_check(objs)
os.makedirs(os.path.join(ROOT, 'assets/maps'), exist_ok=True)
for o in objs: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets/maps/voiddeck.glb'), export_format='GLB', use_selection=True, export_yup=True, export_apply=True)

cam = stage()
want = ARGS or ['overview', 'topdown_check', 'ground_a', 'ground_b', 'detail', 'park', 'shops']
if 'topdown_check' in want:                    # roofs, towers and tree crowns hidden, every v2 collider outlined in red
    chk = outlines()
    for o in objs: o.hide_render = o.name.startswith('VD_hi_')
    cam.location = (0, 0, 120); cam.rotation_euler = (0, 0, 0); cam.data.type = 'ORTHO'; cam.data.ortho_scale = 94
    SC.render.resolution_x, SC.render.resolution_y = 1600, 1100; SC.render.filepath = os.path.join(SHOTS, 'topdown_check.png')
    SC.view_settings.view_transform = 'Standard'; bpy.ops.render.render(write_still=True); SC.view_settings.view_transform = 'AgX'; SC.view_settings.look = 'AgX - Punchy'
    for o in objs: o.hide_render = False
    for o in chk: o.hide_render = True
hero('ahma', -31.5, 6.2, (-41, 7.5)); hero('gym', -27.5, 8.6, (-41, 7.5)); hero('tarik', -34, 9.0, (-41, 7.5))
hero('siao', -12, 2.4, (-24, 2)); hero('gym', -6.2, -.4, (-24, 2)); hero('ahma', -3.0, 6.0, (9, 8))
hero('gym', -17.4, -12.9, (-15, -4)); hero('siao', -24, -9.2, (-15, -4)); hero('tarik', -39.3, 22.4, (-41.6, 16.2)); hero('ahma', -43.0, 19.3, (-41.6, 16.2))
if 'overview' in want: shoot(cam, 'overview', (62, 58, 74), (-4, 2, 2), 30)
if 'ground_a' in want: shoot(cam, 'ground_a', (-41, 1.6, 7.6), (-14, 1.5, 7.8), 20)
if 'ground_b' in want: shoot(cam, 'ground_b', (-20.2, 1.6, .9), (0, 3.0, .9), 22)
if 'detail' in want: shoot(cam, 'detail', (9.5, 3.4, 8.5), (-.5, 3.0, .6), 32)
if 'park' in want: shoot(cam, 'park', (-14.6, 7.5, -3.9), (-33, 1, -18), 20)
if 'shops' in want: shoot(cam, 'shops', (-41.6, 1.7, 15.8), (-39.9, 1.9, 24.5), 16)
