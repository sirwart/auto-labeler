import os

import personal_trainer

from .archive import set_active_labels
from .data_dir import get_data_dir
from .database import get_conn
from .gmail import get_service, get_training_messages
from .watermark import watermark_for_message, set_watermark

def train_command(labels):
    service = get_service()

    training_messages, latest_message = get_training_messages(service, labels)

    classifier = personal_trainer.MultiLabelTextClassifier()
    classifier.train(training_messages)

    model_dir = os.path.join(get_data_dir(), 'model')
    classifier.save(model_dir)

    with get_conn() as conn:
        set_active_labels(conn, labels)
        set_watermark(conn, watermark_for_message(latest_message))