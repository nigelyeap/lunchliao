"""Ah Ma, Pixar-film style frame (style id: pixar).
  /opt/homebrew/bin/blender -b -P tools/blender/styles/pixar/ahma_pixar.py -- build shots [hero face expressions turn]
build saves ahma_pixar.blend next to this file. shots re-opens it and renders into shots/styles/pixar/.
Blender axes: Z up, she faces +Y. Game scale: about 2.13 m tall."""
import bpy, bmesh, math, os, sys, random
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'blender', 'heroes'))
from hero_lib import Soup, apply_mod, tri_count, decimate, shade_smooth, boolean_cut, srgb, override
import render_lib as RL

BLEND = os.path.join(HERE, 'ahma_pixar.blend')
SHOTS = os.path.join(ROOT, 'shots', 'styles', 'pixar')
TMP = os.environ.get('PIXAR_TMP', '/tmp/lunchliao-scratch')
DECIMATE = os.environ.get('PIXAR_DECIMATE', '1') == '1'

V = lambda *a: Vector(a)

# ---------------- landmarks ----------------
R_EYE = 0.078; EX = 0.152; EYE_Y = 0.283; EYE_Z = 1.60
A_EYE = 0.068; HU = 0.047; HL = 0.037; TILT = 0.06      # eye opening: half width, upper and lower heights
ZM = 1.405; XC = 0.105; SM = 0.9                          # mouth line height, corner x, smile curvature
HINGE = np.array([0.0, 0.0, 1.50])
HX = 0.40; HZ = 0.74; RG = 0.031; GY = 0.33               # walker grip: x, height, foam radius, hand y
HEAD_PIVOT = V(0, 0, 1.22)
EXPRS = ('smile', 'angry', 'grin', 'ult')

PRM = dict(
    smile=dict(jaw=0.0, c_up=0.032, c_out=0.02, lip_up=-0.003, lip_dn=-0.004, cheek=0.016, lid_u=1.0, lid_in=0.0, lid_l=0.8,
               brow_in=0.006, brow_out=0.004, brow_dx=0.0, teeth=0.0),
    angry=dict(jaw=0.0, c_up=-0.036, c_out=-0.006, lip_up=-0.003, lip_dn=-0.004, cheek=0.0, lid_u=0.86, lid_in=-0.42, lid_l=0.78,
               brow_in=-0.06, brow_out=0.014, brow_dx=0.014, teeth=0.0),
    grin=dict(jaw=0.09, c_up=0.04, c_out=0.032, lip_up=0.016, lip_dn=0.0, cheek=0.03, lid_u=0.92, lid_in=0.0, lid_l=0.42,
              brow_in=0.018, brow_out=0.012, brow_dx=0.0, teeth=0.018),
    ult=dict(jaw=0.36, c_up=-0.018, c_out=-0.006, lip_up=0.02, lip_dn=0.006, cheek=0.008, lid_u=1.12, lid_in=-0.3, lid_l=0.92,
             brow_in=-0.04, brow_out=0.03, brow_dx=0.01, teeth=0.014),
)

COL = {k: srgb(v) for k, v in dict(
    skin='#E9B994', blush='#E67F6C', lip='#B9525F', mouth='#4E1A20', tongue='#D8707A', teeth='#F6F1E6',
    hair_root='#2C2930', hair_tip='#8E8B97', brow='#3A3640', lash='#2A2024',
    blouse='#AEB7E8', petal='#FBF3E6', petal2='#EE8FA8', centre='#F2BE48', leaf='#6FAE86', piping='#96397A',
    slacks='#2B3048', slipper='#D7322E', metal='#C9CDD2', rubber='#34363A', foam='#4A4D55', basket='#D2332D',
    jade='#3FA06E', gold='#E0B04A', sclera='#F1ECE6', onion_w='#F1F1DC', onion_g='#5FA548', orange='#F08A1C',
).items()}

def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

# =====================================================================================
# mesh helpers
# =====================================================================================
def new_obj(name, verts, faces, smooth=True, fix=True):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    if fix: fix_normals(ob)
    if smooth: shade_smooth(ob)
    return ob

def fix_normals(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()

def get_co(ob):
    a = np.empty(len(ob.data.vertices) * 3, np.float32); ob.data.vertices.foreach_get('co', a); return a.reshape(-1, 3).astype(np.float64)

def set_co(ob, P):
    ob.data.vertices.foreach_set('co', P.astype(np.float32).ravel()); ob.data.update()

def bvh_of(ob):
    me = ob.data
    return BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])

def remesh_ob(ob, voxel, smooth=0, factor=0.5):
    m = ob.modifiers.new('remesh', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = voxel; m.use_smooth_shade = True; apply_mod(ob, m)
    if smooth:
        s = ob.modifiers.new('smooth', 'SMOOTH'); s.factor = factor; s.iterations = smooth; apply_mod(ob, s)
    shade_smooth(ob); return ob

def dec(ob, n, vg=None):
    """Decimate to n tris, then copy the smooth normals of the dense mesh back on (the vertex-level stand-in for a baked normal map)."""
    if not DECIMATE or tri_count(ob) <= n: return ob
    hi = ob.copy(); hi.data = ob.data.copy(); bpy.context.scene.collection.objects.link(hi)
    if vg:   # thin out the part nobody sees first (weight 1 = free to collapse, 0 = protected)
        m = ob.modifiers.new('dec', 'DECIMATE'); m.ratio = 0.04; m.vertex_group = vg; apply_mod(ob, m)
    if tri_count(ob) > n:
        m = ob.modifiers.new('dec', 'DECIMATE'); m.ratio = n / tri_count(ob); apply_mod(ob, m)
    dt = ob.modifiers.new('nrm', 'DATA_TRANSFER'); dt.object = hi; dt.use_loop_data = True; dt.data_types_loops = {'CUSTOM_NORMAL'}; dt.loop_mapping = 'POLYINTERP_NEAREST'
    apply_mod(ob, dt); bpy.data.objects.remove(hi, do_unlink=True); return ob

def add_keys(ob, variants):
    ob.shape_key_add(name='Basis')
    for k, arr in variants.items():
        kb = ob.shape_key_add(name=k); kb.data.foreach_set('co', np.asarray(arr, np.float32).ravel())

def set_mat(ob, m):
    ob.data.materials.clear(); ob.data.materials.append(m)

def fillet(pts, rad, n=6):
    pts = [Vector(p) for p in pts]; out = [pts[0]]
    for i in range(1, len(pts) - 1):
        c = pts[i]; d1 = (pts[i - 1] - c); d2 = (pts[i + 1] - c)
        r = min(rad, d1.length * .45, d2.length * .45)
        a = c + d1.normalized() * r; b = c + d2.normalized() * r
        for k in range(n + 1):
            t = k / n; out.append((1 - t) ** 2 * a + 2 * t * (1 - t) * c + t * t * b)
    out.append(pts[-1]); return out

def tube(name, pts, r, seg=10, closed=False, fx=1.0, fy=1.0, up=None):
    """Sweep an ellipse along a polyline. fx scales along the frame normal (starts near `up`), fy along the binormal."""
    pts = [Vector(p) for p in pts]; n = len(pts)
    rs = list(r) if hasattr(r, '__len__') else [r] * n
    T = []
    for i in range(n):
        a = pts[i - 1] if (i > 0 or closed) else pts[i]; b = pts[(i + 1) % n] if (i < n - 1 or closed) else pts[i]
        T.append((b - a).normalized())
    upv = Vector(up) if up is not None else (Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0)))
    N = (upv - T[0] * upv.dot(T[0])).normalized()
    verts = []; faces = []
    for i in range(n):
        if up is not None: N = (upv - T[i] * upv.dot(T[i])).normalized()
        else: N = (N - T[i] * N.dot(T[i])).normalized()
        B = T[i].cross(N)
        for k in range(seg):
            a = 2 * math.pi * k / seg
            verts.append(pts[i] + (N * math.cos(a) * fx + B * math.sin(a) * fy) * rs[i])
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        for k in range(seg):
            k2 = (k + 1) % seg; faces.append((i * seg + k, i * seg + k2, j * seg + k2, j * seg + k))
    if not closed:
        verts.append(pts[0] - T[0] * rs[0] * .6 * min(fx, fy)); c0 = len(verts) - 1
        verts.append(pts[-1] + T[-1] * rs[-1] * .6 * min(fx, fy)); c1 = len(verts) - 1
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((c0, k2, k)); faces.append((c1, (n - 1) * seg + k, (n - 1) * seg + k2))
    return new_obj(name, verts, faces)

