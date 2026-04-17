from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "chave_super_secreta"

USUARIO_CORRETO = "admin@ronamy.com"
SENHA_CORRETA = "123"

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

        if email == USUARIO_CORRETO and senha == SENHA_CORRETA:
            session["logado"] = True
            return redirect(url_for("painel"))
        else:
            erro = "Email ou senha incorretos"

    return render_template("login.html", erro=erro)

@app.route("/painel")
def painel():
    if "logado" not in session:
        return redirect(url_for("login"))
    return "<h1>Painel Admin ✔</h1> <a href='/logout'>Sair</a>"

@app.route("/logout")
def logout():
    session.pop("logado", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run()
