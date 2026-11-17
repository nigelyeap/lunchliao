"""Sign atlas for the carpark map. Run with system python (needs Pillow): python3 tools/blender/maps_toy/carpark_signs.py
Wording comes only from layouts/carpark.json signs.rows (English, plus Malay where the row has it). Everything else is English or a pictogram.
Colours follow carpark_REF.md section 5 (blue parking boards, green way-out boards, maroon and ochre from People's Park).
Writes assets/maps/carpark_tex/signs.png + signs.json (uv rects, keyed by row index or name)."""
import json, os, math
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
J = json.load(open(os.path.join(ROOT, 'tools/blender/maps_toy/layouts/carpark.json')))
F = os.path.join(ROOT, 'assets/fonts/')
rows, place = J['signs']['rows'], J['signs']['place']
N = 2048
FLOOR = '#a68b66'          # must match the 'floor' material in carpark.py so floor decals blend in
BLUE, GREEN, RED, MAROON, OCHRE, CREAM, INK = '#1f5fae', '#2f7d4f', '#c8221b', '#9c2f33', '#e3a224', '#f6f0e0', '#2a2623'
# board colour per row: (bg, fg). Parking info blue, way out green, prohibition red, name board maroon, loading bay ochre.
STYLE = {0: (MAROON, CREAM), 1: (BLUE, CREAM), 2: (GREEN, CREAM), 3: (GREEN, CREAM), 4: (RED, CREAM), 5: (GREEN, CREAM), 6: (BLUE, CREAM),
         7: (BLUE, CREAM), 8: (BLUE, CREAM), 9: (OCHRE, INK), 10: (GREEN, CREAM), 11: (GREEN, CREAM)}
im = Image.new('RGB', (N, N), FLOOR); d = ImageDraw.Draw(im); out = {}

def font(name, s): return ImageFont.truetype(F + name, s)
def fit(txt, name, maxw, maxh):
    s = int(maxh)
    while s > 8:
        f = font(name, s); b = d.textbbox((0, 0), txt, font=f)
        if b[2] - b[0] <= maxw and b[3] - b[1] <= maxh: break
        s -= 2
    return f, b
def text(txt, name, cx, cy, maxw, maxh, fill):
    f, b = fit(txt, name, maxw, maxh); d.text((cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2), txt, font=f, fill=fill)
def rect(key, x0, y0, w, h): out[key] = [x0 / N, 1 - (y0 + h) / N, (x0 + w) / N, 1 - y0 / N]

