"""Draws every collider of layouts/classroom_solids_v4.json over the two plan renders from classroom.py and writes shots/maps_toy/classroom/topdown_check.png.
Top panel: level 1 (camera cut at y 3.15). Bottom panel: level 2 (cut at y 6.65). Red = collider, blue = floor slab or roof piece, yellow = stair step.
Then marks zones, spawns and the main routes on it and on topdown_check_v3.png (the v3 plan, ortho 52) and writes topdown_compare.png, old left, new right."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..')); sys.path.insert(0, HERE)
import classroom_layout4 as L4
TMP = '/tmp/lunchliao-scratch'
SHOTS = os.path.join(ROOT, 'shots', 'maps_toy', 'classroom')
S = json.load(open(os.path.join(HERE, 'layouts', 'classroom_solids_v4.json')))
W, H = 1600, 1150
FONT = ImageFont.truetype(os.path.join(ROOT, 'assets/fonts/NotoSansSC-Black.otf'), 30)

def plan(scale):
    return lambda x, z: (W / 2 + x * scale, H / 2 + z * scale)

def colliders():
    px = plan(1600 / 66); out = Image.new('RGB', (W, H * 2))
    for i, (lo, hi) in enumerate(((-.1, 3.15), (3.19, 7.0))):
        im = Image.open(os.path.join(TMP, 'classroom_top%d.png' % (i + 1))).convert('RGB'); d = ImageDraw.Draw(im); n = 0
        for x0, y0, z0, x1, y1, z1, f in S:
            if not (lo <= y0 < hi): continue
            col = '#ffd400' if f == 'stair' else '#2a5cff' if 'r' in f else '#ff1010'
            d.rectangle([px(x0, z0), px(x1, z1)], outline=col, width=1 if col != '#ff1010' else 2); n += 1
        d.text((12, 10), 'LEVEL %d  colliders drawn: %d' % (i + 1, n), fill='#ffffff')
        out.paste(im, (0, H * i))
    out.save(os.path.join(SHOTS, 'topdown_check.png'))

# routes in v3 plan coordinates, (x, z, level). Mapped with fx, fz for v4. North half, mirrored for team 2.
ROUTES = [('#ff8a00', [(-21, -13.25, 1), (-21, -7.75, 1), (16.5, -7.75, 1), (19.5, -4, 1), (19.5, 0, 1)]),            # spawn, level 1 corridor, bridge to B
          ('#00c8ff', [(-21, -13.25, 1), (-18.9, -16.75, 1), (-22.5, -16.75, 2), (-23, -7.75, 2), (-0.1, -7.75, 2), (-0.1, -10.5, 2), (2.5, -14.35, 2)]),  # west stair up, level 2 corridor, front door, A
          ('#b4ff00', [(16.5, -7.75, 1), (17.2, -16.75, 1), (20, -16.75, 1), (20, -14.75, 1), (17.2, -14.75, 2), (16.5, -7.75, 2), (5.1, -7.75, 2), (5.1, -10.5, 2), (2.5, -14.35, 2)])]  # east stair up, back door, A

OLD_ROUTES = [ROUTES[0], ('#00c8ff', [(-21, -13.25, 1), (-21, -7.75, 1), (-0.1, -7.75, 1), (-0.1, -10.5, 1), (2.5, -14.35, 1)])]   # v3: A is on level 1

def marks(im, scale, remap, m2, label):
    d = ImageDraw.Draw(im); px = plan(scale); f = (lambda x, z: (L4.fx(x), L4.fz(z))) if remap else (lambda x, z: (x, z))
    for panel in (1, 2):
        oy = H * (panel - 1); P = lambda x, z: (px(x, z)[0], px(x, z)[1] + oy)
        for col, pts in (ROUTES if remap else OLD_ROUTES):
            for s in (1, -1):
                seg = [P(*f(x, z * s)) for x, z, lv in pts if lv == panel]
                if len(seg) > 1: d.line(seg, fill=col, width=5)
        for z in m2['zones']:
            if (z.get('y', 0) > 1) != (panel == 2): continue
            c = P(z['x'], z['z']); r = z['r'] * scale
            d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline='#ffffff', width=5); d.text((c[0] - 10, c[1] - 18), z['id'], fill='#ffffff', font=FONT)
        if panel == 1:
            for s in m2['spawns']:
                a = P(s['x'] - s['w'] / 2, s['z'] - s['d'] / 2); b = P(s['x'] + s['w'] / 2, s['z'] + s['d'] / 2)
                d.rectangle([a, b], outline='#ff3df5', width=5); d.text((a[0] + 6, a[1] + 4), 'T%d' % s['team'], fill='#ff3df5', font=FONT)
        d.text((W - 520, oy + 12), '%s  LEVEL %d' % (label, panel), fill='#ffffff', font=FONT)
    return im

def compare():
    old = json.load(open(os.path.join(HERE, 'layouts', 'classroom.json'))); new = json.load(open(os.path.join(HERE, 'layouts', 'classroom_map2_v4.json')))
    a = marks(Image.open(os.path.join(SHOTS, 'topdown_check_v3.png')).convert('RGB'), 1600 / 52, False, old, 'OLD v3 49 x 35.5 m')
    b = marks(Image.open(os.path.join(SHOTS, 'topdown_check.png')).convert('RGB'), 1600 / 66, True, new, 'NEW v4 59.8 x 45.7 m')
    out = Image.new('RGB', (W * 2 + 20, H * 2), '#ffffff'); out.paste(a, (0, 0)); out.paste(b, (W + 20, 0))
    out.save(os.path.join(SHOTS, 'topdown_compare.png'))

if __name__ == '__main__':
    if 'compare' not in sys.argv: colliders()
    compare()
