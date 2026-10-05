"""
tests/cases.py - The test cases (input sentence -> what the NLP engine must understand).
Used by test_nlp.py and also copied into Appendix D of the project report.
"""
PRODUCTS = [
    {"name": "rice", "aliases": "ris"},
    {"name": "sugar", "aliases": "sugah"},
    {"name": "palm oil", "aliases": "red oil"},
]

# (id, sentence, expected language, expected intent, expected entities (only the ones we check))
NLP_CASES = [
    ("TC01", "Sold 3 bags of rice to Mariama", "en", "record_sale", {"product": "rice", "quantity": 3, "customer_name": "Mariama"}),
    ("TC02", "sell two palm oil for 500", "en", "record_sale", {"product": "palm oil", "quantity": 2, "price": 500}),
    ("TC03", "I sold twenty five rice", "en", "record_sale", {"product": "rice", "quantity": 25}),
    ("TC04", "add 20 bags of rice at 150", "en", "add_stock", {"product": "rice", "quantity": 20, "price": 150}),
    ("TC05", "restock sugar 30", "en", "add_stock", {"product": "sugar", "quantity": 30}),
    ("TC06", "how many rice do I have", "en", "check_stock", {"product": "rice"}),
    ("TC07", "what is the price of sugar", "en", "check_price", {"product": "sugar"}),
    ("TC08", "show low stock", "en", "low_stock", {}),
    ("TC09", "register customer Fatmata Sesay phone 076 123 456", "en", "register_customer", {"customer_name": "Fatmata Sesay", "phone": "076123456"}),
    ("TC10", "book appointment for Mariama on 2026-10-05 at 3 pm", "en", "schedule_appointment", {"customer_name": "Mariama", "date": "2026-10-05", "time": "15:00"}),
    ("TC11", "schedule appointment with Abu at 10:30 am", "en", "schedule_appointment", {"customer_name": "Abu", "time": "10:30"}),
    ("TC12", "how much did I make today", "en", "daily_summary", {}),
    ("TC13", "what did I sell today", "en", "daily_summary", {}),
    ("TC14", "give me the monthly report", "en", "monthly_report", {}),
    ("TC15", "good morning", "en", "greeting", {}),
    ("TC16", "help", "en", "help", {}),
    ("TC17", "mi don sel tri ris to Fatmata", "kri", "record_sale", {"product": "rice", "quantity": 3, "customer_name": "Fatmata"}),
    ("TC18", "omos ris de lef", "kri", "check_stock", {"product": "rice"}),
    ("TC19", "aw di bodi", "kri", "greeting", {}),
    ("TC20", "pris fɔ sugah", "kri", "check_price", {"product": "sugar"}),
    ("TC21", "mi don sel 2 ris", "kri", "record_sale", {"product": "rice", "quantity": 2}),
    ("TC22", "banana bicycle moon", "en", None, {}),
]
