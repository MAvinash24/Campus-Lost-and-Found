from jira_sync import api,state,save
state['associatedWorkflowScheme']=api('GET','/rest/api/3/workflowscheme/project?projectId='+str(state['project']['id']))
state['workflowRead']=api('POST','/rest/api/3/workflows',{'workflowNames':['Software Simplified Workflow for Project CLF24']},optional=True)
save()
print(str(state['associatedWorkflowScheme'])[:3000]);print(str(state['workflowRead'])[:9000])
