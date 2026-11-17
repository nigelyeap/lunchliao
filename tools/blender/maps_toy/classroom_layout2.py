"""Two-storey Classroom Block layout (Nigel approved, 2026-11-16).
Reads layouts/classroom_expanded.json (never edits it) and writes layouts/classroom2_expanded.json and classroom2_solids.json.
Run: python3 tools/blender/maps_toy/classroom_layout2.py
Lower storey = the old map. Upper storey = a copy 3.5 m up, standing on the old roof slab (r boxes are solid).
Changes to the lower storey: the lobby grille and fake steps become a real stair (west), and the STAIRCASE 2 door opens into a real stair (east)."""
import json, math, os, copy
L = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'layouts')
UP = 3.5          # storey height: 3.2 clear + 0.3 slab
E = json.load(open(os.path.join(L, 'classroom_expanded.json')))

def bx(x0, x1, z0, z1, h, col, y0=0, f='s'):
    return [round((x0 + x1) / 2, 4), round((z0 + z1) / 2, 4), round(x1 - x0, 4), round(z1 - z0, 4), h, col, y0, f]
def near(a, b, e=.02): return abs(a - b) < e
def both(fn):
    """Run fn(s) for the north half (s=-1, z negative) and the south half (s=+1). zz(a,b) orders a z pair for that side."""
    out = []
    for s in (-1, 1): out += fn(s, lambda a, b: (min(-s * a, -s * b), max(-s * a, -s * b)))
    return out

WALL, TILE, SLAB = '#efe6cf', '#ffffff@walltile', '#e6dcc4'
low, top_only = [], []
for b in E['boxes']:
    x, z, w, d, h, col, y0, f = b[:8]; az = abs(z)
    if x < -17.5 and near(az, 16.2): continue                                   # lobby grille (i wall, rail, bars)
    if near(az, 17.025) and near(d, 1.45) and f == 'v': continue                # fake steps
    if col == '#ffffff@walltile' and near(w, 7.0): continue                     # toilet block east mass, rebuilt below
    if near(x, 19.5) and near(az, 9.515) and near(h, 2.4): continue             # STAIRCASE 2 door panel, now an opening
    if 'r' in f and 'x' not in f: continue                                      # wing roof slab, rebuilt with stair holes
    if near(y0, 3.5) and near(h, .8): top_only.append(b[:8]); continue          # roof fascia, belongs on the top roof only
    low.append(b[:8])

def lower_extra(s, zz):
    o = []
    # slab under the upper floor, with the two stair holes (west x -23.5..-19, z 15.75..17.75; east x 18.4..20.6, z 9.75..14.75)
    for x0, x1, a, b in [(-25, -23.5, 6, 18), (-23.5, -19, 6, 15.75), (-19, 18.4, 6, 18), (18.4, 20.6, 6, 9.75), (18.4, 20.6, 14.75, 18), (20.6, 24.5, 6, 18)]:
        o.append(bx(x0, x1, *zz(a, b), .3, SLAB, 3.2, 'r'))
        o.append(bx(max(x0, -24.5), x1, *zz(a, min(b, 17.75)), .006, '#b9735c', UP, 'vn'))   # terracotta tile on the upper floor
    # toilet block east mass, carved for the stair
    o.append(bx(17.5, 18.4, *zz(9.5, 17.75), 3.2, TILE))
    o.append(bx(20.6, 24.5, *zz(9.5, 17.75), 3.2, TILE))
    o.append(bx(18.4, 20.6, *zz(14.75, 17.75), 3.2, TILE))
    o.append(bx(18.4, 20.6, *zz(9.5, 9.75), .8, WALL, 2.4))                     # lintel over the stair door
    return o
