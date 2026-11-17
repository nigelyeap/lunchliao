"""The Siaolang (key siao), Gate 2 hero. Headless build:
  /opt/homebrew/bin/blender -b -P tools/blender/heroes/siao.py -- build look rig expr bake anim export verify shots exprfinal
Stages save a .blend in SIAO_WORK (default /tmp/siao_work) so later stages can be re-run alone.
Blender axes: Z up, he faces +Y. The glTF exporter makes that Y up, facing -Z.
Same pipeline as ahma.py. Generic helpers (MB node builder, bake, stitch, pose maths) are imported from it unchanged."""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix, Euler, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
from hero_lib import *
import render_lib as RL
from ahma import (MB, new_image, bake, px, set_px, save_png, export_material, stitch, smoothstep, falloff,
                  rest_mat, world_quat_to_local, set_world_rot, axis_rot, reset_pose, play, make_armature as _unused)

WORK = os.environ.get('SIAO_WORK', '/tmp/siao_work'); os.makedirs(WORK, exist_ok=True)
OUT_GLB = os.path.join(ROOT, 'assets', 'heroes', 'siao.glb')
SHOTS = os.path.join(ROOT, 'shots', 'heroes', 'siao'); os.makedirs(SHOTS, exist_ok=True)

# ---------------- palette (sRGB hex, converted to linear for nodes) ----------------
COL = dict(
    skin='#CF9470', skin_warm='#EDB98A', skin_cool='#C48A72', skin_shade='#95607A', blush='#D97E62', stubble='#8A7484',
    lip='#B5565C', lid='#4A2E3C', mouth='#4A1E2C', teeth='#EDE2C8',
    hair='#302C2D', hair_light='#8C7A6A', hair_deep='#141318', hair_grey='#5A5658', hair_cool='#55607A',
    singlet='#EDE6D2', singlet_cool='#D9D2C6', singlet_shade='#A9A2BC', stain='#CBB37E', stain_dark='#B69A5E',
    shorts='#7E2630', shorts_light='#A03E48', shorts_shade='#45162A', slipper='#C8102E', slipper_dark='#8F0B20',
    frame='#151414', glint='#FFFFFF', sweat='#C9E3F2', drool='#D6F1FB',
    sclera='#FFF7E9', sclera_shade='#E8D8CC', iris='#5A3A28', iris_light='#9A6A42', pupil='#1A1210',
)
LIN = {k: srgb(v) for k, v in COL.items()}
def c4(k): return (*LIN[k], 1)

# ---------------- landmarks (metres, Blender Z up, +Y forward) ----------------
HEAD_C = Vector((0, 0.06, 1.57)); CRAN = (0.37, 0.36, 0.389)         # dome top 1.95, strands bring it to 1.96
EYE_L = Vector((-0.16, 0.36, 1.565)); EYE_R = Vector((0.16, 0.36, 1.565)); EYE_R_BALL = 0.068
MOUTH_C = Vector((0, 0.40, 1.355))
BROW_Z = 1.695

def sx(v, s): return Vector((v.x * s, v.y, v.z))

def dome_z(x, y, lift=0.0):
    """z of the cranium surface above (x, y), plus lift."""
    t = 1 - (x / CRAN[0]) ** 2 - ((y - HEAD_C.y) / CRAN[1]) ** 2
    return HEAD_C.z + CRAN[2] * math.sqrt(max(t, 0.0)) + lift

# =====================================================================================
# geometry
# =====================================================================================
def build_head():
    """Big clean forms: cranium, wide cheek mass, jaw, chin, ears, a rounded uncle nose and a thick neck. Everything else is painted."""
    s = Soup('siao_head_skin')
    s.ellipsoid(HEAD_C, CRAN)
    s.ellipsoid((0, 0.10, 1.44), (0.33, 0.30, 0.22))
    s.ellipsoid((0, 0.16, 1.34), (0.27, 0.25, 0.13))
    s.sphere((0, 0.30, 1.29), 0.095)
    for k in (-1, 1):
        s.ellipsoid((k * 0.375, 0.04, 1.54), (0.05, 0.08, 0.11))
    s.capsule((0, 0.39, 1.575), (0, 0.455, 1.465), 0.03, 0.05)
    s.sphere((0, 0.46, 1.455), 0.058)                              # bulb tip
    s.ellipsoid((0, 0.14, 1.27), (0.23, 0.20, 0.09))                 # jowl, blends jaw into neck
    s.capsule((0, 0.05, 1.08), (0, 0.07, 1.40), 0.19)              # thick neck
    head, _ = s.remesh(voxel=0.010, smooth=8, smooth_factor=0.6)
    for k in (-1, 1):
        c = Soup('cut_eye'); c.sphere(sx(EYE_L, -k) + Vector((0, 0.022, 0)), EYE_R_BALL + 0.004, seg=32)
        boolean_cut(head, c.to_object())
    c = Soup('cut_mouth'); c.ellipsoid(MOUTH_C + Vector((0, 0.03, 0)), (0.13, 0.10, 0.010), seg=32)
    boolean_cut(head, c.to_object())
    return head

def build_mouth_parts():
    """Dark cavity box and two front teeth. Joined into the head so the jaw keys stretch the box open."""
    cav = Soup('siao_cavity').box(MOUTH_C + Vector((0, -0.115, -0.02)), (0.21, 0.10, 0.08)).to_object()
    set_material(cav, flat_material('siao_mouth', LIN['mouth'], .6))
    teeth = Soup('siao_teeth')
    for x in (-0.034, 0.034): teeth.ellipsoid(MOUTH_C + Vector((x, -0.02, 0.016)), (0.027, 0.016, 0.034), seg=12)
    t = teeth.to_object(); set_material(t, flat_material('siao_teeth', LIN['teeth'], .5))
    return [cav, t]

def build_brows():
    """Heavy dark brows: thick at the inner end, low over the glasses, a point at the outer end."""
    out = []
    for k in (-1, 1):
        b = Soup('siao_brow').capsule((k * 0.05, 0.395, BROW_Z - 0.01), (k * 0.19, 0.375, BROW_Z + 0.005), 0.030, 0.024, seg=10) \
            .capsule((k * 0.19, 0.375, BROW_Z + 0.005), (k * 0.31, 0.27, BROW_Z - 0.02), 0.024, 0.008, seg=10)
        ob, _ = b.remesh(voxel=0.005, smooth=1, target_tris=260)
        set_material(ob, flat_material('siao_brow', LIN['hair'], .8)); out.append(ob)
    return out

# messy side tufts and a back band (centre, radii, euler degrees). Mirrored where x != 0.
HAIR_TUFTS = [
    ((0.335, 0.10, 1.625), (0.024, 0.11, 0.06), (0, 12, -20)),
    ((0.35, -0.06, 1.635), (0.026, 0.14, 0.065), (0, 18, 5)),
    ((0.30, -0.21, 1.595), (0.026, 0.13, 0.06), (0, 22, 40)),
]

