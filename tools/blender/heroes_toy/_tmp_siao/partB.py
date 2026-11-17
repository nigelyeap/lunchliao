
# ---------------------------------------------------------------- rig
LEG = {}
for _k in (-1, 1): LEG[_k] = (V((_k * .20, BY, .52)), V((_k * .20, BY, KNEE_Z)), V((_k * .20, BY, ANK_Z)))
BONES = [
    ('root', (0, 0, 0), (0, 0, 0.25), None),
    ('hips', (0, BY, .50), (0, BY, .64), 'root'),
    ('spine', (0, BY, .64), (0, BY, .76), 'hips'),
    ('chest', (0, BY, .76), (0, BY, .86), 'spine'),
    ('neck', (0, BY, .86), (0, BY, 1.03), 'chest'),
    ('head', (0, BY, 1.03), (0, BY, 1.95), 'neck'),
    ('eye.l', tuple(surf(-EXe, EZe)[0]), tuple(surf(-EXe, EZe)[0] + V((0, .06, 0))), 'head'),
    ('eye.r', tuple(surf(EXe, EZe)[0]), tuple(surf(EXe, EZe)[0] + V((0, .06, 0))), 'head'),
]
for k, side in ((-1, 'l'), (1, 'r')):
    sh, el, wr = ARM[k]; hp, kn, an = LEG[k]
    BONES += [
        ('upperarm.' + side, tuple(sh), tuple(el), 'chest'),
        ('lowerarm.' + side, tuple(el), tuple(wr), 'upperarm.' + side),
        ('hand.' + side, tuple(wr), tuple(wr + V((0, .10, -.02))), 'lowerarm.' + side),
        ('handslot.' + side, tuple(wr + V((0, .06, 0))), tuple(wr + V((0, .14, 0))), 'hand.' + side),
        ('upperleg.' + side, tuple(hp), tuple(kn), 'hips'),
        ('lowerleg.' + side, tuple(kn), tuple(an), 'upperleg.' + side),
        ('foot.' + side, tuple(an), (k * .20, BY + .20, .05), 'lowerleg.' + side),
        ('toes.' + side, (k * .20, BY + .20, .05), (k * .20, BY + .31, .04), 'foot.' + side),
    ]
BONES.append(('prop', (0, 0, 0), (0, 0, 0.3), 'root'))
RIGID = {'eye.l', 'eye.r', 'prop', 'handslot.l', 'handslot.r'}

def make_armature():
    arm = bpy.data.armatures.new('siao_rig'); ob = bpy.data.objects.new('siao_rig', arm)
    SC.collection.objects.link(ob); H.select_only([ob], ob)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, h, t, parent in BONES:
        b = arm.edit_bones.new(name); b.head = Vector(h) * KSC; b.tail = Vector(t) * KSC
        if parent: b.parent = arm.edit_bones[parent]; b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in arm.bones: b.use_deform = b.name not in RIGID
    return ob

def rest_mat(rig, name): return rig.data.bones[name].matrix_local
def world_quat_to_local(rig, pb, q):
    M = rest_mat(rig, pb.name).to_3x3(); return (M.inverted() @ q.to_matrix() @ M).to_quaternion()
def set_world_rot(rig, pb, q):
    pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = world_quat_to_local(rig, pb, q)
def axis_rot(axis, deg): return Quaternion(Vector(axis), math.radians(deg))
def reset_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)

