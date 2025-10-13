import email
from email import policy
from email.parser import BytesParser
import re
import sqlite3

# Database configuration
DB_PATH = 'db/emails.db'

def init_db():
    """Initialize database with schema"""
    conn = sqlite3.connect(DB_PATH)
    with open('db/schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def extract_sender_ip(msg):
    """Extract sender IP from Received headers"""
    received_headers = msg.get_all('Received', [])
    for header in received_headers:
        # Look for IP addresses in brackets or after 'from'
        # Pattern matches IPv4 addresses
        ip_match = re.search(r'\[?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]?', header)
        if ip_match:
            return ip_match.group(1)
    return None

def extract_urls(text):
    """Extract all URLs from text"""
    if not text:
        return []
    # Pattern to match http and https URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    return urls

def parse_eml_file(file_content):
    """Parse .eml file and extract required data"""
    # Parse the email
    msg = BytesParser(policy=policy.default).parsebytes(file_content)
    
    # Extract sender IP
    sender_ip = extract_sender_ip(msg)
    
    # Extract sender email
    from_header = msg.get('From', '')
    # Extract email address from "Name <email@domain.com>" format
    email_match = re.search(r'<(.+?)>|([^\s<>]+@[^\s<>]+)', from_header)
    sender_email = email_match.group(1) if email_match and email_match.group(1) else (email_match.group(2) if email_match else from_header)
    
    # Extract plain text body
    body_text = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    body_text = part.get_content()
                    break
                except:
                    pass
    else:
        if msg.get_content_type() == "text/plain":
            try:
                body_text = msg.get_content()
            except:
                pass
    
    # Extract URLs from body
    urls = extract_urls(body_text)
    
    return {
        'sender_ip': sender_ip,
        'sender_email': sender_email,
        'body_text': body_text,
        'urls': urls
    }
