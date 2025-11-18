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
from api.VirusTotal import VirusTotal
from Analysis.analysis_db_store import AnalysisStore

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
        data = request.get_json(silent=True) or {}

        # Accept message, optional comment, and optional email_id so we can pull
        # context from the DB when available.
        message = (data.get('message') or '').strip()
        if not message:
            message = (request.form.get('message') or '').strip()

        # Allow email_id to come from JSON or form-data
        email_id = data.get('email_id')
        if email_id is None:
            email_id = request.form.get('email_id')
        try:
            email_id = int(email_id) if email_id not in (None, '') else None
        except ValueError:
            email_id = None

        # Comments can be supplied in JSON or form-data
        comments = request.form.getlist('comments[]')
        if not comments:
            # Fallback if the key was sent without the brackets
            comments = request.form.getlist('comments')
        user_comment = data.get('comment') or (comments[0] if comments else None)

        db_body_text = None
        db_comment = None

        # If we have an email_id, pull the stored LLM-ready body and comment
        if email_id is not None:
            conn = sqlite3.connect(DB_PATH)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT Body_Text, Email_Description FROM Email WHERE Email_ID = ?",
                    (email_id,)
                )
                row = cursor.fetchone()
            finally:
                conn.close()

            if row:
                db_body_text, db_comment = row

        # Prefer the parsed/stored LLM body from the DB when available
        if db_body_text:
            message = (db_body_text or '').strip() or message
        # Use the stored comment if the caller didn't provide one
        if not user_comment and db_comment:
            user_comment = db_comment

        if not message:
            return jsonify({
                "success": False,
                "error": "No message provided",
                "status_code": 400,
                "message": "Request must include a 'message' field"
            }), 400

        # Merge the optional user comment into the LLM prompt
        if user_comment:
            message = f"=== USER COMMENT/CONTEXT ===\n{user_comment}\n\n{message}"
        
        # Call the LLM API
        result = query_llm(message)
        
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

# VirusTotal API endpoints
@app.post('/api/scan-file')
def scan_file_api():
    try:
        data = request.get_json()
        
        if not data or 'email_id' not in data:
            return jsonify({
                "success": False,
                "error": "No email_id provided",
                "status_code": 400,
                "message": "Request must include an 'email_id' field"
            }), 400
        
        email_id = data['email_id']
        
        # Retrieve the file from the database
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Eml_file FROM Email WHERE Email_ID = ?", (email_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    "success": False,
                    "error": "Email not found",
                    "status_code": 404,
                    "message": f"No email found with ID {email_id}"
                }), 404
            
            file_content = result[0]
        finally:
            conn.close()
        
        # Initialize VirusTotal client
        try:
            vt = VirusTotal()
        except ValueError as e:
            return jsonify({
                "success": False,
                "error": "API key not configured",
                "status_code": 500,
                "message": "VirusTotal API key not configured. Please add VIRUSTOTAL_API_KEY to .env file"
            }), 500
        
        # Scan the file
        result = vt.is_malicious(file_content, f"email_{email_id}.eml")
        
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
                "message": "Failed to scan file with VirusTotal"
            }), status_code
        
        return jsonify({
            "success": True,
            "status_code": 200,
            "email_id": email_id,
            "analysis_id": result['analysis_id'],
            "type": result['type'],
            "message": result.get('message', 'File submitted for analysis'),
            "note": "Use the analysis_id to check results later via VirusTotal API"
        }), 200
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "status_code": 500,
            "message": "An unexpected error occurred while scanning file"
        }), 500