def ring_pts(c, R, axis='y', n=40, rx=1.0, rz=1.0):
    c = Vector(c); out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        if axis == 'y': out.append(c + V(R * rx * math.cos(a), 0, R * rz * math.sin(a)))
        elif axis == 'z': out.append(c + V(R * rx * math.cos(a), R * rz * math.sin(a), 0))
        else: out.append(c + V(0, R * rx * math.cos(a), R * rz * math.sin(a)))
    return out

def uvsphere(name, c, r, seg=24, rings=14, scale=(1, 1, 1)):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    for v in bm.verts: v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) + Vector(c)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); shade_smooth(ob); return ob

def join(objs, name):
    for o in bpy.data.objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs):
        bpy.ops.object.join()
    objs[0].name = name; objs[0].data.name = name; return objs[0]

def soup_cone(s, c0, c1, r0, r1, sy=1.0, seg=48):
    """Capped elliptical cone along Z from c0 to c1 added to a Soup."""
    g = bmesh.ops.create_cone(s.bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=c1[2] - c0[2])
    for v in g['verts']: v.co = Vector((v.co.x, v.co.y * sy, v.co.z + (c0[2] + c1[2]) * .5)) + Vector((c0[0], c0[1], 0))

# =====================================================================================
# materials
# =====================================================================================
def principled(name, col, rough=0.5, metal=0.0, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    for k, v in kw.items(): b.inputs[k].default_value = v
    return m

def mixc(nt, fac, a, b):
    n = nt.nodes.new('ShaderNodeMix'); n.data_type = 'RGBA'
    for sock, val in ((n.inputs[0], fac), (n.inputs[6], a), (n.inputs[7], b)):
        if hasattr(val, 'links') or hasattr(val, 'is_linked'): nt.links.new(val, sock)
        elif isinstance(val, (int, float)): sock.default_value = val
        else: sock.default_value = (*val, 1)
    return n.outputs[2]

def math_node(nt, op, a, b=None):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op
    for sock, val in ((n.inputs[0], a), (n.inputs[1], b)):
        if val is None: continue
        if hasattr(val, 'is_linked'): nt.links.new(val, sock)
        else: sock.default_value = val
    return n.outputs[0]

def make_materials():
    M = {}
    SSS = {'Subsurface Weight': 0.35, 'Subsurface Radius': (1.0, 0.36, 0.2), 'Subsurface Scale': 0.035}
    # skin: flat base, soft blush, lips and mouth interior from the 'mask' colour attribute (R blush, G lip, B inner)
    m = principled('skin', COL['skin'], rough=0.46, **SSS); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'mask'
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(at.outputs['Color'], sep.inputs[0])
    c = mixc(nt, math_node(nt, 'MULTIPLY', sep.outputs[0], 0.8), COL['skin'], COL['blush'])
    c = mixc(nt, math_node(nt, 'MULTIPLY', sep.outputs[1], 1.0), c, COL['lip'])
    c = mixc(nt, sep.outputs[2], c, COL['mouth'])
    nt.links.new(c, b.inputs['Base Color'])
    nt.links.new(math_node(nt, 'SUBTRACT', 0.46, math_node(nt, 'MULTIPLY', sep.outputs[1], 0.14)), b.inputs['Roughness'])
    M['skin'] = m
    # hair: root to tip gradient from the 'tip' attribute
    m = principled('hair', COL['hair_root'], rough=0.42); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'tip'
    nt.links.new(mixc(nt, at.outputs['Fac'], COL['hair_root'], COL['hair_tip']), b.inputs['Base Color'])
    b.inputs['Sheen Weight'].default_value = 0.25; b.inputs['Sheen Roughness'].default_value = 0.4
    M['hair'] = m
    M['brow'] = principled('brow', COL['brow'], rough=0.55)
    M['lash'] = principled('lash', COL['lash'], rough=0.5)
    # eye: procedural iris on object coords, glossy coat
    m = principled('eye', COL['sclera'], rough=0.07); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sp.inputs[0])
    cb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(sp.outputs['X'], cb.inputs['X']); nt.links.new(sp.outputs['Z'], cb.inputs['Z'])
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(cb.outputs[0], ln.inputs[0])
    r = math_node(nt, 'DIVIDE', ln.outputs['Value'], R_EYE)
    ramp = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(r, ramp.inputs[0]); el = ramp.color_ramp.elements
    stops = [(0.0, '#050303'), (0.185, '#050303'), (0.225, '#7A4A28'), (0.40, '#4A2A17'), (0.485, '#160C08'), (0.525, '#F1ECE6'), (1.0, '#E3CFC6')]
    el[0].position = stops[0][0]; el[0].color = (*srgb(stops[0][1]), 1); el[1].position = stops[-1][0]; el[1].color = (*srgb(stops[-1][1]), 1)
    for p, h in stops[1:-1]:
        e = el.new(p); e.color = (*srgb(h), 1)
    # lighter amber in the lower half of the iris, the way a film iris catches light
    low = math_node(nt, 'MULTIPLY', math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', sp.outputs['Z'], -1.0 / (R_EYE * 0.45)), 0.25), 1.0)
    low_n = nt.nodes.new('ShaderNodeClamp'); nt.links.new(low, low_n.inputs[0])
    band = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(r, band.inputs[0]); be = band.color_ramp.elements
    be[0].position = 0.2; be[0].color = (0, 0, 0, 1); be[1].position = 0.30; be[1].color = (1, 1, 1, 1)
    e = be.new(0.42); e.color = (1, 1, 1, 1); e = be.new(0.48); e.color = (0, 0, 0, 1)
    fac = math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', low_n.outputs[0], band.outputs['Color']), 0.75)
    c = mixc(nt, fac, ramp.outputs['Color'], srgb('#B67A3C'))
    front = math_node(nt, 'GREATER_THAN', sp.outputs['Y'], 0.0)
    c = mixc(nt, front, COL['sclera'], c)
    nt.links.new(c, b.inputs['Base Color'])
    b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.02
    b.inputs['Subsurface Weight'].default_value = 0.08; b.inputs['Subsurface Radius'].default_value = (1, .5, .4); b.inputs['Subsurface Scale'].default_value = 0.02
    M['eye'] = m
    M['teeth'] = principled('teeth', COL['teeth'], rough=0.25, **{'Subsurface Weight': 0.15, 'Subsurface Radius': (1, .8, .6), 'Subsurface Scale': 0.02})
    M['tongue'] = principled('tongue', COL['tongue'], rough=0.35, **{'Subsurface Weight': 0.3, 'Subsurface Radius': (1, .3, .2), 'Subsurface Scale': 0.03})
    cloth = {'Sheen Weight': 0.12, 'Sheen Roughness': 0.5}
    for k in ('blouse', 'petal', 'petal2', 'centre', 'leaf', 'piping'):
        M[k] = principled(k, COL[k], rough=0.72, **cloth)
    M['slacks'] = principled('slacks', COL['slacks'], rough=0.8, **cloth)
    M['slipper'] = principled('slipper', COL['slipper'], rough=0.5)
    M['metal'] = principled('metal', COL['metal'], rough=0.28, metal=1.0)
    M['rubber'] = principled('rubber', COL['rubber'], rough=0.75)
    M['foam'] = principled('foam', COL['foam'], rough=0.9)
    M['basket'] = principled('basket', COL['basket'], rough=0.38, **{'Coat Weight': 0.3, 'Coat Roughness': 0.2})
    M['jade'] = principled('jade', COL['jade'], rough=0.12, **{'Subsurface Weight': 0.6, 'Subsurface Radius': (0.3, 1.0, 0.5), 'Subsurface Scale': 0.03, 'Coat Weight': 0.6})
    M['gold'] = principled('gold', COL['gold'], rough=0.22, metal=1.0)
    M['onion_w'] = principled('onion_w', COL['onion_w'], rough=0.45); M['onion_g'] = principled('onion_g', COL['onion_g'], rough=0.5)
    M['orange'] = principled('orange', COL['orange'], rough=0.45, **{'Subsurface Weight': 0.2, 'Subsurface Radius': (1, .5, .1), 'Subsurface Scale': 0.02})
    # lens: mostly clear, glossy reflection that grows at grazing angles
    m = bpy.data.materials.new('lens'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); tr.inputs[0].default_value = (0.97, 0.99, 1, 1)
    gl = nt.nodes.new('ShaderNodeBsdfPrincipled'); gl.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1); gl.inputs['Roughness'].default_value = 0.03
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.25
    f = math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', lw.outputs['Fresnel'], 0.3), 0.03)
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(f, mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    try: m.surface_render_method = 'BLENDED'
    except Exception: m.blend_method = 'BLEND'
    M['lens'] = m
    return M

# =====================================================================================
# head
# =====================================================================================
def eye_c(s): return V(s * EX, EYE_Y, EYE_Z)

def lid_curves(xl, s, ku=1.0, kl=1.0):
    u = np.clip(xl / A_EYE, -1, 1); base = np.maximum(1 - u * u, 0); tz = TILT * xl * s
    return HU * ku * base ** 0.55 + tz, -HL * kl * base ** 0.6 + tz

def lid_delta(P, s, prm):
    """Slide the lid skin over the eyeball so the rims land on the expression's lid curves. Returns an (N,3) delta."""
    ec = np.array(eye_c(s)); p = P - ec; x, y, z = p.T; rho = np.linalg.norm(p, axis=1)
    u = np.clip(x / A_EYE, -1, 1); inner = 0.5 - 0.5 * s * u
    zu, zl = lid_curves(x, s)
    zu2, zl2 = lid_curves(x, s, prm['lid_u'] + prm['lid_in'] * inner, prm['lid_l'])
    ZT, ZB = 0.118, -0.105
    t = np.clip((z - zu) / (ZT - zu), 0, 1); zn_u = zu2 + t * (ZT - zu2) + np.minimum(z - zu, 0)
    tl = np.clip((zl - z) / (zl - ZB), 0, 1); zn_l = zl2 - tl * (zl2 - ZB) + np.maximum(z - zl, 0)
    zn = np.where(z >= 0.5 * (zu + zl), zn_u, zn_l)
    w = (1 - sstep(R_EYE + 0.03, R_EYE + 0.055, rho)) * sstep(0.0, 0.02, y) * (rho > R_EYE * 0.9)
    yn = np.sqrt(np.maximum(rho * rho - x * x - zn * zn, 1e-6))
    D = np.zeros_like(P); D[:, 2] = (zn - z) * w; D[:, 1] = (yn - y) * w
    return D

def jaw_rot(P, ang):
    rel = P - HINGE; c, sn = math.cos(-ang), math.sin(-ang)
    out = P.copy(); out[:, 1] = HINGE[1] + rel[:, 1] * c - rel[:, 2] * sn; out[:, 2] = HINGE[2] + rel[:, 1] * sn + rel[:, 2] * c
    return out

def deform_head(P, prm, lipy):
    x, y, z = P.T; ax = np.abs(x); zs = ZM + SM * x * x; d = z - zs
    D = np.zeros_like(P)
    # keep everything but the lid slide away from the eye sockets, so nothing can cut into an eyeball
    eyefree = np.ones(len(P))
    for s in (-1, 1): eyefree *= sstep(R_EYE + 0.035, R_EYE + 0.08, np.linalg.norm(P - np.array(eye_c(s)), axis=1))
    # jaw: lower lip and chin follow the hinge, the corners take half, the cheeks stretch
    cc = np.where(ax <= XC, sstep(XC * 0.3, XC, ax), 1.0); tau = 0.035 + 0.7 * np.maximum(ax - XC, 0)
    w = np.where(d < 0, 1 - 0.5 * cc * (1 - sstep(0, tau, -d)), 0.5 * cc * (1 - sstep(0, tau, d)))
    w *= sstep(-0.02, 0.16, y) * (1 - sstep(0.24, 0.38, ax)) * sstep(1.15, 1.25, z) * eyefree
    D += w[:, None] * (jaw_rot(P, prm['jaw']) - P)
    cz = ZM + SM * XC * XC
    for s in (-1, 1):
        cp = np.array([s * XC, lipy(XC), cz]); g = np.exp(-np.sum((P - cp) ** 2, axis=1) / (2 * 0.045 ** 2)) * eyefree
        D += g[:, None] * np.array([s * prm['c_out'], -0.4 * abs(prm['c_out']), prm['c_up']])
        cp = np.array([s * 0.21, 0.27, 1.47]); g = np.exp(-np.sum((P - cp) ** 2, axis=1) / (2 * 0.07 ** 2)) * eyefree
        D += g[:, None] * np.array([s * 0.2, 0.5, 1.0]) * prm['cheek']
    gx = np.exp(-(x / 0.085) ** 2) * sstep(0.12, 0.2, y)
    D[:, 2] += prm['lip_up'] * gx * (d > 0) * (1 - sstep(0, 0.06, d))
    D[:, 2] -= prm['lip_dn'] * gx * (d < 0) * (1 - sstep(0, 0.06, -d))
    for s in (-1, 1): D += lid_delta(P, s, prm)
    Q = P + D
    for s in (-1, 1):   # final guard: never inside the eyeball
        ec = np.array(eye_c(s)); p = Q - ec; rho = np.linalg.norm(p, axis=1); bad = rho < R_EYE + 0.005
        Q[bad] = ec + p[bad] / rho[bad, None] * (R_EYE + 0.005)
    return Q

def build_head(M):
    b = Soup('base')                                                      # big soft masses first, smoothed hard
    b.ellipsoid((0, 0, 1.66), (0.39, 0.37, 0.36), seg=48)                 # cranium
    b.ellipsoid((0, 0.04, 1.47), (0.378, 0.33, 0.25), seg=48)             # wide soft lower face
    b.ellipsoid((0, 0.22, 1.41), (0.15, 0.125, 0.10))                     # muzzle
    b.sphere((0, 0.265, 1.325), 0.075)                                    # chin
    b.sphere((0, 0.12, 1.31), 0.10)                                       # soft under-chin
    b.capsule((0, -0.02, 1.10), (0, 0.0, 1.40), 0.14)                     # neck
    for k in (-1, 1):
        b.sphere((k * 0.185, 0.20, 1.47), 0.15, seg=32)                   # cheeks
        b.sphere((k * 0.195, 0.15, 1.39), 0.112, seg=32)                  # jowls
    base, _ = b.remesh(voxel=0.01, smooth=30, smooth_factor=0.7)
    P = get_co(base); k = 0.385 / np.abs(P[:, 0]).max(); set_co(base, np.array([0, 0, 1.5]) + (P - np.array([0, 0, 1.5])) * k); print('base rescale %.3f' % k)
    s = Soup('head'); s.bm.from_mesh(base.data); bpy.data.objects.remove(base, do_unlink=True)
    s.ellipsoid((0, 0.325, ZM - 0.022), (0.088, 0.03, 0.02))              # lower lip
    s.ellipsoid((0, 0.33, ZM + 0.018), (0.098, 0.028, 0.016))             # upper lip
    s.capsule((0, 0.35, 1.61), (0, 0.395, 1.525), 0.032, 0.044)           # nose bridge
    s.sphere((0, 0.405, 1.515), 0.052)                                    # nose tip
    for k in (-1, 1):
        s.sphere(eye_c(k), R_EYE + 0.024, seg=32)                         # lid bulge
        s.sphere((k * 0.048, 0.372, 1.498), 0.034)                        # alae
        s.ellipsoid((k * 0.402, -0.03, 1.555), (0.04, 0.075, 0.115), rot=Quaternion((0, 0, 1), k * 0.5))   # ears
        s.sphere((k * 0.412, -0.015, 1.455), 0.04)                         # long lobes
    head, _ = s.remesh(voxel=0.007, smooth=6, smooth_factor=0.6)
    bvh = bvh_of(head)
    xs = np.linspace(-0.12, 0.12, 13)
    ys = [bvh.ray_cast(V(x, 1.0, ZM + SM * x * x), V(0, -1, 0))[0].y for x in xs]
    co = np.polyfit(xs, ys, 2); lipy = lambda x: co[0] * x * x + co[2]
    print('lip front y0=%.3f curve=%.2f' % (co[2], co[0]))
    # cuts: eye sockets, eye openings, ear bowls, mouth slit and cavity
    for k in (-1, 1):
        c = Soup('cut'); c.sphere(eye_c(k), R_EYE + 0.006, seg=48); boolean_cut(head, c.to_object())
        ec = eye_c(k); us = np.linspace(-1, 1, 25); xl = us * A_EYE
        zu, zl = lid_curves(xl, k)
        outline = [(xl[i], zu[i]) for i in range(25)] + [(xl[i], zl[i]) for i in range(23, 0, -1)]
        n = len(outline); verts = [ec + V(x, 0.03, z) for x, z in outline] + [ec + V(x, 0.22, z) for x, z in outline]
        faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)] + [tuple(range(n)), tuple(range(n, 2 * n))]
        boolean_cut(head, new_obj('cut_eye', verts, faces, smooth=False))
        c = Soup('cut'); c.ellipsoid((k * 0.452, -0.012, 1.57), (0.03, 0.038, 0.065), rot=Quaternion((0, 0, 1), k * 0.5)); boolean_cut(head, c.to_object())
    remesh_ob(head, 0.005, smooth=2, factor=0.5)
    c = Soup('cut_mouth'); c.ellipsoid((0, lipy(0) - 0.05, ZM), (XC + 0.008, 0.12, 0.0045), seg=48)
    for v in c.bm.verts: v.co.z += SM * v.co.x ** 2
    for x in np.linspace(-0.075, 0.075, 7): c.sphere((x, lipy(x) - 0.056, ZM + SM * x * x - 0.006), 0.03, seg=16)
    c.sphere((0, lipy(0) - 0.11, ZM - 0.015), 0.055)
    cut, _ = c.remesh(voxel=0.003, smooth=0); boolean_cut(head, cut)   # no remesh after this, a voxel pass would weld the lips shut
    P = get_co(head); vg = head.vertex_groups.new(name='hidden')
    for i in np.nonzero(((P[:, 1] < 0.0) & (P[:, 2] > 1.70)) | (P[:, 2] > 1.86) | (P[:, 2] < 1.15))[0]: vg.add([int(i)], 1.0, 'REPLACE')
    n0 = np.mean(P[:, 1] > 0.1); dec(head, 10500, vg='hidden'); print('face share of verts %.2f -> %.2f' % (n0, np.mean(get_co(head)[:, 1] > 0.1)))
    P = get_co(head)
    q = np.sqrt((P[:, 0] / 0.39) ** 2 + (P[:, 1] / 0.37) ** 2 + ((P[:, 2] - 1.66) / 0.36) ** 2); up = (P[:, 2] > 1.75) & (q > 0.97)
    P[up] = np.array([0, 0, 1.66]) + (P[up] - np.array([0, 0, 1.66])) * (0.97 / q[up])[:, None]   # coarse scalp stays under the hair
    for k in (-1, 1):
        ec = np.array(eye_c(k)); p = P - ec; rho = np.linalg.norm(p, axis=1); bad = rho < R_EYE + 0.005
        P[bad] = ec + p[bad] / rho[bad, None] * (R_EYE + 0.005)
    set_co(head, P)
    # colour masks
    bvh = bvh_of(head); x, y, z = P.T; ax = np.abs(x); zs = ZM + SM * x * x; d = z - zs
    blush = np.zeros(len(P))
    for c, sg, wt in (((0.225, 0.27, 1.465), 0.075, 1.0), ((-0.225, 0.27, 1.465), 0.075, 1.0), ((0, 0.43, 1.51), 0.04, 0.55),
                      ((0.43, -0.03, 1.53), 0.07, 0.8), ((-0.43, -0.03, 1.53), 0.07, 0.8), ((0, 0.31, 1.32), 0.05, 0.3)):
        blush += wt * np.exp(-np.sum((P - np.array(c)) ** 2, axis=1) / (2 * sg * sg))
    hu = 0.020 * np.sqrt(np.maximum(1 - (x / (XC * 0.97)) ** 2, 0)); hl = 0.027 * np.sqrt(np.maximum(1 - (x / (XC * 0.9)) ** 2, 0))
    h = np.where(d > 0, hu, hl) + 1e-5
    lip = (1 - sstep(0.7 * h, h + 0.003, np.abs(d))) * (h > 0.002) * (y > lipy(x) - 0.03) * (y > 0.15)
    inner = (((x / (XC + 0.008)) ** 2 + ((y - lipy(0) + 0.05) / 0.12) ** 2 + (d / 0.0045) ** 2 < 1.4) & (y < lipy(x) - 0.012)).astype(float)
    for cx in list(np.linspace(-0.075, 0.075, 7)) + [None]:
        cc, rr = ((0, lipy(0) - 0.11, ZM - 0.015), 0.055) if cx is None else ((cx, lipy(cx) - 0.056, ZM + SM * cx * cx - 0.006), 0.03)
        inner[np.linalg.norm(P - np.array(cc), axis=1) < rr + 0.004] = 1.0
    e = np.empty(len(head.data.edges) * 2, np.int32); head.data.edges.foreach_get('vertices', e); e = e.reshape(-1, 2)
    cnt = np.zeros(len(P)); np.add.at(cnt, e[:, 0], 1); np.add.at(cnt, e[:, 1], 1)
    for arr in (inner, lip):
        for _ in range(2):
            acc = np.zeros(len(P)); np.add.at(acc, e[:, 0], arr[e[:, 1]]); np.add.at(acc, e[:, 1], arr[e[:, 0]])
            arr[:] = 0.5 * arr + 0.5 * acc / np.maximum(cnt, 1)
    at = head.data.color_attributes.new('mask', 'FLOAT_COLOR', 'POINT')
    at.data.foreach_set('color', np.stack([np.clip(blush, 0, 1), np.clip(lip, 0, 1), np.clip(inner * 1.3, 0, 1), np.ones(len(P))], axis=1).astype(np.float32).ravel())
    set_mat(head, M['skin'])
    add_keys(head, {k: deform_head(P, PRM[k], lipy) for k in EXPRS})
    return head, lipy

