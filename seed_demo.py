"""
seed_demo.py  -  Puts sample shop data in the database so the system looks alive for testing and the defence.
Run once with:   python seed_demo.py
(Running it again will not duplicate the data.)
"""
import random
import sqlite3
from datetime import datetime, timedelta

from app import create_app
import database as db

PRODUCTS = [
    ("rice", "ris", 120, 450, 20),
    ("sugar", "sugah", 60, 300, 10),
    ("palm oil", "red oil,paam oil", 40, 800, 8),
    ("onion", "inyin,onions", 80, 100, 15),
    ("groundnut", "grɔndnɔt,groundnuts", 35, 250, 10),
    ("cooking oil", "oil", 6, 900, 8),
    ("tomato paste", "tomato", 50, 150, 10),
]
CUSTOMERS = [("Mariama Kamara", "076123456"), ("Fatmata Sesay", "077234567"), ("Abu Bangura", "078345678"),
             ("Isatu Conteh", "079456789")]

app = create_app()
with app.app_context():
    if db.query("SELECT 1 FROM products LIMIT 1", one=True):
        print("Demo data already exists. Nothing to do.")
    else:
        for n, a, q, p, r in PRODUCTS:
            db.execute("INSERT INTO products (name, aliases, quantity, price, reorder_level) VALUES (?,?,?,?,?)", (n, a, q, p, r))
        for n, ph in CUSTOMERS:
            db.execute("INSERT INTO customers (name, phone) VALUES (?,?)", (n, ph))
        random.seed(10)
        products = db.query("SELECT * FROM products")
        for day in range(6, -1, -1):
            for _ in range(random.randint(3, 6)):
                p = random.choice(products)
                qty = random.randint(1, 5)
                when = (datetime.now() - timedelta(days=day, hours=random.randint(0, 6))).strftime("%Y-%m-%d %H:%M:%S")
                db.execute("INSERT INTO sales (product_id, customer_id, user_id, quantity, unit_price, total, sale_date) "
                           "VALUES (?,?,?,?,?,?,?)", (p["id"], random.randint(1, 4), 1, qty, p["price"], qty * p["price"], when))
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        db.execute("INSERT INTO appointments (customer_id, customer_name, appt_date, appt_time, note, user_id) VALUES (1,'Mariama Kamara',?, '10:30','Bulk rice order',1)", (tomorrow,))
        print("Demo data added: 7 products, 4 customers, a week of sales, 1 appointment.")
