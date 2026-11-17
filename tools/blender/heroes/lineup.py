"""Gate 2 line-up: the four new heroes posed with expressions, and each next to its old model at the same scale.
Run: blender -b -P tools/blender/heroes/lineup.py   Writes shots/heroes/lineup_*.png."""
import bpy, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
import render_lib as RL
OUT = os.path.join(ROOT, 'shots', 'heroes')
HEROES = ('ahma', 'gym', 'tarik', 'siao')
FACE = {'ahma': {'smile': 1}, 'gym': {'angry': 1}, 'tarik': {'grin': 1}, 'siao': {'grin': .8, 'mouth_open': .4}}

def load(path, x, turn=False):
    bpy.ops.import_scene.gltf(filepath=path)
    sel = list(bpy.context.selected_objects)
    for o in sel:
        if o.parent is None:
            o.location.x += x
            if turn: o.rotation_mode = 'XYZ'; o.rotation_euler.z += math.pi
        if o.name.startswith('Icosphere'): o.hide_render = True
    return sel

def pose(objs, acts, face):
    idle = next((a for a in acts if 'idle' in a.name.lower()), next(iter(acts), None))
    for o in objs:
        if o.type == 'ARMATURE' and idle:
            o.animation_data_create(); o.animation_data.action = idle
        sk = o.data.shape_keys if o.type == 'MESH' else None
        if sk:
            for k in sk.key_blocks[1:]: k.value = face.get(k.name, 0.0)

def scene(rows):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for path, x, turn, key, face in rows:
        before = set(bpy.data.actions)
        objs = load(path, x, turn)
        pose(objs, set(bpy.data.actions) - before, face)
    bpy.context.scene.frame_set(0)

new = lambda k: os.path.join(ROOT, 'assets', 'heroes', f'{k}.glb')
old = lambda k: os.path.join(ROOT, 'ref', 'heroes', f'{k}.glb')
STEP = 1.9

# 1. the new four, side by side, each with its own face
scene([(new(k), (1.5 - i) * STEP, False, f'n{k}', FACE[k]) for i, k in enumerate(HEROES)])
RL.setup_render(2400, 1100, 48); RL.studio_light((0, 0, 1.1)); RL.floor()
RL.shoot(os.path.join(OUT, 'lineup_new.png'), (0, 11.5, 1.7), (0, 0, 1.05), 45)
RL.shoot(os.path.join(OUT, 'lineup_new_34.png'), (-6.5, 9.5, 2.4), (0, 0, 1.0), 45)

# 2. old and new in pairs at the same scale (old ref glbs face +Z, so turn them round)
rows = []
for i, k in enumerate(HEROES):
    cx = (1.5 - i) * 2 * STEP  # camera looks down -Y, so +x is screen left
    rows += [(old(k), cx + .85, True, f'o{k}', {}), (new(k), cx - .85, False, f'n{k}', FACE[k])]
scene(rows)
RL.setup_render(3000, 1000, 48); RL.studio_light((0, 0, 1.1)); RL.floor()
RL.shoot(os.path.join(OUT, 'lineup_old_vs_new.png'), (0, 20.5, 1.6), (0, 0, 1.05), 45)
print('[lineup] written to', OUT)
