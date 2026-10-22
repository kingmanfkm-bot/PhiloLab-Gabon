import os
import requests
from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "philo-gabon-2026")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")

# Configure Gemini une seule fois au démarrage
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- ROUTE 1 : PAGE D'ACCUEIL (pour éviter le Not Found sur /) ---
@app.route('/')
def home():
    return 'PhiloLab-Gabon est en ligne ✅ - Webhook: /webhook', 200

# --- ROUTE 2 : VERIFICATION META (GET) - OBLIGATOIRE ---
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    print(f"=== VERIFICATION META ===")
    print(f"Mode: {mode} | Token reçu: {token} | Token attendu: {VERIFY_TOKEN} | Challenge: {challenge}")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("VERIFICATION OK - Je renvoie le challenge")
        return challenge, 200
    else:
        print("VERIFICATION ECHEC - Forbidden")
        return 'Forbidden', 403

# --- ROUTE 3 : RECEPTION MESSAGES (POST) - COEUR DU ROBOT ---
@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    data = request.get_json()
    print(f"=== WEBHOOK RECU === {data}")
    
    try:
        entry = data['entry'][0]['changes'][0]['value']
        
        # On ignore les status (lu, reçu) - on ne traite que les vrais messages
        if 'messages' not in entry:
            print("Ce n'est pas un message, c'est un status. J'ignore.")
            return 'OK', 200
            
        msg = entry['messages'][0]
        from_number = msg['from']
        msg_type = msg.get('type')
        
        # On ne traite que le texte pour l'instant
        if msg_type != 'text':
            print(f"Type {msg_type} non géré")
            return 'OK', 200
            
        text = msg['text']['body']
        print(f"Message de {from_number}: {text}")

        # 1. Vérif que toutes les clés existent
        if not all([GEMINI_API_KEY, PHONE_NUMBER_ID, WHATSAPP_TOKEN]):
            print(f"ERREUR CONFIG: GEMINI={bool(GEMINI_API_KEY)} PHONE_ID={bool(PHONE_NUMBER_ID)} WA_TOKEN={bool(WHATSAPP_TOKEN)}")
            return 'OK', 200

        # 2. Appel Gemini avec ton prompt PhiloLab
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt_system = """Tu es Kangamukun, le professeur de philosophie de PhiloLab Gabon pour les Terminales A et B du Gabon.
        Ton rôle: Expliquer les cours (Conscience, Inconscient, Liberté, Etat, etc.) de façon simple, courte, avec exemples gabonais.
        Réponds en 4 lignes max, style WhatsApp, motivant. Termine toujours par une petite question pour faire réfléchir."""
        
        response = model.generate_content(f"{prompt_system}\n\nQuestion de l'élève: {text}")
        reply_text = response.text
        print(f"Réponse Gemini: {reply_text}")

        # 3. Renvoi sur WhatsApp
        url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": from_number,
            "type": "text",
            "text": {"body": reply_text}
        }
        r = requests.post(url, headers=headers, json=payload)
        print(f"ENVOI WHATSAPP -> Status: {r.status_code} | Réponse: {r.text}")
            
    except Exception as e:
        print(f"ERREUR CRITIQUE webhook: {e}")
        import traceback
        traceback.print_exc()

    return 'OK', 200

# --- LANCEMENT ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    print(f"Demarrage sur port {port}")
    app.run(host='0.0.0.0', port=port)
