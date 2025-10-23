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
  - User Dashboard panel
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
    ├── Dashboard.html          # User dashboard
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

From OpenRouter Create an Account and then a Key: 
https://openrouter.ai/settings/keys <-- API_KEY

```

4. Run the application:
```bash
python Server.py
```

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

## API Endpoints

### Authentication

#### POST /Signup
Create a new user account
- **Request:** `multipart/form-data` with `Username`, `Password`, `pass-ver`
- **Response:** `{"success": true}` or error message

#### POST /login
Authenticate user
- **Request:** `multipart/form-data` with `name`, `pass`
- **Response:** `{"success": true}` or error message

#### GET /logout
Log out current user
- **Response:** `{"success": true}`

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
  "email_id": 1,
  "filename": "suspicious_email.eml",
  "data": {
    "sender_ip": "192.168.1.100",
    "sender_email": "john.doe@example.com",
    "body_text": "=== EMAIL METADATA ===\nSubject: ...\n=== EMAIL BODY ===\n...",
    "body_length": 1234,
    "urls_count": 3,
    "urls": [
      "https://example.com",
      "https://secure-site.com/login",
      "http://another-example.org/page"
    ]
  },
  "uploaded_files": [
    {
      "email_id": 1,
      "filename": "suspicious_email.eml",
      "data": { ... }
    }
  ]
}
```

**Error Response (400/500):**
```json
{
  "error": "Error message here"
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
