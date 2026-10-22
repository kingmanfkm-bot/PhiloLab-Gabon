from flask import Flask, request, jsonify, render_template_string
import random
from datetime import datetime

app = Flask(__name__)

# --- BASE DE CONNAISSANCE PHILO GABON SANS CLE ---
PHILO_DB = {
    "dissertation": "Méthode Dissertation (Officiel Gabon):\n1. Analyser le sujet (mots clés)\n2. Problématiser: Quelle est la question cachée ?\n3. Plan: Thèse (oui) / Antithèse (mais) / Synthèse (dépassement)\n4. Intro: Accroche + Définition + Problématique + Annonce plan\n5. Conclusion: Bilan + Ouverture",
    "commentaire": "Méthode Commentaire: \n1. Situation du texte (auteur, thème)\n2. Thèse de l'auteur\n3. Mouvements du texte (Idée 1, 2, 3)\n4. Analyse des concepts clés + exemples\n5. Enjeux et limites",
    "liberté": "La Liberté selon Sartre: 'L'homme est condamné à être libre'. Mais pour le Gabon, on ajoute: être libre c'est aussi respecter la communauté et les valeurs. Rousseau: Ma liberté s'arrête où commence celle d'autrui.",
    "conscience": "Conscience: Descartes 'Je pense donc je suis'. C'est la voix intérieure qui juge. Freud ajoute: il y a aussi l'inconscient qui nous trompe.",
    "travail": "Travail: Pour Marx, il aliène. Pour le programme gabonais, il humanise et développe la nation. 'Par le travail, l'esclave devient maître de la nature' - Hegel.",
    "bonjour": "Mboté Maître MANFOUMBI ! Je suis le PhiloBot Gabon. Pose-moi ta notion : liberté, conscience, travail, vérité, État ? Ou tape 'dissertation' ou 'commentaire'.",
}

def bot_reponse(question):
    q = question.lower()
    for mot_cle, reponse in PHILO_DB.items():
        if mot_cle in q:
            return reponse
    if "exemple" in q or "plan" in q:
        return PHILO_DB["dissertation"]
    if "aide" in q:
        return PHILO_DB["bonjour"]
    return "Bonne question ! Pour le programme de Tle A/B Gabon, essaie avec: liberté, conscience, travail, dissertation, commentaire. Reformule ta question autour d'une notion."

