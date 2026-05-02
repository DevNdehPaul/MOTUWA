from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_from_directory
import os
os.makedirs('uploads', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
import sqlite3
import re
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import smtplib
from email.message import EmailMessage
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "AdminPrincaMotuwa@gmail.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "DecJanFebMotuwa1201022026&")
app.secret_key  = os.environ.get("SECRET_KEY", "super_secret_key")

DB_NAME = 'safety_reports.db'

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users table — column names match existing Railway DB
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT NOT NULL,
            email            TEXT NOT NULL UNIQUE,
            phone            TEXT NOT NULL,
            emergency_email1 TEXT NOT NULL,
            emergency_phone1 TEXT NOT NULL,
            emergency_email2 TEXT NOT NULL,
            emergency_phone2 TEXT NOT NULL,
            password         TEXT NOT NULL,
            national_id_file TEXT,
            status           TEXT DEFAULT 'Unverified',
            timestamp        TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS transport_reviews (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER,
            transport_type TEXT,
            license_plate  TEXT,
            route          TEXT,
            company        TEXT,
            driver_name    TEXT,
            driver_contact TEXT,
            driver_behavior TEXT,
            driving_quality TEXT,
            rating         INTEGER,
            review         TEXT,
            created_at     TEXT,
            status         TEXT DEFAULT 'Pending'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT,
            email     TEXT,
            topic     TEXT,
            phone     TEXT,
            ride_date TEXT,
            message   TEXT,
            timestamp TEXT
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
    conn.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_password(password):
    return (
        len(password) >= 8
        and re.search(r"[A-Za-z]", password)
        and re.search(r"\d", password)
        and re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
    )


def send_email(to_email, subject, body):
    EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "paulndeh86@gmail.com")
    EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "qqww pglu zzje bcsd")

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From']    = EMAIL_ADDRESS
        msg['To']      = to_email
        msg.set_content(body)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        app.logger.error("Email failed: %s", e)


def monitor_ride(report_id, interval=60):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT plate_number, vehicle_type, driver_name, pickup_text, dest_text,
               emergency_name, emergency_email
        FROM ride_reports WHERE id = ?
    """, (report_id,))
    ride = cursor.fetchone()
    conn.close()

    if not ride:
        return

    subject = "🚨 MOTUWA Alert: Ride Monitoring"
    body = f"""
Hello {ride[5]},

Your loved one is on a ride. Details:
  Taxi   : {ride[1]} ({ride[0]})
  Driver : {ride[2]}
  Route  : {ride[3]} → {ride[4]}

This alert repeats every minute until the ride is marked safe.

