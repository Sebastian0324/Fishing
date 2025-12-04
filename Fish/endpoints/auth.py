from flask import Blueprint, request, session, jsonify
import sqlite3
from bcrypt import hashpw, checkpw, gensalt
from static.Helper_eml import DB_PATH

bp_auth = Blueprint('auth', __name__)

@bp_auth.post('/Signup')
def CreateAccount():
    if (request.form.get("Username") == None or request.form.get("Password") == None or request.form.get("pass-ver") == None):
        return jsonify({
            "success": False,
            "error": "Missing required fields",
            "status_code": 400,
            "message": "Username, Password, and password verification are required"
        }), 400
    
    if (request.form.get("Password") != request.form.get("pass-ver")):
        return jsonify({
            "success": False,
            "error": "Password mismatch",
            "status_code": 400,
            "message": "Password does not match password verification"
        }), 400

    username = request.form.get("Username")
    # conect to DB and check if account allredy exist
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""SELECT Username FROM USER WHERE Username = ?""",(username, ))
        if( cursor.fetchall() ):
            return jsonify({
                "success": False,
                "error": "User already exists",
                "status_code": 409,
                "message": f"Username '{username}' is already registered"
            }), 409
        # bcrypt automatically generates salt and hashes
        password_bytes = request.form.get("Password").encode()
        password_hash = hashpw(password_bytes, gensalt()).decode()
        cursor.execute("""
                        INSERT INTO USER (
                            Username, Password_Hash
                        ) VALUES (?, ?)""", (
                        username,
                        password_hash
                    ))
        user_id = cursor.lastrowid
        session["name"] = username
        session["user_id"] = user_id
        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "status_code": 200,
            "message": "Account created successfully"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "status_code": 500,
            "message": "Failed to create account due to server error"
        }), 500

@bp_auth.post('/login')
def Login():
    username = request.form.get("name") or ""
    passw = request.form.get("pass") or ""
    if (username == None or passw == None):
        return jsonify({
            "success": False,
            "error": "Missing credentials",
            "status_code": 400,
            "message": "Username and password are required"
        }), 400
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""SELECT User_ID, Password_Hash FROM USER WHERE Username = ?""",(username, ))
        row = cursor.fetchone()
        if not row:
            return jsonify({
                "success": False,
                "error": "User not found",
                "status_code": 404,
                "message": f"No account found with username '{username}'"
            }), 404
        user_id, stored_hash = row
        # bcrypt.checkpw returns True if password matches
        if not checkpw(passw.encode(), stored_hash.encode()):
            return jsonify({
                "success": False,
                "error": "Invalid password",
                "status_code": 401,
                "message": "The password you entered is incorrect"
            }), 401
        session["name"] = username
        session["user_id"] = user_id
        conn.close()
        return jsonify({
            "success": True,
            "status_code": 200,
            "message": "Login successful"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "status_code": 500,
            "message": "Failed to authenticate due to server error"
        }), 500

@bp_auth.route("/logout")
def logout():
    session["name"] = None
    session["user_id"] = None
    return jsonify({
        "success": True,
        "status_code": 200,
        "message": "Logged out successfully"
    }), 200

@bp_auth.post('/change-password')
def change_password():
    """Change user password with validation"""
    if not session.get("user_id"):
        return jsonify({
            "success": False,
            "error": "Not authenticated",
            "status_code": 401
        }), 401
    
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    
    if not current_password or not new_password:
        return jsonify({
            "success": False,
            "error": "All fields are required",
            "status_code": 400
        }), 400
    
    if current_password == new_password:
        return jsonify({
            "success": False,
            "error": "New password must be different from current password",
            "status_code": 400
        }), 400
    
    try:
        user_id = session.get("user_id")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""SELECT Password_Hash FROM USER WHERE User_ID = ?""", (user_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({
                "success": False,
                "error": "User not found",
                "status_code": 404
            }), 404
        stored_hash = result[0]
        # bcrypt.checkpw returns True if password matches
        if not checkpw(current_password.encode(), stored_hash.encode()):
            conn.close()
            return jsonify({
                "success": False,
                "error": "Current password is incorrect",
                "status_code": 401
            }), 401
        # bcrypt automatically generates salt and hashes
        new_password_bytes = new_password.encode()
        new_hash = hashpw(new_password_bytes, gensalt()).decode()
        cursor.execute("""UPDATE USER SET Password_Hash = ? WHERE User_ID = ?""",
                      (new_hash, user_id))
        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "message": "Password changed successfully",
            "status_code": 200
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "status_code": 500
        }), 500
    
@bp_auth.post('/delete-account')
def delete_account():
    """Deactivate user account"""
    # check if is logged in
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not authenticated", "status_code": 401}), 401
    user_id = session["user_id"]

    # get option from request
    data = request.get_json(silent=True) or {}
    option = (data.get("option") if isinstance(data, dict) else None) or "anonymize"

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # reasign comments to the deleted user acc
        if option == "anonymize":
            cursor.execute("""UPDATE Comment SET User_ID = 0 WHERE User_ID = ?""", (user_id,))
            cursor.execute("""UPDATE Email SET User_ID = 0 WHERE User_ID = ?""", (user_id,))

        # handle option2
        elif option == "delete":
            cursor.execute("""DELETE FROM Comment WHERE User_ID = ?""", (user_id,))
            cursor.execute("""DELETE FROM Email WHERE User_ID = ?""", (user_id,))
            # ska vi ta bort analysis också? om inte ta bort följande del
            cursor.execute("""DELETE FROM Analysis WHERE Email_ID NOT IN (SELECT Email_ID FROM Email)""")
        
        # remove the user entirely
        cursor.execute("""DELETE FROM User WHERE User_ID = ?""", (user_id,))

        conn.commit()
        conn.close()
        session.clear()
        return jsonify({"success": True, "message": "Account deleted successfully", "status_code": 200}), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Database error: {str(e)}", "status_code": 500, 
                        "message": "Failed to delete account due to server error"}), 500
