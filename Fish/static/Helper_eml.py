# static/helper_eml.py
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
import sqlite3

# Single source of truth for paths
DB_PATH = "Fish/db/emails.db"
SCHEMA_PATH = "Fish/db/schema.sql"

# ---------------------- DB init ----------------------

def init_db(db_path: str = DB_PATH, schema_path: str = SCHEMA_PATH) -> None:
    """Create DB directory, apply schema, and set sane pragmas."""
    dbp = Path(db_path)
    dbp.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = Path(schema_path).read_text(encoding="utf-8")

    with sqlite3.connect(str(dbp)) as con:
        con.execute("PRAGMA foreign_keys = ON;")
        con.execute("PRAGMA journal_mode = WAL;")
        con.execute("PRAGMA synchronous = NORMAL;")
        try:
            con.execute("BEGIN;")
            con.executescript(schema_sql)
        except sqlite3.Error:
            con.rollback()
            raise
        else:
            con.commit()

# ------------------ EML normalization ----------------

def _normalize_eml_format(file_content: bytes) -> bytes:
    """Ensure one blank line between headers and body; return original on failure."""
    try:
        s = file_content.decode("utf-8", errors="replace")
        lines = s.split("\n")
        header_lines = []
        body_start = len(lines)

        for i, line in enumerate(lines):
            is_header = False
            if line and line[0] not in (" ", "\t"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    field = parts[0].strip()
                    if field and " " not in field:
                        is_header = True
            elif line and line[0] in (" ", "\t"):
                is_header = len(header_lines) > 0

            if is_header:
                header_lines.append(line)
            elif line.strip() == "":
                # look-ahead: is this the real separator?
                has_more_headers = False
                for nxt in lines[i+1:i+6]:
                    if nxt.strip() and ":" in nxt and nxt[0] not in (" ", "\t"):
                        has_more_headers = True
                        break
                    elif nxt.strip() and nxt[0] not in (" ", "\t", "-"):
                        break
                if not has_more_headers:
                    body_start = i + 1
                    break
            else:
                body_start = i
                break

        return ("\n".join(header_lines + [""] + lines[body_start:])).encode("utf-8", errors="replace")
    except Exception:
        return file_content

def _parse_message(eml_bytes: bytes):
    normalized = _normalize_eml_format(eml_bytes)
    return BytesParser(policy=policy.default).parsebytes(normalized)

# ------------------- Field helpers -------------------

def _iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def extract_received_at_iso(msg) -> str:
    """Prefer Date: header (normalized to UTC ISO-8601 Z). Fallback to now()."""
    hdr = msg.get("Date")
    if hdr:
        try:
            return _iso_utc(parsedate_to_datetime(hdr))
        except Exception:
            pass
    return _iso_utc(datetime.now(timezone.utc))

def extract_sender_ip(msg) -> str | None:
    for hdr in msg.get_all("Received", []) or []:
        m = re.search(r"\[?(\d{1,3}(?:\.\d{1,3}){3})\]?", hdr)
        if m:
            ip = m.group(1)
            if not ip.startswith("127.") and not ip.startswith("0."):
                return ip
    return None

def extract_sender_info(msg) -> dict[str, str | None]:
    from_header = msg.get("From", "") or ""
    m = re.search(r"(.+?)\s*<(.+?)>", from_header)
    if m:
        return {"name": m.group(1).strip('" ').strip(), "email": m.group(2).strip()}
    m2 = re.search(r"([^\s<>]+@[^\s<>]+)", from_header)
    return {"name": None, "email": (m2.group(1) if m2 else (from_header or None))}

# ------------------- HTML → Text & URLs -------------------

class _HTMLToText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = StringIO()
        self.link = None
        self.link_text = StringIO()

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.link = dict(attrs).get("href", "")
            self.link_text = StringIO()
        elif tag in ["br", "p", "div", "tr"]:
            self.text.write("\n")

    def handle_endtag(self, tag):
        if tag == "a" and self.link is not None:
            t = self.link_text.getvalue().strip()
            if t and self.link and not self.link.startswith("#"):
                self.text.write(t if t == self.link else f"{t} → {self.link}")
            elif self.link:
                self.text.write(self.link)
            self.link = None
            self.link_text = StringIO()

    def handle_data(self, data):
        (self.link_text if self.link is not None else self.text).write(data)

    def get_text(self) -> str:
        return self.text.getvalue()

def _html_to_text(html: str | None) -> str:
    if not html:
        return ""
    try:
        p = _HTMLToText(); p.feed(html); return p.get_text()
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)

