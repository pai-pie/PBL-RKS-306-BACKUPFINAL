from flask import Flask, render_template, redirect, url_for, session, jsonify, request, flash
import os
import time

# Import services dan controllers
from services.database_service import DatabaseService
from services.auth_service import AuthService
from services.security_service import SecurityService
from controllers.auth_controller import AuthController
from controllers.admin_controller import AdminController

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# ==========================
#   INITIALIZE SERVICES - DOCKER VERSION
# ==========================

# Dapatkan environment variables untuk Docker
DATABASE_API_URL = os.getenv('DATABASE_API_URL', 'http://localhost:8000')
print(f"🔗 Database API URL: {DATABASE_API_URL}")

# Initialize services
security_service = SecurityService()
database_service = DatabaseService(security_service)
database_service.api_url = DATABASE_API_URL  # ← OVERRIDE UNTUK DOCKER

auth_service = AuthService(database_service, security_service)

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

# User routes
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

# Health check endpoint
@app.route("/health")
def health_check():
    """Health check endpoint untuk Docker"""
    try:
        user = auth_service.get_current_user()
        return jsonify({
            "status": "healthy",
            "service": "GuardianTix Web App",
            "database_connected": user.is_authenticated() if user else False,
            "database_api_url": DATABASE_API_URL
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

# ==========================
#   APPLICATION STARTUP
# ==========================

def wait_for_services():
    """Tunggu services lain siap (untuk Docker)"""
    print("⏳ Waiting for backend services to be ready...")
    time.sleep(15)  # Tunggu lebih lama
    print("✅ Starting web application...")

if __name__ == "__main__":
    # Tunggu services siap sebelum start
    wait_for_services()
    
    print("🚀 Server starting...")
    print("📊 Database: MySQL (Docker)")
    print("🔗 Database API URL:", DATABASE_API_URL)
    print("🔒 Security: Enhanced with SHA-256 hashing & input sanitization")
    print("🏠 Host: 0.0.0.0:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)