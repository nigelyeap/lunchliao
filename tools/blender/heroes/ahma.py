"""Ah Ma, the Gate 1 hero. Headless build:
  /opt/homebrew/bin/blender -b -P tools/blender/heroes/ahma.py -- [build] [rig] [bake] [export] [shots]
Stages save a .blend in the scratchpad (AHMA_WORK env or /tmp) so later stages can be re-run alone.
Blender axes: Z up, she faces +Y. The glTF exporter makes that Y up, facing -Z."""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Euler, Quaternion, kdtree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
from hero_lib import *
import render_lib as RL

WORK = os.environ.get('AHMA_WORK', '/tmp/ahma_work'); os.makedirs(WORK, exist_ok=True)
OUT_GLB = os.path.join(ROOT, 'assets', 'heroes', 'ahma.glb')
SHOTS = os.path.join(ROOT, 'shots', 'heroes', 'ahma'); os.makedirs(SHOTS, exist_ok=True)
TEX = 2048

# ---------------- palette (sRGB hex, converted to linear for nodes) ----------------
COL = dict(
    skin='#E8B58C', skin_cool='#D6A283', skin_warm='#F5CFA4', skin_shade='#B07A94', blush='#E2907A', lip='#CF6A70', lid='#5A3A50', mouth='#4A1E2C', tongue='#D9767C', teeth='#F4EFE4', gold='#D8A94A',
    hair='#2A242E', hair_mid='#3A3148', hair_dark='#17121F', hair_deep='#1A2E36', hair_light='#5C4C4C', hair_grey='#B7B0BC', scalp='#6B636E', brow='#3E3440', blouse='#F8EEDB', blouse_cool='#E6DCCF', blouse_shade='#C4B8CF', floral_a='#E9A6B8', floral_b='#93BEDC', floral_leaf='#9CC39A', piping='#9A6E9E',
    slacks='#34405C', slacks_dark='#232A42', slacks_shade='#1C2038', slipper='#D7322E', slipper_dark='#9E1F1C', metal='#B8BCC2', rubber='#3A3C40', basket='#C8302A', rattan='#B98447',
    jade='#4FA47A', frame='#C9A054', sclera='#FFF7E9', sclera_shade='#E6D6CB', iris='#2B1B15', iris_light='#523226', pupil='#241612', pocket='#EFE3C8', balm='#D9892E',
)
LIN = {k: srgb(v) for k, v in COL.items()}

# ---------------- key landmarks (metres, Blender Z up, +Y forward) ----------------
HEAD_C = Vector((0, 0.0, 1.60))
EYE_L = Vector((-0.165, 0.268, 1.60)); EYE_R = Vector((0.165, 0.268, 1.60))
EYE_R_BALL = 0.062
MOUTH_C = Vector((0, 0.34, 1.385))
WALKER_PIVOT = Vector((0, 0.70, 0))

def sx(v, s):  # mirror helper
    return Vector((v.x * s, v.y, v.z))

# =====================================================================================
# geometry
# =====================================================================================
def build_head():
    """Clean simple planes: a cranium, a rounded jaw box (cheekbone plane and jaw line), a small chin and a wedge nose.
    Age, lids, lips and cheeks are painted in mat_skin, nothing is sculpted."""
    s = Soup('ahma_head_skin')
    s.ellipsoid(HEAD_C, (0.42, 0.38, 0.37))                       # cranium, broader and rounder
    s.ellipsoid((0, 0.05, 1.48), (0.36, 0.31, 0.20))               # lower face: full round cheek mass, the planes are painted
    s.ellipsoid((0, 0.12, 1.37), (0.27, 0.26, 0.11))               # jaw narrows toward the chin
    s.sphere((0, 0.27, 1.315), 0.08)                               # small simple chin
    for k in (-1, 1):
        s.ellipsoid((k * 0.405, -0.02, 1.56), (0.05, 0.09, 0.12))  # ears
    s.capsule((0, 0.33, 1.60), (0, 0.385, 1.505), 0.026, 0.040)    # low soft nose bridge
    s.sphere((0, 0.395, 1.49), 0.045)                              # small rounded tip
    for k in (-1, 1): s.sphere((k * 0.038, 0.365, 1.485), 0.030)   # soft alae
    s.capsule((0, 0, 1.18), (0, 0.02, 1.42), 0.14)                 # neck
    head, head_hi = s.remesh(voxel=0.010, smooth=8, smooth_factor=0.6, keep_hi=False)
    # small eye sockets so the lid rims hold the eyeballs, and a thin mouth cut the painted lip line covers at rest
    for k in (-1, 1):   # almond openings, outer corner a touch higher; the ball sits deeper so the lids cover its top and bottom
        c = Soup('cut_eye'); c.ellipsoid(sx(EYE_L, -k) + Vector((0, 0.05, 0)), (0.078, 0.07, 0.036), rot=Quaternion((0, 1, 0), math.radians(-k * 6)), seg=32)
        boolean_cut(head, c.to_object())
    c = Soup('cut_mouth'); c.ellipsoid(MOUTH_C + Vector((0, 0.03, 0)), (0.125, 0.10, 0.006), seg=32)
    boolean_cut(head, c.to_object())
    return head

def build_mouth_parts():
    """Flat dark interior with a hint of teeth. Joined into the head so the jaw keys stretch the box open."""
    cav = Soup('ahma_cavity').box(MOUTH_C + Vector((0, -0.10, -0.02)), (0.24, 0.10, 0.10)).to_object()   # stays inside the curved cheeks
    teeth = Soup('ahma_teeth').box(MOUTH_C + Vector((0, -0.03, 0.026)), (0.15, 0.03, 0.022)).to_object()   # sits above the jaw split, so it stays with the upper lip
    set_material(cav, flat_material('ahma_mouth', LIN['mouth'], .6))
    set_material(teeth, flat_material('ahma_teeth', LIN['teeth'], .5))
    return [cav, teeth]

def build_brows():
    """Thin clean wedges with a designed silhouette: thick at the inner end, a point at the outer end."""
    out = []
    for k in (-1, 1):
        b = Soup('ahma_brow').capsule((k * 0.06, 0.352, 1.694), (k * 0.17, 0.332, 1.708), 0.016, 0.013, seg=10) \
            .capsule((k * 0.17, 0.332, 1.708), (k * 0.29, 0.258, 1.692), 0.013, 0.005, seg=10)
        ob, _ = b.remesh(voxel=0.005, smooth=1, target_tris=220)
        set_material(ob, flat_material('ahma_brow', LIN['brow'], .7)); out.append(ob)
    return out

# tight short ah ma perm: a scalp cap plus small curls spread over it (fibonacci points), none over the face or the ear lobes
HAIR_C = Vector((0, -0.04, 1.66)); HAIR_R = (0.43, 0.40, 0.37)
HAIR_TOP = (Vector((0, -0.03, 2.04)), 0.09)   # the one curl that sets the height: 2.127

def curl_points(n=64):
    """Curl centres on the scalp cap, skipping the face, the ear lobes and below the nape."""
    out = []; ga = math.pi * (3 - 5 ** .5)
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n; rr = (1 - z * z) ** .5; a = ga * i
        d = Vector((rr * math.cos(a), rr * math.sin(a), z))
        p = HAIR_C + Vector((d.x * HAIR_R[0], d.y * HAIR_R[1], d.z * HAIR_R[2])) * 0.90
        if p.y > 0.15 and p.z < 1.86: continue      # face
        if p.z < 1.62 and abs(p.x) > 0.30: continue  # ears stay clear
        if p.z < 1.50: continue
        out.append((p, 0.10 + 0.02 * ((i * 7) % 5) / 4))
    return out

def build_hair():
    """Crisp curls, no remesh: each curl is its own shell so the edges between them stay sharp."""
    s = Soup('ahma_hair')
    s.ellipsoid(HAIR_C, HAIR_R, seg=20)   # scalp cap the clumps sit on
    for p, r in curl_points() + [HAIR_TOP]: s.sphere(p, r, seg=12)
    hair, _ = s.remesh(voxel=0.012, smooth=2, smooth_factor=0.5, target_tris=3300)   # one soft cauliflower shell, clumps touching
    shade_smooth(hair)
    set_material(hair, flat_material('ahma_hair', LIN['hair'], .75))
    return hair, None

def build_eyes():
    objs = []
    for name, c in (('eye.l', EYE_L), ('eye.r', EYE_R)):
        o = Soup('ahma_' + name).sphere(c, EYE_R_BALL, seg=20).to_object(); shade_smooth(o)
        set_material(o, flat_material('ahma_eye', LIN['sclera'], .2)); objs.append(o)
    return objs

def build_glasses():
    """Thin round gold wire rims, bridge and temple arms. No lenses, so nothing magnifies."""
    parts = []
    R = EYE_R_BALL + 0.022
    for k in (-1, 1):
        c = sx(EYE_L, -k) + Vector((0, 0.11, -0.005))
        t = torus('rim', c, R, 0.005, rot=(math.radians(90), 0, 0), seg=28, rseg=6); parts.append(t)
        arm = Soup('temple').capsule((k * (abs(EYE_L.x) + R), c.y - 0.01, c.z + 0.02), (k * 0.41, -0.02, 1.58), 0.0045, 0.004, seg=8) \
            .capsule((k * 0.41, -0.02, 1.58), (k * 0.41, -0.06, 1.50), 0.004, 0.0035, seg=8).to_object(); shade_smooth(arm); parts.append(arm)
    bx = abs(EYE_L.x) - R
    br = Soup('bridge').capsule((-bx, EYE_L.y + 0.11, 1.60), (bx, EYE_L.y + 0.11, 1.60), 0.005, seg=8).to_object(); shade_smooth(br); parts.append(br)
    g = join(parts, 'ahma_glasses'); set_material(g, flat_material('ahma_frame', LIN['frame'], .35, .0))
    return g

def build_earrings():
    out = []
    for k in (-1, 1):
        o = Soup('earring').sphere((k * 0.445, 0.0, 1.47), 0.013, seg=10).to_object(); shade_smooth(o)
        set_material(o, flat_material('ahma_frame', LIN['frame'], .35, .0)); out.append(o)
    return out

