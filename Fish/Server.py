#!/usr/bin/python

import imaplib, email
from flask import Flask, request, jsonify, render_template
# import sqlite3  # Database

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False

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
        return "No file uploaded", 400
    file = request.files["file"]




if __name__ == '__main__':
    app.run(debug=True)
