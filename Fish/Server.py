#!/usr/bin/python
from flask import Flask, request, jsonify, render_template
import sqlite3
import hashlib
import json
from datetime import datetime
from static.Helper_eml import parse_eml_file, init_db, DB_PATH

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False

# Limit upload size to 1MB
# Change to 10*1024*1024 for 10 MB after test or exact size needed
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

#Change to accual size after test
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File exceeds 1MB limit"}), 413


# Routes
@app.route('/')
def form():
    return render_template('index.html')

# Routes
@app.route('/Forum')
def Forum():
    return render_template('Forum.html')

# Routes
@app.route('/Dashboard')
def admin():
    return render_template('Dashboard.html')

# Routes
@app.route('/Account')
def account():
    return render_template('Account.html')

# Routes
@app.route('/AboutUs')
def info():
    return render_template('AboutUs.html')

# test function
@app.post('/test')
def set_text():
    return "AAA"


@app.post('/upload')
def upload():
    files = request.files.getlist("file")

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    if len(files) > 5:
        return jsonify({"error": "Maximum 5 files allowed"}), 400
    try:
        uploaded_results = [] 

        for file in files:
            # Check if file was selected
            if file.filename == '':
                return jsonify({"error": "Empty filename detected"}), 400
            
            # Check if file is .eml
            if not file.filename.endswith('.eml'):
                return jsonify({"error": "Only .eml files are supported"}), 400
        
            # Read file content
            file_content = file.read()
            file_size = len(file_content)
            sha256_hash = hashlib.sha256(file_content).hexdigest()
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
                1, # Default user ID - modify based on your authentication system
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

            #List for multiple file upload content print
            uploaded_results.append({
                "email_id": email_id,
                "filename": file.filename,
                "data": {
                    "sender_ip": parsed_data['sender_ip'],
                    "sender_email": parsed_data['sender_email'],
                    "body_preview": parsed_data['body_text'][:200] + "..." if len(parsed_data['body_text']) > 200 else parsed_data['body_text'],
                    "urls_count": len(parsed_data['urls']),
                    "urls": parsed_data['urls']
                }
            })

        # Return success response with extracted data for last file 
        return jsonify({
            "success": True,
            "email_id": email_id,
            "filename": file.filename,
            "data": {
                "sender_ip": parsed_data['sender_ip'],
                "sender_email": parsed_data['sender_email'],
                "body_preview": parsed_data['body_text'][:200] + "..." if len(parsed_data['body_text']) > 200 else parsed_data['body_text'],
                "urls_count": len(parsed_data['urls']),
                "urls": parsed_data['urls']
            },

        # Can be used for multiple file upload content print , Need justification in js to handle it
            "uploaded_files": uploaded_results
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    print("Database initialized successfully")
    app.run(debug=True)