def build_eyes(M):
    out = []
    for s in (-1, 1):
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=16, radius=R_EYE)
        for v in bm.verts:
            c = Vector((v.co.x, v.co.z, -v.co.y))          # pole to +Y, so the iris sits on clean rings
            rp = math.hypot(c.x, c.z) / R_EYE
            if c.y > 0 and rp < 0.56: c *= 1 + 0.004 / R_EYE * math.cos(math.pi / 2 * rp / 0.56) ** 2   # corneal dome
            v.co = c
        me = bpy.data.meshes.new('eye'); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new('eye_R' if s > 0 else 'eye_L', me); bpy.context.scene.collection.objects.link(ob)
        fix_normals(ob); shade_smooth(ob); ob.location = eye_c(s); set_mat(ob, M['eye']); out.append(ob)
    return out

def build_lashes(M):
    out = []
    for s in (-1, 1):
        us = np.linspace(-0.9, 1.12, 22); pts = []; rs = []
        for u in us:
            xl = s * A_EYE * u; zu, _ = lid_curves(np.array([min(abs(xl), A_EYE) * np.sign(xl)]), s); z = zu[0] - 0.001
            if u > 1: z += (u - 1) * 0.07;
            rho = R_EYE + 0.022; y = math.sqrt(max(rho * rho - xl * xl - z * z, 1e-6))
            pts.append(eye_c(s) + V(xl, y, z)); rs.append(0.0035 + 0.0045 * sstep(-0.9, 0.7, u) * (1 - sstep(0.95, 1.12, u)))
        ob = tube('lash', pts, rs, seg=6); set_mat(ob, M['lash'])
        P = get_co(ob); add_keys(ob, {k: P + lid_delta(P, s, PRM[k]) for k in EXPRS}); out.append(ob)
    return out

