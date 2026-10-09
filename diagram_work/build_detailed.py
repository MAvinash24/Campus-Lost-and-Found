from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math,html,json,zipfile
OUT=Path(r'D:\sse\deliverables\detailed_diagrams');OUT.mkdir(parents=True,exist_ok=True)
NAVY='#16324F';INK='#20364B';BLUE='#EAF3FC';TEAL='#E5F5F2';AMBER='#FFF3D9';RED='#FCEBEA';MUTED='#587086';WHITE='#FFFFFF'
F='C:/Windows/Fonts/arial.ttf';B='C:/Windows/Fonts/arialbd.ttf'
class D:
 def __init__(self,name,title,sub,h=1600):
  self.name=name;self.h=h;self.im=Image.new('RGB',(2400,h),WHITE);self.d=ImageDraw.Draw(self.im);self.s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="{h}" viewBox="0 0 2400 {h}"><rect width="2400" height="{h}" fill="white"/>'];self.nodes={}
  self.text(90,70,title,48,True,False,NAVY);self.text(90,140,sub,27,False,False,MUTED)
  self.text(90,h-55,'COLLEGE LOST AND FOUND  /  SECURE SOFTWARE ENGINEERING',23,True,False,MUTED)
 def text(self,x,y,t,size=30,bold=False,center=True,color=INK):
  f=ImageFont.truetype(B if bold else F,size)
  for i,l in enumerate(t.split('\n')):
   yy=y+i*(size+11);self.d.text((x,yy),l,font=f,fill=color,anchor='mm' if center else 'lm');self.s.append(f'<text x="{x}" y="{yy+size*.34}" text-anchor="{"middle" if center else "start"}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(l)}</text>')
 def rect(self,x,y,w,h,fill=WHITE,stroke=NAVY,dash=False):
  self.d.rectangle((x,y,x+w,y+h),fill=fill,outline=stroke,width=3)
  self.s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="3"'+(' stroke-dasharray="12 9"' if dash else '')+'/>')
 def box(self,id,x,y,w,h,title,body='',fill=BLUE,shape='box',size=29):
  self.nodes[id]=(x,y,w,h)
  if shape=='ellipse':
   self.d.ellipse((x,y,x+w,y+h),fill=fill,outline=NAVY,width=3);self.s.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}" stroke="{NAVY}" stroke-width="3"/>')
   lines=(title+('\n'+body if body else '')).split('\n');self.text(x+w/2,y+h/2-(len(lines)-1)*(size+11)/2,'\n'.join(lines),size,False)
  else:
   self.rect(x,y,w,h,fill);self.text(x+w/2,y+42,title,size,True)
   if body:self.text(x+25,y+100,body,size-2,False,False)
   if shape=='store':
    self.line([(x+12,y),(x+12,y+h)],arrow=False)
 def zone(self,x,y,w,h,label,color=MUTED):
  self.rect(x,y,w,h,WHITE,color,True);self.text(x+20,y+30,label,25,True,False,color)
 def line(self,pts,label='',pos=None,dash=False,arrow=True,color=NAVY,openarrow=False):
  for (x1,y1),(x2,y2) in zip(pts,pts[1:]):
   if dash:
    dist=math.hypot(x2-x1,y2-y1)
    for st in range(0,int(dist),24):
     a=st/dist;b=min(st+13,dist)/dist;self.d.line((x1+(x2-x1)*a,y1+(y2-y1)*a,x1+(x2-x1)*b,y1+(y2-y1)*b),fill=color,width=3)
   else:self.d.line((x1,y1,x2,y2),fill=color,width=3)
  self.s.append(f'<polyline points="'+ ' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="3"'+(' stroke-dasharray="13 11"' if dash else '')+'/>')
  if arrow:
   x,y=pts[-1];px,py=pts[-2];a=math.atan2(y-py,x-px);p=[(x,y),(x-19*math.cos(a-.45),y-19*math.sin(a-.45)),(x-19*math.cos(a+.45),y-19*math.sin(a+.45))]
   self.d.polygon(p,fill=WHITE if openarrow else color,outline=color);self.s.append('<polygon points="'+' '.join(f'{xx},{yy}' for xx,yy in p)+f'" fill="{WHITE if openarrow else color}" stroke="{color}"/>')
  if label:
   x,y=pos or ((pts[0][0]+pts[-1][0])/2,(pts[0][1]+pts[-1][1])/2-25);f=ImageFont.truetype(F,25)
   for i,l in enumerate(label.split('\n')):
    yy=y+i*34;bb=self.d.textbbox((x,yy),l,font=f,anchor='mm');self.rect(bb[0]-6,bb[1]-4,bb[2]-bb[0]+12,bb[3]-bb[1]+8,WHITE,WHITE);self.text(x,yy,l,25)
 def edge(self,a,b,label='',side='right',end='left',via=None,pos=None,dash=False,arrow=True):
  def p(n,s):
   x,y,w,h=self.nodes[n];return {'left':(x,y+h/2),'right':(x+w,y+h/2),'top':(x+w/2,y),'bottom':(x+w/2,y+h)}[s]
  self.line([p(a,side)]+(via or [])+[p(b,end)],label,pos,dash,arrow)
 def actor(self,id,x,y,label):
  self.nodes[id]=(x,y,160,190);cx=x+80
  self.d.ellipse((cx-24,y,cx+24,y+48),outline=NAVY,width=4);self.s.append(f'<circle cx="{cx}" cy="{y+24}" r="24" fill="white" stroke="{NAVY}" stroke-width="4"/>')
  self.line([(cx,y+48),(cx,y+110)],arrow=False);self.line([(cx-48,y+72),(cx+48,y+72)],arrow=False);self.line([(cx-45,y+155),(cx,y+110),(cx+45,y+155)],arrow=False);self.text(cx,y+185,label,28,True)
 def save(self):
  self.im.save(OUT/(self.name+'.png'));(OUT/(self.name+'.svg')).write_text(''.join(self.s)+'</svg>',encoding='utf8')
  return self
