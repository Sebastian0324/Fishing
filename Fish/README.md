# Fish - Email Processing Web Application

A Flask-based web application for processing and managing email files (.eml format) used to analyze review phishing attempts.

## Project Overview

Fish is a Python web application built with Flask that allows users to upload and process email files. The application features a clean interface with multiple views including an admin panel and Forum section.

## Features

- **Email Upload**: Upload and process .eml (email) files through a web interface
- **Multiple Views**: 
  - Main index page with file upload form
  - Forum section
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
    ├── Forum.html        
    └── Dashboard.html   
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

### Uploading Email Files
```
# ADD Rought tutorial here and/ord consult the Tutorial on the website
```

### API Endpoints

```
# ADD enpoints and what they do here
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
