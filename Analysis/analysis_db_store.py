import sqlite3
import json
from datetime import datetime
from typing import Dict, Optional, Any

class AnalysisStore:
    """
    Module to store and manage email analysis results in the database.
    Aggregates results from multiple sources (VirusTotal, AbuseIPDB, LLM) 
    and stores them with proper relations to Email table.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def calculate_score_and_verdict(self, vt_result: Optional[Dict], 
                                     abuseip_result: Optional[Dict], 
                                     llm_result: Optional[Dict]) -> tuple:
        """
        Calculate an overall phishing score and verdict based on all analysis results.
        
        Args:
            vt_result: VirusTotal scan results
            abuseip_result: AbuseIPDB check results
            llm_result: LLM analysis results
        
        Returns:
            tuple: (score: int 0-100, verdict: str)
        """
        score = 0
        factors = []
        
        # VirusTotal analysis (0-60 points)
        # Malicious vendor flags are weighted heavily in the verdict
        if vt_result and not vt_result.get('error'):
            stats = vt_result.get('stats', {})
            if stats:
                malicious = stats.get('malicious', 0)
                suspicious = stats.get('suspicious', 0)
                total_scans = stats.get('total_scans', 1)
                
                # If ANY vendors flag as malicious, give high score
                # Malicious verdicts are treated much more seriously than suspicious
                if malicious > 0:
                    # Base score for having malicious detections
                    malicious_ratio = malicious / max(total_scans, 1)
                    # Even 1 malicious flag out of many gets 45 points (high confidence indicator)
                    # Multiple malicious flags get progressively higher scores up to 60
                    vt_score = min(60, int(45 + (malicious_ratio * 15)))
                    factors.append(f"VirusTotal: {malicious}/{total_scans} engines flagged as malicious - HIGH RISK")
                else:
                    # For suspicious-only detections, use moderate scoring
                    detection_rate = suspicious / max(total_scans, 1) * 100
                    vt_score = min(30, int(detection_rate * 0.3))
                    if suspicious > 0:
                        factors.append(f"VirusTotal: {suspicious}/{total_scans} engines flagged as suspicious")
                
                score += vt_score
            elif vt_result.get('is_malicious'):
                # Binary result if available
                score += 50
                factors.append("VirusTotal: File flagged as malicious - HIGH RISK")
        
        # AbuseIPDB analysis (0-40 points)
        if abuseip_result and not abuseip_result.get('error'):
            abuse_score = abuseip_result.get('abuse_score', 0)
            
            # Scale abuse score (0-100) to our points (0-40)
            ip_score = int(abuse_score * 0.4)
            score += ip_score
            
            if abuse_score > 0:
                total_reports = abuseip_result.get('total_reports', 0)
                factors.append(f"Sender IP: Abuse score {abuse_score}/100 ({total_reports} reports)")
        
        # LLM analysis (0-20 points)
        if llm_result and not llm_result.get('error'):
            response = llm_result.get('response', '').lower()
            
            # Look for phishing indicators in LLM response
            phishing_keywords = [
                'phishing', 'scam', 'fraud', 'malicious', 'suspicious',
                'deceptive', 'fake', 'impersonation', 'credential theft'
            ]
            
            keyword_count = sum(1 for keyword in phishing_keywords if keyword in response)
            llm_score = min(20, keyword_count * 4)
            score += llm_score
            
            if keyword_count > 0:
                factors.append(f"LLM Analysis: Identified {keyword_count} phishing indicators")
        
        # Determine verdict based on score
        # Aggressive thresholds (with higher VirusTotal weight):
        # - Phishing: Score 50+ (malicious VT detection alone triggers phishing)
        # - Suspicious: Score 20+ (any concern from vendors)
        # - Benign: Score <20
        if score >= 50:
            verdict = "Phishing"
        elif score >= 20:
            verdict = "Suspicious"
        else:
            verdict = "Benign"
        
        return score, verdict, factors
    
    def store_analysis(self, email_id: int, 
                      vt_result: Optional[Dict] = None,
                      abuseip_result: Optional[Dict] = None, 
                      llm_result: Optional[Dict] = None) -> bool:
        """
        Store comprehensive analysis results in the Analysis table.
        
        Args:
            email_id: The Email_ID to link this analysis to
            vt_result: VirusTotal scan results
            abuseip_result: AbuseIPDB check results
            llm_result: LLM analysis results
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Calculate overall score and verdict
            score, verdict, factors = self.calculate_score_and_verdict(
                vt_result, abuseip_result, llm_result
            )
            
            # Build comprehensive details JSON
            details = {
                'timestamp': datetime.utcnow().isoformat(),
                'score_breakdown': {
                    'total_score': score,
                    'verdict': verdict,
                    'factors': factors
                },
                'virustotal': None,
                'abuseipdb': None,
                'llm': None
            }
            
            # Add VirusTotal details
            if vt_result and not vt_result.get('error'):
                details['virustotal'] = {
                    'analysis_id': vt_result.get('analysis_id'),
                    'type': vt_result.get('type'),
                    'is_malicious': vt_result.get('is_malicious'),
                    'stats': vt_result.get('stats'),
                    'reputation': vt_result.get('reputation'),
                    'file_type': vt_result.get('file_type'),
                    'scan_date': vt_result.get('scan_date')
                }
            elif vt_result:
                details['virustotal'] = {
                    'error': vt_result.get('error'),
                    'analysis_id': vt_result.get('analysis_id')
                }
            
            # Add AbuseIPDB details
            if abuseip_result and not abuseip_result.get('error'):
                details['abuseipdb'] = {
                    'is_malicious': abuseip_result.get('is_malicious'),
                    'abuse_score': abuseip_result.get('abuse_score'),
                    'total_reports': abuseip_result.get('total_reports'),
                    'country_code': abuseip_result.get('country_code'),
                    'usage_type': abuseip_result.get('usage_type'),
                    'isp': abuseip_result.get('isp'),
                    'is_whitelisted': abuseip_result.get('is_whitelisted')
                }
            elif abuseip_result:
                details['abuseipdb'] = {
                    'error': abuseip_result.get('error')
                }
            
            # Add LLM details
            if llm_result and not llm_result.get('error'):
                details['llm'] = {
                    'response': llm_result.get('response'),
                    'analysis_successful': True
                }
            elif llm_result:
                details['llm'] = {
                    'error': llm_result.get('error'),
                    'analysis_successful': False
                }
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("PRAGMA foreign_keys = ON;")
                cursor = conn.cursor()
                
                # Check if analysis already exists for this email
                cursor.execute(
                    "SELECT Email_ID FROM Analysis WHERE Email_ID = ?",
                    (email_id,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing analysis
                    cursor.execute("""
                        UPDATE Analysis 
                        SET Score = ?,
                            Analyzed = 1,
                            Verdict = ?,
                            Details_json = ?,
                            Analyzed_At = ?
                        WHERE Email_ID = ?
                    """, (
                        score,
                        verdict,
                        json.dumps(details, indent=2),
                        datetime.utcnow().isoformat(),
                        email_id
                    ))
                else:
                    # Insert new analysis
                    cursor.execute("""
                        INSERT INTO Analysis (
                            Email_ID, Score, Analyzed, Verdict, 
                            Details_json, Analyzed_At
                        ) VALUES (?, ?, 1, ?, ?, ?)
                    """, (
                        email_id,
                        score,
                        verdict,
                        json.dumps(details, indent=2),
                        datetime.utcnow().isoformat()
                    ))
                
                conn.commit()
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Error storing analysis: {str(e)}")
            return False
    
    def get_analysis(self, email_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve analysis results for a specific email.
        
        Args:
            email_id: The Email_ID to retrieve analysis for
        
        Returns:
            dict: Analysis data or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT Email_ID, Score, Analyzed, Verdict, 
                           Details_json, Analyzed_At
                    FROM Analysis
                    WHERE Email_ID = ?
                """, (email_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Parse JSON details
                details = json.loads(row['Details_json']) if row['Details_json'] else {}
                
                return {
                    'email_id': row['Email_ID'],
                    'score': row['Score'],
                    'analyzed': bool(row['Analyzed']),
                    'verdict': row['Verdict'],
                    'details': details,
                    'analyzed_at': row['Analyzed_At']
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Error retrieving analysis: {str(e)}")
            return None
    
    def get_all_analyses(self, user_id: Optional[int] = None) -> list:
        """
        Retrieve all analyses, optionally filtered by user.
        
        Args:
            user_id: Optional user ID to filter by
        
        Returns:
            list: List of analysis dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.cursor()
                
                if user_id:
                    cursor.execute("""
                        SELECT a.Email_ID, a.Score, a.Analyzed, a.Verdict, 
                               a.Details_json, a.Analyzed_At,
                               e.From_Addr, e.Received_At
                        FROM Analysis a
                        JOIN Email e ON a.Email_ID = e.Email_ID
                        WHERE e.User_ID = ?
                        ORDER BY a.Analyzed_At DESC
                    """, (user_id,))
                else:
                    cursor.execute("""
                        SELECT a.Email_ID, a.Score, a.Analyzed, a.Verdict, 
                               a.Details_json, a.Analyzed_At,
                               e.From_Addr, e.Received_At
                        FROM Analysis a
                        JOIN Email e ON a.Email_ID = e.Email_ID
                        ORDER BY a.Analyzed_At DESC
                    """)
                
                rows = cursor.fetchall()
                analyses = []
                
                for row in rows:
                    details = json.loads(row['Details_json']) if row['Details_json'] else {}
                    analyses.append({
                        'email_id': row['Email_ID'],
                        'score': row['Score'],
                        'analyzed': bool(row['Analyzed']),
                        'verdict': row['Verdict'],
                        'details': details,
                        'analyzed_at': row['Analyzed_At'],
                        'from_addr': row['From_Addr'],
                        'received_at': row['Received_At']
                    })
                
                return analyses
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Error retrieving analyses: {str(e)}")
            return []
