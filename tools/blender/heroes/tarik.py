"""Teh Tarik Auntie (key `tarik`), Gate 2 hero. Headless build, same pipeline as ahma.py:
  /opt/homebrew/bin/blender -b -P tools/blender/heroes/tarik.py -- build look rig expr bake anim export verify shots exprfinal
Stages save a .blend in TARIK_WORK (default: the session scratchpad) so later stages can be re-run alone.
Blender axes: Z up, she faces +Y. The glTF exporter makes that Y up, facing -Z.
Design (from ref/heroes/tarik.glb): a Chinese kopitiam drinks-stall auntie. Short dark perm with grey streaks, strong brows,
beige blouse with cloth knots, pink arm sleeves, green stall apron with a pocket, towel over the left shoulder, steel cups on the
right hip, dark slacks, red slippers. Steel jug in the right hand, steel mug of teh in the left. Empties spout_jug and spout_mug
mark the pour points for the tea stream."""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
from hero_lib import *
import render_lib as RL
import ahma as A   # MB node builder and the generic helpers are reused from Ah Ma, nothing in ahma.py is changed

WORK = os.environ.get('TARIK_WORK', '/tmp/tarik_work'); os.makedirs(WORK, exist_ok=True)
OUT_GLB = os.path.join(ROOT, 'assets', 'heroes', 'tarik.glb')
SHOTS = os.path.join(ROOT, 'shots', 'heroes', 'tarik'); os.makedirs(SHOTS, exist_ok=True)
MB = A.MB; smoothstep = A.smoothstep; falloff = A.falloff

# ---------------- palette (sRGB hex -> linear) ----------------
COL = dict(
    skin='#DFA67C', skin_cool='#C99070', skin_warm='#F3C89C', skin_shade='#9A5F72', blush='#E27E6C', lip='#B9585E', lid='#4A2E3A', mouth='#3E1A26', tongue='#C96E74', teeth='#F2ECE0',
    hair='#3E2E34', hair_mid='#2C2028', hair_dark='#1A1420', hair_deep='#1C3042', hair_light='#8E7A92', grey='#C9C2C8', brow='#2A1E24',
    blouse='#EADFC4', blouse_warm='#F2E6CC', blouse_cool='#D5C9B9', blouse_shade='#AC9DB0', knot='#C9B48E',
    sleeve='#E07CC8', sleeve_light='#F5A8E0', sleeve_shade='#8F4A90', apron='#2A8F78', apron_light='#4FB89A', apron_shade='#1C5E62', apron_deep='#15434C', stain='#B27A44', tie='#E88CC4',
    slacks='#2C2D38', slacks_light='#454860', slacks_shade='#1A1B2A', slipper='#D7322E', slipper_dark='#9A1F1C', towel='#F4F1EA', towel_shade='#BFC3D6', towel_stripe='#3F6FB5',
    steel='#C9CCD2', steel_dark='#6E747C', steel_light='#F1F3F6', tea='#B87A3E', tea_dark='#7A4A1E', foam='#F2E6CF', gold='#D8A94A',
    sclera='#FFF7E9', sclera_shade='#E4D3C8', iris='#4A2A1A', iris_light='#8A5A32', pupil='#1A100E',
)
LIN = {k: srgb(v) for k, v in COL.items()}
def c4(k): return (*LIN[k], 1)

# ---------------- landmarks (metres, Blender Z up, +Y forward) ----------------
HS = 0.95                                   # head scale relative to Ah Ma's head
HEAD_C = Vector((0, 0.0, 1.42))
def R(x, y, z): return HEAD_C + Vector((x, y, z)) * HS     # head-relative point, Ah Ma offsets scaled
EYE_L = R(-0.165, 0.318, 0.0); EYE_R = R(0.165, 0.318, 0.0)
EYE_R_BALL = 0.066 * HS
MOUTH_C = R(0, 0.34, -0.215)
SHOULDER = {k: Vector((k * 0.40, 0.0, 1.02)) for k in (-1, 1)}
ELBOW = {k: Vector((k * 0.58, 0.06, 0.82)) for k in (-1, 1)}
WRIST = {k: Vector((k * 0.60, 0.20, 0.64)) for k in (-1, 1)}
GRIP = {k: WRIST[k] + Vector((-k * 0.04, 0.0, -0.19)) for k in (-1, 1)}   # handle bar centre inside the fist = handslot bone head
JUG_C = GRIP[1] + Vector((0, 0.17, 0.0))     # jug axis, right hand
MUG_C = GRIP[-1] + Vector((0, 0.13, -0.02))  # mug axis, left hand
SPOUT_JUG = JUG_C + Vector((0, 0.19, 0.17))
SPOUT_MUG = MUG_C + Vector((0, 0, 0.085))

def sx(v, s): return Vector((v.x * s, v.y, v.z))

def ecyl(s, c, z0, z1, r0, r1, yscale=1.0, seg=24):
    """Tapered cylinder with an elliptical section (y squashed by yscale) along Z, added to soup s."""
    g = bmesh.ops.create_cone(s.bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=z1 - z0)
    m = Matrix.Translation(Vector((c[0], c[1], (z0 + z1) / 2))) @ Matrix.Diagonal((1, yscale, 1, 1))
    for v in g['verts']: v.co = m @ v.co
    return s

def cut_box(ob, c, size):
    boolean_cut(ob, Soup('cut').box(c, size).to_object())

# =====================================================================================
# geometry
# =====================================================================================
def build_head():
    """Big clean forms, smoothed: cranium, wide cheek mass, jaw, small chin, one wedge nose, ears. Everything else is painted."""
    s = Soup('tarik_head_skin')
    s.ellipsoid(HEAD_C, (0.40 * HS, 0.38 * HS, 0.38 * HS))
    s.ellipsoid(R(0, 0.05, -0.12), (0.37 * HS, 0.31 * HS, 0.23 * HS))    # cheek mass, a touch wider than Ah Ma: a rounder, fuller face
    s.ellipsoid(R(0, 0.09, -0.24), (0.29 * HS, 0.22 * HS, 0.14 * HS))    # jaw, kept just inside the cranium: a jaw that pokes out leaves a crease ridge after decimation
    s.sphere(R(0, 0.23, -0.27), 0.07 * HS)                                # chin
    for k in (-1, 1):
        s.ellipsoid(R(k * 0.405, -0.02, -0.04), (0.05 * HS, 0.09 * HS, 0.12 * HS))   # ears (short hair, they show)
    s.capsule(R(0, 0.34, 0.03), R(0, 0.405, -0.10), 0.028 * HS, 0.052 * HS)         # wedge nose
    s.capsule(R(0, 0, -0.42), R(0, 0.02, -0.18), 0.14 * HS)                           # neck
    head, _ = s.remesh(voxel=0.010, smooth=16, smooth_factor=0.6)
    return head

def cut_face(head):
    """Eye sockets and the mouth slit, cut after decimation: cutting first left ragged socket rims and a gappy slit once the slivers collapsed."""
    for k in (-1, 1):
        c = Soup('cut_eye'); c.sphere(sx(EYE_L, -k) + Vector((0, 0.022, 0)), EYE_R_BALL + 0.004, seg=32)
        boolean_cut(head, c.to_object())
    mc = MOUTH_C + Vector((0, 0.03, 0)); mr = (0.125 * HS, 0.10 * HS, 0.005)
    c = Soup('cut_mouth'); c.ellipsoid(mc, mr, seg=32)
    boolean_cut(head, c.to_object())
    bm = bmesh.new(); bm.from_mesh(head.data)   # the boolean leaves a dent, delete the cutter faces so the mouth is a hole
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if sum(((f.calc_center_median() - mc)[i] / mr[i]) ** 2 for i in range(3)) < 1.03], context='FACES')
    bm.to_mesh(head.data); bm.free()
    for i in reversed(range(len(head.data.materials))):   # the cutters bring an empty material slot along
        if head.data.materials[i] is None: head.data.materials.pop(index=i)

def build_mouth_parts():
    cav = Soup('tarik_cavity').box(MOUTH_C + Vector((0, -0.16, -0.045)), (0.28 * HS, 0.10, 0.15 * HS)).to_object()
    teeth = Soup('tarik_teeth').box(MOUTH_C + Vector((0, -0.055, -0.017)), (0.15 * HS, 0.03, 0.022)).to_object()
    set_material(cav, flat_material('tarik_mouth', LIN['mouth'], .6))
    set_material(teeth, flat_material('tarik_teeth', LIN['teeth'], .5))
    return [cav, teeth]

