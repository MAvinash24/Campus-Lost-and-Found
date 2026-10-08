"""Create and attach a workflow only to this task's dedicated Jira project."""
import uuid
from jira_sync import api, state, save, catalog

statuses=api('GET','/rest/api/3/project/'+catalog['project_key']+'/statuses')
lookup={s['name'].lower():s for t in statuses for s in t['statuses']}
allstatuses=api('GET','/rest/api/3/status')
testing=next((s for s in allstatuses if s['name']=='Testing'),None)
lookup['testing']=testing or {**state['statusCreate'][0], 'statusCategory':{'key':'indeterminate'}}
names=['To Do','In Progress','Testing','Done']
refs={name:str(uuid.uuid4()) for name in names}
payload={'scope':{'type':'GLOBAL'},'statuses':[],'workflows':[{'name':'CLF24 Campus Lab Workflow','description':'Dedicated four-stage secure software lab workflow','startPointLayout':{'x':0,'y':0},'statuses':[],'transitions':[]}]}
w=payload['workflows'][0]
for i,n in enumerate(names):
    s=lookup[n.lower()]
    payload['statuses'].append({'id':s['id'],'name':s['name'],'description':s.get('description',''),'statusCategory':{'new':'TODO','indeterminate':'IN_PROGRESS','done':'DONE'}[s['statusCategory']['key']],'statusReference':refs[n]})
    w['statuses'].append({'statusReference':refs[n],'layout':{'x':200+i*250,'y':100},'properties':{}})
    w['transitions'].append({'id':str((i+1)*10),'name':n,'type':'GLOBAL','toStatusReference':refs[n],'links':[],'actions':[],'validators':[],'triggers':[],'properties':{}})
w['transitions'].append({'id':'1','name':'Create','type':'INITIAL','toStatusReference':refs['To Do'],'links':[],'actions':[],'validators':[],'triggers':[],'properties':{}})
result=api('POST','/rest/api/3/workflows/create',payload,optional=True)
state['workflowCreateV2']=result;save()
if 'error' in result:raise SystemExit(str(result))
scheme=api('POST','/rest/api/3/workflowscheme',{'name':'CLF24 Campus Lab Scheme','defaultWorkflow':w['name']},optional=True)
state['workflowScheme']=scheme;save()
if 'id' not in scheme:raise SystemExit(str(scheme))
state['workflowAssign']=api('PUT','/rest/api/3/workflowscheme/project',{'projectId':str(state['project']['id']),'workflowSchemeId':scheme['id']},optional=True);save()
print('Dedicated workflow assignment:',state['workflowAssign'])
