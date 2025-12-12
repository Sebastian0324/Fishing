from flask import Blueprint, request, session, render_template, jsonify
from datetime import datetime, timedelta
import sqlite3
import html

from static.Helper_eml import DB_PATH, extract_email_for_display

bp_forum = Blueprint('bp_forum', __name__)

@bp_forum.get('/Forum_Posts_By_Tag')
def ForumPostsByTag():
    tag = request.args.get('tag', '').strip()
    posts = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if tag:
            cursor.execute('''
                SELECT d.Discussion_ID, d.Title, d.Created_At, COUNT(c.Comment_ID) AS comment_count
                FROM Discussion d
                LEFT JOIN Comment c ON c.Discussion_ID = d.Discussion_ID
                JOIN Email e ON d.Email_ID = e.Email_ID
                WHERE e.Tag = ?
                GROUP BY d.Discussion_ID
                ORDER BY d.Created_At DESC
            ''', (tag,))
        else:
            cursor.execute('''
                SELECT d.Discussion_ID, d.Title, d.Created_At, COUNT(c.Comment_ID) AS comment_count
                FROM Discussion d
                LEFT JOIN Comment c ON c.Discussion_ID = d.Discussion_ID
                GROUP BY d.Discussion_ID
                ORDER BY d.Created_At DESC
            ''')
        q = cursor.fetchall()
        posts = [[id, title, TimeDiff(created), count] for id, title, created, count in q]
        posts.reverse()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "status_code": 500,
            "message": "Failed due to server error"
        }), 500
    return jsonify({"success": True, "posts": posts})

MAX_COMMENT_LENGTH = 2000

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
    raw_title = request.form.get("title")
    raw_text = request.form.get("description")

    title = html.escape(raw_title)
    text = html.escape(raw_text)

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

        cursor.execute("""
            SELECT
                d.Discussion_ID,
                d.Title,
                d.Created_At,
                COUNT(c.Comment_ID) AS comment_count
            FROM Discussion d
            LEFT JOIN Comment c
                ON c.Discussion_ID = d.Discussion_ID
            GROUP BY d.Discussion_ID
            ORDER BY d.Created_At DESC
        """)

        q = cursor.fetchall()
        posts = [[id, title, TimeDiff(created), count]
            for id, title, created, count in q]

        posts.reverse()

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "status_code": 500,
            "message": "Failed due to server error"
        }), 500
    
    return posts

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

        # Get discussion details along with user info who uploaded the email and the tag
        cursor.execute("""SELECT Discussion.Title, Discussion.Text, Discussion.Created_At, 
                       Discussion.Updated_At, Email.Tag, Email.Eml_file, User.Username, User.Profile_picture, User.User_ID
                       FROM Discussion 
                       JOIN Email ON Email.Email_ID = Discussion.Email_ID 
                       JOIN User ON User.User_ID = Email.User_ID
                       WHERE Discussion.Discussion_ID = ?""",
                    (post_id, ))

        q = cursor.fetchone()

        post = [q[0], q[1], q[2], q[3], q[4]]
        
        # Parse the email for display (Eml_file is at index 5)
        eml_bytes = q[5]
        email_display = None
        if eml_bytes:
            email_display = extract_email_for_display(eml_bytes)
        
        # User info
        import base64
        profile_pic = None
        if q[7]:
            profile_pic = base64.b64encode(q[7]).decode('utf-8')
        
        user_info = {
            "username": q[6],
            "profile_picture": profile_pic,
            "user_id": q[8]
        }
        
        is_owner = False
        if session.get("user_id") and session["user_id"] == q[8]:
            is_owner = True

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
    "message": "Creation complete",
    "Forum": post,
    "user": user_info,
    "email": email_display,
    "is_owner": is_owner,
    "discussion_id": post_id,
    "is_logged_in": bool(session.get("user_id"))
    }), 200



