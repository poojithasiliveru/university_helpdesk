
import mysql.connector

from config import DB_CONFIG, NUM_ARTICLES

db = mysql.connector.connect(**DB_CONFIG)
cursor = db.cursor(dictionary=True)

# Get all parent policy records
cursor.execute("""
    SELECT policy_id, title, domain
    FROM policy_documents
    ORDER BY policy_id
""")

policies = cursor.fetchall()

# Five versions per policy
version_dates = [
    ("2026-01-01", "2026-03-31", "Expired"),
    ("2026-04-01", "2026-06-30", "Expired"),
    ("2026-07-01", "2026-09-30", "Expired"),
    ("2026-10-01", "2026-12-31", "Published"),
    ("2027-01-01", "2027-03-31", "Draft")
]

articles = []
counter = 1

for policy in policies:

    for version, dates in enumerate(version_dates, 1):

        start_date, end_date, status = dates

        article_id = f"KB-{counter:06d}"

        title = policy["title"]

        content = (
            f"University Knowledge Article: {title}. "
            f"Policy domain: {policy['domain']}. "
            f"Version: {version}. "
            f"Students should review the applicable requirements "
            f"and follow the official university support process. "
            f"For questions that cannot be resolved using this "
            f"article, contact the authorized support department."
        )

        articles.append((
            article_id,
            policy["policy_id"],
            title,
            content,
            version,
            start_date,
            end_date,
            status
        ))

        counter += 1

if len(articles) != NUM_ARTICLES:
    raise ValueError(
        f"Expected {NUM_ARTICLES} articles, "
        f"but generated {len(articles)}"
    )

cursor.executemany("""
    INSERT INTO knowledge_articles
    (
        article_id, policy_id, title, content,
        version, effective_from, effective_to, status
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        title = VALUES(title),
        content = VALUES(content),
        status = VALUES(status)
""", articles)

db.commit()

print("Knowledge Articles Generated Successfully")
print("Total Articles:", len(articles))

cursor.close()
db.close()
