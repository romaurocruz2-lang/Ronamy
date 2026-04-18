import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

import bcrypt
from flask import (Flask, flash, g, redirect, render_template, request,
                   session, url_for)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ronamy-secret-2024-change-in-production")

DATABASE = "ronamy.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS professionals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            ativo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            duracao_min INTEGER NOT NULL,
            ativo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            whatsapp TEXT NOT NULL,
            profissional_id INTEGER NOT NULL,
            servico_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            status TEXT DEFAULT 'confirmado',
            criado_em TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (profissional_id) REFERENCES professionals(id),
            FOREIGN KEY (servico_id) REFERENCES services(id)
        );

        CREATE TABLE IF NOT EXISTS blocked_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profissional_id INTEGER,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            motivo TEXT,
            FOREIGN KEY (profissional_id) REFERENCES professionals(id)
        );

        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL
        );
    """)
    db.commit()

    profs = db.execute("SELECT COUNT(*) as c FROM professionals").fetchone()["c"]
    if profs == 0:
        for nome in ["Larissa Magna", "Selvina", "Ronamy"]:
            db.execute("INSERT INTO professionals (nome) VALUES (?)", (nome,))

    svcs = db.execute("SELECT COUNT(*) as c FROM services").fetchone()["c"]
    if svcs == 0:
        initial = [
            ("Corte feminino", 50.0, 30),
            ("Escova", 40.0, 30),
            ("Hidratação", 60.0, 40),
            ("Progressiva", 150.0, 120),
            ("Alisamento", 120.0, 90),
            ("Corte + Escova", 80.0, 60),
        ]
        for nome, preco, dur in initial:
            db.execute("INSERT INTO services (nome, preco, duracao_min) VALUES (?,?,?)", (nome, preco, dur))

    admin_count = db.execute("SELECT COUNT(*) as c FROM admin").fetchone()["c"]
    if admin_count == 0:
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        db.execute("INSERT INTO admin (email, senha_hash) VALUES (?, ?)", ("admin@ronamy.com", hashed))

    db.commit()
    db.close()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def generate_slots():
    slots = []
    start = datetime.strptime("08:00", "%H:%M")
    end = datetime.strptime("18:00", "%H:%M")
    current = start
    while current <= end:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=30)
    return slots


def get_available_slots(profissional_id, data):
    db = get_db()
    all_slots = generate_slots()

    booked = db.execute(
        "SELECT hora FROM appointments WHERE profissional_id=? AND data=? AND status!='cancelado'",
        (profissional_id, data)
    ).fetchall()
    booked_times = {r["hora"] for r in booked}

    blocked = db.execute(
        "SELECT hora FROM blocked_slots WHERE (profissional_id=? OR profissional_id IS NULL) AND data=?",
        (profissional_id, data)
    ).fetchall()
    blocked_times = {r["hora"] for r in blocked}

    occupied = booked_times | blocked_times

    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M")

    result = []
    for s in all_slots:
        status = "disponivel"
        if s in occupied:
            status = "ocupado"
        elif data == today and s <= now_time:
            status = "passado"
        result.append({"hora": s, "status": status})
    return result


# (continua exatamente igual até o final do arquivo que você enviou...)
