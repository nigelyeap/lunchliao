"""Contact sheet of the viewmodel check renders. Run: python3 sheet.py"""
import os
from PIL import Image, ImageDraw, ImageFont
HD = os.path.dirname(os.path.abspath(__file__)); SH = os.path.abspath(os.path.join(HD, '..', '..', '..', 'shots', 'viewmodels_toy'))
N = dict(ahma='Ah Ma', uncle='Stinky Uncle', nsboy='NSF', engineer='Engineer Encik', gym='Gym Hunk', rascal='Recess Rascal', debater='Head Prefect',
         tarik='Teh Tarik Auntie', rider='Delivery Driver', dj='Nightclub DJ', lens='Birdwatcher', siao='The Siaolang', ice='Ice Cream Uncle')
W = Image.new('RGB', (3200, 1800), (28, 28, 28)); D = ImageDraw.Draw(W); F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 26)
for i, (k, name) in enumerate(N.items()):
    x, y = (i % 4) * 800, (i // 4) * 450
    W.paste(Image.open(os.path.join(SH, k + '.png')).convert('RGB').resize((800, 450), Image.LANCZOS), (x, y))
    D.text((x + 10, y + 8), '%s (%s)' % (name, k), fill='white', font=F, stroke_width=2, stroke_fill='black')
W.save(os.path.join(SH, 'sheet.png'))
