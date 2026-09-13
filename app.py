import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enables index.html to communicate with this backend

DB_NAME = "appointments.db"
CLINIC_EMAIL = "baruchimedicalcentre@gmail.com"

# Email Configuration (Set environment variables or edit credentials)
EMAIL_SENDER = os.environ.get("SENDER_EMAIL", CLINIC_EMAIL)
EMAIL_PASSWORD = os.environ.get("SENDER_APP_PASSWORD", "")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def send_email_notification(name, phone, preferred_date, message):
    if not EMAIL_PASSWORD:
        print("Email password not set; skipping email alert.")
        return

    subject = f"New Appointment Request: {name}"
    body = f"""
    New appointment request received:

    Name: {name}
    Phone: {phone}
    Preferred Date: {preferred_date}
    Message/Reason: {message}
    """

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = CLINIC_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Notification email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/api/book', methods=['POST'])
def book_appointment():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data"}), 400

    name = data.get('name')
    phone = data.get('phone')
    preferred_date = data.get('preferred_date')
    message = data.get('message', '')

    if not name or not phone or not preferred_date:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    # Save record to SQLite Database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO appointments (name, phone, preferred_date, message) VALUES (?, ?, ?, ?)",
        (name, phone, preferred_date, message)
    )
    conn.commit()
    conn.close()

    # Trigger Email Alert
    send_email_notification(name, phone, preferred_date, message)

    return jsonify({"status": "success", "message": "Appointment booked successfully!"}), 201

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, preferred_date, message, created_at FROM appointments ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    appointments = [
        {"id": r[0], "name": r[1], "phone": r[2], "preferred_date": r[3], "message": r[4], "created_at": r[5]}
        for r in rows
    ]
    return jsonify({"status": "success", "data": appointments}), 200

if __name__ == '__main__':
    init_db()
    print("Starting local backend server on port 5000...")
    app.run(host='0.0.0.0', port=5000)