def hand_soup(s, wrist, side):
    """Chunky stylised hand with four fingers and a thumb, relaxed curl. side: +1 right, -1 left.
    Canonical frame: wrist at origin, fingers down -Z, palm normal +Y, thumb +X. Then rotated so the palm faces the body."""
    rot = Matrix.Rotation(math.radians(90 * side), 4, 'Z')  # right: +Y -> -X (palm in), thumb -> +Y (forward)
    if side < 0: rot = rot @ Matrix.Diagonal((-1, 1, 1, 1))  # mirror the left hand
    T = Matrix.Translation(wrist) @ rot
    def P(x, y, z): return T @ Vector((x, y, z))
    s.ellipsoid(P(0, 0, -0.075), (0.082, 0.032, 0.085), rot=rot)
    s.sphere(P(0, 0, -0.01), 0.045)                             # wrist knob
    s.ellipsoid(P(0, 0.0, -0.15), (0.09, 0.03, 0.028), rot=rot)  # knuckle row
    fingers = [(-0.072, 0.90), (-0.024, 1.0), (0.024, 0.95), (0.072, 0.76)]
    for x, L in fingers:
        p = Vector((x, 0.0, -0.15)); d = Vector((0, 0, -1)); r = 0.0205
        for seg in (0.052, 0.042, 0.036):
            # curl toward the palm (+Y) a little more each joint
            d = (Matrix.Rotation(math.radians(22), 3, 'X') @ d).normalized()
            q = p + d * seg * L
            s.capsule(P(*p), P(*q), r, r * .9, seg=12); p = q; r *= .9
    # thumb: out of the palm side, angled forward and down
    p = Vector((0.075, 0.015, -0.06)); d = Vector((0.5, 0.5, -0.7)).normalized(); r = 0.024
    for seg in (0.05, 0.042):
        q = p + d * seg; s.capsule(P(*p), P(*q), r, r * .88, seg=12); p = q; r *= .9
        d = (Matrix.Rotation(math.radians(-25), 3, 'Y') @ d).normalized()
    return s

def build_arm(side):
    """Skin arm from the shoulder (inside the sleeve) to the fingertips."""
    k = side; s = Soup('ahma_arm')
    sh = Vector((k * 0.44, 0.0, 1.19)); el = Vector((k * 0.63, 0.03, 0.96)); wr = Vector((k * 0.70, 0.10, 0.74))
    s.capsule(sh, el, 0.098, 0.092).capsule(el, wr, 0.092, 0.066)  # thin under the sleeve so the decimated blouse never shows skin
    s.sphere(el, 0.095)
    hand_soup(s, wr, k)
    arm, arm_hi = s.remesh(voxel=0.0055, smooth=2, smooth_factor=.4, target_tris=1300, keep_hi=True)
    set_material(arm, flat_material('ahma_skin', LIN['skin'], .55))
    return arm, arm_hi

def build_blouse():
    s = Soup('ahma_blouse')
    s.ellipsoid((0, 0.0, 1.04), (0.43, 0.32, 0.27))
    s.sphere((0, 0.11, 0.94), 0.30)                                  # belly, forward
    s.ellipsoid((0, 0.03, 0.88), (0.43, 0.35, 0.18))                 # hem body
    s.capsule((0, 0.04, 0.90), (0, 0.04, 0.76), 0.43, 0.46, seg=32)  # flared hem
    for k in (-1, 1):
        s.sphere((k * 0.41, 0.0, 1.19), 0.165)                       # shoulders
        s.capsule((k * 0.43, 0.0, 1.17), (k * 0.59, 0.02, 0.99), 0.165, 0.14)  # short sleeves, puffy
    s.box((-0.23, 0.335, 0.90), (0.15, 0.05, 0.12))                   # patch pocket (her left side)
    blouse, blouse_hi = s.remesh(voxel=0.010, smooth=4, target_tris=3200, keep_hi=True)
    set_material(blouse, flat_material('ahma_blouse', LIN['blouse'], .8))
    return blouse, blouse_hi

def build_collar_and_trim(blouse):
    col = torus('ahma_collar', (0, 0.01, 1.262), 0.20, 0.042, rot=(0, 0, 0), seg=24, rseg=6)   # mandarin stand collar: cream band, shows at the sides and back
    set_material(col, flat_material('ahma_collar', LIN['blouse'], .8))
    pip = torus('ahma_collar_pipe', (0, 0.01, 1.30), 0.226, 0.013, rot=(0, 0, 0), seg=24, rseg=5)   # violet piping along the top edge
    set_material(pip, flat_material('ahma_piping', LIN['piping'], .6))
    col = join([col, pip], 'ahma_collar')
    # frog buttons down the samfu diagonal, small knots
    knots = []
    for i, (x, z) in enumerate(((0.10, 1.17), (0.17, 1.10), (0.21, 1.02))):
        hit, loc, nrm, _ = blouse.ray_cast(Vector((x, 2.0, z)), Vector((0, -1, 0)))
        c = loc + nrm * 0.012 if hit else Vector((x, 0.30, z)); print(f'[build] knot {i} at {tuple(round(v, 3) for v in c)}')
        k = Soup('knot').sphere(c, 0.022, seg=10).sphere(c + Vector((0.036, -0.004, 0)), 0.015, seg=10).to_object(); shade_smooth(k)
        set_material(k, flat_material('ahma_piping', LIN['piping'], .6)); knots.append(k)
    # Tiger Balm jar peeking out of the pocket
    jar = Soup('ahma_balm').capsule((-0.23, 0.355, 0.955), (-0.23, 0.355, 0.985), 0.03, 0.03, seg=6).to_object(); shade_smooth(jar)
    set_material(jar, flat_material('ahma_balm', LIN['balm'], .3))
    bangle = torus('ahma_bangle', (-0.70, 0.10, 0.76), 0.082, 0.010, rot=(math.radians(8), 0, 0), seg=24, rseg=8)
    set_material(bangle, flat_material('ahma_jade', LIN['jade'], .25))
    return [col, jar, bangle, build_cane()] + knots

def build_cane():
    """Rotan cane slung diagonally across her back, crook hooked over her left shoulder. Joined into the body, chest-rigid."""
    top = Vector((-0.27, -0.25, 1.33)); bot = Vector((0.30, -0.56, 0.60)); r = 0.014
    s = Soup('ahma_cane').capsule(top, bot, r, seg=8)
    cc = top + Vector((0, 0.05, 0))   # crook arc in the y-z plane, up and over toward her front
    for i in range(5):
        a0 = math.pi * i / 5; a1 = math.pi * (i + 1) / 5
        p0 = cc + Vector((0, -0.05 * math.cos(a0), 0.05 * math.sin(a0))); p1 = cc + Vector((0, -0.05 * math.cos(a1), 0.05 * math.sin(a1)))
        s.capsule(p0, p1, r, seg=6)
    s.capsule(cc + Vector((0, 0.05, 0)), cc + Vector((0, 0.05, -0.04)), r, seg=6)
    c = s.to_object(); shade_smooth(c); set_material(c, flat_material('ahma_rattan', LIN['rattan'], .6)); return c

def build_slacks():
    s = Soup('ahma_slacks')
    s.ellipsoid((0, 0.02, 0.80), (0.40, 0.30, 0.18))
    for k in (-1, 1):
        s.capsule((k * 0.17, 0.02, 0.78), (k * 0.185, 0.0, 0.46), 0.155, 0.135)
        s.capsule((k * 0.185, 0.0, 0.46), (k * 0.185, 0.0, 0.15), 0.135, 0.125)
    slacks, slacks_hi = s.remesh(voxel=0.010, smooth=4, target_tris=1700, keep_hi=True)
    set_material(slacks, flat_material('ahma_slacks', LIN['slacks'], .85))
    return slacks, slacks_hi

def build_feet():
    s = Soup('ahma_feet'); sl = Soup('ahma_slippers')
    for k in (-1, 1):
        x = k * 0.185
        s.capsule((x, 0.0, 0.18), (x, 0.02, 0.07), 0.065, 0.06)             # ankle
        s.ellipsoid((x, 0.075, 0.055), (0.075, 0.14, 0.045))                 # foot
        for i, (tx, ty, tr) in enumerate(((0.045, 0.215, 0.03), (0.015, 0.225, 0.026), (-0.015, 0.22, 0.024), (-0.042, 0.205, 0.022))):
            s.sphere((x + k * tx, ty, 0.045), tr, seg=12)                     # toes, big toe inward
        sl.box((x, 0.07, 0.013), (0.19, 0.36, 0.026))                          # sole
        sl.capsule((x, 0.185, 0.03), (x + k * 0.08, 0.06, 0.05), 0.012)        # straps
        sl.capsule((x, 0.185, 0.03), (x - k * 0.08, 0.06, 0.05), 0.012)
    feet, feet_hi = s.remesh(voxel=0.007, smooth=3, target_tris=900, keep_hi=True)
    set_material(feet, flat_material('ahma_skin', LIN['skin'], .55))
    slip, slip_hi = sl.remesh(voxel=0.006, smooth=2, target_tris=800, keep_hi=True)
    set_material(slip, flat_material('ahma_slipper', LIN['slipper'], .5))
    return feet, feet_hi, slip, slip_hi

