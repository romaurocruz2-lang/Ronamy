from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import bcrypt

app = Flask(__name__)
app.secret_key = "saas_super_secret"

DB = "database.db"

# ---------------- BANCO ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password BLOB
    )
    """)

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

    c.execute("""
    CREATE TABLE IF NOT EXISTS profissionais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT
    )
    """)

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

# ---------------- USUÁRIO TESTE ----------------
def seed_user():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        senha = bcrypt.hashpw("123".encode(), bcrypt.gensalt())
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                  ("admin@ronamy.com", senha))

    conn.commit()
    conn.close()

seed_user()

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        user = c.execute("SELECT id, password FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if user and bcrypt.checkpw(senha.encode(), user[1]):
            session["user_id"] = user[0]
            return redirect(url_for("painel"))
        else:
            erro = "Login inválido"

    return render_template("login.html", erro=erro)

# ---------------- PAINEL ----------------
@app.route("/painel")
def painel():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    agendamentos = c.execute("""
        SELECT id, nome, data, hora, profissional, servico, status
        FROM agendamentos
        WHERE user_id=?
        ORDER BY id DESC
    """, (session["user_id"],)).fetchall()

    profissionais = c.execute("SELECT nome FROM profissionais").fetchall()
    servicos = c.execute("SELECT nome, preco FROM servicos").fetchall()

    conn.close()

    return render_template("painel.html",
                           agendamentos=agendamentos,
                           profissionais=profissionais,
                           servicos=servicos)

# ---------------- AGENDAR ----------------
@app.route("/agendar", methods=["POST"])
def agendar():
    if "user_id" not in session:
        return redirect(url_for("login"))

    nome = request.form.get("nome")
    data = request.form.get("data")
    hora = request.form.get("hora")
    profissional = request.form.get("profissional")
    servico = request.form.get("servico")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO agendamentos (user_id, nome, data, hora, profissional, servico)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (session["user_id"], nome, data, hora, profissional, servico))

    conn.commit()
    conn.close()

    return redirect(url_for("painel"))

# ---------------- STATUS ----------------
@app.route("/status/<int:id>/<novo>")
def status(id, novo):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("UPDATE agendamentos SET status=? WHERE id=?", (novo, id))

    conn.commit()
    conn.close()

    return redirect(url_for("painel"))

# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("DELETE FROM agendamentos WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("painel"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run()
