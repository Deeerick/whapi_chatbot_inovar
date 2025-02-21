import os
import requests

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from requests_toolbelt.multipart.encoder import MultipartEncoder


load_dotenv()

app = Flask(__name__)

# Define responses for specific commands
RESPONSES = {
    'default': 'Bem vindo ao atendimento da Inovar! \n\nPara seguirmos com seu atendimento, por favor, informe seu nome:'
}

# Lista de condomínios válidos
VALID_CONDOMINIOS = ['Condominio A', 'Condominio B', 'Condominio C']

# Dicionário para armazenar o estado da conversa com cada usuário
user_states = {}

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

    return response.json()


def handle_user_response(sender_id, message_text):
    """Handle the user's response based on the current state."""

    if sender_id not in user_states:
        user_states[sender_id] = {'state': 'ask_name'}
        return RESPONSES['default']

    state = user_states[sender_id]['state']

    if state == 'ask_name':
        user_states[sender_id]['name'] = message_text
        user_states[sender_id]['state'] = 'ask_condominio'
        return 'Por favor, informe o condomínio onde você mora:'

    elif state == 'ask_condominio':
        if message_text in VALID_CONDOMINIOS:
            user_states[sender_id]['condominio'] = message_text
            user_states[sender_id]['state'] = 'triage_complete'

            # Chame o arquivo Python correspondente ao condomínio
            condominio_script = f"{message_text.replace(' ', '_').lower()}.py"
            
            # Aqui você pode importar e chamar a função principal do script do condomínio
            # Por exemplo: import condominio_a; condominio_a.main()
            return f"Condomínio válido. Chamando o script {condominio_script}..."
        else:
            return 'Condomínio inválido. Por favor, informe um condomínio válido:'

    return 'Desculpe, não entendi sua resposta.'


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

                # Handle the user's response based on the current state
                response_text = handle_user_response(sender_id, command_text)
                payload['body'] = response_text
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
