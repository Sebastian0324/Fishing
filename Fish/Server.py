#!/usr/bin/python
from flask import Flask, jsonify, send_file
from flask_session import Session
from static.Helper_eml import init_db
import zipfile 
from io import BytesIO
import sqlite3

DB_PATH = "db/emails.db"
app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Limit upload size to 1MB
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        "success": False,
        "error": "File too large",
        "status_code": 413,
        "message": "File exceeds the 1MB size limit. Please upload a smaller file."
    }), 413

@app.route('/check/emails')
def check_emails():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Email")
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({"hasEmails": count > 0})

@app.route('/check/analysis')
def check_analysis():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Analysis")
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({"hasAnalysis": count > 0})

@app.route('/check/both')
def check_both():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Email")
    hasEmails = cursor.fetchone()[0] > 0
    cursor.execute("SELECT COUNT(*) FROM Analysis")
    hasAnalysis = cursor.fetchone()[0] > 0
    conn.close()
    return jsonify({"hasEmails": hasEmails, "hasAnalysis": hasAnalysis})


@app.route('/download/emails')
def download_emails():
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT Email_ID, Eml_file FROM Email")
    emails = cursor.fetchall()
    conn.close()
    
    if not emails:
        return "No emails found in database.", 404

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for email_id, eml_blob in emails:
            filename = f"email_{email_id}.eml"
            zip_file.writestr(filename, eml_blob)
    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        download_name="angler_phishing_emails.zip",
        as_attachment=True
        )
    
@app.route('/download/analysis')
def download_analysis():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT Email_ID, Details_json FROM Analysis")
    analyses = cursor.fetchall()
    conn.close()

    if not analyses:
        return "No analyses found in database.", 404

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for email_id, details_json in analyses:
            filename = f"analysis_{email_id}.json"
            zip_file.writestr(filename, details_json or "{}")
    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        download_name="angler_phishing_analysis.zip",
        as_attachment=True
    )

@app.route('/download/both')
def download_both():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.Email_ID, e.Eml_file, a.Details_json
        FROM Email e
        LEFT JOIN Analysis a ON e.Email_ID = a.Email_ID
    """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No emails found in database.", 404

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for email_id, eml_blob, details_json in rows:
            # Emails folder
            if eml_blob:
                zip_file.writestr(f"emails/email_{email_id}.eml", eml_blob)
            # Analysis folder (if exists)
            if details_json:
                zip_file.writestr(f"analysis/analysis_{email_id}.json", details_json)

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        download_name="angler_phishing_emails_and_analysis.zip",
        as_attachment=True
    )




# Register endpoint blueprints
from endpoints import register_blueprints
register_blueprints(app)

# Initialize database on startup
init_db()
print("Database initialized successfully")

if __name__ == '__main__':
    app.run(debug=True, load_dotenv=True)
