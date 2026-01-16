# Angler - Email Processing Web Application

A Flask-based web application for processing and managing email files (.eml format) used to analyze review phishing attempts.

## Project Overview

Angler is a Python web application built with Flask that allows users to upload and process email files. The application features a clean interface with multiple views including an admin panel and Forum section.

## Features

- **Email Upload & Analysis**: Upload and process up to 5 .eml files simultaneously for phishing detection
- **User Authentication**: User registration, login, and account management
- **Multiple Views**: 
  - Main index page with file upload form
  - Forum/Discussion section for collaborative analysis
  - User Statistics panel
  - Account management page
  - About Us information page
- **LLM Integration**: AI-powered email analysis for phishing detection
- **Database Storage**: Persistent storage of emails, users, analysis results, and discussions

## Technology Stack

- **Backend**: Python 3, Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite

## Project Structure

```
Fish/
├── Server.py                    # Main Flask application server
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── api/                         # API modules
├── db/
│   ├── schema.sql              # Database schema (User, Email, Analysis, Discussion, Comment)
│   └── emails.db               # SQLite database (auto-created)
├── static/
│   ├── Helper_eml.py           # Email parsing and processing utilities
│   ├── Style.css               # Application styling
│   ├── script.js               # Client-side JavaScript
│   └── how_to_temp.png         # Template image
├── flask_session/              # Server-side session storage
└── templates/
    ├── index.html              # Main landing page
    ├── form.html               # Email upload form
    ├── Forum.html              # Discussion forum
    ├── Statistics.html          # User statistics
    ├── Account.html            # Account management
    └── AboutUs.html            # About page
```

## Installation

### Prerequisites

- Python 3.x
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Sebastian0324/Fishing.git
cd Fish
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables, should be configured in a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env

API_KEY
From OpenRouter Create an Account and then a Key: 
https://openrouter.ai/settings/keys

ABUSEIPDB_API_KEY
From AbuseIPDB Create an Account and then a Key:
https://www.abuseipdb.com/account/api#create-api-key <-- 

```

4. Run the application:

**Development Mode (Debug ON - with auto-reload):**
```bash
python Server.py
```
- Automatically reloads on code changes
- Shows detailed error messages with interactive debugger
- Best for active development and debugging

**"Production" Mode (Debug OFF - without auto-reload):**
```bash
flask --app Server.py run
```
- No automatic reloads (manual restart required for code changes)
- Cleaner error handling
- Note: Flask's development server is not suitable for production. For production deployment, use a WSGI server like Gunicorn or Waitress instead.

5. Access the application at `http://localhost:5000`

## Usage

### Email Upload & Analysis

The `/upload` endpoint processes up to 5 `.eml` files simultaneously and extracts key information for phishing detection.

#### Data Extraction
When `.eml` files are uploaded, the system automatically extracts:

1. **Sender IP Address** - Extracted from the "Received" headers
2. **Sender Email Address** - Extracted from the "From" header
3. **Sender Name** - Display name of the sender
4. **Subject Line** - Email subject
5. **Email Body** - Plain text or HTML-converted body, cleaned and formatted
6. **URLs** - All HTTP/HTTPS URLs found in the email body
7. **File Metadata** - SHA256 hash, file size, upload timestamp

#### Database Storage
All extracted data is stored in the SQLite database (`db/emails.db`) with the following tables:

**Email Table:**
- `Email_ID` - Unique identifier
- `User_ID` - Associated user
- `Eml_file` - Raw email file (BLOB)
- `Sender_IP` - The sender's IP address
- `From_Addr` - Sender email address
- `Body_Text` - Full plain text body optimized for LLM analysis
- `Extracted_URLs` - JSON array of all URLs found
- `SHA256` - Hash of the file for duplicate detection
- `Size_Bytes` - File size
- `Received_At` - Timestamp when uploaded
- `Tag` - Optional classification tag

**User Table:**
- `User_ID` - Unique identifier
- `Username` - User login name
- `Password_Hash` - SHA3-512 hashed password

