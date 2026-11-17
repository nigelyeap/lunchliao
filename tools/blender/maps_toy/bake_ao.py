"""Bake an ambient occlusion lightmap for one toy map.

blender -b -P bake_ao.py -- <id> [res=4096] [samples=64] [dist=2.0] [gamma=2.4] [check]

Imports assets/maps/<id>.glb (the build scripts always overwrite their glb, so we never rerun them),
adds a 'lightmap' UV layer (TEXCOORD_1) to every static opaque mesh, bakes Cycles AO into one atlas and writes
assets/maps/<id>_lit.glb, <id>_ao.png (greyscale, white = open, glTF orientation: load with flipY=false) and <id>_ao.json.
'check' also renders the ground_a view with base colour x AO to _tmp_bake/<id>_check.png.
"""
import bpy, bmesh, sys, os, json, math, struct, zlib, time
T0 = time.time()
def log(*a): print('AO %4.0fs' % (time.time() - T0), *a, flush=True)
import numpy as np
from bpy_extras import bmesh_utils
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ARGS = sys.argv[sys.argv.index('--') + 1:]
MID = ARGS[0]
OPT = dict(a.split('=') for a in ARGS[1:] if '=' in a)
RES, SAMPLES, DIST = int(OPT.get('res', 4096)), int(OPT.get('samples', 64)), float(OPT.get('dist', 2.0))
MAPS = os.path.join(ROOT, 'assets', 'maps')
SRC, OUT_GLB = os.path.join(MAPS, MID + '.glb'), os.path.join(MAPS, MID + '_lit.glb')
TMP = os.path.join(HERE, '_tmp_bake'); os.makedirs(TMP, exist_ok=True)
MOVING = ('FAN_', 'STEAM_', 'SHUTTER_')
CAMS = {  # ground_a views from the build scripts, game coords (x, y up, z)
    'hawker': ((-27.2, 1.6, -18.0), (-10, 1.9, -19.6), 20), 'voiddeck': ((-41, 1.6, 7.6), (-14, 1.5, 7.8), 20),
    'wetmarket': ((-35.6, 1.6, -.7), (-8, 1.7, -.2), 22), 'carpark': ((-7.5, 1.6, -3.6), (3, 1.2, -1), 24),
    'classroom': ((-15.4, 1.6, -9.9), (7.6, 1.3, -10.5), 20)}


