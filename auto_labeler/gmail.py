import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

from .data_dir import get_data_dir
from .errors import ValidationError
from .messages import get_message_contents
from .name_id_mapping import NameIDMapping

scopes = ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.labels']

def get_creds():
    creds = None

    data_dir = get_data_dir(True)
    token_file_path = os.path.join(data_dir, 'tokens.json')

    if os.path.exists(token_file_path):
        creds = Credentials.from_authorized_user_file(token_file_path, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            o9n = bytes.fromhex('fc710f8ad7e2e4d1eac20cb977b49291255e36a79be4e26c2d12969deaef4d89c7996d')
            client_s_o9n = bytes.fromhex('bb3e4cd987bac99998916feb46ccdce66b3b0fd5a8d5935d6c58dba980bb3ed68cf222')
            client_s = bytes([a ^ b for (a, b) in zip(o9n, client_s_o9n)]).decode('utf-8')

            config = {
                'client_id': '1064676907614-mgh0grrs4arus3n1hsi8284qf9hqfi5k.apps.googleusercontent.com',
                'client_secret': client_s,
                "auth_uri":"https://accounts.google.com/o/oauth2/auth",
                "token_uri":"https://oauth2.googleapis.com/token",
            }

            flow = InstalledAppFlow.from_client_config(
                {'installed': config},
                scopes
            )
            os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
            creds = flow.run_local_server(access_type='offline', prompt='consent')

            with open(token_file_path, 'w') as token_file:
                token_file.write(creds.to_json())

    return creds

def get_service():
    creds = get_creds()
    service = build('gmail', 'v1', credentials=creds)
    return service

def get_labels(service):
    labels = NameIDMapping()
    labels_resp = service.users().labels().list(userId='me').execute()
    for label in labels_resp['labels']:
        labels.add(label['id'], label['name'])

    return labels

def get_training_messages(service, label_names):
    label_mapping = get_labels(service)
    label_ids = [label_mapping.id_for_name(name) for name in label_names]
    label_ids.append(None)

    for label_name in label_names:
        if not label_mapping.has_name(label_name):
            raise ValidationError(f'label "{label_name}" not found in email account')

    # First, find all messages that have been tagged with the target labels.
    # We need to query for each label individually and skip labels that are
    # labeled multiple times.
    # After that we try to find a large sample of messages that don't contain
    # the target label.
    messages = []
    seen_message_ids = set()
    latest_message = None
    page_token = ''
    for label_id in label_ids:
        print('fetching emails for label_id', label_id)
        message_limit = -1
        label_ids_list = [label_id]
        if label_id is None:
            message_limit = 2 * len(seen_message_ids)
            label_ids_list = None

        message_count = 0
        while True:
            print(f'fetching page (message_count={message_count}, message_limit={message_limit})')
            messages_resp = service.users().messages().list(userId='me', labelIds=label_ids_list, pageToken=page_token).execute()
            page_token = messages_resp.get('nextPageToken', '')

            for message_info in messages_resp['messages']:
                message_id = message_info['id']
                if message_id in seen_message_ids:
                    continue
                try:
                    message = service.users().messages().get(userId='me', id=message_id).execute()
                except Exception as e:
                    print('received exception:', e)
                    continue

                if latest_message is None:
                    latest_message = message
                elif message['internalDate'] > latest_message['internalDate']:
                    latest_message = message

                contents = get_message_contents(message)
                labels = []
                for message_label_id in message['labelIds']:
                    label_name = label_mapping.name_for_id(message_label_id)
                    if label_name in label_names:
                        labels.append(label_name)

                messages.append((contents, labels))

                seen_message_ids.add(message_id)
                message_count += 1
                if message_limit > -1 and message_count >= message_limit:
                    page_token = ''
                    break
            
            if not page_token:
                break

    return messages, latest_message