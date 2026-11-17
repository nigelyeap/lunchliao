# Contact sheets. blender -b -P _sheet.py -- props|tex
import sys, os, math, bpy
from mathutils import Vector
ROOT = '/Users/nigelyeap/Documents/lunchliao-hd'
mode = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sc = bpy.context.scene
def setup(res, ortho=None, cam=None, look=None, lens=50):
    sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = res
    w = bpy.data.worlds.new('w'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.95, 0.85, 0.68, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.3; sc.world = w
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 2.6; sun.data.color = (1, 0.82, 0.58); sun.rotation_euler = (math.radians(55), math.radians(10), math.radians(-35)); sc.collection.objects.link(sun)
    fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); fill.data.energy = 0.6; fill.data.color = (0.7, 0.8, 1); fill.rotation_euler = (math.radians(70), 0, math.radians(150)); sc.collection.objects.link(fill)
    c = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(c); sc.camera = c
    c.data.lens = lens
    if ortho: c.data.type = 'ORTHO'; c.data.ortho_scale = ortho
    c.location = cam; c.rotation_euler = (Vector(look) - Vector(cam)).to_track_quat('-Z', 'Y').to_euler()
def label(t, loc, size=0.22):
    d = bpy.data.curves.new(t, 'FONT'); d.body = t; d.size = size; d.align_x = 'CENTER'
    o = bpy.data.objects.new(t, d); o.location = loc; o.rotation_euler = (math.radians(90), 0, 0); sc.collection.objects.link(o)
    m = bpy.data.materials.new('lbl'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs[0].default_value = (0.12, 0.08, 0.05, 1); d.materials.append(m)
def ground(size=40, z=0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z)); g = bpy.context.object
    m = bpy.data.materials.new('g'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs[0].default_value = (0.62, 0.52, 0.42, 1); m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9; g.data.materials.append(m)

if mode == 'props':
    P = ROOT + '/assets/props/'
    layout = [('stall_front', -5.2, 0, 1, 0), ('hawker_table', -1.6, 0, 1, 0), ('tray_return_rack', 0.9, 0, 1, 0), ('stockpot_wok', 2.8, 0, 1, 0), ('bin', 4.6, 0, 1, 0),
              ('stool_plastic_red', -5.8, -3.3, 1, 0), ('stool_plastic_blue', -4.9, -3.3, 1, 0), ('teh_tarik', -3.6, -3.3, 2.5, 0), ('bowls_plates', -2.2, -3.3, 2.5, 0), ('chope_tissue', -0.9, -3.3, 6, 0),
              ('ceiling_fan', 1.0, -3.3, 1, 1.5), ('fluorescent_tube', 4.0, -3.3, 1, 1.5)]
    setup((2600, 1300), cam=(-0.6, -17.5, 4.2), look=(-0.6, -1.3, 0.9), lens=32); ground(40)
    for name, x, y, s, dz in layout:
        bpy.ops.import_scene.gltf(filepath=P + name + '.glb')
        new = [o for o in bpy.context.selected_objects]
        top = [o for o in new if o.parent is None]
        e = bpy.data.objects.new('e_' + name, None); sc.collection.objects.link(e); e.location = (x, y, dz); e.scale = (s, s, s)
        for o in top: o.parent = e
        label(name + (f' x{s}' if s != 1 else ''), (x, y - 0.9, -0.3 if dz == 0 else 0.0), 0.2)
        if name == 'ceiling_fan':
            for o in bpy.data.objects:
                if o.name.startswith('FAN_rotor'): o.rotation_mode = 'XYZ'
elif mode == 'tex':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _common import tex, reset
    names = ['floor_tile', 'wall_tile', 'steel_brushed', 'formica', 'concrete_painted', 'plywood', 'plastic_blue', 'plastic_red']
    setup((2400, 880), ortho=17.8, cam=(0, -20, 0), look=(0, 0, 0))
    for i, n in enumerate(names):
        x = (i - 3.5) * 2.2; m = tex(n)
        nt = m.node_tree; mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (2, 2, 2); tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
        for nd in nt.nodes:
            if nd.type == 'TEX_IMAGE': nt.links.new(mp.outputs['Vector'], nd.inputs['Vector'])
        bpy.ops.mesh.primitive_plane_add(size=2.0, location=(x, 0, 1.15), rotation=(math.radians(90), 0, 0)); bpy.context.object.data.materials.append(m)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24, location=(x, 0, -1.15)); s = bpy.context.object; bpy.ops.object.shade_smooth(); s.data.materials.append(m)
        label(n, (x, -0.1, -2.5), 0.17)
    bpy.data.worlds['w'].node_tree.nodes['Background'].inputs[0].default_value = (0.9, 0.85, 0.75, 1)
sc.render.filepath = f"{ROOT}/shots/props/{'sheet' if mode == 'props' else 'tex'}.png"
sc.view_settings.view_transform = 'AgX' if 'AgX' in [v.identifier for v in sc.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Standard'
bpy.ops.render.render(write_still=True)
