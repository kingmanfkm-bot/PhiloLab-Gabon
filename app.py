import os
import requests
from flask import Flask, request
from google import genai

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "philo-gabon-2026")

# Client Gemini avec nouvelle clé AQ.
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/')
def home():
    return 'PhiloLab-Gabon est en ligne - AQ Ready - v3.5', 200

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    data = request.get_json()
    try:
        value = data['entry'][0]['changes'][0]['value']
        if 'messages' not in value:
            return 'OK', 200
            
        msg = value['messages'][0]
        from_number = msg['from']
        text = msg['text']['body'] if msg.get('type') == 'text' else ''

        phone_id = os.environ.get("PHONE_NUMBER_ID")
        wa_token = os.environ.get("WHATSAPP_TOKEN")

        # Modèle qui marche pour les nouvelles clés gratuites AQ.
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=f"Tu es un prof de philo de Terminale au Gabon. Tu réponds court, clair, pour WhatsApp, avec exemples du Gabon si possible. Question de l'élève: {text}"
        )
        reply = response.text

        # Envoi WhatsApp
        url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        headers = {"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"}
        payload = {
            "messaging_product": "whatsapp",
            "to": from_number,
            "text": {"body": reply}
        }
        requests.post(url, headers=headers, json=payload)

    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        
    return 'OK', 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