# 1-2 Use cases
for admin in [False,True]:
 d=D('02_use_cases_administration' if admin else '01_use_cases_campus','Use cases | Administration and operations' if admin else 'Use cases | Campus reporting and recovery','UML model  /  Solid lines: actor associations  /  Dashed arrows: mandatory included behavior')
 d.zone(420,230,1860,1100,'College Lost and Found system')
 if not admin:
  d.actor('campus',90,650,'Campus user')
  cases=[('UC01',550,320,'UC01 Register / sign in','Student or faculty registration'),('UC02',550,590,'UC02 Report lost / found','Create pending, open report'),('UC03',550,860,'UC03 Search / view items','Verified results; own pending items'),('UC07',550,1130,'UC07 Track own reports','Owner-scoped report listing'),('UC04',1440,320,'UC04 Contact / reply','Private report-related messages'),('UC05',1440,590,'UC05 Mark recovered','Only the report creator'),('V',1440,860,'Validate report fields','Bounds, kind, date and category'),('A',1440,1130,'Authorize recovery','Reporter + open + verified')]
  for id,x,y,t,b in cases:d.box(id,x,y,700,145,t,b,shape='ellipse',size=28)
  for id in ['UC01','UC02','UC03','UC07']:d.edge('campus',id,arrow=False)
  d.line([(250,700),(350,700),(350,300),(1790,300),(1790,320)],arrow=False)
  d.line([(250,740),(375,740),(375,535),(1790,535),(1790,590)],arrow=False)
  d.line([(1250,662),(1340,662),(1340,932),(1440,932)],'<<include>>',(1330,750),dash=True)
  d.line([(2140,662),(2205,662),(2205,1202),(2140,1202)],'<<include>>',(2210,925),dash=True)
  d.text(100,1410,'Actors: Student and Faculty share campus-user capabilities. Contact requires an open verified report.',28,False,False)
  d.text(100,1460,'Security preconditions: authenticated session and CSRF validation for protected state-changing forms.',28,False,False)
 else:
  d.actor('admin',90,440,'Administrator');d.actor('operator',90,1040,'Operator')
  for id,x,y,t,b in [('m',570,320,'UC06 Verify / remove report','Review queue and record reason'),('a',570,590,'UC08 Review audit','Actor, event, object and outcome'),('d',570,1050,'UC09 Deploy verified application','Build, TLS, health and storage'),('r',1480,320,'Check administrator role','Server-side authorization guard'),('e',1480,590,'Record moderation event','No credentials or message bodies'),('s',1480,1050,'Configure runtime resources','Secrets, private volume and backup')]:d.box(id,x,y,650,160,t,b,shape='ellipse',size=28)
  d.edge('admin','m',arrow=False);d.edge('admin','a',arrow=False);d.edge('operator','d',arrow=False)
  d.edge('m','r','<<include>>',dash=True);d.line([(895,480),(895,530),(1400,530),(1400,670),(1480,670)],'<<include>>',(1110,530),dash=True);d.edge('a','r','<<include>>',via=[(1320,670),(1320,400)],pos=(1315,620),dash=True)
  d.edge('d','s','<<include>>',dash=True)
  d.text(100,1400,'Administrators may use ordinary campus features; moderation does not grant ownership of another report.',28,False,False)
  d.text(100,1450,'Operator is a privileged deployment actor. Public registration cannot create administrator accounts.',28,False,False)
 d.save()
