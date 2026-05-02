from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_from_directory
import os
os.makedirs('uploads', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
import sqlite3
import re
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler 
from geopy.distance import geodesic 
import threading
import smtplib
from email.message import EmailMessage
import time
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Hard-coded admin credentials
ADMIN_USERNAME = "AdminPrincaMotuwa@gmail.com"
ADMIN_PASSWORD = "DecJanFebMotuwa1201022026&"
app.secret_key = "super_secret_key"  # Needed for sessions
DB_NAME = 'safety_reports.db'
# Background scheduler 
scheduler = BackgroundScheduler() 
scheduler.start()
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
def get_db(): 
    conn = sqlite3.connect(DB_NAME) 
    conn.row_factory = sqlite3.Row 
    return conn
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users table
    c.execute(""" CREATE TABLE IF NOT EXISTS users (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               email TEXT NOT NULL UNIQUE,
               phone TEXT NOT NULL,
               emergency_name1 TEXT NOT NULL,
               emergency_phone1 TEXT NOT NULL,
               emergency_name2 TEXT NOT NULL,
               emergency_phone2 TEXT NOT NULL,
               password TEXT NOT NULL,
               national_id_file TEXT,
               status TEXT DEFAULT 'Unverified',  
               timestamp TEXT

               ) """)

    # Reports table
    c.execute("""
CREATE TABLE IF NOT EXISTS transport_reviews (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
transport_type TEXT,
license_plate TEXT,
route TEXT,
company TEXT,
driver_name TEXT,
driver_contact TEXT,
driver_behavior TEXT,
driving_quality TEXT,
rating INTEGER,
review TEXT,
created_at TEXT,
status TEXT DEFAULT 'Pending'
)
""")

    # Contact messages table
    c.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            topic TEXT,
            phone TEXT,
            ride_date TEXT,
            message TEXT,
            timestamp TEXT
        )
    ''')

    c.execute("""CREATE TABLE IF NOT EXISTS ride_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    plate_number TEXT,
    vehicle_type TEXT,
    driver_name TEXT,
    driver_id TEXT,
    pickup_text TEXT,
    dest_text TEXT,
    unsafe_notes TEXT,
    emergency_name TEXT,
    emergency_email TEXT,
    created_at TEXT
);
              """)

    conn.commit()
    conn.close()
def save_report(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO reports (selected_pills, selected_scale, step3_option, toggles, notes, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        ', '.join(data.get('selectedPills', [])),
        data.get('selectedScale'),
        data.get('step3Option'),
        ', '.join(data.get('toggles', [])),
        data.get('notes'),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
def valid_password(password): 
    if len(password) < 8:
        return False 
    if not re.search(r"[A-Za-z]", password): # must contain letters 
        return False 
    if not re.search(r"\d", password): # must contain numbers 
        return False 
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): # must contain special char 
        return False 
    return True
def send_alert(contacts, subject, body): 
    # Replace with Twilio/SendGrid for SMS/email in production 
    print(f"[ALERT] {subject}: {body} → {contacts}") 
# Background thread to send alerts every 1 minutes
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

    subject = f"🚨 MOTUWA Alert: Ride Monitoring"
    body = f"""
Hello {ride[5]},

Your Love one is on a ride. Details:
Taxi: {ride[1]} ({ride[0]})
Driver: {ride[2]}
From: {ride[3]} To: {ride[4]}

This alert will repeat every 1 minutes until the ride is marked safe.
"""
    # Loop to send repeated alerts
    while True:
        send_email(ride[6], subject, body)
        time.sleep(interval)
# Function to send email
def send_email(to_email, subject, body):
    EMAIL_ADDRESS = "paulndeh86@gmail.com"
    EMAIL_PASSWORD = "qqww pglu zzje bcsd"
    
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(body)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
@app.route('/')
def homepage():
    return render_template('MOTUWALanding.html')
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route("/features", methods=["GET", "POST"])
def features():
    if request.method == "POST":
        user_id = session.get("user_id")  # logged-in user

        plate_number = request.form.get("plate_number")
        vehicle_type = request.form.get("vehicle_type")
        driver_name = request.form.get("driver_name")
        driver_id = request.form.get("driver_id")
        pickup_text = request.form.get("pickup_text")
        dest_text = request.form.get("dest_text")
        unsafe_notes = request.form.get("unsafe_notes")
        emergency_name = request.form.get("emergency_name")
        emergency_email = request.form.get("emergency_email")

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save report
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

        # Start background thread for email alerts
        threading.Thread(target=monitor_ride, args=(report_id,), daemon=True).start()

        # Render the same page with a success message
        return render_template(
            "FeaturesFlow.html",
            alert_message="Ride monitoring started. Emergency contact will receive emails every 1 minutes."
        )

    return render_template("FeaturesFlow.html")
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        topic = request.form.get("topic")
        phone = request.form.get("phone")
        ride_date = request.form.get("ride_date")
        message = request.form.get("message")
        attachment = request.files.get("attachment")

        # Save to DB
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""INSERT INTO contacts (name, email, topic, phone, ride_date, message, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (name, email, topic, phone, ride_date, message, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        # Optionally save attachment
        if attachment:
            attachment.save(f"uploads/{attachment.filename}")
        flash("Message sent successfully!", "success")
        return redirect(url_for("contact"))
    message = "Response Recorded SucessFully!!!"
    return render_template('ContactSupport.html', message = message)

    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO contacts (name, email, message, timestamp) VALUES (?, ?, ?, ?)",
                  (name, email, message, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        flash("Message sent successfully!", "success")
        return redirect(url_for("contact"))

    return render_template('ContactSupport.html')
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if admin login
        if email == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["role"] = "admin"
            flash("Admin login successful!", "success")
            return redirect(url_for("admin"))  # admin dashboard route

        # Otherwise check normal user login
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = "user"
            flash("Login successful!", "success")
            return redirect(url_for("features"))  # normal user dashboard
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for("login"))

    return render_template("UserLogin.html")
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        emergency_email1 = request.form.get("emergency_email1")
        emergency_name1 = request.form.get("emergency_name1")
        emergency_email2 = request.form.get("emergency_email2")
        emergency_name2 = request.form.get("emergency_name2")
        password = request.form.get("password")
        national_id = request.files.get("national_id")
        if not valid_password(password):
            flash("Password must be at least 8 characters long and include letters, numbers, and special symbols.", "danger")
            return redirect(url_for("signup"))

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email=?", (email, ))
        if c.fetchone():
            flash("Email already exists. Please log in.", "danger")
            return redirect(url_for("signup"))
        # Handle file upload
        filename = None
        if national_id and national_id.filename != "":
            filename = secure_filename(national_id.filename)
            national_id.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        # Insert into database

        hashed_password = generate_password_hash(password)
        c.execute("""INSERT INTO users 
                     (name, email, phone, emergency_name1, emergency_phone1, emergency_name2, emergency_phone2, password, national_id_file, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (name, email, phone, emergency_email1, emergency_name1, emergency_email2, emergency_name2,
                   hashed_password, filename, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        flash("Account created successfully!", "success")
        return redirect(url_for("signup"))

    return render_template('UserRegistration.html')
@app.route("/submit-report", methods=["GET", "POST"])
def submit_report():
    if request.method == "POST":
        # Get form data
        transport_type = request.form.get("transport_type")
        license_plate = request.form.get("license_plate")
        route_name = request.form.get("route")
        company = request.form.get("company")

        driver_name = request.form.get("driver_name")
        driver_contact = request.form.get("driver_contact")
        driver_behavior = request.form.get("driver_behavior")
        driving_quality = request.form.get("driving_quality")

        rating = request.form.get("rating")
        review = request.form.get("review")

        # Get user ID if login system exists
        user_id = session.get("user_id")  # will be None if no login

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save to database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transport_reviews
            (user_id, transport_type, license_plate, route, company,
             driver_name, driver_contact, driver_behavior,
             driving_quality, rating, review, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, transport_type, license_plate, route_name, company,
            driver_name, driver_contact, driver_behavior,
            driving_quality, rating, review, created_at
        ))
        conn.commit()
        conn.close()

        # After submitting, redirect to Weblog.html
        return redirect("/blog")  # assuming /weblog route renders Weblog.html

    # If GET request, show the QuickReport.html page
    return render_template("QuickReport.html")
@app.route("/blog")
def blog():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT transport_reviews.*, users.name, users.email
FROM transport_reviews
LEFT JOIN users ON transport_reviews.user_id = users.id
WHERE transport_reviews.status = 'Approved'
ORDER BY transport_reviews.created_at DESC;

""")
    reports = cursor.fetchall()
    conn.close()

    # Convert to dicts if needed and add "is_new" flag
    formatted_reports = []
    for r in reports:
        report = {
            "transport_type": r[2],
            "license_plate": r[3],
            "route": r[4],
            "company": r[5],
            "driver_name": r[6],
            "driver_contact": r[7],
            "driver_behavior": r[8],
            "driving_quality": r[9],
            "rating": r[10],
            "review": r[11],
            "created_at": r[12],
            "user_name": r[13],  # from users table
            "user_email": r[14] # from users table
        }

        # Check if report is within last 2 days
        report_time = datetime.strptime(report["created_at"], "%Y-%m-%d %H:%M:%S")
        report["is_new"] = (datetime.now() - report_time) <= timedelta(days=2)

        formatted_reports.append(report)

    return render_template("Weblog.html", reports=formatted_reports)
@app.route("/admin")
def admin():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, name, email, timestamp, national_id_file, status FROM users ")
    users = c.fetchall()
    c.execute("""SELECT id, name, email, phone, emergency_name1, emergency_phone1, emergency_name2
                    emergency_email2, timestamp, national_id_file, status
             FROM users""")
    user1s = c.fetchall()
    c.execute("""
    SELECT tr.id, tr.transport_type, tr.license_plate, tr.route, tr.company,
           tr.driver_name, tr.driver_contact, tr.driver_behavior, tr.driving_quality,
           tr.rating, tr.review, tr.created_at, tr.status,
           u.name AS author_name, u.email AS author_email
    FROM transport_reviews tr
    JOIN users u ON tr.user_id = u.id
""")
    reviews = c.fetchall()
    conn.close()
    return render_template("MotuwaAdmin.html", users=users, user1s=user1s, reviews=reviews)
@app.route("/verify/<int:user_id>", methods=["POST"])
def verify_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET status = ? WHERE id = ?", ("Verified", user_id))
    conn.commit()
    conn.close()
    flash("User verified successfully!", "success")
    return redirect(url_for("admin"))
@app.route("/revoke/<int:user_id>", methods=["POST"])
def revoke_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET status = ? WHERE id = ?", ("Unverified", user_id))
    conn.commit()
    conn.close()
    flash("User status revoked.", "danger")
    return redirect(url_for("admin"))
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("homepage"))
@app.route("/admin/reviews/<int:review_id>/approve", methods=["POST"])
def approve_review(review_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Example: mark review as approved
    c.execute("UPDATE transport_reviews SET status = 'Approved' WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))
@app.route("/admin/reviews/<int:review_id>/reject", methods=["POST"])
def reject_review(review_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Example: mark review as rejected
    c.execute("UPDATE transport_reviews SET status = 'Rejected' WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
