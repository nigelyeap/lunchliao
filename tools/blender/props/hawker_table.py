import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
reset()
# Round hawker table with fixed pole base + 4 bolted round stools. Origin: floor centre.
steel = tex('steel_brushed'); fm = tex('formica'); red = tex('plastic_red'); dark = flat('rubber_black', 0x22201e, 0.8)
cyl('top', 0.5, 0.035, fm, (0, 0, 0.7325), n=32, bv=0.012, seg=2)
lathe('rim', [(0.49, 0.7), (0.515, 0.7), (0.52, 0.708), (0.52, 0.745), (0.515, 0.752), (0.49, 0.752)], steel, n=40)
cyl('under', 0.13, 0.04, steel, (0, 0, 0.68), n=16, bv=0.008)
cyl('pole', 0.04, 0.68, steel, (0, 0, 0.34), n=12, bv=0)
cyl('flange', 0.2, 0.03, steel, (0, 0, 0.015), r2=0.17, n=24, bv=0.006)
cyl('collar', 0.07, 0.05, steel, (0, 0, 0.055), r2=0.04, n=12, bv=0)
for k in range(4):
    a = math.radians(45 + 90 * k); x, y = 0.68 * math.cos(a), 0.68 * math.sin(a)
    cyl(f'sflange{k}', 0.12, 0.025, steel, (x, y, 0.0125), n=20, bv=0.005)
    cyl(f'spole{k}', 0.032, 0.40, steel, (x, y, 0.22), n=10, bv=0)
    lathe(f'seat{k}', [(0.0, 0.42), (0.14, 0.42), (0.175, 0.435), (0.18, 0.455), (0.17, 0.472), (0.1, 0.478), (0.0, 0.478)], red, (x, y, 0), n=20)
    for j in range(3):
        b = a + math.radians(120 * j + 20)
        cyl(f'bolt{k}{j}', 0.009, 0.012, steel, (x + 0.08 * math.cos(b), y + 0.08 * math.sin(b), 0.031), n=6, bv=0)
finalize('hawker_table')
