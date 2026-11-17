"""Gym Hunk, the bruiser. Headless build:
  /opt/homebrew/bin/blender -b -P tools/blender/heroes/gym.py -- build look rig expr bake anim export verify shots exprfinal
Same pipeline as ahma.py. Shared helpers (node builder MB, bake, pose maths) are imported from ahma.py unchanged.
Blender axes: Z up, he faces +Y. The glTF exporter makes that Y up, facing -Z.
Look: chunky local gym bro. Huge chest, delts and arms on short legs, short textured crop with a fade, thick straight brows,
square jaw with painted stubble, black tank and shorts, chunky trainers, violet wrist straps, a 20KG medicine ball cupped in the right hand."""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix, Euler, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
from hero_lib import *
import render_lib as RL
import ahma as A
from ahma import MB, new_image, bake, px, set_px, save_png, export_material, stitch, smoothstep, falloff, rest_mat, set_world_rot, axis_rot, reset_pose, key_all, hips_lift, rigid_weights, auto_weights, hide_hi, mat_simple

WORK = os.environ.get('GYM_WORK', os.path.join(os.environ.get('TMPDIR', '/tmp'), 'gym_work')); os.makedirs(WORK, exist_ok=True)
OUT_GLB = os.path.join(ROOT, 'assets', 'heroes', 'gym.glb')
SHOTS = os.path.join(ROOT, 'shots', 'heroes', 'gym'); os.makedirs(SHOTS, exist_ok=True)

COL = dict(
    skin='#D9A070', skin_cool='#C68A6E', skin_warm='#F3C48E', skin_shade='#8F5A70', blush='#D9785E', lid='#4A2E3A', mouth='#4A1E2C', teeth='#F4EFE4',
    stubble='#7A5A62', hair='#1A1614', hair_light='#4A3228', hair_deep='#1C1426', fade='#A8785A', brow='#1C1720', canvas='#A89468', canvas_dark='#6E5E3E', strap='#2A2630',
    tank='#1E1D24', tank_light='#3C3A52', tank_shade='#0E0C14', violet='#6B3FD4', violet_light='#9B78F0',
    shorts='#15141A', shorts_light='#2E2C40', shoe='#1A191F', shoe_light='#3A3850', sole='#F2EEE6', sock='#F5F1E8', sock_shade='#C9C0D6',
    ball='#1C1B20', ball_light='#3A3848', ball_band='#2E2D36', ball_text='#F2F2F2', shaker='#8A63E8', lid_black='#1C1C22',
    sclera='#FFF7E9', sclera_shade='#E6D6CB', iris='#4A2A1A', iris_light='#8A5A33', pupil='#1A100C',
)
LIN = {k: srgb(v) for k, v in COL.items()}
def c4(k): return (*LIN[k], 1)

# landmarks (metres, Blender Z up, +Y forward)
HEAD_C = Vector((0, 0.0, 1.44))
EYE_L = Vector((-0.125, 0.225, 1.45)); EYE_R = Vector((0.125, 0.225, 1.45)); EYE_RAD = 0.052
MOUTH_C = Vector((0, 0.30, 1.27))
SH = {-1: Vector((-0.50, 0.0, 1.02)), 1: Vector((0.50, 0.0, 1.02))}            # shoulder joints
EL = {-1: Vector((-0.64, 0.02, 0.80)), 1: Vector((0.62, 0.02, 0.80))}
WR = {-1: Vector((-0.66, 0.08, 0.58)), 1: Vector((0.56, 0.30, 0.82))}           # right forearm forward, palm up
BALL_C = WR[1] + Vector((0, 0.09, 0.24)); BALL_R = 0.21
PROP = Vector((0, -0.33, 1.02))

def sx(v, s): return Vector((v.x * s, v.y, v.z))

# =====================================================================================
# geometry
# =====================================================================================
def build_head():
    """Few big clean forms: cranium, cheek planes, one rounded square jaw block, wedge nose, bull neck. Everything else is painted."""
    s = Soup('gym_head_skin')
    s.ellipsoid(HEAD_C, (0.33, 0.32, 0.31))
    s.ellipsoid((0, 0.03, 1.37), (0.315, 0.29, 0.22))       # cheek planes
    for k in (-1, 1): s.ellipsoid((k * 0.12, 0.08, 1.26), (0.20, 0.25, 0.125))   # two lobes make one wide flat-bottomed jaw with rounded corners
    s.ellipsoid((0, 0.18, 1.235), (0.19, 0.09, 0.075))      # chin, flat and wide so it stays one jaw mass
    for k in (-1, 1): s.ellipsoid((k * 0.335, -0.02, 1.42), (0.05, 0.08, 0.10))
    s.capsule((0, 0.29, 1.47), (0, 0.35, 1.36), 0.03, 0.05)  # wedge nose
    s.capsule((0, 0, 1.0), (0, 0.02, 1.26), 0.14)            # bull neck
    head, _ = s.remesh(voxel=0.010, smooth=14, smooth_factor=0.6)
    for k in (-1, 1):   # shallow dish, soft rim
        c = Soup('cut_eye'); c.sphere(sx(EYE_L, -k) + Vector((0, 0.06, 0)), 0.075, seg=32)
        boolean_cut(head, c.to_object())
    c = Soup('cut_mouth'); c.ellipsoid(MOUTH_C + Vector((0, 0.03, 0)), (0.115, 0.10, 0.006), seg=32)
    boolean_cut(head, c.to_object())
    return head

