import sqlite3
from flask import Blueprint, jsonify, render_template, session

from Analysis.mailstore import DB_PATH

bp_ui = Blueprint('ui', __name__)

@bp_ui.route('/')
def form():
    return render_template('index.html')

@bp_ui.route('/Forum')
def Forum():
    return render_template('Forum.html')

@bp_ui.route('/Dashboard')
def admin():
    return render_template('Dashboard.html')

@bp_ui.route('/Account')
def account():
    emails = ''
    if (session['name'] != None):
        try:
            # Connect to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""SELECT Email.Email_ID, Analysis.Analyzed_At, Email.Title FROM Email 
                           LEFT JOIN Analysis ON Email.Email_ID = Analysis.Email_ID WHERE User_ID = ?""",
                       (session["user_id"], ))
            
            q = cursor.fetchall()
            emails = [(id, str(title).strip('"'), str(time).split('T')[0]) for id, time, title in q]
            print(q)
            print(session["user_id"])

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Database error: {str(e)}",
                "status_code": 500,
                "message": "Failed to load emails due to server error"
            }), 500

    return render_template('Account.html', emails = emails)

@bp_ui.route('/AboutUs')
def info():
    return render_template('AboutUs.html')
