import os, requests, threading
from flask import Flask, request
from google import genai

app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "philo-gabon-2026")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
app.last_msg_id = None

# MÉMOIRE PHILOLAB : garde les 5 derniers échanges par élève
MEMOIRE = {}

SYSTEM_PROMPT = """
Tu es PhiloLab-Gabon, concue par Maitre Alix kevin MANFOUMBI methode IPN.
BASE: NotebookLM officielle (grilles IGS, fiche pédagogique, leçon dissertée, correction Sujet 3, progression 2026-2027)

REGLES D'OR:
1. Toujours commencer par: "PhiloLab-Gabon concue par Maitre Alix kevin MANFOUMBI methode IPN"
2. REGLE MEMOIRE CRITIQUE: Tu as accès à l'historique de la conversation. Si l'utilisateur dit "fiche de révision", "grille", "fiche complète" sans préciser le thème, tu dois REPRENDRE le dernier thème traité dans l'historique. Ne jamais répondre à côté.
3. Sujet Question/Citation: grille IGS. Sujet 3: méthode 4 temps.
4. Exemple Gabon obligatoire (PK12, taxi, Mont-Bouët...)
5. Finis par: "Tu veux la grille de notation, la fiche complete ou la fiche de revision ? 👉"
6. Max 150 mots. Objectif 17/20.
"""

@app.route('/')
def home():
    return 'PhiloLab-Gabon V3 MEMOIRE OK', 200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return 'Forbidden', 403

def repondre_vite(from_number, text, phone_id, wa_token):
    try:
        # 1. Récupère l'historique de cet élève
        hist = MEMOIRE.get(from_number, [])
        hist_text = "\n".join(hist[-5:]) # les 5 derniers

        prompt_complet = f"""
        HISTORIQUE DES 5 DERNIERS ECHANGES AVEC CET ELEVE:
        {hist_text}

        NOUVELLE QUESTION DE L'ELEVE: {text}

        INSTRUCTION: Si la nouvelle question est courte ("fiche de revision", "grille", "et la fiche ?"), c'est une suite logique. Tu dois répondre sur le thème du dernier échange.
        """

        resp = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=[SYSTEM_PROMPT, prompt_complet]
        )
        reponse = resp.text[:1000]

        # 2. Sauvegarde en mémoire
        MEMOIRE[from_number] = (hist + [f"Eleve: {text}", f"PhiloLab: {reponse}"])[-10:]
        
        url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        headers = {"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp", "to": from_number, "text": {"body": reponse}}
        requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print(f"ERREUR: {e}")

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
        threading.Thread(target=repondre_vite, args=(from_number, text, os.environ.get("PHONE_NUMBER_ID"), os.environ.get("WHATSAPP_TOKEN"))).start()
    except Exception as e:
        print(e)
    return 'OK', 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
