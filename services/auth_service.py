from flask import session
from models.user import User

class AuthService:
    def __init__(self, database_service):
        self.db = database_service
    
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
        if password != confirm_password:
            return {'success': False, 'error': 'Passwords do not match!'}
        
        response = self.db.register_user(username, email, password)
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