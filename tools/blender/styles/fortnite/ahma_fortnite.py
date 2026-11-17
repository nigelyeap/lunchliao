"""Ah Ma, Fortnite-skin style frame. Headless:
  /opt/homebrew/bin/blender -b -P tools/blender/styles/fortnite/ahma_fortnite.py -- [build] [shots] [hero|face|expr|turn]
build saves ahma_fortnite.blend next to this file. shots opens it and renders into shots/styles/fortnite/.
Blender axes: Z up, she faces +Y. Basis shape = neutral smile, shape keys: angry, grin, ult (same names on every face part)."""
import bpy, bmesh, math, os, sys, random
import numpy as np
from math import sin, cos, pi, radians
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'blender', 'heroes'))
from hero_lib import Soup, V, apply_mod, tri_count, decimate, shade_smooth, srgb, override
BLEND = os.path.join(HERE, 'ahma_fortnite.blend')
SHOTS = os.path.join(ROOT, 'shots', 'styles', 'fortnite'); os.makedirs(SHOTS, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build', 'shots']

def sstep(a, b, x):
    t = min(1, max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t
def mixc(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

# ------------------------------------------------------------------ landmarks
EYE_X, EYE_Z, ER = 0.150, 1.585, 0.070      # eyeball
RL = ER + 0.005                             # lid shell radius
MZ = 1.400                                  # mouth line height
ZB = 1.722                                  # brow height
CR_C = Vector((0, 0.04, 1.63)); CR_R = Vector((0.36, 0.36, 0.33))   # cranium
EXPRS = ('smile', 'angry', 'grin', 'ult')
E = dict(
    smile=dict(w=.118, lift=.030, up=0, lo=0, jaw=0, cheek=0, lu=31, ll=34, tilt=0, bi=0, bo=0, tf=.5, tg=0),
    angry=dict(w=.132, lift=-.034, up=.020, lo=.036, jaw=.012, cheek=0, lu=25, ll=26, tilt=17, bi=-.052, bo=.014, tf=1.0, tg=0),
    grin=dict(w=.168, lift=.052, up=.008, lo=.078, jaw=.035, cheek=.6, lu=34, ll=10, tilt=0, bi=.022, bo=.02, tf=.42, tg=.7),
    ult=dict(w=.128, lift=-.012, up=.030, lo=.130, jaw=.085, cheek=.3, lu=52, ll=44, tilt=13, bi=-.046, bo=.032, tf=.26, tg=1),
)
COL = {k: srgb(v) for k, v in dict(
    skin='#EDA272', skin_hi='#F6C096', skin_lo='#D2805C', blush='#EC7F6C', lip='#C8706A', mouth='#35101C', tongue='#E46E7C', teeth='#FFF7EA',
    hair='#F4F1FA', hair_lo='#8D84B8', brow='#4A4658', blouse='#7A3BD0', pipe='#FF4FA0', slacks='#232B52', slipper='#E8261F',
    basket='#E3261E', metal='#C9CED6', rubber='#33353B', grip='#4A4E57', jade='#2FB57A', gold='#F2B63A', sclera='#FFFAF0',
    leek='#3FA83A', leek_w='#F2F4DA', floor='#8C8780', bg='#7F8794').items()}

# ------------------------------------------------------------------ mesh helpers
def root():
    r = bpy.data.objects.get('AhMa_root')
    if not r:
        r = bpy.data.objects.new('AhMa_root', None); bpy.context.scene.collection.objects.link(r)
        h = bpy.data.objects.new('head_ctrl', None); bpy.context.scene.collection.objects.link(h)
        h.location = (0, 0.03, 1.33); h.parent = r
    return r
def adopt(ob, head=False):
    root(); bpy.context.view_layer.update()
    p = bpy.data.objects['head_ctrl'] if head else bpy.data.objects['AhMa_root']
    ob.parent = p; ob.matrix_parent_inverse = p.matrix_world.inverted(); return ob

def mesh_obj(name, verts, faces, mat=None, smooth=True, uvs=None):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    if smooth: shade_smooth(ob)
    if uvs:
        uvl = me.uv_layers.new(name='UVMap')
        for p in me.polygons:
            for li, uv in zip(p.loop_indices, uvs[p.index]): uvl.data[li].uv = uv
    if mat: me.materials.append(mat)
    return ob

def loft(name, rings, seg=32, n_exp=2.0, cap_bot=False, cap_top=False, mat=None, urep=1, vscale=1.0):
    """rings: list of (centre, u, v). Point = c + u*f(cos t) + v*f(sin t). Seam at t=0."""
    verts, faces, uvs = [], [], []; vv = [0.0]
    for i, (c, u, v) in enumerate(rings):
        if i: vv.append(vv[-1] + (Vector(c) - Vector(rings[i - 1][0])).length / vscale)
        for j in range(seg):
            t = 2 * pi * j / seg; ct, st = cos(t), sin(t)
            if n_exp != 2.0:
                ct = math.copysign(abs(ct) ** (2 / n_exp), ct); st = math.copysign(abs(st) ** (2 / n_exp), st)
            verts.append(Vector(c) + Vector(u) * ct + Vector(v) * st)
    for i in range(len(rings) - 1):
        for j in range(seg):
            a = i * seg + j; b = i * seg + (j + 1) % seg
            faces.append((a, b, b + seg, a + seg))
            u0, u1 = urep * j / seg, urep * (j + 1) / seg
            uvs.append(((u0, vv[i]), (u1, vv[i]), (u1, vv[i + 1]), (u0, vv[i + 1])))
    for cap, i in ((cap_bot, 0), (cap_top, len(rings) - 1)):
        if cap:
            verts.append(Vector(rings[i][0])); ci = len(verts) - 1
            for j in range(seg):
                faces.append((ci, i * seg + j, i * seg + (j + 1) % seg)); uvs.append(((0, 0),) * 3)
    return mesh_obj(name, verts, faces, mat, uvs=uvs)

def ring_xy(z, cy, rx, ry, cx=0.0): return (Vector((cx, cy, z)), Vector((0, -ry, 0)), Vector((rx, 0, 0)))

def spline(rows, n):
    """Catmull-Rom through rows (any width), n samples per span."""
    P = np.array(rows, float); P = np.vstack([P[0], P, P[-1]]); out = []
    for i in range(1, len(P) - 2):
        for s in range(n):
            t = s / n; t2, t3 = t * t, t * t * t
            out.append(.5 * ((2 * P[i]) + (-P[i - 1] + P[i + 1]) * t + (2 * P[i - 1] - 5 * P[i] + 4 * P[i + 1] - P[i + 2]) * t2 + (-P[i - 1] + 3 * P[i] - 3 * P[i + 1] + P[i + 2]) * t3))
    out.append(P[-2]); return out

def fillet(pts, rad, n=6):
    pts = [Vector(p) for p in pts]; out = [pts[0]]
    for a, p, b in zip(pts, pts[1:], pts[2:]):
        d1 = (a - p).normalized(); d2 = (b - p).normalized(); th = d1.angle(d2)
        tl = rad / math.tan(th / 2); c = p + (d1 + d2).normalized() * (rad / sin(th / 2))
        s, e = p + d1 * tl - c, p + d2 * tl - c
        for i in range(n + 1): out.append(c + s.slerp(e, i / n) * rad)
    out.append(pts[-1]); return out

def tube(name, pts, radii, seg=12, mat=None, cap=True, squash=1.0, **kw):
    """Round tube along a polyline. radii: scalar or one per point."""
    pts = [Vector(p) for p in pts]
    if isinstance(radii, (int, float)): radii = [radii] * len(pts)
    rings = []; up = None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if up is None:
            up = Vector((0, 0, 1)) if abs(t.z) < .9 else Vector((1, 0, 0))
        u = (up - t * up.dot(t)).normalized(); v = t.cross(u); up = u
        rings.append((p, u * radii[i], v * radii[i] * squash))
    return loft(name, rings, seg, cap_bot=cap, cap_top=cap, mat=mat, **kw)

def paint(ob, fn):
    a = ob.data.color_attributes.get('Col') or ob.data.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    for i, v in enumerate(ob.data.vertices): a.data[i].color = (*fn(v.co), 1.0)

def add_keys(ob, coords_by_expr):
    ob.shape_key_add(name='Basis')
    for e in EXPRS[1:]:
        k = ob.shape_key_add(name=e)
        for i, co in enumerate(coords_by_expr[e]): k.data[i].co = co

def keyed(name, builder, mat, head=True):
    v, f = builder('smile'); ob = mesh_obj(name, v, f, mat)
    add_keys(ob, {e: builder(e)[0] for e in EXPRS[1:]}); return adopt(ob, head)

def bvh_of(coords, ob): return BVHTree.FromPolygons([tuple(c) for c in coords], [tuple(p.vertices) for p in ob.data.polygons])
def ray(bvh, x, z):
    loc, n, _, _ = bvh.ray_cast(Vector((x, 1.5, z)), Vector((0, -1, 0)))
    if loc is None: return Vector((x, 0.3, z)), Vector((0, 1, 0))
    return loc, n

# ------------------------------------------------------------------ materials
def mat(name, col, rough=.5, metal=0.0, sss=0.0, coat=0.0, vcol=False, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss; b.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.2); b.inputs['Subsurface Scale'].default_value = 0.03
    if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.04
    if emit: b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = emit
    if vcol:
        a = nt.nodes.new('ShaderNodeVertexColor'); a.layer_name = 'Col'; nt.links.new(a.outputs['Color'], b.inputs['Base Color'])
    return m

def worn(m, light, amount=.35, scale=9.0):
    """A little hand-painted wear for props: soft noisy lighter scuffs."""
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = 3
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = .58; r.color_ramp.elements[1].position = .72
    mx = nt.nodes.new('ShaderNodeMixRGB'); mx.inputs['Color1'].default_value = b.inputs['Base Color'].default_value; mx.inputs['Color2'].default_value = (*light, 1)
    sc = nt.nodes.new('ShaderNodeMath'); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = amount
    nt.links.new(tc.outputs['Object'], n.inputs['Vector']); nt.links.new(n.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], sc.inputs[0])
    nt.links.new(sc.outputs[0], mx.inputs['Fac']); nt.links.new(mx.outputs['Color'], b.inputs['Base Color']); return m

def eye_mat():
    m = mat('eye', COL['sclera'], rough=.18, coat=1.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nm = nt.nodes.new('ShaderNodeVectorMath'); nm.operation = 'NORMALIZE'
    sp = nt.nodes.new('ShaderNodeSeparateXYZ'); r = nt.nodes.new('ShaderNodeValToRGB'); cr = r.color_ramp
    stops = [(0.0, COL['sclera']), (cos(radians(40)), COL['sclera']), (cos(radians(38.5)), srgb('#2A150E')), (cos(radians(33)), srgb('#6B3A1E')),
             (cos(radians(20)), srgb('#8A5228')), (cos(radians(18.5)), srgb('#0A0606')), (1.0, srgb('#0A0606'))]
    cr.elements[0].position = stops[0][0]; cr.elements[0].color = (*stops[0][1], 1); cr.elements[1].position = stops[1][0]; cr.elements[1].color = (*stops[1][1], 1)
    for p, c in stops[2:]:
        el = cr.elements.new(p); el.color = (*c, 1)
    nt.links.new(tc.outputs['Object'], nm.inputs[0]); nt.links.new(nm.outputs['Vector'], sp.inputs[0]); nt.links.new(sp.outputs['Y'], r.inputs['Fac'])
    nt.links.new(r.outputs['Color'], b.inputs['Base Color']); return m

def lens_mat():
    m = bpy.data.materials.new('lens'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); mx = nt.nodes.new('ShaderNodeMixShader'); t = nt.nodes.new('ShaderNodeBsdfTransparent'); g = nt.nodes.new('ShaderNodeBsdfGlossy')
    g.inputs['Roughness'].default_value = .03; g.inputs['Color'].default_value = (.8, .9, 1, 1); mx.inputs[0].default_value = .018
    nt.links.new(t.outputs[0], mx.inputs[1]); nt.links.new(g.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs['Surface'])
    m.surface_render_method = 'BLENDED'; return m

def floral_image():
    """Tileable samfu print: big cream and pink flowers on violet."""
    N = 1024; yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / N
    def s2l(h): return np.array(srgb(h), np.float32)
    img = np.empty((N, N, 3), np.float32); img[:] = s2l('#5A1FB8')
    def blob(cx, cy, r, soft=.004):
        dx = np.abs(xx - cx); dx = np.minimum(dx, 1 - dx); dy = np.abs(yy - cy); dy = np.minimum(dy, 1 - dy)
        return np.clip((r - np.sqrt(dx * dx + dy * dy)) / soft, 0, 1)
    def put(mask, col): img[:] = img * (1 - mask[..., None]) + s2l(col) * mask[..., None]
    rnd = random.Random(7)
    flowers = [(.18, .2, .105, '#FFF1D6'), (.68, .12, .085, '#FF7DB4'), (.45, .5, .11, '#FF7DB4'), (.88, .58, .1, '#FFF1D6'), (.16, .74, .09, '#FF7DB4'), (.62, .86, .1, '#FFF1D6')]
    for cx, cy, r, col in flowers:                       # leaves first, under the petals
        a0 = rnd.random() * 6.28
        for k in range(3):
            a = a0 + k * 2.1
            for t in (1.25, 1.55, 1.8): put(blob(cx + cos(a) * r * t, cy + sin(a) * r * t, r * (.36 - .1 * (t - 1.25) * 3)), '#22C7A0')
    for cx, cy, r, col in flowers:
        a0 = rnd.random() * 6.28
        for k in range(5):
            a = a0 + k * 2 * pi / 5; put(blob(cx + cos(a) * r * .55, cy + sin(a) * r * .55, r * .46), col)
        put(blob(cx, cy, r * .3), '#FFC83A')
    for _ in range(26): put(blob(rnd.random(), rnd.random(), .012), '#8B52E6')
    im = bpy.data.images.new('floral', N, N, alpha=False)
    buf = np.ones((N, N, 4), np.float32); buf[..., :3] = np.where(img <= .0031308, img * 12.92, 1.055 * np.power(np.maximum(img, 1e-6), 1 / 2.4) - .055)
    im.pixels.foreach_set(buf.ravel()); im.filepath_raw = os.path.join(HERE, 'floral.png'); im.file_format = 'PNG'; im.save(); im.pack(); return im

def blouse_mat():
    m = mat('blouse', COL['blouse'], rough=.62); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = floral_image(); nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Sheen Weight'].default_value = .08; return m

M = {}
def make_materials():
    M.update(
        skin=mat('skin', COL['skin'], rough=.46, sss=.18, vcol=True), lip=mat('lip', COL['lip'], rough=.38, sss=.1),
        mouth=mat('mouth', COL['mouth'], rough=.7), tongue=mat('tongue', COL['tongue'], rough=.35, sss=.1), teeth=mat('teeth', COL['teeth'], rough=.25, emit=.3),
        hair=mat('hair', COL['hair'], rough=.45, vcol=True), brow=mat('brow', COL['brow'], rough=.55),
        blouse=blouse_mat(), pipe=mat('pipe', COL['pipe'], rough=.5), slacks=mat('slacks', COL['slacks'], rough=.7),
        slipper=worn(mat('slipper', COL['slipper'], rough=.5), srgb('#FF8A70'), .3, 14), basket=worn(mat('basket', COL['basket'], rough=.38), srgb('#FF9C86'), .2, 17),
        metal=worn(mat('metal', COL['metal'], rough=.28, metal=1.0), srgb('#FFFFFF'), .25, 5), rubber=mat('rubber', COL['rubber'], rough=.75), grip=mat('grip', COL['grip'], rough=.85),
        jade=mat('jade', COL['jade'], rough=.15, sss=.4, coat=.6), gold=mat('gold', COL['gold'], rough=.22, metal=1.0),
        eye=eye_mat(), lens=lens_mat(), glint=mat('glint', (1, 1, 1), emit=6.0), leek=mat('leek', COL['leek'], rough=.5, vcol=True))

# ------------------------------------------------------------------ head
def skin_paint(co):
    c = mixc(COL['skin_lo'], COL['skin'], sstep(1.20, 1.40, co.z)); c = mixc(c, COL['skin_hi'], .7 * sstep(1.6, 1.85, co.z) * sstep(.1, .35, co.y))
    for k in (-1, 1):
        c = mixc(c, COL['blush'], .55 * math.exp(-((co - Vector((k * .215, .30, 1.475))).length / .085) ** 2))
        c = mixc(c, COL['blush'], .45 * math.exp(-((co - Vector((k * .39, 0, 1.56))).length / .08) ** 2))
    return mixc(c, COL['blush'], .4 * math.exp(-((co - Vector((0, .44, 1.50))).length / .05) ** 2))

def build_head():
    s = Soup('head')
    s.ellipsoid(CR_C, CR_R)
    s.ellipsoid((0, 0.07, 1.47), (0.345, 0.31, 0.21))                 # jowly lower face
    s.ellipsoid((0, 0.13, 1.335), (0.23, 0.22, 0.09))                 # soft double chin
    s.sphere((0, 0.295, 1.325), 0.072)                                # chin
    for k in (-1, 1):
        s.sphere((k * 0.20, 0.235, 1.47), 0.11)                       # apple cheeks
        s.ellipsoid((k * 0.365, 0.0, 1.565), (0.04, 0.07, 0.10))      # ears
        s.sphere((k * 0.034, 0.385, 1.495), 0.025)
    s.capsule((0, 0.34, 1.60), (0, 0.40, 1.515), 0.03, 0.042)         # nose
    s.sphere((0, 0.412, 1.505), 0.041)
    s.capsule((0, 0.02, 1.18), (0, 0.04, 1.42), 0.135)                # neck
    head, _ = s.remesh(voxel=0.008, smooth=10, smooth_factor=0.6, target_tris=6400)
    paint(head, skin_paint); head.data.materials.append(M['skin'])
    rest = [v.co.copy() for v in head.data.vertices]
    add_keys(head, {e: [head_deform(p, e) for p in rest] for e in EXPRS[1:]})
    BV = {e: bvh_of([head_deform(p, e, False) for p in rest], head) for e in EXPRS}   # jaw and cheeks, no mouth dent
    adopt(head, True); return head, BV

def lip_curves(e):
    P = E[e]
    b = lambda u: MZ + P['lift'] * u * u
    return (lambda u: b(u) + P['up'] * (1 - u * u) ** .7), (lambda u: b(u) - P['lo'] * (1 - u * u) ** .6)

def head_deform(p, e, dent=True):
    P = E[e]; q = p.copy()
    if p.y < 0.0 or not (P['jaw'] or P['cheek'] or P['lo']): return q
    front = sstep(0.0, 0.16, p.y)
    q.z -= P['jaw'] * sstep(MZ + .03, MZ - .05, p.z) * front * sstep(1.2, 1.28, p.z)
    for k in (-1, 1):
        g = math.exp(-((p - Vector((k * .21, .29, 1.48))).length / .09) ** 2) * P['cheek']
        q.z += .028 * g; q.y += .012 * g
    u = q.x / P['w']
    if dent and abs(u) < 1 and p.y > .15:
        zu, zl = lip_curves(e); d = min(zu(u) - q.z, q.z - zl(u)); op = zu(u) - zl(u)
        if d > 0: q.y -= .048 * sstep(0, .014, d) * min(1, op / .03)
    return q

def lip_builder(BV, upper):
    def build(e):
        P = E[e]; zu, zl = lip_curves(e); NU, MS = 25, 8; r0 = .0085 if upper else .0115
        thin = 1 - .25 * min(1, (P['up'] + P['lo']) / .1)
        cs = []
        for i in range(NU):
            u = -1 + 2 * i / (NU - 1); r = (r0 * (1 - u * u) ** .5) * thin + .0015
            z = zu(u) + r * .8 if upper else zl(u) - r * .8
            hit, n = ray(BV[e], P['w'] * u, z); cs.append((hit + n * (.2 * r), n, r))
        verts, faces = [], []
        for i, (c, n, r) in enumerate(cs):
            t = (cs[min(i + 1, NU - 1)][0] - cs[max(i - 1, 0)][0]).normalized(); sd = n.cross(t).normalized()
            for j in range(MS):
                a = 2 * pi * j / MS; verts.append(c + sd * (r * cos(a)) + n * (.75 * r * sin(a)))
        for i in range(NU - 1):
            for j in range(MS):
                a = i * MS + j; b = i * MS + (j + 1) % MS; faces.append((a, b, b + MS, a + MS))
        return verts, faces
    return build

def bag_builder(BV, kind):
    """kind: bag (dark cavity), teeth (upper row), tongue. All smooth, independent of the head tessellation."""
    def build(e):
        P = E[e]; zu, zl = lip_curves(e); NU = 25; verts, faces = [], []
        rows = {'bag': 9, 'teeth': 5, 'tongue': 7}[kind]
        def cav(u, t):   # point on the cavity floor
            op = max(0, zu(u) - zl(u)); hit, n = ray(BV[e], P['w'] * u, lerp(zu(u), zl(u), t))
            return hit + n * .003 + Vector((0, -.024 * sstep(0, .03, min(t, 1 - t) * op) * min(1, op / .03), 0)), op
        for i in range(NU):
            u = -1 + 2 * i / (NU - 1)
            for j in range(rows):
                t = j / (rows - 1)
                if kind == 'bag': verts.append(cav(u, t)[0])
                elif kind == 'teeth':
                    uu = u * .9; opu = max(0, zu(uu) - zl(uu)); h = P['tf'] * opu
                    tt = min(t, .75) / .75; z = zu(uu) + .004 - (h + .004) * tt
                    hit, n = ray(BV['smile'], P['w'] * uu, z); back = .016 if j == rows - 1 else 0
                    verts.append(hit + Vector((0, .004 - back - .03 * (1 - min(1, opu / .012)), 0)))
                else:
                    uu = u * .55; c, opu = cav(uu, lerp(.46, .93, t))
                    bump = (sin(pi * t) ** .5) * (1 - u * u) ** .5
                    verts.append(c + Vector((0, (.004 + .015 * bump) * P['tg'] - .01 * (1 - P['tg']), 0)))
        for i in range(NU - 1):
            for j in range(rows - 1):
                a = i * rows + j; faces.append((a, a + 1, a + rows + 1, a + rows))
        return verts, faces
    return build

def lid_builder(k, upper):
    Ek = Vector((k * EYE_X, EYE_Y, EYE_Z))
    def build(e):
        P = E[e]; NI, NJ = 19, 7; phm = radians(80); verts, faces = [], []
        for i in range(NI):
            ph = -phm + 2 * phm * i / (NI - 1); c = max(0, cos(ph / phm * pi / 2)) ** .6; inner = -k * sin(ph)
            edge = (P['lu'] - P['tilt'] * inner) * c if upper else -P['ll'] * c
            end = 172 if upper else -172
            rows = [(edge, ER - .004)] + [(edge + (end - edge) * j / (NJ - 1), RL) for j in range(NJ)]
            for th, rad in rows:
                t = radians(th); verts.append(Ek + Vector((rad * sin(ph), rad * cos(ph) * cos(t), rad * cos(ph) * sin(t))))
        R = NJ + 1
        for i in range(NI - 1):
            for j in range(R - 1):
                a = i * R + j; faces.append((a, a + 1, a + R + 1, a + R))
        return verts, faces
    return build

def brow_builder(BV, k):
    def build(e):
        P = E[e]; NS, MS = 13, 8; cs = []
        for i in range(NS):
            s = i / (NS - 1); x = k * (.060 + .198 * s)
            z = ZB + .024 * sin(pi * s ** .8) - .028 * s * s + P['bi'] * (1 - s) ** 1.5 + P['bo'] * s ** 1.5
            hit, _ = ray(BV['smile'], x, z); n = Vector((hit.x, hit.y - .04, 0)).normalized(); cs.append((hit + n * .004, n, s))
        verts, faces = [], []
        for i, (c, n, s) in enumerate(cs):
            t = (cs[min(i + 1, NS - 1)][0] - cs[max(i - 1, 0)][0]).normalized(); sd = n.cross(t).normalized()
            capf = min(1, 1.15 * sin(pi * (.02 + .96 * s)) ** .4); a_, b_ = .029 * (1 - .45 * s) * capf, .014 * capf
            for j in range(MS):
                a = 2 * pi * j / MS; verts.append(c + sd * (a_ * cos(a)) + n * (b_ * sin(a)))
        for i in range(NS - 1):
            for j in range(MS):
                a = i * MS + j; b = i * MS + (j + 1) % MS; faces.append((a, b, b + MS, a + MS))
        return verts, faces
    return build

def build_face(BV):
    global EYE_Y
    hit, _ = ray(BV['smile'], EYE_X, EYE_Z); EYE_Y = hit.y - 0.040
    keyed('lip_up', lip_builder(BV, True), M['lip']); keyed('lip_lo', lip_builder(BV, False), M['lip'])
    keyed('mouth_bag', bag_builder(BV, 'bag'), M['mouth']); keyed('teeth', bag_builder(BV, 'teeth'), M['teeth']); keyed('tongue', bag_builder(BV, 'tongue'), M['tongue'])
    for k in (-1, 1):
        Ek = Vector((k * EYE_X, EYE_Y, EYE_Z))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=ER, location=Ek)
        eb = bpy.context.object; eb.name = 'eye_%d' % k; eb.rotation_euler = (0, 0, radians(k * 2)); shade_smooth(eb); eb.data.materials.append(M['eye']); adopt(eb, True)
        gl = bpy.data.objects.new('glint_%d' % k, None)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=.011, location=Ek + Vector((.26, .93, .25)).normalized() * (ER + .0005))
        g = bpy.context.object; g.name = 'glint_%d' % k; g.scale = (1, .25, 1); shade_smooth(g); g.data.materials.append(M['glint']); adopt(g, True)
        for up in (True, False):
            lid = keyed('lid_%s_%d' % ('up' if up else 'lo', k), lid_builder(k, up), M['skin'])
            paint(lid, lambda co: mixc(COL['skin'], COL['blush'], .12))
        keyed('brow_%d' % k, brow_builder(BV, k), M['brow'])
    # glasses
    yg = EYE_Y + ER + .034
    for k in (-1, 1):
        bpy.ops.mesh.primitive_torus_add(major_segments=36, minor_segments=6, major_radius=.106, minor_radius=.0085, location=(k * EYE_X, yg, EYE_Z))
        t = bpy.context.object; t.name = 'rim_%d' % k; t.rotation_euler = (radians(90), 0, radians(-k * 9)); shade_smooth(t); t.data.materials.append(M['gold']); adopt(t, True)
        bpy.ops.mesh.primitive_circle_add(vertices=40, radius=.104, fill_type='NGON', location=(k * EYE_X, yg, EYE_Z))
        l = bpy.context.object; l.name = 'lens_%d' % k; l.rotation_euler = t.rotation_euler; l.data.materials.append(M['lens']); l.visible_shadow = False; adopt(l, True)
        pts = spline([(k * .253, yg - .02, EYE_Z + .012), (k * .335, .25, EYE_Z + .03), (k * .392, .04, EYE_Z + .045), (k * .385, -.03, EYE_Z + .01)], 6)
        adopt(tube('temple_%d' % k, pts, .0065, 8, M['gold']), True)
    pts = spline([(-.046, yg + .004, EYE_Z + .012), (0, yg + .012, EYE_Z + .034), (.046, yg + .004, EYE_Z + .012)], 6)
    adopt(tube('bridge', pts, .0075, 8, M['gold']), True)
    for k in (-1, 1):   # gold studs
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=.019, location=(k * .392, .012, 1.485))
        g = bpy.context.object; g.name = 'stud_%d' % k; shade_smooth(g); g.data.materials.append(M['gold']); adopt(g, True)