def build_brows(M, head):
    bvh = bvh_of(head); out = []
    def pts_for(s, prm):
        pts = []
        for t in np.linspace(0, 1, 12):
            x = s * (0.062 + 0.185 * t) - s * prm['brow_dx'] * (1 - t)
            z = 1.735 + 0.03 * math.sin(math.pi * (0.15 + 0.75 * t)) - 0.012 * t + prm['brow_in'] * (1 - t) ** 1.5 + prm['brow_out'] * t ** 1.5
            hit = bvh.ray_cast(V(x, 1.0, z), V(0, -1, 0))[0]
            pts.append(V(x, hit.y + 0.006, z))
        return pts
    zero = dict(brow_in=0, brow_out=0, brow_dx=0)
    rs = [0.006 + 0.012 * math.sin(math.pi * (0.25 + 0.75 * t)) ** 1.2 for t in np.linspace(0, 1, 12)]
    for s in (-1, 1):
        ob = tube('brow', pts_for(s, zero), rs, seg=8, fx=1.0, fy=0.55, up=(0, 0, 1)); set_mat(ob, M['brow'])
        var = {}
        for k in EXPRS:
            tmp = tube('tmp', pts_for(s, PRM[k]), rs, seg=8, fx=1.0, fy=0.55, up=(0, 0, 1)); var[k] = get_co(tmp)
            bpy.data.objects.remove(tmp, do_unlink=True)
        add_keys(ob, var); out.append(ob)
    return out

def build_mouth_parts(M, lipy):
    out = []
    xs = np.linspace(-0.088, 0.088, 15)
    up = tube('teeth_upper', [V(x, lipy(x) - 0.037, ZM + SM * x * x + 0.036) for x in xs], 0.022, seg=10, fx=1.0, fy=0.36, up=(0, 0, 1))
    set_mat(up, M['teeth']); P = get_co(up)
    add_keys(up, {k: P + np.array([0, 0, -PRM[k]['teeth']]) for k in EXPRS}); out.append(up)
    xs = np.linspace(-0.07, 0.07, 13)
    lo = tube('teeth_lower', [V(x, lipy(x) - 0.042, ZM + SM * x * x - 0.032) for x in xs], 0.016, seg=10, fx=1.0, fy=0.4, up=(0, 0, 1))
    set_mat(lo, M['teeth']); P = get_co(lo); add_keys(lo, {k: jaw_rot(P, PRM[k]['jaw']) for k in EXPRS}); out.append(lo)
    tg = uvsphere('tongue', (0, lipy(0) - 0.085, ZM - 0.04), 1.0, seg=14, rings=8, scale=(0.06, 0.06, 0.02))
    set_mat(tg, M['tongue']); P = get_co(tg); add_keys(tg, {k: jaw_rot(P, PRM[k]['jaw'] * 0.9) for k in EXPRS}); out.append(tg)
    return out

