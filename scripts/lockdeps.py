import json
import urllib.request
from pathlib import Path
out=[]
for line in Path('requirements.txt').read_text().splitlines():
    if not line or line.startswith('#'):continue
    name,version=line.split('==',1)
    version=version.split(';')[0].strip()
    with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json',timeout=45) as r:meta=json.load(r)
    hashes=sorted({u['digests']['sha256'] for u in meta['urls']})
    out.append(line+' \\\n'+' \\\n'.join('    --hash=sha256:'+v for v in hashes))
Path('requirements.lock').write_text('\n'.join(out)+'\n')
print('Created all-platform hash lock for',len(out),'explicit dependencies.')
