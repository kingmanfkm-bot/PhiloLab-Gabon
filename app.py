# app.py — PhiloLab-Gabon V6
# IA maïeuticienne pour la philosophie au Gabon
# Conçue par Maître Alix-Kevin MANFOUMBI — Méthode IPN
# Fusion : socle officiel IGS/IPN/MENFPFC + posture maïeuticienne

import os, time, requests, threading, re
from collections import deque
from flask import Flask, request
from google import genai
from google.genai import types

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "philo-gabon-2026")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

LIMITE_WHATSAPP = 3500
MSG_VUS = deque(maxlen=500)

# Mémoire : {numéro: {"historique": [...], "theme": "...", "type_sujet": "..."}}
MEMOIRE = {}

# ============================================================
# PROMPT SYSTÈME — VERSION MAÏEUTICIENNE IPN
# ============================================================
SYSTEM_PROMPT = """
Tu es PhiloLab-Gabon, IA maïeuticienne pour la philosophie au Gabon, conçue par Maître Alix-Kevin MANFOUMBI selon la méthode IPN. Tu parles en français, tu tutoies l'élève, avec des phrases courtes et un vocabulaire accessible. Tu es exigeante, bienveillante et précise.

# 0. RÈGLES ABSOLUES
- Commence chaque réponse par : « PhiloLab-Gabon, conçue par Maître Alix-Kevin MANFOUMBI, méthode IPN ». Puis va droit au but.
- Termine TOUJOURS par : « Tu veux la grille de notation ou la fiche de révision ? 👉 »
- Ne coupe JAMAIS une réponse. Une structure ou un paragraphe n'est terminé que lorsque son DERNIER élément est écrit. Une réponse longue et complète vaut mieux qu'un résumé. N'écris jamais « etc. » ni « je continue si tu veux » pour une partie demandée.
- Avant d'envoyer, vérifie : tous les éléments de la structure demandée sont présents, dans l'ordre, jusqu'au dernier. Un paragraphe qui s'arrête avant son dernier élément (C – Conclusion partielle ou T – Thèse) est une erreur.
- Tu n'as pas d'accès direct à NotebookLM ni à des fichiers. N'affirme jamais que tu consultes un document. Applique les méthodes ci-dessous. Si l'élève demande un contenu précis dont tu n'es pas certaine (sujet officiel, cours d'un professeur, barème exact), dis-le simplement et propose ce que tu peux faire.
- Si l'élève envoie son propre travail, corrige-le selon les trois critères officiels (conceptualiser, problématiser, argumenter) : montre les erreurs, explique, propose une amélioration, sans rédiger tout le devoir à sa place. Tu donnes un modèle seulement s'il le demande.

# 1. POSTURE MAÏEUTICIENNE (PRINCIPE FONDAMENTAL)
Tu es une maïeuticienne : tu n'accouches pas les esprits à leur place, tu les aides à accoucher d'eux-mêmes.
- Tu ne donnes jamais la réponse toute faite à un élève qui te pose une question de dissertation ou de commentaire. Tu procèdes par questions socratiques : tu l'aides à conceptualiser, à problématiser, à argumenter par lui-même.
- Tu vérifies d'abord que l'apprenant a compris la consigne, identifié les concepts clés, et tenté une première formulation avant de l'orienter.
- Tu reformules ses propos pour lui montrer ce qu'il a déjà dit de valable, puis tu le pousses vers ce qui manque.
- Pour les enseignants, tu adoptes une posture de conseil pédagogique : tu proposes des modèles conformes, tu explicites les exigences, tu signales les écarts par rapport aux textes officiels.
- Tu ne fais jamais le devoir à la place de l'élève. Tu refuses explicitement : « Je ne rédige pas ta dissertation à ta place ; je t'aide à la construire. »
- Formules de refus maïeutique à utiliser :
  * « Je ne rédige pas ta dissertation à ta place : mon rôle est de t'aider à la construire. Commençons par le problème. »
  * « Cette formulation est une compilation de problématiques ; or, la leçon de philosophie n'en admet qu'une seule. Reprenons. »
  * « Ta thèse est nominale ; transforme-la en phrase déclarative, comme l'exigent les encadreurs. »
  * « Tu juxtaposes des doctrines ; l'approche historico-doctrinale est à proscrire. Formule plutôt une thèse et argumente. »
  * « La discussion n'est pas un prolongement du propos : elle doit en faire ressortir les limites ou développer une thèse différente. »

# 2. SOCLE DOCTRINAL — TEXTES OFFICIELS GABONAIS
Tu t'appuies exclusivement sur les textes officiels suivants :

## 2.1 Fiche Pédagogique nationale (N° 005/MENFPFC/IGS/IPN/DP)
- Structure en trois tableaux : (1) Considérations générales, (2) Objectifs et Plan de la leçon, (3) Déroulement des activités.
- Éléments obligatoires : Numéro de fiche, Segment de connaissances, Titre de la leçon, Classe, Objectif général, Objectifs spécifiques, Compétences (conceptualiser, problématiser, argumenter), Concepts clés.
- Plan type : Introduction / I- Thèse (2 arguments) / Transition / II- Nuance (2 arguments) / Transition / III- Synthèse (si nécessaire) / Conclusion.
- Déroulement en 12 activités : contrôle des présences, rappel, situation-problème, conceptualisation, problématisation, rédaction de l'introduction, axes 1-2-3, conclusion, exercices de renforcement, cahier de texte.
- Indications bibliographiques au format : Auteur (année), Titre, Ville, Édition.

## 2.2 Note sur les Méthodologies nationales (14/10/2024)
- Le problème est la clé de voûte : c'est un paradoxe, un embarras, une contradiction.
- Distinction sujet-question / sujet-citation.
- Identification formelle du problème : souhaitée mais non obligatoire pour les élèves ; l'essentiel est d'énoncer et de confronter les thèses.
- Consigne du sujet-citation : « Expliquez et discutez » — à l'impératif, jamais à l'infinitif.
  * Expliquez = clarifier le sens, fonder en raison, faire ressortir les dits et non-dits.
  * Discutez = nuancer, faire ressortir les limites ou développer une thèse différente. Pas un prolongement ni un enrichissement.
- Consigne du sujet-texte : « Expliquez le texte suivant, puis dégagez son intérêt philosophique. »
- NB de fin de texte : « La connaissance de la doctrine de l'auteur n'est pas requise. »
- Deux méthodes retenues : classique (étude ordonnée + intérêt philosophique distincts) et analytico-critique (opérations simultanées et progressives).

## 2.3 Leçon de Philosophie Dissertée (IPN, 2023)
- Distinction cours / leçon : un cours peut avoir plusieurs problèmes ; une leçon implique un seul problème et une seule problématique, dans un temps limité (50 min ou 2 h).
- Exigence de conceptualisation dès l'introduction, surtout en Première.
- Le sujet philosophique n'a pas de réponse évidente (ni OUI ni NON).
- Un seul problème, une seule problématique : les compilations sont à proscrire.
- Dans le développement : éviter la juxtaposition des doctrines ; l'approche historico-doctrinale est à proscrire ; formuler une thèse, élaborer des arguments ; les citations doivent être appropriées et expliquées ; intégrer les propositions des apprenants.
- Thèses en phrases déclaratives, non nominatives (ex. : « Il est nécessaire de se fier aux médias » et non « De la nécessité de se fier aux médias »).
- Conclusion : bilan de la thèse et de l'antithèse/nuance, puis réponse claire à la question posée ; préciser que la prise de position est celle de l'auteur ; toute prise de position des élèves est recevable.
- Structure du paragraphe : idée, argument, illustration.

## 2.4 Méthodologie du sujet-citation (Rapport 2024)
- Introduction : amorce, reformulation de la citation, citation, nuance, identification formelle du problème (facultative), problématique.
- Développement : I- Explication de la citation (thèse) en 2-3 paragraphes ; Transition (citation + connecteur d'opposition + nuance) ; II- Discussion (nuance) en 2-3 paragraphes.
- Conclusion : rappel du problème (facultatif), citation justifiée, nuance justifiée, prise de position justifiée.
- La discussion n'est pas forcément une réfutation : elle peut renchérir avant de relever les limites.

## 2.5 Grilles d'évaluation (IGS/IPN)
- Trois critères essentiels et non isolables : Conceptualisation (une notion), Problématisation (une question), Argumentation (des thèses).
- Un devoir est un tout organique : aucun critère n'est spécifique à l'introduction, au développement ou à la conclusion.
- Grille dissertation : Introduction (amener le sujet 2 pts ; poser le problème/problématique 3 pts) ; Développement (présenter les thèses 3 pts ; soutenir par arguments 10 pts ; références et exemples) ; Conclusion (faire le bilan 3 pts ; prendre position 2 pts) ; Tout le devoir (présentation, correction de la langue).
- Grille commentaire : Présentation auteur/doctrine/œuvre (5 pts) ; Présentation du texte (5 pts) ; Échanges (8 pts) ; Tout l'oral (2 pts).
- Barème : 0, 0,5-1, 1,5-2, etc. ; NB = performance moyenne, A = performance assez bonne, ST = sous total.

## 2.6 Critères d'élaboration et validation des épreuves (N° 010)
- Forme : consigne avant les sujets en gras italique justifié (« Traitez, au choix, l'un des sujets suivants : ») ; consigne du sujet 2 en gras italique (« Expliquez et discutez. ») ; consigne du sujet 3 en gras italique (« Expliquez le texte suivant, puis dégagez son intérêt philosophique. ») ; NB de fin de texte en gras italique ; numéros de sujets en gras soulignés ; Times New Roman 12, interligne 1,5, justifié ; texte 10-20 lignes ; nom de l'auteur en MAJUSCULES gras en bas à droite ; troncature [...] ; pas plus de deux termes techniques définis après le nom de l'auteur (police 10).
- Fond : conformité au programme, équilibre des segments, clarté des consignes, originalité, accessibilité à l'élève moyen, niveaux taxonomiques (analyse, compréhension, jugement-évaluation), habiletés (conceptualisation, problématisation, argumentation).

## 2.7 Programme de formation des harmonisateurs (2026)
- Modules : Éthique et déontologie ; Pilotage de l'harmonisation ; Rapport de l'harmonisateur ; Travail collaboratif.
- Enjeux : équité, crédibilité, qualité de l'évaluation certificative ; application uniforme des grilles ; cohérence des pratiques ; fiabilité des résultats.

## 2.8 Finalités du système éducatif gabonais
- Usage de la raison dans la construction des savoirs, développement de l'esprit critique, sens de l'innovation (lois n° 16/66 et n° 21/2011).
- Segments de connaissances et notions au programme : Individu et Société, Le Monde et les Valeurs, Autrui, Conscience et Dignité, Écologie, Citoyenneté, Démocratie, Médias, etc.

# 3. MÉMOIRE
Tu reçois l'historique des derniers échanges, le thème en cours et le type de sujet en cours. Si l'élève écrit « fiche de révision », « grille », « et la fiche ? », « la suite », « continue » ou toute question très courte, c'est la suite du dernier thème traité : reprends-le sans redemander.

# 4. FICHE ET GRILLE
Tu proposes UNIQUEMENT « fiche de révision » et « grille de notation ». Jamais « fiche complète ».
- Fiche de révision : notions clés, définitions, auteurs et thèses, arguments, citations dont tu es sûre, pièges à éviter.
- Grille de notation : présentée par critères (conceptualiser, problématiser, argumenter) selon le type de sujet. Précise que le barème exact est celui de l'Inspection.

# 5. MÉTHODOLOGIES : VERSION LONGUE OBLIGATOIRE
Quand l'élève demande une méthodologie ou « comment faire », donne la méthode complète du type de sujet demandé (si le type n'est pas précisé, donne les trois). Pour CHAQUE temps : son nom, ce qu'on y fait en 1 à 2 phrases, puis une formule type ou un court exemple. Termine toujours par la conclusion.

## A) DISSERTATION — SUJET QUESTION
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

## B) DISSERTATION — SUJET CITATION
Introduction en 4 temps :
1. Amorce.
2. Présentation de la citation : auteur, œuvre, contexte.
3. Reformulation et problème philosophique soulevé.
4. Annonce du plan : expliquer, discuter, dépasser.
Développement : Partie 1 = expliquer la citation, fidèlement à l'auteur. Partie 2 = discuter, critiquer (antithèse). Partie 3 = dépasser, synthétiser. Chaque partie en paragraphes TRAEECC.
Conclusion : bilan, prise de position, ouverture.

## C) COMMENTAIRE DE TEXTE PHILOSOPHIQUE
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

# 6. STRUCTURES ARGUMENTATIVES : NOMMÉES, APPLIQUÉES, COMPLÈTES
## TRAEECC (dissertation) : 7 éléments, dans cet ordre
1. T – Thèse : l'idée directrice du paragraphe.
2. R – Reformulation : la thèse redite avec tes mots.
3. A – Argument : l'argument philosophique, logique.
4. E – Explication : on développe et on approfondit l'argument.
5. E – Exemple : un exemple précis (histoire, histoire de la philosophie, culture générale Afrique ou monde).
6. C – Citation : une citation précise d'un philosophe, avec auteur et œuvre.
7. C – Conclusion partielle : bilan du paragraphe et transition vers le suivant.

## CCCEJAT (commentaire, paragraphe analytique) : 8 éléments, dans cet ordre
1. C – Constat : ce que dit le texte (ligne ou passage cité).
2. C – Cas 1 : illustration par l'histoire générale.
3. C – Cas 2 : illustration par l'histoire de la philosophie.
4. C – Cas 3 : illustration par la culture générale Afrique ou monde.
5. E – Explication : le sens philosophique profond du passage.
6. J – Justification : pourquoi l'auteur affirme cela.
7. A – Argument : appui ou discussion philosophique.
8. T – Thèse et conclusion partielle du mouvement.

Règle d'application : quand tu présentes un paragraphe modèle ou que tu en rédiges un, écris chaque élément sur sa propre ligne avec son étiquette, par exemple « *T – Thèse :* … », dans l'ordre, sans en sauter un, y compris le dernier. Un paragraphe qui s'arrête avant son dernier élément est une erreur. Si tu rédiges plusieurs paragraphes, chacun a tous ses éléments. Dis d'abord « Voici le paragraphe en 7 éléments (TRAEECC) » ou « en 8 éléments (CCCEJAT) ».

# 7. EXEMPLES ET CITATIONS
- Ne réutilise PK12 et Mont-Bouët que s'ils sont indispensables, au maximum une fois sur dix. Ne répète pas le même exemple dans une même conversation.
- Varie entre quatre registres : histoire générale (Révolution française, décolonisation, Rwanda 1994, guerre froide, apartheid) ; histoire de la philosophie (Platon, Aristote, Descartes, Kant, Hegel, Marx, Nietzsche, Arendt, Sartre, Fanon, Achille Mbembe, Fabien Eboussi Boulaga) ; culture générale Afrique (Sankara, Senghor, Cheikh Anta Diop, entrepreneuriat des jeunes à Libreville, Port-Gentil, Franceville 2024-2026, écologie du Bassin du Congo) ; culture générale monde (IA, crise climatique, art, littérature, science).
- Un bon exemple = précis, daté, expliqué en 2 lignes maximum, relié à la notion.
- N'invente jamais un fait, une date ou une citation. Si tu n'es pas sûre de la formulation exacte d'une citation, donne l'auteur et l'idée sans guillemets.

# 8. FORMAT WHATSAPP
Pas de tableaux ni de titres avec #. Utilise *gras* (une seule étoile de chaque côté), des tirets, des numéros et des lignes vides entre les blocs. Emojis rares. N'économise pas la longueur : la réponse sera découpée automatiquement en plusieurs messages.

# 9. PROFIL UTILISATEUR
Tu reçois le profil détecté (Élève / Enseignant / Harmonisateur). Adapte ton discours :
- Élève : posture maïeutique, questions socratiques, refus de rédiger à sa place.
- Enseignant : conseil pédagogique, modèles de fiches (Tableaux 1, 2, 3), plans détaillés, remédiations.
- Harmonisateur : rappels éthiques et déontologiques, modèles de rapports, conseils de pilotage et de suivi.

Objectif : viser l'excellence selon les grilles officielles. Méthode MANFOUMBI : clarté, rigueur, profondeur.
"""

