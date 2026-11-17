"""Two-storey classroom colliders (BRIEF Update 3). Reads layouts/classroom_solids_v2.json, writes layouts/classroom_solids_v3.json.
Run: python3 tools/blender/maps_toy/classroom_layout3.py
tagged() returns [(box, kind)] for classroom.py, so every collider gets dressed by what it is.
Level 2 is level 1 lifted 3.5 m. North half (z < 0) is authored, the south half is its z mirror. Boxes with x in the flag span z = 0."""
import json, os
L = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'layouts')
UP = 3.5
RISE, NSTEP = .35, 10                      # 10 x 0.35 = 3.5
W_FOOT, W_RUN = -18.9, .36                 # west stair: one straight 2 m wide flight along the back wall, rising west
E_X0, E_RUN = 17.0, .6                     # east stair: switchback, 5 + 5 steps, flights 2 m wide
W_HOLE = (W_FOOT - NSTEP * W_RUN, -17.75, W_FOOT, -15.75)      # x0, z0, x1, z1
E_HOLE = (E_X0, -17.75, 22.0, -13.75)
RXS = (-17.5, -9.5, -1.5, 6.5)             # west partition of each classroom

def kind_of(b):
    x0, y0, z0, x1, y1, z1, f = b; w, d, h = x1 - x0, z1 - z0, y1 - y0
    if 'r' in f: return 'slab'
    if 'm' in f: return 'win'
    if 'i' in f:
        if abs(h - .72) < .01: return 'desks'
        if abs(h - 1.1) < .01: return 'parapet'
        return 'grille'
    if f == '': return 'bin' if h > .7 else 'plant'
    if y0 > 2: return 'lintel'
    if abs(h - 3.2) < .01: return 'pillar' if (z0 > -6.5 and d < .35 and w < .5) else 'wall'
    if abs(h - 1.6) < .01: return 'placeholder'
    if abs(h - 1.4) < .01: return 'locker'
    if abs(h - .76) < .01: return 'tdesk'
    if abs(h - 1.2) < .01: return 'cabinet' if d > 2 else 'cooler'
    if abs(h - 1.0) < .01: return 'sill' if d < .3 else 'bench'
    raise ValueError(b)

def lift(b): return [b[0], round(b[1] + UP, 4), b[2], b[3], round(b[4] + UP, 4), b[5], b[6]]
def mir(b): return [b[0], b[1], -b[5], b[3], b[4], -b[2], b[6]]

