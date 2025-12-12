import sqlite3
from flask import Blueprint, jsonify, render_template, session, request, redirect, send_file
import json
from io import BytesIO
from datetime import datetime, timedelta

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
        # Add admin-specific statistics if user is admin
    if session.get('name') == 'admin':
        admin_stats = get_admin_statistics()
        stats.update(admin_stats)
    frequent_senders = get_frequent_sender_statistics()
    common_subjects = get_common_subjects_statistics()  # aggregates by Email.Tag (categories)
    most_commented = get_most_commented_statistics()
    return render_template('Statistics.html', stats=stats, frequent_senders=frequent_senders, common_subjects=common_subjects, most_commented=most_commented)

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


def get_common_subjects_statistics(limit=10, days=30):
    """Aggregate by Email.Tag (whitelisted categories). Return top and historical lists.
    This function replaces raw subject grouping with categorized Tag statistics.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Top overall tags
        cursor.execute("""
            SELECT Tag AS tag, COUNT(*) as count
            FROM Email
            WHERE Tag IS NOT NULL AND TRIM(Tag) != ''
            GROUP BY Tag
            ORDER BY count DESC
            LIMIT ?
        """, (limit,))
        top = cursor.fetchall()

        # Top tags in the last `days` days using Received_At timestamp
        cutoff = (datetime.utcnow() - timedelta(days=days)).replace(microsecond=0).isoformat() + 'Z'
        cursor.execute("""
            SELECT Tag AS tag, COUNT(*) as count
            FROM Email
            WHERE Received_At >= ? AND Tag IS NOT NULL AND TRIM(Tag) != ''
            GROUP BY Tag
            ORDER BY count DESC
            LIMIT ?
        """, (cutoff, limit))
        historical = cursor.fetchall()

        conn.close()
        # Return lists of dicts for easy template use (key names match macro expectations)
        return {
            "top": [{"tag": t, "count": c} for t, c in top],
            "historical": [{"tag": t, "count": c} for t, c in historical]
        }
    except Exception as e:
        print(f"Error fetching tag statistics: {e}")
        return {"top": [], "historical": []}


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

def get_admin_statistics():
    """Get admin-specific statistics including system status and moderation data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total uploads (emails)
        cursor.execute("SELECT COUNT(*) FROM Email")
        total_uploads = cursor.fetchone()[0]
        
        # Active sessions (approximate - count unique users with recent activity)
        cursor.execute("SELECT COUNT(DISTINCT User_ID) FROM Email WHERE datetime(Received_At) > datetime('now', '-24 hours')")
        active_sessions = cursor.fetchone()[0]
        
        # Phishing emails detected
        cursor.execute("SELECT COUNT(*) FROM Analysis WHERE Verdict = 'Phishing'")
        phishing_detected = cursor.fetchone()[0]
        
        # Total forum posts
        cursor.execute("SELECT COUNT(*) FROM Discussion")
        total_posts = cursor.fetchone()[0]
        
        # Total comments
        cursor.execute("SELECT COUNT(*) FROM Comment")
        total_comments = cursor.fetchone()[0]
        
        # Pending moderations (discussions without any comments could be pending review)
        cursor.execute("""
            SELECT COUNT(*) FROM Discussion d
            LEFT JOIN Comment c ON d.Discussion_ID = c.Discussion_ID
            WHERE c.Comment_ID IS NULL
        """)
        pending_moderations = cursor.fetchone()[0]
        
        # Flagged IPs (IPs with phishing or suspicious emails)
        cursor.execute("""
            SELECT COUNT(DISTINCT e.Sender_IP)
            FROM Email e
            JOIN Analysis a ON e.Email_ID = a.Email_ID
            WHERE e.Sender_IP IS NOT NULL AND e.Sender_IP != ''
            AND a.Verdict IN ('Phishing', 'Suspicious')
        """)
        flagged_ips = cursor.fetchone()[0]
        
        # Get database file size for storage info
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size_bytes = cursor.fetchone()[0]
        db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
        
        # Get last analysis timestamp
        cursor.execute("SELECT MAX(Analyzed_At) FROM Analysis WHERE Analyzed = 1")
        last_backup = cursor.fetchone()[0]
        if last_backup:
         
            try:
                last_backup_dt = datetime.fromisoformat(last_backup)
                now = datetime.now()
                diff = now - last_backup_dt
                if diff.days > 0:
                    last_backup = f"{diff.days} days ago"
                else:
                    last_backup = f"{diff.seconds // 3600} hours and {(diff.seconds // 60) % 60} minutes ago"
            except:
                last_backup = "Recently"

        else:
            last_backup = "Never"
        
        conn.close()
        
        # Check API service status
        server_status = "Online"  # If this code runs, server is online
        database_status = "Connected"  # If we got here, DB is connected
        
        # Check VirusTotal API
        virustotal_status = "Disconnected"
        try:
            from api.VirusTotal import VirusTotal
            vt = VirusTotal()
            if vt.api_key:
                virustotal_status = "Connected"
        except:
            virustotal_status = "Not Configured"
        
        # Check AbuseIPDB API
        abuseipdb_status = "Disconnected"
        try:
            from api.AbuseIp import AbuseIPDB
            abuse = AbuseIPDB()
            if abuse.api_key:
                abuseipdb_status = "Connected"
        except:
            abuseipdb_status = "Not Configured"
        
        # Check LLM Service
        llm_status = "Disconnected"
        try:
            import os
            llm_key = os.getenv('API_KEY') or os.getenv('API_KEY')
            if llm_key:
                llm_status = "Running"
        except:
            llm_status = "Not Configured"
        
        # API Services status (general)
        api_services_status = "Active" if any([
            virustotal_status == "Connected",
            abuseipdb_status == "Connected",
            llm_status == "Running"
        ]) else "Limited"
        
        return {
            "total_uploads": total_uploads,
            "active_sessions": active_sessions,
            "phishing_detected": phishing_detected,
            "total_posts": total_posts,
            "total_comments": total_comments,
            "pending_moderations": pending_moderations,
            "flagged_ips": flagged_ips,
            "storage_available": f"{db_size_mb} MB",
            "last_backup": last_backup,
            "server_status": server_status,
            "database_status": database_status,
            "api_services_status": api_services_status,
            "virustotal_status": virustotal_status,
            "abuseipdb_status": abuseipdb_status,
            "llm_status": llm_status
        }
    except Exception as e:
        print(f"Error fetching admin statistics: {e}")
        return {
            "total_uploads": 0,
            "active_sessions": 0,
            "phishing_detected": 0,
            "total_posts": 0,
            "total_comments": 0,
            "pending_moderations": 0,
            "flagged_ips": 0,
            "storage_available": "Unknown",
            "last_backup": "Unknown",
            "server_status": "Error",
            "database_status": "Error",
            "api_services_status": "Error",
            "virustotal_status": "Error",
            "abuseipdb_status": "Error",
            "llm_status": "Error"
        }

