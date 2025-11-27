from flask import Blueprint, request, jsonify
import sqlite3
from Analysis.mailstore import DB_PATH
from api.AbuseIp import AbuseIPDB
from api.VirusTotal import VirusTotal

bp_security = Blueprint('api_security', __name__)

@bp_security.post('/api/check-ip')
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
        if not ip_address or ip_address == 'None':
            return jsonify({
                "success": False,
                "error": "Invalid IP address",
                "status_code": 400,
                "message": "The provided IP address is invalid or empty"
            }), 400
        try:
            abuse_checker = AbuseIPDB()
        except ValueError:
            return jsonify({
                "success": False,
                "error": "API key not configured",
                "status_code": 500,
                "message": "AbuseIPDB API key not configured. Please add ABUSEIPDB_API_KEY to .env file"
            }), 500
        result = abuse_checker.is_malicious(ip_address)
        if result['error']:
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

@bp_security.post('/api/scan-file')
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
        try:
            vt = VirusTotal()
        except ValueError:
            return jsonify({
                "success": False,
                "error": "API key not configured",
                "status_code": 500,
                "message": "VirusTotal API key not configured. Please add VIRUSTOTAL_API_KEY to .env file"
            }), 500
        result = vt.is_malicious(file_content, f"email_{email_id}.eml")
        if result['error']:
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
        if result.get('already_exists'):
            return jsonify({
                "success": True,
                "status_code": 200,
                "email_id": email_id,
                "analysis_id": result['analysis_id'],
                "file_hash": result.get('file_hash'),
                "type": result['type'],
                "is_malicious": result.get('is_malicious'),
                "stats": result.get('stats'),
                "message": result.get('message', 'File already analyzed - results retrieved'),
                "already_exists": True
            }), 200
        return jsonify({
            "success": True,
            "status_code": 200,
            "email_id": email_id,
            "analysis_id": result['analysis_id'],
            "file_hash": result.get('file_hash'),
            "type": result['type'],
            "message": result.get('message', 'File submitted for analysis'),
            "already_exists": False,
            "note": "Use the analysis_id to check results later via VirusTotal API"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "status_code": 500,
            "message": "An unexpected error occurred while scanning file"
        }), 500

@bp_security.post('/api/file-report')
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
        conn = sqlite3.connect(DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SHA256, Eml_file FROM Email WHERE Email_ID = ?", (email_id,))
            result = cursor.fetchone()
            if not result:
                return jsonify({
                    "success": False,
                    "error": "Email not found",
                    "status_code": 404,
                    "message": f"No email found with ID {email_id}"
                }), 404
            file_hash, file_content = result
        finally:
            conn.close()
        try:
            vt = VirusTotal()
        except ValueError:
            return jsonify({
                "success": False,
                "error": "API key not configured",
                "status_code": 500,
                "message": "VirusTotal API key not configured. Please add VIRUSTOTAL_API_KEY to .env file"
            }), 500
        result = vt.get_file_report(file_hash)
        if result['error']:
            if 'not found' in result['error'].lower():
                scan_result = vt.scan_file(file_content, f"email_{email_id}.eml")
                if scan_result['success']:
                    analysis_id = scan_result['data'].get('id', '')
                    return jsonify({
                        "success": True,
                        "status_code": 200,
                        "email_id": email_id,
                        "file_hash": file_hash,
                        "analysis_id": analysis_id,
                        "is_malicious": None,
                        "message": "File submitted for analysis. Results will be available shortly.",
                        "pending": True
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error": scan_result['error'],
                        "status_code": 500,
                        "message": "Failed to submit file to VirusTotal for scanning"
                    }), 500
            status_code = 500
            if 'rate limit' in result['error'].lower():
                status_code = 429
            elif 'invalid api key' in result['error'].lower():
                status_code = 401
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
