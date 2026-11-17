import bpy,sys
from mathutils import Vector as V
bpy.ops.wm.open_mainfile(filepath='/Users/nigelyeap/Documents/lunchliao-hd/tools/blender/heroes_toy/_tmp_gym/gym_build.blend')
for n,(E,W) in {'arm_r':(V((.60,.06,.42)),V((.50,.34,.48))),'arm_l':(V((-.60,.02,.40)),V((-.60,.10,.27)))}.items():
    o=bpy.data.objects[n]; ax=(W-E).normalized(); L=(W-E).length
    for t in (.7,.8,.86,.92,1.0):
        c=E+(W-E)*t; best=0;n_=0
        for v in o.data.vertices:
            d=v.co-c
            if abs(d.dot(ax))<.01:
                r=(d-ax*d.dot(ax)).length; best=max(best,r)
        # centroid offset
        pts=[v.co for v in o.data.vertices if abs((v.co-c).dot(ax))<.01]
        import numpy as np
        P=np.array([list(p) for p in pts]); cen=V(((P.max(0)+P.min(0))/2).tolist()); off=(cen-c-ax*(cen-c).dot(ax)).length
        print(n,t,'maxr',round(best,3),'centroid_off',round(off,3))