# 3 Sequence
q=D('03_analysis_sequence','Sequence | Report, moderate and recover','Boundary-control-entity analysis  /  Report creation, administrator verification and creator confirmation',h=1900)
xs=[220,690,1210,1720,2200];titles=['Campus user','Browser / forms','Flask controls','SQLite entities','Administrator']
for x,t in zip(xs,titles):
 q.box(t,x-165,240,330,115,t,fill=BLUE,size=27);q.line([(x,355),(x,1580)],arrow=False,dash=True,color=MUTED)
def msg(a,b,y,t,ret=False):q.line([(xs[a],y),(xs[b],y)],t,((xs[a]+xs[b])/2,y-26),dash=ret)
msg(0,1,420,'1 Submit lost / found details');msg(1,2,520,'2 POST /report + session + CSRF');msg(2,3,630,'3 Validate; INSERT reporter-owned report');msg(3,2,735,'4 Pending + open report reference',True);msg(2,1,830,'5 Redirect to report details',True)
msg(4,2,950,'6 POST moderation: verify + admin guard');msg(2,3,1060,'7 UPDATE moderation; audit decision');msg(0,1,1190,'8 Confirm return; mark recovered');msg(1,2,1300,'9 POST /items/<id>/recover + CSRF');msg(2,3,1410,'10 Check owner + state; update; audit');msg(2,1,1515,'11 Show recovered state',True)
q.text(100,1650,'Alternative paths: invalid input -> form feedback; invalid CSRF -> 400; another user recovery -> 403.',29,False,False)
q.text(100,1710,'Closed / unverified recovery -> 409 when visible; hidden report -> 404. No authorized update occurs.',29,False,False)
q.text(100,1770,'Physical handover is confirmed by the creator; the application records the software workflow.',29,False,False);q.save()
# 4 ER
r=D('04_entity_relationship','Entity relationships | Implemented SQLite schema','Primary keys, foreign keys and cardinalities  /  Each connecting role is shown separately',h=1900)
r.box('u',90,250,600,460,'USER','PK  id\nname\nemail  UNIQUE, NOT NULL\npassword_hash\nrole: student | faculty | administrator\ncreated_at',size=29)
r.box('r',900,250,650,735,'REPORT','PK  id\nFK  reporter_id -> USER.id  NOT NULL\nFK  moderator_id -> USER.id  NULL\nkind: lost | found\ntitle, description, category\nlocation, item_date\nstatus: open | recovered\nmoderation: pending | verified | removed\nmoderation_reason\ncreated_at, recovered_at',fill=TEAL,size=28)
r.box('m',1760,250,550,470,'MESSAGE','PK  id\nFK  report_id -> REPORT.id\nFK  sender_id -> USER.id\nFK  recipient_id -> USER.id\nbody\ncreated_at',size=28)
r.box('a',90,1260,780,330,'AUDIT_EVENT','PK  id\nFK  actor_id -> USER.id  NULL\nevent, object_id (logical reference)\noutcome, created_at',fill=AMBER,size=29)
r.box('l',1480,1260,830,330,'LOGIN_ATTEMPT','PK  id\nemail (may be an unknown login identifier)\nsource (keyed source hash)\ncreated_at; no USER foreign key',fill=AMBER,size=29)
r.line([(690,360),(900,360)],'creates\n1 : 0..N',(795,290));r.line([(690,540),(805,540),(805,620),(900,620)],'moderates\n0..1 : 0..N',(795,465))
r.line([(1550,430),(1760,430)],'has\n1 : 0..N',(1655,345))
r.line([(390,710),(390,1070),(2035,1070),(2035,720)],'sends  1 : 0..N',(1440,1040));r.line([(550,710),(550,1160),(2190,1160),(2190,720)],'receives  1 : 0..N',(1430,1130))
r.line([(215,710),(215,1260)],'performs\n0..1 : 0..N',(225,920))
r.text(100,1690,'Every report has one reporter and an optional moderator. Every message has one report, sender and recipient.',29,False,False)
r.text(100,1750,'Cardinalities read as parent participation : number of child records. Login attempts are independent records.',29,False,False);r.save()
# 5 DFD context
c=D('05_dfd_level_0','DFD Level 0 | System context','External actors and named data flows  /  The entire application is one process')
c.zone(660,270,1040,900,'TB1  Client / application boundary')
c.box('u',80,440,420,180,'E1 Campus user','Student / Faculty',fill=TEAL)
c.box('a',1900,440,420,180,'E2 Administrator','Moderation / audit',fill=TEAL)
c.box('p',780,450,800,370,'P0 College Lost and Found','Identity | Report | Search\nContact | Recover | Moderate',shape='ellipse',size=33)
c.box('o',800,1270,760,140,'E3 Privileged operator','Deployment, secrets and storage',fill=AMBER)
c.line([(500,480),(780,560)],'F01 Credentials / reports / search',(620,420));c.line([(780,730),(590,900),(290,900),(290,620)],'F02 Verified reports / own reports / messages',(595,940))
c.line([(1900,480),(1580,560)],'F03 Moderation decisions / audit queries',(1810,420));c.line([(1580,730),(1790,900),(2110,900),(2110,620)],'F04 Review queue / audit metadata',(1810,940))
c.line([(1180,1270),(1180,820)],'F05 Runtime configuration / backup access',(1390,1080))
c.text(100,1470,'Deployed client flows use HTTPS. E3 crosses TB3, the privileged operational boundary.',28,False,False);c.save()
# 6 DFD 1
v=D('06_dfd_level_1','DFD Level 1 | Processes, stores and trust boundaries','P0 decomposed into P1-P4  /  Bidirectional client flows  /  D1-D4 share one private SQLite database',h=1900)
v.zone(460,240,1260,1400,'TB1  Browser / application');v.zone(1850,240,480,1400,'TB2  Application / private data')
v.box('u',60,520,320,150,'E1 Campus user','Student / Faculty',fill=TEAL,size=27);v.box('a',60,1400,320,150,'E2 Administrator','Privileged review',fill=TEAL,size=27)
for i,(id,t,b,store,sbody) in enumerate([('P1','P1 Identity / sessions','Validate identity; throttle login','D1 Users + attempts','Hash / role / attempt keys'),('P2','P2 Reports / search','Pending creation; verified discovery','D2 Reports','Ownership / states / content'),('P3','P3 Contact / recovery','Participant inbox; creator closure','D3 Messages','Sender / recipient / body'),('P4','P4 Moderation / audit','Admin decisions; event review','D4 Audit events','Actor / event / outcome')]):
 y=340+i*320;v.box(id,620,y,870,175,t,b,shape='ellipse',size=29);v.box('D'+str(i+1),1890,y,400,175,store,sbody,shape='store',fill=AMBER,size=25)
 v.line([(1490,y+55),(1890,y+55)],['Credential / attempt data','Create / query reports','Write / query messages','Append / read audit events'][i],(1690,y+20));v.line([(1890,y+135),(1490,y+135)],['User / throttle result','Report rows / states','Participant messages','Audit metadata'][i],(1690,y+205))
