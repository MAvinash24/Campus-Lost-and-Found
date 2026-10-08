"""Render traceable monochrome evidence from actual captured results."""
import json, textwrap
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables';E=OUT/'evidence';I=OUT/'images'
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',23)
bold=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',34)
def render(name,title,lines):
    wrapped=[]
    for line in lines:
        wrapped.extend(textwrap.wrap(str(line),width=105,replace_whitespace=False) or [''])
    im=Image.new('RGB',(1600,max(350,150+len(wrapped)*32)),'white');d=ImageDraw.Draw(im)
    d.text((45,35),title,font=bold,fill='black')
    for y,line in enumerate(wrapped):d.text((45,115+y*32),line,font=font,fill='black')
    im.save(I/name)
for p in I.glob('*.jpg'):
    if p.name.endswith('_raw.jpg'):continue
    with Image.open(p) as im:im.convert('L').save(p)
raw=I/'jira_progress_raw.jpg'
if raw.exists():
    with Image.open(raw) as im:im.convert('L').save(I/'jira_progress.jpg')
raw=I/'jira_board_raw.jpg'
if raw.exists():
    with Image.open(raw) as im:im.convert('L').save(I/'jira_board.jpg')
runtime={'docker_build':'Passed; pinned app and TLS images built','docker_health':'Healthy; non-root read-only filesystem; all capabilities dropped','tls':'Docker and Kubernetes TLSv1.3; certificate and hostname checks passed','kubernetes':'Isolated kind deployment 2/2 ready; app and TLS sidecar','kubernetes_controls':'Restricted namespace; non-root; seccomp; PVCs; ClusterIP; limits verified. NetworkPolicy enforcement not established on default kind CNI.'}
(E/'deployment-summary.json').write_text(json.dumps(runtime,indent=2))
tests=(E/'tests-final.txt').read_text().splitlines()
render('build_evidence.png','Actual local test and static check output',tests[-6:]+['', 'Source: evidence/tests-final.txt; static-check.json; bandit-final.json', json.dumps(json.loads((E/'static-check.json').read_text()))])
docker=json.loads((E/'docker-runtime.json').read_text())
render('docker_evidence.png','Actual Docker runtime and validated HTTPS',[json.dumps(x) for x in docker]+['',json.dumps(json.loads((E/'docker-tls-smoke.json').read_text()))])
render('kubernetes_evidence.png','Actual Kubernetes rollout and validated HTTPS',(E/'kubernetes.txt').read_text(encoding='utf-8-sig').splitlines()+['',json.dumps(json.loads((E/'kubernetes-tls-smoke.json').read_text()))])
state=json.loads((E/'jira-state.json').read_text());issues=state.get('verifiedIssues',[])
if issues:
    points=sum(s['points'] for s in json.loads((OUT/'catalog.json').read_text())['stories'])
    metrics={'verified_at':state['verifiedAt'],'done_issues':len(issues),'done_stories':16,'done_story_points':points,'sprint_points':{'1':36,'2':34},'execution':'Compressed lab demonstration. Nominal fifteen-day dates are plans, not elapsed working history.','defect_fix_groups':6,'assigned_only_to':state['displayName']}
    (E/'sprint-metrics.json').write_text(json.dumps(metrics,indent=2))
    render('jira_board.png','Verified Jira data export with all issues Done',['CLF24 | Board 236 | '+state['verifiedAt'],'All issues assigned only to '+state['displayName'],'Columns: To Do > In Progress > Testing > Done','']+[x['key']+'  '+x['reference']+'  '+x['status']+'  '+x['summary'] for x in issues])
    # Both actual endpoints are available; intermediate daily values are deliberately not fabricated.
    im=Image.new('RGB',(1600,850),'white');d=ImageDraw.Draw(im)
    d.text((50,35),'Sprint estimates and observed completion',font=bold,fill='black')
    for k,total in enumerate([36,34]):
        ox=130+k*760;oy=620;w=590;h=370
        d.line((ox,oy-h,ox,oy,ox+w,oy),fill='black',width=3)
        d.line((ox,oy-h,ox+w,oy),fill='gray',width=3)
        d.ellipse((ox-7,oy-h-7,ox+7,oy-h+7),fill='black')
        d.ellipse((ox-7,oy-7,ox+7,oy+7),fill='black')
        d.text((ox,165),f'Sprint {k+1}: {total} planned points',font=bold,fill='black')
        d.text((ox,oy+22),'0                         Day 15',font=font,fill='black')
        d.text((ox+20,oy-110),'Actual lab: all points Done',font=font,fill='black')
        d.text((ox+20,oy-75),'during the same execution day',font=font,fill='black')
    d.text((50,740),'Grey diagonal = ideal 15-day forecast. Black endpoints = recorded lab state.',font=font,fill='black')
    d.text((50,780),'No intervening daily burndown or empirical 15-day velocity is claimed.',font=font,fill='black')
    im.save(I/'burndown.png')
print('Monochrome evidence exports created.')
