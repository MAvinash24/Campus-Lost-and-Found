import re
import secrets
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from app import can_manage, create_app, now, validate_text
from werkzeug.security import generate_password_hash

TEST_HASH = generate_password_hash('TestPassphrase!123',method='scrypt')


class CampusTests(unittest.TestCase):
    def test_signing_secret_fails_closed(self):
        for value in ['', 'x' * 31]:
            with self.subTest(secret_length=len(value)), patch.dict('os.environ', {'APP_SECRET': value}):
                with self.assertRaises(RuntimeError):
                    create_app({'DATABASE': str(Path(self.tmp.name) / 'guard.db')})
        with patch.dict('os.environ', {'APP_SECRET': ''}):
            with self.assertRaises(RuntimeError):
                create_app({'SECRET_KEY': None, 'DATABASE': str(Path(self.tmp.name) / 'guard.db')})
            valid = secrets.token_hex(32)
            app = create_app({'TESTING': True, 'SECRET_KEY': valid, 'DATABASE': str(Path(self.tmp.name) / 'override.db')})
            self.assertEqual(app.secret_key, valid)
        with patch.dict('os.environ', {'APP_SECRET': secrets.token_hex(32)}):
            app = create_app({'TESTING': True, 'DATABASE': str(Path(self.tmp.name) / 'environment.db')})
            self.assertGreaterEqual(len(app.secret_key), 32)

    def setUp(self):
        Path('tests/.tmp').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir='tests/.tmp')
        self.app = create_app({'TESTING': True, 'SECRET_KEY': secrets.token_hex(32), 'DATABASE': str(Path(self.tmp.name)/'test.db')})
        self.client = self.app.test_client()
        with self.app.app_context():
            for name, role in [('Alice','student'),('Bob','faculty'),('Admin','administrator')]:
                self.app.db().execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',
                    (name,name.lower()+'@example.edu',TEST_HASH,role,now()))
            self.app.db().commit()

    def tearDown(self):
        self.tmp.cleanup()

    def csrf(self, client=None):
        client = client or self.client
        client.get('/login')
        with client.session_transaction() as s:
            return s['csrf']

    def login(self, name='alice', client=None):
        client=client or self.client
        return client.post('/login',data={'csrf':self.csrf(client),'email':name+'@example.edu','password':'TestPassphrase!123'})

    def post(self, path, data=None, client=None):
        client=client or self.client
        with client.session_transaction() as s:
            token=s['csrf']
        return client.post(path,data={'csrf':token,**(data or {})})

    def report(self, title='Black backpack', verified=False):
        self.login()
        result=self.post('/report',{'kind':'lost','category':'Bags','title':title,'description':'Black bag with a silver zip.','location':'Library','item_date':'2026-10-01'})
        self.assertEqual(result.status_code,302)
        with self.app.app_context():
            item=self.app.db().execute('SELECT max(id) FROM reports').fetchone()[0]
            if verified:
                self.app.db().execute("UPDATE reports SET moderation='verified' WHERE id=?",(item,));self.app.db().commit()
        return item

    def test_text_validation_bounds(self):
        self.assertEqual(validate_text('  Good  ','Title',3,10),'Good')
        for value in ['', 'a'*101, '\x00abc']:
            with self.assertRaises(ValueError):validate_text(value,'Title',3,100)

    def test_owner_policy(self):
        self.assertTrue(can_manage({'id':1},{'reporter_id':1}))
        self.assertFalse(can_manage({'id':2},{'reporter_id':1}))
        self.assertFalse(can_manage(None,{'reporter_id':1}))

    def test_anonymous_requires_login(self):
        self.assertEqual(self.client.get('/').status_code,302)

    def test_health_and_headers(self):
        r=self.client.get('/healthz')
        self.assertEqual(r.json,{'status':'ok'})
        self.assertIn("script-src 'none'",r.headers['Content-Security-Policy'])
        self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff')

    def test_host_validation(self):
        self.assertEqual(self.client.get('/healthz',headers={'Host':'evil.example'}).status_code,400)

    def test_csrf_required(self):
        self.assertEqual(self.client.post('/login',data={'email':'alice@example.edu'}).status_code,400)

    def test_csrf_rejects_all_mutation_routes(self):
        item = self.report(verified=True)
        other_token = self.csrf(self.app.test_client())
        paths = ['/register', '/login', '/logout', '/report',
                 f'/items/{item}/recover', f'/items/{item}/contact',
                 '/messages/1/reply', f'/admin/items/{item}']
        for path in paths:
            for token in [None, 'invalid', other_token]:
                with self.subTest(path=path, token_kind='missing' if token is None else 'wrong'):
                    self.assertEqual(self.client.post(path, data={} if token is None else {'csrf': token}).status_code, 400)
        for path in ['/logout', f'/items/{item}/recover', f'/items/{item}/contact', '/messages/1/reply', f'/admin/items/{item}']:
            self.assertEqual(self.client.get(path).status_code, 405)
        with self.app.app_context():
            self.assertEqual(self.app.db().execute('SELECT status FROM reports WHERE id=?', (item,)).fetchone()[0], 'open')
            self.assertEqual(self.app.db().execute('SELECT count(*) FROM messages').fetchone()[0], 0)

    def test_login_session_rotation(self):
        old=self.csrf();self.login()
        with self.client.session_transaction() as s:self.assertNotEqual(s['csrf'],old);self.assertEqual(s['uid'],1)

    def test_session_cookie_security(self):
        self.app.config['SESSION_COOKIE_SECURE']=True
        r=self.login()
        cookie=r.headers['Set-Cookie']
        for flag in ['Secure','HttpOnly','SameSite=Lax']:self.assertIn(flag,cookie)
        self.assertIn('Strict-Transport-Security',r.headers)

    def test_password_not_plaintext(self):
        with self.app.app_context():
            h=self.app.db().execute('SELECT password_hash FROM users WHERE id=1').fetchone()[0]
            self.assertTrue(h.startswith('scrypt:'));self.assertNotIn('TestPassphrase',h)

    def test_login_throttling(self):
        for _ in range(5):
            self.client.post('/login',data={'csrf':self.csrf(),'email':'alice@example.edu','password':'wrong'})
        r=self.client.post('/login',data={'csrf':self.csrf(),'email':'alice@example.edu','password':'wrong'})
        self.assertEqual(r.status_code,429)

    def test_registration_admin_escalation_denied(self):
        r=self.client.post('/register',data={'csrf':self.csrf(),'name':'Mallory','email':'mallory@example.edu','password':'TestPassphrase!123','role':'administrator'})
        self.assertIn(b'Select student or faculty',r.data)
        with self.app.app_context():self.assertEqual(self.app.db().execute('SELECT count(*) FROM users').fetchone()[0],3)

    def test_attacker_cannot_lock_out_other_source(self):
        for _ in range(5):
            self.client.post('/login',data={'csrf':self.csrf(),'email':'alice@example.edu','password':'wrong'},environ_overrides={'REMOTE_ADDR':'192.0.2.10'})
        r=self.client.post('/login',data={'csrf':self.csrf(),'email':'alice@example.edu','password':'TestPassphrase!123'},environ_overrides={'REMOTE_ADDR':'192.0.2.11'})
        self.assertEqual(r.status_code,302)

    def test_closed_inbox_hides_reply(self):
        item=self.report(verified=True);self.login('bob');self.post(f'/items/{item}/contact',{'body':'I found the item at the library.'})
        self.login();self.post(f'/items/{item}/recover')
        self.assertNotIn(b'Reply privately',self.client.get('/inbox').data)

    def test_admin_pagination(self):
        item=self.report();self.login('admin')
        with self.app.app_context():
            for i in range(101):
                self.app.db().execute("INSERT INTO reports(reporter_id,kind,title,description,category,location,item_date,created_at) VALUES(1,'lost',?,'Long enough description','Other','Library','2026-10-01',?)",(f'Extra item {i}',now()))
            self.app.db().commit()
        self.assertIn(b'Next page',self.client.get('/admin').data)
        self.assertIn(b'Black backpack',self.client.get('/admin?page=2').data)

    def test_registration_valid(self):
        r=self.client.post('/register',data={'csrf':self.csrf(),'name':'Carol','email':'carol@example.edu','password':'TestPassphrase!123','role':'student'})
        self.assertEqual(r.status_code,302)

    def test_pending_visibility(self):
        item=self.report();self.login('bob')
        self.assertEqual(self.client.get(f'/items/{item}').status_code,404)
        self.assertNotIn(b'Black backpack',self.client.get('/').data)

    def test_admin_gate(self):
        self.login();self.assertEqual(self.client.get('/admin').status_code,403)

    def test_moderation_and_removal(self):
        item=self.report();self.login('admin')
        self.assertEqual(self.post(f'/admin/items/{item}',{'action':'verified'}).status_code,302)
        self.login('bob');self.assertEqual(self.client.get(f'/items/{item}').status_code,200)
        self.login('admin');self.assertEqual(self.post(f'/admin/items/{item}',{'action':'removed','reason':'Suspicious personal data'}).status_code,302)
        self.login('bob');self.assertEqual(self.client.get(f'/items/{item}').status_code,404)

    def test_remove_requires_reason(self):
        item=self.report();self.login('admin')
        self.assertEqual(self.post(f'/admin/items/{item}',{'action':'removed'}).status_code,400)

    def test_unauthorized_recovery(self):
        item=self.report(verified=True);self.login('bob')
        self.assertEqual(self.post(f'/items/{item}/recover').status_code,403)
        with self.app.app_context():self.assertEqual(self.app.db().execute('SELECT status FROM reports WHERE id=?',(item,)).fetchone()[0],'open')

    def test_pending_cannot_recover(self):
        item=self.report();self.assertEqual(self.post(f'/items/{item}/recover').status_code,409)

    def test_recovery_idempotency(self):
        item=self.report(verified=True)
        self.assertEqual(self.post(f'/items/{item}/recover').status_code,302)
        self.assertEqual(self.post(f'/items/{item}/recover').status_code,409)

    def test_xss_escaped(self):
        item=self.report('<script>alert(1)</script>',True)
        r=self.client.get(f'/items/{item}')
        self.assertNotIn(b'<script>alert(1)</script>',r.data)
        self.assertIn(b'&lt;script&gt;',r.data)

    def test_sql_injection_search(self):
        self.report(verified=True)
        r=self.client.get('/',query_string={'q':"' OR 1=1 --"})
        self.assertEqual(r.status_code,200)
        self.assertNotIn(b'Black backpack',r.data)

    def test_search_wildcards_are_literal(self):
        self.report(verified=True)
        self.assertNotIn(b'Black backpack',self.client.get('/',query_string={'q':'%'}).data)

    def test_private_messages_and_reply(self):
        item=self.report(verified=True);self.login('bob')
        self.assertEqual(self.post(f'/items/{item}/contact',{'body':'I found your bag at the library desk.'}).status_code,302)
        self.login('alice');r=self.client.get('/inbox')
        self.assertIn(b'I found your bag',r.data);self.assertNotIn(b'bob@example.edu',r.data)
        self.assertEqual(self.post('/messages/1/reply',{'body':'Thank you, I will visit the desk.'}).status_code,302)
        self.login('bob');self.assertIn(b'Thank you',self.client.get('/inbox').data)
        self.login('admin');self.assertNotIn(b'I found your bag',self.client.get('/inbox').data)
        self.assertEqual(self.post('/messages/1/reply',{'body':'Unauthorized reply'}).status_code,404)

    def test_contact_closed_or_self_denied(self):
        item=self.report(verified=True)
        self.assertEqual(self.post(f'/items/{item}/contact',{'body':'Contact myself'}).status_code,409)
        self.post(f'/items/{item}/recover');self.login('bob')
        self.assertEqual(self.post(f'/items/{item}/contact',{'body':'Message to closed item'}).status_code,409)

    def test_message_throttle(self):
        item=self.report(verified=True);self.login('bob')
        for _ in range(10):self.assertEqual(self.post(f'/items/{item}/contact',{'body':'Safe message content'}).status_code,302)
        self.assertEqual(self.post(f'/items/{item}/contact',{'body':'One extra message'}).status_code,429)

    def test_email_not_public(self):
        item=self.report(verified=True)
        self.assertNotIn(b'alice@example.edu',self.client.get(f'/items/{item}').data)

    def test_future_date_rejected(self):
        self.login()
        r=self.post('/report',{'kind':'found','category':'Keys','title':'Found keys','description':'A silver keyring with two keys','location':'Library','item_date':'2099-01-01'})
        self.assertIn(b'cannot be in the future',r.data)

    def test_body_limit(self):
        self.login();self.assertEqual(self.post('/report',{'title':'a'*20000}).status_code,413)

    def test_audit_contains_no_secrets(self):
        item=self.report(verified=True);self.post(f'/items/{item}/recover')
        with self.app.app_context():
            rows=self.app.db().execute('SELECT event,outcome FROM audit_events').fetchall()
            self.assertIn(('item_recovered','success'),[tuple(r) for r in rows])
            self.assertNotIn('TestPassphrase',str([tuple(r) for r in rows]))

    def test_end_to_end_report_verify_contact_recover(self):
        item=self.report();self.login('admin');self.post(f'/admin/items/{item}',{'action':'verified'})
        self.login('bob');self.post(f'/items/{item}/contact',{'body':'I can identify your bag. Please meet at security.'})
        self.login();self.assertIn(b'identify your bag',self.client.get('/inbox').data)
        self.post(f'/items/{item}/recover');self.assertIn(b'Recovered',self.client.get(f'/items/{item}').data)

    def test_fuzz_report_boundary(self):
        self.login();cases=['','x','a'*101,'\x00bad',"' OR 1=1 --",'<img src=x onerror=alert(1)>','Ω'*50,'line\nnew','%_\\']
        for title in cases:
            r=self.post('/report',{'kind':'lost','category':'Other','title':title,'description':'Fuzz boundary description','location':'Library','item_date':'2026-10-01'})
            self.assertIn(r.status_code,(200,302));self.assertNotEqual(r.status_code,500)


if __name__=='__main__':unittest.main(verbosity=2)
