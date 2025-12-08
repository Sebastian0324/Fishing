from flask import Blueprint, request, session, render_template, jsonify
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