def build_hair():
    rnd = random.Random(3); s = Soup('hair'); N = 170
    for i in range(N):
        z = 1 - 2 * (i + .5) / N; r = math.sqrt(1 - z * z); a = i * 2.39996
        d = Vector((r * cos(a), r * sin(a), z)); hz = math.hypot(d.x, d.y) + 1e-6
        fr = d.y / hz                                                   # +1 front, -1 back
        line = .06 + .52 * fr if fr > 0 else .06 + .5 * fr              # hairline: high at the forehead, low at the nape
        if d.z < line: continue
        edge = sstep(line, line + .35, d.z)
        rad = lerp(.078, .112, rnd.random()) * lerp(.85, 1.0, edge)
        c = CR_C + Vector((d.x * CR_R.x, d.y * CR_R.y, d.z * CR_R.z * 1.08)) + d * (.02 + .03 * edge)
        s.sphere(c, rad, seg=16)
    s.ellipsoid(CR_C + Vector((0, -.06, .05)), (.372, .33, .33))   # scalp fill, sits behind the hairline
    hair, _ = s.remesh(voxel=0.010, smooth=4, smooth_factor=0.5, target_tris=5000)
    def hp(co):
        d = ((co.x - CR_C.x) / CR_R.x) ** 2 + ((co.y - CR_C.y) / CR_R.y) ** 2 + ((co.z - CR_C.z) / (CR_R.z * 1.08)) ** 2
        return mixc(COL['hair_lo'], COL['hair'], sstep(1.12, 1.62, d))
    paint(hair, hp); hair.data.materials.append(M['hair']); adopt(hair, True); return hair

