"""
nlp/parser.py  -  The "brain" that understands what the user said.

It is a rule-based Natural Language Processing (NLP) engine:
  1. clean the sentence (lower-case, fold special letters such as the Krio  ɔ  and  ɛ),
  2. detect the language (English / Krio / Mende / Temne),
  3. detect the intent (what does the user want?),
  4. extract the entities (product, quantity, price, customer name, phone, date, time).

It does NOT need the internet and it does NOT need a database, so it is easy to test.
"""
import json
import os
import re
import unicodedata
from datetime import date, timedelta

LEX_DIR = os.path.join(os.path.dirname(__file__), "lexicons")
LANG_FILES = {"en": "english.json", "kri": "krio.json", "men": "mende.json", "tem": "temne.json"}
LANG_NAMES = {"en": "English", "kri": "Krio", "men": "Mende", "tem": "Temne"}

# If two intents have the same score, the one earlier in this list wins.
PRIORITY = ["register_customer", "schedule_appointment", "list_appointments", "monthly_report",
            "daily_summary", "low_stock", "check_price", "check_stock", "add_stock",
            "record_sale", "help", "greeting"]

WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
MONTHS = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7,
          "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}
TOMORROW_WORDS = ["tomorrow", "tumara", "tumoro", "tumorow"]
TODAY_WORDS = ["today", "tide", "tuday"]


def fold(text):
    """Lower-case and replace special letters so that 'kɔstoma' == 'kostoma'."""
    text = (text or "").lower()
    text = text.replace("ɔ", "o").replace("ɛ", "e").replace("ŋ", "n")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"(?<=\d),(?=\d{3})", "", text)  # 1,500 -> 1500
    return text


def _phrase_regex(phrase):
    return re.compile(r"(?<![a-z0-9])" + re.escape(fold(phrase)) + r"(?![a-z0-9])")


class Lexicons:
    def __init__(self):
        self.data = {}
        for code, fname in LANG_FILES.items():
            with open(os.path.join(LEX_DIR, fname), encoding="utf-8") as f:
                raw = json.load(f)
            lex = {
                "aliases": {fold(k): fold(v) for k, v in raw.get("product_aliases", {}).items()},
                "intents": {k: [fold(p) for p in v] for k, v in raw.get("intents", {}).items()},
                "stopwords": {fold(w) for w in raw.get("stopwords", [])},
                "numbers": {fold(k): v for k, v in raw.get("number_words", {}).items()},
                "cust": {fold(w) for w in raw.get("customer_markers", [])},
                "price": {fold(w) for w in raw.get("price_markers", [])},
                "phone": {fold(w) for w in raw.get("phone_markers", [])},
            }
            vocab = set(lex["stopwords"]) | set(lex["numbers"]) | lex["cust"] | lex["price"] | lex["phone"]
            for phrases in lex["intents"].values():
                for p in phrases:
                    vocab.update(p.split())
            lex["vocab"] = vocab
            self.data[code] = lex
        for code, lex in self.data.items():
            others = set()
            for c2, l2 in self.data.items():
                if c2 != code:
                    others |= l2["vocab"]
            lex["unique"] = lex["vocab"] - others
        # merged helpers (the assistant understands code-mixed sentences)
        self.stopwords = set().union(*[l["stopwords"] for l in self.data.values()])
        self.numbers = {}
        for l in self.data.values():
            self.numbers.update(l["numbers"])
        self.cust = set().union(*[l["cust"] for l in self.data.values()])
        self.price = set().union(*[l["price"] for l in self.data.values()])
        self.phone = set().union(*[l["phone"] for l in self.data.values()])
        self.builtin_aliases = {}   # built-in local names for common products, e.g. ris -> rice
        for l in self.data.values():
            self.builtin_aliases.update(l["aliases"])


_LEX = None


def lexicons():
    global _LEX
    if _LEX is None:
        _LEX = Lexicons()
    return _LEX


# ----------------------------------------------------------------- language & intent
def detect_intent(folded):
    """Return (intent, matched_phrases, scores)."""
    lex = lexicons()
    scores, matched = {}, {}
    for code, l in lex.data.items():
        for intent, phrases in l["intents"].items():
            for p in phrases:
                if p and _phrase_regex(p).search(folded):
                    scores[intent] = max(scores.get(intent, 0), len(p.split()) + len(p) / 100.0)
                    matched.setdefault(intent, []).append(p)
    if not scores:
        return None, [], scores
    best = sorted(scores, key=lambda i: (-scores[i], PRIORITY.index(i) if i in PRIORITY else 99))[0]
    return best, matched.get(best, []), scores


def detect_language(folded):
    lex = lexicons()
    tokens = set(re.findall(r"[a-z0-9]+", folded))
    best, best_score = "en", 0.0
    results = {}
    for code, l in lex.data.items():
        score = 0.0
        for phrases in l["intents"].values():
            for p in phrases:
                if p and _phrase_regex(p).search(folded):
                    score += len(p.split())
        score += len(tokens & l["unique"])
        results[code] = score
    for code in ("kri", "men", "tem"):          # English wins ties
        if results[code] > best_score and results[code] > results["en"]:
            best, best_score = code, results[code]
    return best


