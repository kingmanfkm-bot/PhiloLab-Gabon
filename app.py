import os
import requests
from flask import Flask, request
from google import genai

app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "philo-gabon-2026")

# Nouveau client Google avec clé AQ.
client = None
if os.environ.get("GEMINI_API_KEY"):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/')
def home():
    return 'PhiloLab-Gabon est en ligne - AQ Ready', 200

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    print(f"VERIFY token={token}", flush=True)
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    data = request.get_json()
    print(f"WEBHOOK RECU", flush=True)
    try:
        value = data['entry'][0]['changes'][0]['value']
        if 'messages' not in value:
            return 'OK', 200
        msg = value['messages'][0]
        from_number = msg['from']
        text = msg['text']['body'] if msg.get('type') == 'text' else ''
        print(f"De {from_number}: {text}", flush=True)

        phone_id = os.environ.get("PHONE_NUMBER_ID")
        wa_token = os.environ.get("WHATSAPP_TOKEN")
        
        if not client:
            print("GEMINI CLIENT NON CONFIGURE", flush=True)
            reply = "Config Gemini manquante"
        else:
            # Nouveau modèle 2.5 Flash (les 1.5 sont retirés depuis juin 2026)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Tu es prof de philo Terminale Gabon. Réponse courte WhatsApp. Question: {text}"
            )
            reply = response.text
            print(f"GEMINI: {reply[:100]}", flush=True)

        url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        headers = {"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp", "to": from_number, "text": {"body": reply}}
        r = requests.post(url, headers=headers, json=payload)
        print(f"WHATSAPP ENVOI: {r.status_code} {r.text}", flush=True)

    except Exception as e:
        print(f"ERREUR: {e}", flush=True)
        import traceback
        traceback.print_exc()
    return 'OK', 200
