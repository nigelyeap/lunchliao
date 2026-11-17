# Verify every non-ASCII character used in the sign HTML exists in the shipped font files.
import glob, re, sys
from fontTools.ttLib import TTFont
F = '../../assets/fonts/'
cmaps = {n: set(TTFont(F + n, lazy=True).getBestCmap()) for n in
         ['NotoSansSC-Black.otf', 'NotoSansSC-Bold.otf', 'NotoSerifSC-Black.otf', 'NotoSansTamil-Bold.ttf', 'NotoSerifDisplay-Black.ttf']}
bad = 0
for f in sorted(glob.glob('_html/*.html')):
    t = open(f, encoding='utf8').read()
    t = re.sub(r'<style>.*?</style>', '', t, flags=re.S)
    for ch in sorted({c for c in re.sub(r'<[^>]+>', '', t) if ord(c) > 127 and not c.isspace()}):
        cp = ord(ch)
        fonts = ['NotoSansTamil-Bold.ttf'] if 0x0B80 <= cp <= 0x0BFF else ['NotoSansSC-Bold.otf', 'NotoSansSC-Black.otf', 'NotoSerifSC-Black.otf']
        if not any(cp in cmaps[n] for n in fonts):
            print('MISSING', f, ch, hex(cp)); bad += 1
print('missing glyphs:', bad)
sys.exit(bad > 0)