def build_walker():
    """Zimmer frame with a red basket. Local origin = WALKER_PIVOT on the ground.
    Grips at -Y (her side), wheels at +Y."""
    P = WALKER_PIVOT; frame = Soup('ahma_walker_frame'); rub = Soup('ahma_walker_rubber'); bask = Soup('ahma_walker_basket')
    for k in (-1, 1):
        x = k * 0.36
        frame.capsule(P + Vector((x, 0.18, 0.08)), P + Vector((x, 0.18, 0.90)), 0.018, seg=10)          # front leg
        frame.capsule(P + Vector((x, -0.22, 0.04)), P + Vector((x, -0.22, 0.86)), 0.018, seg=10)         # back leg
        frame.capsule(P + Vector((x, 0.18, 0.90)), P + Vector((x, -0.24, 0.88)), 0.018, seg=10)          # top rail
        frame.capsule(P + Vector((x, 0.18, 0.34)), P + Vector((x, -0.22, 0.32)), 0.014, seg=8)           # side brace
        rub.capsule(P + Vector((x, -0.08, 0.89)), P + Vector((x, -0.26, 0.885)), 0.032, seg=10)          # grip
        rub.capsule(P + Vector((x, -0.22, 0.03)), P + Vector((x, -0.22, 0.06)), 0.03, 0.026, seg=10)     # rubber foot, bottom on the floor
        rub.ellipsoid(P + Vector((x, 0.18, 0.06)), (0.022, 0.06, 0.06), seg=14)                           # wheel
        frame.box(P + Vector((x, 0.18, 0.10)), (0.05, 0.03, 0.08))                                       # fork
    frame.capsule(P + Vector((-0.36, 0.18, 0.80)), P + Vector((0.36, 0.18, 0.80)), 0.018, seg=10)        # front crossbar
    frame.capsule(P + Vector((-0.36, 0.18, 0.34)), P + Vector((0.36, 0.18, 0.34)), 0.014, seg=8)
    bask.box(P + Vector((0, 0.32, 0.50)), (0.50, 0.26, 0.016))                                           # basket floor
    for y in (0.20, 0.44): bask.box(P + Vector((0, y, 0.60)), (0.50, 0.016, 0.22))
    for x in (-0.25, 0.25): bask.box(P + Vector((x, 0.32, 0.60)), (0.016, 0.26, 0.22))
    f = frame.to_object(); shade_smooth(f); set_material(f, flat_material('ahma_metal', LIN['metal'], .3, 1.0))
    r = rub.to_object(); shade_smooth(r); set_material(r, flat_material('ahma_rubber', LIN['rubber'], .8))
    b = bask.to_object(); set_material(b, flat_material('ahma_basket', LIN['basket'], .45))
    w = join([f, r, b], 'ahma_walker'); decimate(w, 1800); shade_smooth(w); return w

def stage_build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    head = build_head(); set_material(head, flat_material('ahma_skin', LIN['skin'], .55))
    head_hi = head.copy(); head_hi.data = head.data.copy(); head_hi.name = 'ahma_head_hi'; bpy.context.scene.collection.objects.link(head_hi)
    decimate(head, 4600); shade_smooth(head)
    mouth = build_mouth_parts(); brows = build_brows()
    head = join([head] + mouth + brows, 'ahma_head')
    hair, hair_hi = build_hair(); glasses = build_glasses(); ears = build_earrings()
    headgear = join([hair, glasses] + ears, 'ahma_headgear')
    eyes = build_eyes(); eyes = join(eyes, 'ahma_eyes')
    body_parts = []; hi = [head_hi]
    for k in (-1, 1):
        a, ah = build_arm(k); body_parts.append(a); hi.append(ah)
    bl, blh = build_blouse(); body_parts.append(bl); hi.append(blh)
    sl, slh = build_slacks(); body_parts.append(sl); hi.append(slh)
    ft, fth, sp, sph = build_feet(); body_parts += [ft, sp]; hi += [fth, sph]
    body_parts += build_collar_and_trim(bl)
    body = join(body_parts, 'ahma_body')
    walker = build_walker()
    hi_col = bpy.data.collections.new('hi'); bpy.context.scene.collection.children.link(hi_col)
    for h in hi:
        for c in h.users_collection: c.objects.unlink(h)
        hi_col.objects.link(h); h.hide_render = True; h.hide_viewport = True
    for o in (head, headgear, eyes, body, walker):
        print(f'[build] {o.name}: {tri_count(o)} tris, {len(o.data.materials)} mats')
    print('[build] total tris', sum(tri_count(o) for o in (head, headgear, eyes, body, walker)))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'ahma_build.blend'))

# =====================================================================================
# quick look shots (flat materials)
# =====================================================================================
def hide_hi():
    for o in bpy.data.objects: o.hide_render = o.name.endswith('_hi') or o.name.startswith('cut')

def stage_look(tag='look', blend='ahma_build.blend'):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, blend))
    hide_hi(); RL.setup_render(1024, 1024, 24); RL.studio_light((0, 0, 1.1)); RL.floor()
    RL.shoot(os.path.join(SHOTS, f'{tag}_front.png'), (0, 6.3, 1.5), (0, 0, 1.05), 60)
    RL.shoot(os.path.join(SHOTS, f'{tag}_three_quarter.png'), (-4.2, 4.6, 2.0), (0, 0, 1.05), 60)
    RL.shoot(os.path.join(SHOTS, f'{tag}_face.png'), (-1.2, 2.2, 1.9), (0, 0.1, 1.58), 85)
    RL.shoot(os.path.join(SHOTS, f'{tag}_hand.png'), (-1.6, 1.0, 0.8), (-0.70, 0.1, 0.65), 100)

# =====================================================================================
# rig: armature, weights, face shape keys
# =====================================================================================
BONES = [  # name, head, tail, parent
    ('root', (0, 0, 0), (0, 0, 0.25), None),
    ('hips', (0, 0, 0.74), (0, 0, 0.88), 'root'),
    ('spine', (0, 0, 0.88), (0, 0, 1.05), 'hips'),
    ('chest', (0, 0, 1.05), (0, 0, 1.22), 'spine'),
    ('neck', (0, 0, 1.22), (0, 0.01, 1.33), 'chest'),
    ('head', (0, 0.01, 1.33), (0, 0.02, 1.75), 'neck'),
    ('eye.l', tuple(EYE_L), tuple(EYE_L + Vector((0, 0.06, 0))), 'head'),
    ('eye.r', tuple(EYE_R), tuple(EYE_R + Vector((0, 0.06, 0))), 'head'),
    ('upperarm.l', (-0.42, 0, 1.20), (-0.63, 0.03, 0.96), 'chest'),
    ('lowerarm.l', (-0.63, 0.03, 0.96), (-0.70, 0.10, 0.74), 'upperarm.l'),
    ('hand.l', (-0.70, 0.10, 0.74), (-0.70, 0.13, 0.56), 'lowerarm.l'),
    ('handslot.l', (-0.70, 0.11, 0.62), (-0.70, 0.19, 0.62), 'hand.l'),
    ('upperarm.r', (0.42, 0, 1.20), (0.63, 0.03, 0.96), 'chest'),
    ('lowerarm.r', (0.63, 0.03, 0.96), (0.70, 0.10, 0.74), 'upperarm.r'),
    ('hand.r', (0.70, 0.10, 0.74), (0.70, 0.13, 0.56), 'lowerarm.r'),
    ('handslot.r', (0.70, 0.11, 0.62), (0.70, 0.19, 0.62), 'hand.r'),
    ('upperleg.l', (-0.17, 0.02, 0.76), (-0.185, 0.0, 0.46), 'hips'),
    ('lowerleg.l', (-0.185, 0.0, 0.46), (-0.185, 0.0, 0.12), 'upperleg.l'),
    ('foot.l', (-0.185, 0.0, 0.12), (-0.185, 0.14, 0.04), 'lowerleg.l'),
    ('toes.l', (-0.185, 0.14, 0.04), (-0.185, 0.25, 0.03), 'foot.l'),
    ('upperleg.r', (0.17, 0.02, 0.76), (0.185, 0.0, 0.46), 'hips'),
    ('lowerleg.r', (0.185, 0.0, 0.46), (0.185, 0.0, 0.12), 'upperleg.r'),
    ('foot.r', (0.185, 0.0, 0.12), (0.185, 0.14, 0.04), 'lowerleg.r'),
    ('toes.r', (0.185, 0.14, 0.04), (0.185, 0.25, 0.03), 'foot.r'),
    ('prop', tuple(WALKER_PIVOT), tuple(WALKER_PIVOT + Vector((0, 0, 0.3))), 'root'),
]
RIGID = {'eye.l', 'eye.r', 'prop', 'handslot.l', 'handslot.r'}  # never take automatic weights

def make_armature():
    arm = bpy.data.armatures.new('ahma_rig'); ob = bpy.data.objects.new('ahma_rig', arm)
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
    """groups: list of (bone, predicate(co)) ; every vertex goes 1.0 to the first bone whose predicate holds."""
    for g in list(ob.vertex_groups): ob.vertex_groups.remove(g)
    vg = {b: ob.vertex_groups.new(name=b) for b, _ in groups}
    for v in ob.data.vertices:
        for b, pred in groups:
            if pred(v.co): vg[b].add([v.index], 1.0, 'REPLACE'); break
    ob.parent = rig; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = rig

def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)

def falloff(co, c, r_in, r_out):
    return 1 - smoothstep(r_in, r_out, (Vector(co) - Vector(c)).length)

