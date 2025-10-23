from email import policy
from email.parser import BytesParser
import re
import sqlite3
import json
from html.parser import HTMLParser
from io import StringIO

# Database configuration
DB_PATH = 'db/emails.db'

def init_db():
    """Initialize database with schema"""
    conn = sqlite3.connect(DB_PATH)
    with open('db/schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


# ============================================================================
# HELPER FUNCTIONS - MODULAR EXTRACTION
# ============================================================================

def extract_sender_ip(msg):
    """
    Extract sender IP from Received headers.
    Returns the first valid IPv4 address found.
    """
    received_headers = msg.get_all('Received', [])
    for header in received_headers:
        # Pattern matches IPv4 addresses
        ip_match = re.search(r'\[?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]?', header)
        if ip_match:
            ip = ip_match.group(1)
            # Basic validation - skip localhost and invalid ranges
            if not ip.startswith('127.') and not ip.startswith('0.'):
                return ip
    return None


def extract_sender_info(msg):
    """
    Extract sender name and email address.
    Returns dict with 'name' and 'email' keys.
    """
    from_header = msg.get('From', '')
    
    # Parse "Display Name <email@domain.com>" format
    name_email_match = re.search(r'(.+?)\s*<(.+?)>', from_header)
    if name_email_match:
        display_name = name_email_match.group(1).strip('"').strip()
        email_addr = name_email_match.group(2).strip()
    else:
        # Try to extract just email
        email_match = re.search(r'([^\s<>]+@[^\s<>]+)', from_header)
        display_name = None
        email_addr = email_match.group(1) if email_match else from_header
    
    return {
        'name': display_name,
        'email': email_addr
    }


def extract_urls(text):
    """
    Extract all URLs from text.
    Returns list of unique URLs.
    """
    if not text:
        return []
    
    # Pattern to match http and https URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    
    # Return unique URLs while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls


# ============================================================================
# HTML TO TEXT CONVERSION
# ============================================================================

class HTMLToTextConverter(HTMLParser):
    """
    Convert HTML to readable text while preserving links.
    Shows both link text and actual URL for anchor tags.
    """
    def __init__(self):
        super().__init__()
        self.text = StringIO()
        self.current_link = None
        self.current_link_text = StringIO()
        
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            # Start collecting link text
            self.current_link = dict(attrs).get('href', '')
            self.current_link_text = StringIO()
        elif tag in ['br', 'p', 'div', 'tr']:
            self.text.write('\n')
    
    def handle_endtag(self, tag):
        if tag == 'a' and self.current_link:
            # Output link in format: "display text → actual_url"
            link_text = self.current_link_text.getvalue().strip()
            if link_text and self.current_link:
                # Show both if they're different
                if link_text != self.current_link and not self.current_link.startswith('#'):
                    self.text.write(f"{link_text} → {self.current_link}")
                else:
                    self.text.write(self.current_link)
            elif self.current_link:
                self.text.write(self.current_link)
            
            self.current_link = None
            self.current_link_text = StringIO()
    
    def handle_data(self, data):
        if self.current_link is not None:
            # Collecting link text
            self.current_link_text.write(data)
        else:
            self.text.write(data)
    
    def get_text(self):
        return self.text.getvalue()


def html_to_text(html_content):
    """
    Convert HTML content to readable text.
    Preserves links in 'text → url' format.
    """
    if not html_content:
        return ""
    
    try:
        converter = HTMLToTextConverter()
        converter.feed(html_content)
        return converter.get_text()
    except Exception as e:
        # Fallback: simple tag stripping
        return re.sub(r'<[^>]+>', ' ', html_content)


# ============================================================================
# TEXT CLEANING
# ============================================================================

def clean_text(text):
    """
    General-purpose text cleaner that:
    - Removes quoted replies (lines starting with >)
    - Removes common email signatures
    - Normalizes whitespace
    - Retains URLs and visible text
    """
    if not text:
        return ""
    
    lines = text.split('\n')
    cleaned_lines = []
    in_signature = False
    
    for line in lines:
        # Remove quoted replies
        if line.strip().startswith('>'):
            continue
        
        # Detect signature start
        if re.match(r'^[-_]{2,}|^--\s*$', line.strip()):
            in_signature = True
            continue
        
        # Common signature indicators
        if re.search(r'(sent from|get outlook|unsubscribe)', line.lower()):
            in_signature = True
        
        # Skip signature content
        if in_signature:
            continue
        
        # Keep non-empty lines
        if line.strip():
            cleaned_lines.append(line)
    
    # Join and normalize whitespace
    cleaned = '\n'.join(cleaned_lines)
    
    # Normalize multiple blank lines to single blank line
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    # Normalize spaces
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    
    return cleaned.strip()


# ============================================================================
# MESSAGE BODY EXTRACTION
# ============================================================================

def extract_message_body(msg, prefer_plain=True):
    """
    Extract message body with support for both plain text and HTML.
    Handles multipart emails and concatenates multiple HTML/plain parts.
    
    Args:
        msg: Parsed email.message.EmailMessage object
        prefer_plain: If True, prefer plain text over HTML for display
    
    Returns:
        dict with 'text', 'format', and 'html_links' keys
    """
    plain_text_parts = []
    html_text_parts = []

    # Walk through all parts
    if msg.is_multipart():
        for part in msg.walk():
            # Skip multipart containers
            if part.get_content_maintype() == "multipart":
                continue

            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", "")).lower()

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            try:
                payload = part.get_payload(decode=True)  # bytes
                if not payload:
                    continue
                charset = part.get_content_charset() or 'utf-8'
                decoded_text = payload.decode(charset, errors='replace')
            except Exception:
                continue

            if content_type == "text/plain":
                plain_text_parts.append(decoded_text)
            elif content_type == "text/html":
                html_text_parts.append(decoded_text)
    else:
        # Single-part message
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                decoded_text = payload.decode(charset, errors='replace')
                if content_type == "text/plain":
                    plain_text_parts.append(decoded_text)
                elif content_type == "text/html":
                    html_text_parts.append(decoded_text)
        except Exception:
            pass

    # Concatenate parts
    plain_text = "\n".join(plain_text_parts) if plain_text_parts else None
    html_text = "\n".join(html_text_parts) if html_text_parts else None

    # Convert HTML to text and extract links
    html_links = []
    if html_text:
        body_text_from_html = html_to_text(html_text)
        html_links = extract_urls(body_text_from_html)
    else:
        body_text_from_html = None

    # Decide which body to use
    if html_text and (not prefer_plain or not plain_text):
        body_text = body_text_from_html
        body_format = 'html'
    elif plain_text:
        body_text = plain_text
        body_format = 'plain'
    else:
        body_text = ''
        body_format = 'none'

    # Extract URLs from body text itself
    body_urls = extract_urls(body_text)
    # Combine with links extracted from HTML conversion
    all_urls = list(dict.fromkeys(body_urls + html_links))  # remove duplicates while preserving order

    return {
        'text': body_text,
        'format': body_format,
        'html_links': all_urls
    }

# ============================================================================
# EMAIL FORMAT NORMALIZATION
# ============================================================================

def normalize_eml_format(file_content):
    """
    Normalize .eml format to ensure proper header-body separation.
    
    Some .eml files may have blank lines within headers or improper formatting.
    This function ensures RFC 5322 compliance by:
    1. Removing blank lines within the header section
    2. Ensuring exactly one blank line separates headers from body
    
    Args:
        file_content: Raw bytes of .eml file
    
    Returns:
        Normalized bytes ready for parsing
    """
    try:
        # Decode to string for processing
        content_str = file_content.decode('utf-8', errors='replace')
        lines = content_str.split('\n')
        
        # First pass: identify where headers actually end
        header_lines = []
        body_start_idx = len(lines)
        
        for i, line in enumerate(lines):
            # Check if this looks like a header line
            is_header = False
            if line and line[0] not in (' ', '\t'):
                # Could be a header if it has a colon
                parts = line.split(':', 1)
                if len(parts) == 2:
                    # Check if the field name is valid (no spaces, starts with letter/digit)
                    field_name = parts[0].strip()
                    if field_name and not ' ' in field_name:
                        is_header = True
            elif line and line[0] in (' ', '\t'):
                # Continuation line - is header if we're still in headers
                is_header = len(header_lines) > 0
            
            if is_header:
                header_lines.append(line)
            elif line.strip() == '':
                # Blank line - could be separator or within headers
                # Look ahead to see if there are more headers
                has_more_headers = False
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j]
                    if next_line.strip() and ':' in next_line and next_line[0] not in (' ', '\t'):
                        # Found another header-like line
                        has_more_headers = True
                        break
                    elif next_line.strip() and next_line[0] not in (' ', '\t', '-'):
                        # Found non-header content
                        break
                
                if not has_more_headers:
                    # This is the header-body separator
                    body_start_idx = i + 1
                    break
            else:
                # Non-header, non-blank line - headers are done
                body_start_idx = i
                break
        
        # Rebuild the email
        normalized_lines = header_lines + [''] + lines[body_start_idx:]
        
        # Rejoin and encode back to bytes
        normalized_str = '\n'.join(normalized_lines)
        return normalized_str.encode('utf-8', errors='replace')
        
    except Exception as e:
        # If normalization fails, return original content
        return file_content


