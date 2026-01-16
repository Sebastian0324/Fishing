import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AbuseIPDB:
    """
    Class to interact with AbuseIPDB API for checking IP reputation
    API Documentation: https://docs.abuseipdb.com/
    """
    
    def __init__(self):
        self.api_key = os.getenv('ABUSEIPDB_API_KEY')
        self.base_url = 'https://api.abuseipdb.com/api/v2'
        
        if not self.api_key:
            raise ValueError("ABUSEIPDB_API_KEY not found in environment variables")
    
    def check_ip(self, ip_address, max_age_in_days=90, verbose=False):
        """
        Check an IP address for malicious activity
        
        Args:
            ip_address (str): The IP address to check
            max_age_in_days (int): Maximum age of reports to include (default: 90)
            verbose (bool): Include detailed report information (default: False)
        
        Returns:
            dict: API response containing IP reputation data
        """
        endpoint = f'{self.base_url}/check'
        
        headers = {
            'Key': self.api_key,
            'Accept': 'application/json'
        }
        
        params = {
            'ipAddress': ip_address,
            'maxAgeInDays': max_age_in_days,
            'verbose': verbose
        }
        
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'data': data.get('data', {}),
                'error': None
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            if e.response.status_code == 401:
                error_msg = "Invalid API key"
            elif e.response.status_code == 429:
                error_msg = "Rate limit exceeded"
            
            return {
                'success': False,
                'data': None,
                'error': error_msg
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'data': None,
                'error': f"Request failed: {str(e)}"
            }
    
    def is_malicious(self, ip_address, threshold=50):
        """
        Check if an IP is considered malicious based on abuse confidence score
        
        Args:
            ip_address (str): The IP address to check
            threshold (int): Abuse confidence score threshold (0-100, default: 50)
        
        Returns:
            dict: Contains is_malicious boolean and abuse score
        """
        result = self.check_ip(ip_address)
        
        if not result['success']:
            return {
                'is_malicious': None,
                'abuse_score': None,
                'error': result['error']
            }
        
        data = result['data']
        abuse_score = data.get('abuseConfidenceScore', 0)
        
        return {
            'is_malicious': abuse_score >= threshold,
            'abuse_score': abuse_score,
            'total_reports': data.get('totalReports', 0),
            'country_code': data.get('countryCode', 'Unknown'),
            'usage_type': data.get('usageType', 'Unknown'),
            'isp': data.get('isp', 'Unknown'),
            'is_whitelisted': data.get('isWhitelisted', False),
            'error': None
        }