**Analysis Table:**
- `Email_ID` - Reference to analyzed email
- `Score` - Phishing risk score
- `Analyzed` - Analysis completion flag
- `Verdict` - Classification (Phishing/Suspicious/Benign)
- `Details_json` - Detailed analysis results
- `Analyzed_At` - Analysis timestamp

**Discussion & Comment Tables:**
- Collaborative discussion and commenting system for email analysis

## HTTP Status Codes & Error Handling

The application uses standard HTTP status codes to indicate the success or failure of API requests. All responses include:
- `success`: Boolean indicating if the request was successful
- `status_code`: The HTTP status code
- `message`: A human-readable message describing the result
- `error`: (On failure) A short error identifier

### Status Code Reference

#### Success Codes
- **200 OK**: Request successful
- **201 Created**: Resource created successfully (not currently used)

#### Client Error Codes (4xx)
- **400 Bad Request**: Invalid input, missing required fields, or malformed request
  - Missing required fields (username, password, etc.)
  - Invalid file type (non-.eml files)
  - Password mismatch during signup
  - Empty filename or invalid data
  
- **401 Unauthorized**: Authentication failed
  - Invalid password during login
  - Invalid API key for external services
  
- **404 Not Found**: Resource not found
  - User account does not exist during login
  
- **409 Conflict**: Resource conflict
  - Username already exists during signup
  
- **413 Payload Too Large**: File size exceeds limit
  - Email file exceeds 1MB limit
  - More than 5 files uploaded at once

#### Server Error Codes (5xx)
- **429 Too Many Requests**: Rate limit exceeded
  - API rate limit exceeded (LLM or AbuseIPDB)
  
- **500 Internal Server Error**: Server-side error
  - Database connection failures
  - Unexpected processing errors
  - External API errors

### Error Response Format

All error responses follow this structure:

```json
{
  "success": false,
  "error": "Short error identifier",
  "status_code": 400,
  "message": "Detailed human-readable error message"
}
```

**Example Error Response:**
```json
{
  "success": false,
  "error": "Invalid file type",
  "status_code": 400,
  "message": "File 'document.pdf' is not a .eml file. Only .eml files are supported."
}
```

## API Endpoints

### Authentication

#### POST /Signup
Create a new user account

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Fields:
  - `Username`: Desired username (required)
  - `Password`: User password (required)
  - `pass-ver`: Password verification (must match Password)

**Success Response (200):**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Account created successfully"
}
```

**Error Responses:**
- **400**: Missing fields or password mismatch
  ```json
  {
    "success": false,
    "error": "Missing required fields",
    "status_code": 400,
    "message": "Username, Password, and password verification are required"
  }
  ```
- **409**: Username already exists
  ```json
  {
    "success": false,
    "error": "User already exists",
    "status_code": 409,
    "message": "Username 'john_doe' is already registered"
  }
  ```
- **500**: Database error

#### POST /login
Authenticate user and create session

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Fields:
  - `name`: Username (required)
  - `pass`: Password (required)

**Success Response (200):**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Login successful"
}
```

**Error Responses:**
- **400**: Missing credentials
  ```json
  {
    "success": false,
    "error": "Missing credentials",
    "status_code": 400,
    "message": "Username and password are required"
  }
  ```
- **404**: User not found
  ```json
  {
    "success": false,
    "error": "User not found",
    "status_code": 404,
    "message": "No account found with username 'john_doe'"
  }
  ```
- **401**: Invalid password
  ```json
  {
    "success": false,
    "error": "Invalid password",
    "status_code": 401,
    "message": "The password you entered is incorrect"
  }
  ```
- **500**: Database error

#### GET /logout
Log out current user

**Request:**
- Method: `GET`
- No parameters required