v.line([(380,550),(480,550),(480,427),(620,427)],'Credentials / session',(475,470));v.line([(380,580),(500,580),(500,747),(620,747)],'Reports / search results',(490,695));v.line([(380,620),(480,620),(480,1067),(620,1067)],'Contact / messages / recovery',(485,955));v.edge('a','P4','Decisions / queue / audit',pos=(485,1440))
v.line([(1490,1090),(1770,1090),(1770,820),(1890,820)],'Recovery updates D2',(1630,1040));v.line([(1490,1400),(1810,1400),(1810,865),(2090,865),(2090,835)],'Moderation updates D2',(1660,1450))

for pts in [[(415,550),(380,550)],[(415,580),(380,580)],[(415,620),(380,620)],[(415,1465),(380,1465)]]:v.line(pts)
v.text(100,1720,'P1 supplies identity to protected routes; P1-P3 also append security events to D4 (shared audit function).',28,False,False)
v.text(100,1775,'TB3: privileged operator controls secrets, container images, persistent volumes and backups.',28,False,False);v.save()
# 7 DFD 2 recovery
w=D('07_dfd_level_2_recovery','DFD Level 2 | Detailed creator-only recovery','P3 recovery subflow  /  Session identity is authoritative; report ownership never comes from the form',h=1900)
w.box('u',70,300,400,160,'E1 Report creator','Report ID + CSRF token',fill=TEAL)
w.zone(590,240,1210,1270,'TB1  Protected Flask application')
for id,x,y,t,b in [('p1',680,330,'P3.1 Authenticate + CSRF','Read current user; validate token'),('p2',680,640,'P3.2 Load report + authorize','reporter_id == session user.id'),('p3',680,950,'P3.3 Validate state','moderation=verified; status=open')]:w.box(id,x,y,990,170,t,b,shape='ellipse',size=30)
w.box('d2',1900,520,400,250,'D2 Reports','Owner + current state\nRecovery timestamp',fill=AMBER,shape='store',size=27)
w.box('update',680,1240,990,170,'P3.4 Update + audit','Parameterized UPDATE; append item_recovered',shape='ellipse',size=29)
w.box('d4',1900,950,400,170,'D4 Audit events','Actor / object / outcome',fill=AMBER,shape='store',size=26)
w.edge('u','p1','POST recovery',pos=(555,325));w.edge('p1','p2','Identity + report ID',side='bottom',end='top');w.edge('p2','p3','Authorized report',side='bottom',end='top');w.edge('p2','d2','Read report',pos=(1790,610));w.line([(1900,710),(1740,710),(1740,790),(1670,790)],'Owner / state',(1800,805));w.edge('p3','update','Verified + open',side='bottom',end='top',pos=(1175,1180))
w.line([(1670,1280),(1840,1280),(1840,645),(1900,645)],'Recovery update',(1780,870))
w.line([(1670,1350),(1810,1350),(1810,1035),(1900,1035)],'Audit metadata',(1820,1425))
w.box('out',680,1590,1620,130,'Response and denial audit','Success -> redirect | invalid CSRF -> 400 | unauthorized -> 403 | invalid state -> 409',fill=TEAL,size=28)
w.line([(1175,1410),(1175,1590)],'Result / redirect',(1360,1525));w.text(100,1790,'Invisible or missing report -> 404. Invalid inputs terminate the path; the report is not modified.',27,False,False);w.save()
# 8 Architecture
for refined in [False,True]:
 a=D('11_security_refined_architecture' if refined else '08_application_architecture','Architecture | Security controls by layer' if refined else 'Architecture | Modular monolith and deployment','Implementation view  /  Browser -> Caddy -> Gunicorn / Flask -> private SQLite',h=1800)
 a.box('b',90,300,400,190,'Browser','Server-rendered forms\nStudent / Faculty / Admin',fill=TEAL,size=27);a.box('tls',750,300,440,190,'Caddy TLS proxy','HTTPS :8443\nInternal HTTP :8080',size=28)
 a.zone(1360,230,940,1110,'Application runtime  /  non-root UID 10001')
 a.box('gate',1440,330,780,210,'Request and response security','Trusted hosts | session lookup | CSRF\nCSP | output escaping | secure cookies',fill=BLUE,size=29)
 a.box('service',1440,710,780,210,'Flask route and policy layer','Identity | reports | contact | recovery\nAdmin moderation | participant inbox',fill=TEAL,size=29)
 a.box('repo',1440,1090,780,175,'Database access layer','Parameterized SQL | bounded queries\nForeign keys | constrained report states',size=28)
 a.box('db',700,1080,510,240,'Private SQLite persistence','Users | reports | messages\nAudit events | login attempts\nDocker volume / Kubernetes PVC',fill=AMBER,shape='store',size=27)
 a.edge('b','tls','HTTPS',pos=(620,355));a.edge('tls','gate','Internal HTTP',pos=(1300,345));a.edge('gate','service','Authenticated context',side='bottom',end='top',pos=(1830,625));a.edge('service','repo','Policy-checked operation',side='bottom',end='top',pos=(1830,1010));a.edge('repo','db','Read / write',side='left',end='right',pos=(1310,1100))
 if refined:a.box('policy',90,650,1120,280,'Policies on the highest-risk paths','Recovery: creator ID + open / verified state\nModeration: administrator guard\nInbox: sender / recipient scope; replies: recipient only\nIdentity: scrypt + atomic login throttling',fill=TEAL,size=28)
 else:a.box('policy',90,650,1120,280,'Design responsibilities','Boundary: forms and rendered templates\nControl: authentication, validation and route policies\nEntity: relational records in SQLite\nApplication factory with shared guards and audit helper',size=28)
 a.text(100,1450,'Docker: read-only root filesystem, dropped capabilities, runtime secret, health checks and resource limits.',28,False,False)
 a.text(100,1520,'Kubernetes: one replica / Recreate, restricted namespace, Secret, PVC, ClusterIP and RuntimeDefault seccomp.',28,False,False)
 a.text(100,1590,'Operator-managed: volume permissions, backups and trusted TLS certificates. NetworkPolicy enforcement needs verification.',27,False,False)
 a.text(100,1660,'Signed Flask session cookies are not encrypted; private records remain server-side.',27,False,False);a.save()
