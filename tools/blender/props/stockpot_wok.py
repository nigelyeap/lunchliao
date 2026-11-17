import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
reset()
# Stove station: steel stand, gas ring, bubbling stockpot (left) and wok (right). Origin: floor centre. Top of stove 0.7 m.
steel = tex('steel_brushed'); dk = flat('iron_dark', 0x2b2a2a, 0.55, 0.7); broth = flat('broth', 0xc99a4a, 0.25); bub = flat('broth_bubble', 0xe8c880, 0.2)
blue = flat('flame', 0x4aa8ff, 0.5, 0.0, emit=(0x4aa8ff, 3.0)); rub = flat('rubber_black', 0x22201e, 0.8); oil = flat('wok_oil', 0x5a3a1a, 0.15)
box('stand', 1.3, 0.65, 0.6, steel, (0, 0, 0.35), bv=0.015, seg=2); box('top', 1.34, 0.69, 0.05, steel, (0, 0, 0.675), bv=0.012, seg=2)
box('splash', 1.34, 0.04, 0.3, steel, (0, 0.33, 0.85), bv=0.01)
for sx in (-1, 1):
    for sy in (-1, 1): cyl('foot', 0.03, 0.05, rub, (sx * 0.6, sy * 0.28, 0.025), n=8, bv=0.004)
for i in range(2): box(f'door{i}', 0.58, 0.014, 0.5, steel, (-0.31 + 0.62 * i, -0.33, 0.35), bv=0.006)
for i, x in enumerate((-0.33, 0.33)):
    lathe(f'ring{i}', [(0.1, 0.7), (0.2, 0.7), (0.2, 0.72), (0.1, 0.72)], dk, (x, 0, 0), n=20)
    for k in range(3): box(f'grate{i}{k}', 0.34, 0.025, 0.03, dk, (x, 0, 0.745), (0, 0, 60 * k), bv=0.005)
    cyl(f'knob{i}', 0.03, 0.04, dk, (x, -0.35, 0.55), (90, 0, 0), n=10, bv=0.005)
# stockpot
x = -0.33
lathe('pot', [(0.0, 0.76), (0.2, 0.76), (0.23, 0.78), (0.23, 1.08), (0.25, 1.1), (0.25, 1.12), (0.22, 1.12), (0.215, 1.1), (0.215, 0.98), (0.0, 0.98)], steel, (x, 0, 0), n=24)
lathe('pot_fill', [(0, 1.02), (0.212, 1.02), (0.212, 1.04), (0, 1.04)], broth, (x, 0, 0), n=24)
for k in range(7):
    a = k * 0.9; r = 0.04 + 0.025 * k % 0.14
    sphere(f'bub{k}', 0.032, 0.032, 0.018, bub, (x + 0.1 * math.cos(a) * (k % 3 + 1) * 0.6, 0.1 * math.sin(a) * (k % 3 + 1) * 0.6, 1.045), n=8)
for s in (-1, 1): box('pot_handle', 0.08, 0.03, 0.03, dk, (x + s * 0.28, 0, 1.08), bv=0.008)
cyl('lid', 0.2, 0.02, steel, (x + 0.18, 0.28, 0.69), n=18, bv=0.006)
# wok (hemisphere shell) + ladle
x = 0.33
pr = [(0.29 * math.sin(math.radians(t)) , 0.98 - 0.29 * math.cos(math.radians(t)) + 0.0) for t in range(75, -1, -15)]
outer = [(0.29 * math.sin(math.radians(t)), 0.95 - 0.19 * math.cos(math.radians(t))) for t in range(0, 76, 15)]
inner = [(r - 0.012, z + 0.012) for r, z in outer][::-1]
lathe('wok', outer + [(outer[-1][0] + 0.012, outer[-1][1] + 0.012)] + inner[:-1] + [(0, outer[0][1] + 0.012)], dk, (x, 0, 0), n=24)
lathe('wok_oil', [(0, 0.972), (0.19, 0.972), (0.19, 0.976), (0, 0.976)], oil, (x, 0, 0), n=16)
limb('wok_handle', (x + 0.28, -0.02, 1.08), (x + 0.28, -0.44, 1.12), 0.018, 0.016, dk)
limb('wok_ear', (x - 0.28, 0, 1.04), (x - 0.34, 0, 1.12), 0.015, 0.015, dk)
limb('ladle_stick', (x - 0.05, -0.05, 1.1), (x - 0.22, 0.04, 1.4), 0.012, 0.012, steel)
sphere('ladle_bowl', 0.05, 0.05, 0.03, steel, (x - 0.04, -0.06, 1.07), n=10)
for i, xx in enumerate((-0.33, 0.33)):
    for k in range(6):
        a = k * math.tau / 6; sphere(f'f{i}{k}', 0.018, 0.018, 0.026, blue, (xx + 0.13 * math.cos(a), 0.13 * math.sin(a), 0.725), n=6)
# anchors for steam particles
for n_, p in (('STEAM_pot', (-0.33, 0, 1.15)), ('STEAM_wok', (0.33, 0, 1.0))):
    e = bpy.data.objects.new(n_, None); bpy.context.collection.objects.link(e); e.location = p
finalize('stockpot_wok')
