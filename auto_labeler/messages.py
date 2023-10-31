import base64

from bs4 import BeautifulSoup

def get_textual_parts(part):
    mime_type = part['mimeType']
    if mime_type == 'text/plain' or mime_type == 'text/html':
        if 'data' not in part['body']:
            return []
        else:
            return [part]
    elif mime_type.startswith('multipart'):
        subparts = []
        for subpart in part['parts']:
            res = get_textual_parts(subpart)
            if len(res) > 0:
                subparts.extend(res)
        return subparts
    else:
        return []


def get_message_contents(message):
    plain_text_contents = ''
    html_contents = ''

    subject = ''
    sender = ''

    for header in message['payload']['headers']:
        if header['name'] == 'Subject':
            subject = header['value']
        elif header['name'] == 'From':
            sender = header['value']

    textual_parts = get_textual_parts(message['payload'])
    for part in textual_parts:
        if 'data' not in part['body']:
            continue

        contents = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        if part['mimeType'] == 'text/plain':
            plain_text_contents = contents
        elif part['mimeType'] == 'text/html':
            html_contents = contents

    if plain_text_contents:
        return subject + '\n' + sender + '\n' + plain_text_contents
    elif html_contents:
        soup = BeautifulSoup(html_contents, 'html.parser')
        html_text_contents = soup.get_text(separator='\n', strip=True)
        return subject + '\n' + sender + '\n' + html_text_contents
    else:
        return ''
