"""Campus Lost and Found: bounded inputs, private messaging and owner-only writes."""
import os
import hashlib
import hmac
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

UTC = timezone.utc


def now():
    return datetime.now(UTC).isoformat()


def validate_text(value, label, minimum=1, maximum=500):
    value = (value or '').strip()
    if not minimum <= len(value) <= maximum or any(ord(c) < 32 and c not in '\n\t' for c in value):
        raise ValueError(f'{label} must contain {minimum} to {maximum} printable characters.')
    return value


def can_manage(user, report):
    return bool(user and user['id'] == report['reporter_id'])


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.getenv('APP_SECRET'), DATABASE=os.getenv('DATABASE', 'data/campus.db'),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                      SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE', 'false').lower() == 'true',
                      PERMANENT_SESSION_LIFETIME=timedelta(minutes=30), MAX_CONTENT_LENGTH=16384,
                      TRUSTED_HOSTS=os.getenv('TRUSTED_HOSTS', 'localhost,127.0.0.1').split(','))
    if config:
        app.config.update(config)
    signing_secret = app.config.get('SECRET_KEY')
    if signing_secret is None or len(signing_secret) < 32:
        raise RuntimeError('APP_SECRET must be a random secret of at least 32 characters.')
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)

    def db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'], timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys=ON')
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        conn = g.pop('db', None)
        if conn:
            conn.close()

    with app.app_context():
        db().executescript(Path(__file__).with_name('schema.sql').read_text())
        if 'source' not in [r[1] for r in db().execute('PRAGMA table_info(login_attempts)')]:
            db().execute("ALTER TABLE login_attempts ADD COLUMN source TEXT NOT NULL DEFAULT ''")
            db().commit()

    def audit(event, object_id=None, outcome='success'):
        db().execute('INSERT INTO audit_events(actor_id,event,object_id,outcome,created_at) VALUES(?,?,?,?,?)',
                     (g.user['id'] if g.get('user') else None, event, object_id, outcome, now()))
        db().commit()

    def auth(admin=False):
        def deco(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                if not g.user:
                    return redirect(url_for('login'))
                if admin and g.user['role'] != 'administrator':
                    audit('authorization_denied', outcome='denied')
                    abort(403)
                return fn(*args, **kwargs)
            return wrapped
        return deco

    @app.before_request
    def security_gate():
        g.user = db().execute('SELECT id,name,role FROM users WHERE id=?', (session.get('uid'),)).fetchone()
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        if request.method == 'POST' and not secrets.compare_digest(session['csrf'], request.form.get('csrf', '')):
            audit('csrf_rejected', outcome='denied')
            abort(400, 'The form expired. Reload the page and try again.')

    @app.after_request
    def headers(response):
        response.headers.update({'Content-Security-Policy': "default-src 'self'; style-src 'self'; script-src 'none'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
                                 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
                                 'X-Frame-Options': 'DENY', 'Cache-Control': 'no-store',
                                 'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'})
        if app.config['SESSION_COOKIE_SECURE']:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    @app.context_processor
    def context():
        return {'user': g.get('user'), 'csrf': session.get('csrf')}

    @app.route('/healthz')
    def health():
        db().execute('SELECT 1').fetchone()
        return {'status': 'ok'}

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            try:
                name = validate_text(request.form.get('name'), 'Name', 2, 80)
                email = validate_text(request.form.get('email'), 'Email', 5, 120).lower()
                if not re.fullmatch(r'[a-z0-9.!#$%&*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}', email):
                    raise ValueError('Enter a valid email address.')
                password = validate_text(request.form.get('password'), 'Password', 12, 128)
                role = request.form.get('role')
                if role not in ('student', 'faculty'):
                    raise ValueError('Select student or faculty.')
                db().execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',
                             (name, email, generate_password_hash(password, method='scrypt'), role, now()))
                db().commit()
                audit('registration')
                flash('Account created. Sign in to continue.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Unable to create this account. Try signing in or use a different address.', 'error')
            except ValueError as e:
                flash(str(e), 'error')
        return render_template('account.html', mode='register')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()[:120]
            cutoff = (datetime.now(UTC) - timedelta(minutes=15)).isoformat()
            source = hmac.new(app.config['SECRET_KEY'].encode(), (request.remote_addr or 'unknown').encode(), hashlib.sha256).hexdigest()
            with db():
                db().execute('BEGIN IMMEDIATE')
                db().execute('DELETE FROM login_attempts WHERE created_at<?', (cutoff,))
                attempts = db().execute('SELECT count(*) FROM login_attempts WHERE email=? AND source=? AND created_at>?', (email, source, cutoff)).fetchone()[0]
                if attempts < 5:
                    db().execute('INSERT INTO login_attempts(email,source,created_at) VALUES(?,?,?)', (email, source, now()))
            if attempts >= 5:
                audit('login_throttled', outcome='denied')
                abort(429, 'Too many attempts. Try again after 15 minutes.')
            u = db().execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
            password = request.form.get('password', '')
            candidate_hash = u['password_hash'] if u else app.config['DUMMY_HASH']
            valid = len(password) <= 128 and check_password_hash(candidate_hash, password)
            if u and valid:
                session.clear()
                session['uid'], session['csrf'] = u['id'], secrets.token_urlsafe(32)
                session.permanent = True
                g.user = u
                db().execute('DELETE FROM login_attempts WHERE email=? AND source=?', (email, source))
                audit('login_success')
                return redirect(url_for('items'))
            audit('login_failed', outcome='denied')
            flash('Email or password is incorrect.', 'error')
        return render_template('account.html', mode='login')

    app.config['DUMMY_HASH'] = generate_password_hash(secrets.token_urlsafe(32), method='scrypt')

    @app.route('/logout', methods=['POST'])
    @auth()
    def logout():
        audit('logout')
        session.clear()
        return redirect(url_for('login'))

    @app.route('/')
    @auth()
    def items():
        q = request.args.get('q', '')[:100].strip()
        kind = request.args.get('kind', '')
        category = request.args.get('category', '')
        mode = request.args.get('view', 'all')
        mode = 'mine' if mode == 'mine' else 'all'
        kind = kind if kind in ('lost','found') else ''
        category = category if category in ('Electronics','Documents','Keys','Bags','Other') else ''
        escaped = '%' + q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        rows = db().execute("""SELECT reports.*, users.name AS reporter FROM reports
            JOIN users ON users.id=reporter_id
            WHERE ((?='mine' AND reporter_id=?) OR (?='all' AND moderation='verified'))
            AND (?='' OR title LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\' OR location LIKE ? ESCAPE '\\')
            AND (?='' OR kind=?) AND (?='' OR category=?)
            ORDER BY reports.id DESC LIMIT 100""",
            (mode,g.user['id'],mode,q,escaped,escaped,escaped,kind,kind,category,category)).fetchall()
        stats = db().execute("SELECT sum(kind='lost'),sum(kind='found'),sum(status='recovered') FROM reports WHERE moderation='verified'").fetchone()
        return render_template('items.html', rows=rows, stats=stats, q=q, kind=kind, category=category, mode=mode)

    @app.route('/report', methods=['GET', 'POST'])
    @auth()
    def report():
        if request.method == 'POST':
            try:
                kind, category = request.form.get('kind'), request.form.get('category')
                if kind not in ('lost', 'found') or category not in ('Electronics', 'Documents', 'Keys', 'Bags', 'Other'):
                    raise ValueError('Choose a valid report type and category.')
                title = validate_text(request.form.get('title'), 'Title', 3, 100)
                desc = validate_text(request.form.get('description'), 'Description', 10, 1000)
                location = validate_text(request.form.get('location'), 'Location', 2, 100)
                date = datetime.strptime(request.form.get('item_date', ''), '%Y-%m-%d').date()
                if date > datetime.now(UTC).date():
                    raise ValueError('The item date cannot be in the future.')
                cursor = db().execute('INSERT INTO reports(reporter_id,kind,title,description,category,location,item_date,created_at) VALUES(?,?,?,?,?,?,?,?)',
                                      (g.user['id'], kind, title, desc, category, location, date.isoformat(), now()))
                audit('report_created', cursor.lastrowid)
                flash('Report submitted for administrator verification.', 'success')
                return redirect(url_for('detail', item_id=cursor.lastrowid))
            except ValueError as e:
                flash(str(e) if str(e).startswith(('Choose', 'Title', 'Description', 'Location', 'The item')) else 'Enter a valid item date.', 'error')
        return render_template('report.html')

    def get_report(item_id):
        r = db().execute('SELECT reports.*,users.name AS reporter FROM reports JOIN users ON users.id=reporter_id WHERE reports.id=?', (item_id,)).fetchone()
        if not r or (r['moderation'] != 'verified' and not can_manage(g.user, r) and g.user['role'] != 'administrator'):
            abort(404)
        return r

    @app.route('/items/<int:item_id>')
    @auth()
    def detail(item_id):
        return render_template('detail.html', item=get_report(item_id))

    @app.route('/items/<int:item_id>/recover', methods=['POST'])
    @auth()
    def recover(item_id):
        r = get_report(item_id)
        if not can_manage(g.user, r):
            audit('recovery_denied', item_id, 'denied'); abort(403)
        if r['moderation'] != 'verified' or r['status'] != 'open':
            abort(409, 'Only an open, verified report can be marked recovered.')
        db().execute("UPDATE reports SET status='recovered',recovered_at=? WHERE id=? AND reporter_id=? AND status='open'", (now(), item_id, g.user['id']))
        audit('item_recovered', item_id)
        flash('Item marked recovered.', 'success')
        return redirect(url_for('detail', item_id=item_id))

    @app.route('/items/<int:item_id>/contact', methods=['POST'])
    @auth()
    def contact(item_id):
        r = get_report(item_id)
        if r['moderation'] != 'verified' or r['status'] != 'open' or r['reporter_id'] == g.user['id']:
            abort(409, 'Contact is available for open verified reports from another user.')
        try:
            text = validate_text(request.form.get('body'), 'Message', 5, 1000)
        except ValueError as e:
            abort(400, str(e))
        cutoff = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
        with db():
            db().execute('BEGIN IMMEDIATE')
            count = db().execute('SELECT count(*) FROM messages WHERE sender_id=? AND created_at>?', (g.user['id'], cutoff)).fetchone()[0]
            if count >= 10:
                abort(429, 'Message limit reached. Please wait a minute.')
            db().execute('INSERT INTO messages(report_id,sender_id,recipient_id,body,created_at) VALUES(?,?,?,?,?)', (item_id, g.user['id'], r['reporter_id'], text, now()))
        audit('message_sent', item_id)
        flash('Private message sent. Your email address was not shared.', 'success')
        return redirect(url_for('inbox'))

    @app.route('/inbox')
    @auth()
    def inbox():
        rows = db().execute('SELECT messages.*,s.name AS sender,r.name AS recipient,reports.title,reports.status,reports.moderation FROM messages JOIN users s ON s.id=sender_id JOIN users r ON r.id=recipient_id JOIN reports ON reports.id=report_id WHERE sender_id=? OR recipient_id=? ORDER BY messages.id DESC LIMIT 100', (g.user['id'], g.user['id'])).fetchall()
        return render_template('inbox.html', messages=rows)

    @app.route('/messages/<int:message_id>/reply', methods=['POST'])
    @auth()
    def reply(message_id):
        msg = db().execute('SELECT * FROM messages WHERE id=? AND recipient_id=?', (message_id, g.user['id'])).fetchone()
        if not msg:
            abort(404)
        r = get_report(msg['report_id'])
        if r['moderation'] != 'verified' or r['status'] != 'open':
            abort(409, 'This report is closed to messages.')
        try:
            text = validate_text(request.form.get('body'), 'Message', 5, 1000)
        except ValueError as e:
            abort(400, str(e))
        cutoff = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
        with db():
            db().execute('BEGIN IMMEDIATE')
            if db().execute('SELECT count(*) FROM messages WHERE sender_id=? AND created_at>?', (g.user['id'], cutoff)).fetchone()[0] >= 10:
                abort(429)
            db().execute('INSERT INTO messages(report_id,sender_id,recipient_id,body,created_at) VALUES(?,?,?,?,?)', (msg['report_id'], g.user['id'], msg['sender_id'], text, now()))
        audit('message_reply', msg['report_id'])
        return redirect(url_for('inbox'))

    @app.route('/admin')
    @auth(admin=True)
    def admin():
        page = max(1, min(request.args.get('page', 1, type=int), 100000))
        rows = db().execute("SELECT reports.*,users.name AS reporter FROM reports JOIN users ON users.id=reporter_id ORDER BY (moderation='pending') DESC,reports.id DESC LIMIT 100 OFFSET ?", ((page-1)*100,)).fetchall()
        total = db().execute('SELECT count(*) FROM reports').fetchone()[0]
        events = db().execute('SELECT audit_events.*,users.name AS actor FROM audit_events LEFT JOIN users ON users.id=actor_id ORDER BY audit_events.id DESC LIMIT 30').fetchall()
        return render_template('admin.html', rows=rows, events=events, page=page, has_next=total>page*100)

    @app.route('/admin/items/<int:item_id>', methods=['POST'])
    @auth(admin=True)
    def moderate(item_id):
        action = request.form.get('action')
        if action not in ('verified', 'removed'):
            abort(400)
        if not db().execute('SELECT id FROM reports WHERE id=?', (item_id,)).fetchone():
            abort(404)
        reason = request.form.get('reason', '').strip()
        if action == 'removed':
            try:
                reason = validate_text(reason, 'Removal reason', 5, 300)
            except ValueError as e:
                abort(400, str(e))
        db().execute('UPDATE reports SET moderation=?,moderation_reason=?,moderator_id=? WHERE id=?', (action, reason[:300], g.user['id'], item_id))
        audit('report_' + action, item_id)
        flash('Moderation decision saved.', 'success')
        return redirect(url_for('admin'))

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(413)
    @app.errorhandler(429)
    def expected_error(error):
        if request.url_rule is None:
            return 'Request could not be completed.', error.code, {'Content-Type': 'text/plain; charset=utf-8'}
        return render_template('error.html', code=error.code, message=error.description), error.code

    @app.errorhandler(500)
    def server_error(error):
        return render_template('error.html', code=500, message='Something went wrong. Please try again later.'), 500

    app.db = db
    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.getenv('PORT','8090')), debug=False)