def glb_json(p):
    b = open(p, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; return json.loads(b[20:20 + n])


# ---------------------------------------------------------------- which meshes get the lightmap
J = glb_json(SRC)
def see_through(m):
    return m.get('alphaMode', 'OPAQUE') != 'OPAQUE' or 'KHR_materials_transmission' in m.get('extensions', {}) \
        or any(k in m.get('name', '').lower() for k in ('glass', 'steam', 'puddle', 'mirror'))
SKIP = set()
for nd in J['nodes']:
    if 'mesh' not in nd: continue
    mats = [J['materials'][p['material']] for p in J['meshes'][nd['mesh']]['primitives'] if 'material' in p]
    if nd['name'].startswith(MOVING) or any(see_through(m) for m in mats): SKIP.add(nd['name'])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
SC = bpy.context.scene
def moving(o):
    while o:
        if o.name.startswith(MOVING): return True
        o = o.parent
    return False
meshes = [o for o in SC.objects if o.type == 'MESH']
names = {nd['name'] for nd in J['nodes'] if 'mesh' in nd}
assert {o.name for o in meshes} == names, ('import renamed nodes', {o.name for o in meshes} ^ names)
BAKE = [o for o in meshes if o.name not in SKIP and not moving(o)]
for o in BAKE:
    if o.data.users > 1: o.data = o.data.copy()  # ponytail: un-instances shared static meshes, none seen so far
print('AO bake', len(BAKE), 'skip', sorted(o.name for o in meshes if o not in BAKE))

# ---------------------------------------------------------------- lightmap UVs
for o in BAKE:
    me = o.data
    if not me.uv_layers:  # placeholder TEXCOORD_0 so the lightmap lands on TEXCOORD_1, zeroed: default per-face UVs split every vertex
        me.uv_layers.new(name='UVMap').data.foreach_set('uv', np.zeros(len(me.loops) * 2, np.float32))
    me.uv_layers.active = me.uv_layers.new(name='lightmap')
bpy.ops.object.select_all(action='DESELECT')
for o in BAKE: o.select_set(True)
bpy.context.view_layer.objects.active = BAKE[0]
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(float(OPT.get('angle', 80))), island_margin=0.0, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale(); log('unwrapped')
bpy.ops.object.mode_set(mode='OBJECT')

z0 = min((o.matrix_world @ Vector(c)).z for o in BAKE for c in o.bound_box)
def density(o, z):
    """Linear texel scale: the floor and props near it get full density, roofs and the skyline less."""
    h = z - z0; w = 1.0 if h < 3 else max(.35, 1 - (h - 3) * .65 / 6)
    if 'hdb' in o.name.lower() or o.name.startswith('VD_hi'): w *= .5
    return w
NISL, CAP, FLOOR = 0, float(OPT.get('cap', 8000)), float(OPT.get('floor', 1.6))
for o in BAKE:
    bm = bmesh.new(); bm.from_mesh(o.data); uvl = bm.loops.layers.uv['lightmap']; mw = o.matrix_world
    isls = bmesh_utils.bmesh_linked_uv_islands(bm, uvl); NISL += len(isls)
    for isl in isls:
        z = sum((mw @ f.calc_center_median()).z for f in isl) / len(isl); s = density(o, z)
        if z - z0 < .6 and sum(f.normal.z * f.calc_area() for f in isl) > .7 * sum(f.calc_area() for f in isl): s *= FLOOR  # walkable ground
        s = min(s, (CAP / max(sum(f.calc_area() for f in isl), 1e-9)) ** .5)  # huge ground planes get no more texels than a CAP m2 island
        if s == 1.0: continue
        loops = [l for f in isl for l in f.loops]; c = sum((l[uvl].uv for l in loops), start=loops[0][uvl].uv * 0) / len(loops)
        for l in loops: l[uvl].uv = c + (l[uvl].uv - c) * s
    bm.to_mesh(o.data); bm.free()
MARGIN = float(OPT.get('margin', 5)) / RES  # px gaps between islands, gaps get dilated so mips blend neighbours only mildly
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method='FRACTION', margin=MARGIN, shape_method=OPT.get('shape', 'CONCAVE')); log('packed')
bpy.ops.object.mode_set(mode='OBJECT')

# ---------------------------------------------------------------- bake
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for d in prefs.devices: d.use = True
SC.render.engine = 'CYCLES'; SC.cycles.device = 'GPU'; SC.cycles.samples = SAMPLES
SC.world = SC.world or bpy.data.worlds.new('W'); SC.world.light_settings.distance = DIST
img = bpy.data.images.new('AO', RES, RES, alpha=True, float_buffer=True); img.colorspace_settings.name = 'Non-Color'
img.generated_color = (0, 0, 0, 0)
added = []
for m in {s.material for o in BAKE for s in o.material_slots if s.material}:
    n = m.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img; m.node_tree.nodes.active = n; added.append((m, n))
for o in meshes: o.hide_render = o not in BAKE  # glass, steam and moving parts cast no AO
for o in BAKE: o.data.uv_layers['lightmap'].active_render = True
log('islands', NISL); bpy.ops.object.bake(type='AO', margin=0, use_clear=False)
log('baked')
for m, n in added: m.node_tree.nodes.remove(n)
for o in meshes: o.hide_render = False
for o in BAKE: o.data.uv_layers[0].active_render = True; o.data.uv_layers.active = o.data.uv_layers[0]

