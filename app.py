import os
import re
import sqlite3
import threading
import time
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from flask import (Flask, flash, jsonify, redirect, render_template,
                   request, send_from_directory, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)

# ⚠️  Move these to environment variables before going to production:
#     export MOTUWA_SECRET_KEY="..."
#     export ADMIN_USERNAME="..."
#     export ADMIN_PASSWORD="..."
#     export EMAIL_ADDRESS="..."
#     export EMAIL_PASSWORD="..."
app.secret_key       = os.environ.get("MOTUWA_SECRET_KEY", "change-me-in-production")
ADMIN_USERNAME       = os.environ.get("ADMIN_USERNAME", "AdminPrincaMotuwa@gmail.com")
ADMIN_PASSWORD       = os.environ.get("ADMIN_PASSWORD", "DecJanFebMotuwa1201022026&")
EMAIL_ADDRESS        = os.environ.get("EMAIL_ADDRESS", "paulndeh86@gmail.com")
EMAIL_PASSWORD       = os.environ.get("EMAIL_PASSWORD", "qqww pglu zzje bcsd")

DB_NAME = "safety_reports.db"

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    """Return a connected SQLite connection with row_factory set."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't already exist."""
    with get_db() as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                name              TEXT    NOT NULL,
                email             TEXT    NOT NULL UNIQUE,
                phone             TEXT    NOT NULL,
                emergency_name1   TEXT    NOT NULL,
                emergency_phone1  TEXT    NOT NULL,
                emergency_name2   TEXT    NOT NULL,
                emergency_phone2  TEXT    NOT NULL,
                password          TEXT    NOT NULL,
                national_id_file  TEXT,
                status            TEXT    DEFAULT 'Unverified',
                timestamp         TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS transport_reviews (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER,
                transport_type   TEXT,
                license_plate    TEXT,
                route            TEXT,
                company          TEXT,
                driver_name      TEXT,
                driver_contact   TEXT,
                driver_behavior  TEXT,
                driving_quality  TEXT,
                rating           INTEGER,
                review           TEXT,
                created_at       TEXT,
                status           TEXT DEFAULT 'Pending'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT,
                email      TEXT,
                topic      TEXT,
                phone      TEXT,
                ride_date  TEXT,
                message    TEXT,
                timestamp  TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS ride_reports (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER,
                plate_number    TEXT,
                vehicle_type    TEXT,
                driver_name     TEXT,
                driver_id       TEXT,
                pickup_text     TEXT,
                dest_text       TEXT,
                unsafe_notes    TEXT,
                emergency_name  TEXT,
                emergency_email TEXT,
                created_at      TEXT,
                is_active       INTEGER DEFAULT 1
            )
        """)

        conn.commit()

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(f):
    """Decorator: redirect to login if no user session exists."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator: redirect to login if the session role is not admin."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def valid_password(password):
    """Enforce a minimum password policy."""
    return (
        len(password) >= 8
        and re.search(r"[A-Za-z]", password)
        and re.search(r"\d", password)
        and re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
    )

# ---------------------------------------------------------------------------
# Email / alert helpers
# ---------------------------------------------------------------------------

def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send a plain-text email. Returns True on success, False on failure."""
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"]    = EMAIL_ADDRESS
        msg["To"]      = to_email
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        app.logger.error("Email send failed to %s: %s", to_email, e)
        return False


def monitor_ride(report_id: int, interval: int = 60):
    """
    Background thread: sends repeated alert emails until the ride is marked
    inactive (is_active = 0) in the database.

    Stops automatically — no more infinite loops that require killing the process.
    """
    with get_db() as conn:
        row = conn.execute("""
            SELECT plate_number, vehicle_type, driver_name,
                   pickup_text, dest_text, emergency_name, emergency_email
            FROM ride_reports WHERE id = ?
        """, (report_id,)).fetchone()

    if not row:
        return

    subject = "🚨 MOTUWA Alert: Ride Monitoring Active"
    body = f"""Hello {row['emergency_name']},

Your loved one is currently on a ride. Here are the details:

  Vehicle : {row['vehicle_type']} — {row['plate_number']}
  Driver  : {row['driver_name']}
  Route   : {row['pickup_text']} → {row['dest_text']}

You will receive this alert every {interval // 60} minute(s) until the ride is marked safe.

— MOTUWA Safety Platform
"""

    while True:
        # Re-check whether the ride is still active before each alert
        with get_db() as conn:
            active = conn.execute(
                "SELECT is_active FROM ride_reports WHERE id = ?", (report_id,)
            ).fetchone()

        if not active or not active["is_active"]:
            break  # Ride ended — stop sending alerts

        send_email(row["emergency_email"], subject, body)
        time.sleep(interval)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def homepage():
    return render_template("MOTUWALanding.html")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ── Features / ride registration ──────────────────────────────────────────

@app.route("/features", methods=["GET", "POST"])
def features():
    if request.method == "POST":
        user_id = session.get("user_id")

        fields = (
            "plate_number", "vehicle_type", "driver_name", "driver_id",
            "pickup_text", "dest_text", "unsafe_notes",
            "emergency_name", "emergency_email",
        )
        data = {f: request.form.get(f) for f in fields}
        data["user_id"]    = user_id
        data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO ride_reports
                    (user_id, plate_number, vehicle_type, driver_name, driver_id,
                     pickup_text, dest_text, unsafe_notes,
                     emergency_name, emergency_email, created_at)
                VALUES
                    (:user_id, :plate_number, :vehicle_type, :driver_name, :driver_id,
                     :pickup_text, :dest_text, :unsafe_notes,
                     :emergency_name, :emergency_email, :created_at)
            """, data)
            report_id = cursor.lastrowid
            conn.commit()

        threading.Thread(
            target=monitor_ride, args=(report_id,), daemon=True
        ).start()

        return render_template(
            "FeaturesFlow.html",
            alert_message=(
                "Ride monitoring started. "
                "Your emergency contact will receive email alerts every minute."
            ),
        )

    return render_template("FeaturesFlow.html")


@app.route("/ride/<int:report_id>/end", methods=["POST"])
@login_required
def end_ride(report_id):
    """Mark a ride as complete so the alert monitor stops."""
    with get_db() as conn:
        conn.execute(
            "UPDATE ride_reports SET is_active = 0 WHERE id = ? AND user_id = ?",
            (report_id, session["user_id"]),
        )
        conn.commit()

    # Notify the emergency contact that the rider arrived safely
    with get_db() as conn:
        row = conn.execute(
            "SELECT emergency_name, emergency_email, driver_name, plate_number "
            "FROM ride_reports WHERE id = ?", (report_id,)
        ).fetchone()

    if row:
        send_email(
            row["emergency_email"],
            "✅ MOTUWA: Ride Completed Safely",
            f"Hello {row['emergency_name']},\n\n"
            f"Your loved one has arrived safely and marked their ride as complete.\n\n"
            f"Driver: {row['driver_name']} | Vehicle: {row['plate_number']}\n\n"
            "— MOTUWA Safety Platform",
        )

    flash("Ride marked as complete. Your emergency contact has been notified.", "success")
    return redirect(url_for("features"))


# ── Contact ────────────────────────────────────────────────────────────────

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        data = {
            "name":      request.form.get("name"),
            "email":     request.form.get("email"),
            "topic":     request.form.get("topic"),
            "phone":     request.form.get("phone"),
            "ride_date": request.form.get("ride_date"),
            "message":   request.form.get("message"),
            "timestamp": datetime.now().isoformat(),
        }

        with get_db() as conn:
            conn.execute("""
                INSERT INTO contacts (name, email, topic, phone, ride_date, message, timestamp)
                VALUES (:name, :email, :topic, :phone, :ride_date, :message, :timestamp)
            """, data)
            conn.commit()

        attachment = request.files.get("attachment")
        if attachment and attachment.filename:
            filename = secure_filename(attachment.filename)
            attachment.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        flash("Message sent successfully!", "success")
        return redirect(url_for("contact"))

    return render_template("ContactSupport.html")


# ── Auth ───────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Admin shortcut (use env-var credentials)
        if email == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session["role"] = "admin"
            flash("Admin login successful!", "success")
            return redirect(url_for("admin"))

        with get_db() as conn:
            user = conn.execute(
                "SELECT id, password FROM users WHERE email = ?", (email,)
            ).fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"]    = "user"
            flash("Login successful!", "success")
            return redirect(url_for("features"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("UserLogin.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip()
        phone    = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        emergency_name1  = request.form.get("emergency_name1", "")
        emergency_email1 = request.form.get("emergency_email1", "")
        emergency_name2  = request.form.get("emergency_name2", "")
        emergency_email2 = request.form.get("emergency_email2", "")

        if not valid_password(password):
            flash(
                "Password must be at least 8 characters and include "
                "letters, numbers, and special symbols.",
                "danger",
            )
            return redirect(url_for("signup"))

        with get_db() as conn:
            if conn.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone():
                flash("That email is already registered. Please log in.", "danger")
                return redirect(url_for("signup"))

            filename = None
            national_id = request.files.get("national_id")
            if national_id and national_id.filename:
                filename = secure_filename(national_id.filename)
                national_id.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            conn.execute("""
                INSERT INTO users
                    (name, email, phone,
                     emergency_name1, emergency_phone1,
                     emergency_name2, emergency_phone2,
                     password, national_id_file, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, email, phone,
                emergency_name1, emergency_email1,
                emergency_name2, emergency_email2,
                generate_password_hash(password),
                filename,
                datetime.now().isoformat(),
            ))
            conn.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("UserRegistration.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.", "info")
    return redirect(url_for("homepage"))


# ── Reports / blog ─────────────────────────────────────────────────────────

@app.route("/submit-report", methods=["GET", "POST"])
def submit_report():
    if request.method == "POST":
        data = {
            "user_id":        session.get("user_id"),
            "transport_type": request.form.get("transport_type"),
            "license_plate":  request.form.get("license_plate"),
            "route":          request.form.get("route"),
            "company":        request.form.get("company"),
            "driver_name":    request.form.get("driver_name"),
            "driver_contact": request.form.get("driver_contact"),
            "driver_behavior":request.form.get("driver_behavior"),
            "driving_quality":request.form.get("driving_quality"),
            "rating":         request.form.get("rating"),
            "review":         request.form.get("review"),
            "created_at":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        with get_db() as conn:
            conn.execute("""
                INSERT INTO transport_reviews
                    (user_id, transport_type, license_plate, route, company,
                     driver_name, driver_contact, driver_behavior,
                     driving_quality, rating, review, created_at)
                VALUES
                    (:user_id, :transport_type, :license_plate, :route, :company,
                     :driver_name, :driver_contact, :driver_behavior,
                     :driving_quality, :rating, :review, :created_at)
            """, data)
            conn.commit()

        return redirect(url_for("blog"))

    return render_template("QuickReport.html")


@app.route("/blog")
def blog():
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        rows = conn.execute("""
            SELECT tr.transport_type, tr.license_plate, tr.route, tr.company,
                   tr.driver_name, tr.driver_contact, tr.driver_behavior,
                   tr.driving_quality, tr.rating, tr.review, tr.created_at,
                   u.name AS user_name, u.email AS user_email
            FROM transport_reviews tr
            LEFT JOIN users u ON tr.user_id = u.id
            WHERE tr.status = 'Approved'
            ORDER BY tr.created_at DESC
        """).fetchall()

    reports = []
    for r in rows:
        report          = dict(r)
        report["is_new"] = report["created_at"] >= two_days_ago
        reports.append(report)

    return render_template("Weblog.html", reports=reports)


# ── Admin ──────────────────────────────────────────────────────────────────

@app.route("/admin")
@admin_required
def admin():
    with get_db() as conn:
        users = conn.execute(
            "SELECT id, name, email, phone, emergency_name1, emergency_phone1, "
            "emergency_name2, emergency_phone2, timestamp, national_id_file, status "
            "FROM users"
        ).fetchall()

        reviews = conn.execute("""
            SELECT tr.id, tr.transport_type, tr.license_plate, tr.route, tr.company,
                   tr.driver_name, tr.driver_contact, tr.driver_behavior,
                   tr.driving_quality, tr.rating, tr.review, tr.created_at, tr.status,
                   u.name AS author_name, u.email AS author_email
            FROM transport_reviews tr
            LEFT JOIN users u ON tr.user_id = u.id
            ORDER BY tr.created_at DESC
        """).fetchall()

    return render_template("MotuwaAdmin.html", users=users, reviews=reviews)


@app.route("/verify/<int:user_id>", methods=["POST"])
@admin_required
def verify_user(user_id):
    with get_db() as conn:
        conn.execute("UPDATE users SET status = 'Verified' WHERE id = ?", (user_id,))
        conn.commit()
    flash("User verified successfully!", "success")
    return redirect(url_for("admin"))


@app.route("/revoke/<int:user_id>", methods=["POST"])
@admin_required
def revoke_user(user_id):
    with get_db() as conn:
        conn.execute("UPDATE users SET status = 'Unverified' WHERE id = ?", (user_id,))
        conn.commit()
    flash("User verification revoked.", "warning")
    return redirect(url_for("admin"))


@app.route("/admin/reviews/<int:review_id>/approve", methods=["POST"])
@admin_required
def approve_review(review_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE transport_reviews SET status = 'Approved' WHERE id = ?", (review_id,)
        )
        conn.commit()
    return redirect(url_for("admin"))


@app.route("/admin/reviews/<int:review_id>/reject", methods=["POST"])
@admin_required
def reject_review(review_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE transport_reviews SET status = 'Rejected' WHERE id = ?", (review_id,)
        )
        conn.commit()
    return redirect(url_for("admin"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
