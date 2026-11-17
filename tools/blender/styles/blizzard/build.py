"""Builds Ah Ma (blizzard style), saves the .blend, renders the bake-off shots.
blender -b -P build.py -- [low] [hero face expr turn] [prev]"""
import bpy, sys, os, math, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, HERE + '/../../heroes')
import bl, head, body, shots_lib as SL, render_lib as RL
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(HERE + '/../../../../shots/styles/blizzard') + '/'
TMP = bl.CACHE + '/'
os.makedirs(OUT, exist_ok=True)
LOW = dict(head=13500, hair=6500, blouse=4500, slacks=1000, hand=1100, foot=400, sole=200)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
root, hobjs = body.build(LOW if 'low' in args else None)
bpy.context.view_layer.update()
from mathutils import Vector
zs = [(o.matrix_world @ Vector(c)).z for o in bpy.data.objects if o.type == 'MESH' for c in o.bound_box]
root.scale = (2.13 / max(zs),) * 3; print('height before scale', max(zs), 'min', min(zs))
per = {}
for o in bpy.data.objects:
    if o.type == 'MESH': per[o.name.split('.')[0]] = per.get(o.name.split('.')[0], 0) + bl.tris(o)
print('TRIS', sum(per.values()), per)
head.set_expr(hobjs.values(), 'smile')
PX = 0.5 if 'prev' in args else 1.0
def setup(w, h): RL.setup_render(int(w * PX), int(h * PX), 24 if PX < 1 else 64)
SL.light((0, 0, 1.1), 0.0)
bpy.ops.wm.save_as_mainfile(filepath=HERE + '/ahma_blizzard.blend')
HC = np.array(body.HEAD) * root.scale[0]

def stitch(paths, out):
    ims = []
    for p in paths:
        im = bpy.data.images.load(p); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); ims.append(a.reshape(h, w, 4))
    a = np.concatenate(ims, 1)[:, :int(1600 * PX)]; h, w = a.shape[:2]
    o = bpy.data.images.new('st', w, h, alpha=False); o.pixels.foreach_set(a.ravel()); o.filepath_raw = out; o.file_format = 'PNG'; o.save()

todo = [a for a in args if a in ('hero', 'face', 'expr', 'turn')] or ['hero', 'face', 'expr', 'turn']
if 'hero' in todo:
    setup(1600, 2000); RL.shoot(OUT + 'hero.png', (-2.6, 5.2, 1.25), (0, 0.22, 1.05), 80)
if 'face' in todo:
    setup(1600, 1600); RL.shoot(OUT + 'face.png', (-1.15, 2.75, HC[2] + 0.05), (0, 0.08, HC[2] - 0.10), 70)
if 'expr' in todo:
    setup(400, 500); ps = []
    for e in ('smile', 'angry', 'grin', 'ult'):
        head.set_expr(hobjs.values(), e); ps.append(TMP + 'ex_%s.png' % e)
        RL.shoot(ps[-1], (0, 4.0, HC[2] + 0.06), (0, 0.06, HC[2] + 0.06), 135)
    stitch(ps, OUT + 'expressions.png'); head.set_expr(hobjs.values(), 'smile')
if 'turn' in todo:
    setup(534, 800); ps = []
    for i, a in enumerate((0, 90, 180)):
        root.rotation_euler = (0, 0, math.radians(a)); ps.append(TMP + 'turn_%d.png' % i)
        RL.shoot(ps[-1], (0, 8.0, 1.1), (0, 0.0, 1.07), 118)
    root.rotation_euler = (0, 0, 0); stitch(ps, OUT + 'turn.png')
