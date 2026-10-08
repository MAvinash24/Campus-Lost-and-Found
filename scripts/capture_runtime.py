import json,subprocess
from pathlib import Path
E=Path('deliverables/evidence')
raw=json.loads(subprocess.check_output(['docker','inspect','sse-app-1','sse-tls-1'],text=True))
safe=[]
for x in raw:
    c=x['HostConfig']
    safe.append({'name':x['Name'],'image_id':x['Image'],'user':x['Config']['User'],'running':x['State']['Running'],'health':x['State'].get('Health',{}).get('Status'),'read_only':c['ReadonlyRootfs'],'cap_drop':c['CapDrop'],'security_options':c['SecurityOpt'],'memory_bytes':c['Memory'],'nano_cpus':c['NanoCpus'],'port_bindings':c['PortBindings']})
(E/'docker-runtime.json').write_text(json.dumps(safe,indent=2))
dep=json.loads((E/'kubernetes-deployment.json').read_text(encoding='utf-8-sig'))
spec=dep['spec']['template']['spec']
safe_k={'replicas':dep['spec']['replicas'],'ready_replicas':dep['status'].get('readyReplicas'),'service_account_token':spec['automountServiceAccountToken'],'pod_security_context':spec['securityContext'],'containers':[{'name':c['name'],'image':c['image'],'security_context':c['securityContext'],'resources':c['resources']} for c in spec['containers']],'network_policy_note':'Manifest present; default kind CNI does not establish policy enforcement.'}
(E/'kubernetes-security.json').write_text(json.dumps(safe_k,indent=2))
print('Sanitized runtime records saved; secret environment values excluded.')
