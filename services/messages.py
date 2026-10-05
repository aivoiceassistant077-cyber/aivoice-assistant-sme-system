"""
services/messages.py  -  The sentences the assistant speaks back.
English (en) and Krio (kri) are written here. For Mende and Temne the assistant answers in English
until the group adds the translations (see the Beginner Guide).
Krio sentences should be checked by a Krio speaker before the defence.
"""

MESSAGES = {
    "greeting": {
        "en": "Hello! I am your business assistant. You can say: sold 3 bags of rice to Mariama, or: how many rice do I have.",
        "kri": "Kushɛ! A na yu biznɛs asistant. Yu kin se: mi dɔn sel 3 ris to Mariama, ɔ: omos ris de lef.",
    },
    "help": {
        "en": "I can record sales, add stock, check stock and prices, register customers, book appointments, "
              "and give today's or this month's report. Try: sold 2 sugar to Fatmata.",
        "kri": "A kin rayt sel, ad stok, chɛk stok ɛn pris, rɛjista kɔstoma, buk apɔyntmɛnt, ɛn gi tide rapɔt. "
               "Tray: mi dɔn sel 2 sugar to Fatmata.",
    },
    "unknown": {
        "en": "Sorry, I did not understand that. Say 'help' to hear what I can do.",
        "kri": "Sori, a nɔ ɔndastand. Se 'ɛp' fɔ yɛri wetin a kin du.",
    },
    "empty": {
        "en": "I did not hear anything. Please try again.",
        "kri": "A nɔ yɛri natin. Pliz tray igen.",
    },
    "product_missing": {
        "en": "I could not find that product. Please say the product name, for example rice.",
        "kri": "A nɔ ban fɔ fɛn da prɔdukt de. Pliz se di nem, lɛk ris.",
    },
    "product_not_found": {
        "en": "I do not have '{product}' in the shop records.",
        "kri": "A nɔ gɛt '{product}' na di rɛkɔd.",
    },
    "quantity_missing": {
        "en": "How many? Please say the number, for example: sold 3 bags of rice.",
        "kri": "Omos? Pliz se di nɔmba, lɛk: mi dɔn sel 3 ris.",
    },
    "not_enough_stock": {
        "en": "Not enough stock. You only have {have} {product}.",
        "kri": "Stok nɔ inɔf. Yu gɛt jus {have} {product}.",
    },
    "sale_ok": {
        "en": "Done. Sale recorded: {qty} {product} for {total} leones. {left} left in stock.{extra}",
        "kri": "Dɔn. Sel rayt: {qty} {product} fɔ {total} Le. {left} de lef.{extra}",
    },
    "stock_added": {
        "en": "Done. {qty} {product} added. You now have {total} in stock.",
        "kri": "Dɔn. {qty} {product} ad. Naw yu gɛt {total}.",
    },
    "product_created": {
        "en": "New product '{product}' created with {qty} in stock at {price} leones each.",
        "kri": "Nyu prɔdukt '{product}' dɔn mek, {qty} de, Le {price} fɔ wan.",
    },
    "name_missing": {
        "en": "I did not catch the name. Please say it again.",
        "kri": "A nɔ yɛri di nem. Pliz se am igen.",
    },
    "stock_info": {
        "en": "You have {qty} {product} in stock.",
        "kri": "Yu gɛt {qty} {product}.",
    },
    "price_info": {
        "en": "{product} costs {price} leones.",
        "kri": "{product} na Le {price}.",
    },
    "low_stock_none": {
        "en": "All products have enough stock.",
        "kri": "Ɔl di prɔdukt dɛm gɛt inɔf.",
    },
    "low_stock_list": {
        "en": "Low stock: {items}.",
        "kri": "Stok lɔw: {items}.",
    },
    "customer_ok": {
        "en": "Customer {name} registered.",
        "kri": "Kɔstoma {name} dɔn rɛjista.",
    },
    "customer_exists": {
        "en": "{name} is already registered.",
        "kri": "{name} dɔn rɛjista bifo.",
    },
    "date_missing": {
        "en": "Which day? Please say a date, for example: book appointment for Mariama tomorrow at 10:30.",
        "kri": "Wich de? Pliz se di de, lɛk: buk apɔyntmɛnt fɔ Mariama tumara.",
    },
    "appointment_ok": {
        "en": "Appointment booked for {name} on {date}{time}.",
        "kri": "Apɔyntmɛnt buk fɔ {name} na {date}{time}.",
    },
    "appointments_none": {
        "en": "You have no upcoming appointments.",
        "kri": "Yu nɔ gɛt apɔyntmɛnt.",
    },
    "appointments_list": {
        "en": "Upcoming appointments: {items}.",
        "kri": "Apɔyntmɛnt dɛm: {items}.",
    },
    "daily": {
        "en": "Today you made {count} sales worth {total} leones.{top}",
        "kri": "Tide yu mek {count} sel, Le {total}.{top}",
    },
    "monthly": {
        "en": "This month you made {count} sales worth {total} leones.{top}",
        "kri": "Dis mɔnt yu mek {count} sel, Le {total}.{top}",
    },
    "owner_only": {
        "en": "Only the shop owner can ask for the monthly report.",
        "kri": "Na di ona nɔmɔ kin aks fɔ di mɔnt rapɔt.",
    },
}


def say(key, lang="en", **kwargs):
    """Return the sentence in the right language (Mende/Temne fall back to English)."""
    table = MESSAGES.get(key, {})
    text = table.get(lang) or table.get("en", key)
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError):
        return text
