import os

import personal_trainer

from .archive import archive_emails, archive_or_queue, get_auto_archive_settings
from .data_dir import get_data_dir
from .database import get_conn
from .messages import get_message_contents
from .gmail import get_labels, get_service
from .watermark import get_watermark, watermark_for_thread, set_watermark

def get_classifier():
    model_dir = os.path.join(get_data_dir(), 'model')
    return personal_trainer.MultiLabelTextClassifier(model_dir)

def label_and_archive_emails():
    service = get_service()
    conn = get_conn()

    try:
        label_emails(service, conn)
        archive_emails(service, conn)
    finally:
        conn.close()

def label_emails(service, conn):
    classifier = None
    label_mapping = None
    auto_archive_settings = None

    cur = conn.cursor()

    try:
        watermark = get_watermark(conn)

        new_watermark_thread = None
        largest_thread_id = watermark.largest_thread_id

        threads_resp = service.users().threads().list(userId='me', q='in:inbox').execute()
        if len(threads_resp['threads']) == 0:
            return

        for thread_info in threads_resp['threads']:
            thread_id = thread_info['id']
            if thread_id == watermark.thread_id and thread_info['historyId'] == watermark.history_id:
                break
            
            thread = service.users().threads().get(userId='me', id=thread_id).execute()
            last_message = thread['messages'][-1]
            if int(last_message['internalDate']) <= watermark.internal_date:
                break
            
            if new_watermark_thread is None:
                new_watermark_thread = thread

            thread_id_int = int(thread_id, 16)

            if thread_id_int > largest_thread_id:
                largest_thread_id = thread_id_int

            if thread_id_int < watermark.largest_thread_id:
                # The largest thread id is to prevent double classifying, since we may
                # need to iterate over threads multiple times if they get replies
                continue
            
            contents = get_message_contents(thread['messages'][0])
            if classifier is None:
                classifier = get_classifier()

            labels = classifier.classify(contents)
            if len(labels) == 0:
                continue
            
            if label_mapping is None:
                label_mapping = get_labels(service)

            label_ids = []
            for label in labels:
                label_ids.append(label_mapping.id_for_name(label))

            subject = contents.split('\n')[0]
            labels_str = ', '.join(labels)
            print(f'adding labels ({labels_str}) to thread {thread_id} ({subject})')
            service.users().threads().modify(userId='me', id=thread_id, body={'addLabelIds': label_ids}).execute()

            if auto_archive_settings is None:
                auto_archive_settings = get_auto_archive_settings(conn)
            archive_or_queue(service, conn, auto_archive_settings, thread_id, labels)

        if new_watermark_thread:
            new_watermark = watermark_for_thread(new_watermark_thread, largest_thread_id)
            set_watermark(conn, new_watermark)
    finally:
        cur.close()