@app.post('/api/file-report')
def file_report_api():
    try:
        data = request.get_json()
        
        if not data or 'email_id' not in data:
            return jsonify({
                "success": False,
                "error": "No email_id provided",
                "status_code": 400,
                "message": "Request must include an 'email_id' field"
            }), 400
        
        email_id = data['email_id']
        
        # Retrieve the file hash from the database
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SHA256 FROM Email WHERE Email_ID = ?", (email_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    "success": False,
                    "error": "Email not found",
                    "status_code": 404,
                    "message": f"No email found with ID {email_id}"
                }), 404
            
            file_hash = result[0]
        finally:
            conn.close()
        
        # Initialize VirusTotal client
        try:
            vt = VirusTotal()
        except ValueError as e:
            return jsonify({
                "success": False,
                "error": "API key not configured",
                "status_code": 500,
                "message": "VirusTotal API key not configured. Please add VIRUSTOTAL_API_KEY to .env file"
            }), 500
        
        # Get file report
        result = vt.get_file_report(file_hash)
        
        if result['error']:
            # Determine appropriate status code based on error type
            status_code = 500
            if 'rate limit' in result['error'].lower():
                status_code = 429
            elif 'invalid api key' in result['error'].lower():
                status_code = 401
            elif 'not found' in result['error'].lower():
                status_code = 404
            
            return jsonify({
                "success": False,
                "error": result['error'],
                "status_code": status_code,
                "message": "Failed to retrieve file report from VirusTotal"
            }), status_code
        
        return jsonify({
            "success": True,
            "status_code": 200,
            "email_id": email_id,
            "file_hash": file_hash,
            "is_malicious": result['is_malicious'],
            "reputation": result['reputation'],
            "file_type": result['file_type'],
            "file_size": result['file_size'],
            "scan_date": result['scan_date'],
            "stats": result['stats'],
            "message": "File report retrieved successfully"
        }), 200
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "status_code": 500,
            "message": "An unexpected error occurred while retrieving file report"
        }), 500

