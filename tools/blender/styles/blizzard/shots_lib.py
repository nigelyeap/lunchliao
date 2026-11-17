"""Shared bake-off lighting: golden-hour key front-left 45 up, cool sky fill, warm rim back-right, neutral floor."""
import bpy, sys, os
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../../heroes')
import render_lib as RL

def light(target=(0, 0, 1.1), floor_z=None):
    w = bpy.data.worlds.get('World') or bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.50, 0.62, 0.80, 1); bg.inputs[1].default_value = 0.45
    t = Vector(target)
    def lamp(name, kind, off, energy, col, size=2.0):
        d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = col
        if kind == 'AREA': d.size = size
        if kind == 'SPOT': d.spot_size = 1.0; d.spot_blend = .7
        o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o); o.location = t + Vector(off)
        RL.look_at(o, t); return o
    # hero faces +Y, camera sits at +Y, so camera-left is +X
    lamp('key', 'AREA', (3.6, 3.6, 5.0), 3000, (1.0, 0.80, 0.56), 2.5)
    lamp('fill', 'AREA', (-4.5, 3.0, 1.5), 380, (0.62, 0.78, 1.0), 5)
    lamp('rim', 'SPOT', (-2.6, -4.2, 3.6), 9000, (1.0, 0.72, 0.42))
    if floor_z is not None:
        p = RL.floor(floor_z, 60); p.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.20, 0.195, 0.19, 1)
    bpy.context.scene.eevee.use_shadows = True
