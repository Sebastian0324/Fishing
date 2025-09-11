#!/usr/bin/python

import imaplib, email
from flask import Flask, request, jsonify, render_template
# import sqlite3  # Database

app = Flask(__name__)

# Routes
@app.route('/')
def form():
    text = "Hello, World!"
    return render_template('form.html', text=text)

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