# 9 Sensitive flows
f=D('09_sensitive_information_flow','Information flow | Assets, permissions and recipients','Confidentiality and integrity controls  /  Audit records metadata rather than secret content',h=1800)
heads=[('Input asset',300),('Server-side policy',1100),('Authorized destination',2010)]
for t,x in heads:f.text(x,260,t,31,True)
rows=[('Credentials','Email + password','Identity verification','TLS | scrypt hash comparison','D1 User store','Hash never returned to client',BLUE),('Private message','Untrusted participant text','Contact / reply policy','Recipient derived server-side','D3 Participant inbox','Escaped text; no account emails',TEAL),('Recovery decision','Creator + report ID + CSRF','Ownership + state policy','Open verified report required','D2 Report + D4 Audit','Recovery timestamp; metadata',BLUE),('Moderation decision','Admin + action + reason','Administrator policy','Allowlisted action; reason bounds','D2 Report + D4 Audit','Visibility state; actor and outcome',AMBER)]
for i,(t,b,pt,pb,dt,db,col) in enumerate(rows):
 y=350+i*290;f.box('a'+str(i),80,y,480,170,t,b,fill=col,size=29);f.box('p'+str(i),760,y,700,170,pt,pb,fill=col,size=29);f.box('d'+str(i),1720,y,590,170,dt,db,fill=col,size=29);f.edge('a'+str(i),'p'+str(i),'TB1',pos=(660,y+60));f.edge('p'+str(i),'d'+str(i),'Authorized flow',pos=(1590,y+60))