def build_brows():
    """Strong dark brows, thick inner end, pointed outer end (the old model's signature)."""
    out = []
    for k in (-1, 1):
        b = Soup('tarik_brow').capsule(R(k * 0.06, 0.355, 0.095), R(k * 0.17, 0.335, 0.118), 0.026, 0.020, seg=10) \
            .capsule(R(k * 0.17, 0.335, 0.118), R(k * 0.30, 0.255, 0.092), 0.020, 0.006, seg=10)
        ob, _ = b.remesh(voxel=0.005, smooth=1, target_tris=240)
        set_material(ob, flat_material('tarik_brow', LIN['brow'], .7)); out.append(ob)
    return out

# short cropped perm: scalp cap plus designed curl masses (head-relative centre, radii, tilt deg). Mirrored where x != 0.
HAIR_CLUMPS = [   # fewer, larger clumps, each its own smooth shell (relative to HEAD_C, in head units)
    ((0.00, -0.03, 0.325), (0.32, 0.30, 0.16), 0),     # crown, sets the 1.88 top
    ((0.00, 0.24, 0.28), (0.16, 0.12, 0.12), 0),       # fringe middle, hairline high so the forehead shows
    ((0.24, 0.18, 0.26), (0.15, 0.13, 0.12), 20),      # fringe sides
    ((0.37, 0.03, 0.12), (0.12, 0.18, 0.16), 0),       # temples
    ((0.33, -0.22, 0.12), (0.15, 0.17, 0.15), -15),    # sides back
    ((0.00, -0.36, 0.12), (0.26, 0.14, 0.20), 0),      # back
    ((0.20, -0.30, -0.10), (0.14, 0.12, 0.12), 10),    # nape
    ((0.00, -0.33, -0.08), (0.22, 0.12, 0.12), 0),     # nape middle, covers the back of the neck
]

def build_hair():
    s = Soup('tarik_hair')
    s.ellipsoid(HEAD_C + Vector((0, -0.05, 0.08)), (0.37 * HS, 0.35 * HS, 0.30 * HS), seg=14)   # scalp cap, tucked under the clumps
    for c, r, tilt in HAIR_CLUMPS:
        for k in ((-1, 1) if c[0] else (1,)):
            q = Quaternion((0, 0, 1), math.radians(k * tilt))
            s.ellipsoid(R(k * c[0], c[1], c[2]), tuple(x * HS for x in r), rot=q, seg=24 if c[2] > 0.3 else 16)
    hair = s.to_object(); shade_smooth(hair)
    set_material(hair, flat_material('tarik_hair', LIN['hair'], .8))
    return hair

def build_eyes():
    objs = []
    for name, c in (('eye.l', EYE_L), ('eye.r', EYE_R)):
        o = Soup('tarik_' + name).sphere(c, EYE_R_BALL, seg=20).to_object(); shade_smooth(o)
        set_material(o, flat_material('tarik_eye', LIN['sclera'], .2)); objs.append(o)
    return objs

def build_earrings():
    out = []
    for k in (-1, 1):
        o = Soup('earring').sphere(R(k * 0.43, -0.01, -0.145), 0.022, seg=12).to_object(); shade_smooth(o)
        set_material(o, flat_material('tarik_gold', LIN['gold'], .3, .8)); out.append(o)
    return out

def hand_soup(s, wrist, side, curl=40):
    """Chunky stylised fist around a vertical handle bar. side: +1 right, -1 left. Copied from Ah Ma with a curl parameter."""
    rot = Matrix.Rotation(math.radians(90 * side), 4, 'Z')
    if side < 0: rot = rot @ Matrix.Diagonal((-1, 1, 1, 1))
    T = Matrix.Translation(wrist) @ rot
    def P(x, y, z): return T @ Vector((x, y, z))
    s.ellipsoid(P(0, 0, -0.075), (0.082, 0.034, 0.085), rot=rot)
    s.sphere(P(0, 0, -0.01), 0.045)
    s.ellipsoid(P(0, 0.0, -0.15), (0.09, 0.032, 0.028), rot=rot)
    fingers = [(-0.072, 0.90), (-0.024, 1.0), (0.024, 0.95), (0.072, 0.76)]
    for x, L in fingers:
        p = Vector((x, 0.0, -0.15)); d = Vector((0, 0, -1)); r = 0.021
        for seg in (0.052, 0.042, 0.036):
            d = (Matrix.Rotation(math.radians(curl), 3, 'X') @ d).normalized()
            q = p + d * seg * L
            s.capsule(P(*p), P(*q), r, r * .9, seg=12); p = q; r *= .9
    p = Vector((0.075, 0.015, -0.06)); d = Vector((0.45, 0.6, -0.65)).normalized(); r = 0.025   # thumb over the fingers
    for seg in (0.05, 0.042):
        q = p + d * seg; s.capsule(P(*p), P(*q), r, r * .88, seg=12); p = q; r *= .9
        d = (Matrix.Rotation(math.radians(-35), 3, 'Y') @ d).normalized()
    return s

def build_arm(k):
    """Skin arm shoulder to fist, plus the pink elastic arm sleeve over the forearm."""
    s = Soup('tarik_arm'); sh, el, wr = SHOULDER[k], ELBOW[k], WRIST[k]
    s.capsule(sh, el, 0.098, 0.090).capsule(el, wr, 0.085, 0.064); s.sphere(el, 0.092)
    hand_soup(s, wr, k)
    arm, arm_hi = s.remesh(voxel=0.0055, smooth=2, smooth_factor=.4, target_tris=1150, keep_hi=True)
    set_material(arm, flat_material('tarik_skin', LIN['skin'], .55))
    sl = Soup('tarik_sleeve')
    sl.capsule(el + (wr - el) * 0.02, wr + (el - wr) * 0.10, 0.100, 0.082, seg=20)
    sleeve, sleeve_hi = sl.remesh(voxel=0.008, smooth=2, target_tris=360, keep_hi=True)
    set_material(sleeve, flat_material('tarik_sleeve', LIN['sleeve'], .8))
    cuffs = []
    for p, rr in ((el + (wr - el) * 0.06, 0.102), (wr + (el - wr) * 0.12, 0.084)):
        d = (wr - el).normalized(); q = d.to_track_quat('Z', 'Y').to_euler()
        t = torus('cuff', p, rr, 0.012, rot=q, seg=16, rseg=5); set_material(t, flat_material('tarik_sleeve_cuff', LIN['sleeve_shade'], .8)); cuffs.append(t)
    return arm, arm_hi, sleeve, sleeve_hi, cuffs

def build_blouse():
    s = Soup('tarik_blouse')
    s.ellipsoid((0, 0.0, 0.88), (0.44, 0.33, 0.24))
    s.sphere((0, 0.12, 0.78), 0.30)                                    # belly
    s.ellipsoid((0, 0.03, 0.72), (0.42, 0.33, 0.16))                   # hem body
    s.capsule((0, 0.04, 0.74), (0, 0.04, 0.62), 0.40, 0.42, seg=32)    # flared hem
    for k in (-1, 1):
        s.sphere((k * 0.41, 0.0, 1.02), 0.16)
        s.capsule((k * 0.43, 0.0, 1.00), (k * 0.56, 0.04, 0.84), 0.16, 0.13)   # short puffy sleeves
    blouse, blouse_hi = s.remesh(voxel=0.010, smooth=4, target_tris=2300, keep_hi=True)
    set_material(blouse, flat_material('tarik_blouse', LIN['blouse'], .8))
    return blouse, blouse_hi

