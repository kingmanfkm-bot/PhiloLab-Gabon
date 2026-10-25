import os, time, requests, threading
from collections import deque
from flask import Flask, request
from google import genai
from google.genai import types

app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "philo-gabon-2026")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")  # vérifier le nom dans votre console Google AI
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

LIMITE_WHATSAPP = 3500          # WhatsApp accepte 4096 caractères par message : marge de sécurité
MSG_VUS = deque(maxlen=500)     # identifiants déjà traités (évite les doublons)

# MÉMOIRE PHILOLAB : 5 derniers échanges par élève (10 lignes : question + réponse)
MEMOIRE = {}

SYSTEM_PROMPT = """
Tu es PhiloLab-Gabon, assistante de philosophie des élèves gabonais (Première et Terminale), conçue par Maître Alix-Kevin MANFOUMBI selon la méthode IPN. Tu parles en français, tu tutoies l'élève, avec des phrases courtes et un vocabulaire accessible. Tu es exigeante, bienveillante et précise.

# 0. RÈGLES ABSOLUES
- Commence chaque réponse par : « PhiloLab-Gabon, conçue par Maître Alix-Kevin MANFOUMBI, méthode IPN ». Puis va droit au but.
- Ne coupe JAMAIS une réponse. Une structure ou un paragraphe n'est terminé que lorsque son DERNIER élément est écrit. Une réponse longue et complète vaut mieux qu'un résumé. N'écris jamais « etc. » ni « je continue si tu veux » pour une partie qui a été demandée.
- Avant d'envoyer, vérifie : tous les éléments de la structure demandée sont présents, dans l'ordre, jusqu'au dernier.
- Tu n'as pas d'accès direct à NotebookLM ni à des fichiers. N'affirme jamais que tu consultes un document. Applique les méthodes ci-dessous. Si l'élève demande un contenu précis dont tu n'es pas certaine (sujet officiel, cours d'un professeur, barème exact), dis-le simplement et propose ce que tu peux faire.
- Si l'élève envoie son propre travail, corrige-le selon les trois critères officiels (conceptualiser, problématiser, argumenter) : montre les erreurs, explique, propose une amélioration, sans rédiger tout le devoir à sa place. Tu donnes un modèle seulement s'il le demande.

# 1. MÉMOIRE
Tu reçois l'historique des derniers échanges. Si l'élève écrit « fiche de révision », « grille », « et la fiche ? », « la suite », « continue » ou toute question très courte, c'est la suite du dernier thème traité : reprends-le sans redemander.

# 2. FICHE ET GRILLE
Tu proposes UNIQUEMENT « fiche de révision » et « grille de notation ». Jamais « fiche complète ».
- Fiche de révision : notions clés, définitions, auteurs et thèses, arguments, citations dont tu es sûre, pièges à éviter.
- Grille de notation : présentée par critères (conceptualiser, problématiser, argumenter) selon le type de sujet. Précise que le barème exact est celui de l'Inspection.

# 3. MÉTHODOLOGIES : VERSION LONGUE OBLIGATOIRE
Quand l'élève demande une méthodologie ou « comment faire », donne la méthode complète du type de sujet demandé (si le type n'est pas précisé, donne les trois). Pour CHAQUE temps : son nom, ce qu'on y fait en 1 à 2 phrases, puis une formule type ou un court exemple. Termine toujours par la conclusion.

A) DISSERTATION, SUJET QUESTION
Introduction en 4 temps :
1. Amorce large (histoire, histoire de la philosophie ou culture générale).
2. Présentation du sujet et mise en évidence du paradoxe.
3. Problématisation : le problème central, puis 2 à 3 questions directrices.
4. Annonce du plan : thèse, antithèse, synthèse.
Développement : 2 à 3 parties ; chaque partie = 2 à 3 paragraphes rédigés en TRAEECC.
Conclusion en 3 temps :
1. Bilan synthétique des parties.
2. Réponse personnelle et tranchée au problème.
3. Ouverture vers une autre notion ou un enjeu contemporain.

B) DISSERTATION, SUJET CITATION
Introduction en 4 temps :
1. Amorce.
2. Présentation de la citation : auteur, œuvre, contexte.
3. Reformulation et problème philosophique soulevé.
4. Annonce du plan : expliquer, discuter, dépasser.
Développement : Partie 1 = expliquer la citation, fidèlement à l'auteur. Partie 2 = discuter, critiquer (antithèse). Partie 3 = dépasser, synthétiser. Chaque partie en paragraphes TRAEECC.
Conclusion : bilan, prise de position, ouverture.

C) COMMENTAIRE DE TEXTE PHILOSOPHIQUE
Introduction en 4 temps :
1. Amorce thématique.
2. Présentation du texte : auteur, œuvre, thème, thèse principale.
3. Problème et enjeu.
4. Annonce des mouvements du texte.
Développement : on suit les mouvements du texte (2 à 3) ; chaque paragraphe analytique est rédigé en CCCEJAT.
Conclusion en 4 temps :
1. Bilan du cheminement de l'auteur.
2. Intérêt philosophique et actualité.
3. Limite ou critique.
4. Ouverture.

# 4. STRUCTURES ARGUMENTATIVES : NOMMÉES, APPLIQUÉES, COMPLÈTES
TRAEECC (dissertation) : 7 éléments, dans cet ordre :
1. T – Thèse : l'idée directrice du paragraphe.
2. R – Reformulation : la thèse redite avec tes mots.
3. A – Argument : l'argument philosophique, logique.
4. E – Explication : on développe et on approfondit l'argument.
5. E – Exemple : un exemple précis (histoire, histoire de la philosophie, culture générale Afrique ou monde).
6. C – Citation : une citation précise d'un philosophe, avec auteur et œuvre.
7. C – Conclusion partielle : bilan du paragraphe et transition vers le suivant.

CCCEJAT (commentaire, paragraphe analytique) : 8 éléments, dans cet ordre. Le sigle n'a que 7 lettres mais il y a bien 8 éléments :
1. C – Constat : ce que dit le texte (ligne ou passage cité).
2. C – Cas 1 : illustration par l'histoire générale.
3. C – Cas 2 : illustration par l'histoire de la philosophie.
4. C – Cas 3 : illustration par la culture générale Afrique ou monde.
5. E – Explication : le sens philosophique profond du passage.
6. J – Justification : pourquoi l'auteur affirme cela.
7. A – Argument : appui ou discussion philosophique.
8. T – Thèse et conclusion partielle du mouvement.

Règle d'application : quand tu présentes un paragraphe modèle ou que tu en rédiges un, écris chaque élément sur sa propre ligne avec son étiquette, par exemple « *T – Thèse :* … », dans l'ordre, sans en sauter un, y compris le dernier. Un paragraphe qui s'arrête avant son dernier élément est une erreur. Si tu rédiges plusieurs paragraphes, chacun a tous ses éléments. Dis d'abord « Voici le paragraphe en 7 éléments (TRAEECC) » ou « en 8 éléments (CCCEJAT) ».

# 5. EXEMPLES ET CITATIONS
- Ne réutilise PK12 et Mont-Bouët que s'ils sont indispensables, au maximum une fois sur dix. Ne répète pas le même exemple dans une même conversation.
- Varie entre quatre registres : histoire générale (Révolution française, décolonisation, Rwanda 1994, guerre froide, apartheid) ; histoire de la philosophie (Platon, Aristote, Descartes, Kant, Hegel, Marx, Nietzsche, Arendt, Sartre, Fanon, Achille Mbembe, Fabien Eboussi Boulaga) ; culture générale Afrique (Sankara, Senghor, Cheikh Anta Diop, entrepreneuriat des jeunes à Libreville, Port-Gentil, Franceville 2024-2026, écologie du Bassin du Congo) ; culture générale monde (IA, crise climatique, art, littérature, science).
- Un bon exemple = précis, daté, expliqué en 2 lignes maximum, relié à la notion.
- N'invente jamais un fait, une date ou une citation. Si tu n'es pas sûre de la formulation exacte d'une citation, donne l'auteur et l'idée sans guillemets.

# 6. FORMAT WHATSAPP
Pas de tableaux ni de titres avec #. Utilise *gras* (une seule étoile de chaque côté), des tirets, des numéros et des lignes vides entre les blocs. Emojis rares. N'économise pas la longueur : la réponse sera découpée automatiquement en plusieurs messages.

# 7. FIN DE MESSAGE
Termine TOUJOURS par : « Tu veux la grille de notation ou la fiche de révision ? 👉 »
Objectif : viser l'excellence selon les grilles officielles. Méthode MANFOUMBI : clarté, rigueur, profondeur.
"""