def add_shape_keys(head):
    me = head.data
    if not me.shape_keys: head.shape_key_add(name='Basis', from_mix=False)
    basis = [v.co.copy() for v in me.vertices]
    mat_of_vert = {}
    for p in me.polygons:
        for vi in p.vertices: mat_of_vert[vi] = p.material_index
    names = [m.name for m in me.materials]
    is_brow = {vi for vi, mi in mat_of_vert.items() if names[mi] == 'ahma_brow'}
    is_skin = {vi for vi, mi in mat_of_vert.items() if names[mi] == 'ahma_skin'}
    n = len(basis); Z = Vector((0, 0, 0))
    comp = {}
    nbr = [[] for _ in range(n)]
    for e in me.edges: a, c = e.vertices; nbr[a].append(c); nbr[c].append(a)
    def key(name, fn):
        d = [Z.copy() for _ in range(n)]
        for i, co in enumerate(basis):
            r = fn(i, co)
            if r is not None: d[i] = Vector(r)
        for _ in range(3):   # relax the deltas over the mesh so the coarse triangulation never shows as lumps
            d = [(d[i] + sum((d[j] for j in nbr[i]), Z.copy()) / len(nbr[i])) * 0.5 if nbr[i] else d[i] for i in range(n)]
        comp[name] = d
    def eye_side(co): return EYE_L if co.x < 0 else EYE_R
    def blink(i, co):
        if i not in is_skin: return None
        E = eye_side(co); w = falloff(co, E, 0.07, 0.17)
        if w <= 0: return None
        if co.z > E.z - 0.015: return (0, 0.018 * w, -0.075 * w * smoothstep(-0.015, 0.05, co.z - E.z))
        return (0, 0.008 * w, 0.02 * w)
    def squint(i, co):
        if i not in is_skin: return None
        E = eye_side(co); w = falloff(co, E, 0.06, 0.17)
        if w <= 0 or co.z > E.z - 0.01: return None
        return (0, 0.01 * w, 0.035 * w)
    def brow_angry(i, co):
        if i in is_brow:
            inner = 1 - smoothstep(0.05, 0.27, abs(co.x))
            return (-0.02 * inner * (1 if co.x > 0 else -1), 0.005, -0.06 * inner + 0.02 * (1 - inner))
        if i in is_skin:
            w = falloff(co, (0, 0.36, 1.69), 0.03, 0.12)
            return (0, -0.006 * w, -0.014 * w) if w > 0 else None
        return None
    def brow_up(i, co):
        if i in is_brow:
            outer = smoothstep(0.03, 0.27, abs(co.x)); return (0, -0.004, 0.035 + 0.02 * outer)
        if i in is_skin:
            w = falloff(co, (0, 0.34, 1.76), 0.05, 0.2) * smoothstep(1.66, 1.74, co.z)
            return (0, 0, 0.012 * w) if w > 0 else None
        return None
    def mouth_open(i, co):
        if i in is_brow: return None
        if co.z > MOUTH_C.z + 0.012: return None
        w = falloff(co, (0, 0.28, 1.35), 0.10, 0.34)
        if w <= 0: return None
        drop = smoothstep(0.008, 0.02, MOUTH_C.z + 0.012 - co.z) * w   # the cut's lower edge already drops in full: the lip paint rides down intact
        return (co.x * 0.08 * w, -0.015 * drop, -0.085 * drop)
    def smile(i, co):
        if i in is_brow: return None
        s = 1 if co.x > 0 else -1; corner = Vector((s * 0.17, 0.33, 1.39))
        w = falloff(co, corner, 0.02, 0.16)
        d = Vector((0, 0, 0))
        if w > 0: d += Vector((s * 0.035 * w, -0.025 * w, 0.06 * w))
        cw = falloff(co, (s * 0.25, 0.22, 1.48), 0.0, 0.22) if i in is_skin else 0
        if cw > 0: d += Vector((0, 0.012 * cw, 0.024 * cw))
        lw = falloff(co, (0, 0.34, 1.355), 0.02, 0.10) if i in is_skin else 0   # tuck the lower lip back so the smile stays thin and wide
        if lw > 0: d += Vector((0, -0.014 * lw, 0.004 * lw))
        return tuple(d) if d.length > 0 else None
    def frown(i, co):
        if i in is_brow: return None
        s = 1 if co.x > 0 else -1; corner = Vector((s * 0.17, 0.33, 1.39))
        w = falloff(co, corner, 0.04, 0.13)
        return (-s * 0.014 * w, 0, -0.04 * w) if w > 0 else None
    for nm, fn in (('blink', blink), ('squint', squint), ('brow_angry', brow_angry), ('brow_up', brow_up),
                   ('mouth_open', mouth_open), ('smile', smile), ('frown', frown)): key(nm, fn)
    mixes = {
        'angry': {'brow_angry': 1.0, 'frown': 1.0, 'blink': 0.45, 'mouth_open': 0.12},
        'grin': {'smile': 1.0, 'squint': 1.0, 'brow_up': 0.5, 'mouth_open': 0.1},
        'ult': {'mouth_open': 1.0, 'brow_angry': 0.7, 'brow_up': 0.4, 'smile': 0.5},
    }
    export = ['blink', 'mouth_open', 'smile', 'angry', 'grin', 'ult']
    for i in range(n):   # rest face carries a slight smile, so the closed mouth never reads as a slit
        basis[i] = basis[i] + comp['smile'][i] * 0.3; me.vertices[i].co = basis[i]
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
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'ahma_build.blend'))
    head = bpy.data.objects['ahma_head']; body = bpy.data.objects['ahma_body']
    gear = bpy.data.objects['ahma_headgear']; eyes = bpy.data.objects['ahma_eyes']; walker = bpy.data.objects['ahma_walker']
    keys = add_shape_keys(head); print('[rig] shape keys', keys)
    rig = make_armature()
    auto_weights(rig, [body, head])
    for b in rig.data.bones: b.use_deform = True
    for ob, bone in ((head, 'head'), (body, 'chest')):   # enclosed bits (teeth, a knot inside the collar) get no heat weights
        for v in ob.data.vertices:
            if not v.groups: ob.vertex_groups[bone].add([v.index], 1.0, 'REPLACE')
    for v in body.data.vertices:  # sleeves follow the upper arm, blended in so no face folds at the boundary
        k = -1 if v.co.x < 0 else 1
        a, bq = Vector((k * 0.42, 0, 1.20)), Vector((k * 0.63, 0.03, 0.96)); ab = bq - a
        tt = max(0.0, min(1.0, (v.co - a).dot(ab) / ab.length_squared)); dist = (v.co - (a + ab * tt)).length
        t = smoothstep(0.38, 0.50, abs(v.co.x)) * smoothstep(0.86, 0.96, v.co.z) * (1 - smoothstep(0.19, 0.25, dist))
        if t <= 0: continue
        bone = 'upperarm.l' if k < 0 else 'upperarm.r'
        for g in list(v.groups):
            body.vertex_groups[g.group].add([v.index], g.weight * (1 - t), 'REPLACE')
        body.vertex_groups[bone].add([v.index], t, 'ADD')
    rat = body.data.materials.find('ahma_rattan'); chest = body.vertex_groups.get('chest') or body.vertex_groups.new(name='chest')
    for vi in {vi for p in body.data.polygons if p.material_index == rat for vi in p.vertices}:   # the cane rides on the chest
        for g in list(body.data.vertices[vi].groups): body.vertex_groups[g.group].remove([vi])
        chest.add([vi], 1.0, 'REPLACE')
    rigid_weights(rig, gear, [('head', lambda co: True)])
    rigid_weights(rig, eyes, [('eye.l', lambda co: co.x < 0), ('eye.r', lambda co: True)])
    rigid_weights(rig, walker, [('prop', lambda co: True)])
    # report weights sanity: any vertex with no group on body/head
    for ob in (body, head):
        loose = sum(1 for v in ob.data.vertices if not v.groups)
        print(f'[rig] {ob.name}: {loose} unweighted verts of {len(ob.data.vertices)}; groups {[g.name for g in ob.vertex_groups]}')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'ahma_rig.blend'))

def stage_expr(blend='ahma_rig.blend', tag='expr'):
    """Four expression close-ups, idle plus the three composite keys."""
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, blend))
    hide_hi(); RL.setup_render(768, 768, 24); RL.studio_light((0, 0.2, 1.55)); RL.floor()
    head = bpy.data.objects['ahma_head']; kb = head.data.shape_keys.key_blocks
    rig = bpy.data.objects.get('ahma_rig')
    if rig: reset_pose(rig)
    for nm in ('idle', 'angry', 'grin', 'ult'):
        for k in kb: k.value = 0.0
        if nm != 'idle': kb[nm].value = 1.0
        RL.shoot(os.path.join(SHOTS, f'{tag}_{nm}.png'), (-1.05, 2.45, 1.9), (0, 0.15, 1.58), 85)
    for k in kb: k.value = 0.0

