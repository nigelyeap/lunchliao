
# =====================================================================================
# animation: hunched, low, animal body language
# =====================================================================================
FPS = 30
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
    drop = (0.25 + 0.20) * (1 - math.cos(math.radians(bend * 0.5)))
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