# Comprehensive scan endpoint that runs all analyses and stores results
@app.post('/api/scan-email')
def scan_email_api():
    """
    Perform comprehensive analysis on an email including:
    - VirusTotal file scan
    - AbuseIPDB IP reputation check
    - LLM phishing analysis
    Store all results in Analysis table with proper relations
    """
    try:
        data = request.get_json()
        
        if not data or 'email_id' not in data:
            return jsonify({
                "success": False,
                "error": "No email_id provided",
                "status_code": 400,
                "message": "Request must include an 'email_id' field"
            }), 400
        
        email_id = data['email_id']
        
        # Retrieve email data from database
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Eml_file, Sender_IP, Body_Text, SHA256, Email_Description
                FROM Email 
                WHERE Email_ID = ?
            """, (email_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    "success": False,
                    "error": "Email not found",
                    "status_code": 404,
                    "message": f"No email found with ID {email_id}"
                }), 404
            
            file_content, sender_ip, body_text, file_hash, description = result
        finally:
            conn.close()
        
        # Initialize analysis storage
        analysis_db_store = AnalysisStore(DB_PATH)
        
        # Collect all analysis results
        vt_result = None
        abuseip_result = None
        llm_result = None
        
        # 1. VirusTotal scan
        try:
            vt = VirusTotal()
            # Try to get existing report first
            vt_report = vt.get_file_report(file_hash)
            if vt_report and not vt_report.get('error'):
                vt_result = vt_report
            else:
                # If no report exists, submit for scanning
                vt_scan = vt.is_malicious(file_content, f"email_{email_id}.eml")
                vt_result = vt_scan
        except ValueError:
            vt_result = {'error': 'VirusTotal API key not configured'}
        except Exception as e:
            vt_result = {'error': f'VirusTotal scan failed: {str(e)}'}
        
        # 2. AbuseIPDB check
        if sender_ip and sender_ip != 'None':
            try:
                abuse_checker = AbuseIPDB()
                abuseip_result = abuse_checker.is_malicious(sender_ip)
            except ValueError:
                abuseip_result = {'error': 'AbuseIPDB API key not configured'}
            except Exception as e:
                abuseip_result = {'error': f'AbuseIPDB check failed: {str(e)}'}
        else:
            abuseip_result = {'error': 'No sender IP available'}
        
        # 3. LLM analysis
        if body_text:
            if description:
                llm_prompt = f"Email Description/context: {description}\n\n{body_text}"
            else:
                llm_prompt = body_text
            try:
                llm_result = query_llm(llm_prompt)
            except Exception as e:
                llm_result = {'error': f'LLM analysis failed: {str(e)}'}
        else:
            llm_result = {'error': 'No body text available for analysis'}
        
        # Store all analysis results in the database
        storage_success = analysis_db_store.store_analysis(
            email_id=email_id,
            vt_result=vt_result,
            abuseip_result=abuseip_result,
            llm_result=llm_result
        )
        
        if not storage_success:
            return jsonify({
                "success": False,
                "error": "Failed to store analysis results",
                "status_code": 500,
                "message": "Analysis completed but failed to save to database"
            }), 500
        
        # Retrieve the stored analysis to return
        stored_analysis = analysis_db_store.get_analysis(email_id)
        
        return jsonify({
            "success": True,
            "status_code": 200,
            "email_id": email_id,
            "score": stored_analysis['score'],
            "verdict": stored_analysis['verdict'],
            "analyzed_at": stored_analysis['analyzed_at'],
            "details": stored_analysis['details'],
            "message": "Comprehensive email analysis completed and stored successfully"
        }), 200
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "status_code": 500,
            "message": "An unexpected error occurred during email analysis"
        }), 500

# Get analysis results endpoint
@app.get('/api/analysis/<int:email_id>')
def get_analysis_api(email_id):
    """
    Retrieve stored analysis results for a specific email
    """
    try:
        analysis_db_store = AnalysisStore(DB_PATH)
        analysis = analysis_db_store.get_analysis(email_id)
        
        if not analysis:
            return jsonify({
                "success": False,
                "error": "Analysis not found",
                "status_code": 404,
                "message": f"No analysis found for email ID {email_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "status_code": 200,
            "analysis": analysis,
            "message": "Analysis retrieved successfully"
        }), 200
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "status_code": 500,
            "message": "An unexpected error occurred while retrieving analysis"
        }), 500

# Get all analyses endpoint
@app.get('/api/analyses')
def get_all_analyses_api():
    """
    Retrieve all stored analyses, optionally filtered by user
    """
    try:
        user_id = request.args.get('user_id', type=int)
        
        analysis_db_store = AnalysisStore(DB_PATH)
        analyses = analysis_db_store.get_all_analyses(user_id=user_id)
        
        return jsonify({
            "success": True,
            "status_code": 200,
            "count": len(analyses),
            "analyses": analyses,
            "message": f"Retrieved {len(analyses)} analysis record(s)"
        }), 200
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "status_code": 500,
            "message": "An unexpected error occurred while retrieving analyses"
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
        
        user_id = cursor.lastrowid
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

        cursor.execute("""SELECT User_ID, Password_Hash FROM USER WHERE Username = ?""",
                       (request.form.get("name"), ))
        
        pass_hash = cursor.fetchall()
        if( not pass_hash ):
            return jsonify({
                "success": False,
                "error": "User not found",
                "status_code": 404,
                "message": f"No account found with username '{request.form.get('name')}'"
            }), 404
        
        user_id, stored_hash = row
        
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
        session["user_id"] = user_id

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

    # Try to get comments from the form. 
    comments = request.form.getlist('comments[]')
    if not comments:
        # Fallback if the key was sent without the brackets
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

            # Insert into DB (include optional user comment / description)
            uid = session.get("user_id") or 1
            conn = sqlite3.connect(DB_PATH)
            try:
                conn.execute("PRAGMA foreign_keys = ON;")
                cursor = conn.cursor()
                # Determine the comment for this file (if provided)
                comment_text = ''
                try:
                    comment_text = (comments[idx] if idx < len(comments) else '') or ''
                except Exception:
                    comment_text = ''
                # Truncate to 500 chars to match front-end limit and DB expectations
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
            
            # Note: API analyses (VirusTotal, AbuseIPDB, LLM) are now handled
            # by the frontend JavaScript after upload completes for better UX
            
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

        # Build response data (API analyses will be performed by JavaScript)
        response_data = {
            "success": True,
            "status_code": 200,
            "email_id": email_id,
            "message": f"Successfully uploaded {len(uploaded_results)} file(s)",
            "data": {
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

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    print("Database initialized successfully")
    app.run(debug=True, load_dotenv=True)
    
