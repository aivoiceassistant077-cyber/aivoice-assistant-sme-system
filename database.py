"""
database.py  -  Everything that talks to the SQLite database.
"""
import os
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

from config import BASE_DIR

DEFAULT_FAQS = [
    ("open,opening,hours,time,close,closing",
     "We are open Monday to Saturday from 8 in the morning to 6 in the evening."),
    ("where,location,address,find",
     "Our shop is in Freetown. Please call the owner for exact directions."),
    ("pay,payment,orange,money,cash",
     "We accept cash and mobile money."),
    ("deliver,delivery",
     "Yes, we deliver within Freetown. Delivery cost depends on the distance."),
]


def get_db():
    """Open one database connection per request and reuse it."""
    if "db" not in g:
        path = current_app.config["DATABASE"]
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id


def init_db(app):
    """Create the tables (if they do not exist) and add the first owner account."""
    with app.app_context():
        db = get_db()
        with open(os.path.join(BASE_DIR, "schema.sql"), encoding="utf-8") as f:
            db.executescript(f.read())
        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            db.execute(
                "INSERT INTO users (name, phone, username, password_hash, role) VALUES (?,?,?,?,?)",
                ("Shop Owner", "", "admin", generate_password_hash("admin123"), "owner"),
            )
        if db.execute("SELECT COUNT(*) FROM faqs").fetchone()[0] == 0:
            db.executemany("INSERT INTO faqs (keywords, answer) VALUES (?,?)", DEFAULT_FAQS)
        db.commit()
        close_db()