**Success Response (200):**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Logged out successfully"
}
```

### Email Processing

#### POST /upload
Upload and analyze email files (max 5 files, max 1MB per file)

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Field name: `file`
- File type: `.eml`
- Max files: 5
- Max size: 1MB per file

**Success Response (200):**
```json
{
  "success": true,
  "status_code": 200,
  "email_id": 1,
  "message": "Successfully uploaded and processed 1 file(s)",
  "data": {
    "sender_ip": "192.168.1.100",
    "sender_email": "john.doe@example.com",
    "body_text": "Full email body text...",
    "body_preview": "First 200 characters of email body...",
    "urls_count": 3,
    "urls": [
      "https://example.com",
      "https://secure-site.com/login",
      "http://another-example.org/page"
    ]
  }
}
```

**Error Responses:**
- **400**: Invalid request
  ```json
  {
    "success": false,
    "error": "No file uploaded",
    "status_code": 400,
    "message": "Please select at least one .eml file to upload"
  }
  ```
- **400**: Too many files
  ```json
  {
    "success": false,
    "error": "Too many files",
    "status_code": 400,
    "message": "Maximum 5 files allowed. Please select fewer files."
  }
  ```
- **400**: Invalid file type
  ```json
  {
    "success": false,
    "error": "Invalid file type",
    "status_code": 400,
    "message": "File 'document.pdf' is not a .eml file. Only .eml files are supported."
  }
  ```
- **413**: File too large
  ```json
  {
    "success": false,
    "error": "File too large",
    "status_code": 413,
    "message": "File exceeds the 1MB size limit. Please upload a smaller file."
  }
  ```
- **500**: Processing error

### AI & Threat Intelligence APIs

#### POST /api/llm
Query the LLM API for email analysis

**Request:**
- Method: `POST`
- Content-Type: `application/json`
- Body:
  ```json
  {
    "message": "Email content to analyze"
  }
  ```

**Success Response (200):**
```json
{
  "success": true,
  "status_code": 200,
  "response": "AI-generated analysis of the email..."
}
```

**Error Responses:**
- **400**: Missing message
  ```json
  {
    "success": false,
    "error": "No message provided",
    "status_code": 400,
    "message": "Request must include a 'message' field"
  }
  ```
- **500**: LLM API error or server error

#### POST /api/check-ip
Check IP address reputation using AbuseIPDB

**Request:**
- Method: `POST`
- Content-Type: `application/json`
- Body:
  ```json
  {
    "ip_address": "192.168.1.100"
  }
  ```

**Success Response (200):**
```json
{
  "success": true,
  "status_code": 200,
  "ip_address": "192.168.1.100",
  "is_malicious": false,
  "abuse_score": 25,
  "total_reports": 5,
  "country_code": "US",
  "usage_type": "Data Center/Web Hosting/Transit",
  "isp": "Example ISP",
  "is_whitelisted": false,
  "message": "IP reputation check completed successfully"
}
```

**Error Responses:**
- **400**: Missing or invalid IP address
  ```json
  {
    "success": false,
    "error": "No IP address provided",
    "status_code": 400,
    "message": "Request must include an 'ip_address' field"
  }
  ```
- **401**: Invalid AbuseIPDB API key
- **429**: Rate limit exceeded
  ```json
  {
    "success": false,
    "error": "HTTP Error: 429",
    "status_code": 429,
    "message": "Failed to check IP reputation"
  }
  ```
- **500**: API configuration error or server error
  ```json
  {
    "success": false,
    "error": "API key not configured",
    "status_code": 500,
    "message": "AbuseIPDB API key not configured. Please add ABUSEIPDB_API_KEY to .env file"
  }
  ```

## Security Notes
- The application uses SHA3-512 for password hashing
- File uploads are limited to 1MB per file
- Maximum 5 files can be uploaded simultaneously
- Session data is stored server-side in the `flask_session/` directory

## Database

The project uses SQLite for data persistence. The database is automatically initialized on first run using the schema defined in `db/schema.sql`. The database supports:

- User authentication and management
- Email storage and metadata
- Phishing analysis results
- Discussion forums and comments with foreign key constraints

## Contributing

This is a personal project. For issues or suggestions, please open an issue on the GitHub repository.

## Contact

For questions or support, please refer to the GitHub repository issues section.