f.text(100,1590,'Excluded from audit: passwords, session secrets and private message bodies. Public reports omit account emails.',28,False,False)
f.text(100,1650,'SQLite files are private but not encrypted by the application; storage and backup protection belongs to the operator.',28,False,False);f.save()
# 10 Attack tree
at=D('10_attack_tree','Attack tree | Unauthorized report recovery','Threat model  /  Hypothetical attack prerequisites and controls; these are not demonstrated vulnerabilities',h=1900)
at.box('root',790,245,820,145,'ROOT GOAL','Mark another creator\'s report recovered',fill=RED,size=32);at.text(1200,445,'OR',32,True)
branches=[(70,'A1 Compromise creator identity','A2 Steal password or session','A3 Authenticate as report creator','scrypt | TLS | HttpOnly cookies\nLogin throttling | denial audit'),(850,'B1 Bypass recovery policy','B2 Choose a victim report ID','B3 Defeat owner + CSRF checks','Server-derived identity | creator check\nState check | CSRF | bound SQL'),(1630,'C1 Modify persistent data','C2 Obtain host / volume access','C3 Write unauthorized state directly','Operator access controls | volume ACLs\nBackups | external integrity monitoring')]
for i,(x,t,l1,l2,ctrl) in enumerate(branches):
 id=str(i);at.box(id,x,540,700,150,t,'Both prerequisites required',fill=BLUE,size=28);at.line([(1200,390),(1200,485),(x+350,485),(x+350,540)],arrow=False);at.text(x+350,760,'AND',30,True)
 at.box('l'+id,x,850,700,130,l1,fill=RED,size=28);at.box('m'+id,x,1090,700,130,l2,fill=RED,size=28);at.line([(x+350,690),(x+350,850)],arrow=False);at.line([(x+350,760),(x+740,760),(x+740,1155),(x+700,1155)],arrow=False)
 at.box('c'+id,x,1360,700,230,'Prevent / detect',ctrl,fill=TEAL,size=27)
