import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
reset()
# Ceiling fan. Origin: ceiling attach point, fan hangs down (-Z in Blender, -Y in glTF). FAN_rotor pivot = hub centre, spin about local Y (glTF).
steel = tex('steel_brushed'); ply = tex('plywood'); cream = flat('paint_cream', 0xe4d8b6, 0.55); dk = flat('rubber_black', 0x22201e, 0.8)
cyl('canopy', 0.07, 0.05, cream, (0, 0, -0.025), r2=0.04, n=14, bv=0.006)
cyl('rod', 0.016, 0.4, steel, (0, 0, -0.25), n=10, bv=0)
cyl('rod_ball', 0.03, 0.04, steel, (0, 0, -0.07), n=12, bv=0.006)
lathe('motor', [(0, -0.43), (0.08, -0.43), (0.125, -0.46), (0.135, -0.5), (0.125, -0.54), (0.08, -0.56), (0, -0.56)], cream, n=24)
P = -0.585
lathe('hub', [(0, P + 0.03), (0.1, P + 0.03), (0.115, P + 0.015), (0.115, P - 0.015), (0.1, P - 0.03), (0.0, P - 0.03)], steel, n=24, group='FAN_rotor')
cyl('hub_cap', 0.04, 0.03, dk, (0, 0, P - 0.045), n=12, bv=0.004, group='FAN_rotor')
for k in range(3):
    a = 120 * k; c = math.radians(a)
    for part, (L, W, T, r0, mat) in (('blade', (0.62, 0.17, 0.014, 0.15, ply)), ('arm', (0.1, 0.05, 0.012, 0.12, steel)),):
        o = box(f'{part}{k}', L, W, T, mat, (0, 0, 0), bv=0.005, seg=1, group='FAN_rotor')
        # pitch the blade about its long axis, then swing out
        o.rotation_mode = 'XYZ'; o.rotation_euler = (math.radians(13 if part == 'blade' else 0), 0, 0)
        o.matrix_world  # noqa
        m = Matrix.Rotation(c, 4, 'Z') @ Matrix.Translation((r0 + L / 2 + (0.06 if part == 'blade' else 0), 0, P)) @ o.rotation_euler.to_matrix().to_4x4()
        o.rotation_euler = m.to_euler(); o.location = m.translation
finalize('ceiling_fan', pivots={'FAN_rotor': (0, 0, P)})
