from datetime import datetime,timezone
from jira_sync import api,state,save,catalog
sp=catalog['sprints'][0];sid=state['sprints']['1']['id']
state['sprint1Start']=api('PUT',f'/rest/agile/1.0/sprint/{sid}',{'name':sp['name'],'state':'active','startDate':sp['start'],'endDate':sp['end'],'goal':sp['goal']+' Compressed laboratory execution; dates are nominal fifteen-day plan.'})
state['boardConfig']=api('GET',f"/rest/agile/1.0/board/{state['board']['id']}/configuration")
for key in [state['stories']['US01'],state['tasks']['T01']]:
    for target in ['In Progress','Testing']:
        options=api('GET',f'/rest/api/3/issue/{key}/transitions')['transitions']
        t=next(t for t in options if t['to']['name']==target)
        api('POST',f'/rest/api/3/issue/{key}/transitions',{'transition':{'id':t['id']}})
        state['history'].append({'issue':key,'target':target,'timestamp':datetime.now(timezone.utc).isoformat(),'execution':'actual API transition during compressed lab demo'})
save();print('Sprint 1 active; identity story and task in Testing; board configuration recorded.')