def build_hair(M):
    random.seed(11); s = Soup('hair')
    C = Vector((0, 0, 1.66)); RX, RY, RZ = 0.39, 0.37, 0.36
    s.ellipsoid((0, -0.06, 1.72), (0.40, 0.36, 0.33), seg=48)            # scalp cap, stays behind the forehead
    n = 150; ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        dz = 1 - 2 * (i + .5) / n; rr = math.sqrt(1 - dz * dz); a = i * ga
        dx, dy = rr * math.cos(a), rr * math.sin(a)
        caz = dy / max(rr, 1e-6)                                         # 1 at the front, -1 at the back
        line = 0.05 + 0.40 * caz if caz > 0 else 0.05 + 0.78 * caz        # hairline: high over the forehead, low at the nape
        line += 0.13 * (1 - abs(caz)) ** 2                               # lift the sides so the ears and studs show
        if dz < line: continue
        r = random.uniform(0.082, 0.11)
        k = 1.0 + random.uniform(0.02, 0.07)
        s.sphere((C.x + dx * RX * k, C.y + dy * RY * k - 0.01, C.z + dz * RZ * k), r, seg=16)
    hair, _ = s.remesh(voxel=0.008, smooth=16, smooth_factor=0.6)
    dec(hair, 7000)
    P = get_co(hair); q = np.sqrt(((P[:, 0] - C.x) / RX) ** 2 + ((P[:, 1] - C.y) / RY) ** 2 + ((P[:, 2] - C.z) / RZ) ** 2)
    at = hair.data.attributes.new('tip', 'FLOAT', 'POINT'); at.data.foreach_set('value', sstep(1.08, 1.31, q).astype(np.float32))
    set_mat(hair, M['hair']); return hair

def build_glasses(M):
    objs = []; gy = EYE_Y + R_EYE + 0.024 + 0.022; zc = EYE_Z - 0.008; RL_ = 0.1
    for s in (-1, 1):
        c = V(s * EX, gy, zc)
        objs.append(tube('rim', ring_pts(c, RL_, 'y', 36), 0.0055, seg=6, closed=True))
        objs.append(tube('temple', fillet([c + V(s * RL_, 0, 0.01), c + V(s * (RL_ + 0.03), -0.005, 0.012), V(s * 0.415, 0.02, 1.64), V(s * 0.418, -0.075, 1.575)], 0.03), 0.0045, seg=6))
    objs.append(tube('bridge', [V(-(EX - RL_), gy, zc + 0.012), V(-0.025, gy + 0.004, zc + 0.034), V(0, gy + 0.005, zc + 0.038), V(0.025, gy + 0.004, zc + 0.034), V(EX - RL_, gy, zc + 0.012)], 0.0055, seg=8))
    fr = join(objs, 'glasses'); set_mat(fr, M['gold'])
    lens = []
    for s in (-1, 1):
        verts = [V(s * EX, gy + 0.005, zc)]; faces = []; nr, ns = 3, 24
        for i in range(1, nr + 1):
            r = RL_ * i / nr
            for k in range(ns):
                a = 2 * math.pi * k / ns; verts.append(V(s * EX + r * math.cos(a), gy + 0.005 * (1 - (i / nr) ** 2), zc + r * math.sin(a)))
        for k in range(ns): faces.append((0, 1 + k, 1 + (k + 1) % ns))
        for i in range(1, nr):
            for k in range(ns):
                a0 = 1 + (i - 1) * ns; a1 = 1 + i * ns; k2 = (k + 1) % ns; faces.append((a0 + k, a1 + k, a1 + k2, a0 + k2))
        lens.append(new_obj('lens', verts, faces, fix=False))
    ln = join(lens, 'lenses'); set_mat(ln, M['lens']); ln.visible_shadow = False
    return [fr, ln]

# =====================================================================================
# body
# =====================================================================================
def arm_pts(s):
    return V(s * 0.30, 0.0, 1.08), V(s * 0.475, 0.03, 0.90), V(s * 0.418, 0.245, 0.835)

def build_blouse(M):
    s = Soup('blouse')
    s.ellipsoid((0, 0.0, 0.86), (0.365, 0.315, 0.36), seg=48)              # belly
    s.ellipsoid((0, -0.02, 1.05), (0.345, 0.245, 0.165), seg=48)           # shoulders
    s.ellipsoid((0, -0.11, 1.02), (0.27, 0.17, 0.17))                      # rounded upper back
    s.ellipsoid((0, 0.13, 0.98), (0.27, 0.17, 0.13))                       # soft bust
    soup_cone(s, (0, 0, 0.42), (0, 0, 0.86), 0.385, 0.36, sy=0.86)         # loose hem
    cuts = []
    for k in (-1, 1):
        sh, el, wr = arm_pts(k); ax = (wr - el).normalized(); cuff = el + (wr - el) * 0.42
        s.capsule(sh, el, 0.125, 0.118); s.capsule(el, cuff + ax * 0.04, 0.118, 0.128)
        c = Soup('cut'); c.capsule(cuff - ax * 0.07, cuff + ax * 0.3, 0.102, 0.102)
        q = ax.to_track_quat('Z', 'Y'); g = bmesh.ops.create_cone(c.bm, cap_ends=True, segments=32, radius1=0.25, radius2=0.25, depth=0.3)
        mt = Matrix.Translation(cuff + ax * 0.15) @ q.to_matrix().to_4x4()
        for v in g['verts']: v.co = mt @ v.co
        cuts.append(c)
    c = Soup('cut'); soup_cone(c, (0, 0, 0.2), (0, 0, 0.66), 0.352, 0.33, sy=0.85); c.box((0, 0, 0.2), (2, 2, 0.54)); cuts.append(c)
    ob, _ = s.remesh(voxel=0.008, smooth=6, smooth_factor=0.6)
    for c in cuts:
        cut, _ = c.remesh(voxel=0.008, smooth=0); boolean_cut(ob, cut)
    remesh_ob(ob, 0.006, smooth=3, factor=0.5)
    # a few big soft folds that grow toward the hem
    P = get_co(ob); th = np.arctan2(P[:, 1], P[:, 0]); z = P[:, 2]
    amp = 0.075 * sstep(0.84, 0.47, z) * (np.hypot(P[:, 0], P[:, 1]) > 0.2)
    f = 1 + amp * (np.sin(6 * th + 0.6 + 2.2 * (z - 0.47)) + 0.35 * np.sin(11 * th + 2.0))
    P[:, 0] *= f; P[:, 1] *= f; set_co(ob, P)
    dec(ob, 5000)
    set_mat(ob, M['blouse']); return ob

