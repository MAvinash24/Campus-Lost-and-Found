"""AST-based project checks; not a substitute for dependency or full security review."""
import ast
import json
from pathlib import Path

findings=[]
for path in [Path('app.py'),Path('wsgi.py'),Path('scripts/bootstrap.py')]:
    tree=ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.Call):
            name=ast.unparse(node.func)
            if name in ('eval','exec','os.system','pickle.loads'):
                findings.append({'file':str(path),'line':node.lineno,'rule':'dangerous execution'})
            for kw in node.keywords:
                if kw.arg=='debug' and isinstance(kw.value,ast.Constant) and kw.value.value is True:
                    findings.append({'file':str(path),'line':node.lineno,'rule':'debug enabled'})
        if isinstance(node,ast.Assign):
            for target in node.targets:
                name=ast.unparse(target).lower()
                if any(s in name for s in ('password','token','secret')) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str) and len(node.value.value)>8:
                    findings.append({'file':str(path),'line':node.lineno,'rule':'literal credential candidate'})
result={'tool':'project AST security check','files_checked':3,'findings':findings,'passed':not findings}
Path('deliverables/evidence').mkdir(parents=True,exist_ok=True)
Path('deliverables/evidence/static-check.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
raise SystemExit(bool(findings))
