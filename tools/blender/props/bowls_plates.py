import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
reset()
# Stack of 5 bowls and a stack of 4 plates, side by side. Origin: surface centre.
w = flat('ceramic_white', 0xf3efe4, 0.25); blue = flat('ceramic_blue', 0x2f5fa8, 0.3); rim = flat('ceramic_rim', 0xd9d2bf, 0.3)
bowl = [(0, 0), (0.03, 0), (0.035, 0.012), (0.075, 0.05), (0.105, 0.11), (0.108, 0.12), (0.1, 0.12), (0.098, 0.11), (0.07, 0.06), (0.03, 0.02), (0, 0.02)]
for i in range(5):
    lathe(f'bowl{i}', [(r, z + i * 0.055) for r, z in bowl], w if i % 2 == 0 else rim, (-0.17, 0, 0), (0, 0, 20 * i), n=20)
    lathe(f'bband{i}', [(0.1, 0.1 + i * 0.055), (0.106, 0.11 + i * 0.055), (0.108, 0.115 + i * 0.055), (0.1, 0.115 + i * 0.055)], blue, (-0.17, 0, 0), n=20)
plate = [(0, 0), (0.08, 0), (0.095, 0.008), (0.13, 0.03), (0.135, 0.035), (0.13, 0.036), (0.1, 0.014), (0.08, 0.008), (0, 0.008)]
for i in range(4): lathe(f'plate{i}', [(r, z + i * 0.026) for r, z in plate], w if i % 2 == 0 else rim, (0.15, 0.02 * (i % 2), 0), n=22)
finalize('bowls_plates')
