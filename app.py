from flask import Flask, render_template, redirect, url_for, session, jsonify, request, flash
import os

# Import services dan controllers
from services.database_service import DatabaseService
from services.auth_service import AuthService
from services.security_service import SecurityService  # ← UNCOMMENT KARENA SUDAH PAKAI FALLBACK
from controllers.auth_controller import AuthController
from controllers.admin_controller import AdminController

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# Initialize services DENGAN SECURITY SERVICE YANG BARU
security_service = SecurityService()  # ← UNCOMMENT - SEKARAN AMAN
database_service = DatabaseService(security_service)  # ← INJECT SECURITY
auth_service = AuthService(database_service, security_service)  # ← INJECT SECURITY

# Initialize controllers
auth_controller = AuthController(auth_service)
admin_controller = AdminController(auth_service, database_service)

# ==========================
#        ROUTES
# ==========================

# Auth Routes
@app.route("/")
@app.route("/homepage")
def homepage():
    return auth_controller.homepage()

@app.route("/register", methods=["GET", "POST"])
def register():
    return auth_controller.register()

@app.route("/login", methods=["GET", "POST"])
def login():
    return auth_controller.login()

@app.route("/logout")
def logout():
    return auth_controller.logout()

# Admin Routes
@app.route("/admin")
def admin_panel():
    return admin_controller.admin_panel()

# API Routes
@app.route("/api/auth/check")
def auth_check():
    return auth_controller.auth_check()

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    return auth_controller.api_login()

@app.route("/api/auth/register", methods=["POST"])
def api_register():
    return auth_controller.api_register()

@app.route("/api/admin/stats")
def admin_stats():
    return admin_controller.admin_stats()

@app.route("/api/admin/users")
def admin_users():
    return admin_controller.admin_users()

@app.route("/api/concerts")
def concerts():
    token = session.get('token')
    response = database_service.get_concerts(token)
    
    if response and response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify([
            {'id': 1, 'name': 'The Mystic Symphony', 'artist': 'Coldplay', 'date': '2024-12-15', 'venue': 'GBK Stadium', 'price': 750000, 'available_tickets': 1000},
            {'id': 2, 'name': 'Blackpink Show', 'artist': 'Blackpink', 'date': '2024-11-20', 'venue': 'Istora Senayan', 'price': 1200000, 'available_tickets': 500}
        ])

# User routes (tetap sama persis)
@app.route("/concert")
def concert():
    user = auth_service.get_current_user()
    if not user.is_authenticated() or user.role != 'user':
        return redirect(url_for("login"))
    return render_template("user/concert.html")

@app.route("/account")
def account():
    user = auth_service.get_current_user()
    if not user.is_authenticated() or user.role != 'user':
        return redirect(url_for("login"))
    return render_template("user/account.html", username=user.username, email=user.email)

@app.route("/payment")
def payment():
    user = auth_service.get_current_user()
    if not user.is_authenticated() or user.role != 'user':
        return redirect(url_for("login"))
    return render_template("user/payment.html")

@app.route("/success")
def success():
    user = auth_service.get_current_user()
    if not user.is_authenticated() or user.role != 'user':
        return redirect(url_for("login"))
    return render_template("user/success.html")

if __name__ == "__main__":
    print("🚀 Server starting...")
    print("📊 Database: External API Service")
    print("🔗 Database API URL:", database_service.api_url)
    print("🔒 Security: Enhanced with SHA-256 hashing & input sanitization")  # ← UPDATE MESSAGE
    app.run(debug=True, host='0.0.0.0', port=5000)