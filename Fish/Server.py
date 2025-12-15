#!/usr/bin/python
from flask import Flask, jsonify, send_file, request
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

@app.route('/download/email/<int:email_id>')
def download_single(email_id):
    """Download individual email, analysis, or both depending on query parameters."""
    want_eml = request.args.get("eml") == "1"
    want_analysis = request.args.get("analysis") == "1"

    if not want_eml and not want_analysis:
        return "No download option selected.", 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.Eml_file, e.Title, a.Details_json
        FROM Email e
        LEFT JOIN Analysis a ON e.Email_ID = a.Email_ID
        WHERE e.Email_ID = ?
    """, (email_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "Email not found", 404

    eml_blob, title, details_json = row

    # Sanitize title for filenames
    safe_title = "".join(c for c in title if c.isalnum() or c in [' ', '-', '_']).rstrip().replace(" ", "_")

    # CASE 1: Only .eml
    if want_eml and not want_analysis:
        return send_file(
            BytesIO(eml_blob),
            mimetype="message/rfc822",
            download_name=f"{safe_title}.eml",
            as_attachment=True
        )

    # CASE 2: Only analysis
    if want_analysis and not want_eml:
        return send_file(
            BytesIO(details_json.encode("utf-8") if details_json else b"{}"),
            mimetype="application/json",
            download_name=f"{safe_title}-analysis.json",
            as_attachment=True
        )

    # CASE 3: Both 
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        if eml_blob:
            z.writestr(f"{safe_title}.eml", eml_blob)
        if details_json:
            z.writestr(f"{safe_title}-analysis.json", details_json.encode("utf-8") if details_json else b"{}")

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        download_name=f"{safe_title}_bundle.zip",
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