# =====================================================================================
# textures: procedural node materials (object-space, hand-painted feel) baked to per-mesh atlases
# =====================================================================================
class MB:
    """Tiny node builder. Every method returns an output socket."""
    def __init__(self, mat):
        mat.use_nodes = True; self.t = mat.node_tree; self.n = self.t.nodes; self.l = self.t.links; self.n.clear()
        self.out = self.n.new('ShaderNodeOutputMaterial'); self.p = self.n.new('ShaderNodeBsdfPrincipled')
        self.l.new(self.p.outputs[0], self.out.inputs[0]); self._co = None; self._nrm = None
    def node(self, kind, **props):
        nd = self.n.new(kind)
        for k, v in props.items(): setattr(nd, k, v)
        return nd
    def link(self, sock, inp):
        if isinstance(sock, (tuple, list)): inp.default_value = (*sock, 1) if len(sock) == 3 and inp.type == 'RGBA' else sock
        elif isinstance(sock, (int, float)): inp.default_value = sock
        else: self.l.new(sock, inp)
    def co(self):
        if self._co is None: self._co = self.n.new('ShaderNodeTexCoord').outputs['Object']
        return self._co
    def mapped(self, vec, scale=(1, 1, 1), loc=(0, 0, 0)):
        m = self.node('ShaderNodeMapping'); self.link(vec, m.inputs['Vector']); m.inputs['Scale'].default_value = scale; m.inputs['Location'].default_value = loc
        return m.outputs[0]
    def vmath(self, op, a, b=None):
        m = self.node('ShaderNodeVectorMath', operation=op); self.link(a, m.inputs[0])
        if b is not None: self.link(b, m.inputs[1])
        return m.outputs['Value'] if op in ('DOT_PRODUCT', 'DISTANCE', 'LENGTH') else m.outputs['Vector']
    def math(self, op, a, b=None, c=None, clamp=False):
        m = self.node('ShaderNodeMath', operation=op, use_clamp=clamp); self.link(a, m.inputs[0])
        if b is not None: self.link(b, m.inputs[1])
        if c is not None: self.link(c, m.inputs[2])
        return m.outputs[0]
    def noise(self, vec=None, scale=10, detail=2, rough=.5):
        nd = self.node('ShaderNodeTexNoise'); self.link(vec or self.co(), nd.inputs['Vector'])
        nd.inputs['Scale'].default_value = scale; nd.inputs['Detail'].default_value = detail; nd.inputs['Roughness'].default_value = rough
        return nd.outputs['Fac']
    def voronoi(self, vec=None, scale=10, rand=1.0):
        nd = self.node('ShaderNodeTexVoronoi'); self.link(vec or self.co(), nd.inputs['Vector'])
        nd.inputs['Scale'].default_value = scale; nd.inputs['Randomness'].default_value = rand
        return nd.outputs['Distance']
    def wave(self, vec=None, scale=10, distortion=0, kind='BANDS', direction='X', profile='SIN'):
        nd = self.node('ShaderNodeTexWave', wave_type=kind, bands_direction=direction, wave_profile=profile); self.link(vec or self.co(), nd.inputs['Vector'])
        nd.inputs['Scale'].default_value = scale; nd.inputs['Distortion'].default_value = distortion
        return nd.outputs['Fac']
    def mix(self, fac, a, b):
        """colour mix: a at fac 0, b at fac 1."""
        m = self.node('ShaderNodeMix', data_type='RGBA', clamp_factor=True)
        self.link(fac, m.inputs['Factor']); self.link(a, m.inputs[6]); self.link(b, m.inputs[7])
        return m.outputs[2]
    def step(self, x, e0, e1):
        return self.math('SMOOTH_MIN', self.math('DIVIDE', self.math('SUBTRACT', x, e0), e1 - e0), 1.0, 0.0, clamp=True) if False else \
            self.math('MULTIPLY', self.math('DIVIDE', self.math('SUBTRACT', x, e0), e1 - e0, clamp=True), 1.0, clamp=True)
    def blob(self, centre, r_in, r_out, fold_x=False):
        """1 inside r_in of centre, 0 outside r_out. fold_x mirrors across X."""
        v = self.vmath('ABSOLUTE', self.co()) if fold_x else self.co()
        d = self.vmath('DISTANCE', v, tuple(centre))
        return self.math('SUBTRACT', 1.0, self.step(d, r_in, r_out))
    def strokes(self, along=(0.12, 1, 1), scale=16, levels=5, detail=1.5):
        """Hand-painted brush bands: noise stretched along one axis, quantised to a few flat levels."""
        n = self.math('MULTIPLY', self.noise(self.mapped(self.co(), along), scale=scale, detail=detail, rough=.45), float(levels))
        fl = self.math('FLOOR', n); fr = self.math('SUBTRACT', n, fl)
        return self.math('DIVIDE', self.math('ADD', fl, self.step(fr, 0.55, 1.0)), float(levels))   # soft-edged flat bands
    def normal(self):
        if self._nrm is None: self._nrm = self.n.new('ShaderNodeNewGeometry').outputs['Normal']
        return self._nrm
    def xyz(self, vec):
        nd = self.node('ShaderNodeSeparateXYZ'); self.link(vec, nd.inputs[0]); return nd.outputs['X'], nd.outputs['Y'], nd.outputs['Z']
    def combine(self, x, y, z):
        nd = self.node('ShaderNodeCombineXYZ'); self.link(x, nd.inputs[0]); self.link(y, nd.inputs[1]); self.link(z, nd.inputs[2]); return nd.outputs[0]
    def radial(self, centre, mirror_x=None, follow_z=None):
        """Smooth designed normal: the direction from a form centre, so the cel bands follow the big shape and never the triangles.
        mirror_x: centre x = sign(x) * mirror_x (limbs). follow_z: centre z = z + follow_z (a vertical axis, for limbs and torso)."""
        x, y, z = self.xyz(self.co())
        cx = self.math('MULTIPLY', self.math('SIGN', x), mirror_x) if mirror_x is not None else centre[0]
        cz = self.math('ADD', z, follow_z) if follow_z is not None else centre[2]
        return self.vmath('NORMALIZE', self.vmath('SUBTRACT', self.co(), self.combine(cx, centre[1], cz)))
    def vmix(self, fac, a, b):
        m = self.node('ShaderNodeMix', data_type='VECTOR', clamp_factor=True)
        self.link(fac, m.inputs['Factor']); self.link(a, m.inputs[4]); self.link(b, m.inputs[5]); return m.outputs[1]
    def paint_light(self, col, light_col, shadow_col, N=None, L=(-0.45, 0.55, 0.70), strokes=None, sh_amt=0.5, hi_amt=0.45, edge=0.14):
        """Painted light: a warm light band and a cool shadow band from a fixed key direction, baked into the albedo.
        N is a designed normal (see radial); strokes wobble the band edges so they read as brushwork."""
        nd = self.vmath('DOT_PRODUCT', N if N is not None else self.normal(), L)
        if strokes is not None: nd = self.math('ADD', nd, self.math('MULTIPLY', self.math('SUBTRACT', strokes, 0.5), edge))
        shade = self.math('SUBTRACT', 1.0, self.step(nd, 0.02, 0.30)); hi = self.step(nd, 0.60, 0.85)
        col = self.mix(self.math('MULTIPLY', shade, sh_amt), col, shadow_col)
        return self.mix(self.math('MULTIPLY', hi, hi_amt), col, light_col)
    def ring(self, centre, r_in, r_out, fold_x=False, flat=(1, 0, 1)):
        """Distance from centre measured in the axes `flat` keeps (default: the xz face plane)."""
        v = self.vmath('ABSOLUTE', self.co()) if fold_x else self.co()
        d = self.vmath('DISTANCE', self.mapped(v, flat), tuple(c * f for c, f in zip(centre, flat)))
        return self.math('MULTIPLY', self.step(d, r_in - 0.006, r_in), self.math('SUBTRACT', 1.0, self.step(d, r_out, r_out + 0.006)))
    def seg(self, p0, p1, w, fold_x=False, flat=(1, 0, 1)):
        """A painted stroke: 1 within w of the segment p0-p1, measured in the axes `flat` keeps. fold_x mirrors across X."""
        v = self.vmath('ABSOLUTE', self.co()) if fold_x else self.co()
        v = self.mapped(v, flat); p0 = Vector([c * f for c, f in zip(p0, flat)]); p1 = Vector([c * f for c, f in zip(p1, flat)]); d = p1 - p0
        t = self.math('DIVIDE', self.vmath('DOT_PRODUCT', self.vmath('SUBTRACT', v, tuple(p0)), tuple(d)), d.length_squared, clamp=True)
        sc = self.node('ShaderNodeVectorMath', operation='SCALE'); sc.inputs[0].default_value = tuple(d); self.link(t, sc.inputs['Scale'])
        proj = self.vmath('ADD', sc.outputs['Vector'], tuple(p0))
        return self.math('SUBTRACT', 1.0, self.step(self.vmath('DISTANCE', v, proj), w, w + 0.006))
    def grad(self, axis, lo, hi):
        """0 at co.axis = lo, 1 at hi."""
        return self.step(self.vmath('DOT_PRODUCT', self.co(), axis), lo, hi)
    def bump(self, height, strength=0.2, distance=0.01):
        b = self.node('ShaderNodeBump'); self.link(height, b.inputs['Height']); b.inputs['Strength'].default_value = strength; b.inputs['Distance'].default_value = distance
        self.l.new(b.outputs[0], self.p.inputs['Normal']); return b
    def finish(self, color, rough=.5, metal=0.0):
        self.link(color, self.p.inputs['Base Color'])
        self.link(rough, self.p.inputs['Roughness']); self.link(metal, self.p.inputs['Metallic'])

def c4(k): return (*LIN[k], 1)

def mat_skin(m):
    """Painted skin: warm light, cool mauve shadow, soft brush strokes, painted lids, lips, cheeks and a nose shadow."""
    b = MB(m)
    st = b.strokes(along=(0.25, 1, 0.7), scale=14, levels=3)
    col = b.mix(b.math('MULTIPLY', st, 0.07), c4('skin'), c4('skin_warm'))
    cool = b.math('MAXIMUM', b.grad((0, 0, 1), 1.66, 1.82), b.math('SUBTRACT', 1.0, b.grad((0, 1, 0), -0.05, 0.20)))
    cool = b.math('MAXIMUM', cool, b.blob((0, 0.16, 1.24), 0.06, 0.24))
    col = b.mix(b.math('MULTIPLY', cool, 0.4), col, c4('skin_cool'))
    # soft painted cheek blush, high on the cheekbone plane, plus the nose tip and ear tips
    cheeks = b.math('MAXIMUM', b.blob((0.24, 0.24, 1.50), 0.05, 0.20, fold_x=True), b.blob((0, 0.42, 1.50), 0.02, 0.09))
    cheeks = b.math('MAXIMUM', cheeks, b.math('MULTIPLY', b.blob((0.42, -0.02, 1.52), 0.03, 0.12, fold_x=True), 0.7))
    col = b.mix(b.math('MULTIPLY', cheeks, 0.75), col, c4('blush'))
    N = b.vmix(b.grad((0, 0, 1), 1.19, 1.25), b.radial((0, 0.03, 0), mirror_x=0.56, follow_z=0.0), b.radial((0, 0.01, 0), follow_z=0.0))   # arms below, neck cylinder above
    N = b.vmix(b.grad((0, 0, 1), 1.38, 1.46), N, b.radial((0, 0.05, 1.52)))                                                                # head
    N = b.vmix(b.grad((0, 0, 1), 0.30, 0.45), b.radial((0, 0.12, 0), mirror_x=0.19, follow_z=-0.08), N)                             # feet
    col = b.paint_light(col, c4('skin_warm'), c4('skin_shade'), N=N, sh_amt=0.55, hi_amt=0.5)   # designed normal only: the real normal streaked the jaw across sliver triangles
    # painted age: two or three graphic strokes only (smile lines, crow's feet), no modelled wrinkles
    E = (abs(EYE_L.x), EYE_L.y, EYE_L.z); r = EYE_R_BALL
    front = b.grad((0, 1, 0), 0.15, 0.25); near_eye = b.blob(E, 0.105, 0.135, fold_x=True)   # xz strokes project along y: keep them off the temple and the neck back
    lines = b.seg((0.085, 0.385, 1.445), (0.145, 0.35, 1.375), 0.0045, fold_x=True)   # one smile line per side; crow's feet read as an X on the temple, so none
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', lines, front), 0.35), col, c4('skin_shade'))
    # painted lids: a soft socket tone, a dark upper lid line that thickens into a lash stroke at the outer corner
    sock = b.math('MULTIPLY', b.blob((E[0], 0.30, E[2] + 0.02), 0.05, 0.13, fold_x=True), b.grad((0, 0, 1), E[2] - 0.02, E[2] + 0.02))
    col = b.mix(b.math('MULTIPLY', sock, 0.3), col, c4('skin_shade'))
    def almond(rx, rz):   # distance in an ellipse around the eye in the face plane, 1 at the rim
        return b.vmath('DISTANCE', b.mapped(b.vmath('ABSOLUTE', b.co()), (1 / rx, 0, 1 / rz)), (E[0] / rx, 0, E[2] / rz))
    up_half = b.grad((0, 0, 1), E[2] - 0.004, E[2] + 0.012)
    d1 = almond(0.088, 0.048); upper = b.math('MULTIPLY', b.math('MULTIPLY', b.step(d1, 0.96, 1.0), b.math('SUBTRACT', 1.0, b.step(d1, 1.12, 1.18))), up_half)   # single lid line
    d2 = almond(0.098, 0.066); crease = b.math('MULTIPLY', b.math('MULTIPLY', b.step(d2, 0.97, 1.0), b.math('SUBTRACT', 1.0, b.step(d2, 1.05, 1.09))), up_half)  # low soft crease
    lash = b.math('MULTIPLY', b.seg((E[0] + 0.075, 0.30, E[2] + 0.012), (E[0] + 0.092, 0.27, E[2] + 0.020), 0.004, fold_x=True), 0.7)
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', b.math('MAXIMUM', upper, lash), near_eye), 0.8), col, c4('lid'))
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', crease, near_eye), 0.3), col, c4('skin_shade'))
    # painted nose shadow, lips with a clean dark upper lip line and upturned corners
    col = b.mix(b.math('MULTIPLY', b.blob((0, 0.39, 1.455), 0.02, 0.07), 0.45), col, c4('skin_shade'))
    lips = b.math('SUBTRACT', 1.0, b.step(b.vmath('DISTANCE', b.mapped(b.co(), (1 / 0.15, 0.25, 1 / 0.040)), (0, MOUTH_C.y * 0.25, MOUTH_C.z / 0.040)), 0.75, 1.05))
    col = b.mix(b.math('MULTIPLY', lips, 0.85), col, c4('lip'))
    mz = MOUTH_C.z + 0.002
    line = b.math('MAXIMUM', b.seg((0, 0.34, mz), (0.12, 0.34, mz), 0.0025, fold_x=True), b.seg((0.12, 0.34, mz), (0.15, 0.33, mz + 0.016), 0.0025, fold_x=True))
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', line, front), 0.85), col, c4('mouth'))
    b.finish(col, 0.62)

