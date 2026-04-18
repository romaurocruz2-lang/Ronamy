from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "chave_super_secreta"

DB = "database.db"

# ---------------- BANCO ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # USUÁRIOS (SaaS real)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # AGENDAMENTOS (multiusuário)
    c.execute("""
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        nome TEXT,
        data TEXT,
        hora TEXT,
        profissional TEXT,
        servico TEXT,
        status TEXT DEFAULT 'Agendado'
    )
    """)

    # PROFISSIONAIS
    c.execute("""
    CREATE TABLE IF NOT EXISTS profissionais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT
    )
    """)

    # SERVIÇOS
    c.execute("""
    CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        preco TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- DADOS PADRÃO ----------------
def seed_data():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if c.execute("SELECT COUNT(*) FROM profissionais").fetchone()[0] == 0:
        c.executemany("INSERT INTO profissionais (nome) VALUES (?)", [
            ("Ronamy",),
            ("Larissa",),
            ("Selvina",)
        ])

    if c.execute("SELECT COUNT(*) FROM servicos").fetchone()[0] == 0:
        c.executemany("INSERT INTO servicos (nome, preco) VALUES (?, ?)", [
            ("Corte", "50"),
            ("Barba", "30"),
            ("Escova", "40")
        ])

    conn.commit()
    conn.close()

seed_data()

# ---------- LOGIN FIXO (temporário SaaS 4) ----------
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
            session["user_id"] = 1
            return redirect(url_for("painel"))
        else:
            erro = "Login inválido"

    return render_template("login.html", erro=erro)

# ---------- PAINEL ----------
@app.route("/painel")
def painel():
    if "logado" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id", 1)

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    agendamentos = c.execute("""
        SELECT id, nome, data, hora, profissional, servico, status
        FROM agendamentos
        WHERE user_id=?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    profissionais = c.execute("SELECT nome FROM profissionais").fetchall()
    servicos = c.execute("SELECT nome, preco FROM servicos").fetchall()

    conn.close()

    return render_template(
        "painel.html",
        agendamentos=agendamentos,
        profissionais=profissionais,
        servicos=servicos
    )

# ---------- AGENDAR ----------
@app.route("/agendar", methods=["POST"])
def agendar():
    if "logado" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id", 1)

    nome = request.form.get("nome")
    data = request.form.get("data")
    hora = request.form.get("hora")
    profissional = request.form.get("profissional")
    servico = request.form.get("servico")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    conflito = c.execute("""
        SELECT * FROM agendamentos
        WHERE data=? AND hora=? AND profissional=?
    """, (data, hora, profissional)).fetchone()

    if conflito:
        conn.close()
        return redirect(url_for("painel"))

    c.execute("""
    INSERT INTO agendamentos (
        user_id, nome, data, hora, profissional, servico
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, nome, data, hora, profissional, servico))

    conn.commit()
    conn.close()

    return redirect(url_for("painel"))

# ---------- STATUS ----------
@app.route("/status/<int:id>/<novo>")
def status(id, novo):
    if "logado" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("UPDATE agendamentos SET status=? WHERE id=?", (novo, id))

    conn.commit()
    conn.close()

    return redirect(url_for("painel"))

# ---------- DELETE ----------
@app.route("/delete/<int:id>")
def delete(id):
    if "logado" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("DELETE FROM agendamentos WHERE id=?", (id,))

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
