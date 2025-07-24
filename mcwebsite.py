from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired
import datetime
import json
import os
import ssl  # Für HTTPS

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Benutzer mit Rollen
users = {
    "admin": {"password": "password", "role": "admin"},
    "user": {"password": "password", "role": "user"},
    "david": {"password": "password", "role": "user"},
}

# Datei für Server-IP-Daten
IP_FILE = "minecraft_servers.json"

if not os.path.exists(IP_FILE):
    with open(IP_FILE, "w") as f:
        json.dump({"servers": {}}, f)

# Flask-WTF Formulare
class LoginForm(FlaskForm):
    username = StringField("Benutzername", validators=[InputRequired()])
    password = PasswordField("Passwort", validators=[InputRequired()])
    submit = SubmitField("Login")

class AddServerForm(FlaskForm):
    name = StringField("Server Name", validators=[InputRequired()])
    ip = StringField("IP-Adresse", validators=[InputRequired()])
    submit = SubmitField("Hinzufügen")

# Lade und speichere IPs
def load_ips():
    with open(IP_FILE, "r") as f:
        return json.load(f)

def save_ips(data):
    with open(IP_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Routen (bleiben unverändert)
@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username in users and users[username]["password"] == password:
            session["username"] = username
            session["role"] = users[username]["role"]
            return redirect(url_for("dashboard"))
    return render_template("login.html", form=form)

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    data = load_ips()
    form = AddServerForm()
    return render_template("dashboard.html", servers=data["servers"], role=session["role"], form=form)

@app.route("/add", methods=["POST"])
def add_server():
    if "username" not in session or session["role"] != "admin":
        return jsonify({"error": "Nur Admins dürfen Server hinzufügen"}), 403
    form = AddServerForm()
    if form.validate_on_submit():
        data = load_ips()
        data["servers"][form.name.data] = form.ip.data
        save_ips(data)
    return redirect(url_for("dashboard"))

@app.route("/remove/<server_name>")
def remove_server(server_name):
    if "username" not in session or session["role"] != "admin":
        return jsonify({"error": "Nur Admins dürfen Server entfernen"}), 403
    data = load_ips()
    if server_name in data["servers"]:
        del data["servers"][server_name]
        save_ips(data)
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Log-Verzeichnis für Nutzerdaten
LOG_DIR = "user_logs"
os.makedirs(LOG_DIR, exist_ok=True)  # Log-Ordner erstellen, falls nicht vorhanden

# Funktion zum Speichern von Nutzerdaten in einer Textdatei
def save_user_data(user_data):
    """Speichert die gesammelten Nutzerdaten als TXT-Datei."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(LOG_DIR, f"user_{timestamp}.txt")

    with open(filename, "w", encoding="utf-8") as file:
        for key, value in user_data.items():
            file.write(f"{key}: {value}\n")

@app.route("/track", methods=["POST"])
def track_user():
    """Erfasst die vom Client gesendeten Daten und speichert sie."""
    try:
        user_data = request.json  # Empfängt die gesendeten JSON-Daten
        save_user_data(user_data)  # Speichert die Daten in einer Textdatei
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    # HTTPS-Konfiguration
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain("cert.pem", "key.pem")  # Pfade zu den Zertifikaten
    app.run(host="0.0.0.0", port=5000, ssl_context=context, debug=True)
