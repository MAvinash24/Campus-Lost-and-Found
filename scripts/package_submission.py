"""Archive reviewable source and deliverables without private runtime state."""
import hashlib,json,zipfile,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'deliverables';archive=out/'College_Lost_and_Found_Complete.zip'
dirs={'.runtime','.runtime_v2','.tools','.git','data','__pycache__','.venv','.pytest_cache'}
files=[]
for p in root.rglob('*'):
    if not p.is_file():continue
    rel=p.relative_to(root)
    if any(x in dirs for x in rel.parts) or 'qa' in rel.parts or '.tmp' in rel.parts:continue
    if p.name in {'.env','.local-secrets.json','package-manifest.json'} or p.suffix in {'.pyc','.zip'} or p.name.endswith('_raw.jpg'):continue
    if p.name=='tests-initial.txt':continue
    files.append((p,rel.as_posix()))
manifest={'archive':archive.name,'files':[]}
for p,rel in files:
    data=p.read_bytes()
    assert not re.search(rb'ATAT[T][A-Za-z0-9_-]{30,}',data),'Unexpected Jira credential pattern in '+rel
    manifest['files'].append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p,rel in files:z.write(p,rel)
    z.writestr('MANIFEST.json',json.dumps(manifest,indent=2))
manifest['archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
(out/'package-manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print('Verified archive:',len(files),'files;',archive.stat().st_size,'bytes;',manifest['archive_sha256'])
