"""Teh Tarik Auntie (key `tarik`), locked style `toy`: designer vinyl collectible, sister to the toy Ah Ma.
Run: blender -b -P tarik.py -- build        (build, rig, shape keys, clips, save .blend, export glb)
     blender -b -P tarik.py -- shots [quick] (render beauty, turnaround, expressions, anim sheet from the .blend)
Axes: Z up, she faces +Y. Exporter turns that into glTF Y up, facing -Z.
Prop and style helpers are copied from tools/blender/styles/toy/ahma_toy.py (read only), rig and anim logic from heroes/ahma.py."""
import bpy, sys, os, math, random
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'blender', 'heroes'))
import hero_lib as H
OUT = os.path.join(ROOT, 'shots', 'heroes_toy', 'tarik')
TMP = os.path.join(HERE, '_tmp_tarik')
BLEND = os.path.join(TMP, 'tarik_toy.blend')
GLB = os.path.join(ROOT, 'assets', 'heroes', 'tarik.glb')
QUICK = 'quick' in sys.argv
os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build']

bpy.ops.wm.read_factory_settings(use_empty=True)
V = Vector; Z = V((0, 0, 1)); FPS = 30
F = 1.80 / 1.958   # final uniform scale, recomputed in stage_build from the measured height (1.80 m target)
DH = .07            # head raised by this much over round 4 so a short neck and the mandarin collar show

def sstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)

