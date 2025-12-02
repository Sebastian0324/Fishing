from flask import Blueprint, request, jsonify
import sqlite3
from static.Helper_eml import DB_PATH
from api.llm import query_llm
from api.AbuseIp import AbuseIPDB
from api.VirusTotal import VirusTotal
from Analysis.analysis_db_store import AnalysisStore

bp_analysis = Blueprint('analysis', __name__)

@bp_analysis.post('/api/scan-email')
def scan_email_api():
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
        analysis_db_store = AnalysisStore(DB_PATH)
        vt_result = None
        abuseip_result = None
        llm_result = None
        try:
            vt = VirusTotal()
            vt_result = vt.is_malicious(file_content, f"email_{email_id}.eml")
        except ValueError:
            vt_result = {'error': 'VirusTotal API key not configured'}
        except Exception as e:
            vt_result = {'error': f'VirusTotal scan failed: {str(e)}'}
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

@bp_analysis.get('/api/analysis/<int:email_id>')
def get_analysis_api(email_id):
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

@bp_analysis.get('/api/analyses')
def get_all_analyses_api():
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
