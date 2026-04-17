from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "chave_super_secreta"

DB = "database.db"

# ---------------- BANCO ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        data TEXT,
        hora TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- LOGIN FIXO ----------
USUARIO = "admin@ronamy.com"
SENHA = "123"

# ---------- HOME ----------
@app.route("/")
def home():
    if "logado" in session:
        return redirect(url_for("painel"))
    return redirect(url_for("login"))

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        if email == USUARIO and senha == SENHA:
            session["logado"] = True
            return redirect(url_for("painel"))
        else:
            erro = "Login inválido"

    return render_template("login.html", erro=erro)

# ---------- PAINEL ----------
@app.route("/painel")
def painel():
    if "logado" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT id, nome, data, hora FROM agendamentos ORDER BY id DESC")
    agendamentos = c.fetchall()

    conn.close()

    return render_template("painel.html", agendamentos=agendamentos)

# ---------- AGENDAR ----------
@app.route("/agendar", methods=["POST"])
def agendar():
    if "logado" not in session:
        return redirect(url_for("login"))

    nome = request.form.get("nome")
    data = request.form.get("data")
    hora = request.form.get("hora")

    if not nome or not data or not hora:
        return redirect(url_for("painel"))

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO agendamentos (nome, data, hora)
    VALUES (?, ?, ?)
    """, (nome, data, hora))

    conn.commit()
    conn.close()

    return redirect(url_for("painel"))

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("logado", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run()