def build_apron():
    """Green stall apron: bib over the chest, skirt to the knee, front half only. A shell 0.04 outside the blouse and belly."""
    s = Soup('tarik_apron')
    s.ellipsoid((0, 0.0, 0.88), (0.50, 0.39, 0.27)); s.sphere((0, 0.12, 0.78), 0.35)
    ecyl(s, (0, 0.05, 0), 0.30, 0.78, 0.39, 0.48, yscale=0.95)
    ap, _ = s.remesh(voxel=0.010, smooth=2, smooth_factor=0.4)
    bm = bmesh.new(); bm.from_mesh(ap.data)   # ponytail: sequential EXACT booleans empty this mesh, so the apron outline is cut by deleting faces
    def gone(p): return p.y < 0.10 or p.z < 0.30 or p.z > 0.95   # one straight hem at the chest, the stepped bib left a ledge and torn corners
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if gone(f.calc_center_median())], context='FACES')
    rim = [v for v in bm.verts if any(e.is_boundary for e in v.link_edges)]
    for _ in range(10):   # straighten the stair-stepped cut edge along the boundary loop
        new = {}
        for v in rim:
            nb = [e.other_vert(v).co for e in v.link_edges if e.is_boundary]
            if len(nb) == 2: new[v] = v.co * 0.4 + (nb[0] + nb[1]) * 0.3
        for v, co in new.items(): v.co = co
    for v in rim:   # snap each rim vert to the nearest of the cut lines, so the hems and the bib edges are straight
        p = v.co
        d, axis, val = min([(abs(p.z - 0.95), 'z', 0.95), (abs(p.z - 0.30), 'z', 0.30), (abs(p.y - 0.10), 'y', 0.10)])
        if d < 0.03: setattr(p, axis, val)
    bmesh.ops.dissolve_degenerate(bm, dist=0.003, edges=bm.edges)   # snapped rim verts can make zero-area faces, which break the bone heat solve
    bm.to_mesh(ap.data); bm.free()
    decimate(ap, 1500); shade_smooth(ap)
    set_material(ap, flat_material('tarik_apron', LIN['apron'], .8))
    parts = [ap]
    bow = Soup('bow').ellipsoid((0.07, -0.40, 0.72), (0.075, 0.03, 0.05), seg=10).ellipsoid((-0.07, -0.40, 0.72), (0.075, 0.03, 0.05), seg=10).sphere((0, -0.415, 0.72), 0.03, seg=10) \
        .capsule((0.03, -0.405, 0.70), (0.06, -0.41, 0.56), 0.02, 0.014, seg=8).capsule((-0.03, -0.405, 0.70), (-0.05, -0.41, 0.58), 0.02, 0.014, seg=8).to_object(); shade_smooth(bow)
    set_material(bow, flat_material('tarik_tie', LIN['tie'], .7)); parts.append(bow)
    st = Soup('tarik_strap')
    for k in (-1, 1): st.capsule((k * 0.20, 0.36, 0.93), (k * 0.11, -0.10, 1.14), 0.013, seg=8)
    st.capsule((-0.11, -0.10, 1.14), (0.11, -0.10, 1.14), 0.013, seg=8)
    strap = st.to_object(); shade_smooth(strap); set_material(strap, flat_material('tarik_apron', LIN['apron'], .8)); parts.append(strap)
    pen = Soup('pen').capsule((0.08, 0.485, 0.53), (0.10, 0.49, 0.64), 0.008, seg=8).to_object(); shade_smooth(pen)   # pen in the painted pocket
    set_material(pen, flat_material('tarik_steel', LIN['steel'], .4, 1.0)); parts.append(pen)
    return parts

def build_collar_and_trim():
    col = torus('tarik_collar', (0, 0.01, 1.10), 0.15, 0.028, seg=24, rseg=6)
    set_material(col, flat_material('tarik_blouse', LIN['blouse'], .8))
    knots = []
    for z in (1.075, 1.035):   # cloth knot buttons down the centre front, above the bib
        y = 0.33 * (1 - ((z - 0.88) / 0.24) ** 2) ** .5 if abs(z - 0.88) < 0.24 else 0.2
        y = max(y, 0.16) + 0.012
        kn = Soup('knot').sphere((0, y + 0.01, z), 0.022, seg=10).capsule((0.02, y + 0.004, z), (0.05, y - 0.012, z), 0.011, seg=8).to_object(); shade_smooth(kn)
        set_material(kn, flat_material('tarik_knot', LIN['knot'], .6)); knots.append(kn)
    # towel over the left shoulder: a slab over the top with a flap down the front and back
    tw = Soup('tarik_towel')
    for i in range(17):   # a strip of flat ellipsoids draped over the shoulder, front flap to the chest, back flap shorter
        a = math.radians(-70 + 140 * i / 16)
        c = Vector((-0.41, 0.21 * math.sin(a), 1.19 - 0.20 * (1 - math.cos(a)) ** 0.8 * 1.15))
        tw.ellipsoid(c, (0.075, 0.06, 0.016), rot=Quaternion((1, 0, 0), -a), seg=10)
    tw.ellipsoid((-0.41, 0.22, 0.93), (0.075, 0.016, 0.11), seg=10); tw.ellipsoid((-0.41, -0.21, 0.96), (0.075, 0.016, 0.09), seg=10)
    towel, _ = tw.remesh(voxel=0.007, smooth=5, smooth_factor=0.5, target_tris=520)
    set_material(towel, flat_material('tarik_towel', LIN['towel'], .9))
    # two steel cups hanging on the right hip, rims up
    cups = Soup('tarik_cups')
    for i, (x, y) in enumerate(((0.47, 0.18), (0.51, 0.07))):
        cups.capsule((x, y, 0.52), (x, y, 0.64), 0.035, 0.038, seg=14)
    cp = cups.to_object(); shade_smooth(cp); set_material(cp, flat_material('tarik_steel', LIN['steel'], .4, 1.0))
    hook = Soup('hook').capsule((0.47, 0.13, 0.64), (0.45, 0.12, 0.71), 0.006, seg=6).to_object(); shade_smooth(hook)
    set_material(hook, flat_material('tarik_steel', LIN['steel'], .4, 1.0))
    return [col, towel, cp, hook] + knots

def build_slacks():
    s = Soup('tarik_slacks')
    s.ellipsoid((0, 0.02, 0.66), (0.40, 0.30, 0.16))
    for k in (-1, 1):
        s.capsule((k * 0.17, 0.02, 0.64), (k * 0.185, 0.0, 0.36), 0.155, 0.135)
        s.capsule((k * 0.185, 0.0, 0.36), (k * 0.185, 0.0, 0.15), 0.135, 0.125)
    slacks, slacks_hi = s.remesh(voxel=0.010, smooth=4, target_tris=1200, keep_hi=True)
    set_material(slacks, flat_material('tarik_slacks', LIN['slacks'], .85))
    return slacks, slacks_hi

def build_feet():
    s = Soup('tarik_feet'); sl = Soup('tarik_slippers')
    for k in (-1, 1):
        x = k * 0.185
        s.capsule((x, 0.0, 0.18), (x, 0.02, 0.07), 0.065, 0.06)
        s.ellipsoid((x, 0.075, 0.055), (0.075, 0.14, 0.045))
        for tx, ty, tr in ((0.045, 0.215, 0.03), (0.015, 0.225, 0.026), (-0.015, 0.22, 0.024), (-0.042, 0.205, 0.022)):
            s.sphere((x + k * tx, ty, 0.045), tr, seg=12)
        sl.box((x, 0.07, 0.013), (0.19, 0.36, 0.026))
        sl.capsule((x, 0.185, 0.03), (x + k * 0.08, 0.06, 0.05), 0.012)
        sl.capsule((x, 0.185, 0.03), (x - k * 0.08, 0.06, 0.05), 0.012)
    feet, feet_hi = s.remesh(voxel=0.007, smooth=3, target_tris=700, keep_hi=True)
    set_material(feet, flat_material('tarik_skin', LIN['skin'], .55))
    slip, slip_hi = sl.remesh(voxel=0.006, smooth=2, target_tris=560, keep_hi=True)
    set_material(slip, flat_material('tarik_slipper', LIN['slipper'], .5))
    return feet, feet_hi, slip, slip_hi

def build_jug():
    """Steel teh tarik jug, handle bar through the right fist, spout forward (+Y)."""
    C = JUG_C; G = GRIP[1]
    st = Soup('tarik_jug_steel')
    ecyl(st, (C.x, C.y, 0), C.z - 0.14, C.z + 0.12, 0.085, 0.10, seg=24)
    st.capsule(C + Vector((0, 0.085, 0.07)), SPOUT_JUG, 0.032, 0.018, seg=12)            # spout
    for a, b in ((C + Vector((0, -0.09, 0.09)), G + Vector((0, 0, 0.12))), (G + Vector((0, 0, 0.12)), G + Vector((0, 0, -0.12))), (G + Vector((0, 0, -0.12)), C + Vector((0, -0.085, -0.10)))):
        st.capsule(a, b, 0.014, seg=8)                                                     # handle
    jug = st.to_object(); shade_smooth(jug); set_material(jug, flat_material('tarik_steel', LIN['steel'], .4, 1.0))
    rim = torus('rim', C + Vector((0, 0, 0.12)), 0.10, 0.012, seg=20, rseg=5); set_material(rim, flat_material('tarik_steel_dark', LIN['steel_dark'], .5, 1.0))
    t = Soup('tarik_jug_tea'); ecyl(t, (C.x, C.y, 0), C.z + 0.05, C.z + 0.07, 0.092, 0.092, seg=24)
    tea = t.to_object(); set_material(tea, flat_material('tarik_tea', LIN['tea'], .3))
    return join([jug, rim, tea], 'tarik_jug')

