from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import os
import jwt
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Database API Configuration
DATABASE_API_URL = os.getenv('DATABASE_API_URL', 'http://localhost:8000')
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Helper functions untuk call Database API
def db_api_request(method, endpoint, data=None, token=None):
    try:
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        
        if method.upper() == 'GET':
            response = requests.get(f"{DATABASE_API_URL}{endpoint}", headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(f"{DATABASE_API_URL}{endpoint}", json=data, headers=headers)
        else:
            return None
            
        return response
    except requests.exceptions.RequestException as e:
        print(f"Database API error: {e}")
        return None

def get_current_user():
    """Get current user from session token"""
    token = session.get('token')
    if not token:
        return None
    
    try:
        response = db_api_request('GET', '/api/check-session', token=token)
        if response and response.status_code == 200:
            return response.json().get('user')
    except Exception as e:
        print(f"Error getting current user: {e}")
    
    return None

# ==========================
#        ROUTES
# ==========================

@app.route("/")
@app.route("/homepage")
def homepage():
    print(f"🏠 Homepage access - Session: {dict(session)}")
    
    user = get_current_user()
    if not user:
        print("❌ No valid user session - redirect to login")
        return redirect(url_for("login"))
    
    # Jika admin → arahkan ke admin panel
    if user.get("role") == "admin":
        print("🔧 Admin detected - redirect to admin panel")
        return redirect(url_for("admin_panel"))
    
    # Jika user → tampilkan homepage
    print(f"✅ User {user['username']} accessing homepage")
    return render_template("user/homepage.html", username=user["username"])  # ✅ DIPERBAIKI

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        print(f"🔰 Register attempt: {username} ({email})")

        # Validasi confirm password
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            print("❌ Password mismatch")
            return render_template("user/register.html")  # ✅ DIPERBAIKI

        # Register user via Database API
        response = db_api_request('POST', '/api/users', {
            'username': username,
            'email': email,
            'password': password,
            'role': 'user'
        })

        if response and response.status_code == 201:
            data = response.json()
            print(f"✅ User created via API - ID: {data['id']}")
            
            # Auto login setelah register
            login_response = db_api_request('POST', '/api/login', {
                'identifier': email,
                'password': password
            })
            
            if login_response and login_response.status_code == 200:
                login_data = login_response.json()
                session['token'] = login_data['token']
                session['user_id'] = login_data['user']['id']
                session['username'] = login_data['user']['username']
                session['role'] = login_data['user']['role']
                
                print(f"✅ Auto-login successful - user_id: {session['user_id']}")
                flash("Registration successful! Welcome!", "success")
                return redirect(url_for("homepage"))
            else:
                flash("Registration successful! Please login.", "success")
                return redirect(url_for("login"))
        else:
            error_msg = "Registration failed!"
            if response:
                error_details = response.json().get('error', 'Unknown error')
                error_msg = f"Registration failed: {error_details}"
            flash(error_msg, "error")
            print(f"❌ Registration failed: {error_msg}")
            return render_template("user/register.html")  # ✅ DIPERBAIKI

    return render_template("user/register.html")  # ✅ DIPERBAIKI

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form["email"].strip()
        password = request.form["password"].strip()
        
        print(f"🔐 Login attempt: {identifier}")

        # Login via Database API
        response = db_api_request('POST', '/api/login', {
            'identifier': identifier,
            'password': password
        })

        if response and response.status_code == 200:
            data = response.json()
            
            # Set session
            session['token'] = data['token']
            session['user_id'] = data['user']['id']
            session['username'] = data['user']['username']
            session['email'] = data['user']['email']
            session['role'] = data['user']['role']
            
            print(f"✅ Login successful - Role: {session['role']}")
            flash(f"Welcome back, {session['username']}!", "success")
            
            if session['role'] == 'admin':
                return redirect(url_for("admin_panel"))
            else:
                return redirect(url_for("homepage"))
        else:
            error_msg = "Invalid credentials!"
            if response:
                error_details = response.json().get('error', 'Unknown error')
                error_msg = f"Login failed: {error_details}"
            flash(error_msg, "danger")
            print(f"❌ Login failed: {error_msg}")
            return render_template("user/login.html")  # ✅ DIPERBAIKI

    return render_template("user/login.html")  # ✅ DIPERBAIKI

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/admin")
def admin_panel():
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        flash("Access denied! Admin only.", "danger")
        return redirect(url_for("login"))
    return render_template("adminpanel.html")  # ✅ SUDAH BENAR

# Routes user lainnya...
@app.route("/concert")
def concert():
    user = get_current_user()
    if not user or user.get('role') != 'user':
        return redirect(url_for("login"))
    return render_template("user/concert.html")  # ✅ DIPERBAIKI

@app.route("/account")
def account():
    user = get_current_user()
    if not user or user.get('role') != 'user':
        return redirect(url_for("login"))
    
    return render_template(
        "user/account.html",  # ✅ DIPERBAIKI
        username=user['username'],
        email=user['email'],
        join_date=user.get('join_date', 'Unknown')
    )

@app.route("/payment")
def payment():
    user = get_current_user()
    if not user or user.get('role') != 'user':
        return redirect(url_for("login"))
    return render_template("user/payment.html")  # ✅ DIPERBAIKI

@app.route("/success")
def success():
    user = get_current_user()
    if not user or user.get('role') != 'user':
        return redirect(url_for("login"))
    return render_template("user/success.html")  # ✅ DIPERBAIKI

if __name__ == "__main__":
    print("🚀 Server starting...")
    print("📊 Database: External API Service")
    print("🔗 Database API URL:", DATABASE_API_URL)
    print("👤 Admin login: admin@guardiantix.com / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)