# --- TEMPLATE HTML UNIQUE AVEC TOUT DEDANS ---
HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PhiloLab Gabon - Maître MANFOUMBI</title>
<style>
body{font-family:Arial,sans-serif;margin:0;background:#f4f8f4}
header{background:linear-gradient(90deg,#009e60,#ffcc00,#0057a8);color:white;padding:20px;text-align:center}
header h1{margin:0;font-size:28px} header p{margin:5px}
nav{background:#003300;display:flex;justify-content:center;gap:15px;padding:10px}
nav button{padding:10px 20px;border:none;border-radius:20px;cursor:pointer;font-weight:bold;background:white}
nav button.active{background:#ffcc00}
section{display:none;padding:20px;max-width:900px;margin:auto;background:white;margin-top:20px;border-radius:15px;box-shadow:0 5px 15px #0002}
section.active{display:block}
.card{border-left:5px solid #009e60;padding:15px;margin:15px 0;background:#f9fff9;border-radius:8px}
.chatbox{height:350px;border:1px solid #ccc;overflow-y:auto;padding:10px;border-radius:10px;background:#fcfffc}
.msg{margin:8px;padding:10px;border-radius:12px;max-width:80%}
.user{background:#d4e8ff;margin-left:auto;text-align:right}
.bot{background:#e8ffe8}
input[type=text]{width:70%;padding:12px;border-radius:20px;border:1px solid #aaa}
.btn-send{padding:12px 20px;border-radius:20px;border:none;background:#009e60;color:white;font-weight:bold;cursor:pointer}
footer{text-align:center;padding:20px;color:#555}
</style>
</head>
<body>
<header>
<h1>🇬🇦 PhiloLab Gabon</h1>
<p><b>Maître MANFOUMBI - Sans Clé - 100% Gratuit</b></p>
<p>Plateforme Officielle Philosophie Tle A/B - Programme Gabonais</p>
</header>
<nav>
<button onclick="show('accueil')" id="b-accueil" class="active">Accueil Gabon</button>
<button onclick="show('philolab')" id="b-philolab">Interface PhiloLab</button>
<button onclick="show('chatbot')" id="b-chatbot">Chatbot Élèves</button>
</nav>

<section id="accueil" class="active">
<h2>Bienvenue dans la Nation Philo !</h2>
<div class="card"><b>Notre Mission:</b> Rendre la philosophie accessible à tous les lycéens du Gabon, de Libreville à Franceville, sans internet cher ni clé API.</div>
<div class="card"><b>Programme Tle 2025-2026:</b><br>• La conscience et l'inconscient<br>• La liberté et la responsabilité<br>• Le travail et la technique<br>• L'État, la justice et le droit<br>• Vérité et Raison</div>
<div class="card"><b>Méthode MANFOUMBI:</b> Apprendre = Comprendre + S'exprimer + Devenir citoyen gabonais éclairé.</div>
<p><b>Site Live:</b> https://philolab-gabon.onrender.com - Déployé le {{date}}</p>
</section>

<section id="philolab">
<h2>Interface PhiloLab - Cours & Méthodes</h2>
<div class="card"><h3>1. Méthodologie Dissertation</h3><p>{{dissert}}</p></div>
<div class="card"><h3>2. Méthodologie Commentaire de Texte</h3><p>{{comment}}</p></div>
<div class="card"><h3>3. Fiches Auteurs Clés</h3><p><b>Platon, Descartes, Kant, Sartre, Rousseau, Fanon (Afrique)</b> - Clique sur Chatbot et tape leur nom.</p></div>
<div class="card"><h3>4. Banque de Sujets Bac Gabon</h3><p>• Peut-on tout dire ? • Le travail libère-t-il ? • Faut-il craindre l'État ?</p></div>
</section>

<section id="chatbot">
<h2>PhiloBot Gabon - Ton Tuteur 24h/24</h2>
<div class="chatbox" id="chat">
<div class="msg bot">Mboté ! Je suis le PhiloBot de Maître MANFOUMBI. Tape : liberté, conscience, dissertation, commentaire...</div>
</div><br>
<input type="text" id="q" placeholder="Pose ta question philo ici..."><button class="btn-send" onclick="envoyer()">Envoyer</button>
</section>

<footer>PhiloLab Gabon © 2026 - Maître MANFOUMBI - Éducation pour tous - Sans Clé</footer>

<script>
function show(id){
document.querySelectorAll('section').forEach(s=>s.classList.remove('active'));
document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active'));
document.getElementById(id).classList.add('active');
document.getElementById('b-'+id).classList.add('active');
}
async function envoyer(){
let input=document.getElementById('q'); let txt=input.value; if(!txt) return;
let chat=document.getElementById('chat');
chat.innerHTML+=`<div class='msg user'>${txt}</div>`; input.value='';
let res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:txt})});
let data=await res.json();
chat.innerHTML+=`<div class='msg bot'>${data.reponse.replace(/\\n/g,'<br>')}</div>`;
chat.scrollTop=chat.scrollHeight;
}
document.getElementById('q').addEventListener('keypress',e=>{if(e.key==='Enter') envoyer()});
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML, 
        date=datetime.now().strftime("%d/%m/%Y"),
        dissert=PHILO_DB["dissertation"],
        comment=PHILO_DB["commentaire"])

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    question = data.get("question","")
    reponse = bot_reponse(question)
    return jsonify({"reponse": reponse})
# === WEBHOOK WHATSAPP POUR NUMERO ROBOT 77082886 ===
import os
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "philo-gabon-2026")

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    data = request.get_json()
    print(f"WEBHOOK RECU: {data}")
    # TODO: ici tu appelles ta fonction qui répond avec Gemini
    # pour l'instant on renvoie OK pour que Meta valide
    return 'OK', 200
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
