import sqlite3
from flask import Blueprint, jsonify, render_template, session, request, redirect, send_file
import json
from io import BytesIO

from static.Helper_eml import DB_PATH
from endpoints.forum import GetForumPosts

bp_ui = Blueprint('ui', __name__)

@bp_ui.route('/')
def form():
    return render_template('index.html')

@bp_ui.route('/Forum')
def Forum():
    posts = GetForumPosts()
    return render_template('Forum.html', post=posts)

@bp_ui.route('/Statistics')
def admin():
    stats = get_general_statistics()
    frequent_senders = get_frequent_sender_statistics()
    return render_template('Statistics.html', stats=stats, frequent_senders=frequent_senders)

def get_frequent_sender_statistics():
    """Get frequent sender IP statistics from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Top sender IPs by email (all time)
        cursor.execute("""
            SELECT Sender_IP, COUNT(*) as count
            FROM Email 
            WHERE Sender_IP IS NOT NULL AND Sender_IP != ''
            GROUP BY Sender_IP
            ORDER BY count DESC
            LIMIT 10
        """)
        top_senders = cursor.fetchall()
        
        # Top sender IPs with phishing emails
        cursor.execute("""
            SELECT e.Sender_IP, COUNT(*) as count
            FROM Email e
            JOIN Analysis a ON e.Email_ID = a.Email_ID
            WHERE e.Sender_IP IS NOT NULL AND e.Sender_IP != ''
            AND a.Verdict = 'Phishing'
            GROUP BY e.Sender_IP
            ORDER BY count DESC
            LIMIT 10
        """)
        top_phishing_senders = cursor.fetchall()
        
        # Top sender IPs that are suspicious
        cursor.execute("""
            SELECT e.Sender_IP, COUNT(*) as count
            FROM Email e
            JOIN Analysis a ON e.Email_ID = a.Email_ID
            WHERE e.Sender_IP IS NOT NULL AND e.Sender_IP != ''
            AND a.Verdict = 'Suspicious'
            GROUP BY e.Sender_IP
            ORDER BY count DESC
            LIMIT 10
        """)
        top_suspicious_senders = cursor.fetchall()
        
        # Total unique sender IPs
        cursor.execute("""
            SELECT COUNT(DISTINCT Sender_IP)
            FROM Email 
            WHERE Sender_IP IS NOT NULL AND Sender_IP != ''
        """)
        total_unique_ips = cursor.fetchone()[0]
        
        # IPs flagged as dangerous (phishing or suspicious)
        cursor.execute("""
            SELECT COUNT(DISTINCT e.Sender_IP)
            FROM Email e
            JOIN Analysis a ON e.Email_ID = a.Email_ID
            WHERE e.Sender_IP IS NOT NULL AND e.Sender_IP != ''
            AND a.Verdict IN ('Phishing', 'Suspicious')
        """)
        dangerous_ips = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "top_senders": top_senders,
            "top_phishing_senders": top_phishing_senders,
            "top_suspicious_senders": top_suspicious_senders,
            "total_unique_ips": total_unique_ips,
            "dangerous_ips": dangerous_ips
        }
    except Exception as e:
        print(f"Error fetching frequent sender statistics: {e}")
        return {
            "top_senders": [],
            "top_phishing_senders": [],
            "top_suspicious_senders": [],
            "total_unique_ips": 0,
            "dangerous_ips": 0
        }

def get_general_statistics():
    """Get general statistics from the database for public display"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total emails analyzed
        cursor.execute("SELECT COUNT(*) FROM Email")
        total_emails = cursor.fetchone()[0]
        
        # Total users registered
        cursor.execute("SELECT COUNT(*) FROM User WHERE User_ID > 1")  # Exclude system users
        total_users = cursor.fetchone()[0]
        
        # Total analyses completed
        cursor.execute("SELECT COUNT(*) FROM Analysis WHERE Analyzed = 1")
        total_analyses = cursor.fetchone()[0]
        
        # Verdict breakdown
        cursor.execute("""
            SELECT Verdict, COUNT(*) 
            FROM Analysis 
            WHERE Verdict IS NOT NULL 
            GROUP BY Verdict
        """)
        verdict_counts = dict(cursor.fetchall())
        
        # Total forum discussions
        cursor.execute("SELECT COUNT(*) FROM Discussion")
        total_discussions = cursor.fetchone()[0]
        
        # Total comments
        cursor.execute("SELECT COUNT(*) FROM Comment")
        total_comments = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_emails": total_emails,
            "total_users": total_users,
            "total_analyses": total_analyses,
            "phishing_count": verdict_counts.get("Phishing", 0),
            "suspicious_count": verdict_counts.get("Suspicious", 0),
            "benign_count": verdict_counts.get("Benign", 0),
            "total_discussions": total_discussions,
            "total_comments": total_comments
        }
    except Exception as e:
        print(f"Error fetching statistics: {e}")
        return {
            "total_emails": 0,
            "total_users": 0,
            "total_analyses": 0,
            "phishing_count": 0,
            "suspicious_count": 0,
            "benign_count": 0,
            "total_discussions": 0,
            "total_comments": 0
        }

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