# ---------------------------------------------------------------- denoise, pad, save
px = np.array(img.pixels[:], dtype=np.float32).reshape(RES, RES, 4)
filled = px[..., 3] > .5; v = np.where(filled, px[..., 0], 0).astype(np.float32)
log('coverage %.1f%%' % (100 * filled.mean()))
def masked_blur(v, f, sigma):  # normalised gaussian inside islands, never pulls in empty texels
    r = int(3 * sigma); k = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * sigma ** 2))
    num, den = v * f, f.astype(np.float32)
    for ax in (0, 1):
        num = sum(w * np.roll(num, i, ax) for i, w in zip(range(-r, r + 1), k))
        den = sum(w * np.roll(den, i, ax) for i, w in zip(range(-r, r + 1), k))
    return np.where(f, num / np.maximum(den, 1e-6), 0)
v = masked_blur(v, filled, float(OPT.get('blur', 1.5)))
for _ in range(int(RES * MARGIN) + 4):  # dilate islands into the gaps
    num = sum(np.roll(v * filled, s, ax) for s in (-1, 1) for ax in (0, 1))
    den = sum(np.roll(filled, s, ax).astype(np.float32) for s in (-1, 1) for ax in (0, 1))
    grow = ~filled & (den > 0); v[grow] = num[grow] / den[grow]; filled = filled | grow
v[~filled] = 1.0  # gamma below deepens contact shading, white stays white
g = (np.clip(v, 0, 1) ** float(OPT.get('gamma', 2.4)) * 255 + .5).astype(np.uint8)[::-1]  # Blender rows are bottom-up, PNG top-down
png = os.path.join(MAPS, MID + '_ao.png')
raw = b''.join(b'\0' + row.tobytes() for row in g)
def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d))
open(png, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', RES, RES, 8, 0, 0, 0, 0))
                      + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))

# ---------------------------------------------------------------- export, same settings as the build scripts
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', export_apply=True, export_yup=True,
                          export_image_format='AUTO', export_animations=False)
json.dump({'ao': MID + '_ao.png', 'meshes': sorted(o.name for o in BAKE)}, open(os.path.join(MAPS, MID + '_ao.json'), 'w'), indent=1)
print('AO wrote', OUT_GLB, os.path.getsize(OUT_GLB) // 1024, 'KB', png, os.path.getsize(png) // 1024, 'KB')

# ---------------------------------------------------------------- optional check render: unlit base colour x AO
if 'check' in ARGS:
    MIXES = []; aoimg = bpy.data.images.load(png); aoimg.colorspace_settings.name = 'Non-Color'
    for m in {s.material for o in BAKE for s in o.material_slots if s.material}:
        nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not bsdf: continue
        uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = 'lightmap'
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = aoimg; nt.links.new(uv.outputs[0], tex.inputs[0])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1
        base = bsdf.inputs['Base Color']
        if base.links: nt.links.new(base.links[0].from_socket, mix.inputs[6])
        else: mix.inputs[6].default_value = base.default_value
        nt.links.new(tex.outputs[0], mix.inputs[7])
        em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(mix.outputs[2], em.inputs[0]); MIXES.append((mix, nt))
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'); nt.links.new(em.outputs[0], out.inputs[0])
    pos, tgt, lens = CAMS[MID]
    cd = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cd); SC.collection.objects.link(cam); SC.camera = cam
    cam.location = (pos[0], -pos[2], pos[1]); cd.lens = lens; cd.clip_start = .1
    cam.rotation_euler = (Vector((tgt[0], -tgt[2], tgt[1])) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.engine = 'CYCLES'; SC.cycles.samples = 16; SC.view_settings.view_transform = 'Standard'
    SC.render.resolution_x, SC.render.resolution_y = 1600, 900
    SC.render.filepath = os.path.join(TMP, MID + '_check.png'); bpy.ops.render.render(write_still=True)
    for mix, nt in MIXES: mix.inputs[6].default_value = (1, 1, 1, 1); [nt.links.remove(l) for l in mix.inputs[6].links]
    SC.render.filepath = os.path.join(TMP, MID + '_check_ao.png'); bpy.ops.render.render(write_still=True)
print('AO done', MID)
