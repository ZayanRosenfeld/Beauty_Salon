import os
import sqlite3
import pandas as pd
import unicodedata
from datetime import datetime
import json



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "salon.db")

SERVICE_PRICES = {
    "corte de cabelo": 35,
    "hidratacao": 30,
    "manicure": 55,
    "relaxamento": 50,
    "mega Hair": 150,
    "escova": 30,
    "progressiva": 180,
    "cabelo 100g/55cm": 370,
    "tintura": 50,
    "cauterização": 80,
    "corte": 35,
    "luzes": 160,
    "manutençao mega": 180,

}


def load_data():
    conn = sqlite3.connect(DB_PATH)

    clients = pd.read_sql_query("SELECT * FROM clients", conn)

    appts = pd.read_sql_query(
        """
        SELECT id, client_id, service,
               substr(created_at,1,19) AS created_at
        FROM appointments
        """,
        conn,
        parse_dates=["created_at"]
    )

    conn.close()
    return clients, appts


def save_to_json(rev_df, service_counts, total_revenue):
    output = {
        "services": [],
        "total_revenue": float(total_revenue)
    }

    for _, row in rev_df.iterrows():
        output["services"].append({
            "service": str(row["service"]),
            "count": int(row["count"]),
            "price": float(row["price"]),
            "total_revenue": float(row["total_revenue"])
        })

    output["service_counts"] = {
        str(service): int(count)
        for service, count in service_counts.items()
    }

    # Clients list
    output["clients"] = []

    if "MERGED_CLIENT_DATA" in globals():
        for _, row in MERGED_CLIENT_DATA.iterrows():
            output["clients"].append({
                "id": int(row["id"]),
                "name": row["name"],
                "phone": row["phone"]
            })

    # Add full appointment schedule
    output["appointments"] = []
    if "FULL_APPOINTMENT_DATA" in globals():
        for _, row in FULL_APPOINTMENT_DATA.iterrows():
            output["appointments"].append({
                "id": int(row["id"]),
                "client_id": int(row["client_id"]),
                "client_name": row["name"],
                "service": row["service"],
                "created_at": str(row["created_at"])
            })



    # Force conversion of numpy types → python types
    output = json.loads(json.dumps(output))

    output_path = os.path.join(BASE_DIR, "report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print(f"\nJSON salvo em: {output_path}")



def summary():
    clients, appts = load_data()

    def normalize(text: str):
        text = text.lower().strip()
        text = unicodedata.normalize("NFD", text)
        text = "".join(c for c in text if unicodedata.category(c) != "Mn")
        return text

    appts['service_normalized'] = appts['service'].apply(normalize)

    print("=== Clientes ===")
    total_clients = len(clients)
    print("Total Clientes:", total_clients)
    print(clients.head(total_clients), "\n")
    print("\n=== Agendamentos ===")
    print("Agendamentos totais:", len(appts))
    total_appts = len(appts)
    print(appts.head(total_appts), "\n")

    # Script for counting services as one, grouping them together and counting prices


    if not appts.empty:
        service_quantity = len(appts["service"])

        # Appointments per day (Agendamentos por dia) DO NOT USE, IT DOESN't WORK AS INTENDED
        #appts['date_only'] = appts['created_at'].dt.date
        #counts = appts.groupby('date_only').size()
        #print("\nAgendamentos por dia (ultimos 10 dias):")
        #print(counts.sort_index(ascending=False).head(10))

        print("\n=== Serviços unificados ===")
        service_counts = appts.groupby("service_normalized").size()

        print(service_counts)

        print("\n=== Receita por serviço ===")
        revenue = []

        for service, count in service_counts.items():
            price = SERVICE_PRICES.get(service, 0)
            revenue.append({
                "service": service,
                "count": count,
                "price": price,
                "total_revenue": price * count
            })

        rev_df = pd.DataFrame(revenue)
        print(rev_df)

        print("\nReceita total:", rev_df["total_revenue"].sum())

        # Visits per client (Visitos pelo cliente)
        print("\nTop clientes pelos visitos:")
        merged = appts.merge(clients, left_on='client_id', right_on='id', how='left')
        print(merged['name'].value_counts().head(10))

        # Clients
        global MERGED_CLIENT_DATA
        MERGED_CLIENT_DATA = clients[["id", "name", "phone"]].copy()

        # Appointment
        global FULL_APPOINTMENT_DATA
        created_col = "created_at"
        if "created_at_x" in merged.columns:
            created_col = "created_at_x"
        elif "created_at_y" in merged.columns:
            created_col = "created_at_y"

        FULL_APPOINTMENT_DATA = merged[[
            "id_x",
            "client_id",
            "name",
            "service",
            created_col
        ]].copy()


        # Rename for clean JSON
        FULL_APPOINTMENT_DATA = FULL_APPOINTMENT_DATA.rename(columns={
            "id_x": "id",
            created_col: "created_at"
        })
        FULL_APPOINTMENT_DATA["created_at"] = FULL_APPOINTMENT_DATA["created_at"].astype(str)

        # Save JSON report
        save_to_json(rev_df, service_counts, rev_df["total_revenue"].sum())
    else:
        print("\nNão tem agendamentos — cria alguns primeiro.")

if __name__ == "__main__":
    summary()
# In the name of holy father and son, please work.