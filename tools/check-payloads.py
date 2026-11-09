"""Check every raci/1 structured note in rules/ against schemas/raci-1.schema.json (SPEC.md section 6.1).

Run from the repository root: python tools/check-payloads.py. Needs the jsonschema package.
A payload fails if it is invalid or is not in canonical form (sorted members, no whitespace).
"""
import json,glob,sys
from jsonschema import Draft202012Validator
schema=json.load(open('schemas/raci-1.schema.json'))
Draft202012Validator.check_schema(schema)
v=Draft202012Validator(schema)
bad=0;n=0
for f in sorted(glob.glob('rules/*.json')):
    if f.endswith('realm.json'): continue
    for note in json.load(open(f)).get('notes',[]):
        if note['type']!='structured': continue
        fmt,payload=note['content'].split(':',1); n+=1
        assert fmt=='raci/1',fmt
        obj=json.loads(payload)
        canon=json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)
        errs=list(v.iter_errors(obj))
        print(note['id'],'OK' if not errs and canon==payload else 'BAD', '' if canon==payload else 'non-canonical')
        for e in errs: print('  ',e.message[:200]); 
        bad+=bool(errs) or canon!=payload
print(n,'payloads',bad,'bad'); sys.exit(1 if bad else 0)