def build_mug():
    C = MUG_C; G = GRIP[-1]
    st = Soup('tarik_mug_steel')
    ecyl(st, (C.x, C.y, 0), C.z - 0.09, C.z + 0.085, 0.072, 0.074, seg=24)
    for a, b in ((C + Vector((0, -0.07, 0.06)), G + Vector((0, 0, 0.08))), (G + Vector((0, 0, 0.08)), G + Vector((0, 0, -0.08))), (G + Vector((0, 0, -0.08)), C + Vector((0, -0.07, -0.06)))):
        st.capsule(a, b, 0.013, seg=8)
    mug = st.to_object(); shade_smooth(mug); set_material(mug, flat_material('tarik_steel', LIN['steel'], .4, 1.0))
    rim = torus('rim', C + Vector((0, 0, 0.085)), 0.074, 0.010, seg=20, rseg=5); set_material(rim, flat_material('tarik_steel_dark', LIN['steel_dark'], .5, 1.0))
    t = Soup('tarik_mug_tea'); ecyl(t, (C.x, C.y, 0), C.z + 0.055, C.z + 0.072, 0.066, 0.066, seg=20)
    tea = t.to_object(); set_material(tea, flat_material('tarik_tea', LIN['tea'], .3))
    f = Soup('tarik_mug_foam'); f.ellipsoid(C + Vector((0, 0, 0.074)), (0.055, 0.055, 0.012), seg=16)
    foam = f.to_object(); shade_smooth(foam); set_material(foam, flat_material('tarik_foam', LIN['foam'], .7))
    return join([mug, rim, tea, foam], 'tarik_mug')

def add_empty(name, pos):
    e = bpy.data.objects.new(name, None); e.empty_display_type = 'SPHERE'; e.empty_display_size = 0.03
    bpy.context.scene.collection.objects.link(e); e.location = pos; return e

def stage_build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    head = build_head(); set_material(head, flat_material('tarik_skin', LIN['skin'], .55))
    head_hi = head.copy(); head_hi.data = head.data.copy(); head_hi.name = 'tarik_head_hi'; bpy.context.scene.collection.objects.link(head_hi)
    d = head.modifiers.new('dec', 'DECIMATE'); d.ratio = 3400 / tri_count(head); d.use_collapse_triangulate = True; d.use_symmetry = True; d.symmetry_axis = 'X'
    apply_mod(head, d); cut_face(head); shade_smooth(head)   # the cuts add about 1900 tris back
    head = join([head] + build_mouth_parts() + build_brows(), 'tarik_head')
    headgear = join([build_hair()] + build_earrings(), 'tarik_headgear')
    eyes = join(build_eyes(), 'tarik_eyes')
    body_parts = []; hi = [head_hi]
    for k in (-1, 1):
        a, ah, sl, slh, cuffs = build_arm(k); body_parts += [a, sl] + cuffs; hi += [ah, slh]
    bl, blh = build_blouse(); body_parts.append(bl); hi.append(blh)
    body_parts += build_apron()
    sk, skh = build_slacks(); body_parts.append(sk); hi.append(skh)
    ft, fth, sp, sph = build_feet(); body_parts += [ft, sp]; hi += [fth, sph]
    body_parts += build_collar_and_trim()
    body = join(body_parts, 'tarik_body')
    jug = build_jug(); mug = build_mug()
    add_empty('spout_jug', SPOUT_JUG); add_empty('spout_mug', SPOUT_MUG)
    hi_col = bpy.data.collections.new('hi'); bpy.context.scene.collection.children.link(hi_col)
    for h in hi:
        for c in h.users_collection: c.objects.unlink(h)
        hi_col.objects.link(h); h.hide_render = True; h.hide_viewport = True
    for o in (head, headgear, eyes, body, jug, mug):
        print(f'[build] {o.name}: {tri_count(o)} tris, {len(o.data.materials)} mats')
    print('[build] total tris', sum(tri_count(o) for o in (head, headgear, eyes, body, jug, mug)))
    zmax = max((o.matrix_world @ v.co).z for o in (head, headgear) for v in o.data.vertices)
    print(f'[build] top of hair z {zmax:.3f}')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'tarik_build.blend'))

# =====================================================================================
# quick look shots
# =====================================================================================
def hide_hi():
    for o in bpy.data.objects: o.hide_render = o.name.endswith('_hi') or o.name.startswith('cut')

def stage_look(tag='look', blend='tarik_build.blend'):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, blend))
    hide_hi(); RL.setup_render(1024, 1024, 24); RL.studio_light((0, 0, 0.95)); RL.floor()
    RL.shoot(os.path.join(SHOTS, f'{tag}_front.png'), (0, 5.8, 1.4), (0, 0, 0.92), 60)
    RL.shoot(os.path.join(SHOTS, f'{tag}_three_quarter.png'), (-3.9, 4.2, 1.8), (0, 0, 0.92), 60)
    RL.shoot(os.path.join(SHOTS, f'{tag}_face.png'), (-1.1, 2.1, 1.7), (0, 0.1, 1.40), 85)
    RL.shoot(os.path.join(SHOTS, f'{tag}_hand.png'), (1.6, 1.3, 0.7), (0.62, 0.25, 0.52), 90)

# =====================================================================================
# rig
# =====================================================================================
def _bones():
    B = [
        ('root', (0, 0, 0), (0, 0, 0.25), None),
        ('hips', (0, 0, 0.62), (0, 0, 0.74), 'root'),
        ('spine', (0, 0, 0.74), (0, 0, 0.88), 'hips'),
        ('chest', (0, 0, 0.88), (0, 0, 1.04), 'spine'),
        ('neck', (0, 0, 1.04), (0, 0.01, 1.14), 'chest'),
        ('head', (0, 0.01, 1.14), (0, 0.02, 1.56), 'neck'),
        ('eye.l', tuple(EYE_L), tuple(EYE_L + Vector((0, 0.06, 0))), 'head'),
        ('eye.r', tuple(EYE_R), tuple(EYE_R + Vector((0, 0.06, 0))), 'head'),
    ]
    for k, sd in ((-1, 'l'), (1, 'r')):
        B += [
            ('upperarm.' + sd, tuple(SHOULDER[k]), tuple(ELBOW[k]), 'chest'),
            ('lowerarm.' + sd, tuple(ELBOW[k]), tuple(WRIST[k]), 'upperarm.' + sd),
            ('hand.' + sd, tuple(WRIST[k]), tuple(WRIST[k] + Vector((0, 0.04, -0.18))), 'lowerarm.' + sd),
            ('handslot.' + sd, tuple(GRIP[k]), tuple(GRIP[k] + Vector((0, 0.08, 0))), 'hand.' + sd),
        ]
    for k, sd in ((-1, 'l'), (1, 'r')):
        B += [
            ('upperleg.' + sd, (k * 0.17, 0.02, 0.64), (k * 0.185, 0.0, 0.36), 'hips'),
            ('lowerleg.' + sd, (k * 0.185, 0.0, 0.36), (k * 0.185, 0.0, 0.12), 'upperleg.' + sd),
            ('foot.' + sd, (k * 0.185, 0.0, 0.12), (k * 0.185, 0.14, 0.04), 'lowerleg.' + sd),
            ('toes.' + sd, (k * 0.185, 0.14, 0.04), (k * 0.185, 0.25, 0.03), 'foot.' + sd),
        ]
    B.append(('prop', (0, 0.30, 0), (0, 0.30, 0.3), 'root'))   # no big prop for her: the engine attaches the tea stream to the spout empties
    return B
BONES = _bones()
RIGID = {'eye.l', 'eye.r', 'prop', 'handslot.l', 'handslot.r'}

def make_armature():
    arm = bpy.data.armatures.new('tarik_rig'); ob = bpy.data.objects.new('tarik_rig', arm)
    bpy.context.scene.collection.objects.link(ob); select_only([ob], ob)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, h, t, parent in BONES:
        b = arm.edit_bones.new(name); b.head = h; b.tail = t
        if parent: b.parent = arm.edit_bones[parent]; b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in arm.bones: b.use_deform = b.name not in RIGID
    return ob

