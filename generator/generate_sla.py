
import mysql.connector
from datetime import timedelta, time
from config import DB_CONFIG


def add_business_minutes(start, minutes):

    current = start
    remaining = int(minutes)

    while remaining > 0:

        if current.weekday() >= 5:
            current = (current + timedelta(days=1)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            continue

        if current.time() < time(9, 0):
            current = current.replace(
                hour=9, minute=0, second=0, microsecond=0
            )

        if current.time() >= time(17, 0):
            current = (current + timedelta(days=1)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            continue

        end_of_day = current.replace(
            hour=17, minute=0, second=0, microsecond=0
        )

        available = int(
            (end_of_day - current).total_seconds() // 60
        )

        if remaining <= available:
            current += timedelta(minutes=remaining)
            remaining = 0
        else:
            remaining -= available
            current = (current + timedelta(days=1)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )

    return current


DEFAULT_RULES = {
    "Low": (480, 2880),
    "Normal": (240, 1440),
    "High": (60, 480),
    "Critical": (15, 240)
}


def main():

    db = None
    cursor = None

    try:
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()

        print("Database connected successfully!")

        cursor.execute("SELECT COUNT(*) FROM sla")
        existing = cursor.fetchone()[0]

        if existing > 0:
            print("SLA records already exist:", existing)
            print("Duplicate generation stopped.")
            return

        cursor.execute("""
            SELECT
                ticket_id,
                category_id,
                priority,
                created_at
            FROM tickets
            ORDER BY ticket_id
        """)

        tickets = cursor.fetchall()

        if not tickets:
            raise Exception("Tickets not found.")

        cursor.execute("""
            SELECT
                category_id,
                priority,
                response_target_minutes,
                resolution_target_minutes,
                business_hours_only
            FROM sla_rules
        """)

        rules = {
            (r[0], r[1]): (r[2], r[3], bool(r[4]))
            for r in cursor.fetchall()
        }

        cursor.execute("""
            SELECT
                ticket_id,
                MIN(created_at)
            FROM messages
            WHERE sender_type IN ('Support', 'Admin')
            GROUP BY ticket_id
        """)

        first_responses = {
            row[0]: row[1]
            for row in cursor.fetchall()
        }

        rows = []

        for ticket_id, category_id, priority, created_at in tickets:

            priority = priority or "Normal"

            rule = rules.get((category_id, priority))

            if rule:
                response_target, resolution_target, business_only = rule
            else:
                response_target, resolution_target = (
                    DEFAULT_RULES.get(priority, DEFAULT_RULES["Normal"])
                )
                business_only = True

            if business_only:
                response_deadline = add_business_minutes(
                    created_at, response_target
                )
                resolution_deadline = add_business_minutes(
                    created_at, resolution_target
                )
            else:
                response_deadline = created_at + timedelta(
                    minutes=response_target
                )
                resolution_deadline = created_at + timedelta(
                    minutes=resolution_target
                )

            first_response = first_responses.get(ticket_id)

            response_breached = (
                first_response is not None
                and first_response > response_deadline
            )

            rows.append((
                f"SLA-{ticket_id}",
                ticket_id,
                response_target,
                resolution_target,
                response_deadline,
                resolution_deadline,
                int(business_only),
                int(response_breached),
                0
            ))

        cursor.executemany("""
            INSERT INTO sla
            (
                sla_id,
                ticket_id,
                response_target_minutes,
                resolution_target_minutes,
                response_deadline,
                resolution_deadline,
                business_hours_only,
                response_breached,
                resolution_breached
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, rows)

        db.commit()

        cursor.execute("SELECT COUNT(*) FROM sla")
        total = cursor.fetchone()[0]

        print("\nSLA GENERATED SUCCESSFULLY!")
        print("New SLA records:", len(rows))
        print("Total SLA records:", total)

    except Exception as error:
        if db and db.is_connected():
            db.rollback()
        print("SLA generation error:", error)

    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()