# ------------------------------------------------------------------ body
ELB = lambda k: Vector((k * .52, .20, 1.10)); WR = lambda k: Vector((k * .425, .535, 1.05))
HX, HZ = .40, .98      # walker grip axis

def build_body():
    rows = spline([(.47, .0, .455, .40), (.50, .0, .45, .40), (.62, .02, .462, .425), (.80, .035, .465, .435), (.98, .02, .435, .39),
                   (1.12, .0, .405, .335), (1.22, -.012, .36, .275), (1.285, .0, .25, .20), (1.325, .02, .16, .15)], 3)
    rings = [ring_xy(z, cy, rx, ry) for z, cy, rx, ry in rows]
    rings = [ring_xy(.56, .0, .40, .35), ring_xy(.47, .0, .435, .385)] + rings          # rolled hem, turns up inside
    blouse = adopt(loft('blouse', rings, 48, n_exp=2.25, mat=M['blouse'], urep=5, vscale=.56))
    adopt(loft('hem', [ring_xy(.468, .0, .452 + a, .398 + a) for a in (0,)] , 48, 2.25))
    bpy.data.objects.remove(bpy.data.objects['hem'])
    hem_pts = [Vector((0, 0, .47)) + Vector((.455 * math.copysign(abs(sin(t)) ** (2 / 2.25), sin(t)), -.402 * math.copysign(abs(cos(t)) ** (2 / 2.25), cos(t)), 0)) for t in [2 * pi * j / 48 for j in range(48)]]
    adopt(ring_tube('hem_pipe', hem_pts, .013, M['pipe'], seg=6))
    # collar
    col = [(Vector((0, .028, 1.315)), Vector((0, -.150, 0)), Vector((.156, 0, 0))), (Vector((0, .036, 1.385)), Vector((0, -.140, .012)), Vector((.146, 0, 0))),
           (Vector((0, .036, 1.385)), Vector((0, -.128, .012)), Vector((.134, 0, 0))), (Vector((0, .03, 1.32)), Vector((0, -.13, 0)), Vector((.136, 0, 0)))]
    adopt(loft('collar', col, 40, mat=M['blouse'], urep=2, vscale=.56))
    cp = [Vector((0, .036, 1.387)) + Vector((.140 * sin(t), -.134 * cos(t), -.012 * cos(t))) for t in [2 * pi * j / 40 for j in range(40)]]
    adopt(ring_tube('collar_pipe', cp, .009, M['pipe'], seg=6))
    # sleeves, arms, hands
    for k in (-1, 1):
        S = Vector((k * .31, -.005, 1.215)); el = ELB(k); wr = WR(k); end = el.lerp(wr, .34)
        rows = spline([(*S, .15), (*(S.lerp(el, .5) + Vector((k * .02, 0, .012))), .15), (*(el + Vector((k * .005, 0, .005))), .118), (*end, .090)], 5)
        pts = [Vector(r[:3]) for r in rows]; rad = [r[3] for r in rows]
        pts += [pts[-1] + (pts[-2] - pts[-1]).normalized() * .05]; rad += [rad[-1] - .018]     # rolled cuff
        adopt(tube('sleeve_%d' % k, pts, rad, 24, M['blouse'], cap=False, urep=2, vscale=.56))
        cdir = (pts[-2] - pts[-3]).normalized(); u = cdir.orthogonal().normalized(); v = cdir.cross(u)
        adopt(ring_tube('cuff_pipe_%d' % k, [pts[-2] + (u * cos(t) + v * sin(t)) * (rad[-2] + .001) for t in [2 * pi * j / 24 for j in range(24)]], .014, M['pipe'], seg=6))
        s = Soup('arm_%d' % k)
        s.capsule((k * .35, 0, 1.2), el, .08, .072); s.capsule(el, wr, .07, .052)
        s.capsule(wr, (k * HX, .585, HZ + .05), .052, .05)
        s.ellipsoid((k * HX, .625, HZ + .043), (.064, .088, .036))
        rho = .0535
        for i, y in enumerate((.552, .599, .647, .694)):
            fr = .0245 if i else .0215
            p = [Vector((k * (HX + rho * cos(radians(a))), y, HZ + rho * sin(radians(a)))) for a in (70, 20, -35, -90, -140)]
            for a, b in zip(p, p[1:]): s.capsule(a, b, fr, fr * .95, seg=12)
        p = [Vector((k * (HX + rho * cos(radians(a))), .70 + .012 * j, HZ + rho * sin(radians(a)) + .004)) for j, a in enumerate((112, 160, 208))]
        for a, b in zip(p, p[1:]): s.capsule(a, b, .027, .025, seg=12)
        arm, _ = s.remesh(voxel=0.0055, smooth=3, smooth_factor=.5, target_tris=1800)
        paint(arm, lambda co: mixc(COL['skin'], COL['blush'], .22 * sstep(1.06, .93, co.z))); arm.data.materials.append(M['skin']); adopt(arm)
    # jade bangle on her left wrist
    k = -1; d = (WR(k) - ELB(k)).normalized(); c = ELB(k).lerp(WR(k), .8); u = d.orthogonal().normalized(); v = d.cross(u)
    adopt(ring_tube('bangle', [c + (u * cos(t) + v * sin(t)) * .072 for t in [2 * pi * j / 28 for j in range(28)]], .0175, M['jade'], seg=8))
    # slacks
    s = Soup('pelvis'); s.ellipsoid((0, .01, .56), (.40, .35, .17)); pel, _ = s.remesh(voxel=.02, smooth=3, target_tris=300); pel.data.materials.append(M['slacks']); adopt(pel)
    for k in (-1, 1):
        pts = [(k * .19, .0, .58), (k * .195, .0, .40), (k * .20, .0, .20), (k * .20, .0, .135), (k * .20, .0, .17)]
        adopt(tube('leg_%d' % k, pts, [.2, .2, .172, .165, .13], 24, M['slacks'], cap=False))
        build_foot(k)
    # placket piping and frog buttons, raycast on the blouse front
    bv = BVHTree.FromPolygons([tuple(v.co) for v in blouse.data.vertices], [tuple(p.vertices) for p in blouse.data.polygons])
    pp = []
    for i in range(30):
        z = lerp(1.305, .475, i / 29); hit, n = ray(bv, 0, z); pp.append(hit + n * .004)
    adopt(tube('placket', pp, .008, 6, M['pipe']))
    for z in (1.24, 1.10, .95, .80, .65):
        hit, n = ray(bv, 0, z); c = hit + n * .012
        s = Soup('frog'); s.sphere(c, .021, seg=8)
        for sgn in (-1, 1): s.capsule(c + Vector((sgn * .02, 0, 0)), c + Vector((sgn * .062, -.004, 0)), .011, .009, seg=8); s.sphere(c + Vector((sgn * .066, -.004, 0)), .015, seg=8)
        f = s.to_object(); shade_smooth(f); f.data.materials.append(M['gold']); adopt(f)

