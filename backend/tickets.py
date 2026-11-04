
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from uuid import uuid4

from database import get_connection
from auth import token_required, role_required


tickets = Blueprint("tickets", __name__)

PRIORITIES = ["Low", "Normal", "High", "Critical"]

STATUSES = [
    "Open",
    "In Progress",
    "Waiting",
    "Escalated",
    "Resolved",
    "Closed"
]


# =====================================
# HELPER: BUSINESS HOURS CALCULATION
# =====================================

def add_business_minutes(start_time, minutes):

    current = start_time
    remaining = int(minutes)

    while remaining > 0:

        # Skip Saturday and Sunday
        if current.weekday() >= 5:
            current = (current + timedelta(days=1)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            continue

        # Start working time at 9 AM
        if current.hour < 9:
            current = current.replace(
                hour=9, minute=0, second=0, microsecond=0
            )

        # Move to next working day after 5 PM
        if current.hour >= 17:
            current = (current + timedelta(days=1)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            continue

        closing_time = current.replace(
            hour=17, minute=0, second=0, microsecond=0
        )

        available_minutes = int(
            (closing_time - current).total_seconds() // 60
        )

        if remaining <= available_minutes:
            current += timedelta(minutes=remaining)
            remaining = 0
        else:
            remaining -= available_minutes

            current = (current + timedelta(days=1)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )

    return current


# =====================================
# HELPER: GET SLA RULES
# =====================================

def get_sla_targets(cursor, category_id, priority):

    cursor.execute("""
        SELECT
            response_target_minutes,
            resolution_target_minutes,
            business_hours_only
        FROM sla_rules
        WHERE category_id = %s
        AND priority = %s
        LIMIT 1
    """, (category_id, priority))

    rule = cursor.fetchone()

    if rule:

        return (
            int(rule["response_target_minutes"]),
            int(rule["resolution_target_minutes"]),
            bool(rule["business_hours_only"])
        )

    # Default SLA targets
    defaults = {
        "Low": (480, 2880),
        "Normal": (240, 1440),
        "High": (60, 480),
        "Critical": (15, 240)
    }

    response_minutes, resolution_minutes = defaults[priority]

    return response_minutes, resolution_minutes, True


# =====================================
# 1. CREATE TICKET API
# Automatic Assignment + SLA + Event
# =====================================

@tickets.route("/", methods=["POST"])
@token_required
@role_required("Student", "Instructor")
def create_ticket():

    data = request.get_json(silent=True) or {}

    subject = data.get("subject", "").strip()
    description = data.get("description", "").strip()
    category_id = data.get("category_id")
    priority = data.get("priority", "Normal")

    if not subject or not description or category_id is None:
        return jsonify({
            "message": "Subject, description and category are required"
        }), 400

    if priority not in PRIORITIES:
        return jsonify({
            "message": "Invalid priority",
            "allowed_priorities": PRIORITIES
        }), 400

    try:
        category_id = int(category_id)

    except (ValueError, TypeError):
        return jsonify({
            "message": "Invalid category ID"
        }), 400

    connection = get_connection()

    if connection is None:
        return jsonify({
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        # 1. Validate category
        cursor.execute("""
            SELECT
                category_id,
                category_name,
                authorized_team
            FROM categories
            WHERE category_id = %s
        """, (category_id,))

        category = cursor.fetchone()

        if not category:
            return jsonify({
                "message": "Invalid category"
            }), 400

        # 2. Find active academic term
        cursor.execute("""
            SELECT term_id
            FROM terms
            WHERE CURDATE() BETWEEN start_date AND end_date
            ORDER BY start_date DESC
            LIMIT 1
        """)

        term = cursor.fetchone()

        if not term:
            return jsonify({
                "message": "No active academic term found"
            }), 400

        requester_id = g.current_user["requester_id"]

        ticket_id = (
            f"TKT-{datetime.now().year}-{uuid4().hex[:8].upper()}"
        )

        created_at = datetime.now()

        # 3. Insert ticket
        cursor.execute("""
            INSERT INTO tickets (
                ticket_id,
                requester_id,
                term_id,
                category_id,
                subject,
                description,
                priority,
                status,
                issue_type
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Open', 'normal')
        """, (
            ticket_id,
            requester_id,
            term["term_id"],
            category_id,
            subject,
            description,
            priority
        ))

        # 4. Find Support Staff
        cursor.execute("""
            SELECT r.requester_id
            FROM requesters r
            JOIN roles ro
                ON r.role_id = ro.role_id
            WHERE ro.role_name = 'Support Staff'
            ORDER BY r.requester_id
            LIMIT 1
        """)

        staff = cursor.fetchone()

        assigned_to = (
            staff["requester_id"] if staff else None
        )

        # 5. Automatic assignment
        cursor.execute("""
            INSERT INTO assignments (
                ticket_id,
                assigned_team,
                assigned_to,
                assigned_at,
                assignment_reason,
                assignment_status
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            ticket_id,
            category["authorized_team"],
            assigned_to,
            created_at,
            "Automatically assigned based on ticket category",
            "Active"
        ))

        # 6. Get SLA targets
        response_minutes, resolution_minutes, business_hours = (
            get_sla_targets(cursor, category_id, priority)
        )

        # 7. Calculate deadlines
        if business_hours:

            response_deadline = add_business_minutes(
                created_at,
                response_minutes
            )

            resolution_deadline = add_business_minutes(
                created_at,
                resolution_minutes
            )

        else:

            response_deadline = created_at + timedelta(
                minutes=response_minutes
            )

            resolution_deadline = created_at + timedelta(
                minutes=resolution_minutes
            )

        # 8. Insert SLA record
        cursor.execute("""
            INSERT INTO sla (
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
        """, (
            f"SLA-{ticket_id}",
            ticket_id,
            response_minutes,
            resolution_minutes,
            response_deadline,
            resolution_deadline,
            int(business_hours),
            0,
            0
        ))

        # 9. Record ticket creation event
        cursor.execute("""
            INSERT INTO ticket_events (
                ticket_id,
                event_type,
                old_value,
                new_value,
                event_description,
                actor_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            ticket_id,
            "Ticket Created",
            None,
            "Open",
            "Ticket created with automatic assignment and SLA",
            requester_id
        ))

        # Save all operations together
        connection.commit()

        return jsonify({
            "message": "Ticket created successfully",
            "ticket_id": ticket_id,
            "category": category["category_name"],
            "assigned_team": category["authorized_team"],
            "assigned_to": assigned_to,
            "status": "Open",
            "assignment_created": True,
            "sla_created": True,
            "response_deadline": response_deadline.isoformat(),
            "resolution_deadline": resolution_deadline.isoformat()
        }), 201

    except Exception as error:

        connection.rollback()

        return jsonify({
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


# =====================================
# 2. VIEW MY TICKETS API
# =====================================

@tickets.route("/my", methods=["GET"])
@token_required
def my_tickets():

    requester_id = g.current_user["requester_id"]

    connection = get_connection()

    if connection is None:
        return jsonify({
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                t.ticket_id,
                t.subject,
                t.description,
                t.priority,
                t.status,
                t.issue_type,
                t.created_at,
                c.category_name
            FROM tickets t
            JOIN categories c
                ON t.category_id = c.category_id
            WHERE t.requester_id = %s
            ORDER BY t.created_at DESC
        """, (requester_id,))

        result = cursor.fetchall()

        return jsonify({
            "total_tickets": len(result),
            "tickets": result
        }), 200

    except Exception as error:

        return jsonify({
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


# =====================================
# 3. VIEW ALL TICKETS API
# =====================================

@tickets.route("/", methods=["GET"])
@token_required
@role_required(
    "Support Staff",
    "Academic Admin",
    "Platform Admin"
)
def all_tickets():

    connection = get_connection()

    if connection is None:
        return jsonify({
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                t.ticket_id,
                t.subject,
                t.priority,
                t.status,
                t.created_at,
                r.name AS requester_name,
                r.email AS requester_email,
                c.category_name,
                c.authorized_team
            FROM tickets t
            JOIN requesters r
                ON t.requester_id = r.requester_id
            JOIN categories c
                ON t.category_id = c.category_id
            ORDER BY t.created_at DESC
        """)

        result = cursor.fetchall()

        return jsonify({
            "total_tickets": len(result),
            "tickets": result
        }), 200

    except Exception as error:

        return jsonify({
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


# =====================================
# 4. VIEW SINGLE TICKET API
# =====================================

@tickets.route("/<ticket_id>", methods=["GET"])
@token_required
def single_ticket(ticket_id):

    connection = get_connection()

    if connection is None:
        return jsonify({
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                t.*,
                r.name AS requester_name,
                r.email AS requester_email,
                c.category_name,
                c.authorized_team
            FROM tickets t
            JOIN requesters r
                ON t.requester_id = r.requester_id
            JOIN categories c
                ON t.category_id = c.category_id
            WHERE t.ticket_id = %s
        """, (ticket_id,))

        ticket = cursor.fetchone()

        if not ticket:
            return jsonify({
                "message": "Ticket not found"
            }), 404

        user = g.current_user

        if user["role"] in ["Student", "Instructor"]:

            if ticket["requester_id"] != user["requester_id"]:

                return jsonify({
                    "message": "Access denied"
                }), 403

        return jsonify(ticket), 200

    except Exception as error:

        return jsonify({
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


# =====================================
# 5. UPDATE TICKET STATUS API
# WITH EVENT HISTORY
# =====================================

@tickets.route("/<ticket_id>/status", methods=["PATCH"])
@token_required
@role_required(
    "Support Staff",
    "Academic Admin",
    "Platform Admin"
)
def update_ticket_status(ticket_id):

    data = request.get_json(silent=True) or {}

    new_status = data.get("status")

    if new_status not in STATUSES:
        return jsonify({
            "message": "Invalid ticket status",
            "allowed_statuses": STATUSES
        }), 400

    connection = get_connection()

    if connection is None:
        return jsonify({
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT ticket_id, status
            FROM tickets
            WHERE ticket_id = %s
        """, (ticket_id,))

        ticket = cursor.fetchone()

        if not ticket:
            return jsonify({
                "message": "Ticket not found"
            }), 404

        old_status = ticket["status"]

        if old_status == new_status:
            return jsonify({
                "message": "Ticket already has this status"
            }), 200

        actor_id = g.current_user["requester_id"]

        cursor.execute("""
            UPDATE tickets
            SET status = %s
            WHERE ticket_id = %s
        """, (new_status, ticket_id))

        cursor.execute("""
            INSERT INTO ticket_events (
                ticket_id,
                event_type,
                old_value,
                new_value,
                event_description,
                actor_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            ticket_id,
            "Status Changed",
            old_status,
            new_status,
            f"Ticket status changed from {old_status} to {new_status}",
            actor_id
        ))

        connection.commit()

        return jsonify({
            "message": "Ticket status updated successfully",
            "ticket_id": ticket_id,
            "old_status": old_status,
            "new_status": new_status,
            "event_recorded": True
        }), 200

    except Exception as error:

        connection.rollback()

        return jsonify({
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


# =====================================
# 6. VIEW TICKET EVENT HISTORY API
# =====================================

@tickets.route("/<ticket_id>/history", methods=["GET"])
@token_required
def ticket_history(ticket_id):

    connection = get_connection()

    if connection is None:
        return jsonify({
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT requester_id
            FROM tickets
            WHERE ticket_id = %s
        """, (ticket_id,))

        ticket = cursor.fetchone()

        if not ticket:
            return jsonify({
                "message": "Ticket not found"
            }), 404

        user = g.current_user

        if user["role"] in ["Student", "Instructor"]:

            if ticket["requester_id"] != user["requester_id"]:

                return jsonify({
                    "message": "Access denied"
                }), 403

        cursor.execute("""
            SELECT
                event_id,
                ticket_id,
                event_type,
                old_value,
                new_value,
                event_description,
                actor_id,
                created_at
            FROM ticket_events
            WHERE ticket_id = %s
            ORDER BY created_at ASC
        """, (ticket_id,))

        events = cursor.fetchall()

        return jsonify({
            "ticket_id": ticket_id,
            "total_events": len(events),
            "history": events
        }), 200

    except Exception as error:

        return jsonify({
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()
