from flask import Flask, render_template, request, redirect, session, flash
import psycopg2
import os
import bcrypt
import urllib.parse
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "ronamy_secret"

# ---------------- CONEXÃO POSTGRESQL ----------------
def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])

# ---------------- INIT DB ----------------
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS professionals (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id SERIAL PRIMARY KEY,
        name TEXT,
        price TEXT,
        duration TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id SERIAL PRIMARY KEY,
        nome TEXT,
        whatsapp TEXT,
        profissional TEXT,
        servico TEXT,
        data TEXT,
        hora TEXT,
        status TEXT DEFAULT 'Agendado'
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS blocked (
        id SERIAL PRIMARY KEY,
        profissional TEXT,
        data TEXT,
        hora TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        email TEXT,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HORÁRIOS ----------------
def gerar_horarios():
    horarios = []
    inicio = datetime.strptime("08:00", "%H:%M")
    fim = datetime.strptime("18:00", "%H:%M")

    while inicio <= fim:
        horarios.append(inicio.strftime("%H:%M"))
        inicio += timedelta(minutes=30)

    return horarios

# ---------------- HOME ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT name FROM professionals")
    professionals = [p[0] for p in c.fetchall()]

    c.execute("SELECT name FROM services")
    services = [s[0] for s in c.fetchall()]

    horarios = gerar_horarios()

    if request.method == "POST":
        nome = request.form["nome"]
        whatsapp = request.form["whatsapp"]
        profissional = request.form["profissional"]
        servico = request.form["servico"]
        data = request.form["data"]
        hora = request.form["hora"]

        c.execute("""
        SELECT * FROM appointments
        WHERE profissional=%s AND data=%s AND hora=%s
        """, (profissional, data, hora))
        conflict = c.fetchone()

        c.execute("""
        SELECT * FROM blocked
        WHERE profissional=%s AND data=%s AND hora=%s
        """, (profissional, data, hora))
        blocked = c.fetchone()

        if conflict or blocked:
            flash("Horário indisponível")
        else:
            c.execute("""
            INSERT INTO appointments (nome, whatsapp, profissional, servico, data, hora)
            VALUES (%s,%s,%s,%s,%s,%s)
            """, (nome, whatsapp, profissional, servico, data, hora))

            conn.commit()

            msg = urllib.parse.quote(
                f"Olá, agendei {servico} com {profissional} no dia {data} às {hora}"
            )

            link = f"https://wa.me/55{whatsapp}?text={msg}"

            conn.close()

            return render_template(
                "success.html",
                nome=nome,
                profissional=profissional,
                servico=servico,
                data=data,
                hora=hora,
                link=link
            )

    conn.close()

    return render_template(
        "index.html",
        professionals=professionals,
        services=services,
        horarios=horarios
    )

# ---------------- LOGIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"].encode()

        c.execute("SELECT * FROM admin WHERE email=%s", (email,))
        user = c.fetchone()

        if user and bcrypt.checkpw(senha, user[1].encode()):
            session["admin"] = True
            return redirect("/dashboard")

        flash("Login inválido")

    conn.close()
    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT name FROM professionals")
    professionals = [p[0] for p in c.fetchall()]

    c.execute("SELECT * FROM appointments ORDER BY data, hora")
    dados = c.fetchall()

    resumo = {}
    for p in professionals:
        c.execute("SELECT COUNT(*) FROM appointments WHERE profissional=%s", (p,))
        resumo[p] = c.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        dados=dados,
        professionals=professionals,
        resumo=resumo
    )

# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    c = conn.cursor()

    c.execute("DELETE FROM appointments WHERE id=%s", (id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- STATUS ----------------
@app.route("/status/<int:id>/<novo>")
def status(id, novo):
    conn = get_db()
    c = conn.cursor()

    c.execute("UPDATE appointments SET status=%s WHERE id=%s", (novo, id))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
