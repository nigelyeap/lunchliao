"""Sign and print atlas for the void deck (toy rebuild). Run with system python3.
Builds one HTML page and screenshots it with headless Chrome, so Tamil shapes correctly.
Non-English text comes only from layouts/voiddeck.json (signs.rows, Malay) and tools/signs/WORDING.md (sign_nosmoke).
Writes assets/maps/voiddeck_tex/signs.png and signs.json (pixel rects per cell).
"""
import json, os, random, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
TEX = os.path.join(ROOT, 'assets/maps/voiddeck_tex')
SCR = '/tmp/lunchliao-scratch'
J = json.load(open(os.path.join(ROOT, 'tools/blender/maps_toy/layouts/voiddeck_expanded.json')))['signs']
rows, place = J['rows'], J['place']
F = 'file://' + os.path.join(ROOT, 'assets/fonts')
S = 2048
cells, html = {}, []

def cell(name, x, y, w, h, inner, bg='#fff', extra=''):
    cells[name] = [x, y, w, h]
    html.append(f'<div class="c" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{bg};{extra}">{inner}</div>')

RING = '<circle cx="50" cy="50" r="42" fill="#fff" stroke="#d3262b" stroke-width="10"/>'
SLASH = '<line x1="21" y1="21" x2="79" y2="79" stroke="#d3262b" stroke-width="10"/>'
def picto(body, ban=True, size=150):
    return f'<svg width="{size}" height="{size}" viewBox="0 0 100 100">{RING if ban else ""}{body}{SLASH if ban else ""}</svg>'
BALL = '<circle cx="50" cy="50" r="19" fill="#fff" stroke="#222" stroke-width="5"/><polygon points="50,40 59,47 56,58 44,58 41,47" fill="#222"/>'
SKATE = '<rect x="26" y="44" width="48" height="8" rx="4" fill="#222"/><circle cx="36" cy="59" r="6" fill="#222"/><circle cx="64" cy="59" r="6" fill="#222"/>'
BIKE = '<g fill="none" stroke="#222" stroke-width="5"><circle cx="33" cy="58" r="12"/><circle cx="67" cy="58" r="12"/><path d="M33 58 L45 40 L62 40 L67 58 M45 40 L52 58 L33 58 M58 33 L66 33"/></g>'
SMOKE = '<rect x="24" y="52" width="40" height="9" fill="#fff" stroke="#222" stroke-width="3"/><rect x="64" y="52" width="12" height="9" fill="#e07b2c" stroke="#222" stroke-width="3"/><path d="M34 44 q-6 -8 0 -14 M44 44 q-6 -8 0 -14" fill="none" stroke="#222" stroke-width="4"/>'
LIFT = '<rect x="20" y="14" width="60" height="72" rx="6" fill="none" stroke="#fff" stroke-width="6"/><polygon points="50,24 64,44 36,44" fill="#fff"/><polygon points="50,76 64,56 36,56" fill="#fff"/>'
BIKEW = BIKE.replace('#222', '#fff')
SWING = '<g fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round"><path d="M18 84 L34 18 L66 18 L82 84 M42 18 L42 60 M58 18 L58 60"/><path d="M38 62 L62 62"/></g>'

def two_line(r, pic=''):
    en, ms = r['en'], r.get('zh')        # in this map the 'zh' field holds the Malay line
    t = f'<div class="en">{en}</div>' + (f'<div class="ms">{ms}</div>' if ms else '')
    return f'<div class="row">{pic}<div class="txt">{t}</div></div>'

