"""Jira REST synchronization. Authentication comes only from environment variables."""
import base64
import json
import os
import sys
from datetime import datetime, timezone
import urllib.error
import urllib.request
from pathlib import Path

root=Path(__file__).resolve().parents[1]
catalog=json.loads((root/'deliverables/catalog.json').read_text())
outfile=root/'deliverables/evidence/jira-state.json'
state=json.loads(outfile.read_text()) if outfile.exists() else {'epics':{},'stories':{},'tasks':{},'sprints':{},'history':[]}
base=os.environ['JIRA_URL'].rstrip('/')
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
auth=base64.b64encode((os.environ['JIRA_EMAIL']+':'+os.environ['JIRA_TOKEN']).encode()).decode()

def save():
    outfile.parent.mkdir(parents=True,exist_ok=True);outfile.write_text(json.dumps(state,indent=2))

def api(method,path,data=None,optional=False):
    req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Authorization':'Basic '+auth,'Content-Type':'application/json','Accept':'application/json'})
    try:
        with opener.open(req,timeout=60) as r:
            text=r.read().decode();return json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        text=e.read().decode()
        if optional:return {'error':e.code,'detail':text[:2000]}
        raise RuntimeError(f'{method} {path}: HTTP {e.code}: {text[:2000]}') from None

def adf(text):
    return {'type':'doc','version':1,'content':[{'type':'paragraph','content':[{'type':'text','text':line}]} for line in text.splitlines() if line]}

def create_issue(kind,summary,description,parent=None):
    fields={'project':{'key':catalog['project_key']},'issuetype':{'id':state['types'][kind]},'summary':summary,'description':adf(description),'assignee':{'accountId':state['accountId']},'labels':['campus-lost-found','secure-software-lab']}
    if parent:fields['parent']={'key':parent}
    result=api('POST','/rest/api/3/issue',{'fields':fields})
    print('Created',result['key'],kind,summary)
    return result['key']

