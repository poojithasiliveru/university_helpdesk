
import random
import mysql.connector
from datetime import timedelta
from config import DB_CONFIG, SEED

rng = random.Random(SEED + 2)


def main():
    db = None
    cursor = None

    try:
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()

        print("Database connected successfully!")

        cursor.execute("SELECT COUNT(*) FROM assignments")
        existing = cursor.fetchone()[0]

        if existing > 0:
            print("Assignments already exist:", existing)
            print("Duplicate generation stopped.")
            return

        cursor.execute("""
            SELECT
                t.ticket_id,
                t.created_at,
                c.authorized_team,
                c.category_name
            FROM tickets t
            JOIN categories c
                ON c.category_id = t.category_id
            ORDER BY t.ticket_id
        """)

        tickets = cursor.fetchall()

        if not tickets:
            raise Exception("Tickets not found. Generate tickets first.")

        cursor.execute("""
            SELECT r.requester_id
            FROM requesters r
            JOIN roles ro ON ro.role_id = r.role_id
            WHERE ro.role_name = 'Support Staff'
            ORDER BY r.requester_id
        """)

        support_ids = [row[0] for row in cursor.fetchall()]

        rows = []

        for ticket_id, created_at, team, category_name in tickets:

            assigned_to = (
                rng.choice(support_ids)
                if support_ids else None
            )

            assigned_at = created_at + timedelta(
                minutes=rng.randint(2, 45)
            )

            reason = (
                f"Assigned to {team} based on "
                f"{category_name} category."
            )

            rows.append((
                ticket_id,
                team,
                assigned_to,
                assigned_at,
                reason,
                "Active"
            ))

        cursor.executemany("""
            INSERT INTO assignments
            (
                ticket_id,
                assigned_team,
                assigned_to,
                assigned_at,
                assignment_reason,
                assignment_status
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, rows)

        db.commit()

        cursor.execute("SELECT COUNT(*) FROM assignments")
        total = cursor.fetchone()[0]

        print("\nASSIGNMENTS GENERATED SUCCESSFULLY!")
        print("New assignments:", len(rows))
        print("Total assignments:", total)

    except Exception as error:
        if db and db.is_connected():
            db.rollback()
        print("Assignment generation error:", error)

    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()