def ring_tube(name, pts, r, material, seg=8):
    """Closed tube around a loop of points."""
    n = len(pts); verts, faces = [], []
    cen = sum(pts, Vector()) / n
    for i, p in enumerate(pts):
        t = (pts[(i + 1) % n] - pts[i - 1]).normalized(); out = (p - cen); out = (out - t * out.dot(t)).normalized(); up = t.cross(out)
        for j in range(seg):
            a = 2 * pi * j / seg; verts.append(p + out * (r * cos(a)) + up * (r * sin(a)))
    for i in range(n):
        for j in range(seg):
            a = i * seg + j; b = i * seg + (j + 1) % seg; i2 = ((i + 1) % n) * seg
            faces.append((a, b, i2 + (j + 1) % seg, i2 + j))
    return mesh_obj(name, verts, faces, material)

def build_foot(k):
    x = k * .20; parts = []
    s = Soup('foot_%d' % k)
    s.capsule((x, -.01, .24), (x, .0, .085), .075, .068)
    s.ellipsoid((x, .085, .078), (.088, .165, .046)); s.ellipsoid((x, .02, .085), (.075, .1, .05))
    for i, (dx, dy, r) in enumerate(((-.052, .225, .034), (-.008, .238, .028), (.028, .232, .026), (.058, .215, .024), (.082, .19, .022))):
        s.sphere((x + k * dx, dy, .058 - i * .002), r, seg=12)
    foot, _ = s.remesh(voxel=.007, smooth=3, smooth_factor=.5, target_tris=800)
    paint(foot, lambda co: mixc(COL['skin'], COL['blush'], .25 * sstep(.12, .25, co.y))); foot.data.materials.append(M['skin']); parts.append(foot)
    c = Vector((x, .085, 0)); sole = [(c + Vector((0, 0, z)), Vector((0, -.215 * f, 0)), Vector((.118 * f, 0, 0))) for z, f in ((0, .9), (.008, 1), (.03, 1), (.038, .93))]
    parts.append(loft('sole_%d' % k, sole, 32, n_exp=2.7, cap_bot=True, cap_top=True, mat=M['slipper']))
    post = Vector((x - k * .03, .215, .035))
    for sgn in (-1, 1):
        endp = Vector((x + sgn * .108, .03, .03)); mid = Vector((x + sgn * .07 - k * .01, .135, .128))
        pts = spline([tuple(post), tuple(post.lerp(mid, .5) + Vector((0, 0, .035))), tuple(mid), tuple(mid.lerp(endp, .55) + Vector((sgn * .028, 0, .02))), tuple(endp)], 5)
        parts.append(tube('strap_%d_%d' % (k, sgn), pts, .015, 10, M['slipper']))
    Mx = Matrix.Translation((x, 0, 0)) @ Matrix.Rotation(radians(-k * 9), 4, 'Z') @ Matrix.Translation((-x, 0, 0))
    for p in parts: p.data.transform(Mx); adopt(p)

