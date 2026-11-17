"""Wider, larger classroom block (Nigel, 2026-11-16): wider corridor, doors, stairs and bridge, zones A and C on level 2.
Run: python3 tools/blender/maps_toy/classroom_layout4.py
Writes layouts/classroom_solids_v4.json (v3 untouched) and layouts/classroom_map2_v4.json (the full MAPS2.classroom object for play/chope.html).
Method: layout3's colliders in old plan coordinates go through fx, fz, piecewise-linear monotone stretches that only open up in empty space
(corridor, courtyard, door openings, stair flights, east hall), so every prop moves rigidly and every room keeps its shape. fz is odd, so the z mirror holds.
New on level 2: the bridge slab gets a void over zone B with railings, so level 2 looks down onto B."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import classroom_layout3 as L3
L = os.path.join(HERE, 'layouts')
UP, RXS = L3.UP, L3.RXS

# stretch intervals (old a, old b, extra metres). z is for the north half, mirrored.
ZS = [(-2.6, -1.0, 1.5),          # courtyard: void between the blocks 12 -> 15 m
      (-8.8, -6.8, 2.0),          # corridor: wall to parapet 3.5 -> 5.5 m
      (-15.6, -15.0, .8),         # east stair flight B 2 -> 2.8 m, room depth
      (-17.4, -16.7, .8)]         # west stair and east flight A 2 -> 2.8 m
XS = [(-23.8, -23.0, .8), (-18.85, -18.15, .8)]                                  # spawn lobby doors 2 -> 2.8 m
for xr in RXS: XS += [(xr + 1.0, xr + 1.8, .9), (xr + 6.2, xr + 7.0, .9)]        # class front and back doors 1.4 -> 2.3 m
XS += [(15.0, 16.5, 2.0)]                                                        # east hall and bridge 10 -> 12 m
XS.sort()
X_SHIFT = -sum(e for _, _, e in XS) / 2                                          # recentre so the bounds stay symmetric

def _stretch(v, iv):
    out = v
    for a, b, e in iv:
        if v > a: out += e * (min(v, b) - a) / (b - a)
    return out
def fx(x): return round(_stretch(x, XS) + X_SHIFT, 4)
def fz(z):
    if z > 0: return -fz(-z)
    neg = [(-b, -a, e) for a, b, e in ZS]                                        # measured outward from z = 0
    return round(-_stretch(-z, neg), 4)
def rbox(b): return [fx(b[0]), b[1], fz(b[2]), fx(b[3]), b[4], fz(b[5]), b[6]]
def rpt(x, z): return fx(x), fz(z)

# level 2 bridge void over B
BR = (fx(14.5), fx(24.5), fz(-6))          # bridge x0, x1, north edge
VOID = (fx(19.5) - 3.0, -4.0, fx(19.5) + 2.0, 4.0)   # x0, z0, x1, z1: 5 x 8 m, B (fx 19.5) inside, west walkway 4 m, east 3 m

def tagged():
    out = []
    for b, k in L3.tagged():
        if b[2] >= 0 and 'x' not in b[6]: continue                               # rebuild the mirror after the remap
        nb = rbox(b)
        if k == 'slab' and 'x' in b[6] and nb[1] > 3:                            # level 2 bridge floor: cut the void
            vx0, vz0, vx1, vz1 = VOID
            for p in ([nb[0], 3.2, nb[2], vx0, 3.5, nb[5], 'rx'], [vx1, 3.2, nb[2], nb[3], 3.5, nb[5], 'rx'], [vx0, 3.2, nb[2], vx1, 3.5, vz0, 'r']):
                out.append((p, 'slab'))
            for g in ([vx0, 3.5, vz0, vx0 + .15, 4.6, vz1, 'ix'], [vx1 - .15, 3.5, vz0, vx1, 4.6, vz1, 'ix'], [vx0 + .15, 3.5, vz0 - .15, vx1 - .15, 4.6, vz0, 'i']):
                out.append(([round(v, 4) if not isinstance(v, str) else v for v in g], 'parapet'))
            continue
        out.append((nb, k))
    full = []
    for b, k in out:
        full.append((b, k))
        if 'x' not in b[6]: full.append((L3.mir(b), k))
    return full

def map2(src):
    """MAPS2.classroom v3 object -> v4. Points move rigidly, boxes and rects remap their edges."""
    m = json.loads(json.dumps(src))
    bx0, bx1, bz0, bz1 = m['bounds']; m['bounds'] = [fx(bx0), fx(bx1), fz(bz0), fz(bz1)]
    m['size'] = [round(m['bounds'][1] - m['bounds'][0]) + 1, round(m['bounds'][3] - m['bounds'][2]) + 1]
    m['fall']['floors'] = [[fx(a), fx(b), fz(c), fz(d)] for a, b, c, d in m['fall']['floors']]
    def rect(o, wk='w', dk='d'):
        x0, x1 = fx(o['x'] - o[wk] / 2), fx(o['x'] + o[wk] / 2); z0, z1 = fz(o['z'] - o[dk] / 2), fz(o['z'] + o[dk] / 2)
        o['x'], o['z'], o[wk], o[dk] = round((x0 + x1) / 2, 4), round((z0 + z1) / 2, 4), round(x1 - x0, 4), round(z1 - z0, 4)
    for b in m['boxes']:                                                          # [cx, cz, w, d, h, col, y0, flags], fallback only
        x0, x1 = fx(b[0] - b[2] / 2), fx(b[0] + b[2] / 2); z0, z1 = fz(b[1] - b[3] / 2), fz(b[1] + b[3] / 2)
        b[0], b[1], b[2], b[3] = round((x0 + x1) / 2, 4), round((z0 + z1) / 2, 4), round(x1 - x0, 4), round(z1 - z0, 4)
    for p in m['props'] + m['signs']['place']: p['x'], p['z'] = rpt(p['x'], p['z'])
    for s in m['spawns']: s['x'], s['z'] = rpt(s['x'], s['z'])                  # spawn boxes keep 5 x 5 m
    for p in m['pickups']: p['x'], p['z'] = rpt(p['x'], p['z'])
    for h in m['hazards']:
        if h['k'] == 'wet': h['x'], h['z'] = 18.7, -8.6                           # wet floor in front of the toilet door (layout3 moved the door to x 18 to 19.4)
        rect(h)
    for z in m['zones']:
        z['x'], z['z'] = rpt(z['x'], z['z'])
        if z['id'] in ('A', 'C'): z['y'] = UP                                    # A and C: level 2, room 3 (two doors, three ways onto the level 2 corridor)
    nav = m['nav']
    for n in nav['nodes']: n[1], n[2] = rpt(n[1], n[2])                          # hand nav: unused while the toy solids load (genNav replaces it)
    for h in nav['holds']:
        h[1], h[2] = rpt(h[1], h[2])
        if h[0] in ('snA', 'tkA', 'bdA', 'asA'): h[3] = UP                       # A team holds go up with zone A
    for h in nav['holds']:
        if h[0] == 'snB': h[1], h[2], h[3] = round(fx(19.5) - 3.6, 4), VOID[1] - 1.2, UP  # sniper on the level 2 bridge crossing, over the void onto B
    for c in nav['chokes']: c[1], c[2] = rpt(c[1], c[2])
    c = m['look']['cam']; c[0], c[2] = rpt(c[0], c[2])
    return m

if __name__ == '__main__':
    T = tagged(); S = [b for b, _ in T]
    json.dump(S, open(os.path.join(L, 'classroom_solids_v4.json'), 'w'))
    key = lambda b: tuple(round(v, 3) for v in b[:6])
    have = set(map(key, S))
    assert all(key(L3.mir(b)) in have for b in S), 'not z-mirrored'
    units = [b for b in S if b[6] == 'i' and abs(b[4] - b[1] - .72) < .01]
    for u in units:
        for o in S:
            if o is u or 'r' in o[6] or o[4] <= u[1] or o[1] >= u[4]: continue
            gap = max(o[0] - u[3], u[0] - o[3], o[2] - u[5], u[2] - o[5])
            assert gap >= 1.1, (u, o, gap)
    assert max(b[4] - b[1] for b in S if b[6] == 'stair' and b[4] <= .36) <= .4
    for b in S: assert b[0] < b[3] and b[2] < b[5], b
    # every desk, locker, bin, plant, cooler keeps its v3 size (the stretches only cross empty space)
    rigid = ('desk', 'locker', 'bin', 'plant', 'cooler', 'tdesk', 'ptable', 'pbench', 'sinks', 'urinals', 'post', 'pillar')
    for b3, k in L3.tagged():
        b4 = rbox(b3)
        if k in rigid: assert abs((b4[3] - b4[0]) - (b3[3] - b3[0])) < .01 and abs((b4[5] - b4[2]) - (b3[5] - b3[2])) < .01, ('stretched', k, b3, b4)
    src = json.load(open(os.path.join(sys.argv[1] if len(sys.argv) > 1 else os.path.join(L, 'classroom.json'))))
    m = map2(src); json.dump(m, open(os.path.join(L, 'classroom_map2_v4.json'), 'w'), separators=(',', ':'))
    print('desk units', len(units), 'v4 solids', len(S))
    print('bounds', src['bounds'], '->', m['bounds'], 'size', m['size'])
    print('zones', [(z['id'], z['x'], z.get('y', 0), z['z']) for z in m['zones']])
    print('spawns', [(s['x'], s['z'], s['w'], s['d']) for s in m['spawns']])
    print('corridor z', fz(-9.5), fz(-6), 'door', fx(-1.5 + 2.1) - fx(-1.5 + .7), 'bridge', BR, 'void', VOID)
