import sqlite3
from flask import Blueprint, jsonify, render_template, session, request, redirect, send_file
import json
from io import BytesIO

from static.Helper_eml import DB_PATH

bp_ui = Blueprint('ui', __name__)

@bp_ui.route('/')
def form():
    return render_template('index.html')

@bp_ui.route('/Forum')
def Forum():
    return render_template('Forum.html')

@bp_ui.route('/Dashboard')
def admin():
    return render_template('Dashboard.html')

@bp_ui.route('/Account')
def account():
    emails = ''
    if ("user_id" in session and session["user_id"] != None):
        try:
            # Connect to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""SELECT Email.Email_ID, Analysis.Analyzed_At, Email.Title FROM Email 
                           LEFT JOIN Analysis ON Email.Email_ID = Analysis.Email_ID WHERE User_ID = ?""",
                       (session["user_id"], ))
            
            q = cursor.fetchall()
            emails = [(id, str(title).strip('"'), str(time).split('T')[0]) for id, time, title in q]
            print(q)
            print(session["user_id"])

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Database error: {str(e)}",
                "status_code": 500,
                "message": "Failed to load emails due to server error"
            }), 500

    return render_template('Account.html', emails = emails)

@bp_ui.route('/AboutUs')
def info():
    return render_template('AboutUs.html')

@bp_ui.get('/api/email/<int:email_id>')
def get_email_api(email_id):
    """Retrieve email data for analysis view"""
    try:
        if "user_id" not in session or not session.get("user_id"):
            return jsonify({
                "success": False,
                "error": "Not authenticated",
                "status_code": 401
            }), 401
        
        user_id = session["user_id"]
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Email_ID, Title, Body_Text, Sender_IP, Eml_file
                FROM Email 
                WHERE Email_ID = ? AND User_ID = ?
            """, (email_id, user_id))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    "success": False,
                    "error": "Email not found",
                    "status_code": 404
                }), 404
            
            email_id_val, title, body_text, sender_ip, eml_file = result
            
            return jsonify({
                "success": True,
                "status_code": 200,
                "email": {
                    "email_id": email_id_val,
                    "filename": title,
                    "data": {
                        "body_text": body_text,
                        "sender_ip": sender_ip
                    }
                }
            }), 200
        finally:
            conn.close()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "status_code": 500
        }), 500
    
@bp_ui.get('/profile-picture/<int:user_id>')
def get_profile_picture(user_id):
    """Get profile picture of a user by user_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""SELECT Profile_picture FROM User WHERE User_ID = ?""", (user_id,))
    row = cursor.fetchone()
    conn.close()

    # if no picture found, return placeholder
    if not row or row[0] is None:
        return send_file('static/default_profile.png', mimetype='image/png')
    
    picture_bytes = row[0]

    # Return actual stored image
    return send_file(
        BytesIO(picture_bytes),
        mimetype="image/png")