def smooth_lower_face(head, factor=0.5, repeat=5):
    """A few Laplacian passes on the lower head only (below the cheekbones), leaving the mouth slot alone, so the cheek, jaw and chin read as clean convex forms."""
    import bmesh
    bm = bmesh.new(); bm.from_mesh(head.data)
    vs = [v for v in bm.verts if v.co.z < 1.36 and not (abs(v.co.x) < 0.17 and 1.25 < v.co.z < 1.345 and v.co.y > 0.18)]
    for _ in range(repeat): bmesh.ops.smooth_vert(bm, verts=vs, factor=factor, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    # mirror the +X half so the keys pull both corners the same way
    bmesh.ops.symmetrize(bm, input=bm.verts[:] + bm.edges[:] + bm.faces[:], direction='-X', dist=0.001)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(head.data); bm.free()

def build_mouth_parts():
    cav = Soup('gym_cavity').box(MOUTH_C + Vector((0, -0.11, -0.015)), (0.19, 0.10, 0.07)).box(MOUTH_C + Vector((0, -0.135, -0.07)), (0.19, 0.09, 0.07)).to_object()   # upper block sits right behind the lips, lower block steps back so it stays inside the chin   # tall and set back, so the open shout shows a dark floor and the box stays inside the chin
    teeth = Soup('gym_teeth').box(MOUTH_C + Vector((0, -0.03, 0.012)), (0.14, 0.03, 0.02)).to_object()   # bottom edge peeks into the slot: a hint of teeth in the grin
    set_material(cav, flat_material('gym_mouth', LIN['mouth'], .6)); set_material(teeth, flat_material('gym_teeth', LIN['teeth'], .5))
    return [cav, teeth]

def build_brows():
    """Thick straight brows, heavy at the inner end."""
    out = []
    for k in (-1, 1):
        b = Soup('gym_brow').capsule((k * 0.045, 0.315, 1.535), (k * 0.16, 0.300, 1.545), 0.024, 0.020, seg=10) \
            .capsule((k * 0.16, 0.300, 1.545), (k * 0.255, 0.235, 1.535), 0.020, 0.008, seg=10)
        ob, _ = b.remesh(voxel=0.005, smooth=1, target_tris=240)
        set_material(ob, flat_material('gym_brow', LIN['brow'], .7)); out.append(ob)
    return out

def build_hair():
    """Black crop: round cap with a flat raised top, three flat wedges lifting at the front hairline. The fade is painted."""
    s = Soup('gym_hair').ellipsoid(HEAD_C + Vector((0, -0.02, 0.03)), (0.35, 0.34, 0.31), seg=24).ellipsoid((0, 0.04, 1.685), (0.27, 0.24, 0.115), seg=24)
    for x, y, z, tilt in ((0.0, 0.16, 1.715, 0), (0.17, 0.12, 1.705, -18)):   # three flat wedges swept back from the hairline
        for k in ((-1, 1) if x else (1,)):
            q = Quaternion((0, 1, 0), math.radians(k * tilt)) @ Quaternion((1, 0, 0), math.radians(-28))
            s.ellipsoid((k * x, y, z), (0.10, 0.15, 0.03), rot=q, seg=12)
    cap, _ = s.remesh(voxel=0.008, smooth=2, smooth_factor=0.5)
    face = Soup('cut_face').ellipsoid((0, 0.18, 1.33), (0.44, 0.36, 0.31), seg=24).to_object()   # carves the hairline and clears the face and ears
    boolean_cut(cap, face); decimate(cap, 1600)
    cap.name = 'gym_hair'; shade_smooth(cap)
    set_material(cap, flat_material('gym_hair', LIN['hair'], .8)); return cap

def build_eyes():
    objs = []
    for name, c in (('eye.l', EYE_L), ('eye.r', EYE_R)):
        o = Soup('gym_' + name).sphere(c, EYE_RAD, seg=20).to_object(); shade_smooth(o)
        set_material(o, flat_material('gym_eye', LIN['sclera'], .2)); objs.append(o)
    return join(objs, 'gym_eyes')

def hand_soup(s, wrist, rot, mirror=False, curl=28):
    """Chunky hand, four fingers and a thumb. curl is the bend per knuckle: 28 relaxed, 62 a loose fist.
    Canonical frame: wrist at origin, fingers -Z, palm normal +Y, thumb +X."""
    if mirror: rot = rot @ Matrix.Diagonal((-1, 1, 1, 1))
    T = Matrix.Translation(wrist) @ rot
    def P(x, y, z): return T @ Vector((x, y, z))
    s.ellipsoid(P(0, 0, -0.08), (0.088, 0.036, 0.09), rot=rot)
    s.sphere(P(0, 0, -0.01), 0.055)
    s.ellipsoid(P(0, 0.0, -0.16), (0.095, 0.034, 0.03), rot=rot)
    for x, L in ((-0.075, 0.9), (-0.025, 1.0), (0.025, 0.95), (0.075, 0.78)):
        p = Vector((x, 0.0, -0.16)); d = Vector((0, 0, -1)); r = 0.023
        for seg in (0.05, 0.04, 0.034):
            d = (Matrix.Rotation(math.radians(curl), 3, 'X') @ d).normalized()
            q = p + d * seg * L; s.capsule(P(*p), P(*q), r, r * .9, seg=12); p = q; r *= .9
    p = Vector((0.08, 0.015, -0.06)); d = Vector((0.5, 0.5, -0.7)).normalized(); r = 0.027
    for seg in (0.05, 0.04):
        q = p + d * seg; s.capsule(P(*p), P(*q), r, r * .88, seg=12); p = q; r *= .9
        d = (Matrix.Rotation(math.radians(-25 - (curl - 28)), 3, 'Y') @ d).normalized()
    return s

def build_arm(k):
    """Skin arm: delt, thick upper arm with a biceps bulge, forearm, hand. Right hand is cupped palm up for the ball."""
    s = Soup('gym_arm'); sh, el, wr = SH[k], EL[k], WR[k]
    s.sphere(sh, 0.165)                                                   # delt
    s.capsule(sh + Vector((k * 0.02, 0, -0.04)), el, 0.13, 0.105)
    s.ellipsoid((sh + el) * .5 + Vector((0, 0.05, 0)), (0.125, 0.13, 0.15))   # biceps
    s.sphere(el, 0.10)
    s.capsule(el, wr, 0.105, 0.075)
    if k > 0: hand_soup(s, wr, Matrix.Rotation(math.radians(90), 4, 'X'))      # palm up, fingers forward
    else: hand_soup(s, wr, Matrix.Rotation(math.radians(-90), 4, 'Z'), mirror=True, curl=62)   # loose fist at the side, reads as a fist in the flex
    arm, hi = s.remesh(voxel=0.0055, smooth=2, smooth_factor=.4, target_tris=2300, keep_hi=True)
    set_material(arm, flat_material('gym_skin', LIN['skin'], .55)); return arm, hi

def build_core():
    """Skin under the tank: traps rising from the shoulders to the neck, so the scoop neckline shows a real yoke."""
    s = Soup('gym_core'); s.ellipsoid((0, -0.01, 1.01), (0.36, 0.25, 0.10)); s.capsule((0, 0, 0.98), (0, 0.02, 1.2), 0.14)
    for k in (-1, 1): s.ellipsoid((k * 0.25, -0.02, 1.08), (0.22, 0.13, 0.075), rot=Quaternion((0, 1, 0), math.radians(k * -22)))   # traps
    core, hi = s.remesh(voxel=0.010, smooth=3, target_tris=1300, keep_hi=True)
    set_material(core, flat_material('gym_skin', LIN['skin'], .55)); return core, hi

def build_tank():
    s = Soup('gym_tank')
    s.ellipsoid((0, 0.02, 0.97), (0.47, 0.29, 0.21))
    for k in (-1, 1): s.box((k * 0.21, 0.19, 0.99), (0.24, 0.16, 0.17))        # squared pec shelf
    for k in (-1, 1): s.ellipsoid((k * 0.30, -0.06, 0.90), (0.17, 0.20, 0.17))  # lats
    s.ellipsoid((0, -0.02, 1.00), (0.40, 0.26, 0.11))                            # upper back
    s.ellipsoid((0, 0.03, 0.82), (0.24, 0.19, 0.15))                             # waist
    s.capsule((0, 0.03, 0.80), (0, 0.03, 0.72), 0.24, 0.26, seg=32)              # hem
    tank, hi = s.remesh(voxel=0.010, smooth=6, target_tris=3200, keep_hi=True)
    for ob in (tank, hi):
        c = Soup('cut_scoop').ellipsoid((0, 0.22, 1.12), (0.19, 0.26, 0.11), seg=24).ellipsoid((0, -0.22, 1.14), (0.17, 0.20, 0.10), seg=24)
        for k in (-1, 1): c.sphere(SH[k], 0.175, seg=24)
        boolean_cut(ob, c.to_object())
    shade_smooth(tank); set_material(tank, flat_material('gym_tank', LIN['tank'], .8)); return tank, hi

def build_shorts():
    s = Soup('gym_shorts'); s.ellipsoid((0, 0.02, 0.66), (0.30, 0.25, 0.12))
    for k in (-1, 1): s.capsule((k * 0.15, 0.02, 0.66), (k * 0.165, 0.0, 0.46), 0.15, 0.14)
    sh, hi = s.remesh(voxel=0.010, smooth=4, target_tris=1500, keep_hi=True)
    set_material(sh, flat_material('gym_shorts', LIN['shorts'], .85)); return sh, hi

def build_legs():
    s = Soup('gym_legs')
    for k in (-1, 1):
        x = k * 0.165
        s.capsule((x, 0, 0.50), (x, 0, 0.36), 0.12, 0.10); s.sphere((x, 0.01, 0.36), 0.10)
        s.capsule((x, 0, 0.36), (x, 0, 0.11), 0.10, 0.065); s.ellipsoid((x, -0.04, 0.27), (0.09, 0.10, 0.11))   # calf
    legs, hi = s.remesh(voxel=0.008, smooth=3, target_tris=1400, keep_hi=True)
    set_material(legs, flat_material('gym_skin', LIN['skin'], .55)); return legs, hi

def build_feet():
    sk = Soup('gym_socks'); sh = Soup('gym_shoes')
    for k in (-1, 1):
        x = k * 0.165
        sk.capsule((x, 0.01, 0.16), (x, 0.01, 0.08), 0.075)
        sh.ellipsoid((x, 0.08, 0.065), (0.10, 0.175, 0.065)); sh.sphere((x, 0.22, 0.05), 0.062); sh.sphere((x, -0.07, 0.07), 0.07)
        sh.box((x, 0.08, 0.018), (0.21, 0.37, 0.036))
    socks, skh = sk.remesh(voxel=0.006, smooth=2, target_tris=400, keep_hi=True)
    set_material(socks, flat_material('gym_sock', LIN['sock'], .8))
    shoes, shh = sh.remesh(voxel=0.006, smooth=3, target_tris=1600, keep_hi=True)
    set_material(shoes, flat_material('gym_shoe', LIN['shoe'], .5)); return socks, skh, shoes, shh

def build_trim():
    out = []
    s = torus('gym_strap_l', tuple(WR[-1] + Vector((0, 0, 0.02))), 0.085, 0.016, rot=(math.radians(-15), 0, 0), seg=20, rseg=8)
    r = torus('gym_strap_r', tuple(WR[1] + Vector((0, -0.03, 0))), 0.085, 0.016, rot=(math.radians(90), 0, 0), seg=20, rseg=8)
    for o in (s, r): set_material(o, flat_material('gym_strap', LIN['violet'], .7)); out.append(o)
    shk = Soup('gym_shaker').capsule((-0.33, 0.15, 0.60), (-0.33, 0.15, 0.74), 0.045, 0.048, seg=14).to_object(); shade_smooth(shk)
    set_material(shk, flat_material('gym_shaker', LIN['shaker'], .3)); out.append(shk)
    lid = Soup('gym_lid').capsule((-0.33, 0.15, 0.74), (-0.33, 0.15, 0.77), 0.05, 0.04, seg=14).to_object(); shade_smooth(lid)
    set_material(lid, flat_material('gym_lid', LIN['lid_black'], .5)); out.append(lid)
    return out

def build_sandbag():
    """Old kit's sandbag on the back: rounded canvas block with two painted straps. Rigid to the prop bone."""
    b, _ = Soup('gym_prop').box(tuple(PROP), (0.46, 0.13, 0.30)).remesh(voxel=0.008, smooth=6, smooth_factor=0.7, target_tris=500)
    set_material(b, flat_material('gym_canvas', LIN['canvas'], .9)); return b

def build_ball():
    b = Soup('gym_ball').sphere(BALL_C, BALL_R, seg=32).to_object(); shade_smooth(b)
    set_material(b, flat_material('gym_ball', LIN['ball'], .85)); return b

def stage_build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    head = build_head(); set_material(head, flat_material('gym_skin', LIN['skin'], .55))
    head_hi = head.copy(); head_hi.data = head.data.copy(); head_hi.name = 'gym_head_hi'; bpy.context.scene.collection.objects.link(head_hi)
    decimate(head, 4600); shade_smooth(head); smooth_lower_face(head)
    head = join([head] + build_mouth_parts() + build_brows(), 'gym_head')
    headgear = build_hair(); headgear.name = 'gym_headgear'
    eyes = build_eyes()
    parts = []; hi = [head_hi]
    for k in (-1, 1):
        a, ah = build_arm(k); parts.append(a); hi.append(ah)
    for fn in (build_core, build_tank, build_shorts, build_legs):
        o, oh = fn(); parts.append(o); hi.append(oh)
    so, soh, sh, shh = build_feet(); parts += [so, sh]; hi += [soh, shh]
    parts += build_trim()
    body = join(parts, 'gym_body'); ball = build_ball(); bag = build_sandbag()
    hi_col = bpy.data.collections.new('hi'); bpy.context.scene.collection.children.link(hi_col)
    for h in hi:
        for c in h.users_collection: c.objects.unlink(h)
        hi_col.objects.link(h); h.hide_render = True; h.hide_viewport = True
    for o in (head, headgear, eyes, body, ball, bag): print(f'[build] {o.name}: {tri_count(o)} tris, {len(o.data.materials)} mats')
    print('[build] total tris', sum(tri_count(o) for o in (head, headgear, eyes, body, ball, bag)))
    zs = [v.co.z for o in (head, headgear, body) for v in o.data.vertices]; xs = [abs(v.co.x) for o in (body, ball) for v in o.data.vertices]
    print(f'[build] height {max(zs) - min(zs):.3f} (z {min(zs):.3f}..{max(zs):.3f}), max |x| {max(xs):.3f}')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'gym_build.blend'))

