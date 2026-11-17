"""Textures for the toy wet market. Run with system python3 (needs PIL): python3 wetmarket_tex.py <outdir>
Writes signs.png (2048 atlas, 1024x256 cells, 2 columns: 13 stall boards, then 12 square stall number plates),
nosmoke.png (four languages, wording from tools/signs/WORDING.md, shaped by headless Chrome so Tamil is correct)
and small clean tile prints. Stall board wording comes from the map JSON only (English and Malay). Pictograms carry the rest."""
import sys, os, json, math, subprocess, pathlib
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'assets', 'maps', 'wetmarket_tex')
os.makedirs(OUT, exist_ok=True)
FONTS = os.path.join(ROOT, 'assets', 'fonts')
FONT = os.path.join(FONTS, 'NotoSansSC-Black.otf')
FONT2 = os.path.join(FONTS, 'NotoSansSC-Bold.otf')
INK, BOARD = '#22303a', '#fbf8ee'
ICON = ['basket', 'fish', 'leaf', 'chicken', 'tofu', 'chilli', 'warn', 'cup', 'flower', 'box', 'drop', 'sack', 'fish']
UNIT = [1, 12, 27, 38, 45, 53, 0, 66, 71, 0, 0, 84, 96]          # stall unit numbers, "#01-xx" (ground floor) style


def fit(d, text, path, maxw, maxh):
    s = maxh
    while s > 8:
        f = ImageFont.truetype(path, s); b = d.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= maxw and b[3] - b[1] <= maxh: return f, b
        s -= 2
    return f, b


def icon(d, k, cx, cy, r, c):
    """flat one-colour pictogram inside radius r"""
    P = lambda pts: d.polygon([(cx + x * r, cy + y * r) for x, y in pts], fill=c)
    E = lambda x0, y0, x1, y1, col=c: d.ellipse([cx + x0 * r, cy + y0 * r, cx + x1 * r, cy + y1 * r], fill=col)
    R = lambda x0, y0, x1, y1, rad=.1: d.rounded_rectangle([cx + x0 * r, cy + y0 * r, cx + x1 * r, cy + y1 * r], radius=rad * r, fill=c)
    if k == 'fish': E(-.75, -.42, .45, .42); P([(.3, 0), (.85, -.45), (.85, .45)])
    elif k == 'leaf': P([(-.7, .6), (-.5, -.3), (.1, -.7), (.75, -.7), (.7, 0), (.3, .5), (-.4, .65)]); d.line([cx - .75 * r, cy + .8 * r, cx - .5 * r, cy + .45 * r], fill=c, width=int(r * .12))
    elif k == 'chicken': E(-.75, -.75, .3, .3); P([(-.1, 0), (.1, -.2), (.7, .45), (.5, .65)]); E(.42, .35, .8, .7); E(.3, .5, .65, .85)
    elif k == 'tofu': P([(-.7, -.25), (0, -.6), (.7, -.25), (0, .1)]); P([(-.7, -.13), (-.06, .2), (-.06, .75), (-.7, .4)]); P([(.7, -.13), (.06, .2), (.06, .75), (.7, .4)])
    elif k == 'chilli': P([(-.8, .55), (-.3, .2), (.2, -.35), (.55, -.5), (.7, -.3), (.45, .15), (-.1, .55), (-.6, .7)]); d.line([cx + .6 * r, cy - .4 * r, cx + .82 * r, cy - .75 * r], fill=c, width=int(r * .14))
    elif k == 'warn': P([(0, -.8), (.85, .65), (-.85, .65)])
    elif k == 'cup': R(-.6, -.35, .35, .6, .2); d.arc([cx + .15 * r, cy - .2 * r, cx + .8 * r, cy + .4 * r], -90, 90, fill=c, width=int(r * .14)); R(-.75, .62, .5, .76, .05)
    elif k == 'flower':
        for i in range(5):
            a = i * 2 * math.pi / 5 - math.pi / 2; E(.45 * math.cos(a) - .32, .45 * math.sin(a) - .32, .45 * math.cos(a) + .32, .45 * math.sin(a) + .32)
    elif k == 'box': R(-.8, -.4, .2, .4, .08); P([(.26, -.15), (.6, -.15), (.82, .1), (.82, .4), (.26, .4)]); E(-.6, .25, -.2, .65); E(.35, .25, .75, .65)
    elif k == 'drop': P([(0, -.85), (.5, 0), (-.5, 0)]); E(-.55, -.25, .55, .8)
    elif k == 'sack': P([(-.35, -.75), (.35, -.75), (.2, -.45), (-.2, -.45)]); R(-.65, -.4, .65, .78, .35)
    elif k == 'basket': P([(-.8, -.1), (.8, -.1), (.6, .7), (-.6, .7)]); d.arc([cx - .55 * r, cy - .8 * r, cx + .55 * r, cy + .5 * r], 180, 360, fill=c, width=int(r * .14))


