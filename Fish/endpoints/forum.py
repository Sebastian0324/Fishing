from flask import Blueprint, request, session, render_template, jsonify
import sqlite3

bp_forum = Blueprint('bp_forum', __name__)

@bp_forum.post('/Forum_Cration')
def ForumCreation():
    return jsonify({
            "success": True,
            "status_code": 200,
            "message": "Creation complet",
            "obj": render_template("ForumCreation.html")
        }), 200
