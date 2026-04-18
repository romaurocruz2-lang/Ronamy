from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "saas5_safe_key"

DB = "database.db"

# ---------------- BANCO ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        password TEXT
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

# ---------------- LOGIN SIMPLES (ESTÁVEL) ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        if email == "admin@ronamy.com" and senha == "123":
            session["user_id"] = 1
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
        WHERE user_id=1
        ORDER BY id DESC
    """).fetchall()

    profissionais = c.execute("SELECT nome FROM profissionais").fetchall()
    servicos = c.execute("SELECT nome, preco FROM servicos").fetchall()

    conn.close()

    return render_template(
        "painel.html",
        agendamentos=agendamentos,
        profissionais=profissionais,
        servicos=servicos
    )

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
    VALUES (1, ?, ?, ?, ?, ?)
    """, (nome, data, hora, profissional, servico))

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
