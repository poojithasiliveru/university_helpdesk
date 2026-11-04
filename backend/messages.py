
from flask import Blueprint, request, jsonify, g
from datetime import datetime
from uuid import uuid4

from database import get_connection
from auth import token_required

messages = Blueprint("messages", __name__)


# View Ticket Messages
@messages.route("/<ticket_id>", methods=["GET"])
@token_required
def get_messages(ticket_id):

    connection = get_connection()

    if connection is None:
        return jsonify({"message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT requester_id
            FROM tickets
            WHERE ticket_id = %s
        """, (ticket_id,))

        ticket = cursor.fetchone()

        if not ticket:
            return jsonify({"message": "Ticket not found"}), 404

        user = g.current_user
        role = user["role"]

        if role in ["Student", "Instructor"]:
            if ticket["requester_id"] != user["requester_id"]:
                return jsonify({"message": "Access denied"}), 403

        cursor.execute("""
            SELECT
                message_id,
                ticket_id,
                sender_id,
                sender_type,
                message_text,
                created_at
            FROM messages
            WHERE ticket_id = %s
            ORDER BY created_at ASC
        """, (ticket_id,))

        result = cursor.fetchall()

        return jsonify({
            "ticket_id": ticket_id,
            "total_messages": len(result),
            "messages": result
        }), 200

    except Exception as error:
        return jsonify({"message": str(error)}), 500

    finally:
        cursor.close()
        connection.close()


# Add Ticket Reply
@messages.route("/<ticket_id>", methods=["POST"])
@token_required
def add_message(ticket_id):

    data = request.get_json(silent=True) or {}
    message_text = data.get("message_text", "").strip()

    if not message_text:
        return jsonify({
            "message": "Message cannot be empty"
        }), 400

    user = g.current_user
    role = user["role"]

    sender_types = {
        "Student": "Student",
        "Instructor": "Instructor",
        "Support Staff": "Support",
        "Academic Admin": "Admin",
        "Platform Admin": "Admin"
    }

    sender_type = sender_types.get(role)

    if not sender_type:
        return jsonify({"message": "Invalid user role"}), 403

    connection = get_connection()

    if connection is None:
        return jsonify({"message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT requester_id
            FROM tickets
            WHERE ticket_id = %s
        """, (ticket_id,))

        ticket = cursor.fetchone()

        if not ticket:
            return jsonify({"message": "Ticket not found"}), 404

        if role in ["Student", "Instructor"]:
            if ticket["requester_id"] != user["requester_id"]:
                return jsonify({"message": "Access denied"}), 403

        message_id = f"MSG-{uuid4().hex[:20].upper()}"

        cursor.execute("""
            INSERT INTO messages (
                message_id,
                ticket_id,
                sender_id,
                sender_type,
                message_text
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            message_id,
            ticket_id,
            user["requester_id"],
            sender_type,
            message_text
        ))

        connection.commit()

        return jsonify({
            "message": "Reply added successfully",
            "message_id": message_id,
            "ticket_id": ticket_id,
            "sender_type": sender_type
        }), 201

    except Exception as error:
        connection.rollback()
        return jsonify({"message": str(error)}), 500

    finally:
        cursor.close()
        connection.close()
