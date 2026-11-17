
# ---------------------------------------------------------------- build, stage, shots, export
def join_groups():
    out = {}
    for key, name in (('body', 'siao_body'), ('head', 'siao_head'), ('gear', 'siao_headgear')):
        obs = [o for o in GROUPS[key] if o.name in bpy.data.objects]
        if key == 'head': out[key] = obs[0]; out[key].name = name; continue
        for o in obs:
            if o.data.users == 1 and not o.modifiers: pass
        H.select_only(obs, obs[0]); bpy.ops.object.join(); o = bpy.context.view_layer.objects.active; o.name = name; out[key] = o
    return out

def look_at(o, target):
    o.rotation_euler = (V(target) - o.location).to_track_quat('-Z', 'Y').to_euler()

def stage():
    w = bpy.data.worlds.new('World'); SC.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (.5, .62, .85, 1); bg.inputs[1].default_value = .45
    def lamp(name, kind, loc, energy, col, size=2.0, tgt=(0, .2, 1.1)):
        d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = col
        if kind == 'AREA': d.size = size
        else: d.spot_size = 1.0; d.spot_blend = .7; d.shadow_soft_size = .3
        o = bpy.data.objects.new(name, d); SC.collection.objects.link(o); o.location = loc; look_at(o, tgt); return o
    lamp('key', 'AREA', (1.9, 4.9, 6.0), 1800, (1.0, .79, .54), 2.2)
    lamp('fill', 'AREA', (-5.0, 3.5, 2.2), 420, (.62, .76, 1.0), 5.0)
    lamp('rim', 'SPOT', (-3.2, -4.6, 3.8), 5200, (1.0, .78, .52))
    prof = [(14, 0)] + [(-5 - 4 * math.sin(a), 4 - 4 * math.cos(a)) for a in [math.pi / 2 * i / 16 for i in range(17)]] + [(-9, 16)]
    vs = [(x, y, z) for (y, z) in prof for x in (-30, 30)]
    fs = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(prof) - 1)]
    me = bpy.data.meshes.new('cyc'); me.from_pydata(vs, [], fs); me.polygons.foreach_set('use_smooth', [True] * len(fs))
    m = bpy.data.materials.new('cyc'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (.46, .44, .42, 1); b.inputs['Roughness'].default_value = .85
    me.materials.append(m); SC.collection.objects.link(bpy.data.objects.new('cyc', me))
    SC.render.engine = 'BLENDER_EEVEE'; SC.eevee.taa_render_samples = 16 if QUICK else 96
    SC.view_settings.view_transform = 'AgX'; SC.view_settings.look = 'AgX - Punchy'
    SC.render.image_settings.file_format = 'PNG'; SC.render.film_transparent = False
    try: SC.eevee.use_raytracing = True
    except Exception: pass
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'HORIZONTAL'; cam = bpy.data.objects.new('cam', cd)
    SC.collection.objects.link(cam); SC.camera = cam; return cam

def shoot(cam, path, w, h, az, dist, target, width_m, cam_z=None):
    SC.render.resolution_x = w; SC.render.resolution_y = h; t = V(target); a = math.radians(az)
    cam.location = (t.x - dist * math.sin(a), t.y + dist * math.cos(a), cam_z if cam_z is not None else t.z)
    cam.data.lens = dist * 36 / width_m; look_at(cam, t)
    SC.render.filepath = path; bpy.ops.render.render(write_still=True)

def row(paths, out, cols=None):
    ims = []
    for p in paths:
        im = bpy.data.images.load(p); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); ims.append(a.reshape(h, w, 4))
    cols = cols or len(ims)
    rows = [np.concatenate(ims[i:i + cols], axis=1) for i in range(0, len(ims), cols)][::-1]
    a = np.concatenate(rows, axis=0); h, w = a.shape[:2]
    o = bpy.data.images.new('row', w, h, alpha=False); o.pixels.foreach_set(a.ravel()); o.filepath_raw = out; o.file_format = 'PNG'; o.save()

def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

