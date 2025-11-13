#!/usr/bin/python
from flask import Flask, request, session, jsonify, render_template
from flask_session import Session
import sqlite3
import hashlib
import json
from datetime import datetime
from static.Helper_eml import generate_llm_body, parse_eml_bytes, init_db, DB_PATH
from api.llm import query_llm
from api.AbuseIp import AbuseIPDB
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
    return jsonify({
        "success": False,
        "error": "File too large",
        "status_code": 413,
        "message": "File exceeds the 1MB size limit. Please upload a smaller file."
    }), 413


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
                "error": "No message provided",
                "status_code": 400,
                "message": "Request must include a 'message' field"
            }), 400
        
        # Call the LLM API
        result = query_llm(data['message'])
        
        # Return the result with status code
        if result['success']:
            result['status_code'] = 200
            return jsonify(result), 200
        else:
            result['status_code'] = 500
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "status_code": 500,
            "message": "An unexpected error occurred while processing your request"
        }), 500

# AbuseIPDB API endpoint
@app.post('/api/check-ip')
def check_ip_api():
    try:
        data = request.get_json()
        
        if not data or 'ip_address' not in data:
            return jsonify({
                "success": False,
                "error": "No IP address provided",
                "status_code": 400,
                "message": "Request must include an 'ip_address' field"
            }), 400
        
        ip_address = data['ip_address']
        
        # Skip checking if IP is None or empty
        if not ip_address or ip_address == 'None':
            return jsonify({
                "success": False,
                "error": "Invalid IP address",
                "status_code": 400,
                "message": "The provided IP address is invalid or empty"
            }), 400
        
        # Initialize AbuseIPDB client
        try:
            abuse_checker = AbuseIPDB()
        except ValueError as e:
            return jsonify({
                "success": False,
                "error": "API key not configured",
                "status_code": 500,
                "message": "AbuseIPDB API key not configured. Please add ABUSEIPDB_API_KEY to .env file"
            }), 500
        
        # Check IP for malicious activity
        result = abuse_checker.is_malicious(ip_address)
        
        if result['error']:
            # Determine appropriate status code based on error type
            status_code = 500
            if 'rate limit' in result['error'].lower():
                status_code = 429
            elif 'invalid api key' in result['error'].lower():
                status_code = 401
            
            return jsonify({
                "success": False,
                "error": result['error'],
                "status_code": status_code,
                "message": "Failed to check IP reputation"
            }), status_code
        
        return jsonify({
            "success": True,
            "status_code": 200,
            "ip_address": ip_address,
            "is_malicious": result['is_malicious'],
            "abuse_score": result['abuse_score'],
            "total_reports": result['total_reports'],
            "country_code": result['country_code'],
            "usage_type": result['usage_type'],
            "isp": result['isp'],
            "is_whitelisted": result['is_whitelisted'],
            "message": "IP reputation check completed successfully"
        }), 200
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "status_code": 500,
            "message": "An unexpected error occurred while checking IP reputation"
        }), 500

@app.post('/Signup')
def CreateAccount():
    if (request.form.get("Username") == None or request.form.get("Password") == None or request.form.get("pass-ver") == None):
        return jsonify({
            "success": False,
            "error": "Missing required fields",
            "status_code": 400,
            "message": "Username, Password, and password verification are required"
        }), 400
    
    if (request.form.get("Password") != request.form.get("pass-ver")):
        return jsonify({
            "success": False,
            "error": "Password mismatch",
            "status_code": 400,
            "message": "Password does not match password verification"
        }), 400

    username = request.form.get("Username")
    # conect to DB and check if account allredy exist
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""SELECT Username FROM USER WHERE Username = ?""",
                       (username, ))

        if( cursor.fetchall() ):
            return jsonify({
                "success": False,
                "error": "User already exists",
                "status_code": 409,
                "message": f"Username '{username}' is already registered"
            }), 409
        
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

        return jsonify({
            "success": True,
            "status_code": 200,
            "message": "Account created successfully"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "status_code": 500,
            "message": "Failed to create account due to server error"
        }), 500

@app.post('/login')
def Login():
    if (request.form.get("name") == None or request.form.get("pass") == None):
        return jsonify({
            "success": False,
            "error": "Missing credentials",
            "status_code": 400,
            "message": "Username and password are required"
        }), 400
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""SELECT Password_Hash FROM USER WHERE Username = ?""",
                       (request.form.get("name"), ))
        
        pass_hash = cursor.fetchall()
        if( not pass_hash ):
            return jsonify({
                "success": False,
                "error": "User not found",
                "status_code": 404,
                "message": f"No account found with username '{request.form.get('name')}'"
            }), 404
        
        hash = hashlib.sha3_512()
        hash.update(request.form.get("pass").encode())

        if (pass_hash[0][0] != hash.hexdigest()):
            return jsonify({
                "success": False,
                "error": "Invalid password",
                "status_code": 401,
                "message": "The password you entered is incorrect"
            }), 401
        
        session["name"] = request.form.get("name")

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "status_code": 200,
            "message": "Login successful"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "status_code": 500,
            "message": "Failed to authenticate due to server error"
        }), 500

@app.route("/logout")
def logout():
    session["name"] = None
    return jsonify({
        "success": True,
        "status_code": 200,
        "message": "Logged out successfully"
    }), 200

# Get Emails
@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist("file")

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

        for file in files:
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

            # Insert into DB
            uid = session.get("user_id") or 1
            conn = sqlite3.connect(DB_PATH)
            try:
                conn.execute("PRAGMA foreign_keys = ON;")
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Email (
                        User_ID, Eml_file, SHA256, Size_Bytes, Received_At,
                        From_Addr, Sender_IP, Body_Text, Extracted_URLs
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    uid,  # Default user ID
                    file_content,
                    hashlib.sha256(file_content).hexdigest(),
                    len(file_content),
                    parsed['received_at'],
                    parsed['sender']['email'],
                    parsed['sender']['ip'],
                    llm_body_text,
                    urls_json
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
                    "urls_count": len(parsed['urls']),
                    "urls": parsed['urls']
                }
            }

            uploaded_results.append(payload)
            last_payload = payload

        # Return response for last file
        return jsonify({
            "success": True,
            "status_code": 200,
            "email_id": email_id,
            "message": f"Successfully uploaded and processed {len(uploaded_results)} file(s)",
            "data": {
                "sender_ip": last_payload['data']['sender_ip'],
                "sender_email": last_payload['data']['sender_email'],
                "body_text": last_payload['data']['body_text'],
                "body_preview": last_payload['data']['body_text'][:200] + "..." if len(last_payload['data']['body_text']) > 200 else last_payload['data']['body_text'],
                "urls_count": last_payload['data']['urls_count'],
                "urls": last_payload['data']['urls']
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Processing error: {str(e)}",
            "status_code": 500,
            "message": "Failed to process email file due to server error"
        }), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    print("Database initialized successfully")
    app.run(debug=True)
