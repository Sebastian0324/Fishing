#!/usr/bin/python
from flask import Flask, request, session, jsonify, render_template
from flask_session import Session
import sqlite3
import hashlib
import json
from datetime import datetime
from static.Helper_eml import generate_llm_body, parse_Eml_file, init_db, DB_PATH
from api.llm import query_llm
import dotenv
dotenv.load_dotenv()

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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

# LLM API endpoint
@app.post('/api/llm')
def llm_api():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "No message provided"
            }), 400
        
        # Call the LLM API
        result = query_llm(data['message'])
        
        # Return the result directly (query_llm already returns properly formatted dict)
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.post('/Signup')
def CreateAccount():
    if (request.form.get("Username") == None or request.form.get("Password") == None or request.form.get("pass-ver") == None):
        # if a requierd field is missing, give an error
    
        # ToDo::
        #   -- Show error
        return jsonify({"success": False,
                        "error": f"Expected data was not provided"}), 400
    
    if (request.form.get("Password") != request.form.get("pass-ver")):
        return jsonify({"success": False,
                        "error": f"Password dose not match password verification"}), 400

    username = request.form.get("Username")
    # conect to DB and check if account allredy exist
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""SELECT Username FROM USER WHERE Username = ?""",
                       (username, ))

        if( cursor.fetchall() ):
            return jsonify({"success": False,
                            "error": f"This user allredy exist"}), 400
        # ToDo::
        #  -- Check password
        
        hash = hashlib.sha3_512()
        hash.update(request.form.get("Password").encode())

        cursor.execute("""
                        INSERT INTO USER (
                            Username, Password_Hash
                        ) VALUES (?, ?)""", (
                        username,
                        hash.hexdigest()
                    ))
        session["name"] = username
            
        conn.commit()
        conn.close()

        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to acces DataBase: {str(e)}"}), 500

@app.post('/login')
def Login():
    if (request.form.get("name") == None or request.form.get("pass") == None):
        # if a requierd field is missing, give an error
    
        # ToDo::
        #   -- Show error
        return jsonify({"success": False,
                        "error": f"Expected data was not provided"}), 400
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""SELECT Password_Hash FROM USER WHERE Username = ?""",
                       (request.form.get("name"), ))
        
        pass_hash = cursor.fetchall()
        if( not pass_hash ):
            return jsonify({"success": False,
                            "error": f"This user dose not exist"}), 400
        
        hash = hashlib.sha3_512()
        hash.update(request.form.get("pass").encode())

        if (pass_hash[0][0] != hash.hexdigest()):
            return jsonify({"success": False,
                            "error": f"Wrong password"}), 400
        
        session["name"] = request.form.get("name")

        conn.commit()
        conn.close()

        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to acces DataBase: {str(e)}"}), 500

@app.route("/logout")
def logout():
    session["name"] = None
    return jsonify({"success": True}), 200

# Get Emails
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
            if file.filename == '':
                return jsonify({"error": "Empty filename detected"}), 400
            
            if not file.filename.endswith('.eml'):
                return jsonify({"error": "Only .eml files are supported"}), 400
        
            file_content = file.read()
            file_size = len(file_content)
            sha256_hash = hashlib.sha256(file_content).hexdigest()

            # Parse email with enhanced format
            parsed_data = parse_Eml_file(file_content, enhanced_format=True)
            llm_body_text = generate_llm_body(parsed_data)

            # Connect to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            urls_json = json.dumps(parsed_data['urls'])

            # Insert into database
            cursor.execute("""
                INSERT INTO Email (
                    User_ID, Eml_file, SHA256, Size_Bytes, Received_At,
                    From_Addr, Sender_IP, Body_Text, Extracted_URLs
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1,  # Default user ID
                file_content,
                sha256_hash,
                file_size,
                datetime.now().isoformat(),
                parsed_data['sender']['email'],
                parsed_data['sender']['ip'],
                llm_body_text,
                urls_json
            ))
            
            email_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Prepare results for frontend
            uploaded_results.append({
                "email_id": email_id,
                "filename": file.filename,
                "data": {
                    "sender_ip": parsed_data['sender']['ip'],
                    "sender_email": parsed_data['sender']['email'],
                    "body_preview": parsed_data['body']['text'][:200] + "..." if len(parsed_data['body']['text']) > 200 else parsed_data['body']['text'],
                    "urls_count": len(parsed_data['urls']),
                    "urls": parsed_data['urls']
                }
            })

        # Return response for last file
        return jsonify({
            "success": True,
            "email_id": email_id,
            "filename": file.filename,
            "data": {
                "sender_ip": parsed_data['sender']['ip'],
                "sender_email": parsed_data['sender']['email'],
                "body_text": llm_body_text,
                "body_length": len(parsed_data['body']['text']),
                "urls_count": len(parsed_data['urls']),
                "urls": parsed_data['urls']
            },
            "uploaded_files": uploaded_results
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    print("Database initialized successfully")
    app.run(debug=True)
