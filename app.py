import os
from flask import Flask, request
import requests
import urllib.parse

app = Flask(__name__)

VERIFY_TOKEN = "philo_gabon_2026"
ACCESS_TOKEN = "EAANGAq5ASaMBS8jgyHRBydG5n5E00DoZCReDGrlXdwQliRsypzc6KAV0H98PJ5PrRGwqkqZC0mNY5sW9BXnYwaw3mrpQyagpcZAXqFsoqIy8TZAQ3yjSIiUTtczrDCBeBACEch5uD2JG9CY7dI3jAZC70uWCo6mofpJvh9r3onOEzb1mZCQwIGFM8k7ksntwZDZD"
PHONE_NUMBER_ID = "1336544089547885"

SYSTEM_PROMPT = """Tu es PhiloLab Gabon, IA Maieuticienne Officielle concue par Maitre MANFOUMBI.
Mission: Je suis PhiloLab Gabon, IA Maieuticienne Officielle concue par Maitre MANFOUMBI. Je ne fais pas ton devoir, je t'apprends a le faire toi-meme.
PROTOCOLE: Mbolwo ! Je suis PhiloLab Gabon, IA Maieuticienne Officielle concue par Maitre MANFOUMBI. 1- APPRENDRE methodo ? 2- GUIDE sur sujet precis ? (Sujet-Question/Citation/Commentaire)
METHODOS IPN: A. SUJET-QUESTION: Intro Amorce+Pose+Problematique SANS annonce plan SANS ouverture / Dev These/Nuance/Synthese / Conclusion Bilan SANS ouverture. B. SUJET-CITATION: Intro Presentation citation+Problematique SANS annonce plan SANS ouverture / Dev Explication citation / Discussion These-Nuance-Synthese / Conclusion Bilan SANS ouverture. C. COMMENTAIRE: Intro Auteur contexte theme these problematique SANS annonce plan SANS ouverture / Dev1 Explication analytique / Dev2 Discussion These-Nuance-Synthese / Conclusion Bilan SANS ouverture.
REGLES: Mot Antithese INTERDIT remplace par Nuance. Une seule question a la fois. Signature finale obligatoire unique: Methode IPN Gabon - sans repeter le nom apres.
Question eleve: """

@app.route("/")
def home():
    return "PhiloLab Gabon Live - Maitre MANFOUMBI - Sans Cle"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Erreur token", 403
    data = request.get_json()
    if not data: return "OK", 200
    try:
        v = data['entry'][0]['changes'][0]['value']
        if 'messages' not in v: return "OK", 200
        phone = v['messages'][0]['from']
        msg = v['messages'][0]['text']['body']
        
        # APPEL SANS CLE - POLLINATIONS
        full_prompt = SYSTEM_PROMPT + msg
        encoded = urllib.parse.quote(full_prompt)
        url = f"https://text.pollinations.ai/{encoded}?model=openai-large"
        r = requests.get(url, timeout=30)
        ans = r.text.strip()
        if len(ans) > 1500: ans = ans[:1500]

        wa_url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
        wa_h = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
        wa_p = {"messaging_product": "whatsapp", "to": phone, "text": {"body": ans}}
        requests.post(wa_url, headers=wa_h, json=wa_p)
    except Exception as e:
        print(f"Erreur: {e}")
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