y = 0
for i, r in enumerate(rows):
    p = next(q for q in place if q['row'] == i); h = round(1024 * p['h'] / p['w'])
    if i < 2:      # block number: big dark numerals on a white enamel plate
        num = r['en'].split()[-1]
        inner = f'<div class="row"><div class="blk">BLK</div><div class="num">{num}</div></div>'
        cell(f'row{i}', 0, y, 1024, h, inner, '#fbf8f0', 'color:#1f2a44;border:10px solid #1f2a44;')
    elif i == 2:   # town council prohibition board: white, red rings, English and Malay
        pics = picto(BALL) + picto(SKATE) + picto(BIKE)
        cell(f'row{i}', 0, y, 1024, h, f'<div class="row">{pics}<div class="txt" style="color:#c8221b">'
             f'<div class="en" style="font-size:54px">{r["en"]}</div><div class="ms" style="font-size:34px;color:#222">{r["zh"]}</div></div></div>',
             '#fbf8f0', 'border:10px solid #c8221b;')
    elif i == 6:   # provision shop: yellow board, red letters (English only, no other wording on file)
        cell(f'row{i}', 0, y, 1024, h, f'<div class="row"><div class="en" style="font-size:96px;letter-spacing:6px">{r["en"]}</div></div>',
             '#f6c62f', 'color:#c8221b;border:8px solid #c8221b;')
    else:
        pic = {3: picto(LIFT, False, 170), 5: picto(SWING, False, 170), 7: picto(BIKEW, False, 150)}.get(i, '')
        cell(f'row{i}', 0, y, 1024, h, two_line(r, pic), r['bg'], f'color:{r["fg"]};')
    y += h + 8

# four-language no smoking plate, wording from tools/signs/WORDING.md (sign_nosmoke)
cell('nosmoke', 1032, 0, 512, 512,
     f'<div class="col">{picto(SMOKE, True, 230)}<div class="en" style="font-size:52px;color:#c8221b">NO SMOKING</div>'
     '<div class="zh" style="font-size:50px">禁止吸烟</div><div class="en" style="font-size:36px">DILARANG MEROKOK</div>'
     '<div class="ta" style="font-size:34px">புகைபிடிக்கக் கூடாது</div></div>', '#fbf8f0', 'color:#222;border:12px solid #c8221b;')

# clock face for the play tower
ticks = ''.join(f'<line x1="50" y1="9" x2="50" y2="{17 if k % 3 == 0 else 13}" stroke="#1f2a44" stroke-width="{4 if k % 3 == 0 else 2}" transform="rotate({k * 30} 50 50)"/>' for k in range(12))
cell('clock', 1552, 0, 256, 256, f'<svg width="256" height="256" viewBox="0 0 100 100"><circle cx="50" cy="50" r="47" fill="#fbf8f0" stroke="#1f2a44" stroke-width="5"/>{ticks}'
     '<line x1="50" y1="50" x2="50" y2="22" stroke="#1f2a44" stroke-width="5" stroke-linecap="round"/><line x1="50" y1="50" x2="70" y2="58" stroke="#1f2a44" stroke-width="6" stroke-linecap="round"/>'
     '<circle cx="50" cy="50" r="5" fill="#c8221b"/></svg>', '#f2c230')

