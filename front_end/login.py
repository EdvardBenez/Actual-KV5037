# Import required libraries # Author Brandon Ayre #24025960
from flask import Flask, render_template_string, request, redirect, session
from flask_bcrypt import Bcrypt
from datetime import datetime
import sqlite3, os

# Create Flask app
app = Flask(__name__)

# Secret key used for session security (CHANGE THIS IN REAL DEPLOYMENT)
app.secret_key = "change_this_to_a_secure_random_value"

# Used to hash passwords securely
bcrypt = Bcrypt(app)

#Database file path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'users.db')


# ---------------- DATABASE FUNCTIONS ----------------

def get_db():
    return sqlite3.connect(DB_PATH)


def create_users_table():
    con = get_db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        password_changed_at TEXT
    )
    """)

    con.commit()
    con.close()


# ---------------- ROUTES ----------------
from flask import send_from_directory

# Serve files from the assets folder
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)


@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard/")
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    # If user submits the login form
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Connect to database
        con = get_db()
        cur = con.cursor()

        # Find user in database
        cur.execute(
            "SELECT id, username, password, password_changed_at FROM users WHERE username = ?",
            (username,)
        )
        user = cur.fetchone()
        con.close()

        # Check if user exists and password is correct
        if user and bcrypt.check_password_hash(user[2], password):
            session["user"] = username
            session["password_changed_at"] = user[3]
            return redirect("/dashboard/")

        # If login fails
        error = "Invalid username or password"

    # Show login page
    return render_template_string(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign in</title>
    <style>
        body {{
            margin: 0;
            font-family: "Segoe UI", Arial, sans-serif;
            background: #f3f2f1;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}

        .page-wrapper {{
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }}

        .login-box {{
            background: #ffffff;
            width: 360px;
            padding: 44px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
            border-radius: 2px;
        }}

        .logo {{
            width: 120px;
            margin-bottom: 16px;
        }}

        h1 {{
            font-size: 24px;
            font-weight: 600;
            color: #1b1b1b;
            margin: 0 0 10px 0;
        }}

        .subtitle {{
            font-size: 14px;
            color: #605e5c;
            margin-bottom: 24px;
        }}

        .input-group {{
            margin-bottom: 16px;
        }}

        input {{
            width: 100%;
            padding: 10px 8px;
            font-size: 15px;
            border: none;
            border-bottom: 1px solid #8a8886;
            background: transparent;
            box-sizing: border-box;
        }}

        input:focus {{
            outline: none;
            border-bottom: 2px solid #0078d4;
        }}

        .error {{
            color: #a4262c;
            font-size: 13px;
            margin: 10px 0 0 0;
        }}

        .button-row {{
            margin-top: 26px;
            display: flex;
            justify-content: flex-end;
        }}

        button {{
            background: #0078d4;
            color: white;
            border: none;
            padding: 9px 28px;
            font-size: 14px;
            cursor: pointer;
            min-width: 108px;
        }}

        button:hover {{
            background: #106ebe;
        }}

        .footer-note {{
            margin-top: 22px;
            font-size: 12px;
            color: #605e5c;
        }}
    </style>
</head>
<body>
    <div class="page-wrapper">
       <div class="login-box">

    <img class="logo" src="/assets/northumbriaUniLogo.png" alt="Logo">

    <h1>Sign in</h1>
    <div class="subtitle">Equipment Loans Centre Footfall Dashboard</div>

            <form method="post">
                <div class="input-group">
                    <input name="username" placeholder="Username" required>
                </div>

                <div class="input-group">
                    <input name="password" type="password" placeholder="Password" required>
                </div>

                {"<div class='error'>" + error + "</div>" if error else ""}

                <div class="button-row">
                    <button type="submit">Sign in</button>
                </div>
            </form>

            <div class="footer-note">
                Authorised admin access only
            </div>
        </div>
    </div>
</body>
</html>
""")


@app.route("/dashboard")
def dashboard_redirect():
    if "user" not in session:
        return redirect("/login")
    return redirect("/dashboard/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- SECURITY ----------------

@app.before_request
def protect_dash_routes():
    if request.path.startswith("/dashboard"):

        if "user" not in session:
            return redirect("/login")

        con = get_db()
        cur = con.cursor()
        cur.execute(
            "SELECT password_changed_at FROM users WHERE username = ?",
            (session["user"],)
        )
        user = cur.fetchone()
        con.close()

        if not user:
            session.clear()
            return redirect("/login")

        if session.get("password_changed_at") != user[0]:
            session.clear()
            return redirect("/login")


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    create_users_table()
    app.run(debug=False, host="0.0.0.0", port=8050)
