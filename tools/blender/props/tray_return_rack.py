import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
reset()
# Tray-return rack on casters. Origin: floor centre. Front faces -Y (glTF +Z).
steel = tex('steel_brushed'); pb = tex('plastic_blue'); pr = tex('plastic_red'); dk = flat('rubber_black', 0x22201e, 0.8); wh = flat('paint_white', 0xf1ede0, 0.55); grn = flat('paint_green', 0x2e7a55, 0.5)
for sx in (-1, 1):
    for sy in (-1, 1): cyl('post', 0.016, 1.72, steel, (sx * 0.42, sy * 0.27, 0.9), n=10, bv=0); cyl('wheel', 0.04, 0.03, dk, (sx * 0.42, sy * 0.27, 0.04), (0, 90, 0), n=12, bv=0.004)
for z in (0.3, 0.7, 1.1):
    box('shelf', 0.88, 0.58, 0.02, steel, (0, 0, z), bv=0.006)
    box('lip_f', 0.88, 0.016, 0.05, steel, (0, -0.28, z + 0.03), bv=0.005); box('lip_b', 0.88, 0.016, 0.05, steel, (0, 0.28, z + 0.03), bv=0.005)
    for i in range(6): box('slot', 0.025, 0.4, 0.004, dk, (-0.35 + i * 0.14, 0, z + 0.011), bv=0)
for i, m in enumerate((pr, pb, pr)): box(f'tray{i}', 0.46, 0.34, 0.025, m, (-0.1 + 0.05 * (i % 2), 0.02, 0.325 + i * 0.027), (0, 0, 4 * i), bv=0.008)
box('tray_lean', 0.46, 0.34, 0.025, pb, (0.22, 0.1, 0.84), (0, 78, 12), bv=0.008)
box('header', 0.92, 0.04, 0.5, grn, (0, -0.27, 1.62), bv=0.01); box('header_in', 0.84, 0.01, 0.42, wh, (0, -0.296, 1.62), bv=0.004)
quad('SIGN_tray', 0.8, 0.38, (0, -0.304, 1.62), flat('SIGN_tray', 0xf4ead0, 0.8))
box('handle', 0.7, 0.03, 0.03, steel, (0, 0.3, 1.45), bv=0.008)
finalize('tray_return_rack')