def get_most_commented_statistics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT e.Title, COUNT(c.Comment_ID) AS comment_count
            FROM Email e
            JOIN Discussion d ON e.Email_ID = d.Email_ID
            JOIN Comment c ON d.Discussion_ID = c.Discussion_ID
            GROUP BY e.Email_ID, e.Title
            ORDER BY comment_count DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        return {
            "top_commented_emails": [(title, count) for (title, count) in rows]
        }

    except Exception as e:
        print(f"Error fetching most commented statistics: {e}")
        return {"top_commented_emails": []}

    finally:
        conn.close()

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


@bp_ui.delete('/api/email/<int:email_id>')
def delete_email_api(email_id):
    """Delete an email and all its associated data (analysis, etc.)"""
    try:
        # Check authentication
        if "user_id" not in session or not session.get("user_id"):
            return jsonify({
                "success": False,
                "error": "Not authenticated",
                "status_code": 401
            }), 401
        
        user_id = session["user_id"]
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            
            # First verify the email belongs to the current user
            cursor.execute("""
                SELECT Email_ID FROM Email 
                WHERE Email_ID = ? AND User_ID = ?
            """, (email_id, user_id))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    "success": False,
                    "error": "Email not found or you do not have permission to delete it",
                    "status_code": 404
                }), 404
            
            cursor.execute("""
                DELETE FROM Analysis WHERE Email_ID = ?
            """, (email_id,))
            
            # Check if there are any discussions linked to this email
            cursor.execute("""
                SELECT Discussion_ID FROM Discussion WHERE Email_ID = ?
            """, (email_id,))
            discussions = cursor.fetchall()
            
            for (discussion_id,) in discussions:
                cursor.execute("""
                    DELETE FROM Comment WHERE Discussion_ID = ?
                """, (discussion_id,))
            
            # Delete discussions linked to this email
            cursor.execute("""
                DELETE FROM Discussion WHERE Email_ID = ?
            """, (email_id,))
            
            cursor.execute("""
                DELETE FROM Email WHERE Email_ID = ? AND User_ID = ?
            """, (email_id, user_id))
            
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": "Email and all associated data deleted successfully",
                "status_code": 200
            }), 200
            
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "status_code": 500
        }), 500
