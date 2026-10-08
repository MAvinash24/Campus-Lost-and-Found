import copy
from jira_sync import api,state,save

read=state['workflowRead'];w=copy.deepcopy(read['workflows'][0])
usages=api('GET',f"/rest/api/3/workflow/{w['id']}/projectUsages",optional=True)
state['workflowProjectUsages']=usages;save()
print('Workflow project usage:',str(usages)[:1000])
statuses=copy.deepcopy(read['statuses'])
testing=state['statusCreate'][0]
statuses.append({'id':testing['id'],'name':'Testing','description':'Verification before completion','statusReference':testing['id'],'statusCategory':'IN_PROGRESS'})
w['statuses'].append({'statusReference':testing['id'],'layout':{'x':450,'y':0},'properties':{}})
w['transitions'].append({'id':'41','name':'Testing','type':'GLOBAL','toStatusReference':testing['id'],'links':[],'actions':[],'validators':[],'triggers':[],'properties':{}})
payload={'statuses':statuses,'workflows':[w]}
state['workflowUpdate']=api('POST','/rest/api/3/workflows/update',payload,optional=True);save()
print('Workflow update:',str(state['workflowUpdate'])[:4000])
