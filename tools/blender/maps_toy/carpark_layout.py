"""Carpark v3 layout (real carpark logic, see carpark_REF.md section 7). Single source for colliders and visuals.
ITEMS is a list of dicts: k kind, b [x0,y0,z0,x1,y1,z1] game coords, f collider flag (None = paint only), plus per-kind fields.
Run with system python (needs Pillow) to write layouts/carpark_solids_v3.json, run the checks and draw the plan image:
  python3 tools/blender/maps_toy/carpark_layout.py [plan.jpg]
carpark.py imports ITEMS to build the visuals, so the model and the colliders cannot drift apart."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); LAY = os.path.join(HERE, 'layouts')
PI = math.pi
H = []          # the west pod and the centre-north block. The point mirror adds the rest.

def add(k, x0, z0, x1, z1, h, f='s', y0=0.0, **kw): H.append(dict(k=k, b=[x0, y0, z0, x1, y0 + h, z1], f=f, **kw))
def hedge(x0, z0, x1, z1, trees=(), lamps=()): add('hedge', x0, z0, x1, z1, 1.5, trees=list(trees), lamps=list(lamps))
def car(x, z, ry, van=False):
    w, d, h = (2.0, 4.8, 2.1) if van else (1.8, 4.2, 1.45)
    if abs(math.sin(ry)) > .5: w, d = d, w
    add('car', x - w / 2, z - d / 2, x + w / 2, z + d / 2, h, ry=ry, van=van)
def bays(x0, z0, x1, z1, op, n, red=False):
    """n bays side by side in the rectangle. op is the side open to the aisle (N = +z, S, E = +x, W)."""
    for i in range(n):
        if op in 'NS': a = x0 + (x1 - x0) * i / n; c = x0 + (x1 - x0) * (i + 1) / n; r = [a, z0, c, z1]
        else: a = z0 + (z1 - z0) * i / n; c = z0 + (z1 - z0) * (i + 1) / n; r = [x0, a, x1, c]
        H.append(dict(k='bay', b=[r[0], 0, r[1], r[2], 0, r[3]], f=None, op=op, red=red))
def arrow(x, z, ry): H.append(dict(k='arrow', b=[x, 0, z, x, 0, z], f=None, ry=ry))

# ---- west end: lift and stair cores either side of the lobby (the spawn), canopy between them
add('core', -44.6, 5.8, -39.6, 12.2, 4.2, kind='lift', door='S')
add('core', -44.6, -12.2, -39.6, -5.8, 4.2, kind='stair', door='N')
add('canopy', -44.6, -5.8, -39.6, 5.8, .2, f='r', y0=3.4)
hedge(-44.6, 23, -39.5, 30.5, trees=[(-42, 26.8)]); hedge(-44.6, -30.5, -39.5, -23, trees=[(-42, -26.8)])   # corner planters, each with a leg that ends the west aisle
hedge(-39.5, 27.4, -34, 30.5, lamps=[(-36.7, 29)]); hedge(-39.5, -30.5, -34, -27.4, lamps=[(-36.7, -29)])
bays(-44.4, 12.8, -39.6, 22.4, 'E', 4, red=True); bays(-44.4, -22.4, -39.6, -12.8, 'E', 4, red=True)
# ---- west pod: three double rows along x with planted medians, aisles between, a cross aisle through the centre row at zone A
hedge(-39.5, -2.5, -34, 2.5, lamps=[(-36.5, 0)])                                      # lobby island, closes the west aisle in front of the spawn
hedge(-34, -5.8, -32.4, 5.8, trees=[(-33.2, 4), (-33.2, -4)]); hedge(-32.4, -1, -27.6, 1)
hedge(-27.6, -5.8, -25.2, 5.8, trees=[(-26.4, 3.6), (-26.4, -3.6)], lamps=[(-26.4, 0)])
bays(-32.4, 1, -27.6, 5.8, 'N', 2); bays(-32.4, -5.8, -27.6, -1, 'S', 2)
hedge(-14, -5.8, -13, 5.8, trees=[(-13.5, 3.4), (-13.5, -3.4)], lamps=[(-13.5, 0)]); hedge(-18.8, -1, -14, 1)    # row end island facing zone B
bays(-18.8, 1, -14, 5.8, 'N', 2); bays(-18.8, -5.8, -14, -1, 'S', 2); car(-17.6, -3.4, PI)
hedge(-34, 12.2, -32.4, 23, trees=[(-33.2, 14.5), (-33.2, 21)])                       # north row
hedge(-32.4, 17, -25.4, 18.2, lamps=[(-29, 17.6)]); hedge(-22.6, 17, -15.6, 18.2, lamps=[(-19, 17.6)])
bays(-32.4, 12.2, -15.6, 17, 'S', 7); bays(-32.4, 18.2, -15.6, 23, 'N', 7, red=True)
hedge(-15.6, 5.8, -13.4, 13.4, trees=[(-14.5, 9)]); hedge(-15.6, 16, -13.4, 30.5, trees=[(-14.5, 20.5), (-14.5, 27)])   # boundary planter, one walk-through gap
hedge(-34, -23, -32.4, -19.3); hedge(-34, -15.7, -32.4, -12.2, trees=[(-33.2, -14)])  # south row, west island split around the pickup
hedge(-32.4, -18.2, -15.6, -17, lamps=[(-29, -17.6), (-19, -17.6)])
hedge(-15.6, -30.5, -14, -12.2, trees=[(-14.8, -14.5), (-14.8, -21), (-14.8, -27.5)])
bays(-32.4, -17, -15.6, -12.2, 'N', 7); bays(-32.4, -23, -15.6, -18.2, 'S', 7, red=True)
for x in (-24, -21.6, -19.2): car(x, 14.6, PI); car(x, -14.6, 0)                      # cars closing both ends of the cross aisle at zone A
car(-28.8, 3.4, 0); car(-28.8, 20.6, 0); car(-24, -20.6, PI)
# ---- centre north: rows along z. Single row, dead-end aisle with the teh pickup, covered double row, ramp aisle
hedge(-13.4, 4.2, -8.6, 8.4, trees=[(-11, 6.3)]); hedge(-13.4, 27.6, -8.6, 30.5)
bays(-13.4, 8.4, -8.6, 27.6, 'E', 8)
hedge(-8.6, 26.6, -2.6, 30.5, trees=[(-5.6, 28.6)])
add('rack', -8.3, 25.5, -5.5, 26.5, 1.1, f=''); add('bin', -4.3, 25.8, -3.7, 26.4, .9, f='')
hedge(-2.6, 4.2, 8.6, 6.5, trees=[(0, 5.3), (6, 5.3)]); hedge(8.6, 6.5, 11.4, 12.2, trees=[(10, 9.3)])   # row end island and the ramp junction island
hedge(-2.6, 28.1, 8, 30.5, trees=[(2.7, 29.3)])
hedge(2.2, 6.5, 3.2, 16, lamps=[(2.7, 11)]); hedge(2.2, 18.6, 3.2, 28.1, lamps=[(2.7, 23.5)])
bays(-2.6, 6.5, 2.2, 28.1, 'W', 9); bays(3.2, 6.5, 8, 28.1, 'E', 9)
for z in (6.5, 13.7, 20.9, 28.1):
    for x in (-2.35, 7.75): add('col', x - .25, z - .25, x + .25, z + .25, 3.0)
add('canopy', -2.9, 6.2, 2.0, 28.4, .2, f='r', y0=3.0); add('canopy', 3.4, 6.2, 8.3, 28.4, .2, f='r', y0=3.0)
hedge(-8.6, -.5, -3.3, .5, lamps=[(-6, 0)])                                           # median in the cross aisle west of zone B
add('booth', 8.2, 26, 10, 28.4, 2.6)                                                  # coupon booth at the ramp head
car(12.6, 16.4, 0, van=True); car(5.6, 22.2, PI / 2, van=True)
car(-.2, 10.1, -PI / 2); car(5.6, 15.3, PI / 2)
for a in ((-37, 8, PI), (-37, -8, 0), (-30, 9, PI / 2), (-20, 9, PI / 2), (-30, -9, -PI / 2), (-18, -9, -PI / 2), (-22, 2, PI), (-28, 26.2, PI / 2), (-28, -26.2, -PI / 2),
          (-5.6, 12, 0), (-5.6, 20, 0), (11, 27, PI), (12.6, 9, PI), (-9, 1.9, -PI / 2), (-9, -1.9, PI / 2)): arrow(*a)

def mirror(i):
    b = i['b']; j = dict(i, b=[-b[3], b[1], -b[5], -b[0], b[4], -b[2]])
    if 'ry' in i: j['ry'] = i['ry'] + PI
    if 'op' in i: j['op'] = dict(N='S', S='N', E='W', W='E')[i['op']]
    if 'door' in i: j['door'] = dict(N='S', S='N')[i['door']]
    for k in ('trees', 'lamps'):
        if k in i: j[k] = [(-x, -z) for x, z in i[k]]
    return j

EDGE = [[-45, 0, -30.7, -44.6, 1.1, 30.7, 's'], [-44.5, 0, 30.5, 8, 1.1, 30.9, 's'], [14, 0, 30.5, 44.5, 1.1, 30.9, 's'],      # outer edge, unchanged from v2
        [-45.2, 0, -30.7, -44.8, 6, 30.7, 'i'], [-45, 0, 30.7, 45, 6, 31.1, 'i']]
ITEMS = [dict(k='iwall' if b[6] == 'i' else 'parapet', b=b[:6], f=b[6]) for b in EDGE]
ITEMS += [mirror(i) for i in ITEMS] + H + [mirror(i) for i in H]
SOLIDS = [[round(v, 3) for v in i['b']] + [i['f']] for i in ITEMS if i['f'] is not None]

if __name__ == '__main__':
    X = json.load(open(os.path.join(LAY, 'carpark_expanded.json')))
    json.dump(SOLIDS, open(os.path.join(LAY, 'carpark_solids_v3.json'), 'w'), separators=(',', ':'))
    real = [b for b in SOLIDS if b[6] not in ('i', 'r')]
    keep = [(s['x'] - s['w'] / 2, s['z'] - s['d'] / 2, s['x'] + s['w'] / 2, s['z'] + s['d'] / 2, 'spawn') for s in X['spawns']]
    keep += [(z['x'] - z['r'], z['z'] - z['r'], z['x'] + z['r'], z['z'] + z['r'], 'zone ' + z['id']) for z in X['zones']]
    keep += [(p['x'] - .8, p['z'] - .8, p['x'] + .8, p['z'] + .8, 'pickup') for p in X['pickups']]
    for k in keep:
        for b in real: assert not (b[0] < k[2] and b[3] > k[0] and b[2] < k[3] and b[5] > k[1]), (k, b)
    for a in real:                                        # nothing overlaps a car
        for b in real:
            if a is not b and round(a[4], 2) in (1.45, 2.1) and round(a[3] - a[0], 1) in (1.8, 4.2, 2.0, 4.8): assert not (a[0] < b[3] - .01 and a[3] > b[0] + .01 and a[2] < b[5] - .01 and a[5] > b[2] + .01), (a, b)
    G = .2; fat = [(b[0] - 1.2, b[2] - 1.2, b[3] + 1.2, b[5] + 1.2) for b in real]
    def free(c): x, z = c[0] * G, c[1] * G; return abs(x) < 43.3 and abs(z) < 29.3 and not any(t[0] < x < t[2] and t[1] < z < t[3] for t in fat)
    c0 = (round(X['spawns'][0]['x'] / G), round(X['spawns'][0]['z'] / G)); assert free(c0); got = {c0}; q = [c0]
    while q:
        c = q.pop()
        for n in ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)):
            if n not in got and free(n): got.add(n); q.append(n)
    for k in keep: assert (round((k[0] + k[2]) / 2 / G), round((k[1] + k[3]) / 2 / G)) in got, ('no 2.4 m wide route to', k)
    cars = [i for i in ITEMS if i['k'] == 'car']
    print('solids', len(SOLIDS), 'cars', sum(not c['van'] for c in cars), 'vans', sum(c['van'] for c in cars))
    # longest clear straight run at eye height. Blockers are solids 1.4 m or taller, grown 0.35 m so slits under 0.7 m do not count.
    tall = [(b[0] - .35, b[2] - .35, b[3] + .35, b[5] + .35) for b in real if b[4] >= 1.4 and b[1] < 1] + [(-99, -99, -44.6, 99), (44.6, -99, 99, 99), (-99, 30.5, 99, 99), (-99, -99, 99, -30.5)]
    def blocked(x, z): return any(t[0] <= x <= t[2] and t[1] <= z <= t[3] for t in tall)
    runs = []
    for ax in (0, 1):
        for i in range(-110 if ax == 0 else -76, 111 if ax == 0 else 77):
            c = i * .4; run = 0; s = None; n = 224 if ax == 1 else 154
            for j in range(-n, n + 1):
                t = j * .2; p = (t, c) if ax == 1 else (c, t)
                if blocked(*p):
                    if run: runs.append((round(run * .2, 1), 'along x' if ax == 1 else 'along z', round(c, 1), round(s, 1), round(t, 1)))
                    run = 0
                else:
                    if not run: s = t
                    run += 1
    runs.sort(reverse=True); seen = []
    for r in runs:
        if all(not (r[1] == q[1] and abs(r[2] - q[2]) < 2.5 and abs(r[3] - q[3]) < 3) for q in seen): seen.append(r)
        if len(seen) == 8: break
    print('longest clear runs (m, axis, at, from, to):'); [print(' ', r) for r in seen]
    if len(sys.argv) > 1:
        from PIL import Image, ImageDraw
        K = 15; W, Hh = 1500, 1080; im = Image.new('RGB', (W, Hh), 'white'); d = ImageDraw.Draw(im)
        def R(b): return [W / 2 + b[0] * K, 110 + 31.5 * K + b[1] * K, W / 2 + b[2] * K, 110 + 31.5 * K + b[3] * K]
        d.text((20, 12), 'CARPARK v3 proposal. Grey = v2 colliders (all replaced). Magenta = v3 solids. Thin lines = painted bays. Dashed = canopy roof.', fill='black')
        d.text((20, 30), 'Blue and orange = spawns. Red circles = zones. Green dots = pickups. Game x right, game z down. Point mirror kept.', fill='black')
        d.text((20, 48), 'solids %d, cars %d, vans %d, longest clear run %.1f m' % (len(SOLIDS), sum(not c['van'] for c in cars), sum(c['van'] for c in cars), seen[0][0]), fill='black')
        for b in json.load(open(os.path.join(LAY, 'carpark_solids_v2.json'))):
            if b[6] != 'i': d.rectangle(R((b[0], b[2], b[3], b[5])), outline=(205, 205, 205), fill=(236, 236, 236))
        for i in ITEMS:
            b = i['b']; r = R((b[0], b[2], b[3], b[5]))
            if i['k'] == 'bay': d.rectangle(r, outline=(200, 60, 60) if i['red'] else (120, 120, 120))
        for i in ITEMS:
            b = i['b']; r = R((b[0], b[2], b[3], b[5]))
            if i['k'] == 'canopy': d.rectangle(r, outline=(120, 0, 160))
            elif i['k'] == 'arrow':
                c, s = math.sin(i['ry']), math.cos(i['ry']); d.line([r[0] - c * 14, r[1] - s * 14, r[0] + c * 14, r[1] + s * 14], fill=(230, 160, 0), width=3); d.ellipse([r[0] + c * 14 - 4, r[1] + s * 14 - 4, r[0] + c * 14 + 4, r[1] + s * 14 + 4], fill=(230, 160, 0))
            elif i['f'] not in (None, 'i'):
                d.rectangle(r, outline=(200, 0, 150), fill={'hedge': (150, 215, 150), 'car': (255, 120, 220), 'core': (190, 120, 220), 'parapet': (255, 0, 200)}.get(i['k'], (255, 170, 235)), width=2)
        for s in X['spawns']: d.rectangle(R((s['x'] - s['w'] / 2, s['z'] - s['d'] / 2, s['x'] + s['w'] / 2, s['z'] + s['d'] / 2)), outline=(30, 90, 220) if s['team'] == 1 else (240, 130, 20), width=4)
        for z in X['zones']: d.ellipse(R((z['x'] - z['r'], z['z'] - z['r'], z['x'] + z['r'], z['z'] + z['r'])), outline=(220, 0, 0), width=3); d.text((W / 2 + z['x'] * K - 3, 110 + 31.5 * K + z['z'] * K - 5), z['id'], fill=(220, 0, 0))
        for p in X['pickups']: d.ellipse(R((p['x'] - .6, p['z'] - .6, p['x'] + .6, p['z'] + .6)), fill=(0, 150, 60)); d.text((W / 2 + p['x'] * K + 11, 110 + 31.5 * K + p['z'] * K - 5), p['k'], fill=(0, 110, 40))
        im.save(sys.argv[1], quality=90); print('plan', sys.argv[1])
