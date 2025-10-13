#!/usr/bin/python
from flask import Flask, request, jsonify, render_template
import sqlite3
import hashlib
import json
from datetime import datetime
from static.Helper_eml import parse_eml_file, init_db, DB_PATH

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False

# Routes
@app.route('/')
def form():
    text = "Hello, World!"
    return render_template('index.html', text=text)

# Routes
@app.route('/Blogg')
def blogg():
    return render_template('blogg.html')

# Routes
@app.route('/AdminPanel')
def admin():
    return render_template('AdminPanel.html')

# test function
@app.post('/test')
def set_text():
    return "AAA"

# Get Emails
@app.post('/upload')
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    
    # Check if file was selected
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Check if file is .eml
    if not file.filename.endswith('.eml'):
        return jsonify({"error": "Only .eml files are supported"}), 400
    
    try:
        # Read file content
        file_content = file.read()
        
        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256(file_content).hexdigest()
        
        # Get file size
        file_size = len(file_content)
        
        # Parse the .eml file
        parsed_data = parse_eml_file(file_content)
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Convert URLs list to JSON string
        urls_json = json.dumps(parsed_data['urls'])
        
        # Insert into database (using User_ID = 1 as default, adjust as needed)
        cursor.execute("""
            INSERT INTO Email (
                User_ID, eml_file, SHA256, Size_Bytes, Received_At,
                From_Addr, Sender_IP, Body_Text, Extracted_URLs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1,  # Default user ID - modify based on your authentication system
            file_content,
            sha256_hash,
            file_size,
            datetime.now().isoformat(),
            parsed_data['sender_email'],
            parsed_data['sender_ip'],
            parsed_data['body_text'],
            urls_json
        ))
        
        email_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return success response with extracted data
        return jsonify({
            "success": True,
            "email_id": email_id,
            "data": {
                "sender_ip": parsed_data['sender_ip'],
                "sender_email": parsed_data['sender_email'],
                "body_preview": parsed_data['body_text'][:200] + "..." if len(parsed_data['body_text']) > 200 else parsed_data['body_text'],
                "urls_count": len(parsed_data['urls']),
                "urls": parsed_data['urls']
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500




if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    print("Database initialized successfully")
    app.run(debug=True)
