-- schema.sql : SQLite database design for the Multilingual Voice-First AI Business Assistant
-- Tables: users, products, customers, sales, appointments, voice_logs, faqs

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    phone         TEXT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'staff' CHECK (role IN ('owner','staff')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS products (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE COLLATE NOCASE,
    aliases       TEXT NOT NULL DEFAULT '',      -- other names (Krio, Mende, Temne ...) separated by commas
    quantity      INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    price         REAL NOT NULL DEFAULT 0 CHECK (price >= 0),
    reorder_level INTEGER NOT NULL DEFAULT 5,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS customers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    phone      TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sales (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    customer_id INTEGER REFERENCES customers(id),
    user_id     INTEGER REFERENCES users(id),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    unit_price  REAL NOT NULL,
    total       REAL NOT NULL,
    sale_date   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS appointments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id   INTEGER REFERENCES customers(id),
    customer_name TEXT NOT NULL,
    appt_date     TEXT NOT NULL,     -- YYYY-MM-DD
    appt_time     TEXT,              -- HH:MM
    note          TEXT,
    status        TEXT NOT NULL DEFAULT 'scheduled',
    user_id       INTEGER REFERENCES users(id),
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS voice_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER REFERENCES users(id),
    language   TEXT,
    transcript TEXT NOT NULL,
    intent     TEXT,
    response   TEXT,
    success    INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS faqs (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    keywords TEXT NOT NULL,          -- words separated by commas, e.g. "open,hours,time"
    answer   TEXT NOT NULL
);
