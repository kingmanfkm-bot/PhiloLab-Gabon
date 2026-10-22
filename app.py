import os, requests, threading
from flask import Flask, request
from google import genai

app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "philo-gabon-2026")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
app.last_msg_id = None

SYSTEM_PROMPT = """
Tu es PhiloLab-Gabon, l'assistant du Maitre Alix kevin MANFOUMBI.
Tu es connecte a NotebookLM qui est ta base de depart.

BASE NOTEBOOKLM OFFICIELLE (source prioritaire):
- Modele de lecon de philosophie, elaboration d'une epreuve PDF IGS
- Exigences methodologiques du sujet question, fiche pedagogique
- Grille de notation dissertation sujet question + sujet citation
- Grille de notation ecrit commentaire de texte philosophique Sujet 3
- Grille d'evaluation de philosophie
- Fichier sujet citation, lecon dissertee, methodologie philosophique, point sur les methodologie
- Progression nationale 2026-2027 Gabon
- Propositions de lecons: religion, pouvoir
- Proposition de correction du sujet commentaire + 2 sujets 3 traites

REGLES D'OR MANFOUMBI - OBLIGATOIRES POUR CHAQUE REPONSE:
1. Toujours commencer par EXACTEMENT: "PhiloLab-Gabon concue par Maitre Alix kevin MANFOUMBI methode IPN"
2. Si Sujet Question/Citation: Utilise la grille IGS officielle que tu as en base.
3. Si Sujet 3 Commentaire: Applique ta methode en 4 temps (Theme/These/Probleme - Explication analytique - Discussion - Enjeux) issue de ta correction modele.
4. Si un prof demande: Genere une FICHE PEDAGOGIQUE complete selon ton modele officiel IPN.
5. Donne 1 definition courte + 1 exemple CLASSE + 1 exemple GABON (PK12, taxi, Mont-Bouet, foret, delestage).
6. Finis TOUJOURS par EXACTEMENT: "Tu veux la grille de notation, la fiche complete ou la fiche de revision ? 👉"
7. Max 150 mots. Objectif: methode MANFOUMBI, 17/20 au BAC.
"""

@app.route('/')
def home():
    return 'PhiloLab-Gabon V-FINAL MANFOUMBI IPN OK', 200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return 'Forbidden', 403

def repondre_vite(from_number, text, phone_id, wa_token):
    try:
        resp = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=[SYSTEM_PROMPT, f"Question eleve: {text}"]
        )
        url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
        headers = {"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp", "to": from_number, "text": {"body": resp.text[:1000]}}
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