def extract_urls(text: str | None) -> list[str]:
    if not text:
        return []
    # keeps http/https and excludes whitespace & typical breakers
    urls = re.findall(r"https?://[^\s<>{}\|\^`\\\[\]]+", text)
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u); out.append(u)
    return out

def clean_text(text: str | None) -> str:
    if not text:
        return ""
    lines, cleaned, in_sig = text.split("\n"), [], False
    for line in lines:
        s = line.strip()
        if s.startswith(">"):           # quoted replies
            continue
        if re.match(r"^[-_]{2,}|^--\s*$", s) or re.search(r"(sent from|get outlook|unsubscribe)", s.lower()):
            in_sig = True; continue
        if in_sig:
            continue
        if s:
            cleaned.append(line)
    out = "\n".join(cleaned)
    out = re.sub(r"\n{3,}", "\n\n", out)
    out = re.sub(r"[ \t]+", " ", out)
    return out.strip()

def _extract_body(msg, prefer_plain: bool = True, include_raw_html: bool = False) -> dict:
    plain_parts, html_parts = [], []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if "attachment" in (part.get("Content-Disposition", "") or "").lower():
                continue
            ctype = part.get_content_type()
            try:
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
            except Exception:
                continue
            (plain_parts if ctype == "text/plain" else html_parts if ctype == "text/html" else []).append(text)
    else:
        ctype = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                (plain_parts if ctype == "text/plain" else html_parts if ctype == "text/html" else []).append(text)
        except Exception:
            pass

    plain_text = "\n".join(plain_parts) if plain_parts else None
    html_text  = "\n".join(html_parts)  if html_parts  else None

    html_links, text_from_html = [], None
    if html_text:
        text_from_html = _html_to_text(html_text)
        html_links = extract_urls(text_from_html)

    if html_text and (not prefer_plain or not plain_text):
        body_text, body_fmt = (text_from_html or ""), "html"
    elif plain_text:
        body_text, body_fmt = plain_text, "plain"
    else:
        body_text, body_fmt = "", "none"

    body_urls = extract_urls(body_text)
    all_urls = list(dict.fromkeys(body_urls + html_links))
    result = {"text": body_text, "format": body_fmt, "html_links": all_urls}
    if include_raw_html:
        result["raw_html"] = html_text
    return result

# -------------------- Public parsing API --------------------

def parse_eml_bytes(
    file_content: bytes,
    max_body_length: int | None = 5000,
    include_json: bool = False,
    enhanced_format: bool = True,
) -> dict:
    """
    Parse .eml bytes → structured dict.
    Adds 'received_at' (UTC ISO-8601 Z) for DB use.
    """
    try:
        msg = _parse_message(file_content)
    except Exception as e:
        return {"error": "Failed to parse email", "error_details": str(e), "valid": False}

    sender = extract_sender_info(msg)
    sender_ip = extract_sender_ip(msg)
    subject = (msg.get("Subject") or "").strip('" ').strip() or "UnTitled"
    received_at = extract_received_at_iso(msg)

    body = _extract_body(msg, prefer_plain=True)
    cleaned_body = clean_text(body["text"])

    truncated = False
    if max_body_length and len(cleaned_body) > max_body_length:
        cleaned_body = cleaned_body[:max_body_length] + "\n[... truncated]"
        truncated = True

    all_urls = list(dict.fromkeys(extract_urls(cleaned_body) + body.get("html_links", [])))

    if enhanced_format:
        result = {
            "valid": True,
            "subject": subject,
            "received_at": received_at,
            "sender": {"email": sender["email"], "name": sender["name"], "ip": sender_ip},
            "body": {"text": cleaned_body, "format": body["format"], "truncated": truncated, "length": len(cleaned_body)},
            "urls": all_urls,
            "url_count": len(all_urls),
            "phishing_indicators": {"suspicious_urls": len(all_urls) > 5},
        }
        if include_json:
            result["json_output"] = json.dumps(result, indent=2, ensure_ascii=False)
        return result

    # simple format
    return {
        "received_at": received_at,
        "sender_ip": sender_ip,
        "sender_email": sender["email"],
        "subject": subject,
        "body_text": cleaned_body,
        "urls": all_urls,
        "valid": True,
    }

