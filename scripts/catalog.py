"""One identifier catalog drives requirements, backlog, reports and Jira."""
import json
from pathlib import Path

requirements=[
 ('R01','Account registration and sign in','Student and faculty register; administrator is provisioned by operator.','Must','UC01','E1',1,5,'test_registration_valid'),
 ('R02','Report a lost item','Capture title description category location and date; create pending report.','Must','UC02','E2',1,5,'test_pending_visibility'),
 ('R03','Report a found item','Use the same validated workflow with kind found.','Must','UC02','E2',1,3,'test_future_date_rejected'),
 ('R04','Search verified reports','Search title description location and filter kind/category.','Must','UC03','E2',1,5,'test_sql_injection_search'),
 ('R05','Private owner or finder contact','Authenticated contact through recipient-scoped internal inbox.','Must','UC04','E3',1,5,'test_private_messages_and_reply'),
 ('R06','Owner-only recovery','Only the reporting user can close an open verified report.','Must','UC05','E3',1,5,'test_unauthorized_recovery'),
 ('R07','Administrator moderation','Administrator verifies or soft-removes suspicious reports with reason.','Must','UC06','E4',1,5,'test_moderation_and_removal'),
 ('R08','Personal report tracking','Owner can see their pending verified and removed reports.','Should','UC07','E2',1,3,'test_pending_visibility'),
 ('R09','Secure communication and sessions','TLS cookie security CSRF request limits CSP and password hashing.','Must','UC01','E1',2,5,'test_session_cookie_security'),
 ('R10','Malicious content prevention','Escape displayed text and use parameterized SQL and bounded input.','Must','UC02','E5',2,5,'test_xss_escaped'),
 ('R11','Security audit and monitoring','Record login denial moderation recovery and message metadata without body or password.','Must','UC08','E4',2,3,'test_audit_contains_no_secrets'),
 ('R12','Private reply and abuse control','Recipient-only replies; cap messages at ten per minute per sender.','Should','UC04','E3',2,3,'test_message_throttle'),
 ('R13','Secure Docker packaging','Pinned dependencies non-root read-only rootfs least privilege TLS health check.','Must','UC09','E6',2,5,'test_health_and_headers'),
 ('R14','Kubernetes deployment','Restricted namespace limits secret PVC ClusterIP network policy.','Must','UC09','E6',2,5,'test_host_validation'),
 ('R15','Verified delivery pipeline','Checkout build tests static check dependency audit image package; fail on errors.','Must','UC09','E5',2,5,'test_end_to_end_report_verify_contact_recover'),
 ('R16','Accessible consistent interface','Responsive labelled controls error feedback cancel clear and progress views.','Should','UC03','E2',2,3,'test_body_limit')]
epics=[('E1','Identity and session security'),('E2','Campus reporting and discovery'),('E3','Private contact and recovery'),('E4','Moderation and accountability'),('E5','Secure build and quality assurance'),('E6','Containers and secure deployment')]
actors=['campus user','student','finder','campus user','campus user','reporter','administrator','reporter','campus user','campus user','administrator','message recipient','operator','operator','developer','campus user']
benefits=['access the service safely','ask the campus community for help','return it to its owner','find a matching item','reconnect without publishing my email','record a successful return','keep suspicious content off the board','follow verification progress','protect my account and communication','view reports without executing malicious content','investigate misuse','reply safely without unsolicited access','run a controlled container','deploy with restricted permissions','ship tested and checked changes','complete tasks with clear feedback']
actions=['register and sign in','report a lost item','report a found item','search verified reports','contact an owner or finder privately','mark my report as recovered','verify or remove suspicious reports','track my own reports','use secure sessions and communication','view safely validated content','inspect security audit metadata','reply privately with abuse controls','package the application in Docker','deploy the application to Kubernetes','run the verified delivery pipeline','use an accessible consistent interface']
catalog={'project':'Campus Lost and Found','project_key':'CLF24','student':{'name':'Marisetti Avinash','register':'CH.SC.U4CYS23024','college':'Amrita Vishwa Vidyapeetham Chennai'},'epics':[{'id':e,'name':n} for e,n in epics],'requirements':[],'stories':[],'sprints':[{'number':1,'name':'Sprint 1 Campus reporting and recovery','start':'2026-10-08T09:00:00+05:30','end':'2026-10-23T09:00:00+05:30','goal':'Deliver identity reporting search moderation private contact and owner-only recovery.'},{'number':2,'name':'Sprint 2 Security and deployment','start':'2026-10-23T09:00:00+05:30','end':'2026-11-07T09:00:00+05:30','goal':'Harden the application verify abuse controls and deliver tested Docker Kubernetes and CI packages.'}]}
for i,(rid,title,desc,priority,uc,epic,sprint,points,test) in enumerate(requirements):
    sid=f'US{i+1:02d}'
    req={'id':rid,'title':title,'description':desc,'priority':priority,'use_case':uc,'story':sid,'test':test}
    catalog['requirements'].append(req)
    catalog['stories'].append({'id':sid,'requirement':rid,'epic':epic,'summary':title,'story':f'As a {actors[i]}, I want to {actions[i]} so that I can {benefits[i]}.','priority':priority,'acceptance':[desc,f'Automated check {test} passes or deployment evidence confirms the control.','No sensitive credentials are published in the implementation or evidence.'],'sprint':sprint,'points':points,'task':f'T{i+1:02d}','test':test})
catalog['sprints'][0]['name']='Sprint 1 Campus Core'
catalog['sprints'][1]['name']='Sprint 2 Secure Delivery'
Path('deliverables').mkdir(exist_ok=True)
Path('deliverables/catalog.json').write_text(json.dumps(catalog,indent=2))
print('Catalog: 16 requirements, 16 stories, 6 epics, 2 fifteen-day sprint plans.')
