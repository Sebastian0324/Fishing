from flask import Blueprint, request, jsonify
import sqlite3
from static.Helper_eml import DB_PATH
from api.llm import query_llm

bp_llm = Blueprint('api_llm', __name__)

@bp_llm.post('/api/llm')
def llm_api():
    try:
        data = request.get_json(silent=True) or {}
        message = (data.get('message') or '').strip()
        if not message:
            message = (request.form.get('message') or '').strip()
        email_id = data.get('email_id')
        if email_id is None:
            email_id = request.form.get('email_id')
        try:
            email_id = int(email_id) if email_id not in (None, '') else None
        except ValueError:
            email_id = None
        comments = request.form.getlist('comments[]')
        if not comments:
            comments = request.form.getlist('comments')
        user_comment = data.get('comment') or (comments[0] if comments else None)
        db_body_text = None
        db_comment = None
        if email_id is not None:
            conn = sqlite3.connect(DB_PATH)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT Body_Text, Email_Description FROM Email WHERE Email_ID = ?", (email_id,))
                row = cursor.fetchone()
            finally:
                conn.close()
            if row:
                db_body_text, db_comment = row
        if db_body_text:
            message = (db_body_text or '').strip() or message
        if not user_comment and db_comment:
            user_comment = db_comment
        if not message:
            return jsonify({"success": False,"error": "No message provided","status_code": 400,"message": "Request must include a 'message' field"}), 400
        if user_comment:
            message = f"=== USER COMMENT/CONTEXT ===\n{user_comment}\n\n{message}"
        result = query_llm(message)
        if result['success']:
            result['status_code'] = 200
            return jsonify(result), 200
        else:
            result['status_code'] = 500
            return jsonify(result), 500
    except Exception as e:
        return jsonify({"success": False,"error": f"Server error: {str(e)}","status_code": 500,"message": "An unexpected error occurred while processing your request"}), 500
