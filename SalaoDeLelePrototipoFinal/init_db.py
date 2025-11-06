# init_db.py
import os
import sqlite3
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "salon.db")

# Connect to the database (creates if not exists)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Recreate the tables (reset all data on second use)
# POR FAVOR SABE QUE ISSO VAI LIMPAR TODOS OS DADOS, SEJA CUIDADO.
cursor.executescript("""
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS clients;

CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    total_visits INTEGER DEFAULT 0
);

CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    service TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (client_id) REFERENCES clients (id)
);
""")

# /// Insert sample clients ///
clients = [
    ("Thais", "11998765432"),
    ("Zayan", "11991234567"),
    ("Ramon", "21987654321"),
    ("Lucas", "31976543210"),
]

cursor.executemany("INSERT INTO clients (name, phone) VALUES (?, ?);", clients)

# /// Insert sample appointments ///
appointments = [
    (1, "Corte de cabelo", datetime.utcnow() - timedelta(days=3)),
    (1, "Hidratação", datetime.utcnow() - timedelta(days=1)),
    (2, "Corte de cabelo", datetime.utcnow() - timedelta(days=2)),
    (3, "Manicure", datetime.utcnow()),
]

cursor.executemany(
    "INSERT INTO appointments (client_id, service, created_at) VALUES (?, ?, ?);",
    [(a[0], a[1], a[2].strftime("%Y-%m-%d %H:%M:%S")) for a in appointments]
)

# /// Update total visits for each client ///
cursor.execute("UPDATE clients SET total_visits = (SELECT COUNT(*) FROM appointments WHERE appointments.client_id = clients.id);")

conn.commit()
conn.close()

print("Database initialized")
