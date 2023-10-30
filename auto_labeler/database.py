import os
import sqlite3

from .data_dir import get_data_dir

migrations = [
    'CREATE TABLE auto_archive_settings (label_name TEXT NOT NULL, delay INTEGER NOT NULL)',
    'CREATE TABLE pending_archives (message_id TEXT NOT NULL, archive_at TIMESTAMP NOT NULL)',
    'CREATE TABLE watermarks (id INTEGER PRIMARY KEY, message_id TEXT NOT NULL, internal_date INT NOT NULL)',
]

def get_db_path():
    return os.path.join(get_data_dir(), 'auto-labeler.db')

def get_conn():
    db_dir = get_db_path()

    new_db = not os.path.exists(db_dir)

    conn = sqlite3.connect(db_dir)

    cur = conn.cursor()
    if new_db:
        cur.execute('PRAGMA journal_mode=wal')
        cur.execute('CREATE TABLE migrations (version INTEGER PRIMARY KEY, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)')

    max_version = cur.execute('SELECT MAX(version) FROM migrations').fetchone()[0]
    max_version = 0 if max_version is None else max_version

    for i in range(max_version, len(migrations)):
        cur.execute("BEGIN")
        try:
            cur.execute(migrations[i])
            cur.execute('INSERT INTO migrations (version) VALUES (?)', [i+1])
            cur.execute('COMMIT')
        except conn.Error as e:
            cur.execute('ROLLBACK')
            raise e

    return conn