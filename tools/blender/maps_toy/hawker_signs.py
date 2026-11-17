"""Clean toy-style sign atlases for the hawker map. Run with system python3 (needs PIL):
  python3 tools/blender/maps_toy/hawker_signs.py
signs.png: 2048x2048, 16 stall signboards, 2 cols x 8 rows of 1024x256.
menus.png: 2048x2048, 16 menu boards, 4 x 4 of 512x512.
Non-English lines come only from the map JSON (Malay, field `zh`) and tools/signs/WORDING.md (Chinese)."""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'maps', 'hawker_tex'); os.makedirs(OUT, exist_ok=True)
F = os.path.join(ROOT, 'assets', 'fonts')
font = lambda s, f='NotoSansSC-Black.otf': ImageFont.truetype(os.path.join(F, f), s)
rows = json.load(open(os.path.join(HERE, 'layouts', 'hawker_expanded.json')))['signs']['rows']
# Chinese copied from WORDING.md (sign_main, sign_drinks). Stalls with no checked wording get none.
ZH = {'CHICKEN RICE': '金成海南鸡饭', 'KOPI · TEH': '咖啡 · 茶', 'SUGARCANE': '甘蔗水', 'TAU HUAY': '豆浆', 'ROTI PRATA': '拉茶'}

def fit(d, text, size, maxw, f='NotoSansSC-Black.otf'):
    while size > 10:
        ft = font(size, f)
        if d.textlength(text, font=ft) <= maxw: return ft
        size -= 2
    return font(size, f)

