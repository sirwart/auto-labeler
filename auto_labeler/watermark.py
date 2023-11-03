import collections

Watermark = collections.namedtuple('Watermark', ['thread_id', 'history_id', 'internal_date', 'largest_thread_id'])

def watermark_for_thread(thread, largest_thread_id):
    latest_message = thread['messages'][-1]
    return Watermark(thread['id'], thread['historyId'], int(latest_message['internalDate']), largest_thread_id)

def set_watermark(conn, watermark):
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO watermarks
            (id, thread_id, history_id, internal_date, largest_thread_id)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT (id)
        DO UPDATE SET
            thread_id = excluded.thread_id,
            history_id = excluded.history_id,
            internal_date = excluded.internal_date,
            largest_thread_id = excluded.largest_thread_id
    ''', watermark)
    conn.commit()

def get_watermark(conn):
    cur = conn.cursor()
    row = cur.execute('SELECT thread_id, history_id, internal_date, largest_thread_id FROM watermarks').fetchone()
    watermark = Watermark(*row)

    return watermark