def signs():
    """REF 8: every stall is a numbered unit. One board style: white board, colour block with pictogram and unit number."""
    rows = json.load(open(os.path.join(HERE, 'layouts', 'wetmarket_expanded.json')))['signs']['rows']
    S = 2; W, H = 1024 * S, 256 * S
    im = Image.new('RGB', (2048 * S, 2048 * S), '#808080'); d = ImageDraw.Draw(im)
    for i, r in enumerate(rows):
        x0, y0 = (i % 2) * W, (i // 2) * H; acc = r['bg']; warn = ICON[i] == 'warn'
        d.rectangle([x0, y0, x0 + W, y0 + H], fill=acc if warn else '#f6c544')       # Update 5: yellow boards
        bw = 250 * S
        d.rectangle([x0, y0, x0 + bw, y0 + H], fill=INK if warn else acc)
        d.rectangle([x0, y0 + H - 14 * S, x0 + W, y0 + H], fill=INK if warn else acc)
        lite = INK if (acc.lower() in ('#e3c46a', '#f3ecd9') and not warn) else ('#e3c46a' if warn else BOARD)
        if acc.lower() == '#f3ecd9' and not warn: d.rectangle([x0, y0, x0 + bw, y0 + H], fill='#9aa6ad'); d.rectangle([x0, y0 + H - 14 * S, x0 + W, y0 + H], fill='#9aa6ad'); lite = BOARD
        cy = y0 + (98 if UNIT[i] else 122) * S
        icon(d, ICON[i], x0 + bw / 2, cy, (72 if UNIT[i] else 88) * S, lite)
        if warn: f = ImageFont.truetype(FONT, 90 * S); d.text((x0 + bw / 2, cy + 22 * S), '!', font=f, fill=INK, anchor='mm')
        if UNIT[i]:
            f = ImageFont.truetype(FONT, 46 * S); d.text((x0 + bw / 2, y0 + 206 * S), '#01-%02d' % UNIT[i], font=f, fill=lite, anchor='mm')
        tx, tw = x0 + bw + 30 * S, W - bw - 60 * S
        f, b = fit(d, r['en'], FONT, tw, 96 * S)
        d.text((tx + tw / 2 - (b[0] + b[2]) / 2, y0 + 88 * S - (b[1] + b[3]) / 2), r['en'], font=f, fill=INK)
        f, b = fit(d, r['zh'], FONT2, tw - 80 * S, 50 * S)
        d.text((tx + tw / 2 - (b[0] + b[2]) / 2, y0 + 178 * S - (b[1] + b[3]) / 2), r['zh'], font=f, fill=INK)
    for k in range(12):                                             # stall number plates, 256 px squares in cells 13..15
        c = 13 + k // 4; x0, y0 = (c % 2) * W + (k % 4) * 256 * S, (c // 2) * H; q = 256 * S
        d.rectangle([x0, y0, x0 + q, y0 + q], fill='#d8362f')
        d.rounded_rectangle([x0 + 14 * S, y0 + 14 * S, x0 + q - 14 * S, y0 + q - 14 * S], radius=26 * S, outline=BOARD, width=7 * S)
        f = ImageFont.truetype(FONT2, 44 * S); d.text((x0 + q / 2, y0 + 78 * S), '#01', font=f, fill=BOARD, anchor='mm')
        f = ImageFont.truetype(FONT, 104 * S); d.text((x0 + q / 2, y0 + 160 * S), '%03d' % (101 + k * 7), font=f, fill=BOARD, anchor='mm')
    im.resize((2048, 2048), Image.LANCZOS).save(os.path.join(OUT, 'signs.png'))


def nosmoke():
    """clean four-language no-smoking sign. Text lines copied from tools/signs/WORDING.md (sign_nosmoke)."""
    chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    out = os.path.join(OUT, 'nosmoke.png')
    if not os.path.exists(chrome): print('no Chrome: nosmoke.png not rebuilt'); return
    tmp = os.environ.get('WM_TMP', '/tmp/lunchliao-scratch'); os.makedirs(tmp, exist_ok=True)
    fu = pathlib.Path(FONTS).as_uri()
    html = f"""<!doctype html><meta charset=utf-8><style>
@font-face{{font-family:SC;src:url('{fu}/NotoSansSC-Black.otf')}}@font-face{{font-family:TA;src:url('{fu}/NotoSansTamil-Black.ttf')}}
*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:512px;height:512px;overflow:hidden}}
body{{background:#fbf8ee;border:14px solid #d8362f;border-radius:44px;font-family:SC;color:#22303a;text-align:center}}
.r{{position:relative;width:190px;height:190px;margin:22px auto 6px;border:22px solid #d8362f;border-radius:50%}}
.c{{position:absolute;left:22px;top:60px;width:102px;height:26px;background:#22303a;border-radius:5px}}
.c:after{{content:'';position:absolute;right:-8px;top:0;width:22px;height:26px;background:#ee7b2e;border-radius:0 5px 5px 0}}
.s{{position:absolute;left:-8px;top:62px;width:162px;height:22px;background:#d8362f;transform:rotate(45deg)}}
h1{{font-size:54px;line-height:62px;color:#d8362f}}h2{{font-size:46px;line-height:56px}}h3{{font-size:38px;line-height:50px}}h4{{font-family:TA;font-size:35px;line-height:54px}}
</style><body><div class=r><div class=c></div><div class=s></div></div><h1>NO SMOKING</h1><h2>禁止吸烟</h2><h3>DILARANG MEROKOK</h3><h4>புகைபிடிக்கக் கூடாது</h4>"""
    hp = os.path.join(tmp, 'wm_nosmoke.html'); open(hp, 'w', encoding='utf-8').write(html)
    subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=2', '--window-size=512,512',
                    '--user-data-dir=' + os.path.join(tmp, 'chrome-wm'), '--virtual-time-budget=3000', '--screenshot=' + out, pathlib.Path(hp).as_uri()],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)


