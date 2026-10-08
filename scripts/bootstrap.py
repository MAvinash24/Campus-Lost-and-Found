"""Bootstrap an administrator; all passwords are supplied through environment."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app, now
from werkzeug.security import generate_password_hash

def bootstrap():
    password = os.environ['ADMIN_PASSWORD']
    if len(password) < 12:
        raise SystemExit('ADMIN_PASSWORD must contain at least 12 characters.')
    app = create_app()
    with app.app_context():
        app.db().execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',
                         (os.getenv('ADMIN_NAME','Campus Administrator'), os.environ['ADMIN_EMAIL'].lower(), generate_password_hash(password,method='scrypt'), 'administrator', now()))
        app.db().commit()
    print('Administrator created. No credential values were printed.')

if __name__ == '__main__':
    bootstrap()