# ============================================================================
# MAIN PARSING ROUTINE
# ============================================================================

def parse_Eml_file(file_content, max_body_length=5000, include_json=False, enhanced_format=False):
    """
    Parse .eml file and extract data suitable for LLM analysis.
    
    Args:
        file_content: Raw bytes of .eml file
        max_body_length: Maximum characters to extract from body (None for unlimited)
        include_json: If True, also return formatted JSON string
        enhanced_format: If True, return enhanced nested format; if False, return simple format for backward compatibility
    
    Returns:
        Dictionary with structured email data, optionally with JSON string
    """
    try:
        # Normalize the email format first
        normalized_content = normalize_eml_format(file_content)
        
        # Parse the email
        msg = BytesParser(policy=policy.default).parsebytes(normalized_content)
    except Exception as e:
        # Handle malformed emails gracefully
        return {
            'error': 'Failed to parse email',
            'error_details': str(e),
            'valid': False
        }
    
    # Extract sender information
    sender_info = extract_sender_info(msg)
    
    # Extract sender IP
    sender_ip = extract_sender_ip(msg)
    
    # Extract subject
    subject = msg.get('Subject', '').strip()
    
    # Extract message body
    body_data = extract_message_body(msg, prefer_plain=True)
    body_text = body_data['text']
    
    # Clean the body text
    cleaned_body = clean_text(body_text)
    
    # Truncate if needed
    if max_body_length and len(cleaned_body) > max_body_length:
        cleaned_body = cleaned_body[:max_body_length] + "\n[... truncated]"
        truncated = True
    else:
        truncated = False
    
    # Extract URLs from cleaned body
    body_urls = extract_urls(cleaned_body)
    
    # Combine with HTML links if any
    all_urls = body_urls + body_data.get('html_links', [])
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    # Build structured output
    if enhanced_format:
        # Enhanced format for LLM analysis
        result = {
            'valid': True,
            'subject': subject,
            'sender': {
                'email': sender_info['email'],
                'name': sender_info['name'],
                'ip': sender_ip
            },
            'body': {
                'text': cleaned_body,
                'format': body_data['format'],
                'truncated': truncated,
                'length': len(cleaned_body)
            },
            'urls': unique_urls,
            'url_count': len(unique_urls),
            'phishing_indicators': {
                'suspicious_urls': len(unique_urls) > 5  # Heuristic
            }
        }
        
        # Optionally include JSON string
        if include_json:
            result['json_output'] = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        # Simple format for backward compatibility
        result = {
            'sender_ip': sender_ip,
            'sender_email': sender_info['email'],
            'body_text': cleaned_body,
            'urls': unique_urls
        }
    
    return result

