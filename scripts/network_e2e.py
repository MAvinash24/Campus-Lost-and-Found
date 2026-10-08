"""Test the running TLS application using the lab CA, without disabling verification."""
import json
import re
import ssl
import socket
from urllib.parse import urlsplit
import sys
from datetime import datetime,timezone
from pathlib import Path
import requests

root=Path(__file__).resolve().parents[1]
base=sys.argv[1] if len(sys.argv)>1 else 'https://localhost:8443'
cert=sys.argv[2] if len(sys.argv)>2 else str(root/'deliverables/evidence/campus-lab-root.crt')
prefix=sys.argv[3] if len(sys.argv)>3 else 'docker'
state=json.loads((root/'.local-secrets.json').read_text())
events=[]

def csrf(response):
    m=re.search(r'name="csrf" value="([^"]+)"',response.text)
    assert m,'CSRF field missing';return m.group(1)

def session(role):
    s=requests.Session();s.verify=cert
    token=csrf(s.get(base+'/login',timeout=15))
    r=s.post(base+'/login',data={'csrf':token,**state['accounts'][role]},timeout=15)
    assert r.status_code==200 and 'Browse items' in r.text
    events.append({'step':role+' login','status':r.status_code});return s

student=session('student');faculty=session('faculty');admin=session('administrator')
form=student.get(base+'/report',timeout=15)
title='TLS integration calculator '+datetime.now(timezone.utc).strftime('%H%M%S')
r=student.post(base+'/report',data={'csrf':csrf(form),'kind':'found','category':'Electronics','title':title,'description':'Container integration test record with a protective cover.','location':'Campus security desk','item_date':'2026-10-08'},timeout=15)
assert r.status_code==200 and 'Pending' in r.text
item=int(re.search(r'/items/(\d+)',r.url).group(1));events.append({'step':'report pending','report':item,'status':200})
assert faculty.get(base+f'/items/{item}',timeout=15).status_code==404
events.append({'step':'pending report hidden from other user','status':404})
adm=admin.get(base+'/admin',timeout=15)
r=admin.post(base+f'/admin/items/{item}',data={'csrf':csrf(adm),'action':'verified'},timeout=15);assert r.status_code==200
events.append({'step':'administrator verification','status':200})
detail=faculty.get(base+f'/items/{item}',timeout=15)
r=faculty.post(base+f'/items/{item}/recover',data={'csrf':csrf(detail)},timeout=15);assert r.status_code==403
events.append({'step':'cross-user recovery denied','status':403})
r=faculty.post(base+f'/items/{item}/contact',data={'csrf':csrf(detail),'body':'Integration handover arranged at the staffed security desk.'},timeout=15);assert r.status_code==200
inbox=student.get(base+'/inbox',timeout=15);assert 'Integration handover' in inbox.text
assert state['accounts']['faculty']['email'] not in inbox.text
events.append({'step':'private message without email disclosure','status':200})
detail=student.get(base+f'/items/{item}',timeout=15)
r=student.post(base+f'/items/{item}/recover',data={'csrf':csrf(detail)},timeout=15);assert r.status_code==200 and 'Recovered' in r.text
events.append({'step':'reporter recovery','status':200})
health=student.get(base+'/healthz',timeout=15);assert health.json()['status']=='ok'
context=ssl.create_default_context(cafile=cert)
with socket.create_connection(('localhost',urlsplit(base).port),timeout=15) as sock:
    with context.wrap_socket(sock,server_hostname='localhost') as tls:
        handshake={'version':tls.version(),'cipher':tls.cipher()[0],'certificate_validation':'passed against local lab CA','hostname_validation':'localhost passed'}
result={'base_url':base,'passed':True,'steps':events,'tls':handshake,'headers':{k:health.headers[k] for k in ['Content-Security-Policy','Strict-Transport-Security','X-Content-Type-Options']}}
(root/f'deliverables/evidence/{prefix}-e2e.json').write_text(json.dumps(result,indent=2))
(root/f'deliverables/evidence/{prefix}-tls-smoke.json').write_text(json.dumps(handshake,indent=2))
print(json.dumps(result,indent=2))