# ----------------------------------------------------------------- numbers
def words_to_numbers(tokens):
    """['twenty','five','rice'] -> ['25','rice']"""
    nums = lexicons().numbers
    out, seq = [], []

    def flush():
        if not seq:
            return
        total, current = 0, 0
        for w in seq:
            v = nums[w]
            if v == 1000:
                total += (current or 1) * 1000
                current = 0
            elif v == 100:
                current = (current or 1) * 100
            else:
                current += v
        out.append(str(total + current))
        seq.clear()

    for t in tokens:
        if t.isdigit():
            flush()
            out.append(t)
        elif t in nums:
            if seq:
                last = nums[seq[-1]]
                v = nums[t]
                can_join = (v in (100, 1000)) or (last >= 100) or (20 <= last < 100 and last % 10 == 0 and v < 10)
                if not can_join:
                    flush()
            seq.append(t)
        else:
            flush()
            out.append(t)
    flush()
    return out


# ----------------------------------------------------------------- entity helpers
def extract_phone(folded):
    m = re.search(r"\+?\d[\d \-]{6,}\d", folded)
    if not m:
        return None, folded
    phone = re.sub(r"[ \-]", "", m.group(0))
    return phone, folded[:m.start()] + " " + folded[m.end():]


def extract_date(folded, today=None):
    """Return (iso_date or None, text_without_date)."""
    today = today or date.today()
    m = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", folded)
    if m:
        try:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return d.isoformat(), folded[:m.start()] + " " + folded[m.end():]
        except ValueError:
            pass
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", folded)
    if m:
        try:
            d = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            return d.isoformat(), folded[:m.start()] + " " + folded[m.end():]
        except ValueError:
            pass
    for w in TOMORROW_WORDS:
        m = re.search(r"(?<![a-z])" + w + r"(?![a-z])", folded)
        if m:
            return (today + timedelta(days=1)).isoformat(), folded[:m.start()] + " " + folded[m.end():]
    for w in TODAY_WORDS:
        m = re.search(r"(?<![a-z])" + w + r"(?![a-z])", folded)
        if m:
            return today.isoformat(), folded[:m.start()] + " " + folded[m.end():]
    m = re.search(r"\b(?:next\s+|on\s+)?(" + "|".join(WEEKDAYS) + r")\b", folded)
    if m:
        target = WEEKDAYS[m.group(1)]
        delta = (target - today.weekday()) % 7
        if delta == 0 or m.group(0).startswith("next"):
            delta = delta or 7
        return (today + timedelta(days=delta)).isoformat(), folded[:m.start()] + " " + folded[m.end():]
    m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(" + "|".join(MONTHS) + r")(?:\s+(\d{4}))?\b", folded)
    if m:
        year = int(m.group(3)) if m.group(3) else today.year
        try:
            d = date(year, MONTHS[m.group(2)], int(m.group(1)))
            if not m.group(3) and d < today:
                d = date(year + 1, d.month, d.day)
            return d.isoformat(), folded[:m.start()] + " " + folded[m.end():]
        except ValueError:
            pass
    return None, folded


def extract_time(folded):
    """Return ('HH:MM' or None, text_without_time)."""
    m = re.search(r"\b(\d{1,2})[:.](\d{2})\s*(am|pm)?\b", folded)
    if m:
        h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    else:
        m = re.search(r"\b(?:at\s+)?(\d{1,2})\s*(am|pm)\b", folded)
        if m:
            h, mi, ap = int(m.group(1)), 0, m.group(2)
        else:
            m = re.search(r"\bat\s+(\d{1,2})\b", folded)
            if not m:
                return None, folded
            h, mi, ap = int(m.group(1)), 0, None
    if ap == "pm" and h < 12:
        h += 12
    if ap == "am" and h == 12:
        h = 0
    if h > 23 or mi > 59:
        return None, folded
    return "%02d:%02d" % (h, mi), folded[:m.start()] + " " + folded[m.end():]


def _singular(word):
    if len(word) > 3 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def match_product(tokens, products):
    """
    Look for a known product (name or alias) inside the token list.
    products = [{'name':..., 'aliases':'a,b'}]. Returns (name, start, end) or None.
    """
    best = None
    sing = [_singular(t) for t in tokens]
    for p in products:
        names = [p["name"]] + [a for a in (p.get("aliases") or "").split(",") if a.strip()]
        names += [a for a, target in lexicons().builtin_aliases.items() if target == fold(p["name"])]
        for n in names:
            ntoks = [_singular(t) for t in re.findall(r"[a-z0-9]+", fold(n))]
            if not ntoks:
                continue
            for i in range(len(tokens) - len(ntoks) + 1):
                if sing[i:i + len(ntoks)] == ntoks:
                    if best is None or len(ntoks) > best[3]:
                        best = (p["name"], i, i + len(ntoks), len(ntoks))
    return best[:3] if best else None


