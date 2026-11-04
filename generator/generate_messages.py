
import random
import mysql.connector
from datetime import timedelta
from config import DB_CONFIG, SEED, NUM_MESSAGES

rng = random.Random(SEED + 1)

STUDENT_TEXTS = [
    "Hello, I need assistance with my request. Could you please guide me?",
    "I am sharing additional information about my issue.",
    "Thank you for your response. Please let me know the next steps."
]

SUPPORT_TEXTS = [
    "Thank you for contacting the university support team. We are reviewing your request.",
    "We have reviewed your request and are checking the applicable procedure.",
    "Please let us know if you need any further clarification."
]

INSTRUCTOR_TEXTS = [
    "I am providing additional academic information related to this request.",
    "Please review the academic details shared in this conversation."
]

ADMIN_TEXTS = [
    "The request has been forwarded for administrative review.",
    "The academic support administration has reviewed this request."
]


def main():

    db = None
    cursor = None

    try:

        # 1. Database connection
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()

        print("Database connected successfully!")

        # 2. Check existing messages
        cursor.execute("""
            SELECT COUNT(*)
            FROM messages
        """)

        existing = cursor.fetchone()[0]

        if existing > 0:
            print("Messages already exist:", existing)
            print("Duplicate generation stopped.")
            return

        # 3. Fetch tickets
        cursor.execute("""
            SELECT
                ticket_id,
                requester_id,
                created_at
            FROM tickets
            ORDER BY ticket_id
        """)

        tickets = cursor.fetchall()

        if not tickets:
            raise Exception(
                "Tickets not found. Generate tickets first."
            )

        if NUM_MESSAGES < len(tickets):
            raise Exception(
                "NUM_MESSAGES must be at least the number of tickets."
            )

        print("Tickets fetched:", len(tickets))

        # 4. Fetch requester roles
        cursor.execute("""
            SELECT
                r.requester_id,
                r.role_id,
                ro.role_name
            FROM requesters r
            JOIN roles ro
                ON ro.role_id = r.role_id
            WHERE ro.role_name IN ('Learner', 'Instructor')
            ORDER BY r.requester_id
        """)

        requester_roles = {
            row[0]: row[2]
            for row in cursor.fetchall()
        }

        if not requester_roles:
            raise Exception("Learner and Instructor requesters not found.")

        print("Requester roles fetched:", len(requester_roles))

        # 5. Fetch support staff and other staff
        cursor.execute("""
            SELECT
                r.requester_id,
                ro.role_name
            FROM requesters r
            JOIN roles ro
                ON ro.role_id = r.role_id
            WHERE ro.role_name IN (
                'Support Staff',
                'Instructor',
                'Academic Administrator',
                'Platform Administrator'
            )
            ORDER BY r.requester_id
        """)

        staff = cursor.fetchall()

        support_ids = [
            row[0] for row in staff
            if row[1] == "Support Staff"
        ]

        instructor_ids = [
            row[0] for row in staff
            if row[1] == "Instructor"
        ]

        admin_ids = [
            row[0] for row in staff
            if row[1] in (
                "Academic Administrator",
                "Platform Administrator"
            )
        ]

        print("Support staff:", len(support_ids))
        print("Instructors:", len(instructor_ids))
        print("Administrators:", len(admin_ids))

        # 6. Prepare messages
        rows = []

        # Every ticket receives one initial requester message
        for ticket_id, requester_id, created_at in tickets:

            requester_role = requester_roles.get(requester_id)

            if requester_role == "Instructor":
                sender_type = "Instructor"
                message_text = rng.choice(INSTRUCTOR_TEXTS)

            elif requester_role == "Learner":
                sender_type = "Student"
                message_text = rng.choice(STUDENT_TEXTS)

            else:
                raise Exception(
                    f"Requester role not found: {requester_id}"
                )

            rows.append((
                f"MSG-{ticket_id}-001",
                ticket_id,
                requester_id,
                sender_type,
                message_text,
                created_at
            ))

        # 7. Distribute remaining messages
        extra_counts = [0] * len(tickets)

        remaining_messages = NUM_MESSAGES - len(tickets)

        for _ in range(remaining_messages):
            extra_counts[rng.randrange(len(tickets))] += 1

        for index, ticket in enumerate(tickets):

            ticket_id, requester_id, created_at = ticket

            for seq in range(2, extra_counts[index] + 2):

                sender_id = requester_id
                sender_type = "Student"
                message_text = rng.choice(STUDENT_TEXTS)

                choice = rng.randint(1, 100)

                if choice <= 45 and support_ids:

                    sender_id = rng.choice(support_ids)
                    sender_type = "Support"
                    message_text = rng.choice(SUPPORT_TEXTS)

                elif choice <= 60 and instructor_ids:

                    sender_id = rng.choice(instructor_ids)
                    sender_type = "Instructor"
                    message_text = rng.choice(INSTRUCTOR_TEXTS)

                elif choice <= 70 and admin_ids:

                    sender_id = rng.choice(admin_ids)
                    sender_type = "Admin"
                    message_text = rng.choice(ADMIN_TEXTS)

                elif requester_roles.get(requester_id) == "Instructor":

                    sender_type = "Instructor"
                    message_text = rng.choice(INSTRUCTOR_TEXTS)

                message_time = created_at + timedelta(
                    minutes=seq * rng.randint(5, 20)
                )

                rows.append((
                    f"MSG-{ticket_id}-{seq:03d}",
                    ticket_id,
                    sender_id,
                    sender_type,
                    message_text,
                    message_time
                ))

        # 8. Validate generated message count
        if len(rows) != NUM_MESSAGES:
            raise Exception(
                f"Expected {NUM_MESSAGES} messages, "
                f"but generated {len(rows)}."
            )

        print("Messages prepared:", len(rows))

        # 9. Insert messages
        cursor.executemany("""
            INSERT INTO messages
            (
                message_id,
                ticket_id,
                sender_id,
                sender_type,
                message_text,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, rows)

        # 10. Commit transaction
        db.commit()

        # 11. Verify database count
        cursor.execute("""
            SELECT COUNT(*)
            FROM messages
        """)

        total = cursor.fetchone()[0]

        if total != NUM_MESSAGES:
            raise Exception(
                f"Expected {NUM_MESSAGES}, found {total}."
            )

        print("\n================================")
        print("MESSAGES GENERATED SUCCESSFULLY!")
        print("================================")
        print("New messages:", len(rows))
        print("Total messages:", total)
        print("================================")

    except Exception as error:

        if db and db.is_connected():
            db.rollback()

        print("\nMessage generation error:", error)
        print("Database changes rolled back.")

    finally:

        if cursor:
            cursor.close()

        if db and db.is_connected():
            db.close()

        print("Database connection closed.")


if __name__ == "__main__":
    main()
