
from functools import wraps
from flask import Blueprint, request, jsonify, g
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from database import get_connection

auth = Blueprint("auth", __name__)

SECRET_KEY = "university-helpdesk-secret-key-change-later"


# =====================================
# JWT TOKEN AUTHENTICATION
# =====================================

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "message": "Token is missing"
            }), 401

        token = auth_header.split(" ", 1)[1].strip()

        if not token:
            return jsonify({
                "message": "Token is empty"
            }), 401

        try:
            data = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=["HS256"]
            )

            g.current_user = data

        except jwt.ExpiredSignatureError:
            return jsonify({
                "message": "Token expired"
            }), 401

        except jwt.InvalidSignatureError:
            return jsonify({
                "message": "Token signature mismatch"
            }), 401

        except jwt.DecodeError:
            return jsonify({
                "message": "Invalid token format"
            }), 401

        except jwt.InvalidTokenError:
            return jsonify({
                "message": "Invalid token"
            }), 401

        return f(*args, **kwargs)

    return decorated


# =====================================
# ROLE-BASED ACCESS CONTROL
# =====================================

def role_required(*allowed_roles):

    def decorator(f):

        @wraps(f)
        def decorated(*args, **kwargs):

            user_role = g.current_user.get("role")

            if user_role not in allowed_roles:
                return jsonify({
                    "message": "Access denied",
                    "your_role": user_role
                }), 403

            return f(*args, **kwargs)

        return decorated

    return decorator


# =====================================
# USER REGISTRATION API
# =====================================

@auth.route("/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role_id = data.get("role_id")

    if not name or not email or not password or role_id is None:
        return jsonify({
            "message": "All fields are required"
        }), 400

    if len(password) < 8:
        return jsonify({
            "message": "Password must contain at least 8 characters"
        }), 400

    if len(password.encode("utf-8")) > 72:
        return jsonify({
            "message": "Password must not exceed 72 bytes"
        }), 400

    try:
        role_id = int(role_id)
    except (ValueError, TypeError):
        return jsonify({
            "message": "Invalid role ID"
        }), 400

    connection = get_connection()

    if connection is None:
        return jsonify({
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT requester_id
            FROM requesters
            WHERE email = %s
        """, (email,))

        if cursor.fetchone():
            return jsonify({
                "message": "Email already registered"
            }), 409

        # Public registration allows Student and Instructor only
        cursor.execute("""
            SELECT role_id, role_name
            FROM roles
            WHERE role_id = %s
        """, (role_id,))

        role = cursor.fetchone()

        if not role:
            return jsonify({
                "message": "Invalid role"
            }), 400

        if role["role_name"] not in ["Student", "Instructor"]:
            return jsonify({
                "message": "Registration for this role is not allowed"
            }), 403

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute("""
            INSERT INTO requesters
            (name, email, role_id, password_hash)
            VALUES (%s, %s, %s, %s)
        """, (
            name,
            email,
            role_id,
            password_hash
        ))

        requester_id = cursor.lastrowid

        connection.commit()

        return jsonify({
            "message": "Registration successful",
            "requester_id": requester_id
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
# USER LOGIN API
# =====================================

@auth.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "message": "Email and password required"
        }), 400

    connection = get_connection()

    if connection is None:
        return jsonify({
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                r.requester_id,
                r.name,
                r.email,
                r.password_hash,
                ro.role_name
            FROM requesters r
            JOIN roles ro
                ON r.role_id = ro.role_id
            WHERE r.email = %s
        """, (email,))

        user = cursor.fetchone()

        if not user or not user["password_hash"]:
            return jsonify({
                "message": "Invalid email or password"
            }), 401

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8")
        ):
            return jsonify({
                "message": "Invalid email or password"
            }), 401

        token = jwt.encode({

            "requester_id": user["requester_id"],
            "role": user["role_name"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=2)

        }, SECRET_KEY, algorithm="HS256")

        return jsonify({

            "message": "Login successful",

            "token": token,

            "user": {
                "requester_id": user["requester_id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role_name"]
            }

        }), 200

    except Exception as error:

        return jsonify({
            "message": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()