def build_hair():
    """Crisp tufts, no remesh, plus three thin strands combed over the dome."""
    s = Soup('siao_hair')
    for c, r, e in HAIR_TUFTS:
        for k in ((-1, 1) if c[0] else (1,)):
            q = Euler((math.radians(e[0]), math.radians(k * e[1]), math.radians(k * e[2]))).to_quaternion()
            s.ellipsoid((k * c[0], c[1], c[2]), r, rot=q, seg=14)
    pts = []                                              # nape band: one low strip wrapping the back of the skull, sunk into the skin
    for j in range(13):
        u = j / 12; t = math.radians(205 + 130 * u); z = 1.475 + 0.015 * math.sin(math.pi * u)
        f = math.sqrt(max(0.0, 1 - ((z - HEAD_C.z) / CRAN[2]) ** 2)) * 0.975
        pts.append((Vector((CRAN[0] * f * math.cos(t), HEAD_C.y + CRAN[1] * f * math.sin(t), z)), 0.007 + 0.016 * math.sin(math.pi * u) ** 0.5))
    for (a, ra), (b, rb) in zip(pts, pts[1:]): s.capsule(a, b, ra, rb, seg=10)
    for i, y0 in enumerate((0.14, 0.01, -0.12)):          # comb-over: three thin strands swept left to right across the dome
        pts = []
        for j, x in enumerate((-0.30, -0.16, -0.02, 0.12, 0.25)):
            y = y0 + 0.025 * math.sin(j * 1.4 + i * 2.0); pts.append(Vector((x, y, dome_z(x, y, 0.0015))))
        for a, b in zip(pts, pts[1:]): s.capsule(a, b, 0.0085, 0.0075, seg=8)
    hair = s.to_object(); shade_smooth(hair)
    set_material(hair, flat_material('siao_hair', LIN['hair'], .8))
    return hair

def build_eyes():
    objs = []
    for name, c in (('eye.l', EYE_L), ('eye.r', EYE_R)):
        o = Soup('siao_' + name).sphere(c, EYE_R_BALL, seg=20).to_object(); shade_smooth(o)
        set_material(o, flat_material('siao_eye', LIN['sclera'], .3)); objs.append(o)
    return objs

def build_glasses():
    """Thick round black rims with a painted-looking white glint strip, no lenses."""
    parts = []; R = 0.105
    for k in (-1, 1):
        c = sx(EYE_L, -k) + Vector((0, 0.105, 0.0))
        parts.append(torus('rim', c, R, 0.014, rot=(math.radians(90), 0, 0), seg=28, rseg=8))
        arm = Soup('temple').capsule((k * (abs(EYE_L.x) + R), c.y - 0.02, c.z + 0.03), (k * 0.395, 0.02, 1.585), 0.008, 0.007, seg=8) \
            .capsule((k * 0.395, 0.02, 1.585), (k * 0.395, -0.03, 1.50), 0.007, 0.006, seg=8).to_object(); shade_smooth(arm); parts.append(arm)
    bx = abs(EYE_L.x) - R
    br = Soup('bridge').capsule((-bx, EYE_L.y + 0.105, EYE_L.z + 0.01), (bx, EYE_L.y + 0.105, EYE_L.z + 0.01), 0.011, seg=8).to_object(); shade_smooth(br); parts.append(br)
    g = join(parts, 'siao_glasses'); set_material(g, flat_material('siao_frame', LIN['frame'], .5))
    return [g]

SWEAT = [(0.31, 1.64), (-0.31, 1.60), (0.27, 1.48)]

def build_sweat_and_drool():
    sw = Soup('siao_sweat')
    for x, z in SWEAT:
        # sit each bead on the cranium or cheek surface (whichever is further forward)
        tc = 1 - (x / CRAN[0]) ** 2 - ((z - HEAD_C.z) / CRAN[2]) ** 2
        yc = HEAD_C.y + CRAN[1] * math.sqrt(max(tc, 0))
        tk = 1 - (x / 0.33) ** 2 - ((z - 1.44) / 0.22) ** 2
        yk = 0.10 + 0.30 * math.sqrt(max(tk, 0))
        sw.ellipsoid((x, max(yc, yk) + 0.002, z), (0.012, 0.010, 0.018), seg=10)
    s = sw.to_object(); shade_smooth(s); set_material(s, flat_material('siao_sweat', LIN['sweat'], .4))
    d = Soup('siao_drool')
    for a, b, r0, r1 in (((0.105, 0.40, 1.345), (0.112, 0.385, 1.31), 0.007, 0.0055), ((0.112, 0.385, 1.31), (0.118, 0.364, 1.275), 0.0055, 0.004), ((0.118, 0.364, 1.275), (0.121, 0.352, 1.25), 0.004, 0.0025)):
        d.capsule(a, b, r0, r1, seg=8)
    d = d.to_object()
    shade_smooth(d); set_material(d, flat_material('siao_drool', LIN['drool'], .12))
    return [s, d]

def claw_soup(s, wrist, side):
    """Chunky hand, fingers spread and hooked like claws. side: +1 right, -1 left.
    Canonical frame: wrist at origin, fingers -Z, palm +Y, thumb +X. Rotated so the palm faces in and the fingers point down and forward."""
    rot = Matrix.Rotation(math.radians(-35), 4, 'X') @ Matrix.Rotation(math.radians(90 * side), 4, 'Z')
    if side < 0: rot = rot @ Matrix.Diagonal((-1, 1, 1, 1))
    T = Matrix.Translation(wrist) @ rot
    def P(x, y, z): return T @ Vector((x, y, z))
    s.ellipsoid(P(0, 0, -0.075), (0.086, 0.034, 0.088), rot=rot)
    s.sphere(P(0, 0, -0.01), 0.05)
    s.ellipsoid(P(0, 0, -0.15), (0.095, 0.032, 0.03), rot=rot)
    fingers = [(-0.075, 0.88, -14), (-0.025, 1.0, -4), (0.025, 0.96, 5), (0.075, 0.78, 15)]
    for x, L, fan in fingers:
        p = Vector((x, 0.0, -0.15)); d = (Matrix.Rotation(math.radians(fan), 3, 'Y') @ Vector((0, 0, -1))).normalized(); r = 0.022
        for seg in (0.052, 0.044, 0.038):
            d = (Matrix.Rotation(math.radians(30), 3, 'X') @ d).normalized()
            q = p + d * seg * L
            s.capsule(P(*p), P(*q), r, r * .88, seg=12); p = q; r *= .88
    p = Vector((0.08, 0.015, -0.06)); d = Vector((0.6, 0.35, -0.7)).normalized(); r = 0.026
    for seg in (0.05, 0.044):
        q = p + d * seg; s.capsule(P(*p), P(*q), r, r * .88, seg=12); p = q; r *= .9
        d = (Matrix.Rotation(math.radians(-30), 3, 'Y') @ d).normalized()
    return s

ARM = {k: (Vector((k * 0.40, 0.0, 1.21)), Vector((k * 0.56, 0.09, 0.95)), Vector((k * 0.56, 0.31, 0.78))) for k in (-1, 1)}  # shoulder, elbow, wrist

def build_upper_skin():
    """Bare shoulders, arms and claw hands, plus the chest skin that shows above the singlet, as one shell."""
    s = Soup('siao_upper')
    s.ellipsoid((0, 0.0, 1.20), (0.40, 0.24, 0.15))
    for k in (-1, 1):
        sh, el, wr = ARM[k]
        s.sphere(sh, 0.135).capsule(sh, el, 0.115, 0.095).sphere(el, 0.10).capsule(el, wr, 0.095, 0.07)
        claw_soup(s, wr, k)
    ob, _ = s.remesh(voxel=0.006, smooth=2, smooth_factor=.4, target_tris=4600)
    set_material(ob, flat_material('siao_skin', LIN['skin'], .6)); return ob

