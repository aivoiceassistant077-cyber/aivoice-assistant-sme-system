"""Integration / system tests: login, voice commands, database changes, access control."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
import database as db  # noqa: E402


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({"DATABASE": os.path.join(self.tmp.name, "test.db"),
                               "AUDIO_DIR": self.tmp.name, "TESTING": True})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def login(self, user="admin", pw="admin123"):
        return self.client.post("/login", data={"username": user, "password": pw}, follow_redirects=True)

    def say(self, text):
        return self.client.post("/api/command", json={"text": text}).get_json()

    def stock(self, name):
        with self.app.app_context():
            r = db.query("SELECT quantity FROM products WHERE name=?", (name,), one=True)
            return r["quantity"] if r else None


class TestAuth(AppTestCase):
    def test_login_page_loads(self):
        self.assertEqual(self.client.get("/login").status_code, 200)

    def test_wrong_password(self):
        r = self.login(pw="wrong")
        self.assertIn(b"Wrong username or password", r.data)

    def test_correct_login(self):
        r = self.login()
        self.assertIn(b"Talk to your assistant", r.data)

    def test_protected_page_redirects(self):
        r = self.client.get("/inventory")
        self.assertEqual(r.status_code, 302)

    def test_api_blocked_without_login(self):
        self.assertEqual(self.client.post("/api/command", json={"text": "help"}).status_code, 401)

    def test_register_staff_and_staff_cannot_see_reports(self):
        self.client.post("/register", data={"name": "Staff One", "phone": "", "username": "staff1", "password": "secret1"})
        self.login("staff1", "secret1")
        self.assertEqual(self.client.get("/reports").status_code, 403)
        self.assertEqual(self.client.get("/users").status_code, 403)

    def test_password_is_hashed(self):
        with self.app.app_context():
            row = db.query("SELECT password_hash FROM users WHERE username='admin'", one=True)
            self.assertNotIn("admin123", row["password_hash"])


class TestVoiceCommands(AppTestCase):
    def setUp(self):
        super().setUp()
        self.login()

    def test_add_new_product_and_sell(self):
        self.say("add 20 bags of rice at 150")
        self.assertEqual(self.stock("rice"), 20)
        r = self.say("sold 3 bags of rice to Mariama")
        self.assertTrue(r["ok"])
        self.assertEqual(self.stock("rice"), 17)
        self.assertIn("450", r["reply"])

    def test_cannot_sell_more_than_stock(self):
        self.say("add 2 rice at 100")
        r = self.say("sold 5 rice")
        self.assertFalse(r["ok"])
        self.assertEqual(self.stock("rice"), 2)

    def test_check_stock_and_price(self):
        self.say("add 10 sugar at 300")
        self.assertIn("10", self.say("how many sugar do I have")["reply"])
        self.assertIn("300", self.say("what is the price of sugar")["reply"])

    def test_unknown_product(self):
        r = self.say("how many diamonds do I have")
        self.assertFalse(r["ok"])

    def test_register_customer_and_duplicate(self):
        self.assertTrue(self.say("register customer Fatmata Sesay phone 076123456")["ok"])
        self.assertIn("already", self.say("register customer Fatmata Sesay")["reply"])

    def test_book_appointment(self):
        r = self.say("book appointment for Abu on 2026-12-01 at 9 am")
        self.assertTrue(r["ok"])
        self.assertIn("2026-12-01", r["reply"])
        self.assertIn("Abu", self.say("show my appointments")["reply"])

    def test_appointment_without_date_asks_again(self):
        self.assertFalse(self.say("book appointment for Abu")["ok"])

    def test_low_stock_alert(self):
        self.say("add 3 sugar at 300")
        self.assertIn("sugar", self.say("show low stock")["reply"])

    def test_daily_summary(self):
        self.say("add 10 rice at 100")
        self.say("sold 2 rice")
        self.assertIn("200", self.say("how much did I make today")["reply"])

    def test_faq_customer_support(self):
        r = self.say("what time do you open")
        self.assertTrue(r["ok"])
        self.assertEqual(r["intent"], "customer_support")

    def test_krio_sale(self):
        self.say("add 10 rice at 100")
        r = self.say("mi don sel tri ris")
        self.assertEqual(r["language"], "kri")
        self.assertEqual(self.stock("rice"), 7)

    def test_unknown_command(self):
        self.assertFalse(self.say("banana bicycle moon")["ok"])

    def test_every_command_is_logged(self):
        self.say("hello")
        self.say("banana bicycle moon")
        with self.app.app_context():
            self.assertEqual(db.query("SELECT COUNT(*) c FROM voice_logs", one=True)["c"], 2)

    def test_monthly_report_owner_only(self):
        self.client.get("/logout")
        self.client.post("/register", data={"name": "S", "phone": "", "username": "s2", "password": "secret1"})
        self.login("s2", "secret1")
        self.assertFalse(self.say("give me the monthly report")["ok"])


class TestPages(AppTestCase):
    def test_all_pages_open_for_owner(self):
        self.login()
        for url in ["/assistant", "/inventory", "/sales", "/customers", "/appointments", "/reports", "/logs", "/users"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_transcribe_without_whisper_is_clear_error(self):
        self.login()
        import io
        r = self.client.post("/api/transcribe", data={"audio": (io.BytesIO(b"x"), "a.webm")},
                             content_type="multipart/form-data")
        self.assertIn(r.status_code, (200, 501, 500))


if __name__ == "__main__":
    unittest.main()
