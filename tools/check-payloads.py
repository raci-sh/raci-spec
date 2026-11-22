"""Check the schemas in schemas/, then every raci/1 structured note in rules/ against
schemas/raci-1.schema.json (SPEC.md section 6.1).

Run from the repository root: python tools/check-payloads.py. Needs the jsonschema package.
A schema fails if it is not a valid draft 2020-12 schema or if one of its $ref targets does not
resolve among the schemas of schemas/. A payload fails if it is invalid or is not in canonical
form (sorted members, no whitespace).
"""
import json,glob,sys
from jsonschema import Draft202012Validator
from referencing import Registry,Resource
from referencing.exceptions import Unresolvable
schemas={f:json.load(open(f)) for f in sorted(glob.glob('schemas/*.schema.json'))}
registry=Registry().with_resources((s['$id'],Resource.from_contents(s)) for s in schemas.values())
def refs(node):
    if isinstance(node,dict):
        if isinstance(node.get('$ref'),str): yield node['$ref']
        for x in node.values(): yield from refs(x)
    elif isinstance(node,list):
        for x in node: yield from refs(x)
bad=0
for f,s in schemas.items():
    Draft202012Validator.check_schema(s)
    resolver=registry.resolver(base_uri=s['$id'])
    for r in sorted(set(refs(s))):
        try: resolver.lookup(r)
        except Unresolvable as e: print(f,'BAD unresolvable $ref',repr(r)); bad+=1
print(len(schemas),'schemas',bad,'bad')
v=Draft202012Validator(schemas['schemas/raci-1.schema.json'],registry=registry)
n=0
for f in sorted(glob.glob('rules/*.json')):
    if f.endswith('realm.json'): continue
    for note in json.load(open(f)).get('notes',[]):
        if note['type']!='structured': continue
        n+=1
        fmt,sep,payload=note['content'].partition(':')
        if not sep or fmt!='raci/1':
            print(note['id'],'BAD unsupported format',repr(fmt)); bad+=1; continue
        obj=json.loads(payload)
        canon=json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)
        errs=list(v.iter_errors(obj))
        print(note['id'],'OK' if not errs and canon==payload else 'BAD', '' if canon==payload else 'non-canonical')
        for e in errs: print('  ',e.message[:200]); 
        bad+=bool(errs) or canon!=payload
print(n,'payloads',bad,'bad'); sys.exit(1 if bad else 0)
