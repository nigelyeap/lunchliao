import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
reset()
# Hanging fluorescent batten with tube. Origin: ceiling attach point, hangs down. TUBE_emit is the glowing tube (renderer may drive intensity).
wh = flat('paint_white', 0xe9e6dc, 0.5); steel = tex('steel_brushed'); dk = flat('rubber_black', 0x22201e, 0.8)
tube = flat('TUBE_emit', 0xfff3d0, 0.3, emit=(0xfff0cc, 4.0))
box('batten', 1.22, 0.1, 0.045, wh, (0, 0, -0.62), bv=0.012, seg=2)
box('lip_a', 1.22, 0.012, 0.04, wh, (0, 0.05, -0.65), (0, 0, 0), bv=0.004); box('lip_b', 1.22, 0.012, 0.04, wh, (0, -0.05, -0.65), bv=0.004)
for s in (-1, 1):
    box('cap', 0.05, 0.07, 0.05, dk, (s * 0.6, 0, -0.655), bv=0.008)
    cyl('chain', 0.004, 0.6, steel, (s * 0.52, 0, -0.3), n=6, bv=0); box('hook', 0.04, 0.04, 0.02, steel, (s * 0.52, 0, 0.0), bv=0.004)
    box('clip', 0.03, 0.05, 0.05, steel, (s * 0.52, 0, -0.6), bv=0.005)
cyl('TUBE_emit', 0.0135, 1.18, tube, (0, 0, -0.665), (0, 90, 0), n=10, bv=0, group='TUBE_emit')
finalize('fluorescent_tube')
