#!/usr/bin/python

import imaplib, email
from flask import Flask, request, jsonify, render_template
from Analysis.mailstore import init_db, store_eml_bytes, get_anonymous_user_id
# import sqlite3  # Database

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024  # 15 MB

# Kör init en gång vid start
init_db()

# Routes
@app.route('/')
def form():
    return render_template('index.html')

# Routes
@app.route('/Forum')
def Forum():
    return render_template('Forum.html')

# Routes
@app.route('/Dashboard')
def admin():
    return render_template('Dashboard.html')

# Routes
@app.route('/Account')
def account():
    return render_template('Account.html')

# Routes
@app.route('/AboutUs')
def info():
    return render_template('AboutUs.html')

# test function
@app.post('/test')
def set_text():
    return "AAA"

# Get Emails
@app.post('/upload')
def upload():
    if "file" not in request.files:
        return jsonify(ok=False, error="No file"), 400
    f = request.files["file"]
    if not f or not f.filename.lower().endswith(".eml"):
        return jsonify(ok=False, error="Only .eml files are accepted"), 400
    
    # Om user_id inte skickas → använd 'anonymous'
    user_id = request.form.get("user_id", type=int)
    if not user_id:
        user_id = get_anonymous_user_id()

    tag = request.form.get("tag")  # valfritt
    eml_bytes = f.read()

    try:
        email_id = store_eml_bytes(eml_bytes, user_id=user_id, tag=tag)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

    return jsonify(ok=True, email_id=email_id, uploader_user_id=user_id)




if __name__ == '__main__':
    app.run(debug=True)
