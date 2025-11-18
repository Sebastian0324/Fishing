import requests
import os
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
    
    def scan_file(self, file_content, filename="file.eml", password=None):
        """
        Upload and scan a file with VirusTotal
        
        Args:
            file_content (bytes): The file content to scan
            filename (str): The filename (default: "file.eml")
            password (str): Optional password for protected ZIP files
        
        Returns:
            dict: API response containing scan results
        """
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
                'error': None
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            if e.response.status_code == 400:
                error_msg = "Bad request - file may be invalid or password incorrect"
            elif e.response.status_code == 401:
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
    
    def is_malicious(self, file_content, filename="file.eml"):
        """
        Scan a file and determine if it's malicious based on detection results
        
        Args:
            file_content (bytes): The file content to scan
            filename (str): The filename (default: "file.eml")
        
        Returns:
            dict: Contains analysis information including malicious status
        """
        # First, upload and scan the file
        scan_result = self.scan_file(file_content, filename)
        
        if not scan_result['success']:
            return {
                'is_malicious': None,
                'analysis_id': None,
                'detections': None,
                'error': scan_result['error']
            }
        
        # Extract analysis ID
        data = scan_result['data']
        analysis_id = data.get('id', '')
        file_type = data.get('type', '')
        
        return {
            'is_malicious': None,  # Requires polling the analysis endpoint
            'analysis_id': analysis_id,
            'type': file_type,
            'detections': None,
            'message': 'File submitted for analysis',
            'error': None
        }


# Example usage
if __name__ == "__main__":
    # Initialize the VirusTotal client
    vt = VirusTotal()
    
    # Example: scan a test file
    test_content = b"This is a test file content"
    
    # Scan the file
    result = vt.is_malicious(test_content, "test.txt")
    
    if result['error']:
        print(f"Error: {result['error']}")
    else:
        print(f"File submitted successfully")
        print(f"Analysis ID: {result['analysis_id']}")
        print(f"Type: {result['type']}")
        print(f"Message: {result['message']}")