def stage_look(tag='look', blend='gym_build.blend'):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, blend))
    hide_hi(); RL.setup_render(1024, 1024, 24); RL.studio_light((0, 0, 0.95)); RL.floor()
    sk = bpy.data.objects['gym_head'].data.shape_keys
    if sk:
        for k in sk.key_blocks: k.value = 0.0
    if 'gym_rig' in bpy.data.objects: reset_pose(bpy.data.objects['gym_rig'])
    RL.shoot(os.path.join(SHOTS, f'{tag}_front.png'), (0, 5.6, 1.3), (0, 0, 0.92), 60)
    RL.shoot(os.path.join(SHOTS, f'{tag}_three_quarter.png'), (-3.8, 4.2, 1.8), (0, 0, 0.92), 60)
    RL.shoot(os.path.join(SHOTS, f'{tag}_face.png'), (-1.0, 2.0, 1.7), (0, 0.1, 1.42), 85)
    RL.shoot(os.path.join(SHOTS, f'{tag}_hand.png'), (1.5, 1.6, 1.0), (0.6, 0.35, 0.9), 90)
    RL.shoot(os.path.join(SHOTS, f'{tag}_ball.png'), (BALL_C.x, BALL_C.y + 2.0, BALL_C.z + 0.1), tuple(BALL_C), 110)

# =====================================================================================
# rig
# =====================================================================================
BONES = [
    ('root', (0, 0, 0), (0, 0, 0.25), None),
    ('hips', (0, 0, 0.64), (0, 0, 0.78), 'root'),
    ('spine', (0, 0, 0.78), (0, 0, 0.92), 'hips'),
    ('chest', (0, 0, 0.92), (0, 0, 1.04), 'spine'),
    ('neck', (0, 0, 1.04), (0, 0.01, 1.20), 'chest'),
    ('head', (0, 0.01, 1.20), (0, 0.02, 1.58), 'neck'),
    ('eye.l', tuple(EYE_L), tuple(EYE_L + Vector((0, 0.06, 0))), 'head'),
    ('eye.r', tuple(EYE_R), tuple(EYE_R + Vector((0, 0.06, 0))), 'head'),
    ('upperarm.l', tuple(SH[-1]), tuple(EL[-1]), 'chest'), ('lowerarm.l', tuple(EL[-1]), tuple(WR[-1]), 'upperarm.l'),
    ('hand.l', tuple(WR[-1]), tuple(WR[-1] + Vector((0, 0.03, -0.18))), 'lowerarm.l'),
    ('handslot.l', tuple(WR[-1] + Vector((0, 0.02, -0.12))), tuple(WR[-1] + Vector((0, 0.10, -0.12))), 'hand.l'),
    ('upperarm.r', tuple(SH[1]), tuple(EL[1]), 'chest'), ('lowerarm.r', tuple(EL[1]), tuple(WR[1]), 'upperarm.r'),
    ('hand.r', tuple(WR[1]), tuple(WR[1] + Vector((0, 0.18, 0.02))), 'lowerarm.r'),
    ('handslot.r', tuple(BALL_C), tuple(BALL_C + Vector((0, 0.1, 0))), 'hand.r'),
    ('upperleg.l', (-0.15, 0.02, 0.66), (-0.165, 0.0, 0.36), 'hips'), ('lowerleg.l', (-0.165, 0.0, 0.36), (-0.165, 0.0, 0.10), 'upperleg.l'),
    ('foot.l', (-0.165, 0.0, 0.10), (-0.165, 0.12, 0.03), 'lowerleg.l'), ('toes.l', (-0.165, 0.12, 0.03), (-0.165, 0.26, 0.02), 'foot.l'),
    ('upperleg.r', (0.15, 0.02, 0.66), (0.165, 0.0, 0.36), 'hips'), ('lowerleg.r', (0.165, 0.0, 0.36), (0.165, 0.0, 0.10), 'upperleg.r'),
    ('foot.r', (0.165, 0.0, 0.10), (0.165, 0.12, 0.03), 'lowerleg.r'), ('toes.r', (0.165, 0.12, 0.03), (0.165, 0.26, 0.02), 'foot.r'),
    ('prop', tuple(PROP), tuple(PROP + Vector((0, 0, 0.3))), 'root'),
]
RIGID = {'eye.l', 'eye.r', 'prop', 'handslot.l', 'handslot.r'}

