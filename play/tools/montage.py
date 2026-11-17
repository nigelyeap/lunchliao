# side by side: Blender ground_a, ground_b (top) vs in-game _a (Blender camera), tp (bottom). usage: python3 montage.py <out_dir> [maps...]
import sys
from PIL import Image
R='/Users/nigelyeap/Documents/lunchliao-hd/shots/'
out=sys.argv[1];maps=sys.argv[2:] or ['hawker','voiddeck','wetmarket','carpark','classroom']
for m in maps:
    ims=[R+f'maps_toy/{m}/ground_a.png',R+f'maps_toy/{m}/ground_b.png',R+f'play/{m}_a.png',R+f'play/{m}_tp.png']
    M=Image.new('RGB',(1600,900))
    for i,p in enumerate(ims):
        M.paste(Image.open(p).convert('RGB').resize((800,450)),((i%2)*800,(i//2)*450))
    M.save(f'{out}/cmp_{m}.jpg',quality=80)
