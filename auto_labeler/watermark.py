import collections

Watermark = collections.namedtuple('Watermark', ['message_id', 'internal_date'])

def watermark_for_message(latest_message):
    return Watermark(latest_message['id'], latest_message['internalDate'])

def set_watermark(conn, watermark):
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO watermarks
            (id, message_id, internal_date)
        VALUES (1, ?, ?)
        ON CONFLICT (id)
        DO UPDATE SET
            message_id = excluded.message_id,
            internal_date = excluded.internal_date
    ''', watermark)
    conn.commit()

def get_watermark(conn):
    cur = conn.cursor()
    row = cur.execute('SELECT message_id, internal_date FROM watermarks').fetchone()
    watermark = Watermark(*row)

    return watermark