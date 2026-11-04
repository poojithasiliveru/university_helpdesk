
import os
import json
import pandas as pd
import mysql.connector
from config import DB_CONFIG

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_DIR = os.path.join(BASE_DIR, "dataset", "exports")

os.makedirs(EXPORT_DIR, exist_ok=True)

TABLES = [
    "requesters",
    "roles",
    "categories",
    "terms",
    "policy_documents",
    "knowledge_articles",
    "tickets",
    "messages",
    "assignments",
    "sla",
    "ticket_events",
    "resolution_feedback",
    "anomaly_labels"
]

db = mysql.connector.connect(**DB_CONFIG)

try:
    for table in TABLES:
        print(f"Exporting {table}...")

        df = pd.read_sql(f"SELECT * FROM `{table}`", db)

        csv_path = os.path.join(EXPORT_DIR, f"{table}.csv")
        json_path = os.path.join(EXPORT_DIR, f"{table}.json")

        df.to_csv(csv_path, index=False)

        records = json.loads(
            df.to_json(orient="records", date_format="iso")
        )

        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=4, ensure_ascii=False)

        print(f"Completed: {table} ({len(df)} rows)")

    print("\nAll CSV and JSON exports completed!")

except Exception as e:
    print("Export error:", e)

finally:
    db.close()
    print("Database connection closed.")