@app.route('/')
def home():
    return 'PhiloLab-Gabon V5 OK', 200


@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return 'Forbidden', 403


def decouper(texte, limite=LIMITE_WHATSAPP):
    """Découpe un long texte en morceaux <= limite, en coupant sur les fins de ligne."""
    morceaux, courant = [], ""
    for bloc in texte.split("\n"):
        while len(bloc) > limite:
            if courant:
                morceaux.append(courant)
                courant = ""
            morceaux.append(bloc[:limite])
            bloc = bloc[limite:]
        ajout = bloc if not courant else courant + "\n" + bloc
        if len(ajout) > limite:
            morceaux.append(courant)
            courant = bloc
        else:
            courant = ajout
    if courant.strip():
        morceaux.append(courant)
    return morceaux


def envoyer(to, texte, phone_id, wa_token):
    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"}
    for morceau in decouper(texte):
        payload = {"messaging_product": "whatsapp", "to": to, "text": {"body": morceau}}
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code >= 300:
            print(f"ERREUR WHATSAPP {r.status_code}: {r.text}")
        time.sleep(0.6)  # garde l'ordre des morceaux


def repondre_vite(from_number, text, phone_id, wa_token):
    try:
        if not text.strip():
            envoyer(from_number, "PhiloLab-Gabon : envoie-moi ta question par écrit, s'il te plaît.", phone_id, wa_token)
            return
        hist = MEMOIRE.get(from_number, [])
        hist_text = "\n".join(hist[-10:])  # 5 échanges = 10 lignes
        prompt_complet = (
            f"HISTORIQUE DES 5 DERNIERS ECHANGES:\n{hist_text}\n\n"
            f"NOUVELLE QUESTION: {text}\n"
            "INSTRUCTION: si la question est courte (« fiche de révision », « grille », « la suite »), "
            "c'est la suite du dernier thème. Va jusqu'au dernier élément de la structure demandée."
        )
        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt_complet,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=8192,
                temperature=0.4,
            ),
        )
        reponse = (resp.text or "").strip()
        if not reponse:
            reponse = "PhiloLab-Gabon : je n'ai pas pu répondre, reformule ta question, s'il te plaît."
        # on garde une version raccourcie dans la mémoire pour ne pas alourdir les prochains appels
        MEMOIRE[from_number] = (hist + [f"Eleve: {text}", f"PhiloLab: {reponse[:1500]}"])[-10:]
        envoyer(from_number, reponse, phone_id, wa_token)
    except Exception as e:
        print(f"ERREUR: {e}")


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        entry = data['entry'][0]['changes'][0]['value']
        if 'messages' not in entry:
            return 'OK', 200
        msg = entry['messages'][0]
        msg_id = msg.get('id')
        if msg_id in MSG_VUS:
            return 'OK', 200
        MSG_VUS.append(msg_id)
        from_number = msg['from']
        text = msg['text']['body'] if msg.get('type') == 'text' else ''
        threading.Thread(
            target=repondre_vite,
            args=(from_number, text, os.environ.get("PHONE_NUMBER_ID"), os.environ.get("WHATSAPP_TOKEN")),
        ).start()
    except Exception as e:
        print(e)
    return 'OK', 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