def build_singlet():
    """Cream singlet over a round gut, scoop neck and deep armholes cut out so the skin shows."""
    s = Soup('siao_singlet')
    s.ellipsoid((0, 0.02, 1.10), (0.37, 0.30, 0.27))
    s.sphere((0, 0.13, 0.95), 0.35)                                   # the gut
    s.ellipsoid((0, 0.07, 0.80), (0.38, 0.32, 0.14))                  # hem body
    ob, _ = s.remesh(voxel=0.010, smooth=4, target_tris=3400)
    c = Soup('cut_hem'); c.box((0, 0, 0.30), (2, 2, 0.92)); boolean_cut(ob, c.to_object())   # crisp hem at z 0.76
    c = Soup('cut_neck'); c.sphere((0, 0.36, 1.46), 0.24, seg=32); boolean_cut(ob, c.to_object())
    for k in (-1, 1):
        c = Soup('cut_arm'); c.ellipsoid((k * 0.47, 0.0, 1.20), (0.20, 0.18, 0.22), seg=32); boolean_cut(ob, c.to_object())
    shade_smooth(ob); set_material(ob, flat_material('siao_singlet', LIN['singlet'], .85)); return ob

LEG = {k: (Vector((k * 0.18, 0.05, 0.70)), Vector((k * 0.19, 0.04, 0.42)), Vector((k * 0.19, 0.02, 0.12))) for k in (-1, 1)}  # hip, knee, ankle

def build_shorts():
    s = Soup('siao_shorts')
    s.ellipsoid((0, 0.06, 0.74), (0.39, 0.31, 0.13))
    for k in (-1, 1):
        hp, kn, an = LEG[k]
        s.capsule(hp + Vector((0, 0, 0.02)), kn + Vector((0, 0, 0.03)), 0.18, 0.16)
    ob, _ = s.remesh(voxel=0.010, smooth=4, target_tris=1600)
    set_material(ob, flat_material('siao_shorts', LIN['shorts'], .85)); return ob

def build_legs_feet():
    s = Soup('siao_legs'); sl = Soup('siao_slippers')
    for k in (-1, 1):
        hp, kn, an = LEG[k]
        s.capsule(hp, kn, 0.135, 0.12).sphere(kn, 0.12).capsule(kn, an, 0.12, 0.08)
        s.ellipsoid(kn + Vector((0, -0.03, -0.12)), (0.11, 0.12, 0.14))         # calf
        x = k * 0.19
        s.capsule((x, 0.02, 0.18), (x, 0.04, 0.07), 0.07, 0.065)
        s.ellipsoid((x, 0.10, 0.055), (0.08, 0.15, 0.045))
        for tx, ty, tr in ((0.05, 0.255, 0.032), (0.016, 0.265, 0.028), (-0.016, 0.26, 0.026), (-0.046, 0.245, 0.024)):
            s.sphere((x + k * tx, ty, 0.045), tr, seg=12)
        sl.box((x, 0.09, 0.013), (0.20, 0.40, 0.026))
        sl.capsule((x, 0.215, 0.03), (x + k * 0.085, 0.08, 0.052), 0.013)
        sl.capsule((x, 0.215, 0.03), (x - k * 0.085, 0.08, 0.052), 0.013)
    legs, _ = s.remesh(voxel=0.007, smooth=3, target_tris=2400)
    set_material(legs, flat_material('siao_skin', LIN['skin'], .6))
    slip, _ = sl.remesh(voxel=0.006, smooth=2, target_tris=800)
    set_material(slip, flat_material('siao_slipper', LIN['slipper'], .5))
    return legs, slip

def stage_build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    head = build_head(); set_material(head, flat_material('siao_skin', LIN['skin'], .6))
    decimate(head, 4600); shade_smooth(head)
    head = join([head] + build_mouth_parts() + build_brows(), 'siao_head')
    headgear = join([build_hair()] + build_glasses() + build_sweat_and_drool(), 'siao_headgear')
    eyes = join(build_eyes(), 'siao_eyes')
    legs, slip = build_legs_feet()
    body = join([build_upper_skin(), build_singlet(), build_shorts(), legs, slip], 'siao_body')
    for o in (head, headgear, eyes, body):
        print(f'[build] {o.name}: {tri_count(o)} tris, {len(o.data.materials)} mats')
    print('[build] total tris', sum(tri_count(o) for o in (head, headgear, eyes, body)))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'siao_build.blend'))

def hide_hi():
    for o in bpy.data.objects: o.hide_render = o.name.endswith('_hi') or o.name.startswith('cut')
    h = bpy.data.objects.get('siao_head')
    if h and h.data.shape_keys:
        for k in h.data.shape_keys.key_blocks: k.value = 0.0

def stage_look(tag='look', blend='siao_build.blend'):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, blend))
    hide_hi(); RL.setup_render(1024, 1024, 24); RL.studio_light((0, 0, 1.0)); RL.floor()
    RL.shoot(os.path.join(SHOTS, f'{tag}_front.png'), (0, 6.0, 1.4), (0, 0, 1.0), 60)
    RL.shoot(os.path.join(SHOTS, f'{tag}_three_quarter.png'), (-4.0, 4.4, 1.9), (0, 0, 1.0), 60)
    RL.shoot(os.path.join(SHOTS, f'{tag}_face.png'), (-1.1, 2.2, 1.85), (0, 0.15, 1.55), 85)
    RL.shoot(os.path.join(SHOTS, f'{tag}_hand.png'), (-1.5, 1.4, 0.7), (-0.58, 0.35, 0.62), 100)

# =====================================================================================
# rig
# =====================================================================================
BONES = [
    ('root', (0, 0, 0), (0, 0, 0.25), None),
    ('hips', (0, 0.02, 0.72), (0, 0.02, 0.86), 'root'),
    ('spine', (0, 0.02, 0.86), (0, 0.02, 1.02), 'hips'),
    ('chest', (0, 0.02, 1.02), (0, 0.0, 1.20), 'spine'),
    ('neck', (0, 0.0, 1.20), (0, 0.05, 1.32), 'chest'),
    ('head', (0, 0.05, 1.32), (0, 0.07, 1.75), 'neck'),
    ('eye.l', tuple(EYE_L), tuple(EYE_L + Vector((0, 0.06, 0))), 'head'),
    ('eye.r', tuple(EYE_R), tuple(EYE_R + Vector((0, 0.06, 0))), 'head'),
]
for k, side in ((-1, 'l'), (1, 'r')):
    sh, el, wr = ARM[k]; hp, kn, an = LEG[k]
    BONES += [
        ('upperarm.' + side, tuple(sh), tuple(el), 'chest'),
        ('lowerarm.' + side, tuple(el), tuple(wr), 'upperarm.' + side),
        ('hand.' + side, tuple(wr), tuple(wr + Vector((0, 0.10, -0.16))), 'lowerarm.' + side),
        ('handslot.' + side, tuple(wr + Vector((0, 0.06, -0.10))), tuple(wr + Vector((0, 0.14, -0.10))), 'hand.' + side),
        ('upperleg.' + side, tuple(hp), tuple(kn), 'hips'),
        ('lowerleg.' + side, tuple(kn), tuple(an), 'upperleg.' + side),
        ('foot.' + side, tuple(an), (k * 0.19, 0.16, 0.04), 'lowerleg.' + side),
        ('toes.' + side, (k * 0.19, 0.16, 0.04), (k * 0.19, 0.28, 0.03), 'foot.' + side),
    ]
BONES.append(('prop', (0, 0, 0), (0, 0, 0.3), 'root'))   # no big prop: the bone stays for the contract
RIGID = {'eye.l', 'eye.r', 'prop', 'handslot.l', 'handslot.r'}

