"""Generate monochrome PNG, SVG and editable draw.io diagrams from one model."""
import html
import math
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT=Path('deliverables/images');OUT.mkdir(parents=True,exist_ok=True)
SRC=Path('deliverables/editable');SRC.mkdir(parents=True,exist_ok=True)
FONT='C:/Windows/Fonts/arial.ttf'
BOLD='C:/Windows/Fonts/arialbd.ttf'

class Diagram:
    def __init__(self,name,title,width=2200,height=1450):
        self.name=name;self.width=width;self.height=height
        self.im=Image.new('RGB',(width,height),'white');self.d=ImageDraw.Draw(self.im)
        self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="white"/>']
        self.mx=ET.Element('mxfile',host='app.diagrams.net');diagram=ET.SubElement(self.mx,'diagram',name=title)
        model=ET.SubElement(diagram,'mxGraphModel',dx=str(width),dy=str(height),grid='1',page='1',pageWidth=str(width),pageHeight=str(height));self.root=ET.SubElement(model,'root')
        ET.SubElement(self.root,'mxCell',id='0');ET.SubElement(self.root,'mxCell',id='1',parent='0')
        self.nodes={};self.count=0
        self.text(width/2,55,title,42,True)
        self.text(width/2,height-45,'College Lost and Found  |  20CYS401  |  Marisetti Avinash  |  CH.SC.U4CYS23024',24)

    def text(self,x,y,text,size=30,bold=False,center=True):
        font=ImageFont.truetype(BOLD if bold else FONT,size)
        lines=text.split('\n')
        for i,line in enumerate(lines):
            yy=y+i*(size+10)
            self.d.text((x,yy),line,fill='black',font=font,anchor='mm' if center else 'lm')
            self.svg.append(f'<text x="{x}" y="{yy+size*.34}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{"middle" if center else "start"}" fill="black">{html.escape(line)}</text>')

    def box(self,id,x,y,w,h,text,shape='rect',fill='white',size=30,dashed=False):
        self.nodes[id]=(x,y,w,h)
        if shape=='actor':
            cx=x+w/2
            self.d.ellipse((cx-22,y,cx+22,y+44),fill='white',outline='black',width=3)
            self.d.line([(cx,y+44),(cx,y+100)],fill='black',width=3)
            self.d.line([(cx-45,y+63),(cx+45,y+63)],fill='black',width=3)
            self.d.line([(cx-42,y+137),(cx,y+100),(cx+42,y+137)],fill='black',width=3)
            self.svg.append(f'<circle cx="{cx}" cy="{y+22}" r="22" fill="white" stroke="black" stroke-width="3"/><path d="M{cx} {y+44} V{y+100} M{cx-45} {y+63} H{cx+45} M{cx-42} {y+137} L{cx} {y+100} L{cx+42} {y+137}" fill="none" stroke="black" stroke-width="3"/>')
            self.text(cx,y+170,text,size)
        elif shape=='ellipse':
            self.d.ellipse((x,y,x+w,y+h),fill=fill,outline='black',width=3)
            self.svg.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}" stroke="black" stroke-width="3"/>')
        else:
            self.d.rectangle((x,y,x+w,y+h),fill=fill,outline='black',width=3)
            self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="black" stroke-width="3" {"stroke-dasharray='12 8'" if dashed else ""}/>')
        lines=text.split('\n')
        if shape!='actor':self.text(x+w/2,y+h/2-(len(lines)-1)*(size+10)/2,text,size)
        cell=ET.SubElement(self.root,'mxCell',id=id,value=text,style=f'{"shape=umlActor;" if shape=="actor" else "ellipse;" if shape=="ellipse" else "rounded=0;"}whiteSpace=wrap;html=0;fillColor={"#f2f2f2" if fill!="white" else "#ffffff"};strokeColor=#000000;fontColor=#000000;fontSize={size};'+('dashed=1;' if dashed else ''),vertex='1',parent='1')
        ET.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})

    def boundary(self,x,y,w,h,label):
        self.d.rectangle((x,y,x+w,y+h),outline='#888',width=3)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#666" stroke-width="3" stroke-dasharray="14 10"/>')
        self.text(x+20,y+28,label,25,True,False)
        self.count+=1
        cell=ET.SubElement(self.root,'mxCell',id=f'b{self.count}',value=label,style='fillColor=none;strokeColor=#777777;dashed=1;verticalAlign=top;align=left;fontSize=25;',vertex='1',parent='1')
        ET.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})

    def edge(self,a,b,label='',start='right',end='left',dashed=False,arrow=True,via=None,label_offset=(0,0)):
        def point(id,side):
            x,y,w,h=self.nodes[id]
            return {'left':(x,y+h/2),'right':(x+w,y+h/2),'top':(x+w/2,y),'bottom':(x+w/2,y+h)}[side]
        p1,p2=point(a,start),point(b,end)
        points=[p1]+(via or [])+[p2]
        if dashed:
            for (x1,y1),(x2,y2) in zip(points,points[1:]):
                dist=math.hypot(x2-x1,y2-y1)
                for step in range(0,int(dist),20):
                    a1=step/dist;a2=min(step+11,dist)/dist
                    self.d.line((x1+(x2-x1)*a1,y1+(y2-y1)*a1,x1+(x2-x1)*a2,y1+(y2-y1)*a2),fill='black',width=3)
        else:self.d.line(points,fill='black',width=3)
        path=' '.join(f'{x},{y}' for x,y in points)
        self.svg.append(f'<polyline points="{path}" fill="none" stroke="black" stroke-width="3" {"stroke-dasharray='10 7'" if dashed else ""}/>')
        if arrow:
            x,y=p2;px,py=points[-2];ang=math.atan2(y-py,x-px)
            tri=[(x,y),(x-17*math.cos(ang-.5),y-17*math.sin(ang-.5)),(x-17*math.cos(ang+.5),y-17*math.sin(ang+.5))]
            self.d.polygon(tri,fill='white' if arrow=='generalization' else 'black',outline='black');self.svg.append('<polygon points="'+' '.join(f'{xx},{yy}' for xx,yy in tri)+f'" fill="{"white" if arrow=="generalization" else "black"}" stroke="black"/>')
        if label:
            x=(p1[0]+p2[0])/2+label_offset[0];y=(p1[1]+p2[1])/2-22+label_offset[1]
            font=ImageFont.truetype(FONT,24);bbox=self.d.textbbox((x,y),label,font=font,anchor='mm');self.d.rectangle((bbox[0]-5,bbox[1]-5,bbox[2]+5,bbox[3]+5),fill='white')
            self.svg.append(f'<rect x="{bbox[0]-5}" y="{bbox[1]-5}" width="{bbox[2]-bbox[0]+10}" height="{bbox[3]-bbox[1]+10}" fill="white"/>');self.text(x,y,label,24)
        self.count+=1
        cell=ET.SubElement(self.root,'mxCell',id=f'e{self.count}',value=label,style='edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;strokeColor=#000000;fontColor=#000000;fontSize=24;'+('dashed=1;' if dashed else '')+('endArrow=block;endFill=0;' if arrow=='generalization' else 'endArrow=classic;' if arrow else 'endArrow=none;'),edge='1',parent='1',source=a,target=b)
        ET.SubElement(cell,'mxGeometry',relative='1',attrib={'as':'geometry'})

    def save(self):
        self.im.save(OUT/(self.name+'.png'))
        (OUT/(self.name+'.svg')).write_text(''.join(self.svg)+'</svg>',encoding='utf8')
        ET.ElementTree(self.mx).write(SRC/(self.name+'.drawio'),encoding='utf-8',xml_declaration=True)

