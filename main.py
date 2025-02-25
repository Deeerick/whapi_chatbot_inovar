import os
import requests

from pytz import timezone
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)

# Define responses for specific commands
RESPONSES = {'default': 'Bem vindo ao atendimento da Inovar! \n\nPara seguirmos com seu atendimento, por favor, informe seu nome:'}

# Lista de condomínios válidos
VALID_CONDOMINIOS = ['Vitalis', 'Spazio Castellon', 'Parque da Mata II',
                     'Atlanta', 'Portal dos Cristais', 'Portal das Safiras',
                     'Inspirazzione', 'Roma Residencial Clube', 'São Gabriel']

# Dicionário para armazenar o estado da conversa com cada usuário
user_states = {}

# Dicionário para armazenar a última interação de cada usuário
last_interaction = {}


def send_whapi_request(endpoint, payload):
    """Enviar uma solicitação para a API do WhatsApp."""

    headers = {
        'Authorization': f"Bearer {os.getenv('TOKEN')}"
    }

    url = f"{os.getenv('API_URL')}/{endpoint}"

    response = requests.post(url, json=payload, headers=headers)

    return response.json()


def handle_condominio(condominio, sender_id):
    """Função para lidar com cada condomínio."""
    # Aqui você pode adicionar a lógica específica para cada condomínio

    if condominio == 'Vitalis':

        OPTS = {
            '1': 'Reforma/Obras',
            '2': 'Mudança',
            '3': 'Entrada/liberação de visitantes',
            '4': 'Entrada/liberação de corretor de imóveis',
            '5': 'Retirada/movimentação de móveis',
            '6': 'Emissão de boleto',
            '7': 'Registro de ocorrências (barulho, vazamento, etc)',
            '8': 'Reserva de área comum',
            '9': 'Empréstimo de vagas',
            '10': 'Documentos úteis',
            '11': 'Outros assuntos'
        }

        return 'Por favor, selecione uma opção:\n\n1 - Reforma/Obras\n2 - Mudança\n3 - Entrada/liberação de visitantes\n4 - Entrada/liberação de corretor de imóveis\n5 - Retirada/movimentação de móveis\n6 - Emissão de boleto\n7 - Registro de ocorrências (barulho, vazamento, etc)\n8 - Reserva de área comum\n9 - Empréstimo de vagas\n10 - Documentos úteis\n11 - Outros assuntos'
    
    

    elif condominio == 'Spazio Castellon':
        pass

    elif condominio == 'Parque da Mata II':
        pass

    elif condominio == 'Atlanta':
        pass

    elif condominio == 'Portal dos Cristais':
        pass

    elif condominio == 'Portal das Safiras':
        pass

    elif condominio == 'Inspirazzione':
        pass

    elif condominio == 'Roma Residencial Clube':
        pass

    elif condominio == 'São Gabriel':
        pass

    return True


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

            # Chame a função correspondente ao condomínio
            return handle_condominio(message_text, sender_id)
        else:
            return 'Condomínio inválido. Por favor, informe um condomínio válido:'

    return 'Desculpe, não entendi sua resposta.'


@app.route('/webhook', methods=['POST'])
def handle_new_messages():
    try:
        # Verificar o horário atual em Brasília
        brasilia_tz = timezone('America/Sao_Paulo')
        now = datetime.now(brasilia_tz)
        if now.hour < 8 or now.hour >= 17:
            return jsonify({'message': 'O atendimento está disponível apenas das 08h às 17h de Brasília.'}), 200

        messages = request.json.get('messages', [])

        for message in messages:
            # Ignore mensagens do próprio bot
            if message.get('from_me'):
                continue

            # Ignore mensagens de grupos e listas de transmissão
            chat_id = message.get('chat_id')
            if '@g.us' in chat_id or '@broadcast' in chat_id:
                continue

            # Verificar a última interação do usuário
            if chat_id in last_interaction:
                last_interaction_time = last_interaction[chat_id]
                if now - last_interaction_time < timedelta(hours=24):
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

                # Atualizar a última interação do usuário
                last_interaction[chat_id] = now

            # Lidar com outros tipos de mensagens
            elif command_type in ['image', 'video', 'gif', 'audio', 'voice', 'document', 'location', 'contact', 'call']:
                response_text = 'Desculpe, o atendimento automático não acessa arquivos enviados. \nPor favor, envie uma mensagem de texto.'
                payload['body'] = response_text
                endpoint = 'messages/text'

                # Atualizar a última interação do usuário
                last_interaction[chat_id] = now

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