def make_armature():
    arm = bpy.data.armatures.new('siao_rig'); ob = bpy.data.objects.new('siao_rig', arm)
    bpy.context.scene.collection.objects.link(ob); select_only([ob], ob)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, h, t, parent in BONES:
        b = arm.edit_bones.new(name); b.head = h; b.tail = t
        if parent: b.parent = arm.edit_bones[parent]; b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in arm.bones: b.use_deform = b.name not in RIGID
    return ob

def auto_weights(rig, obs):
    select_only(obs + [rig], rig)
    with bpy.context.temp_override(active_object=rig, selected_objects=obs + [rig], selected_editable_objects=obs + [rig]):
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')

def rigid_weights(rig, ob, groups):
    for g in list(ob.vertex_groups): ob.vertex_groups.remove(g)
    vg = {b: ob.vertex_groups.new(name=b) for b, _ in groups}
    for v in ob.data.vertices:
        for b, pred in groups:
            if pred(v.co): vg[b].add([v.index], 1.0, 'REPLACE'); break
    ob.parent = rig; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = rig

def add_shape_keys(head):
    me = head.data
    if not me.shape_keys: head.shape_key_add(name='Basis', from_mix=False)
    basis = [v.co.copy() for v in me.vertices]
    mat_of_vert = {}
    for p in me.polygons:
        for vi in p.vertices: mat_of_vert[vi] = p.material_index
    names = [m.name for m in me.materials]
    is_brow = {vi for vi, mi in mat_of_vert.items() if names[mi] == 'siao_brow'}
    is_skin = {vi for vi, mi in mat_of_vert.items() if names[mi] == 'siao_skin'}
    is_teeth = {vi for vi, mi in mat_of_vert.items() if names[mi] == 'siao_teeth'}
    n = len(basis); Z = Vector((0, 0, 0)); comp = {}
    def key(name, fn):
        d = [Z.copy() for _ in range(n)]
        for i, co in enumerate(basis):
            r = fn(i, co)
            if r is not None: d[i] = Vector(r)
        comp[name] = d
    def eye_side(co): return EYE_L if co.x < 0 else EYE_R
    def blink(i, co):
        if i not in is_skin: return None
        E = eye_side(co); w = falloff(co, E, 0.07, 0.17)
        if w <= 0: return None
        if co.z > E.z - 0.015: return (0, 0.018 * w, -0.078 * w * smoothstep(-0.015, 0.05, co.z - E.z))
        return (0, 0.008 * w, 0.02 * w)
    def squint(i, co):
        if i not in is_skin: return None
        E = eye_side(co); w = falloff(co, E, 0.06, 0.17)
        if w <= 0 or co.z > E.z - 0.01: return None
        return (0, 0.01 * w, 0.035 * w)
    def brow_angry(i, co):
        if i in is_brow:
            inner = 1 - smoothstep(0.05, 0.28, abs(co.x))
            return (-0.022 * inner * (1 if co.x > 0 else -1), 0.006, -0.065 * inner + 0.02 * (1 - inner))
        if i in is_skin:
            w = falloff(co, (0, 0.40, BROW_Z), 0.03, 0.12)
            return (0, -0.006 * w, -0.014 * w) if w > 0 else None
        return None
    def brow_up(i, co):
        if i in is_brow:
            outer = smoothstep(0.03, 0.28, abs(co.x)); return (0, -0.004, 0.035 + 0.02 * outer)
        if i in is_skin:
            w = falloff(co, (0, 0.37, BROW_Z + 0.07), 0.05, 0.2) * smoothstep(BROW_Z - 0.03, BROW_Z + 0.05, co.z)
            return (0, 0, 0.012 * w) if w > 0 else None
        return None
    def mouth_open(i, co):
        if i in is_brow or i in is_teeth: return None
        if co.z > MOUTH_C.z + 0.012: return None
        w = falloff(co, (0, 0.28, 1.31), 0.14, 0.32)
        if w <= 0: return None
        drop = smoothstep(0, 0.001, MOUTH_C.z + 0.012 - co.z) * w   # hard step: the decimated slit is only 4 mm tall, so the lower edge must drop as one block
        return (co.x * 0.10 * w, -0.02 * drop, -0.15 * drop)
    def smile(i, co):
        if i in is_brow or i in is_teeth: return None
        s = 1 if co.x > 0 else -1; corner = Vector((s * 0.16, 0.38, MOUTH_C.z + 0.01))
        w = falloff(co, corner, 0.04, 0.14); d = Vector((0, 0, 0))
        if w > 0: d += Vector((s * 0.04 * w, -0.025 * w, 0.06 * w))
        cw = falloff(co, (s * 0.26, 0.26, 1.47), 0.05, 0.18) if i in is_skin else 0
        if cw > 0: d += Vector((0, 0.01 * cw, 0.022 * cw))
        return tuple(d) if d.length > 0 else None
    def frown(i, co):
        if i in is_brow or i in is_teeth: return None
        s = 1 if co.x > 0 else -1; corner = Vector((s * 0.16, 0.38, MOUTH_C.z + 0.01))
        w = falloff(co, corner, 0.04, 0.13)
        return (-s * 0.014 * w, 0, -0.04 * w) if w > 0 else None
    for nm, fn in (('blink', blink), ('squint', squint), ('brow_angry', brow_angry), ('brow_up', brow_up),
                   ('mouth_open', mouth_open), ('smile', smile), ('frown', frown)): key(nm, fn)
    mixes = {
        'angry': {'brow_angry': 1.0, 'frown': 0.6, 'squint': 0.6, 'mouth_open': 0.25},      # snarl, teeth bared
        'grin': {'smile': 0.7, 'squint': 1.0, 'brow_up': 0.5, 'mouth_open': 0.4},
        'ult': {'mouth_open': 1.0, 'brow_angry': 0.8, 'brow_up': 0.3, 'smile': 0.3},        # roar
    }
    export = ['blink', 'mouth_open', 'smile', 'angry', 'grin', 'ult']
    for i in range(n):   # rest face: an open grin, so the two teeth always show
        basis[i] = basis[i] + comp['smile'][i] * 0.55 + comp['mouth_open'][i] * 0.22; me.vertices[i].co = basis[i]
    me.shape_keys.key_blocks['Basis'].data.foreach_set('co', [c for v in basis for c in v])
    for nm in export:
        sk = head.shape_key_add(name=nm, from_mix=False); sk.value = 0.0
        parts = mixes.get(nm, {nm: 1.0})
        for i in range(n):
            d = Vector((0, 0, 0))
            for cn, wgt in parts.items(): d += comp[cn][i] * wgt
            sk.data[i].co = basis[i] + d
    return export

def stage_rig():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'siao_build.blend'))
    head = bpy.data.objects['siao_head']; body = bpy.data.objects['siao_body']
    gear = bpy.data.objects['siao_headgear']; eyes = bpy.data.objects['siao_eyes']
    keys = add_shape_keys(head); print('[rig] shape keys', keys)
    rig = make_armature()
    auto_weights(rig, [body, head])
    for b in rig.data.bones: b.use_deform = True
    rigid_weights(rig, gear, [('head', lambda co: True)])
    rigid_weights(rig, eyes, [('eye.l', lambda co: co.x < 0), ('eye.r', lambda co: True)])
    for ob in (body, head):
        loose = sum(1 for v in ob.data.vertices if not v.groups)
        print(f'[rig] {ob.name}: {loose} unweighted verts of {len(ob.data.vertices)}; groups {[g.name for g in ob.vertex_groups]}')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'siao_rig.blend'))

