import requests
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VirusTotal:
    """
    Class to interact with VirusTotal API for file scanning
    API Documentation: https://docs.virustotal.com/reference/files
    """
    
    def __init__(self):
        self.api_key = os.getenv('VIRUSTOTAL_API_KEY')
        self.base_url = 'https://www.virustotal.com/api/v3'
        
        if not self.api_key:
            raise ValueError("VIRUSTOTAL_API_KEY not found in environment variables")
    
    def scan_file(self, file_content, filename="file.eml", password=None, check_existing=True):
        """
        Upload and scan a file with VirusTotal
        
        Args:
            file_content (bytes): The file content to scan
            filename (str): The filename (default: "file.eml")
            password (str): Optional password for protected ZIP files
            check_existing (bool): If True, check if file exists before uploading (default: True)
        
        Returns:
            dict: API response containing scan results
        """
        # First check if file already exists in VT to avoid unnecessary uploads
        if check_existing:
            import hashlib
            file_hash = hashlib.sha256(file_content).hexdigest()
            existing_report = self.get_file_report(file_hash)
            
            if existing_report['success']:
                # File already exists in VT, return existing analysis
                return {
                    'success': True,
                    'data': {
                        'id': existing_report.get('data', {}).get('id', file_hash),
                        'type': 'analysis',
                        'attributes': existing_report.get('data', {}).get('attributes', {})
                    },
                    'already_exists': True,
                    'file_hash': file_hash,
                    'error': None
                }
        
        endpoint = f'{self.base_url}/files'
        
        headers = {
            'x-apikey': self.api_key,
            'accept': 'application/json'
        }
        
        # Prepare the file for upload
        files = {
            'file': (filename, file_content)
        }
        
        # Add password if provided
        data = {}
        if password:
            data['password'] = password
        
        try:
            response = requests.post(
                endpoint, 
                headers=headers, 
                files=files,
                data=data if password else None
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                'success': True,
                'data': result.get('data', {}),
                'already_exists': False,
                'error': None
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            if e.response.status_code == 400:
                error_msg = "Bad request - file may be invalid or password incorrect"
            elif e.response.status_code == 401:
                error_msg = "Invalid API key"
            elif e.response.status_code == 429:
                error_msg = "Rate limit exceeded - please wait before submitting new files"
            
            return {
                'success': False,
                'data': None,
                'already_exists': False,
                'error': error_msg
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'data': None,
                'already_exists': False,
                'error': f"Request failed: {str(e)}"
            }
    
    def get_analysis(self, analysis_id):
        """
        Get analysis results for a previously submitted file
        
        Args:
            analysis_id (str): The analysis ID returned from scan_file
        
        Returns:
            dict: Analysis results
        """
        endpoint = f'{self.base_url}/analyses/{analysis_id}'
        
        headers = {
            'x-apikey': self.api_key,
            'accept': 'application/json'
        }
        
        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return {
                'success': True,
                'data': result.get('data', {}),
                'error': None
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            if e.response.status_code == 401:
                error_msg = "Invalid API key"
            elif e.response.status_code == 404:
                error_msg = "Analysis not found"
            
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
    
    def get_file_report(self, file_hash):
        """
        Retrieve information and scan results about a file using its hash
        
        Args:
            file_hash (str): SHA-256, SHA-1, or MD5 hash of the file
        
        Returns:
            dict: File report including scan results from all antivirus engines
        """
        endpoint = f'{self.base_url}/files/{file_hash}'
        
        headers = {
            'x-apikey': self.api_key,
            'accept': 'application/json'
        }
        
        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            data = result.get('data', {})
            attributes = data.get('attributes', {})
            
            # Extract scan statistics
            stats = attributes.get('last_analysis_stats', {})
            scan_results = attributes.get('last_analysis_results', {})
            
            return {
                'success': True,
                'data': data,
                'stats': {
                    'malicious': stats.get('malicious', 0),
                    'suspicious': stats.get('suspicious', 0),
                    'undetected': stats.get('undetected', 0),
                    'harmless': stats.get('harmless', 0),
                    'failure': stats.get('failure', 0),
                    'total_scans': len(scan_results)
                },
                'is_malicious': stats.get('malicious', 0) > 0,
                'reputation': attributes.get('reputation', 0),
                'file_type': attributes.get('type_description', 'Unknown'),
                'file_size': attributes.get('size', 0),
                'scan_date': attributes.get('last_analysis_date', None),
                'error': None
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            if e.response.status_code == 401:
                error_msg = "Invalid API key"
            elif e.response.status_code == 404:
                error_msg = "File not found in VirusTotal database"
            
            return {
                'success': False,
                'data': None,
                'stats': None,
                'is_malicious': None,
                'error': error_msg
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'data': None,
                'stats': None,
                'is_malicious': None,
                'error': f"Request failed: {str(e)}"
            }
    
    def is_malicious(self, file_content, filename="file.eml", wait_for_analysis=True, max_wait_time=15):
        """
        Scan a file and determine if it's malicious based on detection results
        
        Args:
            file_content (bytes): The file content to scan
            filename (str): The filename (default: "file.eml")
            wait_for_analysis (bool): If True, wait for analysis to complete (default: True)
            max_wait_time (int): Maximum time in seconds to wait for analysis (default: 15)
        
        Returns:
            dict: Contains analysis information including malicious status
        """
        import hashlib
        import time
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # First, try to get existing report (doesn't consume quota)
        existing_report = self.get_file_report(file_hash)
        
        if existing_report['success']:
            # File already scanned, return existing results
            stats = existing_report.get('stats', {})
            return {
                'is_malicious': existing_report.get('is_malicious'),
                'analysis_id': file_hash,
                'type': 'file',
                'detections': stats,
                'stats': stats,
                'file_hash': file_hash,
                'message': 'File already analyzed - using existing results',
                'already_exists': True,
                'error': None
            }
        
        # File not in VT database, upload it
        scan_result = self.scan_file(file_content, filename, check_existing=False)
        
        if not scan_result['success']:
            return {
                'is_malicious': None,
                'analysis_id': None,
                'detections': None,
                'file_hash': file_hash,
                'already_exists': False,
                'error': scan_result['error']
            }
        
        # Extract analysis ID
        data = scan_result['data']
        analysis_id = data.get('id', '')
        file_type = data.get('type', '')
        
        # If wait_for_analysis is True, poll for results
        if wait_for_analysis and analysis_id:
            start_time = time.time()
            attempts = 0
            
            while (time.time() - start_time) < max_wait_time:
                attempts += 1
                # Wait before checking (exponential backoff: 2s, 3s, 4s, 5s...)
                wait_time = min(2 + attempts, 5)
                time.sleep(wait_time)
                
                # Try to get the file report using the hash
                report = self.get_file_report(file_hash)
                
                if report['success']:
                    # Analysis complete!
                    stats = report.get('stats', {})
                    return {
                        'is_malicious': report.get('is_malicious'),
                        'analysis_id': analysis_id,
                        'type': 'file',
                        'detections': stats,
                        'stats': stats,
                        'file_hash': file_hash,
                        'message': f'File analyzed successfully (took {int(time.time() - start_time)}s)',
                        'already_exists': False,
                        'error': None
                    }
            
            # Timeout - analysis still pending
            return {
                'is_malicious': None,
                'analysis_id': analysis_id,
                'type': file_type,
                'file_hash': file_hash,
                'detections': None,
                'stats': None,
                'message': f'File submitted for analysis but results not ready after {max_wait_time}s',
                'already_exists': False,
                'pending': True,
                'error': None
            }
        
        # Return immediately without waiting
        return {
            'is_malicious': None,
            'analysis_id': analysis_id,
            'type': file_type,
            'file_hash': file_hash,
            'detections': None,
            'stats': None,
            'message': 'File submitted for analysis',
            'already_exists': False,
            'pending': True,
            'error': None
        }