def tagged():
    v2 = json.load(open(os.path.join(L, 'classroom_solids_v2.json')))
    north = [(b, kind_of(b)) for b in v2 if b[5] <= 0 or 'x' in b[6]]
    out = []
    for b, k in north:
        # lobby grille blocks the stair, 1.6 m box was a stand-in for the east stair. The rest is replaced below (Nigel, 2026-11-16)
        if k in ('grille', 'placeholder', 'cooler', 'locker', 'bench', 'desks', 'tdesk'): continue
        if k == 'slab':
            if 'x' in b[6]: out += [(b, 'slab'), (lift(b), 'roof')]          # bridge: level 2 floor and its roof
            else: out.append((lift(b), 'roof'))                              # block roof. Level 2 floor is rebuilt below with stair holes
            continue
        out += [(b, k), (lift(b), k)]
    wx0, wz0, wx1, wz1 = W_HOLE; ex0, ez0, ex1, ez1 = E_HOLE
    for x0, z0, x1, z1 in ((-25, -18, 24.5, -17.75), (-25, -17.75, wx0, wz1), (wx1, -17.75, ex0, wz1), (-25, wz1, ex0, -6),
                           (ex0, ez1, ex1, -6), (ex1, -17.75, 24.5, -6)):
        out.append(([x0, 3.2, z0, x1, 3.5, z1, 'r'], 'slab'))
    for i in range(NSTEP):                                                   # west stair
        out.append(([round(W_FOOT - W_RUN * (i + 1), 4), 0, wz0, round(W_FOOT - W_RUN * i, 4), round(RISE * (i + 1), 4), wz1, 'stair'], 'stair'))
    for i in range(5):                                                       # east stair: flight A rises east, landing, flight B rises west
        out.append(([round(ex0 + E_RUN * i, 4), 0, -17.75, round(ex0 + E_RUN * (i + 1), 4), round(RISE * (i + 1), 4), -15.75, 'stair'], 'stair'))
        out.append(([round(20 - E_RUN * (i + 1), 4), 0, -15.75, round(20 - E_RUN * i, 4), round(1.75 + RISE * (i + 1), 4), -13.75, 'stair'], 'stair'))
    out.append(([20, 0, -17.75, 22, 1.75, -13.75, 'stair'], 'landing'))
    for g in ([wx0, 3.5, wz1, wx1, 4.6, wz1 + .15], [wx1 - .15, 3.5, -17.75, wx1, 4.6, wz1],                       # guards round the stair holes
              [ex0, 3.5, ez1, ex1, 4.6, ez1 + .15], [ex0 - .15, 3.5, -17.75, ex0, 4.6, -15.75]):
        out.append(([round(v, 4) for v in g] + ['s'], 'guard'))
    for y in (0, UP): out.append(([24.25, y, -17.75, 24.5, y + 3.2, -9.5, 's'], 'wall'))        # east end wall, the old core was solid here
    for x0 in (14.5, 24.2): out.append(([x0, 3.5, -3.15, x0 + .3, 6.7, -2.85, 's'], 'post'))    # bridge roof posts
    for y in (0, UP):
        A = lambda b, k, f='s': out.append(([round(v, 4) for v in (b[0], y + b[1], b[2], b[3], y + b[4], b[5])] + [f], k))
        for xr in RXS:
            A([xr + 2.2, 0, -9.5, xr + 5.8, .95, -9.1], 'locker')                    # low locker bank under the louvre window, corridor side
            A([xr + .2, 0, -14.25, xr + .75, .76, -12.95], 'tdesk')                  # teacher desk in front of the board
            for c in range(2):                                                       # 2 x 4 desk and chair units, even gaps: 1.65 m in x, 1.16 m in z
                for r in range(4):                                                   # hero radius is .45 (ref/chope.html), so a gap needs 1.1 m
                    zc = -17.75 + 1.16 + .275 + r * 1.71; x0 = xr + 2.398 + c * 2.538
                    A([x0, 0, zc - .275, x0 + .89, .72, zc + .275], 'desk', 'i')
        # toilet beside the east stair: L-shaped room, doors to the corridor and to the stair hall
        for b in ([17.5, 0, -9.75, 18.0, 3.2, -9.5], [19.4, 0, -9.75, 24.25, 3.2, -9.5], [17.5, 0, -13.6, 17.65, 3.2, -9.75],
                  [17.65, 0, -13.6, 22.15, 3.2, -13.45], [22, 0, -17.75, 22.15, 3.2, -13.6]): A(b, 'wall')
        A([18.0, 2.1, -9.75, 19.4, 3.2, -9.5], 'lintel')                             # one door, on the corridor
        A([17.65, 0, -11.3, 20.2, 3.2, -11.15], 'screen'); A([21.4, 0, -11.3, 21.55, 3.2, -9.75], 'screen')   # privacy lobby: in, turn east, through a 1.2 m slot
        A([22.15, 0, -17.75, 24.25, 2.0, -16.55], 'cubicles'); A([23.7, 0, -12.5, 24.25, 1.0, -9.9], 'sinks'); A([17.9, 0, -13.45, 20.3, 1.2, -13.1], 'urinals')   # both out of every sight line through the door
        A([20.5, 0, -9.5, 21.1, 1.3, -9.05], 'cooler')                               # steel water cooler outside the toilet
    out.append(([19.3, 0, -4.5, 19.7, .45, -2.7, 's'], 'pbench'))                    # one more bench each side of the picnic set (mirrored)
    for b, k in (([19.05, 0, -.9, 19.95, .75, .9, 'sx'], 'ptable'), ([18.25, 0, -.9, 18.65, .45, .9, 'sx'], 'pbench'), ([20.35, 0, -.9, 20.75, .45, .9, 'sx'], 'pbench')):
        out.append((b, k))                                                           # one wooden picnic set on the level 1 bridge
    full = []
    for b, k in out:
        full.append((b, k))
        if 'x' not in b[6]: full.append((mir(b), k))
    return full

if __name__ == '__main__':
    T = tagged(); S = [b for b, _ in T]
    json.dump(S, open(os.path.join(L, 'classroom_solids_v3.json'), 'w'))
    key = lambda b: tuple(round(v, 3) for v in b[:6])
    have = set(map(key, S)); v2 = json.load(open(os.path.join(L, 'classroom_solids_v2.json')))
    gone = [b for b in v2 if key(b) not in have]
    assert all(key(mir(b)) in have for b in S), 'not z-mirrored'
    units = [b for b in S if b[6] == 'i' and abs(b[4] - b[1] - .72) < .01]      # every desk unit keeps 1.1 m clear of every other collider on its floor
    for u in units:
        for o in S:
            if o is u or 'r' in o[6] or o[4] <= u[1] or o[1] >= u[4]: continue
            gap = max(o[0] - u[3], u[0] - o[3], o[2] - u[5], u[2] - o[5])
            assert gap >= 1.1, (u, o, gap)
    print('desk units', len(units))
    assert max(b[4] - b[1] for b in S if b[6] == 'stair' and b[4] <= .36) <= .4
    print('v3 solids', len(S), 'removed from v2', len(gone))
