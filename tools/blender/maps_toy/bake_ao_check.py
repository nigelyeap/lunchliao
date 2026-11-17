"""python3 bake_ao_check.py <id>: compare <id>_lit.glb against <id>.glb (names, transforms, materials, TEXCOORD_1)."""
import json, struct, sys, os

MAPS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'assets', 'maps')
def load(p):
    b = open(p, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; return json.loads(b[20:20 + n]), len(b)

mid = sys.argv[1]
a, sa = load(os.path.join(MAPS, mid + '.glb')); b, sb = load(os.path.join(MAPS, mid + '_lit.glb'))
meta = json.load(open(os.path.join(MAPS, mid + '_ao.json')))
trs = lambda n: [round(x, 4) for k in ('translation', 'rotation', 'scale', 'matrix') for x in n.get(k, [])]
na = {n['name']: n for n in a['nodes']}; nb = {n['name']: n for n in b['nodes']}
bad = []
if set(na) != set(nb): bad.append(('node names differ', set(na) ^ set(nb)))
for k in set(na) & set(nb):
    if trs(na[k]) != trs(nb[k]): bad.append(('transform', k))
    pa = lambda j, n: sorted(nm['name'] for nm in j['nodes'] if nm in [j['nodes'][c] for c in n.get('children', [])])
    if pa(a, na[k]) != pa(b, nb[k]): bad.append(('children', k))
ma = sorted(m['name'] for m in a['materials']); mb = sorted(m['name'] for m in b['materials'])
if ma != mb: bad.append(('materials', set(ma) ^ set(mb)))
rnd = lambda v: round(v, 5) if isinstance(v, float) else [rnd(x) for x in v] if isinstance(v, list) else {k: rnd(x) for k, x in v.items()} if isinstance(v, dict) else v
strip = lambda m: json.dumps(rnd({k: v for k, v in m.items() if k != 'pbrMetallicRoughness'} | {'pbr': {k: v for k, v in m.get('pbrMetallicRoughness', {}).items() if 'Texture' not in k}}), sort_keys=True)
for m1 in a['materials']:
    m2 = next(m for m in b['materials'] if m['name'] == m1['name'])
    if strip(m1) != strip(m2): bad.append(('material props', m1['name']))
uv1 = {n['name'] for n in b['nodes'] if 'mesh' in n and all('TEXCOORD_1' in p['attributes'] for p in b['meshes'][n['mesh']]['primitives'])}
any1 = {n['name'] for n in b['nodes'] if 'mesh' in n and any('TEXCOORD_1' in p['attributes'] for p in b['meshes'][n['mesh']]['primitives'])}
if uv1 != set(meta['meshes']) or any1 != uv1: bad.append(('TEXCOORD_1 set != json', uv1 ^ set(meta['meshes']), any1 - uv1))
lost0 = [n['name'] for n in a['nodes'] if 'mesh' in n and any('TEXCOORD_0' in p['attributes'] for p in a['meshes'][n['mesh']]['primitives'])
         and not all('TEXCOORD_0' in p['attributes'] for p in b['meshes'][nb[n['name']]['mesh']]['primitives'])]
if lost0: bad.append(('lost TEXCOORD_0', lost0))
print(mid, 'glb %.1f -> %.1f MB' % (sa / 2**20, sb / 2**20), 'lightmapped', len(uv1), 'of', sum('mesh' in n for n in b['nodes']))
print('OK' if not bad else bad)