def make_armature():
    arm = bpy.data.armatures.new('gym_rig'); ob = bpy.data.objects.new('gym_rig', arm)
    bpy.context.scene.collection.objects.link(ob); select_only([ob], ob)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, h, t, parent in BONES:
        b = arm.edit_bones.new(name); b.head = h; b.tail = t
        if parent: b.parent = arm.edit_bones[parent]; b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in arm.bones: b.use_deform = b.name not in RIGID
    return ob

def add_shape_keys(head):
    me = head.data
    if not me.shape_keys: head.shape_key_add(name='Basis', from_mix=False)
    basis = [v.co.copy() for v in me.vertices]
    mat_of_vert = {}
    for p in me.polygons:
        for vi in p.vertices: mat_of_vert[vi] = p.material_index
    names = [m.name for m in me.materials]
    is_brow = {vi for vi, mi in mat_of_vert.items() if names[mi] == 'gym_brow'}
    is_cav = {vi for vi, mi in mat_of_vert.items() if names[mi] == 'gym_mouth'}   # the cavity stays put: it is the dark floor behind the dropped jaw
    is_skin = {vi for vi, mi in mat_of_vert.items() if names[mi] == 'gym_skin'}
    n = len(basis); Z = Vector((0, 0, 0)); comp = {}
    NZ = [v.normal.z for v in me.vertices]   # decimation merges the slot edges in z, so the normal tells upper lip from lower
    def key(name, fn):
        d = [Z.copy() for _ in range(n)]
        for i, co in enumerate(basis):
            r = fn(i, co)
            if r is not None: d[i] = Vector(r)
        comp[name] = d
    def eye_side(co): return EYE_L if co.x < 0 else EYE_R
    def blink(i, co):
        if i not in is_skin: return None
        E = eye_side(co); w = falloff(co, E, 0.065, 0.16)
        if w <= 0: return None
        if co.z > E.z - 0.015: return (0, 0.018 * w, -0.07 * w * smoothstep(-0.015, 0.05, co.z - E.z))
        return (0, 0.008 * w, 0.02 * w)
    def squint(i, co):
        if i not in is_skin: return None
        E = eye_side(co); w = falloff(co, E, 0.055, 0.16)
        if w <= 0 or co.z > E.z - 0.01: return None
        return (0, 0.008 * w, 0.02 * w)
    def brow_angry(i, co):
        if i in is_brow:
            inner = 1 - smoothstep(0.04, 0.24, abs(co.x))
            return (-0.02 * inner * (1 if co.x > 0 else -1), 0.006, -0.055 * inner + 0.015 * (1 - inner))
        if i in is_skin:
            w = falloff(co, (0, 0.31, 1.52), 0.03, 0.12)
            return (0, -0.006 * w, -0.014 * w) if w > 0 else None
        return None
    def brow_up(i, co):
        if i in is_brow:
            outer = smoothstep(0.03, 0.24, abs(co.x)); return (0, -0.004, 0.035 + 0.02 * outer)
        if i in is_skin:
            w = falloff(co, (0, 0.30, 1.58), 0.05, 0.18) * smoothstep(1.50, 1.57, co.z)
            return (0, 0, 0.012 * w) if w > 0 else None
        return None
    def mouth_open(i, co):
        if i in is_brow or i in is_cav or co.z > MOUTH_C.z + 0.012: return None
        w = falloff(co, (0, 0.24, 1.24), 0.10, 0.30)
        if w <= 0: return None
        band = MOUTH_C.z + 0.012 - co.z
        if band < 0.016 and NZ[i] < 0.15: return None   # upper slot edge faces down: it stays
        drop = smoothstep(0.0, 0.010, band) * w   # everything below the cut drops in full
        return (co.x * 0.15 * w, -0.012 * drop, -0.09 * drop)
    def smile(i, co):
        if i in is_brow: return None
        s = 1 if co.x > 0 else -1; corner = Vector((s * 0.15, 0.29, 1.275))
        w = falloff(co, corner, 0.03, 0.14); d = Vector((0, 0, 0))
        if w > 0: d += Vector((s * 0.03 * w, -0.015 * w, 0.0))
        # the lip band lifts on a parabola, so the mouth line curves instead of kinking at the centre
        bw = (1 - smoothstep(0.03, 0.07, abs(co.z - MOUTH_C.z))) * (1 - smoothstep(0.17, 0.22, abs(co.x))) if (i in is_skin and co.y > 0.22) else 0
        if bw > 0: d += Vector((0, 0, (0.010 + 0.030 * min(1.0, (abs(co.x) / 0.15) ** 2)) * bw))
        cw = falloff(co, (s * 0.22, 0.18, 1.36), 0.05, 0.17) if i in is_skin else 0
        if cw > 0: d += Vector((0, 0.006 * cw, 0.012 * cw))
        return tuple(d) if d.length > 0 else None
    def lip_up(i, co):
        """Upper lip lifts off the teeth: a band just above the slot."""
        if i not in is_skin or co.y < 0.24 or abs(co.x) > 0.16: return None
        w = (1 - smoothstep(0.0, 0.035, co.z - (MOUTH_C.z + 0.006))) * (1 - smoothstep(0.09, 0.16, abs(co.x)))
        if co.z < MOUTH_C.z + 0.004 or w <= 0: return None
        return (0, 0.004 * w, 0.014 * w)
    def frown(i, co):
        if i in is_brow: return None
        s = 1 if co.x > 0 else -1; w = falloff(co, (s * 0.15, 0.29, 1.275), 0.04, 0.12)
        return (-s * 0.014 * w, 0, -0.04 * w) if w > 0 else None
    for nm, fn in (('blink', blink), ('squint', squint), ('brow_angry', brow_angry), ('brow_up', brow_up), ('mouth_open', mouth_open), ('smile', smile), ('lip_up', lip_up), ('frown', frown)): key(nm, fn)
    mixes = {'angry': {'brow_angry': 1.0, 'frown': 1.0, 'blink': 0.35, 'mouth_open': 0.15},
             'grin': {'smile': 1.0, 'squint': 0.5, 'brow_up': 0.6, 'mouth_open': 0.12, 'lip_up': 0.6},
             'ult': {'mouth_open': 1.0, 'brow_angry': 0.7, 'brow_up': 0.4, 'smile': 0.3, 'lip_up': 0.6}}
    export = ['blink', 'mouth_open', 'smile', 'angry', 'grin', 'ult']
    for i in range(n):   # rest face: a slight cocky smile
        basis[i] = basis[i] + comp['smile'][i] * 0.3; me.vertices[i].co = basis[i]
    me.shape_keys.key_blocks['Basis'].data.foreach_set('co', [c for v in basis for c in v])
    for nm in export:
        sk = head.shape_key_add(name=nm, from_mix=False)
        for i in range(n):
            d = Vector((0, 0, 0))
            for cn, wgt in mixes.get(nm, {nm: 1.0}).items(): d += comp[cn][i] * wgt
            sk.data[i].co = basis[i] + d
    return export

