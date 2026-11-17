import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
reset()
# Hawker-centre pedal bin: steel body, dark swing lid with a flap. Origin: floor centre. 0.46 m dia, 0.85 m high.
steel = tex('steel_brushed'); dk = flat('rubber_black', 0x22201e, 0.7); grn = flat('paint_green', 0x2e7a55, 0.5); wh = flat('paint_white', 0xf1ede0, 0.55); bag = flat('bin_bag', 0x1a1a1a, 0.4)
lathe('body', [(0, 0.05), (0.2, 0.05), (0.23, 0.07), (0.23, 0.75), (0.215, 0.77), (0.19, 0.77), (0.19, 0.74), (0, 0.74)], grn, n=28)
lathe('base', [(0.0, 0.0), (0.21, 0.0), (0.22, 0.012), (0.22, 0.05), (0.0, 0.05)], dk, n=24)
lathe('band', [(0.228, 0.62), (0.238, 0.625), (0.238, 0.7), (0.228, 0.705)], steel, n=28)
lathe('lid', [(0.0, 0.78), (0.15, 0.78), (0.24, 0.775), (0.25, 0.8), (0.245, 0.84), (0.1, 0.85), (0.0, 0.85)], dk, n=28)
lathe('hole_ring', [(0.1, 0.835), (0.12, 0.848), (0.125, 0.835), (0.105, 0.82)], steel, n=24)
box('flap', 0.2, 0.014, 0.16, steel, (0, -0.255, 0.78), (-12, 0, 0), bv=0.008)
box('sticker', 0.14, 0.004, 0.1, wh, (0, -0.236, 0.46), bv=0.002)
quad('SIGN_bin', 0.14, 0.1, (0, -0.2395, 0.46), flat('SIGN_bin', 0xf4ead0, 0.8))
finalize('bin')