def add_shape_keys(head):
    """Ah Ma's painted-face keys, with every landmark taken relative to HEAD_C."""
    me = head.data
    if not me.shape_keys: head.shape_key_add(name='Basis', from_mix=False)
    basis = [v.co.copy() for v in me.vertices]
    mat_of_vert = {}
    for p in me.polygons:
        for vi in p.vertices: mat_of_vert[vi] = p.material_index
    names = [m.name for m in me.materials]
    is_brow = {vi for vi, mi in mat_of_vert.items() if names[mi] == 'tarik_brow'}
    is_skin = {vi for vi, mi in mat_of_vert.items() if names[mi] == 'tarik_skin'}
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
        if co.z > E.z - 0.015: return (0, 0.018 * w, -0.072 * w * smoothstep(-0.015, 0.05, co.z - E.z))
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
            w = falloff(co, R(0, 0.36, 0.09), 0.03, 0.12)
            return (0, -0.006 * w, -0.014 * w) if w > 0 else None
        return None
    def brow_up(i, co):
        if i in is_brow:
            outer = smoothstep(0.03, 0.27, abs(co.x)); return (0, -0.004, 0.035 + 0.02 * outer)
        if i in is_skin:
            w = falloff(co, R(0, 0.34, 0.16), 0.05, 0.2) * smoothstep(R(0, 0, 0.06).z, R(0, 0, 0.14).z, co.z)
            return (0, 0, 0.012 * w) if w > 0 else None
        return None
    def mouth_open(i, co):
        if i in is_brow: return None
        if co.z > MOUTH_C.z + 0.012: return None
        w = falloff(co, R(0, 0.28, -0.25), 0.10, 0.34)
        if w <= 0: return None
        drop = (1 - smoothstep(MOUTH_C.z - 0.001, MOUTH_C.z + 0.001, co.z)) * w   # hinge at the lip cut, the lower face drops as a block
        return (co.x * 0.08 * w, -0.015 * drop, -0.085 * drop)
    def smile(i, co):
        if i in is_brow: return None
        s = 1 if co.x > 0 else -1; corner = R(s * 0.17, 0.33, -0.21)
        w = falloff(co, corner, 0.04, 0.14)
        d = Vector((0, 0, 0))
        if w > 0: d += Vector((s * 0.035 * w, -0.025 * w, 0.05 * w))
        cw = falloff(co, R(s * 0.25, 0.22, -0.12), 0.05, 0.18) if i in is_skin else 0
        if cw > 0: d += Vector((0, 0.01 * cw, 0.015 * cw))
        return tuple(d) if d.length > 0 else None
    def frown(i, co):
        if i in is_brow: return None
        s = 1 if co.x > 0 else -1; corner = R(s * 0.17, 0.33, -0.21)
        w = falloff(co, corner, 0.04, 0.13)
        return (-s * 0.014 * w, 0, -0.04 * w) if w > 0 else None
    for nm, fn in (('blink', blink), ('squint', squint), ('brow_angry', brow_angry), ('brow_up', brow_up),
                   ('mouth_open', mouth_open), ('smile', smile), ('frown', frown)): key(nm, fn)
    nbr = [[] for _ in range(n)]
    for e in me.edges: a, c = e.vertices; nbr[a].append(c); nbr[c].append(a)
    for nm in ('squint', 'smile', 'frown'):   # relax the deltas so the cheek and socket verts move as one plane, no diagonal creases
        d = comp[nm]
        for _ in range(3):
            d[:] = [(d[i] + sum((d[j] for j in nbr[i]), Z.copy()) / max(1, len(nbr[i]))) * 0.5 for i in range(n)]
    mixes = {
        'angry': {'brow_angry': 1.0, 'frown': 1.0, 'blink': 0.45, 'mouth_open': 0.12},
        'grin': {'smile': 1.0, 'squint': 1.0, 'brow_up': 0.5, 'mouth_open': 0.35},
        'ult': {'mouth_open': 1.0, 'brow_up': 0.9, 'smile': 0.7},   # Teh Tarik Rain: a big open-mouthed laugh, brows up
    }
    export = ['blink', 'mouth_open', 'smile', 'angry', 'grin', 'ult']
    for i in range(n):
        basis[i] = basis[i] + comp['smile'][i] * 0.35; me.vertices[i].co = basis[i]   # rest face carries a warm half smile
    me.shape_keys.key_blocks['Basis'].data.foreach_set('co', [c for v in basis for c in v])
    for nm in export:
        sk = head.shape_key_add(name=nm, from_mix=False)
        parts = mixes.get(nm, {nm: 1.0})
        for i in range(n):
            d = Vector((0, 0, 0))
            for cn, wgt in parts.items(): d += comp[cn][i] * wgt
            sk.data[i].co = basis[i] + d
    return export

def stage_rig():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'tarik_build.blend'))
    O = bpy.data.objects
    head, body, gear, eyes, jug, mug = O['tarik_head'], O['tarik_body'], O['tarik_headgear'], O['tarik_eyes'], O['tarik_jug'], O['tarik_mug']
    keys = add_shape_keys(head); print('[rig] shape keys', keys)
    rig = make_armature()
    A.auto_weights(rig, [body, head])
    for v in head.data.vertices:   # the heat map skips a few verts on the open mouth rim
        if not v.groups: head.vertex_groups['head'].add([v.index], 1.0, 'REPLACE')
    for b in rig.data.bones: b.use_deform = True
    names = [m.name for m in body.data.materials]; mat_of = {}
    for p in body.data.polygons:
        for vi in p.vertices: mat_of[vi] = names[p.material_index]
    APRON = ('tarik_apron', 'tarik_tie', 'tarik_steel')
    for v in body.data.vertices:   # blouse sleeves follow the upper arm
        if mat_of.get(v.index) in APRON: continue
        k = -1 if v.co.x < 0 else 1
        a, bq = SHOULDER[k], ELBOW[k]; ab = bq - a
        tt = max(0.0, min(1.0, (v.co - a).dot(ab) / ab.length_squared)); dist = (v.co - (a + ab * tt)).length
        t = smoothstep(0.36, 0.48, abs(v.co.x)) * smoothstep(0.74, 0.84, v.co.z) * (1 - smoothstep(0.18, 0.24, dist))
        if t <= 0: continue
        bone = 'upperarm.l' if k < 0 else 'upperarm.r'
        for g in list(v.groups): body.vertex_groups[g.group].add([v.index], g.weight * (1 - t), 'REPLACE')
        body.vertex_groups[bone].add([v.index], t, 'ADD')
    for v in body.data.vertices:   # loose trim that the heat map skips: cuffs
        if v.groups or mat_of.get(v.index) in APRON: continue
        body.vertex_groups['lowerarm.l' if v.co.x < 0 else 'lowerarm.r'].add([v.index], 1.0, 'REPLACE')
    torso = ('hips', 'spine', 'chest')
    for v in body.data.vertices:   # apron, straps, bow and pen ride the torso only: never an arm, hand or prop bone
        if mat_of.get(v.index) not in APRON: continue
        keep = {body.vertex_groups[g.group].name: g.weight for g in v.groups if body.vertex_groups[g.group].name in torso}
        if not keep: keep = {('chest' if v.co.z > 0.95 else 'spine' if v.co.z > 0.80 else 'hips'): 1.0}
        for gi in [g.group for g in v.groups]: body.vertex_groups[gi].remove([v.index])
        s = sum(keep.values())
        for nm, w in keep.items(): body.vertex_groups[nm].add([v.index], w / s, 'REPLACE')
    A.rigid_weights(rig, gear, [('head', lambda co: True)])
    A.rigid_weights(rig, eyes, [('eye.l', lambda co: co.x < 0), ('eye.r', lambda co: True)])
    A.rigid_weights(rig, jug, [('handslot.r', lambda co: True)])
    A.rigid_weights(rig, mug, [('handslot.l', lambda co: True)])
    for name, bone in (('spout_jug', 'handslot.r'), ('spout_mug', 'handslot.l')):
        e = O[name]; pos = e.matrix_world.translation.copy()
        e.parent = rig; e.parent_type = 'BONE'; e.parent_bone = bone
        bpy.context.view_layer.update(); e.matrix_world = Matrix.Translation(pos)
    for ob in (body, head):
        loose = sum(1 for v in ob.data.vertices if not v.groups)
        print(f'[rig] {ob.name}: {loose} unweighted verts of {len(ob.data.vertices)}')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'tarik_rig.blend'))

def stage_expr(blend='tarik_rig.blend', tag='expr'):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, blend))
    hide_hi(); RL.setup_render(768, 768, 24); RL.studio_light((0, 0.2, 1.38)); RL.floor()
    head = bpy.data.objects['tarik_head']; kb = head.data.shape_keys.key_blocks
    rig = bpy.data.objects.get('tarik_rig')
    if rig: A.reset_pose(rig)
    for nm in ('idle', 'angry', 'grin', 'ult'):
        for k in kb: k.value = 0.0
        if nm != 'idle': kb[nm].value = 1.0
        RL.shoot(os.path.join(SHOTS, f'{tag}_{nm}.png'), (-1.0, 2.3, 1.7), (0, 0.15, 1.40), 85)
    for k in kb: k.value = 0.0