def stage_rig():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'gym_build.blend'))
    O = bpy.data.objects; head, body, gear, eyes, ball = O['gym_head'], O['gym_body'], O['gym_headgear'], O['gym_eyes'], O['gym_ball']
    print('[rig] shape keys', add_shape_keys(head))
    rig = make_armature()
    auto_weights(rig, [body, head])
    for b in rig.data.bones: b.use_deform = True
    rigid_weights(rig, gear, [('head', lambda co: True)])
    rigid_weights(rig, eyes, [('eye.l', lambda co: co.x < 0), ('eye.r', lambda co: True)])
    rigid_weights(rig, ball, [('handslot.r', lambda co: True)]); rigid_weights(rig, O['gym_prop'], [('prop', lambda co: True)])
    deform = [b for b in rig.data.bones if b.name not in RIGID and b.name != 'root']
    for ob in (body, head):
        loose = [v for v in ob.data.vertices if not v.groups]
        for v in loose:   # small loose parts (straps, shaker) miss the heat solve: pin them rigidly
            b = 'hips' if abs(v.co.x) < 0.45 else ('hand.l' if v.co.x < 0 else 'hand.r')
            ob.vertex_groups[b].add([v.index], 1.0, 'REPLACE')
        print(f'[rig] {ob.name}: {len(loose)} unweighted verts of {len(ob.data.vertices)} sent to nearest bone')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'gym_rig.blend'))

def stage_expr(blend='gym_rig.blend', tag='expr'):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, blend))
    hide_hi(); RL.setup_render(768, 768, 24); RL.studio_light((0, 0.2, 1.4)); RL.floor()
    head = bpy.data.objects['gym_head']; kb = head.data.shape_keys.key_blocks
    rig = bpy.data.objects.get('gym_rig')
    if rig: reset_pose(rig)
    for nm in ('idle', 'angry', 'grin', 'ult'):
        for k in kb: k.value = 0.0
        if nm != 'idle': kb[nm].value = 1.0
        RL.shoot(os.path.join(SHOTS, f'{tag}_{nm}.png'), (-0.95, 2.2, 1.72), (0, 0.15, 1.42), 85)
    for k in kb: k.value = 0.0

# =====================================================================================
# materials
# =====================================================================================
def mat_skin(m):
    b = MB(m)
    st = b.strokes(along=(0.25, 1, 0.7), scale=14, levels=3)
    col = b.mix(0.02, c4('skin'), c4('skin_warm'))   # no stroke texture on skin: it read as scratches
    cool = b.math('MAXIMUM', b.grad((0, 0, 1), 1.52, 1.66), b.math('SUBTRACT', 1.0, b.grad((0, 1, 0), -0.05, 0.18)))
    col = b.mix(b.math('MULTIPLY', cool, 0.35), col, c4('skin_cool'))
    cheeks = b.math('MAXIMUM', b.blob((0.21, 0.20, 1.37), 0.03, 0.15, fold_x=True), b.blob((0, 0.37, 1.39), 0.01, 0.06))
    col = b.mix(b.math('MULTIPLY', cheeks, 0.4), col, c4('blush'))
    # stubble as one soft tone: chin and jawline, nothing dotted
    jaw = b.math('MAXIMUM', b.blob((0, 0.24, 1.19), 0.04, 0.14), b.seg((0.06, 0.27, 1.17), (0.25, 0.10, 1.25), 0.05, fold_x=True))
    jaw = b.math('MULTIPLY', jaw, b.math('SUBTRACT', 1.0, b.grad((0, 0, 1), 1.29, 1.34)))
    col = b.mix(b.math('MULTIPLY', jaw, 0.22), col, c4('stubble'))
    # designed normals: head above the collar, arms and neck between, legs below
    ax = b.math('ABSOLUTE', b.xyz(b.co())[0]); y = b.xyz(b.co())[1]
    fwd = b.vmath('NORMALIZE', b.vmath('SUBTRACT', b.co(), b.combine(WR[1].x, y, WR[1].z)))   # right forearm runs forward along Y
    arm_r = b.vmix(b.math('MULTIPLY', b.step(ax, 0.30, 0.42), b.step(y, 0.12, 0.22)), b.radial((0, 0.03, 0), mirror_x=0.58, follow_z=0.0), fwd)
    mid = b.vmix(b.step(ax, 0.30, 0.40), b.radial((0, 0.0, 0), follow_z=0.0), arm_r)
    N = b.vmix(b.grad((0, 0, 1), 1.16, 1.24), mid, b.radial((0, 0.03, 1.38)))
    N = b.vmix(b.grad((0, 0, 1), 0.52, 0.60), b.radial((0, 0.0, 0), mirror_x=0.165, follow_z=-0.05), N)
    col = b.paint_light(col, c4('skin_warm'), c4('skin_shade'), N=N, sh_amt=0.55, hi_amt=0.5)
    # mouth: painted lip shape with a confident smirk (one corner higher). +X is screen left seen from the front.
    lips = b.math('SUBTRACT', 1.0, b.step(b.vmath('DISTANCE', b.mapped(b.co(), (1 / 0.14, 0.25, 1 / 0.036)), (0, MOUTH_C.y * 0.25, MOUTH_C.z / 0.036)), 0.75, 1.05))
    col = b.mix(b.math('MULTIPLY', lips, 0.6), col, c4('skin_cool'))
    mz = MOUTH_C.z + 0.002
    line = b.math('MAXIMUM', b.seg((-0.11, 0.30, mz), (0.11, 0.30, mz), 0.0025), b.seg((0.11, 0.30, mz), (0.135, 0.293, mz + 0.010), 0.0024, fold_x=True))
    col = b.mix(b.math('MULTIPLY', line, 0.8), col, c4('mouth'))
    b.finish(col, 0.6)

def mat_hair(m):
    """Black crop: warm brown-black strands brushed front to back on top, painted skin fade at the sides and back."""
    b = MB(m)
    st = b.strokes(along=(0.3, 1, 0.3), scale=18, levels=4)
    col = b.mix(b.math('MULTIPLY', st, 0.25), c4('hair'), c4('hair_light'))
    strand = b.step(b.noise(b.mapped(b.co(), (0.25, 1, 0.35)), scale=36, detail=1.0, rough=.45), 0.55, 0.59)
    col = b.mix(b.math('MULTIPLY', strand, 0.5), col, c4('hair_deep'))
    N = b.vmix(0.4, b.radial((0, -0.02, 1.46)), b.normal())
    nd = b.vmath('DOT_PRODUCT', N, (-0.45, 0.55, 0.70)); nd = b.math('ADD', nd, b.math('MULTIPLY', b.math('SUBTRACT', st, 0.5), 0.16))
    col = b.mix(b.math('MULTIPLY', b.math('SUBTRACT', 1.0, b.step(nd, -0.2, 0.05)), 0.5), col, c4('hair_deep'))
    col = b.mix(b.math('MULTIPLY', b.step(nd, 0.6, 0.9), 0.45), col, c4('hair_light'))
    ax = b.math('ABSOLUTE', b.xyz(b.co())[0]); y = b.xyz(b.co())[1]
    low = b.math('SUBTRACT', 1.0, b.grad((0, 0, 1), 1.44, 1.56))
    fade = b.math('MULTIPLY', b.math('MAXIMUM', b.step(ax, 0.22, 0.33), b.math('SUBTRACT', 1.0, b.step(y, -0.32, -0.20))), low)
    col = b.mix(b.math('MULTIPLY', fade, 0.9), col, b.mix(b.math('MULTIPLY', dots_of(b), 0.45), c4('fade'), c4('hair')))
    b.finish(col, 0.85)