def build_collar_piping(M, blouse):
    out = []; bvh = bvh_of(blouse)
    # mandarin collar: a band round the neck with a small gap at the front
    verts = []; faces = []; na = 44; prof = [(0.0, 0.0), (0.012, 0.0), (0.014, 0.03), (0.012, 0.058), (0.006, 0.066), (0.0, 0.062), (-0.004, 0.03)]
    npf = len(prof); top = []
    for i in range(na + 1):
        a = math.radians(7 + 346 * i / na) + math.pi / 2          # start just off the front (+Y), go all the way round
        ca, sa = math.cos(a), math.sin(a); front = (sa + 1) * 0.5
        zb = 1.158 - 0.02 * front; lean = 1.0 - 0.0 * front
        for j, (dr, dz) in enumerate(prof):
            r = 0.145 + dr - 0.012 * (dz / 0.066) * lean
            verts.append(V(r * 1.04 * ca, -0.005 + r * 0.97 * sa, zb + dz * (1 - 0.18 * front)))
        r = 0.145 + 0.009 - 0.012; top.append(V(r * 1.04 * ca, -0.005 + r * 0.97 * sa, zb + 0.066 * (1 - 0.18 * front)))
    for i in range(na):
        for j in range(npf):
            j2 = (j + 1) % npf; faces.append((i * npf + j, (i + 1) * npf + j, (i + 1) * npf + j2, i * npf + j2))
    faces.append(tuple(range(npf))); faces.append(tuple(na * npf + j for j in range(npf)))
    col = new_obj('collar', verts, faces); set_mat(col, M['blouse']); out.append(col)
    pp = tube('collar_piping', top, 0.006, seg=6); set_mat(pp, M['piping']); out.append(pp)
    # placket: from the collar front, diagonally to her right, then down the front-side
    key = [(0.0, 1.150), (0.07, 1.125), (0.15, 1.075), (0.22, 1.01), (0.262, 0.94), (0.272, 0.86), (0.272, 0.70), (0.272, 0.56)]
    dense = []
    for (x0, z0), (x1, z1) in zip(key[:-1], key[1:]):
        for t in np.linspace(0, 1, 6, endpoint=False): dense.append((x0 + (x1 - x0) * t, z0 + (z1 - z0) * t))
    dense.append(key[-1])
    for _ in range(3):   # relax the polyline so the bends are soft
        dense = [dense[0]] + [((a[0] + 2 * b[0] + c[0]) / 4, (a[1] + 2 * b[1] + c[1]) / 4) for a, b, c in zip(dense[:-2], dense[1:-1], dense[2:])] + [dense[-1]]
    path = []; nrm = []
    for x, z in dense:
        loc, n, _, _ = bvh.ray_cast(V(x, 2.0, z), V(0, -1, 0)); path.append(loc + n * 0.003); nrm.append(n)
    pp = tube('placket', path, 0.0065, seg=6); set_mat(pp, M['piping']); out.append(pp)
    frogs = []
    for idx in (2, 11, 20, 29, 37, 44):
        idx = min(idx, len(path) - 2); p = path[idx]; n = nrm[idx]; t = (path[idx + 1] - path[idx - 1]).normalized(); side = n.cross(t).normalized()
        frogs.append(uvsphere('knot', p + n * 0.008, 0.015, seg=8, rings=5))
        frogs.append(tube('bar', [p - side * 0.04 + n * 0.002, p - side * 0.02 + n * 0.006, p + side * 0.02 + n * 0.006, p + side * 0.04 + n * 0.002], 0.006, seg=5))
    fr = join(frogs, 'frogs'); set_mat(fr, M['piping']); out.append(fr)
    return out, path

def build_print(M, blouse, path):
    """Clean floral print as thin decals that hug the cloth. In the game this is one baked texture."""
    me = blouse.data; me.calc_loop_triangles(); P = get_co(blouse)
    tr = np.array([t.vertices[:] for t in me.loop_triangles]); a, b, c = P[tr[:, 0]], P[tr[:, 1]], P[tr[:, 2]]
    nn = np.cross(b - a, c - a); area = np.linalg.norm(nn, axis=1) * .5; nn /= np.maximum(2 * area[:, None], 1e-12)
    cum = np.cumsum(area) / area.sum(); rng = np.random.default_rng(5); bvh = bvh_of(blouse)
    k = 9000; idx = np.searchsorted(cum, rng.random(k)); u = rng.random(k); v = rng.random(k); sw = u + v > 1; u[sw] = 1 - u[sw]; v[sw] = 1 - v[sw]
    pts = a[idx] + (b[idx] - a[idx]) * u[:, None] + (c[idx] - a[idx]) * v[:, None]; ns = nn[idx]
    pathA = np.array([tuple(p) for p in path])
    cuffs = [(arm_pts(k)[1], (arm_pts(k)[2] - arm_pts(k)[1]).normalized(), (arm_pts(k)[2] - arm_pts(k)[1]).length) for k in (-1, 1)]
    ok = []
    for p, n in zip(pts, ns):
        if p[2] < 0.53 or n[2] < -0.6: continue
        if any((Vector(p) - el).dot(axv) > 0.3 * ln and ((Vector(p) - el) - axv * (Vector(p) - el).dot(axv)).length < 0.2 for el, axv, ln in cuffs): continue
        if p[2] > 1.12 and math.hypot(p[0], p[1]) < 0.215: continue
        if bvh.ray_cast(Vector(p) + Vector(n) * 0.004, Vector(n), 0.22)[0] is not None: continue
        if np.min(np.linalg.norm(pathA - p, axis=1)) < 0.055: continue
        ok.append((p, n))
    big = []; small = []
    for p, n in ok:
        if all(np.linalg.norm(p - q[0]) > 0.165 for q in big): big.append((p, n))
    for p, n in ok:
        if all(np.linalg.norm(p - q[0]) > 0.085 for q in big) and all(np.linalg.norm(p - q[0]) > 0.075 for q in small): small.append((p, n))
    verts = []; faces = []; mats = []
    def patch(p, n, outline, off, mat):
        n = Vector(n); t1 = n.cross(V(0, 0, 1)); t1 = t1.normalized() if t1.length > 1e-3 else V(1, 0, 0); t2 = n.cross(t1)
        base = len(verts); ring = []
        for (uu, vv) in [(sum(o[0] for o in outline) / len(outline), sum(o[1] for o in outline) / len(outline))] + outline:
            w = Vector(p) + t1 * uu + t2 * vv; loc, nr, _, _ = bvh.find_nearest(w)
            verts.append(loc + nr * off)
        m = len(outline)
        for i in range(m): faces.append((base, base + 1 + i, base + 1 + (i + 1) % m)); mats.append(mat)
    def petal(ang, r, n=10):
        ca, sa = math.cos(ang), math.sin(ang); out = []
        for i in range(n):
            t = 2 * math.pi * i / n; lu = r * 0.56 + r * 0.50 * math.cos(t); lv = r * 0.40 * math.sin(t)
            out.append((lu * ca - lv * sa, lu * sa + lv * ca))
        return out
    def leaf(ang, r0, r1, wd, n=5):
        ca, sa = math.cos(ang), math.sin(ang); out = []
        for i in range(n + 1): t = i / n; lu = r0 + (r1 - r0) * t; lv = wd * math.sin(math.pi * t); out.append((lu, lv))
        for i in range(n - 1, 0, -1): t = i / n; lu = r0 + (r1 - r0) * t; lv = -wd * math.sin(math.pi * t); out.append((lu, lv))
        return [(lu * ca - lv * sa, lu * sa + lv * ca) for lu, lv in out]
    for p, n in big:
        a0 = rng.random() * 6.28; r = 0.05 * (0.9 + 0.25 * rng.random())
        for j in range(2): patch(p, n, leaf(a0 + 0.9 + j * (2.2 + rng.random()), r * 0.7, r * 1.75, r * 0.34), 0.0010, 3)
        for j in range(5): patch(p, n, petal(a0 + j * 2 * math.pi / 5, r), 0.0016, 0)
        patch(p, n, [(r * 0.26 * math.cos(t), r * 0.26 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 10, endpoint=False)], 0.0024, 2)
    for p, n in small:
        a0 = rng.random() * 6.28; r = 0.022 * (0.9 + 0.3 * rng.random())
        for j in range(5): patch(p, n, petal(a0 + j * 2 * math.pi / 5, r, n=8), 0.0016, 1)
        patch(p, n, [(r * 0.28 * math.cos(t), r * 0.28 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 8, endpoint=False)], 0.0024, 2)
    ob = new_obj('print', verts, faces, fix=False)
    for k in ('petal', 'petal2', 'centre', 'leaf'): ob.data.materials.append(M[k])
    ob.data.polygons.foreach_set('material_index', mats); ob.visible_shadow = False
    print('print: %d big, %d small flowers' % (len(big), len(small)))
    return ob

def build_arm(M, s):
    sh, el, wr = arm_pts(s); G = V(s * HX, GY, HZ)
    so = Soup('arm'); so.capsule(sh.lerp(el, 0.5), el, 0.08, 0.076); so.capsule(el, wr, 0.076, 0.058)
    palm = G + V(s * 0.006, -0.012, RG + 0.026)
    so.ellipsoid(palm, (0.06, 0.084, 0.034)); so.capsule(wr, palm + V(0, -0.035, 0.004), 0.057, 0.05)
    for i, yo in enumerate((-0.058, -0.02, 0.018, 0.054)):
        rf = (0.021, 0.0225, 0.022, 0.0195)[i]; pts = []
        for a in np.linspace(math.radians(78), math.radians(-150 + 6 * abs(i - 1.5)), 9):
            rad = RG + rf * 0.92; pts.append(G + V(s * math.cos(a) * rad, yo - 0.012, math.sin(a) * rad))
        for a, b in zip(pts[:-1], pts[1:]): so.capsule(a, b, rf, rf * 0.95, seg=10)
    pts = []
    for i, a in enumerate(np.linspace(math.radians(108), math.radians(205), 6)):
        rad = RG + 0.022; pts.append(G + V(s * math.cos(a) * rad, -0.092 + 0.006 * i, math.sin(a) * rad))
    for a, b in zip(pts[:-1], pts[1:]): so.capsule(a, b, 0.0245, 0.023, seg=10)
    ob, _ = so.remesh(voxel=0.005, smooth=3, smooth_factor=0.5)
    dec(ob, 1800)
    set_mat(ob, M['skin']); ob.name = 'arm_R' if s > 0 else 'arm_L'; return ob

