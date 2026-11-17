import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
reset()
# Tissue packet used to chope a table. Origin: base centre (sits on the table), lying flat, slightly crumpled.
pk = flat('tissue_pack', 0xdbe9f2, 0.5); pr = flat('tissue_print', 0x4c86c8, 0.5); crimp = flat('tissue_crimp', 0xb9ccd9, 0.55)
box('body', 0.105, 0.065, 0.026, pk, (0, 0, 0.015), (0, 0, 8), bv=0.01, seg=2)
box('band', 0.045, 0.067, 0.027, pr, (0.005, 0, 0.0155), (0, 0, 8), bv=0.006)
for s in (-1, 1): box('crimp', 0.012, 0.062, 0.01, crimp, (s * 0.058, s * 0.008, 0.013), (0, 0, 8), bv=0.003)
sphere('puff', 0.04, 0.025, 0.008, pk, (-0.02, 0.0, 0.03), (0, 0, 8), n=8)
finalize('chope_tissue')