# notice board: green baize, pinned papers with grey bars standing in for print (no fake text)
rnd = random.Random(4)
papers = ''
for k in range(8):
    px, py = 24 + (k % 4) * 124, 22 + (k // 4) * 150; pw, ph = 104, 132
    col = rnd.choice(['#fbf8f0', '#fff1c9', '#f6c9c4', '#cfe8d8', '#d7e6f7'])
    bars = ''.join(f'<rect x="{px + 12}" y="{py + 34 + b * 16}" width="{rnd.randint(40, 80)}" height="6" fill="#8a8f98"/>' for b in range(5))
    papers += f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="{col}"/><rect x="{px + 12}" y="{py + 12}" width="{pw - 24}" height="12" fill="{rnd.choice(["#c8221b", "#1f3c80", "#0f8a5f"])}"/>{bars}<circle cx="{px + pw / 2}" cy="{py + 5}" r="5" fill="#c8221b"/>'
cell('notice', 1032, 520, 512, 320, f'<svg width="512" height="320">{papers}</svg>', '#2f7d5b')

# mama shop front: dark interior, shelves of packets and tins, hanging snack strips
rnd = random.Random(11); W, H = 1008, 426; g = ''
PACK = ['#e8452f', '#f2c230', '#2f7fc4', '#3aa35a', '#f08a2c', '#e96aa0', '#fbf8f0', '#7a4fb0']
for s, sy in enumerate((70, 160, 250, 340)):
    x = 14
    while x < W - 40:
        w = rnd.randint(22, 46); hh = rnd.randint(40, 72) if s < 3 else rnd.randint(50, 74); c = rnd.choice(PACK)
        g += f'<rect x="{x}" y="{sy + 78 - hh}" width="{w}" height="{hh}" rx="5" fill="{c}"/><rect x="{x + 4}" y="{sy + 78 - hh + hh * .3}" width="{w - 8}" height="{hh * .25}" fill="#ffffff" opacity=".7"/>'
        x += w + rnd.randint(3, 9)
    g += f'<rect x="0" y="{sy + 78}" width="{W}" height="10" fill="#b98a55"/>'
for k in range(14):                       # hanging strips of snack packets across the top
    x = 30 + k * 70; c = rnd.choice(PACK)
    g += ''.join(f'<rect x="{x}" y="{6 + j * 20}" width="26" height="17" rx="3" fill="{c}"/>' for j in range(3))
cell('shop', 1032, 848, W, H, f'<svg width="{W}" height="{H}">{g}</svg>', '#4a3526')

# vending machine front: drink cans behind glass
rnd = random.Random(5); g = ''
for rr in range(4):
    for cc in range(5):
        g += f'<rect x="{22 + cc * 40}" y="{20 + rr * 62}" width="26" height="46" rx="6" fill="{rnd.choice(PACK)}"/>'
    g += f'<rect x="10" y="{70 + rr * 62}" width="220" height="5" fill="#9aa3ad"/>'
cell('vend', 1560, 264, 240, 270, f'<svg width="240" height="270">{g}</svg>', '#e9f3f7')

# shop row (English only, no other wording on file): signboards and shopfront interiors
CUP = '<path d="M28 34 h36 v22 a14 14 0 0 1 -36 0 z" fill="#fff"/><path d="M64 38 h8 a8 8 0 0 1 0 16 h-8" fill="none" stroke="#fff" stroke-width="5"/><rect x="22" y="72" width="50" height="6" rx="3" fill="#fff"/>'
LEAFP = '<path d="M50 14 C80 30 80 66 50 86 C20 66 20 30 50 14 z" fill="#fff"/><path d="M50 22 V84" stroke="#0f6a4a" stroke-width="4"/>'
SCIS = '<g fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round"><circle cx="30" cy="70" r="11"/><circle cx="70" cy="70" r="11"/><path d="M37 61 L68 16 M63 61 L32 16"/></g>'
BUN = '<path d="M14 64 a36 30 0 0 1 72 0 z" fill="#fff"/><rect x="12" y="68" width="76" height="10" rx="5" fill="#fff"/>'
SHOPS = [('kopi', 'COFFEE SHOP', CUP, '#c8221b', '#fbf8f0'), ('tcm', 'MEDICAL HALL', LEAFP, '#0f6a4a', '#f6e9b8'),
         ('barber', 'BARBER', SCIS, '#1f3c80', '#fbf8f0'), ('bakery', 'BAKERY', BUN, '#e07b2c', '#fbf8f0')]
for k, (n, en, pic, bg, fg) in enumerate(SHOPS):
    bx, by = 1032 + (k % 2) * 504, 1290 + (k // 2) * 104
    cell('b_' + n, bx, by, 496, 96, f'<div class="row" style="gap:16px">{picto(pic, False, 80)}<div class="en" style="font-size:50px;letter-spacing:3px">{en}</div></div>', bg, f'color:{fg};border:5px solid {fg};')
    rnd = random.Random(20 + k); W, H = 496, 216; g = ''
    if n == 'kopi':        # drinks counter: kettle shelf, cup stacks, a row of stools
        for i in range(9): g += f'<rect x="{20 + i * 52}" y="34" width="34" height="40" rx="6" fill="{rnd.choice(["#fbf8f0", "#3aa39a", "#f2c230"])}"/>'
        g += '<rect x="0" y="76" width="496" height="8" fill="#b98a55"/><rect x="0" y="120" width="496" height="96" fill="#9aa3ad"/><rect x="0" y="120" width="496" height="10" fill="#e9edf0"/>'
        for i in range(6): g += f'<circle cx="{50 + i * 80}" cy="108" r="13" fill="#fbf8f0"/><rect x="{38 + i * 80}" y="108" width="24" height="12" fill="#fbf8f0"/>'
    elif n == 'tcm':       # wall of herb drawers over jars
        for i in range(12):
            for j in range(4): g += f'<rect x="{10 + i * 40}" y="{10 + j * 32}" width="36" height="28" fill="#8a5a36"/><circle cx="{28 + i * 40}" cy="{24 + j * 32}" r="3" fill="#e0b05a"/>'
        for i in range(10): g += f'<rect x="{16 + i * 48}" y="150" width="34" height="50" rx="8" fill="#e9f3f7" opacity=".85"/><rect x="{16 + i * 48}" y="170" width="34" height="30" rx="6" fill="{rnd.choice(["#b9742f", "#7a4a2a", "#c9a66b", "#a8352c"])}"/><rect x="{20 + i * 48}" y="144" width="26" height="8" fill="#c8221b"/>'
    elif n == 'barber':    # mirrors, chairs and the striped pole
        for i in range(3): g += f'<rect x="{90 + i * 130}" y="20" width="90" height="100" rx="8" fill="#bfe0ee"/><rect x="{108 + i * 130}" y="130" width="54" height="44" rx="8" fill="#a8352c"/><rect x="{130 + i * 130}" y="174" width="10" height="30" fill="#c9ccd0"/><rect x="{112 + i * 130}" y="200" width="46" height="8" fill="#c9ccd0"/>'
        g += '<rect x="24" y="20" width="36" height="170" rx="16" fill="#fbf8f0"/>' + ''.join(f'<rect x="24" y="{34 + i * 26}" width="36" height="12" fill="{"#d3262b" if i % 2 else "#2f7fc4"}"/>' for i in range(6))
    else:                  # trays of buns
        for j, sy in enumerate((20, 86, 152)):
            for i in range(11): g += f'<ellipse cx="{30 + i * 44}" cy="{sy + 34}" rx="18" ry="13" fill="{rnd.choice(["#e0a04a", "#c9813a", "#f2c66a", "#b56a2e"])}"/>'
            g += f'<rect x="0" y="{sy + 46}" width="496" height="8" fill="#e9edf0"/>'
    cell('f_' + n, bx, 1498 + (k // 2) * 224, W, H, f'<svg width="{W}" height="{H}">{g}</svg>', '#4a3526' if n != 'barber' else '#e6dccb')

face = lambda fam, f, wt: f"@font-face{{font-family:'{fam}';src:url('{F}/{f}');font-weight:{wt}}}"
css = '\n'.join([face('SC', 'NotoSansSC-Black.otf', 900), face('SC', 'NotoSansSC-Bold.otf', 700), face('TA', 'NotoSansTamil-Black.ttf', 900)]) + f'''
*{{box-sizing:border-box;margin:0;padding:0}} html,body{{width:{S}px;height:{S}px;overflow:hidden;background:#888}}
.c{{position:absolute;overflow:hidden;font-family:'SC';font-weight:900;border-radius:0}}
.row{{display:flex;align-items:center;justify-content:center;gap:26px;width:100%;height:100%;padding:0 20px}}
.col{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;width:100%;height:100%}}
.txt{{display:flex;flex-direction:column;align-items:center;line-height:1.05;text-align:center}}
.en{{font-size:76px;white-space:nowrap}} .ms{{font-size:44px;font-weight:700;white-space:nowrap;margin-top:8px}}
.zh{{font-family:'SC'}} .ta{{font-family:'TA';line-height:1.5}}
.blk{{font-size:70px;margin-top:40px}} .num{{font-size:200px;line-height:1;letter-spacing:8px}}'''
page = os.path.join(SCR, 'voiddeck_signs.html')
open(page, 'w').write(f'<!doctype html><meta charset="utf-8"><style>{css}</style><body>{"".join(html)}</body>')
os.makedirs(TEX, exist_ok=True); out = os.path.join(TEX, 'signs.png')
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--headless=new', '--no-first-run', '--hide-scrollbars',
                '--force-device-scale-factor=1', f'--user-data-dir={SCR}/chrome-voiddeck', f'--window-size={S},{S}',
                '--virtual-time-budget=4000', f'--screenshot={out}', 'file://' + page], check=True, timeout=120,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
json.dump({'size': S, 'cells': cells}, open(os.path.join(TEX, 'signs.json'), 'w'))
print(out)