def tile(name, base, grout, n=256, g=7, hi=None, k=1):
    """k x k square tiles per repeat: flat colour, a grout line and a soft lighter inner edge"""
    im = Image.new('RGB', (n * 2, n * 2), grout); d = ImageDraw.Draw(im); s = 2 * n / k
    for i in range(k):
        for j in range(k):
            d.rounded_rectangle([i * s + g, j * s + g, (i + 1) * s - g, (j + 1) * s - g], radius=14 / k + 3, fill=hi or base)
            d.rounded_rectangle([i * s + g + 5, j * s + g + 5, (i + 1) * s - g - 5, (j + 1) * s - g - 5], radius=10 / k + 2, fill=base)
    im.resize((n, n), Image.LANCZOS).save(os.path.join(OUT, name))


def stripes(name, a, b, n=256, k=8):
    im = Image.new('RGB', (n, n), a); d = ImageDraw.Draw(im); s = n / k
    for i in range(k): d.rectangle([i * s + s * .5, 0, i * s + s, n], fill=b)
    im.save(os.path.join(OUT, name))


def hazard(name, n=256):
    im = Image.new('RGB', (n, n), '#f2c230'); d = ImageDraw.Draw(im)
    for i in range(-2, 4):
        x = i * n / 2
        d.polygon([(x, n), (x + n / 4, n), (x + n / 4 + n, 0), (x + n, 0)], fill='#2a2a2e')
    im.save(os.path.join(OUT, name))


signs()
nosmoke()
tile('tile_white.png', '#3f93c4', '#2b6f99', hi='#5aa8d4')                 # Update 5: stall tiles are blue (file name kept)
tile('tile_green.png', '#2fa37e', '#1f7d5e', hi='#45b590')
tile('floor.png', '#b8927a', '#8f705c', g=4, hi='#c29d86', k=4)        # REF 2.1: small white mosaic, grey grout
stripes('zinc.png', '#71a89f', '#62958d')
hazard('hazard.png')
print('textures ->', OUT)