— MOTUWA Safety Platform
"""
    while True:
        with sqlite3.connect(DB_NAME) as c:
            active = c.execute(
                "SELECT is_active FROM ride_reports WHERE id = ?", (report_id,)
            ).fetchone()
        if not active or not active[0]:
            break
        send_email(ride[6], subject, body)
        time.sleep(interval)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def homepage():
    return render_template('MOTUWALanding.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ── Features / ride registration ──────────────────────────────────────────

@app.route("/features", methods=["GET", "POST"])
def features():
    if request.method == "POST":
        user_id       = session.get("user_id")
        plate_number  = request.form.get("plate_number")
        vehicle_type  = request.form.get("vehicle_type")
        driver_name   = request.form.get("driver_name")
        driver_id     = request.form.get("driver_id")
        pickup_text   = request.form.get("pickup_text")
        dest_text     = request.form.get("dest_text")
        unsafe_notes  = request.form.get("unsafe_notes")
        emergency_name  = request.form.get("emergency_name")
        emergency_email = request.form.get("emergency_email")
        created_at    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ride_reports
            (user_id, plate_number, vehicle_type, driver_name, driver_id,
             pickup_text, dest_text, unsafe_notes, emergency_name, emergency_email, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, plate_number, vehicle_type, driver_name, driver_id,
              pickup_text, dest_text, unsafe_notes, emergency_name, emergency_email, created_at))
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()

        threading.Thread(target=monitor_ride, args=(report_id,), daemon=True).start()

        return render_template(
            "FeaturesFlow.html",
            alert_message="Ride monitoring started. Emergency contact will receive emails every minute."
        )

    return render_template("FeaturesFlow.html")


# ── Contact ────────────────────────────────────────────────────────────────

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name      = request.form.get("name")
        email     = request.form.get("email")
        topic     = request.form.get("topic")
        phone     = request.form.get("phone")
        ride_date = request.form.get("ride_date")
        message   = request.form.get("message")
        attachment = request.files.get("attachment")

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            INSERT INTO contacts (name, email, topic, phone, ride_date, message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, email, topic, phone, ride_date, message, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        if attachment and attachment.filename:
            filename = secure_filename(attachment.filename)
            attachment.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        flash("Message sent successfully!", "success")
        return redirect(url_for("contact"))

    return render_template('ContactSupport.html')


# ── Auth ───────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if email == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session["role"] = "admin"
            flash("Admin login successful!", "success")
            return redirect(url_for("admin"))

        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

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
        name             = request.form.get("name", "").strip()
        email            = request.form.get("email", "").strip()
        phone            = request.form.get("phone", "").strip()
        emergency_email1 = request.form.get("emergency_email1", "")
        emergency_phone1 = request.form.get("emergency_phone1", "")
        emergency_email2 = request.form.get("emergency_email2", "")
        emergency_phone2 = request.form.get("emergency_phone2", "")
        password         = request.form.get("password", "")
        national_id      = request.files.get("national_id")

        if not valid_password(password):
            flash("Password must be at least 8 characters and include letters, numbers, and special symbols.", "danger")
            return redirect(url_for("signup"))

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            flash("Email already exists. Please log in.", "danger")
            conn.close()
            return redirect(url_for("signup"))

        filename = None
        if national_id and national_id.filename:
            filename = secure_filename(national_id.filename)
            national_id.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        hashed_password = generate_password_hash(password)
        c.execute("""
            INSERT INTO users
            (name, email, phone, emergency_email1, emergency_phone1,
             emergency_email2, emergency_phone2, password, national_id_file, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, emergency_email1, emergency_phone1,
              emergency_email2, emergency_phone2,
              hashed_password, filename, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        flash("Account created successfully!", "success")
        return redirect(url_for("login"))

    return render_template('UserRegistration.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("homepage"))


# ── Reports / blog ─────────────────────────────────────────────────────────

@app.route("/submit-report", methods=["GET", "POST"])
def submit_report():
    if request.method == "POST":
        user_id        = session.get("user_id")
        transport_type = request.form.get("transport_type")
        license_plate  = request.form.get("license_plate")
        route_name     = request.form.get("route")
        company        = request.form.get("company")
        driver_name    = request.form.get("driver_name")
        driver_contact = request.form.get("driver_contact")
        driver_behavior = request.form.get("driver_behavior")
        driving_quality = request.form.get("driving_quality")
        rating         = request.form.get("rating")
        review         = request.form.get("review")
        created_at     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transport_reviews
            (user_id, transport_type, license_plate, route, company,
             driver_name, driver_contact, driver_behavior,
             driving_quality, rating, review, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, transport_type, license_plate, route_name, company,
              driver_name, driver_contact, driver_behavior,
              driving_quality, rating, review, created_at))
        conn.commit()
        conn.close()

        return redirect("/blog")

    return render_template("QuickReport.html")


@app.route("/blog")
def blog():
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tr.transport_type, tr.license_plate, tr.route, tr.company,
               tr.driver_name, tr.driver_contact, tr.driver_behavior,
               tr.driving_quality, tr.rating, tr.review, tr.created_at,
               u.name AS user_name, u.email AS user_email
        FROM transport_reviews tr
        LEFT JOIN users u ON tr.user_id = u.id
        WHERE tr.status = 'Approved'
        ORDER BY tr.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    formatted_reports = []
    for r in rows:
        report = {
            "transport_type":  r[0],
            "license_plate":   r[1],
            "route":           r[2],
            "company":         r[3],
            "driver_name":     r[4],
            "driver_contact":  r[5],
            "driver_behavior": r[6],
            "driving_quality": r[7],
            "rating":          r[8],
            "review":          r[9],
            "created_at":      r[10],
            "user_name":       r[11],
            "user_email":      r[12],
        }
        report["is_new"] = report["created_at"] >= two_days_ago
        formatted_reports.append(report)

    return render_template("Weblog.html", reports=formatted_reports)


# ── Admin ──────────────────────────────────────────────────────────────────

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT id, name, email, phone,
               emergency_email1, emergency_phone1,
               emergency_email2, emergency_phone2,
               timestamp, national_id_file, status
        FROM users
    """)
    users = c.fetchall()

    c.execute("""
        SELECT tr.id, tr.transport_type, tr.license_plate, tr.route, tr.company,
               tr.driver_name, tr.driver_contact, tr.driver_behavior, tr.driving_quality,
               tr.rating, tr.review, tr.created_at, tr.status,
               u.name AS author_name, u.email AS author_email
        FROM transport_reviews tr
        LEFT JOIN users u ON tr.user_id = u.id
        ORDER BY tr.created_at DESC
    """)
    reviews = c.fetchall()
    conn.close()

    return render_template("MotuwaAdmin.html", users=users, user1s=users, reviews=reviews)


@app.route("/verify/<int:user_id>", methods=["POST"])
def verify_user(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET status = 'Verified' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User verified successfully!", "success")
    return redirect(url_for("admin"))


@app.route("/revoke/<int:user_id>", methods=["POST"])
def revoke_user(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET status = 'Unverified' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User verification revoked.", "warning")
    return redirect(url_for("admin"))


@app.route("/admin/reviews/<int:review_id>/approve", methods=["POST"])
def approve_review(review_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE transport_reviews SET status = 'Approved' WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


@app.route("/admin/reviews/<int:review_id>/reject", methods=["POST"])
def reject_review(review_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE transport_reviews SET status = 'Rejected' WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