# ---- wording rows, 1024 x 256 cells, two columns
for i, r in enumerate(rows):
    asp = next((p['w'] / p['h'] for p in place if p['row'] == i or p.get('mrow') == i), 4)
    w, h = 1024, min(256, int(1024 / asp)); x0, y0 = (i % 2) * 1024, (i // 2) * 256; bg, fg = STYLE[i]; pad = int(h * .09)
    d.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=fg)
    d.rounded_rectangle([x0 + pad // 2, y0 + pad // 2, x0 + w - 1 - pad // 2, y0 + h - 1 - pad // 2], radius=pad * 2, fill=bg)
    ms = r['zh']                                                # this map's second line is Malay
    if ms:
        text(r['en'], 'NotoSansSC-Black.otf', x0 + w / 2, y0 + h * .36, w - pad * 5, h * .40, fg)
        text(ms, 'NotoSansSC-Bold.otf', x0 + w / 2, y0 + h * .73, w - pad * 5, h * .22, fg)
    else: text(r['en'], 'NotoSansSC-Black.otf', x0 + w / 2, y0 + h / 2, w - pad * 5, h * .5, fg)
    rect(str(i), x0, y0, w, h)

# ---- lot numbers 01..24 (white stencil on floor colour), 128 x 64 tiles
for n in range(24):
    x0, y0 = (n % 8) * 128, 1536 + (n // 8) * 64
    text('%02d' % (n + 1), 'NotoSansSC-Black.otf', x0 + 64, y0 + 32, 110, 46, '#f6f1e4'); rect('lot%d' % (n + 1), x0, y0, 128, 64)

# ---- mural strip 1024 x 128 (pictures only): sun, slab blocks, trees, bowls
x0, y0 = 1024, 1536
d.rectangle([x0, y0, x0 + 1023, y0 + 127], fill='#bfe0e6')
d.ellipse([x0 + 40, y0 + 14, x0 + 130, y0 + 104], fill='#f2c14e')
for k, (bx, bw, bh, c) in enumerate([(170, 90, 96, '#e2b84e'), (270, 60, 70, '#f4c7c3'), (340, 110, 104, '#cfe8d8'), (470, 70, 80, '#c7b5d9'), (640, 100, 100, '#e2b84e'), (750, 70, 64, '#9ec9df'), (900, 100, 90, '#f4c7c3')]):
    d.rectangle([x0 + bx, y0 + 128 - bh, x0 + bx + bw, y0 + 127], fill=c)
    for fy in range(y0 + 128 - bh + 10, y0 + 120, 14): d.rectangle([x0 + bx + 6, fy, x0 + bx + bw - 6, fy + 5], fill='#fbf8f0')
for tx in (150, 455, 560, 610, 840, 1005):
    d.rectangle([x0 + tx - 3, y0 + 88, x0 + tx + 3, y0 + 127], fill='#7a5538'); d.ellipse([x0 + tx - 24, y0 + 52, x0 + tx + 24, y0 + 100], fill='#5aa04a')
d.rectangle([x0, y0 + 120, x0 + 1023, y0 + 127], fill='#8fae8a'); rect('mural', x0, y0, 1024, 128)

# ---- SLOW floor paint 512 x 64 (yellow on floor colour)
text('SLOW', 'NotoSansSC-Black.otf', 1024 + 256, 1664 + 32, 480, 52, '#e8bf3f'); rect('slow', 1024, 1664, 512, 64)

# ---- coupon parking pictogram 256 x 256: blue board, white P, a little coupon with tear tabs
x0, y0 = 0, 1728
d.rectangle([x0, y0, x0 + 255, y0 + 255], fill=CREAM); d.rounded_rectangle([x0 + 10, y0 + 10, x0 + 245, y0 + 245], radius=26, fill=BLUE)
text('P', 'NotoSansSC-Black.otf', x0 + 92, y0 + 104, 150, 170, CREAM)
d.rounded_rectangle([x0 + 150, y0 + 52, x0 + 226, y0 + 150], radius=6, fill='#f2d27c')
for ty in range(62, 146, 14): d.ellipse([x0 + 158, y0 + ty, x0 + 166, y0 + ty + 8], fill=BLUE); d.rectangle([x0 + 174, y0 + ty + 2, x0 + 216, y0 + ty + 6], fill=BLUE)
text('COUPON', 'NotoSansSC-Black.otf', x0 + 128, y0 + 204, 200, 40, CREAM); rect('coupon', x0, y0, 256, 256)

# ---- level panel 512 x 256: big number on a solid estate colour with a sunflower icon
x0, y0 = 256, 1728
d.rectangle([x0, y0, x0 + 511, y0 + 255], fill=OCHRE)
cx, cy = x0 + 128, y0 + 128
for k in range(12):
    a = k * math.pi / 6; px, py = cx + math.cos(a) * 62, cy + math.sin(a) * 62; d.ellipse([px - 19, py - 19, px + 19, py + 19], fill='#fbf8f0')
d.ellipse([cx - 44, cy - 44, cx + 44, cy + 44], fill='#7a5538')
text('6', 'NotoSansSC-Black.otf', x0 + 372, y0 + 118, 220, 230, MAROON); rect('level', x0, y0, 512, 256)

# ---- block number plates 256 x 128
for k, (num, bg) in enumerate([('335', MAROON), ('334', GREEN), ('336', BLUE)]):
    x0, y0 = 768 + k * 256, 1728
    d.rectangle([x0, y0, x0 + 255, y0 + 127], fill=bg); text(num, 'NotoSansSC-Black.otf', x0 + 128, y0 + 60, 220, 96, CREAM); rect('blk' + num, x0, y0, 256, 128)

# ---- floor decals (lot numbers, SLOW) get alpha so only the paint shows on the deck
from PIL import ImageChops
im = im.convert('RGBA'); fl = Image.new('RGB', (1, 1), FLOOR).getpixel((0, 0))
for k, (u0, v0, u1, v1) in out.items():
    if not (k.startswith('lot') or k == 'slow'): continue
    bx = (round(u0 * N), round((1 - v1) * N), round(u1 * N), round((1 - v0) * N)); t = im.crop(bx)
    df = ImageChops.difference(t.convert('RGB'), Image.new('RGB', t.size, fl)); r, g, b = df.split()
    t.putalpha(ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda v: min(255, v * 5))); im.paste(t, bx)
os.makedirs(os.path.join(ROOT, 'assets/maps/carpark_tex'), exist_ok=True)
im.save(os.path.join(ROOT, 'assets/maps/carpark_tex/signs.png')); json.dump(out, open(os.path.join(ROOT, 'assets/maps/carpark_tex/signs.json'), 'w'))
print('signs ok', len(out))
