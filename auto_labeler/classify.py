import os

import personal_trainer

from .archive import archive_emails, archive_or_queue, get_auto_archive_settings
from .data_dir import get_data_dir
from .database import get_conn
from .messages import get_message_contents
from .gmail import get_labels, get_service
from .watermark import get_watermark, watermark_for_message, set_watermark

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

        new_watermark = None

        messages_resp = service.users().messages().list(userId='me', q='in:inbox').execute()
        if len(messages_resp['messages']) == 0:
            return

        for message_info in messages_resp['messages']:
            message_id = message_info['id']
            if message_id == watermark.message_id:
                break
            
            message = service.users().messages().get(userId='me', id=message_id).execute()
            if int(message['internalDate']) <= watermark.internal_date:
                break
            
            if new_watermark is None:
                new_watermark = watermark_for_message(message)
            
            contents = get_message_contents(message)
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
            print(f'adding labels ({labels_str}) to message {message_id} ({subject})')
            service.users().messages().modify(userId='me', id=message_id, body={'addLabelIds': label_ids}).execute()

            if auto_archive_settings is None:
                auto_archive_settings = get_auto_archive_settings(conn)
            archive_or_queue(service, conn, auto_archive_settings, message_id, labels)

        if new_watermark:
            set_watermark(conn, new_watermark)
    finally:
        cur.close()
