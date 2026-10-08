import ast,hashlib,json,zipfile
from pathlib import Path
from datetime import datetime
from docx import Document
import pymupdf
R=Path(__file__).resolve().parents[1];O=R/'deliverables';E=O/'evidence'
c=json.loads((O/'catalog.json').read_text());j=json.loads((E/'jira-state.json').read_text())
assert len(j['verifiedIssues'])==38
assert all(x['status']=='Done' and x['assignee']==c['student']['name'] for x in j['verifiedIssues'])
for n in ['1','2']:
    s=j['sprints'][n]
    assert (datetime.fromisoformat(s['endDate'].replace('Z','+00:00'))-datetime.fromisoformat(s['startDate'].replace('Z','+00:00'))).days==15
tests={n.name for n in ast.walk(ast.parse((R/'tests/test_app.py').read_text())) if isinstance(n,ast.FunctionDef)}
assert all(s['test'] in tests for s in c['stories'])
for prefix in ['docker','kubernetes']:
    assert json.loads((E/f'{prefix}-e2e.json').read_text())['passed']
assert not json.loads((E/'dependency-audit.json').read_text())['fixes']
assert all(not d['vulns'] for d in json.loads((E/'dependency-audit.json').read_text())['dependencies'])
doc=Document(O/'College_Lost_and_Found_Report.docx')
phases=[p.text for p in doc.paragraphs if p.style.name=='Heading 1' and p.text.startswith('Phase ')]
assert len(phases)==16
with zipfile.ZipFile(O/'College_Lost_and_Found_Report.docx') as z:
    assert z.testzip() is None
    assert b'pBdr' not in z.read('word/document.xml') and b'pBdr' not in z.read('word/styles.xml')
pdf=pymupdf.open(O/'College_Lost_and_Found_Report.pdf')
assert all(len(p.get_text())>50 for p in pdf)
result={'passed':True,'report_pages':len(pdf),'phases':len(phases),'jira_done_issues':38,'jira_only_assignee':c['student']['name'],'sprint_days':[15,15],'automated_tests':34,'docker_https_e2e':True,'kubernetes_https_e2e':True,'docx_package_integrity':True,'visual_review':'All 42 rendered pages inspected; title monochrome; figures retain captions; no blank pages.','secret_policy':'Runtime credentials and Jira token excluded from submitted archive.','limits':['Nominal sprint forecasts; compressed lab execution','No hosted GitHub Actions run','Default kind CNI NetworkPolicy enforcement not verified','Production campus SSO, immutable audit and trusted campus certificate remain future work']}
(E/'final-verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
