
import random
import mysql.connector
from faker import Faker
from datetime import datetime
from config import SEED, DB_CONFIG, NUM_REQUESTERS

# 1. Initialize
random.seed(SEED)

fake = Faker()
fake.seed_instance(SEED)

db = None
cursor = None

try:
    # 2. Database connection
    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()

    print("Database connected successfully!")

    # 3. Insert Roles
    roles = [
        ("Learner", "Student requesting academic support"),
        ("Instructor", "Faculty member"),
        ("Academic Administrator", "Manages academic policies"),
        ("Support Staff", "Handles support tickets"),
        ("Platform Administrator", "Manages the platform")
    ]

    for role_name, description in roles:
        cursor.execute("""
            SELECT role_id FROM roles
            WHERE role_name = %s
        """, (role_name,))

        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO roles (role_name, description)
                VALUES (%s, %s)
            """, (role_name, description))

    print("Roles inserted successfully!")

    # 4. Insert Categories
    categories = [
        ("Financial Aid",
         "Scholarships, fees and financial assistance",
         "Financial Aid Office"),

        ("Registration",
         "Course and semester registration",
         "Registrar Office"),

        ("IT",
         "Technical and account-related support",
         "IT Support"),

        ("Accessibility",
         "Accessibility and accommodation support",
         "Accessibility Services")
    ]

    for category_name, description, team in categories:
        cursor.execute("""
            SELECT category_id FROM categories
            WHERE category_name = %s
        """, (category_name,))

        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO categories
                (category_name, description, authorized_team)
                VALUES (%s, %s, %s)
            """, (category_name, description, team))
        else:
            cursor.execute("""
                UPDATE categories
                SET description = %s,
                    authorized_team = %s
                WHERE category_name = %s
            """, (description, team, category_name))

    print("Categories inserted successfully!")

    # 5. Insert Academic Terms
    terms = [
        ("Spring 2026", "2026-01-01", "2026-05-31"),
        ("Fall 2026", "2026-08-01", "2026-12-31"),
        ("Spring 2027", "2027-01-01", "2027-05-31")
    ]

    for term in terms:
        cursor.execute("""
            SELECT term_id FROM terms
            WHERE term_name = %s
        """, (term[0],))

        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO terms
                (term_name, start_date, end_date)
                VALUES (%s, %s, %s)
            """, term)

    print("Academic Terms inserted successfully!")

    # 6. Fetch Role IDs
    cursor.execute("""
        SELECT role_id, role_name FROM roles
    """)

    role_ids = {
        role_name: role_id
        for role_id, role_name in cursor.fetchall()
    }

    required_roles = [
        "Learner",
        "Instructor",
        "Academic Administrator",
        "Support Staff",
        "Platform Administrator"
    ]

    for role in required_roles:
        if role not in role_ids:
            raise Exception(f"Required role not found: {role}")

    print("Role IDs fetched successfully!")

    # 7. Inspect Requesters Table
    cursor.execute("SHOW COLUMNS FROM requesters")
    column_info = cursor.fetchall()

    # IMPORTANT: SHOW COLUMNS returns 6 fields:
    # 0 Field, 1 Type, 2 Null, 3 Key, 4 Default, 5 Extra

    columns = {
        row[0]: {
            "type": row[1].lower(),
            "null": row[2],
            "key": row[3],
            "default": row[4],
            "extra": (row[5] or "").lower()
        }
        for row in column_info
    }

    print("Requester table columns:", list(columns.keys()))

    required_columns = {
        "requester_id", "role_id", "email"
    }

    missing = required_columns - set(columns.keys())

    if missing:
        raise Exception(
            f"Missing requester columns: {missing}"
        )

    # Detect name column
    name_column = next(
        (
            col for col in
            ["name", "full_name", "requester_name"]
            if col in columns
        ),
        None
    )

    has_first_last = (
        "first_name" in columns
        and "last_name" in columns
    )

    if name_column is None and not has_first_last:
        raise Exception("Requester name column not found.")

    requester_id_type = columns["requester_id"]["type"]

    auto_increment = (
        "auto_increment" in columns["requester_id"]["extra"]
    )

    numeric_types = (
        "int", "integer", "bigint",
        "smallint", "mediumint"
    )

    is_numeric_id = any(
        requester_id_type.startswith(t)
        for t in numeric_types
    )

    print("Requester ID type:", requester_id_type)
    print("Requester ID auto increment:", auto_increment)

    # 8. Fetch Existing Requesters
    cursor.execute("""
        SELECT requester_id, email
        FROM requesters
    """)

    existing_data = cursor.fetchall()

    existing_ids = {
        str(row[0]) for row in existing_data
    }

    existing_emails = {
        row[1].lower()
        for row in existing_data
        if row[1]
    }

    existing_count = len(existing_data)

    print("Existing Requesters:", existing_count)

    if existing_count > NUM_REQUESTERS:
        raise Exception(
            f"Existing requester count {existing_count} "
            f"exceeds target {NUM_REQUESTERS}."
        )

    # 9. Determine Next Numeric ID
    next_numeric_id = None

    if is_numeric_id and not auto_increment:
        cursor.execute("""
            SELECT COALESCE(MAX(requester_id), 0) + 1
            FROM requesters
        """)

        next_numeric_id = cursor.fetchone()[0]

    # 10. Generate Missing Requesters
    requesters = []
    remaining = NUM_REQUESTERS - existing_count

    index = 1

    while len(requesters) < remaining:

        email = f"user{index}@university.edu"

        if email.lower() in existing_emails:
            index += 1
            continue

        role_name = random.choices(
            required_roles,
            weights=[75, 12, 5, 6, 2],
            k=1
        )[0]

        name = fake.name()

        record = {}

        # Include ID only when it is not auto-generated
        if not auto_increment:
            if is_numeric_id:
                record["requester_id"] = next_numeric_id
                next_numeric_id += 1
            else:
                record["requester_id"] = f"USR-{index:05d}"

        record["role_id"] = role_ids[role_name]

        if name_column:
            record[name_column] = name
        else:
            parts = name.split(" ", 1)
            record["first_name"] = parts[0]
            record["last_name"] = parts[1] if len(parts) > 1 else ""

        record["email"] = email

        # Handle created_at if it has no default
        if "created_at" in columns:
            created = columns["created_at"]

            if (
                created["null"] == "NO"
                and created["default"] is None
                and "auto_increment" not in created["extra"]
            ):
                record["created_at"] = datetime.now()

        requesters.append(record)
        existing_emails.add(email.lower())

        index += 1

    # 11. Insert Requesters
    if requesters:

        insert_columns = list(requesters[0].keys())

        column_names = ", ".join(
            f"`{col}`" for col in insert_columns
        )

        placeholders = ", ".join(
            ["%s"] * len(insert_columns)
        )

        query = f"""
            INSERT INTO requesters
            ({column_names})
            VALUES ({placeholders})
        """

        values = [
            tuple(record[col] for col in insert_columns)
            for record in requesters
        ]

        cursor.executemany(query, values)

        print("New Requesters Inserted:", len(requesters))

    else:
        print("All target requesters already exist!")

    # 12. Verify Counts
    cursor.execute("SELECT COUNT(*) FROM roles")
    role_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM categories")
    category_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM terms")
    term_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM requesters")
    requester_count = cursor.fetchone()[0]

    if role_count < 5:
        raise Exception("Expected at least 5 roles.")

    if category_count < 4:
        raise Exception("Expected at least 4 categories.")

    if term_count < 3:
        raise Exception("Expected at least 3 terms.")

    if requester_count != NUM_REQUESTERS:
        raise Exception(
            f"Expected {NUM_REQUESTERS} requesters, "
            f"but found {requester_count}."
        )

    # 13. Commit
    db.commit()

    print("\n====================================")
    print("MASTER DATA GENERATED SUCCESSFULLY!")
    print("====================================")
    print("Roles:", role_count)
    print("Categories:", category_count)
    print("Terms:", term_count)
    print("Requesters:", requester_count)
    print("New Requesters:", len(requesters))
    print("====================================")

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
