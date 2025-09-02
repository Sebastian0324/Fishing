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
def fetch_emails():
    # Connect to Gmail IMAP server
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login("e-mail", "pass")
    mail.select("inbox")

    return mail.search(None, "ALL")

if __name__ == '__main__':
    app.run(debug=True)