# =====================================================================================
# materials (painted, baked to per-mesh atlases)
# =====================================================================================
def mat_skin(m):
    b = MB(m)
    col = b.mix(0.0, c4('skin'), c4('skin_warm'))
    front = b.grad((0, 1, 0), 0.04, 0.12)   # ring, seg and the lip ellipse are flat in xz, so mask them to the face
    cool = b.math('MAXIMUM', b.grad((0, 0, 1), R(0, 0, 0.06).z, R(0, 0, 0.22).z), b.math('SUBTRACT', 1.0, b.grad((0, 1, 0), -0.05, 0.20)))
    col = b.mix(b.math('MULTIPLY', cool, 0.25), col, c4('skin_cool'))
    cheeks = b.math('MAXIMUM', b.blob(tuple(R(0.24, 0.24, -0.10)), 0.05, 0.20, fold_x=True), b.blob(tuple(R(0, 0.42, -0.10)), 0.02, 0.09))
    cheeks = b.math('MAXIMUM', cheeks, b.math('MULTIPLY', b.blob(tuple(R(0.42, -0.02, -0.08)), 0.03, 0.12, fold_x=True), 0.7))
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', cheeks, front), 0.45), col, c4('blush'))
    x, _, z = b.xyz(b.co())   # arm radial: the arm axis out at the arms, the body axis near the midline, so nothing flips sign at x=0
    cx = b.math('MULTIPLY', b.math('MULTIPLY', b.math('SIGN', x), 0.58), b.step(b.math('ABSOLUTE', x), 0.15, 0.40))
    limb = b.vmath('NORMALIZE', b.vmath('SUBTRACT', b.co(), b.combine(cx, 0.05, z)))
    N = b.vmix(b.grad((0, 0, 1), 0.96, 1.02), limb, b.radial(tuple(R(0, 0.05, -0.08))))   # the head radial owns the chin and neck
    N = b.vmix(b.grad((0, 0, 1), 0.22, 0.30), b.radial((0, 0.12, 0), mirror_x=0.185, follow_z=-0.08), N)
    col = b.paint_light(col, c4('skin_warm'), c4('skin_shade'), N=N, sh_amt=0.55, hi_amt=0.5)
    E = (abs(EYE_L.x), EYE_L.y, EYE_L.z); r = EYE_R_BALL
    upper = b.math('MULTIPLY', b.ring((E[0], 0, E[2]), r + 0.004, r + 0.014, fold_x=True), b.grad((0, 0, 1), E[2] - 0.01, E[2] + 0.015))
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', upper, front), 0.4), col, c4('lid'))
    lips = b.math('SUBTRACT', 1.0, b.step(b.vmath('DISTANCE', b.mapped(b.co(), (1 / 0.15, 0.25, 1 / 0.042)), (0, MOUTH_C.y * 0.25, MOUTH_C.z / 0.042)), 0.75, 1.05))
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', lips, front), 0.85), col, c4('lip'))
    mz = MOUTH_C.z + 0.002
    line = b.math('MAXIMUM', b.seg((0, 0.34, mz - 0.003), (0.10, 0.34, mz + 0.003), 0.0025, fold_x=True), b.seg((0.10, 0.34, mz + 0.003), (0.14, 0.33, mz + 0.022), 0.0025, fold_x=True))
    col = b.mix(b.math('MULTIPLY', b.math('MULTIPLY', line, front), 0.85), col, c4('mouth'))
    b.finish(col, 0.62)

def mat_hair(m):
    """Short dark perm: strand strokes, painted grey streaks, mauve light band, teal in the deep shadow. Half the light from each clump."""
    b = MB(m)
    st = b.strokes(along=(0.18, 1, 0.5), scale=14, levels=4)
    col = b.mix(b.math('MULTIPLY', st, 0.85), c4('hair'), c4('hair_mid'))
    strand = b.step(b.noise(b.mapped(b.co(), (0.18, 1, 0.5)), scale=30, detail=1.0, rough=.45), 0.55, 0.59)
    col = b.mix(b.math('MULTIPLY', strand, 0.5), col, c4('hair_dark'))
    grey = b.step(b.noise(b.mapped(b.co(), (0.10, 1, 0.35)), scale=11, detail=0.5, rough=.3), 0.66, 0.80)    # a few soft grey streaks (a hard contour read as a plastic highlight)
    grey = b.math('MULTIPLY', grey, b.grad((0, 0, 1), HEAD_C.z + 0.05, HEAD_C.z + 0.25))                        # mostly on top
    col = b.mix(b.math('MULTIPLY', grey, 0.22), col, c4('grey'))
    N = b.vmix(0.75, b.radial(tuple(HEAD_C + Vector((0, -0.04, 0.02)))), b.normal())   # mostly the designed normal, the facets of the shells stay out of the bands
    nd = b.vmath('DOT_PRODUCT', N, (-0.45, 0.55, 0.70)); nd = b.math('ADD', nd, b.math('MULTIPLY', b.math('SUBTRACT', st, 0.5), 0.16))
    col = b.mix(b.math('SUBTRACT', 1.0, b.step(nd, 0.22, 0.50)), col, c4('hair_dark'))
    col = b.mix(b.math('MULTIPLY', b.math('SUBTRACT', 1.0, b.step(nd, -0.25, -0.02)), 0.8), col, c4('hair_deep'))
    col = b.mix(b.math('MULTIPLY', b.step(nd, 0.72, 0.90), 0.25), col, c4('hair_light'))
    b.finish(col, 0.98)

def mat_eye(m):
    b = MB(m)
    v = b.vmath('ABSOLUTE', b.co()); d = b.vmath('NORMALIZE', b.vmath('SUBTRACT', v, (abs(EYE_L.x), EYE_L.y, EYE_L.z)))
    dot = b.vmath('DOT_PRODUCT', d, (0, 1, 0))
    iris = b.step(dot, 0.60, 0.64); pupil = b.step(dot, 0.87, 0.90)
    up = b.vmath('DOT_PRODUCT', d, (0, 0, 1))
    iris_col = b.mix(b.step(up, 0.3, -0.5), c4('iris'), c4('iris_light'))
    col = b.mix(b.step(up, 0.40, 0.60), c4('sclera'), c4('sclera_shade'))
    col = b.mix(iris, col, iris_col); col = b.mix(pupil, col, c4('pupil'))
    col = b.mix(b.math('MULTIPLY', b.step(up, 0.48, 0.62), 0.8), col, c4('lid'))
    hl = b.step(b.vmath('DOT_PRODUCT', d, (-0.25, 0.90, 0.36)), 0.955, 0.97)
    col = b.mix(hl, col, (1, 1, 1, 1))
    b.finish(col, 0.5)

def mat_cloth(m, base, warm, cool, shade, N, st_along=(1, 1, 0.15), sh_amt=0.55, hi_amt=0.35, rough=0.82, extra=None):
    b = MB(m)
    st = b.strokes(along=st_along, scale=12, levels=3)
    col = b.mix(b.math('MULTIPLY', st, 0.4), c4(base), c4(cool))
    if extra: col = extra(b, col, st)
    col = b.paint_light(col, c4(warm), c4(shade), N=N(b), strokes=st, sh_amt=sh_amt, hi_amt=hi_amt)
    b.finish(col, rough)

def N_torso(b):
    ax = b.math('ABSOLUTE', b.xyz(b.co())[0])
    return b.vmix(b.step(ax, 0.38, 0.46), b.radial((0, 0.03, 0), follow_z=-0.12), b.radial((0, 0.02, 0), mirror_x=0.50, follow_z=0.0))

def apron_extra(b, col, st):
    """Pocket outline, a tea stain, a darker hem band and the bib edge, all painted on the green."""
    x, y, z = b.xyz(b.co())
    pocket = b.math('MULTIPLY', b.math('SUBTRACT', 1.0, b.step(b.math('ABSOLUTE', x), 0.125, 0.135)), b.math('MULTIPLY', b.step(z, 0.43, 0.44), b.math('SUBTRACT', 1.0, b.step(z, 0.60, 0.61))))
    inner = b.math('MULTIPLY', b.math('SUBTRACT', 1.0, b.step(b.math('ABSOLUTE', x), 0.112, 0.120)), b.math('MULTIPLY', b.step(z, 0.445, 0.455), b.math('SUBTRACT', 1.0, b.step(z, 0.60, 0.61))))
    edge = b.math('SUBTRACT', pocket, inner)
    col = b.mix(b.math('MULTIPLY', edge, 0.8), col, c4('apron_deep'))
    stain = b.blob((-0.11, 0.42, 0.66), 0.03, 0.07)
    col = b.mix(b.math('MULTIPLY', stain, 0.55), col, c4('stain'))
    hem = b.math('SUBTRACT', 1.0, b.step(z, 0.33, 0.345))
    col = b.mix(b.math('MULTIPLY', hem, 0.7), col, c4('apron_deep'))
    band = b.math('MULTIPLY', b.step(z, 0.70, 0.71), b.math('SUBTRACT', 1.0, b.step(z, 0.745, 0.755)))   # pink waistband
    col = b.mix(b.math('MULTIPLY', band, 0.9), col, c4('tie'))
    return col

