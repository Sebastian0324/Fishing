# Fish - Email Processing Web Application

A Flask-based web application for processing and managing email files (.eml format) used to analyze review phishing attempts.

## Project Overview

Fish is a Python web application built with Flask that allows users to upload and process email files. The application features a clean interface with multiple views including an admin panel and blog section.

## Features

- **Email Upload**: Upload and process .eml (email) files through a web interface
- **Multiple Views**: 
  - Main index page with file upload form
  - Blog section
  - Admin / User panel

## Technology Stack

- **Backend**: Python 3, Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite

## Project Structure

```
Fish/
├── server.py             
├── README.md             
├── .env.example          
├── .gitignore            
├── db
│   └── schema.sql        
├── static
│   ├── Style.css         
│   └── script.js         
└── templates
    ├── form.html         
    ├── index.html        
    ├── blogg.html        
    └── AdminPanel.html   
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
pip install flask
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run the application:
```bash
python server.py
```

5. Access the application at `http://localhost:5000`

## Usage
The `/upload` endpoint has been modified to parse `.eml` files and extract key information for phishing detection.

### Features

#### Data Extraction
When a `.eml` file is uploaded, the system automatically extracts:

1. **Sender IP Address** - Extracted from the "Received" headers
2. **Sender Email Address** - Extracted from the "From" header
3. **Plain Text Body** - The email body in plain text format
4. **URLs** - All HTTP/HTTPS URLs found in the email body

#### Database Storage
All extracted data is stored in the SQLite database (`db/emails.db`) in the `Email` table with the following fields:

- `Sender_IP` - The sender's IP address
- `Body_Text` - Full plain text body of the email
- `Extracted_URLs` - JSON array of all URLs found
- `From_Addr` - Sender email address
- `SHA256` - Hash of the file for duplicate detection
- `Size_Bytes` - File size
- `Received_At` - Timestamp when uploaded

## API Endpoint

#### POST /upload

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Field name: `file`
- File type: `.eml`

**Success Response (200):**
```json
{
  "success": true,
  "email_id": 1,
  "data": {
    "sender_ip": "192.168.1.100",
    "sender_email": "john.doe@example.com",
    "body_preview": "Hello,\n\nThis is a test email...",
    "urls_count": 3,
    "urls": [
      "https://example.com",
      "https://secure-site.com/login",
      "http://another-example.org/page"
    ]
  }
}
```

**Error Response (400/500):**
```json
{
  "error": "Error message here"
}
```

## Configuration

Environment variables should be configured in a `.env` file (copy from `.env.example`):

```
# Add required credentials here
```

## Database

The project includes a database schema (`db/schema.sql`) for future data persistence. SQLite support is included in the codebase (currently commented out in `server.py`).

## Contributing

This is a personal project. For issues or suggestions, please open an issue on the GitHub repository.

## Contact

For questions or support, please refer to the GitHub repository issues section.
