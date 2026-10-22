import os, requests, threading
from flask import Flask, request
from google import genai

app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "philo-gabon-2026")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
app.last_msg_id = None

@app.route('/')
def home():
    return 'PhiloLab-Gabon FAST - v4', 200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return 'Forbidden', 403

def repondre_vite(from_number, text, phone_id, wa_token):
    try:
        resp = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=f"Tu es prof de philo Terminale Gabon. Réponds en 5 lignes max, clair, exemple gabonais. Question: {text}"
        )
        url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        headers = {"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp", "to": from_number, "text": {"body": resp.text[:1000]}}
        requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print(f"ERREUR Gemini: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        entry = data['entry'][0]['changes'][0]['value']
        if 'messages' not in entry: return 'OK', 200
        
        msg_id = entry['messages'][0].get('id')
        if msg_id == app.last_msg_id: return 'OK', 200
        app.last_msg_id = msg_id

        msg = entry['messages'][0]
        from_number = msg['from']
        text = msg['text']['body'] if msg.get('type') == 'text' else ''
        
        # On lance la réponse en arrière-plan et on répond OK tout de suite à WhatsApp
        threading.Thread(target=repondre_vite, args=(from_number, text, os.environ.get("PHONE_NUMBER_ID"), os.environ.get("WHATSAPP_TOKEN"))).start()

    except Exception as e:
        print(e)
    return 'OK', 200  # <- Réponse instantanée, plus de doublon

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