at.text(100,1700,'OR: any complete branch can satisfy the root goal. AND: every prerequisite within that branch is needed.',28,False,False)
at.text(100,1760,'Branches A/B have application controls. Branch C depends on privileged infrastructure access and operator controls.',28,False,False);at.save()
# 12 lifecycle
l=D('12_report_lifecycle','State model | Moderation and recovery lifecycle','Two independent state fields  /  moderation: pending, verified, removed  /  status: open, recovered',h=1550)
l.box('p',100,430,610,230,'Created report','moderation = pending\nstatus = open\nOwned by authenticated creator',fill=AMBER,size=30)
l.box('v',900,430,610,230,'Discoverable report','moderation = verified\nstatus = open\nPrivate contact / reply allowed',fill=BLUE,size=30)
l.box('r',1700,430,610,230,'Recovered report','moderation = verified\nstatus = recovered\nFurther contact / reply rejected',fill=TEAL,size=30)
l.edge('p','v','Administrator verifies',pos=(805,410));l.edge('v','r','Creator confirms handover',pos=(1605,410))
l.box('x',900,1000,610,210,'Removed report','moderation = removed\nstatus preserved\nHidden from ordinary discovery',fill=RED,size=30)
l.line([(405,660),(405,1105),(900,1105)],'Administrator removes\nReason required',(425,845));l.line([(1205,660),(1205,1000)],'Administrator removes',(1410,820));l.line([(2005,660),(2005,1105),(1510,1105)],'Administrator removes\nStatus may remain recovered',(2010,835))
l.text(100,1340,'The implementation permits later administrator moderation changes. Moderation does not transfer report ownership.',28,False,False)
l.text(100,1400,'Recovery requires creator identity + verified + open. Repeated recovery is rejected; handover is an external action.',28,False,False);l.save()
files=sorted(OUT.glob('*.png'))
thumbs=[]
for p in files:
 im=Image.open(p);im.thumbnail((800,640));tile=Image.new('RGB',(800,690),'#eeeeee');tile.paste(im,(0,35));ImageDraw.Draw(tile).text((15,10),p.stem,font=ImageFont.truetype(B,20),fill=INK);thumbs.append(tile)
sheet=Image.new('RGB',(2400,690*4),'#eeeeee')
for i,t in enumerate(thumbs):sheet.paste(t,((i%3)*800,(i//3)*690))
sheet.save(OUT/'preview.jpg')
(OUT/'README.md').write_text('# College Lost and Found detailed diagrams\n\nTwelve independently rendered diagrams in PNG and editable SVG. Models follow the supplied College report and local app.py, schema.sql, compose.yaml and deploy/kubernetes.yaml. The ShieldEdge and midsem reports supplied visual examples only. Diagrams are newly authored vector layouts, not generated evidence screenshots.\n\n'+ '\n'.join('- '+p.stem for p in files),encoding='utf8')
with zipfile.ZipFile(OUT/'College_Lost_and_Found_Detailed_Diagrams.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in OUT.iterdir():
  if p.suffix in ['.png','.svg','.md'] and p.name!='preview.jpg':z.write(p,p.name)
print('Created',len(files),'separate diagram images with editable SVG sources in',OUT)
