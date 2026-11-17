import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
reset()
# Teh tarik: two steel pitchers + 3 glass cups of milk tea on a steel tray. Origin: tray bottom centre.
steel = tex('steel_brushed'); tea = flat('tea', 0xb8793c, 0.2); glass = flat('glass', 0xcfe8e8, 0.05, alpha=0.2); mug = flat('paint_cream', 0xefe2bf, 0.4); dk = flat('rubber_black', 0x22201e, 0.8)
lathe('tray', [(0, 0), (0.23, 0), (0.25, 0.012), (0.25, 0.025), (0.235, 0.025), (0.23, 0.014), (0, 0.014)], steel, n=28)
def pitcher(x, y, s=1.0):
    lathe('pitcher', [(0, 0.014), (0.07 * s, 0.014), (0.085 * s, 0.03), (0.075 * s, 0.2 * s), (0.065 * s, 0.26 * s), (0.075 * s, 0.275 * s), (0.06 * s, 0.275 * s), (0.055 * s, 0.25 * s), (0, 0.25 * s)], steel, (x, y, 0), n=20)
    limb('p_handle_a', (x + 0.07 * s, y, 0.22 * s), (x + 0.13 * s, y, 0.22 * s), 0.013, 0.013, steel, n=6)
    limb('p_handle_b', (x + 0.13 * s, y, 0.22 * s), (x + 0.11 * s, y, 0.08 * s), 0.013, 0.013, steel, n=6)
    limb('p_handle_c', (x + 0.11 * s, y, 0.08 * s), (x + 0.08 * s, y, 0.07 * s), 0.013, 0.013, steel, n=6)
    box('p_spout', 0.05, 0.05, 0.04, steel, (x - 0.07 * s, y, 0.27 * s), (0, 0, 0), bv=0.01)
pitcher(-0.1, 0.07); pitcher(0.1, 0.1, 0.85)
for i, (x, y) in enumerate(((-0.1, -0.12), (0.03, -0.1), (0.15, -0.09))):
    lathe(f'cup{i}', [(0, 0.014), (0.04, 0.014), (0.05, 0.1), (0.054, 0.105), (0.047, 0.105), (0.038, 0.03), (0, 0.03)], glass, (x, y, 0), n=16)
    lathe(f'tea{i}', [(0, 0.03), (0.037, 0.03), (0.048, 0.085), (0, 0.085)], tea, (x, y, 0), n=16)
    lathe(f'foam{i}', [(0, 0.085), (0.048, 0.085), (0.045, 0.092), (0, 0.095)], mug, (x, y, 0), n=16)
finalize('teh_tarik')
