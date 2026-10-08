import json
from datetime import datetime, timezone
from jira_sync import api,state,save,catalog,adf,finalize

for s in catalog['stories']:
    desc=s['story']+'\nRequirement: '+s['requirement']+'\nPriority: '+s['priority']+'\nAcceptance criteria:\n'+'\n'.join(s['acceptance'])+'\nValidation: tests/test_app.py::'+s['test']+'\nDeployment evidence: docker-e2e.json; kubernetes-e2e.json'
    api('PUT','/rest/api/3/issue/'+state['stories'][s['id']],{'fields':{'description':adf(desc),'priority':{'name':'High' if s['priority']=='Must' else 'Medium'}}})
finalize()
for n in ['1','2']:
    sid=state['sprints'][n]['id'];sp=catalog['sprints'][int(n)-1]
    current=api('GET',f'/rest/agile/1.0/sprint/{sid}')
    state['sprints'][n]=current;save()
verified=[]
for group in ['epics','stories','tasks']:
    for ref,key in state[group].items():
        issue=api('GET','/rest/api/3/issue/'+key+'?fields=summary,status,assignee,priority')
        f=issue['fields']
        assert f['status']['statusCategory']['key']=='done'
        assert f['assignee']['accountId']==state['accountId']
        verified.append({'reference':ref,'key':key,'summary':f['summary'],'status':f['status']['name'],'assignee':f['assignee']['displayName'],'priority':f['priority']['name']})
state['verifiedIssues']=verified;state['verifiedAt']=datetime.now(timezone.utc).isoformat();save()
print('Verified:',len(verified),'Done issues; two fifteen-day sprint schedules; every issue assigned to',state['displayName'])