def dots_of(b): return b.step(b.noise(scale=120, detail=1), 0.5, 0.56)

def mat_eye(m):
    b = MB(m)
    v = b.vmath('ABSOLUTE', b.co()); d = b.vmath('NORMALIZE', b.vmath('SUBTRACT', v, (abs(EYE_L.x), EYE_L.y, EYE_L.z)))
    dot = b.vmath('DOT_PRODUCT', d, (0, 1, 0))
    iris = b.step(dot, 0.64, 0.68); pupil = b.step(dot, 0.88, 0.91)
    up = b.vmath('DOT_PRODUCT', d, (0, 0, 1))
    iris_col = b.mix(b.step(up, 0.3, -0.5), c4('iris'), c4('iris_light'))
    col = b.mix(b.step(up, 0.40, 0.60), c4('sclera'), c4('sclera_shade'))
    col = b.mix(iris, col, iris_col); col = b.mix(pupil, col, c4('pupil'))
    col = b.mix(b.math('MULTIPLY', b.step(up, 0.52, 0.64), 0.75), col, c4('lid'))
    col = b.mix(b.step(b.vmath('DOT_PRODUCT', d, (-0.25, 0.90, 0.36)), 0.955, 0.97), col, (1, 1, 1, 1))
    b.finish(col, 0.5)

def mat_cloth(m, base, light, shade, N, stripe=None, stroke_axis=(1, 1, 0.15), rough=.85, sh_amt=.6, hi_amt=.45):
    b = MB(m)
    st = b.strokes(along=stroke_axis, scale=12, levels=3)
    col = b.mix(b.math('MULTIPLY', st, 0.45), c4(base), c4(light))
    col = b.paint_light(col, c4(light), c4(shade), N=N(b), strokes=st, sh_amt=sh_amt, hi_amt=hi_amt)
    if stripe: col = stripe(b, col)
    b.finish(col, rough)

def mat_tank(m):
    def N(b): return b.radial((0, 0.02, 0), follow_z=-0.12)
    def stripe(b, col):
        front = b.grad((0, 1, 0), 0.16, 0.24)
        seam = b.math('MULTIPLY', b.seg((0, 0.34, 1.06), (0, 0.30, 0.86), 0.007), front)
        pec = b.math('MULTIPLY', b.seg((0.05, 0.33, 0.86), (0.36, 0.26, 0.92), 0.012, fold_x=True), front)
        fold = b.math('MULTIPLY', b.seg((-0.22, 0.26, 0.80), (0.18, 0.24, 0.76), 0.010), front)
        col = b.mix(b.math('MULTIPLY', b.math('MAXIMUM', b.math('MAXIMUM', seam, pec), fold), 0.75), col, c4('tank_shade'))
        hi = b.math('MULTIPLY', b.seg((-0.33, 0.30, 1.03), (0.05, 0.33, 0.83), 0.035), front)            # one broad highlight stroke across the pecs
        col = b.mix(b.math('MULTIPLY', hi, 0.55), col, c4('tank_light'))
        bar = b.math('MULTIPLY', b.seg((-0.15, 0.33, 0.97), (0.15, 0.33, 0.97), 0.034), front)
        side = b.math('MULTIPLY', b.seg((0.44, 0, 0.95), (0.25, 0, 0.73), 0.02, fold_x=True), b.math('SUBTRACT', 1.0, b.grad((0, 1, 0), -0.02, 0.06)))
        hem = b.math('MULTIPLY', b.grad((0, 0, 1), 0.705, 0.715), b.math('SUBTRACT', 1.0, b.grad((0, 0, 1), 0.725, 0.735)))
        return b.mix(b.math('MAXIMUM', b.math('MAXIMUM', bar, side), hem), col, c4('violet'))
    mat_cloth(m, 'tank', 'tank_light', 'tank_shade', N, stripe, rough=.85)

def mat_shorts(m):
    def stripe(b, col):
        s = b.math('MULTIPLY', b.seg((0.30, 0, 0.70), (0.31, 0, 0.48), 0.012, fold_x=True), b.step(b.math('ABSOLUTE', b.xyz(b.co())[0]), 0.22, 0.27))
        return b.mix(s, col, c4('violet'))
    mat_cloth(m, 'shorts', 'shorts_light', 'tank_shade', lambda b: b.radial((0, 0.01, 0), mirror_x=0.16, follow_z=-0.05), stripe, rough=.9)

def mat_shoe(m):
    def stripe(b, col):
        sole = b.math('SUBTRACT', 1.0, b.grad((0, 0, 1), 0.034, 0.042))
        flash = b.seg((0.19, 0.16, 0.07), (0.09, -0.02, 0.10), 0.012, fold_x=True, flat=(1, 1, 0))
        return b.mix(b.math('MULTIPLY', flash, 0.9), b.mix(sole, col, c4('sole')), c4('violet'))
    mat_cloth(m, 'shoe', 'shoe_light', 'tank_shade', lambda b: b.radial((0, 0.08, 0.02), mirror_x=0.165, follow_z=None), stripe, stroke_axis=(1, 0.2, 1), rough=.55, hi_amt=.5)

def mat_ball(m):
    """Black rubber med ball, a lighter band round the middle with 20KG painted in it."""
    b = MB(m)
    n = b.noise(scale=40, detail=2); col = b.mix(b.math('MULTIPLY', n, 0.3), c4('ball'), c4('ball_light'))
    band = b.math('SUBTRACT', 1.0, b.step(b.math('ABSOLUTE', b.math('SUBTRACT', b.xyz(b.co())[2], BALL_C.z)), 0.045, 0.055))
    col = b.mix(band, col, c4('ball_band'))
    segs = {'2': [((0, 1), (1, 1)), ((1, 1), (1, .5)), ((1, .5), (0, .5)), ((0, .5), (0, 0)), ((0, 0), (1, 0))],
            '0': [((0, 0), (1, 0)), ((1, 0), (1, 1)), ((1, 1), (0, 1)), ((0, 1), (0, 0))],
            'K': [((0, 0), (0, 1)), ((0, .5), (1, 1)), ((0, .5), (1, 0))],
            'G': [((1, 1), (0, 1)), ((0, 1), (0, 0)), ((0, 0), (1, 0)), ((1, 0), (1, .5)), ((1, .5), (.5, .5))]}
    text = None; w, h, gap = 0.032, 0.05, 0.016; x0 = BALL_C.x + (4 * w + 3 * gap) / 2; z0 = BALL_C.z - h / 2   # +X is screen left seen from the front
    for i, ch in enumerate('20KG'):
        for (ax_, az), (bx, bz) in segs[ch]:
            s = b.seg((x0 - i * (w + gap) - ax_ * w, 0, z0 + az * h), (x0 - i * (w + gap) - bx * w, 0, z0 + bz * h), 0.006)
            text = s if text is None else b.math('MAXIMUM', text, s)
    text = b.math('MULTIPLY', text, b.grad((0, 1, 0), BALL_C.y + 0.08, BALL_C.y + 0.12))   # front face only
    col = b.mix(text, col, c4('ball_text'))
    col = b.paint_light(col, c4('ball_light'), (0.03, 0.02, 0.05, 1), N=b.radial(tuple(BALL_C)), sh_amt=0.5, hi_amt=0.35)
    b.bump(n, strength=0.15, distance=0.002)
    b.finish(col, 0.85)

def mat_canvas(m):
    b = MB(m)
    n = b.noise(scale=30, detail=2); col = b.mix(b.math('MULTIPLY', n, 0.35), c4('canvas'), c4('canvas_dark'))
    straps = b.math('MAXIMUM', b.seg((-0.12, PROP.y, 0.80), (-0.12, PROP.y, 1.25), 0.025, flat=(1, 0, 1)), b.seg((0.12, PROP.y, 0.80), (0.12, PROP.y, 1.25), 0.025, flat=(1, 0, 1)))
    col = b.mix(straps, col, c4('strap'))
    col = b.paint_light(col, c4('canvas'), c4('canvas_dark'), N=b.radial(tuple(PROP)), sh_amt=0.5, hi_amt=0.3)
    b.finish(col, 0.9)