@bp_forum.delete('/Delete_Discussion/<int:discussion_id>')
def DeleteDiscussion(discussion_id):
    if not session.get("user_id"):
        return jsonify({
            "success": False,
            "error": "Unauthorized",
            "status_code": 401,
            "message": "You must be logged in to delete a discussion"
        }), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""SELECT Discussion.Discussion_ID, Email.User_ID 
                         FROM Discussion 
                         JOIN Email ON Email.Email_ID = Discussion.Email_ID 
                         WHERE Discussion.Discussion_ID = ?""",
                      (discussion_id,))
        
        result = cursor.fetchone()
        
        if not result:
            return jsonify({
                "success": False,
                "error": "Not found",
                "status_code": 404,
                "message": "Discussion not found"
            }), 404
        
        owner_id = result[1]
        
        if owner_id != session["user_id"]:
            return jsonify({
                "success": False,
                "error": "Forbidden",
                "status_code": 403,
                "message": "You can only delete discussions you created"
            }), 403
        
        cursor.execute("""DELETE FROM Comment WHERE Discussion_ID = ?""", (discussion_id,))
        cursor.execute("""DELETE FROM Discussion WHERE Discussion_ID = ?""", (discussion_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "status_code": 200,
            "message": "Discussion deleted successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "status_code": 500,
            "message": "Failed to delete discussion due to server error"
        }), 500

@bp_forum.post("/comment/create")
def create_comment():
    if not session.get("user_id"):
        return jsonify({
            "success": False,
            "error": "Not authenticated"
        }), 401

    # Check if user is allowed to post
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""SELECT can_post FROM User WHERE User_ID = ?""", (session["user_id"],))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return jsonify({
                "success": False,
                "error": "You have been restricted from posting by an administrator"
            }), 403
    except Exception as e:
        return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request"}), 400

    discussion_id = data.get("discussion_id")
    text = data.get("text", "").strip()
    parent_id = data.get("parent_id")

    if len(text) > MAX_COMMENT_LENGTH:
        return jsonify({
        "success": False,
        "error": "Comment too long"
    }), 413

    if not discussion_id or not text:
        return jsonify({"success": False, "error": "Missing fields"}), 400

    # sanitization to prevent XSS
    safe_text = html.escape(text)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Comment (Discussion_ID, User_ID, Parent_ID, Text)
            VALUES (?, ?, ?, ?)
        """, (discussion_id, session["user_id"], parent_id, safe_text))

        conn.commit()
        conn.close()

        return jsonify({"success": True}), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp_forum.get("/comments/<int:discussion_id>")
def get_comments(discussion_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                Comment.Comment_ID,
                Comment.Parent_ID,
                Comment.Text,
                Comment.Created_At,
                User.User_ID,
                User.Username,
                User.can_post
            FROM Comment
            JOIN User ON User.User_ID = Comment.User_ID
            WHERE Comment.Discussion_ID = ?
            ORDER BY Comment.Created_At ASC
        """, (discussion_id,))

        rows = cursor.fetchall()
        conn.close()

        # Check if current user is admin
        is_admin = session.get("name") == "admin"

        # create flat comments
        comments = []
        for r in rows:
            comments.append({
                "id": r[0],
                "parent_id": r[1],
                "text": r[2],
                "created_at": r[3],
                "user": {
                    "id": r[4],
                    "username": r[5],
                    "can_post": bool(r[6])
                },
                "is_owner": session.get("user_id") == r[4],
                "can_delete": (session.get("user_id") == r[4]) or is_admin
            })
        return jsonify({"success": True, "comments": comments, "is_logged_in": bool(session.get("user_id")), "is_admin": is_admin}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp_forum.post("/comment/edit")
def edit_comment():
    if "user_id" not in session:
        return jsonify({"success": False}), 401

    data = request.get_json(silent=True) or {}
    comment_id = data.get("comment_id")
    new_text = data.get("text", "").strip()

    if len(new_text) > MAX_COMMENT_LENGTH:
        return jsonify({
        "success": False,
        "error": "Comment too long"
    }), 413

    if not comment_id or not new_text:
        return jsonify({"success": False}), 400

    safe_text = html.escape(new_text)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Comment
        SET Text = ?
        WHERE Comment_ID = ? AND User_ID = ?
    """, (safe_text, comment_id, session["user_id"]))

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"success": False, "error": "Not allowed"}), 403

    conn.commit()
    conn.close()
    return jsonify({
            "success": True,
            "status_code": 200,
            "message": "Comment edited successfully"
        }), 200

@bp_forum.post("/comment/delete")
def delete_comment():
    if "user_id" not in session:
        return jsonify({"success": False}), 401

    data = request.get_json(silent=True) or {}
    comment_id = data.get("comment_id")

    if not comment_id:
        return jsonify({"success": False, "error": "Missing comment_id"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if current user is the comment owner
        cursor.execute("""
            SELECT User_ID FROM Comment
            WHERE Comment_ID = ?
        """, (comment_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({"success": False, "error": "Comment not found"}), 404
        
        comment_user_id = result[0]
        is_owner = comment_user_id == session["user_id"]
        
        # Check if current user is admin
        is_admin = session.get("name") == "admin"
        
        # Only owner or admin can delete
        if not is_owner and not is_admin:
            conn.close()
            return jsonify({"success": False, "error": "Not allowed"}), 403

        # soft delete if comment has children otherwise hard delete
        cursor.execute("""
            SELECT COUNT(*) FROM Comment
            WHERE Parent_ID = ?
        """, (comment_id,))
        has_children = cursor.fetchone()[0]
        if has_children > 0:
            # Soft delete
            cursor.execute("""
                UPDATE Comment
                SET Text = '[deleted]', User_ID = 0
                WHERE Comment_ID = ?
            """, (comment_id,))
        else:
            # Hard delete
            cursor.execute("""
                DELETE FROM Comment
                WHERE Comment_ID = ?
            """, (comment_id,))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "status_code": 200,
            "message": "Comment deleted successfully"
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp_forum.post("/admin/toggle-user-posting")
def toggle_user_posting():
    """Admin endpoint to ban/unban a user from posting"""
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    # Check if current user is admin
    if session.get("name") != "admin":
        return jsonify({"success": False, "error": "Admin access required"}), 403
    
    data = request.get_json(silent=True) or {}
    target_user_id = data.get("user_id")
    
    if not target_user_id:
        return jsonify({"success": False, "error": "Missing user_id"}), 400
    
    # Prevent admin from banning themselves
    if target_user_id == session["user_id"]:
        return jsonify({"success": False, "error": "Cannot ban yourself"}), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get current can_post status
        cursor.execute("""SELECT can_post, Username FROM User WHERE User_ID = ?""", (target_user_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"success": False, "error": "User not found"}), 404
        
        current_status = result[0]
        username = result[1]
        new_status = 0 if current_status else 1
        
        # Toggle can_post status
        cursor.execute("""UPDATE User SET can_post = ? WHERE User_ID = ?""", (new_status, target_user_id))
        conn.commit()
        conn.close()
        
        action = "unbanned" if new_status else "banned"
        return jsonify({
            "success": True,
            "status_code": 200,
            "message": f"User {username} has been {action} from posting",
            "can_post": bool(new_status)
        }), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