def build_slacks(M):
    s = Soup('slacks'); s.ellipsoid((0, 0, 0.60), (0.32, 0.26, 0.15), seg=32)
    c = Soup('cut'); c.box((0, 0, -0.4), (2, 2, 1.0))
    for k in (-1, 1):
        s.capsule((k * 0.155, 0.0, 0.60), (k * 0.17, 0.012, 0.13), 0.158, 0.142)
        c.capsule((k * 0.17, 0.012, 0.0), (k * 0.17, 0.012, 0.17), 0.118, 0.118)
    ob, _ = s.remesh(voxel=0.008, smooth=5, smooth_factor=0.6)
    cut, _ = c.remesh(voxel=0.008, smooth=0); boolean_cut(ob, cut)
    remesh_ob(ob, 0.007, smooth=3, factor=0.5)
    dec(ob, 1600)
    set_mat(ob, M['slacks']); return ob

def build_feet(M):
    out = []
    for s in (-1, 1):
        mt = Matrix.Translation((s * 0.17, 0.0, 0)) @ Matrix.Rotation(math.radians(-10 * s), 4, 'Z')
        so = Soup('foot'); so.capsule((0, 0.0, 0.32), (0, -0.005, 0.11), 0.062, 0.058); so.sphere((0, -0.05, 0.087), 0.055)
        so.ellipsoid((0, 0.06, 0.082), (0.063, 0.125, 0.042))
        for xo, yo, r in ((-0.042, 0.19, 0.028), (-0.012, 0.196, 0.022), (0.012, 0.19, 0.020), (0.032, 0.178, 0.018), (0.049, 0.162, 0.016)):
            so.capsule((s * xo, yo - 0.06, 0.068), (s * xo, yo, 0.062), r, r, seg=10)
        for v in so.bm.verts: v.co = mt @ v.co
        ft, _ = so.remesh(voxel=0.005, smooth=3, smooth_factor=0.5)
        dec(ft, 700)
        set_mat(ft, M['skin']); ft.name = 'foot'; out.append(ft); fb = bvh_of(ft)
        # slipper sole: rounded slab, wider at the toes
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=1, radius2=1, depth=1)
        for v in bm.verts:
            y = v.co.y * 0.172 + 0.055; x = v.co.x * 0.078 * (1 + 0.2 * v.co.y); v.co = mt @ Vector((x, y, v.co.z * 0.036 + 0.02))
        me = bpy.data.meshes.new('sole'); bm.to_mesh(me); bm.free()
        sole = bpy.data.objects.new('sole', me); bpy.context.scene.collection.objects.link(sole)
        bv = sole.modifiers.new('bevel', 'BEVEL'); bv.width = 0.01; bv.segments = 2; bv.limit_method = 'ANGLE'; apply_mod(sole, bv)
        shade_smooth(sole); sole.data.set_sharp_from_angle(angle=math.radians(50))
        parts = [sole]
        def over(p):   # keep the strap just above the foot
            w = mt @ Vector(p); hit = fb.ray_cast(V(w.x, w.y, 1.0), V(0, 0, -1))[0]
            if hit is not None: w.z = max(w.z, hit.z + 0.008)
            return w
        post = (-s * 0.027, 0.150, 0.03)
        for side in (-1, 1):
            pts = [over(post), over((-s * 0.027, 0.146, 0.075)), over((side * 0.035 - s * 0.01, 0.10, 0.11)), over((side * 0.066, 0.05, 0.10)), over((side * 0.078, 0.01, 0.07)), mt @ Vector((side * 0.072, -0.005, 0.03))]
            parts.append(tube('strap', fillet(pts, 0.03, 4), 0.012, seg=6))
        sl = join(parts, 'slipper'); set_mat(sl, M['slipper']); out.append(sl)
    return out

# =====================================================================================
# props
# =====================================================================================
def rrect(w, d, r, n=5):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, d / 2 - r, 0), (-(w / 2 - r), d / 2 - r, 90), (-(w / 2 - r), -(d / 2 - r), 180), (w / 2 - r, -(d / 2 - r), 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def loft(name, rings):
    verts = []; faces = []; m = len(rings[0])
    for ring in rings: verts += ring
    for i in range(len(rings) - 1):
        for k in range(m):
            k2 = (k + 1) % m; faces.append((i * m + k, i * m + k2, (i + 1) * m + k2, (i + 1) * m + k))
    faces.append(tuple(range(m))); faces.append(tuple((len(rings) - 1) * m + k for k in range(m)))
    ob = new_obj(name, verts, faces); ob.data.set_sharp_from_angle(angle=math.radians(40)); return ob

def build_walker(M):
    metal = []; rubber = []; foam = []; ZB = 0.05
    legs = {}
    for s in (-1, 1):
        pts = [V(s * (HX + 0.035), 0.085, ZB), V(s * HX, 0.15, HZ), V(s * HX, 0.56, HZ), V(s * (HX + 0.035), 0.66, ZB)]
        metal.append(tube('side', fillet(pts, 0.07, 8), 0.019, seg=12))
        legs[s] = pts
        foam.append(tube('grip', [V(s * HX, y, HZ) for y in np.linspace(0.205, 0.475, 8)], [RG * 0.96] + [RG] * 6 + [RG * 0.96], seg=16))
        for a, b in ((pts[1], pts[0]), (pts[2], pts[3])):
            rubber.append(tube('tip', [a.lerp(b, 0.93), a.lerp(b, 1.045)], [0.026, 0.03], seg=14))
            metal.append(tube('collar', [a.lerp(b, 0.62), a.lerp(b, 0.66)], 0.023, seg=12))
        zb = 0.34; tb = (HZ - zb) / (HZ - ZB)
        metal.append(tube('brace', [pts[1].lerp(pts[0], tb), pts[2].lerp(pts[3], tb)], 0.014, seg=10))
    bars = []
    for zb in (0.60, 0.36):
        t = (HZ - zb) / (HZ - ZB); a = legs[-1][2].lerp(legs[-1][3], t); b = legs[1][2].lerp(legs[1][3], t)
        pts = [a.lerp(b, u) + V(0, 0.05 * (1 - (2 * u - 1) ** 2), 0) for u in np.linspace(0, 1, 13)]
        metal.append(tube('bar', pts, 0.016, seg=10)); bars.append(pts[6])
    wm = join(metal, 'walker_frame'); set_mat(wm, M['metal'])
    wr = join(rubber, 'walker_tips'); set_mat(wr, M['rubber'])
    wf = join(foam, 'walker_grips'); set_mat(wf, M['foam'])
    # red basket hung on the upper front bar
    by = bars[0].y + 0.14; z1 = bars[0].z + 0.02; z0 = z1 - 0.25
    def ring(w, d, r, z): return [V(x, by + y, z) for x, y in rrect(w, d, r)]
    rings = [ring(0.36, 0.12, 0.03, z0), ring(0.42, 0.17, 0.045, z0), ring(0.44, 0.185, 0.05, z0 + 0.02), ring(0.50, 0.225, 0.055, z1 - 0.03),
             ring(0.53, 0.25, 0.06, z1 - 0.03), ring(0.53, 0.25, 0.06, z1), ring(0.475, 0.2, 0.05, z1), ring(0.42, 0.165, 0.045, z0 + 0.03), ring(0.36, 0.12, 0.03, z0 + 0.03)]
    bk = loft('basket', rings)
    hooks = [tube('hook', fillet([V(x, by - 0.118, z1 - 0.01), V(x, by - 0.118, z1 + 0.03), V(x, by - 0.165, z1 + 0.03), V(x, by - 0.165, z1 - 0.03)], 0.015), 0.008, seg=8) for x in (-0.15, 0.15)]
    bk = join([bk] + hooks, 'basket'); set_mat(bk, M['basket'])
    # marketing in the basket: spring onions and two mandarin oranges
    wh = []; gr = []; random.seed(4)
    for i in range(5):
        x0 = -0.13 + 0.035 * i; base = V(x0, by + 0.02, z0 + 0.06); lean = V(-0.10 - 0.02 * i, 0.03 * math.sin(i * 2.1), 0.0)
        mid = base + V(0, 0, 0.17) + lean * 0.4; top = base + V(0, 0, 0.36 + 0.02 * (i % 3)) + lean * 1.2
        wh.append(tube('on_w', [base, base.lerp(mid, 0.5), mid], [0.013, 0.012, 0.011], seg=8))
        for j in (-1, 1):
            tip = top + V(0.03 * j, 0.02 * j * (i % 2 - .5), 0.03 * (j + 1))
            gr.append(tube('on_g', [mid - V(0, 0, 0.01), mid.lerp(top, 0.5) + V(0.008 * j, 0, 0), tip], [0.0105, 0.009, 0.004], seg=8))
    ow = join(wh, 'onion_white'); set_mat(ow, M['onion_w']); og = join(gr, 'onion_green'); set_mat(og, M['onion_g'])
    ors = [uvsphere('orange', (0.09, by - 0.01, z1 - 0.005), 0.058, seg=18, rings=10, scale=(1, 1, 0.9)), uvsphere('orange', (0.16, by + 0.035, z1 - 0.035), 0.055, seg=18, rings=10, scale=(1, 1, 0.9))]
    oo = join(ors, 'oranges'); set_mat(oo, M['orange'])
    return [wm, wr, wf, bk, ow, og, oo]

def build_jewellery(M, head):
    out = []; bvh = bvh_of(head)
    studs = []
    for s in (-1, 1):
        hit = bvh.ray_cast(V(s * 1.0, -0.012, 1.452), V(-s, 0, 0))[0]
        studs.append(uvsphere('stud', hit + V(s * 0.01, 0.004, 0), 0.02, seg=10, rings=6))
    st = join(studs, 'earrings'); set_mat(st, M['gold']); out.append(st)
    sh, el, wr = arm_pts(-1); ax = (wr - el).normalized(); c = el + (wr - el) * 0.86
    q = ax.to_track_quat('Z', 'Y'); pts = [c + q @ V(0.07 * math.cos(a), 0.07 * math.sin(a), 0) for a in np.linspace(0, 2 * math.pi, 28, endpoint=False)]
    bg = tube('bangle', pts, 0.015, seg=8, closed=True); set_mat(bg, M['jade']); out.append(bg)
    return out

# =====================================================================================
# build
# =====================================================================================
def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = make_materials()
    head, lipy = build_head(M)
    head_parts = [head] + build_eyes(M) + build_lashes(M) + build_brows(M, head) + build_mouth_parts(M, lipy) + [build_hair(M)] + build_glasses(M)
    jew = build_jewellery(M, head); head_parts.append(jew[0])
    blouse = build_blouse(M); extra, path = build_collar_piping(M, blouse)
    body = [blouse] + extra + [build_print(M, blouse, path), build_arm(M, -1), build_arm(M, 1), build_slacks(M)] + build_feet(M) + [jew[1]] + build_walker(M)
    root = bpy.data.objects.new('ahma', None); bpy.context.scene.collection.objects.link(root)
    hc = bpy.data.objects.new('head_ctl', None); bpy.context.scene.collection.objects.link(hc); hc.location = HEAD_PIVOT; hc.parent = root
    bpy.context.view_layer.update()
    for o in head_parts:
        o.parent = hc; o.matrix_parent_inverse = hc.matrix_world.inverted()
    for o in body: o.parent = root
    tot = 0; dec = 0
    for o in head_parts + body:
        t = tri_count(o); tot += t
        if o.name == 'print': dec = t
        print('  %-16s %6d tris' % (o.name, t))
    print('TRIS total %d, print decals %d, game mesh without decals %d' % (tot, dec, tot - dec))
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)

