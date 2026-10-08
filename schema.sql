PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('student','faculty','administrator')),
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reports (
 id INTEGER PRIMARY KEY, reporter_id INTEGER NOT NULL REFERENCES users(id),
 kind TEXT NOT NULL CHECK(kind IN ('lost','found')), title TEXT NOT NULL,
 description TEXT NOT NULL, category TEXT NOT NULL, location TEXT NOT NULL, item_date TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','recovered')),
 moderation TEXT NOT NULL DEFAULT 'pending' CHECK(moderation IN ('pending','verified','removed')),
 moderation_reason TEXT NOT NULL DEFAULT '', moderator_id INTEGER REFERENCES users(id),
 created_at TEXT NOT NULL, recovered_at TEXT
);
CREATE TABLE IF NOT EXISTS messages (
 id INTEGER PRIMARY KEY, report_id INTEGER NOT NULL REFERENCES reports(id),
 sender_id INTEGER NOT NULL REFERENCES users(id), recipient_id INTEGER NOT NULL REFERENCES users(id),
 body TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
 id INTEGER PRIMARY KEY, actor_id INTEGER REFERENCES users(id), event TEXT NOT NULL,
 object_id INTEGER, outcome TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS login_attempts (id INTEGER PRIMARY KEY, email TEXT NOT NULL, source TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS reports_visibility ON reports(moderation,status);
CREATE INDEX IF NOT EXISTS reports_owner ON reports(reporter_id);
CREATE INDEX IF NOT EXISTS messages_recipient ON messages(recipient_id);
CREATE INDEX IF NOT EXISTS attempts_window ON login_attempts(email,created_at);
