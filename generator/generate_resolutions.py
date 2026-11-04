
import random
import mysql.connector
from datetime import timedelta, datetime
from config import DB_CONFIG, SEED

rng = random.Random(SEED + 4)

RESOLUTIONS = {
    "Financial Aid":
        "The financial aid request was reviewed and relevant process guidance was provided.",

    "Registration":
        "The registration request was reviewed and registration guidance was provided.",

    "IT":
        "The technical support request was reviewed and troubleshooting guidance was provided.",

    "Accessibility":
        "The accessibility request was reviewed and the appropriate support process was explained."
}


def main():

    db = None
    cursor = None

    try:
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()

        print("Database connected successfully!")

        # Create Resolution Feedback table if it does not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_feedback (
                feedback_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                ticket_id VARCHAR(30) NOT NULL UNIQUE,
                resolution_text TEXT NOT NULL,
                resolved_at DATETIME NOT NULL,
                rating TINYINT NULL,
                feedback_text TEXT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT fk_resolution_ticket
                FOREIGN KEY (ticket_id)
                REFERENCES tickets(ticket_id)
            )
        """)

        cursor.execute("""
            SELECT COUNT(*) FROM ticket_events
        """)
        existing_events = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM resolution_feedback
        """)
        existing_feedback = cursor.fetchone()[0]

        if existing_events > 0 or existing_feedback > 0:
            print("Resolution or event records already exist.")
            print("Duplicate generation stopped.")
            return

        cursor.execute("""
            SELECT
                t.ticket_id,
                t.created_at,
                c.category_name
            FROM tickets t
            JOIN categories c
                ON c.category_id = t.category_id
            ORDER BY t.ticket_id
        """)

        tickets = cursor.fetchall()

        if not tickets:
            raise Exception("Tickets not found.")

        cursor.execute("""
            SELECT requester_id
            FROM requesters
            WHERE role_id IN (
                SELECT role_id
                FROM roles
                WHERE role_name = 'Support Staff'
            )
        """)

        support_ids = [row[0] for row in cursor.fetchall()]

        feedback_rows = []
        event_rows = []
        ticket_updates = []

        now = datetime.now()

        for index, (ticket_id, created_at, category_name) in enumerate(
            tickets, start=1
        ):

            bucket = index % 10

            if bucket <= 6:
                status = "Resolved"
            elif bucket == 7:
                status = "In Progress"
            elif bucket == 8:
                status = "Waiting"
            else:
                status = "Escalated"

            proposed_time = created_at + timedelta(
                hours=rng.randint(2, 48)
            )

            event_time = min(proposed_time, now)

            if status == "Resolved":

                resolution_text = RESOLUTIONS.get(
                    category_name,
                    "The support request was reviewed."
                )

                feedback_rows.append((
                    ticket_id,
                    resolution_text,
                    event_time,
                    rng.randint(3, 5),
                    "Support experience recorded."
                ))

            actor_id = (
                rng.choice(support_ids)
                if support_ids else None
            )

            ticket_updates.append((status, ticket_id))

            event_rows.append((
                ticket_id,
                "Status Changed",
                "Open",
                status,
                f"Ticket status changed from Open to {status}.",
                actor_id,
                event_time
            ))

        # Insert resolution feedback
        if feedback_rows:
            cursor.executemany("""
                INSERT INTO resolution_feedback
                (
                    ticket_id,
                    resolution_text,
                    resolved_at,
                    rating,
                    feedback_text
                )
                VALUES (%s, %s, %s, %s, %s)
            """, feedback_rows)

        # Update ticket statuses
        cursor.executemany("""
            UPDATE tickets
            SET status = %s
            WHERE ticket_id = %s
        """, ticket_updates)

        # Insert ticket history events
        cursor.executemany("""
            INSERT INTO ticket_events
            (
                ticket_id,
                event_type,
                old_value,
                new_value,
                event_description,
                actor_id,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, event_rows)

        # Update resolution breach flags
        for ticket_id, resolution_text, resolved_at, rating, feedback in feedback_rows:

            cursor.execute("""
                SELECT resolution_deadline
                FROM sla
                WHERE ticket_id = %s
            """, (ticket_id,))

            sla_result = cursor.fetchone()

            if sla_result:
                breached = int(resolved_at > sla_result[0])

                cursor.execute("""
                    UPDATE sla
                    SET resolution_breached = %s
                    WHERE ticket_id = %s
                """, (breached, ticket_id))

        db.commit()

        cursor.execute("SELECT COUNT(*) FROM resolution_feedback")
        feedback_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ticket_events")
        event_count = cursor.fetchone()[0]

        print("\nRESOLUTION GENERATION SUCCESSFUL!")
        print("Resolution feedback:", feedback_count)
        print("Ticket events:", event_count)

    except Exception as error:
        if db and db.is_connected():
            db.rollback()
        print("Resolution generation error:", error)

    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()
