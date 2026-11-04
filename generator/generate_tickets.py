
import random
import mysql.connector
from datetime import datetime, timedelta
from config import DB_CONFIG, SEED, NUM_TICKETS


# ==========================================
# 1. INITIALIZATION
# ==========================================

random.seed(SEED)

db = None
cursor = None

# Ticket subjects and descriptions
TICKET_DATA = {
    "Financial Aid": [
        (
            "Scholarship application status",
            "I submitted my scholarship application and need help checking its status."
        ),
        (
            "Financial aid disbursement",
            "I need clarification regarding the financial aid disbursement process."
        ),
        (
            "Tuition payment assistance",
            "I require assistance understanding the available tuition payment options."
        ),
        (
            "Financial aid document submission",
            "Please guide me regarding the documents required for financial aid."
        )
    ],

    "Registration": [
        (
            "Course registration issue",
            "I am facing an issue while registering for my courses."
        ),
        (
            "Unable to add a course",
            "I cannot add a course to my semester registration."
        ),
        (
            "Semester registration clarification",
            "I need clarification regarding the semester registration procedure."
        ),
        (
            "Registration deadline question",
            "Please provide guidance about the registration deadline."
        )
    ],

    "IT": [
        (
            "University portal access issue",
            "I am unable to access the university student portal."
        ),
        (
            "Password reset assistance",
            "I need assistance resetting my university account password."
        ),
        (
            "Learning platform technical issue",
            "I am experiencing a technical issue with the learning platform."
        ),
        (
            "University email access",
            "I cannot access my university email account."
        )
    ],

    "Accessibility": [
        (
            "Learning accommodation request",
            "I need information about requesting learning accommodations."
        ),
        (
            "Accessible course material",
            "I would like assistance accessing accessible course materials."
        ),
        (
            "Exam accommodation clarification",
            "Please explain the process for requesting exam accommodations."
        ),
        (
            "Accessibility support request",
            "I need guidance regarding university accessibility support."
        )
    ]
}


# ==========================================
# 2. MAIN FUNCTION
# ==========================================

try:

    # Connect to MySQL
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()

    print("Database connected successfully!")

    # ======================================
    # 3. CHECK EXISTING TICKETS
    # ======================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
    """)

    existing_count = cursor.fetchone()[0]

    if existing_count > 0:

        print(
            f"Tickets already exist: {existing_count}"
        )

        print("Duplicate generation stopped.")
        raise SystemExit

    # ======================================
    # 4. FETCH REQUESTERS
    # ======================================

    cursor.execute("""
        SELECT
            r.requester_id,
            ro.role_name
        FROM requesters r
        JOIN roles ro
            ON r.role_id = ro.role_id
        WHERE ro.role_name IN ('Learner', 'Instructor')
        ORDER BY r.requester_id
    """)

    requesters = cursor.fetchall()

    if not requesters:
        raise Exception(
            "No Learner or Instructor requesters found."
        )

    print("Requesters fetched:", len(requesters))

    # ======================================
    # 5. FETCH CATEGORIES
    # ======================================

    cursor.execute("""
        SELECT category_id, category_name
        FROM categories
        ORDER BY category_id
    """)

    categories = cursor.fetchall()

    if len(categories) < 4:
        raise Exception(
            "Expected all four support categories."
        )

    for category_id, category_name in categories:

        if category_name not in TICKET_DATA:
            raise Exception(
                f"Unknown category: {category_name}"
            )

    print("Categories fetched:", len(categories))

    # ======================================
    # 6. FETCH ACADEMIC TERMS
    # ======================================

    cursor.execute("""
        SELECT
            term_id,
            term_name,
            start_date,
            end_date
        FROM terms
        ORDER BY start_date
    """)

    terms = cursor.fetchall()

    if not terms:
        raise Exception("No academic terms found.")

    print("Academic terms fetched:", len(terms))

    # ======================================
    # 7. GENERATE TICKETS
    # ======================================

    # Fixed deterministic date range
    start_date = datetime(2026, 10, 1, 9, 0, 0)
    end_date = datetime(2026, 11, 3, 17, 0, 0)

    total_seconds = int(
        (end_date - start_date).total_seconds()
    )

    tickets = []

    priorities = [
        "Low",
        "Normal",
        "High",
        "Critical"
    ]

    priority_weights = [
        15,
        55,
        25,
        5
    ]

    for i in range(1, NUM_TICKETS + 1):

        # Generate unique ticket ID
        ticket_id = f"TKT-2026-{i:06d}"

        # Select requester
        requester_id, role_name = random.choice(requesters)

        # Select category
        category_id, category_name = random.choice(categories)

        # Select creation date
        created_at = start_date + timedelta(
            seconds=random.randint(0, total_seconds)
        )

        # Find matching academic term
        matching_terms = [
            term for term in terms
            if term[2] <= created_at.date() <= term[3]
        ]

        if not matching_terms:
            raise Exception(
                f"No matching academic term for {created_at}"
            )

        term_id, term_name, term_start, term_end = random.choice(
            matching_terms
        )

        # Select subject and description
        subject, description = random.choice(
            TICKET_DATA[category_name]
        )

        # Select priority
        priority = random.choices(
            priorities,
            weights=priority_weights,
            k=1
        )[0]

        # Initial status
        status = "Open"

        # Normal issue type
        issue_type = "normal"

        tickets.append((
            ticket_id,
            requester_id,
            term_id,
            category_id,
            subject,
            description,
            priority,
            status,
            issue_type,
            created_at
        ))

    print("Tickets prepared:", len(tickets))

    # ======================================
    # 8. INSERT TICKETS
    # ======================================

    insert_query = """
        INSERT INTO tickets
        (
            ticket_id,
            requester_id,
            term_id,
            category_id,
            subject,
            description,
            priority,
            status,
            issue_type,
            created_at
        )
        VALUES (%s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s)
    """

    cursor.executemany(
        insert_query,
        tickets
    )

    # ======================================
    # 9. VERIFY INSERTED RECORDS
    # ======================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM tickets
    """)

    total_tickets = cursor.fetchone()[0]

    if total_tickets != NUM_TICKETS:
        raise Exception(
            f"Expected {NUM_TICKETS} tickets, "
            f"but found {total_tickets}."
        )

    # Check duplicate ticket IDs
    cursor.execute("""
        SELECT
            COUNT(*),
            COUNT(DISTINCT ticket_id)
        FROM tickets
    """)

    total_count, unique_count = cursor.fetchone()

    if total_count != unique_count:
        raise Exception("Duplicate ticket IDs detected.")

    # Commit transaction
    db.commit()

    # ======================================
    # 10. SUCCESS MESSAGE
    # ======================================

    print("\n======================================")
    print("TICKET GENERATION SUCCESSFUL!")
    print("======================================")

    print("Expected Tickets:", NUM_TICKETS)
    print("Inserted Tickets:", len(tickets))
    print("Total Tickets:", total_tickets)
    print("Unique Ticket IDs:", unique_count)

    print("======================================")

except SystemExit:
    pass

except Exception as error:

    if db and db.is_connected():
        db.rollback()

    print("\nERROR:", error)
    print("Database changes rolled back.")

finally:

    if cursor:
        cursor.close()

    if db and db.is_connected():
        db.close()

    print("\nDatabase connection closed.")
