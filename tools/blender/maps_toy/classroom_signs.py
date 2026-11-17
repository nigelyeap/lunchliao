"""Sign atlas for the classroom map. Run with system python (Pillow): python3 tools/blender/maps_toy/classroom_signs.py
English and pictograms only: neither the map JSON signs block nor tools/signs/WORDING.md has school wording in Chinese, Malay or Tamil.
Class plates are digits and letters only. Writes assets/maps/classroom_tex/signs.png and signs.json (name -> uv rect)."""
import json, os, math
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = os.path.join(ROOT, 'assets/maps/classroom_tex'); os.makedirs(OUT, exist_ok=True)
FONT = os.path.join(ROOT, 'assets/fonts/NotoSansSC-Black.otf')
GREEN, CREAM, RED, INK = '#1f5a43', '#fbf8ee', '#c8221b', '#22201c'
N = 2048
im = Image.new('RGB', (N, N), '#808080'); d = ImageDraw.Draw(im); uv = {}; cur = [0, 0, 0]

def cell(name, w, h):
    if cur[0] + w > N: cur[0] = 0; cur[1] += cur[2]; cur[2] = 0
    x, y = cur[0], cur[1]; cur[0] += w; cur[2] = max(cur[2], h)
    uv[name] = [x / N, 1 - (y + h) / N, (x + w) / N, 1 - y / N]; return x, y

def fit(txt, maxw, maxh):
    s = int(maxh)
    while s > 8:
        f = ImageFont.truetype(FONT, s); b = d.textbbox((0, 0), txt, font=f)
        if b[2] - b[0] <= maxw and b[3] - b[1] <= maxh: break
        s -= 2
    return f, b

def icon(kind, x, y, s, fg):
    if kind == 'stair':
        pts = [(x, y + s)]
        for i in range(4): pts += [(x + s * i / 4, y + s - s * (i + 1) / 4), (x + s * (i + 1) / 4, y + s - s * (i + 1) / 4)]
        d.polygon(pts + [(x + s, y + s)], fill=fg)
    elif kind in ('right', 'left'):
        a = [(x, y + s * .38), (x + s * .55, y + s * .38), (x + s * .55, y + s * .12), (x + s, y + s * .5), (x + s * .55, y + s * .88), (x + s * .55, y + s * .62), (x, y + s * .62)]
        d.polygon([(2 * x + s - px, py) for px, py in a] if kind == 'left' else a, fill=fg)
    elif kind in ('boy', 'girl'):
        d.ellipse([x + s * .38, y, x + s * .62, y + s * .24], fill=fg)
        if kind == 'boy': d.rectangle([x + s * .3, y + s * .28, x + s * .7, y + s * .62], fill=fg)
        else: d.polygon([(x + s * .5, y + s * .24), (x + s * .16, y + s * .72), (x + s * .84, y + s * .72)], fill=fg)
        for a in (.36, .54): d.rectangle([x + s * a, y + s * .6, x + s * (a + .1), y + s], fill=fg)
    elif kind == 'norun':                                     # running figure in a red ring with a slash
        d.ellipse([x, y, x + s, y + s], fill=CREAM, outline=RED, width=int(s * .11)); c = INK; w = int(s * .075)
        d.ellipse([x + s * .5, y + s * .2, x + s * .64, y + s * .34], fill=c)
        for a, b in (((.52, .38), (.45, .6)), ((.52, .4), (.34, .46)), ((.52, .4), (.68, .5)), ((.45, .6), (.6, .72)), ((.6, .72), (.56, .84)), ((.45, .6), (.3, .7)), ((.3, .7), (.22, .62))):
            d.line([x + s * a[0], y + s * a[1], x + s * b[0], y + s * b[1]], fill=c, width=w)
        d.line([x + s * .2, y + s * .2, x + s * .8, y + s * .8], fill=RED, width=int(s * .1))