def setup():
    me=api('GET','/rest/api/3/myself');state['accountId']=me['accountId'];state['displayName']=me['displayName']
    state['site']=base
    if 'project' not in state:
        existing=api('GET','/rest/api/3/project/'+catalog['project_key'],optional=True)
        if existing.get('error')==404:
            state['project']=api('POST','/rest/api/3/project',{'key':catalog['project_key'],'name':'Campus Lost and Found Secure Software Lab','projectTypeKey':'software','projectTemplateKey':'com.pyxis.greenhopper.jira:gh-simplified-scrum-classic','leadAccountId':state['accountId'],'assigneeType':'PROJECT_LEAD','description':'College lost-and-found application. CH.SC.U4CYS23024. Sixteen connected secure engineering phases. Fifteen-day nominal sprint plans; execution is a compressed laboratory demonstration.'})
        elif 'error' in existing:raise RuntimeError(str(existing))
        else:state['project']=existing
        save()
    project=api('GET','/rest/api/3/project/'+catalog['project_key'])
    state['types']={t['name']:t['id'] for t in project['issueTypes']};save()
    boards=api('GET','/rest/agile/1.0/board?projectKeyOrId='+catalog['project_key'])['values']
    if boards:state['board']=boards[0]
    else:
        f=api('POST','/rest/api/3/filter',{'name':'CLF24 campus backlog','jql':'project = CLF24 ORDER BY Rank ASC'})
        state['board']=api('POST','/rest/agile/1.0/board',{'name':'Campus Lost and Found Scrum','type':'scrum','filterId':int(f['id']),'location':{'type':'project','projectKeyOrId':catalog['project_key']}})
    save()
    # Preserve only the dedicated project's schemes; never change another project.
    if 'workflowAttempt' not in state:
        statuses=api('GET','/rest/api/3/status')
        lookup={s['name'].lower():s['id'] for s in statuses}
        needed=['To Do','In Progress','Testing','Done']
        missing=[n for n in needed if n.lower() not in lookup]
        if missing:
            result=api('POST','/rest/api/3/statuses',{'scope':{'type':'GLOBAL'},'statuses':[{'name':n,'statusCategory':'IN_PROGRESS' if n=='Testing' else 'TODO'} for n in missing]},optional=True)
            state['statusCreate']=result
            for s in result if isinstance(result,list) else []:lookup[s['name'].lower()]=s['id']
        name='CLF24 Campus Lab Workflow'
        if all(n.lower() in lookup for n in needed):
            transitions=[{'name':'Create','type':'initial','to':lookup['to do']},{'name':'Start work','type':'global','to':lookup['in progress']},{'name':'Send to testing','type':'global','to':lookup['testing']},{'name':'Complete','type':'global','to':lookup['done']}]
            result=api('POST','/rest/api/3/workflow',{'name':name,'description':'Dedicated campus lab workflow','statuses':[{'id':lookup[n.lower()]} for n in needed],'transitions':transitions},optional=True)
            state['workflowAttempt']=result
            if 'error' not in result:
                scheme=api('POST','/rest/api/3/workflowscheme',{'name':'CLF24 Campus Lab Scheme','defaultWorkflow':name},optional=True)
                state['workflowScheme']=scheme
                if 'id' in scheme:state['workflowAssign']=api('PUT','/rest/api/3/workflowscheme/project',{'projectId':project['id'],'workflowSchemeId':scheme['id']},optional=True)
        else:state['workflowAttempt']={'error':'required statuses unavailable'}
        save()
    for epic in catalog['epics']:
        if epic['id'] not in state['epics']:
            state['epics'][epic['id']]=create_issue('Epic',epic['id']+' '+epic['name'],'Secure software engineering epic for '+epic['name']);save()
    for sp in catalog['sprints']:
        k=str(sp['number'])
        if k not in state['sprints']:
            state['sprints'][k]=api('POST','/rest/agile/1.0/sprint',{'name':sp['name'],'originBoardId':state['board']['id'],'startDate':sp['start'],'endDate':sp['end'],'goal':sp['goal']+' Nominal 15-day plan; execution is a compressed lab demonstration.'});save()
    fields=api('GET','/rest/api/3/field')
    state['points_field']=next((f['id'] for f in fields if f['name']=='Story Points'),None)
    for story in catalog['stories']:
        if story['id'] not in state['stories']:
            desc=story['story']+'\nRequirement: '+story['requirement']+' | Use case: '+next(r['use_case'] for r in catalog['requirements'] if r['id']==story['requirement'])+'\nPriority: '+story['priority']+'\nAcceptance criteria:\n'+'\n'.join(story['acceptance'])+'\nEstimate: '+str(story['points'])+' story points\nValidation: tests/test_app.py::'+story['test']
            state['stories'][story['id']]=create_issue('Story',story['id']+' '+story['summary'],desc,state['epics'][story['epic']]);save()
            if state['points_field']:
                api('PUT','/rest/api/3/issue/'+state['stories'][story['id']],{'fields':{state['points_field']:story['points']}},optional=True)
        if story['task'] not in state['tasks']:
            subtask_type=next((t for t in state['types'] if t.lower() in ('sub-task','subtask')),None)
            kind=subtask_type or 'Task'
            parent=state['stories'][story['id']] if subtask_type else state['epics'][story['epic']]
            state['tasks'][story['task']]=create_issue(kind,story['task']+' Implement and verify '+story['summary'],'Implement '+story['requirement']+'. Evidence: '+story['test']+'. Validate acceptance criteria and retain results. Compressed laboratory execution.',parent);save()
    for n in [1,2]:
        keys=[state['stories'][s['id']] for s in catalog['stories'] if s['sprint']==n]
        if 'Sub-task' not in state['types'] and 'Subtask' not in state['types']:
            keys += [state['tasks'][s['task']] for s in catalog['stories'] if s['sprint']==n]
        api('POST',f"/rest/agile/1.0/sprint/{state['sprints'][str(n)]['id']}/issue",{'issues':keys})
    state['setup_complete']=True;save()
    print('Jira setup complete:',base+'/plugins/servlet/project-config/'+catalog['project_key'])

def finalize():
    for group in ['tasks','stories','epics']:
        for ref,key in state[group].items():
            issue=api('GET','/rest/api/3/issue/'+key+'?fields=status,assignee')
            if issue['fields']['assignee']['accountId']!=state['accountId']:
                api('PUT','/rest/api/3/issue/'+key+'/assignee',{'accountId':state['accountId']})
            if issue['fields']['status']['statusCategory']['key']=='done':continue
            for target in ['In Progress','Testing','Done']:
                options=api('GET','/rest/api/3/issue/'+key+'/transitions')['transitions']
                t=next((t for t in options if t['to']['name'].lower()==target.lower()),None)
                if not t and target=='Done':t=next((t for t in options if t['to']['statusCategory']['key']=='done'),None)
                if t:
                    api('POST','/rest/api/3/issue/'+key+'/transitions',{'transition':{'id':t['id']}})
                    state['history'].append({'issue':key,'target':t['to']['name'],'timestamp':datetime.now(timezone.utc).isoformat(),'execution':'actual API transition during compressed lab demo'});save()
                elif target=='Testing':state['history'].append({'issue':key,'missing':'Testing transition unavailable; test evidence retained separately'});save()
            final=api('GET','/rest/api/3/issue/'+key+'?fields=status,assignee')
            if final['fields']['status']['statusCategory']['key']!='done':raise RuntimeError(key+' did not reach Done')
            print(key,final['fields']['status']['name'])
    state['final_verified']=True;save()

if __name__=='__main__':
    try:
        (finalize if sys.argv[-1]=='finalize' else setup)()
    except Exception as e:
        save();print('Jira operation stopped:',str(e));raise SystemExit(1)