def _title(words):
    return " ".join(w.capitalize() for w in words)


# ----------------------------------------------------------------- main function
def parse(text, products=None, today=None):
    """
    Understand one sentence.
    Returns a dictionary:
      {'text', 'language', 'language_name', 'intent', 'entities': {...}}
    """
    products = products or []
    lex = lexicons()
    folded = fold(text).strip()
    result = {"text": text, "language": "en", "language_name": "English", "intent": None, "entities": {}}
    if not folded:
        return result

    language = detect_language(folded)
    intent, phrases, _ = detect_intent(folded)
    result["language"] = language
    result["language_name"] = LANG_NAMES[language]
    result["intent"] = intent
    ent = result["entities"]

    # remove the intent phrases so they are not mistaken for product / person names
    work = folded
    for p in sorted(phrases, key=len, reverse=True):
        work = _phrase_regex(p).sub(" ", work)

    if intent == "schedule_appointment":
        d, work = extract_date(work, today)
        t, work = extract_time(work)
        ent["date"], ent["time"] = d, t
        toks = words_to_numbers(re.findall(r"[a-z0-9]+", work))
        ignore = lex.stopwords | lex.cust | {"appointment", "with", "customer", "client", "on", "at", "next", "named", "called"}
        # name = words after for/with/to, else all leftover words
        name_tokens, started = [], False
        for t_ in toks:
            if t_ in ("for", "with", "to", "gi", "fo") and not started:
                started = True
                continue
            if started and t_ not in ignore and not t_.isdigit():
                name_tokens.append(t_)
        if not name_tokens:
            name_tokens = [t_ for t_ in toks if t_ not in ignore and not t_.isdigit()]
        ent["customer_name"] = _title(name_tokens[:3]) or None
        return result

    if intent == "register_customer":
        phone, work = extract_phone(work)
        ent["phone"] = phone
        toks = re.findall(r"[a-z0-9]+", work)
        ignore = lex.stopwords | lex.phone | {"customer", "named", "called", "name", "kostoma", "register", "new", "add"}
        name_tokens = [t_ for t_ in toks if t_ not in ignore and not t_.isdigit()]
        ent["customer_name"] = _title(name_tokens[:3]) or None
        return result

    if intent in ("record_sale", "add_stock", "check_stock", "check_price"):
        toks = words_to_numbers(re.findall(r"[a-z0-9]+", work))
        # 1. known product
        found = match_product(toks, products)
        product_name = None
        if found:
            product_name = found[0]
            toks = toks[:found[1]] + ["_P_"] + toks[found[2]:]
        # 2. price (marker + number)
        price = None
        i = 0
        while i < len(toks) - 1:
            if toks[i] in lex.price and toks[i + 1].isdigit() and intent in ("record_sale", "add_stock"):
                price = int(toks[i + 1])
                del toks[i:i + 2]
                break
            i += 1
        # 3. customer (marker + non-number word) for sales
        customer = None
        if intent == "record_sale":
            for i, t_ in enumerate(toks):
                if t_ in lex.cust and i + 1 < len(toks) and not toks[i + 1].isdigit() and toks[i + 1] != "_P_" \
                        and toks[i + 1] not in lex.stopwords:
                    j = i + 1
                    names = []
                    while j < len(toks) and len(names) < 3 and not toks[j].isdigit() and toks[j] != "_P_" \
                            and toks[j] not in lex.stopwords and toks[j] not in lex.price:
                        names.append(toks[j])
                        j += 1
                    customer = _title(names)
                    del toks[i:j]
                    break
        # 4. quantity = first number left; if a lone number remains after add_stock without price marker
        quantity = None
        for i, t_ in enumerate(toks):
            if t_.isdigit():
                quantity = int(t_)
                del toks[i]
                break
        # a second number in add_stock is taken as the price ("add rice 20 150")
        if price is None and intent == "add_stock":
            for i, t_ in enumerate(toks):
                if t_.isdigit():
                    price = int(t_)
                    del toks[i]
                    break
        # 5. unknown product -> guess the name from the left-over words
        if product_name is None:
            ignore = lex.stopwords | lex.cust | lex.price | {"_p_", "product", "item", "new"}
            guess = [t_ for t_ in toks if t_ not in ignore and not t_.isdigit() and t_ != "_P_"]
            if guess:
                product_name = " ".join(_singular(g) if k == len(guess[:3]) - 1 else g for k, g in enumerate(guess[:3]))
            result["entities"]["product_known"] = False
        else:
            result["entities"]["product_known"] = True
        ent.update({"product": product_name, "quantity": quantity, "price": price, "customer_name": customer})
        return result

    if intent in ("low_stock", "daily_summary", "monthly_report", "list_appointments", "greeting", "help"):
        return result

    return result  # intent None -> maybe a FAQ question (handled in business.py)