def upper_extra(s, zz):
    o = []
    o.append(bx(-25, 24.5, *zz(6, 18), .3, SLAB, UP + 3.2, 'r'))                # top roof
    # guards round the west stair hole
    o.append(bx(-23, -18.9, *zz(15.65, 15.75), 1.1, '#000', UP, 'i'))
    o.append(bx(-19, -18.9, *zz(15.75, 17.75), 1.1, '#000', UP, 'i'))
    # upper stair hall inside the toilet block: landing z 14.75..17.75, passage x 20.6..22.8 back to the corridor
    o.append(bx(17.5, 18.4, *zz(9.5, 17.75), 3.2, TILE, UP))
    o.append(bx(22.8, 24.5, *zz(9.5, 17.75), 3.2, TILE, UP))
    o.append(bx(18.4, 20.6, *zz(9.5, 9.75), 3.2, WALL, UP))                      # closes the hole on the corridor side
    o.append(bx(20.6, 22.8, *zz(9.5, 9.75), .8, WALL, UP + 2.4))                 # lintel over the upper stair door
    o.append(bx(20.6, 20.75, *zz(9.75, 14.25), 1.1, '#d9d4c8', UP))              # low wall between hole and passage
    return o

def lift(b):
    b = list(b); b[6] = round(b[6] + UP, 4); return b
up = [lift(b) for b in low if b[6] >= 0 or (near(b[6], -.4) and near(b[3], .25))]   # everything on the storey, plus the edge beam
up += [lift(b) for b in top_only]                                                      # fascia (the bridge roof is already in low)
boxes = low + both(lower_extra) + up + both(upper_extra)

stairs = both(lambda s, zz: [
    dict(x=-21.25, z=s * 16.75, w=4.5, d=2, axis='x', dir=-1, y0=0, y1=UP, n=9, c='#bdb3a3', c2='#cbc2b2'),
    dict(x=19.5, z=s * 12.5, w=2.2, d=4.5, axis='z', dir=s, y0=0, y1=UP, n=9, c='#bdb3a3', c2='#cbc2b2')])

props = copy.deepcopy(E['props'])
for p in E['props']:
    q = dict(p); q['y'] = round(p.get('y', 0) + UP, 3); props.append(q)

S = copy.deepcopy(E['signs']); rows = S['rows']; n0 = len(rows)
names = ['COURAGE', 'INTEGRITY', 'RESPECT', 'HARMONY']
rows += [dict(bg='#1d6f6a', fg='#fbf8f0', en='P4 ' + n) for n in names] + [dict(bg='#1d6f6a', fg='#fbf8f0', en='P3 ' + n) for n in names]
rows += [dict(bg='#1c1512', fg='#f3ecd9', en='LEVEL 6'), dict(bg='#1c1512', fg='#e3a92b', en='LINK BRIDGE L6')]
remap = {**{i: n0 + i for i in range(8)}, 13: n0 + 8, 17: n0 + 9}
for p in S['place']:
    if p['row'] == 13: p['z'] = math.copysign(17.74, p['z']); p['ry'] = 0 if p['z'] < 0 else math.pi   # LEVEL 5 moves from the grille to the back wall
for p in list(S['place']):
    q = dict(p); q['y'] = round(p['y'] + UP, 3); q['row'] = remap.get(p['row'], p['row']); q.pop('mrow', None); S['place'].append(q)

