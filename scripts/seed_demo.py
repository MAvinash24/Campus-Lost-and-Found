"""Seed demonstrator accounts from stdin; never print or save supplied passwords."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app,now
from werkzeug.security import generate_password_hash
state=json.load(sys.stdin);app=create_app()
with app.app_context():
    for role,account in state['accounts'].items():
        name={'student':'Marisetti Avinash','faculty':'Faculty Demo','administrator':'Campus Administrator'}[role]
        app.db().execute('INSERT OR IGNORE INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',(name,account['email'],generate_password_hash(account['password'],method='scrypt'),role,now()))
    app.db().commit()
print('Demo identities provisioned; credential values were not printed.')