def mat_towel(m):
    def extra(b, col, st):
        x, y, z = b.xyz(b.co())
        stripe = b.math('MAXIMUM', b.math('MULTIPLY', b.step(z, 0.92, 0.93), b.math('SUBTRACT', 1.0, b.step(z, 0.97, 0.98))),
                         b.math('MULTIPLY', b.step(z, 1.02, 1.03), b.math('SUBTRACT', 1.0, b.step(z, 1.045, 1.055))))
        return b.mix(b.math('MULTIPLY', stripe, 0.9), col, c4('towel_stripe'))
    mat_cloth(m, 'towel', 'towel', 'towel_shade', 'towel_shade', lambda b: b.radial((-0.41, 0.0, 1.0)), st_along=(0.2, 1, 1), sh_amt=0.5, hi_amt=0.2, rough=0.9, extra=extra)

def mat_steel(m, light='steel_light'):
    """Painted brushed steel: a crisp light band, deep cool shadow, metallic."""
    b = MB(m)
    br = b.noise(b.mapped(b.co(), (2, 2, 60)), scale=4, detail=2)
    col = b.mix(b.math('MULTIPLY', br, 0.3), c4('steel'), c4('steel_dark'))
    nd = b.vmath('DOT_PRODUCT', b.normal(), (-0.45, 0.55, 0.70))
    col = b.mix(b.math('SUBTRACT', 1.0, b.step(nd, 0.0, 0.25)), col, c4('steel_dark'))
    col = b.mix(b.step(nd, 0.55, 0.75), col, c4(light))
    b.finish(col, b.math('ADD', 0.32, b.math('MULTIPLY', br, 0.2)), 1.0)

def mat_tea(m):
    b = MB(m)
    n = b.noise(scale=25, detail=2)
    col = b.mix(b.math('MULTIPLY', n, 0.35), c4('tea'), c4('tea_dark'))
    b.finish(col, 0.25)

def build_materials():
    M = bpy.data.materials
    mat_skin(M['tarik_skin']); mat_hair(M['tarik_hair']); mat_eye(M['tarik_eye'])
    A.mat_simple(M['tarik_brow'], c4('brow'), 0.7, noise_scale=12, noise_amt=0.12, dark=(0.05, 0.03, 0.04, 1))
    mat_cloth(M['tarik_blouse'], 'blouse', 'blouse_warm', 'blouse_cool', 'blouse_shade', N_torso, hi_amt=0.2)
    mat_cloth(M['tarik_sleeve'], 'sleeve', 'sleeve_light', 'sleeve', 'sleeve_shade', lambda b: b.radial((0, 0.12, 0), mirror_x=0.59, follow_z=0.0), st_along=(0.2, 0.2, 1), sh_amt=0.6, hi_amt=0.45, rough=0.75)
    A.mat_simple(M['tarik_sleeve_cuff'], c4('sleeve_shade'), 0.8, noise_amt=0.1)
    mat_cloth(M['tarik_apron'], 'apron', 'apron_light', 'apron', 'apron_shade', N_torso, st_along=(1, 1, 0.12), sh_amt=0.6, hi_amt=0.4, extra=apron_extra)
    A.mat_simple(M['tarik_tie'], c4('tie'), 0.7, noise_amt=0.15, dark=c4('sleeve_shade'))
    mat_cloth(M['tarik_slacks'], 'slacks', 'slacks_light', 'slacks', 'slacks_shade', lambda b: b.radial((0, 0.0, 0), mirror_x=0.185, follow_z=-0.1), st_along=(1, 1, 0.12), sh_amt=0.6, hi_amt=0.5, rough=0.85)
    mat_towel(M['tarik_towel'])
    A.mat_simple(M['tarik_knot'], c4('knot'), 0.6, noise_amt=0.15, dark=(0.3, 0.22, 0.12, 1))
    A.mat_simple(M['tarik_slipper'], c4('slipper'), 0.45, noise_scale=8, dark=c4('slipper_dark'), noise_amt=0.4)
    A.mat_simple(M['tarik_gold'], c4('gold'), 0.3, 0.8, noise_amt=0.2, dark=(0.4, 0.25, 0.08, 1))
    A.mat_simple(M['tarik_mouth'], c4('mouth'), 0.7, noise_scale=8, noise_amt=0.15, dark=(0.08, 0.03, 0.05, 1))
    A.mat_simple(M['tarik_teeth'], c4('teeth'), 0.5, noise_scale=8, noise_amt=0.1, dark=(0.6, 0.55, 0.5, 1))
    mat_steel(M['tarik_steel']); mat_steel(M['tarik_steel_dark'], light='steel')
    mat_tea(M['tarik_tea']); A.mat_simple(M['tarik_foam'], c4('foam'), 0.7, noise_scale=40, noise_amt=0.2, dark=(0.75, 0.62, 0.45, 1))

ATLAS = {'tarik_head': 2048, 'tarik_body': 2048, 'tarik_headgear': 1024, 'tarik_jug': 1024, 'tarik_mug': 1024, 'tarik_eyes': 256}

def stage_bake():
    import numpy as np
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'tarik_rig.blend'))
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
        col = A.new_image(name + '_col', size); rough = A.new_image(name + '_rough', size, True)
        met = A.new_image(name + '_met', size, True); nrm = A.new_image(name + '_nrm', size, True)
        mets = [(s.material.node_tree.nodes['Principled BSDF'].inputs['Metallic'], s.material.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value) for s in ob.material_slots]
        for inp, _ in mets: inp.default_value = 0.0   # a DIFFUSE colour bake of a metallic surface is black, so bake the paint with metallic off
        A.bake(ob, col, 'DIFFUSE', 1, pass_filter={'COLOR'})
        for inp, v in mets: inp.default_value = v
        A.bake(ob, rough, 'ROUGHNESS', 1)
        A.bake(ob, nrm, 'NORMAL', 1)
        for slot in ob.material_slots:
            p = slot.material.node_tree.nodes['Principled BSDF']; v = p.inputs['Metallic'].default_value
            p.inputs['Emission Color'].default_value = (v, v, v, 1); p.inputs['Emission Strength'].default_value = 1.0
        A.bake(ob, met, 'EMIT', 1)
        for slot in ob.material_slots: slot.material.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.0
        c = A.px(col); r = A.px(rough)[..., 0:1]; mt = A.px(met)[..., 0:1]; a = np.ones_like(r)   # AO flat white, the paint carries the shading
        base = A.new_image(name + '_baseColor', size); orm = A.new_image(name + '_orm', size, True)
        cb = c.copy(); cb[..., 3] = 1; A.set_px(base, cb)
        A.set_px(orm, np.concatenate([a, r, mt, np.ones_like(a)], axis=-1))
        if size >= 2048:
            for im in (orm, nrm): im.scale(size // 2, size // 2)
        base.filepath_raw = os.path.join(tex_dir, base.name + '.jpg'); base.file_format = 'JPEG'; base.save(quality=88)
        for im in (orm, nrm): A.save_png(im, os.path.join(tex_dir, im.name + '.png'))
        for im in (col, rough, met): bpy.data.images.remove(im)
        A.export_material(ob, base, orm, nrm)
        print(f'[bake] {name}: {size}px baseColor/orm/normal')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'tarik_bake.blend'))

# =====================================================================================
# animation
# =====================================================================================
FPS = 30
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
axis_rot = A.axis_rot; set_world_rot = A.set_world_rot; reset_pose = A.reset_pose; hips_lift = A.hips_lift; rest_mat = A.rest_mat
ANIM_BONES = ['hips', 'spine', 'chest', 'neck', 'head', 'upperarm.l', 'lowerarm.l', 'hand.l', 'upperarm.r', 'lowerarm.r', 'hand.r',
              'upperleg.l', 'lowerleg.l', 'foot.l', 'upperleg.r', 'lowerleg.r', 'foot.r']

def pose_arm(rig, k, fwd=0, out=0, elbow=0, hand_tilt=0, hand_roll=0):
    """fwd: swing the upper arm forward (deg), out: lift it sideways, elbow: bend the forearm forward, hand_tilt: tip the hand
    (and the held jug or mug) forward. Child rotations ride on the parent, so the elbow and hand axes are arm-relative."""
    sd = 'l' if k < 0 else 'r'; B = rig.pose.bones
    set_world_rot(rig, B['upperarm.' + sd], axis_rot(Y, -k * out) @ axis_rot(X, fwd))
    set_world_rot(rig, B['lowerarm.' + sd], axis_rot(X, elbow))
    set_world_rot(rig, B['hand.' + sd], axis_rot(Y, -k * hand_roll) @ axis_rot(X, hand_tilt))

