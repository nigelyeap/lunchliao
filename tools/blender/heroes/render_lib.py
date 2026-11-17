"""Shared EEVEE check-shot helpers. Imported by the hero scripts (sys.path is set by the caller)."""
import bpy, math
from mathutils import Vector

def setup_render(w=1024, h=1024, samples=32):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.eevee.taa_render_samples = samples
    sc.render.resolution_x = w; sc.render.resolution_y = h
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Punchy'
    sc.render.image_settings.file_format = 'PNG'

def studio_light(target=(0, 1, 0)):
    """Warm key, cool fill, rim. Golden hour-ish."""
    w = bpy.data.worlds.get('World') or bpy.data.worlds.new('World')
    bpy.context.scene.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.55, 0.62, 0.72, 1); bg.inputs[1].default_value = 0.35
    def lamp(name, kind, loc, energy, col, size=1.5, spot=None):
        d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = col
        if kind == 'AREA': d.size = size
        if kind == 'SPOT': d.spot_size = spot or 1.2; d.spot_blend = .6
        o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o); o.location = loc
        look_at(o, Vector(target)); return o
    lamp('key', 'AREA', (3.5, -4.5, 5), 1200, (1.0, 0.86, 0.68), size=2.5)
    lamp('fill', 'AREA', (-4.5, -3.5, 2.5), 350, (0.7, 0.8, 1.0), size=4)
    lamp('rim', 'SPOT', (-1.5, 4.5, 4.0), 1500, (1.0, 0.92, 0.8), spot=1.0)
    bpy.context.scene.eevee.use_shadows = True

def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def camera(loc, target, lens=50):
    cd = bpy.data.cameras.new('cam'); cd.lens = lens
    cam = bpy.data.objects.new('cam', cd); bpy.context.scene.collection.objects.link(cam)
    cam.location = loc; look_at(cam, Vector(target)); bpy.context.scene.camera = cam
    return cam

def floor(z=0, size=30):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    p = bpy.context.object; p.name = 'floor'
    m = bpy.data.materials.new('floor'); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0.42, 0.40, 0.37, 1); b.inputs['Roughness'].default_value = .9
    p.data.materials.append(m); return p

def shoot(path, cam_loc, target, lens=50):
    cam = bpy.context.scene.camera
    if cam is None: cam = camera(cam_loc, target, lens)
    cam.location = cam_loc; cam.data.lens = lens; look_at(cam, Vector(target))
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