def build_materials():
    M = bpy.data.materials; mat_canvas(M['gym_canvas'])
    mat_skin(M['gym_skin']); mat_hair(M['gym_hair']); mat_eye(M['gym_eye']); mat_tank(M['gym_tank']); mat_shorts(M['gym_shorts']); mat_shoe(M['gym_shoe']); mat_ball(M['gym_ball'])
    mat_simple(M['gym_brow'], c4('brow'), 0.7, noise_scale=12, noise_amt=0.15, dark=c4('hair_light'))
    mat_simple(M['gym_mouth'], c4('mouth'), 0.7, noise_scale=8, noise_amt=0.15, dark=(0.08, 0.03, 0.05, 1))
    mat_simple(M['gym_teeth'], c4('teeth'), 0.5, noise_scale=8, noise_amt=0.1, dark=(0.6, 0.55, 0.5, 1))
    mat_simple(M['gym_sock'], c4('sock'), 0.8, noise_scale=20, noise_amt=0.3, dark=c4('sock_shade'))
    mat_simple(M['gym_strap'], c4('violet'), 0.7, noise_scale=30, noise_amt=0.3, dark=(0.12, 0.06, 0.3, 1))
    mat_simple(M['gym_shaker'], c4('shaker'), 0.3, noise_scale=20, noise_amt=0.3, dark=c4('violet'))
    mat_simple(M['gym_lid'], c4('lid_black'), 0.5, noise_amt=0.1)

ATLAS = {'gym_head': 2048, 'gym_body': 2048, 'gym_headgear': 1024, 'gym_ball': 1024, 'gym_prop': 512, 'gym_eyes': 256}

def stage_bake():
    import numpy as np
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'gym_rig.blend'))
    build_materials()
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.render.bake.use_pass_direct = False; sc.render.bake.use_pass_indirect = False; sc.render.bake.use_pass_color = True
    sc.render.bake.normal_space = 'TANGENT'
    for o in list(bpy.data.objects):
        if o.name.endswith('_hi'): bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects: o.hide_viewport = False
    tex_dir = os.path.join(WORK, 'tex'); os.makedirs(tex_dir, exist_ok=True)
    for name, size in ATLAS.items():
        ob = bpy.data.objects[name]; ob.active_shape_key_index = 0; smart_uv(ob, margin=0.006)
        col = new_image(name + '_col', size); rough = new_image(name + '_rough', size, True); met = new_image(name + '_met', size, True); nrm = new_image(name + '_nrm', size, True)
        bake(ob, col, 'DIFFUSE', 1, pass_filter={'COLOR'}); bake(ob, rough, 'ROUGHNESS', 1); bake(ob, nrm, 'NORMAL', 1)
        for slot in ob.material_slots:
            p = slot.material.node_tree.nodes['Principled BSDF']; v = p.inputs['Metallic'].default_value
            p.inputs['Emission Color'].default_value = (v, v, v, 1); p.inputs['Emission Strength'].default_value = 1.0
        bake(ob, met, 'EMIT', 1)
        for slot in ob.material_slots: slot.material.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.0
        c = px(col); r = px(rough)[..., 0:1]; mt = px(met)[..., 0:1]; a = np.ones_like(r)   # AO flat white, the paint carries the shading
        base = new_image(name + '_baseColor', size); orm = new_image(name + '_orm', size, True)
        cb = c.copy(); cb[..., 3] = 1; set_px(base, cb); set_px(orm, np.concatenate([a, r, mt, np.ones_like(a)], axis=-1))
        if size >= 2048:
            for im in (orm, nrm): im.scale(size // 2, size // 2)
        base.filepath_raw = os.path.join(tex_dir, base.name + '.jpg'); base.file_format = 'JPEG'; base.save(quality=88)
        for im in (orm, nrm): save_png(im, os.path.join(tex_dir, im.name + '.png'))
        for im in (col, rough, met): bpy.data.images.remove(im)
        export_material(ob, base, orm, nrm); print(f'[bake] {name}: {size}px')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'gym_bake.blend'))

# =====================================================================================
# animation
# =====================================================================================
FPS = 30
ANIM_BONES = ['hips', 'spine', 'chest', 'neck', 'head', 'upperarm.l', 'lowerarm.l', 'hand.l', 'upperarm.r', 'lowerarm.r', 'hand.r',
              'upperleg.l', 'lowerleg.l', 'foot.l', 'upperleg.r', 'lowerleg.r', 'foot.r', 'prop']

class Pose:
    """World-space rotations stacked down the chain (set_world_rot is relative to the parent's posed frame)."""
    def __init__(self, rig): self.rig = rig; reset_pose(rig); self.q = {}
    def acc(self, name):
        b = self.rig.data.bones[name]; q = self.acc(b.parent.name) if b.parent else Quaternion()
        return q @ self.q.get(name, Quaternion())
    def rot(self, name, q): self.q[name] = q; set_world_rot(self.rig, self.rig.pose.bones[name], q)
    def aim(self, name, d, roll=0.0):
        """Point the bone along world direction d (minimal rotation from rest, then roll about the bone)."""
        b = self.rig.data.bones[name]; pq = self.acc(b.parent.name) if b.parent else Quaternion()
        rest = (b.tail_local - b.head_local).normalized(); q = rest.rotation_difference(pq.inverted() @ Vector(d).normalized())
        if roll: q = Quaternion(q @ rest, math.radians(roll)) @ q
        self.rot(name, q)

X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)

def pose_frame(rig, t, kind):
    P = Pose(rig); s = math.sin(2 * math.pi * t); c = math.cos(2 * math.pi * t)
    if kind == 'idle':   # breathe, shift the ball a little, look around
        P.rot('chest', axis_rot(X, 2.5 * s) @ axis_rot(Z, 1.0 * c)); P.rot('head', axis_rot(X, -1.5 * s) @ axis_rot(Z, 3.0 * c))
        P.rot('upperarm.l', axis_rot(Y, -3 - 2 * s)); P.rot('upperarm.r', axis_rot(X, 3 * s)); P.rot('lowerarm.r', axis_rot(X, 4 * s))
        hips_lift(rig, 0.008 * s)
    elif kind == 'run':
        for k, sg in ((-1, 1), (1, -1)):
            side = 'l' if k < 0 else 'r'
            P.rot('upperleg.' + side, axis_rot(X, 38 * s * sg)); P.rot('lowerleg.' + side, axis_rot(X, -55 * max(0.0, -s * sg)))
            P.rot('foot.' + side, axis_rot(X, 15 * max(0.0, -s * sg)))
        P.rot('spine', axis_rot(X, 5)); P.rot('chest', axis_rot(X, 8) @ axis_rot(Z, 5 * s)); P.rot('head', axis_rot(X, -8) @ axis_rot(Z, -4 * s))
        P.rot('upperarm.l', axis_rot(X, -35 * s) @ axis_rot(Y, -12)); P.rot('lowerarm.l', axis_rot(X, 60))      # pumping arm
        P.rot('upperarm.r', axis_rot(X, 25 + 10 * s) @ axis_rot(Y, 8)); P.rot('lowerarm.r', axis_rot(X, 20))     # ball hugged up and forward
        hips_lift(rig, 0.035 * abs(s) - 0.015)
    elif kind == 'attack':   # raise the ball overhead, slam it down in front, recover
        if t < 0.33: u = t / 0.33; raise_ = 130 * math.sin(u * math.pi / 2); lean = -12 * u
        elif t < 0.55: u = (t - 0.33) / 0.22; raise_ = 130 - 115 * u * u; lean = -12 + 32 * u
        else: u = (t - 0.55) / 0.45; raise_ = 15 * (1 - u); lean = 20 * (1 - u)
        P.rot('spine', axis_rot(X, lean * 0.5)); P.rot('chest', axis_rot(X, lean)); P.rot('head', axis_rot(X, -lean * 0.6))
        P.rot('upperarm.r', axis_rot(X, raise_) @ axis_rot(Y, -10)); P.rot('lowerarm.r', axis_rot(X, 20 * (1 - abs(raise_ - 65) / 65)))
        P.rot('upperarm.l', axis_rot(X, -0.35 * raise_) @ axis_rot(Y, -15)); P.rot('lowerarm.l', axis_rot(X, 40))
        hips_lift(rig, -0.05 if 0.33 <= t < 0.7 else 0.0)
    elif kind == 'ult':   # Runner's High: double biceps flex, chest out, roar
        P.rot('spine', axis_rot(X, -4)); P.rot('chest', axis_rot(X, -8)); P.rot('head', axis_rot(X, -10))
        for k in (-1, 1):
            side = 'l' if k < 0 else 'r'
            P.aim('upperarm.' + side, (k * 0.95, 0.12, 0.25)); P.aim('lowerarm.' + side, (k * 0.35, 0.15, 0.92))
            P.aim('hand.' + side, (k * 0.1, 0.2, 0.95) if k < 0 else (0.1, 0.35, 0.92))
    return P