def sign(name, txt, w, h, bg=GREEN, fg=CREAM, ic=None, border=True):
    x, y = cell(name, w, h); pad = int(h * .1)
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=fg if border else bg)
    d.rounded_rectangle([x + pad // 2, y + pad // 2, x + w - 1 - pad // 2, y + h - 1 - pad // 2], radius=pad, fill=bg)
    tx0 = x + pad * 2; s = h - pad * 3
    if ic: icon(ic, tx0, y + (h - s) // 2, s, fg); tx0 += s + pad
    tw = x + w - pad * 2 - tx0; f, b = fit(txt, tw, h * .52)
    d.text((tx0 + tw / 2 - (b[0] + b[2]) / 2, y + h / 2 - (b[1] + b[3]) / 2), txt, font=f, fill=fg)

for p in ('3E', '4E', '3N', '4N'):
    for i in range(1, 5): sign(p + str(i), p + str(i), 384, 128, bg=CREAM, fg=GREEN)
sign('norun', 'NO RUNNING ALONG CORRIDOR', 1024, 160, bg=RED, ic='norun')
sign('stair1', 'STAIRCASE 1', 640, 160, ic='stair'); sign('stair2', 'STAIRCASE 2', 640, 160, ic='stair')
sign('lvl5', 'LEVEL 5', 512, 160, bg=INK); sign('lvl6', 'LEVEL 6', 512, 160, bg=INK)
sign('bridgeR', 'LINK BRIDGE', 768, 160, ic='right'); sign('bridgeL', 'LINK BRIDGE', 768, 160, ic='left')
sign('boys', 'BOYS', 512, 224, bg='#2f6fa8', ic='boy'); sign('girls', 'GIRLS', 512, 224, bg='#c94f7c', ic='girl')
sign('keepleft', 'KEEP LEFT', 512, 160, bg='#e3a92b', fg=INK)

# Singapore flag, 3:2
x, y = cell('flag', 384, 256); d.rectangle([x, y, x + 383, y + 127], fill='#d8232a'); d.rectangle([x, y + 128, x + 383, y + 255], fill='#ffffff')
cx, cy, r = x + 70, y + 64, 44
d.ellipse([cx - r, cy - r, cx + r, cy + r], fill='#ffffff'); d.ellipse([cx - r + 16, cy - r, cx + r + 16, cy + r], fill='#d8232a')
for k in range(5):
    a = -math.pi / 2 + k * 2 * math.pi / 5; sx, sy = cx + 62 + 26 * math.cos(a), cy + 26 * math.sin(a)
    d.polygon([(sx + (9 if j % 2 == 0 else 3.6) * math.cos(-math.pi / 2 + j * math.pi / 5), sy + (9 if j % 2 == 0 else 3.6) * math.sin(-math.pi / 2 + j * math.pi / 5)) for j in range(10)], fill='#ffffff')

# green chalkboard with chalk shapes only, no words
x, y = cell('board', 1408, 384); d.rectangle([x, y, x + 1407, y + 383], fill='#2f5b47'); ch = '#e9efe6'
for i in range(4): d.line([(x + 70 + j * 12, y + 70 + i * 46 + 5 * math.sin(j * .9 + i)) for j in range(34 - i * 5)], fill=ch, width=5)
d.polygon([(x + 640, y + 300), (x + 860, y + 300), (x + 860, y + 110)], outline=ch, width=6); d.rectangle([x + 832, y + 272, x + 860, y + 300], outline=ch, width=4)
d.ellipse([x + 980, y + 90, x + 1180, y + 290], outline=ch, width=6); d.line([x + 1080, y + 190, x + 1180, y + 190], fill=ch, width=5)
d.line([x + 1240, y + 300, x + 1240, y + 80], fill=ch, width=5); d.line([x + 1220, y + 280, x + 1380, y + 280], fill=ch, width=5)
d.line([(x + 1240 + j * 6, y + 280 - (j * .09) ** 2 * 9) for j in range(22)], fill='#f4d35e', width=5)
d.rectangle([x + 70, y + 310, x + 330, y + 350], outline='#f4d35e', width=4)

im.save(os.path.join(OUT, 'signs.png')); json.dump(uv, open(os.path.join(OUT, 'signs.json'), 'w'))
print('signs', len(uv))
