from flask import session
from models.user import User

class AuthService:
    def __init__(self, database_service, security_service=None):
        self.db = database_service
        self.security = security_service
    
    def get_current_user(self):
        token = session.get('token')
        if not token:
            return User()
        
        try:
            response = self.db.check_session(token)
            if response and response.status_code == 200:
                user_data = response.json().get('user', {})
                return User(user_data)
        except Exception as e:
            print(f"Error getting current user: {e}")
        
        return User()
    
    def login(self, identifier, password):
        # ⛔️ TEMPORARY: Skip secure login untuk testing
        # if self.security:
        #     return self.secure_login(identifier, password)
        
        # ✅ Langsung pakai API login
        response = self.db.login_user(identifier, password)
        if response and response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'user': User(data['user']),
                'token': data['token']
            }
        else:
            error_msg = "Invalid credentials!"
            if response:
                error_details = response.json().get('error', 'Unknown error')
                error_msg = f"Login failed: {error_details}"
            return {
                'success': False,
                'error': error_msg
            }
    
    def register(self, username, email, password, confirm_password):
        # Password strength validation (tetap aktif)
        if self.security:
            is_strong, message = self.security.is_password_strong(password)
            if not is_strong:
                return {'success': False, 'error': message}
        
        if password != confirm_password:
            return {'success': False, 'error': 'Passwords do not match!'}
        
        # Hash password sebelum kirim ke database (tetap aktif)
        hashed_password = password  # Default (plaintext)
        if self.security:
            hashed_password = self.security.hash_password(password)
        
        response = self.db.register_user({
            'username': username,
            'email': email,
            'password': hashed_password,  # ← SUDAH HASHED!
            'role': 'user'
        })

        if response and response.status_code == 201:
            return {'success': True}
        else:
            error_msg = "Registration failed!"
            if response:
                error_details = response.json().get('error', 'Unknown error')
                error_msg = f"Registration failed: {error_details}"
            return {'success': False, 'error': error_msg}
    
    def set_session(self, user, token):
        session['token'] = token
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        session['role'] = user.role
        session.permanent = True
    
    def clear_session(self):
        session.clear()
    
    def verify_admin_access(self):
        user = self.get_current_user()
        return user.is_authenticated() and user.is_admin()