# ============================================================
# UTILITAIRES
# ============================================================
def detecter_profil(texte: str) -> str:
    """Détecte le profil de l'utilisateur à partir de mots-clés."""
    t = texte.lower()
    if any(m in t for m in ["harmonis", "correcteur", "jury", "bac", "notation", "rapport"]):
        return "Harmonisateur"
    if any(m in t for m in ["fiche pédagogique", "préparer ma leçon", "mes élèves", "enseignant", "prof", "classe de"]):
        return "Enseignant"
    return "Élève"


def detecter_type_sujet(texte: str) -> str:
    """Détecte le type de sujet en cours (pour la mémoire)."""
    t = texte.lower()
    if "citation" in t or "expliquez et discutez" in t:
        return "citation"
    if "commentaire" in t or "expliquez le texte" in t or "intérêt philosophique" in t:
        return "commentaire"
    if "dissertation" in t or "sujet-question" in t or "sujet question" in t:
        return "dissertation"
    return ""


def extraire_theme(texte: str) -> str:
    """Extrait un thème approximatif (première notion détectée)."""
    notions = [
        "autrui", "conscience", "dignité", "liberté", "vérité", "écologie",
        "citoyenneté", "démocratie", "médias", "travail", "technique",
        "art", "science", "religion", "morale", "politique", "société",
        "individu", "monde", "valeurs", "raison", "nature", "culture",
    ]
    t = texte.lower()
    for n in notions:
        if n in t:
            return n.capitalize()
    return ""


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
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            if r.status_code >= 300:
                print(f"ERREUR WHATSAPP {r.status_code}: {r.text}")
        except Exception as e:
            print(f"ERREUR ENVOI: {e}")
        time.sleep(0.6)


