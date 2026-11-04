
import csv
import mysql.connector
from pathlib import Path
from config import DB_CONFIG

# Tables to inspect
TABLES = [
    "roles",
    "requesters",
    "terms",
    "categories",
    "policy_documents",
    "knowledge_articles",
    "tickets",
    "messages",
    "assignments",
    "sla",
    "resolution_feedback",
    "ticket_articles",
    "message_sources",
    "ticket_events",
    "routing_rules",
    "sla_rules"
]

db = None
cursor = None

try:
    # 1. Connect to MySQL
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()

    print("Database connected successfully!")

    # 2. Create dataset folder
    output_folder = Path("dataset")
    output_folder.mkdir(exist_ok=True)

    output_file = output_folder / "database_schema_report.csv"

    # 3. Create CSV report
    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "table_name",
            "column_name",
            "column_type",
            "is_nullable",
            "column_key",
            "column_default",
            "extra"
        ])

        # 4. Inspect table columns
        for table in TABLES:

            cursor.execute("""
                SELECT
                    COLUMN_NAME,
                    COLUMN_TYPE,
                    IS_NULLABLE,
                    COLUMN_KEY,
                    COLUMN_DEFAULT,
                    EXTRA
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (table,))

            columns = cursor.fetchall()

            if not columns:
                print("Table not found:", table)
                continue

            for column in columns:
                writer.writerow([
                    table,
                    *column
                ])

            print(
                table,
                ":",
                len(columns),
                "columns inspected"
            )

        # 5. Inspect foreign keys
        writer.writerow([])
        writer.writerow(["FOREIGN KEY DETAILS"])

        writer.writerow([
            "table_name",
            "column_name",
            "referenced_table",
            "referenced_column"
        ])

        for table in TABLES:

            cursor.execute("""
                SELECT
                    TABLE_NAME,
                    COLUMN_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = %s
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """, (table,))

            foreign_keys = cursor.fetchall()

            for fk in foreign_keys:
                writer.writerow(fk)

    print("\n================================")
    print("SCHEMA REPORT GENERATED!")
    print("================================")
    print("Output file:", output_file)
    print("================================")

except mysql.connector.Error as error:

    print("MySQL Error:", error)

except Exception as error:

    print("Error:", error)

finally:

    if cursor:
        cursor.close()

    if db and db.is_connected():
        db.close()

    print("Database connection closed.")