# ------------------------------------------------------------------ walker
def build_walker():
    T = .018; X = HX
    def fy(z): return .93 + .09 * (1 - z / HZ)      # front leg y at height z
    def ry(z): return .50 - .05 * (1 - z / HZ)      # rear leg
    for k in (-1, 1):
        pts = fillet([(k * X, ry(.05), .05), (k * X, .50, HZ), (k * X, .93, HZ), (k * X, fy(.1), .1)], .07, 8)
        adopt(tube('frame_%d' % k, pts, T, 12, M['metal']))
        adopt(tube('brace_%d' % k, [(k * X, ry(.42), .42), (k * X, fy(.42), .42)], T * .85, 10, M['metal']))
        adopt(tube('grip_%d' % k, [(k * X, .515, HZ), (k * X, .53, HZ), (k * X, .735, HZ), (k * X, .75, HZ)], [.024, .031, .031, .024], 16, M['grip']))
        adopt(tube('tip_%d' % k, [(k * X, ry(0), 0), (k * X, ry(.01), .012), (k * X, ry(.09), .09), (k * X, ry(.1), .1)], [.027, .031, .027, .022], 14, M['rubber']))
        wy = fy(.07) + .01
        adopt(tube('wheel_%d' % k, [(k * X - .024, wy, .07), (k * X - .018, wy, .07), (k * X + .018, wy, .07), (k * X + .024, wy, .07)], [.058, .07, .07, .058], 24, M['rubber']))
        adopt(tube('hub_%d' % k, [(k * X - .028, wy, .07), (k * X + .028, wy, .07)], .03, 14, M['metal']))
    for z in (.80, .46):
        adopt(tube('cross_%.2f' % z, [(-X, fy(z), z), (X, fy(z), z)], T * .9, 10, M['metal']))
    # basket hung on the front
    cy = fy(.8) + .165
    rows = [(.50, .245, .118), (.52, .262, .132), (.66, .28, .142), (.82, .30, .155)]
    outer = [(Vector((0, cy, z)), Vector((0, -ry_, 0)), Vector((rx, 0, 0))) for z, rx, ry_ in rows]
    inner = [(Vector((0, cy, z)), Vector((0, -(ry_ - .014), 0)), Vector((rx - .014, 0, 0))) for z, rx, ry_ in reversed([(z + (.014 if i == 0 else 0), a, b) for i, (z, a, b) in enumerate(rows[1:])])]
    adopt(loft('basket', outer + inner, 40, n_exp=4.5, cap_bot=True, cap_top=True, mat=M['basket']))
    def sup(z, rx, ry_, n=4.5): return [Vector((rx * math.copysign(abs(sin(t)) ** (2 / n), sin(t)), cy - ry_ * math.copysign(abs(cos(t)) ** (2 / n), cos(t)), z)) for t in [2 * pi * j / 40 for j in range(40)]]
    adopt(ring_tube('basket_rim', sup(.822, .30, .155), .016, M['basket'], seg=6))
    for z in (.60, .71): adopt(ring_tube('basket_rib_%.2f' % z, sup(z, lerp(.262, .30, (z - .52) / .3) + .002, lerp(.132, .155, (z - .52) / .3) + .002), .009, M['basket'], seg=6))
    for sx in (-.17, .17):
        adopt(tube('hook_%.2f' % sx, fillet([(sx, cy - .16, .74), (sx, cy - .16, .835), (sx, fy(.8) - .03, .835), (sx, fy(.8) - .03, .78)], .022, 5), .009, 8, M['metal']))
    # leeks poking out
    for i, (x0, lean) in enumerate(((.12, .10), (.17, .16), (.07, .03))):
        base = Vector((x0, cy + .02 * i - .02, .56)); top = base + Vector((lean, .02, .50 + .03 * i))
        lk = tube('leek_%d' % i, [base, base.lerp(top, .5), base.lerp(top, .8), top], [.03, .026, .03, .012], 12, M['leek'])
        paint(lk, lambda co: mixc(COL['leek_w'], COL['leek'], sstep(.78, .92, co.z))); adopt(lk)

