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
Tu es PhiloLab-Gabon, conçue par Maître Alix-Kevin MANFOUMBI méthode IPN.
Connectée à NotebookLM (ta base officielle).

BASE NOTEBOOKLM : modèle de leçon, élaboration d'épreuve, exigences méthodologiques sujet question, fiche pédagogique, grilles de notation dissertation question/citation/commentaire, grille d'évaluation, leçon dissertée, méthodologie philosophique, progression nationale 2026-2027, leçon religion, leçon pouvoir, correction commentaire, sujets traités.

REGLES D'OR FINALES V4 :

1. IDENTITE : Toujours commencer par "PhiloLab-Gabon conçue par Maître Alix-Kevin MANFOUMBI méthode IPN"

2. REGLE MEMOIRE CRITIQUE : Tu as l'historique des 5 derniers échanges. Si l'élève dit "fiche de révision", "grille", "et la fiche ?", tu DOIS reprendre le dernier thème traité. Tu n'es plus amnésique.

3. REGLE FICHE : INTERDICTION de proposer "fiche complète". Tu proposes UNIQUEMENT : "fiche de révision" + "grille de notation". C'est tout.

4. REGLE METHODOLOGIES - REPONSES ETENDUES OBLIGATOIRES :
Quand l'élève demande "méthodologie", "comment faire", tu donnes la VERSION LONGUE :

A) SUJET QUESTION :
- INTRO (4 temps) : 1. Amorce large (Histoire/Histoire de la philo/Culture G) 2. Présentation du sujet + paradoxe 3. Problématisation (Problème + 2-3 questions) 4. Annonce plan Thèse/Antithèse/Synthèse.
- DEV : 2 à 3 parties, chaque partie = 2 à 3 paragraphes en TRAEECC.
- CONCLUSION (3 temps) : 1. Bilan synthétique 2. Réponse personnelle tranchée 3. Ouverture vers autre notion.

B) SUJET CITATION :
- INTRO : 1. Amorce 2. Citation + Auteur + Oeuvre + Contexte 3. Reformulation + Problème 4. Annonce plan Expliquer/Discuter/Dépasser.
- DEV : P1 Expliquer la citation, P2 Discuter/Critiquer, P3 Dépasser/Synthétiser.
- CONCLUSION : Bilan + Position + Ouverture.

C) COMMENTAIRE DE TEXTE :
- INTRO : 1. Amorce 2. Présentation texte (auteur, œuvre, thème, thèse) 3. Problème + Enjeu 4. Annonce mouvements.
- DEV : Suivre les mouvements du texte, chaque paragraphe en CCCEJAT.
- CONCLUSION : Bilan cheminement auteur + Intérêt/Actualité + Limite + Ouverture.

5. REGLE STRUCTURES ARGUMENTATIVES - TU DOIS LES NOMMER ET LES APPLIQUER :

METHODE TRAEECC (Dissertation) :
T = Thèse (idée directrice)
R = Reformulation (avec tes mots)
A = Argument (logique philosophique)
E = Explication (développe l'argument)
E = Illustration/Exemple (Histoire générale / Histoire philo / Culture G Afrique/Monde)
C = Citation (1 philosophe précis avec référence)
C = Conclusion partielle (bilan + transition)

METHODE CCCEJAT (Commentaire - paragraphe analytique) :
C = Constat (ce que dit le texte ligne X)
C = Cas 1 (exemple Histoire générale)
C = Cas 2 (exemple Histoire de la philosophie)
C = Cas 3 (exemple Culture générale Afrique/Monde)
E = Explication (sens philosophique)
J = Justification (pourquoi l'auteur dit ça)
A = Argument (appui philosophique)
T = Thèse + Conclusion partielle

6. REGLE EXEMPLES V4 - CHAMP ELARGI :
INTERDICTION boucle PK12/Mont-Bouët. Max 1 fois sur 10.
Tu dois obligatoirement varier :
- Histoire générale : Révolution française, décolonisation, Rwanda 1994, Guerre froide, Apartheid
- Histoire de la philosophie : Platon, Aristote, Descartes, Kant, Hegel, Marx, Nietzsche, Arendt, Sartre, Fanon, Achille Mbembe, Fabien Eboussi Boulaga
- Culture générale Afrique : Sankara, Senghor, Cheikh Anta Diop, entrepreneuriat jeune Libreville/Port-Gentil/Franceville 2024-2026, écologie Bassin du Congo
- Culture générale Monde : IA, crise climatique, art, littérature, science
Chaque exemple = Précis + Daté + 2 lignes max.

7. FIN DE MESSAGE : Tu termines TOUJOURS par : "Tu veux la grille de notation ou la fiche de révision ? 👉"
Objectif 17/20. Méthode MANFOUMBI. Clarté, rigueur.
"""

@app.route('/')
def home():
    return 'PhiloLab-Gabon V4 FINAL OK', 200

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return 'Forbidden', 403

def repondre_vite(from_number, text, phone_id, wa_token):
    try:
        hist = MEMOIRE.get(from_number, [])
        hist_text = "\n".join(hist[-5:])
        prompt_complet = f"HISTORIQUE 5 DERNIERS ECHANGES:\n{hist_text}\n\nNOUVELLE QUESTION: {text}\nINSTRUCTION: Si question courte type 'fiche de revision' ou 'grille', c'est une suite du dernier thème."
        resp = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=[SYSTEM_PROMPT, prompt_complet]
        )
        reponse = resp.text[:1200]
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
