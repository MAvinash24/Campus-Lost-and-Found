"""Create local demonstration secrets and data; never print passwords."""
import json
import os
import secrets
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app, now
from werkzeug.security import generate_password_hash

root=Path(__file__).resolve().parents[1]
secretfile=root/'.local-secrets.json'
if secretfile.exists():
    state=json.loads(secretfile.read_text())
else:
    state={'APP_SECRET':secrets.token_hex(32),'accounts':{role:{'email':role+'@campus.example','password':secrets.token_urlsafe(18)} for role in ['student','faculty','administrator']}}
    secretfile.write_text(json.dumps(state,indent=2))
(root/'.env').write_text('APP_SECRET='+state['APP_SECRET']+'\n')
os.environ['APP_SECRET']=state['APP_SECRET']
app=create_app()
with app.app_context():
    for role,account in state['accounts'].items():
        name={'student':'Marisetti Avinash','faculty':'Faculty Demo','administrator':'Campus Administrator'}[role]
        app.db().execute('INSERT OR IGNORE INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',(name,account['email'],generate_password_hash(account['password'],method='scrypt'),role,now()))
    if app.db().execute('SELECT count(*) FROM reports').fetchone()[0]==0:
        student=app.db().execute("SELECT id FROM users WHERE role='student'").fetchone()[0]
        faculty=app.db().execute("SELECT id FROM users WHERE role='faculty'").fetchone()[0]
        admin=app.db().execute("SELECT id FROM users WHERE role='administrator'").fetchone()[0]
        for title,kind,cat,loc,desc,status,moderation,reporter in [
            ('Black canvas backpack','lost','Bags','Central library','Black canvas backpack with a silver zipper. Please keep any contents private.','open','verified',student),
            ('Silver keyring','found','Keys','Academic block A','Two silver keys on a plain metal ring. Identify a distinguishing detail to claim.','open','verified',faculty),
            ('Wireless headphones','lost','Electronics','Student activity centre','Over-ear headphones in a dark carrying case. Last seen near the reading area.','open','verified',faculty),
            ('Blue notebook','found','Documents','Cafeteria','A ruled notebook with a plain cover. No personal pages are published.','recovered','verified',student),
            ('Water bottle','found','Other','Sports complex','A steel bottle with a black lid, awaiting report verification.','open','pending',student)]:
            app.db().execute('INSERT INTO reports(reporter_id,kind,title,description,category,location,item_date,status,moderation,moderator_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(reporter,kind,title,desc,cat,loc,'2026-10-08',status,moderation,admin if moderation=='verified' else None,now()))
        app.db().execute('INSERT INTO messages(report_id,sender_id,recipient_id,body,created_at) VALUES(?,?,?,?,?)',(1,faculty,student,'I found a similar backpack near the library. Can you confirm a detail privately?',now()))
        app.db().execute('INSERT INTO audit_events(actor_id,event,object_id,outcome,created_at) VALUES(?,?,?,?,?)',(admin,'report_verified',1,'success',now()))
    app.db().commit()
print('Local demo initialized. Credentials are in the ignored .local-secrets.json file.')