# ------------------------------------------------------------------ scene, lights, shots
def look_at(o, t):
    o.rotation_euler = (Vector(t) - o.location).to_track_quat('-Z', 'Y').to_euler()

def setup_scene():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 64
    for a, v in (('use_shadows', True), ('use_raytracing', True)):
        if hasattr(sc.eevee, a): setattr(sc.eevee, a, v)
    sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    sc.render.image_settings.file_format = 'PNG'; sc.render.film_transparent = False
    w = bpy.data.worlds.new('World'); sc.world = w; w.use_nodes = True; nt = w.node_tree
    bg = nt.nodes['Background']; bg.inputs[0].default_value = (0.5, 0.62, 0.82, 1); bg.inputs[1].default_value = 0.45        # cool sky fill
    cam = nt.nodes.new('ShaderNodeBackground'); cam.inputs[0].default_value = (*COL['bg'], 1); cam.inputs[1].default_value = 1.0
    lp = nt.nodes.new('ShaderNodeLightPath'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Camera Ray'], mx.inputs[0]); nt.links.new(bg.outputs[0], mx.inputs[1]); nt.links.new(cam.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes['World Output'].inputs['Surface'])
    tgt = (0, .2, 1.15)
    def lamp(name, kind, loc, energy, col, size=2.0, spot=1.0):
        d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = col
        if kind == 'AREA': d.size = size
        if kind == 'SPOT': d.spot_size = spot; d.spot_blend = .7; d.shadow_soft_size = .3
        o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.location = loc; look_at(o, tgt); return o
    lamp('key', 'AREA', (3.4, 3.4, 5.4), 2600, (1.0, 0.80, 0.56), size=2.2)             # golden hour, front-left, 45 up
    lamp('fill', 'AREA', (-4.2, 3.0, 2.4), 420, (0.62, 0.78, 1.0), size=5)               # cool sky fill
    lamp('rim_warm', 'SPOT', (-1.8, -4.4, 3.8), 6000, (1.0, 0.72, 0.45), spot=1.0)       # warm rim, back-right
    lamp('rim_cool', 'SPOT', (-4.8, -1.7, 1.5), 9000, (0.42, 0.72, 1.0), spot=1.0)        # style: strong cool rim, back-left
    # soft neutral floor that fades into the backdrop colour
    bpy.ops.mesh.primitive_plane_add(size=80); fl = bpy.context.object; fl.name = 'floor'
    m = mat('floor', COL['floor'], rough=.85); nt = m.node_tree; b = nt.nodes['Principled BSDF']; out = nt.nodes['Material Output']
    geo = nt.nodes.new('ShaderNodeNewGeometry'); ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 3.5; mr.inputs['From Max'].default_value = 13; mr.interpolation_type = 'SMOOTHSTEP'
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = (*COL['bg'], 1); ms = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(geo.outputs['Position'], ln.inputs[0]); nt.links.new(ln.outputs['Value'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], ms.inputs[0])
    nt.links.new(b.outputs[0], ms.inputs[1]); nt.links.new(em.outputs[0], ms.inputs[2]); nt.links.new(ms.outputs[0], out.inputs['Surface'])
    fl.data.materials.append(m)
    cd = bpy.data.cameras.new('cam'); c = bpy.data.objects.new('cam', cd); sc.collection.objects.link(c); sc.camera = c

def set_expr(e):
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks[1:]: kb.value = 1.0 if kb.name == e else 0.0

def shoot(path, w, h, target, az, dist, lens, cz=None):
    sc = bpy.context.scene; sc.render.resolution_x = w; sc.render.resolution_y = h; c = sc.camera
    c.data.lens = lens; t = Vector(target)
    c.location = (t.x - dist * sin(radians(az)), t.y + dist * cos(radians(az)), cz if cz is not None else t.z); look_at(c, t)
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)