def stage_expr(blend='siao_rig.blend', tag='expr'):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, blend))
    hide_hi(); RL.setup_render(768, 768, 24); RL.studio_light((0, 0.2, 1.5)); RL.floor()
    head = bpy.data.objects['siao_head']; kb = head.data.shape_keys.key_blocks
    rig = bpy.data.objects.get('siao_rig')
    if rig: reset_pose(rig)
    for nm in ('idle', 'angry', 'grin', 'ult'):
        for k in kb: k.value = 0.0
        if nm != 'idle': kb[nm].value = 1.0
        RL.shoot(os.path.join(SHOTS, f'{tag}_{nm}.png'), (-1.0, 2.4, 1.85), (0, 0.18, 1.53), 85)
    for k in kb: k.value = 0.0

# =====================================================================================
# materials (procedural, baked to atlases)
# =====================================================================================
def mat_skin(m):
    """Tan uncle skin: warm light, mauve shadow, soft strokes, painted lids, lips, stubble shadow, nose and cheek warmth."""
    b = MB(m)
    st = b.strokes(along=(0.25, 1, 0.7), scale=14, levels=3)
    col = b.mix(b.math('MULTIPLY', st, 0.08), c4('skin'), c4('skin_warm'))
    cool = b.math('MAXIMUM', b.grad((0, 0, 1), 1.72, 1.90), b.math('SUBTRACT', 1.0, b.grad((0, 1, 0), -0.02, 0.22)))
    cool = b.math('MAXIMUM', cool, b.blob((0, 0.20, 1.22), 0.06, 0.24))
    col = b.mix(b.math('MULTIPLY', cool, 0.3), col, c4('skin_cool'))
    warm = b.math('MAXIMUM', b.blob((0.25, 0.28, 1.47), 0.05, 0.20, fold_x=True), b.blob((0, 0.47, 1.455), 0.03, 0.10))
    warm = b.math('MAXIMUM', warm, b.math('MULTIPLY', b.blob((0.40, 0.04, 1.54), 0.03, 0.12, fold_x=True), 0.7))
    col = b.mix(b.math('MULTIPLY', warm, 0.7), col, c4('blush'))
    # painted stubble: a cool grey band over the jaw, chin and upper lip, fading up the cheek
    stub = b.math('MULTIPLY', b.blob((0, 0.22, 1.30), 0.16, 0.30), b.math('SUBTRACT', 1.0, b.grad((0, 0, 1), 1.37, 1.46)))
    stub = b.math('MAXIMUM', stub, b.math('MULTIPLY', b.blob((0, 0.44, 1.405), 0.03, 0.08), 0.6))
    stub = b.math('MULTIPLY', stub, b.grad((0, 1, 0), 0.02, 0.18))
    col = b.mix(b.math('MULTIPLY', stub, b.math('ADD', 0.28, b.math('MULTIPLY', b.noise(scale=60, detail=1), 0.18))), col, c4('stubble'))
    z_arm = b.grad((0, 0, 1), 1.24, 1.32); ax = b.math('ABSOLUTE', b.xyz(b.co())[0])
    N_upper = b.vmix(b.step(ax, 0.30, 0.42), b.radial((0, 0.02, 0), follow_z=-0.1), b.radial((0, 0.08, 0), mirror_x=0.53, follow_z=0.0))   # chest skin, arms
    N = b.vmix(z_arm, N_upper, b.radial(tuple(HEAD_C + Vector((0, 0, -0.05)))))
    N = b.vmix(b.grad((0, 0, 1), 0.68, 0.76), b.radial((0, 0.04, 0), mirror_x=0.19, follow_z=-0.1), N)      # legs and feet
    col = b.paint_light(col, c4('skin_warm'), c4('skin_shade'), N=N, sh_amt=0.34, hi_amt=0.5)
    E = (abs(EYE_L.x), EYE_L.y, EYE_L.z); r = EYE_R_BALL; front = b.grad((0, 1, 0), 0.10, 0.22)
    sock = b.math('MULTIPLY', b.blob((E[0], 0.33, E[2] + 0.02), 0.05, 0.13, fold_x=True), b.grad((0, 0, 1), E[2] - 0.02, E[2] + 0.02))
    col = b.mix(b.math('MULTIPLY', sock, 0.35), col, c4('skin_shade'))
    upper = b.math('MULTIPLY', b.ring((E[0], 0, E[2]), r + 0.004, r + 0.016, fold_x=True), b.grad((0, 0, 1), E[2] - 0.01, E[2] + 0.015))
    lower = b.math('MULTIPLY', b.ring((E[0], 0, E[2]), r + 0.004, r + 0.012, fold_x=True), b.math('SUBTRACT', 1.0, b.grad((0, 0, 1), E[2] - 0.04, E[2] - 0.02)))
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', upper, front), 0.85), col, c4('lid'))
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', lower, front), 0.4), col, c4('skin_shade'))   # a bag under each eye, one soft stroke
    col = b.mix(b.math('MULTIPLY', b.blob((0, 0.44, 1.44), 0.02, 0.07), 0.4), col, c4('skin_shade'))
    lips = b.math('SUBTRACT', 1.0, b.step(b.vmath('DISTANCE', b.mapped(b.co(), (1 / 0.16, 0.25, 1 / 0.045)), (0, MOUTH_C.y * 0.25, MOUTH_C.z / 0.045)), 0.75, 1.05))
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', lips, front), 0.8), col, c4('lip'))
    mz = MOUTH_C.z + 0.016
    line = b.math('MAXIMUM', b.seg((0, 0.40, mz), (0.13, 0.40, mz), 0.0025, fold_x=True), b.seg((0.13, 0.40, mz), (0.165, 0.385, mz + 0.03), 0.003, fold_x=True))
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', line, front), 0.85), col, c4('mouth'))
    # inside of the mouth slit (its back wall stretches when the jaw drops): paint it mouth-dark so the opening reads as a cavity, never as lip
    inner = b.math('MULTIPLY', b.math('SUBTRACT', 1.0, b.step(b.vmath('DISTANCE', b.mapped(b.co(), (1 / 0.14, 0, 1 / 0.016)), (0, 0, MOUTH_C.z / 0.016)), 0.9, 1.1)), b.grad((0, 1, 0), 0.30, 0.325))
    col = b.mix(b.math('MULTIPLY', inner, 0.95), col, c4('mouth'))
    b.finish(col, 0.62)