def mat_blouse(m):
    """Cream samfu cotton: painted light and violet shadow, a small soft floral print, a few painted fold lines."""
    b = MB(m)
    st = b.strokes(along=(1, 1, 0.15), scale=12, levels=3)
    base = b.mix(b.math('MULTIPLY', st, 0.4), c4('blouse'), c4('blouse_cool'))
    v1 = b.voronoi(scale=22); flower = b.math('SUBTRACT', 1.0, b.step(v1, 0.22, 0.32))
    col = b.mix(flower, base, c4('floral_a'))
    col = b.mix(b.math('SUBTRACT', 1.0, b.step(v1, 0.07, 0.12)), col, (0.98, 0.88, 0.55, 1))
    v2 = b.voronoi(b.mapped(b.co(), (1, 1, 1), (0.31, 0.17, 0.23)), scale=22)
    col = b.mix(b.math('MULTIPLY', b.math('SUBTRACT', 1.0, b.step(v2, 0.14, 0.22)), b.math('SUBTRACT', 1.0, flower)), col, c4('floral_leaf'))
    v3 = b.voronoi(b.mapped(b.co(), (1, 1, 1), (-0.2, 0.4, 0.1)), scale=26)
    col = b.mix(b.math('MULTIPLY', b.math('SUBTRACT', 1.0, b.step(v3, 0.12, 0.20)), b.math('SUBTRACT', 1.0, flower)), col, c4('floral_b'))
    ax = b.math('ABSOLUTE', b.xyz(b.co())[0])
    N = b.vmix(b.step(ax, 0.40, 0.48), b.radial((0, 0.02, 0), follow_z=-0.15), b.radial((0, 0.01, 0), mirror_x=0.52, follow_z=0.0))  # torso, sleeves
    col = b.paint_light(col, (1, 0.98, 0.93, 1), c4('blouse_shade'), N=N, strokes=st, sh_amt=0.55, hi_amt=0.35)
    folds = None   # diagonal fold shadows pulling toward the belly
    for k, (dx, dz, c0) in enumerate(((0.55, 0.83, 0.86), (-0.55, 0.83, 0.86), (0.3, 0.95, 1.00), (-0.3, 0.95, 1.00))):
        f = b.math('SUBTRACT', 1.0, b.step(b.math('ABSOLUTE', b.math('SUBTRACT', b.vmath('DOT_PRODUCT', b.co(), (dx, 0, dz)), c0)), 0.008, 0.026))
        f = b.math('MULTIPLY', f, b.math('MULTIPLY', b.grad((0, 1, 0), 0.05, 0.25), b.math('SUBTRACT', 1.0, b.grad((0, 0, 1), 1.02, 1.12))))
        folds = f if folds is None else b.math('MAXIMUM', folds, f)
    col = b.mix(b.math('MULTIPLY', folds, 0.5), col, c4('blouse_shade'))
    b.finish(col, 0.82)

def mat_slacks(m):
    b = MB(m)
    st = b.strokes(along=(1, 1, 0.12), scale=10, levels=3)
    col = b.mix(b.math('MULTIPLY', st, 0.45), c4('slacks'), c4('slacks_dark'))
    col = b.paint_light(col, (0.33, 0.40, 0.56, 1), c4('slacks_shade'), N=b.radial((0, 0.0, 0), mirror_x=0.185, follow_z=-0.1), strokes=st, sh_amt=0.6, hi_amt=0.5)
    b.finish(col, 0.85)

def mat_hair(m):
    """Painted black perm: grey at the roots (deep between the curls) and the temples, a few grey strands,
    violet then teal in the shadow, a lavender light band. Half the light comes from each curl's own normal."""
    b = MB(m)
    st = b.strokes(along=(0.18, 1, 0.5), scale=14, levels=4)
    col = b.mix(b.math('MULTIPLY', st, 0.7), c4('hair'), c4('hair_mid'))
    strand = b.step(b.noise(b.mapped(b.co(), (0.18, 1, 0.5)), scale=34, detail=1.0, rough=.45), 0.57, 0.60)                     # thin grey strands
    col = b.mix(b.math('MULTIPLY', strand, 0.4), col, c4('hair_grey'))
    temples = b.math('MULTIPLY', b.blob((0.41, 0.06, 1.70), 0.04, 0.16, fold_x=True), 0.55)
    col = b.mix(b.math('MULTIPLY', temples, 0.6), col, c4('hair_grey'))
    cell = b.voronoi(scale=9)   # painted curl strokes: a dark seam between cells, a warm sheen ring inside each
    col = b.mix(b.math('MULTIPLY', b.step(cell, 0.34, 0.46), 0.6), col, c4('hair_dark'))
    ring = b.math('MULTIPLY', b.step(cell, 0.10, 0.18), b.math('SUBTRACT', 1.0, b.step(cell, 0.22, 0.30)))
    col = b.mix(b.math('MULTIPLY', ring, 0.2), col, c4('hair_light'))
    N = b.vmix(0.5, b.radial(tuple(HAIR_C)), b.normal())                                                                         # each curl carries its own painted shade
    nd = b.vmath('DOT_PRODUCT', N, (-0.45, 0.55, 0.70)); nd = b.math('ADD', nd, b.math('MULTIPLY', b.math('SUBTRACT', st, 0.5), 0.12))
    col = b.mix(b.math('MULTIPLY', b.math('SUBTRACT', 1.0, b.step(nd, 0.15, 0.45)), 0.85), col, c4('hair_dark'))               # violet-black shadow band
    col = b.mix(b.math('MULTIPLY', b.math('SUBTRACT', 1.0, b.step(nd, -0.25, -0.02)), 0.7), col, c4('hair_deep'))              # teal in the deepest shadow
    col = b.mix(b.math('MULTIPLY', b.step(nd, 0.62, 0.88), 0.35), col, c4('hair_light'))                                         # lavender light band
    b.finish(col, 0.85)

def mat_eye(m):
    """Clear friendly eyes: a smaller near-black iris with a slightly warmer lower half, soft lid shadow on the sclera, one catchlight."""
    b = MB(m)
    v = b.vmath('ABSOLUTE', b.co()); d = b.vmath('NORMALIZE', b.vmath('SUBTRACT', v, (abs(EYE_L.x), EYE_L.y, EYE_L.z)))
    dot = b.vmath('DOT_PRODUCT', d, (0, 1, 0))
    iris = b.step(dot, 0.79, 0.82); pupil = b.step(dot, 0.93, 0.95)      # smaller graphic iris, flat painted pupil
    up = b.vmath('DOT_PRODUCT', d, (0, 0, 1))
    iris_col = b.mix(b.step(up, 0.3, -0.5), c4('iris'), c4('iris_light'))
    col = b.mix(b.step(up, 0.40, 0.60), c4('sclera'), c4('sclera_shade'))
    col = b.mix(iris, col, iris_col); col = b.mix(pupil, col, c4('pupil'))
    col = b.mix(b.math('MULTIPLY', b.step(up, 0.52, 0.64), 0.75), col, c4('lid'))   # painted upper lid shadow and lash line on the ball itself
    hl = b.step(b.vmath('DOT_PRODUCT', d, (-0.22, 0.92, 0.32)), 0.975, 0.985)
    col = b.mix(hl, col, (1, 1, 1, 1))
    b.finish(col, 0.5)   # matte, no glassy ball

def mat_frame(m):
    b = MB(m)
    b.finish(b.mix(b.math('MULTIPLY', b.noise(scale=20, detail=1), 0.3), c4('frame'), (0.45, 0.30, 0.10, 1)), 0.35, 0.7)

def mat_metal(m):
    b = MB(m)
    br = b.noise(b.mapped(b.co(), (2, 2, 80)), scale=3, detail=3)
    b.bump(br, strength=0.08, distance=0.002)
    b.finish(b.mix(b.math('MULTIPLY', br, 0.25), c4('metal'), (0.35, 0.36, 0.38, 1)), b.math('ADD', 0.25, b.math('MULTIPLY', br, 0.3)), 1.0)

def mat_simple(m, col, rough, metal=0.0, noise_scale=30, noise_amt=0.15, dark=(0.1, 0.1, 0.1, 1), bump=0.0):
    b = MB(m)
    n = b.noise(scale=noise_scale, detail=2)
    c = b.mix(b.math('MULTIPLY', n, noise_amt), c4(col) if isinstance(col, str) else col, dark)
    if bump: b.bump(n, strength=bump, distance=0.003)
    b.finish(c, b.math('ADD', rough, b.math('MULTIPLY', n, 0.1)), metal)

