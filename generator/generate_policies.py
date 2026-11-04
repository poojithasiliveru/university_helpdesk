
import random
import mysql.connector

from config import SEED, DB_CONFIG, NUM_POLICIES

random.seed(SEED)

db = mysql.connector.connect(**DB_CONFIG)
cursor = db.cursor()

domains = [
    "financial_aid",
    "registration",
    "it",
    "accessibility"
]

policy_topics = {
    "financial_aid": [
        "Scholarship Eligibility",
        "Financial Aid Application",
        "Grant Requirements",
        "Aid Renewal",
        "Financial Aid Deadlines",
        "Student Loan Guidance",
        "Merit Scholarship",
        "Need Based Assistance",
        "Aid Documentation",
        "Financial Aid Appeals"
    ],

    "registration": [
        "Course Registration",
        "Late Registration",
        "Course Withdrawal",
        "Semester Enrollment",
        "Registration Eligibility",
        "Add Drop Period",
        "Course Prerequisites",
        "Credit Requirements",
        "Registration Holds",
        "Registration Appeals"
    ],

    "it": [
        "Account Access",
        "Password Reset",
        "Campus WiFi",
        "Email Access",
        "Software Access",
        "Device Support",
        "IT Security",
        "Account Recovery",
        "Technical Support",
        "IT Incident Reporting"
    ],

    "accessibility": [
        "Accommodation Requests",
        "Accessible Learning",
        "Exam Accommodations",
        "Assistive Technology",
        "Accessibility Services",
        "Accessible Classrooms",
        "Learning Support",
        "Disability Documentation",
        "Accommodation Renewal",
        "Accessibility Appeals"
    ]
}

# 40 policy documents
policies = []

for domain in domains:

    for i, topic in enumerate(policy_topics[domain], 1):

        policy_id = f"POL-{domain}-2026-{i:03d}"

        content = (
            f"Synthetic University Policy: {topic}. "
            f"Domain: {domain}. "
            f"Students must follow the published university "
            f"requirements and submit applicable documentation "
            f"through the designated university support process. "
            f"Requests are reviewed by the authorized department."
        )

        policies.append((
            policy_id,
            domain,
            topic,
            i,
            "2026-01-01",
            None,
            content,
            "Published"
        ))

cursor.executemany("""
    INSERT INTO policy_documents
    (
        policy_id, domain, title, version,
        effective_from, effective_to,
        policy_content, status
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        title = VALUES(title),
        policy_content = VALUES(policy_content),
        status = VALUES(status)
""", policies)

db.commit()

print("Policy Documents Generated Successfully")
print("Total Policies:", len(policies))

cursor.close()
db.close()