def mat_singlet(m):
    """Cream ribbed cotton, violet shadow, a sweat patch and a kopi stain painted on."""
    b = MB(m)
    st = b.strokes(along=(1, 1, 0.15), scale=12, levels=3)
    base = b.mix(b.math('MULTIPLY', st, 0.4), c4('singlet'), c4('singlet_cool'))
    rib = b.wave(b.mapped(b.co(), (1, 1, 0.1)), scale=70, direction='X')
    base = b.mix(b.math('MULTIPLY', rib, 0.08), base, c4('singlet_cool'))
    sweat = b.blob((0.12, 0.46, 1.02), 0.04, 0.16); sweat = b.math('MULTIPLY', sweat, b.math('ADD', 0.5, b.math('MULTIPLY', b.noise(scale=12, detail=2), 0.6)))
    col = b.mix(b.math('MULTIPLY', sweat, 0.75), base, c4('stain'))
    kopi = b.math('MAXIMUM', b.blob((-0.11, 0.50, 0.86), 0.025, 0.07), b.blob((-0.16, 0.48, 0.80), 0.012, 0.035))
    col = b.mix(b.math('MULTIPLY', kopi, 0.8), col, c4('stain_dark'))
    pits = b.blob((0.36, 0.08, 1.12), 0.04, 0.12, fold_x=True)
    col = b.mix(b.math('MULTIPLY', pits, 0.5), col, c4('stain'))
    col = b.paint_light(col, (1, 0.98, 0.93, 1), c4('singlet_shade'), N=b.radial((0, 0.12, 0), follow_z=-0.1), strokes=st, sh_amt=0.55, hi_amt=0.35)
    folds = None
    for dx, dz, c0 in ((0.55, 0.83, 0.70), (-0.55, 0.83, 0.70), (0.3, 0.95, 0.78), (-0.3, 0.95, 0.78)):
        f = b.math('SUBTRACT', 1.0, b.step(b.math('ABSOLUTE', b.math('SUBTRACT', b.vmath('DOT_PRODUCT', b.co(), (dx, 0, dz)), c0)), 0.008, 0.026))
        f = b.math('MULTIPLY', f, b.math('MULTIPLY', b.grad((0, 1, 0), 0.05, 0.25), b.math('SUBTRACT', 1.0, b.grad((0, 0, 1), 0.95, 1.05))))
        folds = f if folds is None else b.math('MAXIMUM', folds, f)
    col = b.mix(b.math('MULTIPLY', folds, 0.5), col, c4('singlet_shade'))
    b.finish(col, 0.85)

def mat_shorts(m):
    b = MB(m)
    st = b.strokes(along=(1, 1, 0.12), scale=10, levels=3)
    col = b.mix(b.math('MULTIPLY', st, 0.45), c4('shorts'), c4('shorts_light'))
    col = b.paint_light(col, c4('shorts_light'), c4('shorts_shade'), N=b.radial((0, 0.04, 0), mirror_x=0.19, follow_z=-0.1), strokes=st, sh_amt=0.6, hi_amt=0.45)
    b.finish(col, 0.85)

def mat_hair(m):
    """Grey-black strand strokes, a cool rim and a warm sheen band."""
    b = MB(m)
    st = b.strokes(along=(0.15, 1, 0.5), scale=18, levels=4)
    col = b.mix(b.math('MULTIPLY', st, 0.75), c4('hair_deep'), c4('hair_grey'))
    N = b.vmix(0.5, b.radial(tuple(HEAD_C)), b.normal())
    nd = b.vmath('DOT_PRODUCT', N, (-0.45, 0.55, 0.70)); nd = b.math('ADD', nd, b.math('MULTIPLY', b.math('SUBTRACT', st, 0.5), 0.2))
    col = b.mix(b.math('MULTIPLY', b.step(nd, 0.25, 0.55), 0.45), col, c4('hair_cool'))
    col = b.mix(b.math('MULTIPLY', b.step(nd, 0.6, 0.85), 0.85), col, c4('hair_light'))
    b.finish(col, 0.75)

def mat_eye(m):
    """Wide feral stare: small dark iris, plenty of sclera, lid shadow, one catchlight."""
    b = MB(m)
    v = b.vmath('ABSOLUTE', b.co()); d = b.vmath('NORMALIZE', b.vmath('SUBTRACT', v, (abs(EYE_L.x), EYE_L.y, EYE_L.z)))
    dot = b.vmath('DOT_PRODUCT', d, (0.08, 1, -0.05))
    iris = b.step(dot, 0.74, 0.78); pupil = b.step(dot, 0.90, 0.93)
    up = b.vmath('DOT_PRODUCT', d, (0, 0, 1))
    iris_col = b.mix(b.step(up, 0.3, -0.5), c4('iris'), c4('iris_light'))
    col = b.mix(b.step(up, 0.40, 0.60), c4('sclera'), c4('sclera_shade'))
    col = b.mix(iris, col, iris_col); col = b.mix(pupil, col, c4('pupil'))
    col = b.mix(b.math('MULTIPLY', b.step(up, 0.56, 0.68), 0.7), col, c4('lid'))
    hl = b.step(b.vmath('DOT_PRODUCT', d, (-0.25, 0.90, 0.36)), 0.955, 0.97)
    col = b.mix(hl, col, (1, 1, 1, 1))
    # two soft diagonal lens glints, painted on the eye since there is no lens
    band = b.vmath('DOT_PRODUCT', d, (0.707, 0, 0.707)); front = b.step(b.vmath('DOT_PRODUCT', d, (-0.3, 0.85, 0.35)), 0.55, 0.75)
    g1 = b.math('SUBTRACT', 1.0, b.step(b.math('ABSOLUTE', b.math('SUBTRACT', band, 0.05)), 0.05, 0.10))
    g2 = b.math('SUBTRACT', 1.0, b.step(b.math('ABSOLUTE', b.math('SUBTRACT', band, 0.26)), 0.03, 0.07))
    short = b.math('SUBTRACT', 1.0, b.step(b.math('ABSOLUTE', b.math('SUBTRACT', b.vmath('DOT_PRODUCT', d, (0.707, 0, -0.707)), -0.15)), 0.12, 0.26))
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', b.math('MULTIPLY', b.math('MAXIMUM', g1, g2), front), short), 0.28), col, (1, 1, 1, 1))
    b.finish(col, 0.5)

def mat_simple(m, col, rough, metal=0.0, noise_scale=30, noise_amt=0.15, dark=(0.1, 0.1, 0.1, 1)):
    b = MB(m)
    n = b.noise(scale=noise_scale, detail=2)
    c = b.mix(b.math('MULTIPLY', n, noise_amt), c4(col) if isinstance(col, str) else col, dark)
    b.finish(c, b.math('ADD', rough, b.math('MULTIPLY', n, 0.1)), metal)

def build_materials():
    M = bpy.data.materials
    mat_skin(M['siao_skin']); mat_singlet(M['siao_singlet']); mat_shorts(M['siao_shorts']); mat_hair(M['siao_hair']); mat_eye(M['siao_eye'])
    mat_hair(M['siao_brow'])
    mat_simple(M['siao_slipper'], 'slipper', 0.45, noise_scale=8, dark=c4('slipper_dark'), noise_amt=0.4)
    mat_simple(M['siao_frame'], 'frame', 0.5, noise_scale=20, noise_amt=0.2, dark=(0.12, 0.12, 0.14, 1))
    mat_simple(M['siao_sweat'], 'sweat', 0.15, noise_scale=40, noise_amt=0.3, dark=(0.55, 0.75, 0.95, 1))
    mat_simple(M['siao_drool'], 'drool', 0.12, noise_scale=40, noise_amt=0.25, dark=(0.6, 0.8, 0.95, 1))
    mat_simple(M['siao_mouth'], 'mouth', 0.7, noise_scale=8, noise_amt=0.15, dark=(0.08, 0.03, 0.05, 1))
    mat_simple(M['siao_teeth'], 'teeth', 0.5, noise_scale=8, noise_amt=0.1, dark=(0.6, 0.55, 0.5, 1))

ATLAS = {'siao_head': 2048, 'siao_body': 2048, 'siao_headgear': 1024, 'siao_eyes': 256}

