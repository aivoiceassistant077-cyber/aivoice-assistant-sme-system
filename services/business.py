"""
services/business.py  -  The "business logic layer".
It takes what the NLP engine understood and performs the real action in the database.
"""
from datetime import date

import database as db
from nlp.parser import parse
from services.messages import say


def _fmt(n):
    n = float(n)
    return "{:,.0f}".format(n) if n == int(n) else "{:,.2f}".format(n)


def _get_product(name):
    if not name:
        return None
    rows = db.query("SELECT * FROM products")
    low = name.lower()
    for r in rows:
        if r["name"].lower() == low:
            return r
    return None


def _find_customer(name):
    if not name:
        return None
    return db.query("SELECT * FROM customers WHERE lower(name)=lower(?)", (name,), one=True)


def get_products_for_parser():
    return [{"name": r["name"], "aliases": r["aliases"]} for r in db.query("SELECT name, aliases FROM products")]


def answer_faq(text):
    folded = text.lower()
    best, best_hits = None, 0
    for row in db.query("SELECT * FROM faqs"):
        hits = sum(1 for k in row["keywords"].split(",") if k.strip() and k.strip() in folded)
        if hits > best_hits:
            best, best_hits = row, hits
    return best["answer"] if best else None


# ---------------------------------------------------------------- the actions
def record_sale(ent, lang, user):
    prod = _get_product(ent.get("product"))
    if not ent.get("product"):
        return False, say("product_missing", lang)
    if prod is None:
        return False, say("product_not_found", lang, product=ent["product"])
    qty = ent.get("quantity")
    if not qty or qty <= 0:
        return False, say("quantity_missing", lang)
    if prod["quantity"] < qty:
        return False, say("not_enough_stock", lang, have=prod["quantity"], product=prod["name"])
    unit = ent.get("price") if ent.get("price") else prod["price"]
    total = unit * qty
    customer_id, extra = None, ""
    if ent.get("customer_name"):
        cust = _find_customer(ent["customer_name"])
        if cust is None:
            customer_id = db.execute("INSERT INTO customers (name) VALUES (?)", (ent["customer_name"],))
        else:
            customer_id = cust["id"]
        extra = " Customer: %s." % ent["customer_name"]
    db.execute("INSERT INTO sales (product_id, customer_id, user_id, quantity, unit_price, total) VALUES (?,?,?,?,?,?)",
               (prod["id"], customer_id, user["id"], qty, unit, total))
    db.execute("UPDATE products SET quantity = quantity - ? WHERE id=?", (qty, prod["id"]))
    left = prod["quantity"] - qty
    msg = say("sale_ok", lang, qty=qty, product=prod["name"], total=_fmt(total), left=left, extra=extra)
    if left <= prod["reorder_level"]:
        msg += " Warning: %s is running low." % prod["name"]
    return True, msg


def add_stock(ent, lang, user):
    name = ent.get("product")
    qty = ent.get("quantity")
    if not name:
        return False, say("product_missing", lang)
    if not qty or qty <= 0:
        return False, say("quantity_missing", lang)
    prod = _get_product(name)
    if prod:
        if ent.get("price"):
            db.execute("UPDATE products SET price=? WHERE id=?", (ent["price"], prod["id"]))
        db.execute("UPDATE products SET quantity = quantity + ? WHERE id=?", (qty, prod["id"]))
        return True, say("stock_added", lang, qty=qty, product=prod["name"], total=prod["quantity"] + qty)
    price = ent.get("price") or 0
    db.execute("INSERT INTO products (name, quantity, price) VALUES (?,?,?)", (name, qty, price))
    return True, say("product_created", lang, product=name, qty=qty, price=_fmt(price))


def check_stock(ent, lang, user):
    prod = _get_product(ent.get("product"))
    if not ent.get("product"):
        return False, say("product_missing", lang)
    if prod is None:
        return False, say("product_not_found", lang, product=ent["product"])
    return True, say("stock_info", lang, qty=prod["quantity"], product=prod["name"])


def check_price(ent, lang, user):
    prod = _get_product(ent.get("product"))
    if not ent.get("product"):
        return False, say("product_missing", lang)
    if prod is None:
        return False, say("product_not_found", lang, product=ent["product"])
    return True, say("price_info", lang, product=prod["name"], price=_fmt(prod["price"]))


def low_stock(ent, lang, user):
    rows = db.query("SELECT name, quantity FROM products WHERE quantity <= reorder_level ORDER BY quantity")
    if not rows:
        return True, say("low_stock_none", lang)
    items = ", ".join("%s (%s)" % (r["name"], r["quantity"]) for r in rows)
    return True, say("low_stock_list", lang, items=items)