def pose_frame(rig, t, kind):
    reset_pose(rig); B = rig.pose.bones
    s = math.sin(2 * math.pi * t); c = math.cos(2 * math.pi * t)
    if kind == 'idle':   # a slow breathing sway, the jug arm does a small lift and tip, the mug arm steady
        set_world_rot(rig, B['chest'], axis_rot(X, 2.0 * s)); set_world_rot(rig, B['head'], axis_rot(X, -1.5 * s) @ axis_rot(Z, 2.5 * c))
        hips_lift(rig, 0.006 * s)
        pose_arm(rig, 1, fwd=18 + 6 * s, out=14, elbow=30 + 10 * s, hand_tilt=8 + 10 * s)
        pose_arm(rig, -1, fwd=14 - 3 * s, out=12, elbow=36, hand_tilt=4)
    elif kind == 'run':   # stubby-legged shuffle run, tea held up out of harm's way
        for k, sg in ((-1, 1), (1, -1)):
            sd = 'l' if k < 0 else 'r'
            set_world_rot(rig, B['upperleg.' + sd], axis_rot(X, 34 * s * sg))
            set_world_rot(rig, B['lowerleg.' + sd], axis_rot(X, -48 * max(0.0, -s * sg)))
            set_world_rot(rig, B['foot.' + sd], axis_rot(X, 15 * max(0.0, -s * sg)))
        set_world_rot(rig, B['chest'], axis_rot(X, 10) @ axis_rot(Z, 4 * s)); set_world_rot(rig, B['head'], axis_rot(X, -7) @ axis_rot(Z, -3 * s))
        set_world_rot(rig, B['spine'], axis_rot(X, 4))
        hips_lift(rig, 0.03 * abs(s) - 0.015)
        pose_arm(rig, 1, fwd=40 + 6 * s, out=16, elbow=70, hand_tilt=-10 + 4 * s)
        pose_arm(rig, -1, fwd=30 - 6 * s, out=14, elbow=60, hand_tilt=-6)
    elif kind == 'attack':   # Tea Stream: the jug goes up high and tips forward, the mug comes up to catch
        if t < 0.35: u = smoothstep(0, 1, t / 0.35)
        elif t < 0.65: u = 1.0
        else: u = 1 - smoothstep(0, 1, (t - 0.65) / 0.35)
        pose_arm(rig, 1, fwd=18 + 62 * u, out=14 + 16 * u, elbow=30 + 50 * u, hand_tilt=8 + 55 * u, hand_roll=-20 * u)
        pose_arm(rig, -1, fwd=14 + 30 * u, out=12 + 6 * u, elbow=36 + 24 * u, hand_tilt=4 - 12 * u)
        set_world_rot(rig, B['chest'], axis_rot(X, -6 * u)); set_world_rot(rig, B['spine'], axis_rot(X, -3 * u))
        set_world_rot(rig, B['head'], axis_rot(X, -6 * u) @ axis_rot(Z, 6 * u))
        hips_lift(rig, -0.02 * u)
    elif kind == 'ult':   # Teh Tarik Rain: jug straight overhead, mug held high, head back, big laugh
        pose_arm(rig, 1, fwd=150, out=25, elbow=20, hand_tilt=70)
        pose_arm(rig, -1, fwd=95, out=35, elbow=40, hand_tilt=-20)
        set_world_rot(rig, B['chest'], axis_rot(X, -8)); set_world_rot(rig, B['spine'], axis_rot(X, -4)); set_world_rot(rig, B['head'], axis_rot(X, -10))

def make_action(rig, name, kind, frames, loop=True):
    act = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act
    for f in range(frames + 1):
        t = (f % frames) / frames if loop else min(f, frames) / frames
        bpy.context.scene.frame_set(f); pose_frame(rig, t, kind); A.key_all(rig, f, ANIM_BONES)
    act.frame_range = (0, frames); act.use_frame_range = True; act.use_fake_user = True; return act

def stage_anim():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'tarik_bake.blend'))
    bpy.context.scene.render.fps = FPS
    rig = bpy.data.objects['tarik_rig']
    acts = [make_action(rig, 'idle', 'idle', 60), make_action(rig, 'run', 'run', 24), make_action(rig, 'attack', 'attack', 18, loop=False), make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'tarik_anim.blend'))
    print('[anim] actions', [a.name for a in acts])

# =====================================================================================
# export + verify
# =====================================================================================
def stage_export():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'tarik_anim.blend'))
    rig = bpy.data.objects['tarik_rig']; reset_pose(rig)
    for k in bpy.data.objects['tarik_head'].data.shape_keys.key_blocks: k.value = 0.0
    objs = [bpy.data.objects[n] for n in ATLAS] + [rig, bpy.data.objects['spout_jug'], bpy.data.objects['spout_mug']]
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
    bpy.context.view_layer.update()
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
    for o in bpy.data.objects:
        if o.type == 'EMPTY' and o.name != 'Icosphere':
            p = o.matrix_world.translation; print(f'[verify] empty {o.name} at Blender {tuple(round(x, 3) for x in p)} parent {o.parent_bone or o.parent}')
    for o in meshes:
        if o.data.shape_keys: print('[verify] morphs on', o.name, [k.name for k in o.data.shape_keys.key_blocks][1:])
        print(f'[verify] {o.name}: {tri_count(o)} tris, mats {[m.name for m in o.data.materials]}')
    print('[verify] animations', [(a.name, a.frame_range[:]) for a in bpy.data.actions], 'images', [(i.name, i.size[0]) for i in bpy.data.images])

# =====================================================================================
# final shots
# =====================================================================================
def play(rig, name, frame):
    rig.animation_data.action = bpy.data.actions[name]; bpy.context.scene.frame_set(frame)

def stage_shots():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'tarik_anim.blend'))
    hide_hi(); RL.setup_render(768, 1024, 32); RL.studio_light((0, 0, 0.95)); RL.floor()
    rig = bpy.data.objects['tarik_rig']; tmp = os.path.join(WORK, 'shots'); os.makedirs(tmp, exist_ok=True)
    for k in bpy.data.objects['tarik_head'].data.shape_keys.key_blocks: k.value = 0.0
    play(rig, 'idle', 0); paths = []
    for i, ang in enumerate((0, 45, 90, 180)):
        a = math.radians(ang); p = os.path.join(tmp, f'turn_{i}.png'); paths.append(p)
        RL.shoot(p, (-5.6 * math.sin(a), 5.6 * math.cos(a), 1.4), (0, 0, 0.92), 60)
    A.stitch(paths, os.path.join(SHOTS, 'turnaround.png'), 4)
    RL.setup_render(512, 640, 24); paths = []
    for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
        for i in range(4):
            play(rig, name, int(i * n / 4) if name != 'attack' else (0, 6, 9, 17)[i]); p = os.path.join(tmp, f'{name}_{i}.png'); paths.append(p)
            RL.shoot(p, (-3.6, 4.3, 1.7), (0, 0.2, 0.95), 60)
    A.stitch(paths, os.path.join(SHOTS, 'anim_sheet.png'), 4)
    play(rig, 'idle', 0)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'ref', 'heroes', 'tarik.glb'))
    old = [o for o in bpy.context.selected_objects if o.parent is None]
    for o in old: o.location.x += 1.5; o.rotation_euler.z += math.pi
    for o in bpy.data.objects:
        if o.name == 'Icosphere': o.hide_render = True
    rig.location.x = -1.5
    play(rig, 'idle', 0)
    RL.setup_render(1400, 900, 32)
    RL.shoot(os.path.join(SHOTS, 'side_by_side_old_vs_new.png'), (0, 8.0, 1.4), (0, 0, 0.98), 50)
    print('[shots] turnaround, anim_sheet, side_by_side written')

def stage_expr_final():
    stage_expr('tarik_anim.blend', 'expr')
    A.stitch([os.path.join(SHOTS, f'expr_{n}.png') for n in ('idle', 'angry', 'grin', 'ult')], os.path.join(SHOTS, 'expressions.png'), 4)

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build', 'look']
    for a in args:
        {'build': stage_build, 'look': stage_look, 'rig': stage_rig, 'expr': stage_expr, 'bake': stage_bake, 'anim': stage_anim, 'export': stage_export,
         'verify': stage_verify, 'shots': stage_shots, 'exprfinal': stage_expr_final,
         'looktex': lambda: stage_look('tex', 'tarik_bake.blend'), 'exprtex': lambda: stage_expr('tarik_bake.blend', 'exprtex')}[a]()
