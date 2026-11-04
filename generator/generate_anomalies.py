
import mysql.connector
from datetime import datetime
from config import DB_CONFIG

db = mysql.connector.connect(**DB_CONFIG)
cursor = db.cursor()

try:
    # Separate table to record anomaly ground truth
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_labels (
            anomaly_id INT AUTO_INCREMENT PRIMARY KEY,
            ticket_id VARCHAR(30) NOT NULL,
            anomaly_type VARCHAR(100) NOT NULL,
            description TEXT,
            source_table VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_ticket_anomaly (ticket_id, anomaly_type)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM anomaly_labels")
    if cursor.fetchone()[0] > 0:
        print("Anomalies already exist. Skipping to avoid duplicates.")
        db.rollback()
    else:
        # 1. Expired Policy Citation
        cursor.execute("""
            SELECT ka.article_id, ka.title
            FROM knowledge_articles ka
            WHERE ka.effective_to IS NOT NULL
              AND ka.effective_to < CURDATE()
            LIMIT 1
        """)
        expired_article = cursor.fetchone()

        cursor.execute("""
            SELECT ticket_id FROM tickets
            WHERE ticket_id NOT IN (
                SELECT ticket_id FROM messages
                WHERE message_text LIKE '%Expired policy citation%'
            )
            LIMIT 1
        """)
        ticket = cursor.fetchone()

        if expired_article and ticket:
            article_id, title = expired_article
            ticket_id = ticket[0]

            cursor.execute("""
                INSERT INTO messages
                (message_id, ticket_id, sender_id, sender_type,
                 message_text, created_at)
                VALUES (%s, %s, NULL, 'Support', %s, NOW())
            """, (
                f"ANOM-EXP-{ticket_id}",
                ticket_id,
                f"Expired policy citation: {article_id} - {title}"
            ))

            cursor.execute("""
                INSERT INTO anomaly_labels
                (ticket_id, anomaly_type, description, source_table)
                VALUES (%s, %s, %s, %s)
            """, (
                ticket_id, "Expired Policy Citation",
                f"Message cites expired article {article_id}",
                "messages"
            ))
            print("1. Expired Policy Citation created")

        # 2. Unauthorized Team Routing
        cursor.execute("""
            SELECT a.assignment_id, t.ticket_id,
                   a.assigned_team, c.authorized_team
            FROM assignments a
            JOIN tickets t ON t.ticket_id = a.ticket_id
            JOIN categories c ON c.category_id = t.category_id
            WHERE a.assigned_team <> c.authorized_team
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            cursor.execute("""
                SELECT a.assignment_id, t.ticket_id,
                       a.assigned_team, c.authorized_team
                FROM assignments a
                JOIN tickets t ON t.ticket_id = a.ticket_id
                JOIN categories c ON c.category_id = t.category_id
                LIMIT 1
            """)
            row = cursor.fetchone()

            if row:
                assignment_id, ticket_id, old_team, authorized_team = row
                cursor.execute("""
                    UPDATE assignments
                    SET assigned_team = %s
                    WHERE assignment_id = %s
                """, (f"Unauthorized-{authorized_team}", assignment_id))

                cursor.execute("""
                    INSERT INTO anomaly_labels
                    (ticket_id, anomaly_type, description, source_table)
                    VALUES (%s, %s, %s, %s)
                """, (
                    ticket_id, "Unauthorized Team Routing",
                    f"Assigned to Unauthorized-{authorized_team}; "
                    f"authorized team is {authorized_team}",
                    "assignments"
                ))
                print("2. Unauthorized Team Routing created")

        # 3. Unsupported Response Claim
        cursor.execute("""
            SELECT ticket_id FROM tickets
            ORDER BY ticket_id
            LIMIT 1
        """)
        ticket = cursor.fetchone()

        if ticket:
            ticket_id = ticket[0]
            cursor.execute("""
                INSERT INTO messages
                (message_id, ticket_id, sender_id, sender_type,
                 message_text, created_at)
                VALUES (%s, %s, NULL, 'Support', %s, NOW())
            """, (
                f"ANOM-CLAIM-{ticket_id}",
                ticket_id,
                "Your request is guaranteed to be approved. "
                "No further verification is required."
            ))

            cursor.execute("""
                INSERT INTO anomaly_labels
                (ticket_id, anomaly_type, description, source_table)
                VALUES (%s, %s, %s, %s)
            """, (
                ticket_id, "Unsupported Response Claim",
                "Support message makes an unsupported guarantee",
                "messages"
            ))
            print("3. Unsupported Response Claim created")

        # 4. Business-Hours SLA Error
        cursor.execute("""
            SELECT sla_id, ticket_id
            FROM sla
            LIMIT 1
        """)
        row = cursor.fetchone()

        if row:
            sla_id, ticket_id = row

            cursor.execute("""
                UPDATE sla
                SET response_deadline =
                    DATE_SUB(response_deadline, INTERVAL 1 DAY)
                WHERE sla_id = %s
            """, (sla_id,))

            cursor.execute("""
                INSERT INTO anomaly_labels
                (ticket_id, anomaly_type, description, source_table)
                VALUES (%s, %s, %s, %s)
            """, (
                ticket_id, "Business-Hours SLA Error",
                "Response deadline deliberately shifted by one day",
                "sla"
            ))
            print("4. Business-Hours SLA Error created")

        # 5. Missing Escalation
        cursor.execute("""
            SELECT t.ticket_id
            FROM tickets t
            WHERE t.status = 'Escalated'
              AND NOT EXISTS (
                  SELECT 1 FROM ticket_events e
                  WHERE e.ticket_id = t.ticket_id
                    AND e.event_type LIKE '%escalat%'
              )
            LIMIT 1
        """)
        ticket = cursor.fetchone()

        if ticket:
            ticket_id = ticket[0]
            cursor.execute("""
                INSERT INTO anomaly_labels
                (ticket_id, anomaly_type, description, source_table)
                VALUES (%s, %s, %s, %s)
            """, (
                ticket_id, "Missing Escalation",
                "Ticket is Escalated but has no escalation event",
                "ticket_events"
            ))
            print("5. Missing Escalation labelled")
        else:
            print("Warning: No suitable Missing Escalation ticket found")

        db.commit()
        print("\nAnomaly injection process completed.")

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    cursor.close()
    db.close()
    print("Database connection closed.")
