import os
from flask import Flask, request
app = Flask(__name__)
TOKEN = "philolab_gabon_2026_secret"

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.verify_token') == TOKEN:
        return request.args.get('hub.challenge')
    return "Erreur token", 403

@app.route('/webhook', methods=['POST'])
def receive():
    print("Message reçu:", request.json)
    return "OK", 200

@app.route('/')
def home():
    return "PhiloLab Gabon en ligne !"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