S = 2  # supersample
signs = Image.new('RGB', (2048 * S, 2048 * S), '#222')
for i, r in enumerate(rows):
    W, H = 1024 * S, 256 * S; im = Image.new('RGB', (W, H), r['bg']); d = ImageDraw.Draw(im)
    d.rounded_rectangle([14 * S, 14 * S, W - 14 * S, H - 14 * S], 30 * S, outline=r['fg'], width=6 * S)
    cx, cy = 140 * S, 128 * S   # dish icon
    d.ellipse([cx - 84 * S, cy - 84 * S, cx + 84 * S, cy + 84 * S], fill='#FFFDF7', outline=r['fg'], width=5 * S)
    d.ellipse([cx - 62 * S, cy - 62 * S, cx + 62 * S, cy + 62 * S], fill='#EDE6D6')
    d.ellipse([cx - 52 * S, cy - 40 * S, cx + 40 * S, cy + 44 * S], fill=r['food'][0])
    for k, (ox, oy) in enumerate([(-18, -12), (14, 6), (-6, 20), (26, -22)]):
        d.ellipse([cx + (ox - 13) * S, cy + (oy - 10) * S, cx + (ox + 13) * S, cy + (oy + 10) * S], fill=r['food'][1])
    d.ellipse([cx + 28 * S, cy + 22 * S, cx + 52 * S, cy + 38 * S], fill='#4A9A4A')
    x0, x1 = 250 * S, 830 * S; mid = (x0 + x1) // 2
    ft = fit(d, r['en'], 104 * S, x1 - x0); d.text((mid, 100 * S), r['en'], font=ft, fill=r['fg'], anchor='mm')
    zh = ZH.get(r['en']); ms = r['zh']
    fm = fit(d, ms, 40 * S, (x1 - x0) - (300 * S if zh else 0), 'NotoSansSC-Bold.otf')
    if zh:
        fz = font(46 * S); wz = d.textlength(zh, font=fz); wm = d.textlength(ms, font=fm); gap = 28 * S
        sx = mid - (wz + gap + wm) / 2
        d.text((sx, 190 * S), zh, font=fz, fill=r['fg'], anchor='lm'); d.text((sx + wz + gap, 190 * S), ms, font=fm, fill=r['fg'], anchor='lm')
    else: d.text((mid, 190 * S), ms, font=fm, fill=r['fg'], anchor='mm')
    d.rounded_rectangle([850 * S, 96 * S, 996 * S, 160 * S], 32 * S, fill=r['fg'])
    d.text((923 * S, 127 * S), r['sub'], font=font(36 * S), fill=r['bg'], anchor='mm')
    signs.paste(im, ((i % 2) * W, (i // 2) * H))
signs.resize((2048, 2048), Image.LANCZOS).save(os.path.join(OUT, 'signs.png'))

menus = Image.new('RGB', (2048 * S, 2048 * S), '#222')
for i, r in enumerate(rows):
    W = 512 * S; im = Image.new('RGB', (W, W), '#FFF7E6'); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 110 * S], fill=r['bg'])
    d.text((W // 2, 55 * S), r['en'], font=fit(d, r['en'], 56 * S, W - 60 * S), fill=r['fg'], anchor='mm')
    for k, (name, price) in enumerate(r['menu']):
        y = (165 + k * 86) * S
        d.ellipse([28 * S, y - 26 * S, 80 * S, y + 26 * S], fill=r['food'][k % 2], outline='#2A2420', width=3 * S)
        d.text((98 * S, y), name, font=fit(d, name, 34 * S, 270 * S, 'NotoSansSC-Bold.otf'), fill='#2A2420', anchor='lm')
        d.rounded_rectangle([386 * S, y - 26 * S, 490 * S, y + 26 * S], 26 * S, fill='#C8221B')
        d.text((438 * S, y), '$' + price, font=font(30 * S), fill='#FFF7E6', anchor='mm')
    d.rectangle([0, 0, W - 1, W - 1], outline='#2A2420', width=8 * S)
    menus.paste(im, ((i % 4) * W, (i // 4) * W))
menus.resize((2048, 2048), Image.LANCZOS).save(os.path.join(OUT, 'menus.png'))
print('ok', OUT)

# ---------------------------------------------------------------- extras.png (2048x2048): notices, pictograms, numbers
# Baked with headless Chrome so Tamil shapes correctly (PIL here has no raqm). Non-English lines are copied from
# tools/signs/WORDING.md (sign_grade, sign_tray, sign_nosmoke). Everything else is English plus pictograms.
import subprocess, pathlib
SCR = '/tmp/lunchliao-scratch/hawker'
os.makedirs(SCR, exist_ok=True)
FU = pathlib.Path(F).as_uri()
MAN = '<svg viewBox="0 0 100 100"><circle cx="50" cy="16" r="11"/><rect x="33" y="30" width="34" height="34" rx="7"/><rect x="36" y="60" width="12" height="36" rx="5"/><rect x="52" y="60" width="12" height="36" rx="5"/></svg>'
WOMAN = '<svg viewBox="0 0 100 100"><circle cx="50" cy="16" r="11"/><path d="M40 30h20l16 42H24z"/><rect x="38" y="68" width="10" height="28" rx="5"/><rect x="52" y="68" width="10" height="28" rx="5"/></svg>'
TRAY = '<svg viewBox="0 0 120 80"><rect x="6" y="52" width="108" height="14" rx="7"/><path d="M34 48a26 22 0 0 1 52 0z"/><rect x="26" y="44" width="68" height="7" rx="3"/></svg>'
NOSM = '<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="41" fill="#fff" stroke="#d6322b" stroke-width="10"/><rect x="24" y="45" width="40" height="10" fill="#2a2420"/><rect x="64" y="45" width="10" height="10" fill="#e8843a"/><path d="M70 38q6-6 0-12" fill="none" stroke="#8a8a8a" stroke-width="4"/><line x1="21" y1="21" x2="79" y2="79" stroke="#d6322b" stroke-width="10"/></svg>'
nums = ''.join(f'<div class="tn" style="left:{(i % 8) * 128}px;top:{1280 + (i // 8) * 128}px"><b>{i + 1}</b></div>' for i in range(32))
blks = ''.join(f'<div class="blk" style="left:{i * 256}px;top:1024px"><i>BLK</i><b>{n}</b></div>' for i, n in enumerate((22, 38, 43, 95)))
html = f'''<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:S;src:url('{FU}/NotoSansSC-Bold.otf');font-weight:700}}
@font-face{{font-family:S;src:url('{FU}/NotoSansSC-Black.otf');font-weight:900}}
@font-face{{font-family:T;src:url('{FU}/NotoSansTamil-Bold.ttf');font-weight:700}}
*{{box-sizing:border-box;margin:0;padding:0}}body{{width:2048px;height:2048px;background:#222;position:relative;overflow:hidden;font-family:S,T;font-weight:900;color:#2a2420}}
body>div{{position:absolute;overflow:hidden;text-align:center}}svg{{display:block}}
.grade{{left:0;top:0;width:512px;height:512px;background:#fbf8f0;border:14px solid #2e8b57;border-radius:44px}}
.grade h1{{font-size:40px;margin-top:22px;color:#2e8b57;line-height:1.1}}.grade .a{{width:230px;height:230px;border-radius:50%;background:#2e8b57;color:#fbf8f0;font-size:190px;line-height:222px;margin:10px auto}}
.grade p{{font-size:40px;line-height:1.2}}.grade small{{font-size:27px;font-weight:700}}
.ns{{left:512px;top:0;width:512px;height:512px;background:#fbf8f0;border:14px solid #d6322b;border-radius:44px}}
.ns svg{{width:190px;margin:14px auto 2px}}.ns h1{{font-size:50px;color:#d6322b;line-height:1.1}}.ns p{{font-size:38px;line-height:1.3}}.ns .t{{font-family:T;font-weight:700;font-size:33px}}
.tray{{left:1024px;top:0;width:1024px;height:512px;background:#fbf8f0;border:14px solid #2e8b57;border-radius:44px}}
.tray .hd{{background:#2e8b57;color:#fbf8f0;height:128px;display:flex;align-items:center;justify-content:center;gap:28px;font-size:76px}}.tray .hd svg{{width:150px;fill:#fbf8f0}}
.tray p{{font-size:42px;line-height:1.36;font-weight:700}}.tray p.t{{font-family:T;font-size:34px;line-height:1.6}}.tray p.th{{font-size:30px;color:#2e8b57;line-height:1.5}}
.wc{{left:0;top:512px;width:1024px;height:256px;background:#2b5fa8;color:#fff;border-radius:36px;display:flex;align-items:center;justify-content:center;gap:34px;font-size:128px}}
.wc svg{{width:150px;fill:#fff}}
.tr2{{left:1024px;top:512px;width:1024px;height:256px;background:#2e8b57;color:#fbf8f0;border-radius:36px;display:flex;align-items:center;justify-content:center;gap:34px;font-size:104px}}.tr2 svg{{width:200px;fill:#fbf8f0}}
.name{{left:0;top:768px;width:2048px;height:256px;background:#fbf8f0;border:12px solid #e8843a;display:flex;align-items:center;justify-content:center;gap:44px;font-size:92px;color:#c8501e;white-space:nowrap}}
.name span{{background:#e8843a;color:#fbf8f0;border-radius:24px;padding:0 30px;font-size:84px}}
.blk{{width:256px;height:256px;background:#fbf8f0}}.blk i{{display:block;font-style:normal;font-size:44px;margin-top:22px;color:#555}}.blk b{{font-size:140px;line-height:150px}}
.pic{{top:1024px;width:256px;height:256px;border-radius:36px}}.pic svg{{width:200px;margin:28px auto;fill:#fff}}
.tn{{width:128px;height:128px;background:#f0c040;border-radius:50%;border:8px solid #2a2420}}.tn b{{font-size:66px;line-height:108px}}
</style>
<div class="grade"><h1>FOOD HYGIENE<br>GRADE</h1><div class="a">A</div><p>食品卫生等级</p><small>Gred Kebersihan Makanan</small></div>
<div class="ns">{NOSM}<h1>NO SMOKING</h1><p>禁止吸烟</p><p>DILARANG MEROKOK</p><p class="t">புகைபிடிக்கக் கூடாது</p></div>
<div class="tray"><div class="hd">{TRAY}TRAY RETURN</div><p>Please return your tray here.</p><p>请将托盘归还此处。</p><p>Sila pulangkan dulang anda di sini.</p>
<p class="t">தயவுசெய்து உங்கள் தட்டை இங்கே திருப்பி வைக்கவும்.</p><p class="th">Thank you · 谢谢 · Terima kasih · <span style="font-family:T">நன்றி</span></p></div>
<div class="wc">{MAN}{WOMAN}TOILETS</div>
<div class="tr2">{TRAY}TRAY RETURN</div>
<div class="name"><span>BLK 51</span>OLD AIRPORT ROAD FOOD CENTRE</div>
{blks}
<div class="pic" style="left:1024px;background:#2b5fa8">{MAN}</div><div class="pic" style="left:1280px;background:#c2477f">{WOMAN}</div>
{nums}'''
hp = os.path.join(SCR, 'extras.html'); open(hp, 'w').write(html)
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--headless=new', '--disable-gpu', '--hide-scrollbars',
                '--force-device-scale-factor=1', '--window-size=2048,2048', '--user-data-dir=' + os.path.join(SCR, 'chrome'),
                '--screenshot=' + os.path.join(OUT, 'extras.png'), pathlib.Path(hp).as_uri()], check=True, capture_output=True, timeout=120)
print('extras', Image.open(os.path.join(OUT, 'extras.png')).size)