def make_action(rig, name, kind, frames, loop=True):
    act = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act
    for f in range(frames + 1):
        t = (f % frames) / frames if loop else min(f, frames) / frames
        bpy.context.scene.frame_set(f); pose_frame(rig, t, kind); key_all(rig, f, ANIM_BONES)
    act.frame_range = (0, frames); act.use_frame_range = True; act.use_fake_user = True; return act

def stage_anim():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'gym_bake.blend'))
    bpy.context.scene.render.fps = FPS; rig = bpy.data.objects['gym_rig']
    acts = [make_action(rig, 'idle', 'idle', 60), make_action(rig, 'run', 'run', 24), make_action(rig, 'attack', 'attack', 18, loop=False), make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'gym_anim.blend')); print('[anim] actions', [a.name for a in acts])

# =====================================================================================
# export, verify, shots
# =====================================================================================
def stage_export():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'gym_anim.blend'))
    rig = bpy.data.objects['gym_rig']; reset_pose(rig)
    for k in bpy.data.objects['gym_head'].data.shape_keys.key_blocks: k.value = 0.0
    objs = [bpy.data.objects[n] for n in ATLAS] + [rig]; select_only(objs, rig)
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
                              export_animations=True, export_animation_mode='ACTIONS', export_nla_strips=True, export_skins=True, export_def_bones=False,
                              export_morph=True, export_morph_normal=False, export_image_format='AUTO', export_materials='EXPORT', export_texcoords=True,
                              export_normals=True, export_tangents=False, export_all_influences=False, export_optimize_animation_size=True)
    print('[export] wrote', OUT_GLB, os.path.getsize(OUT_GLB) // 1024, 'KB')

def stage_verify():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=OUT_GLB)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('Icosphere')]
    rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in meshes:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co; lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    print(f'[verify] tris {sum(tri_count(o) for o in meshes)}; bounds X {lo.x:.3f}..{hi.x:.3f} height {hi.z - lo.z:.3f} depth(Y) {lo.y:.3f}..{hi.y:.3f}')
    print('[verify] facing (nose at Blender +Y = glTF -Z):', 'OK' if hi.y > 0.3 else 'WRONG')
    print('[verify] bones', [b.name for b in rig.data.bones])
    hb = rig.matrix_world @ rig.data.bones['head'].head_local; print(f'[verify] head bone head (Blender) {tuple(round(x, 3) for x in hb)}')
    for o in meshes:
        if o.data.shape_keys: print('[verify] morphs on', o.name, [k.name for k in o.data.shape_keys.key_blocks][1:])
        print(f'[verify] {o.name}: {tri_count(o)} tris, mats {[m.name for m in o.data.materials]}')
    print('[verify] animations', [a.name for a in bpy.data.actions], 'images', [(i.name, i.size[0]) for i in bpy.data.images])

def play(rig, name, frame):
    rig.animation_data.action = bpy.data.actions[name]; bpy.context.scene.frame_set(frame)

def stage_shots():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'gym_anim.blend'))
    hide_hi(); RL.setup_render(768, 1024, 32); RL.studio_light((0, 0, 0.95)); RL.floor()
    rig = bpy.data.objects['gym_rig']; tmp = os.path.join(WORK, 'shots'); os.makedirs(tmp, exist_ok=True)
    for k in bpy.data.objects['gym_head'].data.shape_keys.key_blocks: k.value = 0.0
    play(rig, 'idle', 0); paths = []
    for i, ang in enumerate((0, 45, 90, 180)):
        a = math.radians(ang); p = os.path.join(tmp, f'turn_{i}.png'); paths.append(p)
        RL.shoot(p, (-5.6 * math.sin(a), 5.6 * math.cos(a), 1.4), (0, 0, 0.92), 60)
    stitch(paths, os.path.join(SHOTS, 'turnaround.png'), 4)
    RL.setup_render(512, 640, 24); paths = []
    for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
        for i in range(4):
            play(rig, name, int(i * n / 4)); p = os.path.join(tmp, f'{name}_{i}.png'); paths.append(p)
            RL.shoot(p, (-3.6, 4.3, 1.7), (0, 0.2, 0.9), 60)
    stitch(paths, os.path.join(SHOTS, 'anim_sheet.png'), 4)
    play(rig, 'idle', 0)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'ref', 'heroes', 'gym.glb'))
    for o in [o for o in bpy.context.selected_objects if o.parent is None]: o.location.x += 1.4
    for o in bpy.data.objects:
        if o.name.startswith('Icosphere'): o.hide_render = True
    rig.location.x = -1.4; play(rig, 'idle', 0)
    RL.setup_render(1400, 900, 32)
    RL.shoot(os.path.join(SHOTS, 'side_by_side_old_vs_new.png'), (0, 7.5, 1.4), (0, 0, 0.95), 50)
    print('[shots] turnaround, anim_sheet, side_by_side written')

def stage_expr_final():
    stage_expr('gym_anim.blend', 'expr')
    stitch([os.path.join(SHOTS, f'expr_{n}.png') for n in ('idle', 'angry', 'grin', 'ult')], os.path.join(SHOTS, 'expressions.png'), 4)

def stage_jpeg():
    """JPEG previews in the scratchpad for a quick look."""
    out = os.environ.get('GYM_PREVIEW', WORK); bpy.ops.wm.read_factory_settings(use_empty=True)
    tag = os.environ.get('GYM_TAG', '')
    for src, dst in (('expressions.png', f'gym_expr{tag}.jpg'), ('turnaround.png', f'gym_turn{tag}.jpg')):
        im = bpy.data.images.load(os.path.join(SHOTS, src), check_existing=False); _ = im.pixels[0]; im.filepath_raw = os.path.join(out, dst); im.file_format = 'JPEG'; im.save(quality=85)
        print('[jpeg]', im.filepath_raw)

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build', 'look']
    for a in args:
        {'build': stage_build, 'look': stage_look, 'rig': stage_rig, 'expr': stage_expr, 'bake': stage_bake, 'anim': stage_anim, 'export': stage_export,
         'verify': stage_verify, 'shots': stage_shots, 'exprfinal': stage_expr_final, 'jpeg': stage_jpeg,
         'looktex': lambda: stage_look('tex', 'gym_bake.blend'), 'exprtex': lambda: stage_expr('gym_bake.blend', 'exprtex')}[a]()