def mat_rattan(m):
    b = MB(m)
    bands = b.wave(scale=90, direction='Z')
    b.bump(bands, strength=0.3, distance=0.003)
    b.finish(b.mix(b.math('MULTIPLY', bands, 0.4), c4('rattan'), (0.35, 0.22, 0.09, 1)), 0.55)

def build_materials():
    M = bpy.data.materials
    mat_skin(M['ahma_skin']); mat_blouse(M['ahma_blouse']); mat_slacks(M['ahma_slacks'])
    mat_hair(M['ahma_hair']); mat_simple(M['ahma_brow'], 'brow', 0.7, noise_scale=12, noise_amt=0.12, dark=c4('hair_dark')); mat_eye(M['ahma_eye']); mat_frame(M['ahma_frame']); mat_metal(M['ahma_metal']); mat_rattan(M['ahma_rattan'])
    mat_simple(M['ahma_slipper'], 'slipper', 0.45, noise_scale=8, dark=c4('slipper_dark'), noise_amt=0.4)
    mat_simple(M['ahma_basket'], 'basket', 0.4, noise_amt=0.25, dark=(0.35, 0.05, 0.04, 1))
    mat_simple(M['ahma_rubber'], 'rubber', 0.85, noise_scale=120, noise_amt=0.3, bump=0.3)
    mat_simple(M['ahma_jade'], 'jade', 0.25, noise_scale=40, noise_amt=0.5, dark=(0.12, 0.35, 0.22, 1))
    mat_simple(M['ahma_piping'], 'piping', 0.6, noise_amt=0.1)
    mat_simple(M['ahma_collar'], 'blouse', 0.8, noise_scale=10, noise_amt=0.12, dark=c4('blouse_shade'))
    mat_simple(M['ahma_balm'], 'balm', 0.3, noise_amt=0.1)
    mat_simple(M['ahma_mouth'], 'mouth', 0.7, noise_scale=8, noise_amt=0.15, dark=(0.08, 0.03, 0.05, 1))
    mat_simple(M['ahma_teeth'], 'teeth', 0.5, noise_scale=8, noise_amt=0.1, dark=(0.6, 0.55, 0.5, 1))

# per export mesh: texture size
ATLAS = {'ahma_head': 2048, 'ahma_body': 2048, 'ahma_headgear': 1024, 'ahma_walker': 1024, 'ahma_eyes': 256}

def new_image(name, size, noncolor=False):
    im = bpy.data.images.get(name)
    if im: bpy.data.images.remove(im)
    im = bpy.data.images.new(name, size, size, alpha=False, float_buffer=False)
    if noncolor: im.colorspace_settings.name = 'Non-Color'
    return im

def bake(ob, img, btype, samples=1, **kw):
    for slot in ob.material_slots:
        nt = slot.material.node_tree; n = nt.nodes.get('BAKE') or nt.nodes.new('ShaderNodeTexImage'); n.name = 'BAKE'; n.image = img; nt.nodes.active = n
    bpy.context.scene.cycles.samples = samples
    select_only([ob], ob)
    bpy.ops.object.bake(type=btype, margin=6, use_clear=True, **kw)

def px(img):
    import numpy as np
    a = np.empty(img.size[0] * img.size[1] * 4, np.float32); img.pixels.foreach_get(a); return a.reshape(img.size[1], img.size[0], 4)

def set_px(img, arr):
    img.pixels.foreach_set(arr.astype('float32').ravel())

def save_png(img, path):
    img.filepath_raw = path; img.file_format = 'PNG'; img.save()

def gltf_ao_group():
    g = bpy.data.node_groups.get('glTF Material Output')
    if g: return g
    g = bpy.data.node_groups.new('glTF Material Output', 'ShaderNodeTree')
    g.interface.new_socket('Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
    g.nodes.new('NodeGroupInput'); return g

def export_material(ob, base, orm, nrm):
    m = bpy.data.materials.new(ob.name + '_mat'); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links
    p = n['Principled BSDF']
    tb = n.new('ShaderNodeTexImage'); tb.image = base; l.new(tb.outputs[0], p.inputs['Base Color'])
    to = n.new('ShaderNodeTexImage'); to.image = orm; sep = n.new('ShaderNodeSeparateColor'); l.new(to.outputs[0], sep.inputs[0])
    l.new(sep.outputs['Green'], p.inputs['Roughness']); l.new(sep.outputs['Blue'], p.inputs['Metallic'])
    grp = n.new('ShaderNodeGroup'); grp.node_tree = gltf_ao_group(); l.new(sep.outputs['Red'], grp.inputs['Occlusion'])
    tn = n.new('ShaderNodeTexImage'); tn.image = nrm; nm = n.new('ShaderNodeNormalMap'); l.new(tn.outputs[0], nm.inputs['Color']); l.new(nm.outputs[0], p.inputs['Normal'])
    set_material(ob, m)

def stage_bake():
    import numpy as np
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'ahma_rig.blend'))
    for k in bpy.data.objects['ahma_head'].data.shape_keys.key_blocks: k.value = 0.0   # bake the rest face
    build_materials()
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.render.bake.use_pass_direct = False; sc.render.bake.use_pass_indirect = False; sc.render.bake.use_pass_color = True
    sc.render.bake.normal_space = 'TANGENT'
    for o in list(bpy.data.objects):  # the hi copies occlude the AO bake (bake uses viewport visibility), so drop them here
        if o.name.endswith('_hi'): bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects: o.hide_viewport = False
    tex_dir = os.path.join(WORK, 'tex'); os.makedirs(tex_dir, exist_ok=True)
    for name, size in ATLAS.items():
        ob = bpy.data.objects[name]; ob.active_shape_key_index = 0; smart_uv(ob, margin=0.006)
        col = new_image(name + '_col', size); ao = new_image(name + '_ao', size, True); rough = new_image(name + '_rough', size, True)
        met = new_image(name + '_met', size, True); nrm = new_image(name + '_nrm', size, True)
        bake(ob, col, 'DIFFUSE', 1, pass_filter={'COLOR'})
        bake(ob, rough, 'ROUGHNESS', 1)
        bake(ob, nrm, 'NORMAL', 1)
        for slot in ob.material_slots:  # metallic through an emission pass
            p = slot.material.node_tree.nodes['Principled BSDF']; v = p.inputs['Metallic'].default_value
            p.inputs['Emission Color'].default_value = (v, v, v, 1); p.inputs['Emission Strength'].default_value = 1.0
        bake(ob, met, 'EMIT', 1)
        for slot in ob.material_slots: slot.material.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.0
        c = px(col); r = px(rough)[..., 0:1]; mt = px(met)[..., 0:1]; a = np.ones_like(r)   # AO flat white: the paint carries the shading, a baked AO showed black patches under the glasses arms and hair
        base = new_image(name + '_baseColor', size); orm = new_image(name + '_orm', size, True)
        cb = c.copy(); cb[..., 3] = 1; set_px(base, cb)
        o = np.concatenate([a, r, mt, np.ones_like(a)], axis=-1); set_px(orm, o)
        if size >= 2048:
            for im in (orm, nrm): im.scale(size // 2, size // 2)
        base.filepath_raw = os.path.join(tex_dir, base.name + '.jpg'); base.file_format = 'JPEG'; base.save(quality=88)
        for im in (orm, nrm): save_png(im, os.path.join(tex_dir, im.name + '.png'))
        for im in (col, rough, met): bpy.data.images.remove(im)
        export_material(ob, base, orm, nrm)
        print(f'[bake] {name}: {size}px baseColor/orm/normal')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'ahma_bake.blend'))

# =====================================================================================
# animation: actions on the rig, pushed to NLA, exported as glTF animations
# =====================================================================================
FPS = 30
GRIP = {k: WALKER_PIVOT + Vector((k * 0.36, -0.17, 0.89)) for k in (-1, 1)}   # rest grip centres (world)
WRIST_OFF = Vector((0, -0.03, 0.09))                                          # wrist sits just above and behind the grip

def rest_mat(rig, name): return rig.data.bones[name].matrix_local  # armature space rest

def world_quat_to_local(rig, pb, q_world):
    """A rotation given in armature (world) space, expressed in the pose bone's local rotation."""
    M = rest_mat(rig, pb.name).to_3x3()
    return (M.inverted() @ q_world.to_matrix() @ M).to_quaternion()

def set_world_rot(rig, pb, q_world):
    pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = world_quat_to_local(rig, pb, q_world)

def axis_rot(axis, deg): return Quaternion(Vector(axis), math.radians(deg))

def aim_arm(rig, k, wrist_world):
    """Rotate the whole arm (upper + lower rigid) so the shoulder points at wrist_world, then bend the hand down over the grip."""
    side = 'l' if k < 0 else 'r'
    up = rig.pose.bones['upperarm.' + side]; hand = rig.pose.bones['hand.' + side]; low = rig.pose.bones['lowerarm.' + side]
    sh = rest_mat(rig, up.name).translation; wr = rest_mat(rig, hand.name).translation
    q = (wr - sh).rotation_difference(Vector(wrist_world) - sh)
    set_world_rot(rig, up, q); low.rotation_quaternion = Quaternion()
    set_world_rot(rig, hand, axis_rot((1, 0, 0), -50))

def prop_grips(q, t):
    """Grip centres after the prop bone rotates by q (about the pivot) and translates by t."""
    return {k: WALKER_PIVOT + q @ (GRIP[k] - WALKER_PIVOT) + t for k in GRIP}

def set_prop(rig, q, t):
    pb = rig.pose.bones['prop']; set_world_rot(rig, pb, q)
    M = rest_mat(rig, 'prop').to_3x3(); pb.location = M.inverted() @ Vector(t)

def key_all(rig, frame, names):
    for n in names:
        pb = rig.pose.bones[n]
        pb.keyframe_insert('rotation_quaternion', frame=frame)
        if n in ('hips', 'prop', 'root'): pb.keyframe_insert('location', frame=frame)

def reset_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)

ANIM_BONES = ['hips', 'spine', 'chest', 'neck', 'head', 'upperarm.l', 'lowerarm.l', 'hand.l', 'upperarm.r', 'lowerarm.r', 'hand.r',
              'upperleg.l', 'lowerleg.l', 'foot.l', 'upperleg.r', 'lowerleg.r', 'foot.r', 'prop']