# nav: upper corridor and bridge nodes are copies with a u prefix, joined to the lower floor through the four stairs
UPN = {'h1', 'h2', 'cF1', 'cB1', 'cF2', 'cB2', 'cF3', 'cB3', 'cF4', 'cB4', 'c5', 'c6', 'bA', 'bW', 'bE', 'bWm', 'bEm', 'B'}
base = lambda i: i.rstrip("'")
nodes = E['nodes'] + [dict(n, id='u' + n['id'], y=UP) for n in E['nodes'] if base(n['id']) in UPN]
links = E['links'] + [['u' + a, 'u' + b, f] for a, b, f in E['links'] if base(a) in UPN and base(b) in UPN]
for s, q in ((-1, ''), (1, "'")):
    def N(i, x, z, y): nodes.append(dict(id=i + q, x=x, z=s * z, y=y, f=''))
    N('sw0', -18.5, 16.75, 0); N('sw1', -24, 16.75, UP); N('ulb', -24, 13, UP)          # west stair: foot, head, upper lobby
    N('se0', 19.5, 10, 0); N('se1', 19.5, 15.5, UP); N('se2', 21.7, 15.5, UP); N('se3', 21.7, 10, UP)   # east stair
    for a, b in [('sp', 'sw0'), ('sw0', 'sw1'), ('sw1', 'ulb'), ('ulb', 'uh1'), ('c5', 'se0'), ('c6', 'se0'), ('se0', 'se1'), ('se1', 'se2'), ('se2', 'se3'), ('se3', 'uc6')]:
        links.append([a + q, b + q, 'stair' if {a, b} in ({'sw0', 'sw1'}, {'se0', 'se1'}) else ''])

X = dict(E, boxes=boxes, props=props, stairs=stairs, signs=S, nodes=nodes, links=links)
X['storeys'] = [0, UP]
X['notes'] = 'Two storeys. Zones, spawns, pickups, hazards, holds and chokes are unchanged and all on the lower floor. Props may carry y (desk, bin, plant too).'

def solids(X):
    """Port of mapSolids(X, R=true) from ref/chope.html, plus prop y."""
    out = []
    def ab(x, z, w, d, ry, y0, h, f=''):
        c, s = abs(math.cos(ry or 0)), abs(math.sin(ry or 0)); W, D = w * c + d * s, w * s + d * c
        out.append([round(v, 4) for v in (x - W / 2, y0, z - D / 2, x + W / 2, y0 + h, z + D / 2)] + [f])
    for x, z, w, d, h, _, y0, f in (b[:8] for b in X['boxes']):
        if 'i' in f or not ('v' in f or 'g' in f): ab(x, z, w, d, 0, y0, h, f)
    for s in X['stairs']:
        n = s['n']; rise = (s['y1'] - s['y0']) / n; ax = s['axis'] == 'x'; ln = s['w'] if ax else s['d']; run = ln / n
        for i in range(n):
            o = -ln / 2 + run * (i + .5) if s['dir'] > 0 else ln / 2 - run * (i + .5)
            ab(s['x'] + o if ax else s['x'], s['z'] if ax else s['z'] + o, run if ax else s['w'], s['d'] if ax else run, 0, 0, s['y0'] + (i + 1) * rise, 'stair')
    P = dict(plant=(.64, .64, .55), bin=(.62, .62, .88))
    for p in X['props']:
        if p['k'] in P and not p.get('vis'): w, d, h = P[p['k']]; ab(p['x'], p['z'], w, d, 0, p.get('y', 0), h)
    return out

if __name__ == '__main__':
    sol = solids(X)
    json.dump(X, open(os.path.join(L, 'classroom2_expanded.json'), 'w'), separators=(',', ':'))
    json.dump(sol, open(os.path.join(L, 'classroom2_solids.json'), 'w'), separators=(',', ':'))
    # self-check: the port reproduces the old solids file from the old expanded map, and the new map is z-symmetric
    old = json.load(open(os.path.join(L, 'classroom_solids.json'))); mine = solids(dict(E, stairs=[]))
    key = lambda s: tuple(round(v, 2) for v in s[:6])
    assert all(max(abs(p - q) for p, q in zip(a, b)) < .011 for a, b in zip(sorted(map(key, old)), sorted(map(key, mine)))), 'solids port differs from mapSolids'
    mk = lambda s: (round(s[0], 2), round(s[1], 2), round(-s[5], 2), round(s[3], 2), round(s[4], 2), round(-s[2], 2))
    asym = [s for s in sol if 'x' not in s[6] and mk(s) not in set(map(key, sol))]
    assert not asym, asym[:5]
    print('boxes', len(boxes), 'props', len(props), 'solids', len(sol), 'nodes', len(nodes), 'links', len(links))
