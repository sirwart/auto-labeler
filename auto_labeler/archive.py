import googleapiclient

from tabulate import tabulate

from .database import get_conn

def print_auto_archive_settings():
    with get_conn() as conn:
        cur = conn.cursor()
        rows = cur.execute('SELECT label_name, delay FROM auto_archive_settings ORDER BY label_name').fetchall()
        print(tabulate(rows, headers=['label', 'delay'], tablefmt='simple'))

def update_auto_archive(label, delay):
    with get_conn() as conn:
        cur = conn.cursor()
        query = 'UPDATE auto_archive_settings SET delay = ?'
        args = [delay]
        if label != 'all':
            query += ' WHERE label_name = ?'
            args.append(label)

        cur.execute(query, args)
        conn.commit()

def n_placeholders(count):
    return ', '.join(['?'] * count)

def set_active_labels(conn, label_names):
    cur = conn.cursor()

    cur.execute('BEGIN')
    try:
        existing_labels_rows = cur.execute('SELECT label_name FROM auto_archive_settings').fetchall()
        existing_labels = [row[0] for row in existing_labels_rows]
        to_add = []
        to_delete = []
        for existing in existing_labels:
            if existing not in label_names:
                to_delete.append(existing)
        
        for label in label_names:
            if label not in existing_labels:
                to_add.append(label)

        if len(to_delete) > 0:
            placeholders = n_placeholders(len(to_delete))
            cur.execute(f'DELETE FROM auto_archive_settings WHERE label_name in ({placeholders})', to_delete)

        if len(to_add) > 0:
            # Need to nest each value in to_add in order to match the expected input of executemany
            to_insert = [[label] for label in to_add]
            cur.executemany('INSERT INTO auto_archive_settings (label_name, delay) VALUES (?, -1)', to_insert)

        cur.execute('COMMIT')
    except conn.Error as e:
        cur.execute('ROLLBACK')
        raise e

def get_auto_archive_settings(conn):
    settings = {}

    cur = conn.cursor()
    setting_rows = cur.execute('SELECT label_name, delay FROM auto_archive_settings').fetchall()
    for (label, delay) in setting_rows:
        settings[label] = delay

    return settings

def archive_or_queue(service, conn, auto_archive_settings, message_id, labels):
    delay = -1
    for label in labels:
        label_delay = auto_archive_settings[label]
        if label_delay != -1 and (delay == -1 or label_delay < delay):
            delay = label_delay
    
    if delay == 0:
        archive_email(service, message_id)
    elif delay > 0:
        queue_archive(conn, message_id, delay)

def queue_archive(conn, message_id, delay):
    cur = conn.cursor()
    delay_expr = f"DATETIME('now', '+{delay} hours')"
    cur.execute(f'INSERT INTO pending_archives (message_id, archive_at) VALUES (?, {delay_expr})', [message_id])
    conn.commit()

def archive_emails(service, conn):
    cur = conn.cursor()
    to_archive = cur.execute('SELECT message_id FROM pending_archives WHERE archive_at <= CURRENT_TIMESTAMP').fetchall()
    for (message_id,) in to_archive:
        archive_email(service, message_id)
        cur.execute('DELETE FROM pending_archives WHERE message_id = ?', [message_id])
        conn.commit()

def archive_email(service, message_id):
    try:
        service.users().messages().modify(userId='me', id=message_id, body={"removeLabelIds": ['INBOX']}).execute()
        print(f'removed message {message_id} from inbox')
    except googleapiclient.errors.HttpError as e:
        if e.status_code == 404:
            print(f'tried to remove {message_id} from inbox but no longer found')
        else:
            raise e