def stitch(paths, out, widths):
    ims = []
    for p in paths:
        im = bpy.data.images.load(p); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); ims.append(a.reshape(h, w, 4)); bpy.data.images.remove(im)
    buf = np.concatenate([a[:, :w] for a, w in zip(ims, widths)], axis=1); h, w = buf.shape[:2]
    o = bpy.data.images.new('stitch', w, h); o.pixels.foreach_set(buf.ravel()); o.filepath_raw = out; o.file_format = 'PNG'; o.save(); bpy.data.images.remove(o)
    for p in paths: os.remove(p)

def shots(which):
    R = bpy.data.objects['AhMa_root']; H = bpy.data.objects['head_ctrl']; tmp = os.path.join(SHOTS, '_t%d.png')
    def pose(yaw=0, roll=0, pitch=0): H.rotation_euler = (radians(pitch), radians(roll), radians(yaw))
    if 'hero' in which:
        set_expr('smile'); R.rotation_euler.z = 0; pose(yaw=13, roll=4)
        shoot(os.path.join(SHOTS, 'hero.png'), 1600, 2000, (0, .38, 1.07), 30, 5.9, 70, cz=1.15)
    if 'face' in which:
        set_expr('smile'); R.rotation_euler.z = 0; pose(yaw=12, roll=4)
        shoot(os.path.join(SHOTS, 'face.png'), 1600, 1600, (0, .12, 1.63), 32, 2.75, 85)
    pose()
    if 'expr' in which:
        for i, e in enumerate(EXPRS):
            set_expr(e); shoot(tmp % i, 400, 500, (0, .1, 1.66), 0, 2.75, 85)
        stitch([tmp % i for i in range(4)], os.path.join(SHOTS, 'expressions.png'), [400] * 4)
    if 'turn' in which:
        set_expr('smile')
        for i, rz in enumerate((0, 90, 180)):
            R.rotation_euler.z = radians(rz); tx = -.42 * sin(radians(rz))
            shoot(tmp % i, 534, 760, (tx, .0, 1.09), 0, 6.9, 85)
        stitch([tmp % i for i in range(3)], os.path.join(SHOTS, 'turn.png'), [534, 533, 533]); R.rotation_euler.z = 0
    set_expr('smile')

def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    make_materials(); root()
    head, BV = build_head(); build_face(BV); build_hair(); build_body(); build_walker(); setup_scene()
    tris = sum(tri_count(o) for o in bpy.data.objects if o.type == 'MESH' and o.name != 'floor')
    zs = [(o.matrix_world @ v.co).z for o in bpy.data.objects if o.type == 'MESH' and o.name != 'floor' for v in o.data.vertices]
    print('AHMA_TRIS', tris, 'HEIGHT %.3f' % max(zs))
    for o in sorted((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: -tri_count(o))[:40]: print('  ', o.name, tri_count(o))
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)

if 'build' in ARGS: build()
which = [a for a in ARGS if a in ('hero', 'face', 'expr', 'turn')]
if 'shots' in ARGS or which:
    if 'build' not in ARGS: bpy.ops.wm.open_mainfile(filepath=BLEND)
    shots(which or ['hero', 'face', 'expr', 'turn'])