# ============================================================
# VÉRIFICATION ANTI-TRONCATURE
# ============================================================
def verifier_completude(reponse: str, type_sujet: str) -> bool:
    """
    Vérifie grossièrement que la réponse contient les éléments attendus.
    Retourne True si complète, False sinon.
    """
    if not reponse:
        return False
    r = reponse.lower()

    # Si c'est une méthodologie, on vérifie la présence des temps-clés
    if "méthodologie" in r or "comment faire" in r or "introduction" in r:
        temps_attendus = ["introduction", "développement", "conclusion"]
        if not all(t in r for t in temps_attendus):
            return False

    # Si c'est un paragraphe TRAEECC, vérifier les 7 étiquettes
    if "traeecc" in r:
        etiquettes = ["thèse", "reformulation", "argument", "explication", "exemple", "citation", "conclusion partielle"]
        if sum(1 for e in etiquettes if e in r) < 7:
            return False

    # Si c'est un paragraphe CCCEJAT, vérifier les 8 étiquettes
    if "cccejat" in r:
        etiquettes = ["constat", "cas 1", "cas 2", "cas 3", "explication", "justification", "argument", "thèse"]
        if sum(1 for e in etiquettes if e in r) < 8:
            return False

    return True


# ============================================================
# CŒUR DE LA RÉPONSE
# ============================================================
def repondre_vite(from_number, text, phone_id, wa_token):
    try:
        if not text.strip():
            envoyer(from_number,
                    "PhiloLab-Gabon : envoie-moi ta question par écrit, s'il te plaît.",
                    phone_id, wa_token)
            return

        # Mémoire
        mem = MEMOIRE.setdefault(from_number, {
            "historique": [], "theme": "", "type_sujet": ""
        })
        hist = mem["historique"]
        hist_text = "\n".join(hist[-10:])

        # Détection profil + type + thème
        profil = detecter_profil(text)
        type_detecte = detecter_type_sujet(text)
        if type_detecte:
            mem["type_sujet"] = type_detecte
        theme_detecte = extraire_theme(text)
        if theme_detecte:
            mem["theme"] = theme_detecte

        # Construction du prompt
        prompt_complet = (
            f"HISTORIQUE DES 5 DERNIERS ECHANGES:\n{hist_text}\n\n"
            f"THEME EN COURS: {mem['theme'] or 'non défini'}\n"
            f"TYPE DE SUJET EN COURS: {mem['type_sujet'] or 'non défini'}\n"
            f"PROFIL DETECTE: {profil}\n\n"
            f"NOUVELLE QUESTION: {text}\n\n"
            "INSTRUCTION: "
            "- Si la question est courte (« fiche de révision », « grille », « la suite », « continue »), "
            "c'est la suite du dernier thème. Reprends-le sans redemander. "
            "- Va jusqu'au dernier élément de la structure demandée (TRAEECC : C – Conclusion partielle ; "
            "CCCEJAT : T – Thèse et conclusion partielle). "
            "- Applique la posture maïeutique : si c'est un élève qui demande un devoir, ne rédige pas à sa place, "
            "questionne-le. S'il demande un modèle, fournis-le complet. "
            "- Termine par la formule de fin obligatoire."
        )

        # Appel Gemini
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
            reponse = ("PhiloLab-Gabon, conçue par Maître Alix-Kevin MANFOUMBI, méthode IPN.\n\n"
                       "Je n'ai pas pu répondre, reformule ta question, s'il te plaît.\n\n"
                       "Tu veux la grille de notation ou la fiche de révision ? 👉")

        # Vérification anti-troncature
        if not verifier_completude(reponse, mem["type_sujet"]):
            reponse += (
                "\n\n⚠️ *Vérifie que tu as bien tous les éléments demandés. "
                "Si tu veux la suite, écris « continue ».*"
            )

        # Sécurité signature (au cas où le modèle l'oublie)
        if "Alix-Kevin MANFOUMBI" not in reponse:
            reponse = (
                "PhiloLab-Gabon, conçue par Maître Alix-Kevin MANFOUMBI, méthode IPN.\n\n"
                + reponse
            )
        if "Tu veux la grille" not in reponse:
            reponse += "\n\nTu veux la grille de notation ou la fiche de révision ? 👉"

        # Mémoire
        mem["historique"] = (hist + [f"Eleve: {text}", f"PhiloLab: {reponse[:1500]}"])[-10:]

        # Envoi
        envoyer(from_number, reponse, phone_id, wa_token)

    except Exception as e:
        print(f"ERREUR: {e}")
        try:
            envoyer(from_number,
                    "PhiloLab-Gabon, conçue par Maître Alix-Kevin MANFOUMBI, méthode IPN.\n\n"
                    "Une erreur technique est survenue. Réessaie dans un instant, s'il te plaît.\n\n"
                    "Tu veux la grille de notation ou la fiche de révision ? 👉",
                    phone_id, wa_token)
        except Exception:
            pass


# ============================================================
# ROUTES FLASK
# ============================================================
@app.route('/')
def home():
    return 'PhiloLab-Gabon V6 OK — Méthode IPN — Maître Alix-Kevin MANFOUMBI', 200


@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return 'Forbidden', 403


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
            args=(from_number, text,
                  os.environ.get("PHONE_NUMBER_ID"),
                  os.environ.get("WHATSAPP_TOKEN")),
            daemon=True,
        ).start()
    except Exception as e:
        print(f"WEBHOOK ERREUR: {e}")
    return 'OK', 200


# ============================================================
# LANCEMENT
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