def generate_llm_body(parsed_email):
    """
    Generate a structured body text optimized for LLM analysis.
    Clearly indicates the source format and provides context about the email content.
    
    Args:
        parsed_email: Dictionary containing parsed email data with enhanced format
    
    Returns:
        String with structured, LLM-friendly email content
    """
    subject = parsed_email.get('subject', '')
    body_data = parsed_email.get('body', {})
    body_text = body_data.get('text', '')
    body_format = body_data.get('format', 'unknown')
    truncated = body_data.get('truncated', False)
    sender = parsed_email.get('sender', {})
    
    llm_text_parts = []
    
    # Header section with metadata
    llm_text_parts.append("=== EMAIL METADATA ===")
    if subject:
        llm_text_parts.append(f"Subject: {subject}")
    if sender.get('email'):
        sender_name = sender.get('name')
        if sender_name:
            llm_text_parts.append(f"From: {sender_name} <{sender.get('email')}>")
        else:
            llm_text_parts.append(f"From: {sender.get('email')}")
    if sender.get('ip'):
        llm_text_parts.append(f"Sender IP: {sender.get('ip')}")
    
    # Body section with clear format indication
    llm_text_parts.append("\n=== EMAIL BODY ===")
    
    # Indicate the source format clearly
    if body_format == 'html':
        llm_text_parts.append("[Source: HTML email - converted to plain text for analysis]")
    elif body_format == 'plain':
        llm_text_parts.append("[Source: Plain text email]")
    elif body_format == 'none':
        llm_text_parts.append("[Source: No text content found in email]")
    else:
        llm_text_parts.append(f"[Source: {body_format}]")
    
    if truncated:
        llm_text_parts.append("[Note: Content has been truncated due to length]")
    
    llm_text_parts.append("")  # Blank line before body
    llm_text_parts.append(body_text)
    
    return "\n".join(llm_text_parts)
