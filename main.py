import os
import requests

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from requests_toolbelt.multipart.encoder import MultipartEncoder


load_dotenv()

app = Flask(__name__)

# Define responses for specific commands
RESPONSES = {'default': 'Bem vindo ao atendimento da Inovar! \n\nPara seguirmos com seu atendimento, por favor, informe seu nome:'}

# Lista de condomínios válidos
VALID_CONDOMINIOS = ['Vitalis', 'Spazio Castellon', 'Parque da Mata II', 
                     'Atlanta', 'Portal dos Cristais', 'Portal das Safiras'
                     'Inspirazzione', 'Roma Residencial Clube', 'São Gabriel'
                     ]

# Dicionário para armazenar o estado da conversa com cada usuário
user_states = {}

IMAGE_PATH = './files/helicopter.jfif'
IMAGE_CAPTION = 'Caption.'


def send_whapi_request(endpoint, payload):
    """Enviar uma solicitação para a API do WhatsApp."""

    headers = {
        'Authorization': f"Bearer {os.getenv('TOKEN')}"
    }

    url = f"{os.getenv('API_URL')}/{endpoint}"

    # Verifique se estamos enviando uma imagem
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
    """Lida com a resposta do usuário com base no estado atual."""

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


# O link do Webhook para o seu servidor é configurado no painel de controle da API.
# Para este script, é importante que o link esteja no formato: {link para o servidor}/webhook.
@app.route('/webhook', methods=['POST'])
def handle_new_messages():
    try:
        messages = request.json.get('messages', [])

        for message in messages:
            # Ignore mensagens do próprio bot
            if message.get('from_me'):
                continue

            # Ignore mensagens de grupos e listas de transmissão
            chat_id = message.get('chat_id')
            if '@g.us' in chat_id or '@broadcast' in chat_id:
                continue

            command_type = message.get('type', {}).strip().lower()
            sender_id = chat_id
            payload = {'to': sender_id}

            if command_type == 'text':
                # Obter o texto do comando da mensagem recebida
                command_text = message.get('text', {}).get(
                    'body', '').strip().lower()

                # Lidar com a resposta do usuário com base no estado atual
                response_text = handle_user_response(sender_id, command_text)
                payload['body'] = response_text
                endpoint = 'messages/text'

            # Lidar com outros tipos de mensagens
            elif command_type in ['image', 'video', 'gif', 'audio', 'voice', 'document', 'location', 'contact', 'call']:
                response_text = 'Desculpe, o atendimento automático não acessa arquivos enviados. \nPor favor, envie uma mensagem de texto.'
                payload['body'] = response_text
                endpoint = 'messages/text'

            # Enviar a resposta
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
