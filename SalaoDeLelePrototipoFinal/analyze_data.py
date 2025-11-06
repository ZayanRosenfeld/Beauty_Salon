# analyze_data.py
import os
import sqlite3
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "salon.db")

def load_data():
    conn = sqlite3.connect(DB_PATH)
    clients = pd.read_sql_query("SELECT * FROM clients", conn, parse_dates=["created_at"])
    appts = pd.read_sql_query("SELECT * FROM appointments", conn, parse_dates=["created_at"])
    conn.close()
    return clients, appts

def summary():
    clients, appts = load_data()
    print("=== CLIENTS ===")
    print(clients.head(), "\n")
    print("Total clients:", len(clients))
    print("\n=== APPOINTMENTS ===")
    print(appts.head(), "\n")
    print("Total appointments:", len(appts))

    if not appts.empty:
        print("\nTop services:")
        print(appts['service'].value_counts().head(10))

        # Appointments per day (Agendamentos por dia)
        appts['date_only'] = appts['created_at'].dt.date
        counts = appts.groupby('date_only').size()
        print("\nAppointments per day (last 10 days):")
        print(counts.sort_index(ascending=False).head(10))

        # Visits per client (Visitos pelo cliente)
        print("\nTop clients by visits:")
        merged = appts.merge(clients, left_on='client_id', right_on='id', how='left')
        print(merged['name'].value_counts().head(10))
    else:
        print("\nNo appointments yet — create some appointments first.")

if __name__ == "__main__":
    summary()

# In the name of holy father and son, please work.