def generate_email_body(parsed_email: dict) -> str:
    """For UI/DB preview: short and clean."""
    subject = parsed_email.get("subject", "")
    body_text = parsed_email.get("body", {}).get("text", "") or ""
    parts = []
    if subject:
        parts.append(f"Subject: {subject}")
    parts.append("\nEmail body:\n")
    parts.append(body_text)
    return "\n\n".join(parts)

def sanitize_html_for_display(html: str) -> str:
    """
    Sanitize HTML for safe display in forum:
    - Remove scripts, event handlers, forms
    - Convert links to non-clickable spans
    - Keep images (external URLs load normally)
    """
    import bleach
    
    # Allowed tags - keep visual elements, remove dangerous ones
    ALLOWED_TAGS = [
        'p', 'br', 'div', 'span', 'table', 'tr', 'td', 'th', 'thead', 'tbody',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b', 'em', 'i', 'u',
        'ul', 'ol', 'li', 'img', 'hr', 'blockquote', 'pre', 'code',
        'font', 'center', 'a', 'style', 'head', 'body', 'html'
    ]
    
    ALLOWED_ATTRS = {
        '*': ['style', 'class', 'id'],
        'img': ['src', 'alt', 'width', 'height'],
        'a': ['href', 'title'],
        'td': ['colspan', 'rowspan', 'width', 'height', 'align', 'valign', 'bgcolor'],
        'th': ['colspan', 'rowspan', 'width', 'height', 'align', 'valign', 'bgcolor'],
        'table': ['width', 'height', 'border', 'cellpadding', 'cellspacing', 'bgcolor', 'align'],
        'font': ['color', 'size', 'face'],
        'body': ['bgcolor', 'background'],
    }
    
    # First pass: bleach sanitization
    cleaned = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    
    # Second pass: neutralize links (convert <a> to <span>)
    cleaned = re.sub(
        r'<a\s+[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
        r'<span class="neutralized-link" title="URL: \1">\2</span>',
        cleaned,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Also handle <a> tags without quotes around href
    cleaned = re.sub(
        r'<a\s+[^>]*href=([^\s>]+)[^>]*>(.*?)</a>',
        r'<span class="neutralized-link" title="URL: \1">\2</span>',
        cleaned,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    return cleaned


def extract_email_for_display(eml_bytes: bytes) -> dict:
    """
    Extract email content for safe display in forum.
    Returns metadata + sanitized HTML body.
    """
    try:
        msg = _parse_message(eml_bytes)
    except Exception as e:
        return {"error": str(e), "valid": False}
    
    # Get metadata
    sender = extract_sender_info(msg)
    subject = (msg.get("Subject") or "").strip('" ').strip() or "No Subject"
    date = msg.get("Date") or "Unknown Date"
    
    # Get body with raw HTML
    body = _extract_body(msg, prefer_plain=False, include_raw_html=True)
    
    # Sanitize HTML (neutralize links, remove scripts)
    raw_html = body.get("raw_html")
    if raw_html:
        sanitized_html = sanitize_html_for_display(raw_html)
    else:
        # Fallback: wrap plain text in pre tag
        plain_text = body.get("text", "")
        # Escape HTML entities in plain text
        import html
        escaped = html.escape(plain_text)
        sanitized_html = f"<pre style='white-space: pre-wrap; font-family: inherit;'>{escaped}</pre>"
    
    return {
        "valid": True,
        "from_email": sender.get("email"),
        "from_name": sender.get("name"),
        "subject": subject,
        "date": date,
        "html_body": sanitized_html,
        "is_html": raw_html is not None
    }


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
