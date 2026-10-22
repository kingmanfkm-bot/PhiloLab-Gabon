import os
import sys
import requests
from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "philo-gabon-2026")

if os.environ.get("GEMINI_API_KEY"):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/')
def home():
    return 'PhiloLab-Gabon est en ligne', 200

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    print(f"VERIFY token={token} challenge={challenge}", flush=True)
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    data = request.get_json()
    print(f"WEBHOOK RECU: {data}", flush=True)
    try:
        value = data['entry'][0]['changes'][0]['value']
        if 'messages' not in value:
            print("Pas un message, status update", flush=True)
            return 'OK', 200
        
        msg = value['messages'][0]
        from_number = msg['from']
        text = msg['text']['body'] if msg.get('type') == 'text' else ''
        print(f"De {from_number}: {text}", flush=True)

        gemini_key = os.environ.get("GEMINI_API_KEY")
        phone_id = os.environ.get("PHONE_NUMBER_ID")
        wa_token = os.environ.get("WHATSAPP_TOKEN")
        
        print(f"CONFIG -> GEMINI:{bool(gemini_key)} PHONE_ID:{phone_id} WA_TOKEN:{bool(wa_token)}", flush=True)

        if not all([gemini_key, phone_id, wa_token]):
            print("ERREUR: Une variable d'environnement manque !", flush=True)
            return 'OK', 200

        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"Tu es un professeur de philosophie pour Terminale au Gabon (programme gabonais). Explique simplement, court, style WhatsApp. Question: {text}"
        resp = model.generate_content(prompt)
        reply = resp.text
        print(f"GEMINI REPONSE: {reply}", flush=True)

        url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        headers = {"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp", "to": from_number, "text": {"body": reply}}
        r = requests.post(url, headers=headers, json=payload)
        print(f"WHATSAPP ENVOI: {r.status_code} - {r.text}", flush=True)

    except Exception as e:
        print(f"ERREUR CRITIQUE: {e}", flush=True)
        import traceback
        traceback.print_exc()
    return 'OK', 200
