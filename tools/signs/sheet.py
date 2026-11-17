# Contact sheet of all baked signs -> shots/signs/sheet.png
import glob, os
from PIL import Image, ImageDraw
files = sorted(glob.glob('assets/signs/sign_*.png'))
cell = 480; pad = 16
cols = 4; rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (cell + pad) + pad, rows * (cell + pad + 22) + pad), (58, 52, 46))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGBA'); im.thumbnail((cell, cell), Image.LANCZOS)
    bg = Image.new('RGBA', im.size, (90, 84, 78, 255)); bg.alpha_composite(im)
    x = pad + (i % cols) * (cell + pad); y = pad + (i // cols) * (cell + pad + 22)
    sheet.paste(bg.convert('RGB'), (x, y)); d.text((x, y + im.height + 4), os.path.basename(f), fill=(230, 220, 190))
sheet.save('shots/signs/sheet.png')
