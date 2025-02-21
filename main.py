from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
from requests_toolbelt.multipart.encoder import MultipartEncoder

load_dotenv()

app = Flask(__name__)

# Define responses for specific commands
RESPONSES = {
    'default': 'Bem vindo ao atendimento da Inovar! \n\nPara seguirmos com seu atendimento, escolha uma das opções abaixo: \n\n1 - Opção 1 \n2 - Opção 2 \n3 - Opção 3',
    '1': 'Você escolheu a opção 1.',
    '2': 'Você escolheu a opção 2.',
    '3': 'Você escolheu a opção 3.',
}

IMAGE_PATH = './files/helicopter.jfif'
IMAGE_CAPTION = 'Caption.'


def send_whapi_request(endpoint, payload):
    """Send a request to the WhatsApp API."""

    headers = {
        'Authorization': f"Bearer {os.getenv('TOKEN')}"
    }

    url = f"{os.getenv('API_URL')}/{endpoint}"

    # Check if we're sending an image
    if 'media' in payload:
        image_path, mime_type = payload.pop('media').split(';')

        with open(image_path, 'rb') as image_file:
            m = MultipartEncoder(
                fields={
                    **payload,
                    'media': (image_path, image_file, mime_type)
                }
            )

            headers['Content-Type'] = m.content_type
            response = requests.post(url, data=m, headers=headers)
    else:
        headers['Content-Type'] = 'application/json'
        response = requests.post(url, json=payload, headers=headers)

    # Log the request and response for debugging
    print(f"Request URL: {url}")
    print(f"Request Headers: {headers}")
    print(f"Request Payload: {payload}")
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.content}")

    return response.json()


# The Webhook link to your server is set in the dashboard.
# For this script it is important that the link is in the format: {link to server}/hook.
@app.route('/webhook', methods=['POST'])
def handle_new_messages():
    try:
        messages = request.json.get('messages', [])

        for message in messages:
            # Ignore messages from the bot itself
            if message.get('from_me'):
                continue

            # Ignore messages from groups and broadcast lists
            chat_id = message.get('chat_id')
            if '@g.us' in chat_id or '@broadcast' in chat_id:
                continue

            command_type = message.get('type', {}).strip().lower()
            sender_id = chat_id
            payload = {'to': sender_id}

            if command_type == 'text':
                # Get the command text from the incoming message
                command_text = message.get('text', {}).get(
                    'body', '').strip().lower()

                # Determine the response based on the command
                if command_text in RESPONSES:
                    payload['body'] = RESPONSES[command_text]
                else:
                    payload['body'] = RESPONSES['default']
                endpoint = 'messages/text'

            elif command_type == 'image':
                payload['caption'] = IMAGE_CAPTION
                payload['media'] = IMAGE_PATH + \
                    ';image/' + IMAGE_PATH.split('.')[-1]
                endpoint = 'messages/image'

            # Send the response
            send_whapi_request(endpoint, payload)

        return 'Ok', 200

    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500


@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'


if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT', 5000)), debug=True)
