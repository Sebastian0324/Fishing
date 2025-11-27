#!/usr/bin/python
from flask import Flask, jsonify
from flask_session import Session
from static.Helper_eml import init_db

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Limit upload size to 1MB
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        "success": False,
        "error": "File too large",
        "status_code": 413,
        "message": "File exceeds the 1MB size limit. Please upload a smaller file."
    }), 413

# Register endpoint blueprints
from endpoints import register_blueprints
register_blueprints(app)

# Initialize database on startup
init_db()
print("Database initialized successfully")

if __name__ == '__main__':
    app.run(debug=True, load_dotenv=True)
