-- schema_mysql.sql : the SAME database design written for MySQL.
-- Open this file in MySQL Workbench and press the lightning (Execute) button.
-- The running prototype uses SQLite (simple and works offline).
-- This file shows the central MySQL version used for larger deployments.

CREATE DATABASE IF NOT EXISTS voice_assistant_sme CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE voice_assistant_sme;

CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    phone         VARCHAR(20),
    username      VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('owner','staff') NOT NULL DEFAULT 'staff',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE,
    aliases       VARCHAR(255) NOT NULL DEFAULT '',
    quantity      INT NOT NULL DEFAULT 0,
    price         DECIMAL(12,2) NOT NULL DEFAULT 0,
    reorder_level INT NOT NULL DEFAULT 5,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (quantity >= 0), CHECK (price >= 0)
);

CREATE TABLE IF NOT EXISTS customers (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    phone      VARCHAR(20),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    product_id  INT NOT NULL,
    customer_id INT NULL,
    user_id     INT NULL,
    quantity    INT NOT NULL,
    unit_price  DECIMAL(12,2) NOT NULL,
    total       DECIMAL(12,2) NOT NULL,
    sale_date   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id)  REFERENCES products(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (user_id)     REFERENCES users(id),
    CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS appointments (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    customer_id   INT NULL,
    customer_name VARCHAR(100) NOT NULL,
    appt_date     DATE NOT NULL,
    appt_time     TIME NULL,
    note          VARCHAR(255),
    status        VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    user_id       INT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (user_id)     REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS voice_logs (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NULL,
    language   VARCHAR(20),
    transcript TEXT NOT NULL,
    intent     VARCHAR(50),
    response   TEXT,
    success    TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS faqs (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    keywords VARCHAR(255) NOT NULL,
    answer   TEXT NOT NULL
);
