import bpy, sys, os, math, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, HERE + '/../../heroes')
import bl, head, render_lib as RL
t = time.time()
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
objs = head.build(None)
print('built', time.time() - t, {k: bl.tris(v) for k, v in objs.items()})
RL.setup_render(1000, 1000, 32)
import shots_lib as SL
SL.light((0, 0, 0)); 
S = '/tmp/lunchliao-scratch/'
ex = (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []) or ['smile']
for e in ex:
    head.set_expr(objs.values(), e)
    RL.shoot(S + 'th_%s.png' % e, (-0.65, 1.75, 0.0), (0, 0, -0.03), 60)
RL.shoot(S + 'th_side.png', (-1.6, -1.2, 0.3), (0, 0, 0.05), 60)
