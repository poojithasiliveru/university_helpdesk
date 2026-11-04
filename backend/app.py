
from flask import Flask, jsonify, g, render_template
from flask_cors import CORS

from tickets import tickets
from policies import policies
from messages import messages
from database import get_connection
from auth import auth, token_required, role_required


# Flask Configuration
app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

CORS(app)


# Register Blueprints
app.register_blueprint(auth, url_prefix="/api/auth")
app.register_blueprint(tickets, url_prefix="/api/tickets")
app.register_blueprint(policies, url_prefix="/api/policies")
app.register_blueprint(messages, url_prefix="/api/messages")


# ---------------- FRONTEND ROUTES ----------------

# Home Page
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "University Helpdesk API is Running",
        "status": "success"
    })


# Login Page
@app.route("/login")
def login_page():
    return render_template("login.html")


# Registration Page
@app.route("/register")
def register_page():
    return render_template("register.html")


# Student Dashboard Page
@app.route("/student-dashboard")
def student_page():
    return render_template("student_dashboard.html")


# Support Dashboard Page
@app.route("/support-dashboard")
def support_page():
    return render_template("support_dashboard.html")


# Knowledge Base Page
@app.route("/knowledge-base")
def knowledge_page():
    return render_template("knowledge_base.html")


# ---------------- DATABASE HEALTH API ----------------

@app.route("/api/health", methods=["GET"])
def health():

    connection = get_connection()

    if connection is None:
        return jsonify({
            "status": "error",
            "message": "Database connection failed"
        }), 500

    connection.close()

    return jsonify({
        "status": "success",
        "message": "Flask and MySQL Connected Successfully"
    })


# ---------------- PROFILE API ----------------

@app.route("/api/profile", methods=["GET"])
@token_required
def profile():

    return jsonify({
        "message": "Profile accessed successfully",
        "user": g.current_user
    })


# ---------------- STUDENT DASHBOARD API ----------------

@app.route("/api/student/dashboard", methods=["GET"])
@token_required
@role_required("Student")
def student_dashboard():

    return jsonify({
        "message": "Welcome to Student Dashboard",
        "role": "Student"
    })


# ---------------- INSTRUCTOR DASHBOARD API ----------------

@app.route("/api/instructor/dashboard", methods=["GET"])
@token_required
@role_required("Instructor")
def instructor_dashboard():

    return jsonify({
        "message": "Welcome to Instructor Dashboard",
        "role": "Instructor"
    })


# ---------------- SUPPORT STAFF DASHBOARD API ----------------

@app.route("/api/support/dashboard", methods=["GET"])
@token_required
@role_required("Support Staff")
def support_dashboard():

    return jsonify({
        "message": "Welcome to Support Staff Dashboard",
        "role": "Support Staff"
    })


# ---------------- ACADEMIC ADMIN DASHBOARD API ----------------

@app.route("/api/academic-admin/dashboard", methods=["GET"])
@token_required
@role_required("Academic Admin")
def academic_admin_dashboard():

    return jsonify({
        "message": "Welcome to Academic Admin Dashboard",
        "role": "Academic Admin"
    })


# ---------------- PLATFORM ADMIN DASHBOARD API ----------------

@app.route("/api/platform-admin/dashboard", methods=["GET"])
@token_required
@role_required("Platform Admin")
def platform_admin_dashboard():

    return jsonify({
        "message": "Welcome to Platform Admin Dashboard",
        "role": "Platform Admin"
    })


# ---------------- COMBINED ADMIN DASHBOARD API ----------------

@app.route("/api/admin/dashboard", methods=["GET"])
@token_required
@role_required("Platform Admin", "Academic Admin")
def admin_dashboard():

    return jsonify({
        "message": "Welcome to Admin Dashboard",
        "status": "success"
    })


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
