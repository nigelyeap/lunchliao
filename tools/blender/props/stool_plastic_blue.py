import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
reset()
# Plastic kopitiam stool, colour: blue. Origin: floor centre, seat at 0.45 m.
pl = tex('plastic_blue'); dk = flat('rubber_black', 0x22201e, 0.8)
lathe('seat', [(0, 0.43), (0.15, 0.43), (0.18, 0.44), (0.19, 0.455), (0.185, 0.47), (0.16, 0.477), (0.08, 0.477), (0, 0.477)], pl, n=24)
lathe('ringtop', [(0.12, 0.40), (0.17, 0.40), (0.17, 0.43), (0.12, 0.43)], pl, n=24)
for k in range(4):
    a = math.radians(45 + 90 * k)
    limb(f'leg{k}', (0.12 * math.cos(a), 0.12 * math.sin(a), 0.42), (0.19 * math.cos(a), 0.19 * math.sin(a), 0.01), 0.026, 0.02, pl, n=8)
    box(f'foot{k}', 0.05, 0.05, 0.015, dk, (0.19 * math.cos(a), 0.19 * math.sin(a), 0.0075), (0, 0, 45 + 90 * k), bv=0.004)
lathe('brace', [(0.158 + 0.012 * math.cos(t), 0.2 + 0.012 * math.sin(t)) for t in [i * math.tau / 7 for i in range(8)]][:7] + [(0.158 + 0.012, 0.2)], pl, n=24)
finalize('stool_plastic_blue')
