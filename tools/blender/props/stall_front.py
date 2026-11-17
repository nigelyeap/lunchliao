import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
reset()
steel = tex('steel_brushed'); wall = tex('wall_tile')
dark = flat('rubber_black', 0x22201e, 0.8); maroon = flat('paint_maroon', 0x7a2a22, 0.55); gold = flat('paint_gold', 0xd9a530, 0.4, 0.3)
shut = flat('paint_shutter', 0x6f8187, 0.5, 0.2); glass = flat('glass', 0xcfe8e8, 0.05, 0.0, alpha=0.18)
cream = flat('paint_cream', 0xefe2bf, 0.6); red = flat('food_charsiu', 0xa8291c, 0.45); brown = flat('food_roast', 0x8a4a1c, 0.4); chick = flat('food_chicken', 0xe3c68e, 0.45)
sg = lambda n, c: flat(n, c, 0.7)
# counter (x -1.6..0.7), front y=-0.5
box('counter_body', 2.3, 0.7, 0.8, steel, (-0.45, -0.15, 0.5), bv=0.012)
box('counter_top', 2.38, 0.78, 0.05, steel, (-0.45, -0.15, 0.925), bv=0.014, seg=2)
box('kick', 2.2, 0.6, 0.1, dark, (-0.45, -0.15, 0.05), bv=0.01)
for i in range(4):
    x = -1.35 + i * 0.58
    box(f'panel{i}', 0.52, 0.016, 0.56, steel, (x, -0.505, 0.5), bv=0.008)
    cyl(f'handle{i}', 0.01, 0.16, steel, (x, -0.525, 0.7), (0, 90, 0), n=8, bv=0)
# back wall + side pillars + right unit
box('back_wall', 3.32, 0.1, 2.2, wall, (-0.06, 0.3, 1.1), bv=0.01)
box('pillar_L', 0.12, 0.9, 2.2, wall, (-1.66, -0.05, 1.1), bv=0.01)
box('side_unit', 0.9, 0.9, 2.2, wall, (1.15, -0.05, 1.1), bv=0.012)
box('side_foot', 0.94, 0.94, 0.1, dark, (1.15, -0.05, 0.05), bv=0.01)
for i in range(3):
    x = 0.89 + i * 0.26
    box(f'menu_frame{i}', 0.25, 0.02, 0.7, dark, (x, -0.51, 1.45), bv=0.006)
    quad(f'SIGN_menu_{i+1}', 0.22, 0.66, (x, -0.523, 1.45), flat(f'SIGN_menu_{i+1}', 0xf4ead0, 0.8))
box('grade_frame', 0.26, 0.02, 0.34, dark, (1.15, -0.51, 0.75), bv=0.006)
quad('SIGN_grade', 0.22, 0.30, (1.15, -0.523, 0.75), flat('SIGN_grade', 0xffffff, 0.5))
# glass display case on counter
box('case_base', 1.3, 0.42, 0.04, steel, (-0.8, -0.2, 0.97), bv=0.008)
box('case_top', 1.3, 0.42, 0.03, steel, (-0.8, -0.2, 1.575), bv=0.008)
for sx in (-1, 1):
    for sy in (-1, 1): box('case_post', 0.03, 0.03, 0.6, steel, (-0.8 + sx * 0.635, -0.2 + sy * 0.195, 1.27), bv=0.006)
box('case_shelf', 1.24, 0.38, 0.015, steel, (-0.8, -0.2, 1.27), bv=0.005)
box('case_glass', 1.26, 0.40, 0.55, glass, (-0.8, -0.2, 1.27), bv=0.01)
for i in range(3):
    box(f'tray{i}', 0.34, 0.26, 0.03, steel, (-1.2 + i * 0.4, -0.2, 1.005), bv=0.006)
    sphere(f'food_a{i}', 0.14, 0.09, 0.05, [red, chick, brown][i], (-1.2 + i * 0.4, -0.2, 1.045))
    sphere(f'food_b{i}', 0.07, 0.05, 0.1, brown if i != 1 else red, (-1.2 + i * 0.4, -0.2, 1.37), n=8)
    sphere(f'food_c{i}', 0.07, 0.05, 0.1, brown, (-1.12 + i * 0.4, -0.2, 1.37), n=8)
# roller shutter box + guide rails
box('shutter_box', 2.3, 0.28, 0.26, shut, (-0.45, -0.36, 2.05), bv=0.02, seg=2)
for i in range(7): box(f'rib{i}', 0.02, 0.01, 0.2, dark, (-1.5 + i * 0.35, -0.505, 2.05), bv=0.003)
for x in (-1.58, 0.68): box('rail', 0.04, 0.08, 1.0, steel, (x, -0.42, 1.42), bv=0.006)
# sign frame
box('sign_back', 3.32, 0.04, 0.7, cream, (-0.06, -0.44, 2.57), bv=0.006)
for z in (2.25, 2.89): box('sign_rail', 3.4, 0.12, 0.08, maroon, (-0.06, -0.46, z), bv=0.015, seg=2)
for x in (-1.72, 1.6): box('sign_stile', 0.08, 0.12, 0.72, maroon, (x, -0.46, 2.57), bv=0.015, seg=2)
box('sign_trim_a', 3.2, 0.014, 0.02, gold, (-0.06, -0.52, 2.31), bv=0.004); box('sign_trim_b', 3.2, 0.014, 0.02, gold, (-0.06, -0.52, 2.83), bv=0.004)
quad('SIGN_main', 3.1, 0.48, (-0.06, -0.465, 2.57), flat('SIGN_main', 0xf4ead0, 0.8))
finalize('stall_front')