def hips_lift(rig, dz):
    pb = rig.pose.bones['hips']; pb.location = rest_mat(rig, 'hips').to_3x3().inverted() @ Vector((0, 0, dz))

def pose_frame(rig, t, kind):
    """t in [0,1) of the cycle. Sets the whole pose for one frame of `kind`."""
    reset_pose(rig); B = rig.pose.bones; X = (1, 0, 0); Y = (0, 1, 0); Z = (0, 0, 1)
    s = math.sin(2 * math.pi * t); c = math.cos(2 * math.pi * t)
    if kind == 'idle':
        set_world_rot(rig, B['chest'], axis_rot(X, 2.0 * s)); set_world_rot(rig, B['head'], axis_rot(X, -1.5 * s) @ axis_rot(Z, 2.0 * c))
        hips_lift(rig, 0.006 * s); pq, pt = Quaternion(), Vector((0, 0, 0))
    elif kind == 'run':
        for k, sg in ((-1, 1), (1, -1)):
            side = 'l' if k < 0 else 'r'
            set_world_rot(rig, B['upperleg.' + side], axis_rot(X, 32 * s * sg))
            set_world_rot(rig, B['lowerleg.' + side], axis_rot(X, -45 * max(0.0, -s * sg)))
            set_world_rot(rig, B['foot.' + side], axis_rot(X, 15 * max(0.0, -s * sg)))
        set_world_rot(rig, B['chest'], axis_rot(X, 9) @ axis_rot(Z, 4 * s)); set_world_rot(rig, B['head'], axis_rot(X, -6) @ axis_rot(Z, -3 * s))
        set_world_rot(rig, B['spine'], axis_rot(X, 4))
        hips_lift(rig, 0.03 * abs(s) - 0.015)
        pq = axis_rot(X, 3 * math.sin(4 * math.pi * t)); pt = Vector((0, 0.0, 0.025 * abs(s)))
    elif kind == 'attack':  # lift the frame, tilt it back, slam it down in front
        if t < 0.33: u = t / 0.33; lift = 0.38 * math.sin(u * math.pi / 2); tilt = -40 * u; fwd = -0.05 * u
        elif t < 0.55: u = (t - 0.33) / 0.22; lift = 0.38 * (1 - u) ** 2; tilt = -40 + 60 * u; fwd = -0.05 + 0.30 * u
        else: u = (t - 0.55) / 0.45; lift = 0.0; tilt = 20 * (1 - u); fwd = 0.25 * (1 - u)
        pq = axis_rot(X, tilt); pt = Vector((0, fwd, lift))
        lean = -10 if t < 0.33 else (14 if t < 0.55 else 14 * (1 - u))
        set_world_rot(rig, B['chest'], axis_rot(X, lean)); set_world_rot(rig, B['spine'], axis_rot(X, lean * 0.5))
        set_world_rot(rig, B['head'], axis_rot(X, -lean * 0.6))
        hips_lift(rig, -0.04 if 0.33 <= t < 0.7 else 0.0)
    elif kind == 'ult':  # arms up, head back, slipper storm face
        # rotations stack down the chain, so keep each small: about 17 degrees back in total, face still readable
        set_world_rot(rig, B['chest'], axis_rot(X, -6)); set_world_rot(rig, B['head'], axis_rot(X, -8)); set_world_rot(rig, B['spine'], axis_rot(X, -3))
        pq, pt = Quaternion(), Vector((0, 0, 0))
        for k in (-1, 1):
            side = 'l' if k < 0 else 'r'
            sh = rest_mat(rig, 'upperarm.' + side).translation; wr = rest_mat(rig, 'hand.' + side).translation
            q = (wr - sh).rotation_difference(Vector((k * 0.85, 0.12, 1.95)) - sh)  # hands clear of the hair silhouette
            set_world_rot(rig, B['upperarm.' + side], q); set_world_rot(rig, B['hand.' + side], axis_rot(X, 10))
        set_prop(rig, pq, pt); return
    set_prop(rig, pq, pt)
    g = prop_grips(pq, pt)
    for k in (-1, 1): aim_arm(rig, k, g[k] + WRIST_OFF)

def make_action(rig, name, kind, frames, loop=True):
    act = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act
    n = frames
    for f in range(n + 1):
        t = (f % n) / n if loop else min(f, n) / n
        bpy.context.scene.frame_set(f); pose_frame(rig, t, kind); key_all(rig, f, ANIM_BONES)
    act.frame_range = (0, n); act.use_frame_range = True
    act.use_fake_user = True; return act

def stage_anim():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'ahma_bake.blend'))
    sc = bpy.context.scene; sc.render.fps = FPS
    rig = bpy.data.objects['ahma_rig']
    acts = [make_action(rig, 'idle', 'idle', 60), make_action(rig, 'run', 'run', 24), make_action(rig, 'attack', 'attack', 18), make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; st = tr.strips.new(a.name, 0, a); tr.mute = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'ahma_anim.blend'))
    print('[anim] actions', [a.name for a in acts])

# =====================================================================================
# export + verify
# =====================================================================================
def stage_export():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'ahma_anim.blend'))
    rig = bpy.data.objects['ahma_rig']; reset_pose(rig)
    head = bpy.data.objects['ahma_head']
    for k in head.data.shape_keys.key_blocks: k.value = 0.0
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
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Icosphere']  # Icosphere = importer bone-shape helper
    rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in meshes:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co; lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    # importer converts back to Blender axes: glTF y -> Blender z, glTF -z -> Blender y
    print(f'[verify] tris {sum(tri_count(o) for o in meshes)}; bounds X {lo.x:.3f}..{hi.x:.3f} height {hi.z - lo.z:.3f} depth(Y) {lo.y:.3f}..{hi.y:.3f}')
    print('[verify] facing: nose/glasses at Blender +Y means glTF -Z ->', 'OK' if hi.y > 0.3 else 'WRONG')
    print('[verify] bones', [b.name for b in rig.data.bones])
    hb = rig.matrix_world @ rig.data.bones['head'].head_local; print(f'[verify] head bone head (Blender) {tuple(round(x, 3) for x in hb)}')
    for o in meshes:
        if o.data.shape_keys: print('[verify] morphs on', o.name, [k.name for k in o.data.shape_keys.key_blocks][1:])
        print(f'[verify] {o.name}: {tri_count(o)} tris, mats {[m.name for m in o.data.materials]}')
    print('[verify] animations', [a.name for a in bpy.data.actions], 'images', [(i.name, i.size[0]) for i in bpy.data.images])

# =====================================================================================
# final check shots
# =====================================================================================
def stitch(paths, out, cols):
    import numpy as np
    ims = [bpy.data.images.load(p) for p in paths]; w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
    buf = np.zeros((h * rows, w * cols, 4), np.float32)
    for i, im in enumerate(ims):
        r, c = divmod(i, cols); a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a)
        buf[(rows - 1 - r) * h:(rows - r) * h, c * w:(c + 1) * w] = a.reshape(h, w, 4)
    o = bpy.data.images.new('stitch', w * cols, h * rows); o.pixels.foreach_set(buf.ravel()); o.filepath_raw = out; o.file_format = 'PNG'; o.save()
    for im in ims: bpy.data.images.remove(im)
    bpy.data.images.remove(o)

def play(rig, name, frame):
    rig.animation_data.action = bpy.data.actions[name]; bpy.context.scene.frame_set(frame)

def stage_shots():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'ahma_anim.blend'))
    hide_hi(); RL.setup_render(768, 1024, 32); RL.studio_light((0, 0, 1.1)); RL.floor()
    rig = bpy.data.objects['ahma_rig']; tmp = os.path.join(WORK, 'shots'); os.makedirs(tmp, exist_ok=True)
    for k in bpy.data.objects['ahma_head'].data.shape_keys.key_blocks: k.value = 0.0
    # turnaround in the idle pose (hands on the walker)
    play(rig, 'idle', 0); paths = []
    for i, ang in enumerate((0, 45, 90, 180)):
        a = math.radians(ang); p = os.path.join(tmp, f'turn_{i}.png'); paths.append(p)
        RL.shoot(p, (-6.3 * math.sin(a), 6.3 * math.cos(a), 1.6), (0, 0, 1.05), 60)
    stitch(paths, os.path.join(SHOTS, 'turnaround.png'), 4)
    # animation contact sheet: four frames of each action, three-quarter view
    RL.setup_render(512, 640, 24); paths = []
    for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
        for i in range(4):
            play(rig, name, int(i * n / 4)); p = os.path.join(tmp, f'{name}_{i}.png'); paths.append(p)
            RL.shoot(p, (-4.0, 4.8, 1.9), (0, 0.2, 1.0), 60)
    stitch(paths, os.path.join(SHOTS, 'anim_sheet.png'), 4)
    play(rig, 'idle', 0)
    # side by side with the old model at the same scale (old glb faces +Z, so turn it round)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'ref', 'heroes', 'ahma.glb'))
    old = [o for o in bpy.context.selected_objects if o.parent is None]
    for o in old: o.location.x += 1.5; o.rotation_euler.z += math.pi
    for o in bpy.data.objects:
        if o.name == 'Icosphere': o.hide_render = True
    rig.location.x = -1.5  # meshes are parented to the rig
    play(rig, 'idle', 0)
    RL.setup_render(1400, 900, 32)
    RL.shoot(os.path.join(SHOTS, 'side_by_side_old_vs_new.png'), (0, 8.5, 1.5), (0, 0, 1.05), 50)
    print('[shots] turnaround, anim_sheet, side_by_side written')

def stage_expr_final():
    stage_expr('ahma_anim.blend', 'expr')
    stitch([os.path.join(SHOTS, f'expr_{n}.png') for n in ('idle', 'angry', 'grin', 'ult')], os.path.join(SHOTS, 'expressions.png'), 4)

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build', 'look']
    for a in args:
        {'build': stage_build, 'look': stage_look, 'rig': stage_rig, 'expr': stage_expr, 'bake': stage_bake, 'anim': stage_anim, 'export': stage_export, 'verify': stage_verify, 'shots': stage_shots, 'exprfinal': stage_expr_final, 'looktex': lambda: stage_look('tex', 'ahma_bake.blend'), 'exprtex': lambda: stage_expr('ahma_bake.blend', 'exprtex')}[a]()
