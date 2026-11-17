"""Draws every collider from layouts/carpark_solids_v3.json in red over shots/maps_toy/carpark/topdown_check.png.
Called by carpark.py after the orthographic render (ortho scale 96 m over 1600 px, game x right, game z down). System python + Pillow."""
import json, os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
P = os.path.join(ROOT, 'shots', 'maps_toy', 'carpark', 'topdown_check.png')
im = Image.open(P).convert('RGB'); d = ImageDraw.Draw(im); W, H = im.size; k = W / 96
for b in json.load(open(os.path.join(HERE, 'layouts', 'carpark_solids_v3.json'))):
    d.rectangle([W / 2 + b[0] * k, H / 2 + b[2] * k, W / 2 + b[3] * k, H / 2 + b[5] * k], outline=(255, 0, 255) if b[6] == 'i' else (255, 0, 0), width=1)
im.save(P); print('topdown overlay ok')
