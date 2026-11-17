import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath='/Users/nigelyeap/Documents/lunchliao-hd/tools/blender/heroes_toy/_tmp_nsboy/nsboy_anim.blend')
o=bpy.data.objects['nsboy_body']; me=o.data
mi=[i for i,m in enumerate(me.materials) if m.name.startswith('camo')]; print('camo slots', mi, [m.name for m in me.materials if m.name.startswith('camo')])
uv=np.zeros(len(me.loops)*2); me.uv_layers.active.data.foreach_get('uv',uv); uv=uv.reshape(-1,2)
im=bpy.data.images['nsboy_camo']; w,h=im.size; px=np.array(im.pixels[:]).reshape(h,w,4)
cols=[]
for p in me.polygons:
    if p.material_index in mi:
        for li in p.loop_indices:
            u,v=uv[li]%1.0; cols.append(tuple(px[int(v*h)%h,int(u*w)%w,:3].round(2)))
from collections import Counter; print(Counter(cols).most_common(5), len(cols))
print('uv layers', [l.name for l in me.uv_layers], 'active render', [l.active_render for l in me.uv_layers])
m=bpy.data.materials['camo']; t=[n for n in m.node_tree.nodes if n.type=='TEX_IMAGE'][0]; print(t.image.name, t.image.source, t.image.colorspace_settings.name, t.interpolation)
