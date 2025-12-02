from flask import Blueprint, request, session, jsonify
import sqlite3
import hashlib
import json
from static.Helper_eml import parse_eml_bytes, generate_llm_body, DB_PATH

bp_upload = Blueprint('upload', __name__)

@bp_upload.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist("file")
    comments = request.form.getlist('comments[]')
    if not comments:
        comments = request.form.getlist('comments')
    if "file" not in request.files:
        return jsonify({
            "success": False,
            "error": "No file uploaded",
            "status_code": 400,
            "message": "Please select at least one .eml file to upload"
        }), 400
    if len(files) > 5:
        return jsonify({
            "success": False,
            "error": "Too many files",
            "status_code": 400,
            "message": "Maximum 5 files allowed. Please select fewer files."
        }), 400
    try:
        uploaded_results = []
        last_payload = None
        for idx, file in enumerate(files):
            if file.filename == '':
                return jsonify({
                    "success": False,
                    "error": "Empty filename",
                    "status_code": 400,
                    "message": "One or more files have an empty filename"
                }), 400
            if not file.filename.endswith('.eml'):
                return jsonify({
                    "success": False,
                    "error": "Invalid file type",
                    "status_code": 400,
                    "message": f"File '{file.filename}' is not a .eml file. Only .eml files are supported."
                }), 400
            file_content = file.read()
            parsed = parse_eml_bytes(file_content, enhanced_format=True)
            if not parsed.get("valid", False):
                return jsonify({
                    "success": False,
                    "error": "Email parsing failed",
                    "status_code": 400,
                    "message": f"Failed to parse email file '{file.filename}'. The file may be corrupted or not a valid .eml file."
                }), 400
            llm_body_text = generate_llm_body(parsed)
            urls_json = json.dumps(parsed['urls'])
            uid = session.get("user_id") or 1
            conn = sqlite3.connect(DB_PATH)
            try:
                conn.execute("PRAGMA foreign_keys = ON;")
                cursor = conn.cursor()
                comment_text = ''
                try:
                    comment_text = (comments[idx] if idx < len(comments) else '') or ''
                except Exception:
                    comment_text = ''
                if isinstance(comment_text, str) and len(comment_text) > 500:
                    comment_text = comment_text[:500]
                cursor.execute("""
                    INSERT INTO Email (
                        User_ID, Eml_file, SHA256, Size_Bytes, Received_At,
                        From_Addr, Sender_IP, Body_Text, Extracted_URLs, Email_Description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    uid,
                    file_content,
                    hashlib.sha256(file_content).hexdigest(),
                    len(file_content),
                    parsed['received_at'],
                    parsed['sender']['email'],
                    parsed['sender']['ip'],
                    llm_body_text,
                    urls_json,
                    comment_text
                ))
                email_id = cursor.lastrowid
                conn.commit()
            finally:
                conn.close()
            body_text = parsed['body']['text']
            payload = {
                "email_id": email_id,
                "filename": file.filename,
                "data": {
                    "sender_ip": parsed['sender']['ip'],
                    "sender_email": parsed['sender']['email'],
                    "body_text": body_text,
                    "body_preview": body_text[:200] + "..." if len(body_text) > 200 else body_text,
                    "comment": comment_text,
                    "urls_count": len(parsed['urls']),
                    "urls": parsed['urls']
                }
            }
            uploaded_results.append(payload)
            last_payload = payload
        response_data = {
            "success": True,
            "status_code": 200,
            "message": f"Successfully uploaded {len(uploaded_results)} file(s)",
            "data": {
                "files": uploaded_results,
                "count": len(uploaded_results),
                "sender_ip": last_payload['data']['sender_ip'],
                "sender_email": last_payload['data']['sender_email'],
                "body_text": last_payload['data']['body_text'],
                "body_preview": last_payload['data']['body_text'][:200] + "..." if len(last_payload['data']['body_text']) > 200 else last_payload['data']['body_text'],
                "comment": last_payload['data']['comment'],
                "urls_count": last_payload['data']['urls_count'],
                "urls": last_payload['data']['urls']
            }
        }
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Processing error: {str(e)}",
            "status_code": 500,
            "message": "Failed to process email file due to server error"
        }), 500