def main():
    build_body(); build_arms(); build_head_gear(); build_face()
    print('BREAK', sorted([(o.name, tris(o)) for g in GROUPS.values() for o in g if o.name in bpy.data.objects], key=lambda t: -t[1])[:14])
    objs = join_groups(); body, head, gear = objs['body'], objs['head'], objs['gear']
    for o in (body, head, gear):
        H.select_only([o], o); o.scale = (KSC, KSC, KSC); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); o.data.update()
    print('SIAO_TRIS', {o.name: tris(o) for o in (body, head, gear)}, 'total', sum(tris(o) for o in (body, head, gear)))
    # shape keys carry no tangents. weights of joined body were set before joining.
    rig = make_armature()
    for o in (body, head, gear):
        o.parent = rig; md = o.modifiers.new('arm', 'ARMATURE'); md.object = rig
    # gear and body groups: ensure every vertex weighted
    for o in (body, head, gear):
        loose = sum(1 for v in o.data.vertices if not v.groups); print('unweighted', o.name, loose)
    face = head
    cam = stage()
    reset_pose(rig); set_expr(face, None)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(TMP, 'siao_rig.blend'))
    # actions
    SC.render.fps = FPS
    rig.animation_data_create()
    acts = [make_action(rig, 'idle', 'idle', 60), make_action(rig, 'run', 'run', 24), make_action(rig, 'attack', 'attack', 18, loop=False), make_action(rig, 'ult', 'ult', 2)]
    rig.animation_data.action = None
    for a in acts:
        tr = rig.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, a); tr.mute = True
    reset_pose(rig)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'siao.blend'))
    # export
    for k in face.data.shape_keys.key_blocks: k.value = 0.0
    for o in list(bpy.data.objects):
        if o.name in ('cyc',) or o.type in ('LIGHT', 'CAMERA'): o.select_set(False)
    H.select_only([body, head, gear, rig], rig)
    os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
        export_animations=True, export_animation_mode='ACTIONS', export_nla_strips=True, export_skins=True, export_def_bones=False,
        export_morph=True, export_morph_normal=False, export_image_format='AUTO', export_materials='EXPORT', export_texcoords=True,
        export_normals=True, export_all_influences=False, export_optimize_animation_size=True)
    print('EXPORT', OUT_GLB, os.path.getsize(OUT_GLB) // 1024, 'KB')
    # shots
    tmp = os.path.join(TMP, 'shots'); os.makedirs(tmp, exist_ok=True)
    def play(name, f):
        rig.animation_data.action = bpy.data.actions[name]; SC.frame_set(f + 5); SC.frame_set(f); bpy.context.view_layer.update()
    rig.animation_data.action = None; reset_pose(rig)
    play('idle', 0)
    shoot(cam, os.path.join(OUT, 'beauty.png'), 1600, 1600, 28, 8, (0, .05, .96), 2.8, cam_z=1.1)
    ps = []
    for i, az in enumerate((0, 90, 180)):
        rig.rotation_euler = (0, 0, math.radians(-az)); bpy.context.view_layer.update()
        p = os.path.join(tmp, f't{i}.png'); ps.append(p); shoot(cam, p, 534, 800, 0, 9, (0, 0, .96), 2.15, cam_z=.96)
    rig.rotation_euler = (0, 0, 0); row(ps, os.path.join(OUT, 'turnaround.png'))
    rig.animation_data.action = None; reset_pose(rig); ps = []
    for name in ('smile', 'angry', 'grin', 'ult'):
        set_expr(face, name); p = os.path.join(tmp, 'e_%s.png' % name); ps.append(p); shoot(cam, p, 400, 440, 0, 7, (0, 0, 1.44), 1.35)
    row(ps, os.path.join(OUT, 'expressions.png')); set_expr(face, None)
    ps = []
    for name, n in (('idle', 60), ('run', 24), ('attack', 18), ('ult', 2)):
        for i in range(4):
            play(name, int(i * n / 4)); p = os.path.join(tmp, f'{name}_{i}.png'); ps.append(p)
            shoot(cam, p, 400, 500, 35, 7, (0, .1, 0.92), 2.25, cam_z=1.1)
    row(ps, os.path.join(OUT, 'anim_sheet.png'), 4)

main()
