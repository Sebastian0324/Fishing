from flask import Blueprint, request, session, render_template, jsonify
from datetime import datetime, timedelta
import sqlite3

from static.Helper_eml import DB_PATH

bp_forum = Blueprint('bp_forum', __name__)

@bp_forum.post('/Forum_Creator')
def ForumCreator():
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""SELECT Email_ID, Title FROM Email 
                        WHERE User_ID = ?""",
                    (session["user_id"], ))
        
        q = cursor.fetchall()
        emails = [(id, str(title).strip('"')) for id, title in q]

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "status_code": 500,
            "message": "Failed to load emails due to server error"
        }), 500
    
    return jsonify({
            "success": True,
            "status_code": 200,
            "message": "Creation complet",
            "obj": render_template("ForumCreation.html", emails=emails)
        }), 200


@bp_forum.post('/Forum_Creation')
def ForumCreation():
    if (request.form.get("Selected-email") == None or request.form.get("title") == None or request.form.get("description") == None):
        return jsonify({
            "success": False,
            "error": "Missing required fields",
            "status_code": 400,
            "message": "Selected-email, title, and description are required"
        }), 400
    
    eml_id = request.form.get("Selected-email")
    title = request.form.get("title")
    text = request.form.get("description")

    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""INSERT INTO Discussion (
                            Email_ID, Title, Text
                        ) VALUES (?, ?, ?)""", (eml_id, title, text))
        conn.commit()

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "status_code": 500,
            "message": "Failed due to server error"
        }), 500

    return jsonify({
            "success": True,
            "status_code": 200,
            "message": "Creation complet",
        }), 200


def TimeDiff(date):
    general_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    diff = now - general_time - timedelta(hours=1)

    if (diff.total_seconds() < 3600):
        diff = str(int(diff.total_seconds() / 60)) + " Minutes"
    elif (diff.total_seconds() < 86400):
        diff = str(int(diff.total_seconds() / 3600)) + " Hours"
    else:
        diff = str(diff.days) + " Days"

    return diff

def GetForumPosts():
    posts = []
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""SELECT Discussion_ID, Title, Created_At FROM Discussion""")

        q = cursor.fetchall()
        posts = [[id, t, TimeDiff(d), 0] for id, t, d in q]
        posts.reverse()

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "status_code": 500,
            "message": "Failed due to server error"
        }), 500
    
    return posts or [[0, "None", "--", 0]]

@bp_forum.post('/Get_Forum')
def GetForum():
    data = request.get_json(silent=True) or {}
    if (data.get("post_id") == None):
        return jsonify({
            "success": False,
            "error": "Missing required fields",
            "status_code": 400,
            "message": "Forum ID is required"
        }), 400
    
    post_id = data.get("post_id")

    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""SELECT Discussion.Title, Discussion.Text, Discussion.Created_At, 
                       Discussion.Updated_At, Email.Eml_file FROM Discussion JOIN Email ON 
                       Email.Email_ID = Discussion.Email_ID WHERE Discussion.Discussion_ID =?""",
                    (post_id, ))

        q = cursor.fetchone()

        post = [q[0], q[1], q[2], q[3]]
        # eml = render_template(q[4])

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "status_code": 500,
            "message": "Failed due to server error"
        }), 500

    return jsonify({
            "success": True,
            "status_code": 200,
            "message": "Creation complet",
            "Forum": post,
            # "eml": eml,
        }), 200