def build():
    d=Diagram('use_cases','UML use cases and authorization relationships',height=1600)
    d.boundary(440,140,1650,1300,'Campus Lost and Found system')
    d.box('student',20,190,150,190,'Student','actor',size=27)
    d.box('faculty',220,190,150,190,'Faculty','actor',size=27)
    d.box('campus',60,650,280,190,'Campus user','actor',size=27)
    d.box('admin',60,1050,280,110,'Administrator','actor')
    cases=[('UC01',550,200,'UC01 Register / sign in'),('UC02',550,390,'UC02 Report lost / found'),('UC03',550,580,'UC03 Search / view'),('UC04',550,770,'UC04 Contact / reply'),('UC05',550,960,'UC05 Mark recovered'),('UC06',550,1150,'UC06 Verify / remove'),('UC07',1130,200,'UC07 Track own reports'),('UC08',1130,1310,'UC08 Review audit'),('validate',1500,390,'Validate input'),('owner',1500,960,'Authorize owner'),('audit',1500,1150,'Record decision')]
    for id,x,y,t in cases:d.box(id,x,y,480,110,t,'ellipse',size=27)
    for actor in ['student','faculty']:d.edge(actor,'campus',start='bottom',end='top',arrow='generalization')
    for uc in ['UC01','UC02','UC03','UC04','UC05']:d.edge('campus',uc,arrow=False)
    d.edge('campus','UC07',start='right',end='top',arrow=False,via=[(380,745),(380,160),(1370,160)])
    d.edge('admin','UC06',arrow=False)
    d.edge('admin','UC08',arrow=False,start='bottom',end='left',via=[(200,1350),(1000,1350)])
    d.edge('UC02','validate','«include»',dashed=True,label_offset=(0,-10))
    d.edge('UC05','owner','«include»',dashed=True)
    d.edge('UC06','audit','«include»',dashed=True)
    d.edge('UC04','UC03','«extend» open verified report',start='top',end='bottom',dashed=True,label_offset=(230,0))
    d.text(1080,1470,'Student and Faculty can also contact, recover their own report and track progress.\nAdministrator includes ordinary user capabilities; every mutation requires authentication.',26)
    d.save()

    d=Diagram('analysis_sequence','Scenario analysis  Report an item and complete recovery')
    roles=[('user','Campus user'),('ui','Boundary\nReport form'),('control','Control\nReport service'),('entity','Entity\nReport repository'),('admin','Administrator')]
    for i,(id,t) in enumerate(roles):
        x=70+i*430;d.box(id,x,145,330,110,t,fill='#f2f2f2')
        d.d.line((x+165,255,x+165,1260),fill='#777',width=2)
        d.svg.append(f'<line x1="{x+165}" y1="255" x2="{x+165}" y2="1260" stroke="#777" stroke-dasharray="8 6"/>')
    seq=[(0,1,340,'1 Enter lost or found details'),(1,2,450,'2 Validate input + CSRF + user'),(2,3,560,'3 Save pending report with reporter ID'),(3,1,670,'4 Return report reference and pending status'),(4,2,780,'5 Verify legitimate report'),(2,3,890,'6 Store moderation and audit event'),(0,2,1000,'7 Confirm recovery after handover'),(2,3,1110,'8 Authorize reporter; set recovered; audit')]
    for a,b,y,t in seq:
        p1=(235+a*430,y);p2=(235+b*430,y);d.d.line((p1,p2),fill='black',width=3)
        direction=1 if p2[0]>p1[0] else -1;d.d.polygon([p2,(p2[0]-direction*18,y-9),(p2[0]-direction*18,y+9)],fill='black')
        d.svg.append(f'<line x1="{p1[0]}" y1="{y}" x2="{p2[0]}" y2="{y}" stroke="black" stroke-width="3"/>');d.text((p1[0]+p2[0])/2,y-25,t,25)
    d.text(1100,1305,'Alternative: invalid form → validation feedback. Unauthorized recovery → 403, state unchanged.\nThe generic examination scenario is adapted to the assigned case study, as instructed.',25);d.save()

    d=Diagram('er_model','ER model  Keys relationships and cardinalities',height=1500)
    d.box('users',75,180,520,400,'USERS\nPK id\nname | UNIQUE email\npassword_hash | role\ncreated_at',size=32)
    d.box('reports',825,180,620,560,'REPORTS\nPK id\nFK reporter_id → users.id\nFK moderator_id → users.id (nullable)\nkind | title | description | category\nlocation | item_date | status\nmoderation | moderation_reason\ncreated_at | recovered_at',size=30)
    d.box('messages',1680,180,450,480,'MESSAGES\nPK id\nFK report_id → reports.id\nFK sender_id → users.id\nFK recipient_id → users.id\nbody | created_at',size=29)
    d.box('audits',75,900,640,310,'AUDIT_EVENTS\nPK id | FK actor_id → users.id (nullable)\nevent | object_id | outcome | created_at\nobject_id is a logical reference',size=29)
    d.box('attempts',1320,920,760,250,'LOGIN_ATTEMPTS\nPK id | email | source (keyed hash) | created_at\nNo user FK: includes unknown login identifiers',size=30)
    d.edge('users','reports','1 reporter : 0..N reports',label_offset=(0,-90))
    d.edge('reports','messages','1 report : 0..N messages',label_offset=(0,-90))
    d.edge('users','messages','1 sender : 0..N messages',start='bottom',end='bottom',via=[(660,580),(660,790),(1905,790)],label_offset=(0,180))
    d.edge('users','messages','1 recipient : 0..N messages',start='bottom',end='bottom',via=[(710,580),(710,860),(2010,860)],label_offset=(0,250))
    d.edge('users','audits','0..1 actor : 0..N events',start='bottom',end='top',label_offset=(150,0))
    d.text(1100,1230,'Each report has exactly 1 reporter and 0..1 moderator.\nEach message has exactly 1 sender and 1 recipient.',30)
    d.text(1100,1330,'SQLite enforces FK constraints and state enumerations.\nPassword hashes and emails are excluded from public report and inbox queries.',29);d.save()

    d=Diagram('dfd_level0','Level 0 DFD  System context and trust boundary')
    d.boundary(690,210,840,900,'TB1  Application trust zone')
    d.box('user',80,360,460,190,'E1 Campus user\nStudent / Faculty',fill='#f2f2f2',size=35)
    d.box('system',780,440,660,350,'P0 Campus Lost and Found\nAuthenticate · Report · Search\nContact · Recover · Moderate','ellipse',size=34)
    d.box('admin',1710,360,400,190,'E2 Administrator',fill='#f2f2f2',size=34)
    d.box('operator',780,1180,660,140,'E3 Operator  Deployment and backup',fill='#f2f2f2',size=30)
    d.edge('user','system','Credentials / reports / contact',label_offset=(0,-80))
    d.edge('system','user','Verified reports / private messages',start='left',end='right',via=[(650,900),(540,900)],label_offset=(0,170))
    d.edge('admin','system','Moderation decision',start='bottom',end='top',via=[(1910,660),(1540,660),(1540,320),(1110,320)],label_offset=(50,-220))
    d.edge('system','admin','Review queue / audit events',label_offset=(0,90))
    d.edge('operator','system','Secret / image / storage',start='top',end='bottom')
    d.text(1100,1020,'All client flows use HTTPS in the container deployment.\nOperator is a privileged actor, not an ordinary campus user.',30);d.save()

    d=Diagram('dfd_level1','Level 1 DFD  Processes stores and trust boundaries',height=1800)
    d.boundary(420,160,1650,1450,'TB1 Browser → application   |   TB2 Application → private persistent store')
    d.box('user',45,280,290,180,'E1 Campus user\nStudent / Faculty',fill='#f2f2f2',size=29)
    d.box('admin',45,1040,290,150,'E2 Administrator',fill='#f2f2f2',size=28)
    processes=[('P1',500,260,'P1 Identity / sessions'),('P2',500,590,'P2 Reports / search'),('P3',500,920,'P3 Contact / recovery'),('P4',500,1250,'P4 Moderation / audit')]
    stores=[('D1',1470,260,'D1 Users + login attempts'),('D2',1470,590,'D2 Reports'),('D3',1470,920,'D3 Private messages'),('D4',1470,1250,'D4 Audit events')]
    for id,x,y,t in processes:d.box(id,x,y,640,150,t,'ellipse',size=31)
    for id,x,y,t in stores:d.box(id,x,y,520,150,t,fill='#f2f2f2',size=31)
    for p,s,label in [('P1','D1','Credentials / throttling'),('P2','D2','Pending report / verified search'),('P3','D3','Participant-scoped messages'),('P4','D4','Security event metadata')]:d.edge(p,s,label)
    d.edge('user','P1','Sign in',label_offset=(0,-30))
    d.edge('user','P2','Report / search',label_offset=(0,-30))
    d.edge('user','P3','Contact / recover',label_offset=(0,-30))
    d.edge('admin','P4','Verify / remove',label_offset=(0,-30))
    d.edge('P3','D2','Owner-only recovery',start='top',end='bottom',label_offset=(100,0))
    d.edge('P4','D2','Admin moderation',start='bottom',end='bottom',via=[(820,1470),(2050,1470),(2050,830),(1730,830)],label_offset=(550,100))
    d.text(1110,1550,'P1 authenticates all protected routes. P1 P2 and P3 also append events to D4.\nTB3 Operator → secrets / image / data volumes; operator access is controlled outside the application.',28)
    d.save()

    for refined in [False,True]:
        d=Diagram('architecture_refined' if refined else 'architecture','Security refined architecture' if refined else 'Layered modular application architecture')
        d.box('browser',60,270,430,190,'Browser interface\nStudent / Faculty / Admin',fill='#f2f2f2',size=31)
        d.box('proxy',680,270,410,190,'Caddy TLS proxy\nlocalhost:8443',size=31)
        d.boundary(1250,160,850,1010,'Application container  UID 10001')
        d.box('middleware',1320,255,710,170,'Security middleware\nHost · CSRF · headers · session',fill='#f2f2f2',size=31)
        d.box('services',1320,565,710,230,'Flask services\nIdentity | Reports | Messaging\nRecovery | Moderation | Audit',size=33)
        d.box('repository',1320,920,710,150,'Repository access\nBounded queries + parameterized SQL',size=30)
        d.box('store',650,990,470,210,'SQLite persistent volume\nUsers · Reports · Messages\nAudit · Login attempts',fill='#f2f2f2',size=29)
        d.edge('browser','proxy','HTTPS  / private data')
        d.edge('proxy','middleware','Internal HTTP')
        d.edge('middleware','services','Authenticated context',start='bottom',end='top',label_offset=(210,0))
        d.edge('services','repository','Policy-checked operations',start='bottom',end='top',label_offset=(250,0))
        d.edge('repository','store','Read / write',start='left',end='right')
        if refined:
            d.box('controls',60,640,1040,260,'Highest-risk paths closed\nOwner policy for recovery | Admin policy for moderation\nParticipant policy for inbox | scrypt + atomic throttling\nEscaped output + strict CSP | secret outside image',size=30)
        else:
            d.box('patterns',60,640,1040,260,'Design concepts\nApplication factory · Decorator / guard\nRepository-style SQL access · Boundary / control / entity\nSeparation of concerns · Fail-closed state transitions',size=30)
        d.text(1100,1300,'Docker: non-root, read-only rootfs, dropped capabilities, health checks and resource limits.\nKubernetes: restricted namespace, ClusterIP, Secret, PVC, seccomp and NetworkPolicy.',29);d.save()

    d=Diagram('attack_tree','Attack tree  Modify another user’s recovery state',height=1500)
    d.box('root',680,160,830,140,'ROOT  Unauthorized report recovery\nOR',fill='#f2f2f2',size=34)
    for id,x,t in [('identity',80,'Compromise reporter identity\nAND'),('bypass',800,'Bypass recovery authorization\nAND'),('data',1520,'Modify data outside the app\nAND')]:
        d.box(id,x,460,610,130,t,size=31);d.edge('root',id,start='bottom',end='top')
    leaves=[('cred',80,800,'Obtain password / session\nAND authenticate as reporter'),('idor',800,800,'Choose victim report ID\nAND exploit missing owner check'),('host',1520,800,'Gain operator / volume access\nAND issue direct data write')]
    for id,x,y,t in leaves:
        d.box(id,x,y,610,160,t,size=30);d.edge({'cred':'identity','idor':'bypass','host':'data'}[id],id,start='bottom',end='top')
    for id,x,t in [('c1',80,'Prevent: scrypt, TLS, secure cookie, throttling\nDetect: login denials and unusual sessions'),('c2',800,'Prevent: reporter_id check + CSRF + SQL binding\nDetect: recovery_denied / item_recovered'),('c3',1520,'Prevent: host RBAC, storage ACL, backups\nDetect: external audit export / integrity checks')]:d.box(id,x,1110,610,170,t,fill='#f2f2f2',size=27)
    d.text(1100,1370,'OR: one branch can achieve the goal. AND: both prerequisites in that branch are required.',28);d.save()

    d=Diagram('information_flow','Sensitive information flow and recipient constraints')
    d.box('credentials',70,220,500,190,'A1 Credentials\nEmail + password',fill='#f2f2f2',size=33)
    d.box('auth',820,220,550,190,'P1 TLS sign in / verification\nPassword → scrypt comparison',size=31)
    d.box('users',1660,220,460,190,'D1 Private user store\nHash never in browser',size=31)
    d.box('message',70,600,500,190,'A3 Private message\nUntrusted sender text',fill='#f2f2f2',size=33)
    d.box('contact',820,600,550,190,'P3 Recipient policy\nEscaping + sender throttle',size=31)
    d.box('inbox',1660,600,460,190,'D3 → Participant inbox\nNo email disclosure',size=31)
    d.box('status',70,980,500,190,'A4 Recovery decision\nReporter-owned operation',fill='#f2f2f2',size=32)
    d.box('recover',820,980,550,190,'P3 Owner policy + CSRF\nOpen verified state required',size=31)
    d.box('audit',1660,980,460,190,'D2 Updated state\nD4 Audit metadata',size=31)
    for a,b,c in [('credentials','auth','users'),('message','contact','inbox'),('status','recover','audit')]:d.edge(a,b,'Trust boundary');d.edge(b,c,'Authorized flow')
    d.text(1100,1310,'No credential values or message bodies enter the audit trail.\nLocal storage is private but not application-encrypted; operators must secure volumes and backups.',30);d.save()

if __name__=='__main__':build();print('Generated 10 monochrome diagrams in PNG SVG and editable draw.io formats.')
