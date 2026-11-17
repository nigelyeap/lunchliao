"""Hawker v3 colliders: v2 minus the scattered tables, plus dense tidy table rows. Run with system python3 (PIL).
  python3 tools/blender/maps_toy/hawker_tables.py [plan.jpg]
Writes layouts/hawker_solids_v3.json. Every new box is flagged 's' and has its point-mirror twin (x,z) -> (-x,-z).
A table set is the old 1.5 x 1.5 x 0.86 table plus four 0.48 stools, two on each facing side at (+-0.4, +-0.88), footprint 1.5 x 2.24.
Zone tables keep their table but get the same facing stools (Nigel 2026-11-16: no diagonal stools)."""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); LAY = os.path.join(HERE, 'layouts')
S2 = json.load(open(os.path.join(LAY, 'hawker_solids_v2.json'))); X = json.load(open(os.path.join(LAY, 'hawker_expanded.json')))
dims = lambda s: (round(s[3] - s[0], 2), round(s[5] - s[2], 2), round(s[4] - s[1], 2))
cen = lambda s: ((s[0] + s[3]) / 2, (s[2] + s[5]) / 2)
ZONES = [(q['x'], q['z'], q['r']) for q in X['zones']]
LANE = 1.5          # min free gap between a new set and anything else
SERVE = 2.4         # queue space in front of stall counters, islands and tray returns
PITCH = 3.8         # 3.8 m pitch: table edges 2.3 m apart, stool to stool 1.56 m
NAV = False

is_table = lambda s: dims(s) == (1.5, 1.5, .86)
is_stool = lambda s: dims(s) == (.48, .48, .44)
zone_tab = lambda c: any(abs(c[0] - zx) < .01 and abs(c[1] - zz) < .01 for zx, zz, _ in ZONES)
old_tabs = [cen(s) for s in S2 if is_table(s) and not zone_tab(cen(s))]
all_tabs = [cen(s) for s in S2 if is_table(s)]
def stool_of_old(s):
    c = cen(s); return any(abs(abs(c[0] - tx) - .88) < .01 and abs(abs(c[1] - tz) - .88) < .01 for tx, tz in all_tabs)
zone_tabs = [c for c in all_tabs if zone_tab(c)]
# four free-standing tray racks (and mirrors) that sit in the middle of seating rows. The racks that flank zones A and C stay.
RACK_RM = [[-26.4, 0, -12.8, -25.6, 2, -10.2], [-5.4, 0, -18.3, -4.6, 2, -15.7], [25.6, 0, -16.3, 26.4, 2, -13.7], [8.6, 0, -14.3, 9.4, 2, -11.7]]
RACK_RM += [[-r[3], r[1], -r[5], -r[0], r[4], -r[2]] for r in RACK_RM]
key6 = lambda s: [round(v, 2) + 0.0 for v in s[:6]]
REMOVED = [s for s in S2 if (is_table(s) and not zone_tab(cen(s))) or (is_stool(s) and stool_of_old(s)) or key6(s) in [key6(r) for r in RACK_RM]]
KEEP = [s for s in S2 if s not in REMOVED]
BLOCK = [s for s in KEEP if s[1] < 2.2 and (len(s) < 7 or s[6] not in ('i', 'rider', 'v', 'g'))]
SERV = [s for s in BLOCK if dims(s) in ((6.6, 2.0, 1.1), (10.0, 4.0, 2.6), (2.0, 1.5, 1.1))]

def rgap(a, b):
    """Euclidean gap between two xz rectangles (x0,z0,x1,z1)."""
    dx = max(a[0] - b[2], b[0] - a[2], 0); dz = max(a[1] - b[3], b[1] - a[3], 0); return math.hypot(dx, dz)
R = lambda s: (s[0], s[2], s[3], s[5])
def seg_rect(p, q, r, buf):
    """True if segment pq comes within buf of rect r (sampled)."""
    n = max(2, int(math.hypot(q[0] - p[0], q[1] - p[1]) / .25))
    for i in range(n + 1):
        t = i / n; x, z = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        if r[0] - buf < x < r[2] + buf and r[1] - buf < z < r[3] + buf: return True
    return False
NODES = {n['id']: (n['x'], n['z']) for n in X['nodes']}
LINKS = [(NODES[a], NODES[b]) for a, b, _ in X['links'] if not (a.startswith('L') or b.startswith('L'))]

def ok(x, z):
    f = (x - 1.12, z - 1.12, x + 1.12, z + 1.12)
    if not (-31.0 < f[0] and f[2] < 31.0 and -18.0 < f[1] and f[3] < 18.0): return False   # hall: clear of spawn plaza and queues
    if abs(z) < 3.7: return False                                   # z=0 lane from the spawns to B
    for zx, zz, zr in ZONES:
        if rgap(f, (zx, zz, zx, zz)) < zr + LANE: return False      # zones stay clear
    for p in X['pickups']:
        if rgap(f, (p['x'], p['z'], p['x'], p['z'])) < 2.5: return False
    if any(rgap(f, R(s)) < LANE for s in BLOCK): return False
    if any(rgap(f, R(s)) < SERVE for s in SERV): return False
    if NAV and any(seg_rect(p, q, f, .5) for p, q in LINKS): return False   # keep the nav routes open
    return True