# ---------------------------------------------------------------- materials
def mat(name, hexcol, rough=.38, metal=0.0, coat=0.0, sss=0.0, spec=.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*H.srgb(hexcol), 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .08
    b.inputs['Specular IOR Level'].default_value = spec
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss
        b.inputs['Subsurface Radius'].default_value = (.08, .03, .02); b.inputs['Subsurface Scale'].default_value = .25
    return m

def textured(name, img, rough=.5):
    m = mat(name, '#FFFFFF', rough); nt = m.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
    nt.links.new(t.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color']); return m

def pack(name, img):
    n = img.shape[0]; im = bpy.data.images.new(name, img.shape[1], n, alpha=False)
    rgba = np.concatenate([img, np.ones((n, img.shape[1], 1), np.float32)], axis=2)
    im.pixels.foreach_set(rgba[::1].ravel()); im.pack(); return im

def dots_image(n=512):
    """Clean polka print: small cream dots on a warm sand blouse, drawn with distance fields."""
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / n
    img = np.empty((n, n, 3), np.float32); img[:] = (0.93, 0.84, 0.66)
    g = 6
    for iy in range(g):
        for ix in range(g):
            for (ox, oy, r, col) in ((0, 0, .030, (0.99, 0.95, 0.86)), (.5, .5, .018, (0.86, 0.60, 0.50))):
                cx = (ix + .5 + ox + (.5 if iy % 2 and ox == 0 else 0)) / g % 1.0; cy = (iy + .5 + oy) / g % 1.0
                dx = np.abs(xx - cx); dx = np.minimum(dx, 1 - dx); dy = np.abs(yy - cy); dy = np.minimum(dy, 1 - dy)
                a = np.clip((r - np.sqrt(dx * dx + dy * dy)) * n / 1.5 + .5, 0, 1)[..., None]
                img[:] = img * (1 - a) + np.array(col, np.float32) * a
    return pack('dots', img)

def towel_image(w=512, h=128):
    """Towel: white with two blue stripes near each end. u runs along the length."""
    img = np.empty((h, w, 3), np.float32); img[:] = (0.97, 0.96, 0.93)
    xs = np.arange(w) / w
    for c0, c1 in ((.07, .10), (.12, .13), (.87, .88), (.90, .93)):
        m = (xs >= c0) & (xs < c1); img[:, m] = (0.18, 0.40, 0.74)
    return pack('towel', img)

M = dict(
    skin=mat('skin', '#EDB48C', .42, sss=.12), nose=mat('nose', '#E9A27E', .42, sss=.12),
    blush=mat('blush', '#F0808C', .5), line=mat('line', '#CD8A68', .45),
    hair=mat('hair', '#3C2C36', .33, coat=.25), streak=mat('streak', '#C9C4CE', .33, coat=.25),
    brow=mat('brow', '#2A1E26', .45), eye=mat('eye', '#1A1214', .08, coat=1.0), white=mat('white', '#FFFDF8', .25),
    mouth=mat('mouth', '#6E1F2D', .45), tongue=mat('tongue', '#F2818C', .35), teeth=mat('teeth', '#FFFAF0', .25),
    lip=mat('lip', '#D9535F', .3, coat=.3),
    gold=mat('gold', '#F0B94A', .22, metal=1.0), pink=mat('pink', '#E96CB4', .4), pinkd=mat('pink_dark', '#C24E94', .4),
    apron=mat('apron', '#2E9C7E', .45), apronl=mat('apron_trim', '#F6F0E4', .4), tie=mat('apron_tie', '#2A8570', .45),
    slacks=mat('slacks', '#34384F', .5), red=mat('red', '#DB2A2E', .3, coat=.4),
    steel=mat('steel', '#DADDE2', .24, metal=1.0), steeld=mat('steel_dark', '#8A9099', .3, metal=1.0),
    tea=mat('tea', '#B0733A', .3, coat=.5), foam=mat('foam', '#F6EBD6', .5), collar=mat('collar', '#F3E7CB', .5),
)
M['blouse'] = textured('blouse', dots_image(), .5)
M['towel'] = textured('towel', towel_image(), .6)

# ---------------------------------------------------------------- scene + mesh helpers
SC = bpy.context.scene
HERO = []
GRP = ['body']          # current part group tag: 'body' or 'head'

def mk(name, verts, faces, m, uvs=None, mat_idx=None):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    for mm in (m if isinstance(m, (list, tuple)) else [m]): me.materials.append(mm)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    if mat_idx: me.polygons.foreach_set('material_index', mat_idx)
    if uvs:
        uv = me.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv', [c for f in uvs for co in f for c in co])
    ob = bpy.data.objects.new(name, me); SC.collection.objects.link(ob); return reg(ob)

def reg(ob):
    ob['grp'] = GRP[0]; HERO.append(ob); return ob

def sph_vf(seg=32, rings=16):
    vs = [V((0, 0, 1))]
    for j in range(1, rings):
        ph = math.pi * j / rings
        for i in range(seg):
            th = 2 * math.pi * i / seg; vs.append(V((math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph))))
    vs.append(V((0, 0, -1))); fs = []
    ring = lambda j, i: 1 + (j - 1) * seg + i % seg
    for i in range(seg): fs.append((0, ring(1, i), ring(1, i + 1)))
    for j in range(1, rings - 1):
        for i in range(seg): fs.append((ring(j, i), ring(j + 1, i), ring(j + 1, i + 1), ring(j, i + 1)))
    last = len(vs) - 1
    for i in range(seg): fs.append((last, ring(rings - 1, i + 1), ring(rings - 1, i)))
    return vs, fs

def ell(name, c, r, m, rot=None, seg=24):
    seg = max(10, int(seg * .7)); vs, fs = sph_vf(seg, seg // 2); c = V(c); R = rot if rot is not None else Matrix.Identity(3)
    return mk(name, [c + R @ V((v.x * r[0], v.y * r[1], v.z * r[2])) for v in vs], fs, m)

def frame_from(axis):
    n = V(axis).normalized(); a = V((1, 0, 0)) if abs(n.x) < .9 else V((0, 1, 0))
    t = n.cross(a).normalized(); u = n.cross(t).normalized(); return t, u, n

def tor(name, c, axis, R, r, m, seg=40, rseg=10, squash=None):
    seg = int(seg * .75); rseg = max(6, int(rseg * .8))
    t, u, n = frame_from(axis); c = V(c); vs = []; fs = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; d = t * math.cos(a) + u * math.sin(a)
        for j in range(rseg):
            b = 2 * math.pi * j / rseg; p = d * (R + r * math.cos(b)) + n * (r * math.sin(b))
            if squash: p = V((p.x * squash[0], p.y * squash[1], p.z * squash[2]))
            vs.append(c + p)
    for i in range(seg):
        for j in range(rseg):
            a = i * rseg + j; b = ((i + 1) % seg) * rseg + j; c2 = ((i + 1) % seg) * rseg + (j + 1) % rseg; d2 = i * rseg + (j + 1) % rseg
            fs.append((a, b, c2, d2))
    return mk(name, vs, fs, m)

def fillet(pts, R, k=6):
    pts = [V(p) for p in pts]; out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p = pts[i]; d1 = (pts[i - 1] - p).normalized(); d2 = (pts[i + 1] - p).normalized(); th = d1.angle(d2)
        if th > 3.1: out.append(p); continue
        tl = R / math.tan(th / 2); c = p + (d1 + d2).normalized() * (R / math.sin(th / 2))
        v0 = p + d1 * tl - c; v1 = p + d2 * tl - c
        for s in range(k + 1): out.append(c + v0.slerp(v1, s / k).normalized() * R)
    out.append(pts[-1]); return out

def bez(a, b, c, n=10):
    a, b, c = V(a), V(b), V(c)
    return [a * (1 - t) ** 2 + b * 2 * t * (1 - t) + c * t * t for t in [i / (n - 1) for i in range(n)]]

def sweep(name, pts, radii, m, seg=14, uvrep=None, round_caps=True, lip=None):
    seg = max(6, int(seg * .75)); pts = [V(p) for p in pts]; n = len(pts)
    if isinstance(radii, (int, float)): radii = [radii] * n
    T = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    N = frame_from(T[0])[0]; rings = []
    def ring(c, Nn, Bn, r): return [c + (Nn * math.cos(2 * math.pi * i / seg) + Bn * math.sin(2 * math.pi * i / seg)) * r for i in range(seg)]
    def dome(c, t, Nn, Bn, r, sign):
        return [ring(c + t * (sign * r * math.sin(a)), Nn, Bn, r * math.cos(a)) for a in (math.radians(35), math.radians(65), math.radians(89))]
    for i in range(n):
        N = (N - T[i] * N.dot(T[i])).normalized(); B = T[i].cross(N)
        if i == 0 and round_caps: rings += reversed(dome(pts[0], T[0], N, B, radii[0], -1))
        rings.append(ring(pts[i], N, B, radii[i]))
    if lip:
        rings.append(ring(pts[-1] - T[-1] * lip[0], N, B, lip[1])); rings.append(ring(pts[-1] - T[-1] * lip[0] * 3, N, B, lip[1] * .2))
    elif round_caps: rings += dome(pts[-1], T[-1], N, B, radii[-1], 1)
    vs = [p for r in rings for p in r]; fs = []; uvs = []; L = [0.0]
    for j in range(1, len(rings)): L.append(L[-1] + ((rings[j][0] + rings[j][seg // 2]) * .5 - (rings[j - 1][0] + rings[j - 1][seg // 2]) * .5).length)
    ur, vr = uvrep or (1, 1)
    for j in range(len(rings) - 1):
        for i in range(seg):
            fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
            uvs.append([(i / seg * ur, L[j] * vr), ((i + 1) / seg * ur, L[j] * vr), ((i + 1) / seg * ur, L[j + 1] * vr), (i / seg * ur, L[j + 1] * vr)])
    fs.append(tuple(reversed(range(seg)))); uvs.append([(0, 0)] * seg)
    fs.append(tuple(range((len(rings) - 1) * seg, len(rings) * seg))); uvs.append([(0, 0)] * seg)
    return mk(name, vs, fs, m, uvs)

def rbox(name, c, size, m, bevel=.01, rot=None, bseg=4):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); ob = bpy.context.object; ob.name = name
    for v in ob.data.vertices: v.co = V((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    b = ob.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = bseg; b.limit_method = 'ANGLE'; H.apply_mod(ob, b)
    H.shade_smooth(ob); ob.data.materials.append(m)
    ob.matrix_world = Matrix.Translation(V(c)) @ (rot.to_4x4() if rot is not None else Matrix.Identity(4))
    H.apply_transforms(ob); return reg(ob)

def lathe(name, prof, m, seg=32, c=(0, 0, 0)):
    """prof: list of (radius, z) from bottom to top. Closed shell round the vertical axis through c."""
    seg = int(seg * .75); vs = []; fs = []; c = V(c); n = len(prof)
    for r, z in prof:
        for i in range(seg):
            a = 2 * math.pi * i / seg; vs.append(c + V((r * math.cos(a), r * math.sin(a), z)))
    for j in range(n - 1):
        for i in range(seg): fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
    return mk(name, vs, fs, m)

# ---------------------------------------------------------------- proportions
BY = -0.04
HC = V((0, -0.01, 1.33 + DH)); HR = V((0.50, 0.47, 0.44))
EXe, EZe = .185, .03
HOLE = (0.0, -.22, .215, .145)          # mouth plate outer ellipse: cx, cz, a, b (face coordinates). The head hole is .03 smaller

def surf(fx, fz, off=0.0):
    k = max(1e-4, 1 - (fx / HR.x) ** 2 - (fz / HR.z) ** 2); y = HR.y * math.sqrt(k)
    n = V((fx / HR.x ** 2, y / HR.y ** 2, fz / HR.z ** 2)).normalized()
    t = n.cross(Z).normalized(); u = t.cross(n).normalized()
    return HC + V((fx, y, fz)) + n * off, n, t, u

# ---------------------------------------------------------------- body
BODY_Z = [.30, .36, .44, .52, .60, .68, .76, .82, .865, .90]
BODY_R = [.285, .33, .395, .43, .435, .41, .365, .30, .20, .09]
def BR(z): return float(np.interp(z, BODY_Z, BODY_R))
def torso_xy(r, a): return (r * math.cos(a), BY + .88 * r * math.sin(a))

def build_body():
    zs = np.linspace(.30, .90, 22); rs = np.array([BR(z) for z in zs])
    for _ in range(2): rs[1:-1] = (rs[:-2] + 2 * rs[1:-1] + rs[2:]) / 4
    global BR
    tab = (zs, rs); BR = lambda z: float(np.interp(z, tab[0], tab[1]))
    seg = 36; vs = []; fs = []; uvs = []
    for r, z in zip(rs, zs):
        for i in range(seg):
            a = 2 * math.pi * i / seg; vs.append(V((r * math.cos(a), BY + .88 * r * math.sin(a), z)))
    for j in range(len(zs) - 1):
        for i in range(seg):
            fs.append((j * seg + i, j * seg + (i + 1) % seg, (j + 1) * seg + (i + 1) % seg, (j + 1) * seg + i))
            v0 = zs[j] * 1.6; v1 = zs[j + 1] * 1.6
            uvs.append([(i / seg * 4, v0), ((i + 1) / seg * 4, v0), ((i + 1) / seg * 4, v1), (i / seg * 4, v1)])
    fs.append(tuple(range((len(zs) - 1) * seg, len(zs) * seg))); uvs.append([(0, 0)] * seg)
    mk('blouse', vs, fs, M['blouse'], uvs)
    # short neck, then a stand-up mandarin collar: one closed band with real thickness, open at the front
    NY = -.025
    sweep('neck', [(0, NY, .80), (0, NY, 1.0)], [.112, .108], M['skin'], seg=24, round_caps=False)
    na, nz, th = 28, 4, .014; gap = math.radians(13); vs = []; fs = []
    def cr(z): return .158 - .32 * (z - .845)          # collar leans in towards the neck
    for side in (0, 1):                                 # 0 outer, 1 inner
        for j in range(nz + 1):
            z = .845 + .085 * j / nz
            for i in range(na + 1):
                a = math.pi / 2 + gap + (2 * math.pi - 2 * gap) * i / na; r = cr(z) - th * side
                vs.append(V((r * math.cos(a), NY + .93 * r * math.sin(a), z)))
    W = na + 1; L = (nz + 1) * W; ix = lambda sd, j, i: sd * L + j * W + i
    for j in range(nz):
        for i in range(na):
            fs.append((ix(0, j, i), ix(0, j, i + 1), ix(0, j + 1, i + 1), ix(0, j + 1, i)))
            fs.append((ix(1, j, i), ix(1, j + 1, i), ix(1, j + 1, i + 1), ix(1, j, i + 1)))
    for i in range(na):
        fs.append((ix(0, nz, i), ix(0, nz, i + 1), ix(1, nz, i + 1), ix(1, nz, i)))
        fs.append((ix(0, 0, i), ix(1, 0, i), ix(1, 0, i + 1), ix(0, 0, i + 1)))
    for j in range(nz):
        fs.append((ix(0, j, 0), ix(0, j + 1, 0), ix(1, j + 1, 0), ix(1, j, 0)))
        fs.append((ix(0, j, na), ix(1, j, na), ix(1, j + 1, na), ix(0, j + 1, na)))
    import bmesh
    ob = mk('collar', vs, fs, M['collar']); bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    ell('collar_knot', (0, BY + .88 * BR(.855) + .004, .855), (.021, .016, .019), M['collar'], seg=14)
    tor('blouse_hem', (0, BY, .31), Z, BR(.31), .012, M['collar'], seg=48, rseg=6, squash=(1, .88, 1))
    # hips and legs (slacks)
    ell('hips', (0, BY, .43), (.30, .26, .10), M['slacks'])
    for s in (-1, 1):
        sweep('leg', [(s * .15, BY, .46), (s * .152, BY, .30), (s * .155, BY, .13)], [.125, .118, .112], M['slacks'], seg=24, lip=(.012, .08))
        sweep('cuff', [(s * .155, BY, .14), (s * .155, BY, .13)], .118, M['slacks'], seg=24, round_caps=False)
        ell('foot', (s * .155, BY + .08, .075), (.095, .165, .052), M['skin'])
        ell('sole', (s * .155, BY + .075, .03), (.118, .205, .03), M['red'])
        post = V((s * .155, BY + .19, .09))
        for o in (-1, 1):
            sweep('strap', bez(post, (s * .155 + o * .08, BY + .13, .165), (s * .155 + o * .105, BY + .01, .045)), .016, M['red'], seg=8)
        ell('strap_post', post, (.019, .019, .024), M['red'], seg=12)

def AR(z):   # apron base radius: follows the body over the belly, then hangs straight down like cloth instead of tucking under
    return max(BR(max(z, .30)), .435 - .30 * max(0.0, .58 - z))

def build_apron():
    z0, z1 = .27, .80; nz, na = 16, 22
    def half(z):  # half angle (deg) of the apron wrap by height: front skirt, narrow flat bib
        return 84 - 56 * sstep(.54, .66, z)
    outer = []; inner = []
    for j in range(nz + 1):
        ro = []; ri = []
        for i in range(na + 1):
            zb = z0 + .06 * (2 * i / na - 1) ** 4; z = zb + (z1 - zb) * j / nz      # hem lifts at the sides like cloth over the hips
            a = math.pi / 2 + math.radians(half(z)) * (2 * i / na - 1); r = AR(z)
            ro.append(V((*torso_xy(r + .030, a), z))); ri.append(V((*torso_xy(r + .010, a), z)))
        outer.append(ro); inner.append(ri)
    vs = []; idx = {}
    for nm, g in (('o', outer), ('i', inner)):
        for j in range(nz + 1):
            for i in range(na + 1): idx[(nm, j, i)] = len(vs); vs.append(g[j][i])
    fs = []
    for j in range(nz):
        for i in range(na):
            a, b, c, d = idx[('o', j, i)], idx[('o', j, i + 1)], idx[('o', j + 1, i + 1)], idx[('o', j + 1, i)]
            fs.append((a, d, c, b))
            a, b, c, d = idx[('i', j, i)], idx[('i', j, i + 1)], idx[('i', j + 1, i + 1)], idx[('i', j + 1, i)]
            fs.append((a, b, c, d))
    for j in range(nz):  # side walls
        for i in (0, na):
            a, b, c, d = idx[('o', j, i)], idx[('o', j + 1, i)], idx[('i', j + 1, i)], idx[('i', j, i)]
            fs.append((a, b, c, d) if i else (a, d, c, b))
    for i in range(na):
        for j, flip in ((0, 1), (nz, 0)):
            a, b, c, d = idx[('o', j, i)], idx[('o', j, i + 1)], idx[('i', j, i + 1)], idx[('i', j, i)]
            fs.append((a, d, c, b) if flip else (a, b, c, d))
    mk('apron', vs, fs, M['apron'])
    # white hem trim along the skirt and the bib top
    hem = [V((*torso_xy(AR(z0 + .06 * (2 * i / 22 - 1) ** 4) + .032, math.pi / 2 + math.radians(half(z0)) * (2 * i / 22 - 1)), z0 + .06 * (2 * i / 22 - 1) ** 4 + .004)) for i in range(23)]
    sweep('apron_hem', hem, .0125, M['apronl'], seg=8)
    top = [V((*torso_xy(AR(z1) + .032, math.pi / 2 + math.radians(half(z1)) * (2 * i / 12 - 1)), z1 - .004)) for i in range(13)]
    sweep('apron_top', top, .0115, M['apronl'], seg=8)
    # pocket
    zc = .44; yf = BY + .88 * (AR(zc) + .030)
    rbox('pocket', (0, yf + .008, zc), (.21, .03, .15), M['apron'], bevel=.012)
    sweep('pocket_trim', [(-.095, yf + .0245, zc + .070), (.095, yf + .0245, zc + .070)], .008, M['apronl'], seg=8)
    # straps over the shoulders and a waist tie with a bow at the back
    for s in (-1, 1):
        p0 = V((s * .155, torso_xy(BR(.80) + .03, math.atan2(.5, s * .17))[1] , .79))
        p0 = V((s * .155, BY + .88 * math.sqrt(max(1e-4, (BR(.80) + .03) ** 2 - .155 ** 2)), .79))
        pts = bez(p0 + V((0, 0, 0)), V((s * .24, BY + .02, .965)), V((s * .17, BY - .26, .74)), 12)
        sweep('strap', pts, [.021] * 12, M['tie'], seg=8)
    zt = .58
    for s in (-1, 1):
        pts = [V((*torso_xy(AR(zt) + .031, math.radians(90 + s * (half(zt) - 2 + k * (174 - half(zt)) / 8))), zt)) for k in range(9)]
        sweep('waist_tie', [V((p.x, p.y, p.z)) for p in pts], .018, M['tie'], seg=8)
    bc = V((0, BY - .88 * (AR(zt) + .05), zt))
    for s in (-1, 1):
        ell('bow_loop', bc + V((s * .085, -.012, .012)), (.085, .03, .05), M['tie'], rot=Matrix.Rotation(s * .35, 3, 'Y'), seg=20)
        sweep('bow_tail', bez(bc, bc + V((s * .05, -.03, -.06)), bc + V((s * .09, -.02, -.17)), 8), [.02, .02, .02, .02, .02, .018, .015, .01], M['tie'], seg=8)
    ell('bow_knot', bc, (.032, .026, .032), M['tie'], seg=16)

def build_towel():
    """Hand towel over the left shoulder (character left, -x). Flat ribbon that follows the body."""
    s = -1
    P = [V((s * .27, BY + .88 * math.sqrt(max(1e-4, (AR(.68) + .05) ** 2 - .27 ** 2)), .68)),     # front end hangs beside the bib, not over it
         V((s * .20, BY + .88 * math.sqrt(max(1e-4, (BR(.80) + .04) ** 2 - .2 ** 2)), .80)),
         V((s * .205, BY + .06, .95)), V((s * .22, BY - .10, .935)),
         V((s * .20, BY - .88 * math.sqrt(max(1e-4, (BR(.80) + .04) ** 2 - .2 ** 2)) + .0, .80)),
         V((s * .17, BY - .88 * math.sqrt(max(1e-4, (BR(.56) + .04) ** 2 - .17 ** 2)), .56))]
    # smooth path
    path = []
    for k in range(len(P) - 1):
        for t in np.linspace(0, 1, 6, endpoint=(k == len(P) - 2)):
            a = P[max(k - 1, 0)]; b = P[k]; c = P[k + 1]; d = P[min(k + 2, len(P) - 1)]
            path.append(.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3))
    n = len(path); wdt = .075; th = .012; vs = []; fs = []; uvs = []; L = [0.0]
    for i in range(1, n): L.append(L[-1] + (path[i] - path[i - 1]).length)
    for i in range(n):
        T = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        out = V((path[i].x, (path[i].y - BY) / .88, 0)).normalized(); out = V((out.x, out.y * .88, 0)).normalized()
        if path[i].z > .90: out = Z * .6 + out * .4
        wd = T.cross(out).normalized(); out = wd.cross(T).normalized()
        for sg in (-1, 1):
            for sd in (-1, 1): vs.append(path[i] + wd * (sg * wdt) + out * (th if sd > 0 else 0) * (1 if sd > 0 else 1))
    for i in range(n - 1):
        a0 = i * 4; a1 = (i + 1) * 4
        # faces: outer (sd=1) -> idx 1 (sg=-1) and 3 (sg=1); inner (sd=-1) -> 0 and 2
        fs += [(a0 + 1, a0 + 3, a1 + 3, a1 + 1), (a0 + 0, a1 + 0, a1 + 2, a0 + 2), (a0 + 0, a0 + 1, a1 + 1, a1 + 0), (a0 + 2, a1 + 2, a1 + 3, a0 + 3)]
        u0 = L[i] / L[-1]; u1 = L[i + 1] / L[-1]
        uvs += [[(u0, 0), (u0, 1), (u1, 1), (u1, 0)], [(u0, 0), (u1, 0), (u1, 1), (u0, 1)], [(u0, 0), (u0, 0), (u1, 0), (u1, 0)], [(u0, 1), (u1, 1), (u1, 1), (u0, 1)]]
    fs.append((0, 2, 3, 1)); uvs.append([(0, 0)] * 4); fs.append((4 * (n - 1), 4 * (n - 1) + 1, 4 * (n - 1) + 3, 4 * (n - 1) + 2)); uvs.append([(1, 0)] * 4)
    mk('towel', vs, fs, M['towel'], uvs)

# ---------------------------------------------------------------- arms, hands, props
SH = {1: V((.27, BY, .78)), -1: V((-.27, BY, .78))}
EL = {1: V((.50, .10, .62)), -1: V((-.50, .10, .60))}
WR = {1: V((.44, .31, .72)), -1: V((-.44, .27, .58))}
# grip bar centres (vertical bar through the fist)
GR = {1: V((.50, .42, .80)), -1: V((-.50, .38, .62))}
JUG_O = GR[1] - V((.165, 0, .155))     # right: tall pulling mug with a pour lip (kept the `jug` names: spout_jug is contract)
MUG_O = GR[-1] - V((-.15, 0, .115))    # left: shorter pulling mug with tea and foam
LIP = V((-.142, 0, .318))               # pour lip tip on the right mug, relative to JUG_O

def build_arms():
    for s in (1, -1):
        S, E, W = SH[s], EL[s], WR[s]
        mid = S.lerp(E, .55)
        # blouse sleeve: shoulder to just past the elbow
        pts = bez(S, S.lerp(E, .5) + V((s * .02, 0, .02)), E.lerp(W, .22), 9)
        sweep('sleeve', pts, [.135, .14, .14, .138, .134, .128, .122, .115, .108], M['blouse'], seg=22, uvrep=(1.3, 1.55), lip=(.004, .088))
        tor('sleeve_hem', pts[-1], pts[-1] - pts[-2], .104, .011, M['collar'], seg=28, rseg=6)
        # pink arm sleeve from the elbow to the wrist, ruched band at the top
        a0 = E.lerp(W, .16); dirv = (W - a0).normalized()
        fpts = [a0 + dirv * (W - a0).length * t for t in np.linspace(0, 1, 6)]
        sweep('armsleeve', fpts, [.098, .099, .097, .092, .087, .083], M['pink'], seg=20, round_caps=False)
        tor('armsleeve_top', fpts[0], dirv, .096, .016, M['pinkd'], seg=28, rseg=6)
        tor('armsleeve_cuff', fpts[-1], dirv, .083, .012, M['pinkd'], seg=28, rseg=6)
        build_hand(s)

def build_hand(s):
    """Fist round a vertical handle bar: palm behind the bar, four separate fingers through the handle loop, thumb over the top.
    Same build as gym.py: capsules remeshed at a fine voxel so the finger grooves survive."""
    G = GR[s]; W = WR[s]; a = V((0, 0, 1)); u = V((0, -1, 0)); w = V((-s, 0, 0)); rb = .0185
    so = H.Soup('hand')
    pc = G + u * (rb + .05) + V((0, 0, .006))
    so.ellipsoid(pc, (.05, .036, .072))
    so.capsule(W, pc, .06, .052, seg=16)
    for k in range(4):
        y = (1.5 - k) * .037 + .004; r = .0205 - .0015 * (k == 3)
        arc = [G + a * y + (u * math.cos(math.radians(ph)) + w * math.sin(math.radians(ph))) * (rb + r + .002) for ph in (15, 75, 135, 190, 225)]
        rr = [r + .003, r + .001, r, r, r * .9]
        for p0, p1, r0, r1 in zip(arc[:-1], arc[1:], rr[:-1], rr[1:]): so.capsule(p0, p1, r0, r1, seg=12)
    # thumb: leaves the inner top of the palm and closes over the bar from the other side
    tb = pc + a * .05 + w * -.012
    arc = [tb, G + a * .078 + (u * math.cos(math.radians(-35)) - w * math.sin(math.radians(35))) * (rb + .028),
           G + a * .076 + (u * math.cos(math.radians(-95)) + w * math.sin(math.radians(-95))) * (rb + .026)]
    for p0, p1, r0, r1 in zip(arc[:-1], arc[1:], (.029, .026), (.026, .023)): so.capsule(p0, p1, r0, r1, seg=12)
    hand, _ = so.remesh(voxel=.0062, smooth=5, smooth_factor=.5, target_tris=1100)
    H.set_material(hand, M['skin']); hand.name = 'hand'; reg(hand)

def build_props():
    """Two stainless pulling mugs. Lathed with a rolled rim and an inner wall, so they read as open steel cups, not solid cans."""
    steel = M['steel']; jo = JUG_O
    lathe('jug_body', [(0, 0), (.07, 0), (.082, .01), (.086, .05), (.092, .27), (.1, .3), (.104, .312), (.097, .318), (.09, .306), (.084, .27), (.08, .25)], steel, seg=36, c=jo)
    ell('jug_tea', jo + V((0, 0, .25)), (.081, .081, .01), M['tea'], seg=24)
    sweep('jug_lip', [jo + V((-.07, 0, .29)), jo + V((-.11, 0, .305)), jo + LIP], [.034, .022, .01], steel, seg=14)
    sweep('jug_handle', fillet([jo + V(p) for p in ((.09, 0, .26), (.165, 0, .27), (.165, 0, .04), (.088, 0, .05))], .04, 6), .0185, steel, seg=12)
    mo = MUG_O
    lathe('mug_body', [(0, 0), (.058, 0), (.07, .012), (.074, .05), (.08, .21), (.087, .228), (.09, .236), (.083, .24), (.077, .226), (.074, .2)], steel, seg=32, c=mo)
    ell('mug_tea', mo + V((0, 0, .21)), (.075, .075, .01), M['tea'], seg=20)
    ell('mug_foam', mo + V((0, 0, .218)), (.066, .066, .014), M['foam'], seg=20)
    sweep('mug_handle', fillet([mo + V(p) for p in ((-.077, 0, .2), (-.15, 0, .205), (-.15, 0, .025), (-.072, 0, .03))], .035, 6), .0185, steel, seg=12)

# ---------------------------------------------------------------- head
def head_surface():
    vs, fs = sph_vf(48, 24); P = [HC + V((v.x * HR.x, v.y * HR.y, v.z * HR.z)) for v in vs]
    cx, cz, a, b = HOLE; a -= .03; b -= .03; keep = []
    for f in fs:
        c = sum((P[i] for i in f), V()) / len(f); fx = c.x - HC.x; fz = c.z - HC.z
        if c.y > HC.y and ((fx - cx) / a) ** 2 + ((fz - cz) / b) ** 2 < 1: continue
        keep.append(f)
    used = sorted({i for f in keep for i in f}); remap = {o: n for n, o in enumerate(used)}
    return mk('head', [P[i] for i in used], [tuple(remap[i] for i in f) for f in keep], M['skin'])

def head_normal(p):     # analytic ellipsoid normal, shared by the head shell and the mouth plate so the plate edge does not shade as a patch
    d = p - HC; return V((d.x / HR.x ** 2, d.y / HR.y ** 2, d.z / HR.z ** 2)).normalized()

def ellipsoid_normals(ob, only=None):
    me = ob.data; ns = []
    for v in me.vertices:
        ns.append(head_normal(v.co) if (only is None or v.index in only) else v.normal.copy())
    me.normals_split_custom_set_from_vertices([tuple(n) for n in ns])

def build_head():
    ellipsoid_normals(head_surface())
    rnd = random.Random(5); so = H.Soup('hair'); n = 90
    def thr(az): return float(np.interp(az, [0, 35, 65, 95, 180], [58, 52, 36, 10, -36]))
    for i in range(n):
        z = 1 - 2 * (i + .5) / n; a = i * 2.39996; r = math.sqrt(1 - z * z); d = V((r * math.cos(a), r * math.sin(a), z))
        az = math.degrees(math.atan2(abs(d.x), d.y)); el = math.degrees(math.asin(d.z))
        if el < thr(az): continue
        rim = el - thr(az) < 14; rad = rnd.uniform(.12, .14) if rim else rnd.uniform(.15, .17)
        so.sphere(HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z)) * (.93 if rim else .85), rad, seg=20)
    hair, _ = so.remesh(voxel=.012, smooth=24, smooth_factor=.6, target_tris=3400); H.set_material(hair, M['hair']); reg(hair)
    # clean grey lock: one smooth tube swept from the hairline over the crown
    pts = []
    for el in np.linspace(62, 112, 14):
        e = math.radians(el); d = V((-.24 * math.cos(e) ** 2, math.cos(e) * .97, math.sin(e))).normalized()
        pts.append(HC + V((d.x * HR.x, d.y * HR.y, d.z * HR.z)) + d * .068)
    sweep('streak', pts, [.012, .03, .042, .048, .05, .05, .05, .05, .05, .048, .044, .036, .026, .012], M['streak'], seg=12)
    for s in (-1, 1):
        ell('ear', HC + V((s * .495, -.03, -.05)), (.042, .075, .095), M['skin'], seg=20)
        ell('stud', HC + V((s * .532, -.01, -.105)), (.024, .024, .024), M['gold'], seg=16)
    p, n_, t, u = surf(0, -.075); ell('nose', p + n_ * .004, (.05, .042, .04), M['nose'], seg=24)

# ---------------------------------------------------------------- face (one mesh, shape keys)
E0 = dict(bz=.17, tilt=-.004, arch=.02, eye='bead', es=(1, 1), cut=None, hl=.026, w=.15, curve=.022, up=0, dn=0, teeth=0, tongue=0, cz=-.215, crease=0, bth=1.0)
def ex(**k): d = dict(E0); d.update(k); return d
EXPR = {
    'rest': ex(),
    'smile': ex(bz=.185, arch=.03, w=.21, curve=.046),
    'blink': ex(eye='lid', arch=.0, bz=.165),
    'mouth_open': ex(bz=.19, w=.15, curve=.012, up=.03, dn=.07, teeth=.03, tongue=.045),
    'angry': ex(bz=.08, tilt=.09, arch=-.008, es=(1.02, .84), cut=(.014, .85), hl=.0, w=.22, curve=-.06, up=.02, dn=.05, teeth=.034, tongue=0, cz=-.205, crease=1, bth=1.25),
    'grin': ex(bz=.205, tilt=-.012, arch=.034, eye='arc', w=.31, curve=.06, up=.004, dn=.085, teeth=.034, tongue=.05, cz=-.225),
    'ult': ex(bz=.19, tilt=.07, arch=.004, es=(1.12, 1.16), hl=.03, w=.25, curve=.006, up=.05, dn=.10, teeth=.034, tongue=.07, cz=-.22),
}
FM = ['skin', 'brow', 'eye', 'white', 'line', 'mouth', 'lip', 'teeth', 'tongue', 'blush']

def face_geo(e):
    vs = []; fs = []; mi = []
    def add(v, f, m):
        o = len(vs); vs.extend(v); fs.extend([tuple(i + o for i in ff) for ff in f]); mi.extend([FM.index(m)] * len(f))
    def hide(v): return [HC.copy() for _ in v]
    def stroke(pts, rw, rn, off, m, show=True, seg=8):
        P = [surf(x, z, off) for x, z in pts]; n = len(P); v = []
        for i in range(n):
            p, nn, _, _ = P[i]; tan = (P[min(i + 1, n - 1)][0] - P[max(i - 1, 0)][0]).normalized(); side = nn.cross(tan).normalized()
            f = math.sin(math.pi * i / (n - 1)) ** .45 if 0 < i < n - 1 else 0.0
            v += [p + (side * math.cos(a) * rw + nn * math.sin(a) * rn) * f for a in [2 * math.pi * k / seg for k in range(seg)]]
        f = [(i * seg + k, i * seg + (k + 1) % seg, (i + 1) * seg + (k + 1) % seg, (i + 1) * seg + k) for i in range(n - 1) for k in range(seg)]
        add(v if show else hide(v), f, m)
    def blob(fx, fz, rad, off, m, tilt=0.0, show=True, seg=20, d=(0, 0), cut=None):
        p, n, t, u = surf(fx, fz); sv, sf = sph_vf(seg, seg // 2); ct, st_ = math.cos(tilt), math.sin(tilt); v = []
        for q in sv:
            lx, lz = q.x * rad[0], q.z * rad[2]
            if cut: lz = min(lz, cut[0] + cut[1] * lx)
            v.append(p + t * (lx * ct - lz * st_ + d[0]) + u * (lx * st_ + lz * ct + d[1]) + n * (q.y * rad[1] + off))
        add(v if show else hide(v), sf, m)
    def patch(x0, x1, lo, hi, off, m, nx=24, ny=3):
        v = []
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx; a, b = lo(x), hi(x)
            for j in range(ny + 1): v.append(surf(x, a + (b - a) * j / ny, off)[0])
        f = [(i * (ny + 1) + j, i * (ny + 1) + j + 1, (i + 1) * (ny + 1) + j + 1, (i + 1) * (ny + 1) + j) for i in range(nx) for j in range(ny)]
        add(v, f, m)
    bead = e['eye'] == 'bead'; bth = e['bth']
    for s in (-1, 1):
        stroke([(s * (EXe + q * .095), e['bz'] + q * e['tilt'] + e['arch'] * (1 - q * q)) for q in [i / 5 - 1 for i in range(11)]], .033 * bth, .018, .004, 'brow')
        a, c = .055 * e['es'][0], .07 * e['es'][1]
        blob(s * EXe, EZe, (a, .036, c), 0, 'eye', show=bead, seg=24, cut=(e['cut'][0], e['cut'][1] * s) if e['cut'] else None)
        blob(s * EXe, EZe, (.019, .012, .019), .028, 'white', show=bead and e['hl'] > 0, seg=12, d=(.02, e['hl']))
        blob(s * EXe, EZe, (.008, .006, .008), .026, 'white', show=bead and e['hl'] > 0, seg=8, d=(-.022, -.03))
        # happy arc and closed lid strokes
        stroke([(s * EXe + .066 * math.cos(ph), EZe - .028 + .062 * math.sin(ph)) for ph in [math.radians(168 - 156 * i / 11) for i in range(12)]], .0145, .011, .005, 'eye', show=e['eye'] == 'arc')
        stroke([(s * EXe + .062 * math.cos(ph), EZe + .03 - .05 * math.sin(ph)) for ph in [math.radians(168 - 156 * i / 11) for i in range(12)]], .0145, .011, .005, 'eye', show=e['eye'] == 'lid')
        # frown crease between the brows (angry only)
        stroke([(s * .035 + s * q * .006, .082 + .05 * (i / 5)) for i, q in zip(range(6), [0] * 6)], .0085, .006, .002, 'line', show=bool(e['crease']))
        v = [surf(s * .31, -.115, .0025)[0]]; f = []
        for j in range(1, 4):
            for i in range(20):
                ang = 2 * math.pi * i / 20; v.append(surf(s * .31 + .07 * j / 3 * math.cos(ang), -.115 + .052 * j / 3 * math.sin(ang), .0025 if j < 3 else .0)[0])
        ri = lambda j, i: 1 + (j - 1) * 20 + i % 20
        f += [(0, ri(1, i), ri(1, i + 1)) for i in range(20)]
        f += [(ri(j, i), ri(j + 1, i), ri(j + 1, i + 1), ri(j, i + 1)) for j in (1, 2) for i in range(20)]
        add(v, f, 'blush')
    # ---- mouth: skin ring, lips, a real cavity, upper tooth row and tongue
    cx0, cz0, Ao, Bo = HOLE; hw = e['w'] / 2; U = e['up'] + .0065; D = e['dn'] + .0065
    def zc(x): return e['cz'] + e['curve'] * (x / hw) ** 2
    def opening(th):
        x = hw * math.cos(th); sn = math.sin(th); return x, zc(x) + (U if sn >= 0 else D) * (sn if sn >= 0 else -sn) * (1 if sn >= 0 else -1)
    cen = (0.0, e['cz'] + (U - D) * .3)
    rings = []
    lerpp = lambda p, q, t: (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
    for k in range(NTH):
        th = 2 * math.pi * k / NTH; ox, oz = opening(th)
        outer = (Ao * math.cos(th), cz0 + Bo * math.sin(th)); lipo = (ox + .014 * math.cos(th), oz + .016 * math.sin(th))
        sc = lambda t: (cen[0] + (ox - cen[0]) * t, cen[1] + (oz - cen[1]) * t)
        rows = [surf(*outer, .0008)[0], surf(*lerpp(outer, lipo, .5), .0025)[0], surf(*lipo, .0065)[0],
                surf(*lerpp(lipo, (ox, oz), .5), .0125)[0], surf(ox, oz, .006)[0],
                surf(ox, oz, -.012)[0], surf(*sc(.88), -.04)[0], surf(*sc(.62), -.068)[0], surf(*sc(.28), -.088)[0]]
        rings.append(rows)
    nr = len(rings[0]); v = [rings[k][r] for r in range(nr) for k in range(NTH)] + [surf(cen[0], cen[1], -.092)[0]]
    f = []; fm = []
    mats = ['skin', 'skin', 'lip', 'lip', 'mouth', 'mouth', 'mouth', 'mouth']
    for r in range(nr - 1):
        for k in range(NTH):
            a_, b_ = r * NTH + k, r * NTH + (k + 1) % NTH; c_, d_ = (r + 1) * NTH + (k + 1) % NTH, (r + 1) * NTH + k
            f.append((a_, d_, c_, b_)); fm.append(mats[r])
    cv = nr * NTH
    for k in range(NTH): f.append(((nr - 1) * NTH + k, cv, (nr - 1) * NTH + (k + 1) % NTH)); fm.append('mouth')
    o = len(vs); MOUTH0[0] = o; vs.extend(v); fs.extend([tuple(i + o for i in ff) for ff in f]); mi.extend([FM.index(m) for m in fm])
    env = lambda x: max(0.0, 1 - (x / hw) ** 2) ** .5
    def up_e(x): return zc(x) + U * env(x)
    def lo_e(x): return zc(x) - D * env(x)
    tw = hw * .86
    th_ = e['teeth']
    patch(-tw, tw, lambda x: up_e(x) - th_ * (1.1 - .45 * (x / tw) ** 2) if th_ else up_e(x) - .0005, lambda x: up_e(x) - .0005, -.011, 'teeth')
    gw = hw * .6; tg = e['tongue']
    patch(-gw, gw, lambda x: lo_e(x) + .004, lambda x: lo_e(x) + .004 + tg * max(0.0, 1 - (x / gw) ** 2) ** .5, -.036, 'tongue')
    return vs, fs, mi

NTH = 40; MOUTH0 = [0]

def build_face():
    vs, fs, mi = face_geo(EXPR['rest'])
    ob = mk('face', vs, fs, [M[k] for k in FM], mat_idx=mi)
    ellipsoid_normals(ob, set(range(MOUTH0[0], MOUTH0[0] + 2 * NTH)))      # the two skin rows of the mouth plate
    ob.shape_key_add(name='Basis')
    for name in ('blink', 'mouth_open', 'smile', 'angry', 'grin', 'ult'):
        k = ob.shape_key_add(name=name); v2 = face_geo(EXPR[name])[0]; k.data.foreach_set('co', [c for v in v2 for c in v])
    return ob

def set_expr(head, name):
    for k in head.data.shape_keys.key_blocks:
        if k.name != 'Basis': k.value = 1.0 if k.name == name else 0.0

# ---------------------------------------------------------------- rig
BONES = [
    ('root', (0, 0, 0), (0, 0, .2), None),
    ('hips', (0, BY, .42), (0, BY, .52), 'root'),
    ('spine', (0, BY, .52), (0, BY, .68), 'hips'),
    ('chest', (0, BY, .68), (0, BY, .84), 'spine'),
    ('neck', (0, BY, .84), (0, BY + .01, .93 + DH), 'chest'),
    ('head', (0, 0, .93 + DH), (0, 0, 1.80 + DH), 'neck'),
    ('eye.l', (-EXe, HC.y + .43, HC.z + EZe), (-EXe, HC.y + .49, HC.z + EZe), 'head'),
    ('eye.r', (EXe, HC.y + .43, HC.z + EZe), (EXe, HC.y + .49, HC.z + EZe), 'head'),
]
for s, sd in ((-1, 'l'), (1, 'r')):
    S, E, W, G = SH[s], EL[s], WR[s], GR[s]
    BONES += [('upperarm.' + sd, tuple(S), tuple(E), 'chest'), ('lowerarm.' + sd, tuple(E), tuple(W), 'upperarm.' + sd),
              ('hand.' + sd, tuple(W), tuple(G + V((0, 0, .05))), 'lowerarm.' + sd), ('handslot.' + sd, tuple(G), tuple(G + V((0, .08, 0))), 'hand.' + sd)]
for s, sd in ((-1, 'l'), (1, 'r')):
    BONES += [('upperleg.' + sd, (s * .15, BY, .42), (s * .152, BY, .26), 'hips'), ('lowerleg.' + sd, (s * .152, BY, .26), (s * .155, BY, .11), 'upperleg.' + sd),
              ('foot.' + sd, (s * .155, BY, .11), (s * .155, BY + .12, .04), 'lowerleg.' + sd), ('toes.' + sd, (s * .155, BY + .12, .04), (s * .155, BY + .24, .03), 'foot.' + sd)]
BONES.append(('prop', (0, .45, .5), (0, .45, .75), 'root'))

def make_armature():
    arm = bpy.data.armatures.new('tarik_rig'); ob = bpy.data.objects.new('tarik_rig', arm)
    SC.collection.objects.link(ob); H.select_only([ob], ob); bpy.ops.object.mode_set(mode='EDIT')
    for name, h, t, parent in BONES:
        b = arm.edit_bones.new(name); b.head = h; b.tail = t
        if parent: b.parent = arm.edit_bones[parent]; b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in arm.bones: b.use_deform = b.name not in ('prop',)
    return ob

# ---- weights: explicit per part, no auto weights
def chain_weights(p, joints, bones, bw):
    """p: position along the chain. joints ascending, len = len(bones)-1. Returns {bone: w}."""
    a = [sstep(j - bw[k], j + bw[k], p) for k, j in enumerate(joints)]
    w = {bones[0]: 1 - a[0] if a else 1.0}
    for k in range(1, len(bones)):
        w[bones[k]] = a[k - 1] * ((1 - a[k]) if k < len(a) else 1.0)
    return w

def wt_torso(co):  # hips -> spine -> chest -> neck by height
    return chain_weights(co.z, [.50, .68, .86], ['hips', 'spine', 'chest', 'neck'], [.05, .05, .03])
def wt_apron(co):  # spine and hips only
    return chain_weights(co.z, [.44], ['hips', 'spine'], [.07])
def wt_leg(sd):
    return lambda co: chain_weights(-co.z, [-.42, -.26, -.11], ['hips', 'upperleg.' + sd, 'lowerleg.' + sd, 'foot.' + sd], [.045, .05, .03])
def wt_arm(s, shoulder=False):
    sd = 'l' if s < 0 else 'r'; P = [SH[s], EL[s], WR[s], GR[s]]
    def f(co):
        best = (1e9, 0.0)
        for i in range(3):
            a, b = P[i], P[i + 1]; ab = b - a; t = max(0.0, min(1.0, (co - a).dot(ab) / ab.length_squared)); d = (co - (a + ab * t)).length
            if d < best[0]: best = (d, i + t)
        sp = best[1]
        w = chain_weights(sp, [1.0, 2.0], ['upperarm.' + sd, 'lowerarm.' + sd, 'hand.' + sd], [.22, .15])
        if shoulder:   # ease the sleeve root into the chest so the print does not shear
            c = 1 - sstep(.0, .2, (co - P[0]).length)
            if c > 0: w = {k: v * (1 - c) for k, v in w.items()}; w['chest'] = c
        return w
    return f
def const(b): return lambda co: {b: 1.0}
def side_of(ob):
    return 1 if ob.matrix_world.translation.x >= 0 else -1

def weigh(ob, fn):
    for g in list(ob.vertex_groups): ob.vertex_groups.remove(g)
    vg = {}
    for v in ob.data.vertices:
        for b, w in fn(v.co).items():
            if w < 1e-3: continue
            if b not in vg: vg[b] = ob.vertex_groups.new(name=b)
            vg[b].add([v.index], w, 'REPLACE')

def apply_weights(rig):
    legs = {1: wt_leg('r'), -1: wt_leg('l')}
    for ob in HERO:
        n = ob.name.split('.')[0]; g = ob['grp']
        if g == 'head': weigh(ob, const('head'))
        elif n in ('blouse', 'collar', 'hips', 'neck', 'collar_knot', 'blouse_hem'): weigh(ob, const('chest') if n == 'collar' else (const('hips') if n == 'hips' else wt_torso))
        elif n in ('apron', 'apron_hem', 'apron_top', 'pocket', 'pocket_trim', 'strap_waist', 'waist_tie', 'bow_loop', 'bow_tail', 'bow_knot') or (n == 'strap' and ob.data.materials[0] is M['tie']):
            weigh(ob, wt_apron)
        elif n == 'towel': weigh(ob, const('chest'))
        elif n in ('leg', 'cuff', 'foot', 'sole', 'strap', 'strap_post'):
            c = ob.data.vertices[0].co; side = 1 if sum(v.co.x for v in ob.data.vertices) >= 0 else -1; weigh(ob, legs[side])
        elif n in ('sleeve', 'sleeve_hem', 'armsleeve', 'armsleeve_top', 'armsleeve_cuff', 'hand'):
            side = 1 if sum(v.co.x for v in ob.data.vertices) >= 0 else -1; weigh(ob, wt_arm(side, n.startswith('sleeve')))
        elif n.startswith('jug'): weigh(ob, const('handslot.r'))
        elif n.startswith('mug'): weigh(ob, const('handslot.l'))
        else: raise Exception('no weights for ' + n)

# ---------------------------------------------------------------- animation
def rest_mat(rig, name): return rig.data.bones[name].matrix_local
def world_quat_to_local(rig, pb, q):
    M3 = rest_mat(rig, pb.name).to_3x3(); return (M3.inverted() @ q.to_matrix() @ M3).to_quaternion()
def set_world_rot(rig, name, q):
    pb = rig.pose.bones[name]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = world_quat_to_local(rig, pb, q)
def axr(axis, deg): return Quaternion(V(axis), math.radians(deg))
X = (1, 0, 0); Y = (0, 1, 0); ZZ = (0, 0, 1)

def reset_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)

def aim(rig, name, target):
    """Rotate pose bone `name` (minimal rotation) so its head->tail points at world point target."""
    bpy.context.view_layer.update(); pb = rig.pose.bones[name]; m = pb.matrix.copy()
    head = m.translation; cur = (m.to_3x3() @ V((0, 1, 0))).normalized(); q = cur.rotation_difference((V(target) - head).normalized())
    pb.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ m.to_3x3().to_4x4()
    bpy.context.view_layer.update()

def arm_pose(rig, s, du, dl, hand_x=0.0):
    """du, dl: world directions for upper and lower arm."""
    sd = 'l' if s < 0 else 'r'
    Lu = (EL[s] - SH[s]).length * F; Ll = (WR[s] - EL[s]).length * F
    bpy.context.view_layer.update(); S = rig.pose.bones['upperarm.' + sd].head.copy()
    aim(rig, 'upperarm.' + sd, S + V(du).normalized() * Lu)
    El = rig.pose.bones['lowerarm.' + sd].head.copy()
    aim(rig, 'lowerarm.' + sd, El + V(dl).normalized() * Ll)

U0 = {s: (EL[s] - SH[s]).normalized() for s in (1, -1)}; L0 = {s: (WR[s] - EL[s]).normalized() for s in (1, -1)}
def rx(d, deg): return Matrix.Rotation(math.radians(deg), 3, 'X') @ d
def rz(d, deg): return Matrix.Rotation(math.radians(deg), 3, 'Z') @ d
def ry(d, deg): return Matrix.Rotation(math.radians(deg), 3, 'Y') @ d

def hips_lift(rig, dz):
    rig.pose.bones['hips'].location = rest_mat(rig, 'hips').to_3x3().inverted() @ V((0, 0, dz))

def lerpk(keys, t):
    """keys: [(t, value)] sorted; smooth interpolation."""
    for (t0, v0), (t1, v1) in zip(keys[:-1], keys[1:]):
        if t0 <= t <= t1:
            u = sstep(t0, t1, t); return v0 + (v1 - v0) * u
    return keys[-1][1]

def pose_frame(rig, t, kind):
    reset_pose(rig); s_ = math.sin(2 * math.pi * t); c_ = math.cos(2 * math.pi * t)
    A = {}
    if kind == 'idle':
        set_world_rot(rig, 'chest', axr(X, 1.5 * s_)); set_world_rot(rig, 'head', axr(X, -1.0 * s_) @ axr(ZZ, 2.0 * c_)); hips_lift(rig, .006 * s_)
        for k in (1, -1): A[k] = (rx(U0[k], 2 * s_), rx(L0[k], 3 * s_ + 1.5 * c_))
    elif kind == 'run':
        for k, sg in ((-1, 1), (1, -1)):
            sd = 'l' if k < 0 else 'r'
            set_world_rot(rig, 'upperleg.' + sd, axr(X, 34 * s_ * sg)); set_world_rot(rig, 'lowerleg.' + sd, axr(X, -48 * max(0.0, -s_ * sg)))
            set_world_rot(rig, 'foot.' + sd, axr(X, 16 * max(0.0, -s_ * sg)))
            A[k] = (rx(U0[k], 20 * s_ * -sg), rx(L0[k], 28 * s_ * -sg + 10))
        set_world_rot(rig, 'chest', axr(X, 5) @ axr(ZZ, 4 * s_)); set_world_rot(rig, 'head', axr(X, -4) @ axr(ZZ, -3 * s_)); set_world_rot(rig, 'spine', axr(X, 3))
        hips_lift(rig, .03 * abs(s_) - .012)
    elif kind == 'attack':   # raise the jug high behind, whip it down in front (pull the tea)
        a1 = lerpk([(0, 0), (.33, 100), (.55, 20), (1.0, 0)], t); a2 = lerpk([(0, 0), (.33, 40), (.55, -10), (1.0, 0)], t)
        lean = lerpk([(0, 0), (.33, -8), (.55, 10), (1.0, 0)], t)
        set_world_rot(rig, 'chest', axr(X, lean)); set_world_rot(rig, 'spine', axr(X, lean * .5)); set_world_rot(rig, 'head', axr(X, -lean * .5))
        hips_lift(rig, -.03 if .33 <= t < .7 else 0.0)
        A[1] = (rx(ry(U0[1], -30), a1), rx(ry(L0[1], -30), a1 + a2 * .45)); A[-1] = (rx(U0[-1], -a1 * .2 + 5), rx(L0[-1], a2 * -.1))
    elif kind == 'ult':   # both arms flung up wide, head back, tea held high
        set_world_rot(rig, 'chest', axr(X, -4)); set_world_rot(rig, 'head', axr(X, -8)); set_world_rot(rig, 'spine', axr(X, -2))
        A[1] = (V((.92, .0, .38)), V((.75, .0, .66))); A[-1] = (V((-.92, .0, .38)), V((-.75, .0, .66)))
    for k, (du, dl) in A.items(): arm_pose(rig, k, du, dl)
    for k in (1, -1):   # keep the jug and mug upright
        sd = 'l' if k < 0 else 'r'
        bpy.context.view_layer.update()
        hb = rig.pose.bones['hand.' + sd]; cur = (hb.matrix.to_3x3() @ V((0, 1, 0))).normalized()
        aim(rig, 'hand.' + sd, hb.head + (V((0, .0, 1)) * .6 + cur * .4))

ANIM_BONES = ['hips', 'spine', 'chest', 'neck', 'head', 'upperarm.l', 'lowerarm.l', 'hand.l', 'upperarm.r', 'lowerarm.r', 'hand.r',
              'upperleg.l', 'lowerleg.l', 'foot.l', 'upperleg.r', 'lowerleg.r', 'foot.r']

def make_action(rig, name, kind, frames, loop=True):
    act = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act
    for f in range(frames + 1):
        t = (f % frames) / frames if loop else min(f, frames) / frames
        SC.frame_set(f); pose_frame(rig, t, kind)
        for n in ANIM_BONES:
            pb = rig.pose.bones[n]; pb.keyframe_insert('rotation_quaternion', frame=f)
            if n == 'hips': pb.keyframe_insert('location', frame=f)
    act.frame_range = (0, frames); act.use_frame_range = True; act.use_fake_user = True; return act

# ---------------------------------------------------------------- stage (copied from ahma_toy.py)
def look_at(o, target): o.rotation_euler = (V(target) - o.location).to_track_quat('-Z', 'Y').to_euler()

def stage():
    w = bpy.data.worlds.new('World'); SC.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (.5, .62, .85, 1); bg.inputs[1].default_value = .45
    def lamp(name, kind, loc, energy, col, size=2.0, tgt=(0, .2, 1.1)):
        d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = col
        if kind == 'AREA': d.size = size
        else: d.spot_size = 1.0; d.spot_blend = .7; d.shadow_soft_size = .3
        o = bpy.data.objects.new(name, d); SC.collection.objects.link(o); o.location = loc; look_at(o, tgt); return o
    lamp('key', 'AREA', (1.9, 4.9, 6.0), 1800, (1.0, .79, .54), 2.2)
    lamp('fill', 'AREA', (-5.0, 3.5, 2.2), 420, (.62, .76, 1.0), 5.0)
    lamp('rim', 'SPOT', (-3.2, -4.6, 3.8), 5200, (1.0, .78, .52))
    prof = [(14, 0)] + [(-5 - 4 * math.sin(a), 4 - 4 * math.cos(a)) for a in [math.pi / 2 * i / 16 for i in range(17)]] + [(-9, 16)]
    vs = [(x, y, z) for (y, z) in prof for x in (-30, 30)]; fs = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(prof) - 1)]
    me = bpy.data.meshes.new('cyc'); me.from_pydata(vs, [], fs); me.polygons.foreach_set('use_smooth', [True] * len(fs))
    m = bpy.data.materials.new('cyc'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (.46, .44, .42, 1); b.inputs['Roughness'].default_value = .85
    me.materials.append(m); SC.collection.objects.link(bpy.data.objects.new('cyc', me))
    SC.render.engine = 'BLENDER_EEVEE'; SC.eevee.taa_render_samples = 16 if QUICK else 96
    SC.view_settings.view_transform = 'AgX'; SC.view_settings.look = 'AgX - Punchy'
    SC.render.image_settings.file_format = 'PNG'; SC.render.film_transparent = False
    for a, v in (('use_shadows', True), ('use_raytracing', True)):
        try: setattr(SC.eevee, a, v)
        except Exception: pass
    try: SC.eevee.shadow_ray_count = 3; SC.eevee.shadow_step_count = 12
    except Exception: pass
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'HORIZONTAL'; cam = bpy.data.objects.new('cam', cd)
    SC.collection.objects.link(cam); SC.camera = cam; return cam

def shoot(cam, path, w, h, az, dist, target, width_m, cam_z=None):
    SC.render.resolution_x = w; SC.render.resolution_y = h; t = V(target); a = math.radians(az)
    cam.location = (t.x - dist * math.sin(a), t.y + dist * math.cos(a), cam_z if cam_z is not None else t.z)
    cam.data.lens = dist * 36 / width_m; look_at(cam, t); SC.render.filepath = path; bpy.ops.render.render(write_still=True)

def row(paths, out, cols=None, width=1600):
    ims = []
    for p in paths:
        im = bpy.data.images.load(p); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); ims.append(a.reshape(h, w, 4))
    cols = cols or len(ims); rows = []
    for r in range((len(ims) + cols - 1) // cols):
        rr = ims[r * cols:(r + 1) * cols]
        while len(rr) < cols: rr.append(np.zeros_like(ims[0]))
        rows.append(np.concatenate(rr, axis=1))
    a = np.concatenate(rows[::-1], axis=0); h, w = a.shape[:2]
    o = bpy.data.images.new('row', w, h, alpha=False); o.pixels.foreach_set(a.ravel()); o.filepath_raw = out; o.file_format = 'PNG'; o.save()

# ---------------------------------------------------------------- main: build
def stage_build():
    global GRP
    GRP[0] = 'body'; build_body(); build_apron(); build_towel(); build_arms(); build_props()
    GRP[0] = 'head'; build_head(); face = build_face()
    # cleanup: bake any object transforms, then weights, then join into four meshes
    rig = make_armature()
    for o in HERO:
        if o.matrix_world != Matrix.Identity(4): H.apply_transforms(o)
    apply_weights(rig)
    def bucket(o):
        n = o.name.split('.')[0]
        if o['grp'] == 'head': return 'tarik_head'
        if n.startswith('jug'): return 'tarik_jug'
        if n.startswith('mug'): return 'tarik_mug'
        return 'tarik_body'
    for o in sorted(HERO, key=lambda o: -len(o.data.polygons))[:14]: print('[parts]', o.name, sum(len(p.vertices)-2 for p in o.data.polygons))
    groups = {}
    for o in HERO: groups.setdefault(bucket(o), []).append(o)
    final = {}
    for name, obs in groups.items():
        if name == 'tarik_head': obs.remove(face); obs.insert(0, face)   # face (the shape keys) is the active object
        final[name] = H.join(obs, name) if len(obs) > 1 else obs[0]
        final[name].name = name
    for name, ob in final.items():
        for o in ob.data.materials: pass
        ob.parent = rig; m = ob.modifiers.new('Armature', 'ARMATURE'); m.object = rig
        for p in ob.data.polygons: p.use_smooth = True
    head = final['tarik_head']
    print('[build] shape keys', [k.name for k in head.data.shape_keys.key_blocks])
    for n, ob in final.items(): print('[build]', n, H.tri_count(ob), 'tris')
    print('[build] TOTAL TRIS', sum(H.tri_count(o) for o in final.values()))
    # uniform scale to the 1.80 m target: verts, shape keys and rest bones (feet stay at z=0)
    global F
    F = 1.80 / max(v.co.z for ob in final.values() for v in ob.data.vertices); SC['F'] = F; print('[build] scale F', round(F, 4))
    for ob in final.values():
        for v in ob.data.vertices: v.co *= F
        if ob.data.shape_keys:
            for kb in ob.data.shape_keys.key_blocks:
                for p in kb.data: p.co *= F
    H.select_only([rig], rig); bpy.ops.object.mode_set(mode='EDIT')
    for b in rig.data.edit_bones: b.head *= F; b.tail *= F
    bpy.ops.object.mode_set(mode='OBJECT')
    # spouts for the tea stream
    for name, pos, bone in (('spout_jug', (JUG_O + LIP) * F, 'handslot.r'), ('spout_mug', (MUG_O + V((0, 0, .24))) * F, 'handslot.l')):
        e = bpy.data.objects.new(name, None); e.empty_display_type = 'SPHERE'; e.empty_display_size = .03; SC.collection.objects.link(e)
        e.parent = rig; e.parent_type = 'BONE'; e.parent_bone = bone; bpy.context.view_layer.update(); e.matrix_world = Matrix.Translation(pos)
    # clips
    SC.render.fps = FPS
    acts = [make_action(rig, 'idle', 'idle', 60), make_action(rig, 'run', 'run', 24), make_action(rig, 'attack', 'attack', 18), make_action(rig, 'ult', 'ult', 2, loop=False)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    reset_pose(rig)
    for k in head.data.shape_keys.key_blocks: k.value = 0.0
    # bounds
    lo = V((1e9,) * 3); hi = V((-1e9,) * 3)
    for ob in final.values():
        for v in ob.data.vertices:
            lo = V(map(min, lo, v.co)); hi = V(map(max, hi, v.co))
    print('[build] bounds', tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi), 'height', round(hi.z - lo.z, 3))
    stage()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    export(rig, list(final.values()))

def export(rig, meshes):
    objs = meshes + [rig] + [o for o in bpy.data.objects if o.name.startswith('spout_')]
    H.select_only(objs, rig); os.makedirs(os.path.dirname(GLB), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=GLB, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
                              export_animations=True, export_animation_mode='ACTIONS', export_nla_strips=True, export_skins=True, export_def_bones=False,
                              export_morph=True, export_morph_normal=False, export_image_format='AUTO', export_materials='EXPORT', export_texcoords=True,
                              export_normals=True, export_tangents=False, export_all_influences=False, export_optimize_animation_size=True)
    print('[export] wrote', GLB, os.path.getsize(GLB) // 1024, 'KB')

# ---------------------------------------------------------------- shots
def stage_shots():
    global SC
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    SC = bpy.context.scene; F = SC['F']
    rig = bpy.data.objects['tarik_rig']; head = bpy.data.objects['tarik_head']; cam = bpy.data.objects['cam']
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith('tarik'): o.hide_render = False
    def play(name, frame): rig.animation_data.action = bpy.data.actions[name]; SC.frame_set(frame)
    rig.animation_data_create(); play('idle', 0)
    if 'beauty' in ARGS or 'all' in ARGS:
        set_expr(head, 'smile'); shoot(cam, os.path.join(OUT, 'beauty.png'), 1600, 1600, 28, 8, (0, .2, .98), 2.5, cam_z=.95)
    if 'face' in ARGS: set_expr(head, 'smile'); shoot(cam, os.path.join(TMP, 'face.png'), 1200, 1200, 25, 6, (0, .05, HC.z * F - .02), 1.5)
    if 'turn' in ARGS or 'all' in ARGS:
        set_expr(head, 'smile'); ps = []
        for i, ang in enumerate((0, 90, 180)):
            rig.rotation_euler = (0, 0, math.radians(-ang)); bpy.context.view_layer.update()
            t = Matrix.Rotation(math.radians(-ang), 3, 'Z') @ V((0, .2, .98)); p = os.path.join(TMP, 't_%d.png' % i); ps.append(p)
            shoot(cam, p, 534, 800, 0, 9, t, 1.9)
        rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(OUT, 'turnaround.png'))
    if 'expr' in ARGS or 'all' in ARGS:
        ps = []
        for name in ('smile', 'angry', 'grin', 'ult'):
            set_expr(head, name); p = os.path.join(TMP, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, 0, HC.z * F - .02), 1.3)
        row(ps, os.path.join(OUT, 'expressions.png')); set_expr(head, 'smile')
    if 'anim' in ARGS or 'all' in ARGS:
        ps = []
        for name, n, frames in (('idle', 60, (0, 15, 30, 45)), ('run', 24, (0, 6, 12, 18)), ('attack', 18, (0, 6, 10, 15)), ('ult', 2, (0, 1, 2, 2))):
            for i, f in enumerate(frames):
                play(name, f); set_expr(head, 'ult' if name == 'ult' else ('angry' if name == 'attack' else 'smile'))
                p = os.path.join(TMP, 'a_%s_%d.png' % (name, i)); ps.append(p)
                shoot(cam, p, 400, 520, 25, 8.5, (0, .15, .98), 2.2)
        play('idle', 0); row(ps, os.path.join(OUT, 'anim_sheet.png'), cols=4)

def stage_verify():
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps = FPS
    bpy.ops.import_scene.gltf(filepath=GLB)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Icosphere']
    rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    lo = V((1e9,) * 3); hi = V((-1e9,) * 3)
    for o in meshes:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co; lo = V(map(min, lo, w)); hi = V(map(max, hi, w))
    print(f'[verify] tris {sum(H.tri_count(o) for o in meshes)}; X {lo.x:.3f}..{hi.x:.3f} height {hi.z - lo.z:.3f} Y {lo.y:.3f}..{hi.y:.3f}')
    print('[verify] bones', len(rig.data.bones), [b.name for b in rig.data.bones])
    for o in meshes:
        if o.data.shape_keys: print('[verify] morphs on', o.name, [k.name for k in o.data.shape_keys.key_blocks][1:])
    print('[verify] meshes', [(o.name, H.tri_count(o)) for o in meshes])
    print('[verify] actions', [(a.name, tuple(a.frame_range)) for a in bpy.data.actions])
    print('[verify] others', [o.name for o in bpy.data.objects if o.type == 'EMPTY'])

if 'build' in ARGS: stage_build()
if 'shots' in ARGS: stage_shots()
if 'verify' in ARGS: stage_verify()
