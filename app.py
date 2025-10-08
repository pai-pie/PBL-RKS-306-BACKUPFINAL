from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
import os
import jwt
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session

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

def verify_admin_access():
    """Verify if current user is admin"""
    user = get_current_user()
    return user and user.get('role') == 'admin'

# ==========================
#        ROUTES
# ==========================

@app.route("/")
@app.route("/homepage")
def homepage():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    if user.get("role") == "admin":
        return redirect(url_for("admin_panel"))
    
    return render_template("user/homepage.html", username=user["username"])

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return render_template("user/register.html")

        response = db_api_request('POST', '/api/users', {
            'username': username,
            'email': email,
            'password': password,
            'role': 'user'
        })

        if response and response.status_code == 201:
            data = response.json()
            
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
                session.permanent = True
                
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
            return render_template("user/register.html")

    return render_template("user/register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form["email"].strip()
        password = request.form["password"].strip()

        response = db_api_request('POST', '/api/login', {
            'identifier': identifier,
            'password': password
        })

        if response and response.status_code == 200:
            data = response.json()
            
            session['token'] = data['token']
            session['user_id'] = data['user']['id']
            session['username'] = data['user']['username']
            session['email'] = data['user']['email']
            session['role'] = data['user']['role']
            session.permanent = True
            
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
            return render_template("user/login.html")

    return render_template("user/login.html")

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
    return render_template("adminpanel.html")

# API Endpoints untuk JavaScript
@app.route("/api/auth/check")
def auth_check():
    """Check if user is authenticated"""
    user = get_current_user()
    if user:
        return jsonify({
            'authenticated': True,
            'user': user,
            'token': session.get('token')
        })
    else:
        return jsonify({'authenticated': False}), 401

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """API login untuk JavaScript"""
    data = request.json
    identifier = data.get('identifier', '').strip()
    password = data.get('password', '').strip()

    response = db_api_request('POST', '/api/login', {
        'identifier': identifier,
        'password': password
    })

    if response and response.status_code == 200:
        data = response.json()
        session['token'] = data['token']
        session['user_id'] = data['user']['id']
        session['username'] = data['user']['username']
        session['role'] = data['user']['role']
        session.permanent = True
        
        return jsonify({
            'success': True,
            'user': data['user'],
            'redirect': '/admin' if data['user']['role'] == 'admin' else '/homepage'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401

@app.route("/api/auth/register", methods=["POST"])
def api_register():
    """API register untuk JavaScript"""
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    response = db_api_request('POST', '/api/users', {
        'username': username,
        'email': email,
        'password': password,
        'role': 'user'
    })

    if response and response.status_code == 201:
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
            session.permanent = True
            
            return jsonify({
                'success': True,
                'user': login_data['user'],
                'redirect': '/homepage'
            })
    
    return jsonify({
        'success': False,
        'error': 'Registration failed'
    }), 400

# Admin API endpoints
@app.route("/api/admin/stats")
def admin_stats():
    if not verify_admin_access():
        return jsonify({'error': 'Not authorized'}), 401
    
    token = session.get('token')
    response = db_api_request('GET', '/api/admin/stats', token=token)
    
    if response and response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({
            'total_users': 2,
            'total_concerts': 3,
            'recent_users': 1,
            'total_tickets_sold': 1200,
            'total_revenue': 850000000,
            'pending_transactions': 20
        })

@app.route("/api/admin/users")
def admin_users():
    if not verify_admin_access():
        return jsonify({'error': 'Not authorized'}), 401
    
    token = session.get('token')
    response = db_api_request('GET', '/api/admin/users', token=token)
    
    if response and response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify([
            {'id': 1, 'username': 'System Admin', 'email': 'admin@guardiantix.com', 'phone': None, 'role': 'admin', 'join_date': '2024-01-01'},
            {'id': 2, 'username': 'pai', 'email': 'pai@gmail.com', 'phone': None, 'role': 'user', 'join_date': '2024-01-01'}
        ])

@app.route("/api/concerts")
def concerts():
    token = session.get('token')
    response = db_api_request('GET', '/api/concerts', token=token)
    
    if response and response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify([
            {'id': 1, 'name': 'The Mystic Symphony', 'artist': 'Coldplay', 'date': '2024-12-15', 'venue': 'GBK Stadium', 'price': 750000, 'available_tickets': 1000},
            {'id': 2, 'name': 'Blackpink Show', 'artist': 'Blackpink', 'date': '2024-11-20', 'venue': 'Istora Senayan', 'price': 1200000, 'available_tickets': 500}
        ])

# User routes
@app.route("/concert")
def concert():
    user = get_current_user()
    if not user or user.get('role') != 'user':
        return redirect(url_for("login"))
    return render_template("user/concert.html")

@app.route("/account")
def account():
    user = get_current_user()
    if not user or user.get('role') != 'user':
        return redirect(url_for("login"))
    return render_template("user/account.html", username=user['username'], email=user['email'])

@app.route("/payment")
def payment():
    user = get_current_user()
    if not user or user.get('role') != 'user':
        return redirect(url_for("login"))
    return render_template("user/payment.html")

@app.route("/success")
def success():
    user = get_current_user()
    if not user or user.get('role') != 'user':
        return redirect(url_for("login"))
    return render_template("user/success.html")

if __name__ == "__main__":
    print("🚀 Server starting...")
    print("📊 Database: External API Service")
    print("🔗 Database API URL:", DATABASE_API_URL)
    app.run(debug=True, host='0.0.0.0', port=5000)