def stage_bake():
    import numpy as np
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'siao_rig.blend'))
    build_materials()
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.render.bake.use_pass_direct = False; sc.render.bake.use_pass_indirect = False; sc.render.bake.use_pass_color = True
    sc.render.bake.normal_space = 'TANGENT'
    for o in bpy.data.objects: o.hide_viewport = False
    tex_dir = os.path.join(WORK, 'tex'); os.makedirs(tex_dir, exist_ok=True)
    for name, size in ATLAS.items():
        ob = bpy.data.objects[name]; ob.active_shape_key_index = 0; smart_uv(ob, margin=0.006)
        col = new_image(name + '_col', size); rough = new_image(name + '_rough', size, True)
        met = new_image(name + '_met', size, True); nrm = new_image(name + '_nrm', size, True)
        bake(ob, col, 'DIFFUSE', 1, pass_filter={'COLOR'})
        bake(ob, rough, 'ROUGHNESS', 1)
        bake(ob, nrm, 'NORMAL', 1)
        for slot in ob.material_slots:
            p = slot.material.node_tree.nodes['Principled BSDF']; v = p.inputs['Metallic'].default_value
            p.inputs['Emission Color'].default_value = (v, v, v, 1); p.inputs['Emission Strength'].default_value = 1.0
        bake(ob, met, 'EMIT', 1)
        for slot in ob.material_slots: slot.material.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.0
        c = px(col); r = px(rough)[..., 0:1]; mt = px(met)[..., 0:1]; a = np.ones_like(r)   # AO flat white (Ah Ma lesson)
        base = new_image(name + '_baseColor', size); orm = new_image(name + '_orm', size, True)
        cb = c.copy(); cb[..., 3] = 1; set_px(base, cb)
        set_px(orm, np.concatenate([a, r, mt, np.ones_like(a)], axis=-1))
        if size >= 2048:
            for im in (orm, nrm): im.scale(size // 2, size // 2)
        base.filepath_raw = os.path.join(tex_dir, base.name + '.jpg'); base.file_format = 'JPEG'; base.save(quality=88)
        for im in (orm, nrm): save_png(im, os.path.join(tex_dir, im.name + '.png'))
        for im in (col, rough, met): bpy.data.images.remove(im)
        export_material(ob, base, orm, nrm)
        print(f'[bake] {name}: {size}px baseColor/orm/normal')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'siao_bake.blend'))

# =====================================================================================
# animation: hunched, low, animal body language
# =====================================================================================
FPS = 30
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
ANIM_BONES = ['hips', 'spine', 'chest', 'neck', 'head', 'upperarm.l', 'lowerarm.l', 'hand.l', 'upperarm.r', 'lowerarm.r', 'hand.r',
              'upperleg.l', 'lowerleg.l', 'foot.l', 'upperleg.r', 'lowerleg.r', 'foot.r']

def hips_move(rig, dy, dz):
    pb = rig.pose.bones['hips']; pb.location = rest_mat(rig, 'hips').to_3x3().inverted() @ Vector((0, dy, dz))

def rot(rig, name, rx=0.0, ry=0.0, rz=0.0):
    """World-axis euler in degrees. rx < 0 leans the top forward (+Y). For a leg or arm rx > 0 swings it forward."""
    set_world_rot(rig, rig.pose.bones[name], axis_rot(Z, rz) @ axis_rot(Y, ry) @ axis_rot(X, rx))

def crouch(rig, bend, lift=None):
    """Knees bent `bend` degrees, feet kept flat, hips dropped to match."""
    for side in ('l', 'r'):
        rot(rig, 'upperleg.' + side, rx=bend * 0.5); rot(rig, 'lowerleg.' + side, rx=-bend); rot(rig, 'foot.' + side, rx=bend * 0.5)
    drop = (0.28 + 0.30) * (1 - math.cos(math.radians(bend * 0.5)))
    return -drop if lift is None else lift

def lerp_pose(a, b, u):
    return {k: tuple(a[k][i] + (b[k][i] - a[k][i]) * u for i in range(len(a[k]))) for k in a}

def apply_pose(rig, P):
    for k, v in P.items():
        if k == 'hips_t': hips_move(rig, v[0], v[1])
        else: rot(rig, k, *v)

def keyed(keys, t):
    """keys: [(t, pose dict)], pose dicts share the same keys. Smoothstep between neighbours, hold the ends."""
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = smoothstep(0, 1, (t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return lerp_pose(a, b, u)
    return keys[-1][1]

def pose_frame(rig, t, kind):
    reset_pose(rig)
    s = math.sin(2 * math.pi * t); c = math.cos(2 * math.pi * t)
    if kind == 'idle':
        # low and hunched, weight shifting, a slow head tilt and a quick sniff twitch around a third of the way through
        snf = max(0.0, math.sin(2 * math.pi * (t - 0.30) * 1.0)) ** 10
        twitch = 5.0 * snf * math.sin(2 * math.pi * t * 9)
        rot(rig, 'spine', rx=-6); rot(rig, 'chest', rx=-11 + 1.5 * s, rz=2.0 * c)
        rot(rig, 'neck', rx=4); rot(rig, 'head', rx=9 + twitch - 2 * s, ry=9 * math.sin(2 * math.pi * t + 0.8), rz=-3 * c)
        dz = crouch(rig, 22 + 2 * s)
        hips_move(rig, 0.02, dz + 0.008 * s)
        for k, side in ((-1, 'l'), (1, 'r')):
            rot(rig, 'upperarm.' + side, rx=-6 + 3 * s * k, ry=k * -6, rz=k * -4); rot(rig, 'lowerarm.' + side, rx=10 + 4 * c * k); rot(rig, 'hand.' + side, rx=-10 + 6 * s)
    elif kind == 'run':
        # bounding, low, 18 degree lean, arms swept back and wide like a chasing animal
        rot(rig, 'spine', rx=-9); rot(rig, 'chest', rx=-15, rz=5 * s); rot(rig, 'neck', rx=6); rot(rig, 'head', rx=14, rz=-4 * s, ry=2 * c)
        for k, sg in ((-1, 1), (1, -1)):
            side = 'l' if k < 0 else 'r'; ph = s * sg
            rot(rig, 'upperleg.' + side, rx=12 + 40 * ph)
            rot(rig, 'lowerleg.' + side, rx=-25 - 65 * max(0.0, -ph))
            rot(rig, 'foot.' + side, rx=10 + 20 * max(0.0, -ph))
            rot(rig, 'upperarm.' + side, rx=-72 - 12 * ph, ry=k * -10, rz=k * -24)
            rot(rig, 'lowerarm.' + side, rx=22 - 8 * ph)
            rot(rig, 'hand.' + side, rx=-15)
        hips_move(rig, 0.04, -0.09 + 0.05 * abs(s))
    elif kind == 'attack':
        # haymaker with the right arm: coil, swing across, follow through, recover (ACT.siao in chope.html)
        rest = {'chest': (-9, 0, 0), 'spine': (-5, 0, 0), 'head': (9, 0, 0), 'upperarm.r': (-6, 6, 4), 'lowerarm.r': (10, 0, 0), 'hand.r': (-10, 0, 0),
                'upperarm.l': (-6, -6, -4), 'lowerarm.l': (10, 0, 0), 'hand.l': (-10, 0, 0), 'hips_t': (0.02, -0.01)}
        coil = {'chest': (-14, 0, -28), 'spine': (-6, 0, -10), 'head': (12, 0, 24), 'upperarm.r': (-70, 20, 25), 'lowerarm.r': (70, 0, 0), 'hand.r': (-20, 0, 0),
                'upperarm.l': (25, -10, -10), 'lowerarm.l': (30, 0, 0), 'hand.l': (-10, 0, 0), 'hips_t': (-0.03, -0.015)}
        swing = {'chest': (-20, 0, 30), 'spine': (-10, 0, 14), 'head': (10, 0, -20), 'upperarm.r': (80, -30, -50), 'lowerarm.r': (15, 0, 0), 'hand.r': (-30, 0, 0),
                 'upperarm.l': (-40, -10, -10), 'lowerarm.l': (40, 0, 0), 'hand.l': (-10, 0, 0), 'hips_t': (0.12, -0.02)}
        thru = {'chest': (-18, 0, 38), 'spine': (-10, 0, 16), 'head': (10, 0, -26), 'upperarm.r': (60, -45, -75), 'lowerarm.r': (30, 0, 0), 'hand.r': (-30, 0, 0),
                'upperarm.l': (-45, -10, -10), 'lowerarm.l': (40, 0, 0), 'hand.l': (-10, 0, 0), 'hips_t': (0.10, -0.02)}
        P = keyed([(0.0, rest), (0.28, coil), (0.40, swing), (0.50, thru), (1.0, rest)], t)
        crouch(rig, 20); apply_pose(rig, P)
    elif kind == 'ult':
        # Wild Leap: the pounce. 20 degree lean, arms reaching forward, legs tucked under
        rot(rig, 'spine', rx=-10); rot(rig, 'chest', rx=-12); rot(rig, 'neck', rx=6); rot(rig, 'head', rx=14)
        for k, side in ((-1, 'l'), (1, 'r')):
            rot(rig, 'upperarm.' + side, rx=95, ry=k * -10, rz=k * -22); rot(rig, 'lowerarm.' + side, rx=15); rot(rig, 'hand.' + side, rx=-25)
            rot(rig, 'upperleg.' + side, rx=50 + (10 if k > 0 else 0)); rot(rig, 'lowerleg.' + side, rx=-95); rot(rig, 'foot.' + side, rx=25)
        hips_move(rig, 0.05, 0.22)

def key_all(rig, frame, names):
    for n in names:
        pb = rig.pose.bones[n]; pb.keyframe_insert('rotation_quaternion', frame=frame)
        if n == 'hips': pb.keyframe_insert('location', frame=frame)

def make_action(rig, name, kind, frames, loop=True):
    act = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act
    for f in range(frames + 1):
        t = (f % frames) / frames if loop else min(f, frames) / frames
        bpy.context.scene.frame_set(f); pose_frame(rig, t, kind); key_all(rig, f, ANIM_BONES)
    act.frame_range = (0, frames); act.use_frame_range = True; act.use_fake_user = True; return act

def stage_anim():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'siao_bake.blend'))
    bpy.context.scene.render.fps = FPS
    rig = bpy.data.objects['siao_rig']
    acts = [make_action(rig, 'idle', 'idle', 60), make_action(rig, 'run', 'run', 24), make_action(rig, 'attack', 'attack', 18, loop=False), make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'siao_anim.blend'))
    print('[anim] actions', [a.name for a in acts])