def rows(oz):
    """Rows at fixed z (pitch PITCH) in the z<0 half, each packed greedily along x. Point mirror makes z>0."""
    out = []
    for j in range(8):
        z = round(-oz - j * PITCH, 2); x = -31.0; last = -99
        while x < 31.0:
            if x - last >= PITCH - 1e-6 and ok(x, z): out.append((round(x, 2), z)); last = x
            x = round(x + .1, 2)
    return out

def search():
    best = None
    for b in range(39):
        g = rows(4.82 + b * .1)
        if not best or len(g) > len(best[0]): best = (g, 0, 4.82 + b * .1)
    return best

def setboxes(x, z, table=True):
    bs = [[x - .75, 0, z - .75, x + .75, .86, z + .75, 's']] if table else []
    for dx in (-.4, .4):
        for dz in (-.88, .88): bs.append([round(x + dx - .24, 3), 0, round(z + dz - .24, 3), round(x + dx + .24, 3), .44, round(z + dz + .24, 3), 's'])
    return [[round(v, 3) if isinstance(v, float) else v for v in b] for b in bs]

if __name__ == '__main__':
    sets, ox, oz = search()
    centres = sets + [(-x, -z) for x, z in sets]
    NEW = [b for c in centres for b in setboxes(*c)] + [b for c in zone_tabs for b in setboxes(*c, table=False)]
    S3 = KEEP + NEW
    json.dump(S3, open(os.path.join(LAY, 'hawker_solids_v3.json'), 'w'))
    # checks: mirror, min gap between each new set and everything that is not its own set
    keyset = {tuple(round(v, 2) for v in b[:6]) for b in S3}
    mir = all(tuple(round(v, 2) + 0.0 for v in (-b[3], b[1], -b[5], -b[0], b[4], -b[2])) in keyset for b in NEW)
    gaps = []
    for c in centres:
        f = (c[0] - 1.12, c[1] - 1.12, c[0] + 1.12, c[1] + 1.12)
        others = [R(s) for s in BLOCK] + [(d[0] - 1.12, d[1] - 1.12, d[0] + 1.12, d[1] + 1.12) for d in centres if d != c]
        gaps.append(min(rgap(f, o) for o in others))
    ntab = lambda S: sum(is_table(s) for s in S)
    print('grid offset', ox, oz, 'sets per half', len(sets))
    print('tables v2', ntab(S2), 'v3', ntab(S3), '| removed boxes', len(REMOVED), 'new boxes', len(NEW), '| v3 boxes', len(S3))
    print('mirror ok', mir, '| narrowest gap around a new set %.2f m' % min(gaps))
    assert mir and min(gaps) >= LANE - 1e-6
    if len(sys.argv) > 1:
        from PIL import Image, ImageDraw
        sc = 16; W, H = int(94 * sc), int(64 * sc); P = lambda x, z: ((x + 47) * sc, (z + 32) * sc)
        im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
        for s in KEEP:
            if len(s) > 6 and s[6] in ('i', 'rider'): continue
            d.rectangle([*P(s[0], s[2]), *P(s[3], s[5])], fill=(205, 205, 205), outline=(110, 110, 110))
        for s in NEW: d.rectangle([*P(s[0], s[2]), *P(s[3], s[5])], fill=(235, 40, 200), outline=(140, 0, 110))
        for s in REMOVED:
            (a, b), (c, e) = P(s[0], s[2]), P(s[3], s[5]); d.line([a, b, c, e], fill='red', width=3); d.line([a, e, c, b], fill='red', width=3)
        for zx, zz, zr in ZONES: d.ellipse([*P(zx - zr, zz - zr), *P(zx + zr, zz + zr)], outline=(0, 140, 0), width=3)
        for p in X['pickups']: d.ellipse([*P(p['x'] - .6, p['z'] - .6), *P(p['x'] + .6, p['z'] + .6)], fill=(0, 160, 255))
        for sp in X['spawns']: d.rectangle([*P(sp['x'] - sp['w'] / 2, sp['z'] - sp['d'] / 2), *P(sp['x'] + sp['w'] / 2, sp['z'] + sp['d'] / 2)], outline=(0, 0, 255), width=3)
        d.text((10, 6), 'hawker v3: grey kept, magenta new table sets (%d tables), red X removed. z down. tables v2 %d -> v3 %d' % (ntab(NEW), ntab(S2), ntab(S3)), fill='black')
        im.save(sys.argv[1], quality=85)
