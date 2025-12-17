from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# DATABASE SETUP

DB_NAME = 'safety_reports.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            selected_pills TEXT,
            selected_scale TEXT,
            step3_option TEXT,
            toggles TEXT,
            notes TEXT,
            timestamp TEXT
        )
    ''')
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

# Initialize database
init_db()

# ROUTES

@app.route('/')
def homepage():
    return render_template('MOTUWALanding.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template('ContactSupport.html')


# API ENDPOINT FOR QUICK REPORT SUBMISSION
@app.route('/submit-report', methods=['POST'])
def submit_report():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    # Save to SQLite
    save_report(data)

    print("Quick Safety Report Received:", data)
    return jsonify({"status": "success", "message": "Report received successfully"})

if __name__ == '__main__':
    app.run(debug=True)