# =====================================================================================
# export + verify + shots
# =====================================================================================
def stage_export():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'siao_anim.blend'))
    rig = bpy.data.objects['siao_rig']; reset_pose(rig)
    for k in bpy.data.objects['siao_head'].data.shape_keys.key_blocks: k.value = 0.0
    objs = [bpy.data.objects[n] for n in ATLAS] + [rig]
    select_only(objs, rig)
    os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
                              export_animations=True, export_animation_mode='ACTIONS', export_nla_strips=True, export_skins=True, export_def_bones=False,
                              export_morph=True, export_morph_normal=False, export_image_format='AUTO', export_materials='EXPORT', export_texcoords=True,
                              export_normals=True, export_tangents=False, export_all_influences=False, export_optimize_animation_size=True)
    print('[export] wrote', OUT_GLB, os.path.getsize(OUT_GLB) // 1024, 'KB')

def stage_verify():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=OUT_GLB)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Icosphere']
    rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in meshes:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co; lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    print(f'[verify] tris {sum(tri_count(o) for o in meshes)}; bounds X {lo.x:.3f}..{hi.x:.3f} height {hi.z - lo.z:.3f} depth(Y) {lo.y:.3f}..{hi.y:.3f}')
    print('[verify] facing: nose at Blender +Y means glTF -Z ->', 'OK' if hi.y > 0.3 else 'WRONG')
    print('[verify] bones', [b.name for b in rig.data.bones])
    hb = rig.matrix_world @ rig.data.bones['head'].head_local; print(f'[verify] head bone head (Blender) {tuple(round(x, 3) for x in hb)}')
    for o in meshes:
        if o.data.shape_keys: print('[verify] morphs on', o.name, [k.name for k in o.data.shape_keys.key_blocks][1:])
        print(f'[verify] {o.name}: {tri_count(o)} tris, mats {[m.name for m in o.data.materials]}')
    print('[verify] animations', [(a.name, int(a.frame_range[1])) for a in bpy.data.actions], 'images', [(i.name, i.size[0]) for i in bpy.data.images])

def stage_shots():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'siao_anim.blend'))
    hide_hi(); RL.setup_render(768, 1024, 32); RL.studio_light((0, 0, 1.0)); RL.floor()
    rig = bpy.data.objects['siao_rig']; tmp = os.path.join(WORK, 'shots'); os.makedirs(tmp, exist_ok=True)
    for k in bpy.data.objects['siao_head'].data.shape_keys.key_blocks: k.value = 0.0
    play(rig, 'idle', 0); paths = []
    for i, ang in enumerate((0, 45, 90, 180)):
        a = math.radians(ang); p = os.path.join(tmp, f'turn_{i}.png'); paths.append(p)
        RL.shoot(p, (-6.0 * math.sin(a), 6.0 * math.cos(a), 1.5), (0, 0, 0.98), 60)
    stitch(paths, os.path.join(SHOTS, 'turnaround.png'), 4)
    RL.setup_render(512, 640, 24); paths = []
    for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
        for i in range(4):
            play(rig, name, int(i * n / 4)); p = os.path.join(tmp, f'{name}_{i}.png'); paths.append(p)
            RL.shoot(p, (-3.8, 4.6, 1.8), (0, 0.2, 0.95), 60)
    stitch(paths, os.path.join(SHOTS, 'anim_sheet.png'), 4)
    play(rig, 'idle', 0)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'ref', 'heroes', 'siao.glb'))
    old = [o for o in bpy.context.selected_objects if o.parent is None]
    for o in old: o.rotation_mode = 'XYZ'; o.location.x += 1.5; o.rotation_euler.z += math.pi   # importer leaves quaternion mode; old glb faces -Y
    for o in bpy.data.objects:
        if o.name == 'Icosphere': o.hide_render = True
    rig.location.x = -1.5
    play(rig, 'idle', 0)
    RL.setup_render(1400, 900, 32)
    RL.shoot(os.path.join(SHOTS, 'side_by_side_old_vs_new.png'), (0, 8.5, 1.5), (0, 0, 1.0), 50)
    print('[shots] turnaround, anim_sheet, side_by_side written')

def stage_expr_final():
    stage_expr('siao_anim.blend', 'expr')
    stitch([os.path.join(SHOTS, f'expr_{n}.png') for n in ('idle', 'angry', 'grin', 'ult')], os.path.join(SHOTS, 'expressions.png'), 4)

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build', 'look']
    for a in args:
        {'build': stage_build, 'look': stage_look, 'rig': stage_rig, 'expr': stage_expr, 'bake': stage_bake, 'anim': stage_anim, 'export': stage_export,
         'verify': stage_verify, 'shots': stage_shots, 'exprfinal': stage_expr_final,
         'looktex': lambda: stage_look('tex', 'siao_bake.blend'), 'exprtex': lambda: stage_expr('siao_bake.blend', 'exprtex')}[a]()
