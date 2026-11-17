"""Mesh helpers for scripted heroes: primitive soups unioned by voxel remesh, then smoothed and decimated.
Blender axes here: Z up, the hero faces +Y (the glTF exporter turns that into Y up, facing -Z)."""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Quaternion

def V(*a): return Vector(a)

def override(obj):
    return bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj],
                                     selected_editable_objects=[obj])

def select_only(objs, active=None):
    for o in bpy.data.objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]

class Soup:
    """Collect closed primitives into one bmesh, then remesh into a single organic shell."""
    def __init__(self, name):
        self.name = name; self.bm = bmesh.new()

    def _xf(self, verts, mat):
        for v in verts: v.co = mat @ v.co

    def sphere(self, c, r, seg=24):
        g = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
        self._xf(g['verts'], Matrix.Translation(Vector(c)) @ Matrix.Diagonal((r, r, r, 1)) if isinstance(r, (int, float))
                 else Matrix.Translation(Vector(c)) @ Matrix.Diagonal((r[0], r[1], r[2], 1)))
        return self

    def ellipsoid(self, c, radii, rot=None, seg=24):
        g = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
        m = Matrix.Translation(Vector(c))
        if rot is not None: m = m @ rot.to_matrix().to_4x4() if hasattr(rot, 'to_matrix') else m @ rot
        m = m @ Matrix.Diagonal((radii[0], radii[1], radii[2], 1))
        self._xf(g['verts'], m); return self

    def capsule(self, p0, p1, r0, r1=None, seg=16):
        """Tapered capsule from p0 (radius r0) to p1 (radius r1)."""
        r1 = r0 if r1 is None else r1
        p0 = Vector(p0); p1 = Vector(p1); d = p1 - p0; L = d.length
        if L > 1e-6:
            g = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=L)
            q = d.normalized().to_track_quat('Z', 'Y')
            self._xf(g['verts'], Matrix.Translation((p0 + p1) * .5) @ q.to_matrix().to_4x4())
        self.sphere(p0, r0, seg); self.sphere(p1, r1, seg); return self

    def box(self, c, size, rot=None):
        g = bmesh.ops.create_cube(self.bm, size=1.0)
        m = Matrix.Translation(Vector(c))
        if rot is not None: m = m @ rot.to_matrix().to_4x4()
        m = m @ Matrix.Diagonal((size[0], size[1], size[2], 1))
        self._xf(g['verts'], m); return self

    def to_object(self):
        me = bpy.data.meshes.new(self.name); self.bm.to_mesh(me); self.bm.free()
        ob = bpy.data.objects.new(self.name, me); bpy.context.scene.collection.objects.link(ob); return ob

    def remesh(self, voxel=0.012, smooth=4, smooth_factor=0.5, target_tris=None, keep_hi=False):
        """Union everything: voxel remesh, smooth the stepping, optional decimate. Returns (lo, hi or None)."""
        ob = self.to_object()
        m = ob.modifiers.new('remesh', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = voxel; m.use_smooth_shade = True
        apply_mod(ob, m)
        if smooth:
            s = ob.modifiers.new('smooth', 'SMOOTH'); s.factor = smooth_factor; s.iterations = smooth; apply_mod(ob, s)
        hi = None
        if keep_hi:
            hi = ob.copy(); hi.data = ob.data.copy(); hi.name = ob.name + '_hi'; bpy.context.scene.collection.objects.link(hi)
        if target_tris: decimate(ob, target_tris)
        shade_smooth(ob)
        return ob, hi

def apply_mod(ob, mod):
    with override(ob): bpy.ops.object.modifier_apply(modifier=mod.name)

def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)

def decimate(ob, target_tris):
    n = tri_count(ob)
    if n <= target_tris: return
    d = ob.modifiers.new('dec', 'DECIMATE'); d.ratio = target_tris / n; d.use_collapse_triangulate = True
    apply_mod(ob, d)

def shade_smooth(ob):
    for p in ob.data.polygons: p.use_smooth = True

def boolean_cut(ob, cutter, solver='EXACT'):
    b = ob.modifiers.new('cut', 'BOOLEAN'); b.operation = 'DIFFERENCE'; b.object = cutter; b.solver = solver
    apply_mod(ob, b)
    bpy.data.objects.remove(cutter, do_unlink=True)

def join(objs, name):
    """Join objects into the first one. Keeps per-object material slots."""
    select_only(objs, objs[0])
    with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs):
        bpy.ops.object.join()
    objs[0].name = name; objs[0].data.name = name; return objs[0]

def set_material(ob, mat):
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for p in ob.data.polygons: p.material_index = 0

def flat_material(name, rgb, rough=.6, metal=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    return m

def torus(name, c, R, r, rot=None, seg=24, rseg=8):
    bpy.ops.mesh.primitive_torus_add(major_segments=seg, minor_segments=rseg, major_radius=R, minor_radius=r, location=c)
    ob = bpy.context.object; ob.name = name
    if rot is not None: ob.rotation_euler = rot
    return ob

def apply_transforms(ob):
    with override(ob): bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def smart_uv(ob, angle=66, margin=0.004):
    select_only([ob], ob)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')

def srgb(hexstr):
    """'#RRGGBB' -> linear rgb tuple."""
    h = hexstr.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c)