def register_customer(ent, lang, user):
    name = ent.get("customer_name")
    if not name:
        return False, say("name_missing", lang)
    if _find_customer(name):
        return True, say("customer_exists", lang, name=name)
    db.execute("INSERT INTO customers (name, phone) VALUES (?,?)", (name, ent.get("phone")))
    return True, say("customer_ok", lang, name=name)


def schedule_appointment(ent, lang, user):
    name = ent.get("customer_name")
    if not name:
        return False, say("name_missing", lang)
    if not ent.get("date"):
        return False, say("date_missing", lang)
    cust = _find_customer(name)
    cid = cust["id"] if cust else db.execute("INSERT INTO customers (name) VALUES (?)", (name,))
    db.execute("INSERT INTO appointments (customer_id, customer_name, appt_date, appt_time, user_id) VALUES (?,?,?,?,?)",
               (cid, name, ent["date"], ent.get("time"), user["id"]))
    time_txt = (" at " + ent["time"]) if ent.get("time") else ""
    return True, say("appointment_ok", lang, name=name, date=ent["date"], time=time_txt)


def list_appointments(ent, lang, user):
    rows = db.query("SELECT * FROM appointments WHERE appt_date >= ? AND status='scheduled' "
                    "ORDER BY appt_date, appt_time LIMIT 5", (date.today().isoformat(),))
    if not rows:
        return True, say("appointments_none", lang)
    items = "; ".join("%s on %s%s" % (r["customer_name"], r["appt_date"], (" " + r["appt_time"]) if r["appt_time"] else "")
                      for r in rows)
    return True, say("appointments_list", lang, items=items)


def _summary(where_sql, args):
    row = db.query("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM sales WHERE " + where_sql, args, one=True)
    top = db.query("SELECT p.name, SUM(s.quantity) q FROM sales s JOIN products p ON p.id=s.product_id "
                   "WHERE " + where_sql.replace("sale_date", "s.sale_date") +
                   " GROUP BY p.name ORDER BY q DESC LIMIT 1", args, one=True)
    top_txt = (" Best seller: %s (%s sold)." % (top["name"], top["q"])) if top else ""
    return row["c"], row["t"], top_txt


def daily_summary(ent, lang, user):
    c, t, top = _summary("date(sale_date) = date('now','localtime')", ())
    return True, say("daily", lang, count=c, total=_fmt(t), top=top)


def monthly_report(ent, lang, user):
    if user["role"] != "owner":
        return False, say("owner_only", lang)
    c, t, top = _summary("strftime('%Y-%m', sale_date) = strftime('%Y-%m','now','localtime')", ())
    return True, say("monthly", lang, count=c, total=_fmt(t), top=top)


def greeting(ent, lang, user):
    return True, say("greeting", lang)


def help_(ent, lang, user):
    return True, say("help", lang)


ACTIONS = {
    "record_sale": record_sale, "add_stock": add_stock, "check_stock": check_stock,
    "check_price": check_price, "low_stock": low_stock, "register_customer": register_customer,
    "schedule_appointment": schedule_appointment, "list_appointments": list_appointments,
    "daily_summary": daily_summary, "monthly_report": monthly_report,
    "greeting": greeting, "help": help_,
}


def handle_command(text, user):
    """
    The full pipeline for one command:
    text -> NLP -> action -> reply, and everything is saved in the voice_logs table.
    """
    text = (text or "").strip()
    if not text:
        return {"ok": False, "intent": None, "language": "en", "language_name": "English",
                "reply": say("empty", "en"), "transcript": ""}
    parsed = parse(text, get_products_for_parser())
    lang = parsed["language"]
    intent = parsed["intent"]
    if intent in ACTIONS:
        ok, reply = ACTIONS[intent](parsed["entities"], lang, user)
    else:
        faq = answer_faq(text)
        if faq:
            ok, reply, intent = True, faq, "customer_support"
        else:
            ok, reply = False, say("unknown", lang)
    db.execute("INSERT INTO voice_logs (user_id, language, transcript, intent, response, success) VALUES (?,?,?,?,?,?)",
               (user["id"], parsed["language_name"], text, intent, reply, 1 if ok else 0))
    return {"ok": ok, "intent": intent, "language": lang, "language_name": parsed["language_name"],
            "reply": reply, "transcript": text, "entities": parsed["entities"]}
