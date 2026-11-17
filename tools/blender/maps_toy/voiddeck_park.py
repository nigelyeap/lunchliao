"""Void deck: colliders added for the park, fitness corner and shop rows.
ADD lists the west half only. The east half is the point mirror (x, z) -> (-x, -z).
Run with python3 to check clearances and append them to layouts/voiddeck_solids_v2.json (safe to rerun).
voiddeck.py imports ADD to build the matching visuals.
"""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.join(HERE, 'layouts/voiddeck_solids_v2.json')
def sq(x, z, s, h): return [round(x - s / 2, 3), 0, round(z - s / 2, 3), round(x + s / 2, 3), h, round(z + s / 2, 3)]
ADD = [  # kind, [x0, y0, z0, x1, y1, z1]
    ('rain', sq(-28.5, -22.5, .5, 2.7)), ('angsana', sq(-40.5, -20.4, .5, 2.7)),
    ('palm', sq(-40.6, -11.6, .35, 5)), ('palm', sq(-37.6, -12.4, .35, 5)),
    ('bench', [-44.6, 0, -14.9, -44.15, .46, -13.1]), ('bin', sq(-44.29, -11.7, .62, .88)),
    ('lamp', sq(-44.5, -21.5, .2, 4)), ('lamp', sq(-44.5, -6.0, .2, 4)), ('lamp', sq(-13.65, -16.0, .2, 4)),
    ('bars', [-19.2, 0, -12.3, -18.0, 1.2, -11.7]), ('pullup', [-16.2, 0, -10.9, -15.0, 2.2, -10.3]), ('walker', [-17.7, 0, -15.1, -16.5, 1.3, -14.5]),
    ('display', [-43.6, 0, 23.9, -41.6, .9, 24.5]), ('sbench', [-37.6, 0, 24.05, -35.8, .46, 24.5]), ('case', [-44.5, 0, 19.3, -43.9, 1.0, 20.9]),
]
def both(): return [(k, b, 1) for k, b in ADD] + [(k, [-b[3], b[1], -b[5], -b[0], b[4], -b[2]], -1) for k, b in ADD]

def gap(a, b):
    dx = max(a[0] - b[3], b[0] - a[3], 0); dz = max(a[2] - b[5], b[2] - a[5], 0); return math.hypot(dx, dz)
def seg_d(b, p, q):
    cx, cz = (b[0] + b[3]) / 2, (b[2] + b[5]) / 2; vx, vz = q[0] - p[0], q[1] - p[1]
    t = max(0, min(1, ((cx - p[0]) * vx + (cz - p[1]) * vz) / (vx * vx + vz * vz or 1)))
    return math.hypot(cx - p[0] - t * vx, cz - p[1] - t * vz) - max(b[3] - b[0], b[5] - b[2]) / 2

if __name__ == '__main__':
    S = json.load(open(V2)); X = json.load(open(os.path.join(HERE, 'layouts/voiddeck_expanded.json')))
    N = {n['id']: n for n in X['nodes']}; new = [b for _, b, _ in both()]
    old = [s for s in S if s[:6] not in new]
    for k, b in ADD:
        for l in X['links']:
            p, q = N[l[0]], N[l[1]]
            if p['y'] == 0 and q['y'] == 0 and seg_d(b, (p['x'], p['z']), (q['x'], q['z'])) < .7: print('ROUTE', k, b, l[:2])
        for z in X['zones'] + X['pickups'] + X['spawns']:
            if seg_d(b, (z['x'], z['z']), (z['x'], z['z'] + 1e-6)) < z.get('r', 2.0): print('ZONE', k, b, z)
        for s in old + [c for c in new if c != b]:
            g = gap(b, s)
            if 'i' not in str(s[6:]) and 'r' not in str(s[6:]) and s[1] < 1 and .12 < g < 2.5: print('LANE %.2f' % g, k, b, [round(v, 2) for v in s[:6]])
    add = [b + ['s'] for b in new if b not in [s[:6] for s in S]]
    if add: json.dump(S + add, open(V2, "w"))
    print('added', len(add), 'total', len(S) + len(add))
