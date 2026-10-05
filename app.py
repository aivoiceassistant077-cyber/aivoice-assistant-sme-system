"""
app.py  -  The main file. It starts the web server (Flask) and connects every part together.

Run it with:    python app.py
Then open:      http://127.0.0.1:5000
"""
import os
from functools import wraps

from flask import (Flask, abort, flash, g, jsonify, redirect, render_template, request,
                   send_file, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

import database as db
from config import Config
from services import business, speech_service, tts_service


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    os.makedirs(app.config["AUDIO_DIR"], exist_ok=True)
    app.teardown_appcontext(db.close_db)
    db.init_db(app)

    # ------------------------------------------------------------ helpers
    @app.before_request
    def load_user():
        uid = session.get("user_id")
        g.user = db.query("SELECT * FROM users WHERE id=?", (uid,), one=True) if uid else None

    @app.context_processor
    def inject_globals():
        return {"business_name": app.config["BUSINESS_NAME"], "currency": app.config["CURRENCY_SYMBOL"]}

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                if request.path.startswith("/api/"):
                    return jsonify({"ok": False, "reply": "Please log in first."}), 401
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def owner_required(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user["role"] != "owner":
                abort(403)
            return view(*args, **kwargs)
        return wrapped

    # ------------------------------------------------------------ authentication
    @app.route("/")
    def home():
        return redirect(url_for("assistant") if g.user else url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = db.query("SELECT * FROM users WHERE username=?", (username,), one=True)
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                return redirect(url_for("assistant"))
            flash("Wrong username or password.", "error")
        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not name or not username or len(password) < 6:
                flash("Please fill every box. The password must have at least 6 characters.", "error")
            elif db.query("SELECT id FROM users WHERE username=?", (username,), one=True):
                flash("That username is already taken.", "error")
            else:
                db.execute("INSERT INTO users (name, phone, username, password_hash, role) VALUES (?,?,?,?, 'staff')",
                           (name, phone, username, generate_password_hash(password)))
                flash("Account created. You can log in now.", "success")
                return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ------------------------------------------------------------ the assistant page + API
    @app.route("/assistant")
    @login_required
    def assistant():
        return render_template("assistant.html")

    @app.route("/api/status")
    @login_required
    def api_status():
        return jsonify({"whisper": speech_service.is_available(), "coqui": tts_service.is_available()})

    @app.route("/api/command", methods=["POST"])
    @login_required
    def api_command():
        data = request.get_json(silent=True) or {}
        return jsonify(business.handle_command(data.get("text", ""), g.user))

    @app.route("/api/transcribe", methods=["POST"])
    @login_required
    def api_transcribe():
        f = request.files.get("audio")
        if f is None:
            return jsonify({"ok": False, "error": "No audio received."}), 400
        if not speech_service.is_available():
            return jsonify({"ok": False, "error": "whisper_not_installed"}), 501
        path = os.path.join(app.config["AUDIO_DIR"], "input_%s.webm" % os.urandom(4).hex())
        f.save(path)
        try:
            lang = request.form.get("language") or None
            if lang in ("auto", "", "kri", "men", "tem"):
                lang = "en" if lang == "kri" else None
            text = speech_service.transcribe(path, app.config["WHISPER_MODEL"], lang)
            return jsonify({"ok": True, "text": text})
        except Exception as exc:  # noqa
            return jsonify({"ok": False, "error": str(exc)}), 500
        finally:
            if os.path.exists(path):
                os.remove(path)

    @app.route("/api/tts", methods=["POST"])
    @login_required
    def api_tts():
        if not tts_service.is_available():
            return jsonify({"ok": False, "error": "coqui_not_installed"}), 501
        text = (request.get_json(silent=True) or {}).get("text", "")
        try:
            path = tts_service.synthesize(text, app.config["AUDIO_DIR"], app.config["TTS_MODEL"])
            return send_file(path, mimetype="audio/wav")
        except Exception as exc:  # noqa
            return jsonify({"ok": False, "error": str(exc)}), 500

    # ------------------------------------------------------------ inventory
    @app.route("/inventory", methods=["GET", "POST"])
    @login_required
    def inventory():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            try:
                qty = int(request.form.get("quantity", 0))
                price = float(request.form.get("price", 0))
                level = int(request.form.get("reorder_level", 5))
            except ValueError:
                flash("Quantity, price and reorder level must be numbers.", "error")
                return redirect(url_for("inventory"))
            aliases = request.form.get("aliases", "").strip()
            if not name or qty < 0 or price < 0:
                flash("Please give a product name and valid numbers.", "error")
            elif db.query("SELECT id FROM products WHERE lower(name)=lower(?)", (name,), one=True):
                flash("That product already exists. Use the voice command 'add 10 %s' to add stock." % name, "error")
            else:
                db.execute("INSERT INTO products (name, aliases, quantity, price, reorder_level) VALUES (?,?,?,?,?)",
                           (name, aliases, qty, price, level))
                flash("Product added.", "success")
            return redirect(url_for("inventory"))
        rows = db.query("SELECT * FROM products ORDER BY name")
        return render_template("inventory.html", products=rows)

    @app.route("/inventory/delete/<int:pid>", methods=["POST"])
    @owner_required
    def delete_product(pid):
        if db.query("SELECT 1 FROM sales WHERE product_id=?", (pid,), one=True):
            flash("This product has sales records and cannot be deleted.", "error")
        else:
            db.execute("DELETE FROM products WHERE id=?", (pid,))
            flash("Product deleted.", "success")
        return redirect(url_for("inventory"))

    # ------------------------------------------------------------ customers
    @app.route("/customers", methods=["GET", "POST"])
    @login_required
    def customers():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            if not name:
                flash("Please type the customer name.", "error")
            else:
                db.execute("INSERT INTO customers (name, phone) VALUES (?,?)", (name, phone))
                flash("Customer registered.", "success")
            return redirect(url_for("customers"))
        return render_template("customers.html", customers=db.query("SELECT * FROM customers ORDER BY name"))

    # ------------------------------------------------------------ sales
    @app.route("/sales")
    @login_required
    def sales():
        rows = db.query(
            "SELECT s.*, p.name product, c.name customer FROM sales s "
            "JOIN products p ON p.id=s.product_id LEFT JOIN customers c ON c.id=s.customer_id "
            "ORDER BY s.id DESC LIMIT 100")
        return render_template("sales.html", sales=rows)

    # ------------------------------------------------------------ appointments
    @app.route("/appointments", methods=["GET", "POST"])
    @login_required
    def appointments():
        if request.method == "POST":
            name = request.form.get("customer_name", "").strip()
            day = request.form.get("appt_date", "")
            time_ = request.form.get("appt_time", "")
            note = request.form.get("note", "").strip()
            if not name or not day:
                flash("Please give the customer name and the date.", "error")
            else:
                cust = db.query("SELECT id FROM customers WHERE lower(name)=lower(?)", (name,), one=True)
                cid = cust["id"] if cust else db.execute("INSERT INTO customers (name) VALUES (?)", (name,))
                db.execute("INSERT INTO appointments (customer_id, customer_name, appt_date, appt_time, note, user_id) "
                           "VALUES (?,?,?,?,?,?)", (cid, name, day, time_ or None, note, g.user["id"]))
                flash("Appointment saved.", "success")
            return redirect(url_for("appointments"))
        rows = db.query("SELECT * FROM appointments ORDER BY appt_date DESC, appt_time DESC")
        return render_template("appointments.html", appointments=rows)

    @app.route("/appointments/<int:aid>/done", methods=["POST"])
    @login_required
    def appointment_done(aid):
        db.execute("UPDATE appointments SET status='completed' WHERE id=?", (aid,))
        return redirect(url_for("appointments"))

    # ------------------------------------------------------------ reports (owner only)
    @app.route("/reports")
    @owner_required
    def reports():
        today = db.query("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM sales "
                         "WHERE date(sale_date)=date('now','localtime')", one=True)
        month = db.query("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM sales "
                         "WHERE strftime('%Y-%m',sale_date)=strftime('%Y-%m','now','localtime')", one=True)
        top = db.query("SELECT p.name, SUM(s.quantity) qty, SUM(s.total) revenue FROM sales s "
                       "JOIN products p ON p.id=s.product_id GROUP BY p.name ORDER BY revenue DESC LIMIT 5")
        last7 = db.query("SELECT date(sale_date) d, SUM(total) t FROM sales "
                         "WHERE date(sale_date) >= date('now','localtime','-6 days') GROUP BY date(sale_date) ORDER BY d")
        low = db.query("SELECT * FROM products WHERE quantity <= reorder_level ORDER BY quantity")
        biggest = max([r["t"] for r in last7], default=0) or 1
        return render_template("reports.html", today=today, month=month, top=top, last7=last7, low=low, biggest=biggest)

    @app.route("/logs")
    @login_required
    def logs():
        rows = db.query("SELECT v.*, u.username FROM voice_logs v LEFT JOIN users u ON u.id=v.user_id "
                        "ORDER BY v.id DESC LIMIT 100")
        return render_template("logs.html", logs=rows)

    @app.route("/users")
    @owner_required
    def users():
        return render_template("users.html", users=db.query("SELECT * FROM users ORDER BY id"))

    @app.errorhandler(403)
    def forbidden(_):
        return render_template("message.html", title="Not allowed",
                               text="Only the shop owner can open this page."), 403

    return app


if __name__ == "__main__":
    create_app().run(host=os.environ.get("HOST", "127.0.0.1"), port=5000, debug=True)