# =====================================================================================
# shots
# =====================================================================================
def set_expr(name):
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks[1:]: kb.value = 1.0 if kb.name == name else 0.0

def lamp(name, kind, loc, target, energy, col, size=1.5, spot=1.0):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = col
    if kind == 'AREA': d.size = size
    if kind == 'SPOT': d.spot_size = spot; d.spot_blend = .6; d.shadow_soft_size = 0.4
    o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o); o.location = loc
    RL.look_at(o, Vector(target)); return o

def stage():
    sc = bpy.context.scene
    RL.setup_render(1600, 2000, samples=200)
    w = bpy.data.worlds.get('World') or bpy.data.worlds.new('World'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.55, 0.62, 0.72, 1); bg.inputs[1].default_value = 0.35
    T = (0, 0.1, 1.1)
    lamp('key', 'AREA', (3.3, 3.9, 6.0), T, 1500, (1.0, 0.84, 0.62), size=2.5)     # golden-hour key, front-left, about 45 degrees up
    lamp('fill', 'AREA', (-4.5, 3.5, 2.5), T, 330, (0.70, 0.80, 1.0), size=4)      # cool sky fill
    lamp('rim', 'SPOT', (-2.6, -4.2, 3.6), (0, 0, 1.4), 2600, (1.0, 0.86, 0.66), spot=0.9)   # warm rim, back-right
    RL.floor()
    for k, v in (('use_shadows', True), ('use_raytracing', True)):
        try: setattr(sc.eevee, k, v)
        except Exception as e: print('eevee', k, e)
    try: sc.eevee.ray_tracing_options.resolution_scale = '1'
    except Exception as e: print('rt opts', e)
    sc.render.image_settings.color_mode = 'RGB'

def cam_shot(path, loc, target, lens, res, dof=None):
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = res
    cam = sc.camera or RL.camera(loc, target, lens)
    cam.location = loc; cam.data.lens = lens; RL.look_at(cam, Vector(target)); cam.data.clip_start = 0.2; cam.data.clip_end = 100
    cam.data.dof.use_dof = dof is not None
    if dof: cam.data.dof.focus_distance = dof[0]; cam.data.dof.aperture_fstop = dof[1]
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)

def stitch(paths, out):
    arrs = []
    for p in paths:
        im = bpy.data.images.load(p); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a)
        arrs.append(a.reshape(h, w, 4)); bpy.data.images.remove(im)
    full = np.concatenate(arrs, axis=1); h, w = full.shape[:2]
    o = bpy.data.images.new('stitch', w, h, alpha=False); o.pixels.foreach_set(full.ravel())
    o.filepath_raw = out; o.file_format = 'PNG'; o.save(); bpy.data.images.remove(o)

def pose(head_rz=0.0, head_ry=0.0, head_rx=0.0, gaze_z=0.0, gaze_x=0.0, root_rz=0.0):
    bpy.data.objects['head_ctl'].rotation_euler = (head_rx, head_ry, head_rz)
    bpy.data.objects['ahma'].rotation_euler = (0, 0, root_rz)
    for n in ('eye_L', 'eye_R'): bpy.data.objects[n].rotation_euler = (gaze_x, 0, gaze_z)

def shots(which):
    bpy.ops.wm.open_mainfile(filepath=BLEND); stage(); os.makedirs(SHOTS, exist_ok=True)
    az = math.radians(-27)   # three-quarter: camera toward her left, so the key models the face
    def orbit(d, z): return (d * math.sin(az), d * math.cos(az), z)
    if 'hero' in which:
        set_expr('smile'); pose(head_rz=0.16, head_ry=-0.04, gaze_z=0.22, gaze_x=0.04)
        cam_shot(os.path.join(SHOTS, 'hero.png'), orbit(5.0, 1.05), (0.0, 0.22, 1.08), 70, (1600, 2000))
    if 'face' in which:
        set_expr('smile'); pose(head_rz=0.12, head_ry=-0.05, gaze_z=0.26, gaze_x=0.0)
        cam_shot(os.path.join(SHOTS, 'face.png'), orbit(2.75, 1.60), (0.02, 0.1, 1.62), 85, (1600, 1600), dof=(2.5, 5.6))
    if 'expressions' in which:
        tiles = []
        for k in EXPRS:
            set_expr(k); pose(); p = os.path.join(TMP, 'pixar_expr_%s.png' % k); tiles.append(p)
            cam_shot(p, (0, 2.75 + 0.2, 1.63), (0, 0.2, 1.65), 85, (400, 480))
        stitch(tiles, os.path.join(SHOTS, 'expressions.png'))
    if 'turn' in which:
        tiles = []; set_expr('smile')
        for i, (rz, wpx) in enumerate(((0, 534), (math.pi / 2, 533), (math.pi, 533))):
            pose(root_rz=rz); p = os.path.join(TMP, 'pixar_turn_%d.png' % i); tiles.append(p)
            cx = -0.27 * math.sin(rz); cam_shot(p, (cx, 6.6, 1.1), (cx, 0.0, 1.08), 90, (wpx, 900))
        stitch(tiles, os.path.join(SHOTS, 'turn.png'))

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build', 'shots']
    if 'build' in args: build()
    if 'shots' in args:
        which = [a for a in args if a in ('hero', 'face', 'expressions', 'turn')] or ['hero', 'face', 'expressions', 'turn']
        shots(which)
