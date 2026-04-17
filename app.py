from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "chave_super_secreta"

# LOGIN FIXO
USUARIO = "admin@ronamy.com"
SENHA = "123"

# BANCO SIMPLES EM MEMÓRIA
agendamentos = []

# ---------- LOGIN ----------
@app.route("/")
def home():
    if "logado" in session:
        return redirect(url_for("painel"))
    return redirect(url_for("login"))

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

    return render_template("painel.html", agendamentos=agendamentos)

# ---------- NOVO AGENDAMENTO ----------
@app.route("/agendar", methods=["POST"])
def agendar():
    if "logado" not in session:
        return redirect(url_for("login"))

    nome = request.form.get("nome")
    data = request.form.get("data")
    hora = request.form.get("hora")

    agendamentos.append({
        "nome": nome,
        "data": data,
        "hora": hora
    })

    return redirect(url_for("painel"))

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("logado", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run()
